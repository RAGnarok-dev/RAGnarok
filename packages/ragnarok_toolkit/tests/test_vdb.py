import pytest
from ragnarok_toolkit.vdb import vdb_client


@pytest.mark.asyncio
async def test_vdb_connection():
    print(await vdb_client.get_collections())
