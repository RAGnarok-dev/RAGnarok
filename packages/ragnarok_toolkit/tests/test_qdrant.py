import numpy as np
import pytest
from ragnarok_toolkit.vdb.qdrant_client import (
    QdrantClient,
    QdrantPoint,
    SearchPayloadDict,
)

qdrant_client = QdrantClient()


@pytest.mark.asyncio
async def test_vdb_connection():
    # docker run -p 6333:6333 qdrant/qdrant:latest
    print(await qdrant_client.init_collection(name="test-collection", dim=5))


@pytest.mark.asyncio
async def test_delete():
    await qdrant_client.delete_collection(name="test-collection")


@pytest.mark.asyncio
async def test_get_collection():
    info = await qdrant_client.get_collection(name="test-collection")
    print(info)


@pytest.mark.asyncio
async def test_vdb_insert_vectors():
    vectors = [np.random.rand(5).tolist() for _ in range(15)]
    await qdrant_client.insert_vectors(
        name="test-collection",
        points=[
            QdrantPoint(id=idx, vector=vector, payload={"db_id": "1", "doc_id": str(idx // 5), "piece_id": str(idx)})
            for idx, vector in enumerate(vectors)
        ],
    )


@pytest.mark.asyncio
async def test_vdb_search_vectors():
    vectors = [np.random.rand(5).tolist() for _ in range(10)]
    result = await qdrant_client.search_vectors(
        name="test-collection",
        query_vector=vectors[0],
        top_k=10,
        payload_filters=[
            SearchPayloadDict(db_id="1", doc_id="0"),
            SearchPayloadDict(doc_id="1"),
        ],
    )
    print(result)  # result of pieces_id


@pytest.mark.asyncio
async def test_vdb_delete_vectors():
    await qdrant_client.delete_vectors(name="test-collection", ids=[0, 1, 2])


@pytest.mark.asyncio
async def test_vdb_delete_vectors_by_payload():
    await qdrant_client.delete_vectors_by_payload(
        name="test-collection",
        payload_filters=[
            SearchPayloadDict(db_id="1", doc_id="0"),
        ],
    )
    vectors = [np.random.rand(5).tolist() for _ in range(10)]
    result = await qdrant_client.search_vectors(
        name="test-collection",
        query_vector=vectors[0],
        top_k=10,
        payload_filters=[
            SearchPayloadDict(db_id="1", doc_id="0"),
        ],
    )
    print(result)
