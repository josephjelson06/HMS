from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.database import get_session
from app.modules.auth.dependencies import CurrentUser, get_current_user, require_permission
from app.modules.hotel.billing.schemas import BillingSummary, InvoiceOut, PlanOut, SubscriptionOut
from app.modules.hotel.billing.service import BillingService


router = APIRouter()


@router.get(
    "/summary",
    response_model=BillingSummary,
    dependencies=[Depends(require_permission("hotel:billing:read"))],
)
async def get_billing_summary(
    limit: int = Query(10, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> BillingSummary:
    if current_user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant context missing")
    service = BillingService(session)
    subscription = await service.get_subscription(current_user.tenant_id)
    plan = await service.get_plan(subscription.plan_id) if subscription else None
    invoices = await service.list_invoices(current_user.tenant_id, limit)
    return BillingSummary(
        subscription=SubscriptionOut.model_validate(subscription) if subscription else None,
        plan=PlanOut.model_validate(plan) if plan else None,
        invoices=[InvoiceOut.model_validate(invoice) for invoice in invoices],
    )


@router.get(
    "/invoices",
    response_model=list[InvoiceOut],
    dependencies=[Depends(require_permission("hotel:billing:read"))],
)
async def list_invoices(
    limit: int = Query(20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[InvoiceOut]:
    if current_user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant context missing")
    service = BillingService(session)
    invoices = await service.list_invoices(current_user.tenant_id, limit)
    return [InvoiceOut.model_validate(invoice) for invoice in invoices]


@router.get(
    "/invoices/{invoice_id}",
    response_model=InvoiceOut,
    dependencies=[Depends(require_permission("hotel:billing:read"))],
)
async def get_invoice(
    invoice_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> InvoiceOut:
    if current_user.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant context missing")
    service = BillingService(session)
    try:
        invoice_uuid = UUID(invoice_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid invoice id") from exc

    invoice = await service.get_invoice(current_user.tenant_id, invoice_uuid)
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    return InvoiceOut.model_validate(invoice)
