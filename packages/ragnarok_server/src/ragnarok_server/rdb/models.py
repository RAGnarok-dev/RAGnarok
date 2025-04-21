import enum
from sqlalchemy import (
    Boolean,
    Integer,
    String,
    Enum as SQLEnum,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


class Tenant(Base):
    """
    Tenant: the top‑level isolation unit (represents an organization or company).
    Fields:
      - id: PK
      - name: tenant name
      - email: tenant admin email
      - password_hash: login password hash
      - is_active: whether the tenant is enabled
    """
    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class User(Base):
    """
    User: can belong to a tenant or be cross‑tenant/system admin.
    Fields:
      - id: PK
      - username, email, password_hash, is_active
      - tenant_id: FK → tenants.id (nullable)
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # tenant_id: FK → tenants.id
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=True)


class KnowledgeBase(Base):
    """
    KnowledgeBase: a resource owned by either a tenant or a user.
    Fields:
      - id: PK
      - title, description
      - owner_type: "user" or "tenant"
      - tenant_id: FK → tenants.id (nullable)
    """
    __tablename__ = "knowledge_bases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    owner_type: Mapped[str] = mapped_column(String, nullable=False)

    # tenant_id: FK → tenants.id
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=True)


class PermissionType(enum.Enum):
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


class Permission(Base):
    """
    Permission: associates a user and tenant context with a knowledge base and grants actions.
    Fields:
      - id: PK
      - user_id: FK → users.id
      - tenant_id: FK → tenants.id
      - knowledge_base_id: FK → knowledge_bases.id
      - entity_type: int code for resource type
      - permission_type: one of "read", "write", "admin"
    """
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # user_id: FK → users.id
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    # tenant_id: FK → tenants.id
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False)
    # knowledge_base_id: FK → knowledge_bases.id
    knowledge_base_id: Mapped[int] = mapped_column(Integer, nullable=False)

    entity_type: Mapped[int] = mapped_column(Integer, nullable=False)
    permission_type: Mapped[PermissionType] = mapped_column(SQLEnum(PermissionType), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "knowledge_base_id", name="_user_kb_uc"),
    )
