"""全局搜索 —— 跨「题目 + 行测知识库 + 行测解题库」联合检索

把顶栏搜索从「只搜题目」升级为跨库检索，返回按板块分组的结果，
前端结果页可一键跳转到对应详情 / 列表（列表页已支持 ?keyword= 深链）。
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from database import get_db, Question, Knowledge, SolveItem

router = APIRouter(prefix="/api/search", tags=["全局搜索"])


def _snippet(text, kw, width=60):
    """截取关键词附近的文本片段，便于结果预览"""
    if not text:
        return ""
    text = " ".join(str(text).split())
    idx = text.find(kw)
    if idx < 0:
        return text[:width]
    start = max(0, idx - width // 2)
    end = min(len(text), start + width)
    snippet = text[start:end]
    if start > 0:
        snippet = "…" + snippet
    if end < len(text):
        snippet = snippet + "…"
    return snippet


@router.get("")
def global_search(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    limit: int = Query(15, ge=1, le=50),
    db: Session = Depends(get_db),
):
    kw = f"%{q}%"

    # 题目：题干 / 细分考点 / 考察意图 / 答案
    questions = (
        db.query(Question)
        .filter(
            or_(
                Question.question_raw.like(kw),
                Question.sub_point.like(kw),
                Question.exam_intent.like(kw),
                Question.answer.like(kw),
            )
        )
        .order_by(Question.create_time.desc())
        .limit(limit)
        .all()
    )
    q_res = [
        {
            "id": x.id,
            "title": (x.question_raw or "").replace("\n", " ")[:80],
            "module": x.level1,
            "level3": x.level3,
            "sub_point": x.sub_point,
            "route": f"/question/{x.id}",
        }
        for x in questions
    ]

    # 行测知识库：标题 / 内容 / 标签
    knowledge = (
        db.query(Knowledge)
        .filter(
            or_(
                Knowledge.title.like(kw),
                Knowledge.content.like(kw),
                Knowledge.tags.like(kw),
            )
        )
        .order_by(Knowledge.id.desc())
        .limit(limit)
        .all()
    )
    k_res = [
        {
            "id": x.id,
            "title": x.title,
            "module": x.module,
            "kg_type": x.kg_type,
            "snippet": _snippet(x.content, q),
            "route": f"/knowledge?keyword={q}",
        }
        for x in knowledge
    ]

    # 行测解题库：标题 / 内容 / 标签
    solve = (
        db.query(SolveItem)
        .filter(
            or_(
                SolveItem.title.like(kw),
                SolveItem.content.like(kw),
                SolveItem.tags.like(kw),
            )
        )
        .order_by(SolveItem.id.desc())
        .limit(limit)
        .all()
    )
    s_res = [
        {
            "id": x.id,
            "title": x.title,
            "module": x.module,
            "solve_type": x.solve_type,
            "snippet": _snippet(x.content, q),
            "route": f"/solve-library?keyword={q}",
        }
        for x in solve
    ]

    total = len(q_res) + len(k_res) + len(s_res)
    return {
        "query": q,
        "total": total,
        "questions": q_res,
        "knowledge": k_res,
        "solve": s_res,
    }
