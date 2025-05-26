import os
import re
import os
import numpy as np
from typing import Any, Dict, Optional, Tuple, List
from ragnarok_toolkit.component import (
    ComponentInputTypeOption,
    ComponentIOType,
    ComponentOutputTypeOption,
    RagnarokComponent,
)
from langchain import CharacterTextSpliter, RecursiveCharacterTextSplitter
import httpx
import asyncio

class UnsupportedFileTypeError(Exception):
    """When the file type is not in the supported list, this exception is thrown."""


class TextSplitComponent(RagnarokComponent):
    DESCRIPTION: str = "txt_split_component"
    ENABLE_HINT_CHECK: bool = True

    @classmethod
    def input_options(cls) -> Tuple[ComponentInputTypeOption, ...]:
        return (
            ComponentInputTypeOption(
                name="file_type",
                allowed_types={ComponentIOType.STRING},
                required=True,
            ),
            ComponentInputTypeOption(
                name="file_byte",
                allowed_types={ComponentIOType.BYTES},
                required=True,
            ),
            ComponentInputTypeOption(
                name="split_type",
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
            ComponentOutputTypeOption(name="text", type=ComponentIOType.LIST_STRING),
        )


    @classmethod
    def execute(cls, file_type: str, file_byte: bytes, split_type: str) -> Dict[str, List[str]]:
        """Main execution method for processing the text content and splitting text."""
        file_type = file_type.lower()
        text = cls.extract_text(file_type, file_byte)
        chunks = []
        if split_type == "character_split" :
            """Split the file by chunk size"""""
            chunks = cls.common_split(text)
        elif split_type == "recursive_split" :
            chunks = cls.recursive_split(text)
        elif split_type == "semantic_split" :
            chunks = cls.semantic_splitting(text)
        else :
            chunks = []

        return {"text_chunks": chunks}


    @staticmethod
    def extract_text(file_type: str, file_byte: bytes) -> str:
        text = ""
        if file_type == "txt" :
            text = file_byte.decode("utf-8")
        elif file_type == "pdf" :
            text = "pdf"
        elif file_type == "image" :
            text = "image"
        return text

    @staticmethod
    def common_split(text: str) -> List[str]:
        text_spliter = CharacterTextSpliter(
            chunk_size = 512,
            chunk_overlap = 128,
            separators = ["\n\n", "\n", "。", "！", "？", ".", "!", "?"]
        )
        return text_spliter(text)

    @staticmethod
    def recursive_split(text: str) -> List[str]:
        text_spliter = RecursiveCharacterTextSplitter(
            chunk_size=512,
            chunk_overlap=128,
            separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?"]
        )
        return text_spliter(text)

    @classmethod
    def semantic_splitting(cls, text: str) -> List[str]:
        chunks = []
        sentences = cls.split_sentences(text)

        sentences = cls.combine_sentences(sentences)

        sentences = cls.embed_sentences(sentences)

        sentences = cls.compute_distances(sentences)

        chunks = cls.chunk_sentences(sentences)

        return chunks

    @staticmethod
    def split_sentences(text: str) -> List[Dict]:
        single_sentences_list = re.split(r'(?<=[。！？；])', text)
        # 转换正字典列表
        sentences = [{'sentence': x, 'index': i} for i, x in enumerate(single_sentences_list)]
        sentences[:3]
        return sentences
    @staticmethod
    def combine_sentences(sentences: List[Dict], buffer_size: int = 1) -> List[Dict]:
        combined_sentences = [
            ' '.join(
                sentences[j]['sentence'] for j in range(max(i - buffer_size, 0), min(i + buffer_size, len(sentences))))
            for i in range(len(sentences))
        ]
        # 更新原始字典列表，添加组合后的句子
        for i, combined_sentence in enumerate(combined_sentences):
            sentences[i]['combined_sentence'] = combined_sentence

        return sentences

    @staticmethod
    def embed_sentences(sentences: List[Dict]) -> List[Dict]:
        combined_texts = [x['combined_sentence'] for x in sentences]

        API_URL = "https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/text-embedding"
        API_KEY = "sk-7ce272f166b84698b4a397b681065c7c"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }

        payload = {
            "model": "text-embedding-v1",
            "input": combined_texts
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(API_URL, headers=headers, json=payload)
                response.raise_for_status()
                res_data = response.json()
                embeddings = [item["embedding"] for item in res_data["output"]["embeddings"]]
        except Exception as e:
            print("获取嵌入失败:", e)
            return []

        for i in range(len(sentences)):
            sentences[i]['combined_sentence_embedding'] = embeddings[i]


        return sentences

    @staticmethod
    def cos_similarity(vec1: List[float], vec2: List[float]) -> float:
        vec1_arr = np.array(vec1)
        vec2_arr = np.array(vec2)
        return float(np.dot(vec1_arr, vec2_arr) / (np.linalg.norm(vec1_arr) * np.linalg.norm(vec2_arr)))

    @classmethod
    def compute_distances(cls, sentences: List[Dict]) -> List[Dict]:
        distances = []
        for i in range(len(sentences) - 1):
            sim = cls.cos_similarity(
                sentences[i]['combined_sentence_embedding'],
                sentences[i + 1]['combined_sentence_embedding']
            )
            distance = 1 - sim
            sentences[i]['distance_to_next'] = distance
            distances.append(distance)
        return sentences

    @staticmethod
    def chunk_sentences(sentences: List[Dict], threshold: float = 0.15) -> List[str]:
        chunks = []
        current_chunk = [sentences[0]['sentence']]
        for i in range(1, len(sentences)):
            if sentences[i - 1].get('distance_to_next', 0) > threshold:
                chunks.append("".join(current_chunk))
                current_chunk = []
            current_chunk.append(sentences[i]['sentence'])
        if current_chunk:
            chunks.append("".join(current_chunk))
        return chunks



