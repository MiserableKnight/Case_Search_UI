"""
应用初始化模块
使用工厂模式创建Flask应用实例
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
import pandas as pd
import numpy as np
from app.services import WordService
from app.services.temp_file_manager import TempFileManager
from werkzeug.exceptions import HTTPException
from app.core.error_handler import AppError, InternalError
from app.services.error_service import ErrorService
from app.core.data_processors.fault_report_processor import load_fault_report_data
from app.core.data_processors.r_and_i_record_processor import load_r_and_i_data

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
    'faults': os.path.join('raw', 'faults.parquet'),
    'r_and_i_record': os.path.join('raw', 'r_and_i_record.parquet')
}

# 数据缓存
data_frames = {}

def create_app(config_name='development'):
    """
    应用工厂函数
    
    Args:
        config_name: 配置名称，默认为'development'
    
    Returns:
        Flask应用实例
    """
    # 加载环境变量
    load_dotenv()
    
    # 初始化 Flask 应用
    app = Flask(__name__, 
                static_folder='static',  # 指定静态文件夹路径
                static_url_path='/static')  # 指定静态文件URL前缀
    
    # 加载配置
    from app.config import config_by_name
    app.config.from_object(config_by_name[config_name])
    
    # 启用CORS
    CORS(app)
    
    # 确保数据目录存在
    for path in app.config['DATA_CONFIG'].values():
        if not os.path.exists(path):
            os.makedirs(path)
    
    # 初始化临时文件管理器
    temp_manager = TempFileManager()
    temp_manager.clean_old_files()  # 启动时清理一次
    temp_manager.start_scheduler()  # 启动定时任务
    app.temp_manager = temp_manager  # 将管理器添加到应用上下文
    
    # 初始化敏感词管理器
    app.word_manager = WordService(app.config['SENSITIVE_WORDS_FILE'])
    
    def allowed_file(filename, types=None):
        """检查文件扩展名是否允许"""
        if types is None:
            types = app.config['ALLOWED_EXTENSIONS']
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in types
    
    # 将 allowed_file 函数添加到应用上下文中
    app.allowed_file = allowed_file
    
    def load_data_source(source):
        """加载指定数据源的数据"""
        try:
            if source not in data_frames:
                data_path = os.path.join(app.config['DATA_CONFIG']['data_dir'], 
                                        app.config['DATA_SOURCES'][source])
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
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # 注册全局错误处理器
    @app.errorhandler(Exception)
    def handle_exception(e):
        """全局异常处理器"""
        return ErrorService.handle_exception(e)
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        """HTTP异常处理器"""
        return ErrorService.handle_exception(e)
    
    @app.errorhandler(AppError)
    def handle_app_error(e):
        """应用自定义异常处理器"""
        return ErrorService.handle_exception(e)
    
    @app.errorhandler(404)
    def handle_404(e):
        """404错误处理器"""
        return ErrorService.handle_exception(e)
    
    @app.errorhandler(500)
    def handle_500(e):
        """500错误处理器"""
        return ErrorService.handle_exception(e)
    
    @app.after_request
    def add_security_headers(response):
        response.headers['Content-Security-Policy'] = app.config['CONTENT_SECURITY_POLICY']
        return response
    
    # 在应用关闭时停止调度器
    @app.teardown_appcontext
    def shutdown_scheduler(exception=None):
        if hasattr(app, 'temp_manager'):
            app.temp_manager.stop_scheduler()

    # 初始化数据
    # 加载故障报告数据
    load_fault_report_data()
    
    # 加载部件拆换记录数据
    load_r_and_i_data()
    
    return app

# 创建默认应用实例
# 可以通过环境变量FLASK_ENV控制使用哪个配置
config_name = os.environ.get('FLASK_ENV', 'development')
app = create_app(config_name)