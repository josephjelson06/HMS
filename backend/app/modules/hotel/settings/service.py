from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.models.hotel_setting import HotelSetting


class SettingsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list(self, tenant_id: UUID, page: int, limit: int) -> tuple[list[HotelSetting], int]:
        page = max(page, 1)
        limit = max(min(limit, 100), 1)

        total_stmt = select(func.count()).select_from(HotelSetting).where(
            HotelSetting.tenant_id == tenant_id
        )
        total = await self.session.scalar(total_stmt)
        stmt = (
            select(HotelSetting)
            .where(HotelSetting.tenant_id == tenant_id)
            .order_by(HotelSetting.updated_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        items = result.scalars().all()
        return items, int(total or 0)

    async def get(self, tenant_id: UUID, setting_id: UUID) -> HotelSetting | None:
        stmt = select(HotelSetting).where(
            HotelSetting.id == setting_id, HotelSetting.tenant_id == tenant_id
        )
        return await self.session.scalar(stmt)

    async def create(self, tenant_id: UUID, payload, updated_by=None) -> HotelSetting:
        existing = await self.session.scalar(
            select(HotelSetting).where(
                HotelSetting.tenant_id == tenant_id, HotelSetting.key == payload.key
            )
        )
        if existing:
            raise ValueError("Setting key already exists")

        setting = HotelSetting(
            tenant_id=tenant_id,
            key=payload.key,
            value=payload.value,
            description=payload.description,
            updated_by=updated_by,
        )
        self.session.add(setting)
        await self.session.commit()
        await self.session.refresh(setting)
        return setting

    async def update(
        self, setting: HotelSetting, payload, updated_by=None
    ) -> HotelSetting:
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

    async def delete(self, setting: HotelSetting) -> None:
        await self.session.delete(setting)
        await self.session.commit()
