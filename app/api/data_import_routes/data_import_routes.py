import json
import logging
import os
import re
import tempfile
import uuid

import pandas as pd
from flask import current_app, jsonify, request

from app.utils.file_handlers import (
    allowed_file,
    cleanup_temp_files,
    parse_preview_message,
    save_temp_file,
    save_temp_info,
)

from . import bp

logger = logging.getLogger(__name__)


class BaseDataImportRoutes:
    def __init__(self, data_type, service_class, file_prefix=None):
        """
        初始化基础数据导入路由
        :param data_type: 数据类型标识符 (例如: 'case', 'faults', 'r_and_i_record')
        :param service_class: 用于处理数据的服务类
        :param file_prefix: 文件名前缀 (可选)
        """
        self.data_type = data_type
        self.service_class = service_class
        self.file_prefix = file_prefix
        self.processor = None

    def process_manual_import(self):
        """处理手动输入的数据"""
        try:
            logger.info(f"开始处理{self.data_type}手动输入数据")
            if not request.is_json:
                logger.error("请求不是JSON格式")
                return (
                    jsonify({"status": "error", "message": "请求必须是JSON格式"}),
                    400,
                )

            data = request.get_json()
            if not data or "data" not in data or not isinstance(data["data"], list):
                logger.error("数据格式错误或没有找到数据")
                return (
                    jsonify(
                        {"status": "error", "message": "数据格式错误或没有找到数据"}
                    ),
                    400,
                )

            rows = data["data"]
            if not rows:
                logger.error("没有找到有效的数据行")
                return (
                    jsonify({"status": "error", "message": "没有找到有效的数据行"}),
                    400,
                )

            # 过滤掉完全为空的行
            filtered_rows = []
            for row in rows:
                if any(
                    value.strip() for value in row.values() if isinstance(value, str)
                ):
                    filtered_rows.append(row)

            if not filtered_rows:
                logger.error("所有行都是空的")
                return jsonify({"status": "error", "message": "所有行都是空的"}), 400

            # 创建临时的Excel文件
            temp_id = str(uuid.uuid4())
            temp_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], temp_id)
            os.makedirs(temp_dir, exist_ok=True)

            excel_path = os.path.join(temp_dir, f"{self.data_type}_manual_import.xlsx")

            # 转换为DataFrame
            df = pd.DataFrame(filtered_rows)

            # 将DataFrame保存为Excel
            df.to_excel(excel_path, index=False)
            logger.info(f"手动输入数据已保存为临时Excel文件: {excel_path}")

            # 保存临时信息
            temp_info_path = os.path.join(
                current_app.config["UPLOAD_FOLDER"], f"{temp_id}_info.json"
            )
            with open(temp_info_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "file_path": excel_path,
                        "data_type": self.data_type,
                        "import_type": "manual",
                    },
                    f,
                )

            # 分析数据变化
            try:
                self.processor = self.service_class()
                success, message, combined_data = self.processor.analyze_changes(
                    excel_path
                )
                logger.info(f"数据分析结果: success={success}, message={message}")

                if not success:
                    cleanup_temp_files(temp_id)
                    return jsonify({"status": "error", "message": message}), 400

                # 解析预览信息
                stats = parse_preview_message(message)
                if not stats:
                    cleanup_temp_files(temp_id)
                    return (
                        jsonify({"status": "error", "message": "解析预览信息失败"}),
                        500,
                    )

                return jsonify(
                    {
                        "status": "success",
                        "data": stats,
                        "temp_id": temp_id,
                        "filename": f"{self.data_type}_manual_import.xlsx",
                    }
                )

            except Exception as e:
                logger.error(f"处理手动输入数据时出错: {str(e)}")
                cleanup_temp_files(temp_id)
                return (
                    jsonify({"status": "error", "message": f"处理数据失败: {str(e)}"}),
                    500,
                )

        except Exception as e:
            logger.error(f"处理手动输入数据时出错: {str(e)}")
            return (
                jsonify({"status": "error", "message": f"处理数据失败: {str(e)}"}),
                500,
            )

    def process_import(self):
        """处理文件上传并生成预览"""
        try:
            logger.info(f"开始处理{self.data_type}文件上传")
            if "file" not in request.files:
                logger.error("没有找到上传的文件")
                return (
                    jsonify({"status": "error", "message": "没有找到上传的文件"}),
                    400,
                )

            file = request.files["file"]
            if file.filename == "":
                logger.error("未选择文件")
                return jsonify({"status": "error", "message": "未选择文件"}), 400

            if not allowed_file(file.filename):
                return jsonify({"status": "error", "message": "不支持的文件类型"}), 400

            # 处理文件名
            filename = file.filename
            if self.file_prefix and re.match(r"^\d{8}.*\.xlsx$", filename):
                filename = f"{self.file_prefix}_{filename}"
                logger.info(f"已为文件添加前缀: {filename}")

            temp_id, temp_path = save_temp_file(file, self.data_type, filename)

            try:
                self.processor = self.service_class()
                success, message, combined_data = self.processor.analyze_changes(
                    temp_path
                )
                logger.info(f"数据分析结果: success={success}, message={message}")

                if not success:
                    cleanup_temp_files(temp_id)
                    return jsonify({"status": "error", "message": message}), 400

                # 保存临时信息
                save_temp_info(temp_id, temp_path, self.data_type, self.data_type)

                # 解析预览信息
                stats = parse_preview_message(message)
                if not stats:
                    cleanup_temp_files(temp_id)
                    return (
                        jsonify({"status": "error", "message": "解析预览信息失败"}),
                        500,
                    )

                return jsonify(
                    {
                        "status": "success",
                        "data": stats,
                        "temp_id": temp_id,
                        "filename": filename,
                    }
                )

            except Exception as e:
                logger.error(f"处理数据时出错: {str(e)}")
                cleanup_temp_files(temp_id)
                return (
                    jsonify({"status": "error", "message": f"处理上传失败: {str(e)}"}),
                    500,
                )

        except Exception as e:
            logger.error(f"处理文件上传时出错: {str(e)}")
            return (
                jsonify({"status": "error", "message": f"处理上传失败: {str(e)}"}),
                500,
            )

    def process_confirm(self):
        """确认导入数据"""
        try:
            data = request.get_json() if request.is_json else request.form.to_dict()
            temp_id = data.get("temp_id")

            if not temp_id:
                logger.error("缺少临时文件ID")
                return jsonify({"status": "error", "message": "缺少临时文件ID"}), 400

            processor = self.service_class()
            success, message = processor.confirm_import(temp_id)

            if success:
                # 清除数据缓存,强制重新加载
                from app import data_frames

                if self.data_type in data_frames:
                    del data_frames[self.data_type]

                return jsonify({"status": "success", "message": "数据导入成功"})
            else:
                return jsonify({"status": "error", "message": message}), 400

        except Exception as e:
            logger.error(f"确认导入时出错: {str(e)}")
            return jsonify({"status": "error", "message": str(e)}), 500
