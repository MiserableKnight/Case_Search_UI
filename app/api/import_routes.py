from flask import request, jsonify, current_app
from app.api import bp
import logging
import os
import uuid
import json
import time
import re
from werkzeug.utils import secure_filename
from app.services import CaseService, FaultReportService, RAndIRecordService

logger = logging.getLogger(__name__)

# 上传文件夹配置
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'temp')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 临时数据目录
TEMP_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'temp_data')
os.makedirs(TEMP_DATA_DIR, exist_ok=True)

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
            'final_count': 0,
            'total_count': 0
        }
        
        # 使用与前端显示一致的格式
        patterns = {
            'original_count': r'原有数据：(\d+)\s*条',
            'uploaded_count': r'上传数据：(\d+)\s*条',
            'duplicate_count': r'重复数据：(\d+)\s*条',
            'new_count': r'实际新增：(\d+)\s*条',
            'final_count': r'变更后数据：(\d+)\s*条'
        }
        
        # 解析消息
        for key, pattern in patterns.items():
            match = re.search(pattern, message)
            if match:
                stats[key] = int(match.group(1))
        
        # 总数等于最终数
        stats['total_count'] = stats['final_count']
                
        return stats
    except Exception as e:
        logger.error(f"解析预览消息时出错: {str(e)}")
        return None

@bp.route('/import_data', methods=['POST'])
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
        if not allowed_file(file.filename):
            return jsonify({
                'status': 'error',
                'message': '不支持的文件类型'
            }), 400

        # 生成临时ID
        temp_id = str(uuid.uuid4())
        logger.info(f"生成临时ID: {temp_id}")
        
        filename = secure_filename(file.filename)
        
        # 根据选择的数据源处理文件名
        if data_source == 'faults':
            # 检查文件名是否只包含日期
            if re.match(r'^\d{8}.*\.xlsx$', filename):
                filename = f"故障报告_{filename}"
                logger.info(f"已为故障报告文件添加前缀: {filename}")
        elif data_source == 'r_and_i_record':
            # 如果选择了部件拆换记录数据源
            if not filename.startswith('部件拆换记录_'):
                # 如果文件名不以"部件拆换记录_"开头，则添加前缀
                if re.match(r'^\d{8}.*\.xlsx$', filename):
                    filename = f"部件拆换记录_{filename}"
                    logger.info(f"已为部件拆换记录文件添加前缀: {filename}")
        
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
            processor = CaseService()
            processor_type = 'case'
        elif data_source == 'faults':
            processor = FaultReportService()
            processor_type = 'fault_report'
            logger.info("使用故障报告处理器")
        elif data_source == 'r_and_i_record':
            processor = RAndIRecordService()
            processor_type = 'r_and_i_record'
            logger.info("使用部件拆换记录处理器")
        else:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return jsonify({
                'status': 'error',
                'message': '暂不支持该数据源的导入'
            }), 400

        # 分析数据变化但不保存
        try:
            success, message, combined_data = processor.analyze_changes(temp_path)
            logger.info(f"数据分析结果: success={success}, message={message}")
            
            if not success:
                cleanup_temp_files(temp_id)
                return jsonify({
                    'status': 'error',
                    'message': message
                }), 400
                
            # 保存临时信息
            temp_info = {
                'temp_id': temp_id,
                'file_path': temp_path,
                'data_source': data_source,
                'processor_type': processor_type,  # 添加处理器类型
                'timestamp': time.time()
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

@bp.route('/confirm_import', methods=['POST'])
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
                processor = CaseService()
            elif data_source == 'faults':
                processor = FaultReportService()
                logger.info("使用故障报告处理器")
            elif data_source == 'r_and_i_record':
                processor = RAndIRecordService()
                logger.info("使用部件拆换记录处理器")
            else:
                raise ValueError('暂不支持该数据源的导入')

            # 重新分析并保存数据
            success, message, combined_data = processor.analyze_changes(temp_path)
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
                # 不要删除配置中的路径信息，只清除数据缓存
                from app import data_frames
                if data_source in data_frames:
                    del data_frames[data_source]
                    print(f"已清除数据源 {data_source} 的缓存")
                
                # 如果是部件拆换记录数据，同时清除faults数据源的缓存
                if data_source == 'r_and_i_record' and 'faults' in data_frames:
                    del data_frames['faults']
                    print(f"已清除数据源 faults 的缓存")

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

@bp.route('/cancel_import', methods=['POST'])
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