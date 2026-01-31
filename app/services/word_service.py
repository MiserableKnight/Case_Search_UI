"""
敏感词管理服务，提供对敏感词的增删改查功能
"""

import json
from pathlib import Path

from flask import current_app

from app.core.word_manager import SensitiveWordManager


class WordService:
    """敏感词管理服务类，封装对SensitiveWordManager的调用"""

    def __init__(self, file_path=None):
        """
        初始化敏感词管理服务

        Args:
            file_path: 敏感词文件路径，默认为None，使用配置中的路径
        """
        if file_path is None:
            # 使用配置中的路径
            file_path = current_app.config["FILE_CONFIG"]["SENSITIVE_WORDS_FILE"]

        # 初始化敏感词管理器
        self.word_manager = SensitiveWordManager(file_path)
        self.file_path = Path(file_path)

        # 定义类别
        self.categories = [
            "organizations",
            "aircraft",
            "locations",
            "registration_numbers",
            "other",
        ]
        self.category_labels = {
            "organizations": "组织机构",
            "aircraft": "设备型号",
            "locations": "地点",
            "registration_numbers": "机号/MSN",
            "other": "其他",
        }

        # 修改初始化顺序，确保文件存在后再加载
        if self._ensure_file_exists():
            self.load_words()
            self.sorted_words = self._create_sorted_list()
        else:
            # 如果文件创建失败，使用默认空数据
            self.words = {
                "organizations": [],
                "aircraft": [],
                "locations": [],
                "registration_numbers": [],
                "other": [],
            }
            self.sorted_words = []

    def get_all_words(self):
        """获取所有敏感词"""
        return self.word_manager.get_all_words()

    def get_sorted_words(self):
        """获取按类别排序的敏感词"""
        return self.word_manager.get_sorted_words()

    def add_word(self, word, category):
        """
        添加敏感词

        Args:
            word: 敏感词
            category: 类别

        Returns:
            添加结果
        """
        return self.word_manager.add_word(word, category)

    def remove_word(self, word, category):
        """
        删除敏感词

        Args:
            word: 敏感词
            category: 类别

        Returns:
            删除结果
        """
        return self.word_manager.remove_word(word, category)

    def get_words_by_category(self, category):
        """
        获取指定类别的敏感词

        Args:
            category: 类别

        Returns:
            该类别下的敏感词列表
        """
        return self.word_manager.get_words_by_category(category)

    def get_categories(self):
        """获取所有敏感词类别"""
        return self.word_manager.categories

    def get_category_labels(self):
        """获取所有敏感词类别标签"""
        return self.word_manager.category_labels

    def _ensure_file_exists(self):
        if not self.file_path.exists():
            self.file_path.touch()
            return False
        return True

    def load_words(self):
        with open(self.file_path, encoding="utf-8") as f:
            self.words = json.load(f)

    def _create_sorted_list(self):
        sorted_words = []
        for category in self.categories:
            sorted_words.extend(self.words[category])
        return sorted_words
