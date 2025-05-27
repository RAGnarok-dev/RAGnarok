import logging

from ragnarok_toolkit.odb.minio_client import MinioClient

logger = logging.getLogger(__name__)


class ODBService:
    odb_service: MinioClient

    def __init__(self):
        self.odb_service = MinioClient()

    async def check_file_exists(self, bucket_name: str, key: str) -> bool:
        return await self.odb_service.check_file_exists(bucket_name, key)

    async def create_bucket(self, bucket_name: str):
        await self.odb_service.create_bucket(bucket_name)

    async def list_buckets(self):
        return await self.odb_service.list_buckets()

    async def upload_file(self, bucket_name: str, key: str, content: bytes):
        await self.odb_service.upload_object(bucket_name, key, content)

    async def delete_object(self, bucket_name: str, key: str):
        await self.odb_service.delete_object(bucket_name, key)

    async def download_file(self, bucket_name: str, key: str) -> bytes:
        return await self.odb_service.download_object(bucket_name, key)

    async def delete_bucket(self, bucket_name: str):
        await self.odb_service.delete_bucket(bucket_name)


odb_service = ODBService()
