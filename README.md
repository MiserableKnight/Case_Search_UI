# Case Search UI

## 项目简介

Case Search UI 是一个基于 Flask 的 Web 应用，旨在提供一个高效、易用的历史问题查询系统。用户可以通过本系统进行关键字搜索、高级搜索、相似度搜索，并支持数据导入、导出和分析功能。

## 技术栈

- **后端**: Flask, Pandas, NumPy
- **前端**: HTML, CSS, JavaScript
- **数据存储**: Parquet 文件

## 主要功能

- **多源数据搜索**: 支持在多个数据源（如快响信息、工程文件、故障报告等）中进行搜索。
- **灵活的搜索选项**:
    - **关键字搜索**: 支持多关键字组合，并可切换 AND/OR 逻辑。
    - **高级搜索**: 支持按指定列、日期范围进行精确筛选。
    - **相似度搜索**: 根据参考案例查找相似的历史问题。
- **数据导入与导出**:
    - 支持从 Excel 文件导入数据，并能自动处理重复项。
    - 支持将搜索结果导出为 Excel 文件。
- **数据分析**: 提供数据可视化分析功能。
- **敏感词管理**: 支持对敏感词进行管理和自动脱敏处理。

## 安装与运行

### 环境要求

- Python 3.10+

### 安装步骤

1.  **创建并激活虚拟环境**:
    ```bash
    # Windows
    python -m venv .venv
    .venv\Scripts\activate

    # 或使用提供的脚本
    activate.bat

    # Linux/macOS
    python3 -m venv .venv
    source .venv/bin/activate
    ```

2.  **安装依赖**:
    ```bash
    # 生产依赖
    pip install -r requirements.txt

    # 开发依赖（包含代码检查工具）
    pip install -r requirements-dev.txt
    ```

3.  **运行应用**:
    ```bash
    python wsgi.py
    ```

### 开发工具

项目使用 [Ruff](https://docs.astral.sh/ruff/) 进行代码检查和格式化：

```bash
# 检查代码质量
ruff check .

# 自动修复问题
ruff check --fix .

# 格式化代码
ruff format .

# 安装 pre-commit hooks（可选）
pre-commit install
```

应用将在本地启动，您可以通过浏览器访问 `http://127.0.0.1:5000`。

## 项目结构

```
.
├── app/                # 应用核心代码
│   ├── api/            # API 蓝图
│   ├── core/           # 核心业务逻辑
│   ├── services/       # 服务层
│   ├── static/         # 静态文件 (CSS, JS)
│   ├── templates/      # HTML 模板
│   ├── __init__.py     # 应用工厂
│   └── routes.py       # 主路由
├── data/               # 数据文件
├── docs/               # 项目文档
├── logs/               # 日志文件
├── scripts/            # 脚本
├── wsgi.py             # WSGI 入口
└── requirements.txt    # Python 依赖
