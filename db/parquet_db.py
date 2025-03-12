from typing import Dict, Any
import pandas as pd
import numpy as np
from datetime import datetime
from tests.base import DatabaseAdapter

class ParquetDB(DatabaseAdapter):
    def __init__(self, file_path: str):
        self.file_path = file_path
        self._df = pd.DataFrame()  # 初始化为空DataFrame
        self.load_data()

    def load_data(self) -> pd.DataFrame:
        """从Parquet文件加载数据"""
        try:
            self._df = pd.read_parquet(self.file_path)
        except FileNotFoundError:
            self._df = pd.DataFrame()
        return self._df

    def save_content(self, content_data: Dict[str, Any]) -> bool:
        """保存内容到Parquet文件"""
        try:
            # 转换为DataFrame并追加
            new_row = pd.DataFrame([content_data])
            self._df = pd.concat([self._df, new_row], ignore_index=True)
            return True
        except Exception as e:
            print(f"保存内容失败: {e}")
            return False

    def commit(self):
        """将数据写入文件"""
        try:
            self._df.to_parquet(self.file_path)
            return True
        except Exception as e:
            print(f"提交数据失败: {e}")
            return False

    def save_embedding(self, content_id: str, embedding: np.ndarray) -> bool:
        """保存向量嵌入到Parquet文件"""
        try:
            if self._df is None:
                self.load_data()
            
            # 更新embedding
            mask = self._df['content_id'] == content_id
            if not mask.any():
                return False
            self._df.loc[mask, 'embedding'] = [embedding]
            self._df.to_parquet(self.file_path)
            return True
        except Exception as e:
            print(f"保存向量嵌入失败: {e}")
            return False

    def close(self) -> None:
        """关闭数据库连接（对于Parquet实际上不需要做什么）"""
        self._df = None 