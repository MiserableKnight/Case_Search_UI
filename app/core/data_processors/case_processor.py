import logging
from pathlib import Path

import pandas as pd

from .data_import_processor import DataImportProcessor

logger = logging.getLogger(__name__)


class CaseProcessor(DataImportProcessor):
    # 原始数据必需的列
    REQUIRED_COLUMNS = [
        "类型",
        "标题",
        "状态",
        "技术请求编号",
        "服务请求单编号",
        "支持单编号",
        "版本号",
        "优先级",
        "受理渠道",
        "申请人",
        "申请时间",
        "初始要求答复日期",
        "协商答复日期",
        "SR变更人",
        "变更原因",
        "实际答复时间",
        "客户名称",
        "TR联系人",
        "联系人电话",
        "联系人邮箱",
        "运营人",
        "mro",
        "机型",
        "飞机序列号/注册号",
        "飞机总小时数",
        "飞机总循环数",
        "故障发生日期",
        "故障发生地点",
        "ATA",
        "CAS信息",
        "CMS信息",
        "维修级别",
        "问题描述",
        "客户期望",
        "答复详情",
        "答复用时(小时)",
        "答复是否超时",
        "SR创建人",
        "创建时间",
        "答复者",
        "答复时间",
        "审批者",
        "审批时间",
        "备注信息",
    ]

    # 最终需要保留的列
    FINAL_COLUMNS = [
        "故障发生日期",
        "申请时间",
        "标题",
        "版本号",
        "问题描述",
        "答复详情",
        "客户期望",
        "ATA",
        "机号/MSN",
        "运营人",
        "服务请求单编号",
        "机型",
        "数据类型",
    ]

    @property
    def processor_name(self):
        return "服务请求处理器"

    @property
    def data_source_key(self):
        return "case"

    @property
    def date_column(self):
        return "申请时间"

    def clean_data(self, df):
        """清洗数据"""
        # 复制数据框以避免修改原始数据
        cleaned_df = df.copy()

        # 清洗日期数据
        date_columns = ["故障发生日期", "申请时间"]
        for col in date_columns:
            cleaned_df[col] = cleaned_df[col].apply(self.convert_date)
            cleaned_df[col] = cleaned_df[col].dt.strftime("%Y-%m-%d")

        # 清洗机型数据
        cleaned_df = self.clean_aircraft_type(cleaned_df)

        # 清洗运营人数据
        cleaned_df = self.clean_operator_names(cleaned_df)

        # 清洗机号数据
        cleaned_df["机号/MSN"] = cleaned_df["飞机序列号/注册号"]  # 重命名列
        cleaned_df["机号/MSN"] = cleaned_df["机号/MSN"].str.replace("all", "ALL", case=True)
        cleaned_df["机号/MSN"] = cleaned_df["机号/MSN"].str.replace("./ALL", "ALL/ALL", case=True)

        # 清洗ATA数据
        cleaned_df["ATA"] = cleaned_df["ATA"].astype(str)

        # 处理数据类型字段
        if "数据类型" not in cleaned_df.columns:
            logger.info("导入数据中缺少'数据类型'列，将设置为默认值'服务请求'")
            cleaned_df["数据类型"] = self.DATA_SOURCE_TYPE_MAP.get(self.data_source_key, "服务请求")

        # 删除答复详情为"无"的记录
        cleaned_df = cleaned_df[cleaned_df["答复详情"] != "无"]

        # 只保留需要的列
        final_df = cleaned_df[self.FINAL_COLUMNS]

        return final_df


def load_case_data():
    """加载原始案例数据"""
    data_path = Path(__file__).parent.parent.parent.parent / "data/raw/case.parquet"
    return pd.read_parquet(data_path)
