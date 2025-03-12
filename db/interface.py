from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
from datetime import datetime

class ContentDataSource(ABC):
    @abstractmethod
    def load_data(self) -> pd.DataFrame:
        """加载所有工作内容数据"""
        pass

    @abstractmethod
    def save_content(self, content_data: Dict[str, Any]) -> bool:
        """保存新的工作内容"""
        pass

    @abstractmethod
    def save_embedding(self, content_id: str, embedding: np.ndarray) -> bool:
        """保存向量嵌入"""
        pass 