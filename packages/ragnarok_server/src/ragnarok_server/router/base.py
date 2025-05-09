from typing import Any, Callable, Dict

from fastapi import APIRouter
from pydantic import BaseModel
from ragnarok_server.rdb.models import Pipeline


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


class PipelineDetailModel(BaseModel):
    id: int
    name: str
    tenant_id: int
    content: str
    description: str | None
    avatar: str | None

    @classmethod
    def from_pipeline(cls, pipeline: Pipeline) -> "PipelineDetailModel":
        return cls(
            id=pipeline.id,
            name=pipeline.name,
            tenant_id=pipeline.tenant_id,
            content=pipeline.content,
            description=pipeline.description,
            avatar=pipeline.avatar,
        )
