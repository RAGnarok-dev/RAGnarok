from ragnarok_toolkit.model.embedding_model import EmbeddingModelEnum
from ragnarok_toolkit.vdb.qdrant_client import QdrantClient


# init vector database
async def init_vector_database():
    for model in EmbeddingModelEnum:
        model_info = model.value
        await QdrantClient.init_collection(model_info["name"], model_info["dim"])
