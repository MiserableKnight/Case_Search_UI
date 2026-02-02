# 测试文档

本项目使用 pytest 作为测试框架，目标测试覆盖率为 60%。

## 目录结构

```
tests/
├── __init__.py              # 测试包初始化
├── conftest.py              # pytest配置和共享夹具
├── unit/                    # 单元测试
│   ├── __init__.py
│   ├── test_unicode_cleaner.py      # Unicode清洗器测试
│   ├── test_anonymizer.py            # 脱敏器测试
│   ├── test_similarity_calculator.py # 相似度计算器测试
│   ├── test_similarity_service.py    # 相似度服务测试
│   ├── test_error_handler.py         # 错误处理测试
│   └── test_data_processor.py        # 数据处理器测试
├── integration/             # 集成测试
│   └── __init__.py
├── api/                     # API测试
│   ├── __init__.py
│   ├── test_similarity_routes.py     # 相似度API测试
│   └── test_api_response.py          # API响应测试
└── fixtures/                # 测试数据文件
```

## 运行测试

### 运行所有测试

```bash
pytest
```

### 运行特定类型的测试

```bash
# 只运行单元测试
pytest -m unit

# 只运行集成测试
pytest -m integration

# 只运行API测试
pytest -m api
```

### 运行特定文件

```bash
# 运行单个测试文件
pytest tests/unit/test_unicode_cleaner.py

# 运行特定测试类
pytest tests/unit/test_unicode_cleaner.py::TestUnicodeCleaner

# 运行特定测试方法
pytest tests/unit/test_unicode_cleaner.py::TestUnicodeCleaner::test_clean_text_normal_string
```

### 生成覆盖率报告

```bash
# 生成覆盖率报告（终端 + HTML）
pytest --cov=app --cov-report=term-missing --cov-report=html

# 生成XML格式覆盖率报告（用于CI）
pytest --cov=app --cov-report=xml

# 设置最低覆盖率要求（60%）
pytest --cov=app --cov-fail-under=60
```

### 并行运行测试

```bash
# 使用4个进程并行运行
pytest -n 4

# 自动检测CPU核心数
pytest -n auto
```

### 使用测试运行脚本

```bash
# 运行所有测试
python scripts/run_tests.py

# 运行单元测试并生成覆盖率
python scripts/run_tests.py --unit --coverage

# 运行API测试，详细输出
python scripts/run_tests.py --api --verbose

# 并行运行测试
python scripts/run_tests.py --parallel 4

# 快速失败模式
python scripts/run_tests.py --fail-fast
```

## 测试标记

- `unit`: 单元测试 - 测试单个类或函数
- `integration`: 集成测试 - 测试多个组件之间的交互
- `api`: API测试 - 测试HTTP端点
- `slow`: 慢速测试 - 运行时间较长的测试

## 测试夹具

测试夹具在 `conftest.py` 中定义，包括：

- `flask_app`: Flask应用实例
- `client`: Flask测试客户端
- `sample_text_data`: 示例文本数据
- `sample_dataframe`: 示例DataFrame
- `sample_excel_file`: 示例Excel文件
- `unicode_polluted_text`: 包含Unicode污染的文本
- `sensitive_words_data`: 敏感词测试数据
- `sample_similarity_data`: 示例相似度计算数据

## 添加新测试

### 单元测试模板

```python
"""
测试描述
"""

import pytest
from app.module import ClassToTest


@pytest.mark.unit
class TestClassToTest:
    """测试类"""

    def setup_method(self):
        """每个测试方法前执行"""
        self.instance = ClassToTest()

    def test_method_name(self):
        """测试方法描述"""
        result = self.instance.method()
        assert result == expected_value


@pytest.mark.parametrize("input,expected", [
    ("input1", "output1"),
    ("input2", "output2"),
])
def test_parametrized(input, expected):
    """参数化测试"""
    assert function(input) == expected
```

### API测试模板

```python
"""
API端点测试
"""

import json
import pytest


@pytest.mark.api
class TestApiRoutes:
    """API路由测试"""

    def test_endpoint_success(self, client):
        """测试成功响应"""
        response = client.post(
            "/api/endpoint",
            json={"key": "value"},
            content_type="application/json",
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
```

## CI/CD

GitHub Actions工作流在 `.github/workflows/tests.yml` 中定义：

- 在推送到主分支或创建PR时自动运行
- 测试Python 3.10和3.11
- 运行ruff代码检查
- 生成测试覆盖率报告
- 上传覆盖率到Codecov

## 当前测试覆盖率

- 目标覆盖率: 60%
- 当前状态: 查看最新的CI运行结果或本地运行 `pytest --cov=app`

## 测试最佳实践

1. **隔离性**: 每个测试应该独立运行，不依赖其他测试
2. **清晰性**: 测试名称应该清楚描述测试的内容
3. **快速性**: 单元测试应该快速运行
4. **可维护性**: 测试代码应该和生产代码一样保持高质量
5. **覆盖率**: 目标是60%的代码覆盖率，重点覆盖核心业务逻辑

## 调试测试

```bash
# 在第一个失败处停止
pytest -x

# 进入调试器
pytest --pdb

# 显示本地变量
pytest -l

# 显示详细输出
pytest -vv
```
