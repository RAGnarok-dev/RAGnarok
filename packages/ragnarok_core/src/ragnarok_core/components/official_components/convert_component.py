from typing import Any, Dict, List, Tuple

from ragnarok_toolkit.component import (
    ComponentInputTypeOption,
    ComponentIOType,
    ComponentOutputTypeOption,
    RagnarokComponent,
)


class Chunks2Object(RagnarokComponent):
    DESCRIPTION: str = "Chunks converted to Object"
    ENABLE_HINT_CHECK: bool = True

    @classmethod
    def input_options(cls) -> Tuple[ComponentInputTypeOption, ...]:
        return (
            ComponentInputTypeOption(
                name="doc_id",
                allowed_types={ComponentIOType.STRING},
                required=True,
            ),
            ComponentInputTypeOption(
                name="text_chunks",
                allowed_types={ComponentIOType.STRING_LIST},
                required=True,
            ),
        )

    @classmethod
    def output_options(cls) -> Tuple[ComponentOutputTypeOption, ...]:
        return (
            ComponentOutputTypeOption(
                name="chunk_ids",
                type=ComponentIOType.STRING_LIST,
            ),
            ComponentOutputTypeOption(
                name="content_bytes_list",
                type=ComponentIOType.BYTES_LIST,
            ),
        )

    @classmethod
    def execute(cls, doc_id: str, text_chunks: List[str]) -> Dict[str, Any]:
        chunk_ids = [f"{doc_id}_{i}" for i in range(len(text_chunks))]
        content_bytes_list = [chunk.encode("utf-8") for chunk in text_chunks]
        return {"chunk_ids": chunk_ids, "content_bytes_list": content_bytes_list}


class Vectors2VecPoints(RagnarokComponent):
    DESCRIPTION: str = "Vectors converted to Vector Points"
    ENABLE_HINT_CHECK: bool = True

    @classmethod
    def input_options(cls) -> Tuple[ComponentInputTypeOption, ...]:
        return (
            ComponentInputTypeOption(
                name="db_id",
                allowed_types={ComponentIOType.STRING},
                required=True,
            ),
            ComponentInputTypeOption(
                name="doc_id",
                allowed_types={ComponentIOType.STRING},
                required=True,
            ),
            ComponentInputTypeOption(
                name="vectors",
                allowed_types={ComponentIOType.FLOAT_LIST_LIST},
                required=True,
            ),
        )

    @classmethod
    def output_options(cls) -> Tuple[ComponentOutputTypeOption, ...]:
        return (
            ComponentOutputTypeOption(
                name="vector_points",
                type=ComponentIOType.VEC_POINT_LIST,
            ),
        )

    @classmethod
    def execute(cls, db_id: str, doc_id: str, vectors: List[List[float]]) -> Dict[str, Any]:
        vector_points = [
            {
                "id": f"{db_id}_{doc_id}_{i}",
                "vector": vector,
                "payload": {"db_id": db_id, "doc_id": doc_id, "chunk_id": f"{doc_id}_{i}"},
            }
            for i, vector in enumerate(vectors)
        ]
        return {"vector_points": vector_points}
