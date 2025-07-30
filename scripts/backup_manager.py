#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""数据自动备份管理模块。

提供自动备份功能，包括创建备份、清理旧备份和维护备份记录。
"""

import datetime
import json
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, cast


def setup_console() -> None:
    """设置控制台以正确显示中文。"""
    if sys.platform == "win32":
        # 设置Windows控制台代码页为UTF-8
        subprocess.run(["chcp", "65001"], shell=True, capture_output=True)
        # 刷新控制台设置
        os.system("")
        # 设置环境变量
        os.environ["PYTHONIOENCODING"] = "utf-8"

    # 设置Python输出编码
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    else:
        # Python 3.7以下版本的替代方案
        import codecs

        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer)  # type: ignore


# 初始化控制台设置
setup_console()


class BackupManager:
    """备份管理器类，负责数据的备份、清理和记录管理。"""

    def __init__(
        self, source_dir: str = "data/raw", backup_root: str = "data/backup_data"
    ):
        """初始化备份管理器。

        Args:
            source_dir: 需要备份的源目录路径（默认为data/raw目录）
            backup_root: 备份文件存储的根目录路径
        """
        self.source_dir = Path(source_dir)
        self.backup_root = Path(backup_root)
        self.log_file = Path("data/backup.log")
        self.backup_record_file = Path("data/backup_records.json")

        # 创建必要的目录和文件
        self.source_dir.mkdir(parents=True, exist_ok=True)  # 确保源目录存在
        self.backup_root.mkdir(parents=True, exist_ok=True)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(self.log_file, encoding="utf-8"),
                logging.StreamHandler(sys.stdout),
            ],
        )
        self.logger = logging.getLogger(__name__)

    def _check_source_directory(self) -> bool:
        """检查源目录是否存在且不为空。

        Returns:
            bool: 如果源目录存在且不为空返回True，否则返回False
        """
        # 检查源目录是否存在
        if not self.source_dir.exists():
            self.logger.error(f"源目录不存在: {self.source_dir}")
            return False

        # 检查源目录是否为空
        if not any(self.source_dir.iterdir()):
            self.logger.warning(f"源目录为空: {self.source_dir}")
            return False

        return True

    def _create_backup_directory(self) -> Path:
        """创建新的备份目录。

        Returns:
            Path: 新创建的备份目录路径
        """
        # 生成当前日期作为备份目录名
        today = datetime.datetime.now().strftime("%Y%m%d")
        backup_dir = self.backup_root / today

        # 如果目录已存在，添加时间戳以避免冲突
        if backup_dir.exists():
            timestamp = datetime.datetime.now().strftime("%H%M%S")
            backup_dir = self.backup_root / f"{today}_{timestamp}"

        # 创建备份目录
        backup_dir.mkdir(parents=True, exist_ok=True)
        return backup_dir

    def _copy_files(self, backup_dir: Path) -> int:
        """复制文件到备份目录。

        Args:
            backup_dir: 备份目录路径

        Returns:
            int: 备份的文件/目录数量
        """
        backup_count = 0
        for item in self.source_dir.iterdir():
            if item.is_dir():
                shutil.copytree(item, backup_dir / item.name)
                backup_count += 1
            else:
                shutil.copy2(item, backup_dir / item.name)
                backup_count += 1

        return backup_count

    def create_backup(self) -> bool:
        """执行备份操作。

        将源目录中的文件和子目录备份到备份目录，排除backup_data目录。

        Returns:
            bool: 备份成功返回True，失败返回False
        """
        try:
            # 检查源目录
            if not self._check_source_directory():
                return False

            # 创建备份目录
            backup_dir = self._create_backup_directory()

            # 复制文件
            backup_count = self._copy_files(backup_dir)

            # 如果没有文件被备份，删除空目录并返回
            if backup_count == 0:
                self.logger.warning(
                    "没有文件被备份（可能所有文件都在 backup_data 目录中）"
                )
                shutil.rmtree(backup_dir)  # 删除空的备份目录
                return False

            # 记录备份信息
            self._update_backup_records(str(backup_dir))

            self.logger.info(f"备份成功完成: {backup_dir}")
            self.logger.info(f"共备份了 {backup_count} 个文件/目录")
            return True

        except Exception as e:
            self.logger.error(f"备份过程中发生错误: {str(e)}")
            return False

    def cleanup_old_backups(self, keep_latest: int = 5) -> None:
        """清理旧的备份，只保留最近的几个。

        Args:
            keep_latest: 要保留的最新备份数量
        """
        try:
            # 获取所有备份目录
            backup_dirs = []
            for d in self.backup_root.iterdir():
                if d.is_dir():
                    try:
                        # 获取目录的创建时间
                        created_time = d.stat().st_ctime
                        backup_dirs.append((created_time, d))
                    except Exception:
                        self.logger.warning(f"无法获取目录信息: {d}")
                        continue

            # 按创建时间排序
            backup_dirs.sort(reverse=True)  # 降序排序，最新的在前面

            # 删除多余的备份
            for _, old_backup in backup_dirs[keep_latest:]:
                try:
                    shutil.rmtree(old_backup)
                    self.logger.info(f"已删除旧备份: {old_backup}")
                except Exception as e:
                    self.logger.error(f"删除旧备份失败 {old_backup}: {str(e)}")

            # 显示保留的备份数量
            remaining = len(backup_dirs[:keep_latest])
            self.logger.info(f"当前保留了 {remaining} 个最新备份")

        except Exception as e:
            self.logger.error(f"清理旧备份时发生错误: {str(e)}")

    def _update_backup_records(self, backup_path: str) -> None:
        """更新备份记录。

        Args:
            backup_path: 备份路径
        """
        try:
            records = self._load_backup_records()

            # 添加新的备份记录
            new_record = {
                "timestamp": datetime.datetime.now().isoformat(),
                "backup_path": backup_path,
                "status": "success",
            }

            records.append(new_record)

            # 保存更新后的记录
            with open(self.backup_record_file, "w", encoding="utf-8") as f:
                json.dump(records, f, ensure_ascii=False, indent=2)

        except Exception as e:
            self.logger.error(f"更新备份记录时发生错误: {str(e)}")

    def _load_backup_records(self) -> List[Dict[str, Any]]:
        """加载备份记录。

        Returns:
            List[Dict[str, Any]]: 备份记录列表，每条记录为一个字典
        """
        try:
            if self.backup_record_file.exists():
                with open(self.backup_record_file, "r", encoding="utf-8") as f:
                    return cast(List[Dict[str, Any]], json.load(f))
            return []
        except Exception as e:
            self.logger.error(f"加载备份记录时发生错误: {str(e)}")
            return []


def main() -> None:
    """主函数，执行备份操作并清理旧备份。"""
    try:
        # 清屏
        os.system("cls" if sys.platform == "win32" else "clear")

        # 显示标题
        print("\n" + "=" * 20 + " 数据备份工具 " + "=" * 20 + "\n")
        print("开始执行备份...\n")

        # 执行备份
        backup_manager = BackupManager()
        if backup_manager.create_backup():
            backup_manager.cleanup_old_backups()

            # 显示完成信息
            current_time = datetime.datetime.now()
            print("\n" + "=" * 50)
            print("备份完成！")
            print(f"完成时间：{current_time.strftime('%Y年%m月%d日 %H:%M:%S')}")
            print(f"备份目录：{backup_manager.backup_root.absolute()}")
            print(f"日志文件：{backup_manager.log_file.absolute()}")
            print(f"记录文件：{backup_manager.backup_record_file.absolute()}")
            print("=" * 50 + "\n")
        else:
            print("\n备份失败！请查看日志了解详细信息。\n")
    except Exception as e:
        print(f"\n发生错误：{str(e)}\n")
    finally:
        if sys.platform == "win32":
            input("按回车键退出...")


if __name__ == "__main__":
    main()
