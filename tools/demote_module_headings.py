#!/usr/bin/env python3
import re
from pathlib import Path

# Каталоги модульных глав: 1 папка = 1 глава
MODULE_DIRS = [
    "content/k_levels",
    "content/m_spaces",
    "content/crossk",
    "content/cycles",
    "content/experiments",
    "content/falsifiability",
    "content/jets",
    "content/predictions",
    "content/processes",
]

# Паттерны: понижаем уровень заголовка на один шаг
DEMOTE_RULES = [
    (r"\\section(\*?)\{",     r"\\subsection\1{"),
    (r"\\subsection(\*?)\{",  r"\\subsubsection\1{"),
]

def demote_in_file(path: Path):
    text = path.read_text(encoding="utf-8")
    original = text

    for pattern, repl in DEMOTE_RULES:
        text = re.sub(pattern, repl, text)

    if text != original:
        path.write_text(text, encoding="utf-8")
        print(f"[demote] Updated headings in {path}")
    else:
        print(f"[demote] No changes in {path}")

def main():
    for d in MODULE_DIRS:
        dir_path = Path(d)
        if not dir_path.exists():
            continue
        for tex in dir_path.glob("*.tex"):
            # master-файлы оставляем как есть: они задают верхний уровень главы
            if tex.name.endswith("master.tex"):
                continue
            demote_in_file(tex)

if __name__ == "__main__":
    main()
