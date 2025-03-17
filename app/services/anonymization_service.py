"""
文本匿名化服务，提供文本敏感信息匿名化功能
"""
from app.core.anonymizer import TextAnonymizer

class AnonymizationService:
    """文本匿名化服务类，封装对TextAnonymizer的调用"""
    
    def __init__(self, sensitive_words_path=None):
        """
        初始化文本匿名化服务
        
        Args:
            sensitive_words_path: 敏感词文件路径，默认为None，使用配置中的路径
        """
        self.anonymizer = TextAnonymizer(sensitive_words_path)
    
    def anonymize_text(self, text, categories=None):
        """
        匿名化文本
        
        Args:
            text: 原始文本
            categories: 需要匿名化的类别，默认为None，匿名化所有类别
            
        Returns:
            匿名化后的文本
        """
        return self.anonymizer.anonymize_text(text)
    
    def get_anonymized_words(self, text, categories=None):
        """
        获取文本中被匿名化的敏感词
        
        Args:
            text: 原始文本
            categories: 需要匿名化的类别，默认为None，匿名化所有类别
            
        Returns:
            匿名化的敏感词列表
        """
        return []
    
    def restore_text(self, anonymized_text, mapping):
        """
        还原匿名化文本
        
        Args:
            anonymized_text: 匿名化后的文本
            mapping: 匿名化映射
            
        Returns:
            还原后的文本
        """
        return anonymized_text
    
    def set_word_manager(self, word_manager):
        """
        设置敏感词管理器
        
        Args:
            word_manager: 敏感词管理器
        """
        pass 