"""提示词模板管理路由 v2"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import get_db, PromptTemplate

router = APIRouter(prefix="/api/prompts", tags=["提示词模板"])


@router.get("/list")
def get_prompts(type: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(PromptTemplate)
    if type:
        query = query.filter(PromptTemplate.type == type)
    prompts = query.order_by(PromptTemplate.is_pinned.desc(), PromptTemplate.id).all()
    return [{
        "id": p.id, "name": p.name, "type": p.type, "tag": p.tag,
        "content": p.content, "is_default": p.is_default, "is_locked": p.is_locked,
        "is_pinned": p.is_pinned, "remark": p.remark,
        "create_time": p.create_time.strftime("%Y-%m-%d %H:%M") if p.create_time else "",
    } for p in prompts]


@router.get("/{prompt_id}")
def get_prompt(prompt_id: int, db: Session = Depends(get_db)):
    p = db.query(PromptTemplate).filter(PromptTemplate.id == prompt_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="提示词不存在")
    return {
        "id": p.id, "name": p.name, "type": p.type, "tag": p.tag,
        "content": p.content, "is_default": p.is_default, "is_locked": p.is_locked,
        "is_pinned": p.is_pinned, "remark": p.remark,
    }


class PromptCreate(BaseModel):
    name: str
    type: str
    tag: str = ""
    content: str
    remark: str = ""


@router.post("/")
def create_prompt(p: PromptCreate, db: Session = Depends(get_db)):
    new_p = PromptTemplate(
        name=p.name, type=p.type, tag=p.tag, content=p.content,
        is_default=False, is_locked=False, is_pinned=False, remark=p.remark,
    )
    db.add(new_p)
    db.commit()
    db.refresh(new_p)
    return {"id": new_p.id, "message": "创建成功"}


class PromptUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    tag: Optional[str] = None
    content: Optional[str] = None
    is_pinned: Optional[bool] = None
    remark: Optional[str] = None


@router.put("/{prompt_id}")
def update_prompt(prompt_id: int, p: PromptUpdate, db: Session = Depends(get_db)):
    existing = db.query(PromptTemplate).filter(PromptTemplate.id == prompt_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="提示词不存在")
    if existing.is_locked:
        raise HTTPException(status_code=403, detail="内置模板已锁定，不可编辑，请新建模板")
    if p.name is not None:
        existing.name = p.name
    if p.type is not None:
        existing.type = p.type
    if p.tag is not None:
        existing.tag = p.tag
    if p.content is not None:
        existing.content = p.content
    if p.is_pinned is not None:
        existing.is_pinned = p.is_pinned
    if p.remark is not None:
        existing.remark = p.remark
    db.commit()
    return {"message": "更新成功"}


@router.delete("/{prompt_id}")
def delete_prompt(prompt_id: int, db: Session = Depends(get_db)):
    existing = db.query(PromptTemplate).filter(PromptTemplate.id == prompt_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="提示词不存在")
    if existing.is_locked:
        raise HTTPException(status_code=403, detail="内置模板不可删除")
    db.delete(existing)
    db.commit()
    return {"message": "删除成功"}


class CopyRequest(BaseModel):
    question_content: str = ""
    extra_info: str = ""


@router.post("/{prompt_id}/build")
def build_question_text_api(prompt_id: int, req: CopyRequest, db: Session = Depends(get_db)):
    p = db.query(PromptTemplate).filter(PromptTemplate.id == prompt_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="提示词不存在")
    content = p.content.replace("{question_content}", req.question_content)
    content = content.replace("{extra_info}", req.extra_info)
    return {"text": content, "prompt_name": p.name}


@router.post("/import")
def import_prompts(prompts: list, db: Session = Depends(get_db)):
    count = 0
    for p_data in prompts:
        new_p = PromptTemplate(
            name=p_data.get("name", ""), type=p_data.get("type", ""),
            tag=p_data.get("tag", ""), content=p_data.get("content", ""),
            is_default=False, is_locked=False, is_pinned=False,
            remark=p_data.get("remark", ""),
        )
        db.add(new_p)
        count += 1
    db.commit()
    return {"message": f"成功导入 {count} 个提示词"}


@router.get("/export/all")
def export_all_prompts(db: Session = Depends(get_db)):
    prompts = db.query(PromptTemplate).all()
    return [{
        "name": p.name, "type": p.type, "tag": p.tag,
        "content": p.content, "remark": p.remark, "is_locked": p.is_locked,
    } for p in prompts]
