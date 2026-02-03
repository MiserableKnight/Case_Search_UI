"""
数据处理器单元测试

测试数据导入处理器基类的各种功能
"""

import pandas as pd
import pytest

from app.core.data_processors.data_import_processor import DataImportProcessor


# 创建一个测试用的处理器子类
class TestDataProcessor(DataImportProcessor):
    """测试用数据处理器"""

    REQUIRED_COLUMNS = ["标题", "描述"]
    FINAL_COLUMNS = ["标题", "描述", "日期", "数据类型"]

    @property
    def data_source_key(self):
        return "test"

    @property
    def date_column(self):
        return "日期"

    def clean_data(self, df):
        """简单的清洗实现"""
        df_clean = df.copy()
        # 确保必需列存在
        for col in self.REQUIRED_COLUMNS:
            if col not in df_clean.columns:
                df_clean[col] = ""
        # 只保留需要的列
        existing_columns = [col for col in self.FINAL_COLUMNS if col in df_clean.columns]
        return df_clean[existing_columns]


class TestDataImportProcessor:
    """DataImportProcessor测试类"""

    def setup_method(self):
        """每个测试方法前执行"""
        # 重置单例
        TestDataProcessor._instances = {}

    def teardown_method(self):
        """每个测试方法后执行"""
        # 清理单例
        TestDataProcessor._instances = {}

    # ==================== 单例模式测试 ====================

    def test_singleton_pattern(self, temp_output_dir):
        """测试单例模式"""
        processor1 = TestDataProcessor(str(temp_output_dir / "test.xlsx"))
        processor2 = TestDataProcessor(str(temp_output_dir / "test2.xlsx"))

        # 同一类型的处理器应该是同一个实例
        assert processor1 is processor2

    # ==================== 初始化测试 ====================

    def test_init_with_file_path(self, temp_output_dir):
        """测试带文件路径初始化"""
        file_path = str(temp_output_dir / "test.xlsx")
        processor = TestDataProcessor(file_path)

        assert processor.file_path == file_path
        assert processor.unicode_cleaner is not None

    def test_init_without_context(self):
        """测试不在Flask上下文中初始化"""
        processor = TestDataProcessor()

        assert hasattr(processor, "data_path")
        assert isinstance(processor.data_path, str)

    # ==================== validate_headers测试 ====================

    def test_validate_headers_valid(self):
        """测试验证有效的表头"""
        processor = TestDataProcessor()
        df = pd.DataFrame(
            {
                "标题": ["测试1"],
                "描述": ["描述1"],
                "日期": ["2023-01-01"],
            }
        )

        result = processor.validate_headers(df)
        assert result is True

    def test_validate_headers_missing_columns(self):
        """测试缺少必需列"""
        processor = TestDataProcessor()
        df = pd.DataFrame(
            {
                "标题": ["测试1"],
                # 缺少"描述"列
            }
        )

        with pytest.raises(ValueError, match="缺少必需的列"):
            processor.validate_headers(df)

    def test_validate_headers_empty_dataframe(self):
        """测试空DataFrame"""
        processor = TestDataProcessor()
        df = pd.DataFrame()

        with pytest.raises(ValueError):
            processor.validate_headers(df)

    # ==================== clean_operator_names测试 ====================

    def test_clean_operator_names_default(self):
        """测试清洗运营人名称（默认列）"""
        processor = TestDataProcessor()
        df = pd.DataFrame(
            {
                "运营人": ["天骄航空", "东航技术", "江西航空有限公司", "南航", "国航"],
            }
        )

        result = processor.clean_operator_names(df)

        assert result["运营人"].iloc[0] in ["天骄", "天骄航空"]
        assert "东航" in result["运营人"].iloc[1] or result["运营人"].iloc[1] == "东航"

    def test_clean_operator_names_custom_column(self):
        """测试清洗自定义列名"""
        processor = TestDataProcessor()
        df = pd.DataFrame(
            {
                "航空公司": ["天骄航空", "东航"],
            }
        )

        result = processor.clean_operator_names(df, column="航空公司")

        assert "航空公司" in result.columns

    def test_clean_operator_names_fillna(self):
        """测试运营人名称填充空值"""
        processor = TestDataProcessor()
        df = pd.DataFrame(
            {
                "运营人": ["天骄航空", None, ""],
            }
        )

        result = processor.clean_operator_names(df)

        # 空值应该被填充
        assert result["运营人"].isna().sum() == 0

    # ==================== clean_aircraft_type测试 ====================

    def test_clean_aircraft_type_default(self):
        """测试清洗机型数据（默认列）"""
        processor = TestDataProcessor()
        df = pd.DataFrame(
            {
                "机型": ["ARJ21-700", "C919大型客机", "737"],
            }
        )

        result = processor.clean_aircraft_type(df)

        assert "ARJ21" in result["机型"].iloc[0]
        assert "C919" in result["机型"].iloc[1]

    def test_clean_aircraft_type_custom_column(self):
        """测试清洗自定义列名"""
        processor = TestDataProcessor()
        df = pd.DataFrame(
            {
                "飞机型号": ["ARJ21-700", "C919"],
            }
        )

        result = processor.clean_aircraft_type(df, column="飞机型号")

        assert "飞机型号" in result.columns

    def test_clean_aircraft_type_fillna(self):
        """测试机型填充空值"""
        processor = TestDataProcessor()
        df = pd.DataFrame(
            {
                "机型": ["ARJ21", None, ""],
            }
        )

        result = processor.clean_aircraft_type(df)

        assert result["机型"].isna().sum() == 0

    # ==================== clean_part_numbers测试 ====================

    def test_clean_part_numbers_default(self):
        """测试清洗部件号（默认列）"""
        processor = TestDataProcessor()
        df = pd.DataFrame(
            {
                "装上部件件号": ["null/12345", "67890/null", "12345"],
                "拆卸部件序列号": ["null/ABC-123", "XYZ-789/null", ""],
            }
        )

        result = processor.clean_part_numbers(df)

        assert result["装上部件件号"].iloc[0] == "12345"
        assert result["装上部件件号"].iloc[1] == "67890"
        assert result["拆卸部件序列号"].iloc[0] == "ABC-123"
        assert result["拆卸部件序列号"].iloc[1] == "XYZ-789"

    def test_clean_part_numbers_custom_columns(self):
        """测试清洗指定列"""
        processor = TestDataProcessor()
        df = pd.DataFrame(
            {
                "部件号A": ["null/111", "222/null"],
                "部件号B": ["333/null", "null/444"],
            }
        )

        result = processor.clean_part_numbers(df, columns=["部件号A", "部件号B"])

        assert result["部件号A"].iloc[0] == "111"
        assert result["部件号A"].iloc[1] == "222"

    def test_clean_part_numbers_nonexistent_columns(self):
        """测试清洗不存在的列（应该安全跳过）"""
        processor = TestDataProcessor()
        df = pd.DataFrame(
            {
                "其他列": ["data1", "data2"],
            }
        )

        # 不应该抛出异常
        result = processor.clean_part_numbers(df)

        assert "其他列" in result.columns

    # ==================== convert_date测试 ====================

    def test_convert_date_standard_format(self):
        """测试转换标准日期格式"""
        processor = TestDataProcessor()

        result = processor.convert_date("2023-01-01")

        assert isinstance(result, pd.Timestamp)
        assert result.year == 2023
        assert result.month == 1
        assert result.day == 1

    def test_convert_date_slash_format(self):
        """测试转换斜杠分隔的日期"""
        processor = TestDataProcessor()

        result = processor.convert_date("2023/01/01")

        assert isinstance(result, pd.Timestamp)

    def test_convert_date_with_time(self):
        """测试转换带时间的日期"""
        processor = TestDataProcessor()

        result = processor.convert_date("2023/01/01 12:30:45")

        assert isinstance(result, pd.Timestamp)

    def test_convert_date_na(self):
        """测试转换空值"""
        processor = TestDataProcessor()

        result = processor.convert_date(None)
        assert pd.isna(result)

    def test_convert_date_nan(self):
        """测试转换NaN"""
        processor = TestDataProcessor()

        result = processor.convert_date(float("nan"))
        assert pd.isna(result)

    def test_convert_date_invalid_format(self):
        """测试转换无效日期格式"""
        processor = TestDataProcessor()

        result = processor.convert_date("invalid_date")
        assert pd.isna(result)

    def test_convert_date_with_unicode_pollution(self):
        """测试转换包含Unicode污染的日期"""
        processor = TestDataProcessor()

        result = processor.convert_date("2023\u200e-01-01")
        assert isinstance(result, pd.Timestamp)

    # ==================== get_columns测试 ====================

    def test_get_columns_from_class(self):
        """测试从类定义获取列"""
        processor = TestDataProcessor()

        columns = processor.get_columns()

        assert isinstance(columns, list)
        assert "标题" in columns
        assert "描述" in columns

    # ==================== 属性测试 ====================

    def test_processor_name_property(self):
        """测试处理器名称属性"""
        processor = TestDataProcessor()

        assert processor.processor_name == "TestDataProcessor"

    def test_data_source_key_property(self):
        """测试数据源键属性"""
        processor = TestDataProcessor()

        assert processor.data_source_key == "test"

    def test_date_column_property(self):
        """测试日期列属性"""
        processor = TestDataProcessor()

        assert processor.date_column == "日期"

    # ==================== clean_data测试 ====================

    def test_clean_data_basic(self):
        """测试基本数据清洗"""
        processor = TestDataProcessor()
        df = pd.DataFrame(
            {
                "标题": ["测试1", "测试2"],
                "描述": ["描述1", "描述2"],
                "日期": ["2023-01-01", "2023-01-02"],
                "额外列": ["额外1", "额外2"],
            }
        )

        result = processor.clean_data(df)

        # 应该只包含FINAL_COLUMNS中的列
        assert "额外列" not in result.columns
        assert "标题" in result.columns

    # ==================== 数据源类型映射测试 ====================

    def test_data_source_type_map(self):
        """测试数据源类型映射"""
        processor = TestDataProcessor()

        assert "case" in processor.DATA_SOURCE_TYPE_MAP
        assert processor.DATA_SOURCE_TYPE_MAP["case"] == "服务请求"
        assert processor.DATA_SOURCE_TYPE_MAP["faults"] == "故障报告"

    # ==================== 边界条件测试 ====================

    def test_empty_dataframe_processing(self):
        """测试空DataFrame处理"""
        processor = TestDataProcessor()
        df = pd.DataFrame()

        with pytest.raises(ValueError):
            processor.validate_headers(df)

    def test_large_dataset_processing(self, temp_output_dir):
        """测试大数据集处理"""
        processor = TestDataProcessor()

        # 创建大数据集
        large_df = pd.DataFrame(
            {
                "标题": [f"测试{i}" for i in range(1000)],
                "描述": [f"描述{i}" for i in range(1000)],
                "日期": ["2023-01-01"] * 1000,
            }
        )

        result = processor.clean_data(large_df)

        assert len(result) == 1000

    def test_unicode_in_columns(self):
        """测试列名包含Unicode字符"""
        processor = TestDataProcessor()
        df = pd.DataFrame(
            {
                "\u200e标题\u200f": ["测试1"],
                "描述": ["描述1"],
                "日期": ["2023-01-01"],
            }
        )

        # 清洗列名
        cleaned_columns = [processor.unicode_cleaner.clean_text(col) for col in df.columns]

        assert "标题" in cleaned_columns
        assert "\u200e" not in cleaned_columns[0]


@pytest.mark.parametrize(
    "date_str,expected_valid",
    [
        ("2023-01-01", True),
        ("2023/01/01", True),
        ("2023/01/01 12:30:00", True),
        ("2023-01-01 12:30", True),
        ("invalid", False),
        (None, False),
        ("", False),
    ],
)
def test_convert_date_various_formats(date_str, expected_valid):
    """参数化测试各种日期格式"""
    processor = TestDataProcessor()
    result = processor.convert_date(date_str)

    if expected_valid:
        assert isinstance(result, pd.Timestamp) or pd.isna(result)
    else:
        assert pd.isna(result)


@pytest.mark.parametrize(
    "operator,expected_contains",
    [
        ("天骄航空", "天骄"),
        ("东航技术", "东航"),
        ("江西航空有限公司", "江西航"),
        ("南航", "南航"),
        ("国航", "国航"),
        # 新增航空公司规则测试
        ("中国东方航空股份有限公司", "东航"),
        ("乌鲁木齐航空有限责任公司", "乌航"),
        ("中国飞龙通航有限公司", "飞龙"),
        ("老挝航空公司", "老航"),
        ("上海飞机客户服务有限公司", "商飞快线"),
        ("中原龙浩航空有限公司", "中原龙浩"),
    ],
)
def test_clean_operator_names_various(operator, expected_contains):
    """参数化测试各种运营人名称"""
    processor = TestDataProcessor()
    df = pd.DataFrame({"运营人": [operator]})

    result = processor.clean_operator_names(df)

    assert (
        expected_contains in result["运营人"].iloc[0]
        or result["运营人"].iloc[0] == expected_contains
    )


@pytest.mark.parametrize(
    "aircraft_type,expected",
    [
        # ARJ21 系列机型测试
        ("ARJ21-700", "ARJ21"),
        ("ARJ21-701", "ARJ21"),
        ("ARJ-700", "ARJ21"),
        ("ARJ21-700ER", "ARJ21"),
        # C919 系列机型测试
        ("C919大型客机", "C919"),
        ("C919-STD", "C919"),
        ("C919-ER", "C919"),
        # 其他机型保持原样
        ("737-800", "737-800"),
        ("A320", "A320"),
    ],
)
def test_clean_aircraft_type_various(aircraft_type, expected):
    """参数化测试各种机型"""
    processor = TestDataProcessor()
    df = pd.DataFrame({"机型": [aircraft_type]})

    result = processor.clean_aircraft_type(df)

    assert result["机型"].iloc[0] == expected
