from aiobotocore.session import get_session

# MinIO 服务器配置
MINIO_ENDPOINT = "http://127.0.0.1:9000"
ACCESS_KEY = "fTdBpg4eFpmMWdojeCHO"
SECRET_KEY = "LgkALYBJiQqiPTuQCfs017k7e8QEjrSPCdZLUki1"


class MinioClient:
    # 创建一个 session 和 minio 客户端的类变量（只初始化一次）
    session = get_session()

    @classmethod
    async def _create_client(cls):
        """异步创建 MinIO 客户端"""
        # 使用 async with 来确保客户端正确管理
        return cls.session.create_client(
            "s3",
            endpoint_url=MINIO_ENDPOINT,  # MinIO 服务器地址
            aws_access_key_id=ACCESS_KEY,
            aws_secret_access_key=SECRET_KEY,
        )

    @classmethod
    async def create_bucket(cls, bucket_name: str):
        async with await cls._create_client() as minio_client:

            existing_buckets = await minio_client.list_buckets()
            bucket_names = [bucket["Name"] for bucket in existing_buckets["Buckets"]]

            if bucket_name in bucket_names:
                print(f"Bucket '{bucket_name}' already exists.")
            else:
                await minio_client.create_bucket(Bucket=bucket_name)
                print(f"Bucket '{bucket_name}' created.")

    @classmethod
    async def list_buckets(cls):

        async with await cls._create_client() as minio_client:
            buckets = await minio_client.list_buckets()
            return buckets

    @classmethod
    async def upload_object(cls, bucket_name: str, key: str, data: bytes):
        async with await cls._create_client() as minio_client:
            await minio_client.put_object(Bucket=bucket_name, Key=key, Body=data)
            print(f"Uploaded {key} to {bucket_name}")

    @classmethod
    async def download_object(cls, bucket_name: str, key: str):
        async with await cls._create_client() as minio_client:
            response = await minio_client.get_object(Bucket=bucket_name, Key=key)
            return await response["Body"].read()
