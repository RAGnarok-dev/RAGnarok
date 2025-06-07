from ragnarok_server.rdb.engine import get_async_session
from ragnarok_server.rdb.models import Pipeline
from sqlalchemy import select, delete, update
from typing import Optional, List


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

    @classmethod
    async def remove_pipeline(cls, pipeline_id: int) -> bool:
        async with get_async_session() as session:
            stmt = delete(Pipeline).where(Pipeline.id == pipeline_id)
            result = await session.execute(stmt)
            return result.rowcount > 0

    @classmethod
    async def update_pipeline(
        cls,
        pipeline_id: int,
        name: Optional[str] = None,
        content: Optional[str] = None,
        description: Optional[str] = None,
        avatar: Optional[str] = None,
        params: Optional[str] = None, 
    ) -> bool:
        values = {k: v for k, v in locals().items() if k not in {"cls", "pipeline_id"} and v is not None}
        if not values:
            return False
        async with get_async_session() as session:
            stmt = update(Pipeline).where(Pipeline.id == pipeline_id).values(**values)
            result = await session.execute(stmt)
            return result.rowcount > 0
        
    @classmethod
    async def get_pipeline_list_by_creator(
        cls, principal_id: int, principal_type: str
    ) -> List[Pipeline]:
        async with get_async_session() as session:
            stmt = (
                select(Pipeline)
                .where(
                    Pipeline.principal_id == principal_id,
                    Pipeline.principal_type == principal_type,
                )
                .order_by(Pipeline.id.desc())
            )
            result = await session.execute(stmt)
            return result.scalars().all()