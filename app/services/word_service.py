"""
敏感词管理服务，提供对敏感词的增删改查功能
"""
from app.core.word_manager import SensitiveWordManager

class WordService:
    """敏感词管理服务类，封装对SensitiveWordManager的调用"""
    
    def __init__(self, file_path=None):
        """
        初始化敏感词管理服务
        
        Args:
            file_path: 敏感词文件路径，默认为None，使用配置中的路径
        """
        self.word_manager = SensitiveWordManager(file_path)
    
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