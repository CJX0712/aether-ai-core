"""P0 门禁：全仓扫描 emoji。

禁止使用 emoji 表情作为功能图标（图标必须是统一描边、可矢量缩放的 SVG 方案）。
交付前与 CI 中运行，发现任何 emoji 即非零退出。
"""

from __future__ import annotations

import os
import re
import sys

EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF"
    "\U00002600-\U000027BF"
    "\U0001F000-\U0001F02F"
    "\U0001F0A0-\U0001F0FF"
    "\U0001F100-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U0000203C\U00002049\U00002122\U00002139"
    "\U000021A9\U000021AA\U0000231A\U0000231B"
    "\U000024C2\U000025AA\U000025AB\U000025B6\U000025C0"
    "\U000025FB-\U000025FE\U00002934\U00002935"
    "\U00002B05-\U00002B07\U00002B1B\U00002B1C"
    "\U00002B50\U00002B55\U00003030\U0000303D"
    "\U00003297\U00003299\U0000FE0F\U0000200D]"
)

TEXT_EXTS = {
    ".py", ".md", ".txt", ".json", ".yaml", ".yml",
    ".html", ".css", ".js", ".ts", ".toml", ".cfg", ".ini",
}
SKIP_DIRS = {".venv", ".git", "__pycache__", ".pytest_cache", "node_modules", ".mypy_cache"}


def scan(root: str) -> list[tuple[str, int, str]]:
    hits: list[tuple[str, int, str]] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if os.path.splitext(fn)[1].lower() not in TEXT_EXTS:
                continue
            path = os.path.join(dirpath, fn)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    for lineno, line in enumerate(f, 1):
                        for m in EMOJI_RE.finditer(line):
                            hits.append((path, lineno, m.group(0)))
            except (OSError, UnicodeDecodeError):
                continue
    return hits


def main() -> None:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    hits = scan(root)
    if hits:
        for path, lineno, ch in hits[:50]:
            print(f"EMOJI_HIT {path}:{lineno} {ch!r}")
        print(f"发现 {len(hits)} 处 emoji，违反 P0 门禁")
        sys.exit(1)
    print("P0 门禁通过：未发现 emoji")
    sys.exit(0)


if __name__ == "__main__":
    main()
