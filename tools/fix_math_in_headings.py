#!/usr/bin/env python3
import re
import os
from pathlib import Path

ROOT = Path("content")

# Patterns for headings/captions
PATTERNS = [
    r"\\section\{([^}]*)\}",
    r"\\subsection\{([^}]*)\}",
    r"\\subsubsection\{([^}]*)\}",
    r"\\paragraph\{([^}]*)\}",
    r"\\caption\{([^}]*)\}",
]

# Math patterns: $, \(...\), \[...\]
MATH_RE = re.compile(
    r"(\$[^$]+\$|\\\([^)]*\\\)|\\\[[^\]]*\\\])"
)

def make_texorpdfstring(text: str) -> str:
    """
    Wrap math in texorpdfstring.
    Plain text version: math stripped of \( \) \[ \] $.
    """
    def repl(m):
        math = m.group(1)
        plain = (
            math.replace("$", "")
                .replace(r"\(", "")
                .replace(r"\)", "")
                .replace(r"\[", "")
                .replace(r"\]", "")
        )
        return rf"\texorpdfstring{{{math}}}{{{plain}}}"

    return MATH_RE.sub(repl, text)


def process_file(path: Path):
    original = path.read_text(encoding="utf-8")
    updated = original

    for pat in PATTERNS:
        regex = re.compile(pat)

        def fix(match):
            full = match.group(0)
            inside = match.group(1)

            # Only apply if math is inside
            if not MATH_RE.search(inside):
                return full

            safe = make_texorpdfstring(inside)
            return full.replace(inside, safe)

        updated = regex.sub(fix, updated)

    if updated != original:
        path.write_text(updated, encoding="utf-8")
        print(f"[fixed] {path}")


def main():
    tex_files = list(ROOT.rglob("*.tex"))
    print(f"[scan] {len(tex_files)} .tex files found")

    for f in tex_files:
        process_file(f)

    print("[done] All headings/captions cleaned.")

if __name__ == "__main__":
    main()
