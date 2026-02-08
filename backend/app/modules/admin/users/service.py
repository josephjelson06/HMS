from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.security import hash_password
from app.models.rbac import Role, UserRole
from app.models.user import User


class AdminUserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_users(
        self, page: int, limit: int
    ) -> tuple[list[tuple[User, list[str]]], int]:
        page = max(page, 1)
        limit = max(min(limit, 100), 1)

        total = await self.session.scalar(
            select(func.count()).select_from(User).where(User.user_type == "platform")
        )

        stmt = (
            select(User, Role.name)
            .join(UserRole, UserRole.user_id == User.id, isouter=True)
            .join(Role, Role.id == UserRole.role_id, isouter=True)
            .where(User.user_type == "platform")
            .order_by(User.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        rows = result.all()

        users: dict[UUID, tuple[User, list[str]]] = {}
        for user, role_name in rows:
            entry = users.get(user.id)
            if entry is None:
                users[user.id] = (user, [] if not role_name else [role_name])
            else:
                if role_name:
                    entry[1].append(role_name)

        return list(users.values()), int(total or 0)

    async def list_roles(self) -> list[Role]:
        stmt = (
            select(Role)
            .where(Role.role_type == "admin", Role.tenant_id.is_(None))
            .order_by(Role.display_name.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get(self, user_id: UUID) -> User | None:
        return await self.session.get(User, user_id)

    async def get_roles_for_user(self, user_id: UUID) -> list[str]:
        stmt = (
            select(Role.name)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return [row[0] for row in result.fetchall()]

    async def create(self, payload) -> User:
        existing = await self.session.scalar(
            select(User).where(User.email == payload.email)
        )
        if existing:
            raise ValueError("Email already exists")

        role = await self.session.get(Role, payload.role_id)
        if not role or role.role_type != "admin" or role.tenant_id is not None:
            raise ValueError("Invalid role")

        user = User(
            email=payload.email,
            username=payload.email.split('@')[0],  # Extract username from email
            password_hash=hash_password(payload.password),
            first_name=payload.first_name,
            last_name=payload.last_name,
            user_type="platform",
            tenant_id=None,
            is_active=payload.is_active,
        )
        self.session.add(user)
        await self.session.flush()

        self.session.add(UserRole(user_id=user.id, role_id=role.id))
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update(self, user: User, payload) -> User:
        if payload.email is not None and payload.email != user.email:
            existing = await self.session.scalar(
                select(User).where(User.email == payload.email)
            )
            if existing:
                raise ValueError("Email already exists")
            user.email = payload.email

        if payload.first_name is not None:
            user.first_name = payload.first_name
        if payload.last_name is not None:
            user.last_name = payload.last_name
        if payload.password is not None:
            user.password_hash = hash_password(payload.password)
        if payload.is_active is not None:
            user.is_active = payload.is_active

        if payload.role_id is not None:
            role = await self.session.get(Role, payload.role_id)
            if not role or role.role_type != "admin" or role.tenant_id is not None:
                raise ValueError("Invalid role")

            await self.session.execute(
                UserRole.__table__.delete().where(UserRole.user_id == user.id)
            )
            self.session.add(UserRole(user_id=user.id, role_id=role.id))

        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        await self.session.delete(user)
        await self.session.commit()
