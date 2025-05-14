from typing import Any, Callable, Dict, Optional

from fastapi import APIRouter
from pydantic import BaseModel, EmailStr

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