#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查仓库内 Markdown 的相对链接与图片引用是否有效。

GitHub 的路径匹配是大小写敏感的，而 Windows 本地不敏感，
所以本脚本按目录逐级比对大小写，能发现「本地能开、线上 404」的链接。

用法：
    python scripts/check_links.py            # 检查全部
    python scripts/check_links.py README.md  # 只检查指定文件
退出码：0 表示没有问题，1 表示发现问题（供 CI 使用）。
"""

import os
import re
import sys
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SKIP_DIRS = {".git", ".github", "node_modules", "venv", "__pycache__", "asset"}
SKIP_PREFIXES = ("http://", "https://", "mailto:", "tel:", "ftp:", "#", "data:")

MD_LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
HTML_REF = re.compile(r"""(?:src|href)\s*=\s*["']([^"']+)["']""")
FENCE = re.compile(r"^\s*(```|~~~)")
INLINE_CODE = re.compile(r"`[^`]*`")


def resolve_exact(base_dir: str, rel: str):
    """按大小写逐级比对；返回 (状态, 说明)。

    状态：ok / missing / case
    """
    parts = [p for p in rel.replace("\\", "/").split("/") if p not in ("", ".")]
    cur = base_dir
    for i, part in enumerate(parts):
        if part == "..":
            cur = os.path.dirname(cur)
            continue
        try:
            entries = os.listdir(cur)
        except OSError:
            return "missing", rel
        if part not in entries:
            lower = {e.lower() for e in entries}
            if part.lower() in lower:
                real = next(e for e in entries if e.lower() == part.lower())
                return "case", "/".join(parts[: i + 1]) + f"  (实际为 {real})"
            return "missing", rel
        cur = os.path.join(cur, part)

    if not os.path.exists(cur):
        return "missing", rel
    return "ok", rel


def iter_md_files(targets):
    if targets:
        for t in targets:
            t = t if os.path.isabs(t) else os.path.join(ROOT, t)
            if os.path.isfile(t):
                yield t
        return
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            if name.lower().endswith(".md"):
                yield os.path.join(dirpath, name)


def check_file(path: str):
    problems = []
    with open(path, encoding="utf-8", errors="replace") as fh:
        lines = fh.read().splitlines()

    in_fence = False
    for lineno, raw in enumerate(lines, 1):
        if FENCE.match(raw):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        line = INLINE_CODE.sub("", raw)
        for match in list(MD_LINK.finditer(line)) + list(HTML_REF.finditer(line)):
            raw_link = match.group(1).strip()
            if not raw_link or raw_link.startswith(SKIP_PREFIXES):
                continue

            target = raw_link.split("#")[0].split("?")[0]
            if not target:
                continue  # 纯锚点链接，本脚本不校验
            target = urllib.parse.unquote(target)

            # 写死的本机绝对路径，别人 clone 后必然失效
            if re.match(r"^[A-Za-z]:[/\\]", target) or target.startswith("/"):
                problems.append((lineno, raw_link, "absolute", "使用了本机绝对路径"))
                continue

            status, detail = resolve_exact(os.path.dirname(path), target)
            if status == "case":
                problems.append((lineno, raw_link, "case", f"大小写不一致：{detail}"))
            elif status == "missing":
                problems.append((lineno, raw_link, "missing", "文件不存在"))
    return problems


def main() -> int:
    targets = sys.argv[1:]
    total, bad = 0, 0
    for path in sorted(iter_md_files(targets)):
        total += 1
        for lineno, link, kind, detail in check_file(path):
            bad += 1
            rel = os.path.relpath(path, ROOT).replace("\\", "/")
            print(f"{rel}:{lineno}: [{kind}] {link} -> {detail}")
    print(f"\n检查了 {total} 个 Markdown 文件，发现 {bad} 处问题。")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
