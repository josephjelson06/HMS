import re
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import Tenant


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value)
    return value.strip("-")


class HotelService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_hotels(self, page: int, limit: int) -> tuple[list[Tenant], int]:
        page = max(page, 1)
        limit = max(min(limit, 100), 1)

        total = await self.session.scalar(select(func.count()).select_from(Tenant))
        stmt = (
            select(Tenant)
            .order_by(Tenant.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        items = result.scalars().all()
        return items, int(total or 0)

    async def get(self, tenant_id) -> Tenant | None:
        return await self.session.get(Tenant, tenant_id)

    async def create(self, payload) -> Tenant:
        raw_slug = payload.slug if payload.slug else payload.name
        slug = slugify(raw_slug)
        if not slug:
            raise ValueError("Invalid slug")

        existing = await self.session.scalar(select(Tenant).where(Tenant.slug == slug))
        if existing:
            raise ValueError("Slug already exists")

        tenant = Tenant(
            name=payload.name,
            slug=slug,
            status=payload.status,
            subscription_tier=payload.subscription_tier,
        )
        self.session.add(tenant)
        await self.session.commit()
        await self.session.refresh(tenant)
        return tenant

    async def update(self, tenant: Tenant, payload) -> Tenant:
        if payload.name is not None:
            tenant.name = payload.name
        if payload.status is not None:
            tenant.status = payload.status
        if payload.subscription_tier is not None:
            tenant.subscription_tier = payload.subscription_tier
        if payload.slug is not None:
            slug = slugify(payload.slug)
            if not slug:
                raise ValueError("Invalid slug")
            existing = await self.session.scalar(
                select(Tenant).where(Tenant.slug == slug, Tenant.id != tenant.id)
            )
            if existing:
                raise ValueError("Slug already exists")
            tenant.slug = slug

        self.session.add(tenant)
        await self.session.commit()
        await self.session.refresh(tenant)
        return tenant

    async def delete(self, tenant: Tenant) -> None:
        await self.session.delete(tenant)
        await self.session.commit()
