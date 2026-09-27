"""Customer order creation and history endpoints."""

from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.address import CustomerAddress
from app.models.business_settings import BusinessSettings
from app.models.customer import Customer
from app.models.order import DeliverySlot, Order, OrderStatus, PaymentStatus
from app.models.product import Product
from app.schemas.order import OrderCreate, OrderCreateResponse, OrderResponse, RefillOrder
from app.services.order_number import generate_order_number

router = APIRouter(prefix="/orders", tags=["orders"])
refill_router = APIRouter(prefix="/customers", tags=["orders"])


async def _get_order_inputs(
    db: AsyncSession,
    customer_id: UUID,
    address_id: UUID,
):
    customer_result = await db.execute(
        select(Customer).where(Customer.id == customer_id, Customer.is_active == True)
    )
    customer = customer_result.scalar_one_or_none()
    if customer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    address_result = await db.execute(
        select(CustomerAddress).where(
            CustomerAddress.id == address_id,
            CustomerAddress.customer_id == customer_id,
        )
    )
    address = address_result.scalar_one_or_none()
    if address is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found")

    product_result = await db.execute(
        select(Product)
        .where(Product.is_active == True)
        .order_by(Product.created_at.asc())
        .limit(1)
    )
    product = product_result.scalar_one_or_none()
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No active water product is configured",
        )

    business_result = await db.execute(select(BusinessSettings).limit(1))
    business_settings = business_result.scalar_one_or_none()
    delivery_charge = Decimal(
        str(business_settings.default_delivery_charge)
        if business_settings is not None
        else "0"
    )
    return customer, address, product, delivery_charge


def _parse_delivery_slot(value: str | None) -> DeliverySlot | None:
    if value is None:
        return None
    try:
        return DeliverySlot(value.upper())
    except ValueError as exc:
        allowed = ", ".join(slot.value for slot in DeliverySlot)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"delivery_slot must be one of: {allowed}",
        ) from exc


async def _create_order(
    db: AsyncSession,
    customer_id: UUID,
    address_id: UUID,
    quantity: int,
    delivery_slot: str | None,
    customer_notes: str | None,
) -> Order:
    _, _, product, delivery_charge = await _get_order_inputs(
        db, customer_id, address_id
    )

    price_per_unit = Decimal(str(product.price_per_unit))
    subtotal = price_per_unit * quantity
    order = Order(
        order_number=await generate_order_number(db),
        customer_id=customer_id,
        address_id=address_id,
        product_id=product.id,
        quantity=quantity,
        price_per_unit=price_per_unit,
        subtotal=subtotal,
        delivery_charge=delivery_charge,
        discount=Decimal("0"),
        total_amount=subtotal + delivery_charge,
        payment_status=PaymentStatus.PENDING,
        order_status=OrderStatus.PENDING_PAYMENT,
        delivery_slot=_parse_delivery_slot(delivery_slot),
        customer_notes=customer_notes,
    )
    db.add(order)
    await db.flush()
    return order


@router.post("", response_model=OrderCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    body: OrderCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a pending-payment order using the current server-side price."""
    return await _create_order(
        db,
        body.customer_id,
        body.address_id,
        body.quantity,
        body.delivery_slot,
        body.customer_notes,
    )


@refill_router.post(
    "/{customer_id}/refill",
    response_model=OrderCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_refill_order(
    customer_id: UUID,
    body: RefillOrder,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a refill against a supplied or default saved address."""
    address_id = body.address_id
    if address_id is None:
        result = await db.execute(
            select(CustomerAddress)
            .where(
                CustomerAddress.customer_id == customer_id,
                CustomerAddress.is_default == True,
            )
            .order_by(CustomerAddress.created_at.asc())
            .limit(1)
        )
        address = result.scalar_one_or_none()
        if address is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An address is required before placing an order",
            )
        address_id = address.id

    return await _create_order(
        db,
        customer_id,
        address_id,
        body.quantity,
        body.delivery_slot,
        body.customer_notes,
    )


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Return the customer-facing order summary."""
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order
