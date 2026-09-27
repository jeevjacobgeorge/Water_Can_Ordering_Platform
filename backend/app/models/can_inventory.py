"""
Customer can balance and can transaction ledger models.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import UUIDMixin


class CanTransactionType(str, enum.Enum):
    DELIVERED = "DELIVERED"
    RETURNED = "RETURNED"
    ADJUSTMENT = "ADJUSTMENT"


class CustomerCanBalance(UUIDMixin, Base):
    __tablename__ = "customer_can_balances"

    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    current_balance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    customer = relationship("Customer", back_populates="can_balance")

    __table_args__ = (
        Index("ix_customer_can_balances_customer_id", "customer_id"),
    )

    def __repr__(self) -> str:
        return f"<CustomerCanBalance customer={self.customer_id} balance={self.current_balance}>"


class CanTransaction(UUIDMixin, Base):
    __tablename__ = "can_transactions"

    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
    )
    order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="SET NULL"),
        nullable=True,
    )
    transaction_type: Mapped[CanTransactionType] = mapped_column(
        Enum(CanTransactionType, name="can_transaction_type"),
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    balance_before: Mapped[int] = mapped_column(Integer, nullable=False)
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    customer = relationship("Customer")
    order = relationship("Order")
    created_by_user = relationship("User")

    __table_args__ = (
        Index("ix_can_transactions_customer_id", "customer_id"),
        Index("ix_can_transactions_order_id", "order_id"),
        Index("ix_can_transactions_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<CanTransaction {self.transaction_type.value} qty={self.quantity}>"
