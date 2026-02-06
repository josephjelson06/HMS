from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.models.rbac import Permission, Role, RolePermission


class AdminRoleService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_roles(self) -> list[tuple[Role, list[str]]]:
        stmt = (
            select(Role, Permission.code)
            .join(RolePermission, RolePermission.role_id == Role.id, isouter=True)
            .join(
                Permission, Permission.id == RolePermission.permission_id, isouter=True
            )
            .where(Role.role_type == "admin", Role.tenant_id.is_(None))
            .order_by(Role.display_name.asc())
        )
        result = await self.session.execute(stmt)
        rows = result.all()

        roles: dict[UUID, tuple[Role, list[str]]] = {}
        for role, perm_code in rows:
            entry = roles.get(role.id)
            if entry is None:
                roles[role.id] = (role, [] if not perm_code else [perm_code])
            else:
                if perm_code:
                    entry[1].append(perm_code)

        return list(roles.values())

    async def list_permissions(self) -> list[Permission]:
        stmt = (
            select(Permission)
            .where(Permission.scope == "admin")
            .order_by(Permission.code.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get(self, role_id: UUID) -> Role | None:
        return await self.session.get(Role, role_id)

    async def get_permissions_for_role(self, role_id: UUID) -> list[str]:
        stmt = (
            select(Permission.code)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(RolePermission.role_id == role_id)
        )
        result = await self.session.execute(stmt)
        return [row[0] for row in result.fetchall()]

    async def create(self, payload) -> Role:
        existing = await self.session.scalar(
            select(Role).where(
                Role.name == payload.name,
                Role.role_type == "admin",
                Role.tenant_id.is_(None),
            )
        )
        if existing:
            raise ValueError("Role name already exists")

        permissions = await self._validate_permissions(payload.permissions)

        role = Role(
            name=payload.name,
            display_name=payload.display_name,
            description=payload.description,
            role_type="admin",
            is_system=False,
            tenant_id=None,
        )
        self.session.add(role)
        await self.session.flush()

        for perm in permissions:
            self.session.add(RolePermission(role_id=role.id, permission_id=perm.id))

        await self.session.commit()
        await self.session.refresh(role)
        return role

    async def update(self, role: Role, payload) -> Role:
        if role.is_system:
            raise ValueError("System roles cannot be modified")

        if payload.name is not None and payload.name != role.name:
            existing = await self.session.scalar(
                select(Role).where(
                    Role.name == payload.name,
                    Role.role_type == "admin",
                    Role.tenant_id.is_(None),
                    Role.id != role.id,
                )
            )
            if existing:
                raise ValueError("Role name already exists")
            role.name = payload.name

        if payload.display_name is not None:
            role.display_name = payload.display_name
        if payload.description is not None:
            role.description = payload.description

        if payload.permissions is not None:
            permissions = await self._validate_permissions(payload.permissions)
            await self.session.execute(
                RolePermission.__table__.delete().where(
                    RolePermission.role_id == role.id
                )
            )
            for perm in permissions:
                self.session.add(RolePermission(role_id=role.id, permission_id=perm.id))

        self.session.add(role)
        await self.session.commit()
        await self.session.refresh(role)
        return role

    async def delete(self, role: Role) -> None:
        if role.is_system:
            raise ValueError("System roles cannot be deleted")
        await self.session.delete(role)
        await self.session.commit()

    async def _validate_permissions(
        self, permission_codes: list[str]
    ) -> list[Permission]:
        if not permission_codes:
            return []
        stmt = select(Permission).where(
            Permission.code.in_(permission_codes), Permission.scope == "admin"
        )
        result = await self.session.execute(stmt)
        permissions = result.scalars().all()
        if len(permissions) != len(set(permission_codes)):
            raise ValueError("One or more permissions are invalid")
        return permissions
