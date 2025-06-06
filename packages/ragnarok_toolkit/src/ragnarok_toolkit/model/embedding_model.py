from enum import Enum
from typing import List

import aiohttp
from ragnarok_toolkit import config

# embedding model leaderboard:
# https://huggingface.co/spaces/mteb/leaderboard


class EmbeddingModelEnum(Enum):  # small embedding model
    ALL_MINI_LM_L6_V2 = {
        "name": "all-MiniLM-L6-v2",
        "dim": 384,
        "api_url": (
            "https://router.huggingface.co/hf-inference/models/"
            "sentence-transformers/all-MiniLM-L6-v2/pipeline/feature-extraction"
        ),
    }
    BGE_SMALL_EN_V1_5 = {
        "name": "bge-small-en-v1.5",
        "dim": 384,
        "api_url": (
            "https://router.huggingface.co/hf-inference/models/" "BAAI/bge-small-en-v1.5/pipeline/feature-extraction"
        ),
    }
    MULTILINGUAL_E5_LARGE_INSTRUCT = {
        "name": "multilingual-e5-large-instruct",
        "dim": 1024,
        "api_url": (
            "https://router.huggingface.co/hf-inference/models/"
            "intfloat/multilingual-e5-large-instruct/pipeline/feature-extraction"
        ),
    }


class EmbeddingModel:

    HEADERS = {"Authorization": f"Bearer {config.HF_API_KEY}"}

    # 设置代理
    PROXIES = {"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}

    TIMEOUT = 30

    @classmethod
    async def embedding(
        cls, texts: List[str], model: EmbeddingModelEnum = EmbeddingModelEnum.ALL_MINI_LM_L6_V2
    ) -> List[List[float]]:
        data = {"inputs": texts}

        async with aiohttp.ClientSession() as session:
            async with session.post(
                model.value["api_url"],
                headers=cls.HEADERS,
                json=data,
                proxy=cls.PROXIES.get("http"),
                timeout=cls.TIMEOUT,
            ) as response:
                if response.status != 200:
                    return {
                        "vectors": [[-1.0]],
                        "error": f"HuggingFace API error: {response.status} - {await response.text()}",
                    }
                vectors = await response.json()
                return vectors
