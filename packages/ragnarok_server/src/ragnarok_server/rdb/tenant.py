from typing import TYPE_CHECKING, Optional
from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

if TYPE_CHECKING:
    from .knowledge_base import KnowledgeBase
    from .user import User

class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    admin_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    admin_user: Mapped[Optional["User"]] = relationship(
        "User", back_populates="tenant_admin_of", foreign_keys=[admin_user_id], uselist=False
    )
    users: Mapped[list["User"]] = relationship("User", back_populates="tenant", foreign_keys="User.tenant_id")
    knowledge_bases: Mapped[list["KnowledgeBase"]] = relationship("KnowledgeBase", back_populates="tenant")

    def __repr__(self) -> str:
        return f"<Tenant {self.id} name={self.name}>"
