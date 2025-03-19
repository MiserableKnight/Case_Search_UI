import logging
import os
from logging.handlers import RotatingFileHandler

import pandas as pd
from flask import Blueprint, current_app, render_template

from app.api.data_source_routes import search_column

# 确保日志目录存在
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 配置轮转日志处理器
log_file = os.path.join(log_dir, "app.log")
file_handler = RotatingFileHandler(
    log_file,
    maxBytes=10 * 1024 * 1024,  # 10MB
    backupCount=5,  # 保留5个备份文件
    encoding="utf-8",
)
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# 创建蓝图
bp = Blueprint("main", __name__)


@bp.route("/")
@bp.route("/index")
def index():
    """渲染主页"""
    return render_template("index.html", importSettings={"dataSource": "case"})


@bp.route("/test")
def test():
    return render_template("test.html")


@bp.route("/analysis")
def analysis():
    """渲染数据分析页面"""
    return render_template("analysis.html")


@bp.route("/data_import")
def data_import():
    """渲染数据导入页面"""
    return render_template("data_import.html")


def init_app(app):
    """初始化应用，注册蓝图"""
    # 注册主蓝图
    app.register_blueprint(bp)

    # 注册API蓝图
    from app.api import bp as api_bp

    app.register_blueprint(api_bp)

    # 添加搜索函数到应用上下文
    app.search_column = search_column

    return app
