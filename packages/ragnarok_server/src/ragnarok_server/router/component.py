from ragnarok_server.common import ListResponseData, Response, ResponseCode
from ragnarok_server.router.base import ComponentDetailModel, CustomAPIRouter
from ragnarok_server.service.component import component_service

router = CustomAPIRouter(prefix="/components", tags=["Component"])


@router.get("", response_model=Response[ListResponseData[ComponentDetailModel]])
async def list_components() -> Response[ListResponseData[ComponentDetailModel]]:
    datas = component_service.list_components()
    return ResponseCode.OK.to_response(
        data=ListResponseData(
            count=len(datas),
            items=[ComponentDetailModel.from_dict(data) for data in datas.values()],
        )
    )
