from typing import Optional

from fastapi import Depends, File, Form, UploadFile
from pydantic import BaseModel
from ragnarok_server import HTTPException
from ragnarok_server.auth import TokenData, decode_access_token
from ragnarok_server.common import ListResponseData, Response, ResponseCode
from ragnarok_server.router.base import CustomAPIRouter
from ragnarok_server.router.permission import require_permission
from ragnarok_server.service.file import file_service

router = CustomAPIRouter(prefix="/files", tags=["File"])


class FileResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    type: str
    size: int
    location: str
    principal_id: int
    principal_type: str
    parent_id: Optional[str]
    knowledge_base_id: int

    class Config:
        from_attributes = True


@router.post("/uploadFile")
@require_permission("write")
async def upload_file(
    parent_id: str = Form(...),
    knowledge_base_id: int = Form(...),
    token: TokenData = Depends(decode_access_token),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...),
) -> Response[FileResponse | None]:

    name = await file_service.check_file_name_or_rename(folder_id=parent_id, file_name=file.filename)

    uploaded_file = await file_service.create_file(
        name=name,
        description=description,
        type=file.content_type,
        size=file.size,
        principal_id=token.principal_id,
        principal_type=token.principal_type,
        parent_id=parent_id,
        knowledge_base_id=knowledge_base_id,
    )

    return ResponseCode.OK.to_response(data=FileResponse.model_validate(uploaded_file))


class FolderCreateRequest(BaseModel):
    name: str
    parent_id: str
    knowledge_base_id: int
    description: Optional[str]


@router.post("/createFolder")
@require_permission("write")
async def create_folder(
    request: FolderCreateRequest, token: TokenData = Depends(decode_access_token)
) -> Response[FileResponse | None]:

    if await file_service.check_file_name(request.name, request.parent_id):
        raise HTTPException(status_code=400, content="name already exists")

    create_folder = await file_service.create_file(
        name=request.name,
        description=request.description,
        type="folder",
        size=0,
        principal_id=token.principal_id,
        principal_type=token.principal_type,
        parent_id=request.parent_id,
        knowledge_base_id=request.knowledge_base_id,
    )

    return ResponseCode.OK.to_response(data=FileResponse.model_validate(create_folder))


class FileRemoveRequest(BaseModel):
    file_id: str
    knowledge_base_id: int


@router.delete("/removeFile")
@require_permission("write")
async def remove_file(request: FileRemoveRequest, token: TokenData = Depends(decode_access_token)) -> Response:

    remove_file = await file_service.remove_file(request.file_id)
    if remove_file:
        return ResponseCode.OK.to_response()
    else:
        return ResponseCode.NO_SUCH_RESOURCE.to_response(detail="No Such File")


@router.get("/getFile")
@require_permission("read")
async def get_file(
    file_id: str, knowledge_base_id: int, token: TokenData = Depends(decode_access_token)
) -> Response[FileResponse | None]:
    file = await file_service.get_file_by_id(file_id)
    return ResponseCode.OK.to_response(data=FileResponse.model_validate(file))


@router.get("/getFileList")
@require_permission("read")
async def get_file_list(
    file_id: str, knowledge_base_id: int, token: TokenData = Depends(decode_access_token)
) -> Response[ListResponseData[FileResponse] | None]:
    file_list = await file_service.get_file_list(file_id)
    return ResponseCode.OK.to_response(
        data=ListResponseData(count=len(file_list), items=[FileResponse.model_validate(file) for file in file_list])
    )


@router.get("/getAllParentFolders")
@require_permission("read")
async def get_all_parent_folders(
    file_id: str, knowledge_base_id: int, token: TokenData = Depends(decode_access_token)
) -> Response[ListResponseData[FileResponse] | None]:
    all_parents = await file_service.get_all_parent_folders(file_id)
    return ResponseCode.OK.to_response(
        data=ListResponseData(
            count=len(all_parents), items=[FileResponse.model_validate(parent) for parent in all_parents]
        )
    )


class FileRenameRequest(BaseModel):
    file_id: str
    new_name: str
    knowledge_base_id: int


@router.patch("/renameFile")
@require_permission("write")
async def rename_file(request: FileRenameRequest, token: TokenData = Depends(decode_access_token)) -> Response:
    if await file_service.check_file_name(request.new_name, request.file_id):
        raise HTTPException(status_code=400, content="name already exists")

    rename_file = await file_service.rename_file(request.file_id, request.new_name)
    if rename_file:
        return ResponseCode.OK.to_response()
    else:
        return ResponseCode.NO_SUCH_RESOURCE.to_response(detail="No Such File")


class FileMoveRequest(BaseModel):
    file_id: str
    dest_folder_id: str
    knowledge_base_id: int


@router.patch("/moveFile")
@require_permission("write")
async def move_file(request: FileMoveRequest, token: TokenData = Depends(decode_access_token)) -> Response:

    file = await file_service.get_file_by_id(request.dest_folder_id)
    if file.type != "folder":
        return ResponseCode.INVALID_ARGS.to_response(detail="Destination is not a folder")

    move_file = await file_service.move_file(request.file_id, request.dest_folder_id)

    if move_file:
        return ResponseCode.OK.to_response()
    else:
        return ResponseCode.NO_SUCH_RESOURCE.to_response(detail="No Such File")
