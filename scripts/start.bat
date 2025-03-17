@echo off
rem 调用 Anaconda 的激活脚本
call D:\anaconda3\Scripts\activate.bat D:\anaconda3
rem 激活指定的 Conda 环境
call conda activate search
if %errorlevel% neq 0 (
    echo 激活 Conda 环境时出错
    pause
    exit /b %errorlevel%
)
rem 切换到指定目录
cd /d D:\Quant\Case_Search_UI
if %errorlevel% neq 0 (
    echo 切换目录时出错
    pause
    exit /b %errorlevel%
)
rem 运行 Python 脚本
python wsgi.py
if %errorlevel% neq 0 (
    echo 运行 Python 脚本时出错
    pause
    exit /b %errorlevel%
)
rem 暂停一下，方便查看输出结果
pause  