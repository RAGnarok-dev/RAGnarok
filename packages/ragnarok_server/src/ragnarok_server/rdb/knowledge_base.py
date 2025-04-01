from typing import TYPE_CHECKING
from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

if TYPE_CHECKING:
    from .permission import Permission
    from .tenant import Tenant

class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    tenant_id: Mapped[int] = mapped_column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="knowledge_bases")
    permissions: Mapped[list["Permission"]] = relationship("Permission", back_populates="knowledge_base")

    def __repr__(self) -> str:
        return f"<KnowledgeBase {self.id} title={self.title} tenant={self.tenant_id}>"
