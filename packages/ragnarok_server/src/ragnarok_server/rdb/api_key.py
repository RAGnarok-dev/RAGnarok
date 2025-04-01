from typing import TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, Integer, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

if TYPE_CHECKING:
    from .user import User

class APIKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    key_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    remark: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    # Relationship back to the User model.
    user: Mapped["User"] = relationship("User", back_populates="api_keys")

    def __repr__(self) -> str:
        return f"<APIKey {self.id} user_id={self.user_id} enabled={self.enabled}>"
