import json
import os
from pathlib import Path

class SensitiveWordManager:
    def __init__(self):
        # 获取当前文件所在目录的父目录（app目录）
        app_dir = Path(__file__).parent.parent
        self.sensitive_words_path = app_dir / 'data' / 'sensitive_words.json'
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """确保敏感词文件存在，如果不存在则创建"""
        try:
            if not self.sensitive_words_path.exists():
                self.sensitive_words_path.parent.mkdir(parents=True, exist_ok=True)
                initial_data = {
                    "organizations": [],
                    "aircraft": [],
                    "locations": [],
                    "registration_numbers": [],
                    "other": []
                }
                with open(self.sensitive_words_path, 'w', encoding='utf-8') as f:
                    json.dump(initial_data, f, ensure_ascii=False, indent=4)
                print(f"已创建敏感词文件: {self.sensitive_words_path}")
        except Exception as e:
            print(f"创建敏感词文件失败: {e}")

    def load_words(self):
        """加载敏感词"""
        try:
            if not self.sensitive_words_path.exists():
                print(f"敏感词文件不存在，正在创建: {self.sensitive_words_path}")
                self._ensure_file_exists()
            
            with open(self.sensitive_words_path, 'r', encoding='utf-8') as f:
                words = json.load(f)
                print(f"成功加载敏感词: {words}")
                return words
        except FileNotFoundError:
            print(f"敏感词文件不存在: {self.sensitive_words_path}")
            return {
                "organizations": [],
                "aircraft": [],
                "locations": [],
                "registration_numbers": [],
                "other": []
            }
        except json.JSONDecodeError as e:
            print(f"敏感词文件格式错误: {self.sensitive_words_path}, 错误: {e}")
            return {
                "organizations": [],
                "aircraft": [],
                "locations": [],
                "registration_numbers": [],
                "other": []
            }
        except Exception as e:
            print(f"加载敏感词文件时发生错误: {e}")
            return {
                "organizations": [],
                "aircraft": [],
                "locations": [],
                "registration_numbers": [],
                "other": []
            }

    def save_words(self, words):
        """保存敏感词"""
        try:
            # 确保目录存在
            self.sensitive_words_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.sensitive_words_path, 'w', encoding='utf-8') as f:
                json.dump(words, f, ensure_ascii=False, indent=4)
            print(f"成功保存敏感词: {words}")
            return True
        except Exception as e:
            print(f"保存敏感词失败: {e}")
            return False

    def add_word(self, word, category):
        """添加敏感词"""
        try:
            words = self.load_words()
            
            # 检查所有类别是否已存在该词
            for cat_words in words.values():
                if any(w.get('word') == word for w in cat_words):
                    print(f"敏感词已存在: {word}")
                    return False, "该敏感词已存在"
            
            # 添加新词
            if category not in words:
                print(f"无效的类别: {category}")
                return False, "无效的类别"
            
            words[category].append({"word": word})
            if self.save_words(words):
                print(f"成功添加敏感词: {word} 到类别: {category}")
                return True, "添加成功"
            return False, "保存失败"
        except Exception as e:
            print(f"添加敏感词失败: {e}")
            return False, str(e)

    def remove_word(self, word, category):
        """删除敏感词"""
        try:
            words = self.load_words()
            if category not in words:
                print(f"无效的类别: {category}")
                return False, "无效的类别"
            
            original_length = len(words[category])
            words[category] = [w for w in words[category] if w.get('word') != word]
            
            if len(words[category]) == original_length:
                print(f"未找到要删除的敏感词: {word}")
                return False, "未找到要删除的敏感词"
            
            if self.save_words(words):
                print(f"成功删除敏感词: {word} 从类别: {category}")
                return True, "删除成功"
            return False, "保存失败"
        except Exception as e:
            print(f"删除敏感词失败: {e}")
            return False, str(e)

    def get_all_words(self):
        """获取所有敏感词"""
        try:
            words = self.load_words()
            print(f"获取所有敏感词: {words}")
            return words
        except Exception as e:
            print(f"获取所有敏感词失败: {e}")
            return {
                "organizations": [],
                "aircraft": [],
                "locations": [],
                "registration_numbers": [],
                "other": []
            }

    def get_words_by_category(self, category):
        """获取指定类别的敏感词"""
        try:
            words = self.load_words()
            category_words = words.get(category, [])
            print(f"获取类别 {category} 的敏感词: {category_words}")
            return category_words
        except Exception as e:
            print(f"获取类别敏感词失败: {e}")
            return [] 