import re
import numpy as np
import pdfplumber
from sentence_transformers import SentenceTransformer
from typing import Any, Dict, Optional, Tuple, List
from ragnarok_toolkit.component import (
    ComponentInputTypeOption,
    ComponentIOType,
    ComponentOutputTypeOption,
    RagnarokComponent,
)



class TextSplitComponent(RagnarokComponent):
    DESCRIPTION: str = "txt_split_component"
    ENABLE_HINT_CHECK: bool = True

    @classmethod
    def input_options(cls) -> Tuple[ComponentInputTypeOption, ...]:
        return (
            ComponentInputTypeOption(
                name="pdf_path",
                allowed_types={ComponentIOType.STRING},
                required=True,
            ),
            # ComponentInputTypeOption(
            #     name="similarity_threshold",
            #     allowed_types={ComponentIOType.FLOAT},
            #     required=False,
            # ),
        )

    @classmethod
    def output_options(cls) -> Tuple[ComponentOutputTypeOption, ...]:
        return (
            ComponentOutputTypeOption(name="text_chunks", type=ComponentIOType.LIST_STRING),
        )


    @classmethod
    def execute(cls, pdf_path: str) -> Dict[str, List[str]]:
        """Main execution method for processing the PDF and splitting text."""
        similarity_threshold = 0.5
        text = cls.extract_text_from_pdf(pdf_path)
        sentences = cls.process_text(text)
        text_chunks = cls.split_by_similarity(sentences, similarity_threshold)

        return {"text_chunks": text_chunks}

    @staticmethod
    def extract_text_from_pdf(pdf_path: str) -> str:
        """Extracts text from a PDF file."""
        with pdfplumber.open(pdf_path) as pdf:
            return "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())

    @classmethod
    def process_text(cls, text: str) -> List[Dict[str, Any]]:
        oaiembeds = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        """Splits text into sentences, generates embeddings, and calculates similarity scores."""
        sentences = [{"sentence": s, "index": i} for i, s in enumerate(re.split(r'(?<=[。！？；])', text)) if s.strip()]

        # Generate sentence embeddings
        embeddings = oaiembeds.encode([s["sentence"] for s in sentences], convert_to_list=True)
        for i, emb in enumerate(embeddings):
            sentences[i]["embedding"] = emb

        # Compute cosine similarities
        for i in range(len(sentences) - 1):
            sentences[i]["similarity"] = cls.cosine_similarity(sentences[i]["embedding"], sentences[i + 1]["embedding"])

        return sentences

    @staticmethod
    def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Computes the cosine similarity between two vectors."""
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

    @classmethod
    def split_by_similarity(cls, sentences: List[Dict[str, Any]], threshold: float) -> List[str]:
        """Splits text into chunks based on cosine similarity scores."""
        chunks, current_chunk = [], [sentences[0]["sentence"]]

        for i in range(1, len(sentences)):
            if sentences[i - 1]["similarity"] < threshold:
                chunks.append("".join(current_chunk))
                current_chunk = []
            current_chunk.append(sentences[i]["sentence"])

        if current_chunk:
            chunks.append("".join(current_chunk))

        return chunks


