@echo off
rem Project startup script

echo Starting script execution...

echo Activating virtual environment...
call search\Scripts\activate.bat

echo Virtual environment activated
echo Current Python path:
where python

echo Changing to project root directory...
cd /d "%~dp0.."

echo Starting smart backup check...
python -c "from scripts.backup_manager import smart_backup_check; smart_backup_check(1)"
echo Smart backup check completed.

echo Starting Flask application...
python wsgi.py

echo Press any key to exit...
pause
