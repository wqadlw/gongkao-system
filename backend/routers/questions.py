"""题目管理路由 v2 - 极简录入流程"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from database import get_db, Question, Category
from services.parser import parse_ai_content, parse_note_content, validate_parsed_content, build_question_text
from services.review_engine import calculate_next_review, update_master_level
from services.stats_engine import update_daily_stat

router = APIRouter(prefix="/api/questions", tags=["题目管理"])


def format_question(q):
    return {
        "id": q.id,
        "create_time": q.create_time.strftime("%Y-%m-%d %H:%M") if q.create_time else "",
        "first_study_time": q.first_study_time.strftime("%Y-%m-%d %H:%M") if q.first_study_time else "",
        "level1": q.level1, "level2": q.level2, "level3": q.level3, "level4": q.level4, "level5": q.level5,
        "question_raw": q.question_raw,
        "source": q.source, "difficulty": q.difficulty, "priority": q.priority, "cost_time": q.cost_time,
        "sub_point": q.sub_point, "exam_intent": q.exam_intent,
        "difficulty_label": q.difficulty_label, "exam_priority": q.exam_priority,
        "suggested_time": q.suggested_time, "option_feature": q.option_feature,
        "break_logic": q.break_logic, "trap_read": q.trap_read, "trap_calc": q.trap_calc,
        "trap_thought": q.trap_thought, "error_path": q.error_path,
        "normal_solve": q.normal_solve, "quick_solve": q.quick_solve, "identify_signal": q.identify_signal,
        "step_detail": q.step_detail, "practice_question": q.practice_question,
        "practice_answer": q.practice_answer, "answer": q.answer,
        "background_knowledge": q.background_knowledge,
        "card_title": q.card_title, "card_tags": q.card_tags, "card_summary": q.card_summary,
        "master_level": q.master_level, "is_error": q.is_error, "error_reason": q.error_reason, "tags": q.tags, "is_favorite": q.is_favorite,
        "stage_id": q.stage_id, "mock_id": q.mock_id,
        "ai_raw_content": q.ai_raw_content,
        "review_count": q.review_count,
        "next_review_time": q.next_review_time.strftime("%Y-%m-%d %H:%M") if q.next_review_time else "",
        "review_status": q.review_status,
    }


@router.get("/list")
def get_questions(
    page: int = 1, page_size: int = 20,
    level1: Optional[str] = None, level2: Optional[str] = None,
    level3: Optional[str] = None, level4: Optional[str] = None, level5: Optional[str] = None,
    is_error: Optional[bool] = None, master_level: Optional[int] = None, is_favorite: Optional[bool] = None,
    deposited: Optional[bool] = None,
    keyword: Optional[str] = None, sort: str = "new",
    db: Session = Depends(get_db)
):
    query = db.query(Question)
    if level1:
        query = query.filter(Question.level1 == level1)
    if level2:
        query = query.filter(Question.level2 == level2)
    if level3:
        query = query.filter(Question.level3 == level3)
    if level4:
        query = query.filter(Question.level4 == level4)
    if level5:
        query = query.filter(Question.level5 == level5)
    if is_favorite is not None:
        query = query.filter(Question.is_favorite == is_favorite)
    if is_error is not None:
        query = query.filter(Question.is_error == is_error)
    if deposited is not None:
        query = query.filter(Question.deposited == deposited)
    if master_level:
        query = query.filter(Question.master_level == master_level)
    if keyword:
        query = query.filter(Question.question_raw.like(f"%{keyword}%"))

    if sort == "new":
        query = query.order_by(Question.create_time.desc())
    elif sort == "old":
        query = query.order_by(Question.create_time.asc())
    elif sort == "difficulty":
        query = query.order_by(Question.difficulty.desc())
    elif sort == "review":
        query = query.order_by(Question.next_review_time.asc())

    total = query.count()
    questions = query.offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [format_question(q) for q in questions], "total": total, "page": page, "page_size": page_size}


@router.get("/{question_id}")
def get_question(question_id: int, db: Session = Depends(get_db)):
    q = db.query(Question).filter(Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="题目不存在")
    return format_question(q)


class QuestionCreate(BaseModel):
    level1: str = ""
    level2: str = ""
    level3: str = ""
    level4: str = ""
    level5: str = ""
    question_raw: str = ""
    source: str = ""
    difficulty: int = 3
    priority: int = 2
    cost_time: int = 60
    is_error: bool = False
    tags: str = ""
    stage_id: Optional[int] = None
    mock_id: Optional[int] = None
    # 结构化字段
    sub_point: str = ""
    exam_intent: str = ""
    difficulty_label: str = ""
    exam_priority: str = ""
    suggested_time: int = 60
    option_feature: str = ""
    break_logic: str = ""
    trap_read: str = ""
    trap_calc: str = ""
    trap_thought: str = ""
    error_path: str = ""
    normal_solve: str = ""
    quick_solve: str = ""
    identify_signal: str = ""
    step_detail: str = ""
    practice_question: str = ""
    practice_answer: str = ""
    answer: str = ""
    background_knowledge: str = ""
    ai_raw_content: str = ""
    # 卡片缩略信息（提示词第八节）
    card_title: str = ""
    card_tags: str = ""
    card_summary: str = ""


@router.post("/")
def create_question(q: QuestionCreate, db: Session = Depends(get_db)):
    now = datetime.now()
    new_q = Question(
        level1=q.level1, level2=q.level2, level3=q.level3, level4=q.level4, level5=q.level5,
        question_raw=q.question_raw, source=q.source, difficulty=q.difficulty,
        priority=q.priority, cost_time=q.cost_time, is_error=q.is_error, tags=q.tags,
        stage_id=q.stage_id, mock_id=q.mock_id,
        sub_point=q.sub_point, exam_intent=q.exam_intent,
        difficulty_label=q.difficulty_label, exam_priority=q.exam_priority,
        suggested_time=q.suggested_time, option_feature=q.option_feature,
        break_logic=q.break_logic, trap_read=q.trap_read, trap_calc=q.trap_calc,
        trap_thought=q.trap_thought, error_path=q.error_path,
        normal_solve=q.normal_solve, quick_solve=q.quick_solve, identify_signal=q.identify_signal,
        step_detail=q.step_detail, practice_question=q.practice_question,
        practice_answer=q.practice_answer, answer=q.answer,
        background_knowledge=q.background_knowledge,
        ai_raw_content=q.ai_raw_content,
        card_title=q.card_title, card_tags=q.card_tags, card_summary=q.card_summary,
        create_time=now, first_study_time=now,
        master_level=1, review_count=0, next_review_time=now,
    )
    db.add(new_q)
    db.commit()
    db.refresh(new_q)

    # 入库后完整重算题型树计数（计数以题目表为唯一事实源，不靠增量累加，避免漂移）
    recalc_category_counts(db)
    update_daily_stat(db, "new")
    if q.is_error:
        update_daily_stat(db, "error")

    return {"id": new_q.id, "message": "题目入库成功"}


class QuestionUpdate(BaseModel):
    level1: Optional[str] = None
    level2: Optional[str] = None
    level3: Optional[str] = None
    level4: Optional[str] = None
    level5: Optional[str] = None
    question_raw: Optional[str] = None
    source: Optional[str] = None
    difficulty: Optional[int] = None
    is_error: Optional[bool] = None
    error_reason: Optional[str] = None
    tags: Optional[str] = None
    sub_point: Optional[str] = None
    exam_intent: Optional[str] = None
    difficulty_label: Optional[str] = None
    exam_priority: Optional[str] = None
    suggested_time: Optional[int] = None
    option_feature: Optional[str] = None
    break_logic: Optional[str] = None
    trap_read: Optional[str] = None
    trap_calc: Optional[str] = None
    trap_thought: Optional[str] = None
    error_path: Optional[str] = None
    normal_solve: Optional[str] = None
    quick_solve: Optional[str] = None
    identify_signal: Optional[str] = None
    step_detail: Optional[str] = None
    practice_question: Optional[str] = None
    practice_answer: Optional[str] = None
    answer: Optional[str] = None
    background_knowledge: Optional[str] = None
    master_level: Optional[int] = None
    is_favorite: Optional[bool] = None
    ai_raw_content: Optional[str] = None
    card_title: Optional[str] = None
    card_tags: Optional[str] = None
    card_summary: Optional[str] = None
    deposited: Optional[bool] = None


@router.put("/{question_id}")
def update_question(question_id: int, q: QuestionUpdate, db: Session = Depends(get_db)):
    existing = db.query(Question).filter(Question.id == question_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="题目不存在")

    update_data = q.dict(exclude_unset=True)
    level_changed = any(k in update_data for k in ("level1", "level2", "level3", "level4", "level5"))
    is_error_changed = "is_error" in update_data
    for key, value in update_data.items():
        setattr(existing, key, value)

    db.commit()

    # 重分类或错题状态变化后，完整重算题型树计数（计数以题目表为唯一事实源，不靠增量累加，避免漂移）
    if level_changed or is_error_changed:
        recalc_category_counts(db)

    return {"message": "更新成功", "level_changed": level_changed, "is_error_changed": is_error_changed}


@router.delete("/{question_id}")
def delete_question(question_id: int, db: Session = Depends(get_db)):
    existing = db.query(Question).filter(Question.id == question_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="题目不存在")
    db.delete(existing)
    db.commit()
    # 删除后完整重算题型树计数（保证前端题型树准确、不残留旧计数）
    recalc_category_counts(db)
    return {"message": "删除成功"}


def recalc_category_counts(db: Session):
    """基于题目表完整重算所有分类节点的计数（重分类后调用，保证题型树准确）"""
    cats = db.query(Category).all()
    questions = db.query(Question).all()
    for c in cats:
        cnt = 0
        err = 0
        for q in questions:
            match = True
            for lv in range(1, 6):
                cv = getattr(c, f"level{lv}")
                if cv:
                    if (getattr(q, f"level{lv}") or "") != cv:
                        match = False
                        break
            if match:
                cnt += 1
                if q.is_error:
                    err += 1
        c.question_count = cnt
        c.error_count = err
    db.commit()


class ParseRequest(BaseModel):
    ai_content: str


@router.post("/parse-only")
def parse_only(req: ParseRequest):
    """仅解析AI返回文本，不入库（预览用）"""
    parsed = parse_ai_content(req.ai_content)
    validation = validate_parsed_content(parsed)
    return {
        "parsed": parsed,
        "validation": validation,
    }


class QuickCreateRequest(BaseModel):
    """极简录入：粘贴AI返回内容；考点由AI的category_path自动识别，也支持手动覆盖"""
    ai_content: str
    level1: str = ""
    level2: str = ""
    level3: str = ""
    level4: str = ""
    level5: str = ""
    is_error: bool = False


@router.post("/quick-create")
def quick_create(req: QuickCreateRequest, db: Session = Depends(get_db)):
    """极简录入：粘贴AI返回内容，自动解析所有字段并入库"""
    parsed = parse_ai_content(req.ai_content)
    validation = validate_parsed_content(parsed)

    # 考点路径：以 AI 识别的 category_path 为准，手动覆盖优先
    levels = {}
    for lvl in range(1, 6):
        key = f"level{lvl}"
        levels[key] = (getattr(req, key) or "").strip() or parsed.get(key, "")

    now = datetime.now()
    new_q = Question(
        level1=levels["level1"], level2=levels["level2"], level3=levels["level3"],
        level4=levels["level4"], level5=levels["level5"],
        question_raw=parsed.get("question_raw", ""),
        source="", difficulty=3, priority=2,
        cost_time=parsed.get("suggested_time", 60) if isinstance(parsed.get("suggested_time"), int) else 60,
        is_error=req.is_error, tags="",
        sub_point=parsed.get("sub_point", ""),
        exam_intent=parsed.get("exam_intent", ""),
        difficulty_label=parsed.get("difficulty_label", ""),
        exam_priority=parsed.get("exam_priority", ""),
        suggested_time=parsed.get("suggested_time", 60) if isinstance(parsed.get("suggested_time"), int) else 60,
        option_feature=parsed.get("option_feature", ""),
        break_logic=parsed.get("break_logic", ""),
        trap_read=parsed.get("trap_read", ""),
        trap_calc=parsed.get("trap_calc", ""),
        trap_thought=parsed.get("trap_thought", ""),
        error_path=parsed.get("error_path", ""),
        normal_solve=parsed.get("normal_solve", ""),
        quick_solve=parsed.get("quick_solve", ""),
        identify_signal=parsed.get("identify_signal", ""),
        step_detail=parsed.get("step_detail", ""),
        practice_question=parsed.get("practice_question", ""),
        practice_answer=parsed.get("practice_answer", ""),
        answer=parsed.get("answer", ""),
        background_knowledge=parsed.get("background_knowledge", ""),
        card_title=parsed.get("card_title", ""),
        card_tags=parsed.get("card_tags", ""),
        card_summary=parsed.get("card_summary", ""),
        ai_raw_content=req.ai_content,
        deposited=False,
        create_time=now, first_study_time=now,
        master_level=1, review_count=0, next_review_time=now,
    )
    db.add(new_q)
    db.commit()
    db.refresh(new_q)

    # 入库后完整重算题型树计数（计数以题目表为唯一事实源，不靠增量累加，避免漂移）
    recalc_category_counts(db)
    update_daily_stat(db, "new")
    if req.is_error:
        update_daily_stat(db, "error")

    return {
        "id": new_q.id,
        "message": "解析入库成功",
        "validation": validation,
        "parsed_fields": {k: (v[:100] + "..." if isinstance(v, str) and len(v) > 100 else v)
                          for k, v in parsed.items() if k != "ai_raw_content"}
    }


@router.get("/aggregate/{level3}/{level4}")
def aggregate_questions(level3: str, level4: str, db: Session = Depends(get_db)):
    query = db.query(Question).filter(Question.level3 == level3)
    if level4 and level4 != "null":
        query = query.filter(Question.level4 == level4)
    questions = query.all()

    all_traps = []
    all_techniques = []
    all_signals = []
    for q in questions:
        if q.trap_read:
            all_traps.append({"type": "读题陷阱", "content": q.trap_read})
        if q.trap_calc:
            all_traps.append({"type": "计算陷阱", "content": q.trap_calc})
        if q.trap_thought:
            all_traps.append({"type": "思维误区", "content": q.trap_thought})
        if q.normal_solve:
            all_techniques.append(q.normal_solve)
        if q.identify_signal:
            all_signals.append(q.identify_signal)

    return {
        "total": len(questions),
        "questions": [format_question(q) for q in questions],
        "aggregated_traps": all_traps,
        "aggregated_techniques": list(set(all_techniques)),
        "aggregated_signals": list(set(all_signals)),
    }
