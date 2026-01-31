import json
import os
import time
from pathlib import Path

from flask import current_app


class SensitiveWordManager:
    def __init__(self, file_path: str | None = None) -> None:
        if file_path is None:
            # 使用配置中的路径
            file_path = current_app.config["FILE_CONFIG"]["SENSITIVE_WORDS_FILE"]
        self.file_path = Path(file_path)

        # 定义类别
        self.categories: list[str] = [
            "organizations",
            "aircraft",
            "locations",
            "registration_numbers",
            "other",
        ]
        self.category_labels: dict[str, str] = {
            "organizations": "组织机构",
            "aircraft": "设备型号",
            "locations": "地点",
            "registration_numbers": "机号/MSN",
            "other": "其他",
        }

        # 初始化敏感词列表和排序列表
        self.words: dict[str, list[dict[str, str]]] = {
            "organizations": [],
            "aircraft": [],
            "locations": [],
            "registration_numbers": [],
            "other": [],
        }
        self.sorted_words: list[str] = []

        # 修改初始化顺序，确保文件存在后再加载
        if self._ensure_file_exists():
            self.load_words()
            self.sorted_words = self._create_sorted_list()

    def _ensure_file_exists(self) -> bool:
        """确保敏感词文件存在，如果不存在则创建"""
        try:
            if not self.file_path.exists():
                # 确保目录存在
                self.file_path.parent.mkdir(parents=True, exist_ok=True)

                # 创建初始文件
                initial_data: dict[str, list[dict[str, str]]] = {
                    "organizations": [],
                    "aircraft": [],
                    "locations": [],
                    "registration_numbers": [],
                    "other": [],
                }
                with self.file_path.open("w", encoding="utf-8") as f:
                    json.dump(initial_data, f, ensure_ascii=False, indent=4)
                return True

            return True
        except Exception:
            return False

    def load_words(self) -> None:
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, encoding="utf-8") as f:
                    self.words = json.load(f)
            else:
                # 保持与 categories 相同的顺序
                self.words = {
                    "organizations": [],
                    "aircraft": [],
                    "locations": [],
                    "registration_numbers": [],
                    "other": [],
                }
                self._save_words()
        except Exception as e:
            print(f"加载敏感词失败: {str(e)}")
            # 这里的顺序也要保持一致
            self.words = {
                "organizations": [],
                "aircraft": [],
                "locations": [],
                "registration_numbers": [],
                "other": [],
            }

    def _create_sorted_list(self) -> list[str]:
        """创建按长度排序的敏感词列表"""
        all_words = []
        for category, words in self.words.items():
            all_words.extend([item["word"] for item in words])

        # 按长度降序排序
        return sorted(all_words, key=len, reverse=True)

    def get_all_words(self) -> dict[str, list[dict[str, str]]]:
        """获取所有敏感词，按照预定义顺序返回"""
        ordered_words = {}
        for category in self.categories:  # self.categories 已经定义了正确的顺序
            ordered_words[category] = self.words.get(category, [])
        return ordered_words

    def get_sorted_words(self) -> list[str]:
        """获取按长度排序的敏感词列表"""
        return self.sorted_words

    def add_word(self, word: str, category: str) -> tuple[bool, str]:
        """添加敏感词"""
        if not word or not word.strip():
            return False, "敏感词不能为空"

        if category not in self.words:
            return False, f"类别 '{category}' 不存在"

        word = word.strip()

        # 检查是否已存在
        for cat, word_list in self.words.items():
            if any(item["word"] == word for item in word_list):
                return False, f"敏感词 '{word}' 已存在于类别 '{cat}'"

        # 添加敏感词
        self.words[category].append(
            {"word": word, "added_time": time.strftime("%Y-%m-%d %H:%M:%S")}
        )

        # 更新排序列表
        self.sorted_words.append(word)
        self.sorted_words.sort(key=len, reverse=True)

        # 保存到文件
        if self._save_words():
            return True, f"敏感词 '{word}' 已添加到类别 '{category}'"
        else:
            return False, "保存敏感词失败"

    def remove_word(self, word: str, category: str) -> tuple[bool, str]:
        """删除敏感词"""
        if category not in self.words:
            return False, f"类别 '{category}' 不存在"

        # 查找并删除敏感词
        found = False
        for i, item in enumerate(self.words[category]):
            if item["word"] == word:
                self.words[category].pop(i)
                found = True
                break

        if not found:
            return False, f"在类别 '{category}' 中未找到敏感词 '{word}'"

        # 更新排序列表
        if word in self.sorted_words:
            self.sorted_words.remove(word)

        # 保存到文件
        if self._save_words():
            return True, f"敏感词 '{word}' 已从类别 '{category}' 中删除"
        else:
            return False, "保存敏感词失败"

    def get_words_by_category(self, category: str) -> list[dict[str, str]]:
        """获取指定类别的敏感词"""
        try:
            self.load_words()
            category_words = self.words.get(category, [])
            return category_words
        except Exception as e:
            print(f"获取类别敏感词失败: {e}")
            return []

    def _save_words(self) -> bool:
        """保存敏感词到文件"""
        try:
            with self.file_path.open("w", encoding="utf-8") as f:
                json.dump(self.words, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存敏感词文件出错: {e}")
            return False
