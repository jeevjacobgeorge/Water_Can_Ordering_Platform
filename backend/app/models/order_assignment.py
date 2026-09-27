"""
Order assignment model — tracks which staff member is assigned to an order.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import UUIDMixin


class OrderAssignment(UUIDMixin, Base):
    __tablename__ = "order_assignments"

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    staff_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    assigned_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    unassigned_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    order = relationship("Order", back_populates="assignment")
    staff = relationship("User", foreign_keys=[staff_id], lazy="selectin")
    assigned_by_user = relationship("User", foreign_keys=[assigned_by], lazy="selectin")

    __table_args__ = (
        Index("ix_order_assignments_order_id", "order_id"),
        Index("ix_order_assignments_staff_id", "staff_id"),
    )

    def __repr__(self) -> str:
        return f"<OrderAssignment order={self.order_id} staff={self.staff_id}>"
