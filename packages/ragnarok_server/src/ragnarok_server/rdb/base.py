# base.py - Define the base class and session for SQLAlchemy models
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
# TODO: The DATABASE_URL should be stored in a .env file for security.
DATABASE_URL = "postgresql+asyncpg://postgres:123456@172.21.166.159:5432/RAGnarok"  # PostgreSQL DSN
Base = declarative_base()

# Create Async Engine and Session maker for use in the app and permission checks
async_engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)