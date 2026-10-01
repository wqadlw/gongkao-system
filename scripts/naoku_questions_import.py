"""
考公脑库 10-真题 逐题深度标注 → 题库导入/回填

- 已存在（bank_imports.bank_qid 命中）的题目：仅回填空字段（非破坏性）
- 未存在的 qid：整题导入（题面 + 结构化字段 + BankImport 映射）
- 图片路径改写为 /api/naoku/media?path=90-图片/...（路由见 routers/resources.py）

用法：
    python scripts/naoku_questions_import.py --root data/kaogong-naoku [--limit 50]
"""
import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from database import SessionLocal, Question, BankImport, recalc_category_counts  # noqa: E402

RATING_EMOJI = re.compile(r"[\U0001F300-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\uFE0F]")
SECTION_RE = re.compile(r"^(##\s+.+|###\s+.+|\*\*问法模型\*\*：.*|\*\*同类特征\*\*：.*)$", re.M)


def clean(text: str) -> str:
    """去 emoji + 收敛空行"""
    text = RATING_EMOJI.sub("", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def strip_html_tags_for_len(text: str) -> str:
    return text


def rewrite_images(text: str) -> str:
    return text.replace("../../../90-图片/", "/api/resources/naoku/media?path=90-图片/")


def parse_front_matter(text: str) -> dict:
    m = re.match(r"\A---\s*\n(.*?)\n---\s*\n", text, re.S)
    meta = {}
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                key, _, val = line.partition(":")
                meta[key.strip()] = val.strip().strip('"').strip("'")
        text = text[m.end():]
    return meta, text


def parse_sections(body: str) -> dict:
    """按标题切块，返回 {小节名: 内容}"""
    sections = {}
    current = "_head"
    sections[current] = []
    for line in body.splitlines():
        m = re.match(r"^(#{2,3})\s+(.+)$", line)
        if m:
            current = m.group(2).strip()
            sections[current] = []
            continue
        sections.setdefault(current, []).append(line)
    return {k: "\n".join(v).strip() for k, v in sections.items()}


def extract_field(body: str, name: str) -> str:
    """提取 **字段名**：单行字段"""
    m = re.search(r"\*\*" + name + r"\*\*：(.*)", body)
    return clean(m.group(1)) if m else ""


def parse_options(block: str):
    """选项块 → (选项行列表, 答案字母)；须传入未 clean 的原文（✅ 是答案标记）"""
    options, answer = [], ""
    for line in block.splitlines():
        line = line.strip()
        if not line:
            continue
        m = re.match(r"^-\s+([A-H])[.、．]\s*(.*)$", line)
        if m:
            correct = "✅" in line
            if correct:
                answer = m.group(1)
            text = clean(m.group(2).replace("✅", "").strip())
            options.append(f"- **{m.group(1)}**. {text}")
    return options, answer


def parse_note(path: Path, module: str, da_lei: str):
    meta, text = parse_front_matter(path.read_text(encoding="utf-8"))
    qid = meta.get("qid", "")
    if not qid:
        return None
    sections = parse_sections(text)

    # 找到分隔线后的题面区（### 题干 / 选项 / 官方解析 / 给定材料）
    # 选项块必须用未 clean 的原文（✅ 是答案标记），其余字段走 clean
    stem = clean(rewrite_images(sections.get("题干", "")))
    options, answer = parse_options(rewrite_images(sections.get("选项", "")))
    analysis = clean(rewrite_images(sections.get("官方解析", "")))
    material = clean(rewrite_images(sections.get("给定材料", "")))

    body = "\n".join(sections.get("_head", []))
    # 题面区之前的全文（单行字段可能出现在任意 ## 小节之后，用全文做 **字段** 提取）
    head_full = text.split("\n### 题干")[0]
    identify = extract_field(head_full, "问法模型")
    # 推理链小节可能把「**最快解法**：…」单行并进来，剔除后单独提取
    logic_raw = sections.get("推理链", "")
    break_logic = clean(rewrite_images(
        "\n".join(l for l in logic_raw.splitlines() if not l.startswith("**最快解法**"))))
    quick = clean(extract_field(head_full, "最快解法"))
    error_path = clean(rewrite_images(sections.get("易错点", "")))
    mother = clean(rewrite_images(sections.get("母题抽象", "")))
    same_feat = extract_field(head_full, "同类特征")
    background = "\n".join(x for x in (mother, ("同类特征：" + same_feat) if same_feat else "") if x)

    kao_dian_leaf = meta.get("考点", "").split(" / ")[-1]

    raw_parts = []
    if material:
        raw_parts.append(material)
    if stem:
        raw_parts.append(stem)
    raw_parts.extend(options)
    question_raw = "\n\n".join([p for p in raw_parts if p])

    return {
        "qid": qid,
        "module": module,
        "level1": module,
        "level2": da_lei,
        "level3": kao_dian_leaf,
        "sub_point": kao_dian_leaf,
        "source": meta.get("试卷", ""),
        "region": meta.get("地区", ""),
        "year": meta.get("年份", ""),
        "question_raw": question_raw,
        "answer": answer,
        "normal_solve": analysis,
        "ai_raw_content": material,
        "identify_signal": identify,
        "break_logic": break_logic,
        "quick_solve": quick,
        "error_path": error_path,
        "background_knowledge": background,
    }


def main():
    parser = argparse.ArgumentParser(description="考公脑库逐题标注 → 题库导入/回填")
    parser.add_argument("--root", required=True, help="脑库克隆根目录")
    parser.add_argument("--limit", type=int, default=0, help="限制处理数量（0=全部）")
    args = parser.parse_args()

    root = Path(args.root) / "10-真题"
    notes = sorted(root.glob("*/*/*.md"))
    if args.limit:
        notes = notes[: args.limit]
    print(f"待处理笔记：{len(notes)}")

    db = SessionLocal()
    qid_map = {b.bank_qid: b.question_id for b in db.query(BankImport).filter(BankImport.bank_qid != "").all()}
    print(f"已有 bank_qid 映射：{len(qid_map)}")

    imported, enriched, skipped = 0, 0, 0
    for note in notes:
        parsed = parse_note(note, note.relative_to(root).parts[0], note.relative_to(root).parts[1])
        if not parsed or not parsed["question_raw"] or not parsed["answer"]:
            skipped += 1
            continue

        exist_id = qid_map.get(parsed["qid"])
        if exist_id:
            # 回填空字段（非破坏性）
            q = db.query(Question).filter(Question.id == exist_id).first()
            if q is None:
                skipped += 1
                continue
            for field in ("identify_signal", "break_logic", "quick_solve", "error_path",
                          "background_knowledge", "sub_point", "normal_solve"):
                if not getattr(q, field) and parsed[field]:
                    setattr(q, field, parsed[field])
            enriched += 1
        else:
            tags = "真题｜脑库标注" + (f"｜{parsed['module']}")
            q = Question(
                level1=parsed["level1"], level2=parsed["level2"], level3=parsed["level3"],
                question_raw=parsed["question_raw"],
                source=parsed["source"], difficulty=3,
                answer=parsed["answer"],
                normal_solve=parsed["normal_solve"],
                ai_raw_content=parsed["ai_raw_content"],
                sub_point=parsed["sub_point"],
                identify_signal=parsed["identify_signal"],
                break_logic=parsed["break_logic"],
                quick_solve=parsed["quick_solve"],
                error_path=parsed["error_path"],
                background_knowledge=parsed["background_knowledge"],
                tags=tags,
            )
            db.add(q)
            db.flush()
            db.add(BankImport(bank_qid=parsed["qid"], question_id=q.id,
                              source_file=parsed["source"] + ".md",
                              module=parsed["module"]))
            qid_map[parsed["qid"]] = q.id
            imported += 1

    if imported or enriched:
        recalc_category_counts(db)
    db.commit()
    print(f"完成：导入 {imported} 题，回填 {enriched} 题，跳过 {skipped} 篇")
    db.close()


if __name__ == "__main__":
    main()
