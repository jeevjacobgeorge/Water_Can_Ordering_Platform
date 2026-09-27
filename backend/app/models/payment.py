"""
Payment model — Razorpay payment records linked to orders.
"""

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import UUIDMixin, TimestampMixin


class PaymentProvider(str, enum.Enum):
    RAZORPAY = "RAZORPAY"


class PaymentRecordStatus(str, enum.Enum):
    CREATED = "CREATED"
    AUTHORIZED = "AUTHORIZED"
    CAPTURED = "CAPTURED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class Payment(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "payments"

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="RESTRICT"),
        nullable=False,
    )
    provider: Mapped[PaymentProvider] = mapped_column(
        Enum(PaymentProvider, name="payment_provider"),
        default=PaymentProvider.RAZORPAY,
        nullable=False,
    )
    provider_order_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider_payment_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    status: Mapped[PaymentRecordStatus] = mapped_column(
        Enum(PaymentRecordStatus, name="payment_record_status"),
        default=PaymentRecordStatus.CREATED,
        nullable=False,
    )
    payment_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    raw_response: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    order = relationship("Order", back_populates="payment")

    __table_args__ = (
        Index("ix_payments_order_id", "order_id"),
        Index("ix_payments_provider_order_id", "provider_order_id"),
        Index("ix_payments_provider_payment_id", "provider_payment_id"),
    )

    def __repr__(self) -> str:
        return f"<Payment order={self.order_id} ₹{self.amount} ({self.status.value})>"
