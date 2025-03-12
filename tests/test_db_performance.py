import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 获取测试数据文件的绝对路径
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
BENCHMARK_FILE = os.path.join(TEST_DATA_DIR, "benchmark_data.parquet")

import time
import numpy as np
from datetime import datetime
from typing import List, Dict, Any
from db.parquet_db import ParquetDB
from db.mongo_db import MongoDB

class TestDBPerformance:
    def __init__(self):
        self.parquet_db = ParquetDB(BENCHMARK_FILE)
        self.mongo_db = MongoDB(db_name="benchmark_db")
        self._clean_data()
        
    def _clean_data(self):
        """清理测试数据"""
        print("清理旧的测试数据...")
        if os.path.exists(BENCHMARK_FILE):
            os.remove(BENCHMARK_FILE)
        # 确保MongoDB连接有效
        if not hasattr(self, 'mongo_db') or self.mongo_db is None:
            self.mongo_db = MongoDB(db_name="benchmark_db")
        self.mongo_db.contents.delete_many({})
        
    def prepare_test_data(self, n_records: int):
        """准备测试数据"""
        print(f"\n准备 {n_records} 条测试数据...")
        test_data = []
        
        # 生成数据
        print("生成测试数据...")
        for i in range(n_records):
            content = {
                "content_id": f"test_{i}",
                "text": f"这是测试内容 {i}",
                "timestamp": datetime.now(),
                "embedding": np.random.rand(1536)
            }
            test_data.append(content)
            if (i + 1) % 1000 == 0:
                print(f"已生成 {i + 1}/{n_records} 条数据")
        
        # 保存到Parquet
        print("\n保存到Parquet...")
        for i, content in enumerate(test_data):
            self.parquet_db.save_content(content)
            if (i + 1) % 1000 == 0:
                print(f"已保存 {i + 1}/{n_records} 条数据到Parquet")
        print("提交Parquet数据到文件...")
        self.parquet_db.commit()
        
        # 保存到MongoDB
        print("\n保存到MongoDB...")
        for i, content in enumerate(test_data):
            self.mongo_db.save_content(content)
            if (i + 1) % 1000 == 0:
                print(f"已保存 {i + 1}/{n_records} 条数据到MongoDB")

    def _ensure_connections(self):
        """确保数据库连接有效"""
        if not hasattr(self, 'parquet_db') or self.parquet_db is None:
            self.parquet_db = ParquetDB(BENCHMARK_FILE)
        if not hasattr(self, 'mongo_db') or self.mongo_db is None:
            self.mongo_db = MongoDB(db_name="benchmark_db")

    def run_read_tests(self):
        """运行读取性能测试"""
        print("\n=== 开始读取性能测试 ===")
        self._ensure_connections()
        self.prepare_test_data(5000)
        self.test_load_performance()
        self.test_cached_load_performance()
        self._clean_up()

    def test_load_performance(self, repeat=5):
        """测试数据加载性能（冷启动）"""
        print("\n测试数据加载性能（冷启动）:")
        
        parquet_times = []
        mongo_times = []
        
        for i in range(repeat):
            # Parquet测试
            self.parquet_db.close()
            self.parquet_db = ParquetDB(BENCHMARK_FILE)
            start_time = time.time()
            df_parquet = self.parquet_db.load_data()
            parquet_times.append(time.time() - start_time)
            
            # MongoDB测试
            # 不关闭连接，而是重新创建实例
            self.mongo_db = MongoDB(db_name="benchmark_db")
            start_time = time.time()
            df_mongo = self.mongo_db.load_data()
            mongo_times.append(time.time() - start_time)
            
        self._print_stats("冷启动加载", parquet_times, mongo_times)

    def test_cached_load_performance(self, repeat=5):
        """测试缓存数据加载性能"""
        print("\n测试数据加载性能（热启动）:")
        
        # 预热
        df_parquet = self.parquet_db.load_data()
        df_mongo = self.mongo_db.load_data()
        
        parquet_times = []
        mongo_times = []
        
        for i in range(repeat):
            # Parquet测试
            start_time = time.time()
            df_parquet = self.parquet_db.load_data()
            parquet_times.append(time.time() - start_time)
            
            # MongoDB测试
            start_time = time.time()
            df_mongo = self.mongo_db.load_data()
            mongo_times.append(time.time() - start_time)
            
        self._print_stats("热启动加载", parquet_times, mongo_times)

    def run_search_tests(self):
        """运行搜索性能测试"""
        print("\n=== 开始搜索性能测试 ===")
        self._ensure_connections()
        self.prepare_test_data(5000)
        self.test_search_performance()
        self._clean_up()

    def test_search_performance(self, n_queries=100, repeat=5):
        """测试搜索性能"""
        print("\n测试搜索性能:")
        
        test_queries = [
            {"keywords": f"测试内容 {i}", "column_name": "text"} 
            for i in range(n_queries)
        ]
        
        parquet_times = []
        mongo_times = []
        
        for i in range(repeat):
            # Parquet测试
            start_time = time.time()
            df = self.parquet_db.load_data()
            for query in test_queries:
                mask = df['text'].str.contains(query['keywords'], na=False)
                results = df[mask]
            parquet_times.append(time.time() - start_time)
            
            # MongoDB测试
            start_time = time.time()
            for query in test_queries:
                results = self.mongo_db.contents.find({
                    "text": {"$regex": query['keywords']}
                })
                list(results)
            mongo_times.append(time.time() - start_time)
            
        self._print_stats("搜索性能", parquet_times, mongo_times)

    def _print_stats(self, test_name: str, parquet_times: List[float], mongo_times: List[float]):
        """打印性能统计"""
        print(f"\n{test_name}统计:")
        print(f"Parquet:")
        print(f"  平均: {np.mean(parquet_times):.3f}秒")
        print(f"  最快: {min(parquet_times):.3f}秒")
        print(f"  最慢: {max(parquet_times):.3f}秒")
        print(f"  标准差: {np.std(parquet_times):.3f}秒")
        print(f"MongoDB:")
        print(f"  平均: {np.mean(mongo_times):.3f}秒")
        print(f"  最快: {min(mongo_times):.3f}秒")
        print(f"  最慢: {max(mongo_times):.3f}秒")
        print(f"  标准差: {np.std(mongo_times):.3f}秒")

    def _clean_up(self):
        """清理资源"""
        if hasattr(self, 'parquet_db'):
            self.parquet_db.close()
        if hasattr(self, 'mongo_db'):
            self.mongo_db.close()
            self.mongo_db = None  # 清除引用

if __name__ == "__main__":
    benchmark = TestDBPerformance()
    # 运行读取性能测试
    benchmark.run_read_tests()
    # 运行搜索性能测试
    benchmark.run_search_tests() 