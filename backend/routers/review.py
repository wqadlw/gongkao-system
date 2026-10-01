"""复习管理路由 v3：FSRS 调度优先，固定周期兜底"""
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from database import get_db, Question, ReviewLog, FsrsState
from services.review_engine import (
    calculate_next_review, update_master_level, calculate_review_stats,
    schedule_fsrs, fsrs_card_summary, FSRS_AVAILABLE, DEFAULT_RETENTION,
)
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

    # FSRS 调度：按每题记忆状态动态安排；失败或未安装 fsrs 时保持固定周期结果
    engine = "legacy"
    fsrs_summary = {}
    if FSRS_AVAILABLE:
        try:
            st = db.query(FsrsState).filter(FsrsState.question_id == q.id).first()
            card_dict = json.loads(st.card_json) if st and st.card_json else None
            retention = st.desired_retention if st and st.desired_retention else DEFAULT_RETENTION
            card_dict, due_local, interval_days = schedule_fsrs(
                card_dict, req.review_result, retention, req.cost_time)
            if not st:
                st = FsrsState(question_id=q.id)
                db.add(st)
            st.card_json = json.dumps(card_dict, ensure_ascii=False)
            st.desired_retention = retention
            st.update_time = datetime.now()
            q.next_review_time = due_local
            engine = "FSRS"
            fsrs_summary = fsrs_card_summary(card_dict)
        except Exception as e:
            print(f"[FSRS 调度失败，本次回退固定周期] {e}")

    db.commit()
    update_daily_stat(db, "review")

    return {
        "message": "复习记录已提交",
        "engine": engine,
        "new_master_level": new_master,
        "next_review_time": q.next_review_time.strftime("%Y-%m-%d %H:%M") if q.next_review_time else "",
        "days_until_next": review_info["days_until_next"] if engine == "legacy" else round(
            (q.next_review_time - datetime.now()).total_seconds() / 86400, 2),
        "fsrs": fsrs_summary,
    }


@router.get("/engine")
def engine_info():
    return {
        "engine": "FSRS" if FSRS_AVAILABLE else "legacy",
        "fsrs_available": FSRS_AVAILABLE,
        "desired_retention": DEFAULT_RETENTION,
        "description": "FSRS 动态记忆调度" if FSRS_AVAILABLE else "固定周期（未安装 fsrs 库）",
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
