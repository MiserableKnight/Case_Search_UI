#!/usr/bin/env python
"""
测试运行脚本

提供各种测试运行选项
"""

import argparse
import subprocess
import sys


def run_command(cmd: list[str], description: str) -> int:
    """运行命令并返回退出码"""
    print(f"\n{'=' * 60}")
    print(f"运行: {description}")
    print(f"命令: {' '.join(cmd)}")
    print("=" * 60)

    result = subprocess.run(cmd)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="运行项目测试")
    parser.add_argument("--unit", action="store_true", help="只运行单元测试")
    parser.add_argument("--integration", action="store_true", help="只运行集成测试")
    parser.add_argument("--api", action="store_true", help="只运行API测试")
    parser.add_argument("--coverage", action="store_true", help="生成测试覆盖率报告")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    parser.add_argument("--parallel", "-n", type=int, help="并行测试进程数")
    parser.add_argument("--fail-fast", "-x", action="store_true", help="遇到第一个失败就停止")

    args = parser.parse_args()

    # 构建pytest命令
    cmd = ["python", "-m", "pytest"]

    # 添加标记
    markers = []
    if args.unit:
        markers.append("unit")
    if args.integration:
        markers.append("integration")
    if args.api:
        markers.append("api")

    if markers:
        cmd.extend(["-m", " or ".join(markers)])

    # 添加覆盖率
    if args.coverage:
        cmd.extend(
            ["--cov=app", "--cov-report=term-missing", "--cov-report=html", "--cov-report=xml"]
        )

    # 添加详细输出
    if args.verbose:
        cmd.append("-vv")
    else:
        cmd.append("-v")

    # 添加并行测试
    if args.parallel:
        cmd.extend(["-n", str(args.parallel)])

    # 添加快速失败
    if args.fail_fast:
        cmd.append("-x")

    # 运行测试
    exit_code = run_command(cmd, "测试")

    # 如果生成了覆盖率报告，显示信息
    if args.coverage and exit_code == 0:
        print("\n" + "=" * 60)
        print("覆盖率报告已生成:")
        print("  - 终端报告: 见上方输出")
        print("  - HTML报告: htmlcov/index.html")
        print("  - XML报告: coverage.xml")
        print("=" * 60)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
