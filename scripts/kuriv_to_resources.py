"""
kuriv/civil-service-exam 思维导图 → 资料库导入清单

- 拷贝每个导图节点的 .emmx（源文件）与 .png（预览图）到 data/resources/kuriv/<相对路径>/
- 生成资料清单 JSON（mindmap 条目 + 推荐外链条目），通过 /api/resources/batch 导入

用法：
    python scripts/kuriv_to_resources.py --clone data/kuriv-mindmaps --out data/resources/kuriv_manifest.json
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

LINK_RESOURCES = [
    {
        "category": "经验指南", "sub_path": "程序员考公", "resource_type": "link",
        "title": "互联网首份程序员考公指南（coder2gwy）",
        "description": "由 3 位已上岸的前大厂程序员联合编写，覆盖备考决策、行测申论复习方法与上岸经历（⭐27.7k）。",
        "source_url": "https://github.com/coder2gwy/coder2gwy",
        "source": "coder2gwy/coder2gwy",
    },
    {
        "category": "经验指南", "sub_path": "程序员考公", "resource_type": "link",
        "title": "公务员从入门到上岸，最佳程序员公考实践教程（developer2gwy）",
        "description": "面向程序员的公考实践教程：选岗、行测/申论备考路线与时间规划（⭐11.3k）。",
        "source_url": "https://github.com/miss-mumu/developer2gwy",
        "source": "miss-mumu/developer2gwy",
    },
    {
        "category": "行测", "sub_path": "题库", "resource_type": "link",
        "title": "xingcezhenti：2016-2026 国考+省考行测真题库（2962 份试卷）",
        "description": "本系统「真题库对接」功能的数据源仓库，可整体克隆后自动识别。",
        "source_url": "https://github.com/ERRRC/xingcezhenti",
        "source": "ERRRC/xingcezhenti",
    },
    {
        "category": "行测", "sub_path": "题库", "resource_type": "link",
        "title": "LogiQA：源自国考的逻辑推理数据集（8600+ 题）",
        "description": "已通过「数据集导入」接入本系统，此处保留原始仓库链接便于追溯。",
        "source_url": "https://github.com/lgw863/LogiQA-dataset",
        "source": "lgw863/LogiQA-dataset",
    },
]


def copy_file(src: Path, dest_root: Path, rel_parts) -> str:
    dest = dest_root.joinpath(*rel_parts)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        shutil.copy2(src, dest)
    return "/".join(rel_parts)  # 相对 data/resources/（与路由 RESOURCES_DIR 同基准）


def main():
    parser = argparse.ArgumentParser(description="kuriv 思维导图 → 资料库清单")
    parser.add_argument("--clone", required=True, help="kuriv 仓库克隆目录")
    parser.add_argument("--out", required=True, help="输出清单 JSON 路径")
    args = parser.parse_args()

    clone = Path(args.clone)
    hangce = clone / "行测"
    items = list(LINK_RESOURCES)

    emmx_files = sorted(hangce.rglob("*.emmx")) if hangce.is_dir() else []
    # 申论 / 面试为顶层单文件导图
    for top in ("申论", "面试"):
        f = clone / top / f"{top}.emmx"
        if f.exists():
            emmx_files.append(f)

    for emmx in emmx_files:
        rel = emmx.relative_to(clone).parts  # (分类, 主题?, 考点?, name.emmx)
        category = rel[0]
        sub_path = "/".join(rel[1:-1]) if len(rel) > 2 else ""
        stem = emmx.stem
        png = emmx.with_suffix(".png")

        resources_root = Path(args.out).parent
        image_path = file_path = ""
        if png.exists():
            image_path = copy_file(png, resources_root, ("kuriv",) + rel[:-1] + (stem + ".png",))
        file_path = copy_file(emmx, resources_root, ("kuriv",) + rel[:-1] + (emmx.name,))

        branches = []
        items.append({
            "category": category,
            "sub_path": sub_path,
            "resource_type": "mindmap",
            "title": stem,
            "description": "",
            "image_path": image_path,
            "file_path": file_path,
            "source": "kuriv/civil-service-exam (MIT)",
            "source_url": "https://github.com/kuriv/civil-service-exam",
        })

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"清单完成：{len(items)} 条资料（导图 {len(items) - len(LINK_RESOURCES)} + 外链 {len(LINK_RESOURCES)}）→ {out}")


if __name__ == "__main__":
    sys.exit(main())
