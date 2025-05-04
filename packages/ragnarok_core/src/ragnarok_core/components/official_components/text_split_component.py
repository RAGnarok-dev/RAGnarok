import os
import re
from typing import Dict, List, Tuple

import numpy as np
import pdfplumber
import requests
from ragnarok_toolkit.component import (
    ComponentInputTypeOption,
    ComponentIOType,
    ComponentOutputTypeOption,
    RagnarokComponent,
)


class UnsupportedFileTypeError(Exception):
    """When the file type is not in the supported list, this exception is thrown."""


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
        return (ComponentOutputTypeOption(name="text_chunks", type=ComponentIOType.LIST_STRING),)

    @classmethod
    def execute(cls, pdf_path: str) -> Dict[str, List[str]]:
        """Main execution method for processing the PDF and splitting text."""
        text = cls.extract_text_from_pdf(pdf_path)

        sentences = cls.split_sentences(text)

        sentences = cls.combine_sentences(sentences)

        sentences = cls.embed_sentences(sentences)

        sentences = cls.compute_distances(sentences)

        chunks = cls.chunk_sentences(sentences)

        return {"text_chunks": chunks}

    class UnsupportedFileTypeError(Exception):
        """When the file type is not in the supported list, this exception is thrown."""

    @staticmethod
    def extract_text_from_pdf(pdf_path: str) -> str:
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
        return text

    @staticmethod
    def split_sentences(text: str) -> List[Dict]:
        single_sentences_list = re.split(r"(?<=[。！？；])", text)
        # 转换正字典列表
        sentences = [{"sentence": x, "index": i} for i, x in enumerate(single_sentences_list)]
        sentences[:3]
        return sentences

    @staticmethod
    def combine_sentences(sentences: List[Dict], buffer_size: int = 1) -> List[Dict]:
        combined_sentences = [
            " ".join(
                sentences[j]["sentence"] for j in range(max(i - buffer_size, 0), min(i + buffer_size, len(sentences)))
            )
            for i in range(len(sentences))
        ]
        # 更新原始字典列表，添加组合后的句子
        for i, combined_sentence in enumerate(combined_sentences):
            sentences[i]["combined_sentence"] = combined_sentence

        return sentences

    @staticmethod
    def embed_sentences(sentences: List[Dict]) -> List[Dict]:
        combined_texts = [x["combined_sentence"] for x in sentences]
        API_URL = (
            "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2"
        )
        headers = {"Authorization": "Bearer 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"}

        try:
            response = requests.post(API_URL, headers=headers, json={"inputs": combined_texts})
            response.raise_for_status()
            embeddings = response.json()
        except Exception as e:
            print("获取嵌入失败:", e)
            return []

        for i in range(len(sentences)):
            sentences[i]["combined_sentence_embedding"] = embeddings[i]

        return sentences

    @staticmethod
    def cos_similarity(vec1, vec2):
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

    @classmethod
    def compute_distances(cls, sentences: List[Dict]) -> List[Dict]:
        distances = []
        for i in range(len(sentences) - 1):
            sim = cls.cos_similarity(
                sentences[i]["combined_sentence_embedding"], sentences[i + 1]["combined_sentence_embedding"]
            )
            distance = 1 - sim
            sentences[i]["distance_to_next"] = distance
            distances.append(distance)
        return sentences

    @staticmethod
    def chunk_sentences(sentences: List[Dict], threshold: float = 0.15) -> List[str]:
        chunks = []
        current_chunk = [sentences[0]["sentence"]]
        for i in range(1, len(sentences)):
            if sentences[i - 1].get("distance_to_next", 0) > threshold:
                chunks.append("".join(current_chunk))
                current_chunk = []
            current_chunk.append(sentences[i]["sentence"])
        if current_chunk:
            chunks.append("".join(current_chunk))
        return chunks

    """Identifying file types through file suffixes"""

    @staticmethod
    def get_file_type(file_path: str) -> str:
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        if ext == ".md":
            return "markdown"
        elif ext == ".pdf":
            return "pdf"
        elif ext == ".doc" or ext == ".docx":
            return "word"
        else:
            raise UnsupportedFileTypeError(f"Unsupported file type: {ext}")

    @staticmethod
    def pdf2md(pdf_path: str) -> str:
        """translate pdf to md by Mineru"""
