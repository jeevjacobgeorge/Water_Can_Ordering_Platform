"""Helpers for resolving active seller/business tenants."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import HTTPException, status

from app.models.business import Business


async def resolve_business(
    db: AsyncSession,
    slug: str | None = None,
) -> Business:
    query = select(Business).where(Business.is_active == True).order_by(Business.created_at.asc())
    if slug:
        query = query.where(Business.slug == slug.strip().lower())
    result = await db.execute(query.limit(1))
    business = result.scalar_one_or_none()
    if business is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seller/business not found",
        )
    return business
