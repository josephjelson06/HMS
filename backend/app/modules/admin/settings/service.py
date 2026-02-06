from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.platform_setting import PlatformSetting


class SettingsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list(self, page: int, limit: int) -> tuple[list[PlatformSetting], int]:
        page = max(page, 1)
        limit = max(min(limit, 100), 1)

        total = await self.session.scalar(select(func.count()).select_from(PlatformSetting))
        stmt = (
            select(PlatformSetting)
            .order_by(PlatformSetting.updated_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        items = result.scalars().all()
        return items, int(total or 0)

    async def get(self, setting_id) -> PlatformSetting | None:
        return await self.session.get(PlatformSetting, setting_id)

    async def create(self, payload, updated_by=None) -> PlatformSetting:
        existing = await self.session.scalar(
            select(PlatformSetting).where(PlatformSetting.key == payload.key)
        )
        if existing:
            raise ValueError("Setting key already exists")

        setting = PlatformSetting(
            key=payload.key,
            value=payload.value,
            description=payload.description,
            updated_by=updated_by,
        )
        self.session.add(setting)
        await self.session.commit()
        await self.session.refresh(setting)
        return setting

    async def update(self, setting: PlatformSetting, payload, updated_by=None) -> PlatformSetting:
        if payload.value is not None:
            setting.value = payload.value
        if payload.description is not None:
            setting.description = payload.description
        if updated_by is not None:
            setting.updated_by = updated_by

        self.session.add(setting)
        await self.session.commit()
        await self.session.refresh(setting)
        return setting

    async def delete(self, setting: PlatformSetting) -> None:
        await self.session.delete(setting)
        await self.session.commit()
