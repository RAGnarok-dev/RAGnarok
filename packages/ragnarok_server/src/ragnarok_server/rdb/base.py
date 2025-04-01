# base.py
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from datetime import date, datetime
from sqlalchemy import (
    Date,
    DateTime,
)

# TODO: Store the DATABASE_URL in an environment variable for security.
DATABASE_URL = "postgresql+asyncpg://postgres:123456@172.21.166.159:5432/RAGnarok"

# Create an asynchronous engine
async_engine = create_async_engine(DATABASE_URL, echo=True)

# Create an async session factory
AsyncSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False)


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    # Optionally define type_annotation_map if needed.
    type_annotation_map = {
        datetime: DateTime(),
        date: Date,
    }
