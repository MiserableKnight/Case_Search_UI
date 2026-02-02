# 备份脚本使用指南

## 概述

本系统提供了一套完整的数据备份解决方案，支持智能备份检查和定期备份功能。

## 文件说明

### 核心文件
- `backup_manager.py` - 备份管理器核心模块
- `smart_backup_check.bat` - 智能备份检查脚本（已优化支持10天间隔）
- `backup_config.ini` - 备份配置文件
- `setup_10day_backup.ps1` - 10天定期备份任务设置脚本
- `test_backup.bat` - 备份脚本测试工具

### 辅助文件
- `run_backup.bat` - 基础备份脚本

## 使用方法

### 1. 智能备份检查（推荐）

#### 基本用法
```batch
# 使用默认10天间隔
scripts\smart_backup_check.bat

# 使用7天间隔
scripts\smart_backup_check.bat -interval 7

# 强制执行备份
scripts\smart_backup_check.bat -force

# 显示详细信息
scripts\smart_backup_check.bat -verbose

# 显示帮助信息
scripts\smart_backup_check.bat -help
```

#### 功能特点
- **智能检测**: 基于数据大小变化决定是否需要备份
- **间隔控制**: 默认10天间隔，避免频繁备份
- **自动清理**: 自动清理旧备份，保留最新5个
- **错误处理**: 完善的错误处理和日志记录

### 2. 设置定期备份任务

#### 10天定期备份（推荐）
以管理员身份运行PowerShell：
```powershell
scripts\setup_10day_backup.ps1
```

这将创建一个每10天运行一次的Windows计划任务。


### 3. 测试备份系统

运行测试工具：
```batch
scripts\test_backup.bat
```

测试工具将检查：
- 必要文件是否存在
- Python环境是否正常
- 模块导入是否成功
- 当前配置信息
- 备份需求状态

### 4. 配置文件说明

编辑 `scripts\backup_config.ini` 文件来自定义备份行为：

```ini
[BackupConfig]
# 备份间隔天数（默认：10天）
backup_interval_days = 10

# 是否启用强制备份模式（默认：false）
force_backup = false

# 是否启用详细输出（默认：false）
verbose_output = false

# 备份保留数量（默认：5个）
keep_backups_count = 5

# 源数据目录
source_directory = data/raw

# 备份存储目录
backup_directory = data/backup_data

# 日志文件路径
log_file_path = data/backup.log

# 备份记录文件路径
record_file_path = data/backup_records.json
```

## 工作原理

### 智能备份逻辑
1. **数据大小检查**: 比较当前数据大小与上次备份时的大小
2. **时间间隔检查**: 检查距离上次备份是否达到最小间隔天数
3. **备份决策**: 满足以下任一条件即执行备份：
   - 数据大小发生变化
   - 达到最小备份间隔天数

### 备份流程
1. 检查源目录是否存在且不为空
2. 创建带时间戳的备份目录
3. 复制数据文件到备份目录
4. 更新备份记录
5. 清理旧备份（保留指定数量）

## 管理备份

### 查看备份
备份文件存储在 `data/backup_data` 目录，按日期组织：
```
data/backup_data/
├── 20250815_210548/
├── 20250820/
├── 20250820_154556/
└── ...
```

### 查看备份记录
备份记录存储在 `data/backup_records.json` 文件中，包含：
- 备份时间戳
- 备份路径
- 备份状态
- 数据大小

### 查看日志
详细日志记录在 `data/backup.log` 文件中。

## 故障排除

### 常见问题

1. **Python环境问题**
   ```
   [错误] Python环境未找到
   ```
   解决方案：确保Python已安装并添加到PATH环境变量

2. **文件权限问题**
   ```
   [错误] 无法切换到项目根目录
   ```
   解决方案：确保有足够的文件系统权限

3. **模块导入失败**
   ```
   [错误] 备份管理器模块导入失败
   ```
   解决方案：检查backup_manager.py文件是否存在且完整

4. **备份检查跳过**
   ```
   数据无变化或间隔时间过短，跳过备份
   ```
   这是正常行为，表示数据未发生变化

### 手动清理备份
如果需要手动清理备份，删除 `data/backup_data` 目录中的相应文件夹即可。

## 高级用法

### 自定义备份间隔
修改 `smart_backup_check.bat` 中的默认间隔：
```batch
set DEFAULT_INTERVAL=10
```

### 修改备份保留数量
在 `backup_config.ini` 中修改：
```ini
keep_backups_count = 5
```

### 强制备份
无论数据是否变化，都可以强制执行备份：
```batch
scripts\smart_backup_check.bat -force
```

## 监控和维护

### 定期检查
建议每月运行一次测试工具：
```batch
scripts\test_backup.bat
```

### 日志监控
定期检查 `data/backup.log` 文件，确保备份正常运行。

### 存储空间监控
监控 `data/backup_data` 目录大小，确保有足够的存储空间。

## 技术支持

如遇到问题，请：
1. 检查日志文件 `data/backup.log`
2. 运行测试工具 `scripts\test_backup.bat`
3. 确认Python环境正常
4. 检查文件权限

---

*注意：所有脚本都支持中文路径和文件名，使用UTF-8编码。*
