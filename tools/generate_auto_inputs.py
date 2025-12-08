#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
Generate a LaTeX \input list from master_core_structure.yaml.

The generator walks the hierarchical YAML structure (root/sections + children)
and writes a flat list of \input{...} lines into:

    content/_auto_core_inputs.tex

Supported YAML shapes (tolerant):

1) New Core 1.1 schema (recommended):

root:
  entrypoint: main.tex
  sections:
    - id: intro
      path: content/01_intro.tex
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

- top-level list of paths or nodes
- dict with keys: root / sections / nodes / chapters / toc / content
- dict-of-dicts: {Title: {file: ..., children: [...]}, ...}

Each node may contain:
  - path or file: path to .tex
  - title / id: optional metadata (ignored here)
  - children / subsections / nodes / sections: optional nested nodes
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

def load_yaml(path: Path):
    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
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
      - {nodes|chapters|toc|content: [...]}
      - first list-of-dicts in values
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

        # Fallback: first list-of-dicts
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
    if not isinstance(node, dict):
        return []
    for key in ("children", "subsections", "nodes", "sections"):
        value = node.get(key)
        if isinstance(value, list):
            return value
    return []


def flatten_paths(nodes):
    """
    Recursively walk node tree and collect all path/file entries (DFS order).

    Nodes may be:
      - strings (treated directly as paths),
      - dicts with "path"/"file" and optional children.
    """
    collected = []

    def _walk(items):
        for item in items:
            # Case: plain string => direct path
            if isinstance(item, str):
                collected.append(item)
                continue

            if not isinstance(item, dict):
                continue

            path = item.get("path") or item.get("file")
            if path:
                collected.append(path)

            children = iter_children(item)
            if children:
                _walk(children)

    _walk(nodes)
    return collected


def extract_tex_paths(yaml_data):
    """
    Unified extractor:

    1) find root node list (extract_root_nodes),
    2) flatten whole tree (including children),
    3) deduplicate while preserving order.
    """
    nodes = extract_root_nodes(yaml_data)
    paths = flatten_paths(nodes)

    # Deduplicate by normalized string path, keep order
    uniq = []
    seen = set()
    for p in paths:
        s = str(p).replace("\\", "/")
        if s in seen:
            continue
        seen.add(s)
        uniq.append(s)

    if not uniq:
        raise ValueError(
            "Не смог извлечь ни одного пути из YAML.\n"
            "Проверь root/sections или другие обёртки."
        )

    print(f"[inputs-debug] total unique paths (DFS): {len(uniq)}")
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
        "%  Auto-generated by tools/generate_auto_inputs.py",
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
        data = load_yaml(yaml_path)
    except Exception as e:
        print(f"[ERROR] Failed to parse YAML: {e}", file=sys.stderr)
        write_inputs_file(out_path, [])
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
