import logging
import socket

import pytest
from ragnarok_core.components.official_components.object_database_component import (
    StoreODB,
)
from ragnarok_core.components.official_components.vector_database_component import (
    RetrieveComponent,
    StoreVDB,
)
from ragnarok_core.pipeline.pipeline_entity import PipelineEntity
from ragnarok_core.pipeline.pipeline_node import PipelineNode
from ragnarok_toolkit.odb.minio_client import MinioClient
from ragnarok_toolkit.vdb.qdrant_client import QdrantClient

logger = logging.getLogger(__name__)
minio_client = MinioClient()
qdrant_client = QdrantClient()


# 尝试连本地端口，判断服务是否存在
def is_qdrant_running():
    try:
        socket.create_connection(("localhost", 6333), timeout=1)
        return True
    except OSError:
        return False


def is_minio_running():
    try:
        socket.create_connection(("localhost", 9000), timeout=1)
        return True
    except OSError:
        return False


@pytest.mark.skipif(not is_qdrant_running(), reason="Qdrant service not running on localhost:6333")
@pytest.mark.asyncio
async def test_store_vdb():
    try:
        await qdrant_client.init_collection("test_vdb", dim=10)
    except Exception as e:
        print(e)
        pass
    node1 = PipelineNode(node_id="1", component=StoreVDB, forward_node_info=())
    pipeline = PipelineEntity(
        {
            "1": node1,
        },
        {
            "name_input": ("1", "vector_database_name"),
            "points_input": ("1", "vector_points"),
        },
    )
    print("\n\n")
    async for output in pipeline.run_async(
        name_input="test_vdb",
        points_input=[
            {
                "id": 1,
                "vector": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
                "payload": {"db_id": "1", "doc_id": "1", "piece_id": "1"},
            },
            {
                "id": 2,
                "vector": [1, 1, 2, 3, 4, 5, 6, 7, 8, 9],
                "payload": {"db_id": "1", "doc_id": "1", "piece_id": "2"},
            },
        ],
    ):
        logger.info(output)


@pytest.mark.skipif(not is_qdrant_running(), reason="Qdrant service not running on localhost:6333")
@pytest.mark.asyncio
async def test_vdb_retrieval():
    node1 = PipelineNode(node_id="1", component=RetrieveComponent, forward_node_info=())
    pipeline = PipelineEntity(
        {
            "1": node1,
        },
        {
            "vdb_name": ("1", "vector_database_name"),
            "query_vector": ("1", "query_vector"),
            "top_k": ("1", "top_k"),
            "payload_filters": ("1", "payload_filters"),
        },
    )
    print("\n\n")
    async for output in pipeline.run_async(
        vdb_name="test_vdb",
        query_vector=[1, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        top_k=2,
        payload_filters=[
            {
                "db_id": "1",
                "doc_id": "1",
            }
        ],
    ):
        print(output)


@pytest.mark.skipif(not is_minio_running(), reason="Minio service not running on localhost:9000")
@pytest.mark.asyncio
async def test_store_odb():
    await minio_client.create_bucket("test-odb")
    node1 = PipelineNode(node_id="1", component=StoreODB, forward_node_info=())
    pipeline = PipelineEntity(
        {
            "1": node1,
        },
        {
            "bucket_name": ("1", "bucket_name"),
            "object_key": ("1", "object_key"),
            "content_bytes": ("1", "content_bytes"),
        },
    )

    print("\n\n")
    async for output in pipeline.run_async(
        bucket_name="test-odb", object_key="object_key", content_bytes=b"content_bytes"
    ):
        print(output)
