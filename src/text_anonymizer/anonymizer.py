import json
import re
import os

class TextAnonymizer:
    def __init__(self, sensitive_words_path='app/data/sensitive_words.json'):
        self.sensitive_words = self.load_sensitive_words(sensitive_words_path)
        self.patterns = [
            r'(909|ARJ)/B-?[A-Z0-9]{4}',
            r'B-?[A-Z0-9]{4}',
            r'10\d{3}',
            r'执行.{1,15}?航班',
            r'[A-Z]{2}\d{4}'
        ]
        # 对初始敏感词列表按长度降序排序
        self.sensitive_words.sort(key=len, reverse=True)

    def load_sensitive_words(self, file_path):
        sensitive_words = []
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read().strip()
                sensitive_words = json.loads(content)
                
                unique_sensitive_words = []
                for word in sensitive_words:
                    if word not in unique_sensitive_words:
                        unique_sensitive_words.append(word)
                sensitive_words = unique_sensitive_words
                print("敏感词列表读取成功")
        except FileNotFoundError:
            print(f"未找到文件：{file_path}，请检查文件路径和文件名。")
        except Exception as e:
            print(f"读取文件时出现错误：{e}")
        return sensitive_words

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
            return text
        return text

    def get_sensitive_words(self):
        return self.sensitive_words

    def get_patterns(self):
        return self.patterns

# 创建默认实例
default_anonymizer = TextAnonymizer()

# 为了保持向后兼容，导出函数版本的API
anonymize_text = default_anonymizer.anonymize_text
add_sensitive_words = default_anonymizer.add_sensitive_words
add_patterns = default_anonymizer.add_patterns
get_sensitive_words = default_anonymizer.get_sensitive_words
get_patterns = default_anonymizer.get_patterns