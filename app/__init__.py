from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
import pandas as pd
import numpy as np
from app.services import WordService

# 配置数据目录
DATA_CONFIG = {
    'data_dir': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data'),
    'temp_dir': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'temp'),
    'processed_dir': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'processed'),
    'raw_dir': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'raw')
}

# 文件配置
FILE_CONFIG = {
    'UPLOAD_FOLDER': DATA_CONFIG['temp_dir'],
    'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,  # 16MB max-limit
    'SENSITIVE_WORDS_FILE': os.path.join(DATA_CONFIG['raw_dir'], 'sensitive_words.json')
}

# 数据源配置
DATA_SOURCES = {
    'case': os.path.join('raw', 'case.parquet'),
    'engineering': os.path.join('raw', 'engineering.parquet'),
    'manual': os.path.join('raw', 'manual.parquet'),
    'faults': os.path.join('raw', 'faults.parquet')
}

# 数据缓存
data_frames = {}

def create_app():
    # 加载环境变量
    load_dotenv()

    # 初始化 Flask 应用
    app = Flask(__name__, 
                static_folder='static',  # 指定静态文件夹路径
                static_url_path='/static')  # 指定静态文件URL前缀
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
    app.word_manager = WordService(FILE_CONFIG['SENSITIVE_WORDS_FILE'])

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
        try:
            if source not in data_frames:
                data_path = os.path.join(DATA_CONFIG['data_dir'], DATA_SOURCES[source])
                if os.path.exists(data_path):
                    print(f"加载数据源 {source} 从: {data_path}")
                    data_frames[source] = pd.read_parquet(data_path)
                    print(f"数据源 {source} 加载成功，形状: {data_frames[source].shape}")
                else:
                    print(f"数据文件不存在: {data_path}")
                    return None
            return data_frames[source]
        except Exception as e:
            print(f"加载数据源 {source} 时出错: {str(e)}")
            return None

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

    # 添加脱敏处理路由
    @app.route('/api/anonymize', methods=['POST'])
    def anonymize():
        try:
            data = request.get_json()
            if not data or 'results' not in data or 'fields' not in data:
                return jsonify({'status': 'error', 'message': '无效的请求数据'})
            
            results = data['results']
            fields = data['fields']
            data_source = data.get('dataSource', 'case')
            
            # 初始化脱敏器
            from app.services import AnonymizationService
            anonymizer_service = AnonymizationService()
            
            # 对指定字段进行脱敏
            for result in results:
                for field in fields:
                    if field in result and result[field]:
                        result[field] = anonymizer_service.anonymize_text(result[field])
            
            return jsonify({
                'status': 'success',
                'data': results
            })
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'脱敏处理失败: {str(e)}'
            })

    # 注册路由
    from app.routes import bp
    app.register_blueprint(bp)
    
    # 注册API蓝图
    from app.api import bp as api_bp
    app.register_blueprint(api_bp)
    
    @app.after_request
    def add_security_headers(response):
        response.headers['Content-Security-Policy'] = (
            "default-src 'self' lib.baomitu.com; "
            "style-src 'self' 'unsafe-inline' lib.baomitu.com; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' lib.baomitu.com; "
            "img-src 'self' data:; "
            "font-src 'self' data: lib.baomitu.com;"
        )
        return response

    return app

# 创建应用实例
app = create_app()