"""
生产环境配置文件
"""

from app.config.default import DefaultConfig


class ProductionConfig(DefaultConfig):
    """生产环境配置类"""

    DEBUG = False
    TESTING = False

    # 生产环境特定配置
    # 例如：
    # DATABASE_URI = os.environ.get('DATABASE_URI')

    # 更严格的安全策略
    CONTENT_SECURITY_POLICY = (
        "default-src 'self' lib.baomitu.com; "
        "style-src 'self' lib.baomitu.com; "
        "script-src 'self' lib.baomitu.com; "
        "img-src 'self'; "
        "font-src 'self' lib.baomitu.com;"
    )
