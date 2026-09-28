"""Seller/business tenant model."""

import uuid

from sqlalchemy import Boolean, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import UUIDMixin, TimestampMixin


class Business(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "businesses"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    settings = relationship("BusinessSettings", back_populates="business", uselist=False, lazy="selectin")
    users = relationship("User", back_populates="business", lazy="select")
    products = relationship("Product", back_populates="business", lazy="select")
    customers = relationship("Customer", back_populates="business", lazy="select")
    orders = relationship("Order", back_populates="business", lazy="select")

    __table_args__ = (Index("ix_businesses_is_active", "is_active"),)

    def __repr__(self) -> str:
        return f"<Business {self.slug}>"
