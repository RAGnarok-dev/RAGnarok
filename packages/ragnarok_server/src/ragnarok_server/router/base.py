from typing import Any, Callable, Dict, Optional

from fastapi import APIRouter

from pydantic import BaseModel,EmailStr
from ragnarok_server.rdb.models import Pipeline
import json

class CustomAPIRouter(APIRouter):
    """
    Custom APIRouter that excludes None values from response models by default.
    """

    def get(self, path: str, *, response_model_exclude_none: bool = True, **kwargs: Any) -> Callable:
        return super().get(path, response_model_exclude_none=response_model_exclude_none, **kwargs)

    def post(self, path: str, *, response_model_exclude_none: bool = True, **kwargs: Any) -> Callable:
        return super().post(path, response_model_exclude_none=response_model_exclude_none, **kwargs)

    def put(self, path: str, *, response_model_exclude_none: bool = True, **kwargs: Any) -> Callable:
        return super().put(path, response_model_exclude_none=response_model_exclude_none, **kwargs)

    def delete(self, path: str, *, response_model_exclude_none: bool = True, **kwargs: Any) -> Callable:
        return super().delete(path, response_model_exclude_none=response_model_exclude_none, **kwargs)

    def patch(self, path: str, *, response_model_exclude_none: bool = True, **kwargs: Any) -> Callable:
        return super().patch(path, response_model_exclude_none=response_model_exclude_none, **kwargs)


class ComponentDetailModel(BaseModel):
    name: str
    is_official: bool
    detail: Dict[str, Any]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ComponentDetailModel":
        return cls(name=data["name"], is_official=data["is_official"], detail=data["detail"])


class UserRegisterRequestModel(BaseModel):
    email: EmailStr
    username: str
    password: str


class UserRegisterResponseModel(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_active: bool


class UserLoginRequestModel(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: str


class UserLoginResponseModel(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_active: bool
    access_token: str
    token_type: str


class UserInfoResponseModel(BaseModel):
    username: str
    id: int
    avatar: str


class UserJoinTenantRequestModel(BaseModel):
    tenant_id: str


class UserJoinTenantResponseModel(BaseModel):
    username: str
    user_id: str
    tenantname: str
    tenant_id: str


class TenantRegisterRequestModel(BaseModel):
    email: EmailStr
    tenantname: str
    password: str


class TenantRegisterResponseModel(BaseModel):
    id: int
    tenantname: str
    email: EmailStr
    is_active: bool


class TenantLoginRequestModel(BaseModel):
    tenantname: Optional[str] = None
    email: Optional[EmailStr] = None
    password: str


class TenantLoginResponseModel(BaseModel):
    id: int
    tenantname: str
    email: EmailStr
    is_active: bool
    access_token: str
    token_type: str

class TenantInviteRequestModel(BaseModel):
    tenant_id: int
    user_email: EmailStr

class TenantInviteResponseModel(BaseModel):
    user_id: int
    username: str
    user_email: EmailStr
    tenant_id: int


class TenantRemoveUserRequestModel(BaseModel):
    tenant_id: int
    user_email: EmailStr

class TenantRemoveUserResponseModel(BaseModel):
    user_id: int
    username: str
    user_email: EmailStr
    tenant_id: int

class TenantInfoResponseModel(BaseModel):
    tenantname: str
    id: int
    avatar: str


class TenantGetUsersResponseModel(BaseModel):
    tenantname: str
    tenant_id: int
    users: list[UserInfoResponseModel]


class PipelineDetailModel(BaseModel):
    id: int
    name: str
    principal_id: int
    principal_type: str
    content: str
    description: str | None
    avatar: str | None
    params: Optional[Dict[str, Any]] = None

    @classmethod
    def from_pipeline(cls, pipeline: Pipeline) -> "PipelineDetailModel":
        return cls(
            id=pipeline.id,
            name=pipeline.name,
            principal_id=pipeline.principal_id,       
            principal_type=pipeline.principal_type,   
            content=pipeline.content,
            description=pipeline.description,
            avatar=pipeline.avatar,
            params=json.loads(pipeline.params) if pipeline.params else None, 
        )