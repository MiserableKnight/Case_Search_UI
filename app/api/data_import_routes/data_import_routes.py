import json
import logging
import os
import re
import shutil
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

    def _ensure_temp_dir(self, temp_id):
        """确保临时目录存在且有正确的访问权限"""
        try:
            # 使用系统临时目录作为基础
            temp_base_dir = tempfile.gettempdir()
            # 在临时目录中创建一个应用特定的子目录
            app_temp_dir = os.path.join(temp_base_dir, "case_search_ui_temp")
            os.makedirs(app_temp_dir, exist_ok=True)

            # 创建特定导入请求的子目录
            temp_dir = os.path.join(app_temp_dir, temp_id)
            os.makedirs(temp_dir, exist_ok=True)

            # 设置目录权限
            os.chmod(temp_dir, 0o755)  # rwxr-xr-x

            return temp_dir
        except Exception as e:
            logger.exception(f"创建临时目录时出错: {str(e)}")
            raise

    def process_manual_import(self):
        """处理手动输入的数据"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({"status": "error", "message": "未接收到数据"}), 400

            # 创建唯一的临时目录
            temp_id = str(uuid.uuid4())
            try:
                # 使用安全的临时目录创建方法
                temp_dir = self._ensure_temp_dir(temp_id)
                excel_path = os.path.join(temp_dir, f"{temp_id}.xlsx")

                # 将数据转换为DataFrame并保存为Excel
                df = pd.DataFrame(data)
                df.to_excel(excel_path, index=False)
                logger.info(f"手动输入数据已保存为临时Excel文件: {excel_path}")

                # 保存临时信息
                temp_info_path = os.path.join(temp_dir, f"{temp_id}_info.json")
                with open(temp_info_path, "w", encoding="utf-8") as f:
                    json.dump(
                        {
                            "file_path": excel_path,
                            "data_type": self.data_type,
                            "import_type": "manual",
                        },
                        f,
                    )

                # 分析数据变化（启用Unicode清洗）
                self.processor = self.service_class()
                success, message, combined_data = self.processor.analyze_changes(
                    excel_path, enable_unicode_cleaning=True
                )

                if not success:
                    # 清理临时文件
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    return jsonify({"status": "error", "message": message}), 400

                # 解析预览信息
                stats = parse_preview_message(message)
                if not stats:
                    # 清理临时文件
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    return (
                        jsonify({"status": "error", "message": "解析预览信息失败"}),
                        500,
                    )

                # 获取预览数据
                preview_rows = df.head(10).to_dict("records")  # 获取前10行数据
                columns = df.columns.tolist()  # 获取列名列表

                # 合并统计信息和预览数据
                preview_data = {
                    **stats,
                    "preview_rows": preview_rows,
                    "columns": columns,
                }

                return jsonify(
                    {
                        "status": "success",
                        "message": "手动输入数据处理成功",
                        "data": preview_data,
                        "temp_id": temp_id,
                    }
                )
            except Exception as e:
                logger.exception(f"分析数据变化时出错: {str(e)}")
                try:
                    # 尝试清理临时目录
                    temp_dir = self._ensure_temp_dir(temp_id)
                    shutil.rmtree(temp_dir, ignore_errors=True)
                except:
                    pass
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": f"分析数据变化时出错: {str(e)}",
                        }
                    ),
                    500,
                )
        except Exception as e:
            logger.exception(f"处理手动输入数据时出错: {str(e)}")
            return jsonify({"status": "error", "message": str(e)}), 500

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

            # 创建唯一的临时目录
            temp_id = str(uuid.uuid4())
            try:
                # 使用安全的临时目录创建方法
                temp_dir = self._ensure_temp_dir(temp_id)
                excel_path = os.path.join(temp_dir, filename)

                # 保存上传文件
                file.save(excel_path)
                logger.info(f"上传文件已保存为临时Excel文件: {excel_path}")

                # 保存临时信息
                temp_info_path = os.path.join(temp_dir, f"{temp_id}_info.json")
                with open(temp_info_path, "w", encoding="utf-8") as f:
                    json.dump(
                        {
                            "file_path": excel_path,
                            "data_type": self.data_type,
                            "import_type": "upload",
                        },
                        f,
                    )

                # 分析数据变化（启用Unicode清洗）
                self.processor = self.service_class()
                success, message, combined_data = self.processor.analyze_changes(
                    excel_path, enable_unicode_cleaning=True
                )

                if not success:
                    # 清理临时文件
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    return jsonify({"status": "error", "message": message}), 400

                # 解析预览信息
                stats = parse_preview_message(message)
                if not stats:
                    # 清理临时文件
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    return (
                        jsonify({"status": "error", "message": "解析预览信息失败"}),
                        500,
                    )

                # 读取上传的Excel文件获取预览数据
                try:
                    df = pd.read_excel(excel_path)
                    preview_rows = df.head(10).to_dict("records")  # 获取前10行数据
                    columns = df.columns.tolist()  # 获取列名列表
                except Exception as e:
                    logger.error(f"读取预览数据时出错: {str(e)}")
                    preview_rows = []
                    columns = []

                # 合并统计信息和预览数据
                preview_data = {
                    **stats,
                    "preview_rows": preview_rows,
                    "columns": columns,
                }

                return jsonify(
                    {
                        "status": "success",
                        "message": "预览处理成功",
                        "preview": preview_data,
                        "temp_id": temp_id,
                    }
                )
            except Exception as e:
                logger.exception(f"预览分析时出错: {str(e)}")
                try:
                    # 尝试清理临时目录
                    temp_dir = self._ensure_temp_dir(temp_id)
                    shutil.rmtree(temp_dir, ignore_errors=True)
                except:
                    pass
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": f"预览分析时出错: {str(e)}",
                        }
                    ),
                    500,
                )
        except Exception as e:
            logger.exception(f"处理预览请求时出错: {str(e)}")
            return jsonify({"status": "error", "message": str(e)}), 500

    def process_confirm(self):
        """确认导入数据"""
        try:
            data = request.get_json() if request.is_json else request.form.to_dict()
            temp_id = data.get("temp_id")

            if not temp_id:
                logger.error("缺少临时文件ID")
                return jsonify({"status": "error", "message": "缺少临时文件ID"}), 400

            # 处理临时目录路径
            temp_base_dir = tempfile.gettempdir()
            app_temp_dir = os.path.join(temp_base_dir, "case_search_ui_temp")
            temp_dir = os.path.join(app_temp_dir, temp_id)

            # 检查临时目录是否存在
            if not os.path.exists(temp_dir):
                logger.error(f"临时目录 {temp_dir} 不存在")
                return (
                    jsonify(
                        {"status": "error", "message": "无法找到临时数据，请重新预览"}
                    ),
                    400,
                )

            # 获取临时信息文件路径
            temp_info_path = os.path.join(temp_dir, f"{temp_id}_info.json")

            # 检查临时信息文件是否存在
            if not os.path.exists(temp_info_path):
                logger.error(f"临时信息文件 {temp_info_path} 不存在")
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": "无法找到临时数据信息，请重新预览",
                        }
                    ),
                    400,
                )

            # 读取临时信息
            with open(temp_info_path, "r", encoding="utf-8") as f:
                temp_info = json.load(f)

            excel_path = temp_info.get("file_path")

            # 检查Excel文件是否存在
            if not os.path.exists(excel_path):
                logger.error(f"临时Excel文件 {excel_path} 不存在")
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": "无法找到临时Excel文件，请重新预览",
                        }
                    ),
                    400,
                )

            processor = self.service_class()
            success, message = processor.confirm_import(excel_path)

            # 无论成功与否，都尝试清理临时文件
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception as e:
                logger.warning(f"清理临时目录时出错: {str(e)}")

            if success:
                # 清除数据缓存,强制重新加载
                from app import data_frames

                if self.data_type in data_frames:
                    del data_frames[self.data_type]

                return jsonify(
                    {
                        "status": "success",
                        "message": "数据导入成功",
                        "data": {
                            "new_count": (
                                re.search(r"成功导入\s*(\d+)\s*条", message).group(1)
                                if re.search(r"成功导入\s*(\d+)\s*条", message)
                                else 0
                            )
                        },
                    }
                )
            else:
                return jsonify({"status": "error", "message": message}), 400

        except Exception as e:
            logger.error(f"确认导入时出错: {str(e)}")
            return jsonify({"status": "error", "message": str(e)}), 500

    def process_preview(self):
        """处理预览请求，用于手动数据导入"""
        try:
            logger.info(f"开始处理{self.data_type}预览请求")
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
            # 过滤掉完全为空的行
            filtered_rows = []
            for row in rows:
                # 检查行中至少有一个非空值
                if any(value for value in row.values() if value and str(value).strip()):
                    filtered_rows.append(row)

            if not filtered_rows:
                logger.error("所有行都是空的")
                return jsonify({"status": "error", "message": "所有行都是空的"}), 400

            # 创建临时的Excel文件
            temp_id = str(uuid.uuid4())

            try:
                # 使用安全的临时目录创建方法
                temp_dir = self._ensure_temp_dir(temp_id)
                excel_path = os.path.join(temp_dir, f"{self.data_type}_preview.xlsx")

                # 转换为DataFrame
                df = pd.DataFrame(filtered_rows)

                # 将DataFrame保存为Excel
                df.to_excel(excel_path, index=False)
                logger.info(f"预览数据已保存为临时Excel文件: {excel_path}")

                # 保存临时信息
                temp_info_path = os.path.join(temp_dir, f"{temp_id}_info.json")
                with open(temp_info_path, "w", encoding="utf-8") as f:
                    json.dump(
                        {
                            "file_path": excel_path,
                            "data_type": self.data_type,
                            "import_type": "preview",
                        },
                        f,
                    )

                # 分析数据变化（启用Unicode清洗）
                self.processor = self.service_class()
                success, message, combined_data = self.processor.analyze_changes(
                    excel_path, enable_unicode_cleaning=True
                )
                logger.info(f"预览分析结果: success={success}, message={message}")

                if not success:
                    # 清理临时文件
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    return jsonify({"status": "error", "message": message}), 400

                # 解析预览信息
                stats = parse_preview_message(message)
                if not stats:
                    # 清理临时文件
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    return (
                        jsonify({"status": "error", "message": "解析预览信息失败"}),
                        500,
                    )

                # 获取预览数据
                preview_rows = df.head(10).to_dict("records")  # 获取前10行数据
                columns = df.columns.tolist()  # 获取列名列表

                # 合并统计信息和预览数据
                preview_data = {
                    **stats,
                    "preview_rows": preview_rows,
                    "columns": columns,
                }

                return jsonify(
                    {
                        "status": "success",
                        "message": "预览处理成功",
                        "preview": preview_data,
                        "temp_id": temp_id,
                    }
                )
            except Exception as e:
                logger.exception(f"预览分析时出错: {str(e)}")
                try:
                    # 尝试清理临时目录
                    temp_dir = self._ensure_temp_dir(temp_id)
                    shutil.rmtree(temp_dir, ignore_errors=True)
                except:
                    pass
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": f"预览分析时出错: {str(e)}",
                        }
                    ),
                    500,
                )
        except Exception as e:
            logger.exception(f"处理预览请求时出错: {str(e)}")
            return jsonify({"status": "error", "message": str(e)}), 500
