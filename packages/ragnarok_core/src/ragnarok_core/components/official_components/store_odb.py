from typing import Any, Dict, List, Tuple

from ragnarok_core.object_database import minio_client
from ragnarok_toolkit.component import (
    ComponentInputTypeOption,
    ComponentIOType,
    ComponentOutputTypeOption,
    RagnarokComponent,
)


class StoreODB(RagnarokComponent):
    DESCRIPTION: str = "Store Object into Object database"
    ENABLE_HINT_CHECK: bool = True

    @classmethod
    def input_options(cls) -> Tuple[ComponentInputTypeOption, ...]:
        return (
            ComponentInputTypeOption(
                name="bucket_name",
                allowed_types={ComponentIOType.STRING},
                required=True,
            ),
            ComponentInputTypeOption(
                name="chunk_ids",
                allowed_types={ComponentIOType.STRING_LIST},
                required=True,
            ),
            ComponentInputTypeOption(
                name="content_bytes_list",
                allowed_types={ComponentIOType.BYTES_LIST},
                required=True,
            ),
        )

    @classmethod
    def output_options(cls) -> Tuple[ComponentOutputTypeOption, ...]:
        return ()

    @classmethod
    async def execute(cls, bucket_name: str, chunk_ids: List[str], content_bytes_list: List[bytes]) -> Dict[str, Any]:
        for chunk_id, content_bytes in zip(chunk_ids, content_bytes_list):
            await minio_client.upload_object(bucket_name, chunk_id, content_bytes)
        return {}
