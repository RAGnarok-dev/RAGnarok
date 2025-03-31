import pytest
from sqlalchemy import text
from ragnarok_server.rdb.base import async_engine

@pytest.mark.asyncio
async def test_connection():
    # Try to create a connection and execute a simple query
    async with async_engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        scalar_result = result.scalar()
        # Assert that the query returns 1
        assert scalar_result == 1, f"Expected 1, got {scalar_result}"