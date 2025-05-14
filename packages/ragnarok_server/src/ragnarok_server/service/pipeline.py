import logging
from typing import Any, AsyncGenerator, Dict, Optional

from ragnarok_core.pipeline.pipeline_entity import PipelineEntity, PipelineExecutionInfo
from ragnarok_server.rdb.models import Pipeline
from ragnarok_server.rdb.repositories.pipeline import PipelineRepository

logger = logging.getLogger(__name__)


class PipelineService:
    pipeline_repo: PipelineRepository

    def __init__(self) -> None:
        self.pipeline_repo = PipelineRepository()

    def validate_pipeline_str(self, content: str) -> bool:
        """
        try to create a pipeline from a given string,
        return true if the pipeline is valid
        """
        # TODO consider add error msg as return value
        try:
            _ = PipelineEntity.from_json_str(content)
        except Exception as e:
            logger.warning(f"Failed to create pipeline from string: {content}, err: {e}")
            return False
        return True

    async def create_pipeline(
        self, name: str, tenant_id: int, content: str, description: Optional[str] = None, avatar: Optional[str] = None
    ) -> Pipeline:
        pipeline = Pipeline(
            name=name,
            tenant_id=tenant_id,
            content=content,
            description=description,
            avatar=avatar,
        )
        return await self.pipeline_repo.create_pipeline(pipeline)

    async def get_pipeline_by_id(self, pipeline_id: int) -> Optional[Pipeline]:
        return await self.pipeline_repo.get_pipeline_by_id(pipeline_id)

    async def execute_pipeline(
        self, content: str, params: Dict[str, Any]
    ) -> AsyncGenerator[PipelineExecutionInfo, None]:
        pipeline_entity = PipelineEntity.from_json_str(content)
        return pipeline_entity.run_async(**params)


pipeline_service = PipelineService()
