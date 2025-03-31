# permission.py - Permission model (association table with extra field)
import enum
from sqlalchemy import Column, Integer, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from .base import Base


# Define an enumeration for permission types
class PermissionType(str, enum.Enum):
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    # Additional permission levels can be added here as needed


class Permission(Base):
    __tablename__ = "permissions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    knowledge_base_id = Column(Integer, ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False)
    permission_type = Column(Enum(PermissionType), nullable=False)

    # Ensure one permission record per user per knowledge base (no duplicate entries)
    __table_args__ = (UniqueConstraint("user_id", "knowledge_base_id", name="_user_kb_uc"),)

    # Relationships
    user = relationship("User", back_populates="permissions")
    knowledge_base = relationship("KnowledgeBase", back_populates="permissions")

    def __repr__(self):
        return f"<Permission user={self.user_id} kb={self.knowledge_base_id} type={self.permission_type.value}>"
