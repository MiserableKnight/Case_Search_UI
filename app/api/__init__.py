from flask import Blueprint

# 创建蓝图，添加url_prefix
bp = Blueprint('api', __name__, url_prefix='/api')

# 导入路由
from .data_source_routes import *
from .sensitive_word_routes import *
from .similarity_routes import *
from .import_routes import *
from .analysis_routes import *