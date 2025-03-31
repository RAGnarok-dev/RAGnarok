import pytest
from ragnarok_core.components.official_components.text_split_component import text_split_component

def test_text_split_component():
    # Replace with the path to your test PDF file
    test_pdf_path = "test_document.pdf"
    # Execute the text splitting component
    output = text_split_component.execute(test_pdf_path, similarity_threshold=0.15)
    # Assertions to check if the output is as expected
    assert isinstance(output, list), "The output should be a dictionary"
    assert all(isinstance(chunk, str) for chunk in output), "All elements in the output list should be strings"
    assert len(output) > 0, "The text chunks list should not be empty"
