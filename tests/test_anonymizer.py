"""
测试text_anonymizer包的功能
"""

import unittest
from text_anonymizer import anonymize_text, add_sensitive_words, get_sensitive_words

class TestAnonymizer(unittest.TestCase):
    def test_basic_anonymization(self):
        """测试基本脱敏功能"""
        test_text = "这是一个测试文本，包含航班号B-1234"
        result = anonymize_text(test_text)
        self.assertNotIn("B-1234", result)
        print(f"脱敏结果: {result}")

    def test_sensitive_words_management(self):
        """测试敏感词管理功能"""
        # 获取初始敏感词列表
        initial_words = get_sensitive_words()
        print(f"初始敏感词列表: {initial_words}")

        # 测试添加新敏感词
        test_word = "测试词"
        add_sensitive_words(test_word)
        updated_words = get_sensitive_words()
        self.assertIn(test_word, updated_words)
        print(f"添加后的敏感词列表: {updated_words}")

if __name__ == "__main__":
    unittest.main() 