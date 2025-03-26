"""
相似度计算服务，提供文本相似度计算功能
"""

import logging
from typing import Any, Dict, List, Optional

from flask import current_app

from app.core.calculator import TextSimilarityCalculator
from app.core.error_handler import ServiceError, ValidationError

logger = logging.getLogger(__name__)


class SimilarityService:
    """相似度计算服务类，封装对TextSimilarityCalculator的调用"""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        初始化相似度计算服务

        Args:
            config: 配置信息，默认为None，不使用
        """
        # TextSimilarityCalculator使用静态方法，不需要实例化
        self.config = config

    def calculate_similarity(
        self, text1: str, text2: str, method: str = "tfidf"
    ) -> float:
        """
        计算两段文本的相似度

        Args:
            text1: 第一段文本
            text2: 第二段文本
            method: 计算方法，默认为'tfidf'

        Returns:
            相似度得分
        """
        if not text1 or not text2:
            raise ValidationError("文本不能为空")

        try:
            # 调用静态方法
            return TextSimilarityCalculator.calculate_similarity(text1, text2, method)
        except Exception as e:
            logger.error(f"计算相似度时出错: {str(e)}")
            raise ServiceError(f"计算相似度失败: {str(e)}")

    def calculate_batch_similarity(
        self, query_text: str, text_list: List[Dict[str, Any]], columns: List[str]
    ) -> List[Dict[str, Any]]:
        """
        批量计算一段文本与多段文本的相似度

        Args:
            query_text: 查询文本
            text_list: 文本列表
            columns: 要比较的列

        Returns:
            相似度得分列表
        """
        if not query_text:
            raise ValidationError("查询文本不能为空")

        if not text_list:
            logger.warning("文本列表为空，返回空结果")
            return []

        if not columns or len(columns) == 0:
            raise ValidationError("必须指定至少一个比较列")

        try:
            # 直接使用 TextSimilarityCalculator 类方法
            return TextSimilarityCalculator.calculate_similarity(
                query_text, text_list, columns
            )
        except Exception as e:
            logger.error(f"批量计算相似度时出错: {str(e)}")
            raise ServiceError(f"批量计算相似度失败: {str(e)}")

    def get_available_methods(self) -> List[str]:
        """
        获取可用的相似度计算方法

        Returns:
            可用方法列表
        """
        try:
            # 直接使用 TextSimilarityCalculator 实例方法
            calculator = TextSimilarityCalculator()
            return calculator.get_available_methods()
        except Exception as e:
            logger.error(f"获取可用方法时出错: {str(e)}")
            raise ServiceError(f"获取可用方法失败: {str(e)}")

    def preprocess_text(self, text: str) -> str:
        """
        预处理文本

        Args:
            text: 要预处理的文本

        Returns:
            预处理后的文本
        """
        if not text:
            return ""

        try:
            # 直接使用 TextSimilarityCalculator 实例方法
            calculator = TextSimilarityCalculator()
            return calculator.preprocess_text(text)
        except Exception as e:
            logger.error(f"预处理文本时出错: {str(e)}")
            raise ServiceError(f"预处理文本失败: {str(e)}")

    def search_by_similarity(
        self, search_text: str, data_source: str, columns: List[str], limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        根据相似度搜索数据

        Args:
            search_text: 搜索文本
            data_source: 数据源名称
            columns: 要搜索的列
            limit: 返回结果数量限制

        Returns:
            搜索结果列表
        """
        if not search_text:
            raise ValidationError("搜索文本不能为空")

        if not columns or len(columns) == 0:
            raise ValidationError("必须指定至少一个搜索列")

        try:
            # 加载数据源
            df = current_app.load_data_source(data_source)
            if df is None:
                raise ValidationError(f"找不到数据源: {data_source}")

            logger.info(f"成功加载数据源: {data_source}, 数据行数: {len(df)}")

            # 转换为字典列表
            results = df.to_dict("records")

            # 计算相似度
            sorted_results = self.calculate_batch_similarity(
                search_text, results, columns
            )

            # 限制结果数量
            if limit > 0 and len(sorted_results) > limit:
                sorted_results = sorted_results[:limit]

            return sorted_results

        except ValidationError:
            # 重新抛出验证错误
            raise
        except Exception as e:
            logger.error(f"相似度搜索时出错: {str(e)}")
            raise ServiceError(f"相似度搜索失败: {str(e)}")
