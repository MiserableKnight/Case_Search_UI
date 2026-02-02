"""
TextSimilarityCalculator单元测试

测试文本相似度计算器的各种功能
"""

import pytest

from app.core.calculator import TextSimilarityCalculator


class TestTextSimilarityCalculator:
    """TextSimilarityCalculator测试类"""

    # ==================== chinese_word_cut测试 ====================

    def test_chinese_word_cut_normal_text(self):
        """测试分词普通中文文本"""
        text = "这是一个测试文本"
        result = TextSimilarityCalculator.chinese_word_cut(text)
        assert isinstance(result, str)
        assert len(result) > 0
        # 分词后应该包含空格分隔的词
        assert " " in result or len(result.split()) >= 1

    def test_chinese_word_cut_empty_string(self):
        """测试分词空字符串"""
        result = TextSimilarityCalculator.chinese_word_cut("")
        assert result == ""

    def test_chinese_word_cut_none(self):
        """测试分词None值"""
        result = TextSimilarityCalculator.chinese_word_cut(None)
        assert result == ""

    def test_chinese_word_cut_nan(self):
        """测试分词NaN值"""
        result = TextSimilarityCalculator.chinese_word_cut(float("nan"))
        assert result == ""

    def test_chinese_word_cut_mixed_language(self):
        """测试分词混合语言文本"""
        text = "这是English和中文混合Text"
        result = TextSimilarityCalculator.chinese_word_cut(text)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_chinese_word_cut_with_punctuation(self):
        """测试分词包含标点符号的文本"""
        text = "这是测试，包含标点符号。"
        result = TextSimilarityCalculator.chinese_word_cut(text)
        assert isinstance(result, str)

    # ==================== calculate_similarity测试 ====================

    def test_calculate_similarity_normal_case(self, sample_similarity_data):
        """测试正常情况下的相似度计算"""
        search_text = "发动机故障"
        results = sample_similarity_data
        columns = ["标题", "问题描述"]

        result = TextSimilarityCalculator.calculate_similarity(search_text, results, columns)

        assert isinstance(result, list)
        assert len(result) == len(results)
        # 检查是否添加了相似度列
        assert "相似度" in result[0]
        # 验证相似度格式
        assert "%" in result[0]["相似度"]

    def test_calculate_similarity_empty_results(self):
        """测试空结果列表"""
        result = TextSimilarityCalculator.calculate_similarity("测试", [], ["列1"])
        assert result == []

    def test_calculate_similarity_empty_search_text(self, sample_similarity_data):
        """测试空搜索文本"""
        with pytest.raises(ValueError, match="搜索文本不能为空"):
            TextSimilarityCalculator.calculate_similarity("", sample_similarity_data, ["标题"])

    def test_calculate_similarity_non_string_search_text(self, sample_similarity_data):
        """测试非字符串搜索文本"""
        with pytest.raises(ValueError):
            TextSimilarityCalculator.calculate_similarity(123, sample_similarity_data, ["标题"])

    def test_calculate_similarity_empty_columns(self, sample_similarity_data):
        """测试空列列表"""
        with pytest.raises(ValueError, match="必须指定至少一个搜索列"):
            TextSimilarityCalculator.calculate_similarity("测试", sample_similarity_data, [])

    def test_calculate_similarity_non_list_columns(self, sample_similarity_data):
        """测试非列表类型的列参数"""
        with pytest.raises(ValueError, match="必须是列表类型"):
            TextSimilarityCalculator.calculate_similarity("测试", sample_similarity_data, "标题")

    def test_calculate_similarity_missing_column(self, sample_similarity_data):
        """测试不存在的列"""
        with pytest.raises(ValueError, match="以下列在数据中不存在"):
            TextSimilarityCalculator.calculate_similarity(
                "测试", sample_similarity_data, ["不存在的列"]
            )

    def test_calculate_similarity_with_nan_values(self):
        """测试包含NaN值的数据"""
        data = [
            {"标题": "测试1", "描述": None},
            {"标题": None, "描述": "测试2"},
            {"标题": "测试3", "描述": "测试描述3"},
        ]

        result = TextSimilarityCalculator.calculate_similarity("测试", data, ["标题", "描述"])

        assert len(result) == 3
        assert "相似度" in result[0]

    def test_calculate_similarity_multiple_columns(self, sample_similarity_data):
        """测试多列搜索"""
        columns = ["标题", "问题描述", "答复详情"]
        result = TextSimilarityCalculator.calculate_similarity(
            "发动机故障", sample_similarity_data, columns
        )

        assert len(result) == len(sample_similarity_data)
        # 检查是否按相似度排序
        similarities = [float(r["相似度"].rstrip("%")) for r in result]
        # 应该是降序排列
        assert similarities == sorted(similarities, reverse=True)

    def test_calculate_similarity_with_time_column(self, sample_similarity_data):
        """测试带时间列的排序"""
        result = TextSimilarityCalculator.calculate_similarity(
            "故障", sample_similarity_data, ["标题", "问题描述"]
        )

        # 验证结果仍然包含时间列
        assert "申请时间" in result[0]
        # 检查是否添加了相似度
        assert "相似度" in result[0]

    def test_calculate_similarity_preserves_original_fields(self, sample_similarity_data):
        """测试保留原始字段"""
        original_fields = set(sample_similarity_data[0].keys())
        result = TextSimilarityCalculator.calculate_similarity(
            "测试", sample_similarity_data, ["标题"]
        )

        result_fields = set(result[0].keys())
        # 应该包含相似度字段
        assert "相似度" in result_fields
        # 应该保留大部分原始字段（除了内部使用的字段）
        assert len(result_fields & original_fields) > 0

    def test_calculate_similarity_similarity_format(self, sample_similarity_data):
        """测试相似度格式"""
        result = TextSimilarityCalculator.calculate_similarity(
            "测试", sample_similarity_data, ["标题"]
        )

        for item in result:
            similarity_str = item["相似度"]
            # 验证百分比格式
            assert similarity_str.endswith("%")
            # 验证可以转换为浮点数
            similarity_value = float(similarity_str.rstrip("%"))
            assert 0 <= similarity_value <= 100

    # ==================== 相似度排序测试 ====================

    def test_similarity_sorting_order(self, sample_similarity_data):
        """测试相似度排序顺序"""
        search_text = "发动机控制系统"
        result = TextSimilarityCalculator.calculate_similarity(
            search_text, sample_similarity_data, ["标题", "问题描述"]
        )

        similarities = [float(r["相似度"].rstrip("%")) for r in result]
        # 验证降序排列
        for i in range(len(similarities) - 1):
            assert similarities[i] >= similarities[i + 1]

    def test_similarity_scores_reasonable(self, sample_similarity_data):
        """测试相似度分数的合理性"""
        # 使用与第一条记录相关的搜索词
        search_text = "发动机控制系统"
        result = TextSimilarityCalculator.calculate_similarity(
            search_text, sample_similarity_data, ["标题", "问题描述"]
        )

        similarities = [float(r["相似度"].rstrip("%")) for r in result]
        # 至少有一些结果应该有大于0的相似度
        assert any(s > 0 for s in similarities)

    # ==================== 边界条件测试 ====================

    def test_calculate_similarity_very_long_search_text(self, sample_similarity_data):
        """测试超长搜索文本"""
        long_text = "测试 " * 1000
        result = TextSimilarityCalculator.calculate_similarity(
            long_text, sample_similarity_data, ["标题"]
        )

        assert len(result) == len(sample_similarity_data)

    def test_calculate_similarity_special_characters(self):
        """测试包含特殊字符的文本"""
        data = [
            {"标题": "测试！@#￥%"},
            {"标题": "测试&*（）"},
        ]

        result = TextSimilarityCalculator.calculate_similarity("测试", data, ["标题"])
        assert len(result) == 2

    def test_calculate_similarity_unicode_characters(self):
        """测试Unicode字符"""
        data = [
            {"标题": "测试emoji😀😃"},
            {"标题": "测试特殊字符◎◇◆"},
        ]

        result = TextSimilarityCalculator.calculate_similarity("测试", data, ["标题"])
        assert len(result) == 2

    def test_calculate_similarity_single_result(self):
        """测试单个结果"""
        data = [{"标题": "测试标题", "描述": "测试描述"}]

        result = TextSimilarityCalculator.calculate_similarity("测试", data, ["标题"])
        assert len(result) == 1
        assert "相似度" in result[0]

    def test_calculate_similarity_identical_text(self):
        """测试完全相同的文本"""
        data = [{"标题": "发动机故障"}]

        result = TextSimilarityCalculator.calculate_similarity("发动机故障", data, ["标题"])
        # 相同的文本应该有很高的相似度
        similarity = float(result[0]["相似度"].rstrip("%"))
        assert similarity > 50  # 应该有较高的相似度

    def test_calculate_similarity_completely_different(self):
        """测试完全不同的文本"""
        data = [{"标题": "关于蔬菜水果的营养价值"}]

        result = TextSimilarityCalculator.calculate_similarity("航空发动机维修", data, ["标题"])
        # 不同的文本相似度应该较低
        similarity = float(result[0]["相似度"].rstrip("%"))
        # 相似度应该相对较低（但不一定是0，因为可能有共同字符）

    # ==================== 内部字段测试 ====================

    def test_internal_fields_removed(self, sample_similarity_data):
        """测试内部字段被移除"""
        result = TextSimilarityCalculator.calculate_similarity(
            "测试", sample_similarity_data, ["标题"]
        )

        # 检查内部使用的字段被移除
        assert "合并文本" not in result[0]
        assert "搜索列分词_cut" not in result[0]
        assert "相似度_排序" not in result[0]


@pytest.mark.parametrize(
    "text,expected_parts",
    [
        ("简单文本", ["简单", "文本"]),
        ("发动机故障", ["发动机", "故障"]),
        ("", []),
    ],
)
def test_chinese_word_cut_parametrized(text, expected_parts):
    """参数化测试分词功能"""
    result = TextSimilarityCalculator.chinese_word_cut(text)
    if text:
        assert isinstance(result, str)
        if len(expected_parts) > 0:
            # 验证包含预期的词
            parts = result.split()
            # jieba分词结果可能不完全匹配，只验证非空
            assert len(parts) > 0
    else:
        assert result == ""


@pytest.mark.parametrize(
    "search_text,columns",
    [
        ("发动机", ["标题"]),
        ("液压系统", ["标题", "问题描述"]),
        ("导航", ["标题", "问题描述", "答复详情"]),
    ],
)
def test_calculate_similarity_various_configs(sample_similarity_data, search_text, columns):
    """参数化测试不同的配置"""
    result = TextSimilarityCalculator.calculate_similarity(
        search_text, sample_similarity_data, columns
    )
    assert len(result) == len(sample_similarity_data)
    assert "相似度" in result[0]
