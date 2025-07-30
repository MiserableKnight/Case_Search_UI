@echo off
rem Project startup script

echo Starting script execution...

echo Activating virtual environment...
call D:\Code\Case_Search_UI\search\Scripts\activate.bat

echo Virtual environment activated
echo Current Python path:
where python

echo Changing to project root directory...
cd /d D:\Code\Case_Search_UI

echo Starting Flask application...
python wsgi.py

echo Press any key to exit...
pause
