import logging
import unittest
from unittest.mock import MagicMock, patch

from ragnarok_core.components.official_components.embedding_component import (
    EmbeddingComponent,
)

logger = logging.getLogger(__name__)


def test_embedding_component_execute_basic():
    # 输入可以是单个句子或句子列表
    input_text = [
        "为什么良好的睡眠对健康至关重要",
        "良好的睡眠有助于身体修复自身,增强免疫系统",
        "在监督学习中，算法经常需要大量的标记数据来进行有效学习",
        "睡眠不足可能导致长期健康问题,如心脏病和糖尿病",
        "这种学习方法依赖于数据质量和数量",
        "它帮助维持正常的新陈代谢和体重控制",
        "睡眠对儿童和青少年的大脑发育和成长尤为重要",
        "良好的睡眠有助于提高日间的工作效率和注意力",
        "监督学习的成功取决于特征选择和算法的选择",
        "量子计算机的发展仍处于早期阶段，面临技术和物理挑战",
        "量子计算机与传统计算机不同，后者使用二进制位进行计算",
        "机器学习使我睡不着觉",
    ]

    result = EmbeddingComponent.execute(input_text)

    logger.info(f"Output: {result}")


class TestEmbeddingComponent(unittest.TestCase):

    @patch("requests.post")
    def test_execute_with_multiple_sentences(self, mock_post):
        # 模拟 Hugging Face API 的响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        mock_post.return_value = mock_response

        sentences = ["Sentence 1", "Sentence 2"]

        # 执行 execute 方法
        result = EmbeddingComponent.execute(sentences)

        # 检查返回的 embeddings 是否与预期一致
        self.assertEqual(result["embeddings"], [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
        self.assertNotIn("error", result)


if __name__ == "__main__":
    unittest.main()
