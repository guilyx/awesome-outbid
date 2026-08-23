#!/usr/bin/env python3
"""Fail if a markdown link into this repo does not resolve, anchors included.

External links are deliberately not checked here: boards in this genre expire
constantly, and a contributor should never have a pull request blocked by
someone else's dead domain. Those are checked weekly by link-check.yml.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

LINK = re.compile(r"\]\(\s*(<[^>]*>|[^)\s]+)")
EXTERNAL = re.compile(r"^(https?:|mailto:|tel:)", re.IGNORECASE)
HEADING = re.compile(r"^(#{1,6})\s+(.*)$")


def slugify(heading: str) -> str:
    """Approximate GitHub's heading-to-anchor transformation."""
    text = heading.strip().lower()
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"\*{1,2}([^*]*)\*{1,2}", r"\1", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    return re.sub(r"\s", "-", text)


def main() -> int:
    root = Path.cwd()
    files = subprocess.run(
        ["git", "ls-files", "*.md"], capture_output=True, text=True, check=True
    ).stdout.split()

    anchors: dict[str, set[str]] = {}
    for name in files:
        found = set()
        for line in Path(name).read_text(encoding="utf-8").splitlines():
            match = HEADING.match(line)
            if match:
                found.add(slugify(match.group(2)))
        anchors[name] = found

    broken = 0
    for name in files:
        path = Path(name)
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for match in LINK.finditer(line):
                target = match.group(1).strip("<>")
                if EXTERNAL.match(target):
                    continue

                file_part, _, anchor = target.partition("#")

                if file_part:
                    resolved = (path.parent / file_part).resolve()
                    if not resolved.exists():
                        print(f"::error file={name},line={lineno}::broken link -> {target}")
                        broken += 1
                        continue
                    try:
                        key = str(resolved.relative_to(root))
                    except ValueError:
                        continue  # outside the repo, nothing to check
                else:
                    key = name

                if anchor and key in anchors and anchor not in anchors[key]:
                    print(f"::error file={name},line={lineno}::broken anchor -> {target}")
                    broken += 1

    if broken:
        print(f"\n{broken} broken link(s)", file=sys.stderr)
        return 1

    print(f"checked {len(files)} markdown files: all in-repo links and anchors resolve")
    return 0


if __name__ == "__main__":
    sys.exit(main())
