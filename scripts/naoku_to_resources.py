"""
考公脑库（ERRRC/kaogongzhentizhengliu，Obsidian vault）→ 资料库导入清单

- 20-考点/<模块>/<大类>/*.md：考点 MOC（核心立场 + 跨卷聚合真题）→ 考点精讲
- 15-材料/资料分析/*.md：资料分析大材料结构档案 → 材料档案

处理：
- 剥离 YAML frontmatter；wikilink [[path|alias]] 清洗为可读文本；
- 从真题链接中提取 qid（写入 related_qids，前端可跳转题库）；
- 清理来源 emoji（🧩⚡⚠📌 等），保持站内 UI 风格统一。

用法：
    python scripts/naoku_to_resources.py --root data/kaogong-naoku --out data/resources/naoku_manifest.json
"""
import argparse
import json
import re
import sys
from pathlib import Path

SOURCE = "ERRRC/kaogongzhentizhengliu (考公脑库)"
FRONT_MATTER = re.compile(r"\A---\s*\n.*?\n---\s*\n", re.S)
WIKILINK_ALIAS = re.compile(r"\[\[[^\]|]+\|([^\]]+)\]\]")
WIKILINK_PLAIN = re.compile(r"\[\[([^\]]+)\]\]")
QID_IN_LINK = re.compile(r"\|\s*(\d{6,})\s*\]\]|(?:^|\s)(\d{6,})(?:\s|$)")
EMOJI = re.compile(r"[\U0001F300-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\uFE0F]")


def clean_text(text: str):
    """wikilink 清洗 + emoji 清理 + 图片路径改写，返回 (正文, qid 列表)"""
    qids = []
    for m in re.finditer(r"\[\[([^\]]+)\]\]", text):
        inner = m.group(1)
        alias = inner.split("|")[-1]
        for q in re.findall(r"\d{6,}", alias):
            qids.append(q)
    text = WIKILINK_ALIAS.sub(r"\1", text)
    text = WIKILINK_PLAIN.sub(lambda m: m.group(1).split("/")[-1], text)
    text = EMOJI.sub("", text)
    # 正文内的配图改写为站内媒体端点（相对层级不定，统一按 90-图片/ 后缀匹配）
    text = re.sub(
        r"(?:\.\./)*90-图片/",
        "/api/resources/naoku/media?path=90-图片/",
        text,
    )
    return text.strip(), qids


def parse_note(path: Path):
    text = path.read_text(encoding="utf-8")
    text = FRONT_MATTER.sub("", text, count=1)
    return clean_text(text)


def convert(root: Path):
    items = []

    # 考点精讲：20-考点/<模块>/<大类>/*.md（跳过总览）
    kao_dian = root / "20-考点"
    if kao_dian.is_dir():
        for module_dir in sorted(p for p in kao_dian.iterdir() if p.is_dir()):
            for da_lei_dir in sorted(p for p in module_dir.iterdir() if p.is_dir()):
                for note in sorted(da_lei_dir.glob("*.md")):
                    if note.stem.startswith("00-"):
                        continue
                    content, qids = parse_note(note)
                    if len(content) < 30:
                        continue
                    seen, uniq = set(), []
                    for q in qids:
                        if q not in seen:
                            seen.add(q)
                            uniq.append(q)
                    items.append({
                        "category": "考点精讲",
                        "sub_path": f"{module_dir.name}/{da_lei_dir.name}",
                        "resource_type": "考点精讲",
                        "title": note.stem,
                        "content": content,
                        "related_qids": uniq[:50],
                        "source": SOURCE,
                        "source_url": "https://github.com/ERRRC/kaogongzhentizhengliu",
                    })

    # 材料档案：15-材料/资料分析/*.md
    cai_liao = root / "15-材料"
    if cai_liao.is_dir():
        for module_dir in sorted(p for p in cai_liao.iterdir() if p.is_dir()):
            for note in sorted(module_dir.glob("*.md")):
                if note.stem.startswith("00-"):
                    continue
                content, qids = parse_note(note)
                if len(content) < 30:
                    continue
                items.append({
                    "category": "材料档案",
                    "sub_path": module_dir.name,
                    "resource_type": "材料档案",
                    "title": note.stem,
                    "content": content,
                    "related_qids": qids[:50],
                    "source": SOURCE,
                    "source_url": "https://github.com/ERRRC/kaogongzhentizhengliu",
                })

    return items


def main():
    parser = argparse.ArgumentParser(description="考公脑库 → 资料库清单")
    parser.add_argument("--root", required=True, help="脑库克隆根目录")
    parser.add_argument("--out", required=True, help="输出清单 JSON 路径")
    args = parser.parse_args()

    items = convert(Path(args.root))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")

    import collections
    by_cat = collections.Counter(x["category"] for x in items)
    with_qids = sum(1 for x in items if x["related_qids"])
    print(f"转换完成：{len(items)} 条 → {out}")
    print("分类分布:", dict(by_cat), "| 带 qid 关联:", with_qids)
    sample = next((x for x in items if x["category"] == "考点精讲"), None)
    if sample:
        print("样例:", sample["title"][:40], "| qids:", sample["related_qids"][:3])


if __name__ == "__main__":
    sys.exit(main())
