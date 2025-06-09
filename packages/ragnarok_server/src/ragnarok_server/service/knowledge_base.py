import logging
from typing import List, Optional

from ragnarok_server.rdb.models import KnowledgeBase
from ragnarok_server.rdb.repositories.knowledge_base import KnowledgeBaseRepository
from ragnarok_server.rdb.repositories.permission import PermissionRepository

logger = logging.getLogger(__name__)


class KnowledgeBaseService:
    kb_repo: KnowledgeBaseRepository

    def __init__(self) -> None:
        self.kb_repo = KnowledgeBaseRepository()

    async def validate_title(self, title: str, principal_id: int, principal_type: str) -> bool:
        return await self.kb_repo.validate_title(title, principal_id, principal_type)

    async def create_knowledge_base(
        self,
        title: str,
        description: str,
        embedding_model_name: str,
        split_type: str,
        principal_id: int,
        principal_type: str,
    ) -> KnowledgeBase:
        kb = KnowledgeBase(
            title=title,
            description=description,
            embedding_model_name=embedding_model_name,
            split_type=split_type,
            root_file_id="",
            principal_id=principal_id,
            principal_type=principal_type,
        )
        return await self.kb_repo.create_knowledge_base(kb)

    async def fix_kb_root_file_id(self, kb_id: int, root_file_id: str) -> bool:
        return await self.kb_repo.fix_kb_root_file_id(kb_id, root_file_id)

    async def get_knowledge_base_by_id(self, id: int) -> KnowledgeBase:
        return await self.kb_repo.get_knowledge_base_by_id(id)

    async def get_knowledge_base_list_by_creator(self, principal_id: int, principal_type: str) -> List[KnowledgeBase]:
        return await self.kb_repo.get_knowledge_base_list_by_creator(principal_id, principal_type)

    async def remove_knowledge_base(self, id: int) -> bool:
        return await self.kb_repo.remove_knowledge_base(id)

    async def retitle_knowledge_base(self, id: int, new_title: str) -> bool:
        return await self.kb_repo.retitle_knowledge_base(id, new_title)

    async def get_all_knowledge_bases(self, principal_id: int, principal_type: str) -> List[dict]:
        """
        获取当前用户或者租户的所有知识库
        Returns:
            List[KnowledgeBase]: 知识库列表
        """
        result = await PermissionRepository.get_all_knowledge_bases_by_id(principal_id, principal_type)

        kbs=[]
        for kb_id, permission in result.items():
            kb = await self.kb_repo.get_knowledge_base_by_id(kb_id)
            if kb:
                kbs.append({
                    "id": kb.id,
                    "title": kb.title,
                    "description": kb.description,
                    "embedding_model_name": kb.embedding_model_name,
                    "split_type": kb.split_type,
                    "root_file_id": kb.root_file_id,
                    "permission": permission,
                    "principal_id": kb.principal_id,
                    "principal_type": kb.principal_type
                })

        return kbs

    async def modify_knowledge_base(
        self,
        kb_id: int,
        title: Optional[str],
        description: Optional[str],
        embedding_model_name: Optional[str],
        split_type: Optional[str],
    ) -> bool:
        return await self.kb_repo.modify_knowledge_base(kb_id, title, description, embedding_model_name, split_type)

    async def update_avatar(self, knowledge_base_id: int, new_avatar: str) -> KnowledgeBase:
        return await self.kb_repo.update_avatar(knowledge_base_id, new_avatar)


kb_service = KnowledgeBaseService()
