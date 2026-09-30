"""
通用题源数据集导入服务
支持把 data/question_sources/ 下的 JSON / CSV / Parquet 题库文件导入本系统。
字段自动映射：question|stem|题目 → 题干；A..D 列 → 选项；answer|答案 → 答案；explanation|解析 → 解析。
"""
import csv
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend/
PROJECT_DIR = os.path.dirname(BASE_DIR)
SOURCES_DIR = os.path.join(PROJECT_DIR, "data", "question_sources")

SUPPORTED_EXT = (".json", ".csv", ".parquet")

STEM_KEYS = ("question", "stem", "题目", "题干")
ANSWER_KEYS = ("answer", "答案")
ANALYSIS_KEYS = ("explanation", "analysis", "解析")
OPTION_KEYS = ("A", "B", "C", "D", "E", "F", "G", "H")


def _row_to_question(row: dict):
    """把一行原始数据映射为标准题目结构；非题目行返回 None"""
    stem = ""
    for k in STEM_KEYS:
        if row.get(k):
            stem = str(row[k]).strip()
            break
    if not stem:
        return None

    options = []
    for label in OPTION_KEYS:
        val = row.get(label)
        if val:
            options.append({"label": label, "text": str(val).strip()})

    answer = ""
    for k in ANSWER_KEYS:
        if row.get(k):
            answer = str(row[k]).strip().upper()[:8]
            break

    analysis = ""
    for k in ANALYSIS_KEYS:
        if row.get(k):
            analysis = str(row[k]).strip()
            break

    if not options or not answer:
        return None
    return {"stem": stem, "options": options, "answer": answer, "analysis": analysis}


def _load_rows(path: str):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".json":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            for key in ("questions", "data", "items", "examples"):
                if key in data and isinstance(data[key], list):
                    data = data[key]
                    break
        if not isinstance(data, list):
            raise ValueError("JSON 结构不支持：需要题目数组或含 questions/data/items 键的对象")
        return data
    if ext == ".csv":
        with open(path, "r", encoding="utf-8-sig") as f:
            return list(csv.DictReader(f))
    if ext == ".parquet":
        try:
            import pyarrow.parquet as pq
        except ImportError:
            raise ValueError("读取 parquet 需要安装 pyarrow：pip install pyarrow")
        table = pq.read_table(path)
        return table.to_pylist()
    raise ValueError(f"不支持的文件类型：{ext}")


def list_sources():
    """扫描数据集目录，返回可导入文件与解析出的题数"""
    if not os.path.isdir(SOURCES_DIR):
        return []
    items = []
    for name in sorted(os.listdir(SOURCES_DIR)):
        if not name.lower().endswith(SUPPORTED_EXT):
            continue
        path = os.path.join(SOURCES_DIR, name)
        count, error = 0, ""
        try:
            rows = _load_rows(path)
            count = sum(1 for r in rows if _row_to_question(r if isinstance(r, dict) else {}) is not None)
        except Exception as e:
            error = str(e)
        items.append({"file": name, "count": count, "size_kb": round(os.path.getsize(path) / 1024, 1), "error": error})
    return items


def load_questions(filename: str):
    """解析单个数据集文件为标准题目列表"""
    path = os.path.join(SOURCES_DIR, filename)
    root = os.path.normpath(SOURCES_DIR)
    if not os.path.normpath(path).startswith(root + os.sep) or not os.path.isfile(path):
        raise ValueError("数据集文件不存在")
    rows = _load_rows(path)
    questions = []
    for r in rows:
        q = _row_to_question(r if isinstance(r, dict) else {})
        if q:
            q["subject"] = str(r.get("subject", "")).strip()
            questions.append(q)
    return questions
