"""
Customer model — customers who order water cans.
"""

from sqlalchemy import Boolean, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import UUIDMixin, TimestampMixin


class Customer(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "customers"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(15), unique=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    addresses = relationship("CustomerAddress", back_populates="customer", lazy="selectin")
    orders = relationship("Order", back_populates="customer", lazy="select")
    can_balance = relationship("CustomerCanBalance", back_populates="customer", uselist=False, lazy="selectin")

    __table_args__ = (
        Index("ix_customers_phone", "phone"),
        Index("ix_customers_name", "name"),
    )

    def __repr__(self) -> str:
        return f"<Customer {self.name} ({self.phone})>"
