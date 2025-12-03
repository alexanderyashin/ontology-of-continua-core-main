#!/usr/bin/env python3
"""
Generate missing LaTeX content files from a YAML structure.

Usage (from repo root):

    python tools/generate_core_from_yaml.py          # uses master_core_structure.yaml
    python tools/generate_core_from_yaml.py path/to/your.yaml

YAML format (минимальный пример):

root:
  - title: Introduction
    file: content/01_intro.tex
  - title: K-levels
    file: content/k_levels/klevels_master.tex
    children:
      - title: K0
        file: content/k_levels/k0.tex
      - title: K1
        file: content/k_levels/k1.tex

Каждый узел:
  - file:   путь к .tex
  - title:  заголовок секции (опционально)
  - children / subsections: дочерние узлы (опционально)

Скрипт терпимо относится к разным верхним обёрткам YAML.
"""

import os
import sys
import textwrap

import yaml  # pip install pyyaml

# ------------------------------------------------------------
# Настройки
# ------------------------------------------------------------

# По умолчанию читаем master_core_structure.yaml из корня проекта.
STRUCTURE_FILE = sys.argv[1] if len(sys.argv) > 1 else "master_core_structure.yaml"

# Базовый шаблон содержимого нового файла.
# {filepath} будет подставлен автоматически.
DEFAULT_PLACEHOLDER = textwrap.dedent(
    r"""
    % ================================================================
    %  Ontology of Continua — Core
    %  AUTO-GENERATED PLACEHOLDER
    %  File: {filepath}
    %  Status: EMPTY — TO BE FILLED
    % ================================================================

    % This file was created automatically by tools/generate_core_from_yaml.py.
    % Replace this placeholder with the actual content.

    """
).lstrip("\n")

# Если True, в начало файла будет добавлен \section/\subsection и т.п.
ADD_LATEX_HEADER = True


# ------------------------------------------------------------
# Вспомогательные функции
# ------------------------------------------------------------

def load_nodes(path: str):
    """Загрузить список узлов из YAML.

    Поддерживаем много вариантов структуры:
      - верхний уровень — список нод;
      - верхний уровень — словарь с ключом root / sections / nodes / chapters / toc / content;
      - верхний уровень — произвольный dict, где одно из значений — список нод;
      - верхний уровень — dict вида {Title: {file: ..., children: [...]}}.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if data is None:
        raise SystemExit("YAML пустой. Ожидал список секций.")

    # 1) Прямо список нод
    if isinstance(data, list):
        return data

    # 2) Словарь со стандартными ключами-обёртками
    if isinstance(data, dict):
        for key in ("root", "sections", "nodes", "chapters", "toc", "content"):
            value = data.get(key)
            if isinstance(value, list):
                return value

        # 3) Любое значение-список из словарей → считаем его списком нод
        for value in data.values():
            if isinstance(value, list) and (not value or isinstance(value[0], dict)):
                return value

        # 4) Fallback: превращаем dict в список нод {title: key, ...value}
        nodes = []
        for key, value in data.items():
            node = {"title": str(key)}
            if isinstance(value, dict):
                node.update(value)
            nodes.append(node)
        return nodes

    raise SystemExit(
        "Не могу понять структуру YAML даже после всех попыток. "
        "Ожидал list или dict с вложенными нодами."
    )


def ensure_dir_for_file(filepath: str) -> None:
    """Создать директорию под файл, если её ещё нет."""
    directory = os.path.dirname(filepath)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)


def make_latex_header(title: str, level: int) -> str:
    """
    level 0 -> \\section
    level 1 -> \\subsection
    level 2 -> \\subsubsection
    дальше -> \\paragraph
    """
    if not ADD_LATEX_HEADER:
        return ""

    if level == 0:
        cmd = r"\section"
    elif level == 1:
        cmd = r"\subsection"
    elif level == 2:
        cmd = r"\subsubsection"
    else:
        cmd = r"\paragraph"

    return f"{cmd}{{{title}}}\n\n"


def create_file_if_missing(filepath: str, title: str, level: int) -> None:
    """Создать .tex, если его ещё нет."""
    ensure_dir_for_file(filepath)

    if os.path.exists(filepath):
        print(f"[skip   ] {filepath} (already exists)")
        return

    header = make_latex_header(title, level)
    body = DEFAULT_PLACEHOLDER.format(filepath=filepath)

    content = body + header

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[create ] {filepath}")


def walk_nodes(nodes, level: int = 0) -> None:
    """Рекурсивно обойти дерево узлов и создать файлы."""
    for node in nodes:
        if not isinstance(node, dict):
            # Защита от мусора в YAML
            continue

        file_path = node.get("file")
        if not file_path:
            # Нода без файла нам не интересна
            continue

        title = node.get("title") or os.path.splitext(os.path.basename(file_path))[0]
        create_file_if_missing(file_path, title, level)

        children = (
            node.get("children")
            or node.get("subsections")
            or []
        )
        if children:
            walk_nodes(children, level=level + 1)


# ------------------------------------------------------------
# main
# ------------------------------------------------------------

def main() -> None:
    if not os.path.exists(STRUCTURE_FILE):
        raise SystemExit(f"YAML не найден: {STRUCTURE_FILE}")

    print(f"Использую YAML структуру: {STRUCTURE_FILE}")
    nodes = load_nodes(STRUCTURE_FILE)
    walk_nodes(nodes)
    print("\nГотово: все недостающие .tex-файлы созданы (существующие не трогали).")


if __name__ == "__main__":
    main()
