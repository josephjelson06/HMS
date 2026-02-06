from datetime import datetime, timedelta, timezone
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.models.plan import Plan
from app.models.subscription import Subscription
from app.models.tenant import Tenant


class SubscriptionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_subscriptions(
        self, page: int, limit: int
    ) -> tuple[list[tuple[Subscription, str | None, str | None, str | None]], int]:
        page = max(page, 1)
        limit = max(min(limit, 100), 1)

        total = await self.session.scalar(
            select(func.count()).select_from(Subscription)
        )
        stmt = (
            select(Subscription, Tenant.name, Plan.name, Plan.code)
            .join(Tenant, Tenant.id == Subscription.tenant_id)
            .join(Plan, Plan.id == Subscription.plan_id)
            .order_by(Subscription.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        items = result.all()
        return items, int(total or 0)

    async def get(self, subscription_id: UUID) -> Subscription | None:
        return await self.session.get(Subscription, subscription_id)

    async def get_names(
        self, subscription: Subscription
    ) -> tuple[str | None, str | None, str | None]:
        tenant = await self.session.get(Tenant, subscription.tenant_id)
        plan = await self.session.get(Plan, subscription.plan_id)
        return (
            tenant.name if tenant else None,
            plan.name if plan else None,
            plan.code if plan else None,
        )

    async def create(self, payload) -> Subscription:
        tenant = await self.session.get(Tenant, payload.tenant_id)
        if not tenant:
            raise ValueError("Tenant not found")

        plan = await self.session.get(Plan, payload.plan_id)
        if not plan:
            raise ValueError("Plan not found")

        now = datetime.now(timezone.utc)
        start_date = payload.start_date or now
        current_period_start = start_date
        current_period_end = payload.current_period_end or self._derive_end_date(
            start_date, plan.billing_interval
        )

        subscription = Subscription(
            tenant_id=tenant.id,
            plan_id=plan.id,
            status=payload.status,
            start_date=start_date,
            current_period_start=current_period_start,
            current_period_end=current_period_end,
            cancel_at=payload.cancel_at,
        )
        self.session.add(subscription)
        await self.session.commit()
        await self.session.refresh(subscription)
        return subscription

    async def update(self, subscription: Subscription, payload) -> Subscription:
        if payload.tenant_id is not None:
            tenant = await self.session.get(Tenant, payload.tenant_id)
            if not tenant:
                raise ValueError("Tenant not found")
            subscription.tenant_id = tenant.id

        if payload.plan_id is not None:
            plan = await self.session.get(Plan, payload.plan_id)
            if not plan:
                raise ValueError("Plan not found")
            subscription.plan_id = plan.id

        if payload.status is not None:
            subscription.status = payload.status
            if (
                payload.status.lower() == "canceled"
                and subscription.canceled_at is None
            ):
                subscription.canceled_at = datetime.now(timezone.utc)

        if payload.current_period_end is not None:
            subscription.current_period_end = payload.current_period_end
        if payload.cancel_at is not None:
            subscription.cancel_at = payload.cancel_at
        if payload.canceled_at is not None:
            subscription.canceled_at = payload.canceled_at

        self.session.add(subscription)
        await self.session.commit()
        await self.session.refresh(subscription)
        return subscription

    async def delete(self, subscription: Subscription) -> None:
        await self.session.delete(subscription)
        await self.session.commit()

    def _derive_end_date(
        self, start_date: datetime, interval: str | None
    ) -> datetime | None:
        if not interval:
            return None
        interval_key = interval.lower()
        if interval_key in {"monthly", "month"}:
            return start_date + timedelta(days=30)
        if interval_key in {"yearly", "annual", "year"}:
            return start_date + timedelta(days=365)
        if interval_key in {"weekly", "week"}:
            return start_date + timedelta(days=7)
        return None
