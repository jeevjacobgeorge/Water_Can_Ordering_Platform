"""
Business settings model — single-row configuration for the water can business.
"""

import uuid

from sqlalchemy import ForeignKey, Index, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import UUIDMixin, TimestampMixin


class BusinessSettings(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "business_settings"

    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False
    )
    business_name: Mapped[str] = mapped_column(String(255), nullable=False)
    business_phone: Mapped[str] = mapped_column(String(15), nullable=False)
    business_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    business_whatsapp: Mapped[str | None] = mapped_column(String(15), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    default_delivery_charge: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)

    business = relationship("Business", back_populates="settings", lazy="selectin")

    __table_args__ = (
        Index("ix_business_settings_business_id", "business_id"),
        UniqueConstraint("business_id", name="uq_business_settings_business_id"),
    )

    def __repr__(self) -> str:
        return f"<BusinessSettings {self.business_name}>"
