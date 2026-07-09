"""运营人名称清洗的纯函数实现。

把清洗逻辑集中到此处，供两处调用方共用，避免逻辑重复与漂移：
- 数据导入处理器 ``DataImportProcessor.clean_operator_names``（导入时清洗新数据）
- 一次性历史数据清洗脚本 ``scripts/clean_operator_data.py``（回填已落库的脏数据）

本模块不依赖 Flask / 处理器类，可作为命令行工具直接调用。
"""

from __future__ import annotations

import pandas as pd

from app.config.data_cleaning_config import AIRLINE_REPLACE_RULES, NULL_VALUE_REPLACEMENTS

OPERATOR_COLUMN = "运营人"


def clean_operator_series(
    series: pd.Series,
    *,
    airline_rules: list[tuple[list[str], str]] | None = None,
    null_replacements: list[str] | None = None,
) -> pd.Series:
    """对「运营人」Series 应用标准化清洗。

    处理流程：
    1. 去除前后空格（纯空格 → 空字符串）
    2. 各种空值变体统一为「无」
    3. 应用航空公司名称标准化规则
    4. 剩余 NaN 填充为「无」

    Args:
        series: 待清洗的运营人 Series
        airline_rules: 航空公司替换规则，默认取 ``AIRLINE_REPLACE_RULES``
        null_replacements: 空值变体列表，默认取 ``NULL_VALUE_REPLACEMENTS``

    Returns:
        清洗后的 Series（新对象，不修改输入）
    """
    if airline_rules is None:
        airline_rules = AIRLINE_REPLACE_RULES
    if null_replacements is None:
        null_replacements = NULL_VALUE_REPLACEMENTS

    cleaned = series.copy()
    # 第零步：去除前后空格（纯空格变为空字符串，后续会被替换为「无」）
    cleaned = cleaned.str.strip()
    # 第一步：将各种空值变体替换为「无」
    cleaned = cleaned.replace(null_replacements, "无")
    # 第二步：应用航空公司名称标准化规则
    for replacements, target in airline_rules:
        cleaned = cleaned.replace(replacements, target)
    # 第三步：将剩余的 NaN 填充为「无」
    cleaned = cleaned.fillna("无")
    return cleaned
