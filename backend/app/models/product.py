"""
Product model — water can products with configurable pricing.
"""

import uuid

from sqlalchemy import Boolean, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import UUIDMixin, TimestampMixin


class Product(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "products"

    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    price_per_unit: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    unit_name: Mapped[str] = mapped_column(String(50), default="can", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    business = relationship("Business", back_populates="products", lazy="selectin")

    __table_args__ = (
        Index("ix_products_is_active", "is_active"),
        Index("ix_products_business_id", "business_id"),
    )

    def __repr__(self) -> str:
        return f"<Product {self.name} ₹{self.price_per_unit}/{self.unit_name}>"
