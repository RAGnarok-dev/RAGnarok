from typing import Any, Dict, List, Optional, Tuple

from ragnarok_core.vector_database import qdrant_client
from ragnarok_toolkit.component import (
    ComponentInputTypeOption,
    ComponentIOType,
    ComponentOutputTypeOption,
    RagnarokComponent,
)
from ragnarok_toolkit.vdb.qdrant_client import QdrantPoint, SearchPayloadDict


class StoreVDB(RagnarokComponent):
    DESCRIPTION: str = "Store embeddings into vector database"
    ENABLE_HINT_CHECK: bool = True

    @classmethod
    def input_options(cls) -> Tuple[ComponentInputTypeOption, ...]:
        return (
            ComponentInputTypeOption(
                name="vector_database_name",
                allowed_types={ComponentIOType.STRING},
                required=True,
            ),
            ComponentInputTypeOption(
                name="vector_points",
                allowed_types={ComponentIOType.VEC_POINT_LIST},
                required=True,
            ),
        )

    @classmethod
    def output_options(cls) -> Tuple[ComponentOutputTypeOption, ...]:
        return ()

    @classmethod
    async def execute(cls, vector_database_name: str, vector_points: List[QdrantPoint]) -> Dict[str, Any]:
        await qdrant_client.insert_vectors(vector_database_name, vector_points)
        return {}


class RetrieveComponent(RagnarokComponent):
    DESCRIPTION: str = "Retrieve embeddings in vector database"
    ENABLE_HINT_CHECK: bool = True

    @classmethod
    def input_options(cls) -> Tuple[ComponentInputTypeOption, ...]:
        return (
            ComponentInputTypeOption(
                name="vector_database_name",
                allowed_types={ComponentIOType.STRING},
                required=True,
            ),
            ComponentInputTypeOption(
                name="query_vector",
                allowed_types={ComponentIOType.FLOAT_LIST},
                required=True,
            ),
            ComponentInputTypeOption(
                name="top_k",
                allowed_types={ComponentIOType.INT},
                required=False,
            ),
            ComponentInputTypeOption(
                name="payload_filters",
                allowed_types={ComponentIOType.SEARCH_PAYLOAD_DICT_LIST},
                required=False,
            ),
        )

    @classmethod
    def output_options(cls) -> Tuple[ComponentOutputTypeOption, ...]:
        return (ComponentOutputTypeOption(name="piece_ids", type=ComponentIOType.STRING_LIST),)

    @classmethod
    async def execute(
        cls,
        vector_database_name: str,
        query_vector: List[float],
        top_k: Optional[int],
        payload_filters: Optional[List[SearchPayloadDict]],
    ) -> Dict[str, Any]:
        piece_ids = await qdrant_client.search_vectors(
            name=vector_database_name,
            query_vector=query_vector,
            top_k=10 if top_k is None else top_k,
            payload_filters=payload_filters,
        )
        return {"piece_ids": piece_ids}
