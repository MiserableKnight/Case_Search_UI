"""搜索结果默认排序逻辑的单元测试。

覆盖 _apply_default_sort：
- 日期列优先级回退（申请时间无效时用故障发生日期）
- 倒序（最新在上）
- 所有日期列无效的记录排到最后
- 临时排序列不泄漏到结果
- 非配置数据源 / 缺列时不改变顺序
"""

from __future__ import annotations

import pandas as pd

from app.api.data_source_routes import SORT_DATE_PRIORITY, _apply_default_sort


def _sample_case_df() -> pd.DataFrame:
    """构造覆盖各种日期有效性的 case 样本数据。

    期望排序键（倒序）：
        C  -> 故障发生日期 2024-04-01（申请时间无效，回退）
        A  -> 申请时间 2024-03-01
        E  -> 申请时间 2024-02-01
        B  -> 申请时间 2024-01-01
        D  -> 两列均无效（文本垃圾 + 空），排最后
    """
    return pd.DataFrame(
        {
            "申请时间": ["2024-03-01", "2024-01-01", pd.NA, "更改计划制定中，暂无法确认", "2024-02-01"],
            "故障发生日期": ["", "", "2024-04-01", "", "2024-02-15"],
            "标题": ["A", "B", "C", "D", "E"],
        }
    )


class TestApplyDefaultSort:
    def test_case_sorts_descending_with_fallback(self):
        df = _sample_case_df()

        result = _apply_default_sort(df, "case")

        # 倒序：C(回退04-01) > A(03-01) > E(02-01) > B(01-01) > D(无效,最后)
        assert result["标题"].tolist() == ["C", "A", "E", "B", "D"]

    def test_temp_sort_column_not_leaked(self):
        df = _sample_case_df()

        result = _apply_default_sort(df, "case")

        assert "_sort_key" not in result.columns

    def test_does_not_mutate_input(self):
        df = _sample_case_df()
        original = df["标题"].tolist()

        _apply_default_sort(df, "case")

        # 输入数据框的行顺序不应被修改
        assert df["标题"].tolist() == original

    def test_unknown_source_returns_unchanged(self):
        df = _sample_case_df()

        result = _apply_default_sort(df, "engineering")

        # engineering 不在排序配置中，应保持原顺序
        assert result["标题"].tolist() == df["标题"].tolist()

    def test_missing_date_columns_returns_unchanged(self):
        # 缺少所有配置的日期列
        df = pd.DataFrame({"标题": ["A", "B", "C"]})

        result = _apply_default_sort(df, "case")

        assert result["标题"].tolist() == ["A", "B", "C"]

    def test_all_invalid_dates_sorted_last(self):
        # 所有日期都无效时，应保持稳定（全部排最后，不报错）
        df = pd.DataFrame(
            {
                "申请时间": ["abc", "", pd.NA],
                "故障发生日期": ["", "xyz", ""],
                "标题": ["A", "B", "C"],
            }
        )

        result = _apply_default_sort(df, "case")

        assert len(result) == 3
        assert sorted(result["标题"].tolist()) == ["A", "B", "C"]


class TestSortDatePriorityConfig:
    def test_case_priority_is_application_time_then_fault_date(self):
        assert SORT_DATE_PRIORITY["case"] == ["申请时间", "故障发生日期"]
