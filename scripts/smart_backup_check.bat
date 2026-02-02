@echo off
setlocal enabledelayedexpansion

:: ============================================================================
:: 智能备份检查脚本 - 支持10天定期备份
:: 功能: 基于数据变化和时间间隔智能执行备份
:: 默认间隔: 10天
:: ============================================================================

echo ========================================
echo      智能备份检查工具 v2.0
echo ========================================
echo.

:: 设置默认参数
set DEFAULT_INTERVAL=10
set CONFIG_FILE=scripts\backup_config.ini
set LOG_FILE=data\backup.log

:: 解析命令行参数
set INTERVAL_DAYS=%DEFAULT_INTERVAL%
set FORCE_BACKUP=false
set VERBOSE=false

:parse_args
if "%~1"=="" goto :end_parse
if /i "%~1"=="-interval" (
    set INTERVAL_DAYS=%~2
    shift
    shift
    goto :parse_args
)
if /i "%~1"=="-force" (
    set FORCE_BACKUP=true
    shift
    goto :parse_args
)
if /i "%~1"=="-verbose" (
    set VERBOSE=true
    shift
    goto :parse_args
)
if /i "%~1"=="-help" goto :show_help
shift
goto :parse_args

:end_parse

:: 显示配置信息
echo 备份配置信息:
echo   - 备份间隔: %INTERVAL_DAYS% 天
echo   - 强制备份: %FORCE_BACKUP%
echo   - 详细模式: %VERBOSE%
echo.

:: 切换到项目根目录
cd /d "%~dp0.." 2>nul
if errorlevel 1 (
    echo [错误] 无法切换到项目根目录
    pause
    exit /b 1
)

:: 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Python环境未找到，请确保Python已安装并添加到PATH
    pause
    exit /b 1
)

:: 检查备份管理器模块
if not exist "scripts\backup_manager.py" (
    echo [错误] 备份管理器文件不存在: scripts\backup_manager.py
    pause
    exit /b 1
)

:: 构建Python命令
set PYTHON_CMD=from scripts.backup_manager import smart_backup_check;
if "%FORCE_BACKUP%"=="true" (
    set PYTHON_CMD=!PYTHON_CMD! backup_manager = __import__('scripts.backup_manager', fromlist=['BackupManager']).BackupManager();
    set PYTHON_CMD=!PYTHON_CMD! result = backup_manager.create_backup();
    set PYTHON_CMD=!PYTHON_CMD! if result: backup_manager.cleanup_old_backups()
) else (
    set PYTHON_CMD=!PYTHON_CMD! smart_backup_check(%INTERVAL_DAYS%)
)

:: 添加详细输出
if "%VERBOSE%"=="true" (
    set PYTHON_CMD=!PYTHON_CMD!; print('备份操作执行完成')
)

:: 执行备份检查
echo 开始执行智能备份检查...
echo.

python -c "!PYTHON_CMD!"

:: 检查执行结果
if errorlevel 1 (
    echo.
    echo [错误] 备份检查执行失败，错误代码: !errorlevel!
    echo 请查看日志文件获取详细信息: %LOG_FILE%
    endlocal
    pause
    exit /b 1
) else (
    echo.
    echo [成功] 备份检查执行完成
    if "%VERBOSE%"=="true" (
        echo 日志文件位置: %LOG_FILE%
        echo 备份记录位置: data\backup_records.json
    )
)

:: 显示完成信息
echo ========================================
echo 备份检查完成时间: %date% %time%
echo ========================================

endlocal
timeout /t 5
exit /b 0

:show_help
echo 智能备份检查工具使用说明:
echo.
echo 语法: smart_backup_check.bat [选项]
echo.
echo 选项:
echo   -interval N    设置备份间隔天数 (默认: 10)
echo   -force        强制执行备份，忽略检查
echo   -verbose      显示详细输出信息
echo   -help         显示此帮助信息
echo.
echo 示例:
echo   smart_backup_check.bat           # 使用默认10天间隔
echo   smart_backup_check.bat -interval 7  # 使用7天间隔
echo   smart_backup_check.bat -force     # 强制执行备份
echo   smart_backup_check.bat -verbose   # 显示详细信息
echo.
pause
exit /b 0
