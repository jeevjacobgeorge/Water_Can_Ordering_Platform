"""
User model — owner and staff accounts.
"""

import enum
import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import UUIDMixin, TimestampMixin


class UserRole(str, enum.Enum):
    PLATFORM_ADMIN = "PLATFORM_ADMIN"
    OWNER = "OWNER"
    STAFF = "STAFF"


class User(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "users"

    business_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(15), nullable=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    business = relationship("Business", back_populates="users", lazy="selectin")

    __table_args__ = (
        Index("ix_users_email", "email"),
        Index("ix_users_role", "role"),
        Index("ix_users_business_id", "business_id"),
    )

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role.value})>"
