"""
数据导入服务基类，为所有数据导入处理服务提供通用功能
"""

import json
import os
from typing import Any, Dict, List, Optional, Tuple

from app.utils.file_handlers import UPLOAD_FOLDER


class DataImportService:
    """数据导入服务基类，包含所有数据导入处理服务的通用方法"""

    def __init__(self, processor_class, config=None):
        """
        初始化数据导入服务

        Args:
            processor_class: 处理器类
            config: 配置信息，默认为None，使用默认配置
        """
        self.processor = processor_class(config)

    def analyze_changes(self, temp_path: str) -> Tuple[bool, str, Any]:
        """
        分析数据变化

        Args:
            temp_path: 临时文件路径

        Returns:
            (success, message, combined_data): 分析结果
        """
        temp_processor = self.processor.__class__(temp_path)
        return temp_processor.analyze_changes()

    def save_changes(self, combined_data: Any) -> Tuple[bool, str]:
        """
        保存数据变化

        Args:
            combined_data: 合并后的数据

        Returns:
            (success, message): 保存结果
        """
        return self.processor.save_changes(combined_data)

    def get_columns(self) -> List[str]:
        """
        获取数据的列信息

        Returns:
            列信息列表
        """
        return self.processor.get_columns()

    def confirm_import(self, temp_id: str) -> Tuple[bool, str]:
        """
        确认导入数据

        Args:
            temp_id: 临时文件ID

        Returns:
            (success, message): 导入结果
        """
        try:
            # 读取临时文件信息
            info_path = os.path.join(UPLOAD_FOLDER, f"{temp_id}_info.json")
            if not os.path.exists(info_path):
                return False, "临时文件信息不存在"

            with open(info_path, "r", encoding="utf-8") as f:
                temp_info = json.load(f)

            # 获取文件路径
            temp_path = temp_info.get("file_path")
            if not temp_path or not os.path.exists(temp_path):
                return False, "临时文件不存在"

            # 分析变化
            success, message, combined_data = self.analyze_changes(temp_path)
            if not success:
                return False, message

            # 保存变化
            return self.save_changes(combined_data)

        except Exception as e:
            return False, f"导入失败: {str(e)}"
