from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
from datetime import datetime

class DatabaseAdapter(ABC):
    """数据库适配器基类"""
    
    @abstractmethod
    def load_data(self) -> pd.DataFrame:
        """加载所有数据"""
        pass

    @abstractmethod
    def save_content(self, content_data: Dict[str, Any]) -> bool:
        """保存内容"""
        pass

    @abstractmethod
    def save_embedding(self, content_id: str, embedding: np.ndarray) -> bool:
        """保存向量嵌入"""
        pass

    @abstractmethod
    def close(self) -> None:
        """关闭数据库连接"""
        pass 