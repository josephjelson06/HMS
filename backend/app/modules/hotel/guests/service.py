from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.models.guest import Guest


class GuestService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list(
        self,
        tenant_id: UUID,
        page: int,
        limit: int,
        search: str | None = None,
    ) -> tuple[list[Guest], int]:
        page = max(page, 1)
        limit = max(min(limit, 100), 1)

        total_stmt = select(func.count()).select_from(Guest).where(Guest.tenant_id == tenant_id)
        stmt = select(Guest).where(Guest.tenant_id == tenant_id)

        if search:
            like = f"%{search.strip()}%"
            total_stmt = total_stmt.where(
                or_(
                    Guest.first_name.ilike(like),
                    Guest.last_name.ilike(like),
                    Guest.email.ilike(like),
                )
            )
            stmt = stmt.where(
                or_(
                    Guest.first_name.ilike(like),
                    Guest.last_name.ilike(like),
                    Guest.email.ilike(like),
                )
            )

        total = await self.session.scalar(total_stmt)
        stmt = stmt.order_by(Guest.created_at.desc()).offset((page - 1) * limit).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all(), int(total or 0)

    async def get(self, tenant_id: UUID, guest_id: UUID) -> Guest | None:
        stmt = select(Guest).where(Guest.id == guest_id, Guest.tenant_id == tenant_id)
        return await self.session.scalar(stmt)

    async def create(self, tenant_id: UUID, payload) -> Guest:
        if payload.email:
            existing = await self.session.scalar(
                select(Guest).where(Guest.tenant_id == tenant_id, Guest.email == payload.email)
            )
            if existing:
                raise ValueError("Guest email already exists")

        guest = Guest(
            tenant_id=tenant_id,
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=payload.email,
            phone=payload.phone,
            status=payload.status,
            check_in_at=payload.check_in_at,
            check_out_at=payload.check_out_at,
            notes=payload.notes,
        )
        self.session.add(guest)
        await self.session.commit()
        await self.session.refresh(guest)
        return guest

    async def update(self, guest: Guest, payload) -> Guest:
        if payload.first_name is not None:
            guest.first_name = payload.first_name
        if payload.last_name is not None:
            guest.last_name = payload.last_name
        if payload.email is not None:
            if payload.email:
                existing = await self.session.scalar(
                    select(Guest).where(
                        Guest.tenant_id == guest.tenant_id,
                        Guest.email == payload.email,
                        Guest.id != guest.id,
                    )
                )
                if existing:
                    raise ValueError("Guest email already exists")
            guest.email = payload.email
        if payload.phone is not None:
            guest.phone = payload.phone
        if payload.status is not None:
            guest.status = payload.status
        if payload.check_in_at is not None:
            guest.check_in_at = payload.check_in_at
        if payload.check_out_at is not None:
            guest.check_out_at = payload.check_out_at
        if payload.notes is not None:
            guest.notes = payload.notes

        self.session.add(guest)
        await self.session.commit()
        await self.session.refresh(guest)
        return guest

    async def delete(self, guest: Guest) -> None:
        await self.session.delete(guest)
        await self.session.commit()
