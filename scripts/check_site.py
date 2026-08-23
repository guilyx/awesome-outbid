#!/usr/bin/env python3
"""Verify every internal link and anchor in the built site resolves."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "_site"
HREF = re.compile(r'(?:href|src)="([^"]+)"')
ID = re.compile(r'id="([^"]+)"')
BASE = "/awesome-outbid"


def main() -> int:
    if not OUT.exists():
        print("no _site/ -- run scripts/build.py first", file=sys.stderr)
        return 1

    pages = sorted(OUT.rglob("*.html"))
    ids: dict[str, set[str]] = {
        p.relative_to(OUT).as_posix(): set(ID.findall(p.read_text(encoding="utf-8")))
        for p in pages
    }

    def resolve(target: str) -> str:
        """Map a site-absolute URL to the file that would serve it."""
        path = target[len(BASE):] if target.startswith(BASE) else target
        path = path.lstrip("/")
        if path in ("", "/"):
            return "index.html"
        return path + "index.html" if path.endswith("/") else path

    broken = 0
    for page in pages:
        rel = page.relative_to(OUT).as_posix()
        for target in HREF.findall(page.read_text(encoding="utf-8")):
            if target.startswith(("http://", "https://", "mailto:", "data:")):
                continue

            if target.startswith("#"):
                anchor, key = target[1:], rel
            else:
                path, _, anchor = target.partition("#")
                key = resolve(path)
                if not (OUT / key).exists():
                    print(f"::error file=_site/{rel}::broken link -> {target}")
                    broken += 1
                    continue

            if anchor and anchor not in ids.get(key, set()):
                print(f"::error file=_site/{rel}::broken anchor -> {target} (no #{anchor} in {key})")
                broken += 1

    if broken:
        print(f"\n{broken} broken internal link(s) in the built site", file=sys.stderr)
        return 1

    print(f"site: {len(pages)} pages, all internal links and anchors resolve")
    return 0


if __name__ == "__main__":
    sys.exit(main())
