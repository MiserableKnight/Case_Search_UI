import json
import logging
import os
import re
import uuid

from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)

# 上传文件夹配置
UPLOAD_FOLDER = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "temp"
)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 临时数据目录
TEMP_DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "temp_data"
)
os.makedirs(TEMP_DATA_DIR, exist_ok=True)

# 添加支持的Excel文件扩展名
ALLOWED_EXTENSIONS = {"xls", "xlsx"}


def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_temp_file(file, data_source, custom_filename=None):
    """保存上传的临时文件"""
    temp_id = str(uuid.uuid4())
    filename = custom_filename or secure_filename(file.filename)
    temp_path = os.path.join(UPLOAD_FOLDER, f"{temp_id}_{filename}")

    try:
        file.save(temp_path)
        logger.info(f"文件保存成功: {temp_path}")
        return temp_id, temp_path
    except Exception as e:
        logger.error(f"保存文件失败: {str(e)}")
        raise


def save_temp_info(temp_id, temp_path, data_source, processor_type):
    """保存临时文件信息"""
    try:
        temp_info = {
            "temp_id": temp_id,
            "file_path": temp_path,
            "data_source": data_source,
            "processor_type": processor_type,
        }

        info_path = os.path.join(UPLOAD_FOLDER, f"{temp_id}_info.json")
        with open(info_path, "w", encoding="utf-8") as f:
            json.dump(temp_info, f, ensure_ascii=False)
        logger.info("临时信息保存成功")

    except Exception as e:
        logger.error(f"保存临时信息失败: {str(e)}")
        raise


def parse_preview_message(message):
    """从预览消息中解析数据统计信息"""
    try:
        stats = {
            "original_count": 0,
            "uploaded_count": 0,
            "duplicate_count": 0,
            "new_count": 0,
            "final_count": 0,
            "total_count": 0,
        }

        # 使用与前端显示一致的格式
        patterns = {
            "original_count": r"原有数据：(\d+)\s*条",
            "uploaded_count": r"上传数据：(\d+)\s*条",
            "duplicate_count": r"重复数据：(\d+)\s*条",
            "new_count": r"实际新增：(\d+)\s*条",
            "final_count": r"变更后数据：(\d+)\s*条",
        }

        # 解析消息
        for key, pattern in patterns.items():
            match = re.search(pattern, message)
            if match:
                stats[key] = int(match.group(1))

        # 总数等于最终数
        stats["total_count"] = stats["final_count"]

        return stats
    except Exception as e:
        logger.error(f"解析预览消息时出错: {str(e)}")
        return None


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
        raise
