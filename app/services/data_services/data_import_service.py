"""
数据导入服务基类，为所有数据导入处理服务提供通用功能
"""

import os
import re
from typing import Any, Dict, List, Optional, Tuple, Type, Union, cast

import pandas as pd


class DataImportService:
    """数据导入服务基类，包含所有数据导入处理服务的通用方法"""

    def __init__(
        self, processor_class: Type[Any], config: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        初始化数据导入服务

        Args:
            processor_class: 处理器类
            config: 配置信息，默认为None，使用默认配置
        """
        self.processor = processor_class(config)

    def analyze_changes(
        self, temp_path: str, enable_unicode_cleaning: bool = True
    ) -> Tuple[bool, str, Optional[pd.DataFrame]]:
        """
        分析数据变化

        Args:
            temp_path: 临时文件路径
            enable_unicode_cleaning: 是否启用Unicode字符清洗

        Returns:
            (success, message, combined_data): 分析结果
        """
        temp_processor = self.processor.__class__(temp_path)
        success, message = temp_processor.analyze_changes(enable_unicode_cleaning=enable_unicode_cleaning)

        # 如果分析成功，获取合并后的数据
        combined_data = None
        if success:
            try:
                # 尝试加载原始数据和上传数据来创建合并数据
                # 这里需要访问处理器内部细节，不是很理想的做法
                new_data = pd.read_excel(temp_path)
                
                # 清洗列名，确保与处理器中的逻辑一致
                cleaned_columns = [temp_processor.unicode_cleaner.clean_text(col) for col in new_data.columns]
                new_data.columns = cleaned_columns

                # 补上缺失的数据内容清洗步骤
                new_data = temp_processor.unicode_cleaner.clean_dataframe(new_data)
                
                new_data = temp_processor.clean_data(new_data)

                # 获取现有数据
                if os.path.exists(temp_processor.data_path):
                    existing_data = pd.read_parquet(temp_processor.data_path)
                else:
                    existing_data = pd.DataFrame(columns=temp_processor.FINAL_COLUMNS)

                # 合并数据
                combined_data = pd.concat([new_data, existing_data], ignore_index=True)

                # 排序和去重
                if hasattr(temp_processor, "date_column"):
                    combined_data = combined_data.sort_values(
                        temp_processor.date_column, ascending=False
                    )
                combined_data = combined_data.drop_duplicates(keep="first")
            except Exception as e:
                # 如果处理过程中出错，返回None
                combined_data = None

        return success, message, combined_data

    def save_changes(self, combined_data: pd.DataFrame) -> Tuple[bool, str]:
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
        columns = self.processor.get_columns()
        return cast(List[str], columns)

    def confirm_import(self, file_path: str) -> Tuple[bool, str]:
        """
        确认导入数据

        Args:
            file_path: Excel文件路径

        Returns:
            (success, message): 导入结果
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                return False, "导入文件不存在"

            # 分析变化
            success, message, combined_data = self.analyze_changes(file_path)
            if not success or combined_data is None:
                return False, message

            # 从预览消息中提取新增数量
            new_count_match = re.search(r"实际新增：(\d+)\s*条", message)
            new_count = int(new_count_match.group(1)) if new_count_match else 0

            # 保存变化
            return self.processor.save_changes(combined_data, new_count)

        except Exception as e:
            return False, f"导入失败: {str(e)}"
