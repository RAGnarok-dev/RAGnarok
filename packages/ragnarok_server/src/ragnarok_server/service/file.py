import logging
from typing import Optional

from ragnarok_server.rdb.models import File
from ragnarok_server.rdb.repositories.file import FileRepository
from ragnarok_server.service.store import store_service

logger = logging.getLogger(__name__)


class FileService:
    file_repo: FileRepository

    def __init__(self) -> None:
        self.file_repo = FileRepository()

    async def check_file_name_or_rename(self, file_name: str, folder_id: str) -> str:
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

    async def check_file_name(self, file_name: str, folder_id: str) -> bool:
        if await self.file_repo.check_file_name(file_name, folder_id):
            logger.error(f"the name '{file_name}' is exisited")
        return await self.file_repo.check_file_name(file_name, folder_id)

    async def check_parent_folder(self, parent_id: str) -> bool:
        file = await self.file_repo.get_file_by_id(parent_id)
        if not (file and (file.type == "folder" or file.type == "root")):
            logger.warning(f"file {file.name} isn't a folder")
            return False
        return True

    async def create_kb_root_folder(
        self, knowldge_base_name: str, knowledge_base_id: int, principal_id: int, principal_type: str, description: str
    ) -> File:
        file = File(
            name=knowldge_base_name,
            description=description,
            type="root",
            size=0,
            location="/",
            principal_id=principal_id,
            principal_type=principal_type,
            parent_id=None,
            knowledge_base_id=knowledge_base_id,
            chunk_size=0,
        )
        return await self.file_repo.create_file(file)

    async def create_file(
        self,
        name: str,
        type: str,
        size: int,
        parent_id: str,
        knowledge_base_id: int,
        principal_id: int,
        principal_type: str,
        description: Optional[str] = None,
        chunk_size: int = 0,
    ) -> File:
        parent_file = await self.file_repo.get_file_by_id(parent_id)
        location = parent_file.location.rstrip("/") + "/" + name

        file = File(
            name=name,
            description=description,
            type=type,
            size=size,
            location=location,
            principal_id=principal_id,
            principal_type=principal_type,
            parent_id=parent_id,
            knowledge_base_id=knowledge_base_id,
            chunk_size=chunk_size,
        )
        # TODO: upload file to vdb and odb
        return await self.file_repo.create_file(file)

    async def get_file_list(self, folder_id: str) -> list[File]:
        return await self.file_repo.get_file_list(folder_id)

    async def remove_file(self, file_id: str, principal_type: str, principal_id: int) -> bool:
        file_list = await self.get_file_list(file_id)
        for file in file_list:
            await self.remove_file(file.id, principal_type, principal_id)
        if await store_service.check_file_exists(principal_type=principal_type, principal_id=principal_id, key=file_id):
            await store_service.delete_object(principal_type=principal_type, principal_id=principal_id, key=file_id)
        return await self.file_repo.remove_file(file_id)

    async def move_file(self, file_id: str, dest_folder_id: str) -> bool:
        if not await self.file_repo.move_file(file_id, dest_folder_id):
            logger.error(f"failed to move file {file_id} to {dest_folder_id}")
            return False
        await self.fix_file_location(file_id)
        return True

    async def get_file_by_id(self, file_id: str) -> Optional[File]:
        return await self.file_repo.get_file_by_id(file_id)

    async def rename_file(self, file_id: str, new_name: str) -> bool:
        if not await self.file_repo.rename_file(file_id, new_name):
            logger.error(f"failed to rename file {file_id} to {new_name}")
            return False
        await self.fix_file_location(file_id)
        return True

    async def rename_root_file(self, file_id: str, new_name: str) -> bool:
        return await self.file_repo.rename_file(file_id, new_name)

    async def get_parent_id(self, file_id: str) -> Optional[str]:
        return await self.file_repo.get_parent_id(file_id)

    async def get_all_parent_folders(self, file_id: str) -> list[File]:
        file = await self.get_file_by_id(file_id)
        parent_folders = []
        while file.parent_id is not None:
            file = await self.get_file_by_id(file.parent_id)
            parent_folders.append(file)
        return parent_folders

    async def fix_file_location(self, file_id: str) -> None:
        await self.file_repo.fix_file_location(file_id)
        file_list = await self.get_file_list(file_id)
        for file in file_list:
            await self.fix_file_location(file.id)

    async def update_file_chunk_size(self, file_id: str, chunk_size: int) -> None:
        await self.file_repo.update_file_chunk_size(file_id, chunk_size)


file_service = FileService()
