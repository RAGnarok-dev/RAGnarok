import enum
from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    # Optionally define type_annotation_map if needed.
    type_annotation_map = {
        datetime: DateTime(),
        date: Date,
    }


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    tenant_id: Mapped[int] = mapped_column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    is_tenant_admin: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationship to APIKey (one-to-many)
    api_keys: Mapped[List["APIKey"]] = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="users", foreign_keys=[tenant_id])
    tenant_admin_of: Mapped[Optional["Tenant"]] = relationship(
        "Tenant", back_populates="admin_user", uselist=False, foreign_keys="Tenant.admin_user_id"
    )
    permissions: Mapped[List["Permission"]] = relationship("Permission", back_populates="user")

    def __repr__(self) -> str:
        return f"<User {self.id} username={self.username} tenant={self.tenant_id}>"


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    admin_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    admin_user: Mapped[Optional["User"]] = relationship(
        "User", back_populates="tenant_admin_of", foreign_keys=[admin_user_id], uselist=False
    )
    users: Mapped[List["User"]] = relationship("User", back_populates="tenant", foreign_keys="User.tenant_id")
    knowledge_bases: Mapped[List["KnowledgeBase"]] = relationship("KnowledgeBase", back_populates="tenant")

    def __repr__(self) -> str:
        return f"<Tenant {self.id} name={self.name}>"


class PermissionType(str, enum.Enum):
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
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


class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    tenant_id: Mapped[int] = mapped_column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="knowledge_bases")
    permissions: Mapped[List["Permission"]] = relationship("Permission", back_populates="knowledge_base")

    def __repr__(self) -> str:
        return f"<KnowledgeBase {self.id} title={self.title} tenant={self.tenant_id}>"


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
