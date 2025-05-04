from typing import Any

from fastapi.encoders import jsonable_encoder
from ragnarok_server.common import ResponseCode
from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class CustomRuntimeError(RuntimeError):
    def __init__(self, message):
        super().__init__(message)


class InternalServerError(CustomRuntimeError): ...


class NoResultFoundError(CustomRuntimeError): ...


class DuplicateEntryError(CustomRuntimeError): ...


class InvalidArgsError(CustomRuntimeError): ...


class AccessDeniedError(CustomRuntimeError): ...


class HTTPException(Exception):
    """
    Custom HTTPException that returns the exception detail as a JSON response.
    """

    def __init__(self, status_code: int, content: Any = None, headers: dict[str, str] | None = None) -> None:
        self.status_code = status_code
        self.content = content
        self.headers = headers


def custom_http_exception_handler(request: Request, exc: HTTPException) -> Response:
    if isinstance(exc.content, (bytes, bytearray)):
        return Response(content=exc.content, status_code=exc.status_code, headers=exc.headers)
    # Treat the content as a pydantic model
    content = jsonable_encoder(exc.content, exclude_none=True)
    return JSONResponse(content=content, status_code=exc.status_code, headers=exc.headers)


def custom_runtime_error_handler(request: Request, exc: RuntimeError) -> Response:
    body = ResponseCode.INTERNAL_SERVER_ERROR.to_response(detail=str(exc))
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    if isinstance(exc, NoResultFoundError):
        body = ResponseCode.NO_SUCH_RESOURCE.to_response(detail=str(exc))
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, DuplicateEntryError):
        body = ResponseCode.DUPLICATE_RESOURCE.to_response(detail=str(exc))
        status_code = status.HTTP_400_BAD_REQUEST
    elif isinstance(exc, InvalidArgsError):
        body = ResponseCode.INVALID_ARGS.to_response(detail=str(exc))
        status_code = status.HTTP_400_BAD_REQUEST
    elif isinstance(exc, AccessDeniedError):
        body = ResponseCode.ACCESS_DENIED.to_response(detail=str(exc))
        status_code = status.HTTP_403_FORBIDDEN

    return JSONResponse(content=jsonable_encoder(body), status_code=status_code)
