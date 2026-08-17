@echo off
chcp 65001 >nul
title 停止公考行测系统

echo 正在停止系统服务...
taskkill /f /im python.exe 2>nul
if errorlevel 1 (
    echo 没有找到运行中的Python进程
) else (
    echo 系统服务已停止
)
timeout /t 2 /nobreak >nul
