from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    generate_csrf_token,
    hash_token,
    verify_password_constant_time,
)
from app.models.audit import AuditLog
from app.models.tenant import Tenant
from app.models.user import User
from app.modules.auth.refresh_tokens import (
    issue_new_refresh_token_family,
    rotate_refresh_token,
    revoke_family_by_refresh_token,
    RefreshTokenError,
    RefreshTokenReuseDetectedError,
)
from app.modules.auth.schemas import AuthResponse, TenantOut, UserOut
from app.repositories.impersonation import ImpersonationSessionRepository
from app.repositories.permission import PermissionRepository
from app.repositories.token import RefreshTokenRepository
from app.repositories.user import UserRepository


@dataclass
class AuthResult:
    response: AuthResponse
    access_token: str
    refresh_token: str
    csrf_token: str


class AuthService:
    def __init__(self, session: AsyncSession, request: Request) -> None:
        self.session = session
        self.request = request
        self.user_repo = UserRepository(session)
        self.perm_repo = PermissionRepository(session)
        self.token_repo = RefreshTokenRepository(session)
        self.impersonation_repo = ImpersonationSessionRepository(session)

    async def login(self, email: str, password: str) -> AuthResult:
        user = await self.user_repo.get_by_email(email)
        password_hash = user.password_hash if user is not None else None
        authenticated = verify_password_constant_time(password, password_hash)

        if not authenticated or user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User inactive")

        roles = await self.perm_repo.get_role_names_for_user(user.id)
        permissions = await self.perm_repo.get_permissions_for_user(user.id)
        tenant = await self._get_tenant_context(user)

        refresh_token_override = None
        # Use family tokens only when a tenant context exists.
        if user.tenant_id is not None:
            family_result = await issue_new_refresh_token_family(
                self.session,
                tenant_id=user.tenant_id,
                user_id=user.id,
                refresh_token_days=settings.jwt_refresh_ttl_days,
                created_by_user_id=user.id,
            )
            refresh_token_override = family_result.raw_token

        result = await self._issue_auth_result(
            user=user,
            roles=roles,
            permissions=permissions,
            tenant=tenant,
            impersonation=None,
            refresh_token_override=refresh_token_override,
        )
        await self.session.commit()
        return result

    async def refresh(self, refresh_token: str | None) -> AuthResult:
        if not refresh_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token")

        stored = await self.token_repo.get_by_hash(hash_token(refresh_token))
        if not stored or stored.revoked_at or stored.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        # Legacy path (non-family tokens), used for platform users during transition.
        if stored.family_id is None:
            user = await self.user_repo.get_by_id(UUID(str(stored.user_id)))
            if not user or not user.is_active:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

            roles = await self.perm_repo.get_role_names_for_user(user.id)
            permissions = await self.perm_repo.get_permissions_for_user(user.id)
            tenant = await self._get_tenant_context(user)

            impersonation = None
            if stored.impersonation_session_id and stored.impersonated_by_user_id:
                imp_session = await self.impersonation_repo.get_active_by_id(stored.impersonation_session_id)
                if not imp_session or str(imp_session.acting_as_user_id) != str(user.id):
                    await self.token_repo.revoke(stored)
                    await self.session.commit()
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Impersonation session ended")
                imp_tenant = await self.session.get(Tenant, imp_session.tenant_id)
                impersonation = self._build_impersonation_context(imp_session, imp_tenant)

            await self.token_repo.revoke(stored)

            result = await self._issue_auth_result(
                user=user,
                roles=roles,
                permissions=permissions,
                tenant=tenant,
                impersonation=impersonation,
                impersonation_session_id=stored.impersonation_session_id,
                impersonated_by_user_id=stored.impersonated_by_user_id,
            )
            await self.session.commit()
            return result

        # Family-token path with rotation + reuse detection.
        try:
            rotated = await rotate_refresh_token(
                self.session,
                raw_token=refresh_token,
                refresh_token_days=settings.jwt_refresh_ttl_days,
            )
        except RefreshTokenReuseDetectedError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token reuse detected. All sessions revoked.",
            )
        except RefreshTokenError as exc:
            raise HTTPException(
                status_code=exc.status_code,
                detail=exc.detail,
            )

        user = await self.user_repo.get_by_id(rotated.user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

        roles = await self.perm_repo.get_role_names_for_user(user.id)
        permissions = await self.perm_repo.get_permissions_for_user(user.id)
        tenant = await self._get_tenant_context(user)

        impersonation = None
        new_token_hash = hash_token(rotated.raw_token)
        new_stored = await self.token_repo.get_by_hash(new_token_hash)
        if new_stored and new_stored.impersonation_session_id and new_stored.impersonated_by_user_id:
            imp_session = await self.impersonation_repo.get_active_by_id(new_stored.impersonation_session_id)
            if not imp_session or str(imp_session.acting_as_user_id) != str(user.id):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Impersonation session ended")
            imp_tenant = await self.session.get(Tenant, imp_session.tenant_id)
            impersonation = self._build_impersonation_context(imp_session, imp_tenant)

        result = await self._issue_auth_result(
            user=user,
            roles=roles,
            permissions=permissions,
            tenant=tenant,
            refresh_token_override=rotated.raw_token,
            impersonation=impersonation,
        )
        await self.session.commit()
        return result

    async def logout(self, refresh_token: str | None) -> None:
        if refresh_token:
            stored = await self.token_repo.get_by_hash(hash_token(refresh_token))
            if stored and stored.family_id is None:
                if not stored.revoked_at:
                    await self.token_repo.revoke(stored)
            else:
                try:
                    await revoke_family_by_refresh_token(
                        self.session,
                        raw_token=refresh_token,
                        reason="logout",
                    )
                except RefreshTokenError:
                    pass  # Token already invalid — still clear cookies
        await self.session.commit()

    async def start_impersonation(
        self,
        *,
        admin_user_id: UUID,
        tenant_id: UUID | None,
        target_user_id: UUID | None,
        reason: str | None,
    ) -> AuthResult:
        admin_user = await self.user_repo.get_by_id(admin_user_id)
        if not admin_user or not admin_user.is_active or admin_user.user_type != "platform":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only platform admins can impersonate")

        existing = await self.impersonation_repo.get_active_for_actor(admin_user_id)
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An impersonation session is already active")

        target_user: User | None = None

        if target_user_id:
            target = await self.user_repo.get_by_id(target_user_id)
            if not target or not target.is_active or target.user_type != "hotel":
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target user not found")
            if tenant_id and str(target.tenant_id) != str(tenant_id):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Target user does not belong to tenant")
            target_user = target
        else:
            if tenant_id is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="tenant_id is required")
            target_user = await self.user_repo.get_default_hotel_manager_for_tenant(tenant_id)

        if not target_user or not target_user.tenant_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No eligible hotel user found for tenant")

        tenant = await self.session.get(Tenant, target_user.tenant_id)
        if not tenant:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

        imp_session = await self.impersonation_repo.create(
            actor_user_id=admin_user.id,
            acting_as_user_id=target_user.id,
            tenant_id=target_user.tenant_id,
            reason=reason,
            ip_address=self.request.client.host if self.request.client else None,
        )

        self.session.add(
            AuditLog(
                tenant_id=target_user.tenant_id,
                actor_user_id=admin_user.id,
                action="impersonation.started",
                resource_type="impersonation_session",
                resource_id=imp_session.id,
                metadata_json={
                    "target_user_id": str(target_user.id),
                    "target_user_email": target_user.email,
                    "target_tenant_id": str(target_user.tenant_id),
                    "reason": reason,
                },
                ip_address=self.request.client.host if self.request.client else None,
                user_agent=self.request.headers.get("user-agent"),
            )
        )

        roles = await self.perm_repo.get_role_names_for_user(target_user.id)
        permissions = await self.perm_repo.get_permissions_for_user(target_user.id)
        impersonation = self._build_impersonation_context(imp_session, tenant)

        # Issue new refresh token family for impersonation session
        family_result = await issue_new_refresh_token_family(
            self.session,
            tenant_id=target_user.tenant_id,
            user_id=target_user.id,
            refresh_token_days=settings.jwt_refresh_ttl_days,
            created_by_user_id=admin_user.id,
            impersonation_session_id=imp_session.id,
            impersonated_by_user_id=admin_user.id,
        )

        result = await self._issue_auth_result(
            user=target_user,
            roles=roles,
            permissions=permissions,
            tenant=TenantOut.model_validate(tenant),
            impersonation=impersonation,
            refresh_token_override=family_result.raw_token,
        )

        await self.session.commit()
        return result

    async def stop_impersonation(
        self,
        *,
        acting_user_id: UUID,
        impersonation: dict | None,
        current_refresh_token: str | None,
    ) -> AuthResult:
        if not impersonation or not impersonation.get("active"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active impersonation")

        session_id = impersonation.get("session_id")
        admin_user_id = impersonation.get("admin_user_id")
        if not session_id or not admin_user_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Impersonation context invalid")

        try:
            session_uuid = UUID(str(session_id))
            admin_uuid = UUID(str(admin_user_id))
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Impersonation context invalid") from exc

        imp_session = await self.impersonation_repo.get_active_by_id(session_uuid)
        if not imp_session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Impersonation session not found")

        if str(imp_session.acting_as_user_id) != str(acting_user_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid impersonation actor")
        if str(imp_session.actor_user_id) != str(admin_uuid):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid impersonation admin")

        admin_user = await self.user_repo.get_by_id(admin_uuid)
        if not admin_user or not admin_user.is_active or admin_user.user_type != "platform":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin user not found")

        await self.impersonation_repo.end(imp_session)

        # Revoke the impersonation token family
        if current_refresh_token:
            try:
                await revoke_family_by_refresh_token(
                    self.session,
                    raw_token=current_refresh_token,
                    reason="impersonation_ended",
                )
            except RefreshTokenError:
                pass  # Token already invalid

        self.session.add(
            AuditLog(
                tenant_id=imp_session.tenant_id,
                actor_user_id=admin_user.id,
                action="impersonation.ended",
                resource_type="impersonation_session",
                resource_id=imp_session.id,
                metadata_json={
                    "target_user_id": str(imp_session.acting_as_user_id),
                },
                ip_address=self.request.client.host if self.request.client else None,
                user_agent=self.request.headers.get("user-agent"),
            )
        )

        roles = await self.perm_repo.get_role_names_for_user(admin_user.id)
        permissions = await self.perm_repo.get_permissions_for_user(admin_user.id)
        tenant = await self._get_tenant_context(admin_user)

        refresh_token_override = None
        if admin_user.tenant_id is not None:
            family_result = await issue_new_refresh_token_family(
                self.session,
                tenant_id=admin_user.tenant_id,
                user_id=admin_user.id,
                refresh_token_days=settings.jwt_refresh_ttl_days,
                created_by_user_id=admin_user.id,
            )
            refresh_token_override = family_result.raw_token

        result = await self._issue_auth_result(
            user=admin_user,
            roles=roles,
            permissions=permissions,
            tenant=tenant,
            impersonation=None,
            refresh_token_override=refresh_token_override,
        )

        await self.session.commit()
        return result

    async def _get_tenant_context(self, user: User) -> TenantOut | None:
        if not user.tenant_id:
            return None
        tenant_obj = await self.session.get(Tenant, user.tenant_id)
        if not tenant_obj:
            return None
        return TenantOut.model_validate(tenant_obj)

    async def _issue_auth_result(
        self,
        *,
        user: User,
        roles: list[str],
        permissions: list[str],
        tenant: TenantOut | None,
        impersonation: dict | None,
        refresh_token_override: str | None = None,
        refresh_jti_override: str | None = None,
        impersonation_session_id: UUID | None = None,
        impersonated_by_user_id: UUID | None = None,
    ) -> AuthResult:
        token_payload = {
            "sub": str(user.id),
            "user_type": user.user_type,
            "roles": roles,
            "tenant_id": str(user.tenant_id) if user.user_type == "hotel" else None,
        }
        if impersonation:
            token_payload["impersonation"] = impersonation

        access_token = create_access_token(token_payload)

        # When using family system, refresh_token_override is provided
        # and we skip the old token creation logic
        refresh_token = refresh_token_override
        if refresh_token is None:
            # Fallback to old system (should not happen with new code)
            refresh_token, refresh_jti = create_refresh_token()
            await self.token_repo.create(
                user_id=user.id,
                tenant_id=user.tenant_id,
                jti=refresh_jti,
                token_hash=hash_token(refresh_token),
                expires_in_days=settings.jwt_refresh_ttl_days,
                ip_address=self.request.client.host if self.request.client else None,
                user_agent=self.request.headers.get("user-agent"),
                impersonation_session_id=impersonation_session_id,
                impersonated_by_user_id=impersonated_by_user_id,
            )

        csrf_token = generate_csrf_token()
        response = AuthResponse(
            user=UserOut(
                id=user.id,
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                user_type=user.user_type,
                tenant_id=user.tenant_id,
                roles=roles,
            ),
            permissions=permissions,
            tenant=tenant,
            impersonation=impersonation,
        )
        return AuthResult(
            response=response,
            access_token=access_token,
            refresh_token=refresh_token,
            csrf_token=csrf_token,
        )

    @staticmethod
    def _build_impersonation_context(session, tenant: Tenant | None) -> dict:
        return {
            "active": True,
            "tenant_id": str(session.tenant_id),
            "tenant_name": tenant.name if tenant else "Unknown Tenant",
            "session_id": str(session.id),
            "started_at": session.started_at.isoformat() if session.started_at else datetime.now(timezone.utc).isoformat(),
            "admin_user_id": str(session.actor_user_id),
            "target_user_id": str(session.acting_as_user_id),
        }
