import numpy as np
import pytest
from ragnarok_toolkit.vdb import vdb_client
from ragnarok_toolkit.vdb.vdb_base import VdbBase
from ragnarok_toolkit.vdb_qdrant import PayloadIndex, VdbPoint, VdbQdrant

vdb = VdbQdrant("qdrant_test")


@pytest.mark.asyncio
async def test_vdb_connection():
    # docker run -p 6333:6333 qdrant/qdrant:latest
    print(await vdb_client.get_collections())


@pytest.mark.asyncio
async def test_vdb_base():
    vdb_base = VdbBase("vdb_b")
    assert vdb_base.name == "vdb_b"


@pytest.mark.asyncio
async def test_vdb_init_collection():
    await vdb.init_collection(dim=10, distance_map="COSINE")


@pytest.mark.asyncio
async def test_delete_collection():
    await vdb.delete_collection()


@pytest.mark.asyncio
async def test_vdb_create_pyload_indexes():
    await vdb.create_pyload_indexes(
        payload_indexes=[
            PayloadIndex(filed_name="role", field_schema="keyword"),
            PayloadIndex(filed_name="doc_id", field_schema="integer"),
        ]
    )


@pytest.mark.asyncio
async def test_vdb_insert_vectors():
    vectors = [np.random.rand(10).tolist() for _ in range(15)]
    await vdb.insert_vectors(
        points=[
            VdbPoint(id=idx, vector=vector, payload={"role": "test", "doc_id": idx // 5})
            for idx, vector in enumerate(vectors)
        ]
    )


@pytest.mark.asyncio
async def test_vdb_search_vectors():
    vectors = [np.random.rand(10).tolist() for _ in range(10)]
    result = await vdb.search_vectors(
        query_vector=vectors[0],
        top_k=10,
        payload_filters=[
            {"role": "test", "doc_id": 0},
            {"role": "test", "doc_id": 1},
        ],
    )
    print(result)


@pytest.mark.asyncio
async def test_vdb_delete_vectors():
    await vdb.delete_vectors(ids=[0, 1, 2])


@pytest.mark.asyncio
async def test_vdb_delete_vectors_by_payload():
    await vdb.delete_vectors_by_payload(payload_filters=[{"role": "test", "doc_id": 0}])
