import pytest
from ragnarok_core.components.official_components.convert_component import (
    Chunks2Object,
    Vectors2VecPoints,
)
from ragnarok_core.components.official_components.embedding_component import (
    EmbeddingComponent,
)
from ragnarok_core.components.official_components.object_database_component import (
    StoreODB,
)
from ragnarok_core.components.official_components.text_split_component import (
    TextSplitComponent,
)
from ragnarok_core.components.official_components.vector_database_component import (
    StoreVDB,
)
from ragnarok_core.pipeline.pipeline_entity import PipelineEntity
from ragnarok_core.pipeline.pipeline_node import PipelineNode
from ragnarok_toolkit.odb.minio_client import MinioClient
from ragnarok_toolkit.vdb.qdrant_client import QdrantClient

minio_client = MinioClient()
qdrant_client = QdrantClient()


@pytest.mark.asyncio
async def test_create_test_db():
    await minio_client.create_bucket("test-bucket")
    await qdrant_client.init_collection("test_vdb", 384)


@pytest.mark.asyncio
async def test_split2database():
    connection1 = PipelineNode.NodeConnection(
        from_node_id="1",
        to_node_id="2",
        from_node_output_name="text_chunks",
        to_node_input_name="text_chunks",
    )
    connection2 = PipelineNode.NodeConnection(
        from_node_id="2",
        to_node_id="3",
        from_node_output_name="chunk_ids",
        to_node_input_name="chunk_ids",
    )
    connection3 = PipelineNode.NodeConnection(
        from_node_id="2",
        to_node_id="3",
        from_node_output_name="chunk_bytes_list",
        to_node_input_name="chunk_bytes_list",
    )

    connection4 = PipelineNode.NodeConnection(
        from_node_id="1",
        to_node_id="4",
        from_node_output_name="text_chunks",
        to_node_input_name="text_chunks",
    )

    connection5 = PipelineNode.NodeConnection(
        from_node_id="4",
        to_node_id="5",
        from_node_output_name="vectors",
        to_node_input_name="vectors",
    )

    connection6 = PipelineNode.NodeConnection(
        from_node_id="5",
        to_node_id="6",
        from_node_output_name="vector_points",
        to_node_input_name="vector_points",
    )

    node1 = PipelineNode(
        node_id="1",
        component=TextSplitComponent,
        forward_node_info=(),
    )

    node2 = PipelineNode(
        node_id="2",
        component=Chunks2Object,
        forward_node_info=(connection1,),
    )

    node3 = PipelineNode(
        node_id="3",
        component=StoreODB,
        forward_node_info=(connection2, connection3),
    )

    node4 = PipelineNode(
        node_id="4",
        component=EmbeddingComponent,
        forward_node_info=(connection4,),
    )

    node5 = PipelineNode(
        node_id="5",
        component=Vectors2VecPoints,
        forward_node_info=(connection5,),
    )
    node6 = PipelineNode(
        node_id="6",
        component=StoreVDB,
        forward_node_info=(connection6,),
    )

    pipeline = PipelineEntity(
        {
            "1": node1,
            "2": node2,
            "3": node3,
            "4": node4,
            "5": node5,
            "6": node6,
        },
        {
            "pdf_path": ("1", "pdf_path"),
            "doc_id_1": ("2", "doc_id"),
            "bucket_name": ("3", "bucket_name"),
            "doc_id_2": ("5", "doc_id"),
            "db_id": ("5", "db_id"),
            "vector_database_name": ("6", "vector_database_name"),
        },
    )

    pdf_test_path = "test_document.pdf"

    async for output in pipeline.run_async(
        pdf_path=pdf_test_path,
        db_id="test_db",
        doc_id_1="test_doc",
        doc_id_2="test_doc",
        vector_database_name="test_vdb",
        bucket_name="test-bucket",
    ):
        print(output)
