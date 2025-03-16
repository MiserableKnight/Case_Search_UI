from flask import Blueprint, render_template, current_app
import os
import logging
import pandas as pd
from logging.handlers import RotatingFileHandler

# 确保日志目录存在
log_dir = 'logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 配置轮转日志处理器
log_file = os.path.join(log_dir, 'app.log')
file_handler = RotatingFileHandler(
    log_file,
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5,          # 保留5个备份文件
    encoding='utf-8'
)
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# 创建蓝图
bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/test')
def test():
    return render_template('test.html')

def search_column(df, keywords, column_name, logic='and', negative_filtering=False):
    """基础搜索功能"""
    if not keywords:
        return df
        
    # 将所有关键字转换为小写
    if isinstance(keywords, str):
        keywords = keywords.replace('，', ',')
        keywords = [k.strip() for k in keywords.split(',') if k.strip()]
    keywords = [str(k).lower() for k in keywords]
    
    # 确定要搜索的列
    if isinstance(column_name, str):
        columns_to_search = [column_name]
    elif isinstance(column_name, list):
        columns_to_search = [col for col in column_name if col in df.columns]
    else:
        raise ValueError("无效的列名参数")
    
    if not columns_to_search:
        raise ValueError("未指定有效的搜索列")
    
    # 使用相同的搜索逻辑
    if logic == 'and':
        final_mask = pd.Series(True, index=df.index)
        for keyword in keywords:
            keyword_mask = pd.Series(False, index=df.index)
            for col in columns_to_search:
                col_values = df[col].fillna('').astype(str).str.lower()
                keyword_mask |= col_values.str.contains(keyword, na=False, regex=False)
            final_mask &= keyword_mask
    else:  # logic == 'or'
        final_mask = pd.Series(False, index=df.index)
        for keyword in keywords:
            for col in columns_to_search:
                col_values = df[col].fillna('').astype(str).str.lower()
                final_mask |= col_values.str.contains(keyword, na=False, regex=False)
    
    # 根据negative_filtering参数决定是否反向过滤
    return df[~final_mask] if negative_filtering else df[final_mask]

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