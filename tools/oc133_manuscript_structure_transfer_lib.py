from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
EDITORIAL = ROOT / "releases" / RELEASE_ID / "editorial"
STRUCTURE_DIR = EDITORIAL / "master_manuscript_structure"
LEGACY_L2_MD = EDITORIAL / "MASTER_MANUSCRIPT_L2_CHAPTER_STRUCTURE_1_3_3.md"
RECOVERED_MASTER_JSON = EDITORIAL / "MASTER_MANUSCRIPT_STRUCTURE_1_3_3.json"

EXPECTED_L1_TOTAL = 20
EXPECTED_L2_TOTAL = 164
MAX_DEPTH = 10

LEVEL_NAMES = {
    1: "top_level_block",
    2: "chapter",
    3: "section",
    4: "subsection",
    5: "subsubsection",
    6: "paragraph_group",
    7: "argument_move",
    8: "evidence_proof_example_slot",
    9: "transition_claim_support_slot",
    10: "paragraph_slot",
}

L3_TEMPLATES = [
    ("Purpose and Reader Task", "purpose_and_reader_task"),
    ("Core Material and Definitions", "core_material_and_definitions"),
    ("Evidence and Corpus Anchors", "evidence_and_corpus_anchors"),
    ("Boundary and Forward Transition", "boundary_and_forward_transition"),
]

DEEPER_CHAIN = {
    4: "Scope and Inclusion Rules",
    5: "Required Subclaim Coverage",
    6: "Paragraph Group Draft Slot",
    7: "Argument Move Draft Slot",
    8: "Evidence, Proof, or Example Draft Slot",
    9: "Claim-Support Transition Draft Slot",
    10: "Paragraph Draft Slot",
}

STOPWORDS = {
    "and",
    "the",
    "with",
    "from",
    "into",
    "that",
    "this",
    "core",
    "what",
    "does",
    "not",
    "claim",
    "claims",
    "release",
    "chapter",
    "section",
}

UNSAFE_TITLE_PATTERNS = [
    re.compile(r"^import:", re.I),
    re.compile(r"\.(?:tex|md|json|pdf|zip|ndjson)\b", re.I),
    re.compile(r"\b(?:route|payload|manifest|release[-_ ]machine|control[-_ ]plane)\b", re.I),
]


@dataclass(frozen=True)
class OutlineNode:
    node_id: str
    parent_id: str | None
    level: int
    order_path: list[int]
    outline_number: str
    title: str
    level_name: str
    status: str
    source: str
    provenance: list[dict[str, Any]]

    def to_json(self) -> dict[str, Any]:
        return {
            "level": self.level,
            "level_name": self.level_name,
            "node_id": self.node_id,
            "order_path": self.order_path,
            "outline_number": self.outline_number,
            "parent_id": self.parent_id,
            "provenance": self.provenance,
            "source": self.source,
            "status": self.status,
            "title": self.title,
        }


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def stable_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True).rstrip() + "\n"


def write_text_if_changed(path: Path, text: str) -> bool:
    normalized = text.rstrip() + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding="utf-8", errors="replace") == normalized:
        return False
    path.write_text(normalized, encoding="utf-8", newline="\n")
    return True


def node_id(level: int, order_path: list[int]) -> str:
    return f"OC133-MS-L{level:02d}-" + "-".join(f"{part:03d}" for part in order_path)


def outline_number(order_path: list[int]) -> str:
    return ".".join(str(part) for part in order_path)


def sort_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(nodes, key=lambda node: tuple(node["order_path"]))


def nodes_hash(nodes: list[dict[str, Any]]) -> str:
    return sha256_text(stable_json(sort_nodes(nodes)))


def artifact_paths(depth: int) -> tuple[Path, Path]:
    stem = f"MASTER_MANUSCRIPT_STRUCTURE_L{depth:02d}_1_3_3"
    return STRUCTURE_DIR / f"{stem}.json", STRUCTURE_DIR / f"{stem}.md"


def index_paths() -> tuple[Path, Path]:
    return (
        STRUCTURE_DIR / "MASTER_MANUSCRIPT_STRUCTURE_CASCADE_INDEX_1_3_3.json",
        STRUCTURE_DIR / "MASTER_MANUSCRIPT_STRUCTURE_CASCADE_INDEX_1_3_3.md",
    )


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def parse_l1_l2_source(path: Path = LEGACY_L2_MD) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not path.exists():
        raise FileNotFoundError(path)
    l1: list[dict[str, Any]] = []
    l2: list[dict[str, Any]] = []
    current_l1: int | None = None
    l1_re = re.compile(r"^##\s+(\d+)\.\s+(.+?)\s*$")
    l2_re = re.compile(r"^###\s+(\d+)\.(\d+)\s+(.+?)\s*$")
    for line_number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        if match := l1_re.match(line):
            current_l1 = int(match.group(1))
            l1.append(
                {
                    "index": current_l1,
                    "title": match.group(2).strip(),
                    "line": line_number,
                    "path": relative(path),
                }
            )
            continue
        if match := l2_re.match(line):
            parent = int(match.group(1))
            if current_l1 is not None and parent != current_l1:
                raise ValueError(f"L2 parent mismatch on line {line_number}: {line}")
            l2.append(
                {
                    "parent_index": parent,
                    "index": int(match.group(2)),
                    "title": match.group(3).strip(),
                    "line": line_number,
                    "path": relative(path),
                }
            )
    return l1, l2


def unsafe_reader_title(title: str) -> bool:
    return any(pattern.search(title) for pattern in UNSAFE_TITLE_PATTERNS)


def tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[A-Za-z0-9]+", text.lower())
        if len(token) >= 4 and token not in STOPWORDS
    }


def load_recovered_nodes() -> list[dict[str, Any]]:
    if not RECOVERED_MASTER_JSON.exists():
        return []
    data = json.loads(RECOVERED_MASTER_JSON.read_text(encoding="utf-8"))
    nodes: list[dict[str, Any]] = []
    for node in data.get("nodes", []):
        title = str(node.get("title", "")).strip()
        if not title or unsafe_reader_title(title):
            continue
        nodes.append(node)
    return nodes


def provenance_candidates(chapter_title: str, l1_title: str, recovered_nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    chapter_tokens = tokens(chapter_title) | tokens(l1_title)
    if not chapter_tokens:
        return []
    scored: list[tuple[int, str, dict[str, Any]]] = []
    for node in recovered_nodes:
        title = str(node.get("title", ""))
        score = len(chapter_tokens & tokens(title))
        if score <= 0:
            continue
        scored.append((score, title.lower(), node))
    scored.sort(key=lambda item: (-item[0], item[1]))
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()
    for score, _, node in scored:
        title = str(node.get("title", "")).strip()
        if title.lower() in seen:
            continue
        seen.add(title.lower())
        provenance = node.get("provenance") or []
        first = provenance[0] if provenance else {}
        candidates.append(
            {
                "commit": first.get("commit"),
                "line": first.get("line"),
                "node_id": node.get("node_id"),
                "path": first.get("path"),
                "role": node.get("role"),
                "score": score,
                "title": title,
            }
        )
        if len(candidates) == 3:
            break
    return candidates


def build_level_catalog() -> dict[int, list[dict[str, Any]]]:
    l1_items, l2_items = parse_l1_l2_source()
    if len(l1_items) != EXPECTED_L1_TOTAL:
        raise ValueError(f"Expected {EXPECTED_L1_TOTAL} L1 blocks, found {len(l1_items)}")
    if len(l2_items) != EXPECTED_L2_TOTAL:
        raise ValueError(f"Expected {EXPECTED_L2_TOTAL} L2 chapters, found {len(l2_items)}")

    recovered_nodes = load_recovered_nodes()
    catalog: dict[int, list[OutlineNode]] = {level: [] for level in range(1, MAX_DEPTH + 1)}
    l1_by_index = {item["index"]: item for item in l1_items}

    for l1 in l1_items:
        path = [l1["index"]]
        catalog[1].append(
            OutlineNode(
                node_id=node_id(1, path),
                parent_id=None,
                level=1,
                order_path=path,
                outline_number=outline_number(path),
                title=l1["title"],
                level_name=LEVEL_NAMES[1],
                status="APPROVED_FROZEN_BY_OWNER",
                source="owner_approved_l1_structure",
                provenance=[{"kind": "owner_approved_l1", "line": l1["line"], "path": l1["path"]}],
            )
        )

    for l2 in l2_items:
        l1 = l1_by_index[l2["parent_index"]]
        path2 = [l2["parent_index"], l2["index"]]
        l2_id = node_id(2, path2)
        catalog[2].append(
            OutlineNode(
                node_id=l2_id,
                parent_id=node_id(1, [l2["parent_index"]]),
                level=2,
                order_path=path2,
                outline_number=outline_number(path2),
                title=l2["title"],
                level_name=LEVEL_NAMES[2],
                status="DRAFT_STRUCTURE_ONLY",
                source="owner_approved_l2_source_demoted_to_draft_cascade",
                provenance=[{"kind": "owner_approved_l2_source", "line": l2["line"], "path": l2["path"]}],
            )
        )
        candidates = provenance_candidates(l2["title"], l1["title"], recovered_nodes)
        for l3_index, (title, source_key) in enumerate(L3_TEMPLATES, start=1):
            path3 = [*path2, l3_index]
            l3_id = node_id(3, path3)
            catalog[3].append(
                OutlineNode(
                    node_id=l3_id,
                    parent_id=l2_id,
                    level=3,
                    order_path=path3,
                    outline_number=outline_number(path3),
                    title=title,
                    level_name=LEVEL_NAMES[3],
                    status="DRAFT_STRUCTURE_ONLY",
                    source=f"deterministic_l3_template::{source_key}",
                    provenance=[
                        {"kind": "template", "chapter": l2["title"], "template": source_key},
                        {"candidates": candidates, "kind": "recovered_corpus_candidates"},
                    ],
                )
            )
            parent_id = l3_id
            parent_path = path3
            for level in range(4, MAX_DEPTH + 1):
                current_path = [*parent_path, 1]
                current_id = node_id(level, current_path)
                catalog[level].append(
                    OutlineNode(
                        node_id=current_id,
                        parent_id=parent_id,
                        level=level,
                        order_path=current_path,
                        outline_number=outline_number(current_path),
                        title=DEEPER_CHAIN[level],
                        level_name=LEVEL_NAMES[level],
                        status="DRAFT_SLOT",
                        source=f"deterministic_l{level}_draft_slot_template",
                        provenance=[{"kind": "template", "parent_level": level - 1, "parent_node_id": parent_id}],
                    )
                )
                parent_id = current_id
                parent_path = current_path

    return {level: [node.to_json() for node in sorted(nodes, key=lambda item: item.order_path)] for level, nodes in catalog.items()}


def payload_without_hash(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if key != "artifact_hash"}


def build_level_payload(depth: int, parent_payload: dict[str, Any] | None = None) -> dict[str, Any]:
    if depth < 1 or depth > MAX_DEPTH:
        raise ValueError(f"Depth out of range: {depth}")
    catalog = build_level_catalog()
    own_expansion = catalog[depth]
    if depth == 1:
        inherited_locked_nodes: list[dict[str, Any]] = []
        parent_artifact = None
        parent_artifact_hash = None
        parent_combined_hash = None
        status = "APPROVED_FROZEN_BY_OWNER"
    else:
        if parent_payload is None:
            raise ValueError(f"L{depth:02d} transfer requires parent L{depth - 1:02d} payload")
        if int(parent_payload["depth"]) != depth - 1:
            raise ValueError(f"Parent depth mismatch for L{depth:02d}")
        inherited_locked_nodes = parent_payload["combined_nodes"]
        parent_json_path, _ = artifact_paths(depth - 1)
        parent_artifact = relative(parent_json_path)
        parent_artifact_hash = parent_payload["artifact_hash"]
        parent_combined_hash = parent_payload["combined_hash"]
        status = "DRAFT_STRUCTURE_ONLY"

    combined_nodes = sort_nodes([*inherited_locked_nodes, *own_expansion])
    own_node_ids = {node["node_id"] for node in own_expansion}
    inherited_node_ids = {node["node_id"] for node in inherited_locked_nodes}
    if inherited_node_ids & own_node_ids:
        overlap = sorted(inherited_node_ids & own_node_ids)[:5]
        raise ValueError(f"L{depth:02d} own expansion overlaps inherited nodes: {overlap}")
    inherited_lookup = set(inherited_node_ids)
    for node in own_expansion:
        if node["parent_id"] is not None and node["parent_id"] not in inherited_lookup:
            raise ValueError(f"L{depth:02d} node {node['node_id']} has missing parent {node['parent_id']}")
        if unsafe_reader_title(str(node["title"])):
            raise ValueError(f"L{depth:02d} unsafe title in {node['node_id']}: {node['title']}")

    json_path, md_path = artifact_paths(depth)
    payload: dict[str, Any] = {
        "artifact_kind": "MASTER_MANUSCRIPT_LEVEL_STRUCTURE",
        "body_prose_included": False,
        "combined_hash": nodes_hash(combined_nodes),
        "combined_nodes": combined_nodes,
        "depth": depth,
        "depth_label": f"L{depth:02d}",
        "depth_semantics": {str(key): value for key, value in LEVEL_NAMES.items()},
        "inherited_locked_hash": nodes_hash(inherited_locked_nodes),
        "inherited_locked_nodes": inherited_locked_nodes,
        "node_counts": {
            "combined": len(combined_nodes),
            "inherited_locked": len(inherited_locked_nodes),
            "own_expansion": len(own_expansion),
        },
        "own_expansion_hash": nodes_hash(own_expansion),
        "own_expansion_nodes": own_expansion,
        "parent_artifact": parent_artifact,
        "parent_artifact_hash": parent_artifact_hash,
        "parent_combined_hash": parent_combined_hash,
        "release_id": RELEASE_ID,
        "status": status,
        "structure_scope": f"L01-L{depth:02d}" if depth > 1 else "L01",
        "version": VERSION,
        "written_artifacts": {"json": relative(json_path), "markdown": relative(md_path)},
    }
    payload["artifact_hash"] = sha256_text(stable_json(payload_without_hash(payload)))
    return payload


def validate_level_payload(payload: dict[str, Any], parent_payload: dict[str, Any] | None = None) -> list[str]:
    failures: list[str] = []
    depth = int(payload["depth"])
    if depth == 1:
        if payload["node_counts"]["own_expansion"] != EXPECTED_L1_TOTAL:
            failures.append("l1_total_mismatch")
        if payload["inherited_locked_nodes"]:
            failures.append("l1_has_inherited_nodes")
        if payload["status"] != "APPROVED_FROZEN_BY_OWNER":
            failures.append("l1_status_not_approved_frozen")
    else:
        if parent_payload is None:
            failures.append("missing_parent_payload")
        else:
            if payload["inherited_locked_nodes"] != parent_payload["combined_nodes"]:
                failures.append("inherited_locked_nodes_not_equal_parent_combined_nodes")
            if payload["parent_artifact_hash"] != parent_payload["artifact_hash"]:
                failures.append("parent_artifact_hash_mismatch")
            if payload["parent_combined_hash"] != parent_payload["combined_hash"]:
                failures.append("parent_combined_hash_mismatch")
        if payload["status"] != "DRAFT_STRUCTURE_ONLY":
            failures.append("draft_status_mismatch")
    if depth == 2 and payload["node_counts"]["own_expansion"] != EXPECTED_L2_TOTAL:
        failures.append("l2_total_mismatch")
    for node in payload["own_expansion_nodes"]:
        if int(node["level"]) != depth:
            failures.append(f"own_expansion_wrong_level::{node['node_id']}")
        if unsafe_reader_title(str(node["title"])):
            failures.append(f"unsafe_reader_title::{node['node_id']}")
    return failures


def render_node_list(nodes: list[dict[str, Any]], *, root_indent: int = 0) -> list[str]:
    lines: list[str] = []
    for node in sort_nodes(nodes):
        indent = "  " * max(0, int(node["level"]) - 1 + root_indent)
        status = str(node["status"])
        if status == "APPROVED_FROZEN_BY_OWNER":
            suffix = " [APPROVED_FROZEN]"
        elif status == "DRAFT_SLOT":
            suffix = " [DRAFT_SLOT]"
        else:
            suffix = " [DRAFT]"
        lines.append(f"{indent}- {node['outline_number']} {node['title']}{suffix}")
    return lines


def render_level_markdown(payload: dict[str, Any]) -> str:
    depth = int(payload["depth"])
    lines = [
        f"# OC Core 1.3.3 Master Manuscript Structure {payload['structure_scope']}",
        "",
        f"Status: {payload['status']}",
        f"Version: {payload['version']}",
        f"Depth: {payload['depth_label']}",
        f"Artifact hash: `{payload['artifact_hash']}`",
        f"Parent artifact hash: `{payload['parent_artifact_hash'] or 'NONE'}`",
        f"Parent combined hash: `{payload['parent_combined_hash'] or 'NONE'}`",
        f"Inherited locked hash: `{payload['inherited_locked_hash']}`",
        f"Own expansion hash: `{payload['own_expansion_hash']}`",
        f"Combined hash: `{payload['combined_hash']}`",
        "",
        "Structure-only artifact. It contains headings, draft slots, hashes, and provenance only.",
        "",
        "## Level Semantics",
        "",
    ]
    for level in range(1, depth + 1):
        lines.append(f"- L{level:02d}: {LEVEL_NAMES[level]}")
    lines.extend(["", "## Inherited Locked Structure", ""])
    if payload["inherited_locked_nodes"]:
        lines.extend(render_node_list(payload["inherited_locked_nodes"]))
    else:
        lines.append("None.")
    lines.extend(["", "## Own Draft Expansion", ""])
    lines.extend(render_node_list(payload["own_expansion_nodes"]))
    lines.extend(["", "## Combined Outline", ""])
    lines.extend(render_node_list(payload["combined_nodes"]))
    return "\n".join(lines) + "\n"


def read_payload(depth: int) -> dict[str, Any]:
    json_path, _ = artifact_paths(depth)
    if not json_path.exists():
        raise FileNotFoundError(json_path)
    return json.loads(json_path.read_text(encoding="utf-8"))


def expected_level_files(depth: int, parent_payload: dict[str, Any] | None = None) -> dict[Path, str]:
    payload = build_level_payload(depth, parent_payload)
    failures = validate_level_payload(payload, parent_payload)
    if failures:
        raise RuntimeError(f"L{depth:02d} payload validation failed: {failures}")
    json_path, md_path = artifact_paths(depth)
    return {json_path: stable_json(payload), md_path: render_level_markdown(payload)}


def check_files(files: dict[Path, str]) -> dict[str, Any]:
    missing: list[str] = []
    changed: list[str] = []
    for path, text in files.items():
        rel = relative(path)
        if not path.exists():
            missing.append(rel)
            continue
        if path.read_text(encoding="utf-8", errors="replace") != text:
            changed.append(rel)
    return {"changed": changed, "missing": missing, "state": "PASS" if not missing and not changed else "FAIL"}


def write_files(files: dict[Path, str]) -> list[str]:
    changed: list[str] = []
    for path, text in files.items():
        if write_text_if_changed(path, text):
            changed.append(relative(path))
    return changed


def run_l1(write: bool) -> dict[str, Any]:
    files = expected_level_files(1, None)
    if write:
        result = {"changed": write_files(files), "missing": [], "state": "PASS"}
    else:
        result = check_files(files)
    result["depth"] = 1
    result["script_role"] = "l1_base"
    return result


def run_transfer(depth: int, write: bool) -> dict[str, Any]:
    if depth < 2 or depth > MAX_DEPTH:
        raise ValueError(f"Transfer depth out of range: {depth}")
    parent_payload = read_payload(depth - 1)
    files = expected_level_files(depth, parent_payload)
    if write:
        result = {"changed": write_files(files), "missing": [], "state": "PASS"}
    else:
        result = check_files(files)
    result["depth"] = depth
    result["script_role"] = f"transfer_l{depth - 1:02d}_to_l{depth:02d}"
    return result


def all_payloads_from_disk() -> list[dict[str, Any]]:
    return [read_payload(depth) for depth in range(1, MAX_DEPTH + 1)]


def build_index_payload(payloads: list[dict[str, Any]]) -> dict[str, Any]:
    entries = []
    for payload in payloads:
        entries.append(
            {
                "artifact_hash": payload["artifact_hash"],
                "combined_hash": payload["combined_hash"],
                "depth": payload["depth"],
                "inherited_locked_hash": payload["inherited_locked_hash"],
                "node_counts": payload["node_counts"],
                "own_expansion_hash": payload["own_expansion_hash"],
                "parent_artifact_hash": payload["parent_artifact_hash"],
                "paths": payload["written_artifacts"],
                "status": payload["status"],
                "structure_scope": payload["structure_scope"],
            }
        )
    index_payload = {
        "artifact_kind": "MASTER_MANUSCRIPT_STRUCTURE_CASCADE_INDEX",
        "body_prose_included": False,
        "cascade_depth_total": MAX_DEPTH,
        "entries": entries,
        "release_id": RELEASE_ID,
        "structure_policy": {
            "l1_status": "APPROVED_FROZEN_BY_OWNER",
            "l2_to_l10_status": "DRAFT_STRUCTURE_ONLY",
            "lower_levels_must_preserve_inherited_locked_nodes": True,
            "lower_levels_split_inherited_and_own_expansion": True,
        },
        "version": VERSION,
    }
    index_payload["artifact_hash"] = sha256_text(stable_json(index_payload))
    return index_payload


def render_index_markdown(index_payload: dict[str, Any]) -> str:
    lines = [
        "# OC Core 1.3.3 Master Manuscript Structure Cascade Index",
        "",
        f"Version: {index_payload['version']}",
        f"Artifact hash: `{index_payload['artifact_hash']}`",
        "",
        "This index records the separate L1-L10 structure documents.",
        "Each lower level has a locked inherited part and its own draft expansion.",
        "",
        "## Artifacts",
        "",
        "| Scope | Status | Inherited | Own | Combined | Parent artifact hash | Artifact hash |",
        "| --- | --- | ---: | ---: | ---: | --- | --- |",
    ]
    for entry in index_payload["entries"]:
        counts = entry["node_counts"]
        lines.append(
            f"| {entry['structure_scope']} | {entry['status']} | {counts['inherited_locked']} | "
            f"{counts['own_expansion']} | {counts['combined']} | "
            f"`{entry['parent_artifact_hash'] or 'NONE'}` | `{entry['artifact_hash']}` |"
        )
    return "\n".join(lines) + "\n"


def expected_index_files() -> dict[Path, str]:
    payloads = all_payloads_from_disk()
    failures = validate_cascade_payloads(payloads)
    if failures:
        raise RuntimeError(f"Cascade validation failed before index build: {failures}")
    index_payload = build_index_payload(payloads)
    json_path, md_path = index_paths()
    return {json_path: stable_json(index_payload), md_path: render_index_markdown(index_payload)}


def validate_cascade_payloads(payloads: list[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    if len(payloads) != MAX_DEPTH:
        failures.append("depth_total_mismatch")
        return failures
    for expected_depth, payload in enumerate(payloads, start=1):
        if int(payload["depth"]) != expected_depth:
            failures.append(f"depth_order_mismatch::{expected_depth}")
        parent = payloads[expected_depth - 2] if expected_depth > 1 else None
        failures.extend(f"L{expected_depth:02d}::{failure}" for failure in validate_level_payload(payload, parent))
    if payloads[0]["node_counts"]["own_expansion"] != EXPECTED_L1_TOTAL:
        failures.append("l1_total_mismatch")
    if payloads[1]["node_counts"]["own_expansion"] != EXPECTED_L2_TOTAL:
        failures.append("l2_total_mismatch")
    l3_total = payloads[2]["node_counts"]["own_expansion"]
    if payloads[9]["node_counts"]["own_expansion"] != l3_total:
        failures.append("l10_paragraph_slot_total_mismatch")
    return failures


def run_index(write: bool) -> dict[str, Any]:
    files = expected_index_files()
    if write:
        result = {"changed": write_files(files), "missing": [], "state": "PASS"}
    else:
        result = check_files(files)
    result["script_role"] = "cascade_index"
    return result


def run_transfer_cli(depth: int, argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=f"Transfer OC133 manuscript structure L{depth - 1:02d} to L{depth:02d}.")
    parser.add_argument("--write", action="store_true", help="Write this transfer output if changed.")
    parser.add_argument("--check", action="store_true", help="Check this transfer output without writing.")
    args = parser.parse_args(argv)
    if not args.write and not args.check:
        args.check = True
    result = run_transfer(depth, write=args.write)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["state"] == "PASS" else 1


def main_l1(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build/check OC133 manuscript structure L01 base.")
    parser.add_argument("--write", action="store_true", help="Write L01 output if changed.")
    parser.add_argument("--check", action="store_true", help="Check L01 output without writing.")
    args = parser.parse_args(argv)
    if not args.write and not args.check:
        args.check = True
    result = run_l1(write=args.write)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["state"] == "PASS" else 1
