"""
数据导入处理器模块，提供通用数据导入功能
"""

import logging
import os
from typing import Any, ClassVar, Dict, List, Optional, Set, Tuple, Type

import re

import pandas as pd
from flask import current_app

from app.utils.unicode_cleaner import UnicodeCleaner

logger = logging.getLogger(__name__)


class DataImportProcessor:
    """数据导入处理器基类，提供通用数据导入和处理功能"""

    # 数据源到数据类型的映射
    DATA_SOURCE_TYPE_MAP: ClassVar[Dict[str, str]] = {
        "case": "服务请求",
        "faults": "故障报告",
        "r_and_i_record": "部件拆换记录",
    }

    # 基类中定义默认的必需列和最终列，子类可以覆盖
    REQUIRED_COLUMNS: ClassVar[List[str]] = ["问题描述"]
    FINAL_COLUMNS: ClassVar[List[str]] = ["问题描述", "数据类型"]

    _instances: ClassVar[Dict[Type["DataImportProcessor"], "DataImportProcessor"]] = {}

    def __new__(cls, file_path: Optional[str] = None) -> "DataImportProcessor":
        """单例模式创建实例。

        Args:
            file_path: 数据文件路径

        Returns:
            DataImportProcessor实例
        """
        if cls not in cls._instances:
            cls._instances[cls] = super().__new__(cls)
        return cls._instances[cls]

    def __init__(self, file_path: Optional[str] = None) -> None:
        """初始化数据导入处理器。

        Args:
            file_path: 数据文件路径
        """
        # 确保初始化代码只运行一次
        if not hasattr(self, "_initialized"):
            self.__initialize()
            self._initialized = True
        self.file_path = file_path
        self.unicode_cleaner = UnicodeCleaner()

    def __initialize(self) -> None:
        """私有初始化方法，设置数据路径和其他初始属性。"""
        # 从应用配置中获取数据路径
        try:
            # 尝试在当前应用上下文中获取配置
            if current_app:
                self.data_path = os.path.join(
                    current_app.config["DATA_CONFIG"]["data_dir"],
                    current_app.config["DATA_SOURCES"][self.data_source_key],
                )
            else:
                # 不在应用上下文中，使用默认路径
                app_dir = os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                )
                data_dir = os.path.join(os.path.dirname(app_dir), "data")
                self.data_path = os.path.join(
                    data_dir, "raw", f"{self.data_source_key}.parquet"
                )
        except Exception:
            # 如果不在Flask上下文中，使用默认路径
            app_dir = os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )
            data_dir = os.path.join(os.path.dirname(app_dir), "data")
            self.data_path = os.path.join(
                data_dir, "raw", f"{self.data_source_key}.parquet"
            )

        # 检查并创建数据目录
        os.makedirs(os.path.dirname(self.data_path), exist_ok=True)

        if not os.path.exists(self.data_path):
            logger.warning(f"数据文件不存在: {self.data_path}")

    def validate_headers(self, df: pd.DataFrame) -> bool:
        """验证数据表头是否符合要求。

        Args:
            df: 待验证的数据框

        Returns:
            验证通过返回True，否则抛出异常

        Raises:
            ValueError: 当缺少必需的列时
        """
        current_columns = set(df.columns)
        required_columns = set(self.REQUIRED_COLUMNS)
        missing_columns = required_columns - current_columns
        if missing_columns:
            raise ValueError(f"缺少必需的列: {missing_columns}")
        return True

    def clean_operator_names(
        self, df: pd.DataFrame, column: str = "运营人"
    ) -> pd.DataFrame:
        """清洗运营人名称的通用方法。

        Args:
            df: 待处理的数据框
            column: 运营人列名，默认为"运营人"

        Returns:
            清洗后的数据框
        """
        replace_rules = [
            (["天骄", "天骄航空", "天骄航空有限公司"], "天骄"),
            (
                [
                    "东航",
                    "东方航空",
                    "一二三航空",
                    "一二三航空有限公司（东方航空）",
                    "东航技术",
                    "中国东方航空有限公司",
                    "一二三航空有限公司（东航）",
                    "一二三航空有限公司",
                    "中国东方航空集团有限公司",
                ],
                "东航",
            ),
            (["江西航", "江西航空有限公司", "江西航空"], "江西航"),
            (
                [
                    "南航",
                    "南方航空",
                    "中国南方航空有限公司",
                    "中国南方航空股份有限公司",
                ],
                "南航",
            ),
            (["国航", "中国国航", "中国国际航空股份有限公司"], "国航"),
            (["成航", "成都航空", "成都航空有限公司"], "成航"),
            (["乌航", "乌鲁木齐航空"], "乌航"),
            (["华夏", "华夏航空", "华夏航空股份有限公司"], "华夏"),
            (["金鹏", "金鹏航空"], "金鹏"),
            (["圆通", "圆通货航", "圆通航空", "杭州圆通货运航空有限公司"], "圆通"),
            (["中飞通", "中飞通航", "中飞通用航空有限责任公司"], "中飞通"),
            (["中原龙浩", "中原龙浩航空"], "中原龙浩"),
            (["上飞公司维修中心"], "上飞公司维修中心"),
            (["GAMECO", "广州飞机维修工程有限公司（GAMECO）"], "GAMECO"),
            (
                [
                    "翎亚",
                    "翎亚航空 PT TransNusa Aviation Mandiri",
                    "TRANSNUSA AVIATION MANDIRI",
                    "TransNusa",
                ],
                "翎亚",
            ),
            (["中国商飞", "中国商用飞机有限责任公司"], "中国商飞"),
            (["AMECO", "北京飞机维修工程有限公司"], "AMECO"),
            (["山东太古", "山东太古飞机工程有限公司"], "山东太古"),
            (
                [
                    "STARCO",
                    "上海科技宇航有限公司 Shanghai Technologies Aerospace (STARCO)",
                ],
                "STARCO",
            ),
            (["中飞租", "中国飞机租赁集团控股有限公司"], "中飞租"),
        ]

        # 过滤掉只有单个元素的规则
        filtered_replace_rules = [rule for rule in replace_rules if len(rule[0]) > 1]

        # 进行替换操作
        df_copy = df.copy()
        for replacements, target in filtered_replace_rules:
            df_copy[column] = df_copy[column].replace(replacements, target)
        df_copy[column] = df_copy[column].fillna("无")

        return df_copy

    def clean_aircraft_type(
        self, df: pd.DataFrame, column: str = "机型"
    ) -> pd.DataFrame:
        """清洗机型数据的通用方法。

        Args:
            df: 待处理的数据框
            column: 机型列名，默认为"机型"

        Returns:
            清洗后的数据框
        """
        df_copy = df.copy()
        df_copy[column] = df_copy[column].fillna("无")
        df_copy[column] = df_copy[column].str.replace(r".*ARJ21.*", "ARJ21", regex=True)
        df_copy[column] = df_copy[column].str.replace(r".*C919.*", "C919", regex=True)
        return df_copy

    def convert_date(self, date_str: Any) -> pd.Timestamp:
        """
        转换日期格式的通用方法。
        增强了对特定格式和脏数据的处理能力。
        """
        if pd.isna(date_str):
            return pd.NaT

        # 确保输入是字符串并进行初步清理
        cleaned_str = self.unicode_cleaner.clean_text(str(date_str))

        # 优先使用正则表达式提取 YYYY/MM/DD 或 YYYY-MM-DD 格式
        match = re.match(r"(\d{4}[/-]\d{1,2}[/-]\d{1,2})", cleaned_str)
        if match:
            try:
                return pd.to_datetime(match.group(1))
            except ValueError:
                pass  # 如果正则提取的部分也无法解析，则继续尝试后续方法

        # 定义多种可能的日期时间格式
        formats = [
            "%Y-%m-%d",
            "%Y/%m/%d %H:%M:%S",
            "%Y/%m/%d %H:%M",
            "%Y/%m/%d %H %M",  # 支持 "YYYY/MM/DD HH MM" 格式
            "%Y/%m/%d",
        ]

        # 遍历格式列表进行尝试
        for fmt in formats:
            try:
                return pd.to_datetime(cleaned_str, format=fmt)
            except ValueError:
                continue

        # 最后尝试让pandas自动识别格式
        try:
            return pd.to_datetime(cleaned_str)
        except ValueError:
            logger.error(f"无法解析的日期格式: {date_str}")
            return pd.NaT

    def analyze_changes(self, enable_unicode_cleaning: bool = True) -> Tuple[bool, str]:
        """分析数据变化的通用方法。

        Args:
            enable_unicode_cleaning: 是否启用Unicode字符清洗

        Returns:
            (成功标志, 预览消息)
        """
        try:
            # 读取并清洗新数据
            new_data = pd.read_excel(self.file_path)

            # 清洗列名
            cleaned_columns = [self.unicode_cleaner.clean_text(col) for col in new_data.columns]
            new_data.columns = cleaned_columns
            logger.info(f"清洗后的列名: {new_data.columns.tolist()}")
            
            # Unicode字符清洗（可选）
            if enable_unicode_cleaning:
                logger.info("开始Unicode字符清洗...")
                pollution_analysis = self.unicode_cleaner.analyze_file_pollution(self.file_path)
                if pollution_analysis.get("needs_cleaning", False):
                    logger.info(f"检测到Unicode字符污染: {pollution_analysis}")
                    new_data = self.unicode_cleaner.clean_dataframe(new_data)
                    logger.info("Unicode字符清洗完成")
                else:
                    logger.info("未检测到Unicode字符污染，跳过清洗")
            
            self.validate_headers(new_data)
            cleaned_new_data = self.clean_data(new_data)

            # 只有在数据类型字段为空时才设置默认值
            if (
                "数据类型" not in cleaned_new_data.columns
                or cleaned_new_data["数据类型"].isna().all()
            ):
                data_type = self.DATA_SOURCE_TYPE_MAP.get(
                    self.data_source_key, self.data_source_key
                )
                cleaned_new_data["数据类型"] = data_type
                logger.info(f"设置默认数据类型为: {data_type}")
            else:
                logger.info("保留已设置的数据类型")

            # 读取现有数据
            original_count = 0
            if os.path.exists(self.data_path):
                try:
                    existing_data = pd.read_parquet(self.data_path)
                    original_count = len(existing_data)
                    logger.info(f"现有数据条数: {original_count}")
                except Exception as e:
                    logger.error(f"读取现有数据失败: {str(e)}")
                    existing_data = pd.DataFrame(columns=self.FINAL_COLUMNS)
            else:
                logger.info(f"数据文件不存在，将在保存时创建新文件: {self.data_path}")
                existing_data = pd.DataFrame(columns=self.FINAL_COLUMNS)

            uploaded_count = len(cleaned_new_data)
            logger.info(f"上传文件包含数据: {uploaded_count} 条")

            # --- 在合并前，只对新数据进行最终的标准化，确保空值处理一致 ---
            for col in self.FINAL_COLUMNS:
                # 统一处理新数据中对象/字符串列的空值
                if col in cleaned_new_data.columns and cleaned_new_data[col].dtype == 'object':
                    cleaned_new_data[col] = cleaned_new_data[col].fillna('')
            
            # 合并数据
            combined_data = pd.concat(
                [cleaned_new_data, existing_data], ignore_index=True
            )
            logger.info(f"合并后的数据量: {len(combined_data)} 条")

            # 按日期倒序排序并去重
            combined_data = combined_data.sort_values(self.date_column, ascending=False)
            logger.info(f"排序后的数据量: {len(combined_data)} 条")

            combined_data = combined_data.drop_duplicates(keep="first")
            logger.info(f"去重后的数据量: {len(combined_data)} 条")

            final_count = len(combined_data)

            # 计算实际新增的数据量
            actual_new_count = final_count - original_count
            logger.info(f"实际新增数据: {actual_new_count} 条")

            # 构建预览消息
            message = (
                f"数据变更预览：\n"
                f"原有数据：{original_count} 条\n"
                f"上传数据：{uploaded_count} 条\n"
                f"重复数据：{uploaded_count - actual_new_count} 条\n"
                f"实际新增：{actual_new_count} 条\n"
                f"变更后数据：{final_count} 条\n\n"
                f"是否确认更新数据？"
            )

            return True, message
        except Exception as e:
            logger.error(f"分析数据变化时出错: {str(e)}")
            return False, f"分析数据失败: {str(e)}"

    def save_changes(
        self, combined_data: pd.DataFrame, new_count: int
    ) -> Tuple[bool, str]:
        """保存数据变更的通用方法。

        Args:
            combined_data: 合并后的数据框
            new_count: 新增的数据条数

        Returns:
            (成功标志, 消息)
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.data_path), exist_ok=True)

            # 保存数据
            combined_data.to_parquet(self.data_path, index=False)
            logger.info(
                f"已保存 {len(combined_data)} 条数据到 {self.data_path}，其中新增 {new_count} 条"
            )

            return True, f"成功导入 {new_count} 条数据"
        except Exception as e:
            logger.error(f"保存数据时出错: {str(e)}")
            return False, f"保存数据失败: {str(e)}"

    @staticmethod
    def validate_columns(columns: List[str]) -> bool:
        """验证列名是否合法。

        Args:
            columns: 列名列表

        Returns:
            验证结果
        """
        # TODO: 实现具体的列名验证逻辑
        return len(columns) > 0

    def get_columns(self) -> List[str]:
        """获取数据源的列名列表。

        Returns:
            列名列表
        """
        if hasattr(self, "FINAL_COLUMNS"):
            return self.FINAL_COLUMNS
        else:
            # 尝试从数据文件中读取列名
            if os.path.exists(self.data_path):
                try:
                    df = pd.read_parquet(self.data_path)
                    return list(df.columns)
                except Exception:
                    return []
            return []

    @property
    def processor_name(self) -> str:
        """获取处理器名称。"""
        class_name = self.__class__.__name__
        return class_name

    @property
    def data_source_key(self) -> str:
        """获取数据源键名。"""
        raise NotImplementedError("子类必须实现data_source_key属性")

    @property
    def date_column(self) -> str:
        """获取日期列名。"""
        raise NotImplementedError("子类必须实现date_column属性")

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """清洗数据的通用方法，子类应该重写此方法。

        Args:
            df: 待清洗的数据框

        Returns:
            清洗后的数据框
        """
        raise NotImplementedError("子类必须实现clean_data方法")
