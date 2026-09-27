"""
Business settings model — single-row configuration for the water can business.
"""

from sqlalchemy import Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.base import UUIDMixin, TimestampMixin


class BusinessSettings(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "business_settings"

    business_name: Mapped[str] = mapped_column(String(255), nullable=False)
    business_phone: Mapped[str] = mapped_column(String(15), nullable=False)
    business_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    business_whatsapp: Mapped[str | None] = mapped_column(String(15), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    default_delivery_charge: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)

    def __repr__(self) -> str:
        return f"<BusinessSettings {self.business_name}>"
