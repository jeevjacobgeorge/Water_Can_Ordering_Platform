"""Staff delivery order endpoints."""

from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import require_staff
from app.db.session import get_db
from app.models.customer import Customer
from app.models.order import Order, OrderStatus
from app.models.order_assignment import OrderAssignment
from app.models.user import User
from app.schemas.common import StaffDashboardResponse
from app.schemas.order import OrderDetailResponse

from app.api.v1.admin import _order_detail, _order_options

router = APIRouter(prefix="/staff", tags=["staff"])


@router.get("/dashboard", response_model=StaffDashboardResponse)
async def dashboard(
    db: Annotated[AsyncSession, Depends(get_db)],
    staff: Annotated[User, Depends(require_staff)],
):
    """Return the signed-in staff member's delivery workload."""
    assigned_result = await db.execute(
        select(func.count(Order.id))
        .join(OrderAssignment, OrderAssignment.order_id == Order.id)
        .where(
            OrderAssignment.staff_id == staff.id,
            Order.business_id == staff.business_id,
            OrderAssignment.unassigned_at.is_(None),
            Order.order_status.not_in([OrderStatus.DELIVERED, OrderStatus.CANCELLED]),
        )
    )
    available_result = await db.execute(
        select(func.count(Order.id)).where(
            Order.business_id == staff.business_id,
            Order.order_status == OrderStatus.CONFIRMED,
            ~exists(
                select(OrderAssignment.id).where(
                    OrderAssignment.order_id == Order.id,
                    OrderAssignment.unassigned_at.is_(None),
                )
            ),
        )
    )
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    delivered_result = await db.execute(
        select(func.count(Order.id))
        .join(OrderAssignment, OrderAssignment.order_id == Order.id)
        .where(
            OrderAssignment.staff_id == staff.id,
            Order.business_id == staff.business_id,
            Order.order_status == OrderStatus.DELIVERED,
            Order.updated_at >= today,
        )
    )
    return {
        "assigned_orders": assigned_result.scalar_one(),
        "available_orders": available_result.scalar_one(),
        "delivered_today": delivered_result.scalar_one(),
    }


@router.get("/orders", response_model=list[OrderDetailResponse])
async def list_assigned_orders(
    db: Annotated[AsyncSession, Depends(get_db)],
    staff: Annotated[User, Depends(require_staff)],
):
    result = await db.execute(
        select(Order)
        .join(OrderAssignment, OrderAssignment.order_id == Order.id)
        .where(
            OrderAssignment.staff_id == staff.id,
            Order.business_id == staff.business_id,
            OrderAssignment.unassigned_at.is_(None),
            Order.order_status.not_in([OrderStatus.DELIVERED, OrderStatus.CANCELLED]),
        )
        .options(*_order_options())
        .order_by(Order.created_at.desc())
    )
    return [_order_detail(order) for order in result.scalars().unique().all()]


@router.get("/orders/available", response_model=list[OrderDetailResponse])
async def list_available_orders(
    db: Annotated[AsyncSession, Depends(get_db)],
    staff: Annotated[User, Depends(require_staff)],
):
    result = await db.execute(
        select(Order)
        .join(Customer)
        .where(
            Order.business_id == staff.business_id,
            Order.order_status == OrderStatus.CONFIRMED,
            ~exists(
                select(OrderAssignment.id).where(
                    OrderAssignment.order_id == Order.id,
                    OrderAssignment.unassigned_at.is_(None),
                )
            ),
        )
        .options(*_order_options())
        .order_by(Order.created_at.asc())
    )
    return [_order_detail(order) for order in result.scalars().unique().all()]


@router.post("/orders/{order_id}/claim", response_model=OrderDetailResponse)
async def claim_order(
    order_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    staff: Annotated[User, Depends(require_staff)],
):
    result = await db.execute(
        select(Order)
        .where(Order.id == order_id, Order.business_id == staff.business_id)
        .options(*_order_options())
        .with_for_update()
    )
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if order.order_status != OrderStatus.CONFIRMED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This order is no longer available")
    if any(assignment.unassigned_at is None for assignment in order.assignments):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This order is already assigned")

    order.order_status = OrderStatus.ASSIGNED
    db.add(OrderAssignment(
        order_id=order.id,
        staff_id=staff.id,
        assigned_by=staff.id,
        assigned_at=datetime.now(timezone.utc),
    ))
    await db.flush()
    await db.refresh(order, attribute_names=["assignments"])
    return _order_detail(order)
