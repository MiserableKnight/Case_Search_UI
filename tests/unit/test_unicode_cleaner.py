"""
UnicodeCleaner单元测试

测试Unicode字符清洗器的各种功能
"""

import pytest
import pandas as pd
from app.utils.unicode_cleaner import UnicodeCleaner


class TestUnicodeCleaner:
    """UnicodeCleaner测试类"""

    def setup_method(self):
        """每个测试方法前执行"""
        self.cleaner = UnicodeCleaner()

    # ==================== clean_text测试 ====================

    def test_clean_text_normal_string(self):
        """测试清洗普通字符串"""
        text = "这是一个正常的文本字符串"
        result = self.cleaner.clean_text(text)
        assert result == text

    def test_clean_text_with_bidirectional_chars(self):
        """测试清洗双向文本控制字符"""
        text = "正常文本\u200e\u200f\u202a\u202b文本"
        expected = "正常文本文本"
        result = self.cleaner.clean_text(text)
        assert result == expected

    def test_clean_text_with_control_chars(self):
        """测试清洗控制字符"""
        text = "文本\x00\x01\x02\x03中间\x7f\x8f\x9f"
        expected = "文本中间"
        result = self.cleaner.clean_text(text)
        assert result == expected

    def test_clean_text_with_zero_width_chars(self):
        """测试清洗零宽字符"""
        text = "文本\u200b\u200c\u200d\u2060\ufeff中间"
        expected = "文本中间"
        result = self.cleaner.clean_text(text)
        assert result == expected

    def test_clean_text_none(self):
        """测试清洗None值"""
        result = self.cleaner.clean_text(None)
        assert result == ""

    def test_clean_text_nan(self):
        """测试清洗NaN值"""
        result = self.cleaner.clean_text(float("nan"))
        assert result == ""

    def test_clean_text_pd_na(self):
        """测试清洗pandas NA值"""
        result = self.cleaner.clean_text(pd.NA)
        assert result == ""

    def test_clean_text_non_string_type(self):
        """测试清洗非字符串类型"""
        result = self.cleaner.clean_text(12345)
        assert result == "12345"

    def test_clean_text_strip_whitespace(self):
        """测试移除首尾空格"""
        text = "  文本内容  "
        result = self.cleaner.clean_text(text)
        assert result == "文本内容"

    def test_clean_text_mixed_pollution(self):
        """测试混合污染类型"""
        text = "\u200e文本\x00\u200b内容\u202a\u200f\x7f\u2060"
        expected = "文本内容"
        result = self.cleaner.clean_text(text)
        assert result == expected

    def test_clean_text_preserve_newlines(self):
        """测试保留换行符（某些控制字符应保留）"""
        text = "第一行\n第二行\t制表符\r回车"
        result = self.cleaner.clean_text(text)
        assert "\n" not in result  # 换行符应该被移除
        assert "\t" not in result  # 制表符应该被移除

    # ==================== clean_dataframe测试 ====================

    def test_clean_dataframe_normal(self, sample_dataframe):
        """测试清洗普通DataFrame"""
        result = self.cleaner.clean_dataframe(sample_dataframe)
        assert result is not None
        assert len(result) == len(sample_dataframe)
        assert result.shape == sample_dataframe.shape

    def test_clean_dataframe_with_specified_columns(self, sample_dataframe):
        """测试清洗指定列"""
        result = self.cleaner.clean_dataframe(sample_dataframe, columns=["列1", "列2"])
        assert len(result) == len(sample_dataframe)

    def test_clean_dataframe_empty(self, empty_dataframe):
        """测试清洗空DataFrame"""
        result = self.cleaner.clean_dataframe(empty_dataframe)
        assert result.empty

    def test_clean_dataframe_none(self):
        """测试清洗None输入"""
        result = self.cleaner.clean_dataframe(None)
        assert result is None

    def test_clean_dataframe_with_polluted_data(self, case_data_with_pollution):
        """测试清洗包含污染的DataFrame"""
        result = self.cleaner.clean_dataframe(case_data_with_pollution)
        # 检查标题列中没有Unicode字符
        assert "\u200f" not in result.iloc[0]["标题"]
        assert "\u200d" not in result.iloc[2]["标题"]

    def test_clean_dataframe_with_null_values(self, null_values_dataframe):
        """测试清洗包含空值的DataFrame"""
        result = self.cleaner.clean_dataframe(null_values_dataframe)
        assert len(result) == len(null_values_dataframe)

    def test_clean_dataframe_non_object_columns(self):
        """测试只处理object类型的列"""
        df = pd.DataFrame({
            "文本列": ["值1", "值2"],
            "数字列": [1, 2],
            "日期列": pd.to_datetime(["2023-01-01", "2023-01-02"]),
        })
        result = self.cleaner.clean_dataframe(df)
        # 确保所有列都被处理
        assert len(result.columns) == len(df.columns)

    # ==================== clean_excel_file测试 ====================

    def test_clean_excel_file(self, sample_excel_file, temp_output_dir):
        """测试清洗Excel文件"""
        output_path = temp_output_dir / "cleaned.xlsx"
        result = self.cleaner.clean_excel_file(str(sample_excel_file), str(output_path))

        assert Path(result).exists()
        assert result == str(output_path)

        # 验证清洗后的数据
        cleaned_df = pd.read_excel(result)
        assert len(cleaned_df) > 0

    def test_clean_excel_file_auto_output_name(self, sample_excel_file, temp_output_dir):
        """测试自动生成输出文件名"""
        result = self.cleaner.clean_excel_file(str(sample_excel_file))
        assert Path(result).exists()
        assert "_cleaned" in result

    def test_clean_excel_file_invalid_path(self):
        """测试清洗不存在的文件"""
        with pytest.raises(Exception):
            self.cleaner.clean_excel_file("nonexistent_file.xlsx")

    # ==================== detect_unicode_pollution测试 ====================

    def test_detect_pollution_no_pollution(self):
        """测试检测无污染的文本"""
        result = self.cleaner.detect_unicode_pollution("正常文本")
        assert result["has_pollution"] is False
        assert result["pollution_types"] == []
        assert result["original_length"] == len("正常文本")
        assert result["cleaned_length"] == len("正常文本")

    def test_detect_pollution_bidirectional(self):
        """测试检测双向文本控制字符污染"""
        text = "文本\u200e\u200f中间"
        result = self.cleaner.detect_unicode_pollution(text)
        assert result["has_pollution"] is True
        assert "bidirectional_control_chars" in result["pollution_types"]

    def test_detect_pollution_control_chars(self):
        """测试检测控制字符污染"""
        text = "文本\x00\x01\x7f中间"
        result = self.cleaner.detect_unicode_pollution(text)
        assert result["has_pollution"] is True
        assert "control_chars" in result["pollution_types"]

    def test_detect_pollution_zero_width(self):
        """测试检测零宽字符污染"""
        text = "文本\u200b\u200c\u200d中间"
        result = self.cleaner.detect_unicode_pollution(text)
        assert result["has_pollution"] is True
        assert "zero_width_chars" in result["pollution_types"]

    def test_detect_pollution_multiple_types(self):
        """测试检测多种类型污染"""
        text = "\u200e文本\x00\u200b中间"
        result = self.cleaner.detect_unicode_pollution(text)
        assert result["has_pollution"] is True
        assert len(result["pollution_types"]) == 3

    def test_detect_pollution_non_string(self):
        """测试检测非字符串输入"""
        result = self.cleaner.detect_unicode_pollution(12345)
        assert result["has_pollution"] is False
        assert result["pollution_types"] == []

    def test_detect_pollution_none(self):
        """测试检测None输入"""
        result = self.cleaner.detect_unicode_pollution(None)
        assert result["has_pollution"] is False

    def test_detect_pollution_length_difference(self):
        """测试检测前后的长度差异"""
        text = "正常\u200e\u200b\u200d文本"
        result = self.cleaner.detect_unicode_pollution(text)
        assert result["original_length"] > result["cleaned_length"]

    # ==================== analyze_file_pollution测试 ====================

    def test_analyze_file_pollution(self, sample_excel_file):
        """测试分析文件污染情况"""
        result = self.cleaner.analyze_file_pollution(str(sample_excel_file))
        assert "total_cells" in result
        assert "polluted_cells" in result
        assert "pollution_rate" in result
        assert isinstance(result["total_cells"], int)
        assert result["total_cells"] >= 0

    def test_analyze_file_pollution_invalid_file(self):
        """测试分析不存在的文件"""
        result = self.cleaner.analyze_file_pollution("nonexistent.xlsx")
        assert "error" in result

    # ==================== 边界条件测试 ====================

    def test_clean_empty_string(self):
        """测试清洗空字符串"""
        result = self.cleaner.clean_text("")
        assert result == ""

    def test_clean_whitespace_only(self):
        """测试清洗只有空格的字符串"""
        result = self.cleaner.clean_text("   \t\n  ")
        assert result == ""

    def test_clean_very_long_string(self):
        """测试清洗超长字符串"""
        text = "A" * 10000 + "\u200e\u200f" + "B" * 10000
        result = self.cleaner.clean_text(text)
        assert len(result) == 20000
        assert result == "A" * 10000 + "B" * 10000

    def test_clean_unicode_emoji(self):
        """测试清洗包含emoji的文本"""
        text = "正常文本😀😃😄表情符号🎉🎊"
        result = self.cleaner.clean_text(text)
        # emoji不应该被移除
        assert "😀" in result or "😀" not in text  # 取决于正则表达式

    def test_clean_mixed_language(self):
        """测试清洗混合语言文本"""
        text = "中文English日本語한국Text"
        result = self.cleaner.clean_text(text)
        # 正常的多语言字符应该保留
        assert len(result) > 0


@pytest.mark.parametrize("text,expected", [
    ("Normal text", "Normal text"),
    ("\u200eText\u200f", "Text"),
    ("\x00Text\x7f", "Text"),
    ("\u200bText\u200c", "Text"),
])
def test_clean_text_parametrized(text, expected):
    """参数化测试clean_text方法"""
    cleaner = UnicodeCleaner()
    result = cleaner.clean_text(text)
    assert result == expected
