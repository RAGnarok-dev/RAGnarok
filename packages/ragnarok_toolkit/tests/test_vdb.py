import pytest
from ragnarok_toolkit.vdb import vdb_client
import socket
# 尝试连本地端口，判断服务是否存在
def is_qdrant_running():
    try:
        socket.create_connection(("localhost", 6333), timeout=1)
        return True
    except OSError:
        return False
@pytest.mark.skipif(not is_qdrant_running(), reason="Qdrant service not running on localhost:6333")
@pytest.mark.asyncio
async def test_vdb_connection():
    print(await vdb_client.get_collections())
