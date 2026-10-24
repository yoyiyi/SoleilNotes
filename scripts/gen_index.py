#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""根据仓库里的 Markdown 文件生成 INDEX.md（全量笔记索引）。

用法：
    python scripts/gen_index.py          # 重新生成 INDEX.md
    python scripts/gen_index.py --check  # 只检查 INDEX.md 是否与文件树一致
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT = os.path.join(ROOT, "INDEX.md")

SKIP_DIRS = {".git", ".github", "node_modules", "venv", "__pycache__", "asset", "scripts"}
SKIP_FILES = {"README.md", "INDEX.md"}


def md_target(path: str) -> str:
    """转义会破坏 Markdown 链接语法的字符。"""
    return path.replace(" ", "%20").replace("(", "%28").replace(")", "%29")


def collect():
    groups = {}
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS and not d.startswith("."))
        for name in sorted(filenames):
            if not name.lower().endswith(".md") or name in SKIP_FILES:
                continue
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, ROOT).replace("\\", "/")
            top = rel.split("/")[0] if "/" in rel else "（根目录）"
            groups.setdefault(top, []).append(rel)
    return groups


def render(groups) -> str:
    total = sum(len(v) for v in groups.values())
    lines = [
        "# 全部笔记索引",
        "",
        "> 本文件由 `scripts/gen_index.py` 自动生成，请勿手工编辑；新增笔记后执行 `python scripts/gen_index.py` 更新。",
        "",
        f"当前共收录 **{total}** 篇笔记。",
        "",
    ]
    for top in sorted(groups):
        lines.append(f"## {top}")
        lines.append("")
        for rel in sorted(groups[top]):
            title = os.path.splitext(os.path.basename(rel))[0]
            lines.append(f"- [{title}]({md_target(rel)})")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    content = render(collect())
    if "--check" in sys.argv:
        current = open(OUTPUT, encoding="utf-8").read() if os.path.exists(OUTPUT) else ""
        if current != content:
            print("INDEX.md 已过期，请运行：python scripts/gen_index.py")
            return 1
        print("INDEX.md 已是最新。")
        return 0

    with open(OUTPUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(content)
    print(f"已生成 {os.path.relpath(OUTPUT, ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
