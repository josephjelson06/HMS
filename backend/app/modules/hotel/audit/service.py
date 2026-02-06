from datetime import datetime
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.models.audit import AuditLog


class HotelAuditLogService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_logs(
        self,
        tenant_id: UUID,
        page: int,
        limit: int,
        action: str | None = None,
        user_id: UUID | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> tuple[list[AuditLog], int]:
        page = max(page, 1)
        limit = max(min(limit, 100), 1)

        stmt = select(AuditLog).where(AuditLog.tenant_id == tenant_id)
        count_stmt = select(func.count()).select_from(AuditLog).where(AuditLog.tenant_id == tenant_id)

        if action:
            stmt = stmt.where(AuditLog.action.ilike(f"%{action}%"))
            count_stmt = count_stmt.where(AuditLog.action.ilike(f"%{action}%"))
        if user_id:
            stmt = stmt.where(AuditLog.user_id == user_id)
            count_stmt = count_stmt.where(AuditLog.user_id == user_id)
        if date_from:
            stmt = stmt.where(AuditLog.created_at >= date_from)
            count_stmt = count_stmt.where(AuditLog.created_at >= date_from)
        if date_to:
            stmt = stmt.where(AuditLog.created_at <= date_to)
            count_stmt = count_stmt.where(AuditLog.created_at <= date_to)

        total = await self.session.scalar(count_stmt)
        stmt = (
            stmt.order_by(AuditLog.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        items = result.scalars().all()
        return items, int(total or 0)

    async def get(self, tenant_id: UUID, audit_id: UUID) -> AuditLog | None:
        stmt = select(AuditLog).where(AuditLog.id == audit_id, AuditLog.tenant_id == tenant_id)
        return await self.session.scalar(stmt)
