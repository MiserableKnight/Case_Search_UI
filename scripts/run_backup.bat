@echo off
echo 开始执行备份...
cd /d "%~dp0.."
python scripts/backup_manager.py
echo.
echo 备份完成于 %date% %time%
echo 请查看上方日志信息了解详细情况
echo 备份文件位置: data\backup_data
echo 备份日志位置: data\backup.log
echo 备份记录位置: data\backup_records.json
pause
