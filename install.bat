@echo off
chcp 65001 >nul
title 公考行测知识库系统 v2 - 首次安装

echo ════════════════════════════════════════════════════════════
echo   公考行测知识库系统 v2 - 首次环境安装
echo ════════════════════════════════════════════════════════════
echo.

cd /d "%~dp0"

python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python！
    echo 请先安装 Python 3.9+ ：https://www.python.org/downloads/
    echo 安装时务必勾选 "Add Python to PATH"
    pause
    exit /b 1
)

echo [1/3] 创建虚拟环境...
python -m venv venv
call venv\Scripts\activate.bat

echo.
echo [2/3] 安装后端依赖...
pip install -r backend\requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

echo.
echo [3/3] 检查前端文件...
if not exist "frontend\dist\index.html" (
    echo 前端需要构建...
    where npm >nul 2>&1
    if errorlevel 1 (
        echo [警告] 未检测到npm，前端已预构建，跳过
    ) else (
        cd frontend
        npm install
        npm run build
        cd ..
    )
) else (
    echo 前端已就绪
)

echo.
echo ════════════════════════════════════════════════════════════
echo   安装完成！
echo   请运行 start.bat 启动系统
echo ════════════════════════════════════════════════════════════
pause
