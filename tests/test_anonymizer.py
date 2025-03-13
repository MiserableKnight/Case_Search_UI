"""
测试text_anonymizer包的功能
"""

import os
import sys
import unittest

# 确保能找到 app 模块
import conftest

from app.utils.text_anonymizer import anonymize_text, add_sensitive_words, get_sensitive_words
from app.utils import TextAnonymizer

class TestAnonymizer(unittest.TestCase):
    def test_basic_anonymization(self):
        """测试基本脱敏功能"""
        test_text = "这是一个测试文本，包含航班号B-1234和机构名称东航"
        result = anonymize_text(test_text)
        self.assertNotIn("B-1234", result)
        self.assertNotIn("东航", result)
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

    def test_complex_anonymization(self):
        """测试复杂场景的脱敏功能"""
        # 测试文本
        test_text = """
        ARJ/B-1234执行MU5288航班
        东航的B-123A飞机
        天骄航空10123
        """
        
        # 测试脱敏结果
        result = anonymize_text(test_text)
        
        # 验证敏感信息是否被删除
        self.assertNotIn('ARJ/B-1234', result)
        self.assertNotIn('B-123A', result)
        self.assertNotIn('10123', result)
        self.assertNotIn('东航', result)
        self.assertNotIn('天骄航空', result)
        
        print("原文本:", test_text)
        print("脱敏后:", result)

if __name__ == "__main__":
    unittest.main() 