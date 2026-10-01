"""真题库对接路由 - 浏览 xingcezhenti 仓库并导入题目到本系统题库"""
import mimetypes
import os

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db, Question, BankImport, recalc_category_counts
from services import dataset_bank
from services.question_bank import (
    BANK_DIR, is_available, list_modules, parse_bank_file,
    safe_media_path, build_question_raw,
)

router = APIRouter(prefix="/api/question-bank", tags=["真题库对接"])


@router.get("/status")
def bank_status():
    return {
        "available": is_available(),
        "root": BANK_DIR,
        "modules": list_modules() if is_available() else [],
    }


@router.get("/files")
def bank_files(
    module: str,
    keyword: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
):
    if not is_available():
        raise HTTPException(status_code=404, detail="未找到 xingcezhenti 仓库目录")
    if module not in [m["dir"] for m in list_modules()]:
        raise HTTPException(status_code=404, detail="模块目录不存在")
    module_path = os.path.join(BANK_DIR, module)
    if not os.path.isdir(module_path):
        raise HTTPException(status_code=404, detail="模块目录不存在")
    files = [f for f in os.listdir(module_path) if f.endswith(".md")]
    files.sort()
    if keyword:
        files = [f for f in files if keyword in f]

    imported_map = {}
    imports = db.query(BankImport).filter(BankImport.module == module).all()
    for imp in imports:
        imported_map.setdefault(imp.source_file, 0)
        imported_map[imp.source_file] += 1

    items = []
    for name in files[(page - 1) * page_size: page * page_size]:
        items.append({
            "file": name,
            "title": name[:-3],
            "imported_count": imported_map.get(name, 0),
        })
    return {"items": items, "total": len(files), "page": page, "page_size": page_size}


@router.get("/file")
def bank_file_detail(module: str, name: str, db: Session = Depends(get_db)):
    if not is_available():
        raise HTTPException(status_code=404, detail="未找到 xingcezhenti 仓库目录")

    try:
        parsed = parse_bank_file(name, module)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    # 标记已导入的题目
    qids = [q["qid"] for q in parsed["questions"] if q["qid"]]
    imported_qids = set()
    if qids:
        rows = db.query(BankImport.bank_qid).filter(BankImport.bank_qid.in_(qids)).all()
        imported_qids = {r[0] for r in rows}
    for q in parsed["questions"]:
        q["imported"] = bool(q["qid"] and q["qid"] in imported_qids)
    return parsed


class BankImportRequest(BaseModel):
    module: str
    name: str                       # 试卷 md 文件名
    indexes: List[int] = []         # 要导入的题号（no）；为空表示全部未导入题目
    level1: str = ""
    level2: str = ""
    level3: str = ""
    level4: str = ""
    level5: str = ""


@router.post("/import")
def bank_import(req: BankImportRequest, db: Session = Depends(get_db)):
    if not is_available():
        raise HTTPException(status_code=404, detail="未找到 xingcezhenti 仓库目录")
    try:
        parsed = parse_bank_file(req.name, req.module)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    questions = parsed["questions"]
    if req.indexes:
        wanted = set(req.indexes)
        questions = [q for q in questions if q["no"] in wanted]

    # 去重：仓库 qid 已导入的跳过
    qids = [q["qid"] for q in questions if q["qid"]]
    existing = set()
    if qids:
        rows = db.query(BankImport.bank_qid).filter(BankImport.bank_qid.in_(qids)).all()
        existing = {r[0] for r in rows}

    imported, skipped = [], []
    for q in questions:
        if q["qid"] and q["qid"] in existing:
            skipped.append({"no": q["no"], "reason": "已导入"})
            continue
        qobj = Question(
            level1=req.level1, level2=req.level2, level3=req.level3,
            level4=req.level4, level5=req.level5,
            question_raw=build_question_raw(q),
            source=parsed["meta"].get("试卷", req.name[:-3]),
            difficulty=3,
            answer=q.get("answer", ""),
            normal_solve=q.get("analysis", ""),
            tags="真题" + (f"｜{q['subtype']}" if q["subtype"] else ""),
            ai_raw_content=q.get("material", ""),
        )
        db.add(qobj)
        db.flush()
        if q["qid"]:
            db.add(BankImport(
                bank_qid=q["qid"], question_id=qobj.id,
                source_file=req.name, module=req.module,
            ))
        imported.append({"no": q["no"], "question_id": qobj.id})

    if imported:
        recalc_category_counts(db)
    db.commit()
    return {"imported": imported, "skipped": skipped, "count": len(imported)}


# ========== 通用数据集导入（C-Eval / Xiezhi 等，放 data/question_sources/ 即可） ==========

@router.get("/datasets")
def bank_datasets():
    return {"items": dataset_bank.list_sources(), "dir": dataset_bank.SOURCES_DIR}


class DatasetImportRequest(BaseModel):
    file: str
    level1: str = ""      # 一级考点；为空则默认"常识判断"
    limit: int = 0        # 只导入前 N 题；0 表示全部


@router.post("/import-dataset")
def import_dataset(req: DatasetImportRequest, db: Session = Depends(get_db)):
    try:
        questions = dataset_bank.load_questions(req.file)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not questions:
        raise HTTPException(status_code=400, detail="数据集中没有可识别的题目")
    if req.limit and req.limit > 0:
        questions = questions[:req.limit]

    level1 = req.level1 or "常识判断"
    # 一次性取该来源已有题面集合，避免逐题查重的 N+1
    existing = {r[0] for r in db.query(Question.question_raw).filter(Question.source == req.file).all()}
    imported, skipped = 0, 0
    for q in questions:
        raw_parts = [q["stem"]]
        raw_parts.extend([f"- **{o['label']}**. {o['text']}" for o in q["options"]])
        raw = "\n".join(raw_parts)
        if raw in existing:
            skipped += 1
            continue
        db.add(Question(
            level1=level1,
            question_raw=raw,
            source=req.file,
            difficulty=3,
            answer=q["answer"],
            normal_solve=q.get("analysis", ""),
            tags="数据集" + (f"｜{q['subject']}" if q.get("subject") else ""),
        ))
        imported += 1

    if imported:
        recalc_category_counts(db)
    db.commit()
    return {"imported": imported, "skipped": skipped, "total": len(questions)}


@router.get("/media")
def bank_media(path: str = Query(...)):
    abs_path = safe_media_path(path)
    if not abs_path:
        raise HTTPException(status_code=404, detail="文件不存在")
    media_type = mimetypes.guess_type(abs_path)[0] or "application/octet-stream"
    return FileResponse(abs_path, media_type=media_type, headers={"Cache-Control": "public, max-age=86400"})
