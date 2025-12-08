#!/usr/bin/env python3
"""
Generate missing LaTeX content files from a YAML structure.

Usage (from repo root):

    python tools/generate_core_from_yaml.py          # uses master_core_structure.yaml
    python tools/generate_core_from_yaml.py path/to/your.yaml

Supported YAML shapes (tolerant):

1) New Core 1.1 schema (recommended):

root:
  entrypoint: main.tex
  sections:
    - id: intro
      path: content/01_intro.tex
    - id: klevels_full
      path: content/10_klevels_full.tex
    - id: modules_master
      path: content/16_modules_master.tex
      children:
        - id: k_levels_master
          path: content/k_levels/klevels_master.tex
          children:
            - id: k0
              path: content/k_levels/k0.tex
            ...

2) Legacy examples:

- top-level list of nodes
- dict with keys: root / sections / nodes / chapters / toc / content
- dict-of-dicts: {Title: {file: ..., children: [...]}, ...}

Each node may contain:
  - path or file: path to .tex
  - title / id: optional title
  - children / subsections / nodes / sections: optional nested nodes
"""

import os
import sys
import textwrap

import yaml  # pip install pyyaml

# ------------------------------------------------------------
# Settings
# ------------------------------------------------------------

# By default read master_core_structure.yaml from repo root.
STRUCTURE_FILE = sys.argv[1] if len(sys.argv) > 1 else "master_core_structure.yaml"

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

# If True, add a simple \section / \subsection header to new files.
ADD_LATEX_HEADER = True


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def load_yaml(path: str):
    """Load raw YAML."""
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if data is None:
        raise SystemExit("YAML пустой. Ожидал структуру секций.")
    return data


def extract_root_nodes(data):
    """
    Extract the top-level list of nodes from various wrapper schemes.

    Supports:
      - top-level list
      - {root: {sections: [...]}}
      - {sections: [...]}
      - {root: [...]}
      - any dict value that is a list[dict]
      - dict-of-dicts fallback
    """
    # 1) Direct list
    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        # New Core schema: root: {entrypoint: ..., sections: [...]}
        root = data.get("root")
        if isinstance(root, dict) and isinstance(root.get("sections"), list):
            return root["sections"]

        # Simple wrapper: sections: [...]
        if isinstance(data.get("sections"), list):
            return data["sections"]

        # Legacy: root: [...]
        if isinstance(root, list):
            return root

        # Legacy: other typical keys
        for key in ("nodes", "chapters", "toc", "content"):
            value = data.get(key)
            if isinstance(value, list):
                return value

        # Fallback: first list-of-dicts in values
        for value in data.values():
            if isinstance(value, list) and (not value or isinstance(value[0], dict)):
                return value

        # Ultimate fallback: dict-of-dicts → list of nodes
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


def iter_children(node):
    """
    Return list of children for a node.

    Supports keys:
      - children
      - subsections
      - nodes
      - sections
    """
    for key in ("children", "subsections", "nodes", "sections"):
        value = node.get(key)
        if isinstance(value, list):
            return value
    return []


def ensure_dir_for_file(filepath: str) -> None:
    """Create directory for file if it does not exist."""
    directory = os.path.dirname(filepath)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)


def make_latex_header(title: str, level: int) -> str:
    """
    level 0 -> \\section
    level 1 -> \\subsection
    level 2 -> \\subsubsection
    >=3   -> \\paragraph
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
    """Create .tex file if it does not exist yet."""
    # Normalize separators
    filepath = filepath.replace("\\", "/")
    ensure_dir_for_file(filepath)

    if os.path.exists(filepath):
        print(f"[skip   ] {filepath} (already exists)")
        return

    header = make_latex_header(title, level)
    body = DEFAULT_PLACEHOLDER.format(filepath=filepath)

    # Put header after the placeholder comment block — or before, as you prefer.
    content = body + header

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[create ] {filepath}")


def walk_nodes(nodes, level: int = 0) -> None:
    """Recursively walk node tree and create files."""
    for node in nodes:
        if not isinstance(node, dict):
            # Skip garbage in YAML
            continue

        # Accept both "path" (new) and "file" (legacy)
        file_path = node.get("path") or node.get("file")
        if file_path:
            title = (
                node.get("title")
                or node.get("id")
                or os.path.splitext(os.path.basename(file_path))[0]
            )
            create_file_if_missing(file_path, title, level)

        children = iter_children(node)
        if children:
            walk_nodes(children, level=level + 1)


# ------------------------------------------------------------
# main
# ------------------------------------------------------------

def main() -> None:
    if not os.path.exists(STRUCTURE_FILE):
        raise SystemExit(f"YAML не найден: {STRUCTURE_FILE}")

    print(f"Использую YAML структуру: {STRUCTURE_FILE}")
    data = load_yaml(STRUCTURE_FILE)
    nodes = extract_root_nodes(data)
    walk_nodes(nodes)
    print("\nГотово: все недостающие .tex-файлы созданы (существующие не трогали).")


if __name__ == "__main__":
    main()
