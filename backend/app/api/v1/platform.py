"""Platform administration for onboarding and managing sellers."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import require_platform_admin
from app.core.security import hash_password
from app.db.session import get_db
from app.models.business import Business
from app.models.business_settings import BusinessSettings
from app.models.user import User, UserRole
from app.schemas.business import SellerCreate, SellerResponse

router = APIRouter(prefix="/platform", tags=["platform"])


def _seller_response(business: Business) -> SellerResponse:
    owner = next((user for user in business.users if user.role == UserRole.OWNER), None)
    return SellerResponse(
        id=business.id,
        name=business.name,
        slug=business.slug,
        is_active=business.is_active,
        owner_name=owner.name if owner else None,
        owner_email=owner.email if owner else None,
        created_at=business.created_at,
    )


@router.get("/sellers", response_model=list[SellerResponse])
async def list_sellers(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_platform_admin)],
):
    result = await db.execute(
        select(Business)
        .options(selectinload(Business.users))
        .order_by(Business.created_at.asc())
    )
    return [_seller_response(business) for business in result.scalars().unique().all()]


@router.post("/sellers", response_model=SellerResponse, status_code=status.HTTP_201_CREATED)
async def create_seller(
    body: SellerCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_platform_admin)],
):
    slug = body.slug.strip().lower()
    existing_slug = await db.execute(select(Business).where(Business.slug == slug))
    if existing_slug.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Seller slug is already in use")
    owner_email = body.owner_email.strip().lower()
    existing_email = await db.execute(select(User).where(User.email == owner_email))
    if existing_email.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Owner email is already in use")

    business = Business(name=body.business_name.strip(), slug=slug, is_active=True)
    db.add(business)
    await db.flush()
    db.add(BusinessSettings(
        business_id=business.id,
        business_name=body.business_name.strip(),
        business_phone=body.business_phone,
        business_address=body.business_address,
        business_whatsapp=body.business_whatsapp,
        currency=body.currency.upper(),
        default_delivery_charge=body.default_delivery_charge,
    ))
    db.add(User(
        business_id=business.id,
        name=body.owner_name.strip(),
        phone=body.owner_phone,
        email=owner_email,
        password_hash=hash_password(body.owner_password),
        role=UserRole.OWNER,
        is_active=True,
    ))
    await db.flush()
    await db.refresh(business, attribute_names=["users"])
    return _seller_response(business)


@router.post("/sellers/{business_id}/activate", response_model=SellerResponse)
async def activate_seller(
    business_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_platform_admin)],
):
    return await _set_seller_active(business_id, True, db)


@router.post("/sellers/{business_id}/deactivate", response_model=SellerResponse)
async def deactivate_seller(
    business_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_platform_admin)],
):
    return await _set_seller_active(business_id, False, db)


async def _set_seller_active(business_id: UUID, is_active: bool, db: AsyncSession) -> SellerResponse:
    result = await db.execute(
        select(Business).where(Business.id == business_id).options(selectinload(Business.users))
    )
    business = result.scalar_one_or_none()
    if business is None:
        raise HTTPException(status_code=404, detail="Seller not found")
    business.is_active = is_active
    for user in business.users:
        user.is_active = is_active
    await db.flush()
    return _seller_response(business)
