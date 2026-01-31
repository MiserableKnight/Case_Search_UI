@echo off
rem Project startup script

echo Starting script execution...

echo Changing to project root directory...
cd /d "%~dp0.."

echo Activating virtual environment...
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
    echo Virtual environment activated successfully
) else (
    echo Virtual environment not found, using system Python
    echo Please run: activate.bat
)

echo Current Python path:
where python

echo Checking Python packages...
python -c "import sys; print('Python executable:', sys.executable)"
python -c "import numpy; print('numpy version:', numpy.__version__)" 2>nul || echo numpy not found

echo Starting smart backup check...
python -c "from scripts.backup_manager import smart_backup_check; smart_backup_check(1)"
echo Smart backup check completed.

echo Starting Flask application...
python wsgi.py

echo Press any key to exit...
pause
