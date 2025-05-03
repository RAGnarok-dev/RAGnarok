from ragnarok_toolkit.common import PermissionType, PrincipalType
from sqlalchemy import Boolean
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Integer, String, UniqueConstraint
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
      - tenant: PK -> tenant
    """

    __tablename__ = "knowledge_bases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)

    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False)


class Permission(Base):
    """
    Permission: grants a specific action on a knowledge base to a principal.
    Fields:
      - id: PK
      - principal_id: reference to a user | tenant
      - principal_type: distinguish user tenant or user kb
      - knowledge_base_id: FK → knowledge_bases.id
      - permission_type: one of "read", "write", "admin"
    """

    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    principal_id: Mapped[int] = mapped_column(Integer, nullable=False)
    principal_type: Mapped[PrincipalType] = mapped_column(SQLEnum(PrincipalType), nullable=False)

    # knowledge_base_id: FK → knowledge_bases.id
    knowledge_base_id: Mapped[int] = mapped_column(Integer, nullable=False)

    # permission_type: "read", "write", or "admin"
    permission_type: Mapped[PermissionType] = mapped_column(SQLEnum(PermissionType), nullable=False)

    __table_args__ = (
        # ensure each principal only has one record per KB
        UniqueConstraint(
            "principal_id", "principal_type", "knowledge_base_id", "permission_type", name="_principal_kb_uc"
        ),
    )
