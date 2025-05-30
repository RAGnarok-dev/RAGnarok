import logging

import pytest
from ragnarok_core.components.official_components.text_split_component import (
    TextSplitComponent,
)

logger = logging.getLogger(__name__)


# async def test_text_split_component():
#     # Replace with the path to your test PDF file
#     test_dir = os.path.dirname(os.path.abspath(__file__))
#     test_pdf_path = os.path.join(test_dir, "test_document.pdf")
#     with open(test_pdf_path, "rb") as f:
#         test_file_byte = f.read()
#     # Execute the text splitting componentsemantic
#     # character_split、recursive_split、semantic_split
#     output = await TextSplitComponent.execute("application/pdf", test_file_byte, "character_split")
#     # Assertions to check if the output is as expected
#     assert isinstance(output, dict), "The output should be a dictionary"
#     assert all(isinstance(chunk, str) for chunk in output), "All elements in the output list should be strings"
#     assert len(output) > 0, "The text chunks list should not be empty"
#     text_chunks = output["text_chunks"]  # 提取出 chunks 列表
#     logger.info(f"text_chunks: {len(text_chunks)}")
#     for i, chunk in enumerate(text_chunks, 1):
#         logger.info(f"Chunk {i}:\n{chunk}\n{'-' * 40}")


@pytest.mark.asyncio
async def test_text_split_component():
    # 创建一个简单的测试文本，确保每个句子都超过chunk_size
    test_text = "这是第一句.这是第二句.这是第三句." * 50  # 重复50次使文本足够长

    # 测试 recursive_split
    chunks = TextSplitComponent.recursive_split(test_text)

    # 打印每个chunk的内容和长度
    for i, chunk in enumerate(chunks, 1):
        print(f"\nChunk {i} (length: {len(chunk)}):")
        print(chunk)
        print("-" * 40)

    # 验证是否在句号处分割
    for chunk in chunks:
        # 检查chunk中是否包含完整的句子
        assert "." in chunk, "Chunk should contain complete sentences"
        # 检查chunk是否以句号结尾
        assert chunk.strip().endswith("."), "Chunk should end with a period"
