"""备考阶段与模考管理路由 v2"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from database import get_db, StudyStage

router = APIRouter(prefix="/api/study", tags=["备考管理"])


@router.get("/stages")
def get_stages(db: Session = Depends(get_db)):
    stages = db.query(StudyStage).order_by(StudyStage.start_date.desc()).all()
    return [{
        "id": s.id, "name": s.name,
        "start_date": s.start_date.strftime("%Y-%m-%d") if s.start_date else "",
        "end_date": s.end_date.strftime("%Y-%m-%d") if s.end_date else "",
        "goal": s.goal, "daily_target": s.daily_target,
        "is_active": s.is_active, "remark": s.remark,
    } for s in stages]


class StageCreate(BaseModel):
    name: str
    start_date: str
    end_date: Optional[str] = None
    goal: str = ""
    daily_target: int = 20
    remark: str = ""


@router.post("/stages")
def create_stage(s: StageCreate, db: Session = Depends(get_db)):
    new_s = StudyStage(
        name=s.name,
        start_date=datetime.strptime(s.start_date, "%Y-%m-%d") if s.start_date else None,
        end_date=datetime.strptime(s.end_date, "%Y-%m-%d") if s.end_date else None,
        goal=s.goal, daily_target=s.daily_target, remark=s.remark,
    )
    db.add(new_s)
    db.commit()
    db.refresh(new_s)
    return {"id": new_s.id, "message": "创建成功"}


class StageUpdate(BaseModel):
    is_active: Optional[bool] = None
    name: Optional[str] = None
    goal: Optional[str] = None
    daily_target: Optional[int] = None


@router.put("/stages/{stage_id}")
def update_stage(stage_id: int, s: StageUpdate, db: Session = Depends(get_db)):
    existing = db.query(StudyStage).filter(StudyStage.id == stage_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="阶段不存在")
    update_data = s.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(existing, key, value)
    db.commit()
    return {"message": "更新成功"}


@router.delete("/stages/{stage_id}")
def delete_stage(stage_id: int, db: Session = Depends(get_db)):
    existing = db.query(StudyStage).filter(StudyStage.id == stage_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="阶段不存在")
    db.delete(existing)
    db.commit()
    return {"message": "删除成功"}


