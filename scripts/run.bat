@echo off
rem 项目启动脚本

rem 激活 Anaconda 环境
call D:\anaconda3\Scripts\activate.bat D:\anaconda3

rem 激活指定的 Conda 环境
call conda activate search
if %errorlevel% neq 0 (
    echo Conda 环境激活失败
    pause
    exit /b %errorlevel%
)

rem 切换到项目目录
cd /d D:\Quant\Case_Search_UI
if %errorlevel% neq 0 (
    echo 切换目录失败
    pause
    exit /b %errorlevel%
)

rem 启动 Flask 应用
python wsgi.py
if %errorlevel% neq 0 (
    echo 应用启动失败
    pause
    exit /b %errorlevel%
)

rem 保持窗口打开以查看输出
pause  