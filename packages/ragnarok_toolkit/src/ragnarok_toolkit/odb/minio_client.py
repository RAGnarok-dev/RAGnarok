import logging

from aiobotocore.session import get_session
from ragnarok_toolkit import config

logger = logging.getLogger(__name__)


class MinioClient:
    session = get_session()

    @classmethod
    async def _create_client(cls):
        return cls.session.create_client(
            "s3",
            endpoint_url=config.ODB_ENDPOINT,
            aws_access_key_id=config.ODB_ACCESS_KEY,
            aws_secret_access_key=config.ODB_SECRET_KEY,
        )

    @classmethod
    async def create_bucket(cls, bucket_name: str):
        async with await cls._create_client() as minio_client:
            existing_buckets = await minio_client.list_buckets()
            bucket_names = [bucket["Name"] for bucket in existing_buckets["Buckets"]]

            if bucket_name in bucket_names:
                logger.info(f"Bucket '{bucket_name}' already exists.")
            else:
                await minio_client.create_bucket(Bucket=bucket_name)
                logger.info(f"Bucket '{bucket_name}' created.")

    @classmethod
    async def delete_bucket(cls, bucket_name: str):
        async with await cls._create_client() as minio_client:
            await minio_client.delete_bucket(Bucket=bucket_name)
            logger.info(f"Bucket '{bucket_name}' deleted.")

    @classmethod
    async def list_buckets(cls):
        async with await cls._create_client() as minio_client:
            buckets = await minio_client.list_buckets()
            return buckets

    @classmethod
    async def upload_object(cls, bucket_name: str, key: str, data: bytes, metadata: dict = None):
        async with await cls._create_client() as minio_client:
            kwargs = {"Bucket": bucket_name, "Key": key, "Body": data}
            if metadata:
                kwargs["Metadata"] = metadata
            await minio_client.put_object(**kwargs)
            logger.info(f"Uploaded {key} to {bucket_name}")

    @classmethod
    async def download_object(cls, bucket_name: str, key: str) -> bytes:
        async with await cls._create_client() as minio_client:
            response = await minio_client.get_object(Bucket=bucket_name, Key=key)
            return {"content": await response["Body"].read(), "metadata": response.get("Metadata", {})}

    @classmethod
    async def delete_object(cls, bucket_name: str, key: str):
        async with await cls._create_client() as minio_client:
            await minio_client.delete_object(Bucket=bucket_name, Key=key)
            logger.info(f"Deleted {key} from {bucket_name}")

    @classmethod
    async def check_file_exists(cls, bucket_name: str, key: str) -> bool:
        async with await cls._create_client() as minio_client:
            response = await minio_client.head_object(Bucket=bucket_name, Key=key)
            return response is not None
