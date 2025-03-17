import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path

class TempFileManager:
    def __init__(self, base_dir='data/temp'):
        self.base_dir = Path(base_dir)
        self.categories = ['search', 'process', 'export']
        self._init_dirs()

    def _init_dirs(self):
        """初始化临时文件目录结构"""
        for category in self.categories:
            (self.base_dir / category).mkdir(parents=True, exist_ok=True)

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
    manager.clean_old_files()

if __name__ == '__main__':
    main() 