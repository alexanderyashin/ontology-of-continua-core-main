#!/usr/bin/env python3
import re
from pathlib import Path

ROOT = Path("content")

# Math patterns: $, \(...\), \[...\]
MATH_RE = re.compile(r"(\$[^$]+\$|\\\([^)]*\\\)|\\\[[^\]]*\\\])")

# Heading-like commands, inkl. paragraphs & captions
HEADING_CMDS = ("section", "subsection", "subsubsection", "paragraph", "caption")


def wrap_math_in_texorpdfstring(text: str) -> str:
    """
    Wrap math segments in \\texorpdfstring{<math>}{<plain>}.

    Sicherheitsregeln:
    - Wenn im Text bereits '\\texorpdfstring' vorkommt -> nichts tun.
    - Plain-Version: wir strippen nur die Math-Klammern ($, \\(\\), \\[\\]),
      der Rest bleibt wie er ist.
    """
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
        return r"\texorpdfstring{" + math + "}{" + plain + "}"

    return MATH_RE.sub(repl, text)


def process_tex_file(path: Path) -> bool:
    """
    Process one .tex file.
    Returns True if file was modified.
    """
    original = path.read_text(encoding="utf-8")

    # Regex: \section{...}, \section*{...}, \paragraph{...}, \caption{...}, etc.
    # Gruppe 1: Befehl (section / subsection / paragraph / caption)
    # Gruppe 2: optionaler Stern *
    # Gruppe 3: Inhalt { ... }
    pattern = re.compile(
        r"\\(" + "|".join(HEADING_CMDS) + r")(\*?)\{([^}]*)\}",
        flags=re.DOTALL,
    )

    def heading_repl(m):
        cmd = m.group(1)
        star = m.group(2)
        body = m.group(3)

        new_body = wrap_math_in_texorpdfstring(body)
        return "\\" + cmd + star + "{" + new_body + "}"

    modified = pattern.sub(heading_repl, original)

    if modified != original:
        path.write_text(modified, encoding="utf-8")
        print(f"[fix_math] Updated: {path}")
        return True

    return False


def main():
    tex_files = sorted(ROOT.rglob("*.tex"))
    if not tex_files:
        print("No .tex files found under 'content/'.")
        return

    changed_any = False
    for f in tex_files:
        if process_tex_file(f):
            changed_any = True

    if not changed_any:
        print("[fix_math] No changes made (already clean).")
    else:
        print("[fix_math] Done.")


if __name__ == "__main__":
    main()
