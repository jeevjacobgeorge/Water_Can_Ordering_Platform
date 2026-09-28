"""Seller/business API schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class BusinessPublicResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    business_phone: str
    business_address: str | None
    business_whatsapp: str | None
    currency: str
    default_delivery_charge: float


class SellerCreate(BaseModel):
    business_name: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=2, max_length=100, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    business_phone: str = Field(..., min_length=10, max_length=15)
    business_address: str | None = None
    business_whatsapp: str | None = None
    currency: str = Field("INR", min_length=3, max_length=3)
    default_delivery_charge: float = Field(0, ge=0)
    owner_name: str = Field(..., min_length=2, max_length=255)
    owner_email: str
    owner_phone: str | None = None
    owner_password: str = Field(..., min_length=8)


class SellerResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    is_active: bool
    owner_name: str | None = None
    owner_email: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
