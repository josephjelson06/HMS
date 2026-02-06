import re
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.plan import Plan


def normalize_code(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value)
    return value.strip("-")


class PlanService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_plans(self, page: int, limit: int) -> tuple[list[Plan], int]:
        page = max(page, 1)
        limit = max(min(limit, 100), 1)

        total = await self.session.scalar(select(func.count()).select_from(Plan))
        stmt = (
            select(Plan)
            .order_by(Plan.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        items = result.scalars().all()
        return items, int(total or 0)

    async def get(self, plan_id) -> Plan | None:
        return await self.session.get(Plan, plan_id)

    async def create(self, payload) -> Plan:
        code_raw = payload.code or payload.name
        code = normalize_code(code_raw)
        if not code:
            raise ValueError("Invalid code")

        existing = await self.session.scalar(select(Plan).where(Plan.code == code))
        if existing:
            raise ValueError("Plan code already exists")

        plan = Plan(
            name=payload.name,
            code=code,
            description=payload.description,
            price_cents=payload.price_cents,
            currency=payload.currency.upper(),
            billing_interval=payload.billing_interval,
            is_active=payload.is_active,
        )
        self.session.add(plan)
        await self.session.commit()
        await self.session.refresh(plan)
        return plan

    async def update(self, plan: Plan, payload) -> Plan:
        if payload.name is not None:
            plan.name = payload.name
        if payload.description is not None:
            plan.description = payload.description
        if payload.price_cents is not None:
            plan.price_cents = payload.price_cents
        if payload.currency is not None:
            plan.currency = payload.currency.upper()
        if payload.billing_interval is not None:
            plan.billing_interval = payload.billing_interval
        if payload.is_active is not None:
            plan.is_active = payload.is_active
        if payload.code is not None:
            code = normalize_code(payload.code)
            if not code:
                raise ValueError("Invalid code")
            existing = await self.session.scalar(
                select(Plan).where(Plan.code == code, Plan.id != plan.id)
            )
            if existing:
                raise ValueError("Plan code already exists")
            plan.code = code

        self.session.add(plan)
        await self.session.commit()
        await self.session.refresh(plan)
        return plan

    async def delete(self, plan: Plan) -> None:
        await self.session.delete(plan)
        await self.session.commit()
