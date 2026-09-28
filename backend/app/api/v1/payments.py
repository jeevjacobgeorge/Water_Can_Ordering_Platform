"""Razorpay payment creation, verification, and webhook handling."""

import hashlib
import hmac
import json
import asyncio
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_db
from app.models.order import Order, OrderStatus, PaymentStatus
from app.models.payment import Payment, PaymentProvider, PaymentRecordStatus
from app.schemas.payment import (
    CreatePaymentOrderRequest,
    CreatePaymentOrderResponse,
    PaymentVerifyResponse,
    VerifyPaymentRequest,
)

router = APIRouter(prefix="/payments", tags=["payments"])
settings = get_settings()


def _require_razorpay():
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Razorpay is not configured",
        )
    import razorpay

    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def _amount_in_paise(amount: Decimal | float) -> int:
    return int((Decimal(str(amount)) * 100).quantize(Decimal("1")))


@router.post("/create-order", response_model=CreatePaymentOrderResponse)
async def create_payment_order(
    body: CreatePaymentOrderRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create or reuse the Razorpay order for a pending water order."""
    result = await db.execute(select(Order).where(Order.id == body.order_id))
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if order.order_status == OrderStatus.CANCELLED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cancelled orders cannot be paid")

    amount = _amount_in_paise(order.total_amount)
    if amount < 100:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Razorpay orders must be at least 100 paise",
        )
    existing_result = await db.execute(
        select(Payment)
        .where(Payment.order_id == order.id)
        .order_by(Payment.created_at.desc())
        .limit(1)
    )
    existing = existing_result.scalar_one_or_none()
    if existing and existing.provider_order_id:
        return CreatePaymentOrderResponse(
            razorpay_order_id=existing.provider_order_id,
            amount=amount,
            currency=existing.currency,
            order_id=order.id,
        )

    client = _require_razorpay()
    try:
        provider_order = await asyncio.to_thread(
            client.order.create,
            {
                "amount": amount,
                "currency": "INR",
                "receipt": order.order_number,
                "notes": {"order_id": str(order.id)},
            },
        )
    except Exception as exc:
        provider_status = getattr(exc, "status_code", None)
        response = getattr(exc, "response", None)
        if provider_status == 401 or getattr(response, "status_code", None) == 401:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Razorpay authentication failed",
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to create the Razorpay order",
        ) from exc

    payment = existing or Payment(order_id=order.id, provider=PaymentProvider.RAZORPAY)
    payment.provider_order_id = provider_order["id"]
    payment.amount = Decimal(str(order.total_amount))
    payment.currency = "INR"
    payment.status = PaymentRecordStatus.CREATED
    payment.raw_response = json.dumps(provider_order)
    db.add(payment)
    await db.flush()

    return CreatePaymentOrderResponse(
        razorpay_order_id=payment.provider_order_id,
        amount=amount,
        currency=payment.currency,
        order_id=order.id,
    )


@router.post("/verify", response_model=PaymentVerifyResponse)
async def verify_payment(
    body: VerifyPaymentRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Verify the browser callback signature before marking an order paid."""
    result = await db.execute(select(Order).where(Order.id == body.order_id))
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if not settings.RAZORPAY_KEY_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Razorpay is not configured",
        )

    payment_result = await db.execute(
        select(Payment).where(
            Payment.order_id == order.id,
            Payment.provider_order_id == body.razorpay_order_id,
        )
    )
    payment = payment_result.scalar_one_or_none()
    if payment is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment order is not registered")

    message = f"{body.razorpay_order_id}|{body.razorpay_payment_id}".encode()
    expected_signature = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode(), message, hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected_signature, body.razorpay_signature):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payment signature")

    if order.payment_status != PaymentStatus.PAID:
        payment.provider_payment_id = body.razorpay_payment_id
        payment.status = PaymentRecordStatus.CAPTURED
        order.payment_status = PaymentStatus.PAID
        if order.order_status == OrderStatus.PENDING_PAYMENT:
            order.order_status = OrderStatus.PAID
        await db.flush()

    return PaymentVerifyResponse(
        success=True,
        order_id=order.id,
        order_number=order.order_number,
        payment_status=order.payment_status.value,
        order_status=order.order_status.value,
    )


@router.post("/webhook")
async def razorpay_webhook(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    x_razorpay_signature: Annotated[str | None, Header()] = None,
):
    """Accept signed Razorpay payment events and process them once."""
    raw_body = await request.body()
    if not settings.RAZORPAY_WEBHOOK_SECRET or not x_razorpay_signature:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing webhook signature")

    expected_signature = hmac.new(
        settings.RAZORPAY_WEBHOOK_SECRET.encode(), raw_body, hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected_signature, x_razorpay_signature):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid webhook signature")

    try:
        event = json.loads(raw_body)
        entity = event["payload"]["payment"]["entity"]
        provider_order_id = entity["order_id"]
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid webhook payload") from exc

    result = await db.execute(
        select(Payment).where(Payment.provider_order_id == provider_order_id)
    )
    payment = result.scalar_one_or_none()
    if payment is None:
        return {"received": True, "processed": False}

    order_result = await db.execute(select(Order).where(Order.id == payment.order_id))
    order = order_result.scalar_one_or_none()
    if order is None:
        return {"received": True, "processed": False}

    event_name = event.get("event")
    if event_name == "payment.captured" and order.payment_status != PaymentStatus.PAID:
        payment.provider_payment_id = entity.get("id")
        payment.status = PaymentRecordStatus.CAPTURED
        payment.raw_response = raw_body.decode("utf-8")
        order.payment_status = PaymentStatus.PAID
        if order.order_status == OrderStatus.PENDING_PAYMENT:
            order.order_status = OrderStatus.PAID
    elif event_name == "payment.failed" and order.payment_status == PaymentStatus.PENDING:
        payment.provider_payment_id = entity.get("id")
        payment.status = PaymentRecordStatus.FAILED
        payment.raw_response = raw_body.decode("utf-8")
        order.payment_status = PaymentStatus.FAILED

    await db.flush()
    return {"received": True, "processed": True}
