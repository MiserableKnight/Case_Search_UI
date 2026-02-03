"""
故障报告数据处理器模块，提供故障报告数据的导入和处理功能
"""

import logging
import os
import re
from typing import ClassVar

import pandas as pd

from .data_import_processor import DataImportProcessor

logger = logging.getLogger(__name__)


class FaultReportProcessor(DataImportProcessor):
    """故障报告数据处理器，处理故障报告的导入和转换"""

    # 必需的原始列
    REQUIRED_COLUMNS: ClassVar[list[str]] = [
        "运营人",
        "机型",
        "系列",
        "飞机序列号",
        "机号",
        "日期",
        "航班号",
        "故障报告类型",
        "故障ATA",
        "维修ATA",
        "故障确认",
        "确认人",
        "确认时间",
        "问题描述",
        "排故措施",
        "飞行阶段",
        "发生地",
        "是否ETOPS航班",
        "故障报告来源编码",
        "其他排故措施编码",
        "主要排故措施编码",
    ]

    # 最终需要保留的列
    FINAL_COLUMNS: ClassVar[list[str]] = [
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
    def processor_name(self) -> str:
        """获取处理器名称。

        Returns:
            处理器名称
        """
        return "故障报告处理器"

    @property
    def data_source_key(self) -> str:
        """获取数据源键名。

        Returns:
            数据源键名
        """
        return "faults"

    @property
    def date_column(self) -> str:
        """获取日期列名。

        Returns:
            日期列名
        """
        return "日期"

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """清洗故障报告数据。

        Args:
            df: 原始数据框

        Returns:
            清洗后的数据框

        Raises:
            ValueError: 当缺少必需的列时
        """
        # 复制数据框以避免修改原始数据
        cleaned_df = df.copy()

        # 验证表头
        self.validate_headers(cleaned_df)

        # 删除空列
        cleaned_df = cleaned_df.dropna(axis=1, how="all")

        # 设置数据类型为"故障报告"
        cleaned_df["数据类型"] = "故障报告"
        logger.info("设置数据类型为: 故障报告")

        # 清洗日期数据
        if "日期" in cleaned_df.columns:
            # 添加日志记录原始日期格式
            sample_dates = cleaned_df["日期"].head()
            logger.info(f"日期列样本数据: {sample_dates.tolist()}")

            cleaned_df["日期"] = cleaned_df["日期"].apply(self.convert_date)

            # 检查转换后的结果
            null_dates = cleaned_df["日期"].isna().sum()
            if null_dates > 0:
                logger.warning(f"有 {null_dates} 条日期数据转换失败")

            cleaned_df["日期"] = cleaned_df["日期"].dt.strftime("%Y-%m-%d")

        # 清洗机型数据
        cleaned_df = self.clean_aircraft_type(cleaned_df)

        # 清洗运营人数据
        cleaned_df = self.clean_operator_names(cleaned_df)

        # 标准化飞机序列号：统一为5位数字格式（添加前导零）
        if "飞机序列号" in cleaned_df.columns:
            # 先转换为字符串
            cleaned_df["飞机序列号"] = cleaned_df["飞机序列号"].astype(str)
            # 移除非数字字符
            cleaned_df["飞机序列号"] = cleaned_df["飞机序列号"].str.replace(r"\D", "", regex=True)
            # 填充为5位数字
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

    def validate_file_name(self, file_path: str | None) -> bool:
        """验证文件名是否符合要求。

        Args:
            file_path: 文件路径

        Returns:
            验证结果

        Raises:
            ValueError: 当文件名格式不正确时
        """
        if file_path is None:
            return False

        filename = os.path.basename(file_path)
        # 验证文件名格式：故障报告_YYYYMMDD
        # 注意：这里的YYYYMMDD是日期格式，例如20250312
        pattern = r"^故障报告_\d{8}.*\.xlsx$"
        if not re.match(pattern, filename):
            # 检查是否是临时文件名格式（UUID_原始文件名）
            uuid_pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}_(.*)$"
            uuid_match = re.match(uuid_pattern, filename)

            if uuid_match:
                # 从临时文件名中提取原始文件名
                original_filename = uuid_match.group(1)
                # 验证原始文件名是否符合要求
                if re.match(r"^\d{8}.*\.xlsx$", original_filename):
                    # 如果原始文件名只有日期部分，则添加"故障报告_"前缀
                    return True
                elif re.match(r"^故障报告_\d{8}.*\.xlsx$", original_filename):
                    return True

            raise ValueError(
                "文件名格式不正确，应为'故障报告_YYYYMMDD.xlsx'，"
                f"其中YYYYMMDD为日期格式（如20250312），但得到的是'{filename}'"
            )

        return True


def load_fault_report_data() -> bool:
    """加载故障报告数据，用于应用初始化时。

    Returns:
        加载成功返回True，否则返回False
    """
    try:
        # 此函数只作为占位符，实际操作由服务类完成
        return True
    except Exception as e:
        logger.error(f"加载故障报告数据时出错: {str(e)}")
        return False
