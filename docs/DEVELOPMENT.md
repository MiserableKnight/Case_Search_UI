# 开发指南

## 📋 目录结构

```
Case_Search_UI/
├── .venv/                   # 虚拟环境（Python 最佳实践）
├── app/                     # 应用核心代码
│   ├── api/                 # API 蓝图
│   ├── core/                # 核心业务逻辑
│   ├── services/            # 服务层
│   ├── static/              # 静态文件 (CSS, JS)
│   ├── templates/           # HTML 模板
│   ├── config/              # 配置模块
│   └── utils/               # 工具函数
├── data/                    # 数据文件
│   ├── raw/                 # 原始数据
│   ├── processed/           # 处理后数据
│   └── temp/                # 临时文件
├── docs/                    # 项目文档
├── logs/                    # 日志文件
├── scripts/                 # 工具脚本
│   └── run.bat              # 启动脚本
├── tests/                   # 测试代码（待添加）
├── .editorconfig            # 编辑器配置
├── .gitignore               # Git 忽略规则
├── .python-version          # Python 版本
├── .pre-commit-config.yaml  # Pre-commit hooks
├── pyproject.toml           # 项目配置（Ruff）
├── requirements.txt         # 生产依赖
├── requirements-dev.txt     # 开发依赖
├── wsgi.py                  # WSGI 入口
├── activate.bat             # 激活虚拟环境（Windows）
└── deactivate.bat           # 停用虚拟环境（Windows）
```

## 🚀 快速开始

### 1. 虚拟环境设置

```bash
# Windows 快速启动
activate.bat

# Linux/macOS
source .venv/bin/activate
```

### 2. 安装依赖

```bash
# 生产环境
pip install -r requirements.txt

# 开发环境（包含 Ruff）
pip install -r requirements-dev.txt
```

### 3. 运行应用

```bash
# 方式1：直接运行
python wsgi.py

# 方式2：使用脚本（Windows）
scripts\run.bat

# 应用将在 http://127.0.0.1:5000 启动
```

## 🔧 代码质量工具

### Ruff 配置

项目使用 [Ruff](https://docs.astral.sh/ruff/) 进行代码检查和格式化，配置文件为 `pyproject.toml`。

```bash
# 检查代码
ruff check .

# 自动修复
ruff check --fix .

# 格式化代码
ruff format .

# 同时检查和格式化
ruff check --fix . && ruff format .
```

### Pre-commit Hooks（可选）

```bash
# 安装
pip install pre-commit
pre-commit install

# 手动运行所有检查
pre-commit run --all-files
```

## 📝 编码规范

### 代码风格

- **行长度**: 100 字符
- **缩进**: 4 空格
- **引号**: 双引号（Ruff 默认）
- **导入顺序**: Ruff 自动排序

### 命名规范

- **类名**: `PascalCase`（例：`CaseService`）
- **函数/变量**: `snake_case`（例：`load_data`）
- **常量**: `UPPER_SNAKE_CASE`（例：`MAX_CONTENT_LENGTH`）
- **私有成员**: `_leading_underscore`（例：`_internal_method`）

### 文档字符串

- 使用中文文档字符串
- 函数必须包含参数和返回值说明
- 类和模块需要说明用途

```python
def search_cases(keyword: str, limit: int = 100) -> list:
    """
    搜索案例数据

    Args:
        keyword: 搜索关键字
        limit: 返回结果数量限制

    Returns:
        匹配的案例列表
    """
    pass
```

## 🏗️ 项目架构

### 分层架构

```
Routes (API 层)
    ↓
Services (业务逻辑层)
    ↓
Processors (数据处理层)
    ↓
Data Sources (数据源)
```

### 蓝图结构

- `data_import_routes/` - 数据导入 API
- `analysis_routes/` - 数据分析 API
- `similarity_routes/` - 相似度搜索 API
- `sensitive_word_routes/` - 敏感词管理 API

### 服务层

每个数据源都有对应的服务类：

- `CaseService` - 案例数据服务
- `FaultReportService` - 故障报告服务
- `EngineeringService` - 工程文件服务
- `ManualService` - 手册数据服务
- `RAndIRecordService` - 部件拆换记录服务

## 🐛 调试技巧

### 启用调试模式

```python
# wsgi.py
app.run(debug=True)
```

或设置环境变量：
```bash
set FLASK_ENV=development
python wsgi.py
```

### 查看日志

日志文件位于 `logs/` 目录，按日期分类。

### 常见问题

1. **端口被占用**
   ```python
   # wsgi.py 中修改端口
   port=int(os.environ.get("PORT", 5001))
   ```

2. **数据文件缺失**
   - 检查 `data/raw/` 目录下是否有 `.parquet` 文件

3. **依赖冲突**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

## 🔄 工作流程

### 提交代码前

```bash
# 1. 格式化代码
ruff format .

# 2. 检查代码
ruff check --fix .

# 3. 运行测试（待添加）
# pytest

# 4. 提交
git add .
git commit -m "描述你的更改"
```

### 添加新功能

1. 在 `app/core/` 添加业务逻辑
2. 在 `app/services/` 添加服务层
3. 在 `app/api/` 添加 API 路由
4. 更新相关文档

## 📚 相关文档

- [Flask 文档](https://flask.palletsprojects.com/)
- [Pandas 文档](https://pandas.pydata.org/docs/)
- [Ruff 文档](https://docs.astral.sh/ruff/)
- [项目分析报告](./code_quality_analysis_20260131.md)

## 🤝 贡献指南

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request
