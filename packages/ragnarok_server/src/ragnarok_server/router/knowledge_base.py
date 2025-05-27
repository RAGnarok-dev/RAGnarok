from typing import Optional

from fastapi import Depends
from pydantic import BaseModel
from ragnarok_server.auth import TokenData, decode_access_token
from ragnarok_server.common import ListResponseData, Response, ResponseCode
from ragnarok_server.exceptions import HTTPException
from ragnarok_server.rdb.models import Permission
from ragnarok_server.router.base import CustomAPIRouter
from ragnarok_server.router.file import FileResponse
from ragnarok_server.router.permission import require_permission
from ragnarok_server.service.file import file_service
from ragnarok_server.service.knowledge_base import kb_service
from ragnarok_server.service.permission import permission_service

router = CustomAPIRouter(prefix="/knowledge_base", tags=["Knowledge Base"])


class KnowledgeBaseResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    embedding_model_id: int
    root_file_id: str
    principal_id: int
    principal_type: str

    class Config:
        from_attributes = True


class KnowledgeBaseCreateRequest(BaseModel):
    title: str
    description: str
    embedding_model_id: int


@router.post("/create")
async def create_knowledge_base(
    request: KnowledgeBaseCreateRequest, token: TokenData = Depends(decode_access_token)
) -> Response[KnowledgeBaseResponse]:
    if not await kb_service.validate_title(request.title, token.principal_id, token.principal_type):
        raise HTTPException(status_code=400, content="Knowledge base title already exists")

    kb = await kb_service.create_knowledge_base(
        request.title, request.description, request.embedding_model_id, token.principal_id, token.principal_type
    )

    await permission_service.create_or_update_permission(
        Permission(
            principal_id=token.principal_id,
            principal_type=token.principal_type,
            knowledge_base_id=kb.id,
            permission_type="admin",
        )
    )

    kb_root_folder = await file_service.create_kb_root_folder(
        knowldge_base_name=request.title,
        knowledge_base_id=kb.id,
        principal_id=token.principal_id,
        principal_type=token.principal_type,
        description="root folder of knowledge base",
    )
    await kb_service.fix_kb_root_file_id(kb.id, kb_root_folder.id)
    kb.root_file_id = kb_root_folder.id
    return ResponseCode.OK.to_response(data=KnowledgeBaseResponse.model_validate(kb))


class KnowledgeBaseChangePermissionRequest(BaseModel):
    knowledge_base_id: int
    principal_id: int
    principal_type: str
    permission_type: str


@router.post("/change_permission")
@require_permission("admin")
async def change_permission(
    request: KnowledgeBaseChangePermissionRequest, token: TokenData = Depends(decode_access_token)
) -> Response:
    await permission_service.change_permission(
        request.knowledge_base_id, request.principal_id, request.principal_type, request.permission_type
    )
    return ResponseCode.OK.to_response()


class KnowledgeBaseRemoveRequest(BaseModel):
    knowledge_base_id: int


@router.delete("/remove")
@require_permission("admin")
async def remove_knowledge_base(
    request: KnowledgeBaseRemoveRequest, token: TokenData = Depends(decode_access_token)
) -> Response:
    kb = await kb_service.get_knowledge_base_by_id(request.knowledge_base_id)
    if kb is None:
        return ResponseCode.NO_SUCH_RESOURCE.to_response(detail="Knowledge base not found")
    await file_service.remove_file(kb.root_file_id, f"{kb.principal_type}-{kb.principal_id}")
    await kb_service.remove_knowledge_base(request.knowledge_base_id)
    return ResponseCode.OK.to_response()


class KnowledgeBaseRetitleRequest(BaseModel):
    knowledge_base_id: int
    title: str


@router.patch("/retitle")
@require_permission("admin")
async def retitle_knowledge_base(
    request: KnowledgeBaseRetitleRequest, token: TokenData = Depends(decode_access_token)
) -> Response:
    kb = await kb_service.get_knowledge_base_by_id(request.knowledge_base_id)
    if kb is None:
        raise HTTPException(status_code=400, content="Knowledge base not found")
    if not await kb_service.validate_title(request.title, kb.principal_id, kb.principal_type):
        raise HTTPException(status_code=400, content="Knowledge base title already exists")
    await file_service.rename_root_file(kb.root_file_id, request.title)
    await kb_service.retitle_knowledge_base(request.knowledge_base_id, request.title)
    return ResponseCode.OK.to_response()


@router.get("/list")
async def list_knowledge_base(
    token: TokenData = Depends(decode_access_token),
) -> Response[ListResponseData[KnowledgeBaseResponse]]:
    kbs = await kb_service.get_knowledge_base_list_by_creator(token.principal_id, token.principal_type)
    return ResponseCode.OK.to_response(
        data=ListResponseData(count=len(kbs), items=[KnowledgeBaseResponse.model_validate(kb) for kb in kbs])
    )


@router.get("/get")
@require_permission("read")
async def get_knowledge_base(
    knowledge_base_id: int, token: TokenData = Depends(decode_access_token)
) -> Response[KnowledgeBaseResponse]:
    kb = await kb_service.get_knowledge_base_by_id(knowledge_base_id)
    return ResponseCode.OK.to_response(data=KnowledgeBaseResponse.model_validate(kb))


@router.get("/get_root_file")
@require_permission("read")
async def get_root_file(
    knowledge_base_id: int, token: TokenData = Depends(decode_access_token)
) -> Response[FileResponse]:
    kb = await kb_service.get_knowledge_base_by_id(knowledge_base_id)
    root_file_id = kb.root_file_id
    file = await file_service.get_file_by_id(root_file_id)
    return ResponseCode.OK.to_response(data=FileResponse.model_validate(file))


@router.get("/get_permission")
async def get_permission(knowledge_base_id: int, token: TokenData = Depends(decode_access_token)) -> Response[str]:
    permission = await permission_service.get_permission(token.principal_id, token.principal_type, knowledge_base_id)
    if permission is None:
        return ResponseCode.OK.to_response(data="none")
    return ResponseCode.OK.to_response(data=permission.permission_type)
