from datetime import datetime
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


class Blog(Base):
    """
    Blog model for the application.
    """

    __tablename__ = "blogs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    author = relationship("User", back_populates="blogs")
    comments = relationship("Comment", back_populates="blog")
    liked_by = relationship(
        "User",
        secondary="blog_likes",
        back_populates="liked_blogs",
    )

    def __repr__(self):
        return f"<Blog(id={self.id}, title={self.title}, author_id={self.author_id})>"


class Comment(Base):
    """
    Comment model for the application.
    """

    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    blog_id: Mapped[int] = mapped_column(
        ForeignKey("blogs.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="comments")
    blog = relationship("Blog", back_populates="comments")

    def __repr__(self):
        return (
            f"<Comment(id={self.id}, blog_id={self.blog_id}, user_id={self.user_id})>"
        )


blog_likes = Table(
    "blog_likes",
    Base.metadata,
    Column(
        "user_id", UUID, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    ),
    Column(
        "blog_id", Integer, ForeignKey("blogs.id", ondelete="CASCADE"), primary_key=True
    ),
    Column("created_at", DateTime, default=datetime.utcnow),
    UniqueConstraint("user_id", "blog_id", name="uq_user_blog_like"),
)
