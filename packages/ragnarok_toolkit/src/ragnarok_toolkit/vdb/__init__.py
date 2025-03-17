from qdrant_client import AsyncQdrantClient

vdb_client: AsyncQdrantClient = AsyncQdrantClient(url="http://localhost:6333")
