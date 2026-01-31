# 项目设置完整指南

**最后更新**: 2026-01-31
**状态**: ✅ 配置优化完成，依赖已安装

---

## 📋 项目当前状态

### ✅ 已完成的配置

1. **虚拟环境**
   - 路径：`.venv/`
   - Python 版本：3.10.11
   - 状态：已激活，所有依赖已安装

2. **代码质量工具**
   - Ruff 0.9.14（已安装）
   - Pre-commit 4.5.1（已安装）
   - 配置文件：`pyproject.toml`

3. **应用依赖**
   - Flask 2.3.3
   - Pandas 2.1.0
   - NumPy 1.24.3
   - 所有其他依赖已安装 ✅

4. **应用状态**
   - 测试运行：✅ 成功
   - 访问地址：http://127.0.0.1:5000
   - 功能验证：✅ 正常响应

---

## 🚀 快速启动

### 方式1：使用激活脚本（推荐）

```bash
# Windows
activate.bat
python wsgi.py

# Linux/macOS
source .venv/bin/activate
python wsgi.py
```

### 方式2：使用启动脚本（Windows）

```bash
scripts\run.bat
```

该脚本会：
1. 自动激活虚拟环境
2. 检查 Python 环境
3. 执行智能备份检查
4. 启动 Flask 应用

---

## 📦 已安装的包

### 核心依赖（requirements.txt）

```
flask==2.3.3
flask-cors==4.0.0
pandas==2.1.0
pyarrow==14.0.1
python-dotenv==1.0.0
numpy==1.24.3
scikit-learn==1.3.0
jieba==0.42.1
requests==2.31.0
xlrd>=2.0.1
openpyxl>=3.0.0
APScheduler==3.10.4
```

### 开发依赖（requirements-dev.txt）

```
ruff>=0.9.0
pre-commit>=4.0.0
```

---

## 🛠️ 开发工具使用

### 代码检查

```bash
# 检查代码质量
ruff check .

# 自动修复问题
ruff check --fix .

# 查看统计信息
ruff check . --statistics
```

**当前状态**: 3 个问题（非阻塞，不影响运行）

### 代码格式化

```bash
# 格式化所有代码
ruff format .

# 检查格式（不修改文件）
ruff format . --check
```

**当前状态**: 21 个文件已格式化 ✅

### Pre-commit Hooks（可选）

```bash
# 安装
pre-commit install

# 运行所有检查
pre-commit run --all-files

# 提交前自动运行
git commit -m "your message"
```

---

## 🔧 虚拟环境管理

### 激活/停用

```bash
# 激活
activate.bat              # Windows
source .venv/bin/activate # Linux/macOS

# 停用
deactivate.bat            # Windows
deactivate                # Linux/macOS
```

### 重建虚拟环境

```bash
# 删除现有环境
rm -rf .venv  # Linux/macOS
rmdir /s .venv # Windows

# 创建新环境
python -m venv .venv

# 安装依赖
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

---

## 📝 常用命令

### 运行应用

```bash
# 直接运行
python wsgi.py

# 指定端口
set PORT=8000
python wsgi.py

# 指定环境
set FLASK_ENV=production
python wsgi.py
```

### 代码质量

```bash
# 检查 + 格式化
ruff check --fix . && ruff format .

# 查看问题
ruff check . --output-format=concise

# 只查看特定文件
ruff check app/__init__.py
```

### 数据备份

```bash
# 智能备份检查（自动）
python -c "from scripts.backup_manager import smart_backup_check; smart_backup_check(1)"

# 手动备份
python scripts\backup_manager.py
```

---

## 🐛 故障排除

### 问题1：ModuleNotFoundError

**原因**: 虚拟环境未激活或依赖未安装

**解决**:
```bash
activate.bat
pip install -r requirements.txt
```

### 问题2：端口被占用

**错误**: `Address already in use`

**解决**:
```bash
# 方式1：查找并关闭占用进程
netstat -ano | findstr :5000
taskkill /F /PID <进程ID>

# 方式2：使用其他端口
set PORT=8000
python wsgi.py
```

### 问题3：数据文件缺失

**错误**: `FileNotFoundError: case.parquet`

**解决**:
- 检查 `data/raw/` 目录
- 确保数据文件存在
- 参考 `docs/` 下的文档准备数据

### 问题4：Ruff 检查失败

**错误**: Ruff 报告大量错误

**解决**:
```bash
# 自动修复
ruff check --fix .

# 格式化
ruff format .

# 查看详情
ruff check . --output-format=full
```

---

## 📊 项目结构

```
Case_Search_UI/
├── .venv/                    # 虚拟环境 ✅
├── app/                      # 应用代码
├── data/                     # 数据文件
│   ├── raw/                  # 原始数据
│   ├── processed/            # 处理后数据
│   └── temp/                 # 临时文件
├── docs/                     # 文档
├── logs/                     # 日志文件
├── scripts/                  # 工具脚本
├── tests/                    # 测试代码（待添加）
├── .editorconfig             # 编辑器配置 ✅
├── .gitignore                # Git 忽略规则 ✅
├── .python-version           # Python 版本 ✅
├── .pre-commit-config.yaml   # Pre-commit 配置 ✅
├── pyproject.toml            # 项目配置 ✅
├── requirements.txt          # 生产依赖 ✅
├── requirements-dev.txt      # 开发依赖 ✅
├── wsgi.py                   # 应用入口
├── activate.bat              # 激活脚本 ✅
└── deactivate.bat            # 停用脚本 ✅
```

---

## 🎯 下一步

### 开发前检查

- [x] 虚拟环境已创建
- [x] 依赖已安装
- [x] 应用可以运行
- [x] 代码工具已配置

### 可选优化

1. **安装 pre-commit hooks**
   ```bash
   pre-commit install
   ```

2. **修复剩余的 3 个代码问题**
   - app/__init__.py:172 - 未使用的变量
   - app/api/data_source_routes.py:250 - 不必要的 list() 调用
   - app/core/__init__.py:5 - 已弃用的导入

3. **添加测试**
   - 创建 `tests/` 目录
   - 编写单元测试
   - 配置 pytest

---

## 📚 相关文档

- [开发指南](./DEVELOPMENT.md) - 详细的开发说明
- [优化总结](./OPTIMIZATION_SUMMARY.md) - 配置优化详情
- [代码质量分析](./code_quality_analysis_20260131.md) - 项目分析报告
- [README](../README.md) - 项目概述

---

## ✨ 配置优化亮点

1. **统一配置** - 所有工具配置集中在 `pyproject.toml`
2. **工具简化** - 从 4 个工具简化到 1 个 Ruff
3. **标准化** - 符合 Python 社区最佳实践
4. **开发体验** - 完善的脚本和文档
5. **代码质量** - 从 251 个问题减少到 3 个

---

**状态**: ✅ 项目配置已优化完成，可以正常开发和运行！
