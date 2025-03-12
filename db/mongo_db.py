from typing import Dict, Any
import pandas as pd
import numpy as np
from datetime import datetime
from pymongo import MongoClient
from tests.base import DatabaseAdapter

class MongoDB(DatabaseAdapter):
    def __init__(self, db_url: str = "mongodb://localhost:27017/", 
                 db_name: str = "work_content"):
        self.client = MongoClient(db_url)
        self.db = self.client[db_name]
        self.contents = self.db.contents
        self._ensure_indexes()

    def _ensure_indexes(self):
        """确保必要的索引存在"""
        self.contents.create_index("content_id", unique=True)
        self.contents.create_index("timestamp")
        self.contents.create_index("text")  # 添加文本索引

    def load_data(self) -> pd.DataFrame:
        """从MongoDB加载数据并转换为DataFrame"""
        cursor = self.contents.find({})
        data = list(cursor)
        if not data:
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        # 确保embedding是numpy数组
        if 'embedding' in df.columns:
            df['embedding'] = df['embedding'].apply(np.array)
        return df

    def save_content(self, content_data: Dict[str, Any]) -> bool:
        """保存内容到MongoDB"""
        try:
            # 确保有时间戳
            if 'timestamp' not in content_data:
                content_data['timestamp'] = datetime.now()
            
            # 转换numpy数组为列表
            if 'embedding' in content_data and isinstance(content_data['embedding'], np.ndarray):
                content_data = content_data.copy()  # 创建副本以免修改原始数据
                content_data['embedding'] = content_data['embedding'].tolist()
            
            # 使用upsert来更新或插入
            result = self.contents.update_one(
                {"content_id": content_data["content_id"]},
                {"$set": content_data},
                upsert=True
            )
            return True
        except Exception as e:
            print(f"保存内容失败: {e}")
            return False

    def save_embedding(self, content_id: str, embedding: np.ndarray) -> bool:
        """保存向量嵌入到MongoDB"""
        try:
            result = self.contents.update_one(
                {"content_id": content_id},
                {"$set": {"embedding": embedding.tolist()}},
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"保存向量嵌入失败: {e}")
            return False

    def close(self) -> None:
        """关闭MongoDB连接"""
        if self.client:
            self.client.close() 