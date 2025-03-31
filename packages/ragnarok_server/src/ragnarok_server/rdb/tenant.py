# tenant.py - Tenant model
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .base import Base


class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    # admin_user_id references a User who is the tenant admin (can be null until set)
    admin_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    admin_user = relationship("User", back_populates="tenant_admin_of", uselist=False)  # one admin per tenant
    users = relationship("User", back_populates="tenant")  # all users in this tenant
    knowledge_bases = relationship("KnowledgeBase", back_populates="tenant")  # all KBs under this tenant

    def __repr__(self):
        return f"<Tenant {self.id} name={self.name}>"
