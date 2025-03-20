from typing import Literal, Optional, TypedDict

from qdrant_client import models
from qdrant_client.models import Distance, PayloadSchemaType
from ragnarok_toolkit.vdb import vdb_client
from ragnarok_toolkit.vdb.vdb_base import VdbBase


class VdbPoint(TypedDict):
    id: int
    vector: list[float]
    payload: Optional[dict]


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


class VdbQdrant(VdbBase):
    """
    Vector database using qdrant
    """

    def __init__(self, name: str) -> None:
        super().__init__(name)

    async def init_collection(self, dim: int, distance_map: str = "COSINE") -> None:
        """
        Initialize the collection
        Args:
            dim (int): Dimension of the vector
            distance_map (str): Distance metric to use, default is "COSINE"
        Returns:
            None
        """
        try:
            await vdb_client.create_collection(
                collection_name=self.name,
                vectors_config=models.VectorParams(
                    size=dim,
                    distance=DISTANCE_TYPE_MAP[distance_map],
                ),
            )
        except Exception as e:
            raise ValueError(f"Collection {self.name} already exists.") from e

    async def delete_collection(self) -> None:
        """
        Delete the collection
        Returns:
            None
        """
        try:
            await vdb_client.delete_collection(collection_name=self.name)
        except Exception as e:
            raise ValueError(f"Collection {self.name} does not exist.") from e

    async def create_pyload_indexes(self, payload_indexes: list[PayloadIndex]) -> None:
        """
        Create a payload index
        Args:
            payload_indexes (list[PayloadIndex]) : List of payload indexes to create
        Returns:
            None
        """
        for payload_index in payload_indexes:
            try:
                await vdb_client.create_payload_index(
                    collection_name=self.name,
                    field_name=payload_index["filed_name"],
                    field_schema=SCHEMA_TYPE_MAP[payload_index["field_schema"]],
                )
            except Exception as e:
                raise ValueError(f"Failed to create payload index of {payload_index['filed_name']}") from e

    async def insert_vectors(self, points: list[VdbPoint]) -> None:
        """
        Insert vectors into the collection
        Args:
            points (list[VdbPoint]): Vectors to insert
        Returns:
            None
        """
        try:
            await vdb_client.upsert(
                collection_name=self.name,
                points=[
                    models.PointStruct(
                        id=point["id"],
                        vector=point["vector"],
                        payload=point["payload"],
                    )
                    for point in points
                ],
            )
        except Exception as e:
            raise ValueError(f"Failed to insert vectors into collection {self.name}.") from e

    async def search_vectors(
        self, query_vector: list[float], top_k: int = 10, payload_filters: Optional[list[dict]] = None
    ):
        """
        Search for vectors in the collection
        Args:
            query_vector (list[float]): Query vector
            top_k (int): Number of results to return
            payload_filters (list[dict]): Payload to filter
        Returns:
            list[list[float]]: List of vectors
        """
        try:
            search_result = await vdb_client.query_points(
                collection_name=self.name,
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

            return search_result
        except Exception as e:
            raise ValueError(f"Failed to search vectors in collection {self.name}.") from e

    async def delete_vectors(self, ids: list[int]) -> None:
        """
        Delete a vector from the collection
        Args:
            ids (int): ID of the vector to delete
        Returns:
            None
        """
        try:
            await vdb_client.delete(collection_name=self.name, points_selector=ids)
        except Exception as e:
            raise ValueError(f"Failed to delete vector from collection {self.name}.") from e

    async def delete_vectors_by_payload(self, payload_filters: list[dict]) -> None:
        """
        Delete vectors from the collection by payload with AND logic
        Args:
            payload_filters (list[dict]): Payload to delete
        Returns:
            None
        Example:
            delete_vectors_by_payload([
                {
                    "role": "admin",
                    "age": 18
                },
                {
                    "role": "user1"
                    "age": 18
                }
            ])
            will delete all vectors with (role=admin and age=18) or (role=user1 and age=18)
        """
        try:
            await vdb_client.delete(
                collection_name=self.name,
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
        except Exception as e:
            raise ValueError(f"Failed to delete vectors from collection {self.name}.") from e

    # async def insert_vector(self, v_id:int, vector:list[float], payload:Optional[dict] = None) -> None:
    #     """
    #     Insert a vector into the collection
    #     Args:
    #         v_id (int): ID of the vector
    #
    #         vector (list[float]): Vector to insert
    #         payload (dict): Payload to insert
    #     Returns:
    #         None
    #     """
    #
    #     try:
    #         await vdb_client.upsert(
    #             collection_name=self.name,
    #             points=[
    #                 models.PointStruct(
    #                     id=v_id,
    #                     vector=vector,
    #                     payload=payload,
    #                 )
    #             ]
    #         )
    #     except Exception as e:
    #         raise ValueError(f"Failed to insert vector into collection {self.name}.") from e
