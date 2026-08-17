"""行测知识库路由 —— 与模块提示词/题目耦合：按 module 关联知识点"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from database import get_db, Knowledge

router = APIRouter(prefix="/api/knowledge", tags=["行测知识库"])


def format_knowledge(k):
    return {
        "id": k.id,
        "module": k.module,
        "kg_type": k.kg_type,
        "title": k.title,
        "content": k.content,
        "tags": k.tags,
        "related_prompt": k.related_prompt,
        "source": k.source,
        "difficulty": k.difficulty,
        "level1": k.level1, "level2": k.level2, "level3": k.level3,
        "level4": k.level4, "level5": k.level5,
        "source_question_id": k.source_question_id,
        "card_title": k.card_title, "card_tags": k.card_tags, "card_summary": k.card_summary,
        "create_time": k.create_time.strftime("%Y-%m-%d %H:%M") if k.create_time else "",
        "update_time": k.update_time.strftime("%Y-%m-%d %H:%M") if k.update_time else "",
    }


@router.get("/list")
def list_knowledge(
    module: Optional[str] = None,
    kg_type: Optional[str] = None,
    keyword: Optional[str] = None,
    level1: Optional[str] = None,
    level2: Optional[str] = None,
    level3: Optional[str] = None,
    level4: Optional[str] = None,
    level5: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
):
    query = db.query(Knowledge)
    if module:
        query = query.filter(Knowledge.module == module)
    if kg_type:
        query = query.filter(Knowledge.kg_type == kg_type)
    for lvl, val in [("level1", level1), ("level2", level2), ("level3", level3),
                     ("level4", level4), ("level5", level5)]:
        if val:
            query = query.filter(getattr(Knowledge, lvl) == val)
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            Knowledge.title.like(like) | Knowledge.content.like(like) | Knowledge.tags.like(like)
        )
    total = query.count()
    items = query.order_by(Knowledge.module, Knowledge.id).offset((page - 1) * page_size).limit(page_size).all()
    # 返回按模块聚合，便于前端左导航分组
    return {"total": total, "items": [format_knowledge(k) for k in items]}


@router.get("/by-module/{module}")
def by_module(module: str, db: Session = Depends(get_db)):
    items = db.query(Knowledge).filter(Knowledge.module == module).order_by(Knowledge.kg_type, Knowledge.id).all()
    counts = {}
    for k in items:
        counts[k.kg_type] = counts.get(k.kg_type, 0) + 1
    return {"module": module, "total": len(items), "type_counts": counts, "items": [format_knowledge(k) for k in items]}


@router.get("/{kid}")
def get_knowledge(kid: int, db: Session = Depends(get_db)):
    k = db.query(Knowledge).filter(Knowledge.id == kid).first()
    if not k:
        raise HTTPException(status_code=404, detail="知识点不存在")
    return format_knowledge(k)


class KnowledgeCreate(BaseModel):
    module: str
    kg_type: Optional[str] = "概念"
    title: str
    content: str = ""
    tags: Optional[str] = ""
    related_prompt: Optional[str] = ""
    source: Optional[str] = ""
    difficulty: Optional[int] = 2
    level1: Optional[str] = ""
    level2: Optional[str] = ""
    level3: Optional[str] = ""
    level4: Optional[str] = ""
    level5: Optional[str] = ""
    source_question_id: Optional[int] = 0
    card_title: Optional[str] = ""
    card_tags: Optional[str] = ""
    card_summary: Optional[str] = ""


class KnowledgeUpdate(BaseModel):
    module: Optional[str] = None
    kg_type: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[str] = None
    related_prompt: Optional[str] = None
    source: Optional[str] = None
    difficulty: Optional[int] = None
    level1: Optional[str] = None
    level2: Optional[str] = None
    level3: Optional[str] = None
    level4: Optional[str] = None
    level5: Optional[str] = None
    source_question_id: Optional[int] = None
    card_title: Optional[str] = None
    card_tags: Optional[str] = None
    card_summary: Optional[str] = None


@router.post("/")
def create_knowledge(data: KnowledgeCreate, db: Session = Depends(get_db)):
    k = Knowledge(
        module=data.module, kg_type=data.kg_type or "概念", title=data.title,
        content=data.content, tags=data.tags or "", related_prompt=data.related_prompt or data.module,
        source=data.source or "自定义", difficulty=data.difficulty or 2,
        level1=data.level1 or "", level2=data.level2 or "", level3=data.level3 or "",
        level4=data.level4 or "", level5=data.level5 or "",
        source_question_id=data.source_question_id or 0,
        card_title=data.card_title or "", card_tags=data.card_tags or "", card_summary=data.card_summary or "",
        create_time=datetime.now(), update_time=datetime.now(),
    )
    db.add(k)
    db.commit()
    db.refresh(k)
    return {"id": k.id, "message": "知识点已创建"}


class KnowledgeBatchItem(BaseModel):
    module: str
    kg_type: Optional[str] = "概念"
    title: str
    content: str = ""
    tags: Optional[str] = ""
    related_prompt: Optional[str] = ""
    source: Optional[str] = ""
    difficulty: Optional[int] = 2
    level1: Optional[str] = ""
    level2: Optional[str] = ""
    level3: Optional[str] = ""
    level4: Optional[str] = ""
    level5: Optional[str] = ""
    source_question_id: Optional[int] = 0
    card_title: Optional[str] = ""
    card_tags: Optional[str] = ""
    card_summary: Optional[str] = ""


class KnowledgeBatch(BaseModel):
    items: List[KnowledgeBatchItem]


@router.post("/batch")
def batch_create_knowledge(data: KnowledgeBatch, db: Session = Depends(get_db)):
    """批量导入知识点（来自提示词助手 / 文件 / 粘贴的 JSON 数组 / 录入沉淀）"""
    created = 0
    errors = []
    for idx, it in enumerate(data.items):
        if not (it and it.title and it.title.strip() and it.module and it.module.strip()):
            errors.append({"index": idx, "title": (it.title if it else None), "reason": "缺少 module 或 title"})
            continue
        k = Knowledge(
            module=it.module.strip(), kg_type=(it.kg_type or "概念").strip() or "概念",
            title=it.title.strip(), content=it.content or "",
            tags=it.tags or "", related_prompt=it.related_prompt or it.module.strip(),
            source=it.source or "批量导入", difficulty=it.difficulty or 2,
            level1=it.level1 or "", level2=it.level2 or "", level3=it.level3 or "",
            level4=it.level4 or "", level5=it.level5 or "",
            source_question_id=it.source_question_id or 0,
            card_title=it.card_title or "", card_tags=it.card_tags or "", card_summary=it.card_summary or "",
            create_time=datetime.now(), update_time=datetime.now(),
        )
        db.add(k)
        created += 1
    db.commit()
    return {"created": created, "total": len(data.items), "errors": errors}


@router.put("/{kid}")
def update_knowledge(kid: int, data: KnowledgeUpdate, db: Session = Depends(get_db)):
    k = db.query(Knowledge).filter(Knowledge.id == kid).first()
    if not k:
        raise HTTPException(status_code=404, detail="知识点不存在")
    for key, value in data.dict(exclude_unset=True).items():
        setattr(k, key, value)
    k.update_time = datetime.now()
    db.commit()
    return {"message": "知识点已更新"}


@router.delete("/{kid}")
def delete_knowledge(kid: int, db: Session = Depends(get_db)):
    k = db.query(Knowledge).filter(Knowledge.id == kid).first()
    if not k:
        raise HTTPException(status_code=404, detail="知识点不存在")
    db.delete(k)
    db.commit()
    return {"message": "知识点已删除"}
