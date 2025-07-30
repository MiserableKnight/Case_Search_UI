"""
开发环境配置文件
"""

from app.config.default import DefaultConfig


class DevelopmentConfig(DefaultConfig):
    """开发环境配置类"""

    DEBUG = True
    TESTING = False

    # 可以在这里覆盖默认配置
    # 例如：
    # DATABASE_URI = "sqlite:///dev.db"
