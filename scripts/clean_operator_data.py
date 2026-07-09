"""对指定数据源的「运营人」列做一次性数据清洗。

背景：正常通过 Web 导入的数据会经过 clean_operator_names 清洗，但有时数据是
直接用 Jupyter Notebook 合并进 parquet 的，导致「运营人」列里残留未清洗的名称
（如「中国东方航空」「中国国际航空」等）。本脚本按照
app/config/data_cleaning_config.py 的 AIRLINE_REPLACE_RULES 对现有 parquet 数据
做一次回填式清洗。

用法:
    # 预览（dry-run，不写回，只打印将被修改的项）
    python scripts/clean_operator_data.py case
    python scripts/clean_operator_data.py            # 默认 case

    # 实际执行（自动备份原文件到 data/backup_data/）
    python scripts/clean_operator_data.py case --apply

注意：执行后若 Flask 服务正在运行，需重启服务（或调用 /api/reset_data_source/<source>
清缓存）才能让搜索结果反映清洗后的数据。
"""

from __future__ import annotations

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

# 让脚本能直接 import app.*
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from app.config.data_cleaning_config import AIRLINE_REPLACE_RULES, NULL_VALUE_REPLACEMENTS  # noqa: E402, I001

RAW_DIR = ROOT_DIR / "data" / "raw"
BACKUP_DIR = ROOT_DIR / "data" / "backup_data"
OPERATOR_COLUMN = "运营人"


def clean_operator_series(series: pd.Series) -> pd.Series:
    """对「运营人」Series 应用与 DataImportProcessor.clean_operator_names 一致的清洗逻辑。"""
    cleaned = series.copy()
    cleaned = cleaned.str.strip()
    cleaned = cleaned.replace(NULL_VALUE_REPLACEMENTS, "无")
    for replacements, target in AIRLINE_REPLACE_RULES:
        cleaned = cleaned.replace(replacements, target)
    cleaned = cleaned.fillna("无")
    return cleaned


def build_change_report(before: pd.Series, after: pd.Series) -> list[tuple[str, str, int]]:
    """统计每个被修改的取值：原值 -> 新值 -> 受影响行数。"""
    # 按原始索引对齐，仅保留发生变化的行
    comparison = pd.DataFrame({"before": before, "after": after})
    changed = comparison[comparison["before"] != comparison["after"]]
    if changed.empty:
        return []
    grouped = (
        changed.groupby(["before", "after"]).size().reset_index(name="count").sort_values("count", ascending=False)
    )
    return list(grouped.itertuples(index=False, name=None))


def main() -> int:
    parser = argparse.ArgumentParser(description="清洗指定数据源的「运营人」列")
    parser.add_argument("source", nargs="?", default="case", help="数据源名称（默认 case）")
    parser.add_argument("--apply", action="store_true", help="实际执行写回（默认仅预览）")
    args = parser.parse_args()

    source = args.source
    data_path = RAW_DIR / f"{source}.parquet"
    if not data_path.exists():
        print(f"[错误] 数据文件不存在: {data_path}")
        return 1

    df = pd.read_parquet(data_path)
    if OPERATOR_COLUMN not in df.columns:
        print(f"[错误] 数据源 {source} 没有「{OPERATOR_COLUMN}」列")
        return 1

    total = len(df)
    before = df[OPERATOR_COLUMN]
    after = clean_operator_series(before)

    changes = build_change_report(before, after)
    affected = sum(cnt for _, _, cnt in changes)

    print("=" * 60)
    print(f"数据源: {source}    总行数: {total}")
    print(f"清洗前不同取值数: {before.nunique(dropna=False)}")
    print(f"清洗后不同取值数: {pd.Series(after).nunique(dropna=False)}")
    print(f"受影响行数: {affected}")
    print("=" * 60)

    if not changes:
        print("无需清洗：所有「运营人」取值已符合规则。")
        return 0

    print("将被修改的取值（原值 -> 新值  影响行数）:")
    for old, new, cnt in changes:
        print(f"  {old!r:>30} -> {new!r:<10}  ({cnt} 行)")

    if not args.apply:
        print("\n[预览模式] 未写回。确认无误后加 --apply 实际执行。")
        return 0

    # 实际写回：先备份
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"{source}_operator_{timestamp}.parquet"
    shutil.copy2(data_path, backup_path)
    print(f"\n已备份原文件到: {backup_path}")

    df[OPERATOR_COLUMN] = after
    df.to_parquet(data_path, index=False)
    print(f"已写回清洗后的数据: {data_path}")
    print(f"完成：共清洗 {affected} 行运营人数据。")
    print("提示：若 Flask 服务正在运行，请重启服务以刷新数据缓存。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
