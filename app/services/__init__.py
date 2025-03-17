"""
服务层模块，提供对核心功能的封装和对外接口
"""

# 导入服务
from .word_service import WordService
from .case_service import CaseService
from .similarity_service import SimilarityService
from .anonymization_service import AnonymizationService

# 导出所有服务
__all__ = [
    'WordService',
    'CaseService',
    'SimilarityService',
    'AnonymizationService'
] 