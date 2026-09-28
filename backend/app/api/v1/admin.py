"""Owner order management and delivery inventory endpoints."""

from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import require_owner
from app.core.security import hash_password
from app.db.session import get_db
from app.models.address import CustomerAddress
from app.models.can_inventory import CanTransaction, CanTransactionType, CustomerCanBalance
from app.models.customer import Customer
from app.models.order import Order, OrderStatus, PaymentStatus
from app.models.order_assignment import OrderAssignment
from app.models.order_can_summary import OrderCanSummary
from app.models.user import User, UserRole
from app.schemas.common import DashboardResponse
from app.schemas.customer import AddressResponse
from app.schemas.common import StaffCreate, StaffResponse, StaffUpdate
from app.schemas.order import (
    AssignOrderRequest,
    DeliverOrderRequest,
    OrderDetailResponse,
    OrderListFilters,
    PaginatedOrders,
)
from app.services.order_state import InvalidStatusTransition, validate_transition

router = APIRouter(prefix="/admin", tags=["admin"])


def _order_options():
    return (
        selectinload(Order.customer),
        selectinload(Order.address),
        selectinload(Order.assignments).selectinload(OrderAssignment.staff),
        selectinload(Order.can_summary),
    )


def _order_detail(order: Order) -> dict:
    active_assignment = next(
        (assignment for assignment in order.assignments if assignment.unassigned_at is None),
        None,
    )
    summary = order.can_summary
    return {
        "id": order.id,
        "order_number": order.order_number,
        "customer_id": order.customer_id,
        "customer_name": order.customer.name,
        "customer_phone": order.customer.phone,
        "quantity": order.quantity,
        "price_per_unit": order.price_per_unit,
        "subtotal": order.subtotal,
        "delivery_charge": order.delivery_charge,
        "discount": order.discount,
        "total_amount": order.total_amount,
        "payment_status": order.payment_status.value,
        "order_status": order.order_status.value,
        "delivery_slot": order.delivery_slot.value if order.delivery_slot else None,
        "customer_notes": order.customer_notes,
        "address": AddressResponse.model_validate(order.address) if order.address else None,
        "assigned_staff_name": active_assignment.staff.name if active_assignment else None,
        "assigned_staff_id": active_assignment.staff_id if active_assignment else None,
        "cans_delivered": summary.cans_delivered if summary else None,
        "empty_cans_returned": summary.empty_cans_returned if summary else None,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
    }


async def _get_order(db: AsyncSession, order_id: UUID, business_id: UUID) -> Order:
    result = await db.execute(
        select(Order)
        .execution_options(populate_existing=True)
        .where(Order.id == order_id, Order.business_id == business_id)
        .options(*_order_options())
    )
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order


async def _get_order_detail(db: AsyncSession, order_id: UUID, business_id: UUID) -> dict:
    """Reload an order with all response relationships after a write."""
    return _order_detail(await _get_order(db, order_id, business_id))


def _transition(order: Order, target: OrderStatus) -> None:
    try:
        validate_transition(order.order_status, target)
    except InvalidStatusTransition as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    order.order_status = target


@router.get("/dashboard", response_model=DashboardResponse)
async def dashboard(
    db: Annotated[AsyncSession, Depends(get_db)],
    owner: Annotated[User, Depends(require_owner)],
):
    """Return the owner's current-day order and can metrics."""
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    stats_result = await db.execute(
        select(
            func.count(Order.id),
            func.count(Order.id).filter(Order.payment_status == PaymentStatus.PAID),
            func.count(Order.id).filter(Order.order_status == OrderStatus.DELIVERED),
            func.coalesce(func.sum(Order.total_amount).filter(Order.payment_status == PaymentStatus.PAID), 0),
            func.coalesce(func.sum(Order.quantity), 0),
        ).where(Order.business_id == owner.business_id, Order.created_at >= today)
    )
    orders, paid_orders, delivered_orders, revenue, cans_ordered = stats_result.one()

    can_stats_result = await db.execute(
        select(
            func.coalesce(func.sum(OrderCanSummary.cans_delivered), 0),
            func.coalesce(func.sum(OrderCanSummary.empty_cans_returned), 0),
        )
        .join(Order, Order.id == OrderCanSummary.order_id)
        .where(Order.business_id == owner.business_id, Order.created_at >= today)
    )
    cans_delivered, empty_cans_returned = can_stats_result.one()

    pending_result = await db.execute(
        select(func.count(Order.id)).where(
            Order.business_id == owner.business_id,
            Order.order_status.in_([
                OrderStatus.PENDING_PAYMENT,
                OrderStatus.PAID,
                OrderStatus.CONFIRMED,
            ])
        )
    )
    unassigned_result = await db.execute(
        select(func.count(Order.id)).where(
            Order.business_id == owner.business_id,
            Order.order_status == OrderStatus.CONFIRMED,
            ~exists(
                select(OrderAssignment.id).where(
                    OrderAssignment.order_id == Order.id,
                    OrderAssignment.unassigned_at.is_(None),
                )
            ),
        )
    )
    out_for_delivery_result = await db.execute(
        select(func.count(Order.id)).where(
            Order.business_id == owner.business_id,
            Order.order_status == OrderStatus.OUT_FOR_DELIVERY,
        )
    )
    balance_result = await db.execute(
        select(func.coalesce(func.sum(CustomerCanBalance.current_balance), 0)).where(
            CustomerCanBalance.business_id == owner.business_id
        )
    )

    return {
        "today": {
            "orders": orders,
            "paid_orders": paid_orders,
            "delivered_orders": delivered_orders,
            "revenue": revenue,
            "cans_ordered": cans_ordered,
            "cans_delivered": cans_delivered,
            "empty_cans_returned": empty_cans_returned,
        },
        "pending_orders": pending_result.scalar_one(),
        "unassigned_orders": unassigned_result.scalar_one(),
        "out_for_delivery": out_for_delivery_result.scalar_one(),
        "total_cans_with_customers": balance_result.scalar_one(),
    }


@router.get("/staff", response_model=list[StaffResponse])
async def list_staff(
    db: Annotated[AsyncSession, Depends(get_db)],
    owner: Annotated[User, Depends(require_owner)],
):
    result = await db.execute(
        select(User)
        .where(User.role == UserRole.STAFF, User.business_id == owner.business_id)
        .order_by(User.name.asc())
    )
    return result.scalars().all()


@router.post("/staff", response_model=StaffResponse, status_code=status.HTTP_201_CREATED)
async def create_staff(
    body: StaffCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    owner: Annotated[User, Depends(require_owner)],
):
    existing_result = await db.execute(select(User).where(User.email == body.email))
    if existing_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already in use")
    staff = User(
        business_id=owner.business_id,
        name=body.name,
        phone=body.phone,
        email=body.email,
        password_hash=hash_password(body.password),
        role=UserRole.STAFF,
        is_active=True,
    )
    db.add(staff)
    await db.flush()
    return staff


@router.patch("/staff/{staff_id}", response_model=StaffResponse)
async def update_staff(
    staff_id: UUID,
    body: StaffUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    owner: Annotated[User, Depends(require_owner)],
):
    result = await db.execute(
        select(User).where(
            User.id == staff_id,
            User.role == UserRole.STAFF,
            User.business_id == owner.business_id,
        )
    )
    staff = result.scalar_one_or_none()
    if staff is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff member not found")
    if body.email is not None and body.email != staff.email:
        duplicate_result = await db.execute(select(User).where(User.email == body.email))
        if duplicate_result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already in use")
        staff.email = body.email
    if body.name is not None:
        staff.name = body.name
    if body.phone is not None:
        staff.phone = body.phone
    await db.flush()
    return staff


async def _set_staff_active(
    staff_id: UUID,
    is_active: bool,
    db: AsyncSession,
    business_id: UUID,
) -> User:
    result = await db.execute(
        select(User).where(
            User.id == staff_id,
            User.role == UserRole.STAFF,
            User.business_id == business_id,
        )
    )
    staff = result.scalar_one_or_none()
    if staff is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff member not found")
    staff.is_active = is_active
    await db.flush()
    return staff


@router.post("/staff/{staff_id}/activate", response_model=StaffResponse)
async def activate_staff(
    staff_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    owner: Annotated[User, Depends(require_owner)],
):
    return await _set_staff_active(staff_id, True, db, owner.business_id)


@router.post("/staff/{staff_id}/deactivate", response_model=StaffResponse)
async def deactivate_staff(
    staff_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    owner: Annotated[User, Depends(require_owner)],
):
    return await _set_staff_active(staff_id, False, db, owner.business_id)


@router.get("/orders", response_model=PaginatedOrders)
async def list_orders(
    db: Annotated[AsyncSession, Depends(get_db)],
    owner: Annotated[User, Depends(require_owner)],
    status_filter: str | None = Query(None, alias="status"),
    payment_status: str | None = None,
    assigned_staff: UUID | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List orders with the filters needed by the owner dashboard."""
    conditions = [Order.business_id == owner.business_id]
    if status_filter:
        try:
            conditions.append(Order.order_status == OrderStatus(status_filter.upper()))
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="Invalid order status") from exc
    if payment_status:
        try:
            conditions.append(Order.payment_status == PaymentStatus(payment_status.upper()))
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="Invalid payment status") from exc
    if assigned_staff:
        conditions.append(
            exists(
                select(OrderAssignment.id).where(
                    OrderAssignment.order_id == Order.id,
                    OrderAssignment.staff_id == assigned_staff,
                    OrderAssignment.unassigned_at.is_(None),
                )
            )
        )
    if search:
        term = f"%{search.strip()}%"
        conditions.append(
            or_(Order.order_number.ilike(term), Customer.name.ilike(term), Customer.phone.ilike(term))
        )

    count_result = await db.execute(
        select(func.count(Order.id)).join(Customer).where(*conditions)
    )
    total = count_result.scalar_one()
    result = await db.execute(
        select(Order)
        .join(Customer)
        .where(*conditions)
        .options(*_order_options())
        .order_by(Order.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    orders = result.scalars().unique().all()
    return {
        "items": [_order_detail(order) for order in orders],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.get("/orders/{order_id}", response_model=OrderDetailResponse)
async def get_admin_order(
    order_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    owner: Annotated[User, Depends(require_owner)],
):
    return _order_detail(await _get_order(db, order_id, owner.business_id))


@router.post("/orders/{order_id}/confirm", response_model=OrderDetailResponse)
async def confirm_order(
    order_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    owner: Annotated[User, Depends(require_owner)],
):
    order = await _get_order(db, order_id, owner.business_id)
    _transition(order, OrderStatus.CONFIRMED)
    await db.flush()
    return await _get_order_detail(db, order_id, owner.business_id)


@router.post("/orders/{order_id}/assign", response_model=OrderDetailResponse)
async def assign_order(
    order_id: UUID,
    body: AssignOrderRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    owner: Annotated[User, Depends(require_owner)],
):
    order = await _get_order(db, order_id, owner.business_id)
    staff_result = await db.execute(
        select(User).where(
            User.id == body.staff_id,
            User.role == UserRole.STAFF,
            User.is_active == True,
            User.business_id == owner.business_id,
        )
    )
    staff = staff_result.scalar_one_or_none()
    if staff is None:
        raise HTTPException(status_code=404, detail="Active staff member not found")

    if order.order_status != OrderStatus.ASSIGNED:
        _transition(order, OrderStatus.ASSIGNED)
    active_assignment = next(
        (assignment for assignment in order.assignments if assignment.unassigned_at is None),
        None,
    )
    if active_assignment:
        active_assignment.unassigned_at = datetime.now(timezone.utc)
    assignment = OrderAssignment(
        order_id=order.id,
        staff_id=staff.id,
        assigned_by=owner.id,
        assigned_at=datetime.now(timezone.utc),
    )
    db.add(assignment)
    await db.flush()
    return await _get_order_detail(db, order_id, owner.business_id)


@router.post("/orders/{order_id}/unassign", response_model=OrderDetailResponse)
async def unassign_order(
    order_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    owner: Annotated[User, Depends(require_owner)],
):
    order = await _get_order(db, order_id, owner.business_id)
    active_assignment = next(
        (assignment for assignment in order.assignments if assignment.unassigned_at is None),
        None,
    )
    if active_assignment:
        active_assignment.unassigned_at = datetime.now(timezone.utc)
    if order.order_status == OrderStatus.ASSIGNED:
        _transition(order, OrderStatus.CONFIRMED)
    await db.flush()
    return await _get_order_detail(db, order_id, owner.business_id)


@router.post("/orders/{order_id}/out-for-delivery", response_model=OrderDetailResponse)
async def mark_out_for_delivery(
    order_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    owner: Annotated[User, Depends(require_owner)],
):
    order = await _get_order(db, order_id, owner.business_id)
    _transition(order, OrderStatus.OUT_FOR_DELIVERY)
    await db.flush()
    return await _get_order_detail(db, order_id, owner.business_id)


@router.post("/orders/{order_id}/delivered", response_model=OrderDetailResponse)
async def mark_delivered(
    order_id: UUID,
    body: DeliverOrderRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    owner: Annotated[User, Depends(require_owner)],
):
    order = await _get_order(db, order_id, owner.business_id)
    _transition(order, OrderStatus.DELIVERED)
    if body.cans_delivered > order.quantity:
        raise HTTPException(status_code=422, detail="Delivered cans cannot exceed ordered quantity")

    balance_result = await db.execute(
        select(CustomerCanBalance)
        .where(
            CustomerCanBalance.customer_id == order.customer_id,
            CustomerCanBalance.business_id == owner.business_id,
        )
        .with_for_update()
    )
    balance = balance_result.scalar_one_or_none()
    if balance is None:
        balance = CustomerCanBalance(
            business_id=owner.business_id,
            customer_id=order.customer_id,
            current_balance=0,
        )
        db.add(balance)
        await db.flush()

    new_balance = balance.current_balance + body.cans_delivered - body.empty_cans_returned
    if new_balance < 0:
        raise HTTPException(status_code=422, detail="Returned cans exceed the customer's current balance")

    before = balance.current_balance
    balance.current_balance = new_balance
    summary = OrderCanSummary(
        order_id=order.id,
        cans_delivered=body.cans_delivered,
        empty_cans_returned=body.empty_cans_returned,
        notes=body.notes,
    )
    db.add(summary)
    if body.cans_delivered:
        db.add(CanTransaction(
            business_id=owner.business_id,
            customer_id=order.customer_id,
            order_id=order.id,
            transaction_type=CanTransactionType.DELIVERED,
            quantity=body.cans_delivered,
            balance_before=before,
            balance_after=before + body.cans_delivered,
            notes=body.notes,
            created_by=owner.id,
        ))
    if body.empty_cans_returned:
        db.add(CanTransaction(
            business_id=owner.business_id,
            customer_id=order.customer_id,
            order_id=order.id,
            transaction_type=CanTransactionType.RETURNED,
            quantity=body.empty_cans_returned,
            balance_before=before + body.cans_delivered,
            balance_after=new_balance,
            notes=body.notes,
            created_by=owner.id,
        ))
    await db.flush()
    return await _get_order_detail(db, order_id, owner.business_id)


@router.post("/orders/{order_id}/cancel", response_model=OrderDetailResponse)
async def cancel_order(
    order_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    owner: Annotated[User, Depends(require_owner)],
):
    order = await _get_order(db, order_id, owner.business_id)
    _transition(order, OrderStatus.CANCELLED)
    await db.flush()
    return await _get_order_detail(db, order_id, owner.business_id)
