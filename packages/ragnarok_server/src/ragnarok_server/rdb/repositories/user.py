import logging
from typing import Optional

from passlib.context import CryptContext
from ragnarok_server.rdb.engine import get_async_session
from ragnarok_server.rdb.models import User
from sqlalchemy import select

logger = logging.getLogger(__name__)

# configure your password hashing context (must match how you created password_hash)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# todo: need add tenant
class UserRepository:
    """
    Repository for User authentication and lookup.
    """

    def __init__(self, session_factory=get_async_session):
        self._session_factory = session_factory

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Fetch a User by username.
        """
        async with self._session_factory() as session:  # type: AsyncSession
            stmt = select(User).where(User.username == username)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Fetch a User by its primary key.
        """
        async with self._session_factory() as session:
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def authenticate(self, username: str, password: str) -> Optional[User]:
        """
        Validate credentials. Returns the User if successful, else None.
        """
        user = await self.get_user_by_username(username)
        if not user:
            logger.debug(f"Authentication failed: user {username!r} not found.")
            return None

        if not pwd_context.verify(password, user.password_hash):
            logger.debug(f"Authentication failed: invalid password for {username!r}.")
            return None

        return user
