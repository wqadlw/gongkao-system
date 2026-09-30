"""
xingcezhenti 真题库对接服务
解析本地 xingcezhenti 仓库（2016-2026 国考+省考行测真题 markdown），
供浏览与一键导入本系统题库使用。纯本地文件读取，零联网。
"""
import os
import re
from urllib.parse import quote

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend/
PROJECT_DIR = os.path.dirname(BASE_DIR)

# 仓库根目录：环境变量 XINGCE_BANK_DIR 可覆盖，默认项目根下 xingcezhenti/
BANK_DIR = os.environ.get("XINGCE_BANK_DIR") or os.path.join(PROJECT_DIR, "xingcezhenti")

MODULE_DIRS = [
    "01-政治理论",
    "02-常识判断",
    "03-言语理解与表达",
    "04-数量关系",
    "05-判断推理",
    "06-资料分析",
]

MEDIA_DIR_NAME = "90-图片"

# 与 markdown 内标题对应的正则
RE_FRONT_MATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)
RE_MATERIAL = re.compile(r"^##\s+材料\s*(\d+)")
RE_QUESTION = re.compile(r"^#{2,3}\s+第\s*(\d+)\s*题\s*(?:<sub>qid\s*(\d+)\s*·\s*(.*?)</sub>)?")
RE_OPTION = re.compile(r"^- \*\*([A-H])\*\*\.\s*(.*)$")
RE_ANSWER = re.compile(r"^\*\*答案\*\*：\s*(.*)$")
RE_ANALYSIS = re.compile(r"^\*\*官方解析\*\*")
RE_IMG = re.compile(r'src="([^"]+)"')


def is_available():
    return os.path.isdir(BANK_DIR)


def list_modules():
    """返回各模块目录名与文件数"""
    modules = []
    for d in MODULE_DIRS:
        path = os.path.join(BANK_DIR, d)
        count = 0
        if os.path.isdir(path):
            count = len([f for f in os.listdir(path) if f.endswith(".md")])
        modules.append({"dir": d, "name": d[3:], "file_count": count})
    return modules


def _parse_meta(text):
    meta = {}
    m = RE_FRONT_MATTER.match(text)
    if not m:
        return meta
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        meta[key.strip()] = val.strip().strip('"').strip("'")
    return meta


def _rewrite_img_srcs(html, file_dir):
    """把 markdown/HTML 内相对图片路径改写为本系统媒体接口地址"""
    def repl(m):
        src = m.group(1).strip()
        if src.startswith(("http://", "https://", "/api/", "data:")):
            return m.group(0)
        abs_path = os.path.normpath(os.path.join(file_dir, src))
        root = os.path.normpath(BANK_DIR)
        if not abs_path.startswith(root + os.sep):
            return m.group(0)
        rel = os.path.relpath(abs_path, root).replace("\\", "/")
        return f'src="/api/question-bank/media?path={quote(rel)}"'

    return RE_IMG.sub(repl, html)


def _clean_option_text(text):
    return text.replace("✅", "").rstrip()


def parse_bank_file(filename, module_dir):
    """解析单个试卷 md → {meta, materials, questions}

    questions 每项: {no, qid, subtype, material_no, stem, options, answer, analysis}
    options 每项: {label, text, correct}
    """
    path = os.path.join(BANK_DIR, module_dir, filename)
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    meta = _parse_meta(text)
    file_dir = os.path.dirname(path)

    body = RE_FRONT_MATTER.sub("", text, count=1)
    questions = []
    materials = {}
    current_material = None
    cur = None
    stage = "stem"  # stem / options / analysis
    stem_lines, analysis_lines = [], []

    def flush():
        nonlocal cur, stage, stem_lines, analysis_lines
        if cur is not None:
            cur["stem"] = _rewrite_img_srcs("\n".join(stem_lines).strip("\n"), file_dir)
            cur["analysis"] = _rewrite_img_srcs("\n".join(analysis_lines).strip("\n"), file_dir)
            questions.append(cur)
        cur, stage, stem_lines, analysis_lines = None, "stem", [], []

    for raw_line in body.splitlines():
        line = raw_line.rstrip()
        m = RE_MATERIAL.match(line)
        if m:
            flush()
            current_material = int(m.group(1))
            materials[current_material] = ""
            stage = "material"
            continue
        m = RE_QUESTION.match(line)
        if m:
            flush()
            cur = {
                "no": int(m.group(1)),
                "qid": m.group(2) or "",
                "subtype": (m.group(3) or "").strip(),
                "material_no": current_material,
                "options": [],
            }
            stage = "stem"
            continue
        if line.strip() == "---":
            flush()
            stage = "stem" if current_material is None else "material_idle"
            continue
        if cur is not None:
            m = RE_OPTION.match(line)
            if m:
                stage = "options"
                cur["options"].append({
                    "label": m.group(1),
                    "text": _rewrite_img_srcs(_clean_option_text(m.group(2)).strip(), file_dir),
                    "correct": "✅" in line,
                })
                continue
            if RE_ANSWER.match(line):
                cur["answer"] = RE_ANSWER.match(line).group(1).strip()
                stage = "post_answer"
                continue
            if RE_ANALYSIS.match(line):
                stage = "analysis"
                continue
            if stage == "stem":
                stem_lines.append(line)
            elif stage == "analysis":
                analysis_lines.append(line)
        elif stage == "material" and current_material is not None:
            materials[current_material] = (materials[current_material] + "\n" + line).strip("\n")
    flush()

    # 附上材料内容（已改写图片路径）
    for q in questions:
        mn = q.get("material_no")
        q["material"] = _rewrite_img_srcs(materials.get(mn, ""), file_dir) if mn else ""

    return {"meta": meta, "questions": questions}


def safe_media_path(rel_path):
    """校验媒体路径必须落在仓库 90-图片 目录内，返回绝对路径；非法返回 None"""
    if not rel_path or "\x00" in rel_path:
        return None
    rel_norm = os.path.normpath(rel_path.replace("\\", "/"))
    if rel_norm.startswith(("..", ".")) or os.path.isabs(rel_norm):
        return None
    root = os.path.normpath(os.path.join(BANK_DIR, MEDIA_DIR_NAME))
    abs_path = os.path.normpath(os.path.join(BANK_DIR, rel_norm))
    if not abs_path.startswith(root + os.sep):
        return None
    if not os.path.isfile(abs_path):
        return None
    return abs_path


def build_question_raw(q):
    """组装入库的题面：材料（如有）+ 题干 + 选项行"""
    parts = []
    if q.get("material"):
        parts.append(q["material"])
    parts.append(q["stem"])
    option_lines = [
        f"- **{o['label']}**. {o['text']}"
        for o in q["options"]
    ]
    parts.append("\n".join(option_lines))
    return "\n\n".join(parts)
