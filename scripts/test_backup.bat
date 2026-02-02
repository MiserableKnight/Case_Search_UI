@echo off
chcp 65001 >nul

echo ========================================
echo      备份脚本快速测试工具
echo ========================================
echo.

cd /d "%~dp0.."
if errorlevel 1 (
    echo [错误] 无法切换到项目根目录
    pause
    exit /b 1
)

:: 检查必要文件
echo 检查必要文件...
if not exist "scripts\backup_manager.py" (
    echo [错误] backup_manager.py 不存在
    pause
    exit /b 1
)
if not exist "scripts\smart_backup_check.bat" (
    echo [错误] smart_backup_check.bat 不存在
    pause
    exit /b 1
)
if not exist "scripts\backup_config.ini" (
    echo [警告] backup_config.ini 不存在，将使用默认配置
)

echo [OK] 必要文件检查通过
echo.

:: 检查Python环境
echo 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Python环境未找到
    echo 请确保Python已安装并添加到PATH环境变量
    pause
    exit /b 1
)
echo [OK] Python环境检查通过
echo.

:: 测试导入
echo 测试备份管理器模块...
python -c "import sys; sys.path.append('.'); from scripts.backup_manager import BackupManager; print('模块导入成功')" 2>nul
if errorlevel 1 (
    echo [错误] 备份管理器模块导入失败
    pause
    exit /b 1
)
echo [OK] 模块导入测试通过
echo.

:: 显示配置信息
echo 当前配置信息:
python -c "import configparser; import os; config = configparser.ConfigParser(); config_file = 'scripts/backup_config.ini';
if os.path.exists(config_file):
    config.read(config_file);
    if 'BackupConfig' in config:
        print('  备份间隔:', config.get('BackupConfig', 'backup_interval_days', fallback='10'), '天');
        print('  强制备份:', config.get('BackupConfig', 'force_backup', fallback='False'));
        print('  详细输出:', config.get('BackupConfig', 'verbose_output', fallback='False'));
        print('  备份保留数量:', config.get('BackupConfig', 'keep_backups_count', fallback='5'), '个');
    else:
        print('  使用默认配置');
else:
    print('  配置文件不存在，使用默认配置')"
echo.

:: 运行智能备份检查（模拟模式）
echo 运行智能备份检查（测试模式）...
echo ========================================
python -c "from scripts.backup_manager import BackupManager;
import datetime;
try:
    backup_manager = BackupManager();
    current_size = backup_manager.get_current_data_size();
    last_backup_size = backup_manager.get_last_backup_size();
    print('数据目录:', backup_manager.source_dir.absolute());
    print('当前数据大小:', f'{current_size:,}', '字节');
    print('上次备份大小:', f'{last_backup_size:,}', '字节');
    should_backup = backup_manager.should_backup_based_on_size(10);
    print('是否需要备份:', '是' if should_backup else '否');
    if should_backup:
        print('建议执行备份操作');
    else:
        print('数据无变化或未达到备份间隔，跳过备份');
    print('备份目录:', backup_manager.backup_root.absolute());
    print('日志文件:', backup_manager.log_file.absolute());
except Exception as e:
    print('测试过程中发生错误:', str(e))"
echo ========================================
echo.

echo 测试完成！
echo.
echo 如需执行实际备份，请运行:
echo   scripts\smart_backup_check.bat
echo.
echo 如需设置定时任务，请以管理员身份运行:
echo   scripts\setup_10day_backup.ps1
echo.

pause
