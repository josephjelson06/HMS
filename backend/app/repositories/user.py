import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rbac import Role, UserRole
from app.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_email(self, email: str) -> User | None:
        return await self.session.scalar(select(User).where(User.email == email))

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return await self.session.get(User, user_id)

    async def get_hotel_user_by_tenant_and_id(
        self, tenant_id: uuid.UUID, user_id: uuid.UUID
    ) -> User | None:
        stmt = select(User).where(
            User.id == user_id,
            User.tenant_id == tenant_id,
            User.user_type == "hotel",
            User.is_active.is_(True),
        )
        return await self.session.scalar(stmt)

    async def get_default_hotel_manager_for_tenant(self, tenant_id: uuid.UUID) -> User | None:
        manager_stmt = (
            select(User)
            .join(UserRole, UserRole.user_id == User.id)
            .join(Role, Role.id == UserRole.role_id)
            .where(
                User.tenant_id == tenant_id,
                User.user_type == "hotel",
                User.is_active.is_(True),
                Role.role_type == "hotel",
                Role.name == "HotelManager",
            )
            .order_by(User.created_at.asc())
            .limit(1)
        )
        manager = await self.session.scalar(manager_stmt)
        if manager:
            return manager

        fallback_stmt = (
            select(User)
            .where(
                User.tenant_id == tenant_id,
                User.user_type == "hotel",
                User.is_active.is_(True),
            )
            .order_by(User.created_at.asc())
            .limit(1)
        )
        return await self.session.scalar(fallback_stmt)
