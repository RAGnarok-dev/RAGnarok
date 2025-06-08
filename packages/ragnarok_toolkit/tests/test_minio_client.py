import logging
import socket

import pytest
from ragnarok_toolkit.odb.minio_client import MinioClient

logger = logging.getLogger(__name__)


# 尝试连本地端口，判断服务是否存在
def is_minio_running():
    try:
        socket.create_connection(("localhost", 9000), timeout=1)
        return True
    except OSError:
        return False


minio_client = MinioClient()


@pytest.mark.skipif(not is_minio_running(), reason="Minio service not running on localhost:9000")
@pytest.mark.asyncio
async def test_minio_client():
    await minio_client.create_bucket("test-bucket")
    buckets = await minio_client.list_buckets()
    print(buckets)


@pytest.mark.skipif(not is_minio_running(), reason="Minio service not running on localhost:9000")
@pytest.mark.asyncio
async def test_upload():
    metadata = {"content-type": "text/plain", "author": "test-user"}
    await minio_client.upload_object(bucket_name="test-bucket", key="test-key", data=b"data", metadata=metadata)
    result = await minio_client.download_object(bucket_name="test-bucket", key="test-key")
    assert result["content"] == b"data"
    assert result["metadata"] == metadata
    logger.info("Content: %s", result["content"].decode("utf-8"))
    logger.info("Metadata: %s", result["metadata"])
