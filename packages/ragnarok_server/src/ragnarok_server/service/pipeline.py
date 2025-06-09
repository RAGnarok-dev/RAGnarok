import logging
from typing import Any, AsyncGenerator, Dict, Optional, List

from ragnarok_core.pipeline.pipeline_entity import PipelineEntity, PipelineExecutionInfo
from ragnarok_server.rdb.models import Pipeline
from ragnarok_server.rdb.repositories.pipeline import PipelineRepository
import json

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
        self,
        name: str,
        principal_id: int,          
        principal_type: str,        
        content: str,
        description: Optional[str] = None,
        avatar: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Pipeline:
        pipeline = Pipeline(
            name=name,
            principal_id=principal_id,        
            principal_type=principal_type,    
            content=content,
            description=description,
            avatar=avatar,
            params=json.dumps(params) if params else None,
        )
        return await self.pipeline_repo.create_pipeline(pipeline)

    async def get_pipeline_by_id(self, pipeline_id: int) -> Optional[Pipeline]:
        return await self.pipeline_repo.get_pipeline_by_id(pipeline_id)

    async def execute_pipeline(
        self, content: str, params: Dict[str, Any]
    ) -> AsyncGenerator[PipelineExecutionInfo, None]:
        pipeline_entity = PipelineEntity.from_json_str(content)
        return pipeline_entity.run_async(**params)
    
    async def remove_pipeline(self, pipeline_id: int) -> bool:
        return await self.pipeline_repo.remove_pipeline(pipeline_id)

    async def update_pipeline(
        self,
        pipeline_id: int,
        name: Optional[str] = None,
        content: Optional[str] = None,
        description: Optional[str] = None,
        avatar: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        components: Optional[str] = None,
        path: Optional[str] = None,
    ) -> bool:
        return await self.pipeline_repo.update_pipeline(
            pipeline_id, name=name, content=content, description=description, avatar=avatar,params=json.dumps(params) if params is not None else None,components=components, path=path
        )
    
    async def get_pipeline_list_by_creator(
        self, principal_id: int, principal_type: str
    ) -> List[Pipeline]:
        return await self.pipeline_repo.get_pipeline_list_by_creator(
            principal_id, principal_type
        )

pipeline_service = PipelineService()
