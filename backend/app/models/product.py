"""
Product model — water can products with configurable pricing.
"""

from sqlalchemy import Boolean, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.base import UUIDMixin, TimestampMixin


class Product(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "products"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    price_per_unit: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    unit_name: Mapped[str] = mapped_column(String(50), default="can", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        Index("ix_products_is_active", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<Product {self.name} ₹{self.price_per_unit}/{self.unit_name}>"
