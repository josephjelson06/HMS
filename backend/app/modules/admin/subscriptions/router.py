from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.database import get_session
from app.modules.auth.dependencies import require_permission
from app.modules.admin.subscriptions.schemas import (
    SubscriptionCreate,
    SubscriptionListResponse,
    SubscriptionOut,
    SubscriptionUpdate,
    Pagination,
)
from app.modules.admin.subscriptions.service import SubscriptionService


router = APIRouter()


def build_out(
    subscription, tenant_name=None, plan_name=None, plan_code=None
) -> SubscriptionOut:
    return SubscriptionOut.model_validate(subscription).model_copy(
        update={
            "tenant_name": tenant_name,
            "plan_name": plan_name,
            "plan_code": plan_code,
        }
    )


@router.get(
    "/",
    response_model=SubscriptionListResponse,
    dependencies=[Depends(require_permission("admin:subscriptions:read"))],
)
async def list_subscriptions(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> SubscriptionListResponse:
    service = SubscriptionService(session)
    items, total = await service.list_subscriptions(page, limit)
    return SubscriptionListResponse(
        items=[
            build_out(subscription, tenant_name, plan_name, plan_code)
            for subscription, tenant_name, plan_name, plan_code in items
        ],
        pagination=Pagination(page=page, limit=limit, total=total),
    )


@router.get(
    "/{subscription_id}",
    response_model=SubscriptionOut,
    dependencies=[Depends(require_permission("admin:subscriptions:read"))],
)
async def get_subscription(
    subscription_id: str, session: AsyncSession = Depends(get_session)
) -> SubscriptionOut:
    service = SubscriptionService(session)
    try:
        sub_uuid = UUID(subscription_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid subscription id"
        ) from exc

    subscription = await service.get(sub_uuid)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found"
        )

    tenant_name, plan_name, plan_code = await service.get_names(subscription)
    return build_out(subscription, tenant_name, plan_name, plan_code)


@router.post(
    "/",
    response_model=SubscriptionOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("admin:subscriptions:create"))],
)
async def create_subscription(
    payload: SubscriptionCreate,
    session: AsyncSession = Depends(get_session),
) -> SubscriptionOut:
    service = SubscriptionService(session)
    try:
        subscription = await service.create(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    tenant_name, plan_name, plan_code = await service.get_names(subscription)
    return build_out(subscription, tenant_name, plan_name, plan_code)


@router.put(
    "/{subscription_id}",
    response_model=SubscriptionOut,
    dependencies=[Depends(require_permission("admin:subscriptions:update"))],
)
async def update_subscription(
    subscription_id: str,
    payload: SubscriptionUpdate,
    session: AsyncSession = Depends(get_session),
) -> SubscriptionOut:
    service = SubscriptionService(session)
    try:
        sub_uuid = UUID(subscription_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid subscription id"
        ) from exc

    subscription = await service.get(sub_uuid)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found"
        )

    try:
        updated = await service.update(subscription, payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    tenant_name, plan_name, plan_code = await service.get_names(updated)
    return build_out(updated, tenant_name, plan_name, plan_code)


@router.delete(
    "/{subscription_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("admin:subscriptions:delete"))],
)
async def delete_subscription(
    subscription_id: str, session: AsyncSession = Depends(get_session)
) -> None:
    service = SubscriptionService(session)
    try:
        sub_uuid = UUID(subscription_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid subscription id"
        ) from exc

    subscription = await service.get(sub_uuid)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found"
        )

    await service.delete(subscription)
    return None
