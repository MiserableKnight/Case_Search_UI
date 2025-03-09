import json
import os
import time
from pathlib import Path

class SensitiveWordManager:
    def __init__(self):
        # 获取当前文件所在目录的父目录（app目录）
        app_dir = Path(__file__).parent.parent
        self.sensitive_words_path = app_dir / 'data' / 'sensitive_words.json'
        self.words = self._load_words()
        self.sorted_words = self._create_sorted_list()  # 新增：维护一个已排序的敏感词列表
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

    def _load_words(self):
        """从文件加载敏感词"""
        if self.sensitive_words_path.exists():
            try:
                with open(self.sensitive_words_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载敏感词文件出错: {e}")
                return self._create_default_structure()
        else:
            return self._create_default_structure()

    def _create_default_structure(self):
        """创建默认的敏感词结构"""
        return {
            "organizations": [],
            "aircraft": [],
            "locations": [],
            "registration_numbers": [],
            "other": []
        }

    def _save_words(self):
        """保存敏感词到文件"""
        try:
            with open(self.sensitive_words_path, 'w', encoding='utf-8') as f:
                json.dump(self.words, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存敏感词文件出错: {e}")
            return False

    def _create_sorted_list(self):
        """创建按长度排序的敏感词列表"""
        all_words = []
        for category, words in self.words.items():
            all_words.extend([item['word'] for item in words])
        
        # 按长度降序排序
        return sorted(all_words, key=len, reverse=True)

    def get_all_words(self):
        """获取所有敏感词"""
        return self.words

    def get_sorted_words(self):
        """获取按长度排序的敏感词列表"""
        return self.sorted_words

    def add_word(self, word, category):
        """添加敏感词"""
        if not word or not word.strip():
            return False, "敏感词不能为空"
            
        if category not in self.words:
            return False, f"类别 '{category}' 不存在"
            
        word = word.strip()
        
        # 检查是否已存在
        for cat, word_list in self.words.items():
            if any(item['word'] == word for item in word_list):
                return False, f"敏感词 '{word}' 已存在于类别 '{cat}'"
                
        # 添加敏感词
        self.words[category].append({
            "word": word,
            "added_time": time.strftime("%Y-%m-%d %H:%M:%S")
        })
        
        # 更新排序列表
        self.sorted_words.append(word)
        self.sorted_words.sort(key=len, reverse=True)
        
        # 保存到文件
        if self._save_words():
            return True, f"敏感词 '{word}' 已添加到类别 '{category}'"
        else:
            return False, "保存敏感词失败"

    def remove_word(self, word, category):
        """删除敏感词"""
        if category not in self.words:
            return False, f"类别 '{category}' 不存在"
            
        # 查找并删除敏感词
        found = False
        for i, item in enumerate(self.words[category]):
            if item['word'] == word:
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