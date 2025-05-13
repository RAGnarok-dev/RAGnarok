from typing import Optional

from pydantic import BaseModel
from ragnarok_server.common import ListResponseData, Response, ResponseCode
from ragnarok_server.exceptions import HTTPException
from ragnarok_server.router.base import CustomAPIRouter
from ragnarok_server.router.file import FileResponse
from ragnarok_server.service.file import file_service
from ragnarok_server.service.knowledge_base import kb_service

router = CustomAPIRouter(prefix="/knowledge_base", tags=["Knowledge Base"])


class KnowledgeBaseResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    embedding_model_id: int
    root_file_id: int
    created_by: str

    class Config:
        from_attributes = True


class KnowledgeBaseCreateRequest(BaseModel):
    title: str
    description: str
    embedding_model_id: int
    created_by: str


@router.post("/create")
async def create_knowledge_base(request: KnowledgeBaseCreateRequest) -> Response[KnowledgeBaseResponse]:
    # TODO: verify the embedding model id
    # TODO: verify the created_by
    if not await kb_service.validate_title(request.title, request.created_by):
        raise HTTPException(status_code=400, content="Knowledge base title already exists")

    kb = await kb_service.create_knowledge_base(
        request.title, request.description, request.embedding_model_id, request.created_by
    )
    kb_root_folder = await file_service.create_kb_root_folder(
        knowldge_base_name=request.title,
        knowledge_base_id=kb.id,
        created_by=request.created_by,
        description="root folder of knowledge base",
    )
    await kb_service.fix_kb_root_file_id(kb.id, kb_root_folder.id)
    kb.root_file_id = kb_root_folder.id
    return ResponseCode.OK.to_response(data=KnowledgeBaseResponse.model_validate(kb))


@router.delete("/remove")
async def remove_knowledge_base(id: int) -> Response:
    # TODO: verify the id
    await kb_service.remove_knowledge_base(id)
    return ResponseCode.OK.to_response()


@router.patch("/retitle")
async def retitle_knowledge_base(id: int, title: str) -> Response:
    kb = await kb_service.get_knowledge_base_by_id(id)
    if kb is None:
        raise HTTPException(status_code=400, content="Knowledge base not found")
    if not await kb_service.validate_title(title, kb.created_by):
        raise HTTPException(status_code=400, content="Knowledge base title already exists")
    await file_service.rename_file(kb.root_file_id, title)
    await kb_service.retitle_knowledge_base(id, title)
    return ResponseCode.OK.to_response()


@router.get("/list")
async def list_knowledge_base(created_by: str) -> Response[ListResponseData[KnowledgeBaseResponse]]:
    # TODO: verify the created_by
    kbs = await kb_service.get_knowledge_base_list_by_creator(created_by)
    return ResponseCode.OK.to_response(
        data=ListResponseData(count=len(kbs), items=[KnowledgeBaseResponse.model_validate(kb) for kb in kbs])
    )


@router.get("/get")
async def get_knowledge_base(id: int) -> Response[KnowledgeBaseResponse]:
    # TODO: verify the id
    kb = await kb_service.get_knowledge_base_by_id(id)
    return ResponseCode.OK.to_response(data=KnowledgeBaseResponse.model_validate(kb))


@router.get("/get_root_file")
async def get_root_file(id: int) -> Response[FileResponse]:
    # TODO: verify the id
    kb = await kb_service.get_knowledge_base_by_id(id)
    root_file_id = kb.root_file_id
    file = await file_service.get_file_by_id(root_file_id)
    return ResponseCode.OK.to_response(data=FileResponse.model_validate(file))
