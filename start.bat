@echo off
chcp 65001 >nul
title 公考行测知识库系统 v2 - 一键启动

echo ════════════════════════════════════════════════════════════
echo   公考行测个人结构化知识库系统 v2.0
echo   纯本地离线 · Markdown结构化解析 · 零AI联网
echo ════════════════════════════════════════════════════════════
echo.

cd /d "%~dp0"

REM ========== 检查Python ==========
echo [1/5] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python 3.9+
    echo 下载地址：https://www.python.org/downloads/
    echo 安装时请勾选 "Add Python to PATH"
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo   Python版本：%PYVER%

REM ========== 创建虚拟环境 ==========
echo.
echo [2/5] 检查虚拟环境...
if not exist "venv" (
    echo   正在创建虚拟环境...
    python -m venv venv
    if errorlevel 1 (
        echo [错误] 虚拟环境创建失败
        pause
        exit /b 1
    )
    echo   虚拟环境创建成功
) else (
    echo   虚拟环境已存在
)

REM ========== 激活虚拟环境 ==========
call venv\Scripts\activate.bat

REM ========== 安装依赖 ==========
echo.
echo [3/5] 检查依赖...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo   正在安装后端依赖...
    pip install -r backend\requirements.txt -q
    if errorlevel 1 (
        echo [错误] 依赖安装失败，请使用国内镜像：
        echo   pip install -r backend\requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
        pause
        exit /b 1
    )
    echo   依赖安装成功
) else (
    echo   依赖已安装
)

REM ========== 检查前端构建 ==========
echo.
echo [4/5] 检查前端文件...
if not exist "frontend\dist\index.html" (
    echo   [警告] 前端未构建，正在尝试构建...
    where npm >nul 2>&1
    if errorlevel 1 (
        echo [错误] 未检测到npm，请安装Node.js 16+
        echo 下载地址：https://nodejs.org/
        pause
        exit /b 1
    )
    cd frontend
    npm install
    npm run build
    cd ..
    echo   前端构建完成
) else (
    echo   前端文件就绪
)

REM ========== 启动服务 ==========
echo.
echo [5/5] 启动系统...
echo ════════════════════════════════════════════════════════════
echo   系统启动中...
echo   浏览器访问：http://localhost:7080
echo   按 Ctrl+C 可停止服务
echo ════════════════════════════════════════════════════════════
echo.

REM 延迟3秒后打开浏览器
start /b cmd /c "timeout /t 3 /nobreak >nul && start http://localhost:7080"

REM 启动后端
cd backend
python main.py
pause
