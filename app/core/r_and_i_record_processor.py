import pandas as pd
import os
import logging
from datetime import datetime
from flask import current_app
from pathlib import Path
from .base_processor import BaseDataProcessor

logger = logging.getLogger(__name__)

class RAndIRecordProcessor(BaseDataProcessor):
    # 原始数据必需的列
    REQUIRED_COLUMNS = ['运营人', '机型', '系列', '飞机序列号', '机号', '拆换日期', 'ATA', '拆卸部件件号', 
                       '拆卸部件序列号', '拆换类型', '拆换原因', '装上部件件号', '装上部件序列号', 
                       '本次使用小时', '本次使用循环', '本次使用天数', '累积使用小时', '累积使用循环', 
                       '累积使用天数', '拆卸部件处理措施']
    
    # 最终需要保留的列
    FINAL_COLUMNS = ['日期', '维修ATA', '问题描述', '排故措施', '运营人', '机型', '飞机序列号', '机号',
                     '数据类型', '拆卸部件件号', '拆卸部件序列号', '装上部件件号', '装上部件序列号']

    @property
    def processor_name(self):
        return "部件拆换记录处理器"

    @property
    def data_source_key(self):
        return "faults"

    @property
    def date_column(self):
        return "日期"

    def clean_data(self, df):
        """清洗数据"""
        # 复制数据框以避免修改原始数据
        cleaned_df = df.copy()
        
        # 处理日期列
        cleaned_df['日期'] = cleaned_df['拆换日期'].apply(self.convert_date)
        cleaned_df['日期'] = cleaned_df['日期'].dt.strftime('%Y-%m-%d')
        
        # 重命名列
        cleaned_df['维修ATA'] = cleaned_df['ATA']
        cleaned_df['问题描述'] = cleaned_df['拆换原因']
        cleaned_df['排故措施'] = cleaned_df['拆卸部件处理措施']
        
        # 清洗机型数据
        cleaned_df = self.clean_aircraft_type(cleaned_df)

        # 清洗运营人数据
        cleaned_df = self.clean_operator_names(cleaned_df)

        # 添加数据类型标记
        cleaned_df['数据类型'] = '部件拆换记录'

        # 只保留需要的列
        final_df = cleaned_df[self.FINAL_COLUMNS]
        
        return final_df

def load_faults_data():
    """加载故障数据"""
    data_path = Path(__file__).parent.parent.parent.parent / 'data/raw/faults.parquet'
    return pd.read_parquet(data_path)

def load_r_and_i_data():
    """加载部件拆换记录数据"""
    data_path = Path(__file__).parent.parent.parent.parent / 'data/raw/faults.parquet'
    return pd.read_parquet(data_path)