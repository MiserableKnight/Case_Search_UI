"""
Unicode字符清洗工具模块
提供文本清洗功能，用于处理Excel文件中的Unicode字符污染问题
"""

import re
import logging
from typing import Any, Union

import pandas as pd

logger = logging.getLogger(__name__)


class UnicodeCleaner:
    """Unicode字符清洗器"""
    
    def __init__(self):
        """初始化清洗器"""
        self.bidirectional_pattern = re.compile(
            r'[\u200e\u200f\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069\u061c]'
        )
        self.control_char_pattern = re.compile(
            r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f\ufffe\uffff]'
        )
        self.zero_width_pattern = re.compile(
            r'[\u200b\u200c\u200d\u2060\ufeff\u00ad\u180e]'
        )
    
    def clean_text(self, text: Any) -> str:
        """
        清洗文本中的Unicode字符污染
        
        Args:
            text: 输入文本（可以是任何类型）
            
        Returns:
            str: 清洗后的文本
        """
        # 检查是否为空值（包括pandas和numpy的各种空值类型）
        if text is None or pd.isna(text):
            return ""
        
        # 转换为字符串
        if not isinstance(text, str):
            text = str(text)
        
        # 移除双向文本控制字符
        cleaned = self.bidirectional_pattern.sub('', text)
        
        # 移除控制字符（保留制表符、换行符、回车符）
        cleaned = self.control_char_pattern.sub('', cleaned)
        
        # 移除零宽字符和其他不可见格式字符
        cleaned = self.zero_width_pattern.sub('', cleaned)
        
        # 移除首尾空格
        return cleaned.strip()
    
    def clean_dataframe(self, df, columns: list = None) -> 'pd.DataFrame':
        """
        清洗DataFrame中的文本数据
        
        Args:
            df: 输入的DataFrame
            columns: 需要清洗的列名列表，如果为None则清洗所有文本列
            
        Returns:
            pd.DataFrame: 清洗后的DataFrame
        """
        import pandas as pd
        
        if df is None or df.empty:
            return df
        
        df_copy = df.copy()
        
        # 确定需要清洗的列
        if columns is None:
            # 自动检测文本列
            columns = []
            for col in df_copy.columns:
                # 检查列的数据类型是否为object或string
                if df_copy[col].dtype == 'object':
                    columns.append(col)
        
        # 清洗指定的列
        for col in columns:
            if col in df_copy.columns:
                try:
                    df_copy[col] = df_copy[col].apply(self.clean_text)
                except Exception as e:
                    logger.warning(f"清洗列 {col} 时出错: {e}")
        
        return df_copy
    
    def clean_excel_file(self, input_path: str, output_path: str = None) -> str:
        """
        清洗Excel文件中的Unicode字符
        
        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径（可选）
            
        Returns:
            str: 输出文件路径
        """
        import pandas as pd
        from pathlib import Path
        
        try:
            # 设置默认输出路径
            if output_path is None:
                input_path_obj = Path(input_path)
                output_path = str(input_path_obj.with_name(f"{input_path_obj.stem}_cleaned{input_path_obj.suffix}"))
            
            logger.info(f"开始清洗Excel文件: {input_path}")
            
            # 读取Excel文件
            df = pd.read_excel(input_path)
            
            # 清洗数据
            cleaned_df = self.clean_dataframe(df)
            
            # 保存清洗后的文件
            cleaned_df.to_excel(output_path, index=False)
            
            logger.info(f"Excel文件清洗完成: {output_path}")
            logger.info(f"处理数据量: {len(cleaned_df)} 行, {len(cleaned_df.columns)} 列")
            
            return output_path
            
        except Exception as e:
            logger.error(f"清洗Excel文件时出错: {e}")
            raise
    
    def detect_unicode_pollution(self, text: str) -> dict:
        """
        检测文本中的Unicode字符污染
        
        Args:
            text: 待检测的文本
            
        Returns:
            dict: 检测结果
        """
        if not isinstance(text, str):
            return {"has_pollution": False, "pollution_types": []}
        
        pollution_types = []
        
        # 检测双向文本控制字符
        if self.bidirectional_pattern.search(text):
            pollution_types.append("bidirectional_control_chars")
        
        # 检测控制字符
        if self.control_char_pattern.search(text):
            pollution_types.append("control_chars")
        
        # 检测零宽字符
        if self.zero_width_pattern.search(text):
            pollution_types.append("zero_width_chars")
        
        return {
            "has_pollution": len(pollution_types) > 0,
            "pollution_types": pollution_types,
            "original_length": len(text),
            "cleaned_length": len(self.clean_text(text))
        }
    
    def analyze_file_pollution(self, file_path: str) -> dict:
        """
        分析文件中的Unicode字符污染情况
        
        Args:
            file_path: 文件路径
            
        Returns:
            dict: 分析结果
        """
        import pandas as pd
        
        try:
            df = pd.read_excel(file_path)
            
            total_cells = 0
            polluted_cells = 0
            pollution_details = {}
            
            for col in df.columns:
                if df[col].dtype == 'object':
                    for idx, value in df[col].items():
                        if pd.notna(value):
                            total_cells += 1
                            detection = self.detect_unicode_pollution(str(value))
                            if detection["has_pollution"]:
                                polluted_cells += 1
                                
                                # 记录污染类型
                                for ptype in detection["pollution_types"]:
                                    if ptype not in pollution_details:
                                        pollution_details[ptype] = 0
                                    pollution_details[ptype] += 1
            
            return {
                "total_cells": total_cells,
                "polluted_cells": polluted_cells,
                "pollution_rate": polluted_cells / total_cells if total_cells > 0 else 0,
                "pollution_details": pollution_details,
                "needs_cleaning": polluted_cells > 0
            }
            
        except Exception as e:
            logger.error(f"分析文件污染情况时出错: {e}")
            return {"error": str(e)}
