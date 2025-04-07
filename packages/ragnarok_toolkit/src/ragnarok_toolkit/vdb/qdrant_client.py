from typing import Literal, Optional, TypedDict

from qdrant_client import AsyncQdrantClient, models
from qdrant_client.models import Distance, PayloadSchemaType


class PayloadDict(TypedDict):
    db_id: str
    doc_id: str
    piece_id: str


class SearchPayloadDict(TypedDict, total=False):
    db_id: str
    doc_id: str


class QdrantPoint(TypedDict):
    id: int
    vector: list[float]
    payload: PayloadDict


class PayloadIndex(TypedDict):
    filed_name: str
    field_schema: Literal["keyword", "integer", "float", "bool", "geo", "datetime", "text", "uuid"]


DISTANCE_TYPE_MAP = {
    "COSINE": Distance.COSINE,
    "DOT": Distance.DOT,
    "EUCLID": Distance.EUCLID,
}

SCHEMA_TYPE_MAP = {
    "keyword": PayloadSchemaType.KEYWORD,
    "integer": PayloadSchemaType.INTEGER,
    "float": PayloadSchemaType.FLOAT,
    "bool": PayloadSchemaType.BOOL,
    "geo": PayloadSchemaType.GEO,
    "datetime": PayloadSchemaType.DATETIME,
    "text": PayloadSchemaType.TEXT,
    "uuid": PayloadSchemaType.UUID,
}


class QdrantClient:
    """
    Vector database using qdrant
    """

    qdrant_client = AsyncQdrantClient(url="http://localhost:6333")

    @classmethod
    async def init_collection(cls, name: str, dim: int, distance_map: str = "COSINE") -> None:
        """
        Initialize the collection
        Args:
            name: name of the collection
            dim (int): Dimension of the vector
            distance_map (str): Distance metric to use, default is "COSINE"
        Returns:
            None
        """
        exists = await cls.qdrant_client.collection_exists(collection_name=name)

        if exists:
            raise Exception(f"Collection '{name}' already exists.")

        await cls.qdrant_client.create_collection(
            collection_name=name,
            vectors_config=models.VectorParams(
                size=dim,
                distance=DISTANCE_TYPE_MAP[distance_map],
            ),
        )

        # create pyload indexes
        payload_indexes = [
            PayloadIndex(filed_name="db_id", field_schema="keyword"),
            PayloadIndex(filed_name="doc_id", field_schema="keyword"),
            PayloadIndex(filed_name="piece_id", field_schema="keyword"),
        ]
        await cls.create_pyload_indexes(name=name, payload_indexes=payload_indexes)

    @classmethod
    async def get_collection(cls, name: str):
        collection_info = await cls.qdrant_client.get_collection(collection_name=name)
        if collection_info is None:
            raise Exception(f"Collection '{name}' not found.")
        return collection_info

    @classmethod
    async def delete_collection(cls, name: str) -> None:
        """
        Delete the collection
        """
        exists = await cls.qdrant_client.collection_exists(collection_name=name)
        if not exists:
            raise Exception(f"Collection '{name}' doesn't exists.")

        await cls.qdrant_client.delete_collection(collection_name=name)

    @classmethod
    async def create_pyload_indexes(cls, name: str, payload_indexes: list[PayloadIndex]) -> None:
        """
        Create a payload index
        Args:
            name: name of the collection
            payload_indexes (list[PayloadIndex]) : List of payload indexes to create
        Returns:
            None
        """
        for payload_index in payload_indexes:
            await cls.qdrant_client.create_payload_index(
                collection_name=name,
                field_name=payload_index["filed_name"],
                field_schema=SCHEMA_TYPE_MAP[payload_index["field_schema"]],
            )

    @classmethod
    async def insert_vectors(cls, name: str, points: list[QdrantPoint]) -> None:
        """
        Insert vectors into the collection
        Args:
            name: name of the collection
            points (list[VdbPoint]): Vectors to insert
        Returns:
            None
        """
        await cls.qdrant_client.upsert(
            collection_name=name,
            points=[
                models.PointStruct(
                    id=point["id"],
                    vector=point["vector"],
                    payload=point["payload"],
                )
                for point in points
            ],
        )

    @classmethod
    async def search_vectors(
        cls,
        name: str,
        query_vector: list[float],
        top_k: int = 10,
        payload_filters: Optional[list[SearchPayloadDict]] = None,
    ):
        """
        Search for vectors in the collection
        Args:
            name: name of the collection
            query_vector (list[float]): Query vector
            top_k (int): Number of results to return
            payload_filters (list[dict]): Payload to filter
        Returns:
            list[str]: List of piece_id that results belong to
        """
        search_result = await cls.qdrant_client.query_points(
            collection_name=name,
            query=query_vector,
            limit=top_k,
            query_filter=models.Filter(
                should=[
                    models.Filter(
                        must=[
                            models.FieldCondition(key=key, match=models.MatchValue(value=value))
                            for key, value in payload_filter.items()
                        ]
                    )
                    for payload_filter in (payload_filters or [])
                ]
            ),
        )

        piece_ids = []
        for point in search_result.points:
            piece_ids.append(point.payload["piece_id"])
        return piece_ids

    @classmethod
    async def delete_vectors(cls, name: str, ids: list[int]) -> None:
        """
        Delete a vector from the collection
        Args:
            name: name of the collection
            ids (int): ID of the vector to delete
        Returns:
            None
        """
        await cls.qdrant_client.delete(collection_name=name, points_selector=ids)

    @classmethod
    async def delete_vectors_by_payload(cls, name: str, payload_filters: list[SearchPayloadDict]) -> None:
        """
        Delete vectors from the collection by payload with AND logic
        Args:
            name: name of the collection
            payload_filters (list[dict]): Payload to delete
        Returns:
            None
        Example:
            delete_vectors_by_payload([
                {
                    "db_id": '1',
                    "doc_id": '18'
                },
                {
                    "db_id": '2',
                    "doc_id": '4'
                }
            ])
            will delete all vectors with (db_id='1' and doc_id='18') or (db_id='2' and doc_id='4')
        """
        await cls.qdrant_client.delete(
            collection_name=name,
            points_selector=models.Filter(
                should=[
                    models.Filter(
                        must=[
                            models.FieldCondition(key=key, match=models.MatchValue(value=value))
                            for key, value in payload_filter.items()
                        ]
                    )
                    for payload_filter in payload_filters
                ]
            ),
        )
