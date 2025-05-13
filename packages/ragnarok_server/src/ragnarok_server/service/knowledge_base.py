import logging
from typing import List

from ragnarok_server.rdb.models import KnowledgeBase
from ragnarok_server.rdb.repositories.knowledge_base import KnowledgeBaseRepository

logger = logging.getLogger(__name__)


class KnowledgeBaseService:
    kb_repo: KnowledgeBaseRepository

    def __init__(self) -> None:
        self.kb_repo = KnowledgeBaseRepository()

    async def validate_title(self, title: str, created_by: str) -> bool:
        return await self.kb_repo.validate_title(title, created_by)

    async def create_knowledge_base(
        self, title: str, description: str, embedding_model_id: int, created_by: str
    ) -> KnowledgeBase:
        kb = KnowledgeBase(
            title=title,
            description=description,
            embedding_model_id=embedding_model_id,
            root_file_id=0,
            created_by=created_by,
        )
        return await self.kb_repo.create_knowledge_base(kb)

    async def fix_kb_root_file_id(self, kb_id: int, root_file_id: int) -> bool:
        return await self.kb_repo.fix_kb_root_file_id(kb_id, root_file_id)

    async def get_knowledge_base_by_id(self, id: int) -> KnowledgeBase:
        return await self.kb_repo.get_knowledge_base_by_id(id)

    async def get_knowledge_base_list_by_creator(self, created_by: str) -> List[KnowledgeBase]:
        return await self.kb_repo.get_knowledge_base_list_by_creator(created_by)

    async def remove_knowledge_base(self, id: int) -> bool:
        return await self.kb_repo.remove_knowledge_base(id)

    async def retitle_knowledge_base(self, id: int, new_title: str) -> bool:
        return await self.kb_repo.retitle_knowledge_base(id, new_title)

    async def get_all_knowledge_bases(self) -> List[KnowledgeBase]:
        """
        获取所有知识库
        Returns:
            List[KnowledgeBase]: 知识库列表
        """
        return await self.kb_repo.get_all_knowledge_bases()


kb_service = KnowledgeBaseService()
