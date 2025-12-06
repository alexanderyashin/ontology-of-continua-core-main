#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate LaTeX \\input lines for the Core main article from master_core_structure.yaml.

Unterstützte YAML-Layouts (kombiniert):

1) Einfacher Listenmodus (Legacy):
   - content/01_intro.tex
   - path: content/02_background.tex

2) Baum mit root/sections/nodes (Legacy):
   root:
     sections:
       - path: content/foo.tex
       - nodes:
           - path: content/bar.tex

3) Aktuelles Core-Schema:
   core:
     main_article:
       entrypoint: main.tex
       sections:
         - id: intro
           path: content/01_intro.tex
         ...

4) Top-level sections:
   sections:
     - id: ...
       path: content/...

5) Module-Master-Dateien:
   modules:
     k_levels:
       master: { path: content/k_levels/klevels_master.tex, status: ... }
     ...

Der Generator sammelt ALLE relevanten Pfade:
- core.main_article.sections
- sections (top-level)
- root/sections/nodes
- modules.*.master.path
- einfache Liste (falls verwendet)

und schreibt sie (dedupliziert, in Reihenfolge) nach:
  content/_auto_core_inputs.tex
"""

import argparse
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("[ERROR] PyYAML is required: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


# --------------------------------------------------------------------
# YAML loaders / extractors
# --------------------------------------------------------------------

def _extract_from_simple_list(data):
    """
    Case 1: top-level YAML is just a list of paths or dicts with 'path'.
    Example:
      - content/01_intro.tex
      - path: content/02_background.tex
    """
    paths = []
    for item in data:
        if isinstance(item, str):
            paths.append(item)
        elif isinstance(item, dict) and "path" in item:
            paths.append(item["path"])
    return paths


def _extract_from_root_tree(data):
    """
    Case 2: generic tree with root/sections/nodes (legacy).

    Expected shape (conceptually):
      root:
        sections:
          - path: content/foo.tex
          - nodes:
              - path: content/bar.tex
    """

    def walk_node(node, acc):
        if isinstance(node, dict):
            # direct path
            if "path" in node and isinstance(node["path"], str):
                acc.append(node["path"])
            # nested sections / nodes / children
            for key in ("sections", "nodes", "children"):
                if key in node and isinstance(node[key], list):
                    for child in node[key]:
                        walk_node(child, acc)

    paths = []
    root = data.get("root", {})
    if isinstance(root, dict):
        sections = root.get("sections", [])
        if isinstance(sections, list):
            for node in sections:
                walk_node(node, paths)
    return paths


def _extract_from_core_main_article(data):
    """
    Case 3 (CURRENT PROJECT): structure with 'core' / 'main_article' / 'sections'.

    Expected shape:
    core:
      main_article:
        entrypoint: main.tex
        sections:
          - id: intro
            path: content/01_intro.tex
          - id: background
            path: content/02_background.tex
          ...
    """
    core = data.get("core", {})
    if not isinstance(core, dict):
        return []

    main_article = core.get("main_article", {})
    if not isinstance(main_article, dict):
        return []

    sections = main_article.get("sections", [])
    if not isinstance(sections, list):
        return []

    paths = []
    for sec in sections:
        if isinstance(sec, dict) and "path" in sec:
            paths.append(sec["path"])
    return paths


def _extract_from_top_sections(data):
    """
    Ergänzung: top-level 'sections' (wie in deinem master_core_structure.yaml).

    Expected shape:
      sections:
        - id: ...
          path: content/...
    """
    paths = []
    sections = data.get("sections")
    if isinstance(sections, list):
        for sec in sections:
            if isinstance(sec, dict) and "path" in sec:
                paths.append(sec["path"])
    return paths


def _extract_from_modules_master(data):
    """
    Ergänzung: modules.*.master.path

    Expected shape:
      modules:
        k_levels:
          master: { path: content/k_levels/klevels_master.tex, status: ... }
        m_spaces:
          master: { path: content/m_spaces/mspaces_master.tex, status: ... }
        ...
    """
    paths = []
    modules = data.get("modules")
    if not isinstance(modules, dict):
        return paths

    for name, mod in modules.items():
        if not isinstance(mod, dict):
            continue
        master = mod.get("master")
        if isinstance(master, dict) and "path" in master:
            paths.append(master["path"])
    return paths


def extract_tex_paths(yaml_data):
    """
    Unified extractor:
      - simple list (legacy),
      - core.main_article.sections (основной артикул),
      - top-level sections,
      - root/sections/nodes (legacy),
      - modules.*.master.path (мастер-файлы модулей).

    Все пути объединяются и дедуплицируются по строковому значению.
    """
    # Case 1: plain list
    if isinstance(yaml_data, list):
        return _extract_from_simple_list(yaml_data)

    if not isinstance(yaml_data, dict):
        raise ValueError("Ожидал либо список, либо словарь с описанием структуры Core.")

    paths = []

    # 1) current Core schema (main article)
    paths.extend(_extract_from_core_main_article(yaml_data))

    # 2) top-level 'sections'
    paths.extend(_extract_from_top_sections(yaml_data))

    # 3) generic tree with root/sections/nodes (legacy)
    if "root" in yaml_data:
        paths.extend(_extract_from_root_tree(yaml_data))

    # 4) modules.*.master.path (module masters)
    paths.extend(_extract_from_modules_master(yaml_data))

    # Deduplicate by normalized string path, keep order
    uniq = []
    seen = set()
    for p in paths:
        s = str(p)
        if s in seen:
            continue
        seen.add(s)
        uniq.append(s)

    if not uniq:
        raise ValueError(
            "Не смог извлечь ни одного пути из YAML.\n"
            "Проверь core.main_article.sections, sections, root/sections и modules.*.master."
        )

    return uniq


# --------------------------------------------------------------------
# Writer
# --------------------------------------------------------------------

def write_inputs_file(output_path: Path, paths):
    """
    Write \\input lines into the given file.
    If list is empty, still write a comment header so LaTeX doesn't break.
    """
    header = [
        "% ==========================================",
        "%  Auto-generated by generate_auto_inputs.py",
        "%  DO NOT EDIT THIS FILE MANUALLY",
        "% ==========================================",
        "",
    ]

    lines = header[:]

    if not paths:
        lines.append("% No auto-included sections defined in YAML.\n")
    else:
        for p in paths:
            # Normalize to forward slashes for LaTeX
            s = str(p).replace("\\", "/")
            lines.append(f"\\input{{{s}}}")
        lines.append("")  # final newline

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")


# --------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate LaTeX \\input list from master_core_structure.yaml"
    )
    parser.add_argument(
        "--yaml",
        default="master_core_structure.yaml",
        help="YAML file describing Core structure",
    )
    parser.add_argument(
        "--output",
        default="content/_auto_core_inputs.tex",
        help="Path to the generated .tex with \\input lines",
    )

    args = parser.parse_args()

    yaml_path = Path(args.yaml)
    out_path = Path(args.output)

    if not yaml_path.exists():
        print(f"[ERROR] YAML file not found: {yaml_path}", file=sys.stderr)
        sys.exit(1)

    try:
        data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[ERROR] Failed to parse YAML: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        paths = extract_tex_paths(data)
    except Exception as e:
        print(f"[inputs] ERROR: {e}", file=sys.stderr)
        # Still write a minimal file to keep LaTeX happy
        write_inputs_file(out_path, [])
        sys.exit(1)

    print(f"[inputs] Using YAML: {yaml_path}")
    print(f"[inputs] Found {len(paths)} section(s) for auto-include.")
    write_inputs_file(out_path, paths)
    print(f"[inputs] Written {len(paths)} \\input lines to {out_path}")


if __name__ == "__main__":
    main()
