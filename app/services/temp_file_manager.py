import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

class TempFileManager:
    _instance = None
    _scheduler = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, base_dir='data/temp'):
        if not hasattr(self, 'initialized'):
            self.base_dir = Path(base_dir)
            self.categories = ['search', 'process', 'export']
            self._init_dirs()
            self.initialized = True

    def _init_dirs(self):
        """初始化临时文件目录结构"""
        for category in self.categories:
            (self.base_dir / category).mkdir(parents=True, exist_ok=True)

    def start_scheduler(self, cron_expression='0 0 * * *'):  # 默认每天凌晨执行
        """启动定时清理任务"""
        if self._scheduler is None:
            self._scheduler = BackgroundScheduler()
            self._scheduler.add_job(
                self.clean_old_files,
                trigger=CronTrigger.from_crontab(cron_expression),
                id='clean_temp_files'
            )
            self._scheduler.start()

    def stop_scheduler(self):
        """停止定时清理任务"""
        if self._scheduler:
            self._scheduler.shutdown()
            self._scheduler = None

    def clean_old_files(self, days=7):
        """清理指定天数前的临时文件"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for category in self.categories:
            category_dir = self.base_dir / category
            if not category_dir.exists():
                continue

            for item in category_dir.glob('*'):
                if item.is_file():
                    mtime = datetime.fromtimestamp(item.stat().st_mtime)
                    if mtime < cutoff_date:
                        item.unlink()

    def get_temp_path(self, category, prefix='', suffix=''):
        """获取新的临时文件路径"""
        if category not in self.categories:
            raise ValueError(f"Invalid category. Must be one of {self.categories}")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{prefix}_{timestamp}{suffix}" if prefix else f"{timestamp}{suffix}"
        return self.base_dir / category / filename

def main():
    manager = TempFileManager()
    # 启动时执行一次清理
    manager.clean_old_files()
    # 启动定时任务（每天凌晨执行）
    manager.start_scheduler()

if __name__ == '__main__':
    main() 