#!/usr/bin/env bash
# 公考行测知识库系统 - Windows 桌面版打包脚本
# 前置：项目根 venv 已安装全部依赖 + pyinstaller；frontend/dist 已构建
# 用法：bash scripts/build_exe.sh
set -e
cd "$(dirname "$0")/.."
ROOT="$(pwd)"
PY="$ROOT/venv/Scripts/python.exe"
[ -f "$PY" ] || PY=python

echo "==> 构建前端"
(cd frontend && npm run build)

echo "==> 清理旧产物"
rm -rf packaging/dist packaging/build

echo "==> PyInstaller 打包（排除 cv2/pyarrow/matplotlib/torch，约 135MB）"
"$PY" -m PyInstaller \
  --name GongKaoDesktop \
  --distpath packaging/dist --workpath packaging/build --specpath packaging \
  --add-data "D:/AAAAA/gongkao-system-v2/frontend/dist;frontend_dist" \
  --paths backend \
  --hidden-import uvicorn.logging --hidden-import uvicorn.loops --hidden-import uvicorn.loops.auto \
  --hidden-import uvicorn.protocols --hidden-import uvicorn.protocols.http --hidden-import uvicorn.protocols.http.auto \
  --hidden-import uvicorn.protocols.http.h11_impl --hidden-import uvicorn.protocols.websockets --hidden-import uvicorn.protocols.websockets.auto \
  --hidden-import uvicorn.lifespan --hidden-import uvicorn.lifespan.on \
  --exclude-module cv2 --exclude-module pyarrow --exclude-module matplotlib --exclude-module torch \
  --collect-all rapidocr_onnxruntime \
  --console desktop_launcher.py

echo "==> 清理测试残留"
rm -f packaging/dist/GongKaoDesktop/*.log

echo "==> 完成：packaging/dist/GongKaoDesktop/"
echo "    整个 GongKaoDesktop 文件夹即绿色软件，拷给他人双击 GongKaoDesktop.exe 即用"
echo "    （其 data/ 子目录为个人数据，随使用生成）"
