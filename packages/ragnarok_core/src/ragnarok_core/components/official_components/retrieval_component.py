import json
from typing import Dict, List, Optional, Tuple

from openai import AsyncOpenAI
from ragnarok_toolkit.component import (
    ComponentInputTypeOption,
    ComponentIOType,
    ComponentOutputTypeOption,
    RagnarokComponent,
)
from ragnarok_toolkit.model.embedding_model import EmbeddingModel, EmbeddingModelEnum
from ragnarok_toolkit.odb.minio_client import MinioClient
from ragnarok_toolkit.vdb.qdrant_client import QdrantClient

qdrant_client = QdrantClient()
minio_client = MinioClient()


class RetrievalComponent(RagnarokComponent):
    DESCRIPTION: str = "Retrieve documents from vector database and object database"
    ENABLE_HINT_CHECK: bool = True

    @classmethod
    def input_options(cls) -> Tuple[ComponentInputTypeOption, ...]:
        return (
            ComponentInputTypeOption(
                name="embedding_model",
                allowed_types={ComponentIOType.STRING},
                required=True,
            ),
            ComponentInputTypeOption(
                name="db_id_list",
                allowed_types={ComponentIOType.STRING_LIST},
                required=True,
            ),
            ComponentInputTypeOption(
                name="query",
                allowed_types={ComponentIOType.STRING},
                required=True,
            ),
            ComponentInputTypeOption(
                name="score_threshold",
                allowed_types={ComponentIOType.FLOAT},
                required=False,
            ),
            ComponentInputTypeOption(
                name="top_n",
                allowed_types={ComponentIOType.INT},
                required=False,
            ),
            ComponentInputTypeOption(
                name="rerank_model",
                allowed_types={ComponentIOType.STRING},
                required=False,
            ),
            ComponentInputTypeOption(
                name="api_key",
                allowed_types={ComponentIOType.STRING},
                required=False,
            ),
            ComponentInputTypeOption(
                name="base_url",
                allowed_types={ComponentIOType.STRING},
                required=False,
            ),
        )

    @classmethod
    def output_options(cls) -> Tuple[ComponentOutputTypeOption, ...]:
        return ComponentOutputTypeOption(
            name="texts",
            allowed_types={ComponentIOType.STRING_LIST},
            required=True,
        )

    @classmethod
    async def execute(
        cls,
        embedding_model: str,
        db_id_list: List[str],
        query: str,
        score_threshold: Optional[float] = None,
        top_n: Optional[int] = None,
        rerank_model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> Dict[str, List[str]]:
        try:
            embedding_model = EmbeddingModelEnum(embedding_model)
        except ValueError:
            raise ValueError(f"Invalid embedding model: {embedding_model}, no such model in EmbeddingModelEnum")

        query_vector = await cls.embedding(query, embedding_model)

        # default value
        if top_n is None:
            top_n = 10
        if score_threshold is None:
            score_threshold = 0

        if rerank_model is None:
            texts = await cls.retrieve_texts(
                collection_name=embedding_model.value["name"],
                db_id_list=db_id_list,
                query_vector=query_vector,
                score_threshold=score_threshold,
                top_k=top_n,
            )
        else:
            texts = await cls.retrieve_texts(
                collection_name=embedding_model.value["name"],
                db_id_list=db_id_list,
                query_vector=query_vector,
                score_threshold=score_threshold,
                top_k=top_n * 10,
            )
            texts = await cls.rerank_texts(
                query=query, texts=texts, top_n=top_n, rerank_model=rerank_model, api_key=api_key, base_url=base_url
            )
        return {"texts": texts}

    @classmethod
    async def embedding(cls, query: str, model: EmbeddingModelEnum) -> List[float]:
        vector = await EmbeddingModel.embedding([query], model)
        return vector[0]

    @classmethod
    async def retrieve_texts(
        cls,
        collection_name: str,
        db_id_list: List[str],
        query_vector: List[float],
        score_threshold: float = 0,
        top_k: int = 10,
    ) -> List[str]:
        search_pyloads = [
            {
                "db_id": db_id,
            }
            for db_id in db_id_list
        ]
        texts = await qdrant_client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            score_threshold=score_threshold,
            top_k=top_k,
            payload_filters=search_pyloads,
        )
        return texts

    @classmethod
    async def rerank_texts(
        cls, query: str, texts: List[str], top_n: int, rerank_model: str, api_key: str, base_url: str
    ) -> List[str]:
        client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        response = await client.chat.completions.create(
            model=rerank_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that reranks a list of texts based on the query.",
                },
                {
                    "role": "user",
                    "content": f"""
                        请根据以下查询和文本列表，根据问题和文本的相关程度进行打分，打分范围是1~100的整数，分数越高代表相关程度越高。
                        Query: {query}
                        Texts: {texts}
                        严格按照以下格式返回：
                        result: {{
                            {{
                                "text_id": "文本1的id",
                                "score": 分数1
                            }},
                            {{
                                "text_id": "文本2的id",
                                "score": 分数2
                            }},
                            ...
                        }}
                        其中，text_id1、text_id2、... 是文本列表中的文本list中的id，从0开始，分数1、分数2、... 是打分结果。
                        不要输出任何解释，不要输出任何其他内容, 不要输出任何其他字符，和上述格式完全一模一样。
                        """,
                },
            ],
        )
        response_json = response.choices[0].message.content
        try:
            response_json = response_json.split("result:")[1]
            response_json = json.loads(response_json)
        except ValueError:
            raise ValueError(f"Invalid response: {response_json}")

        response_json = sorted(response_json, key=lambda x: x["score"], reverse=True)
        return [texts[int(x["text_id"])] for x in response_json[:top_n]]
