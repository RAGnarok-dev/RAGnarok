import pytest
from ragnarok_server.rdb.models import Pipeline
from ragnarok_server.rdb.repositories.pipeline import PipelineRepository


@pytest.mark.asyncio
async def test_create_pipeline():
    pipeline = Pipeline(
        name="test_pipeline",
        tenant_id=123,
        content="111",
    )
    res = await PipelineRepository.create_pipeline(pipeline)
    assert res.id != 0
