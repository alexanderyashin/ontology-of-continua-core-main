#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate consistency between master_core_structure.yaml and content/*.tex files.

Ziel:
  - YAML einlesen (tolerant gegenüber verschiedenen Schemata).
  - Alle referenzierten .tex-Pfade einsammeln.
  - Filesystem unter content/ scannen.
  - Missing & Extra Dateien melden.

Unterstützte YAML-Layouts (ähnlich wie generate_auto_inputs.py):

1) Einfacher Listenmodus:
   - content/01_intro.tex
   - path: content/02_background.tex

2) Baum mit root/sections/nodes:
   root:
     sections:
       - path: content/foo.tex
       - nodes:
           - path: content/bar.tex

3) Core-Schema:
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

5) Modules (optional, wenn du später Modul-Master-Dateien tracken willst):
   modules:
     name:
       master: { path: content/..., status: ... }
"""

import sys
from pathlib import Path
from typing import Iterable, Set, Dict, Any

import yaml  # pip install pyyaml

STRUCTURE_FILE = "master_core_structure.yaml"
CONTENT_ROOT = Path("content")


def _iter_nodes_list(nodes: Iterable[Any]) -> Iterable[Dict[str, Any]]:
    """Hilfsfunktion: sichert ab, dass wir nur dict-Knoten iterieren."""
    for n in nodes:
        if isinstance(n, dict):
            yield n


def collect_paths_from_yaml(data: Any) -> Set[str]:
    """
    Sammle alle relevanten .tex-Pfade aus der YAML-Struktur.
    Gibt relative Pfade wie 'content/01_intro.tex' zurück.
    """

    paths: Set[str] = set()

    # --- 1) Core-Schema: core.main_article.sections[*].path
    if isinstance(data, dict):
        core = data.get("core")
        if isinstance(core, dict):
            main_article = core.get("main_article")
            if isinstance(main_article, dict):
                sections = main_article.get("sections")
                if isinstance(sections, list):
                    for node in _iter_nodes_list(sections):
                        p = node.get("path")
                        if isinstance(p, str):
                            paths.add(p)

    # --- 2) Top-level sections: sections[*].path
    if isinstance(data, dict):
        sections = data.get("sections")
        if isinstance(sections, list):
            for node in _iter_nodes_list(sections):
                p = node.get("path")
                if isinstance(p, str):
                    paths.add(p)

    # --- 3) root/sections/nodes-bäume
    def walk_tree(node: Any):
        if isinstance(node, dict):
            p = node.get("file") or node.get("path")
            if isinstance(p, str):
                paths.add(p)
            # typische Schlüssel für Kinder:
            for key in ("children", "subsections", "nodes", "sections"):
                child = node.get(key)
                if isinstance(child, list):
                    for c in child:
                        walk_tree(c)
        elif isinstance(node, list):
            for c in node:
                walk_tree(c)

    if isinstance(data, dict):
        for key in ("root", "toc", "content"):
            if key in data:
                walk_tree(data[key])

    # --- 4) Modules.*.master.path
    if isinstance(data, dict):
        modules = data.get("modules")
        if isinstance(modules, dict):
            for m in modules.values():
                if isinstance(m, dict):
                    master = m.get("master")
                    if isinstance(master, dict):
                        p = master.get("path")
                        if isinstance(p, str):
                            paths.add(p)

    # --- 5) Fallback: einfaches oberes Listenformat
    if not paths and isinstance(data, list):
        for node in _iter_nodes_list(data):
            p = node.get("file") or node.get("path")
            if isinstance(p, str):
                paths.add(p)

    return paths


def load_structure_file(path: Path) -> Any:
    if not path.exists():
        print(f"[ERROR] Structure file not found: {path}", file=sys.stderr)
        sys.exit(1)

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if data is None:
        print(f"[ERROR] YAML {path} ist leer.", file=sys.stderr)
        sys.exit(1)

    return data


def collect_tex_files(root: Path) -> Set[str]:
    """
    Sammle alle .tex-Dateien unterhalb von CONTENT_ROOT.
    Wir geben Pfade relativ zum Repo-Root zurück (z.B. 'content/foo.tex').
    """
    files: Set[str] = set()
    for p in root.rglob("*.tex"):
        # Nur reguläre Dateien
        if p.is_file():
            files.add(str(p.as_posix()))
    return files


def main():
    structure_path = Path(STRUCTURE_FILE)
    print(f"[validate] YAML: {structure_path}")

    data = load_structure_file(structure_path)
    yaml_paths = collect_paths_from_yaml(data)
    tex_files = collect_tex_files(CONTENT_ROOT)

    # Normalisieren: alles in forward slashes, keine ./-Präfixe
    yaml_paths_norm = {Path(p).as_posix().lstrip("./") for p in yaml_paths}
    tex_files_norm = {Path(p).as_posix().lstrip("./") for p in tex_files}

    missing = sorted(yaml_paths_norm - tex_files_norm)
    extra = sorted(tex_files_norm - yaml_paths_norm)

    print()
    print("[INFO] Files referenced in YAML:")
    if yaml_paths_norm:
        for p in sorted(yaml_paths_norm):
            print(f"  - {p}")
    else:
        print("  (none)")

    print()
    print("[INFO] .tex files in filesystem that are NOT in YAML (maybe legacy or manual):")
    if extra:
        for p in extra:
            print(f"  - {p}")
    else:
        print("  (none)")

    print()
    print("[SUMMARY]")
    print(f"  Referenced in YAML: {len(yaml_paths_norm)}")
    print(f"  Found on disk:      {len(tex_files_norm)}")
    print(f"  Missing:            {len(missing)}")
    print(f"  Extra:              {len(extra)}")

    if missing:
        print()
        print("[ERROR] Missing files (in YAML but not on disk):")
        for p in missing:
            print(f"  - {p}")
        # Du kannst hier entscheiden, ob fehlende Files den Build hart abbrechen sollen:
        # sys.exit(1)


if __name__ == "__main__":
    main()

