# ragnarok_server/service/user.py

from typing import Optional
from pydantic import EmailStr
from ragnarok_server.rdb.repositories.user import UserRepository
from ragnarok_server.rdb.repositories.tenant import TenantRepository
from ragnarok_server.rdb.models import User
from ragnarok_server.exceptions import DuplicateEntryError, NoResultFoundError, InvalidArgsError
from ragnarok_server.auth import create_access_token


class UserService:
    """
    Service for handling User-related business logic.
    """

    def __init__(self, repo: UserRepository = UserRepository()):
        self.repo = repo

    async def register_user(
        self, email: EmailStr, password: str, nickname: str, tenant_id: Optional[int] = None
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

    async def login_user(self, email: EmailStr = None, username: str = None, password: str = None) -> dict:
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

        user = await self.repo.authenticate(
            username=username,
            email=email,
            password=password,
        )
        if not user:
            raise InvalidArgsError("Password error")

        token = create_access_token(
            principal_id=user.id,
            principal_type="user"
        )

        return {
            "user": user,
            "access_token": token,
            "token_type": "Bearer"
        }

    @staticmethod
    async def get_user_info(user: User) -> dict:
        if not user:
            raise InvalidArgsError("User does not exist, please log in")

        return {
            "username": user.username,
            "id": user.id,
            "avatar": user.avatar_url,
            "email": user.email

        }

    async def update_user_avatar(self, user: User, new_avatar_url: str, new_username: str) -> User:
        if not user:
            raise NoResultFoundError("User does not exist")

        return await self.repo.update_user_avatar(user.id, new_avatar_url, new_username)

    async def join_tenant(self, tenant_id: int, user: User,) -> dict:
        if not user:
            raise NoResultFoundError("User does not exist")

        if not tenant_id:
            raise InvalidArgsError("Tenant_id must be provide")

        if user.tenant_id is not None:
            raise DuplicateEntryError("User already belongs to a tenant")

        tenant_repo = TenantRepository()
        tenant = await tenant_repo.get_tenant_by_id(tenant_id)

        if not tenant:
            raise NoResultFoundError("Tenant does not exist")

        cur_user = await self.repo.update_tenant_id(user, tenant_id)
        return {
            "username": cur_user.username,
            "user_id": cur_user.id,
            "tenantname": tenant.name,
            "tenant_id": tenant.id
        }

    async def get_all_users_info(self, user: User) -> dict:
        if not user:
            raise NoResultFoundError("User does not exist")

        tenant_id = user.tenant_id
        tenant_repo = TenantRepository()
        users = await tenant_repo.get_all_users_info(tenant_id)

        tenant = await tenant_repo.get_tenant_by_id(tenant_id)
        if not tenant:
            raise NoResultFoundError("Tenant does not exist")

        return {
            "users": users,
            "tenant": tenant
        }

    async def change_password(self, user: User, password: str, new_password: str) -> User:
        if not user:
            raise NoResultFoundError("User does not exist")

        # if password != user.password_hash:
        #     raise InvalidArgsError("The old password is incorrect")

        return await self.repo.change_password(user.id, new_password)


# Initialize the service instance
user_service = UserService()
