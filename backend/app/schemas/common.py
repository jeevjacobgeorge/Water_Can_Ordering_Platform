"""
Dashboard and miscellaneous schemas.
"""

import uuid

from pydantic import BaseModel, Field


# ── Dashboard ─────────────────────────────────────────

class DashboardTodayStats(BaseModel):
    orders: int = 0
    paid_orders: int = 0
    delivered_orders: int = 0
    revenue: float = 0
    cans_ordered: int = 0
    cans_delivered: int = 0
    empty_cans_returned: int = 0


class DashboardResponse(BaseModel):
    today: DashboardTodayStats
    pending_orders: int = 0
    unassigned_orders: int = 0
    out_for_delivery: int = 0
    total_cans_with_customers: int = 0


class StaffDashboardResponse(BaseModel):
    assigned_orders: int = 0
    available_orders: int = 0
    delivered_today: int = 0


# ── Product ───────────────────────────────────────────

class ProductResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    price_per_unit: float
    unit_name: str
    is_active: bool

    model_config = {"from_attributes": True}


class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price_per_unit: float | None = None
    is_active: bool | None = None


# ── Business Settings ─────────────────────────────────

class BusinessSettingsResponse(BaseModel):
    id: uuid.UUID
    business_name: str
    business_phone: str
    business_address: str | None
    business_whatsapp: str | None
    currency: str
    default_delivery_charge: float

    model_config = {"from_attributes": True}


class BusinessSettingsUpdate(BaseModel):
    business_name: str | None = None
    business_phone: str | None = None
    business_address: str | None = None
    business_whatsapp: str | None = None
    default_delivery_charge: float | None = None


# ── Staff ─────────────────────────────────────────────

class StaffCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    phone: str | None = None
    email: str = Field(..., min_length=1)
    password: str = Field(..., min_length=6)


class StaffUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    email: str | None = None


class StaffResponse(BaseModel):
    id: uuid.UUID
    name: str
    phone: str | None
    email: str
    role: str
    is_active: bool

    model_config = {"from_attributes": True}


# ── Can Adjustment ────────────────────────────────────

class CanAdjustmentRequest(BaseModel):
    quantity: int
    notes: str | None = None


class CanTransactionResponse(BaseModel):
    id: uuid.UUID
    transaction_type: str
    quantity: int
    balance_before: int
    balance_after: int
    notes: str | None
    created_at: str

    model_config = {"from_attributes": True}


# ── Generic ───────────────────────────────────────────

class MessageResponse(BaseModel):
    message: str
    data: dict | None = None
