# /ragnarok_server/rdb/repositories/file.py
from ragnarok_server.rdb.engine import get_async_session
from ragnarok_server.rdb.models import File
from sqlalchemy import delete, select, update


class FileRepository:

    @classmethod
    async def check_file_name(cls, file_name: str, folder_id: str) -> bool:
        async with get_async_session() as session:
            stmt = select(File).where(
                File.parent_id == folder_id,
                File.name == file_name,
            )
            result = await session.execute(stmt)
        return result.scalar_one_or_none() is not None

    @classmethod
    async def create_file(cls, file: File) -> File:
        async with get_async_session() as session:
            session.add(file)
        return file

    @classmethod
    async def get_file_list(cls, folder_id: str) -> list[File]:
        async with get_async_session() as session:
            stmt = select(File).where(File.parent_id.is_(None) if folder_id is None else File.parent_id == folder_id)
            result = await session.execute(stmt)
        return result.scalars().all()

    @classmethod
    async def remove_file(cls, file_id: str):
        async with get_async_session() as session:
            stmt = delete(File).where(File.id == file_id)
            result = await session.execute(stmt)
        return result.rowcount > 0

    @classmethod
    async def get_file_by_id(cls, file_id: str) -> File:
        async with get_async_session() as session:
            stmt = select(File).where(File.id == file_id)
            result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def rename_file(cls, file_id: str, new_name: str):
        async with get_async_session() as session:
            stmt = update(File).where(File.id == file_id).values(name=new_name)
            result = await session.execute(stmt)
        return result.rowcount > 0

    @classmethod
    async def fix_file_location(cls, file_id: str):
        async with get_async_session() as session:
            file = await cls.get_file_by_id(file_id)
            parent_file = await cls.get_file_by_id(file.parent_id)
            file.location = parent_file.location.rstrip("/") + "/" + file.name
            stmt = update(File).where(File.id == file_id).values(location=file.location)
            result = await session.execute(stmt)
        return result.rowcount > 0

    @classmethod
    async def move_file(cls, file_id: str, dest_folder_id: str):
        async with get_async_session() as session:
            stmt = update(File).where(File.id == file_id).values(parent_id=dest_folder_id)
            result = await session.execute(stmt)
        return result.rowcount > 0

    @classmethod
    async def update_file_chunk_size(cls, file_id: str, chunk_size: int):
        async with get_async_session() as session:
            stmt = update(File).where(File.id == file_id).values(chunk_size=chunk_size)
            result = await session.execute(stmt)
        return result.rowcount > 0
