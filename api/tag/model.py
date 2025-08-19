import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Table,
    Column,
    ForeignKey,
    Integer,
    String,
    DateTime,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from api.config.database import Base

# Association table for Blog-Tag many-to-many relationship
blog_tags = Table(
    "blog_tags",
    Base.metadata,
    Column("blog_id", UUID(as_uuid=True), ForeignKey("blogs.id"), primary_key=True),
    Column("tag_id", UUID(as_uuid=True), ForeignKey("tags.id"), primary_key=True),
    Column("created_at", DateTime, default=lambda: datetime.now(timezone.utc)),
)


class Tag(Base):
    """
    Tag model for the application.
    """

    __tablename__ = "tags"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    slug: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    description: Mapped[str] = mapped_column(Text, nullable=True)
    color: Mapped[str] = mapped_column(String(7), nullable=True)  # Hex color
    usage_count: Mapped[int] = mapped_column(Integer, default=0, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    blogs = relationship("Blog", secondary=blog_tags, back_populates="tags")

    def __repr__(self):
        return f"<Tag(id={self.id}, name={self.name}, usage_count={self.usage_count})>"
