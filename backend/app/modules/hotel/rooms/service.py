from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.models.room import Room


class RoomService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list(
        self,
        tenant_id: UUID,
        page: int,
        limit: int,
        search: str | None = None,
    ) -> tuple[list[Room], int]:
        page = max(page, 1)
        limit = max(min(limit, 100), 1)

        total_stmt = select(func.count()).select_from(Room).where(Room.tenant_id == tenant_id)
        stmt = select(Room).where(Room.tenant_id == tenant_id)

        if search:
            like = f"%{search.strip()}%"
            total_stmt = total_stmt.where(
                or_(
                    Room.number.ilike(like),
                    Room.room_type.ilike(like),
                )
            )
            stmt = stmt.where(
                or_(
                    Room.number.ilike(like),
                    Room.room_type.ilike(like),
                )
            )

        total = await self.session.scalar(total_stmt)
        stmt = stmt.order_by(Room.created_at.desc()).offset((page - 1) * limit).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all(), int(total or 0)

    async def get(self, tenant_id: UUID, room_id: UUID) -> Room | None:
        stmt = select(Room).where(Room.id == room_id, Room.tenant_id == tenant_id)
        return await self.session.scalar(stmt)

    async def create(self, tenant_id: UUID, payload) -> Room:
        existing = await self.session.scalar(
            select(Room).where(Room.tenant_id == tenant_id, Room.number == payload.number)
        )
        if existing:
            raise ValueError("Room number already exists")

        room = Room(
            tenant_id=tenant_id,
            number=payload.number,
            room_type=payload.room_type,
            floor=payload.floor,
            status=payload.status,
            capacity=payload.capacity,
            rate_cents=payload.rate_cents,
            currency=(payload.currency or "USD").upper(),
            description=payload.description,
        )
        self.session.add(room)
        await self.session.commit()
        await self.session.refresh(room)
        return room

    async def update(self, room: Room, payload) -> Room:
        if payload.number is not None:
            existing = await self.session.scalar(
                select(Room).where(
                    Room.tenant_id == room.tenant_id,
                    Room.number == payload.number,
                    Room.id != room.id,
                )
            )
            if existing:
                raise ValueError("Room number already exists")
            room.number = payload.number
        if payload.room_type is not None:
            room.room_type = payload.room_type
        if payload.floor is not None:
            room.floor = payload.floor
        if payload.status is not None:
            room.status = payload.status
        if payload.capacity is not None:
            room.capacity = payload.capacity
        if payload.rate_cents is not None:
            room.rate_cents = payload.rate_cents
        if payload.currency is not None:
            room.currency = payload.currency.upper()
        if payload.description is not None:
            room.description = payload.description

        self.session.add(room)
        await self.session.commit()
        await self.session.refresh(room)
        return room

    async def delete(self, room: Room) -> None:
        await self.session.delete(room)
        await self.session.commit()
