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

class PipelineCompletionRequest(BaseModel):
    pipeline_id: int
    message_id: str
    params: Dict[str, Any] = {}

class PipelineTestRequest(BaseModel):
    pipeline_content: str
    params: Dict[str, Any]

class PipelineRemoveRequest(BaseModel):
    pipeline_id: int


class PipelineResetRequest(BaseModel):
    pipeline_id: int

class PipelineSaveRequest(BaseModel):
    pipeline_id: int
    name: Optional[str] = None
    content: Optional[str] = None
    description: Optional[str] = None
    avatar: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    components: Optional[str] = None
    path: Optional[str] = None

class PipelineBriefResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    avatar: Optional[str] = None
    content: str
    params: Optional[Dict[str, Any]] = None   
    components: Optional[str] = None
    path: Optional[str] = None      

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


def decode_bytes(data):
    """递归解码字节数据"""
    if isinstance(data, bytes):
        try:
            return data.decode('utf-8')  # 尝试解码为 UTF-8 字符串
        except UnicodeDecodeError:
            return "<invalid utf-8 data>"
    elif isinstance(data, dict):
        # 如果是字典，递归解码所有值
        return {key: decode_bytes(value) for key, value in data.items()}
    elif isinstance(data, list):
        # 如果是列表，递归解码所有元素
        return [decode_bytes(item) for item in data]
    else:
        # 如果既不是字节数据，也不是字典或列表，直接返回
        return data

@router.post("/test")
async def pipeline_test(request: PipelineTestRequest) -> StreamingResponse:
    async def sse_wrapper(ori_gen: AsyncGenerator[PipelineExecutionInfo, None]) -> AsyncGenerator[str, None]:
        async for pipeline_execution_info in ori_gen:
            # 获取 json_data，并处理其中的字节数据
            json_data = pipeline_execution_info.to_json()

            # 解码 json_data 中的字节数据
            json_data = decode_bytes(json_data)

            yield f"data: {json_data}\n\n"

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
        components=request.components,
        path=request.path,   
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


@router.post("/reset")
async def reset_pipeline(
    request: PipelineResetRequest,
    token: TokenData = Depends(decode_access_token),
) -> Response:
    await _check_owner(request.pipeline_id, token)

    ok = await pipeline_service.update_pipeline(
        pipeline_id=request.pipeline_id,
        components="",  
        path="",       
    )
    if not ok:
        return ResponseCode.NO_SUCH_RESOURCE.to_response(detail="Pipeline not found")
    return ResponseCode.OK.to_response()



@router.post("/completion")
async def completion_pipeline(request: PipelineCompletionRequest) -> StreamingResponse:
    async def sse_wrapper(ori_gen: AsyncGenerator[PipelineExecutionInfo, None]) -> AsyncGenerator[str, None]:
        async for pipeline_execution_info in ori_gen:
            if pipeline_execution_info.type == "output_info":
                for key, value in pipeline_execution_info.data.items():
                    if key.endswith('_res'):
                        # 处理字节数据
                        value = decode_bytes(value)  # 解码字节数据
                        
                        content = json.dumps(value)
                        updated_info = {
                            "node_id": pipeline_execution_info.node_id,
                            "type": pipeline_execution_info.type,
                            "data": {
                                "content": content
                            },
                            "timestamp": pipeline_execution_info.timestamp.isoformat()  # 确保时间戳可序列化
                        }
                        yield "data: " + json.dumps(updated_info) + "\n\n"
                        return  

            else:
                # 处理 pipeline_execution_info.data 字段
                pipeline_execution_info.data = decode_bytes(pipeline_execution_info.data)  # 解码字节数据

                content = f"node {pipeline_execution_info.node_id} running, output: {pipeline_execution_info.data}"

                updated_info = {
                    "node_id": pipeline_execution_info.node_id,
                    "type": pipeline_execution_info.type,
                    "data": {
                        "content": content
                    },
                    "timestamp": pipeline_execution_info.timestamp.isoformat()  # 确保时间戳可序列化
                }

                yield "data: " + json.dumps(updated_info) + "\n\n"


    pipeline = await pipeline_service.get_pipeline_by_id(request.pipeline_id)
    if pipeline is None:
        raise HTTPException(status_code=400, content=f"pipeline with id {request.pipeline_id} not found")


    return StreamingResponse(
        sse_wrapper(await pipeline_service.execute_pipeline(pipeline.content, request.params)),
        media_type="text/event-stream",
    )