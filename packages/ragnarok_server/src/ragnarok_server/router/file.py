from typing import Optional

from fastapi import File, Form, UploadFile
from pydantic import BaseModel
from ragnarok_server import HTTPException
from ragnarok_server.common import ListResponseData, Response, ResponseCode
from ragnarok_server.router.base import CustomAPIRouter
from ragnarok_server.service.file import file_service

router = CustomAPIRouter(prefix="/files", tags=["File"])


class FileResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    type: str
    size: int
    location: str
    created_by: str
    parent_id: Optional[int]
    knowledge_base_id: int

    class Config:
        from_attributes = True


@router.post("/uploadFile")
async def upload_file(
    parent_id: int = Form(...),
    knowledge_base_id: int = Form(...),
    created_by: str = Form(...),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...),
) -> Response[FileResponse]:

    name = await file_service.check_file_name_or_rename(folder_id=parent_id, file_name=file.filename)

    uploaded_file = await file_service.create_file(
        name=name,
        description=description,
        type=file.content_type,
        size=file.size,
        created_by=created_by,
        parent_id=parent_id,
        knowledge_base_id=knowledge_base_id,
    )

    return ResponseCode.OK.to_response(data=FileResponse.model_validate(uploaded_file))


class FolderCreateRequest(BaseModel):
    name: str
    parent_id: int
    knowledge_base_id: int
    created_by: str
    description: Optional[str]


@router.post("/createFolder")
async def create_folder(request: FolderCreateRequest) -> Response:

    if await file_service.check_file_name(request.name, request.parent_id):
        raise HTTPException(status_code=400, content="name already exists")

    create_folder = await file_service.create_file(
        name=request.name,
        description=request.description,
        type="folder",
        size=0,
        created_by=request.created_by,
        parent_id=request.parent_id,
        knowledge_base_id=request.knowledge_base_id,
    )

    return ResponseCode.OK.to_response(data=FileResponse.model_validate(create_folder))


class FileRemoveRequest(BaseModel):
    file_id: int


@router.delete("/removeFile")
async def remove_file(request: FileRemoveRequest) -> Response:
    remove_file = await file_service.remove_file(request.file_id)
    if remove_file:
        return ResponseCode.OK.to_response()
    else:
        return ResponseCode.NO_SUCH_RESOURCE.to_response(detail="No Such File")


class FileListRequest(BaseModel):
    file_id: int


@router.get("/getFileList")
async def get_file_list(request: FileListRequest) -> Response[ListResponseData[FileResponse]]:
    file_list = await file_service.get_file_list(request.file_id)
    return ResponseCode.OK.to_response(
        data=ListResponseData(count=len(file_list), items=[FileResponse.model_validate(file) for file in file_list])
    )


class GetAllParentsRequest(BaseModel):
    file_id: int


@router.get("/getAllParentFolders")
async def get_all_parent_folders(request: GetAllParentsRequest) -> Response[ListResponseData[FileResponse]]:
    all_parents = await file_service.get_all_parent_folders(request.file_id)
    return ResponseCode.OK.to_response(
        data=ListResponseData(
            count=len(all_parents), items=[FileResponse.model_validate(parent) for parent in all_parents]
        )
    )


class FileRenameRequest(BaseModel):
    file_id: int
    new_name: str


@router.patch("/renameFile")
async def rename_file(request: FileRenameRequest) -> Response:
    if await file_service.check_file_name(request.new_name, request.file_id):
        raise HTTPException(status_code=400, content="name already exists")
    # TODO: rename children files
    rename_file = await file_service.rename_file(request.file_id, request.new_name)
    if rename_file:
        return ResponseCode.OK.to_response()
    else:
        return ResponseCode.NO_SUCH_RESOURCE.to_response(detail="No Such File")


class FileMoveRequest(BaseModel):
    file_id: int
    dest_folder_id: int


@router.patch("/moveFile")
async def move_file(request: FileMoveRequest) -> Response:
    # TODO: check if dest_folder_id is a folder, if not, return error
    # TODO: change children files' path
    move_file = await file_service.move_file(request.file_id, request.dest_folder_id)
    if move_file:
        return ResponseCode.OK.to_response()
    else:
        return ResponseCode.NO_SUCH_RESOURCE.to_response(detail="No Such File")
