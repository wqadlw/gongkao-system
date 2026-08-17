"""笔记管理路由 v2 - 支持AI追问生成的结构化笔记"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from database import get_db, Note, Question, Knowledge, SolveItem
from services.parser import parse_note_content, _extract_stem

router = APIRouter(prefix="/api/notes", tags=["笔记管理"])


# 笔记按模块定制章节顺序（单一事实源：模块 → 笔记章节）
# 每项为 (字段键, 章节标题)；字段键映射到下方 raw 字段。
MODULE_NOTE_SECTIONS = {
    "言语理解与表达": [
        ("knowledge", "涉及知识点"),
        ("logic", "文段结构与破题逻辑"),
        ("solve", "标准解题步骤"),
        ("pitfalls", "避坑要点"),
        ("speed", "提速技巧"),
    ],
    "数量关系": [
        ("speed", "秒杀/速算技巧"),
        ("logic", "破题逻辑链"),
        ("solve", "标准解题步骤"),
        ("pitfalls", "避坑要点"),
        ("knowledge", "涉及知识点"),
    ],
    "判断推理": [
        ("logic", "规律识别/逻辑链"),
        ("solve", "标准解题步骤"),
        ("speed", "速算与技巧"),
        ("pitfalls", "避坑要点"),
        ("knowledge", "涉及知识点"),
    ],
    "资料分析": [
        ("speed", "速算公式与技巧"),
        ("solve", "列式与计算步骤"),
        ("pitfalls", "避坑要点（口径/单位）"),
        ("knowledge", "涉及知识点"),
    ],
    "常识判断": [
        ("knowledge", "知识点溯源"),
        ("logic", "解题思路"),
        ("pitfalls", "辨析要点"),
    ],
    "政治理论": [
        ("knowledge", "理论依据与原文"),
        ("logic", "解题思路"),
        ("pitfalls", "易混辨析"),
    ],
}
# 无专属配置时回退到通用顺序
DEFAULT_NOTE_SECTIONS = [
    ("knowledge", "涉及知识点"),
    ("logic", "解题逻辑链"),
    ("solve", "标准解题步骤"),
    ("pitfalls", "避坑要点"),
    ("speed", "提速技巧"),
]



@router.get("/list")
def get_notes(
    level1: Optional[str] = None, level5: Optional[str] = None, is_collect: Optional[bool] = None,
    keyword: Optional[str] = None, db: Session = Depends(get_db)
):
    query = db.query(Note)
    if level1:
        query = query.filter(Note.level1 == level1)
    if level5:
        query = query.filter(Note.level5 == level5)
    if is_collect is not None:
        query = query.filter(Note.is_collect == is_collect)
    if keyword:
        query = query.filter(Note.note_content.like(f"%{keyword}%"))

    notes = query.order_by(Note.create_time.desc()).all()
    return [{
        "id": n.id, "question_id": n.question_id,
        "level1": n.level1, "level2": n.level2, "level3": n.level3,
        "level4": n.level4, "level5": n.level5,
        "note_content": n.note_content,
        "question_display": n.question_display, "question_stem": n.question_stem,
        "type_judgment": n.type_judgment,
        "knowledge_points": n.knowledge_points, "logic_chain": n.logic_chain,
        "solve_steps": n.solve_steps, "pitfalls": n.pitfalls, "speed_tips": n.speed_tips,
        "card_title": n.card_title, "card_tags": n.card_tags, "card_summary": n.card_summary,
        "create_time": n.create_time.strftime("%Y-%m-%d %H:%M") if n.create_time else "",
        "is_collect": n.is_collect,
    } for n in notes]


@router.get("/{note_id}")
def get_note(note_id: int, db: Session = Depends(get_db)):
    n = db.query(Note).filter(Note.id == note_id).first()
    if not n:
        raise HTTPException(status_code=404, detail="笔记不存在")
    return {
        "id": n.id, "question_id": n.question_id,
        "level1": n.level1, "level2": n.level2, "level3": n.level3,
        "level4": n.level4, "level5": n.level5,
        "note_content": n.note_content,
        "question_display": n.question_display, "question_stem": n.question_stem,
        "type_judgment": n.type_judgment,
        "knowledge_points": n.knowledge_points, "logic_chain": n.logic_chain,
        "solve_steps": n.solve_steps, "pitfalls": n.pitfalls, "speed_tips": n.speed_tips,
        "card_title": n.card_title, "card_tags": n.card_tags, "card_summary": n.card_summary,
        "create_time": n.create_time.strftime("%Y-%m-%d %H:%M") if n.create_time else "",
        "is_collect": n.is_collect,
    }


class NoteCreate(BaseModel):
    question_id: Optional[int] = None
    level1: str = ""
    level2: str = ""
    level5: str = ""
    note_content: str = ""
    # 结构化字段（AI追问生成）
    question_display: str = ""
    question_stem: str = ""
    type_judgment: str = ""
    knowledge_points: str = ""
    logic_chain: str = ""
    solve_steps: str = ""
    pitfalls: str = ""
    speed_tips: str = ""
    card_title: str = ""
    card_tags: str = ""
    card_summary: str = ""


@router.post("/")
def create_note(n: NoteCreate, db: Session = Depends(get_db)):
    new_n = Note(
        question_id=n.question_id,
        level1=n.level1, level2=n.level2, level5=n.level5,
        note_content=n.note_content,
        question_display=n.question_display, question_stem=n.question_stem, type_judgment=n.type_judgment,
        knowledge_points=n.knowledge_points, logic_chain=n.logic_chain,
        solve_steps=n.solve_steps, pitfalls=n.pitfalls, speed_tips=n.speed_tips,
        card_title=n.card_title, card_tags=n.card_tags, card_summary=n.card_summary,
        is_collect=False,
    )
    db.add(new_n)
    db.commit()
    db.refresh(new_n)
    return {"id": new_n.id, "message": "笔记已保存"}


class NoteFromAIRequest(BaseModel):
    """从AI返回的备考笔记内容创建笔记"""
    ai_note_content: str
    question_id: Optional[int] = None
    level1: str = ""
    level2: str = ""
    level5: str = ""


@router.post("/parse-only")
def parse_note_only(req: NoteFromAIRequest):
    """仅解析备考笔记内容用于预览，不入库"""
    parsed = parse_note_content(req.ai_note_content)
    return {"parsed": parsed}


@router.post("/from-ai")
def create_note_from_ai(req: NoteFromAIRequest, db: Session = Depends(get_db)):
    """解析AI返回的备考笔记并入库"""
    parsed = parse_note_content(req.ai_note_content)

    # 若关联题目，则补全模块/层级路径（便于按模块筛选），手动覆盖优先
    lv = {
        "level1": req.level1 or "",
        "level2": req.level2 or "",
        "level3": "", "level4": "",
        "level5": req.level5 or parsed.get("level5") or "",
    }
    if req.question_id:
        q = db.query(Question).filter(Question.id == req.question_id).first()
        if q:
            lv["level1"] = lv["level1"] or q.level1
            lv["level2"] = lv["level2"] or q.level2
            lv["level3"] = q.level3
            lv["level4"] = q.level4
            lv["level5"] = lv["level5"] or q.level5

    new_n = Note(
        question_id=req.question_id,
        level1=lv["level1"], level2=lv["level2"], level3=lv["level3"],
        level4=lv["level4"], level5=lv["level5"],
        note_content=parsed["note_content"],
        question_display=parsed["question_display"],
        question_stem=parsed.get("question_stem") or _extract_stem(parsed.get("question_display", "")),
        type_judgment=parsed["type_judgment"],
        knowledge_points=parsed["knowledge_points"],
        logic_chain=parsed["logic_chain"],
        solve_steps=parsed["solve_steps"],
        pitfalls=parsed["pitfalls"],
        speed_tips=parsed["speed_tips"],
        card_title=parsed.get("card_title", ""), card_tags=parsed.get("card_tags", ""),
        card_summary=parsed.get("card_summary", ""),
        is_collect=False,
    )
    db.add(new_n)
    db.commit()
    db.refresh(new_n)
    return {"id": new_n.id, "message": "备考笔记已入库", "parsed": parsed}


class NoteGenerateRequest(BaseModel):
    """从已入库题目的结构化字段一键生成备考笔记"""
    question_id: int


@router.post("/generate-from-question")
def generate_note_from_question(req: NoteGenerateRequest, db: Session = Depends(get_db)):
    """一键生成备考笔记：基于题目结构化字段拼装，并合并本题关联的知识库/解题库沉淀，
    自动派生卡片缩略信息（card_title/card_tags/card_summary），无需二次调用 AI。"""
    q = db.query(Question).filter(Question.id == req.question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="题目不存在")

    # 题型判定 = 完整题型树路径
    path = [q.level1, q.level2, q.level3, q.level4, q.level5]
    type_judgment = " > ".join([p for p in path if p]) or "未分类"

    # 涉及知识点
    kp_parts = []
    if q.sub_point:
        kp_parts.append(q.sub_point.strip())
    if q.exam_intent:
        kp_parts.append(q.exam_intent.strip())
    knowledge_points = "\n\n".join(kp_parts)

    logic_chain = (q.break_logic or "").strip()
    solve_steps = (q.step_detail or "").strip()

    # 避坑要点
    pit_parts = []
    if q.trap_read:
        pit_parts.append("读题陷阱：" + q.trap_read.strip())
    if q.trap_calc:
        pit_parts.append("计算陷阱：" + q.trap_calc.strip())
    if q.trap_thought:
        pit_parts.append("思维误区：" + q.trap_thought.strip())
    if q.error_path:
        pit_parts.append("常见错误路径：" + q.error_path.strip())
    pitfalls = "\n\n".join(pit_parts)

    # 提速技巧
    sp_parts = []
    if q.quick_solve:
        sp_parts.append(q.quick_solve.strip())
    if q.identify_signal:
        sp_parts.append("题型识别信号：" + q.identify_signal.strip())
    if q.normal_solve:
        sp_parts.append("常规解法：" + q.normal_solve.strip())
    speed_tips = "\n\n".join(sp_parts)

    question_display = (q.question_raw or "").strip()
    question_stem = _extract_stem(q.question_raw)

    # ---------- 升级：合并本题关联的知识库 / 解题库沉淀 ----------
    kg_entries = db.query(Knowledge).filter(Knowledge.source_question_id == q.id).all()
    sl_entries = db.query(SolveItem).filter(SolveItem.source_question_id == q.id).all()
    merged_tags = []
    kg_blocks, sl_blocks = [], []
    for e in kg_entries:
        title = e.card_title or e.title
        summary = e.card_summary or e.content
        kg_blocks.append(f"- {title}：{summary}")
        if e.card_tags:
            merged_tags += [t.strip() for t in e.card_tags.split("｜") if t.strip()]
    for e in sl_entries:
        title = e.card_title or e.title
        summary = e.card_summary or e.content
        sl_blocks.append(f"- 【{e.solve_type}】{title}：{summary}")
        if e.card_tags:
            merged_tags += [t.strip() for t in e.card_tags.split("｜") if t.strip()]
    if kg_blocks:
        knowledge_points = (knowledge_points + "\n\n" if knowledge_points else "") + \
            "【关联知识库沉淀】\n" + "\n".join(kg_blocks)
    if sl_blocks:
        solve_steps = (solve_steps + "\n\n" if solve_steps else "") + \
            "【关联解题库沉淀】\n" + "\n".join(sl_blocks)

    # 卡片缩略信息（由本题派生，无需 AI）
    card_title = (q.level5 or q.level2 or q.level1 or "综合笔记")[:18]
    card_tags = "｜".join(dict.fromkeys(merged_tags))[:60]
    card_summary = (knowledge_points or solve_steps or "").replace("\n", " ")[:70]

    # 按模块定制的章节顺序（单一事实源：模块 → 笔记章节）
    sections = MODULE_NOTE_SECTIONS.get(q.level1, DEFAULT_NOTE_SECTIONS)
    field_map = {
        "knowledge": knowledge_points,
        "logic": logic_chain,
        "solve": solve_steps,
        "pitfalls": pitfalls,
        "speed": speed_tips,
    }

    # 组装完整 Markdown（无表情符号，题目用代码框标注；按模块章节顺序）
    blocks = ["```", question_display, "```", "", "题型判定", type_judgment]
    for key, label in sections:
        content = field_map.get(key, "")
        if content:
            blocks += ["", label, content]
    note_content = "\n".join(blocks)

    parsed = {
        "question_display": question_display,
        "question_stem": question_stem,
        "type_judgment": type_judgment,
        "knowledge_points": knowledge_points,
        "logic_chain": logic_chain,
        "solve_steps": solve_steps,
        "pitfalls": pitfalls,
        "speed_tips": speed_tips,
        "card_title": card_title,
        "card_tags": card_tags,
        "card_summary": card_summary,
        "note_content": note_content,
        "merged_knowledge": len(kg_entries),
        "merged_solve": len(sl_entries),
    }

    # 同一题目重复生成则更新，避免冗余
    existing = db.query(Note).filter(Note.question_id == q.id).first()
    if existing:
        existing.level1, existing.level2 = q.level1, q.level2
        existing.level3, existing.level4, existing.level5 = q.level3, q.level4, q.level5
        existing.question_display = question_display
        existing.question_stem = question_stem
        existing.type_judgment = type_judgment
        existing.knowledge_points = knowledge_points
        existing.logic_chain = logic_chain
        existing.solve_steps = solve_steps
        existing.pitfalls = pitfalls
        existing.speed_tips = speed_tips
        existing.card_title = card_title
        existing.card_tags = card_tags
        existing.card_summary = card_summary
        existing.note_content = note_content
        db.commit()
        db.refresh(existing)
        note = existing
        msg = "笔记已更新"
    else:
        note = Note(
            question_id=q.id, level1=q.level1, level2=q.level2, level3=q.level3,
            level4=q.level4, level5=q.level5,
            question_display=question_display, question_stem=question_stem, type_judgment=type_judgment,
            knowledge_points=knowledge_points, logic_chain=logic_chain,
            solve_steps=solve_steps, pitfalls=pitfalls, speed_tips=speed_tips,
            card_title=card_title, card_tags=card_tags, card_summary=card_summary,
            note_content=note_content, is_collect=False,
        )
        db.add(note)
        db.commit()
        db.refresh(note)
        msg = "笔记已生成"

    if kg_entries or sl_entries:
        msg += f"（已合并知识库 {len(kg_entries)} 条 / 解题库 {len(sl_entries)} 条）"
    return {"id": note.id, "message": msg, "parsed": parsed}


class NoteUpdate(BaseModel):
    note_content: Optional[str] = None
    is_collect: Optional[bool] = None
    question_display: Optional[str] = None
    question_stem: Optional[str] = None
    type_judgment: Optional[str] = None
    knowledge_points: Optional[str] = None
    logic_chain: Optional[str] = None
    solve_steps: Optional[str] = None
    pitfalls: Optional[str] = None
    speed_tips: Optional[str] = None
    card_title: Optional[str] = None
    card_tags: Optional[str] = None
    card_summary: Optional[str] = None


@router.put("/{note_id}")
def update_note(note_id: int, n: NoteUpdate, db: Session = Depends(get_db)):
    existing = db.query(Note).filter(Note.id == note_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="笔记不存在")

    update_data = n.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(existing, key, value)

    db.commit()
    return {"message": "更新成功"}


@router.delete("/{note_id}")
def delete_note(note_id: int, db: Session = Depends(get_db)):
    existing = db.query(Note).filter(Note.id == note_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="笔记不存在")
    db.delete(existing)
    db.commit()
    return {"message": "删除成功"}


@router.get("/export/all")
def export_all_notes(db: Session = Depends(get_db)):
    notes = db.query(Note).all()
    return [{
        "id": n.id, "question_id": n.question_id,
        "level1": n.level1, "level2": n.level2, "level3": n.level3,
        "level4": n.level4, "level5": n.level5,
        "note_content": n.note_content,
        "create_time": n.create_time.strftime("%Y-%m-%d %H:%M") if n.create_time else "",
        "is_collect": n.is_collect,
    } for n in notes]
