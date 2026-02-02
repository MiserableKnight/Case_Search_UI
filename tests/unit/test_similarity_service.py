"""
SimilarityService单元测试

测试相似度计算服务层的各种功能
"""

from unittest.mock import MagicMock, patch

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

    # ==================== calculate_similarity测试 ====================

    def test_calculate_similarity_normal(self):
        """测试正常计算相似度"""
        text1 = "这是第一段测试文本"
        text2 = "这是第二段测试文本"

        result = self.service.calculate_similarity(text1, text2)

        assert isinstance(result, float)
        # 相似度应该在0-1之间
        assert 0 <= result <= 1

    def test_calculate_similarity_empty_text1(self):
        """测试text1为空"""
        with pytest.raises(ValidationError, match="文本不能为空"):
            self.service.calculate_similarity("", "text2")

    def test_calculate_similarity_empty_text2(self):
        """测试text2为空"""
        with pytest.raises(ValidationError, match="文本不能为空"):
            self.service.calculate_similarity("text1", "")

    def test_calculate_similarity_none_text1(self):
        """测试text1为None"""
        with pytest.raises(ValidationError):
            self.service.calculate_similarity(None, "text2")

    def test_calculate_similarity_with_method(self):
        """测试指定计算方法"""
        text1 = "测试文本"
        text2 = "测试文本"

        result = self.service.calculate_similarity(text1, text2, method="tfidf")
        assert isinstance(result, float)

    def test_calculate_similarity_same_text(self):
        """测试相同文本的相似度"""
        text = "这是测试文本"

        result = self.service.calculate_similarity(text, text)

        # 相同文本应该有较高的相似度
        assert result > 0.5

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

    # ==================== get_available_methods测试 ====================

    def test_get_available_methods(self):
        """测试获取可用方法"""
        methods = self.service.get_available_methods()

        assert isinstance(methods, list)
        assert len(methods) > 0
        # 应该包含默认方法
        assert "tfidf" in methods

    # ==================== preprocess_text测试 ====================

    def test_preprocess_text_normal(self):
        """测试预处理正常文本"""
        text = "这是 测试  文本"
        result = self.service.preprocess_text(text)

        assert isinstance(result, str)
        assert len(result) > 0

    def test_preprocess_text_empty(self):
        """测试预处理空文本"""
        result = self.service.preprocess_text("")
        assert result == ""

    def test_preprocess_text_none(self):
        """测试预处理None文本"""
        result = self.service.preprocess_text(None)
        assert result == ""

    def test_preprocess_text_with_extra_whitespace(self):
        """测试预处理多余空格的文本"""
        text = "  文本   包含   多余   空格  "
        result = self.service.preprocess_text(text)

        assert isinstance(result, str)

    # ==================== search_by_similarity测试 ====================

    def test_search_by_similarity_normal(self, sample_similarity_data, flask_app):
        """测试正常相似度搜索"""
        # Mock current_app.load_data_source
        mock_df = MagicMock()
        mock_df.to_dict.return_value = sample_similarity_data

        with flask_app.app_context():
            with patch("app.services.similarity_service.current_app") as mock_current_app:
                mock_current_app.load_data_source.return_value = mock_df

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
        with flask_app.app_context():
            with patch("app.services.similarity_service.current_app") as mock_current_app:
                mock_current_app.load_data_source.return_value = None

                with pytest.raises(ValidationError, match="找不到数据源"):
                    self.service.search_by_similarity("查询", "nonexistent", ["标题"])

    def test_search_by_similarity_with_limit(self, sample_similarity_data, flask_app):
        """测试限制结果数量"""
        mock_df = MagicMock()
        mock_df.to_dict.return_value = sample_similarity_data

        with flask_app.app_context():
            with patch("app.services.similarity_service.current_app") as mock_current_app:
                mock_current_app.load_data_source.return_value = mock_df

                limit = 2
                result = self.service.search_by_similarity(
                    "发动机", "test_source", ["标题"], limit=limit
                )

                assert len(result) <= limit

    def test_search_by_similarity_no_limit(self, sample_similarity_data, flask_app):
        """测试不限制结果数量"""
        mock_df = MagicMock()
        mock_df.to_dict.return_value = sample_similarity_data

        with flask_app.app_context():
            with patch("app.services.similarity_service.current_app") as mock_current_app:
                mock_current_app.load_data_source.return_value = mock_df

                result = self.service.search_by_similarity(
                    "发动机", "test_source", ["标题"], limit=0
                )

                # 应该返回所有结果
                assert len(result) == len(sample_similarity_data)

    # ==================== 错误处理测试 ====================

    def test_calculate_similarity_calculator_error(self):
        """测试计算器错误时的处理"""
        # Mock一个会抛出异常的计算器
        with patch("app.services.similarity_service.TextSimilarityCalculator") as mock_calculator:
            mock_calculator.calculate_similarity.side_effect = Exception("计算错误")

            with pytest.raises(ServiceError, match="计算相似度失败"):
                self.service.calculate_similarity("text1", "text2")

    def test_calculate_batch_similarity_calculator_error(self, sample_similarity_data):
        """测试批量计算时的计算器错误"""
        with patch("app.services.similarity_service.TextSimilarityCalculator") as mock_calculator:
            mock_calculator.calculate_similarity.side_effect = Exception("计算错误")

            with pytest.raises(ServiceError, match="批量计算相似度失败"):
                self.service.calculate_batch_similarity("查询", sample_similarity_data, ["标题"])

    def test_get_available_methods_error(self):
        """测试获取方法列表时的错误"""
        with patch("app.services.similarity_service.TextSimilarityCalculator") as mock_calculator:
            mock_calculator.return_value.get_available_methods.side_effect = Exception("错误")

            with pytest.raises(ServiceError, match="获取可用方法失败"):
                self.service.get_available_methods()

    def test_preprocess_text_error(self):
        """测试预处理文本时的错误"""
        with patch("app.services.similarity_service.TextSimilarityCalculator") as mock_calculator:
            mock_calculator.return_value.preprocess_text.side_effect = Exception("错误")

            with pytest.raises(ServiceError, match="预处理文本失败"):
                self.service.preprocess_text("测试")

    # ==================== 边界条件测试 ====================

    def test_calculate_similarity_very_long_text(self):
        """测试超长文本"""
        long_text = "测试 " * 10000
        result = self.service.calculate_similarity(long_text, long_text)
        assert isinstance(result, float)

    def test_calculate_similarity_special_characters(self):
        """测试特殊字符"""
        text1 = "测试！@#￥%……&*（）"
        text2 = "测试文本"
        result = self.service.calculate_similarity(text1, text2)
        assert isinstance(result, float)

    def test_calculate_batch_similarity_large_dataset(self):
        """测试大数据集"""
        large_data = [{"标题": f"测试{i}", "描述": f"描述{i}"} for i in range(100)]

        result = self.service.calculate_batch_similarity("测试", large_data, ["标题"])

        assert len(result) == 100

    def test_search_by_similarity_large_dataset(self, flask_app):
        """测试搜索大数据集"""
        large_data = [{"标题": f"测试{i}", "描述": f"描述{i}"} for i in range(100)]
        mock_df = MagicMock()
        mock_df.to_dict.return_value = large_data

        with flask_app.app_context():
            with patch("app.services.similarity_service.current_app") as mock_current_app:
                mock_current_app.load_data_source.return_value = mock_df

                result = self.service.search_by_similarity("测试", "source", ["标题"], limit=50)

                assert len(result) <= 50


@pytest.mark.parametrize(
    "text1,text2,expected_min_similarity",
    [
        ("相同文本", "相同文本", 0.8),
        ("发动机故障", "发动机问题", 0.3),
        ("完全不同", "毫无关系", 0.0),
    ],
)
def test_calculate_similarity_various_texts(text1, text2, expected_min_similarity):
    """参数化测试各种文本的相似度计算"""
    service = SimilarityService()
    result = service.calculate_similarity(text1, text2)
    assert isinstance(result, float)
    assert result >= expected_min_similarity


@pytest.mark.parametrize("limit", [1, 5, 10, 0])
def test_search_by_similarity_various_limits(limit, sample_similarity_data, flask_app):
    """参数化测试不同的limit值"""
    mock_df = MagicMock()
    mock_df.to_dict.return_value = sample_similarity_data

    service = SimilarityService()

    with flask_app.app_context():
        with patch("app.services.similarity_service.current_app") as mock_current_app:
            mock_current_app.load_data_source.return_value = mock_df

            result = service.search_by_similarity("查询", "source", ["标题"], limit=limit)

            if limit > 0:
                assert len(result) <= limit
            else:
                assert len(result) == len(sample_similarity_data)
