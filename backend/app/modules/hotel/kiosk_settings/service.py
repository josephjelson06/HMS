import secrets
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.security import hash_token
from app.models.kiosk import Kiosk


class KioskSettingsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list(self, tenant_id: UUID, page: int, limit: int) -> tuple[list[Kiosk], int]:
        page = max(page, 1)
        limit = max(min(limit, 100), 1)

        total = await self.session.scalar(
            select(func.count()).select_from(Kiosk).where(Kiosk.tenant_id == tenant_id)
        )
        stmt = (
            select(Kiosk)
            .where(Kiosk.tenant_id == tenant_id)
            .order_by(Kiosk.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all(), int(total or 0)

    async def get(self, tenant_id: UUID, kiosk_id: UUID) -> Kiosk | None:
        stmt = select(Kiosk).where(Kiosk.id == kiosk_id, Kiosk.tenant_id == tenant_id)
        return await self.session.scalar(stmt)

    async def create(self, tenant_id: UUID, payload) -> tuple[Kiosk, str]:
        if payload.device_id:
            existing = await self.session.scalar(
                select(Kiosk).where(Kiosk.device_id == payload.device_id)
            )
            if existing:
                raise ValueError("Device ID already exists")

        token = secrets.token_urlsafe(32)
        token_hash = hash_token(token)
        token_last4 = token[-4:] if len(token) >= 4 else token

        kiosk = Kiosk(
            tenant_id=tenant_id,
            name=payload.name,
            location=payload.location,
            status=payload.status,
            device_id=payload.device_id,
            token_hash=token_hash,
            token_last4=token_last4,
        )
        self.session.add(kiosk)
        await self.session.commit()
        await self.session.refresh(kiosk)
        return kiosk, token

    async def update(self, kiosk: Kiosk, payload) -> tuple[Kiosk, str | None]:
        if payload.name is not None:
            kiosk.name = payload.name
        if payload.location is not None:
            kiosk.location = payload.location
        if payload.status is not None:
            kiosk.status = payload.status
        if payload.device_id is not None:
            if payload.device_id:
                existing = await self.session.scalar(
                    select(Kiosk).where(Kiosk.device_id == payload.device_id, Kiosk.id != kiosk.id)
                )
                if existing:
                    raise ValueError("Device ID already exists")
            kiosk.device_id = payload.device_id

        issued_token = None
        if payload.rotate_token:
            token = secrets.token_urlsafe(32)
            kiosk.token_hash = hash_token(token)
            kiosk.token_last4 = token[-4:] if len(token) >= 4 else token
            issued_token = token

        self.session.add(kiosk)
        await self.session.commit()
        await self.session.refresh(kiosk)
        return kiosk, issued_token

    async def delete(self, kiosk: Kiosk) -> None:
        await self.session.delete(kiosk)
        await self.session.commit()
