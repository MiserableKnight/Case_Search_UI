@echo off
rem ���� Anaconda �ļ���ű�
call D:\anaconda3\Scripts\activate.bat D:\anaconda3
rem ����ָ���� Conda ����
call conda activate search
if %errorlevel% neq 0 (
    echo ���� Conda ����ʱ����
    pause
    exit /b %errorlevel%
)
rem �л���ָ��Ŀ¼
cd /d D:\Quant\Case_Search_UI
if %errorlevel% neq 0 (
    echo �л�Ŀ¼ʱ����
    pause
    exit /b %errorlevel%
)
rem ���� Python �ű�
python wsgi.py
if %errorlevel% neq 0 (
    echo ���� Python �ű�ʱ����
    pause
    exit /b %errorlevel%
)
rem ��ͣһ�£�����鿴������
pause  