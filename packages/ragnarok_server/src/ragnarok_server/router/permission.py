from functools import wraps

from ragnarok_server.common import ResponseCode
from ragnarok_server.service.knowledge_base import kb_service
from ragnarok_server.service.permission import permission_service


def require_permission(permission_type: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            token = kwargs.get("token")
            knowledge_base_id = kwargs.get("knowledge_base_id")
            if knowledge_base_id is None:
                knowledge_base_id = kwargs.get("request").knowledge_base_id
            kb = await kb_service.get_knowledge_base_by_id(knowledge_base_id)
            if kb is None:
                return ResponseCode.NO_SUCH_RESOURCE.to_response(detail="No such knowledge base")
            if not await permission_service.check_permission(
                principal_id=token.principal_id,
                principal_type=token.principal_type,
                knowledge_base_id=knowledge_base_id,
                permission_type=permission_type,
            ):
                return ResponseCode.ACCESS_DENIED.to_response(
                    detail=f"No permission, need {permission_type} permission"
                )
            return await func(*args, **kwargs)

        return wrapper

    return decorator
