from datetime import datetime, timezone
import enum
from sqlalchemy import String, DateTime, Boolean, Text, Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
import uuid
from api.config.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"


class User(Base):
    """
    User model for the application.
    """

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    first_name: Mapped[str] = mapped_column(String(255), nullable=True, default="")
    last_name: Mapped[str] = mapped_column(String(255), nullable=True, default="")
    middle_name: Mapped[str] = mapped_column(String(255), nullable=True, default="")
    bio: Mapped[str] = mapped_column(Text, nullable=True, default="")
    avatar: Mapped[str] = mapped_column(
        String, default="https://avatar.iran.liara.run/public/boy?username=Ash"
    )
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.USER)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        index=True,
    )

    # Relationships
    blogs = relationship("Blog", back_populates="author", cascade="all, delete-orphan")
    comments = relationship(
        "Comment", back_populates="author", cascade="all, delete-orphan"
    )
    likes = relationship("Like", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, full_name={self.full_name}, email={self.email})>"

    @property
    def full_name(self):
        """Generate full name from name components"""
        names = [self.first_name, self.middle_name, self.last_name]
        return " ".join(name for name in names if name)
