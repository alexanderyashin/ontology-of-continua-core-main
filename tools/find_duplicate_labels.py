#!/usr/bin/env python3
from pathlib import Path
import re

# Сканируем весь репозиторий, кроме build/, .git/, tools/
EXCLUDE = {".git", "build", "tools", ".venv", "venv"}

LABEL_RE = re.compile(r"\\label\{([^}]+)\}")

def iter_tex():
    for path in Path(".").rglob("*.tex"):
        if any(part in EXCLUDE for part in path.parts):
            continue
        yield path

def main():
    labels = {}

    for path in iter_tex():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for lineno, line in enumerate(text.splitlines(), start=1):
            for m in LABEL_RE.finditer(line):
                name = m.group(1)
                labels.setdefault(name, []).append((path, lineno))

    dupes = {k: v for k, v in labels.items() if len(v) > 1}

    if not dupes:
        print("[labels] No duplicate labels found.")
        return

    print("[labels] Duplicate labels found:")
    print("----------------------------------------")
    for name, locs in sorted(dupes.items()):
        print(f"\n{name} (count={len(locs)}):")
        for p, l in locs:
            print(f"   - {p}:{l}")

if __name__ == "__main__":
    main()
