"""
配置模块初始化文件
用于导入和设置配置
"""

from app.config.default import DefaultConfig
from app.config.development import DevelopmentConfig
from app.config.production import ProductionConfig

# 配置映射
config_by_name = {
    'default': DefaultConfig,
    'development': DevelopmentConfig,
    'production': ProductionConfig
} 