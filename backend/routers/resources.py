"""资料库路由 — 公考资料（思维导图/外链指南）的浏览、预览与下载"""
import os

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db, Resource, DB_PATH

router = APIRouter(prefix="/api/resources", tags=["资料库"])

# 资料文件根目录（与数据库同目录下的 resources/，即项目 data/resources）
RESOURCES_DIR = os.path.normpath(os.path.join(os.path.dirname(DB_PATH), "resources"))


def _safe_resource_path(rel_path: str) -> str:
    """相对路径 → 限定在 data/resources 内的绝对路径；非法返回空串"""
    if not rel_path or "\x00" in rel_path:
        return ""
    rel_norm = rel_path.replace("\\", "/").lstrip("/")
    abs_path = os.path.realpath(os.path.join(RESOURCES_DIR, rel_norm))
    root = os.path.realpath(RESOURCES_DIR)
    if not abs_path.startswith(root + os.sep) or not os.path.isfile(abs_path):
        return ""
    return abs_path


class ResourceBatch(BaseModel):
    items: list


@router.get("/categories")
def resource_categories(db: Session = Depends(get_db)):
    """一级分类与计数"""
    rows = db.query(Resource.category).all()
    counts = {}
    for (cat,) in rows:
        counts[cat] = counts.get(cat, 0) + 1
    order = ["行测", "申论", "面试", "经验指南"]
    items = [{"name": c, "count": counts[c]} for c in order if c in counts]
    items += [{"name": c, "count": n} for c, n in sorted(counts.items()) if c not in order]
    return {"items": items, "total": sum(counts.values())}


@router.get("/list")
def resource_list(
    category: Optional[str] = None,
    keyword: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(24, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Resource)
    if category:
        query = query.filter(Resource.category == category)
    if keyword:
        query = query.filter(Resource.title.contains(keyword) | Resource.sub_path.contains(keyword))
    total = query.count()
    rows = query.order_by(Resource.category, Resource.sub_path, Resource.title).offset(
        (page - 1) * page_size).limit(page_size).all()
    return {
        "items": [{
            "id": r.id, "category": r.category, "sub_path": r.sub_path,
            "title": r.title, "description": r.description,
            "resource_type": r.resource_type,
            "image_path": r.image_path, "file_path": r.file_path,
            "source_url": r.source_url, "source": r.source,
        } for r in rows],
        "total": total, "page": page, "page_size": page_size,
    }


@router.get("/image")
def resource_image(path: str = Query(...)):
    abs_path = _safe_resource_path(path)
    if not abs_path:
        raise HTTPException(status_code=404, detail="图片不存在")
    from mimetypes import guess_type
    return FileResponse(abs_path, media_type=guess_type(abs_path)[0] or "image/png")


@router.get("/file")
def resource_file(path: str = Query(...)):
    abs_path = _safe_resource_path(path)
    if not abs_path:
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(abs_path, filename=os.path.basename(abs_path))


@router.post("/batch")
def resource_batch(data: ResourceBatch, db: Session = Depends(get_db)):
    """批量导入（脚本产出清单后调用）；以 (title, sub_path) 判重"""
    created = skipped = 0
    for it in data.items:
        title = (it.get("title") or "").strip()
        sub_path = (it.get("sub_path") or "").strip()
        category = (it.get("category") or "").strip()
        if not title or not category:
            skipped += 1
            continue
        exists = db.query(Resource.id).filter(
            Resource.title == title, Resource.sub_path == sub_path).first()
        if exists:
            skipped += 1
            continue
        db.add(Resource(
            category=category, sub_path=sub_path, title=title,
            description=it.get("description", ""),
            resource_type=it.get("resource_type", "mindmap"),
            image_path=it.get("image_path", ""),
            file_path=it.get("file_path", ""),
            source_url=it.get("source_url", ""),
            source=it.get("source", ""),
        ))
        created += 1
    db.commit()
    return {"created": created, "skipped": skipped}
