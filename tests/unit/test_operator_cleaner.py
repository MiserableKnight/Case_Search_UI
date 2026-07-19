"""app.utils.operator_cleaner.clean_operator_series 的单元测试。

该纯函数是运营人清洗的唯一逻辑来源，被 DataImportProcessor.clean_operator_names
（导入流程）和 scripts/clean_operator_data.py（历史数据回填）共用。
"""

from __future__ import annotations

import pandas as pd

from app.utils.operator_cleaner import clean_operator_series


class TestCleanOperatorSeries:
    def test_standardizes_airline_variants(self):
        series = pd.Series(["天骄航空", "东航技术", "江西航空有限公司", "中国东方航空", "南航"])

        result = clean_operator_series(series)

        assert result.tolist() == ["天骄", "东航", "江西航", "东航", "南航"]

    def test_null_variants_become_wu(self):
        series = pd.Series(["", "nan", "None", "null", "NaN", "NULL", None, float("nan")])

        result = clean_operator_series(series)

        assert (result == "无").all()
        assert result.isna().sum() == 0

    def test_strips_whitespace(self):
        # 纯空格 → 空字符串 → 「无」；前后空格被去除
        series = pd.Series(["  东航  ", "   ", "南航"])

        result = clean_operator_series(series)

        assert result.tolist() == ["东航", "无", "南航"]

    def test_does_not_mutate_input(self):
        series = pd.Series(["天骄航空", None])
        original = series.tolist()

        clean_operator_series(series)

        # 输入 Series 不应被修改
        assert series.tolist() == original

    def test_unknown_values_kept_as_is(self):
        # 未命中任何规则的值原样保留（仅做 strip）
        series = pd.Series(["试飞院", "某未知航司"])

        result = clean_operator_series(series)

        assert result.tolist() == ["试飞院", "某未知航司"]

    def test_custom_airline_rules(self):
        series = pd.Series(["甲航司", "乙航司"])
        custom_rules = [(["甲航司", "乙航司"], "AB航司")]

        result = clean_operator_series(series, airline_rules=custom_rules)

        assert result.tolist() == ["AB航司", "AB航司"]

    def test_custom_null_replacements(self):
        series = pd.Series(["缺失", "东航"])
        custom_nulls = ["缺失"]

        result = clean_operator_series(series, null_replacements=custom_nulls)

        assert result.tolist() == ["无", "东航"]

    def test_empty_series(self):
        result = clean_operator_series(pd.Series([], dtype=object))

        assert len(result) == 0

    def test_preserves_numeric_cells(self):
        # object 列混入数值时，数值不应被 strip 误杀为 NaN 再被填成「无」
        series = pd.Series(["东航", 12345, None], dtype=object)

        result = clean_operator_series(series)

        assert result.iloc[0] == "东航"
        assert result.iloc[1] == 12345
        assert result.iloc[2] == "无"
