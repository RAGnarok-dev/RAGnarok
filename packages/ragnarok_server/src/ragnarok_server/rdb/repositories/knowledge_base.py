from typing import List

from ragnarok_server.rdb.engine import get_async_session
from ragnarok_server.rdb.models import KnowledgeBase
from sqlalchemy import delete, select, update


class KnowledgeBaseRepository:

    @classmethod
    async def validate_title(cls, title: str, created_by: str) -> bool:
        async with get_async_session() as session:
            stmt = select(KnowledgeBase).where(KnowledgeBase.title == title, KnowledgeBase.created_by == created_by)
            result = await session.execute(stmt)
            return result.scalar_one_or_none() is None

    @classmethod
    async def create_knowledge_base(cls, knowledge_base: KnowledgeBase) -> KnowledgeBase:
        async with get_async_session() as session:
            session.add(knowledge_base)
            return knowledge_base

    @classmethod
    async def fix_kb_root_file_id(cls, kb_id: int, root_file_id: int) -> bool:
        async with get_async_session() as session:
            stmt = update(KnowledgeBase).where(KnowledgeBase.id == kb_id).values(root_file_id=root_file_id)
            result = await session.execute(stmt)
            return result.rowcount > 0

    @classmethod
    async def get_knowledge_base_by_id(cls, id: int) -> KnowledgeBase:
        async with get_async_session() as session:
            stmt = select(KnowledgeBase).where(KnowledgeBase.id == id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    @classmethod
    async def remove_knowledge_base(cls, id: int) -> bool:
        async with get_async_session() as session:
            stmt = delete(KnowledgeBase).where(KnowledgeBase.id == id)
            result = await session.execute(stmt)
            return result.rowcount > 0

    @classmethod
    async def get_knowledge_base_list_by_creator(cls, created_by: str) -> List[KnowledgeBase]:
        async with get_async_session() as session:
            stmt = select(KnowledgeBase).where(KnowledgeBase.created_by == created_by)
            result = await session.execute(stmt)
            return result.scalars().all()

    @classmethod
    async def retitle_knowledge_base(cls, id: int, new_title: str) -> bool:
        async with get_async_session() as session:
            stmt = update(KnowledgeBase).where(KnowledgeBase.id == id).values(title=new_title)
            result = await session.execute(stmt)
            return result.rowcount > 0

    @classmethod
    async def get_all_knowledge_bases(cls) -> List[KnowledgeBase]:
        """
        获取所有知识库
        Returns:
            List[KnowledgeBase]: 知识库列表
        """
        async with get_async_session() as session:
            stmt = select(KnowledgeBase)
            result = await session.execute(stmt)
            return result.scalars().all()
