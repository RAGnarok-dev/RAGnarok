import urllib.parse
from contextlib import asynccontextmanager

from ragnarok_core.vector_database import init_vector_database
from ragnarok_server.rdb.models import Base
from ragnarok_toolkit import config
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

DATABASE_URL = (
    f"postgresql+asyncpg://{config.RDB_USERNAME}:{urllib.parse.quote(config.RDB_PASSWORD)}@"
    f"{config.RDB_HOST}:{config.RDB_PORT}/{config.RDB_DATABASE_NAME}"
)

# Create an asynchronous engine
async_engine = create_async_engine(DATABASE_URL, echo=True)

# Create an async session factory
async_session = async_sessionmaker(async_engine, expire_on_commit=False)


async def init_rdb():
    sql_engine = create_async_engine(DATABASE_URL, echo=True, pool_pre_ping=True)
    async with sql_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # init qdrant
    await init_vector_database()


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
