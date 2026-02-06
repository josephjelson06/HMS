from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.user import User


class ProfileService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, user_id) -> User | None:
        return await self.session.get(User, user_id)

    async def update(self, user: User, payload) -> User:
        if payload.first_name is not None:
            user.first_name = payload.first_name
        if payload.last_name is not None:
            user.last_name = payload.last_name

        if payload.new_password:
            if not payload.current_password:
                raise ValueError("Current password required to change password")
            if not verify_password(payload.current_password, user.password_hash):
                raise ValueError("Current password is incorrect")
            user.password_hash = hash_password(payload.new_password)

        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
