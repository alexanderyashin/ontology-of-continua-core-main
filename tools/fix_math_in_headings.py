#!/usr/bin/env python3
import re
from pathlib import Path

# Welche Verzeichnisse scannen (falls du willst, kannst du später noch "appendix" hinzufügen)
ROOTS = ["content"]

# Überschriften + captions, Stern ist optional (\section{..} oder \section*{..})
PATTERNS = [
    r"(\\section\*?\{)([^}]*)(\})",
    r"(\\subsection\*?\{)([^}]*)(\})",
    r"(\\subsubsection\*?\{)([^}]*)(\})",
    r"(\\paragraph\*?\{)([^}]*)(\})",
    r"(\\subparagraph\*?\{)([^}]*)(\})",
    r"(\\caption\*?\{)([^}]*)(\})",
]

# Math in Überschriften/Kapiteln: $, \(..\), \[..\]
MATH_RE = re.compile(
    r"(\$[^$]+\$|\\\([^)]*\\\)|\\\[[^\]]*\\\])"
)

def make_texorpdfstring(text: str) -> str:
    """
    Wrappt Math-Ausdrücke in \texorpdfstring{...}{...}.
    Die Plain-Variante ist grob "Math ohne Delimiter".
    """
    # Wenn der Text schon texorpdfstring enthält, nicht anfassen
    if r"\texorpdfstring" in text:
        return text

    def repl(m):
        math = m.group(1)
        plain = (
            math.replace("$", "")
                .replace(r"\(", "")
                .replace(r"\)", "")
                .replace(r"\[", "")
                .replace(r"\]", "")
        )
        # ein bisschen Whitespace säubern
        plain = " ".join(plain.split())
        return r"\texorpdfstring{" + math + "}{" + plain + "}"

    return MATH_RE.sub(repl, text)


def process_file(path: Path) -> bool:
    content = path.read_text(encoding="utf-8")
    original = content

    for pattern in PATTERNS:
        def repl(m):
            prefix, inner, suffix = m.group(1), m.group(2), m.group(3)
            new_inner = make_texorpdfstring(inner)
            return prefix + new_inner + suffix

        content = re.sub(pattern, repl, content, flags=re.DOTALL)

    if content != original:
        path.write_text(content, encoding="utf-8")
        print(f"[fix_math] Updated: {path}")
        return True
    return False


def main():
    changed_any = False
    for root in ROOTS:
        for path in Path(root).rglob("*.tex"):
            if process_file(path):
                changed_any = True

    if not changed_any:
        print("[fix_math] No changes made (already clean).")


if __name__ == "__main__":
    main()
