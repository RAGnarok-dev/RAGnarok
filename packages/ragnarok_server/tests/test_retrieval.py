import asyncio
import logging
from typing import List

import pytest
from ragnarok_core.components.official_components.retrieval_component import (
    RetrievalComponent,
)
from ragnarok_toolkit.model.embedding_model import EmbeddingModel, EmbeddingModelEnum
from ragnarok_toolkit.vdb.qdrant_client import QdrantClient

logger = logging.getLogger(__name__)
embedding_model = EmbeddingModelEnum.BGE_SMALL_EN_V1_5
qdrant_client = QdrantClient()

@pytest.mark.asyncio
async def delete_vdb(embedding_model_name: str):
    await qdrant_client.delete_collection(embedding_model_name)

@pytest.mark.asyncio
async def store_vdb(texts: List[str]):

    vectors = await EmbeddingModel.embedding(texts, embedding_model)
    if await qdrant_client.init_collection(name=embedding_model.value["name"], dim=embedding_model.value["dim"]):
        logger.info(f"Collection {embedding_model.value['name']} initialized successfully")
    else:
        logger.error(f"Collection {embedding_model.value['name']} already exists")

    await qdrant_client.insert_vectors(
        name=embedding_model.value["name"],
        points=[
            {"vector": vector, "payload": {"db_id": "1", "doc_id": "1", "chunk_id": chunk_id, "text": text}}
            for chunk_id, (vector, text) in enumerate(zip(vectors, texts))
        ],
    )

@pytest.mark.asyncio
async def retrieve_from_vdb(query: str, top_k: int) -> List[str]:
    result = await RetrievalComponent.execute(
        embedding_model_name=embedding_model.value["name"],
        db_id_list=["1"],
        query=query,
        score_threshold=0,
        top_n=top_k,
    )
    return result

@pytest.mark.asyncio
async def test_retrieval():
    # texts you want to store
    texts = [
        """
        今天是一个难得的晴朗天气，阳光明媚，气温在25度左右，
        非常适合户外活动。微风轻拂，空气清新，能见度极佳。
        公园里的花草树木在阳光下显得格外生机勃勃，
        不少市民选择在这个时候出来散步、运动或者野餐。
        气象专家表示，这样的好天气将持续到明天，是进行户外活动的最佳时机。
        """,
        """
        天气预报显示明天将会有阵雨，气温会降至18度。
        气象台已经发布了黄色预警信号，提醒市民做好防范准备。
        建议出门携带雨伞，注意保暖，特别是老人和儿童要适当添加衣物。
        降雨可能会影响交通，建议提前规划出行路线，避开易积水路段。
        同时，也要注意防范雷电等强对流天气带来的影响。
        """,
        """
        这个周末天气晴朗，最高气温可达30度，是今年入夏以来最热的两天。
        气象部门提醒，紫外线指数较高，外出时记得做好防晒措施，涂抹防晒霜，
        戴遮阳帽，穿防晒衣。同时要注意防暑降温，多补充水分，避免在正午时分进行剧烈运动。
        建议在早晚温度较低的时候进行户外活动，中午尽量在室内休息。
        这样的高温天气预计将持续到下周一，之后会有一波冷空气带来降温。
        """,
        """
        中国是一个拥有五千年文明历史的古老国家，其文化底蕴深厚，地域辽阔。
        从北方的长城到南方的桂林山水，从东部的繁华都市到西部的壮丽高原，
        每个地区都有其独特的自然景观和人文特色。近年来，中国在经济发展、
        科技创新、环境保护等方面取得了显著成就，同时也在积极推动传统文化的传承与创新，
        努力实现中华文化的创造性转化和创新性发展。
        """,
        """
        中国的饮食文化源远流长，八大菜系各具特色。川菜的麻辣鲜香、
        粤菜的清淡精致、鲁菜的醇厚浓郁、苏菜的精致细腻，
        每一种菜系都代表着不同地区的饮食特色和文化传统。除了传统美食，
        中国各地还有丰富多样的地方小吃，如北京的烤鸭、上海的小笼包、西安的肉夹馍、
        成都的火锅等，这些美食不仅满足了人们的味蕾，也成为了中国文化的重要名片。
        """,
        """
        中国的传统节日文化丰富多彩，春节、元宵、清明、端午、
        中秋等节日都承载着深厚的文化内涵。以春节为例，这是中国人最重要的传统节日，
        人们会贴春联、放鞭炮、吃团圆饭、发红包，这些习俗都寄托着人们对新年的美好祝愿。
        近年来，随着时代发展，传统节日也在不断创新，比如元宵节的灯会、
        中秋节的月饼文化等，都在保持传统的同时融入了现代元素，让传统文化焕发出新的活力。
        """,
    ]
    # delete vdb
    # await delete_vdb(embedding_model.value["name"])
    # store texts into vdb
    await store_vdb(texts)
    # retrieve from vdb
    result = await retrieve_from_vdb("告诉我周末的天气", 2)
    print(result)

