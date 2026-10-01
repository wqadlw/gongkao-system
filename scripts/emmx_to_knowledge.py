"""
亿图脑图(.emmx) → 行测知识库批量导入 JSON

数据来源：https://github.com/kuriv/civil-service-exam （MIT License）
目录结构：行测/<模块>/<主题>/<考点>/<考点>.emmx（另含申论/面试，本项目暂不导入）

.emmx 格式（zip）：page/page.xml 内 <Shape ID Type> 节点，<tp> 存文本，
<LevelData><SubLevel V="子ID;子ID"/> 描述层级。

用法：
    python scripts/emmx_to_knowledge.py --root data/kuriv-mindmaps/行测 \
        --out data/question_sources/kuriv_knowledge.json [--source kuriv/civil-service-exam]
"""
import argparse
import json
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

MODULES = {"常识判断", "言语理解与表达", "数量关系", "判断推理", "资料分析", "政治理论"}
MAX_XML_BYTES = 20 * 1024 * 1024  # 单页 XML 上限，防资源耗尽


def safe_parse_xml(data: bytes):
    """解析前拒绝 DTD/ENTITY（防实体扩展攻击），并限制输入大小"""
    if len(data) > MAX_XML_BYTES:
        raise ValueError("XML 过大")
    head = data[:4096].lstrip().lower()
    if b"<!doctype" in head or b"<!entity" in head:
        raise ValueError("XML 包含 DTD/ENTITY，已拒绝解析")
    return ET.fromstring(data)


def parse_emmx(path: Path):
    """解析 .emmx，返回 (标题, 大纲行列表)；解析失败返回 (None, [])"""
    try:
        with zipfile.ZipFile(path) as z:
            page_name = next(n for n in z.namelist() if n.endswith("page.xml"))
            root = safe_parse_xml(z.read(page_name))
    except (zipfile.BadZipFile, StopIteration, ET.ParseError, ValueError):
        return None, []

    shapes, order = {}, []
    for shape in root.iter("Shape"):
        sid = shape.get("ID")
        if not sid:
            continue
        title = " ".join(
            (tp.text or "").strip() for tp in shape.iter("tp") if (tp.text or "").strip()
        )
        sub = shape.find("./LevelData/SubLevel")
        children = [c for c in (sub.get("V").split(";") if sub is not None and sub.get("V") else []) if c]
        shapes[sid] = {"type": shape.get("Type"), "title": title, "children": children}
        order.append(sid)

    root_id = next((s for s in order if shapes[s]["type"] == "MainIdea"), None)
    if root_id is None:
        return None, []

    lines = []

    def walk(node_id, depth):
        node = shapes.get(node_id)
        if node is None:
            return
        if node["title"]:
            lines.append("  " * depth + "- " + node["title"])
        for child in node["children"]:
            walk(child, depth + 1)

    walk(root_id, 0)
    title = shapes[root_id]["title"] or path.stem
    return title, lines


def convert(root: Path, source: str):
    items = []
    for emmx in sorted(root.rglob("*.emmx")):
        rel = emmx.relative_to(root).parts  # 例：(模块, 主题, 考点, 考点.emmx)
        if not rel or rel[0] not in MODULES:
            continue
        module = rel[0]
        title, lines = parse_emmx(emmx)
        if not title or len(lines) < 3:
            continue
        content = "\n".join([f"# {title}"] + lines)
        tags = "｜".join([p for p in rel[:-1] if p != module])
        item = {
            "module": module,
            "kg_type": "概念",
            "title": title,
            "content": content,
            "tags": tags,
            "source": source,
            "difficulty": 2,
            "level1": module,
            "level2": rel[1] if len(rel) > 2 else "",
            "level3": rel[2] if len(rel) > 3 else "",
            "level4": rel[3] if len(rel) > 4 else "",
            "level5": "",
        }
        # 卡片摘要：取大纲一级分支
        branches = [l.strip("- ").strip() for l in lines[1:] if l.startswith("  - ")]
        item["card_title"] = f"{title}（{'/'.join(rel[1:-1])}）" if len(rel) > 2 else title
        item["card_tags"] = tags
        item["card_summary"] = "涵盖：" + "、".join(branches[:6]) + ("等" if len(branches) > 6 else "")
        items.append(item)
    return items


def main():
    parser = argparse.ArgumentParser(description="emmx 思维导图 → 知识库导入 JSON")
    parser.add_argument("--root", required=True, help="行测根目录")
    parser.add_argument("--out", required=True, help="输出 JSON 路径")
    parser.add_argument("--source", default="kuriv/civil-service-exam (MIT)")
    args = parser.parse_args()

    items = convert(Path(args.root), args.source)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"转换完成：{len(items)} 个知识点 → {out}")
    for it in items[:5]:
        print(" -", it["module"], "/", it["level2"], "/", it["title"], f"({len(it['content'])} 字)")


if __name__ == "__main__":
    sys.exit(main())
