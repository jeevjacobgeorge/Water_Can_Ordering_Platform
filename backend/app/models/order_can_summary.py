"""
Order can summary — cans delivered and empty cans returned per order.
"""

import uuid

from sqlalchemy import ForeignKey, Index, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import UUIDMixin, TimestampMixin


class OrderCanSummary(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "order_can_summary"

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    cans_delivered: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    empty_cans_returned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    order = relationship("Order", back_populates="can_summary")

    __table_args__ = (
        Index("ix_order_can_summary_order_id", "order_id"),
    )

    def __repr__(self) -> str:
        return f"<OrderCanSummary order={self.order_id} +{self.cans_delivered} -{self.empty_cans_returned}>"
