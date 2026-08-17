"""复习管理路由 v2"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from database import get_db, Question, ReviewLog
from services.review_engine import calculate_next_review, update_master_level, get_review_status, calculate_review_stats
from services.stats_engine import update_daily_stat

router = APIRouter(prefix="/api/review", tags=["智能复习"])


@router.get("/due")
def get_due_questions(limit: int = 50, db: Session = Depends(get_db)):
    now = datetime.now()
    questions = db.query(Question).filter(
        Question.next_review_time <= now,
        Question.review_count >= 0
    ).order_by(Question.next_review_time.asc()).limit(limit).all()

    return [{
        "id": q.id,
        "question_raw": (q.question_raw[:200] + "...") if q.question_raw and len(q.question_raw) > 200 else q.question_raw,
        "level1": q.level1, "level3": q.level3, "level4": q.level4, "level5": q.level5,
        "answer": q.answer, "master_level": q.master_level, "review_count": q.review_count,
        "next_review_time": q.next_review_time.strftime("%Y-%m-%d %H:%M") if q.next_review_time else "",
        "difficulty": q.difficulty, "is_error": q.is_error,
        "step_detail": q.step_detail, "break_logic": q.break_logic,
        "normal_solve": q.normal_solve, "quick_solve": q.quick_solve,
        "sub_point": q.sub_point, "exam_intent": q.exam_intent,
        "option_feature": q.option_feature, "identify_signal": q.identify_signal,
        "trap_read": q.trap_read, "trap_calc": q.trap_calc, "trap_thought": q.trap_thought,
        "practice_question": q.practice_question, "practice_answer": q.practice_answer,
        "ai_raw_content": q.ai_raw_content,
    } for q in questions]


class ReviewSubmit(BaseModel):
    question_id: int
    review_result: str = "good"  # again/hard/good/easy
    cost_time: int = 0


@router.post("/submit")
def submit_review(req: ReviewSubmit, db: Session = Depends(get_db)):
    q = db.query(Question).filter(Question.id == req.question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="题目不存在")

    master_before = q.master_level
    new_master = update_master_level(q.master_level, req.review_result)
    review_info = calculate_next_review(q.review_count, new_master, req.review_result)

    log = ReviewLog(
        question_id=q.id, review_time=datetime.now(),
        review_result=req.review_result, master_before=master_before,
        master_after=new_master, cost_time=req.cost_time,
    )
    db.add(log)

    q.master_level = new_master
    q.review_count = review_info["review_count"]
    q.next_review_time = review_info["next_review_time"]

    db.commit()
    update_daily_stat(db, "review")

    return {
        "message": "复习记录已提交",
        "new_master_level": new_master,
        "next_review_time": review_info["next_review_time"].strftime("%Y-%m-%d %H:%M"),
        "days_until_next": review_info["days_until_next"],
    }


@router.get("/stats")
def get_review_stats_api(db: Session = Depends(get_db)):
    questions = db.query(Question).all()
    return calculate_review_stats(questions)


@router.get("/logs")
def get_review_logs(limit: int = 100, db: Session = Depends(get_db)):
    logs = db.query(ReviewLog).order_by(ReviewLog.review_time.desc()).limit(limit).all()
    return [{
        "id": log.id, "question_id": log.question_id,
        "review_time": log.review_time.strftime("%Y-%m-%d %H:%M") if log.review_time else "",
        "review_result": log.review_result,
        "master_before": log.master_before, "master_after": log.master_after,
        "cost_time": log.cost_time,
    } for log in logs]


@router.get("/overdue")
def get_overdue_questions_api(db: Session = Depends(get_db)):
    now = datetime.now()
    questions = db.query(Question).filter(
        Question.next_review_time < now,
        Question.review_count > 0
    ).order_by(Question.next_review_time.asc()).all()

    return [{
        "id": q.id,
        "question_raw": (q.question_raw[:100] + "...") if q.question_raw and len(q.question_raw) > 100 else q.question_raw,
        "level1": q.level1, "level4": q.level4, "level5": q.level5,
        "master_level": q.master_level, "review_count": q.review_count,
        "next_review_time": q.next_review_time.strftime("%Y-%m-%d %H:%M") if q.next_review_time else "",
        "overdue_days": (now - q.next_review_time).days if q.next_review_time else 0,
    } for q in questions]
