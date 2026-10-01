"""
LogiQA 数据集转换器：把 LogiQA 的中文逻辑推理题转换为通用数据集 JSON，
放入 data/question_sources/ 后通过系统「数据集导入」功能入库（level1=判断推理）。

数据来源：https://github.com/lgw863/LogiQA-dataset （中文版，题目源自中国国家公务员考试）

原始格式（每个题目块 7 行，块间以空行分隔）：
    行1：正确答案字母（a/b/c/d）
    行2：题干背景（原文）
    行3：问题
    行4-7：四个选项（A./B./C./D. 开头）

用法：
    python scripts/logiqa_to_dataset.py <zh_train.txt> [zh_eval.txt zh_test.txt ...] \
        --out ../data/question_sources/logiqa_judgment.json
"""
import argparse
import json
import re
import sys
from pathlib import Path

ANSWER_RE = re.compile(r"^[a-dA-D]$")
OPTION_RE = re.compile(r"^([A-D])[.、．]\s*")


def parse_blocks(text):
    """按空行分块，解析每个 7 行题目块"""
    blocks, cur = [], []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            if cur:
                blocks.append(cur)
                cur = []
            continue
        cur.append(line)
    if cur:
        blocks.append(cur)
    return blocks


def block_to_question(block):
    """把一个题目块转为标准数据集条目；结构不符返回 None"""
    if len(block) < 6:
        return None
    answer_line, context, question = block[0], block[1], block[2]
    if not ANSWER_RE.match(answer_line):
        return None

    options = {}
    for raw in block[3:]:
        m = OPTION_RE.match(raw)
        if not m:
            return None
        options[m.group(1)] = OPTION_RE.sub("", raw, count=1).strip()
    if sorted(options.keys()) != ["A", "B", "C", "D"]:
        return None

    return {
        "question": f"{context}\n\n{question}",
        "A": options["A"],
        "B": options["B"],
        "C": options["C"],
        "D": options["D"],
        "answer": answer_line.upper(),
        "subject": "判断推理",
        "explanation": "",
    }


def convert(paths):
    questions, seen, skipped = [], set(), 0
    for path in paths:
        text = Path(path).read_text(encoding="utf-8")
        for block in parse_blocks(text):
            q = block_to_question(block)
            if not q:
                skipped += 1
                continue
            key = q["question"][:120]
            if key in seen:
                skipped += 1
                continue
            seen.add(key)
            questions.append(q)
    return questions, skipped


def main():
    parser = argparse.ArgumentParser(description="LogiQA txt → 通用数据集 JSON")
    parser.add_argument("inputs", nargs="+", help="LogiQA 中文 txt 文件（可多个）")
    parser.add_argument("--out", required=True, help="输出 JSON 路径")
    args = parser.parse_args()

    questions, skipped = convert(args.inputs)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(questions, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"转换完成：{len(questions)} 题（跳过 {skipped} 条无效/重复块）→ {out}")
    if questions:
        sample = questions[0]
        print("样例题干前 60 字：", sample["question"][:60].replace("\n", " "))


if __name__ == "__main__":
    sys.exit(main())
