@echo off
echo Starting backup process...
cd /d "%~dp0.."
python scripts/backup_manager.py
echo.
echo Backup completed at %date% %time%
echo Please check the log information above for details
echo Backup files location: data\backup_data
echo Backup log location: data\backup.log
echo Backup records location: data\backup_records.json
pause
