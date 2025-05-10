from ragnarok_server.rdb.engine import get_async_session
from ragnarok_server.rdb.models import Pipeline
from sqlalchemy import select


class PipelineRepository:
    @classmethod
    async def create_pipeline(cls, pipeline: Pipeline) -> Pipeline:
        async with get_async_session() as session:
            session.add(pipeline)
            return pipeline

    @classmethod
    async def get_pipeline_by_id(cls, id: int) -> Pipeline:
        async with get_async_session() as session:
            stmt = select(Pipeline).where(Pipeline.id == id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
