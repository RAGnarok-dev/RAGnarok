import asyncio
import logging

import pytest
from ragnarok_toolkit.model.embedding_model import EmbeddingModel, EmbeddingModelEnum

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_embedding_model():
    embedding_model = EmbeddingModel()
    texts = ["Hello, world!", "This is a test."]
    vectors = await embedding_model.embedding(texts, model=EmbeddingModelEnum.MULTILINGUAL_E5_LARGE_INSTRUCT)
    logger.info(vectors)
    print(len(vectors))
    print(len(vectors[0]))
    print(type(vectors))
    assert len(vectors) == 2


if __name__ == "__main__":
    asyncio.run(test_embedding_model())
