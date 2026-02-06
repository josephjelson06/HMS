from datetime import datetime, timezone
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.models.incident import Incident
from app.models.user import User


class IncidentService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list(
        self,
        tenant_id: UUID,
        page: int,
        limit: int,
        search: str | None = None,
        status: str | None = None,
        severity: str | None = None,
    ) -> tuple[list[Incident], int]:
        page = max(page, 1)
        limit = max(min(limit, 100), 1)

        total_stmt = select(func.count()).select_from(Incident).where(Incident.tenant_id == tenant_id)
        stmt = select(Incident).where(Incident.tenant_id == tenant_id)

        if search:
            like = f"%{search.strip()}%"
            total_stmt = total_stmt.where(
                or_(Incident.title.ilike(like), Incident.description.ilike(like))
            )
            stmt = stmt.where(or_(Incident.title.ilike(like), Incident.description.ilike(like)))

        if status:
            total_stmt = total_stmt.where(Incident.status == status)
            stmt = stmt.where(Incident.status == status)

        if severity:
            total_stmt = total_stmt.where(Incident.severity == severity)
            stmt = stmt.where(Incident.severity == severity)

        total = await self.session.scalar(total_stmt)
        stmt = stmt.order_by(Incident.created_at.desc()).offset((page - 1) * limit).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all(), int(total or 0)

    async def get(self, tenant_id: UUID, incident_id: UUID) -> Incident | None:
        stmt = select(Incident).where(Incident.id == incident_id, Incident.tenant_id == tenant_id)
        return await self.session.scalar(stmt)

    async def create(self, tenant_id: UUID, payload) -> Incident:
        if payload.reported_by:
            user = await self.session.get(User, payload.reported_by)
            if not user or user.tenant_id != tenant_id:
                raise ValueError("Reported user not found")

        incident = Incident(
            tenant_id=tenant_id,
            title=payload.title,
            description=payload.description,
            status=payload.status,
            severity=payload.severity,
            category=payload.category,
            occurred_at=payload.occurred_at,
            resolved_at=payload.resolved_at,
            reported_by=payload.reported_by,
        )
        self.session.add(incident)
        await self.session.commit()
        await self.session.refresh(incident)
        return incident

    async def update(self, incident: Incident, payload) -> Incident:
        if payload.reported_by is not None:
            if payload.reported_by:
                user = await self.session.get(User, payload.reported_by)
                if not user or user.tenant_id != incident.tenant_id:
                    raise ValueError("Reported user not found")
            incident.reported_by = payload.reported_by

        if payload.title is not None:
            incident.title = payload.title
        if payload.description is not None:
            incident.description = payload.description
        if payload.status is not None:
            incident.status = payload.status
            if payload.status.lower() in {"closed", "resolved"} and incident.resolved_at is None:
                incident.resolved_at = datetime.now(timezone.utc)
        if payload.severity is not None:
            incident.severity = payload.severity
        if payload.category is not None:
            incident.category = payload.category
        if payload.occurred_at is not None:
            incident.occurred_at = payload.occurred_at
        if payload.resolved_at is not None:
            incident.resolved_at = payload.resolved_at

        self.session.add(incident)
        await self.session.commit()
        await self.session.refresh(incident)
        return incident

    async def delete(self, incident: Incident) -> None:
        await self.session.delete(incident)
        await self.session.commit()
