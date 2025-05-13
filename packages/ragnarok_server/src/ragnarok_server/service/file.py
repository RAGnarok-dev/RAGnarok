import logging
import os
from typing import Optional

from ragnarok_server.rdb.models import File
from ragnarok_server.rdb.repositories.file import FileRepository

logger = logging.getLogger(__name__)


class FileService:
    file_repo: FileRepository

    def __init__(self) -> None:
        self.file_repo = FileRepository()

    async def check_file_name_or_rename(self, file_name: str, folder_id: int) -> str:
        """
        check if the file name is already exists, if exists, rename the file name
        Args:
            file_name: file name
            folder_id: folder id
        Returns:
            str: available file name
        """
        file_list = await self.get_file_list(folder_id)
        name_set = {file.name for file in file_list}

        name_parts = file_name.rsplit(".", 1)
        if len(name_parts) == 1:
            base_name = file_name
            ext = ""
        else:
            base_name, ext = name_parts
            ext = "." + ext

        count = 1
        name = file_name
        while name in name_set:
            name = f"{base_name}({count}){ext}"
            count += 1
        return name

    async def check_file_name(self, file_name: str, folder_id: int) -> bool:
        return await self.file_repo.check_file_name(file_name, folder_id)

    async def check_parent_folder(self, parent_id: int) -> bool:
        file = await self.file_repo.get_file_by_id(parent_id)
        return file.type == "folder" or file.type == "root"

    async def create_file(
        self,
        name: str,
        type: str,
        size: int,
        created_by: str,
        parent_id: int,
        knowledge_base_id: int,
        description: Optional[str] = None,
    ) -> File:
        parent_file = await self.file_repo.get_file_by_id(parent_id)
        location = os.path.join(parent_file.location, name)

        file = File(
            name=name,
            description=description,
            type=type,
            size=size,
            location=location,
            created_by=created_by,
            parent_id=parent_id,
            knowledge_base_id=knowledge_base_id,
        )
        # TODO: upload file to vdb and odb
        return await self.file_repo.create_file(file)

    async def get_file_list(self, folder_id: int) -> list[File]:
        return await self.file_repo.get_file_list(folder_id)

    async def remove_file(self, file_id: int) -> bool:
        file_list = await self.get_file_list(file_id)
        for file in file_list:
            await self.remove_file(file.id)
        # TODO: delete file from vdb and odb
        return await self.file_repo.remove_file(file_id)

    async def move_file(self, file_id: int, dest_folder_id: int) -> bool:
        return await self.file_repo.move_file(file_id, dest_folder_id)

    async def get_file_by_id(self, file_id: int) -> Optional[File]:
        return await self.file_repo.get_file_by_id(file_id)

    async def rename_file(self, file_id: int, new_name: str) -> bool:
        return await self.file_repo.rename_file(file_id, new_name)

    async def get_parent_id(self, file_id: int) -> Optional[int]:
        return await self.file_repo.get_parent_id(file_id)

    async def get_all_parent_folders(self, file_id: int) -> list[File]:
        file = await self.get_file_by_id(file_id)
        parent_folders = []
        while file.parent_id is not None:
            file = await self.get_file_by_id(file.parent_id)
            parent_folders.append(file)
        return parent_folders


file_service = FileService()
