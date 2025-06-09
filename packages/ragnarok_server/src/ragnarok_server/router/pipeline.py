from typing import Any, AsyncGenerator, Dict, Optional

from pydantic import BaseModel
from ragnarok_core.pipeline.pipeline_entity import PipelineExecutionInfo
from ragnarok_server import HTTPException
from ragnarok_server.common import Response, ResponseCode
from ragnarok_server.router.base import CustomAPIRouter, PipelineDetailModel
from ragnarok_server.service.pipeline import pipeline_service
from ragnarok_server.auth import TokenData, decode_access_token
from starlette.responses import StreamingResponse
from fastapi import Depends
from ragnarok_server.common import ListResponseData
from pydantic import BaseModel, field_validator
import json

router = CustomAPIRouter(prefix="/pipelines", tags=["Pipeline"])


class PipelineCreateRequest(BaseModel):
    name: str
    content: str
    description: Optional[str] = None
    avatar: Optional[str] = None
    params: Optional[Dict[str, Any]] = None     


class PipelineCreateResponse(BaseModel):
    pipeline: PipelineDetailModel


class PipelineExecuteRequest(BaseModel):
    pipeline_id: int
    params: Dict[str, Any]


class PipelineTestRequest(BaseModel):
    pipeline_content: str
    params: Dict[str, Any]

class PipelineRemoveRequest(BaseModel):
    pipeline_id: int


class PipelineSaveRequest(BaseModel):
    pipeline_id: int
    name: Optional[str] = None
    content: Optional[str] = None
    description: Optional[str] = None
    avatar: Optional[str] = None
    params: Optional[Dict[str, Any]] = None

class PipelineBriefResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    avatar: Optional[str] = None
    content: str
    params: Optional[Dict[str, Any]] = None         

    @field_validator("params", mode="before")
    @classmethod
    def parse_params(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return json.loads(v)
            except ValueError:
                return None
        return v

    class Config:
        from_attributes = True


async def _check_owner(pipeline_id: int, token: TokenData):
    pipeline = await pipeline_service.get_pipeline_by_id(pipeline_id)
    if pipeline is None:
        raise HTTPException(status_code=404, content="Pipeline not found")
    if (
        pipeline.principal_id != token.principal_id
        or pipeline.principal_type != token.principal_type
    ):
        raise HTTPException(status_code=403, content="Not the owner")
    return pipeline

@router.post("", response_model=Response[PipelineCreateResponse])
async def create_pipeline(request: PipelineCreateRequest,token: TokenData = Depends(decode_access_token)) -> Response[PipelineCreateResponse]:
    # 1. validate json str format
    if not pipeline_service.validate_pipeline_str(request.content):
        raise HTTPException(status_code=400, content="Invalid pipeline content")

    # 2. create pipeline
    pipeline = await pipeline_service.create_pipeline(
        name=request.name,
        principal_id=token.principal_id,                 
        principal_type=token.principal_type,             
        content=request.content,
        description=request.description,
        avatar=request.avatar,
        params=request.params,
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

@router.delete("/remove")
async def remove_pipeline(
    request: PipelineRemoveRequest, token: TokenData = Depends(decode_access_token)
) -> Response:
    await _check_owner(request.pipeline_id, token)
    ok = await pipeline_service.remove_pipeline(request.pipeline_id)
    if not ok:
        return ResponseCode.NO_SUCH_RESOURCE.to_response(detail="Pipeline not found")
    return ResponseCode.OK.to_response()

@router.patch("/save")
async def save_pipeline(
    request: PipelineSaveRequest, token: TokenData = Depends(decode_access_token)
) -> Response:
    await _check_owner(request.pipeline_id, token)

    # if request.content and not pipeline_service.validate_pipeline_str(request.content):
    #     raise HTTPException(status_code=400, content="Invalid pipeline content")
    ok = await pipeline_service.update_pipeline(
        pipeline_id=request.pipeline_id,
        name=request.name,
        content=request.content,
        description=request.description,
        avatar=request.avatar,
        params=request.params,
    )
    if not ok:
        return ResponseCode.NO_SUCH_RESOURCE.to_response(detail="Pipeline not found")
    return ResponseCode.OK.to_response()


@router.get("/list")
async def list_my_pipelines(
    token: TokenData = Depends(decode_access_token),
) -> Response[ListResponseData[PipelineBriefResponse]]:
    pipelines = await pipeline_service.get_pipeline_list_by_creator(
        token.principal_id, token.principal_type
    )
    return ResponseCode.OK.to_response(
        data=ListResponseData(
            count=len(pipelines),
            items = [
                PipelineBriefResponse.model_validate(p, from_attributes=True)  
                for p in pipelines
            ]
        )
    )

@router.get("/get")
async def get_pipeline(
    pipeline_id: int,                               
    token: TokenData = Depends(decode_access_token),
) -> Response[PipelineDetailModel]:
    pipeline = await _check_owner(pipeline_id, token)
    data = PipelineDetailModel.from_pipeline(pipeline)
    return ResponseCode.OK.to_response(data=data)