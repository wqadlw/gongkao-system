"""学习手册导出 — 按 NovaForge exam-review 模板结构，把系统数据组装为 Markdown 冲刺手册

结构：考情速览 → 薄弱考点 TOP10 → 考点速查（核心立场）→ 公式速查 → 知识点速览 → 我的错题本
数据全部来自本系统（题目统计 / 资料库考点精讲 / 行测知识库 / 错题本），零外部依赖。
模板结构参考 NovaForge（MIT），仅借用章节组织，不复制其内容。
"""
import json
from collections import defaultdict
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from database import get_db, Question, Knowledge, Resource

router = APIRouter(prefix="/api/handbook", tags=["学习手册"])

MODULES = ["政治理论", "常识判断", "言语理解与表达", "数量关系", "判断推理", "资料分析"]


@router.get("/modules")
def handbook_modules(db: Session = Depends(get_db)):
    """各模块的数据概况（供导出前预览）"""
    out = []
    for mod in MODULES:
        questions = db.query(Question).filter(Question.level1 == mod).all()
        out.append({
            "module": mod,
            "total": len(questions),
            "errors": sum(1 for q in questions if q.is_error),
            "mastered": sum(1 for q in questions if q.master_level >= 4),
        })
    return {"items": out}


def _build_handbook(db: Session, module: str) -> str:
    if module not in MODULES:
        raise HTTPException(status_code=400, detail="无效模块")
    questions = db.query(Question).filter(Question.level1 == module).all()
    total = len(questions)
    errors = [q for q in questions if q.is_error]
    mastered = sum(1 for q in questions if q.master_level >= 4)
    avg_mastery = round(sum(q.master_level for q in questions) / total, 1) if total else 0

    lines = [
        f"# {module} 考前冲刺手册",
        "",
        f"> 生成日期：{datetime.now().strftime('%Y-%m-%d')} · 题量 {total} · 掌握 {mastered} · 平均掌握度 {avg_mastery}/5",
        "",
        "---",
        "",
        "## 考情速览",
        "",
        "| 项目 | 数值 |",
        "|------|------|",
        f"| 题目总数 | {total} |",
        f"| 错题数 | {len(errors)} |",
        f"| 已掌握（≥4级） | {mastered} |",
        f"| 平均掌握度 | {avg_mastery} / 5 |",
        "",
    ]

    # 薄弱考点 TOP10（错误率×50 + (5-掌握)×10，与统计引擎口径一致）
    point_stats = defaultdict(lambda: {"total": 0, "error": 0, "mastery": 0})
    for q in questions:
        if q.level3 and q.level4:
            key = (q.level3, q.level4)
            s = point_stats[key]
            s["total"] += 1
            s["error"] += 1 if q.is_error else 0
            s["mastery"] += q.master_level
    weak = sorted(
        (
            {
                "name": f"{l3} / {l4}",
                "total": s["total"], "error": s["error"],
                "score": s["error"] / s["total"] * 50 + (5 - s["mastery"] / s["total"]) * 10,
            }
            for (l3, l4), s in point_stats.items()
        ),
        key=lambda x: -x["score"],
    )[:10]
    if weak:
        lines += ["## 薄弱考点 TOP10", "", "| 考点 | 题数 | 错题 |", "|------|------|------|"]
        lines += [f"| {w['name']} | {w['total']} | {w['error']} |" for w in weak]
        lines += ["", "---", ""]

    # 考点速查：资料库「考点精讲」中该模块的 MOC（按大类分组，标题 + 核心立场一句）
    resources = db.query(Resource).filter(Resource.category == "考点精讲").all()
    by_da_lei = defaultdict(list)
    for r in resources:
        if r.sub_path.startswith(module + "/"):
            stance = ""
            if r.content:
                m = r.content.split("## 真题（跨卷聚合）")[0]
                stance_lines = [
                    l.lstrip("- ").strip() for l in m.splitlines()
                    if l.strip() and not l.startswith(("#", ">", "##"))
                ]
                if stance_lines:
                    stance = "；".join(stance_lines)[:120]
            by_da_lei[r.sub_path.split("/", 1)[1] if "/" in r.sub_path else r.sub_path].append(
                (r.title, stance)
            )
    if by_da_lei:
        lines += ["## 考点速查（核心立场）", "", "> 摘自资料库「考点精讲」，完整版见系统内对应条目。", ""]
        for da_lei in sorted(by_da_lei):
            lines += [f"### {da_lei}", ""]
            for title, stance in sorted(by_da_lei[da_lei]):
                lines.append(f"- **{title}**" + (f"：{stance}" if stance else ""))
            lines.append("")
        lines += ["---", ""]

    # 公式速查 + 知识点速览（行测知识库）
    kbs = db.query(Knowledge).filter(Knowledge.module == module).all()
    formulas = [k for k in kbs if k.kg_type == "公式"]
    if formulas:
        lines += ["## 公式速查", ""]
        for k in formulas:
            lines += [f"### {k.title}", "", (k.content or "").strip(), ""]
    others = [k for k in kbs if k.kg_type != "公式"]
    if others:
        lines += ["## 知识点速览", ""]
        for k in others:
            summary = (k.card_summary or (k.content or "")[:100]).strip()
            lines.append(f"- **{k.kg_type}·{k.title}**：{summary[:100]}")
        lines += ["", "---", ""]

    # 我的错题本（按 level2/level3 分组）
    if errors:
        groups = defaultdict(list)
        for q in errors:
            groups[" / ".join(x for x in (q.level2, q.level3) if x) or "未分类"].append(q)
        lines += ["## 我的错题本", "", f"> 共 {len(errors)} 道，按考点分组。复习时先遮住答案自测。", ""]
        for group in sorted(groups):
            lines += [f"### {group}（{len(groups[group])} 题）", ""]
            for q in groups[group]:
                stem = (q.question_raw or "").replace("\n", " ")
                stem = re.sub(r"<[^>]+>", "", stem)[:80]
                lines.append(f"- {stem}…　**答案：{q.answer or '—'}**")
            lines.append("")

    lines += ["---", "", f"*本手册由公考行测知识库系统生成（{datetime.now().strftime('%Y-%m-%d %H:%M')}），结构参考 NovaForge exam-review 模板（MIT）。*"]
    return "\n".join(lines)


import re  # noqa: E402  （错题本题干清洗用）


@router.get("/export")
def export_handbook(module: str, db: Session = Depends(get_db)):
    from urllib.parse import quote

    md = _build_handbook(db, module)
    filename = f"{module}_冲刺手册_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    encoded = quote(filename)
    return Response(
        content=md, media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename=\"handbook.md\"; filename*=UTF-8''{encoded}"},
    )
