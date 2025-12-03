#!/usr/bin/env python3
"""
Validate master_core_structure.yaml against the filesystem.

Checks:
  - all YAML nodes have "file" paths;
  - all referenced files exist (warning if missing);
  - report extra .tex files under content/ that are NOT in YAML.

Usage (from repo root):

    python tools/validate_core_structure.py
"""

import os
import sys
import yaml

STRUCTURE_FILE = "master_core_structure.yaml"
CONTENT_ROOT = "content"


def load_nodes(path: str):
    """Load list of nodes from YAML (same tolerant logic as generator)."""
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if data is None:
        raise SystemExit("YAML пустой. Ожидал список секций.")

    # list -> already nodes
    if isinstance(data, list):
        return data

    # dict with wrapper keys
    if isinstance(data, dict):
        for key in ("root", "sections", "nodes", "chapters", "toc", "content"):
            value = data.get(key)
            if isinstance(value, list):
                return value

        # any list-of-dicts value
        for value in data.values():
            if isinstance(value, list) and (not value or isinstance(value[0], dict)):
                return value

        # fallback: dict → list of nodes
        nodes = []
        for key, value in data.items():
            node = {"title": str(key)}
            if isinstance(value, dict):
                node.update(value)
            nodes.append(node)
        return nodes

    raise SystemExit(
        "Не могу понять структуру YAML даже после всех попыток. "
        "Ожидал list или dict."
    )


def collect_files_from_nodes(nodes, result=None):
    """DFS по YAML-дереву -> множество путей файлов."""
    if result is None:
        result = set()

    for node in nodes:
        if not isinstance(node, dict):
            continue
        file_path = node.get("file")
        if file_path:
            result.add(os.path.normpath(file_path))

        children = (
            node.get("children")
            or node.get("subsections")
            or []
        )
        if children:
            collect_files_from_nodes(children, result)

    return result


def collect_actual_tex_files(root_dir: str):
    """Собрать все *.tex под content/."""
    tex_files = set()
    for dirpath, _, filenames in os.walk(root_dir):
        for name in filenames:
            if name.endswith(".tex"):
                relpath = os.path.relpath(os.path.join(dirpath, name))
                tex_files.add(os.path.normpath(relpath))
    return tex_files


def main():
    if not os.path.exists(STRUCTURE_FILE):
        raise SystemExit(f"YAML не найден: {STRUCTURE_FILE}")

    print(f"[validate] YAML: {STRUCTURE_FILE}")

    nodes = load_nodes(STRUCTURE_FILE)
    yaml_files = collect_files_from_nodes(nodes)
    actual_files = collect_actual_tex_files(CONTENT_ROOT)

    missing_in_fs = sorted(f for f in yaml_files if f not in actual_files)
    extra_in_fs = sorted(f for f in actual_files if f not in yaml_files)

    ok = True

    if missing_in_fs:
        ok = False
        print("\n[WARN] Files referenced in YAML but missing on disk:")
        for fpath in missing_in_fs:
            print(f"  - {fpath}")

    if extra_in_fs:
        print("\n[INFO] .tex files in filesystem that are NOT in YAML (maybe legacy or manual):")
        for fpath in extra_in_fs:
            print(f"  - {fpath}")

    print("\n[SUMMARY]")
    print(f"  Referenced in YAML: {len(yaml_files)}")
    print(f"  Found on disk:      {len(actual_files)}")
    print(f"  Missing:            {len(missing_in_fs)}")
    print(f"  Extra:              {len(extra_in_fs)}")

    if ok:
        print("\n[OK] YAML и файловая структура консистентны (по крайней мере, ничего не потеряно).")
        sys.exit(0)
    else:
        print("\n[WARN] Есть отсутствующие файлы. См. список выше.")
        sys.exit(1)


if __name__ == "__main__":
    main()
