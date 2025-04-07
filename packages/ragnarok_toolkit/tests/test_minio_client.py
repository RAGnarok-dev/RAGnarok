import pytest
from ragnarok_toolkit.odb.minio_client import MinioClient

minio_client = MinioClient()


@pytest.mark.asyncio
async def test_minio_client():
    await minio_client.create_bucket("test-bucket")
    buckets = await minio_client.list_buckets()
    print(buckets)


@pytest.mark.asyncio
async def test_upload():
    await minio_client.upload_object(bucket_name="test-bucket", key="test-key", data=b"data")
    result = await minio_client.download_object(bucket_name="test-bucket", key="test-key")
    print(result.decode("utf-8"))
