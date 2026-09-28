"""
Auth API — login and current user endpoints.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user
from app.core.security import verify_password, create_access_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, MeResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Authenticate owner or staff and return JWT token."""
    result = await db.execute(
        select(User).where(User.email == body.username).options(selectinload(User.business))
    )
    user = result.scalar_one_or_none()

    if user is None or not verify_password(body.password, user.password_hash):
        logger.warning("Failed login attempt for: %s", body.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role.value}
    )

    logger.info("User logged in: %s (%s)", user.email, user.role.value)

    return LoginResponse(
        access_token=access_token,
        user=UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role.value,
            business_id=user.business_id,
            business_slug=user.business.slug if user.business else None,
        ),
    )


@router.get("/me", response_model=MeResponse)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Return the currently authenticated user's profile."""
    return MeResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        phone=current_user.phone,
        role=current_user.role.value,
        is_active=current_user.is_active,
        business_id=current_user.business_id,
        business_slug=current_user.business.slug if current_user.business else None,
    )
