from typing import Any, AsyncGenerator, Dict, Optional

from pydantic import BaseModel
from ragnarok_core.pipeline.pipeline_entity import PipelineExecutionInfo
from ragnarok_server import HTTPException
from ragnarok_server.common import Response, ResponseCode
from ragnarok_server.router.base import CustomAPIRouter, PipelineDetailModel
from ragnarok_server.service.pipeline import pipeline_service
from starlette.responses import StreamingResponse

router = CustomAPIRouter(prefix="/pipelines", tags=["Pipeline"])


class PipelineCreateRequest(BaseModel):
    name: str
    tenant_id: int
    content: str
    description: Optional[str] = None
    avatar: Optional[str] = None


class PipelineCreateResponse(BaseModel):
    pipeline: PipelineDetailModel


class PipelineExecuteRequest(BaseModel):
    pipeline_id: int
    params: Dict[str, Any]


class PipelineTestRequest(BaseModel):
    pipeline_content: str
    params: Dict[str, Any]


@router.post("", response_model=Response[PipelineCreateResponse])
async def create_pipeline(request: PipelineCreateRequest) -> Response[PipelineCreateResponse]:
    # TODO 1. check tenant_id

    # 2. validate json str format
    if not pipeline_service.validate_pipeline_str(request.content):
        raise HTTPException(status_code=400, content="Invalid pipeline content")

    # 3. create pipeline
    pipeline = await pipeline_service.create_pipeline(
        request.name, request.tenant_id, request.content, request.description, request.avatar
    )
    return ResponseCode.OK.to_response(
        data=PipelineCreateResponse(pipeline=PipelineDetailModel.from_pipeline(pipeline))
    )


@router.post("/execute")
async def execute_pipeline(request: PipelineExecuteRequest) -> StreamingResponse:
    async def sse_wrapper(ori_gen: AsyncGenerator[PipelineExecutionInfo, None]) -> AsyncGenerator[str, None]:
        async for pipeline_execution_info in ori_gen:
            yield "data: " + pipeline_execution_info.to_json() + "\n\n"

    # 1. get pipeline model
    pipeline = await pipeline_service.get_pipeline_by_id(request.pipeline_id)
    if pipeline is None:
        raise HTTPException(status_code=400, content=f"pipeline with id {request.pipeline_id} not found")

    # 2. execute
    return StreamingResponse(
        sse_wrapper(await pipeline_service.execute_pipeline(pipeline.content, request.params)),
        media_type="text/event-stream",
    )


@router.post("/test")
async def pipeline_test(request: PipelineTestRequest) -> StreamingResponse:
    async def sse_wrapper(ori_gen: AsyncGenerator[PipelineExecutionInfo, None]) -> AsyncGenerator[str, None]:
        async for pipeline_execution_info in ori_gen:
            yield "data: " + pipeline_execution_info.to_json() + "\n\n"

    # 1. validate pipeline
    if not pipeline_service.validate_pipeline_str(request.pipeline_content):
        raise HTTPException(status_code=400, content="Invalid pipeline content")

    # 2. execute pipeline
    return StreamingResponse(
        sse_wrapper(await pipeline_service.execute_pipeline(request.pipeline_content, request.params)),
        media_type="text/event-stream",
    )
