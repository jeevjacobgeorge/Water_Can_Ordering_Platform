"""
Customer APIs — public customer lookup and creation for the ordering flow.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.customer import Customer
from app.models.address import CustomerAddress
from app.models.can_inventory import CustomerCanBalance
from app.models.order import Order
from app.schemas.customer import (
    AddressCreate,
    AddressResponse,
    AddressUpdate,
    CustomerCreate,
    CustomerDetailResponse,
    CustomerUpdate,
    CustomerResponse,
)
from app.services.business import resolve_business

router = APIRouter(prefix="/customers", tags=["customers"])
logger = logging.getLogger(__name__)


@router.get("/by-phone/{phone}", response_model=CustomerDetailResponse)
async def get_customer_by_phone(
    phone: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    business_slug: str | None = Query(None),
):
    """
    Public endpoint — lookup a customer by phone number for the ordering flow.
    Returns only the data needed for refill experience.
    """
    # Normalize phone (strip spaces, leading +91)
    phone = phone.strip().replace(" ", "")
    if phone.startswith("+91"):
        phone = phone[3:]
    if phone.startswith("91") and len(phone) == 12:
        phone = phone[2:]

    business = await resolve_business(db, business_slug)
    result = await db.execute(
        select(Customer)
        .where(
            Customer.phone == phone,
            Customer.business_id == business.id,
            Customer.is_active == True,
        )
        .options(
            selectinload(Customer.addresses),
            selectinload(Customer.can_balance),
        )
    )
    customer = result.scalar_one_or_none()

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    # Find default address
    default_addr = None
    addresses = []
    for addr in customer.addresses:
        addr_resp = AddressResponse.model_validate(addr)
        addresses.append(addr_resp)
        if addr.is_default:
            default_addr = addr_resp

    # If no default, use first address
    if default_addr is None and addresses:
        default_addr = addresses[0]

    # Get last order quantity
    last_order_result = await db.execute(
        select(Order.quantity)
        .where(Order.customer_id == customer.id)
        .order_by(Order.created_at.desc())
        .limit(1)
    )
    last_qty = last_order_result.scalar_one_or_none()

    can_bal = customer.can_balance.current_balance if customer.can_balance else 0

    return CustomerDetailResponse(
        id=customer.id,
        name=customer.name,
        phone=customer.phone,
        default_address=default_addr,
        addresses=addresses,
        can_balance=can_bal,
        last_order_quantity=last_qty,
    )


@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    body: CustomerCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    business_slug: str | None = Query(None),
):
    """Create a new customer (used during first-time ordering flow)."""
    business = await resolve_business(db, business_slug)
    # Check for duplicate phone
    existing = await db.execute(
        select(Customer).where(
            Customer.phone == body.phone,
            Customer.business_id == business.id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Customer with this phone number already exists",
        )

    customer = Customer(
        business_id=business.id,
        name=body.name,
        phone=body.phone,
        email=body.email,
    )
    db.add(customer)
    await db.flush()

    # Initialize can balance
    can_balance = CustomerCanBalance(
        business_id=business.id,
        customer_id=customer.id,
        current_balance=0,
    )
    db.add(can_balance)
    await db.flush()

    logger.info("Customer created: %s (%s)", customer.name, customer.phone)
    return CustomerResponse.model_validate(customer)


@router.patch("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: str,
    body: CustomerUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update customer details."""
    result = await db.execute(
        select(Customer).where(Customer.id == customer_id)
    )
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    if body.name is not None:
        customer.name = body.name
    if body.email is not None:
        customer.email = body.email

    await db.flush()
    return CustomerResponse.model_validate(customer)


# ── Address endpoints ─────────────────────────────────

@router.get("/{customer_id}/addresses", response_model=list[AddressResponse])
async def list_addresses(
    customer_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List all addresses for a customer."""
    result = await db.execute(
        select(CustomerAddress).where(CustomerAddress.customer_id == customer_id)
    )
    addresses = result.scalars().all()
    return [AddressResponse.model_validate(a) for a in addresses]


@router.post(
    "/{customer_id}/addresses",
    response_model=AddressResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_address(
    customer_id: str,
    body: AddressCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new address for a customer."""
    # Verify customer exists
    cust_result = await db.execute(
        select(Customer).where(Customer.id == customer_id)
    )
    if not cust_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Customer not found")

    # If this is default, unset other defaults
    if body.is_default:
        existing = await db.execute(
            select(CustomerAddress).where(
                CustomerAddress.customer_id == customer_id,
                CustomerAddress.is_default == True,
            )
        )
        for addr in existing.scalars().all():
            addr.is_default = False

    address = CustomerAddress(
        customer_id=customer_id,
        label=body.label,
        address_line_1=body.address_line_1,
        address_line_2=body.address_line_2,
        city=body.city,
        district=body.district,
        state=body.state,
        pincode=body.pincode,
        latitude=body.latitude,
        longitude=body.longitude,
        is_default=body.is_default,
    )
    db.add(address)
    await db.flush()
    return AddressResponse.model_validate(address)


@router.post("/{customer_id}/addresses/{address_id}/set-default")
async def set_default_address(
    customer_id: str,
    address_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Set an address as the customer's default."""
    # Unset all defaults for this customer
    existing = await db.execute(
        select(CustomerAddress).where(
            CustomerAddress.customer_id == customer_id,
            CustomerAddress.is_default == True,
        )
    )
    for addr in existing.scalars().all():
        addr.is_default = False

    # Set the new default
    result = await db.execute(
        select(CustomerAddress).where(
            CustomerAddress.id == address_id,
            CustomerAddress.customer_id == customer_id,
        )
    )
    address = result.scalar_one_or_none()
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")

    address.is_default = True
    await db.flush()
    return {"message": "Default address updated"}


# ── Can Balance ───────────────────────────────────────

@router.get("/{customer_id}/can-balance")
async def get_can_balance(
    customer_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get customer's current can balance."""
    result = await db.execute(
        select(CustomerCanBalance).where(
            CustomerCanBalance.customer_id == customer_id
        )
    )
    balance = result.scalar_one_or_none()
    return {"current_balance": balance.current_balance if balance else 0}


@router.get("/{customer_id}/can-transactions")
async def get_can_transactions(
    customer_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get customer's can transaction ledger."""
    from app.models.can_inventory import CanTransaction

    result = await db.execute(
        select(CanTransaction)
        .where(CanTransaction.customer_id == customer_id)
        .order_by(CanTransaction.created_at.desc())
        .limit(50)
    )
    transactions = result.scalars().all()
    return [
        {
            "id": str(t.id),
            "transaction_type": t.transaction_type.value,
            "quantity": t.quantity,
            "balance_before": t.balance_before,
            "balance_after": t.balance_after,
            "notes": t.notes,
            "created_at": t.created_at.isoformat(),
        }
        for t in transactions
    ]


# ── Customer Orders ───────────────────────────────────

@router.get("/{customer_id}/orders")
async def get_customer_orders(
    customer_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = 1,
    page_size: int = 10,
):
    """Get customer's order history with pagination."""
    from sqlalchemy import func

    offset = (page - 1) * page_size

    # Count total
    count_result = await db.execute(
        select(func.count(Order.id)).where(Order.customer_id == customer_id)
    )
    total = count_result.scalar_one()

    # Get orders
    result = await db.execute(
        select(Order)
        .where(Order.customer_id == customer_id)
        .order_by(Order.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    orders = result.scalars().all()

    return {
        "items": [
            {
                "id": str(o.id),
                "order_number": o.order_number,
                "quantity": o.quantity,
                "total_amount": float(o.total_amount),
                "order_status": o.order_status.value,
                "payment_status": o.payment_status.value,
                "created_at": o.created_at.isoformat(),
            }
            for o in orders
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
