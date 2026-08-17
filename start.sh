#!/bin/bash
cd "$(dirname "$0")"

echo "════════════════════════════════════════════════════════════"
echo "  公考行测个人结构化知识库系统 v2.0"
echo "════════════════════════════════════════════════════════════"

if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到python3"
    exit 1
fi

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

pip show fastapi &> /dev/null || pip install -r backend/requirements.txt -q

if [ ! -f "frontend/dist/index.html" ]; then
    echo "前端未构建，请先运行: cd frontend && npm install && npm run build"
    exit 1
fi

echo "浏览器访问：http://localhost:7080"
(sleep 3 && (xdg-open http://localhost:7080 || open http://localhost:7080) 2>/dev/null) &

cd backend
python main.py
