from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column
from . import Base


class User(Base):
    """
    User model for the application.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(255), index=True)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    avatar: str = Column(
        String, default="https://avatar.iran.liara.run/public/boy?username=Ash"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    blogs = relationship("Blog", back_populates="author", cascade="all, delete-orphan")
    comments = relationship(
        "Comment", back_populates="user", cascade="all, delete-orphan"
    )
    liked_blogs = relationship(
        "Blog", secondary="blog_likes", back_populates="liked_by"
    )

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"
