# CLAUDE.md

此文件为Claude Code (claude.ai/code) 在本代码仓库中的工作指南。

## 项目概览

**历史问题查询系统** - 基于Flask的Web应用，用于搜索和分析航空维修历史数据。系统支持对快响信息、工程文件、手册、故障报告等多种数据源的智能化搜索。

## 系统架构

### 技术栈
- **后端**: Flask 2.3.3 + Python 3.10
- **前端**: 原生JavaScript + Element UI组件
- **数据存储**: PyArrow 14.0.1处理Parquet文件
- **数据处理**: Pandas 2.1.0, scikit-learn 1.3.0用于相似度搜索
- **任务调度**: APScheduler 3.10.4负责后台清理

### 核心组件

#### 应用结构 (`app/`)
- **工厂模式**: `create_app()` 在 `app/__init__.py:56` 初始化Flask应用
- **蓝图组织**:
  - 主路由 (`app/routes.py:32`)
  - API路由 (`app/api/__init__.py`)
  - 数据导入路由 (`app/api/data_import_routes/`)

#### 数据流向
1. **数据源**: `data/raw/`中的Parquet文件 (case.parquet, engineering.parquet, faults.parquet, manual.parquet)
2. **处理**: 按需缓存加载到Pandas DataFrame (`app/__init__.py:128`)
3. **服务层**: 模块化服务层 (`app/services/`) 处理业务逻辑
4. **API接口**: RESTful端点，统一以`/api/`为前缀

#### 核心服务
- **CaseService**: 快响数据操作
- **EngineeringService**: 工程文件处理
- **FaultReportService**: 故障报告分析
- **ManualService**: 手册文档处理
- **RAndIRecordService**: 部件拆换记录处理
- **SimilarityService**: 基于向量的相似度搜索
- **AnonymizationService**: 敏感数据脱敏

## 开发命令

### 环境配置
```bash
# 创建并激活虚拟环境
conda create -n search python=3.10
conda activate search
pip install -r requirements.txt

# 安装开发依赖
pip install -r requirements-dev.txt
```

### 启动应用
```bash
# 标准启动方式
python wsgi.py

# Windows批处理脚本
scripts\run.bat

# 使用环境变量启动
FLASK_ENV=development python wsgi.py
```

### 代码质量工具
```bash
# 代码格式化
black app/
isort app/

# 类型检查
mypy app/

# 代码检查
flake8 app/

# 运行测试 (如有测试)
pytest tests/
```

### 数据管理
```bash
# 数据备份
python scripts/backup_manager.py

# Windows设置定时备份
powershell -ExecutionPolicy Bypass -File scripts/setup_backup_task.ps1
```

## 配置说明

### 环境变量
- `FLASK_ENV`: 设置为'development'、'production'或'testing'
- `FLASK_SECRET_KEY`: 会话加密密钥
- `PORT`: 服务端口号 (默认: 5000)

### 文件路径
- **数据目录**: `data/`
- **原始数据**: `data/raw/` (Parquet文件)
- **处理数据**: `data/processed/`
- **临时文件**: `data/temp/` (通过调度器自动清理)
- **日志文件**: `logs/app.log` (10MB轮转，保留5个备份)

## 关键API端点

### 搜索操作
- `GET /api/search` - 跨数据源通用搜索
- `POST /api/similarity/batch` - 批量相似度搜索
- `GET /api/data-sources/{source}/columns` - 获取列元数据

### 数据导入
- `POST /api/data-import/upload` - 文件上传端点
- `POST /api/data-import/confirm` - 预览后确认导入
- `GET /api/data-import/progress/{task_id}` - 导入进度跟踪

### 工具端点
- `POST /api/anonymize` - 文本脱敏服务
- `GET /api/sensitive-words` - 敏感词管理

## 开发规范

### 添加新数据源
1. 在 `app/core/data_processors/` 添加处理器
2. 在 `app/services/data_services/` 创建服务
3. 在 `app/api/data_import_routes/` 添加路由
4. 在 `app/__init__.py:44` 更新配置 (DATA_SOURCES)

### 前端集成
- 静态文件位于 `app/static/`
- 模板文件位于 `app/templates/`
- API调用使用相对路径 (如 `/api/search`)
- JavaScript模块位于 `app/static/js/methods/`

### 异常处理
- 通过 `ErrorService` (`app/services/error_service.py`) 统一处理
- 自定义异常在 `app/core/error_handler.py` 中定义
- 全局异常处理器在 `app/__init__.py:199` 中配置

## 性能注意事项
- **数据加载**: 延迟加载 + 内存缓存
- **文件大小**: 配置16MB上传限制
- **内存**: 浏览器存储警告5-10MB
- **分析**: 分析页面建议单批次≤300条记录

## 安全特性
- **数据脱敏**: 自动敏感数据掩码处理
- **CSP头**: 在 `app/config/default.py:45` 中配置
- **文件验证**: 扩展名和大小检查
- **输入清理**: 模板中防止XSS攻击