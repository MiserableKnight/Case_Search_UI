import logging
from pathlib import Path

import pandas as pd

from .data_import_processor import DataImportProcessor

logger = logging.getLogger(__name__)


class RAndIRecordProcessor(DataImportProcessor):
    # 原始数据必需的列
    REQUIRED_COLUMNS = [
        "运营人",
        "机型",
        "系列",
        "飞机序列号",
        "机号",
        "拆换日期",
        "ATA",
        "拆卸部件件号",
        "拆卸部件序列号",
        "拆换类型",
        "拆换原因",
        "装上部件件号",
        "装上部件序列号",
        "本次使用小时",
        "本次使用循环",
        "本次使用天数",
        "累积使用小时",
        "累积使用循环",
        "累积使用天数",
        "拆卸部件处理措施",
    ]

    # 最终需要保留的列
    FINAL_COLUMNS = [
        "日期",
        "维修ATA",
        "问题描述",
        "排故措施",
        "运营人",
        "机型",
        "飞机序列号",
        "机号",
        "数据类型",
        "拆卸部件件号",
        "拆卸部件序列号",
        "装上部件件号",
        "装上部件序列号",
    ]

    @property
    def processor_name(self):
        return "部件拆换记录处理器"

    @property
    def data_source_key(self):
        # 虽然数据类型是"部件拆换记录"，但实际存储在faults.parquet中
        return "faults"

    @property
    def date_column(self):
        return "日期"

    def clean_data(self, df):
        """清洗数据"""
        # 复制数据框以避免修改原始数据
        cleaned_df = df.copy()

        # 验证表头
        self.validate_headers(cleaned_df)

        # 删除空列
        cleaned_df = cleaned_df.dropna(axis=1, how="all")

        # 设置数据类型为"部件拆换记录"
        cleaned_df["数据类型"] = "部件拆换记录"
        logger.info("设置数据类型为: 部件拆换记录")

        # 处理日期列
        if "拆换日期" in cleaned_df.columns:
            logger.info(f"日期列样本数据: {cleaned_df['拆换日期'].head().tolist()}")
            cleaned_df["日期"] = cleaned_df["拆换日期"].apply(self.convert_date)
            null_dates = cleaned_df["日期"].isna().sum()
            if null_dates > 0:
                logger.warning(f"有 {null_dates} 条日期数据转换失败")
            cleaned_df["日期"] = cleaned_df["日期"].dt.strftime("%Y-%m-%d")

        # 重命名列
        if "ATA" in cleaned_df.columns:
            cleaned_df["维修ATA"] = cleaned_df["ATA"]
        if "拆换原因" in cleaned_df.columns:
            cleaned_df["问题描述"] = cleaned_df["拆换原因"]
        if "拆卸部件处理措施" in cleaned_df.columns:
            cleaned_df["排故措施"] = cleaned_df["拆卸部件处理措施"]

        # 清洗机型数据
        cleaned_df = self.clean_aircraft_type(cleaned_df)

        # 清洗运营人数据
        cleaned_df = self.clean_operator_names(cleaned_df)

        # 标准化飞机序列号：统一为5位数字格式（添加前导零）
        if "飞机序列号" in cleaned_df.columns:
            cleaned_df["飞机序列号"] = cleaned_df["飞机序列号"].astype(str)
            cleaned_df["飞机序列号"] = cleaned_df["飞机序列号"].str.replace(r"\D", "", regex=True)
            cleaned_df["飞机序列号"] = cleaned_df["飞机序列号"].str.zfill(5)
            logger.info("飞机序列号已标准化为5位数字格式")

        # 标准化维修ATA：确保为字符串类型
        if "维修ATA" in cleaned_df.columns:
            cleaned_df["维修ATA"] = cleaned_df["维修ATA"].astype(str)
            logger.info("维修ATA已转换为字符串类型")

        # 确保拆卸和装上部件列存在（在清洗空值之前添加，确保它们也能被清洗）
        part_columns = [
            "拆卸部件件号",
            "拆卸部件序列号",
            "装上部件件号",
            "装上部件序列号",
        ]
        for col in part_columns:
            if col not in cleaned_df.columns:
                cleaned_df[col] = None

        # 清洗所有文本列中的空值变体（包括 null/, /null, nan, None 等）
        # 注意：必须在添加部件号列之后调用，这样才能将 None 转换为 "无"
        cleaned_df = self.clean_null_values(cleaned_df)

        # 只保留需要的列
        try:
            final_df = cleaned_df[self.FINAL_COLUMNS]
        except KeyError:
            missing_cols = set(self.FINAL_COLUMNS) - set(cleaned_df.columns)
            logger.error(f"缺少必需的列: {missing_cols}")
            raise ValueError(f"缺少必需的列: {missing_cols}")

        return final_df


def load_faults_data():
    """加载故障数据"""
    data_path = Path(__file__).parent.parent.parent.parent / "data/raw/faults.parquet"
    return pd.read_parquet(data_path)


def load_r_and_i_data():
    """加载部件拆换记录数据"""
    # 此函数只作为占位符，实际操作由服务类完成
    return True
