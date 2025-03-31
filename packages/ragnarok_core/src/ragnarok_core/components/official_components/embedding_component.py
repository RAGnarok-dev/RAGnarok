import requests
from typing import Any, Dict, Tuple

from ragnarok_toolkit.component import (
    ComponentInputTypeOption,
    ComponentIOType,
    ComponentOutputTypeOption,
    RagnarokComponent,
)

class EmbeddingComponent(RagnarokComponent):
    DESCRIPTION: str = "embedding"
    ENABLE_HINT_CHECK: bool = True

    HF_API_URL = "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2"
    HEADERS = {
        "Authorization": "Bearer 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"
    }

    @classmethod
    def input_options(cls) -> Tuple[ComponentInputTypeOption, ...]:
        return (
            ComponentInputTypeOption(
                name="sentences",
                allowed_types={ComponentIOType.LIST_STRING},
                required=True,
            ),
        )

    @classmethod
    def output_options(cls) -> Tuple[ComponentOutputTypeOption, ...]:
        return (
            ComponentOutputTypeOption(name="embeddings", type=ComponentIOType.LIST_LIST_FLOAT),
        )

    @classmethod
    def execute(cls, sentences: list[str]) -> Dict[str, Any]:

        data = {"inputs": sentences}

        try:
            response = requests.post(cls.HF_API_URL, headers=cls.HEADERS, json=data)
            if response.status_code != 200:
                return {
                    "embeddings": [[-1.0]],  # 或者你可以选择抛出异常
                    "error": f"HuggingFace API error: {response.status_code} - {response.text}"
                }
            embeddings = response.json()
            return {"embeddings": embeddings}
        except Exception as e:
            return {
                "embeddings": [[-1.0]],
                "error": str(e)
            }
