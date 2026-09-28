"""
Auth schemas — login request/response models.
"""

import uuid

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    username: str  # email or username
    password: str


class UserResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    role: str
    business_id: uuid.UUID | None = None
    business_slug: str | None = None

    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class MeResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    phone: str | None
    role: str
    is_active: bool
    business_id: uuid.UUID | None = None
    business_slug: str | None = None

    model_config = {"from_attributes": True}
