from typing import Any, Dict, Tuple

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
                name="object_key",
                allowed_types={ComponentIOType.STRING},
                required=True,
            ),
            ComponentInputTypeOption(
                name="content_bytes",
                allowed_types={ComponentIOType.BYTES},
                required=True,
            ),
        )

    @classmethod
    def output_options(cls) -> Tuple[ComponentOutputTypeOption, ...]:
        return ()

    @classmethod
    async def execute(cls, bucket_name: str, object_key: str, content_bytes: bytes) -> Dict[str, Any]:
        await minio_client.upload_object(bucket_name, object_key, content_bytes)
        return {}
