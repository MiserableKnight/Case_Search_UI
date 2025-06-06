import json
import os
import re
from pathlib import Path
from typing import ClassVar, List, Optional, Union

from flask import current_app


class TextAnonymizer:
    _instance: ClassVar[Optional["TextAnonymizer"]] = None

    @classmethod
    def get_instance(cls) -> "TextAnonymizer":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self, sensitive_words_path: Optional[str] = None) -> None:
        self.sensitive_words: List[str] = []
        if sensitive_words_path is None and current_app:
            # 使用配置中的路径
            sensitive_words_path = current_app.config["FILE_CONFIG"][
                "SENSITIVE_WORDS_FILE"
            ]

        if sensitive_words_path:
            self.load_sensitive_words(sensitive_words_path)

        self.patterns: List[str] = [
            r"(909|ARJ)/B-?[A-Z0-9]{4}",
            r"B-?[A-Z0-9]{4}",
            r"10\d{3}",
            r"执行.{1,15}?航班",
            r"[A-Z]{2}\d{4}",
        ]

    def load_sensitive_words(self, file_path: Union[str, Path]) -> None:
        try:
            # 确保文件路径是 Path 对象
            file_path = Path(file_path)
            if not file_path.exists():
                print(f"敏感词文件不存在：{file_path}")
                return

            with file_path.open("r", encoding="utf-8") as file:
                content = json.load(file)
                # 从各个分类中提取敏感词
                for category in content.values():
                    if isinstance(category, list):
                        for item in category:
                            if isinstance(item, dict) and "word" in item:
                                self.sensitive_words.append(item["word"])

                # 对敏感词列表按长度降序排序
                self.sensitive_words.sort(key=len, reverse=True)
                # 只在主进程中打印消息
                if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
                    print("敏感词列表读取成功")
        except Exception as e:
            print(f"读取敏感词文件时出错：{str(e)}")

    def add_sensitive_words(self, new_words: Union[str, List[str]]) -> None:
        if isinstance(new_words, str):
            new_words = [new_words]
        for word in new_words:
            if word not in self.sensitive_words:
                self.sensitive_words.append(word)
        # 重新排序
        self.sensitive_words.sort(key=len, reverse=True)

    def add_patterns(self, new_patterns: Union[str, List[str]]) -> None:
        if isinstance(new_patterns, str):
            new_patterns = [new_patterns]
        for pattern in new_patterns:
            if pattern not in self.patterns:
                self.patterns.append(pattern)

    def anonymize_text(self, text: str) -> str:
        if isinstance(text, str):
            for pattern in self.patterns:
                text = re.sub(pattern, "", text)
            for word in self.sensitive_words:
                text = text.replace(word, "")
            # 清理多余的空白字符
            text = re.sub(r"\s+", " ", text.strip())
            return text
        return text

    def get_sensitive_words(self) -> List[str]:
        return self.sensitive_words

    def get_patterns(self) -> List[str]:
        return self.patterns


# 修改为使用方法获取实例
def get_anonymizer() -> TextAnonymizer:
    return TextAnonymizer.get_instance()


# 导出函数版本的API
def anonymize_text(text: str) -> str:
    return get_anonymizer().anonymize_text(text)


def add_sensitive_words(words: Union[str, List[str]]) -> None:
    return get_anonymizer().add_sensitive_words(words)


def add_patterns(patterns: Union[str, List[str]]) -> None:
    return get_anonymizer().add_patterns(patterns)


def get_sensitive_words() -> List[str]:
    return get_anonymizer().get_sensitive_words()


def get_patterns() -> List[str]:
    return get_anonymizer().get_patterns()
