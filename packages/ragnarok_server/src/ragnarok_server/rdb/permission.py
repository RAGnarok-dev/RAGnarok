from typing import TYPE_CHECKING
import enum
from sqlalchemy import Integer, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

if TYPE_CHECKING:
    from .knowledge_base import KnowledgeBase
    from .user import User

class PermissionType(str, enum.Enum):
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"

class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    knowledge_base_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False
    )
    permission_type: Mapped[PermissionType] = mapped_column(Enum(PermissionType), nullable=False)

    __table_args__ = (UniqueConstraint("user_id", "knowledge_base_id", name="_user_kb_uc"),)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="permissions")
    knowledge_base: Mapped["KnowledgeBase"] = relationship("KnowledgeBase", back_populates="permissions")

    def __repr__(self) -> str:
        return f"<Permission user={self.user_id} kb={self.knowledge_base_id} type={self.permission_type.value}>"
