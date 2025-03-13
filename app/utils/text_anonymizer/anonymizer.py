import json
import re
import os
from flask import current_app

class TextAnonymizer:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self, sensitive_words_path=None):
        self.sensitive_words = []
        if sensitive_words_path is None:
            # 使用配置中的路径
            sensitive_words_path = current_app.config['FILE_CONFIG']['SENSITIVE_WORDS_FILE']
        self.load_sensitive_words(sensitive_words_path)
        self.patterns = [
            r'(909|ARJ)/B-?[A-Z0-9]{4}',
            r'B-?[A-Z0-9]{4}',
            r'10\d{3}',
            r'执行.{1,15}?航班',
            r'[A-Z]{2}\d{4}'
        ]

    def load_sensitive_words(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = json.load(file)
                # 从各个分类中提取敏感词
                for category in content.values():
                    if isinstance(category, list):
                        for item in category:
                            if isinstance(item, dict) and 'word' in item:
                                self.sensitive_words.append(item['word'])
                
                # 对敏感词列表按长度降序排序
                self.sensitive_words.sort(key=len, reverse=True)
                print("敏感词列表读取成功")
        except FileNotFoundError:
            print(f"未找到文件：{file_path}，请检查文件路径和文件名。")
        except Exception as e:
            print(f"读取文件时出错：{e}")

    def add_sensitive_words(self, new_words):
        if isinstance(new_words, str):
            new_words = [new_words]
        for word in new_words:
            if word not in self.sensitive_words:
                self.sensitive_words.append(word)
        # 重新排序
        self.sensitive_words.sort(key=len, reverse=True)

    def add_patterns(self, new_patterns):
        if isinstance(new_patterns, str):
            new_patterns = [new_patterns]
        for pattern in new_patterns:
            if pattern not in self.patterns:
                self.patterns.append(pattern)

    def anonymize_text(self, text):
        if isinstance(text, str):
            for pattern in self.patterns:
                text = re.sub(pattern, "", text)
            for word in self.sensitive_words:
                text = text.replace(word, "")
            # 清理多余的空白字符
            text = re.sub(r'\s+', ' ', text.strip())
            return text
        return text

    def get_sensitive_words(self):
        return self.sensitive_words

    def get_patterns(self):
        return self.patterns

# 修改为使用方法获取实例
def get_anonymizer():
    return TextAnonymizer.get_instance()

# 导出函数版本的API
def anonymize_text(text):
    return get_anonymizer().anonymize_text(text)

def add_sensitive_words(words):
    return get_anonymizer().add_sensitive_words(words)

def add_patterns(patterns):
    return get_anonymizer().add_patterns(patterns)

def get_sensitive_words():
    return get_anonymizer().get_sensitive_words()

def get_patterns():
    return get_anonymizer().get_patterns() 