"""公考行测知识库系统 v2 - 后端入口"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from database import init_all, DB_PATH
from routers import categories, prompts, questions, review, notes, study, stats, backup, exam, knowledge, solve_library, question_bank, anki_export, search, ocr, resources, mock, handbook, favorites

app = FastAPI(
    title="公考行测知识库系统 v2",
    description="纯本地离线公考行测学习系统 - JSON结构化解析版",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(categories.router)
app.include_router(prompts.router)
app.include_router(questions.router)
app.include_router(review.router)
app.include_router(notes.router)
app.include_router(study.router)
app.include_router(stats.router)
app.include_router(backup.router)
app.include_router(exam.router)
app.include_router(knowledge.router)
app.include_router(solve_library.router)
app.include_router(question_bank.router)
app.include_router(anki_export.router)
app.include_router(search.router)
app.include_router(ocr.router)
app.include_router(resources.router)
app.include_router(mock.router)
app.include_router(handbook.router)
app.include_router(favorites.router)


@app.on_event("startup")
def startup_event():
    print("=" * 60)
    print("  公考行测个人结构化知识库系统 v2.0")
    print("  纯本地离线 · JSON结构化解析 · 零AI联网")
    print("=" * 60)
    init_all()
    print(f"  数据库路径：{DB_PATH}")
    print("=" * 60)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "系统运行正常", "version": "2.0.0", "offline": True}


FRONTEND_DIST = os.environ.get("GK_FRONTEND_DIST") or os.path.join(BASE_DIR, "..", "frontend", "dist")
if os.path.exists(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")
    dist_root = os.path.realpath(FRONTEND_DIST)

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not Found")
        file_path = os.path.realpath(os.path.join(dist_root, full_path))
        # 防目录穿越：解析后的真实路径必须仍在 dist 目录内
        if file_path.startswith(dist_root + os.sep) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(dist_root, "index.html"))


if __name__ == "__main__":
    import uvicorn
    print("\n启动中... 浏览器访问 http://localhost:7080\n")
    uvicorn.run("main:app", host="127.0.0.1", port=7080, reload=False, log_level="info")
