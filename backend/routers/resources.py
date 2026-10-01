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
    """模块优先的三级聚合：模块 → 类型 → 大类/年份/主题（每节点自带过滤参数）"""
    from database import DB_PATH as _db_path  # noqa: F401
    KNOWN_MODULES = {"政治理论", "常识判断", "言语理解与表达", "数量关系", "判断推理", "资料分析"}
    TYPE_LABEL = {"mindmap": "思维导图", "考点精讲": "考点精讲", "材料档案": "材料档案", "link": "外部链接"}

    rows = db.query(Resource.category, Resource.resource_type, Resource.sub_path).all()
    tree = {}
    for cat, rtype, sub in rows:
        parts = [p for p in (sub or "").split("/") if p]
        if cat in ("申论", "面试"):
            module, rest = cat, []
        elif cat == "经验指南":
            module, rest = "经验指南", []
        elif parts and parts[0] in KNOWN_MODULES:
            module, rest = parts[0], parts[1:]
        else:
            module, rest = cat, parts
        type_label = TYPE_LABEL.get(rtype, rtype)

        node = tree.setdefault(module, {"count": 0, "children": {}})
        node["count"] += 1
        tnode = node["children"].setdefault(type_label, {"count": 0, "children": {}})
        tnode["count"] += 1
        if rest:
            leaf_key = "/".join(rest)
            leaf = tnode["children"].setdefault(leaf_key, {"count": 0, "children": {}})
            leaf["count"] += 1

    def build_filter(module, type_label, extra_sub=None):
        rtype = next((k for k, v in TYPE_LABEL.items() if v == type_label), None)
        f = {"module_prefix": module}
        if rtype:
            f["resource_type"] = rtype
        if extra_sub and rtype in ("考点精讲", "mindmap", "材料档案"):
            f["sub_prefix"] = f"{module}/{extra_sub}" if extra_sub != module else extra_sub
            if rtype == "考点精讲":
                f["category"] = "考点精讲"
        if module in ("申论", "面试", "经验指南"):
            f = {"category": module if module != "经验指南" else "经验指南"}
            if rtype:
                f["resource_type"] = rtype
        return f

    def sort_children(children_map, module, type_label, parent_extra=None):
        out = []
        for name, info in sorted(children_map.items(), key=lambda x: -x[1]["count"]):
            extra = None
            if type_label == "考点精讲":
                extra = name                      # 大类
            elif type_label == "思维导图":
                extra = name                      # 主题/考点组合（sub_path 余段）
            elif type_label == "材料档案":
                extra = name                      # 年份
            node_filter = build_filter(module, type_label, extra)
            out.append({
                "name": name, "count": info["count"],
                "filter": node_filter,
                "children": sort_children(info["children"], module, type_label, extra),
            })
        return out

    order = ["资料分析", "判断推理", "常识判断", "言语理解与表达", "数量关系", "政治理论", "申论", "面试", "经验指南"]
    items = []
    for module in order:
        if module in tree:
            info = tree[module]
            children = sort_children(info["children"], module, None)
            for child in children:  # 模块层过滤器：该模块下全部
                child["filter"] = build_filter(module, child["name"])
                for gc in child.get("children", []):
                    gc["filter"] = build_filter(module, child["name"], gc["name"] if child["name"] in ("考点精讲", "思维导图", "材料档案") else None)
            items.append({"name": module, "count": info["count"], "children": children})
    for module, info in sorted(tree.items(), key=lambda x: -x[1]["count"]):
        if module not in order:
            children = sort_children(info["children"], module, None)
            for child in children:
                child["filter"] = {"category": module}
                if child["name"] in TYPE_LABEL:
                    child["filter"]["resource_type"] = next(k for k, v in TYPE_LABEL.items() if v == child["name"])
            items.append({"name": module, "count": info["count"], "children": children})
    return {"items": items, "total": sum(i["count"] for i in items)}


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
    module_prefix: Optional[str] = None,
    favorite: Optional[int] = None,
    keyword: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(24, ge=1, le=100),
    db: Session = Depends(get_db),
):
    from sqlalchemy import or_

    query = db.query(Resource)
    if category:
        query = query.filter(Resource.category == category)
    if resource_type:
        query = query.filter(Resource.resource_type == resource_type)
    if sub_prefix:
        query = query.filter(Resource.sub_path.like(sub_prefix + "%"))
    if module_prefix:
        query = query.filter(
            or_(Resource.sub_path.like(module_prefix + "%"), Resource.category == module_prefix)
        )
    if favorite is not None:
        query = query.filter(Resource.is_favorite == (1 if favorite else 0))
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
            "is_favorite": bool(r.is_favorite),
        } for r in rows],
        "total": total, "page": page, "page_size": page_size,
    }


@router.post("/{resource_id}/favorite")
def toggle_favorite(resource_id: int, db: Session = Depends(get_db)):
    r = db.query(Resource).filter(Resource.id == resource_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="资料不存在")
    r.is_favorite = 0 if r.is_favorite else 1
    db.commit()
    return {"is_favorite": bool(r.is_favorite)}


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
