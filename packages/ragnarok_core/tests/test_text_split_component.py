import pytest
from ragnarok_core.components.official_components.text_split_component import TextSplitComponent

def test_text_split_component():
    # Replace with the path to your test PDF file
    test_pdf_path = "test_document.pdf"
    # Execute the text splitting component
    output = TextSplitComponent.execute(test_pdf_path)
    # Assertions to check if the output is as expected
    assert isinstance(output, list), "The output should be a dictionary"
    assert all(isinstance(chunk, str) for chunk in output), "All elements in the output list should be strings"
    assert len(output) > 0, "The text chunks list should not be empty"
    print(len(output))
    for chunk in output:
        print("_____________________________")
        print(chunk)


