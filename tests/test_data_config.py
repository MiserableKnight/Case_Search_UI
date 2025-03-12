import os

class TestDataConfig:
    def __init__(self):
        """测试数据配置"""
        self.data_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'data') 