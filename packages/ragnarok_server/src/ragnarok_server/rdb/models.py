from enum import Enum

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Sequence,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# from sqlalchemy import Sequnce


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
    avatar_url: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_1280.png",  # 默认头像URL
        server_default="https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_1280.png"  # 数据库层面默认值
    )


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
    avatar_url: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_1280.png",  # 默认头像URL
        server_default="https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_1280.png"
        # 数据库层面默认值
    )


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
    embedding_model_name: Mapped[str] = mapped_column(String, nullable=False)
    split_type: Mapped[str] = mapped_column(String, nullable=False)
    root_file_id: Mapped[str] = mapped_column(String, nullable=False)

    principal_id: Mapped[int] = mapped_column(Integer, nullable=False)
    principal_type: Mapped[str] = mapped_column(String, nullable=False)


class LLMSession(Base):
    """
    LLMSession: stores the LLM conversation history for a user or tenant.
    Fields:
      - id: PK
      - title: optional title for the session
      - created_by: 'user-{user_id}' or 'tenant-{tenant_id}'
      - history: conversation history stored as dict (JSON)
      - created_at: timestamp when session was created
      - updated_at: timestamp when session was last updated
    """

    __tablename__ = "llm_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    created_by: Mapped[str] = mapped_column(String, nullable=False, index=True)
    history: Mapped[dict] = mapped_column(JSON, nullable=False)

    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )


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
    # principal_type: "tenant" or "user"
    principal_type: Mapped[str] = mapped_column(String, nullable=False)

    # knowledge_base_id: FK → knowledge_bases.id
    knowledge_base_id: Mapped[int] = mapped_column(Integer, nullable=False)

    # permission_type: "read", "write", or "admin"
    permission_type: Mapped[str] = mapped_column(String, nullable=False)

    __table_args__ = (
        # ensure each principal only has one record per KB
        UniqueConstraint("principal_id", "principal_type", "knowledge_base_id", name="_principal_kb_uc"),
    )


class Pipeline(Base):
    __tablename__ = "pipelines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    principal_id:   Mapped[int]  = mapped_column(Integer, nullable=False)
    principal_type: Mapped[str]  = mapped_column(String,  nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    avatar: Mapped[str | None] = mapped_column(String, nullable=True)
    params: Mapped[str | None] = mapped_column(String, nullable=True)
    components: Mapped[str | None] = mapped_column(String, nullable=True)
    path:       Mapped[str | None] = mapped_column(String, nullable=True)

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
    principal_id: Mapped[int] = mapped_column(Integer, nullable=False)
    # principal_type: "tenant" or "user"
    principal_type: Mapped[str] = mapped_column(String, nullable=False)

    chunk_size: Mapped[int] = mapped_column(Integer, nullable=False)

    parent_id: Mapped[str] = mapped_column(String, ForeignKey("files.id", ondelete="CASCADE"), nullable=True)

    knowledge_base_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False
    )
