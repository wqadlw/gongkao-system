"""模考模式路由 — 限时整卷模考：组卷/答题/判分/复盘"""
import random
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db, Question, MockExam, MockQuestion

router = APIRouter(prefix="/api/mock", tags=["模考模式"])

MODULE_SCORE_FIELD = {
    "政治理论": "score_politics",
    "常识判断": "score_common",
    "言语理解与表达": "score_verbal",
    "数量关系": "score_quant",
    "判断推理": "score_logic",
    "资料分析": "score_data",
}

DEFAULT_SECONDS_PER_QUESTION = 45


def _get_mock(db: Session, mock_id: int) -> MockExam:
    m = db.query(MockExam).filter(MockExam.id == mock_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="模考不存在")
    return m


class MockStart(BaseModel):
    name: str = ""
    modules: List[str] = []          # 模式一：模块多选
    count: int = 20
    source: str = ""                 # 模式二：真题卷来源（优先于模块模式）
    minutes: int = 0                 # 0 = 题数 × 45 秒


@router.post("/start")
def start_mock(req: MockStart, db: Session = Depends(get_db)):
    """组卷并开始模考；返回试卷（不含答案）"""
    if req.source:
        questions = db.query(Question).filter(Question.source == req.source).all()
        if not questions:
            raise HTTPException(status_code=400, detail="该来源没有题目")
        random.shuffle(questions)
        picked = questions[: req.count] if req.count > 0 else questions
    elif req.modules:
        mods = [m for m in req.modules if m in MODULE_SCORE_FIELD]
        if not mods:
            raise HTTPException(status_code=400, detail="请至少选择一个有效模块")
        per = max(1, req.count // len(mods))
        picked = []
        for i, mod in enumerate(mods):
            pool = db.query(Question).filter(Question.level1 == mod).all()
            random.shuffle(pool)
            take = req.count - i if i == len(mods) - 1 else per
            picked.extend(pool[: max(0, take)])
        picked = picked[: req.count]
        if not picked:
            raise HTTPException(status_code=400, detail="所选模块题库为空，请先导入题目")
    else:
        raise HTTPException(status_code=400, detail="请选择模块或真题卷来源")

    random.shuffle(picked)
    name = req.name.strip() or f"模考 {datetime.now().strftime('%m-%d %H:%M')}"
    exam = MockExam(name=name, mock_date=datetime.now(), total_score=0,
                    remark=f"{len(picked)}题")
    db.add(exam)
    db.flush()
    for i, q in enumerate(picked):
        db.add(MockQuestion(
            mock_id=exam.id, question_id=q.id, module=q.level1 or "其他",
            order_no=i + 1, answer=q.answer or "", selected="",
        ))
    db.commit()

    duration_minutes = req.minutes if req.minutes > 0 else max(5, round(len(picked) * DEFAULT_SECONDS_PER_QUESTION / 60))
    return {
        "mock_id": exam.id, "name": name, "count": len(picked),
        "duration_seconds": duration_minutes * 60,
        "questions": [{
            "order_no": i + 1, "question_id": q.id,
            "question_raw": q.question_raw or "",
            "module": q.level1 or "其他",
        } for i, q in enumerate(picked)],
    }


@router.get("/list")
def mock_list(db: Session = Depends(get_db)):
    exams = db.query(MockExam).order_by(MockExam.mock_date.desc()).limit(100).all()
    result = []
    for m in exams:
        total = db.query(MockQuestion).filter(MockQuestion.mock_id == m.id).count()
        answered = db.query(MockQuestion).filter(
            MockQuestion.mock_id == m.id, MockQuestion.selected != "").count()
        graded = db.query(MockQuestion).filter(
            MockQuestion.mock_id == m.id, MockQuestion.is_correct != None).count()  # noqa: E711
        result.append({
            "id": m.id, "name": m.name,
            "mock_date": m.mock_date.strftime("%Y-%m-%d %H:%M") if m.mock_date else "",
            "total_score": m.total_score, "question_total": total,
            "answered": answered, "graded": graded >= total and total > 0,
            "remark": m.remark,
        })
    return {"items": result}


@router.get("/{mock_id}/paper")
def get_paper(mock_id: int, db: Session = Depends(get_db)):
    """取未完成模考的试卷（断点续答，不含答案）"""
    m = _get_mock(db, mock_id)
    rows = db.query(MockQuestion).filter(MockQuestion.mock_id == mock_id).order_by(MockQuestion.order_no).all()
    if not rows:
        raise HTTPException(status_code=400, detail="该模考没有题目")
    graded = sum(1 for r in rows if r.is_correct is not None)
    if graded >= len(rows):
        raise HTTPException(status_code=400, detail="该模考已交卷，请查看复盘")
    return {
        "mock_id": mock_id, "name": m.name,
        "questions": [{
            "order_no": r.order_no, "question_id": r.question_id, "module": r.module,
            "question_raw": (db.query(Question).filter(Question.id == r.question_id).first().question_raw or "")
            if db.query(Question).filter(Question.id == r.question_id).first() else "",
            "selected": r.selected,
        } for r in rows],
    }


class MockSubmit(BaseModel):
    answers: List[dict] = []         # [{question_id, selected}]
    duration_seconds: int = 0


@router.post("/{mock_id}/submit")
def submit_mock(mock_id: int, req: MockSubmit, db: Session = Depends(get_db)):
    m = _get_mock(db, mock_id)
    rows = db.query(MockQuestion).filter(MockQuestion.mock_id == mock_id).order_by(MockQuestion.order_no).all()
    if not rows:
        raise HTTPException(status_code=400, detail="该模考没有题目")
    answer_map = {a.get("question_id"): (a.get("selected") or "").strip() for a in req.answers}

    module_stat = {}
    for r in rows:
        selected = (answer_map.get(r.question_id) or "").strip()
        r.selected = selected
        r.is_correct = 1 if selected and selected == (r.answer or "") else 0
        stat = module_stat.setdefault(r.module or "其他", {"correct": 0, "total": 0})
        stat["total"] += 1
        if r.is_correct:
            stat["correct"] += 1

    total_correct = sum(s["correct"] for s in module_stat.values())
    m.total_score = total_correct
    m.remark = f"{len(rows)}题"
    for module, field in MODULE_SCORE_FIELD.items():
        setattr(m, field, module_stat.get(module, {}).get("correct", 0))
    if req.duration_seconds:
        m.loss_time = round(req.duration_seconds / 60)  # 借用 loss_time 记录用时（分钟）
    db.commit()

    wrong_ids = [r.question_id for r in rows if not r.is_correct]
    return {
        "message": "交卷成功",
        "total": len(rows), "correct": total_correct,
        "accuracy": round(total_correct / len(rows) * 100, 1) if rows else 0,
        "modules": [{"module": k, "correct": v["correct"], "total": v["total"]}
                    for k, v in sorted(module_stat.items(), key=lambda x: -x[1]["total"])],
        "wrong_question_ids": wrong_ids,
    }


@router.get("/{mock_id}/result")
def mock_result(mock_id: int, db: Session = Depends(get_db)):
    """复盘：成绩汇总 + 逐题作答与解析"""
    m = _get_mock(db, mock_id)
    rows = db.query(MockQuestion).filter(MockQuestion.mock_id == mock_id).order_by(MockQuestion.order_no).all()
    questions = []
    for r in rows:
        q = db.query(Question).filter(Question.id == r.question_id).first()
        questions.append({
            "order_no": r.order_no, "question_id": r.question_id, "module": r.module,
            "question_raw": (q.question_raw or "")[:600] if q else "",
            "selected": r.selected, "answer": r.answer,
            "is_correct": r.is_correct,
            "normal_solve": (q.normal_solve or "")[:400] if q else "",
            "break_logic": (q.break_logic or "")[:400] if q else "",
        })
    module_stat = {}
    for r in rows:
        stat = module_stat.setdefault(r.module or "其他", {"correct": 0, "total": 0})
        stat["total"] += 1
        if r.is_correct:
            stat["correct"] += 1
    return {
        "id": m.id, "name": m.name,
        "mock_date": m.mock_date.strftime("%Y-%m-%d %H:%M") if m.mock_date else "",
        "total_score": m.total_score, "total": len(rows),
        "accuracy": round(m.total_score / len(rows) * 100, 1) if rows else 0,
        "duration_minutes": m.loss_time or 0,
        "modules": [{"module": k, "correct": v["correct"], "total": v["total"]}
                    for k, v in sorted(module_stat.items(), key=lambda x: -x[1]["total"])],
        "questions": questions,
    }


@router.delete("/{mock_id}")
def delete_mock(mock_id: int, db: Session = Depends(get_db)):
    _get_mock(db, mock_id)
    db.query(MockQuestion).filter(MockQuestion.mock_id == mock_id).delete()
    db.query(MockExam).filter(MockExam.id == mock_id).delete()
    db.commit()
    return {"message": "已删除"}
