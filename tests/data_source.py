import os

class DataSource:
    def __init__(self):
        # 更新相对路径以适应新的位置
        self.data_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'data') 