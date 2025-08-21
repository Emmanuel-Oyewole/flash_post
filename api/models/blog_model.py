import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    String,
    DateTime,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from api.config.database import Base


class Blog(Base):
    """
    Blog model for the application.
    """

    __tablename__ = "blogs"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    author_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    like_count: Mapped[int] = mapped_column(Integer, default=0)
    comment_count: Mapped[int] = mapped_column(Integer, default=0)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationship
    author = relationship("User", back_populates="blogs")
    comments = relationship(
        "Comment", back_populates="blog", cascade="all, delete-orphan"
    )
    likes = relationship("Like", back_populates="blog", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary="blog_tags", back_populates="blogs")

    def __repr__(self):
        return f"<Blog(id={self.id}, title={self.title}, author_id={self.author_id})>"
