"""
Payment schemas.
"""

import uuid

from pydantic import BaseModel


class CreatePaymentOrderRequest(BaseModel):
    order_id: uuid.UUID


class CreatePaymentOrderResponse(BaseModel):
    razorpay_order_id: str
    amount: int  # in paise
    currency: str
    order_id: uuid.UUID


class VerifyPaymentRequest(BaseModel):
    order_id: uuid.UUID
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class PaymentVerifyResponse(BaseModel):
    success: bool
    order_id: uuid.UUID
    order_number: str
    payment_status: str
    order_status: str
