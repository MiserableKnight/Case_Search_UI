"""
相似度计算服务，提供文本相似度计算功能
"""
from app.core.calculator import TextSimilarityCalculator

class SimilarityService:
    """相似度计算服务类，封装对TextSimilarityCalculator的调用"""
    
    def __init__(self, config=None):
        """
        初始化相似度计算服务
        
        Args:
            config: 配置信息，默认为None，不使用
        """
        # TextSimilarityCalculator使用静态方法，不需要实例化
        self.config = config
    
    def calculate_similarity(self, text1, text2, method='tfidf'):
        """
        计算两段文本的相似度
        
        Args:
            text1: 第一段文本
            text2: 第二段文本
            method: 计算方法，默认为'tfidf'
            
        Returns:
            相似度得分
        """
        # 调用静态方法
        return TextSimilarityCalculator.calculate_similarity(text1, text2, method)
    
    def calculate_batch_similarity(self, query_text, text_list, columns):
        """
        批量计算一段文本与多段文本的相似度
        
        Args:
            query_text: 查询文本
            text_list: 文本列表
            columns: 要比较的列
            
        Returns:
            相似度得分列表
        """
        # 调用类方法
        return TextSimilarityCalculator.calculate_similarity(query_text, text_list, columns)
    
    def get_available_methods(self):
        """
        获取可用的相似度计算方法
        
        Returns:
            方法列表
        """
        # 这个方法在原类中可能不存在，返回默认值
        return ['tfidf']
    
    def preprocess_text(self, text):
        """
        预处理文本
        
        Args:
            text: 原始文本
            
        Returns:
            预处理后的文本
        """
        # 调用静态方法
        return TextSimilarityCalculator.chinese_word_cut(text) 