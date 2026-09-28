"""Public seller/business directory and profile endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.business import Business
from app.schemas.business import BusinessPublicResponse

router = APIRouter(prefix="/businesses", tags=["businesses"])


def _business_response(business: Business) -> BusinessPublicResponse:
    settings = business.settings
    return BusinessPublicResponse(
        id=business.id,
        name=business.name,
        slug=business.slug,
        business_phone=settings.business_phone if settings else "",
        business_address=settings.business_address if settings else None,
        business_whatsapp=settings.business_whatsapp if settings else None,
        currency=settings.currency if settings else "INR",
        default_delivery_charge=settings.default_delivery_charge if settings else 0,
    )


@router.get("", response_model=list[BusinessPublicResponse])
async def list_businesses(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(Business)
        .where(Business.is_active == True)
        .options(selectinload(Business.settings))
        .order_by(Business.name.asc())
    )
    return [_business_response(business) for business in result.scalars().unique().all()]


@router.get("/{slug}", response_model=BusinessPublicResponse)
async def get_business(slug: str, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(Business)
        .where(Business.slug == slug.lower(), Business.is_active == True)
        .options(selectinload(Business.settings))
    )
    business = result.scalar_one_or_none()
    if business is None:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seller/business not found")
    return _business_response(business)
