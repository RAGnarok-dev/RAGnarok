import logging
from typing import List

from ragnarok_core.components.official_components.embedding_component import (
    EmbeddingComponent,
)
from ragnarok_core.components.official_components.text_split_component import (
    SplitType,
    TextSplitComponent,
)
from ragnarok_toolkit.odb.minio_client import MinioClient
from ragnarok_toolkit.vdb.qdrant_client import QdrantClient, QdrantPoint

logger = logging.getLogger(__name__)


class StoreService:
    minio_client: MinioClient
    qdrant_client: QdrantClient
    text_split_component: TextSplitComponent
    embedding_component: EmbeddingComponent

    def __init__(self):
        self.minio_client = MinioClient
        self.qdrant_client = QdrantClient
        self.text_split_component = TextSplitComponent
        self.embedding_component = EmbeddingComponent

    # deal with file
    async def store_file(
        self,
        knowledge_base_id: int,
        principal_type: str,
        principal_id: int,
        file_id: str,
        file_type: str,
        content: bytes,
        split_type: str,
        embedding_model_name: str,
    ):

        # split
        split_type = SplitType(split_type)
        chunks = await self._split_text(file_type, content, split_type)

        # embed
        vectors = await self._embed_text(chunks, embedding_model_name)

        # store into odb
        metadata = {
            "file_type": file_type,
            "file_size": str(len(content)),
            "chunk_size": str(len(chunks)),
        }

        await self._upload_file(
            principal_type=principal_type,
            principal_id=principal_id,
            file_id=file_id,
            content=content,
            chunks=chunks,
            metadata=metadata,
        )

        # store into vdb
        points = [
            await self._vector2Point(
                vector=vector, kb_id=knowledge_base_id, file_id=file_id, chunk_id=chunk_id, text=chunk
            )
            for chunk_id, (vector, chunk) in enumerate(zip(vectors, chunks))
        ]
        if len(points) > 0:
            await self._insert_vectors_to_vdb(embedding_model_name, points)

        return len(chunks)

    # ODB
    async def check_file_exists(self, principal_type: str, principal_id: int, file_id: str) -> bool:
        bucket_name = f"{principal_type}-{principal_id}"
        key = f"{file_id}"
        return await self.minio_client.check_file_exists(bucket_name, key)

    async def create_bucket(self, principal_type: str, principal_id: int):
        bucket_name = f"{principal_type}-{principal_id}"
        await self.minio_client.create_bucket(bucket_name)

    async def _upload_file(
        self, principal_type: str, principal_id: int, file_id: str, content: bytes, chunks: List[str], metadata: dict
    ):
        bucket_name = f"{principal_type}-{principal_id}"
        key = f"{file_id}"
        await self.minio_client.upload_object(bucket_name, key, content, metadata)
        for chunk_id, chunk in enumerate(chunks):
            chunk_bytes = chunk.encode("utf-8")
            key = f"{file_id}-{chunk_id}"
            await self.minio_client.upload_object(bucket_name, key, chunk_bytes, metadata)

    async def download_file(self, principal_type: str, principal_id: int, file_id: str) -> bytes:
        bucket_name = f"{principal_type}-{principal_id}"
        key = f"{file_id}"
        object = await self.minio_client.download_object(bucket_name, key)
        return object["content"]

    async def get_chunks(self, principal_type: str, principal_id: int, file_id: str, chunk_size: int) -> List[str]:
        bucket_name = f"{principal_type}-{principal_id}"
        chunks = []
        for chunk_id in range(chunk_size):
            key = f"{file_id}-{chunk_id}"
            object = await self.minio_client.download_object(bucket_name, key)
            chunk_str = object["content"].decode("utf-8")
            chunks.append(chunk_str)
        return chunks

    async def get_chunk_by_id(self, principal_type: str, principal_id: int, file_id: str, chunk_id: int) -> str:
        bucket_name = f"{principal_type}-{principal_id}"
        key = f"{file_id}-{chunk_id}"
        object = await self.minio_client.download_object(bucket_name, key)
        return object["content"].decode("utf-8")

    async def delete_bucket(self, principal_type: str, principal_id: int):
        bucket_name = f"{principal_type}-{principal_id}"
        await self.minio_client.delete_bucket(bucket_name)

    async def delete_object(self, principal_type: str, principal_id: int, file_id: str, chunk_size: int):
        bucket_name = f"{principal_type}-{principal_id}"
        key = f"{file_id}"
        await self.minio_client.delete_object(bucket_name, key)
        for chunk_id in range(chunk_size):
            key = f"{file_id}-{chunk_id}"
            await self.minio_client.delete_object(bucket_name, key)

    # VDB
    async def _insert_vectors_to_vdb(self, embedding_model_name: str, points: List[QdrantPoint]):
        await self.qdrant_client.insert_vectors(embedding_model_name, points)

    async def _vector2Point(self, vector: List[float], kb_id: int, file_id: str, chunk_id: int, text: str):
        pyload = {"db_id": str(kb_id), "doc_id": file_id, "chunk_id": str(chunk_id), "text": text}
        return QdrantPoint(vector=vector, payload=pyload)

    # split
    async def _split_text(self, file_type: str, content: bytes, split_type: SplitType) -> List[str]:
        result = await self.text_split_component.execute(file_type, content, split_type.value)
        return result["text_chunks"]

    # embedding
    async def _embed_text(self, text_chunks: List[str], embedding_model_name: str) -> List[List[float]]:
        # TODO: component should be selected by embedding_model_name
        result = await self.embedding_component.execute(text_chunks)
        return result["vectors"]


store_service = StoreService()
