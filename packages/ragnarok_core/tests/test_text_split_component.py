import pytest
import asyncio
from ragnarok_core.components.official_components.text_split_component import TextSplitComponent

@pytest.mark.asyncio
async def test_text_split_component():
    # Replace with the path to your test PDF file
    test_pdf_path = "test_file.txt"
    with open(test_pdf_path, "rb") as f:
        test_file_byte = f.read()
    # Execute the text splitting componentsemantic
    #character_split、recursive_split、semantic_split
    output = await TextSplitComponent.execute("txt", test_file_byte, "semantic_split")
    #output = asyncio.run(TextSplitComponent.execute("txt", test_file_byte, "semantic_split"))
    # Assertions to check if the output is as expected
    assert isinstance(output, dict), "The output should be a dictionary"
    assert all(isinstance(chunk, str) for chunk in output), "All elements in the output list should be strings"
    assert len(output) > 0, "The text chunks list should not be empty"
    text_chunks = output["text_chunks"]  # 提取出 chunks 列表
    print(len(text_chunks))
    for i, chunk in enumerate(text_chunks, 1):
        print(f"Chunk {i}:\n{chunk}\n{'-' * 40}")



