import base64
from typing import Optional
import os
from fastapi import Depends, Body, Path
from pydantic import BaseModel
from ragnarok_core.components.official_components.text_split_component import SplitType
from ragnarok_server.auth import TokenData, decode_access_token
from ragnarok_server.common import ListResponseData, Response, ResponseCode
from ragnarok_server.exceptions import HTTPException
from ragnarok_server.rdb.models import Permission, Tenant, User
from ragnarok_server.router.base import CustomAPIRouter
from ragnarok_server.router.file import FileResponse
from ragnarok_server.router.permission import require_permission
from ragnarok_server.service.file import file_service
from ragnarok_server.service.knowledge_base import kb_service
from ragnarok_server.service.permission import permission_service
from ragnarok_server.service.user import user_service
from ragnarok_toolkit.model.embedding_model import EmbeddingModelEnum
from ragnarok_server.router.base import (
    KbGetPermissionListRequestModel,
    KbGetPermissionListResponseModel,
    PermissionListResponseModel
)
from ragnarok_server.rdb.models import KnowledgeBase


router = CustomAPIRouter(prefix="/knowledge_base", tags=["Knowledge Base"])


class KnowledgeBaseResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    embedding_model_name: str
    split_type: str
    root_file_id: str
    principal_id: int
    principal_type: str
    avatar: Optional[str]

    class Config:
        from_attributes = True


class GetAllKnowledgeBaseResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    embedding_model_name: str
    split_type: str
    root_file_id: str
    principal_id: int
    principal_type: str
    permission: str
    avatar: Optional[str]


class KnowledgeBaseCreateRequest(BaseModel):
    title: str
    description: str
    embedding_model_name: str
    split_type: str


@router.post("/create")
async def create_knowledge_base(
    request: KnowledgeBaseCreateRequest, token: TokenData = Depends(decode_access_token)
) -> Response[KnowledgeBaseResponse]:
    # validate
    if not await kb_service.validate_title(request.title, token.principal_id, token.principal_type):
        raise HTTPException(status_code=400, content="Knowledge base title already exists")
    try:
        EmbeddingModelEnum.from_name(request.embedding_model_name)
    except ValueError:
        raise HTTPException(status_code=400, content="Invalid embedding model name")
    try:
        SplitType(request.split_type)
    except ValueError:
        raise HTTPException(status_code=400, content="Invalid split type")

    kb = await kb_service.create_knowledge_base(
        request.title,
        request.description,
        request.embedding_model_name,
        request.split_type,
        token.principal_id,
        token.principal_type,
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
    return ResponseCode.OK.to_response(

    )


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
    await file_service.remove_file(kb.root_file_id, kb.principal_type, kb.principal_id)
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


class KnowledgeBaseModifyRequest(BaseModel):
    knowledge_base_id: int
    title: Optional[str] = None
    description: Optional[str] = None
    embedding_model_name: Optional[str] = None
    split_type: Optional[str] = None
    avatar: str


class KnowledgeBaseModifyResponse(BaseModel):
    title: str
    avatar: str
    description: str


@router.patch("/modify")
@require_permission("admin")
async def modify_knowledge_base(
    request: KnowledgeBaseModifyRequest = Body(...), token: TokenData = Depends(decode_access_token)
) -> Response[KnowledgeBaseModifyResponse]:

    # check validate
    kb = await kb_service.get_knowledge_base_by_id(request.knowledge_base_id)
    if kb is None:
        raise HTTPException(status_code=400, content="Knowledge base not found")
    if request.title is not None and not await kb_service.validate_title(
        request.title, kb.principal_id, kb.principal_type
    ):
        raise HTTPException(status_code=400, content="Knowledge base title already exists")
    if request.embedding_model_name is not None:
        try:
            EmbeddingModelEnum.from_name(request.embedding_model_name)
        except ValueError:
            raise HTTPException(status_code=400, content="Invalid embedding model name")
    if request.split_type is not None:
        try:
            SplitType(request.split_type)
        except ValueError:
            raise HTTPException(status_code=400, content="Invalid split type")
    if request.avatar is not None:
        header, encoded = request.avatar.split(',', 1)
        file_data = base64.b64decode(encoded)
        filename = f"{request.knowledge_base_id}.png"
        save_dir = "static/kb_avatars"

        os.makedirs(save_dir, exist_ok=True)
        filepath = os.path.join(save_dir, filename)

        with open(filepath, "wb") as f:
            f.write(file_data)

        await kb_service.update_avatar(request.knowledge_base_id, request.avatar)

    # TODO modify embedding model and split type
    await kb_service.modify_knowledge_base(
        request.knowledge_base_id, request.title, request.description, request.embedding_model_name, request.split_type
    )
    return ResponseCode.OK.to_response(
        data=KnowledgeBaseModifyResponse(
            title=request.title,
            avatar=request.avatar,
            description=request.description
        )
    )


@router.get("/list")
async def list_knowledge_base(
    token: TokenData = Depends(decode_access_token),
) -> Response[ListResponseData[GetAllKnowledgeBaseResponse]]:
    kbs = await kb_service.get_all_knowledge_bases(token.principal_id, token.principal_type)
    return ResponseCode.OK.to_response(
        data=ListResponseData(count=len(kbs), items=[GetAllKnowledgeBaseResponse.model_validate(kb) for kb in kbs])
    )

class KnowledgeBaseInfoResponse(BaseModel):
    title: str
    description: str
    avatar: str

@router.get("/get")
@require_permission("read")
async def get_knowledge_base(
    knowledge_base_id: int, token: TokenData = Depends(decode_access_token)
) -> Response[KnowledgeBaseResponse]:
    kb = await kb_service.get_knowledge_base_by_id(knowledge_base_id)
    return ResponseCode.OK.to_response(data=KnowledgeBaseResponse(
            id=kb.id,
            title=kb.title,
            description=kb.description,
            embedding_model_name=kb.embedding_model_name,
            split_type=kb.split_type,
            root_file_id=kb.root_file_id,
            principal_id=kb.principal_id,
            principal_type=kb.principal_type,
            avatar=kb.avatar_url,
        )
    )


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


@router.get(
    "/{knowledgeBaseId}/get_permission_list",
    summary="Get permission list by kb_id",
    response_model=Response[KbGetPermissionListResponseModel]
)
async def get_permission_list(
    knowledgeBaseId: int = Path(..., description="Knowledge Base ID"),
    service=Depends(lambda: permission_service),
) -> Response[KbGetPermissionListResponseModel]:
    result: list[Permission] = await service.get_permission_list(knowledgeBaseId)
    permission_lists = []
    for permission in result:
        if permission.principal_type == 'user':
            user: User = await user_service.get_user_by_id(permission.principal_id)
            permission_list = PermissionListResponseModel(
                username=user.username,
                email=user.email,
                permission_type=permission.permission_type
            )
            permission_lists.append(permission_list)
    return ResponseCode.OK.to_response(
        data=KbGetPermissionListResponseModel(
            permission_lists=permission_lists
        )
    )


# embedding model and split type


class EmbeddingModelResponse(BaseModel):
    name: str
    dim: int


@router.get("/get_embedding_model")
async def get_embedding_model() -> Response[ListResponseData[EmbeddingModelResponse]]:
    embedding_models = [
        EmbeddingModelResponse(name=model.value["name"], dim=model.value["dim"]) for model in EmbeddingModelEnum
    ]
    return ResponseCode.OK.to_response(data=ListResponseData(count=len(embedding_models), items=embedding_models))


class SplitTypeResponse(BaseModel):
    name: str


@router.get("/get_split_type")
async def get_split_type() -> Response[ListResponseData[SplitTypeResponse]]:
    split_types = [SplitTypeResponse(name=split_type.value) for split_type in SplitType]
    return ResponseCode.OK.to_response(data=ListResponseData(count=len(split_types), items=split_types))
