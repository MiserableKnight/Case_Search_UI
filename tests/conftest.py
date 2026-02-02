"""
测试配置和共享夹具

提供所有测试模块共享的夹具和配置
"""

import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Generator

import pandas as pd
import pytest
from flask import Flask

# 设置测试日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """获取测试数据目录"""
    return Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def temp_output_dir() -> Generator[Path, None, None]:
    """创建临时输出目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_text_data() -> str:
    """示例文本数据"""
    return "这是一个测试文本，包含中文和English混合内容。This is a test sample."


@pytest.fixture
def sample_dataframe() -> pd.DataFrame:
    """示例DataFrame数据"""
    return pd.DataFrame({
        "列1": ["值1", "值2", "值3"],
        "列2": ["数据A", "数据B", "数据C"],
        "数字列": [100, 200, 300],
    })


@pytest.fixture
def sample_excel_file(test_data_dir: Path, temp_output_dir: Path) -> Path:
    """创建示例Excel文件"""
    df = pd.DataFrame({
        "故障发生日期": ["2023-01-01", "2023-01-02", "2023-01-03"],
        "申请时间": ["2023-01-01", "2023-01-02", "2023-01-03"],
        "标题": ["测试标题1", "测试标题2", "测试标题3"],
        "问题描述": ["测试描述1", "测试描述2", "测试描述3"],
        "答复详情": ["测试答复1", "测试答复2", "测试答复3"],
        "客户期望": ["期望1", "期望2", "期望3"],
        "ATA": ["ATA1", "ATA2", "ATA3"],
        "飞机序列号/注册号": ["B-1234", "B-5678", "B-9012"],
        "运营人": ["运营人A", "运营人B", "运营人C"],
        "服务请求单编号": ["SR001", "SR002", "SR003"],
        "机型": ["737", "777", "787"],
    })

    output_path = temp_output_dir / "test_sample.xlsx"
    df.to_excel(output_path, index=False)
    return output_path


@pytest.fixture
def unicode_polluted_text() -> str:
    """包含Unicode污染的文本"""
    return "正常文本\u200e\u200f\u202a\u202b包含控制字符\u200b\u200c\u200d和零宽字符"


@pytest.fixture
def sensitive_words_data() -> dict:
    """敏感词测试数据"""
    return {
        "航空公司": [{"word": "某某航空"}, {"word": "示例航空"}],
        "机场": [{"word": "某某机场"}, {"word": "示例机场"}],
        "人员": [{"word": "张三"}, {"word": "李四"}],
    }


@pytest.fixture
def sensitive_words_file(test_data_dir: Path, temp_output_dir: Path, sensitive_words_data: dict) -> str:
    """创建敏感词测试文件"""
    file_path = temp_output_dir / "test_sensitive_words.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(sensitive_words_data, f, ensure_ascii=False, indent=2)
    return str(file_path)


@pytest.fixture
def sample_similarity_data() -> list[dict[str, Any]]:
    """示例相似度计算数据"""
    return [
        {
            "申请时间": "2023-01-01",
            "标题": "发动机控制系统故障",
            "问题描述": "飞机在巡航阶段出现发动机控制警告",
            "答复详情": "更换控制单元后问题解决",
            "机型": "737",
        },
        {
            "申请时间": "2023-01-02",
            "标题": "液压系统泄漏",
            "问题描述": "地面检查发现液压系统有泄漏",
            "答复详情": "更换密封圈后测试正常",
            "机型": "777",
        },
        {
            "申请时间": "2023-01-03",
            "标题": "导航设备异常",
            "问题描述": "起飞后导航设备显示异常",
            "答复详情": "重启设备后恢复正常",
            "机型": "787",
        },
    ]


@pytest.fixture
def app_config(temp_output_dir: Path, sensitive_words_file: str) -> dict:
    """应用配置"""
    return {
        "TESTING": True,
        "DEBUG": True,
        "FILE_CONFIG": {
            "SENSITIVE_WORDS_FILE": sensitive_words_file,
            "DATA_DIR": str(temp_output_dir),
        },
    }


@pytest.fixture
def flask_app(app_config: dict) -> Generator[Flask, None, None]:
    """创建Flask应用实例"""
    # 导入应用工厂
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from app import create_app

    app = create_app()
    app.config.update(app_config)

    with app.app_context():
        yield app


@pytest.fixture
def client(flask_app: Flask) -> Any:
    """创建Flask测试客户端"""
    return flask_app.test_client()


@pytest.fixture
def mock_logger(mocker: Any) -> Any:
    """Mock日志记录器"""
    return mocker.patch("app.utils.unicode_cleaner.logger")


@pytest.fixture
def case_data_with_pollution() -> pd.DataFrame:
    """包含Unicode污染的案例数据"""
    return pd.DataFrame({
        "故障发生日期": ["2023-01-01\u200e", "2023-01-02", "2023-01-03\u200b"],
        "申请时间": ["2023-01-01", "2023-01-02\u202a", "2023-01-03"],
        "标题": ["\u200f测试标题1", "测试标题2", "测试标题3\u200d"],
        "问题描述": ["测试描述1\u200c", "测试描述2", "测试描述3"],
        "答复详情": ["测试答复1", "\u200e测试答复2", "测试答复3"],
        "客户期望": ["期望1", "期望2", "期望3"],
        "ATA": ["ATA1", "ATA2", "ATA3"],
        "飞机序列号/注册号": ["B-1234", "B-5678", "B-9012"],
        "运营人": ["运营人A", "运营人B", "运营人C"],
        "服务请求单编号": ["SR001", "SR002", "SR003"],
        "机型": ["737", "777", "787"],
    })


@pytest.fixture
def empty_dataframe() -> pd.DataFrame:
    """空DataFrame"""
    return pd.DataFrame()


@pytest.fixture
def null_values_dataframe() -> pd.DataFrame:
    """包含空值的DataFrame"""
    return pd.DataFrame({
        "列1": ["值1", None, "值3"],
        "列2": [None, "数据B", "数据C"],
        "列3": [1.0, float("nan"), pd.NA],
    })


# Pytest标记定义
pytestmark = [
    pytest.mark.unit,
]


def pytest_configure(config):
    """配置Pytest标记"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "api: API tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
