import logging
import os
from datetime import datetime
from pathlib import Path

import pandas as pd
from flask import current_app

from .data_import_processor import DataImportProcessor

logger = logging.getLogger(__name__)


class EngineeringProcessor(DataImportProcessor):
    # 原始数据必需的列
    REQUIRED_COLUMNS = [
        "文件名称",
        "MSN有效性",
        "分类",
        "原因和说明",
        "机型",
        "数据类型",
        "原文文本",
        "发布时间",
    ]

    # 最终需要保留的列
    FINAL_COLUMNS = [
        "文件名称",
        "MSN有效性",
        "分类",
        "原因和说明",
        "机型",
        "数据类型",
        "原文文本",
        "发布时间",
    ]

    @property
    def processor_name(self):
        return "工程文件处理器"

    @property
    def data_source_key(self):
        return "engineering"

    @property
    def date_column(self):
        return "发布时间"

    def clean_data(self, df):
        """清洗数据"""
        # 复制数据框以避免修改原始数据
        cleaned_df = df.copy()

        # 清洗日期数据
        cleaned_df["发布时间"] = cleaned_df["发布时间"].apply(self.convert_date)
        cleaned_df["发布时间"] = cleaned_df["发布时间"].dt.strftime("%Y-%m-%d")

        # 确保MSN有效性列为字符串类型
        if "MSN有效性" in cleaned_df.columns:
            cleaned_df["MSN有效性"] = cleaned_df["MSN有效性"].astype(str)

        # 清洗机型数据
        if "机型" not in cleaned_df.columns:
            logger.warning("导入数据中缺少'机型'列，将保留为空")
            cleaned_df["机型"] = ""  # 不再默认为ARJ21
        else:
            cleaned_df = self.clean_aircraft_type(cleaned_df)

        # 处理数据类型字段
        if "数据类型" not in cleaned_df.columns:
            logger.warning("导入数据中缺少'数据类型'列，将保留为空")
            cleaned_df["数据类型"] = ""  # 不再硬编码为"工程文件"

        # 只保留需要的列
        for col in self.FINAL_COLUMNS:
            if col not in cleaned_df.columns:
                cleaned_df[col] = ""  # 添加缺失的列

        final_df = cleaned_df[self.FINAL_COLUMNS]

        return final_df


def load_engineering_data():
    """加载工程文件数据"""
    logger.info("工程文件数据加载成功")
    return True
