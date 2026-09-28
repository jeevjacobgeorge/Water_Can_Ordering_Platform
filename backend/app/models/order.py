"""
Order model — tracks customer orders with status and payment lifecycle.
"""

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import UUIDMixin, TimestampMixin


class OrderStatus(str, enum.Enum):
    PENDING_PAYMENT = "PENDING_PAYMENT"
    PAID = "PAID"
    CONFIRMED = "CONFIRMED"
    ASSIGNED = "ASSIGNED"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class DeliverySlot(str, enum.Enum):
    MORNING = "MORNING"
    AFTERNOON = "AFTERNOON"
    EVENING = "EVENING"


# Valid status transitions (from → [allowed destinations])
VALID_STATUS_TRANSITIONS: dict[OrderStatus, list[OrderStatus]] = {
    OrderStatus.PENDING_PAYMENT: [OrderStatus.PAID, OrderStatus.CANCELLED],
    OrderStatus.PAID: [OrderStatus.CONFIRMED, OrderStatus.CANCELLED],
    OrderStatus.CONFIRMED: [OrderStatus.ASSIGNED, OrderStatus.CANCELLED],
    OrderStatus.ASSIGNED: [OrderStatus.OUT_FOR_DELIVERY, OrderStatus.CONFIRMED, OrderStatus.CANCELLED],
    OrderStatus.OUT_FOR_DELIVERY: [OrderStatus.DELIVERED, OrderStatus.ASSIGNED],
    OrderStatus.DELIVERED: [],
    OrderStatus.CANCELLED: [],
}


class Order(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "orders"

    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="RESTRICT"), nullable=False
    )
    order_number: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="RESTRICT"),
        nullable=False,
    )
    address_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customer_addresses.id", ondelete="RESTRICT"),
        nullable=False,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price_per_unit: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    subtotal: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    delivery_charge: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    discount: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    total_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    payment_status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status"),
        default=PaymentStatus.PENDING,
        nullable=False,
    )
    order_status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="order_status"),
        default=OrderStatus.PENDING_PAYMENT,
        nullable=False,
    )
    delivery_slot: Mapped[DeliverySlot | None] = mapped_column(
        Enum(DeliverySlot, name="delivery_slot"),
        nullable=True,
    )
    customer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    customer = relationship("Customer", back_populates="orders")
    address = relationship("CustomerAddress", lazy="selectin")
    product = relationship("Product", lazy="selectin")
    assignments = relationship("OrderAssignment", back_populates="order", lazy="selectin")
    can_summary = relationship("OrderCanSummary", back_populates="order", uselist=False, lazy="selectin")
    payment = relationship("Payment", back_populates="order", uselist=False, lazy="selectin")
    business = relationship("Business", back_populates="orders", lazy="selectin")

    __table_args__ = (
        Index("ix_orders_order_number", "order_number"),
        Index("ix_orders_customer_id", "customer_id"),
        Index("ix_orders_order_status", "order_status"),
        Index("ix_orders_payment_status", "payment_status"),
        Index("ix_orders_created_at", "created_at"),
        Index("ix_orders_business_id", "business_id"),
    )

    def __repr__(self) -> str:
        return f"<Order {self.order_number} ({self.order_status.value})>"
