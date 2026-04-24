# Case Search UI

## 项目简介

Case Search UI 是一个基于 Flask 的 Web 应用，旨在提供一个高效、易用的历史问题查询系统。用户可以通过本系统进行关键字搜索、高级搜索、相似度搜索，并支持数据导入、导出和分析功能。

## 技术栈

- **后端**: Flask, Pandas, NumPy, PyArrow, scikit-learn, jieba
- **前端**: Vue 3, Element Plus, Pinia, Axios, Vite
- **数据存储**: Parquet 文件
- **开发工具**: Ruff, pytest, mypy, pre-commit

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
├── app/                            # 应用核心代码
│   ├── api/                        # API 蓝图
│   │   ├── analysis_routes.py      # 数据分析接口
│   │   ├── data_source_routes.py   # 数据源管理接口
│   │   ├── data_import_routes/     # 数据导入接口（按数据类型拆分）
│   │   ├── sensitive_word_routes.py# 敏感词管理接口
│   │   └── similarity_routes.py    # 相似度搜索接口
│   ├── config/                     # 配置文件
│   │   ├── data_cleaning_config.py # 数据清洗规则配置
│   │   ├── default.py              # 默认配置
│   │   ├── development.py          # 开发环境配置
│   │   └── production.py           # 生产环境配置
│   ├── core/                       # 核心业务逻辑
│   │   ├── anonymizer.py           # 数据脱敏服务
│   │   ├── calculator.py           # 通用计算工具
│   │   ├── data_processors/        # 数据处理器（按数据类型拆分）
│   │   ├── error_handler.py        # 错误处理
│   │   └── word_manager.py         # 敏感词管理
│   ├── services/                   # 服务层
│   │   ├── data_services/          # 数据服务实现（按数据类型拆分）
│   │   ├── anonymization_service.py
│   │   ├── error_service.py
│   │   └── temp_file_manager.py    # 临时文件管理
│   ├── static/                     # 静态文件
│   │   ├── css/                    # 样式表
│   │   ├── js/                     # JavaScript
│   │   │   └── methods/            # 前端模块（搜索、表格、对话框等）
│   │   └── vendor/                 # 第三方库
│   ├── templates/                  # HTML 模板
│   │   └── components/             # 可复用模板组件
│   ├── types.py                    # 类型定义
│   ├── routes.py                   # 主路由
│   └── __init__.py                 # 应用工厂
├── data/                           # 数据存储
│   ├── processed/                  # 处理后的数据文件
│   ├── raw/                        # 原始数据文件
│   ├── backup_data/                # 自动备份
│   └── temp/                       # 临时文件（导入/导出/搜索）
├── tests/                          # 测试
│   ├── unit/                       # 单元测试
│   ├── integration/                # 集成测试
│   ├── api/                        # API 测试
│   └── fixtures/                   # 测试固件
├── scripts/                        # 脚本
├── docs/                           # 项目文档
├── logs/                           # 日志文件
├── wsgi.py                         # WSGI 入口
├── requirements.txt                # Python 依赖
├── pyproject.toml                  # 项目配置（Ruff 等）
└── package.json                    # 前端依赖
