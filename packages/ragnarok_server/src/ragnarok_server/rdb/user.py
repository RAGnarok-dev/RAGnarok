# user.py - User model
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False, unique=True, index=True)
    email = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    # Each user belongs to one tenant
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    # Flag to indicate if this user is the tenant admin (for convenience)
    is_tenant_admin = Column(Boolean, default=False)

    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    tenant_admin_of = relationship("Tenant", back_populates="admin_user",
                                   uselist=False)  # tenant where this user is admin
    # KnowledgeBases this user has direct admin access to (if any) - optional convenience relationship:
    # owned_kbs = relationship("KnowledgeBase", back_populates="owner")

    permissions = relationship("Permission", back_populates="user")  # all permission records of this user

    def __repr__(self):
        return f"<User {self.id} username={self.username} tenant={self.tenant_id}>"
