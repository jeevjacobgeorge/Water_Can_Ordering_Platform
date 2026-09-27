"""
Order schemas — request/response models.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.customer import AddressResponse


class OrderCreate(BaseModel):
    customer_id: uuid.UUID
    address_id: uuid.UUID
    quantity: int = Field(..., gt=0, le=50)
    delivery_slot: str | None = None
    customer_notes: str | None = None


class RefillOrder(BaseModel):
    quantity: int = Field(..., gt=0, le=50)
    address_id: uuid.UUID | None = None
    delivery_slot: str | None = None
    customer_notes: str | None = None


class OrderResponse(BaseModel):
    id: uuid.UUID
    order_number: str
    customer_id: uuid.UUID
    quantity: int
    price_per_unit: float
    subtotal: float
    delivery_charge: float
    discount: float
    total_amount: float
    payment_status: str
    order_status: str
    delivery_slot: str | None
    customer_notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class OrderDetailResponse(BaseModel):
    id: uuid.UUID
    order_number: str
    customer_id: uuid.UUID
    customer_name: str
    customer_phone: str
    quantity: int
    price_per_unit: float
    subtotal: float
    delivery_charge: float
    discount: float
    total_amount: float
    payment_status: str
    order_status: str
    delivery_slot: str | None
    customer_notes: str | None
    address: AddressResponse | None = None
    assigned_staff_name: str | None = None
    assigned_staff_id: uuid.UUID | None = None
    cans_delivered: int | None = None
    empty_cans_returned: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrderCreateResponse(BaseModel):
    id: uuid.UUID
    order_number: str
    total_amount: float
    payment_status: str
    order_status: str

    model_config = {"from_attributes": True}


class DeliverOrderRequest(BaseModel):
    cans_delivered: int = Field(..., ge=0)
    empty_cans_returned: int = Field(0, ge=0)
    notes: str | None = None


class AssignOrderRequest(BaseModel):
    staff_id: uuid.UUID


class OrderListFilters(BaseModel):
    status: str | None = None
    payment_status: str | None = None
    staff_id: uuid.UUID | None = None
    date_from: str | None = None
    date_to: str | None = None
    search: str | None = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class PaginatedOrders(BaseModel):
    items: list[OrderDetailResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
