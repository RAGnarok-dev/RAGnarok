from typing import Any, Dict, List, Tuple

import requests
from ragnarok_toolkit.component import (
    ComponentInputTypeOption,
    ComponentIOType,
    ComponentOutputTypeOption,
    RagnarokComponent,
)


class EmbeddingComponent(RagnarokComponent):
    DESCRIPTION: str = "embedding"
    ENABLE_HINT_CHECK: bool = True

    HF_API_URL = (
        "https://router.huggingface.co/hf-inference/models/sentence-transformers/all-MiniLM-L6-v2/pipeline/feature-extraction"
    )
    HEADERS = {"Authorization": "Bearer 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"}

    @classmethod
    def input_options(cls) -> Tuple[ComponentInputTypeOption, ...]:
        return (
            ComponentInputTypeOption(
                name="text_chunks",
                allowed_types={ComponentIOType.STRING_LIST},
                required=True,
            ),
        )

    @classmethod
    def output_options(cls) -> Tuple[ComponentOutputTypeOption, ...]:
        return (ComponentOutputTypeOption(name="vectors", type=ComponentIOType.FLOAT_LIST_LIST),)

    @classmethod
    def execute(cls, text_chunks: List[str]) -> Dict[str, Any]:

        data = {"inputs": text_chunks}

        try:
            response = requests.post(cls.HF_API_URL, headers=cls.HEADERS, json=data)
            if response.status_code != 200:
                return {
                    "vectors": [[-1.0]],  # 或者你可以选择抛出异常
                    "error": f"HuggingFace API error: {response.status_code} - {response.text}",
                }
            vectors = response.json()
            return {"vectors": vectors}
        except Exception as e:
            return {"vectors": [[-1.0]], "error": str(e)}
