# ragnarok_server/service/user.py

from typing import Optional

from ragnarok_server.rdb.repositories.user import UserRepository
from ragnarok_server.rdb.models import User
from ragnarok_server.exceptions import DuplicateEntryError, NoResultFoundError, InvalidArgsError


class UserService:
    """
    Service for handling User-related business logic.
    """

    def __init__(self, repo: UserRepository = UserRepository()):
        self.repo = repo

    async def register_user(
        self, email: str, password: str, nickname: str, tenant_id: Optional[int] = None
    ) -> User:
        # 1) Check if username is already taken
        if await self.repo.get_user_by_username(nickname):
            raise DuplicateEntryError("用户名已被占用")

        # 2) Check if email is already registered
        if await self.repo.get_user_by_email(email):
            raise DuplicateEntryError("邮箱已被注册")

        # 3) Create user
        return await self.repo.create_user(
            username=nickname,
            email=email,
            password=password,
            tenant_id=tenant_id,
        )

    async def login_user(self, email: str = None, username: str = None, password: str = None) -> User:
        if not (username or email):
            raise InvalidArgsError("Must provide either username or email")
        if not password:
            raise InvalidArgsError("Password is required")

        user = None
        if username:
            user = await self.repo.get_user_by_username(username)
        elif email:
            user = await self.repo.get_user_by_email(email)

        if not user:
            raise NoResultFoundError("User not found")

        # # 校验密码
        # if not verify_password(password, user.password):  # 取决于你是否加密保存密码
        #     raise InvalidArgsError("Password error")

        return await self.repo.authenticate(
            username=username,
            email=email,
            password=password,
        )


# Initialize the service instance
user_service = UserService()
