from flask import Blueprint

# 创建蓝图，添加url_prefix
bp = Blueprint("api", __name__, url_prefix="/api")

# 导入路由
from . import (
    analysis_routes,
    data_source_routes,
    sensitive_word_routes,
    similarity_routes,
)
from .data_import_routes import bp as data_import_bp

# 注册数据导入蓝图，不需要额外的 url_prefix，因为已经在主蓝图中添加了 /api 前缀
bp.register_blueprint(data_import_bp)
