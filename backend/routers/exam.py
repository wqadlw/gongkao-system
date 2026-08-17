"""考试倒计时管理路由"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from database import get_db, ExamCountdown

router = APIRouter(prefix="/api/exam", tags=["考试倒计时"])


@router.get("/list")
def get_exams(db: Session = Depends(get_db)):
    exams = db.query(ExamCountdown).order_by(ExamCountdown.exam_date.asc()).all()
    now = datetime.now()
    return [{
        "id": e.id, "name": e.name, "exam_type": e.exam_type,
        "exam_date": e.exam_date.strftime("%Y-%m-%d") if e.exam_date else "",
        "days_left": (e.exam_date - now).days if e.exam_date else 0,
        "remark": e.remark, "is_active": e.is_active,
        "is_passed": e.exam_date < now if e.exam_date else False,
    } for e in exams]


class ExamCreate(BaseModel):
    name: str
    exam_type: str
    exam_date: str
    remark: str = ""


@router.post("/")
def create_exam(e: ExamCreate, db: Session = Depends(get_db)):
    new_e = ExamCountdown(
        name=e.name, exam_type=e.exam_type,
        exam_date=datetime.strptime(e.exam_date, "%Y-%m-%d"),
        remark=e.remark, is_active=True,
    )
    db.add(new_e)
    db.commit()
    db.refresh(new_e)
    return {"id": new_e.id, "message": "创建成功"}


class ExamUpdate(BaseModel):
    name: Optional[str] = None
    exam_type: Optional[str] = None
    exam_date: Optional[str] = None
    remark: Optional[str] = None
    is_active: Optional[bool] = None


@router.put("/{exam_id}")
def update_exam(exam_id: int, e: ExamUpdate, db: Session = Depends(get_db)):
    existing = db.query(ExamCountdown).filter(ExamCountdown.id == exam_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="考试不存在")
    if e.name is not None:
        existing.name = e.name
    if e.exam_type is not None:
        existing.exam_type = e.exam_type
    if e.exam_date is not None:
        existing.exam_date = datetime.strptime(e.exam_date, "%Y-%m-%d")
    if e.remark is not None:
        existing.remark = e.remark
    if e.is_active is not None:
        existing.is_active = e.is_active
    db.commit()
    return {"message": "更新成功"}


@router.delete("/{exam_id}")
def delete_exam(exam_id: int, db: Session = Depends(get_db)):
    existing = db.query(ExamCountdown).filter(ExamCountdown.id == exam_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="考试不存在")
    db.delete(existing)
    db.commit()
    return {"message": "删除成功"}
