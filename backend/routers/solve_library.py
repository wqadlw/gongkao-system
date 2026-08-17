"""
行测解题库路由 — 解题思路 / 方法模板 / 易错提醒 / 速算技巧，按模块归类
API 结构与 knowledge.py 一致：列表、按模块分组、CRUD、批量导入
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from database import get_db, SolveItem, Question

router = APIRouter(prefix="/api/solve-library", tags=["行测解题库"])


# ========== 序列化 ==========

def format_solve(item) -> dict:
    return {
        "id": item.id,
        "module": item.module,
        "solve_type": item.solve_type,
        "title": item.title,
        "content": item.content,
        "tags": item.tags,
        "source_question_id": item.source_question_id,
        "source": item.source,
        "difficulty": item.difficulty,
        "level1": item.level1, "level2": item.level2, "level3": item.level3,
        "level4": item.level4, "level5": item.level5,
        "card_title": item.card_title, "card_tags": item.card_tags, "card_summary": item.card_summary,
        "create_time": item.create_time.isoformat() if item.create_time else "",
        "update_time": item.update_time.isoformat() if item.update_time else "",
    }


# ========== 列表 + 筛选 ==========

@router.get("/list")
def list_items(
    module: Optional[str] = Query(None),
    solve_type: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    level1: Optional[str] = Query(None),
    level2: Optional[str] = Query(None),
    level3: Optional[str] = Query(None),
    level4: Optional[str] = Query(None),
    level5: Optional[str] = Query(None),
    sort: Optional[str] = Query(None, alias="sort"),
    page: int = Query(1, ge=1),
    page_size: int = Query(2000, ge=1, le=5000),
    db: Session = Depends(get_db),
):
    q = db.query(SolveItem)
    if module:
        q = q.filter(SolveItem.module == module)
    if solve_type:
        q = q.filter(SolveItem.solve_type == solve_type)
    for lvl, val in [("level1", level1), ("level2", level2), ("level3", level3),
                     ("level4", level4), ("level5", level5)]:
        if val:
            q = q.filter(getattr(SolveItem, lvl) == val)
    if keyword:
        kw = f"%{keyword}%"
        q = q.filter(
            (SolveItem.title.ilike(kw)) | (SolveItem.content.ilike(kw)) | (SolveItem.tags.ilike(kw))
        )

    total = q.count()
    if sort == "title":
        q = q.order_by(SolveItem.title)
    elif sort == "difficulty":
        q = q.order_by(SolveItem.difficulty.desc(), SolveItem.create_time.desc())
    elif sort == "updated":
        q = q.order_by(SolveItem.update_time.desc())
    else:
        q = q.order_by(SolveItem.create_time.desc())

    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [format_solve(k) for k in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


# ========== 按模块分组 ==========

@router.get("/by-module/{module}")
def by_module(module: str, db: Session = Depends(get_db)):
    items = db.query(SolveItem).filter(SolveItem.module == module).order_by(SolveItem.solve_type, SolveItem.create_time.desc()).all()
    grouped = {}
    for item in items:
        t = item.solve_type or "其他"
        grouped.setdefault(t, []).append(format_solve(item))
    return {"module": module, "groups": grouped, "total": len(items)}


# ========== 单条 ==========

@router.get("/{item_id}")
def get_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(SolveItem).filter(SolveItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="解题条目不存在")
    return format_solve(item)


# ========== 创建 & 更新模型 ==========

class SolveCreate(BaseModel):
    module: str = ""
    solve_type: str = "解题方法"
    title: str = ""
    content: str = ""
    tags: str = ""
    source_question_id: int = 0
    source: str = ""
    difficulty: int = 2
    level1: str = ""
    level2: str = ""
    level3: str = ""
    level4: str = ""
    level5: str = ""
    card_title: str = ""
    card_tags: str = ""
    card_summary: str = ""


class SolveUpdate(BaseModel):
    module: Optional[str] = None
    solve_type: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[str] = None
    source_question_id: Optional[int] = None
    source: Optional[str] = None
    difficulty: Optional[int] = None
    level1: Optional[str] = None
    level2: Optional[str] = None
    level3: Optional[str] = None
    level4: Optional[str] = None
    level5: Optional[str] = None
    card_title: Optional[str] = None
    card_tags: Optional[str] = None
    card_summary: Optional[str] = None


# ========== CRUD ==========

@router.post("/")
def create_item(body: SolveCreate, db: Session = Depends(get_db)):
    item = SolveItem(
        module=body.module, solve_type=body.solve_type,
        title=body.title, content=body.content,
        tags=body.tags, source_question_id=body.source_question_id,
        source=body.source, difficulty=body.difficulty,
        level1=body.level1 or "", level2=body.level2 or "", level3=body.level3 or "",
        level4=body.level4 or "", level5=body.level5 or "",
        card_title=body.card_title or "", card_tags=body.card_tags or "", card_summary=body.card_summary or "",
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": item.id, "message": "创建成功"}


@router.put("/{item_id}")
def update_item(item_id: int, body: SolveUpdate, db: Session = Depends(get_db)):
    existing = db.query(SolveItem).filter(SolveItem.id == item_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="解题条目不存在")
    update = body.dict(exclude_unset=True)
    for k, v in update.items():
        setattr(existing, k, v)
    existing.update_time = datetime.now()
    db.commit()
    return {"message": "更新成功"}


@router.delete("/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    existing = db.query(SolveItem).filter(SolveItem.id == item_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="解题条目不存在")
    db.delete(existing)
    db.commit()
    return {"message": "删除成功"}


# ========== 批量导入 ==========

class BatchSolveItem(BaseModel):
    module: str = ""
    solve_type: str = "解题方法"
    title: str = ""
    content: str = ""
    tags: str = ""
    source_question_id: int = 0
    source: str = ""
    difficulty: int = 2
    level1: str = ""
    level2: str = ""
    level3: str = ""
    level4: str = ""
    level5: str = ""
    card_title: str = ""
    card_tags: str = ""
    card_summary: str = ""


class BatchSolve(BaseModel):
    items: List[BatchSolveItem]


@router.post("/batch")
def batch_create(body: BatchSolve, db: Session = Depends(get_db)):
    created = 0
    errors = []
    for i, it in enumerate(body.items):
        try:
            item = SolveItem(
                module=it.module, solve_type=it.solve_type,
                title=it.title, content=it.content,
                tags=it.tags, source_question_id=it.source_question_id,
                source=it.source, difficulty=it.difficulty,
                level1=it.level1 or "", level2=it.level2 or "", level3=it.level3 or "",
                level4=it.level4 or "", level5=it.level5 or "",
                card_title=it.card_title or "", card_tags=it.card_tags or "", card_summary=it.card_summary or "",
            )
            db.add(item)
            created += 1
        except Exception as e:
            errors.append({"index": i, "error": str(e)})
    db.commit()
    return {"created": created, "total": len(body.items), "errors": errors}
