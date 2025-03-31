# knowledge_base.py - KnowledgeBase model
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    # Optionally, you could include an owner_user_id if needed:
    # owner_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="knowledge_bases")
    # owner = relationship("User", back_populates="owned_kbs")  # if owner_user_id is used
    permissions = relationship("Permission", back_populates="knowledge_base")  # all permission records for this KB

    def __repr__(self):
        return f"<KnowledgeBase {self.id} title={self.title} tenant={self.tenant_id}>"
