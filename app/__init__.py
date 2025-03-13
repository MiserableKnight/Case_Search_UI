from flask import Flask
from flask_cors import CORS
import os
from dotenv import load_dotenv
import pandas as pd
import numpy as np
from app.utils import SensitiveWordManager

# 配置数据目录
DATA_CONFIG = {
    'data_dir': os.path.join(os.path.dirname(__file__), 'data'),
    'temp_dir': os.path.join(os.path.dirname(__file__), 'data', 'temp'),
    'temp_data_dir': os.path.join(os.path.dirname(__file__), 'data', 'temp_data'),
}

# 文件配置
FILE_CONFIG = {
    'UPLOAD_FOLDER': os.path.join(os.path.dirname(__file__), 'data', 'temp'),
    'MAX_CONTENT_LENGTH': 16 * 1024 * 1024  # 16MB max-limit
}

# 数据源配置
DATA_SOURCES = {
    'case': 'case.parquet',
    'engineering': 'engineering.parquet',
    'manual': 'manual.parquet',
    'faults': 'faults.parquet'
}

# 数据缓存
data_frames = {}

def create_app():
    # 加载环境变量
    load_dotenv()

    # 初始化 Flask 应用
    app = Flask(__name__)
    CORS(app)

    # 配置应用
    app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev_key_for_session')
    app.config.update(FILE_CONFIG)
    app.config['DATA_SOURCES'] = DATA_SOURCES
    app.config['DATA_CONFIG'] = DATA_CONFIG
    
    # 确保数据目录存在
    for path in DATA_CONFIG.values():
        if not os.path.exists(path):
            os.makedirs(path)

    # 初始化敏感词管理器
    app.word_manager = SensitiveWordManager()

    # 允许的文件类型
    ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv', 'parquet'}

    def allowed_file(filename, types=None):
        """检查文件扩展名是否允许"""
        if types is None:
            types = ALLOWED_EXTENSIONS
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in types

    # 将 allowed_file 函数添加到应用上下文中
    app.allowed_file = allowed_file

    def load_data_source(source):
        """加载指定数据源的数据"""
        if source not in data_frames:
            try:
                data_path = os.path.join(os.path.dirname(__file__), "data", DATA_SOURCES[source])
                if os.path.exists(data_path):
                    print(f"加载数据源 {source} 从: {data_path}")
                    data_frames[source] = pd.read_parquet(data_path)
                    
                    # 添加机型检查
                    if '机型' in data_frames[source].columns:
                        unique_types = data_frames[source]['机型'].unique()
                        print(f"数据源 {source} 中的所有机型类别: {unique_types.tolist()}")
                        
                        # 检查是否存在未知机型
                        valid_types = {'ARJ21', 'C919', '无', None, '', np.nan}
                        unknown_types = set(unique_types) - valid_types
                        if unknown_types:
                            print(f"警告：发现未知机型: {unknown_types}")
                            raise ValueError(f"数据源 {source} 中存在未知机型: {unknown_types}")
                    
                    print(f"数据源 {source} 加载成功，形状: {data_frames[source].shape}")
                else:
                    print(f"数据文件不存在: {data_path}")
                    return None
            except Exception as e:
                print(f"加载数据源 {source} 时出错: {str(e)}")
                return None
        return data_frames[source]

    # 将 load_data_source 函数添加到应用上下文中
    app.load_data_source = load_data_source
    
    def format_msn(value):
        """格式化C919的机身序列号为5位数字"""
        try:
            if pd.isna(value) or not str(value).strip():
                return value
            
            # 如果是纯数字，进行格式化
            if str(value).isdigit():
                return f"{int(value):05d}"
            return value
        except:
            return value

    # 注册路由
    from app.routes import bp
    app.register_blueprint(bp)
    
    return app

# 创建应用实例
app = create_app()