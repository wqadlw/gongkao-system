"""资料库路由 — 公考资料（思维导图/外链指南）的浏览、预览与下载"""
import json
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


@router.get("/tree")
def resource_tree(db: Session = Depends(get_db)):
    """三级层级聚合：分类 → 模块 → 大类/考点组（按计数降序），驱动左侧导航树"""
    rows = db.query(Resource.category, Resource.sub_path).all()
    tree = {}
    for cat, sub in rows:
        node = tree.setdefault(cat, {"count": 0, "children": {}})
        node["count"] += 1
        parts = [p for p in (sub or "").split("/") if p]
        if parts:
            lvl1 = node["children"].setdefault(parts[0], {"count": 0, "children": {}})
            lvl1["count"] += 1
            if len(parts) > 1:
                lvl2 = lvl1["children"].setdefault("/".join(parts[1:]), {"count": 0, "children": {}})
                lvl2["count"] += 1

    def sort_children(children_map):
        return [
            {"name": name, "count": info["count"],
             "children": sort_children(info["children"])}
            for name, info in sorted(children_map.items(), key=lambda x: -x[1]["count"])
        ]

    order = ["行测", "申论", "面试", "考点精讲", "材料档案", "经验指南"]
    items = []
    for cat in order:
        if cat in tree:
            items.append({"name": cat, "count": tree[cat]["count"], "children": sort_children(tree[cat]["children"])})
    for cat, info in sorted(tree.items(), key=lambda x: -x[1]["count"]):
        if cat not in order:
            items.append({"name": cat, "count": info["count"], "children": sort_children(info["children"])})
    return {"items": items, "total": sum(c["count"] for c in items)}


@router.get("/categories")
def resource_categories(db: Session = Depends(get_db)):
    """一级分类与计数 + 类型计数 + 考点精讲的模块分面"""
    rows = db.query(Resource.category, Resource.resource_type, Resource.sub_path).all()
    counts, type_counts, subs = {}, {}, {}
    for cat, rtype, sub in rows:
        counts[cat] = counts.get(cat, 0) + 1
        type_counts[rtype] = type_counts.get(rtype, 0) + 1
        if cat == "考点精讲" and sub:
            mod = sub.split("/")[0]
            subs[mod] = subs.get(mod, 0) + 1
    order = ["行测", "申论", "面试", "考点精讲", "材料档案", "经验指南"]
    items = [{"name": c, "count": counts[c]} for c in order if c in counts]
    items += [{"name": c, "count": n} for c, n in sorted(counts.items()) if c not in order]
    return {
        "items": items,
        "total": sum(counts.values()),
        "type_counts": type_counts,
        "subs": dict(sorted(subs.items(), key=lambda x: -x[1])),
    }


@router.get("/list")
def resource_list(
    category: Optional[str] = None,
    resource_type: Optional[str] = None,
    sub_prefix: Optional[str] = None,
    keyword: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(24, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Resource)
    if category:
        query = query.filter(Resource.category == category)
    if resource_type:
        query = query.filter(Resource.resource_type == resource_type)
    if sub_prefix:
        query = query.filter(Resource.sub_path.like(sub_prefix + "%"))
    if keyword:
        query = query.filter(Resource.title.contains(keyword) | Resource.sub_path.contains(keyword))
    total = query.count()
    # 有预览图的资料（思维导图）排在前面，默认首屏可见图片墙
    rows = query.order_by(
        (Resource.image_path == ""), Resource.category, Resource.sub_path, Resource.title
    ).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [{
            "id": r.id, "category": r.category, "sub_path": r.sub_path,
            "title": r.title, "description": r.description,
            "resource_type": r.resource_type,
            "excerpt": (r.content or "")[:150],
            "qid_count": len(json.loads(r.related_qids)) if r.related_qids else 0,
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


@router.get("/detail/{resource_id}")
def resource_detail(resource_id: int, db: Session = Depends(get_db)):
    r = db.query(Resource).filter(Resource.id == resource_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="资料不存在")
    return {
        "id": r.id, "category": r.category, "sub_path": r.sub_path,
        "title": r.title, "description": r.description,
        "resource_type": r.resource_type, "content": r.content,
        "image_path": r.image_path, "file_path": r.file_path,
        "source_url": r.source_url, "source": r.source,
    }


@router.get("/detail/{resource_id}/questions")
def resource_related_questions(resource_id: int, db: Session = Depends(get_db)):
    """把资料的 related_qids 通过 bank_imports 映射到本系统题目（供详情页跳转）"""
    from database import BankImport, Question

    r = db.query(Resource).filter(Resource.id == resource_id).first()
    if not r or not r.related_qids:
        return {"items": []}
    try:
        qids = json.loads(r.related_qids)
    except ValueError:
        return {"items": []}
    if not qids:
        return {"items": []}
    rows = (
        db.query(BankImport.bank_qid, Question.id, Question.answer, Question.source)
        .join(Question, Question.id == BankImport.question_id)
        .filter(BankImport.bank_qid.in_(qids))
        .all()
    )
    return {"items": [
        {"bank_qid": bqid, "question_id": qid, "answer": answer, "source": source}
        for bqid, qid, answer, source in rows
    ]}


@router.get("/naoku/media")
def naoku_media(path: str = Query(...)):
    """考公脑库配图服务：path 相对脑库根目录，但必须落在 90-图片 内"""
    from database import DB_PATH as _db_path
    naoku_root = os.path.realpath(os.path.join(os.path.dirname(_db_path), "kaogong-naoku"))
    media_root = os.path.join(naoku_root, "90-图片")
    if not path or "\x00" in path:
        raise HTTPException(status_code=404, detail="文件不存在")
    abs_path = os.path.realpath(os.path.join(naoku_root, path.replace("\\", "/").lstrip("/")))
    if not abs_path.startswith(media_root + os.sep) or not os.path.isfile(abs_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    from mimetypes import guess_type
    return FileResponse(abs_path, media_type=guess_type(abs_path)[0] or "application/octet-stream")


@router.post("/batch")
def resource_batch(data: ResourceBatch, db: Session = Depends(get_db)):
    """批量导入（脚本产出清单后调用）；以 (title, sub_path) 判重，预载已有集合避免逐条查询"""
    existing = {(t, p) for t, p in db.query(Resource.title, Resource.sub_path).all()}
    created = skipped = 0
    for it in data.items:
        title = (it.get("title") or "").strip()
        sub_path = (it.get("sub_path") or "").strip()
        category = (it.get("category") or "").strip()
        if not title or not category:
            skipped += 1
            continue
        if (title, sub_path) in existing:
            skipped += 1
            continue
        existing.add((title, sub_path))
        db.add(Resource(
            category=category, sub_path=sub_path, title=title,
            description=it.get("description", ""),
            resource_type=it.get("resource_type", "mindmap"),
            content=it.get("content", ""),
            related_qids=json.dumps(it.get("related_qids", []), ensure_ascii=False) if it.get("related_qids") else "",
            image_path=it.get("image_path", ""),
            file_path=it.get("file_path", ""),
            source_url=it.get("source_url", ""),
            source=it.get("source", ""),
        ))
        created += 1
    db.commit()
    return {"created": created, "skipped": skipped}
