from typing import TYPE_CHECKING, Optional
from sqlalchemy import Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

if TYPE_CHECKING:
    from .api_key import APIKey
    from .permission import Permission
    from .tenant import Tenant

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
    api_keys: Mapped[list["APIKey"]] = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="users", foreign_keys=[tenant_id])
    tenant_admin_of: Mapped[Optional["Tenant"]] = relationship(
        "Tenant", back_populates="admin_user", uselist=False, foreign_keys="Tenant.admin_user_id"
    )
    permissions: Mapped[list["Permission"]] = relationship("Permission", back_populates="user")

    def __repr__(self) -> str:
        return f"<User {self.id} username={self.username} tenant={self.tenant_id}>"
