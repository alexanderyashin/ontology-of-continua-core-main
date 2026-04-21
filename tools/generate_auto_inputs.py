#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
Generate LaTeX \input lists from master_core_structure.yaml.

Primary outputs:

    content/_auto_core_inputs.tex
    content/_auto_core_narrative_inputs.tex
    content/_auto_core_technical_appendix_inputs.tex
    content/_auto_core_reference_appendix_inputs.tex
    content/_auto_core_platinum_main_inputs.tex
    content/_auto_core_platinum_technical_appendix_inputs.tex
    content/_auto_core_platinum_reference_appendix_inputs.tex
    content/_auto_core_platinum_toe_support_inputs.tex

The same files are mirrored into:

    releases/oc_core_1_3/monograph/source/content/

`content/_auto_core_inputs.tex` remains the canonical full DFS compatibility
stream. The platinum files drive the flagship English master.
"""

import argparse
import sys
from collections import Counter
from pathlib import Path

try:
    import yaml
except ImportError:
    print("[ERROR] PyYAML is required: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


RELEASE_SOURCE_ROOT = Path("releases/oc_core_1_3/monograph/source")

COMPAT_NARRATIVE_CORE_PATHS = {
    "content/01_intro.tex",
    "content/02_background.tex",
    "content/03_model.tex",
    "content/04_results.tex",
    "content/05_discussion.tex",
    "content/06_conclusion.tex",
    "content/07_figures.tex",
    "content/08_boundary.tex",
    "content/09_thresholds.tex",
    "content/10_klevels_full.tex",
    "content/11_operators_full.tex",
    "content/12_collapse_rebirth.tex",
    "content/13_branching_topology.tex",
    "content/14_disciplines_extended.tex",
    "content/15_falsifiability_extended.tex",
}

COMPAT_TECHNICAL_APPENDIX_PATHS = {
    "content/16_modules_master.tex",
    "content/k_levels/klevels_master.tex",
    "content/m_spaces/mspaces_master.tex",
    "content/crossk/crossk_master.tex",
    "content/cycles/cycles_master.tex",
    "content/jets/jets_master.tex",
    "content/processes/processes_master.tex",
    "content/operators_universal.tex",
    "content/theorems_master.tex",
    "content/complexity_S.tex",
}

COMPAT_REFERENCE_APPENDIX_PATHS = {
    "content/experiments/experiments_master.tex",
    "content/falsifiability/falsifiability_master.tex",
    "content/predictions/predictions_master.tex",
}

FLAGSHIP_OMIT_PATHS = {
    "content/axioms_full.tex",
    "content/toe/toe_master.tex",
}

PLATINUM_MAIN_PATHS = [
    "content/01_intro.tex",
    "content/02_background.tex",
    "content/03_model.tex",
    "content/04_results.tex",
    "content/05_discussion.tex",
    "content/06_conclusion.tex",
    "content/08_boundary.tex",
    "content/09_thresholds.tex",
    "content/10_klevels_full.tex",
    "content/11_operators_full.tex",
    "content/12_collapse_rebirth.tex",
    "content/13_branching_topology.tex",
    "content/14_disciplines_extended.tex",
    "content/15_falsifiability_extended.tex",
    "content/16_modules_master.tex",
]

PLATINUM_TECHNICAL_SPECS = [
    ("k_levels_master", "subtree"),
    ("m_spaces_master", "subtree"),
    ("crossk_master", "subtree"),
    ("cycles_master", "subtree"),
    ("jets_master", "subtree"),
    ("processes_master", "subtree"),
    ("operators_universal", "root_only"),
    ("theorems_master", "root_only"),
    ("complexity_S", "root_only"),
]

PLATINUM_REFERENCE_SPECS = [
    ("experiments_master", "subtree"),
    ("falsifiability_master", "subtree"),
    ("predictions_master", "subtree"),
]

PLATINUM_TOE_SUPPORT_PATHS = [
    "content/toe/toe_k0",
    "content/toe/toe_k1",
    "content/toe/toe_k2",
    "content/toe/toe_k3",
    "content/toe/toe_k4",
    "content/toe/toe_k5",
    "content/toe/toe_k6",
    "content/toe/toe_k7",
    "content/toe/toe_k8",
    "content/toe/toe_k9",
    "content/toe/toe_k10",
    "content/toe/toe_k11",
    "content/toe/toe_k12",
]

PLATINUM_NON_AUTO_COVERAGE = {
    "content/07_figures.tex": "appendix N figure atlas",
    "content/axioms_full.tex": "appendix B axioms full",
    "content/toe/toe_master.tex": "chapter 25 + appendix Q synthesis support dossiers",
}


def normalize_path(path_value):
    return str(path_value).replace("\\", "/")


def dedupe_keep_order(paths):
    ordered = []
    seen = set()
    for path in paths:
        norm = normalize_path(path)
        if norm in seen:
            continue
        seen.add(norm)
        ordered.append(norm)
    return ordered


def load_yaml(path: Path):
    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    if data is None:
        raise SystemExit("YAML is empty. Expected a section structure.")
    return data


def extract_root_nodes(data):
    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        root = data.get("root")
        if isinstance(root, dict) and isinstance(root.get("sections"), list):
            return root["sections"]

        if isinstance(data.get("sections"), list):
            return data["sections"]

        if isinstance(root, list):
            return root

        for key in ("nodes", "chapters", "toc", "content"):
            value = data.get(key)
            if isinstance(value, list):
                return value

        for value in data.values():
            if isinstance(value, list) and (not value or isinstance(value[0], dict)):
                return value

        nodes = []
        for key, value in data.items():
            node = {"title": str(key)}
            if isinstance(value, dict):
                node.update(value)
            nodes.append(node)
        return nodes

    raise SystemExit(
        "Unsupported YAML structure. Expected a list or a dict with nested nodes."
    )


def iter_children(node):
    if not isinstance(node, dict):
        return []
    for key in ("children", "subsections", "nodes", "sections"):
        value = node.get(key)
        if isinstance(value, list):
            return value
    return []


def flatten_paths(nodes):
    collected = []

    def walk(items):
        for item in items:
            if isinstance(item, str):
                collected.append(normalize_path(item))
                continue

            if not isinstance(item, dict):
                continue

            path = item.get("path") or item.get("file")
            if path:
                collected.append(normalize_path(path))

            children = iter_children(item)
            if children:
                walk(children)

    walk(nodes)
    return collected


def extract_tex_paths(yaml_data):
    nodes = extract_root_nodes(yaml_data)
    paths = dedupe_keep_order(flatten_paths(nodes))
    if not paths:
        raise ValueError("Could not extract any paths from YAML.")
    return paths


def build_node_index(nodes):
    index = {}

    def walk(items):
        for item in items:
            if not isinstance(item, dict):
                continue
            node_id = item.get("id")
            if node_id:
                index[node_id] = item
            children = iter_children(item)
            if children:
                walk(children)

    walk(nodes)
    return index


def node_root_path(node):
    path = node.get("path") or node.get("file")
    if not path:
        raise ValueError(f"Node {node.get('id', '<unknown>')} has no path/file field.")
    return normalize_path(path)


def subtree_paths(node):
    paths = []

    def walk(current):
        paths.append(node_root_path(current))
        children = iter_children(current)
        for child in children:
            if isinstance(child, dict):
                walk(child)
            elif isinstance(child, str):
                paths.append(normalize_path(child))

    walk(node)
    return dedupe_keep_order(paths)


def expand_node_specs(index, specs):
    paths = []
    for node_id, mode in specs:
        if node_id not in index:
            raise ValueError(f"Unknown node id in platinum tier spec: {node_id}")
        node = index[node_id]
        if mode == "root_only":
            paths.append(node_root_path(node))
        elif mode == "subtree":
            paths.extend(subtree_paths(node))
        else:
            raise ValueError(f"Unknown node expansion mode: {mode}")
    return dedupe_keep_order(paths)


def build_compatibility_tiers(paths):
    tiers = {
        "narrative": [],
        "technical": [],
        "reference": [],
    }

    for path in paths:
        if path in FLAGSHIP_OMIT_PATHS:
            continue
        if path in COMPAT_NARRATIVE_CORE_PATHS:
            tiers["narrative"].append(path)
        elif path in COMPAT_TECHNICAL_APPENDIX_PATHS:
            tiers["technical"].append(path)
        elif path in COMPAT_REFERENCE_APPENDIX_PATHS:
            tiers["reference"].append(path)

    return tiers


def build_platinum_tiers(index):
    return {
        "main": dedupe_keep_order(PLATINUM_MAIN_PATHS),
        "technical": expand_node_specs(index, PLATINUM_TECHNICAL_SPECS),
        "reference": expand_node_specs(index, PLATINUM_REFERENCE_SPECS),
        "toe_support": dedupe_keep_order(PLATINUM_TOE_SUPPORT_PATHS),
    }


def validate_paths_exist(paths, label):
    missing = [path for path in paths if not Path(path).exists()]
    if missing:
        formatted = "\n  - ".join(missing)
        raise ValueError(f"Missing {label} paths:\n  - {formatted}")


def validate_platinum_coverage(full_paths, tiers):
    full_set = set(full_paths)
    counter = Counter()

    for tier_name in ("main", "technical", "reference"):
        for path in tiers[tier_name]:
            if path not in full_set:
                raise ValueError(
                    f"Path {path} in platinum tier {tier_name} is not present in full DFS set."
                )
            counter[path] += 1

    for path in PLATINUM_NON_AUTO_COVERAGE:
        if path not in full_set:
            raise ValueError(
                f"Non-auto platinum coverage path {path} is not present in full DFS set."
            )
        counter[path] += 1

    duplicates = [path for path in full_paths if counter[path] > 1]
    missing = [path for path in full_paths if counter[path] == 0]

    if duplicates:
        formatted = "\n  - ".join(duplicates)
        raise ValueError(
            "Platinum coverage duplicates detected. Each full-DFS path must appear "
            "exactly once in a tier or an explicitly justified non-auto slot:\n"
            f"  - {formatted}"
        )

    if missing:
        formatted = "\n  - ".join(missing)
        raise ValueError(
            "Platinum coverage is incomplete. Missing full-DFS paths:\n"
            f"  - {formatted}"
        )


def mirrored_targets(output_path: Path):
    return [output_path, RELEASE_SOURCE_ROOT / output_path]


def write_inputs_file(output_path: Path, paths):
    header = [
        "% ==========================================",
        "%  Auto-generated by tools/generate_auto_inputs.py",
        "%  DO NOT EDIT THIS FILE MANUALLY",
        "% ==========================================",
        "",
    ]

    lines = header[:]
    if not paths:
        lines.append("% No auto-included sections defined.")
        lines.append("")
    else:
        for path in paths:
            lines.append(f"\\input{{{normalize_path(path)}}}")
        lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")


def write_mirrored_inputs_file(output_path: Path, paths):
    for target in mirrored_targets(output_path):
        write_inputs_file(target, paths)


def main():
    parser = argparse.ArgumentParser(
        description="Generate LaTeX \\input lists from master_core_structure.yaml"
    )
    parser.add_argument(
        "--yaml",
        default="master_core_structure.yaml",
        help="YAML file describing the Core structure",
    )
    parser.add_argument(
        "--output",
        default="content/_auto_core_inputs.tex",
        help="Path to the generated full DFS compatibility .tex",
    )
    args = parser.parse_args()

    yaml_path = Path(args.yaml)
    output_path = Path(args.output)

    if not yaml_path.exists():
        print(f"[ERROR] YAML file not found: {yaml_path}", file=sys.stderr)
        sys.exit(1)

    data = load_yaml(yaml_path)
    nodes = extract_root_nodes(data)
    full_paths = extract_tex_paths(data)
    node_index = build_node_index(nodes)

    validate_paths_exist(full_paths, "full DFS")

    print(f"[inputs] Using YAML: {yaml_path}")
    print(f"[inputs] Full DFS path count: {len(full_paths)}")

    write_mirrored_inputs_file(output_path, full_paths)
    print(f"[inputs] Written full DFS compatibility stream to {output_path}")

    compatibility_tiers = build_compatibility_tiers(full_paths)
    compatibility_targets = {
        "narrative": output_path.parent / "_auto_core_narrative_inputs.tex",
        "technical": output_path.parent / "_auto_core_technical_appendix_inputs.tex",
        "reference": output_path.parent / "_auto_core_reference_appendix_inputs.tex",
    }
    for tier_name, tier_paths in compatibility_tiers.items():
        write_mirrored_inputs_file(compatibility_targets[tier_name], tier_paths)
        print(
            f"[inputs] Written compatibility {tier_name} tier "
            f"({len(tier_paths)} paths) to {compatibility_targets[tier_name]}"
        )

    platinum_tiers = build_platinum_tiers(node_index)
    validate_paths_exist(platinum_tiers["main"], "platinum main")
    validate_paths_exist(platinum_tiers["technical"], "platinum technical")
    validate_paths_exist(platinum_tiers["reference"], "platinum reference")
    validate_paths_exist(platinum_tiers["toe_support"], "platinum synthesis support")
    validate_platinum_coverage(full_paths, platinum_tiers)

    platinum_targets = {
        "main": output_path.parent / "_auto_core_platinum_main_inputs.tex",
        "technical": output_path.parent / "_auto_core_platinum_technical_appendix_inputs.tex",
        "reference": output_path.parent / "_auto_core_platinum_reference_appendix_inputs.tex",
        "toe_support": output_path.parent / "_auto_core_platinum_toe_support_inputs.tex",
    }
    for tier_name, tier_paths in platinum_tiers.items():
        write_mirrored_inputs_file(platinum_targets[tier_name], tier_paths)
        print(
            f"[inputs] Written platinum {tier_name} tier "
            f"({len(tier_paths)} paths) to {platinum_targets[tier_name]}"
        )

    print("[inputs] Platinum coverage check: PASS")
    for path, reason in PLATINUM_NON_AUTO_COVERAGE.items():
        print(f"[inputs] Non-auto coverage: {path} -> {reason}")


if __name__ == "__main__":
    main()
