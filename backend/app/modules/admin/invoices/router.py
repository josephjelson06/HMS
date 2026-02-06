from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.database import get_session
from app.modules.auth.dependencies import require_permission
from app.modules.admin.invoices.schemas import (
    InvoiceCreate,
    InvoiceListResponse,
    InvoiceOut,
    InvoiceUpdate,
    Pagination,
)
from app.modules.admin.invoices.service import InvoiceService


router = APIRouter()


def build_out(invoice, tenant_name=None, plan_name=None, plan_code=None) -> InvoiceOut:
    return InvoiceOut.model_validate(invoice).model_copy(
        update={
            "tenant_name": tenant_name,
            "plan_name": plan_name,
            "plan_code": plan_code,
        }
    )


@router.get(
    "/",
    response_model=InvoiceListResponse,
    dependencies=[Depends(require_permission("admin:invoices:read"))],
)
async def list_invoices(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> InvoiceListResponse:
    service = InvoiceService(session)
    items, total = await service.list_invoices(page, limit)
    return InvoiceListResponse(
        items=[
            build_out(invoice, tenant_name, plan_name, plan_code)
            for invoice, tenant_name, plan_name, plan_code in items
        ],
        pagination=Pagination(page=page, limit=limit, total=total),
    )


@router.get(
    "/{invoice_id}",
    response_model=InvoiceOut,
    dependencies=[Depends(require_permission("admin:invoices:read"))],
)
async def get_invoice(
    invoice_id: str, session: AsyncSession = Depends(get_session)
) -> InvoiceOut:
    service = InvoiceService(session)
    try:
        invoice_uuid = UUID(invoice_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid invoice id"
        ) from exc

    invoice = await service.get(invoice_uuid)
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found"
        )

    tenant_name, plan_name, plan_code = await service.get_names(invoice)
    return build_out(invoice, tenant_name, plan_name, plan_code)


@router.post(
    "/",
    response_model=InvoiceOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("admin:invoices:create"))],
)
async def create_invoice(
    payload: InvoiceCreate,
    session: AsyncSession = Depends(get_session),
) -> InvoiceOut:
    service = InvoiceService(session)
    try:
        invoice = await service.create(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    tenant_name, plan_name, plan_code = await service.get_names(invoice)
    return build_out(invoice, tenant_name, plan_name, plan_code)


@router.put(
    "/{invoice_id}",
    response_model=InvoiceOut,
    dependencies=[Depends(require_permission("admin:invoices:update"))],
)
async def update_invoice(
    invoice_id: str,
    payload: InvoiceUpdate,
    session: AsyncSession = Depends(get_session),
) -> InvoiceOut:
    service = InvoiceService(session)
    try:
        invoice_uuid = UUID(invoice_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid invoice id"
        ) from exc

    invoice = await service.get(invoice_uuid)
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found"
        )

    try:
        updated = await service.update(invoice, payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    tenant_name, plan_name, plan_code = await service.get_names(updated)
    return build_out(updated, tenant_name, plan_name, plan_code)


@router.delete(
    "/{invoice_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("admin:invoices:delete"))],
)
async def delete_invoice(
    invoice_id: str, session: AsyncSession = Depends(get_session)
) -> None:
    service = InvoiceService(session)
    try:
        invoice_uuid = UUID(invoice_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid invoice id"
        ) from exc

    invoice = await service.get(invoice_uuid)
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found"
        )

    await service.delete(invoice)
    return None
