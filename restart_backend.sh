#!/bin/bash
# 重启后端：先结束占用 7080 端口的旧进程，再用项目 venv 启动 uvicorn
pkill -f "uvicorn main:app" 2>/dev/null
sleep 1
nohup ./venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 7080 > backend.log 2>&1 &
echo "started pid $!"
