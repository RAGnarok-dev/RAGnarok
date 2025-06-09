# /ragnarok_server/rdb/repositories/knowledge_base.py
from typing import List, Optional

from ragnarok_server.rdb.engine import get_async_session
from ragnarok_server.rdb.models import KnowledgeBase
from sqlalchemy import delete, select, update


class KnowledgeBaseRepository:

    @classmethod
    async def validate_title(cls, title: str, principal_id: int, principal_type: str) -> bool:
        async with get_async_session() as session:
            stmt = select(KnowledgeBase).where(
                KnowledgeBase.title == title,
                KnowledgeBase.principal_id == principal_id,
                KnowledgeBase.principal_type == principal_type,
            )
            result = await session.execute(stmt)
        return result.scalar_one_or_none() is None

    @classmethod
    async def create_knowledge_base(cls, knowledge_base: KnowledgeBase) -> KnowledgeBase:
        async with get_async_session() as session:
            session.add(knowledge_base)
            await session.commit()
            await session.refresh(knowledge_base)
            return knowledge_base

    @classmethod
    async def fix_kb_root_file_id(cls, kb_id: int, root_file_id: str) -> bool:
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
    async def get_knowledge_base_list_by_creator(cls, principal_id: int, principal_type: str) -> List[KnowledgeBase]:
        async with get_async_session() as session:
            stmt = select(KnowledgeBase).where(
                KnowledgeBase.principal_id == principal_id, KnowledgeBase.principal_type == principal_type
            )
            result = await session.execute(stmt)
        return result.scalars().all()

    @classmethod
    async def retitle_knowledge_base(cls, id: int, new_title: str) -> bool:
        async with get_async_session() as session:
            stmt = update(KnowledgeBase).where(KnowledgeBase.id == id).values(title=new_title)
            result = await session.execute(stmt)
        return result.rowcount > 0

    @classmethod
    async def get_all_knowledge_bases(cls, id: int, type: str) -> List[KnowledgeBase]:
        """
        获取所有知识库
        Returns:
            List[KnowledgeBase]: 知识库列表
        """
        async with get_async_session() as session:
            stmt = select(KnowledgeBase)
            result = await session.execute(stmt)
        return result.scalars().all()

    @classmethod
    async def modify_knowledge_base(
        cls,
        kb_id: int,
        title: Optional[str],
        description: Optional[str],
        embedding_model_name: Optional[str],
        split_type: Optional[str],
    ) -> bool:
        async with get_async_session() as session:
            stmt = update(KnowledgeBase).where(KnowledgeBase.id == kb_id)
            if title is not None:
                stmt = stmt.values(title=title)
            if description is not None:
                stmt = stmt.values(description=description)
            if embedding_model_name is not None:
                stmt = stmt.values(embedding_model_name=embedding_model_name)
            if split_type is not None:
                stmt = stmt.values(split_type=split_type)
            result = await session.execute(stmt)
        return result.rowcount > 0
