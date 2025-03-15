from flask import request, jsonify, render_template, session, current_app, Blueprint, send_file
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
from app.utils.similarity import TextSimilarityCalculator

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
@bp.route('/api/data_source_columns')
def get_data_source_columns():
    """获取所有数据源的列名"""
    try:
        # 定义各数据源的基础列
        base_columns = {
            'case': [
                '故障发生日期', '申请时间', '标题', '版本号', '问题描述', '答复详情', 
                '客户期望', 'ATA', '机号/MSN', '运营人', '服务请求单编号', '机型', '数据类型'
            ],
            'engineering': [
                '发布时间', '文件名称', '原因和说明', '文件类型', 'MSN有效性', 
                '原文文本', '机型', '数据类型'
            ],
            'manual': [
                '申请时间', '问题描述', '答复详情', '飞机序列号/注册号/运营人',
                '机型', '数据类型'
            ],
            'faults': [
                '日期', '问题描述', '排故措施', '运营人', '飞机序列号', '机号',
                '机型', '数据类型'
            ]
        }

        # 获取实际数据源的列
        columns = {}
        for source in current_app.config['DATA_SOURCES']:
            try:
                # 首先尝试从实际数据中获取列
                df = current_app.load_data_source(source)
                if df is not None:
                    columns[source] = df.columns.tolist()
                else:
                    # 如果无法加载数据，使用基础列定义
                    columns[source] = base_columns.get(source, [])
                
                # 确保列表不为空
                if not columns[source]:
                    columns[source] = base_columns.get(source, [])
                
                # 记录日志
                logger.info(f"数据源 {source} 的列: {columns[source]}")
                
            except Exception as e:
                logger.warning(f"获取数据源 {source} 的列名时出错: {str(e)}")
                # 使用基础列作为后备
                columns[source] = base_columns.get(source, [])

        # 验证返回的数据
        if not columns or not any(cols for cols in columns.values()):
            raise ValueError("无法获取任何数据源的列信息")

        return jsonify({
            'status': 'success',
            'columns': columns
        })

    except Exception as e:
        error_msg = f"获取数据源列名失败: {str(e)}"
        logger.error(error_msg)
        return jsonify({
            'status': 'error',
            'message': error_msg
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

@bp.route('/test')
def test():
    return render_template('test.html')

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

@bp.route('/analysis')
def analysis():
    """数据分析页面路由"""
    return render_template('analysis.html')

@bp.route('/api/similarity', methods=['POST'])
def calculate_text_similarity():
    try:
        data = request.get_json()
        if not data:
            logger.error("相似度计算请求数据为空")
            return jsonify({
                'status': 'error',
                'message': '无效的请求数据'
            }), 400

        # 验证必需的字段
        required_fields = ['text', 'columns', 'results']
        for field in required_fields:
            if field not in data:
                logger.error(f"相似度计算请求缺少必需的字段: {field}")
                return jsonify({
                    'status': 'error',
                    'message': f'缺少必需的字段: {field}'
                }), 400

        # 记录请求信息
        logger.info(f"相似度计算请求: 搜索文本长度={len(data['text'])}, 搜索列={data['columns']}, 结果数量={len(data['results'])}")
        
        # 使用TextSimilarityCalculator计算相似度
        logger.info("开始调用TextSimilarityCalculator.calculate_similarity")
        sorted_results = TextSimilarityCalculator.calculate_similarity(
            data['text'],
            data['results'],
            data['columns']
        )
        logger.info(f"相似度计算完成，结果数量: {len(sorted_results)}")
        
        # 添加序号列
        for index, item in enumerate(sorted_results, 1):
            item['序号'] = index
        
        # 检查结果中是否包含相似度列
        if sorted_results and '相似度' in sorted_results[0]:
            logger.info(f"结果包含相似度列，第一条结果相似度: {sorted_results[0]['相似度']}")
        else:
            logger.warning("结果中不包含相似度列")

        return jsonify({
            'status': 'success',
            'data': sorted_results
        })

    except Exception as e:
        logger.error(f"计算相似度时出错: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'计算相似度失败: {str(e)}'
        }), 500

# 在现有路由之后添加敏感词管理相关的路由

@bp.route('/api/sensitive_words', methods=['GET'])
def get_sensitive_words():
    """获取敏感词列表"""
    try:
        word_manager = current_app.word_manager
        words = word_manager.get_all_words()
        return jsonify({
            'status': 'success',
            'words': words
        })
    except Exception as e:
        logger.error(f"获取敏感词列表失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'获取敏感词列表失败: {str(e)}'
        }), 500

@bp.route('/api/sensitive_words', methods=['POST'])
def add_sensitive_word():
    """添加敏感词"""
    try:
        data = request.get_json()
        if not data or 'word' not in data or 'category' not in data:
            return jsonify({
                'status': 'error',
                'message': '缺少必要参数'
            }), 400

        word = data['word']
        category = data['category']
        
        word_manager = current_app.word_manager
        success, message = word_manager.add_word(word, category)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': message
            })
        else:
            return jsonify({
                'status': 'error',
                'message': message
            }), 400
            
    except Exception as e:
        logger.error(f"添加敏感词失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'添加敏感词失败: {str(e)}'
        }), 500

@bp.route('/api/sensitive_words', methods=['DELETE'])
def remove_sensitive_word():
    """删除敏感词"""
    try:
        data = request.get_json()
        if not data or 'word' not in data or 'category' not in data:
            return jsonify({
                'status': 'error',
                'message': '缺少必要参数'
            }), 400

        word = data['word']
        category = data['category']
        
        word_manager = current_app.word_manager
        success, message = word_manager.remove_word(word, category)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': message
            })
        else:
            return jsonify({
                'status': 'error',
                'message': message
            }), 400
            
    except Exception as e:
        logger.error(f"删除敏感词失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'删除敏感词失败: {str(e)}'
        }), 500

@bp.route('/api/similarity_search', methods=['POST'])
def similarity_search():
    """相似度搜索功能"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': '无效的请求数据'
            }), 400

        # 验证必需的字段
        data_source = data.get('data_source', 'case')
        content = data.get('content', '').strip()
        columns = data.get('columns', [])
        data_types = data.get('data_types', [])
        aircraft_types = data.get('aircraft_types', [])
        
        logger.info(f"相似度搜索请求: 数据源={data_source}, 搜索列={columns}, 数据类型={data_types}, 机型={aircraft_types}")
        logger.info(f"搜索内容长度: {len(content)}")
        
        # 验证搜索内容
        if not content:
            return jsonify({
                'status': 'error',
                'message': '请输入要搜索的内容'
            }), 400
            
        # 验证搜索列
        if not columns or len(columns) == 0:
            return jsonify({
                'status': 'error',
                'message': '请选择要搜索的列'
            }), 400

        # 加载选定的数据源
        df = current_app.load_data_source(data_source)
        if df is None:
            logger.error(f"找不到数据源文件: {current_app.config['DATA_SOURCES'][data_source]}")
            return jsonify({
                'status': 'error',
                'message': f'找不到数据源文件: {current_app.config["DATA_SOURCES"][data_source]}'
            }), 404

        logger.info(f"成功加载数据源: {data_source}, 数据行数: {len(df)}")

        # 复制数据框以避免修改原始数据
        result_df = df.copy()
        
        # 首先按数据类型筛选
        if data_types:
            result_df = result_df[result_df['数据类型'].isin(data_types)]
            logger.info(f"按数据类型筛选后的行数: {len(result_df)}")
            
        # 添加机型筛选
        if aircraft_types:
            result_df = result_df[result_df['机型'].isin(aircraft_types)]
            logger.info(f"按机型筛选后的行数: {len(result_df)}")
        
        # 如果没有数据，直接返回空结果
        if result_df.empty:
            logger.info("筛选后没有数据，返回空结果")
            return jsonify({
                'status': 'success',
                'data': [],
                'total': 0
            })
        
        # 将结果转换为字典列表
        results = result_df.to_dict('records')
        logger.info(f"转换为字典列表，数量: {len(results)}")
        
        # 使用TextSimilarityCalculator计算相似度
        logger.info(f"开始计算相似度，搜索列: {columns}")
        sorted_results = TextSimilarityCalculator.calculate_similarity(
            content,
            results,
            columns
        )
        logger.info(f"相似度计算完成，结果数量: {len(sorted_results)}")
        
        # 添加序号列
        for index, item in enumerate(sorted_results, 1):
            item['序号'] = index
        
        return jsonify({
            'status': 'success',
            'data': sorted_results,
            'total': len(sorted_results)
        })

    except Exception as e:
        logger.error(f"相似度搜索时出错: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'相似度搜索失败: {str(e)}'
        }), 500 