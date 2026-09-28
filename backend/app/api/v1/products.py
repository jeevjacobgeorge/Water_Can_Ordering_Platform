"""Public and owner-facing product endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_owner
from app.db.session import get_db
from app.models.product import Product
from app.models.user import User
from app.schemas.common import ProductResponse, ProductUpdate
from app.services.business import resolve_business

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductResponse])
async def list_products(
    db: Annotated[AsyncSession, Depends(get_db)],
    business_slug: str | None = Query(None),
):
    """Return active products for the customer ordering flow."""
    business = await resolve_business(db, business_slug)
    result = await db.execute(
        select(Product)
        .where(Product.is_active == True, Product.business_id == business.id)
        .order_by(Product.created_at.asc())
    )
    return result.scalars().all()


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    body: ProductUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    owner: Annotated[User, Depends(require_owner)],
):
    """Update product pricing and availability for the owner."""
    result = await db.execute(
        select(Product).where(Product.id == product_id, Product.business_id == owner.business_id)
    )
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    for field in ("name", "description", "price_per_unit", "is_active"):
        value = getattr(body, field)
        if value is not None:
            setattr(product, field, value)

    await db.flush()
    return product
