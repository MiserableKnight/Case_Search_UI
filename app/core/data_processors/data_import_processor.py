import logging
import os
from datetime import datetime
from pathlib import Path

import pandas as pd
from flask import current_app

logger = logging.getLogger(__name__)


class DataImportProcessor:
    _instances = {}

    def __new__(cls, file_path=None):
        if cls not in cls._instances:
            cls._instances[cls] = super().__new__(cls)
        return cls._instances[cls]

    def __init__(self, file_path=None):
        # 确保初始化代码只运行一次
        if not hasattr(self, "_initialized"):
            self.__initialize()
            self._initialized = True
        self.file_path = file_path

    def __initialize(self):
        """私有初始化方法"""
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

    def validate_headers(self, df):
        """验证数据表头是否符合要求"""
        current_columns = set(df.columns)
        required_columns = set(self.REQUIRED_COLUMNS)
        missing_columns = required_columns - current_columns
        if missing_columns:
            raise ValueError(f"缺少必需的列: {missing_columns}")
        return True

    def clean_operator_names(self, df, column="运营人"):
        """清洗运营人名称的通用方法"""
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

    def clean_aircraft_type(self, df, column="机型"):
        """清洗机型数据的通用方法"""
        df_copy = df.copy()
        df_copy[column] = df_copy[column].fillna("无")
        df_copy[column] = df_copy[column].str.replace(r".*ARJ21.*", "ARJ21", regex=True)
        df_copy[column] = df_copy[column].str.replace(r".*C919.*", "C919", regex=True)
        return df_copy

    def convert_date(self, date_str):
        """转换日期格式的通用方法"""
        if pd.isna(date_str):
            return pd.NaT

        formats = [
            "%Y-%m-%d",
            "%Y/%m/%d %H:%M:%S",
            "%Y/%m/%d %H:%M",
            "%Y/%m/%d %H %M",
            "%Y/%m/%d",
        ]

        for fmt in formats:
            try:
                return pd.to_datetime(date_str, format=fmt)
            except:
                continue

        try:
            # 最后尝试让pandas自动识别格式
            return pd.to_datetime(date_str)
        except:
            logger.error(f"无法解析的日期格式: {date_str}")
            return pd.NaT

    def analyze_changes(self):
        """分析数据变化的通用方法"""
        try:
            # 读取并清洗新数据
            new_data = pd.read_excel(self.file_path)
            self.validate_headers(new_data)
            cleaned_new_data = self.clean_data(new_data)
            logger.info("新数据清洗完成")

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

            # 合并数据
            combined_data = pd.concat(
                [cleaned_new_data, existing_data], ignore_index=True
            )

            # 按日期倒序排序并去重
            combined_data = combined_data.sort_values(self.date_column, ascending=False)
            combined_data = combined_data.drop_duplicates(keep="first")
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

            return True, message, combined_data

        except Exception as e:
            logger.error(f"分析数据时出错: {str(e)}")
            return False, f"数据分析失败: {str(e)}", None

    def save_changes(self, combined_data):
        """保存确认后的数据的通用方法"""
        try:
            if combined_data is None:
                raise ValueError("没有可保存的数据")

            # 再次确保数据已全字段去重
            combined_data = combined_data.drop_duplicates(keep="first")

            # 保存合并后的数据
            combined_data.to_parquet(self.data_path, index=False)
            logger.info("数据更新成功")
            return True, "数据更新成功！"
        except Exception as e:
            logger.error(f"保存数据时出错: {str(e)}")
            return False, f"数据保存失败: {str(e)}"

    @staticmethod
    def validate_columns(columns):
        """验证列名是否有效的通用方法"""
        if not columns or not isinstance(columns, list):
            return False
        required_fields = {"问题描述"}  # 基类中定义最基本的必需字段
        return all(field in columns for field in required_fields)

    def get_columns(self):
        """获取数据源的所有列的通用方法"""
        try:
            if os.path.exists(self.data_path):
                df = pd.read_parquet(self.data_path)
                return list(df.columns)
            else:
                return self.FINAL_COLUMNS
        except Exception as e:
            logger.error(f"获取列名时出错: {str(e)}")
            return self.FINAL_COLUMNS

    # 以下属性和方法需要在子类中实现
    @property
    def processor_name(self):
        """处理器名称"""
        raise NotImplementedError("子类必须实现processor_name属性")

    @property
    def data_source_key(self):
        """数据源键名"""
        raise NotImplementedError("子类必须实现data_source_key属性")

    @property
    def date_column(self):
        """日期列名"""
        raise NotImplementedError("子类必须实现date_column属性")

    def clean_data(self, df):
        """数据清洗方法"""
        raise NotImplementedError("子类必须实现clean_data方法")
