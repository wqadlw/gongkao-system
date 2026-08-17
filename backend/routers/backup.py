"""备份与导出路由 v2"""
import os
import json
import shutil
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db, DB_PATH, Question, Note, PromptTemplate, MockExam, StudyStage, ReviewLog, Category, DailyStat, ExamCountdown

router = APIRouter(prefix="/api/backup", tags=["备份导出"])


@router.get("/info")
def backup_info():
    if os.path.exists(DB_PATH):
        size = os.path.getsize(DB_PATH)
        return {
            "db_path": DB_PATH,
            "db_size": f"{size / 1024:.1f} KB",
            "last_modified": datetime.fromtimestamp(os.path.getmtime(DB_PATH)).strftime("%Y-%m-%d %H:%M:%S"),
        }
    return {"db_path": DB_PATH, "db_size": "0 KB", "last_modified": ""}


@router.post("/create")
def create_backup(db: Session = Depends(get_db)):
    backup_dir = os.path.join(os.path.dirname(DB_PATH), "backups")
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"gongkao_backup_{timestamp}.db")
    shutil.copy2(DB_PATH, backup_path)
    return {"message": "备份成功", "backup_path": backup_path, "backup_time": timestamp}


@router.get("/list")
def list_backups():
    backup_dir = os.path.join(os.path.dirname(DB_PATH), "backups")
    if not os.path.exists(backup_dir):
        return []
    backups = []
    for f in os.listdir(backup_dir):
        if f.endswith(".db"):
            path = os.path.join(backup_dir, f)
            stat = os.stat(path)
            backups.append({
                "filename": f,
                "size": f"{stat.st_size / 1024:.1f} KB",
                "time": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            })
    backups.sort(key=lambda x: x["time"], reverse=True)
    return backups


class RestoreRequest(BaseModel):
    filename: str


@router.post("/restore")
def restore_backup(req: dict, db: Session = Depends(get_db)):
    filename = req.get("filename")
    if not filename:
        raise HTTPException(status_code=400, detail="请指定备份文件名")
    backup_path = os.path.join(os.path.dirname(DB_PATH), "backups", filename)
    if not os.path.exists(backup_path):
        raise HTTPException(status_code=404, detail="备份文件不存在")
    shutil.copy2(backup_path, DB_PATH)
    return {"message": "恢复成功，请重启系统"}


@router.delete("/delete")
def delete_backup(filename: str, db: Session = Depends(get_db)):
    backup_path = os.path.join(os.path.dirname(DB_PATH), "backups", filename)
    if os.path.exists(backup_path):
        os.remove(backup_path)
        return {"message": "删除成功"}
    raise HTTPException(status_code=404, detail="备份文件不存在")


@router.get("/export/all")
def export_all(db: Session = Depends(get_db)):
    return {
        "export_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "questions": [{
            "question_raw": q.question_raw, "level1": q.level1, "level3": q.level3,
            "level4": q.level4, "level5": q.level5, "sub_point": q.sub_point,
            "answer": q.answer, "break_logic": q.break_logic,
            "step_detail": q.step_detail, "ai_raw_content": q.ai_raw_content,
        } for q in db.query(Question).all()],
        "notes": [{
            "level5": n.level5, "note_content": n.note_content,
        } for n in db.query(Note).all()],
        "prompts": [{
            "name": p.name, "type": p.type, "content": p.content,
        } for p in db.query(PromptTemplate).all()],
        "mocks": [{
            "name": m.name,
            "mock_date": m.mock_date.strftime("%Y-%m-%d") if m.mock_date else "",
            "total_score": m.total_score,
            "score_politics": m.score_politics, "score_common": m.score_common,
            "score_verbal": m.score_verbal, "score_quant": m.score_quant,
            "score_logic": m.score_logic, "score_data": m.score_data,
            "loss_knowledge": m.loss_knowledge, "loss_skill": m.loss_skill,
            "loss_careless": m.loss_careless, "loss_time": m.loss_time,
            "remark": m.remark,
        } for m in db.query(MockExam).all()],
    }


@router.get("/export/questions/md")
def export_questions_md(db: Session = Depends(get_db)):
    questions = db.query(Question).order_by(Question.create_time.desc()).all()
    lines = ["# 公考行测题目导出\n", f"导出时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n", f"题目总数：{len(questions)}\n", "---\n"]

    for q in questions:
        lines.append(f"## {q.level1} / {q.level3} / {q.level4 or ''} / {q.level5 or ''}\n")
        if q.sub_point:
            lines.append(f"**细分考点**：{q.sub_point}\n")
        lines.append(f"\n### 题干\n```\n{q.question_raw}\n```\n")
        if q.answer:
            lines.append(f"**正确答案**：{q.answer}\n")
        if q.break_logic:
            lines.append(f"\n### 破题逻辑\n{q.break_logic}\n")
        if q.normal_solve:
            lines.append(f"\n### 通用解法\n{q.normal_solve}\n")
        if q.quick_solve:
            lines.append(f"\n### 速算技巧\n{q.quick_solve}\n")
        if q.step_detail:
            lines.append(f"\n### 解题步骤\n{q.step_detail}\n")
        lines.append("---\n")

    content = "\n".join(lines)
    export_dir = os.path.join(os.path.dirname(DB_PATH), "exports")
    os.makedirs(export_dir, exist_ok=True)
    filename = f"questions_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    filepath = os.path.join(export_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return FileResponse(filepath, filename=filename, media_type="text/markdown")


@router.get("/export/notes/md")
def export_notes_md(db: Session = Depends(get_db)):
    notes = db.query(Note).order_by(Note.level5).all()
    lines = ["# 公考行测笔记导出\n", f"导出时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n", f"笔记总数：{len(notes)}\n", "---\n"]
    for n in notes:
        lines.append(n.note_content)
        lines.append("\n---\n")
    content = "\n".join(lines)
    export_dir = os.path.join(os.path.dirname(DB_PATH), "exports")
    os.makedirs(export_dir, exist_ok=True)
    filename = f"notes_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    filepath = os.path.join(export_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return FileResponse(filepath, filename=filename, media_type="text/markdown")
