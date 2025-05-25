from typing import List, Optional

from ragnarok_server.rdb.engine import get_async_session
from ragnarok_server.rdb.models import LLMSession
from sqlalchemy import delete, select, update


class LLMSessionRepository:
    @classmethod
    async def create_session(cls, session_obj: LLMSession) -> LLMSession:
        async with get_async_session() as session:
            session.add(session_obj)
            return session_obj

    @classmethod
    async def get_session_by_id(cls, session_id: int) -> Optional[LLMSession]:
        async with get_async_session() as session:
            stmt = select(LLMSession).where(LLMSession.id == session_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    @classmethod
    async def get_sessions_by_creator(cls, created_by: str) -> List[LLMSession]:
        async with get_async_session() as session:
            stmt = select(LLMSession).where(LLMSession.created_by == created_by)
            result = await session.execute(stmt)
            return result.scalars().all()

    @classmethod
    async def update_dialog_history(cls, session_id: int, new_history: dict) -> bool:
        async with get_async_session() as session:
            stmt = select(LLMSession).where(LLMSession.id == session_id)
            result = await session.execute(stmt)
            old_session = result.scalar_one_or_none()
            history: dict = old_session.history
            history["messages"].extend(new_history["messages"])
            stmt = update(LLMSession).where(LLMSession.id == session_id).values(history=history)
            result = await session.execute(stmt)
            return result.rowcount > 0

    @classmethod
    async def delete_session(cls, session_id: int) -> bool:
        async with get_async_session() as session:
            stmt = delete(LLMSession).where(LLMSession.id == session_id)
            result = await session.execute(stmt)
            return result.rowcount > 0

    @classmethod
    async def get_all_sessions(cls) -> List[LLMSession]:
        async with get_async_session() as session:
            stmt = select(LLMSession)
            result = await session.execute(stmt)
            return result.scalars().all()

    @classmethod
    async def delete_all_session(cls) -> bool:
        async with get_async_session() as session:
            stmt = delete(LLMSession)
            result = await session.execute(stmt)
            return result.rowcount > 0
