"""统一收藏中心路由 — 跨题目/资料/知识点/解题条目的收藏、列表与批量状态"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db, Favorite, Question, Resource, Knowledge, SolveItem

router = APIRouter(prefix="/api/favorites", tags=["收藏中心"])

OBJ_TYPES = ("question", "resource", "knowledge", "solve_item")


def _resolve(db: Session, obj_type: str, obj_id: int):
    """按类型取展示数据；对象不存在返回 None"""
    if obj_type == "question":
        q = db.query(Question).filter(Question.id == obj_id).first()
        if not q:
            return None
        stem = (q.question_raw or "").replace("\n", " ")[:80]
        return {
            "title": stem or f"题目 #{q.id}",
            "subtitle": " / ".join(x for x in (q.level1, q.level3, q.level4) if x),
            "badge": q.answer or "",
            "route": f"/question/{q.id}",
        }
    if obj_type == "resource":
        r = db.query(Resource).filter(Resource.id == obj_id).first()
        if not r:
            return None
        return {
            "title": r.title,
            "subtitle": r.sub_path or r.category,
            "badge": r.resource_type,
            "route": f"/resource-library",
        }
    if obj_type == "knowledge":
        k = db.query(Knowledge).filter(Knowledge.id == obj_id).first()
        if not k:
            return None
        return {"title": k.title, "subtitle": f"{k.module} · {k.kg_type}", "badge": k.kg_type, "route": "/knowledge"}
    if obj_type == "solve_item":
        s = db.query(SolveItem).filter(SolveItem.id == obj_id).first()
        if not s:
            return None
        return {"title": s.title, "subtitle": f"{s.module} · {s.solve_type}", "badge": s.solve_type, "route": "/solve-library"}
    return None


class ToggleRequest(BaseModel):
    obj_type: str
    obj_id: int
    note: str = ""


@router.post("/toggle")
def toggle_favorite(req: ToggleRequest, db: Session = Depends(get_db)):
    if req.obj_type not in OBJ_TYPES:
        raise HTTPException(status_code=400, detail="无效的收藏对象类型")
    row = db.query(Favorite).filter(
        Favorite.obj_type == req.obj_type, Favorite.obj_id == req.obj_id).first()
    if row:
        db.delete(row)
        favorited = False
    else:
        if _resolve(db, req.obj_type, req.obj_id) is None:
            raise HTTPException(status_code=404, detail="收藏对象不存在")
        db.add(Favorite(obj_type=req.obj_type, obj_id=req.obj_id,
                        note=req.note, create_time=datetime.now()))
        favorited = True

    # 题目：双向同步 questions.is_favorite（既有列表筛选体系继续可用）
    if req.obj_type == "question":
        q = db.query(Question).filter(Question.id == req.obj_id).first()
        if q:
            q.is_favorite = favorited
    db.commit()
    return {"favorited": favorited}


@router.post("/status")
def favorite_status(payload: dict, db: Session = Depends(get_db)):
    """批量查询星标态：{obj_type, ids:[...]} → {str(id): bool}"""
    obj_type = payload.get("obj_type", "")
    ids = [int(i) for i in (payload.get("ids") or [])][:500]
    if obj_type not in OBJ_TYPES or not ids:
        return {"status": {}}
    rows = db.query(Favorite.obj_id).filter(
        Favorite.obj_type == obj_type, Favorite.obj_id.in_(ids)).all()
    hit = {r[0] for r in rows}
    if obj_type == "question":  # 题目兼容旧字段
        for qid, in db.query(Question.id).filter(Question.id.in_(ids), Question.is_favorite == True).all():  # noqa: E712
            hit.add(qid)
    return {"status": {str(i): (i in hit) for i in ids}}


@router.get("")
def favorite_list(
    obj_type: str = Query("question"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    if obj_type not in OBJ_TYPES:
        raise HTTPException(status_code=400, detail="无效的收藏对象类型")
    base = db.query(Favorite).filter(Favorite.obj_type == obj_type)
    total = base.count()
    rows = (base.order_by(Favorite.create_time.desc())
            .offset((page - 1) * page_size).limit(page_size).all())
    items = []
    for f in rows:
        info = _resolve(db, obj_type, f.obj_id)
        if not info:  # 对象已被删除，清理收藏
            db.delete(f)
            continue
        items.append({"favorite_id": f.id, "obj_id": f.obj_id,
                      "note": f.note, "collect_time": f.create_time.strftime("%Y-%m-%d %H:%M"),
                      **info})
    db.commit()
    counts = {t: db.query(Favorite).filter(Favorite.obj_type == t).count() for t in OBJ_TYPES}
    return {"items": items, "total": total, "page": page, "page_size": page_size, "counts": counts}
