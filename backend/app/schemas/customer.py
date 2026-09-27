"""
Customer schemas — request/response models for customer endpoints.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CustomerCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    phone: str = Field(..., pattern=r"^[6-9]\d{9}$")
    email: str | None = None


class CustomerUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    email: str | None = None


class AddressCreate(BaseModel):
    label: str = "Home"
    address_line_1: str = Field(..., min_length=1, max_length=500)
    address_line_2: str | None = None
    city: str = Field(..., min_length=1, max_length=100)
    district: str | None = None
    state: str = "Kerala"
    pincode: str = Field(..., pattern=r"^\d{6}$")
    latitude: float | None = None
    longitude: float | None = None
    is_default: bool = False


class AddressUpdate(BaseModel):
    label: str | None = None
    address_line_1: str | None = None
    address_line_2: str | None = None
    city: str | None = None
    district: str | None = None
    state: str | None = None
    pincode: str | None = Field(None, pattern=r"^\d{6}$")
    latitude: float | None = None
    longitude: float | None = None


class AddressResponse(BaseModel):
    id: uuid.UUID
    customer_id: uuid.UUID
    label: str
    address_line_1: str
    address_line_2: str | None
    city: str
    district: str | None
    state: str
    pincode: str
    latitude: float | None
    longitude: float | None
    is_default: bool

    model_config = {"from_attributes": True}


class CanBalanceResponse(BaseModel):
    current_balance: int

    model_config = {"from_attributes": True}


class CustomerResponse(BaseModel):
    id: uuid.UUID
    name: str
    phone: str
    email: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class CustomerDetailResponse(BaseModel):
    """Extended customer info for the ordering flow."""
    id: uuid.UUID
    name: str
    phone: str
    default_address: AddressResponse | None = None
    addresses: list[AddressResponse] = []
    can_balance: int = 0
    last_order_quantity: int | None = None

    model_config = {"from_attributes": True}


class CustomerListResponse(BaseModel):
    """For admin customer listing."""
    id: uuid.UUID
    name: str
    phone: str
    email: str | None
    is_active: bool
    can_balance: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}
