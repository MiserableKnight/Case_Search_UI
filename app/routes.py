from flask import request, jsonify, render_template, session, current_app, Blueprint
from app.utils.data_processing.case_processor import CaseProcessor
import os
import logging
import pandas as pd
import uuid
import json
import time
import jieba
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from werkzeug.utils import secure_filename

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 在文件顶部添加文件日志处理器
file_handler = logging.FileHandler('upload.log')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# 创建蓝图
bp = Blueprint('main', __name__)

# 修改上传文件夹路径
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'data', 'temp')
if not os.path.exists(UPLOAD_FOLDER):
    logger.info(f"创建上传目录: {UPLOAD_FOLDER}")
    os.makedirs(UPLOAD_FOLDER)

# 添加临时文件存储路径
TEMP_DATA_DIR = os.path.join(os.path.dirname(__file__), 'data', 'temp_data')
if not os.path.exists(TEMP_DATA_DIR):
    os.makedirs(TEMP_DATA_DIR)

@bp.record_once
def record_once(state):
    """在蓝图注册时运行一次的配置"""
    app = state.app
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 添加支持的Excel文件扩展名
ALLOWED_EXTENSIONS = {'xls', 'xlsx'}

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def parse_preview_message(message):
    """从预览消息中解析数据统计信息"""
    try:
        stats = {
            'original_count': 0,
            'uploaded_count': 0,
            'duplicate_count': 0,
            'new_count': 0,
            'final_count': 0
        }
        
        patterns = {
            'original_count': r'原有数据：(\d+)\s*条',
            'uploaded_count': r'上传数据：(\d+)\s*条',
            'duplicate_count': r'重复数据：(\d+)\s*条',
            'new_count': r'实际新增：(\d+)\s*条',
            'final_count': r'变更后数据：(\d+)\s*条'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, message)
            if match:
                stats[key] = int(match.group(1))
                
        return stats
    except Exception as e:
        logger.error(f"解析预览消息时出错: {str(e)}")
        return None

# 添加获取数据源列名的路由
@bp.route('/api/data_source_columns', methods=['GET'])
def get_data_source_columns():
    """获取所有数据源的列名"""
    try:
        columns = {}
        for source in current_app.config['DATA_SOURCES']:
            df = current_app.load_data_source(source)
            if df is not None:
                columns[source] = df.columns.tolist()
            else:
                columns[source] = []
        
        return jsonify({
            'status': 'success',
            'columns': columns
        })
    except Exception as e:
        logger.error(f"获取数据源列名时出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# 添加获取数据类型的路由
@bp.route('/api/data_types/<source>', methods=['GET'])
def get_data_types(source):
    """获取指定数据源的数据类型"""
    try:
        if source not in current_app.config['DATA_SOURCES']:
            return jsonify({
                'status': 'error',
                'message': '无效的数据源'
            }), 400
        
        df = current_app.load_data_source(source)
        if df is None:
            return jsonify({
                'status': 'error',
                'message': f'找不到数据源文件: {current_app.config["DATA_SOURCES"][source]}'
            }), 404
        
        logger.info(f"数据源 {source} 的列名: {df.columns.tolist()}")
        
        if '数据类型' not in df.columns:
            logger.warning(f"数据源 {source} 中没有找到'数据类型'列")
            return jsonify({
                'status': 'error',
                'message': f"数据源 {source} 中没有'数据类型'列"
            }), 500
        
        logger.info(f"数据源 {source} 的数据类型: {df['数据类型'].unique().tolist()}")
        
        data_types = sorted(df['数据类型'].unique().tolist())
        
        return jsonify({
            'status': 'success',
            'types': data_types
        })
    except Exception as e:
        logger.error(f"获取数据类型时出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# 添加搜索路由
@bp.route('/api/search', methods=['POST'])
def search():
    """搜索数据"""
    try:
        data = request.get_json()
        data_source = data.get('data_source', 'case')
        search_levels = data.get('search_levels', [])
        data_types = data.get('data_types', [])
        aircraft_types = data.get('aircraft_types', [])
        
        # 加载选定的数据源
        df = current_app.load_data_source(data_source)
        if df is None:
            return jsonify({
                'status': 'error',
                'message': f'找不到数据源文件: {current_app.config["DATA_SOURCES"][data_source]}'
            }), 404

        # 复制数据框以避免修改原始数据
        result_df = df.copy()
        
        # 首先按数据类型筛选
        if data_types:
            result_df = result_df[result_df['数据类型'].isin(data_types)]
            
        # 添加机型筛选
        if aircraft_types:
            result_df = result_df[result_df['机型'].isin(aircraft_types)]
        
        # 处理每个搜索层级
        for level in search_levels:
            keywords = level.get('keywords', '').strip()
            column_name = level.get('column_name')
            logic = level.get('logic', 'and')
            negative = level.get('negative_filtering', False)
            
            if not keywords:
                continue
                
            try:
                result_df = search_column(result_df, keywords, column_name, logic, negative)
            except ValueError as e:
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 400
        
        # 在返回结果之前，格式化C919的飞机序列号
        results = result_df.to_dict('records')
        
        # 添加序号列
        for index, item in enumerate(results, 1):
            item['序号'] = index
        
        return jsonify({
            'status': 'success',
            'data': results,
            'total': len(results)
        })
            
    except Exception as e:
        logger.error(f"搜索时出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

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

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/api/import_data', methods=['POST'])
def import_data():
    """处理文件上传并生成预览"""
    try:
        logger.info("开始处理文件上传")
        if 'file' not in request.files:
            logger.error("没有找到上传的文件")
            return jsonify({
                'status': 'error',
                'message': '没有找到上传的文件'
            }), 400

        file = request.files['file']
        data_source = request.form.get('dataSource', 'case')
        logger.info(f"数据源: {data_source}")

        if file.filename == '':
            logger.error("未选择文件")
            return jsonify({
                'status': 'error',
                'message': '未选择文件'
            }), 400

        # 使用 current_app 访问应用上下文中的函数和变量
        if not current_app.allowed_file(file.filename):
            return jsonify({
                'status': 'error',
                'message': '不支持的文件类型'
            }), 400

        # 生成临时ID
        temp_id = str(uuid.uuid4())
        logger.info(f"生成临时ID: {temp_id}")
        
        filename = secure_filename(file.filename)
        temp_path = os.path.join(UPLOAD_FOLDER, f"{temp_id}_{filename}")
        logger.info(f"临时文件路径: {temp_path}")
        
        try:
            file.save(temp_path)
            logger.info("文件保存成功")
        except Exception as e:
            logger.error(f"保存文件失败: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': f'保存文件失败: {str(e)}'
            }), 500

        # 根据数据源选择相应的处理器
        if data_source == 'case':
            processor = CaseProcessor(temp_path)
        else:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return jsonify({
                'status': 'error',
                'message': '暂不支持该数据源的导入'
            }), 400

        # 分析数据变化但不保存
        try:
            success, message, combined_data = processor.analyze_changes()
            logger.info(f"数据分析结果: success={success}, message={message}")
            
            if not success:
                cleanup_temp_files(temp_id)
                return jsonify({
                    'status': 'error',
                    'message': message
                }), 400

            # 保存临时信息
            temp_info = {
                'file_path': temp_path,
                'data_source': data_source,
                'timestamp': time.time(),
                'filename': filename
            }
            
            info_path = os.path.join(UPLOAD_FOLDER, f"{temp_id}_info.json")
            with open(info_path, 'w', encoding='utf-8') as f:
                json.dump(temp_info, f, ensure_ascii=False)
            logger.info("临时信息保存成功")

            # 解析预览信息
            stats = parse_preview_message(message)
            if not stats:
                cleanup_temp_files(temp_id)
                return jsonify({
                    'status': 'error',
                    'message': '解析预览信息失败'
                }), 500

            return jsonify({
                'status': 'success',
                'data': stats,
                'temp_id': temp_id,  # 确保返回temp_id
                'filename': filename
            })

        except Exception as e:
            logger.error(f"处理数据时出错: {str(e)}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return jsonify({
                'status': 'error',
                'message': f'处理上传失败: {str(e)}'
            }), 500

    except Exception as e:
        logger.error(f"处理文件上传时出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'处理上传失败: {str(e)}'
        }), 500

@bp.route('/api/confirm_import', methods=['POST'])
def confirm_import():
    """确认导入数据"""
    try:
        logger.info("接收到确认导入请求")
        logger.info(f"请求内容类型: {request.content_type}")
        logger.info(f"请求方法: {request.method}")
        
        # 尝试不同方式获取数据
        if request.is_json:
            data = request.get_json()
            logger.info(f"JSON数据: {data}")
        else:
            data = request.form.to_dict()
            logger.info(f"表单数据: {data}")
            
        # 获取temp_id
        temp_id = data.get('temp_id')
        logger.info(f"获取到的temp_id: {temp_id}")
        
        if not temp_id:
            logger.error("缺少临时文件ID")
            return jsonify({
                'status': 'error',
                'message': '缺少临时文件ID'
            }), 400

        # 获取数据源
        data_source = data.get('dataSource', 'case')
        logger.info(f"数据源: {data_source}")

        # 获取临时文件信息
        info_path = os.path.join(UPLOAD_FOLDER, f"{temp_id}_info.json")
        if not os.path.exists(info_path):
            logger.error(f"临时文件信息不存在: {info_path}")
            return jsonify({
                'status': 'error',
                'message': '临时文件已过期或不存在'
            }), 400

        try:
            with open(info_path, 'r', encoding='utf-8') as f:
                temp_info = json.load(f)
                logger.info(f"读取到的临时信息: {temp_info}")
        except Exception as e:
            logger.error(f"读取临时信息失败: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': f'读取临时信息失败: {str(e)}'
            }), 500

        # 验证数据源匹配
        if temp_info['data_source'] != data_source:
            cleanup_temp_files(temp_id)
            return jsonify({
                'status': 'error',
                'message': '数据源不匹配'
            }), 400

        # 获取临时文件路径
        temp_path = temp_info['file_path']
        if not os.path.exists(temp_path):
            cleanup_temp_files(temp_id)
            return jsonify({
                'status': 'error',
                'message': '临时文件不存在'
            }), 400

        try:
            # 根据数据源选择处理器
            if data_source == 'case':
                processor = CaseProcessor(temp_path)
            else:
                raise ValueError('暂不支持该数据源的导入')

            # 重新分析并保存数据
            success, message, combined_data = processor.analyze_changes()
            if success:
                save_success, save_message = processor.save_changes(combined_data)
                if not save_success:
                    raise Exception(save_message)
            else:
                raise Exception(message)

            # 清理临时文件
            cleanup_temp_files(temp_id)
            
            # 清除数据缓存,强制重新加载
            if data_source in current_app.config['DATA_SOURCES']:
                del current_app.config['DATA_SOURCES'][data_source]

            return jsonify({
                'status': 'success',
                'message': '数据导入成功'
            })

        except Exception as e:
            cleanup_temp_files(temp_id)
            raise e

    except Exception as e:
        logger.error(f"确认导入时出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/api/cancel_import', methods=['POST'])
def cancel_import():
    """取消导入并清理临时文件"""
    try:
        data = request.get_json()
        temp_id = data.get('temp_id')

        if temp_id:
            cleanup_temp_files(temp_id)

        return jsonify({
            'status': 'success',
            'message': '已取消导入'
        })

    except Exception as e:
        logger.error(f"取消导入时出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

def cleanup_temp_files(temp_id):
    """清理与指定temp_id相关的所有临时文件"""
    try:
        for filename in os.listdir(UPLOAD_FOLDER):
            if filename.startswith(temp_id):
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
    except Exception as e:
        logger.error(f"清理临时文件时出错: {str(e)}") 