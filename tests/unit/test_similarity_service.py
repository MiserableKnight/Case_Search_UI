"""
SimilarityService单元测试

测试相似度计算服务层的各种功能
"""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from app.core.error_handler import ServiceError, ValidationError
from app.services.similarity_service import SimilarityService


class TestSimilarityService:
    """SimilarityService测试类"""

    def setup_method(self):
        """每个测试方法前执行"""
        self.service = SimilarityService()

    # ==================== 初始化测试 ====================

    def test_init(self):
        """测试初始化"""
        service = SimilarityService()
        assert service.config is None or isinstance(service.config, dict)

    def test_init_with_config(self):
        """测试带配置初始化"""
        config = {"test": "value"}
        service = SimilarityService(config)
        assert service.config == config

    # ==================== calculate_batch_similarity测试 ====================

    def test_calculate_batch_similarity_normal(self, sample_similarity_data):
        """测试批量计算相似度"""
        query_text = "发动机故障"
        columns = ["标题", "问题描述"]

        result = self.service.calculate_batch_similarity(
            query_text, sample_similarity_data, columns
        )

        assert isinstance(result, list)
        assert len(result) == len(sample_similarity_data)
        assert "相似度" in result[0]

    def test_calculate_batch_similarity_empty_query(self, sample_similarity_data):
        """测试空查询文本"""
        with pytest.raises(ValidationError, match="查询文本不能为空"):
            self.service.calculate_batch_similarity("", sample_similarity_data, ["标题"])

    def test_calculate_batch_similarity_empty_results(self):
        """测试空结果列表"""
        result = self.service.calculate_batch_similarity("查询", [], ["标题"])
        assert result == []

    def test_calculate_batch_similarity_empty_columns(self, sample_similarity_data):
        """测试空列列表"""
        with pytest.raises(ValidationError, match="必须指定至少一个比较列"):
            self.service.calculate_batch_similarity("查询", sample_similarity_data, [])

    def test_calculate_batch_similarity_with_nan_values(self):
        """测试包含NaN值的数据"""
        data = [
            {"标题": "测试1", "描述": None},
            {"标题": None, "描述": "测试2"},
        ]

        result = self.service.calculate_batch_similarity("测试", data, ["标题", "描述"])

        assert isinstance(result, list)
        assert len(result) == 2

    def test_calculate_batch_similarity_calculator_error(self, sample_similarity_data):
        """测试批量计算时的计算器错误"""
        with patch("app.services.similarity_service.TextSimilarityCalculator") as mock_calculator:
            mock_calculator.calculate_similarity.side_effect = Exception("计算错误")

            with pytest.raises(ServiceError, match="批量计算相似度失败"):
                self.service.calculate_batch_similarity("查询", sample_similarity_data, ["标题"])

    def test_calculate_batch_similarity_large_dataset(self):
        """测试大数据集"""
        large_data = [{"标题": f"测试{i}", "描述": f"描述{i}"} for i in range(100)]

        result = self.service.calculate_batch_similarity("测试", large_data, ["标题"])

        assert len(result) == 100

    # ==================== search_by_similarity测试 ====================

    def test_search_by_similarity_normal(self, sample_similarity_data, flask_app):
        """测试正常相似度搜索"""
        # 使用真实的DataFrame
        import pandas as pd
        mock_df = pd.DataFrame(sample_similarity_data)

        # 直接替换Flask app的load_data_source方法
        flask_app.load_data_source = lambda x: mock_df  # type: ignore[attr-defined]

        with flask_app.app_context():
            result = self.service.search_by_similarity(
                "发动机", "test_source", ["标题", "问题描述"], limit=10
            )

            assert isinstance(result, list)
            assert len(result) <= 10

    def test_search_by_similarity_empty_search_text(self, flask_app):
        """测试空搜索文本"""
        with flask_app.app_context():
            with pytest.raises(ValidationError, match="搜索文本不能为空"):
                self.service.search_by_similarity("", "source", ["标题"])

    def test_search_by_similarity_empty_columns(self, flask_app):
        """测试空列列表"""
        with flask_app.app_context():
            with pytest.raises(ValidationError, match="必须指定至少一个搜索列"):
                self.service.search_by_similarity("查询", "source", [])

    def test_search_by_similarity_data_source_not_found(self, flask_app):
        """测试数据源不存在"""
        # 直接替换Flask app的load_data_source方法
        flask_app.load_data_source = lambda x: None  # type: ignore[attr-defined]

        with flask_app.app_context():
            with pytest.raises(ValidationError, match="找不到数据源"):
                self.service.search_by_similarity("查询", "nonexistent", ["标题"])

    def test_search_by_similarity_with_limit(self, sample_similarity_data, flask_app):
        """测试限制结果数量"""
        mock_df = pd.DataFrame(sample_similarity_data)
        flask_app.load_data_source = lambda x: mock_df  # type: ignore[attr-defined]

        with flask_app.app_context():
            limit = 2
            result = self.service.search_by_similarity(
                "发动机", "test_source", ["标题"], limit=limit
            )

            assert len(result) <= limit

    def test_search_by_similarity_no_limit(self, sample_similarity_data, flask_app):
        """测试不限制结果数量"""
        mock_df = pd.DataFrame(sample_similarity_data)
        flask_app.load_data_source = lambda x: mock_df  # type: ignore[attr-defined]

        with flask_app.app_context():
            result = self.service.search_by_similarity(
                "发动机", "test_source", ["标题"], limit=0
            )

            # 应该返回所有结果
            assert len(result) == len(sample_similarity_data)

    def test_search_by_similarity_large_dataset(self, flask_app):
        """测试搜索大数据集"""
        large_data = [{"标题": f"测试{i}", "描述": f"描述{i}"} for i in range(100)]
        mock_df = pd.DataFrame(large_data)
        flask_app.load_data_source = lambda x: mock_df  # type: ignore[attr-defined]

        with flask_app.app_context():
            result = self.service.search_by_similarity("测试", "source", ["标题"], limit=50)

            assert len(result) <= 50


@pytest.mark.parametrize("limit", [1, 5, 10, 0])
def test_search_by_similarity_various_limits(limit, sample_similarity_data, flask_app):
    """参数化测试不同的limit值"""
    mock_df = pd.DataFrame(sample_similarity_data)

    service = SimilarityService()
    flask_app.load_data_source = lambda x: mock_df  # type: ignore[attr-defined]

    with flask_app.app_context():
        result = service.search_by_similarity("查询", "source", ["标题"], limit=limit)

        if limit > 0:
            assert len(result) <= limit
        else:
            assert len(result) == len(sample_similarity_data)
