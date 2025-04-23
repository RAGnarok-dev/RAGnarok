from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

# TODO: Store the DATABASE_URL in an environment variable for security.
DATABASE_URL = "postgresql+asyncpg://postgres:123456@172.21.166.159:5432/RAGnarok"

# Create an asynchronous engine
async_engine = create_async_engine(DATABASE_URL, echo=True)

# Create an async session factory
async_session = async_sessionmaker(async_engine, expire_on_commit=False)


@asynccontextmanager
async def get_async_session():
    session = async_session()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
