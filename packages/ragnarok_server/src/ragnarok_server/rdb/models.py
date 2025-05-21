from enum import Enum

from ragnarok_toolkit.common import PermissionType, PrincipalType
from sqlalchemy import Boolean
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Integer, Sequence, String, UniqueConstraint
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


class EmbeddingModel(Base):
    """
    EmbeddingModel: a model that can be used to embed text.
    Fields:
      - id: PK
      - name: name of the embedding model
      - dimension: dimension of the embedding
    """

    __tablename__ = "embedding_models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    dimension: Mapped[int] = mapped_column(Integer, nullable=False)


class KnowledgeBase(Base):
    """
    KnowledgeBase: a resource owned by either a tenant or a user.
    Fields:
      - id: PK
      - title, description
      - embedding_model: name of the embedding model
      - embedding_dimension: dimension of the embedding

      - created_by: creator by ('tenant-{tenant_id}' or 'user-{user_id}')
    """

    __tablename__ = "knowledge_bases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    embedding_model_id: Mapped[int] = mapped_column(Integer, nullable=False)
    root_file_id: Mapped[str] = mapped_column(String, nullable=False)

    created_by: Mapped[str] = mapped_column(String, nullable=False, index=True)


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


class Pipeline(Base):
    __tablename__ = "pipelines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    avatar: Mapped[str | None] = mapped_column(String, nullable=True)


class CreatorType(str, Enum):
    TENANT = "tenant"
    USER = "user"


class File(Base):
    """
    File: represents a file or folder in the system.
    Fields:
      - id: PK (format: 'file-{id}')
      - name: file name
      - type: file type ('folder' or 'file')
      - size: file size
      - location: file location
      - parent_id: parent file id
      - created_by: creator by ('tenant-{tenant_id}' or 'user-{user_id}')
      - knowledge_base_id: knowledge base id
    """

    __tablename__ = "files"

    id: Mapped[str] = mapped_column(String, Sequence("file_id_seq"), primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    type: Mapped[str] = mapped_column(String, nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    location: Mapped[str] = mapped_column(String, nullable=False)
    created_by: Mapped[str] = mapped_column(String, nullable=False)
    # chunk_count: Mapped[int] = mapped_column(Integer, nullable=False)

    parent_id: Mapped[str] = mapped_column(String, ForeignKey("files.id", ondelete="CASCADE"), nullable=True)

    knowledge_base_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False
    )
