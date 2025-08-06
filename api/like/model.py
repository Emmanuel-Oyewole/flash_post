from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
import uuid
from api.config.database import Base

class Like(Base):
    """
    Like model for the application.
    """

    __tablename__ = "likes"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    blog_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("blogs.id"), nullable=True, index=True
    )
    comment_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("comments.id"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="likes")
    blog = relationship("Blog", back_populates="likes")
    comment = relationship("Comment", back_populates="likes")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "(blog_id IS NOT NULL AND comment_id IS NULL) OR (blog_id IS NULL AND comment_id IS NOT NULL)",
            name="like_target_check"
        ),
    )

    def __repr__(self):
        target = f"blog_id={self.blog_id}" if self.blog_id else f"comment_id={self.comment_id}"
        return f"<Like(id={self.id}, user_id={self.user_id}, {target})>"