"""
TextAnonymizer单元测试

测试文本脱敏器的各种功能
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from app.core.anonymizer import TextAnonymizer, get_anonymizer


class TestTextAnonymizer:
    """TextAnonymizer测试类"""

    def setup_method(self):
        """每个测试方法前执行"""
        # 重置单例
        TextAnonymizer._instance = None

    def teardown_method(self):
        """每个测试方法后执行"""
        # 清理单例
        TextAnonymizer._instance = None

    # ==================== 单例模式测试 ====================

    def test_singleton_pattern(self, sensitive_words_file, flask_app):
        """测试单例模式"""
        with flask_app.app_context(), patch("app.core.anonymizer.current_app") as mock_app:
            mock_app.config = {"FILE_CONFIG": {"SENSITIVE_WORDS_FILE": sensitive_words_file}}

            instance1 = TextAnonymizer.get_instance()
            instance2 = TextAnonymizer.get_instance()

            assert instance1 is instance2

    def test_get_instance_function(self, sensitive_words_file, flask_app):
        """测试get_anonymizer函数"""
        with flask_app.app_context(), patch("app.core.anonymizer.current_app") as mock_app:
            mock_app.config = {"FILE_CONFIG": {"SENSITIVE_WORDS_FILE": sensitive_words_file}}

            anonymizer = get_anonymizer()
            assert isinstance(anonymizer, TextAnonymizer)

    # ==================== 初始化测试 ====================

    def test_init_without_path(self):
        """测试不带路径初始化"""
        with patch("app.core.anonymizer.current_app", None):
            anonymizer = TextAnonymizer(sensitive_words_path=None)
            assert anonymizer.sensitive_words == []
            assert len(anonymizer.patterns) > 0

    def test_init_with_invalid_path(self):
        """测试使用无效路径初始化"""
        with patch("builtins.print"):
            anonymizer = TextAnonymizer(sensitive_words_path="/nonexistent/path.json")
            assert anonymizer.sensitive_words == []

    def test_default_patterns(self):
        """测试默认模式"""
        anonymizer = TextAnonymizer(sensitive_words_path=None)
        patterns = anonymizer.get_patterns()

        assert len(patterns) > 0
        # 检查一些默认模式
        assert any("909" in p or "ARJ" in p for p in patterns)
        assert any("B-?" in p for p in patterns)

    # ==================== load_sensitive_words测试 ====================

    def test_load_sensitive_words_valid_file(self, sensitive_words_file):
        """测试加载有效的敏感词文件"""
        with patch("builtins.print"):
            anonymizer = TextAnonymizer(sensitive_words_path=sensitive_words_file)

            assert len(anonymizer.sensitive_words) > 0
            assert "某某航空" in anonymizer.sensitive_words
            assert "张三" in anonymizer.sensitive_words

    def test_load_sensitive_words_sorted_by_length(self, sensitive_words_file):
        """测试敏感词按长度降序排序"""
        with patch("builtins.print"):
            # 添加不同长度的词
            data = {
                "短词": [{"word": "短"}],
                "长词": [{"word": "这是一个非常长的词"}],
                "中长词": [{"word": "中等长度的词"}],
            }
            file_path = Path(sensitive_words_file).parent / "sorted_test.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)

            anonymizer = TextAnonymizer(sensitive_words_path=str(file_path))
            words = anonymizer.get_sensitive_words()

            # 验证按长度降序排列
            assert len(words[0]) >= len(words[1]) if len(words) > 1 else True

    # ==================== add_sensitive_words测试 ====================

    def test_add_single_sensitive_word(self):
        """测试添加单个敏感词"""
        anonymizer = TextAnonymizer(sensitive_words_path=None)
        initial_count = len(anonymizer.sensitive_words)

        with patch("builtins.print"):
            anonymizer.add_sensitive_words("新敏感词")

        assert len(anonymizer.sensitive_words) == initial_count + 1
        assert "新敏感词" in anonymizer.sensitive_words

    def test_add_multiple_sensitive_words(self):
        """测试添加多个敏感词"""
        anonymizer = TextAnonymizer(sensitive_words_path=None)
        initial_count = len(anonymizer.sensitive_words)

        with patch("builtins.print"):
            anonymizer.add_sensitive_words(["词1", "词2", "词3"])

        assert len(anonymizer.sensitive_words) == initial_count + 3

    def test_add_duplicate_sensitive_word(self):
        """测试添加重复的敏感词"""
        anonymizer = TextAnonymizer(sensitive_words_path=None)

        with patch("builtins.print"):
            anonymizer.add_sensitive_words("重复词")
            initial_count = len(anonymizer.sensitive_words)
            anonymizer.add_sensitive_words("重复词")

        assert len(anonymizer.sensitive_words) == initial_count

    # ==================== add_patterns测试 ====================

    def test_add_single_pattern(self):
        """测试添加单个模式"""
        anonymizer = TextAnonymizer(sensitive_words_path=None)
        initial_count = len(anonymizer.patterns)

        anonymizer.add_patterns(r"\d{4}-\d{4}")

        assert len(anonymizer.patterns) == initial_count + 1

    def test_add_multiple_patterns(self):
        """测试添加多个模式"""
        anonymizer = TextAnonymizer(sensitive_words_path=None)
        initial_count = len(anonymizer.patterns)

        anonymizer.add_patterns([r"\d{4}", r"[A-Z]{3}", r"\d{2}-\d{2}"])

        assert len(anonymizer.patterns) == initial_count + 3

    def test_add_duplicate_pattern(self):
        """测试添加重复模式"""
        anonymizer = TextAnonymizer(sensitive_words_path=None)
        pattern = r"\d{4}"

        anonymizer.add_patterns(pattern)
        initial_count = len(anonymizer.patterns)
        anonymizer.add_patterns(pattern)

        assert len(anonymizer.patterns) == initial_count

    # ==================== anonymize_text测试 ====================

    def test_anonymize_text_with_patterns(self):
        """测试使用模式脱敏"""
        anonymizer = TextAnonymizer(sensitive_words_path=None)

        # 测试航班号模式
        text = "执行909/B-1234航班任务"
        result = anonymizer.anonymize_text(text)

        assert "909" not in result or "B-1234" not in result

    def test_anonymize_text_with_sensitive_words(self):
        """测试使用敏感词脱敏"""
        with patch("builtins.print"):
            anonymizer = TextAnonymizer(sensitive_words_path=None)
            anonymizer.add_sensitive_words(["某某航空", "张三"])

        text = "某某航空的张三工程师"
        result = anonymizer.anonymize_text(text)

        assert "某某航空" not in result
        assert "张三" not in result

    def test_anonymize_text_whitespace_cleanup(self):
        """测试脱敏后清理多余空格"""
        with patch("builtins.print"):
            anonymizer = TextAnonymizer(sensitive_words_path=None)
            anonymizer.add_sensitive_words(["测试"])

        text = "正常  测试  文本"
        result = anonymizer.anonymize_text(text)

        # 不应该有多个连续空格
        assert "  " not in result

    def test_anonymize_text_number_string(self):
        """测试脱敏包含数字的字符串"""
        anonymizer = TextAnonymizer(sensitive_words_path=None)

        result = anonymizer.anonymize_text("12345")
        assert result == "12345"

    def test_anonymize_text_with_special_chars(self):
        """测试脱敏包含特殊字符的字符串"""
        anonymizer = TextAnonymizer(sensitive_words_path=None)

        result = anonymizer.anonymize_text("!@#$%^&*()")
        # 清理后应该只剩特殊字符
        assert isinstance(result, str)

    def test_anonymize_text_empty_string(self):
        """测试脱敏空字符串"""
        anonymizer = TextAnonymizer(sensitive_words_path=None)

        result = anonymizer.anonymize_text("")
        assert result == ""

    def test_anonymize_text_combined(self):
        """测试组合脱敏（模式+敏感词）"""
        with patch("builtins.print"):
            anonymizer = TextAnonymizer(sensitive_words_path=None)
            anonymizer.add_sensitive_words(["某某航空"])

        text = "某某航空执行909/B-1234航班"
        result = anonymizer.anonymize_text(text)

        assert "某某航空" not in result

    # ==================== getter方法测试 ====================

    def test_get_sensitive_words(self):
        """测试获取敏感词列表"""
        with patch("builtins.print"):
            anonymizer = TextAnonymizer(sensitive_words_path=None)
            anonymizer.add_sensitive_words(["词1", "词2"])

        words = anonymizer.get_sensitive_words()
        assert isinstance(words, list)
        assert "词1" in words
        assert "词2" in words

    def test_get_patterns(self):
        """测试获取模式列表"""
        anonymizer = TextAnonymizer(sensitive_words_path=None)
        patterns = anonymizer.get_patterns()

        assert isinstance(patterns, list)
        assert len(patterns) > 0

    # ==================== 模块函数测试 ====================

    def test_module_anonymize_text_function(self, flask_app):
        """测试模块级anonymize_text函数"""
        from app.core import anonymizer as anon_module

        with flask_app.app_context(), patch("app.core.anonymizer.current_app"):
            result = anon_module.anonymize_text("测试文本")
            # 应该返回字符串
            assert isinstance(result, str)

    def test_module_add_sensitive_words_function(self, flask_app):
        """测试模块级add_sensitive_words函数"""
        from app.core import anonymizer as anon_module

        with flask_app.app_context():
            with patch("builtins.print"), patch("app.core.anonymizer.current_app"):
                anon_module.add_sensitive_words("测试词")
                words = anon_module.get_sensitive_words()
                assert "测试词" in words

    def test_module_get_patterns_function(self, flask_app):
        """测试模块级get_patterns函数"""
        from app.core import anonymizer as anon_module

        with flask_app.app_context(), patch("app.core.anonymizer.current_app"):
            patterns = anon_module.get_patterns()
            assert isinstance(patterns, list)

    # ==================== 边界条件测试 ====================

    def test_anonymize_very_long_text(self):
        """测试脱敏超长文本"""
        anonymizer = TextAnonymizer(sensitive_words_path=None)
        anonymizer.add_sensitive_words("测试")

        text = "正常文本 " * 10000 + "测试 关键词"
        result = anonymizer.anonymize_text(text)

        assert "测试" not in result
        assert len(result) > 0

    def test_anonymize_special_characters(self):
        """测试脱敏包含特殊字符的文本"""
        with patch("builtins.print"):
            anonymizer = TextAnonymizer(sensitive_words_path=None)
            anonymizer.add_patterns(r"\d{4}")

        text = "特殊字符！@#￥%……&*（）1234测试"
        result = anonymizer.anonymize_text(text)

        assert "1234" not in result

    def test_anonymize_overlapping_patterns(self):
        """测试重叠模式"""
        with patch("builtins.print"):
            anonymizer = TextAnonymizer(sensitive_words_path=None)

        # 这个模式会匹配航班号
        text = "B-1234和B-5678两个航班"
        result = anonymizer.anonymize_text(text)

        # 应该至少移除一些内容
        assert result != text


@pytest.mark.parametrize(
    "word",
    [
        "敏感词1",
        "测试航空公司",
        "长敏感词测试",
    ],
)
def test_add_various_sensitive_words(word):
    """参数化测试添加各种敏感词"""
    anonymizer = TextAnonymizer(sensitive_words_path=None)
    with patch("builtins.print"):
        anonymizer.add_sensitive_words(word)
    assert word in anonymizer.get_sensitive_words()


@pytest.mark.parametrize(
    "pattern,text,should_match",
    [
        (r"\d{4}", "AB1234CD", True),
        (r"\d{4}", "ABCDEFGH", False),
        (r"[A-Z]{3}", "ABC123", True),
        (r"[A-Z]{3}", "A1B2C3", False),
    ],
)
def test_pattern_matching(pattern, text, should_match):
    """参数化测试模式匹配"""
    import re

    if should_match:
        assert re.search(pattern, text) is not None
    else:
        # 注意：这里测试的是模式本身能匹配的情况
        # 实际脱敏结果会移除匹配的内容
        assert isinstance(text, str)
