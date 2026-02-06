from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.database import get_session
from app.modules.auth.dependencies import require_permission
from app.modules.admin.plans.schemas import (
    PlanCreate,
    PlanListResponse,
    PlanOut,
    PlanUpdate,
    Pagination,
)
from app.modules.admin.plans.service import PlanService


router = APIRouter()


@router.get(
    "/",
    response_model=PlanListResponse,
    dependencies=[Depends(require_permission("admin:plans:read"))],
)
async def list_plans(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> PlanListResponse:
    service = PlanService(session)
    items, total = await service.list_plans(page, limit)
    return PlanListResponse(
        items=[PlanOut.model_validate(item) for item in items],
        pagination=Pagination(page=page, limit=limit, total=total),
    )


@router.get(
    "/{plan_id}",
    response_model=PlanOut,
    dependencies=[Depends(require_permission("admin:plans:read"))],
)
async def get_plan(
    plan_id: str, session: AsyncSession = Depends(get_session)
) -> PlanOut:
    service = PlanService(session)
    try:
        plan_uuid = UUID(plan_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid plan id"
        ) from exc

    plan = await service.get(plan_uuid)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found"
        )

    return PlanOut.model_validate(plan)


@router.post(
    "/",
    response_model=PlanOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("admin:plans:create"))],
)
async def create_plan(
    payload: PlanCreate, session: AsyncSession = Depends(get_session)
) -> PlanOut:
    service = PlanService(session)
    try:
        plan = await service.create(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    return PlanOut.model_validate(plan)


@router.put(
    "/{plan_id}",
    response_model=PlanOut,
    dependencies=[Depends(require_permission("admin:plans:update"))],
)
async def update_plan(
    plan_id: str,
    payload: PlanUpdate,
    session: AsyncSession = Depends(get_session),
) -> PlanOut:
    service = PlanService(session)
    try:
        plan_uuid = UUID(plan_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid plan id"
        ) from exc

    plan = await service.get(plan_uuid)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found"
        )

    try:
        updated = await service.update(plan, payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    return PlanOut.model_validate(updated)


@router.delete(
    "/{plan_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("admin:plans:delete"))],
)
async def delete_plan(
    plan_id: str, session: AsyncSession = Depends(get_session)
) -> None:
    service = PlanService(session)
    try:
        plan_uuid = UUID(plan_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid plan id"
        ) from exc

    plan = await service.get(plan_uuid)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found"
        )

    await service.delete(plan)
    return None
