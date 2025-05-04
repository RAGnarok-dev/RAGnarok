from enum import Enum
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel

DataT = TypeVar("DataT")


class Response(BaseModel, Generic[DataT]):
    code: int
    detail: str
    data: Optional[DataT] = None


class ListResponseData(BaseModel, Generic[DataT]):
    count: int
    items: list[DataT]


class ResponseCode(Enum):
    OK = (0, "OK")
    INTERNAL_SERVER_ERROR = (1, "Internal server error")
    INVALID_ARGS = (100, "Invalid arguments")
    NO_SUCH_RESOURCE = (101, "No such resource")
    RESOURCE_EXPIRED = (102, "Resource expired")
    DUPLICATE_RESOURCE = (103, "Duplicate resource")
    ACCESS_DENIED = (104, "Access denied")

    def to_response(self, *, detail: str | None = None, data: DataT | None = None) -> Response[DataT | None]:
        return Response(code=self.value[0], detail=detail if detail else self.value[1], data=data)
