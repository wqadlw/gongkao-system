@echo off
chcp 65001 >nul
title 数据库备份

echo ════════════════════════════════════════════════════════════
echo   公考行测知识库系统 - 数据库备份
echo ════════════════════════════════════════════════════════════
echo.

cd /d "%~dp0"

set TIMESTAMP=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%

if not exist "data\backups" mkdir data\backups

if exist "data\gongkao.db" (
    copy "data\gongkao.db" "data\backups\gongkao_backup_%TIMESTAMP%.db" >nul
    echo 备份成功！
    echo 备份文件：data\backups\gongkao_backup_%TIMESTAMP%.db
) else (
    echo [错误] 未找到数据库文件 data\gongkao.db
)

echo.
pause
