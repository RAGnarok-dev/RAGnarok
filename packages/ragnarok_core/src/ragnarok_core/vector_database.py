from ragnarok_core.components.official_components.embedding_component import (
    EmbeddingModelEnum,
)
from ragnarok_toolkit.vdb.qdrant_client import QdrantClient


# init vector database
async def init_vector_database():
    for model in EmbeddingModelEnum:
        model_info = model.value
        await QdrantClient.init_collection(model_info["name"], model_info["dim"])
