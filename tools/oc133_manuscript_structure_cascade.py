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
                    "path": str(path.relative_to(ROOT)).replace("\\", "/"),
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
                    "path": str(path.relative_to(ROOT)).replace("\\", "/"),
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
    scored: list[tuple[int, str, dict[str, Any]]] = []
    if not chapter_tokens:
        return []
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
                "node_id": node.get("node_id"),
                "title": title,
                "role": node.get("role"),
                "score": score,
                "path": first.get("path"),
                "commit": first.get("commit"),
                "line": first.get("line"),
            }
        )
        if len(candidates) == 3:
            break
    return candidates


def build_nodes() -> list[OutlineNode]:
    l1_items, l2_items = parse_l1_l2_source()
    if len(l1_items) != EXPECTED_L1_TOTAL:
        raise ValueError(f"Expected {EXPECTED_L1_TOTAL} L1 blocks, found {len(l1_items)}")
    if len(l2_items) != EXPECTED_L2_TOTAL:
        raise ValueError(f"Expected {EXPECTED_L2_TOTAL} L2 chapters, found {len(l2_items)}")

    recovered_nodes = load_recovered_nodes()
    nodes: list[OutlineNode] = []
    l1_by_index = {item["index"]: item for item in l1_items}
    l2_by_parent: dict[int, list[dict[str, Any]]] = {}
    for item in l2_items:
        l2_by_parent.setdefault(item["parent_index"], []).append(item)

    for l1 in l1_items:
        path = [l1["index"]]
        l1_id = node_id(1, path)
        nodes.append(
            OutlineNode(
                node_id=l1_id,
                parent_id=None,
                level=1,
                order_path=path,
                outline_number=outline_number(path),
                title=l1["title"],
                level_name=LEVEL_NAMES[1],
                status="APPROVED_FROZEN_BY_OWNER",
                source="owner_approved_l1_structure",
                provenance=[
                    {
                        "kind": "owner_approved_l1",
                        "path": l1["path"],
                        "line": l1["line"],
                    }
                ],
            )
        )

    for l2 in l2_items:
        l1 = l1_by_index[l2["parent_index"]]
        path2 = [l2["parent_index"], l2["index"]]
        l1_id = node_id(1, [l2["parent_index"]])
        l2_id = node_id(2, path2)
        chapter_provenance = [
            {
                "kind": "owner_approved_l2_source",
                "path": l2["path"],
                "line": l2["line"],
            }
        ]
        nodes.append(
            OutlineNode(
                node_id=l2_id,
                parent_id=l1_id,
                level=2,
                order_path=path2,
                outline_number=outline_number(path2),
                title=l2["title"],
                level_name=LEVEL_NAMES[2],
                status="DRAFT_STRUCTURE_ONLY",
                source="owner_approved_l2_source_demoted_to_draft_cascade",
                provenance=chapter_provenance,
            )
        )
        candidates = provenance_candidates(l2["title"], l1["title"], recovered_nodes)
        for l3_index, (title, source_key) in enumerate(L3_TEMPLATES, start=1):
            path3 = [*path2, l3_index]
            l3_id = node_id(3, path3)
            nodes.append(
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
                        {
                            "kind": "template",
                            "template": source_key,
                            "chapter": l2["title"],
                        },
                        {
                            "kind": "recovered_corpus_candidates",
                            "candidates": candidates,
                        },
                    ],
                )
            )
            parent_id = l3_id
            parent_path = path3
            for level in range(4, MAX_DEPTH + 1):
                current_path = [*parent_path, 1]
                current_id = node_id(level, current_path)
                nodes.append(
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
                        provenance=[
                            {
                                "kind": "template",
                                "parent_level": level - 1,
                                "parent_node_id": parent_id,
                            }
                        ],
                    )
                )
                parent_id = current_id
                parent_path = current_path
    return sorted(nodes, key=lambda node: node.order_path)


def nodes_for_depth(nodes: list[OutlineNode], depth: int) -> list[dict[str, Any]]:
    return [node.to_json() for node in nodes if node.level <= depth]


def nodes_hash(nodes: list[dict[str, Any]]) -> str:
    return sha256_text(stable_json(nodes))


def build_depth_payload(
    *,
    depth: int,
    nodes: list[OutlineNode],
    parent_payload: dict[str, Any] | None,
    parent_hash: str | None,
) -> tuple[dict[str, Any], str]:
    depth_nodes = nodes_for_depth(nodes, depth)
    level_counts: dict[str, int] = {}
    for node in depth_nodes:
        level_counts[str(node["level"])] = level_counts.get(str(node["level"]), 0) + 1
    parent_node_hash = nodes_hash(parent_payload["nodes"]) if parent_payload else None
    inherited_node_prefix_ok = True
    if parent_payload:
        inherited_node_prefix_ok = parent_payload["nodes"] == depth_nodes[: len(parent_payload["nodes"])]
    payload: dict[str, Any] = {
        "artifact_kind": "MASTER_MANUSCRIPT_CASCADE_STRUCTURE",
        "body_prose_included": False,
        "cascade_depth": depth,
        "cascade_depth_label": f"L01-L{depth:02d}" if depth > 1 else "L01",
        "children_beyond_depth_included": False,
        "depth_semantics": LEVEL_NAMES,
        "inherited_node_prefix_ok": inherited_node_prefix_ok,
        "level_counts": level_counts,
        "max_level_included": depth,
        "node_hash": nodes_hash(depth_nodes),
        "node_total": len(depth_nodes),
        "nodes": depth_nodes,
        "owner_approval_required_for_l1_mutation": True,
        "parent_artifact": None,
        "parent_hash": parent_hash,
        "parent_node_hash": parent_node_hash,
        "release_id": RELEASE_ID,
        "release_payload_included": False,
        "status": "APPROVED_FROZEN_BY_OWNER" if depth == 1 else "DRAFT_STRUCTURE_ONLY",
        "version": VERSION,
    }
    artifact_hash = sha256_text(stable_json({k: v for k, v in payload.items() if k != "artifact_hash"}))
    payload["artifact_hash"] = artifact_hash
    return payload, artifact_hash


def render_md(payload: dict[str, Any]) -> str:
    depth = int(payload["cascade_depth"])
    lines = [
        f"# OC Core 1.3.3 Master Manuscript Structure {payload['cascade_depth_label']}",
        "",
        f"Status: {payload['status']}",
        f"Version: {payload['version']}",
        f"Depth: {payload['cascade_depth_label']}",
        f"Artifact hash: `{payload['artifact_hash']}`",
        f"Parent hash: `{payload['parent_hash'] or 'NONE'}`",
        "",
        "This is a structure-only cascade artifact. It contains headings, draft slots,",
        "inheritance metadata, and provenance references only. It does not contain",
        "manuscript body text or public package material.",
        "",
        "## Level Semantics",
        "",
    ]
    for level in range(1, depth + 1):
        lines.append(f"- L{level:02d}: {LEVEL_NAMES[level]}")
    lines.extend(["", "## Outline", ""])
    for node in payload["nodes"]:
        indent = "  " * (int(node["level"]) - 1)
        status_suffix = ""
        if node["status"] == "DRAFT_SLOT":
            status_suffix = " [DRAFT_SLOT]"
        elif node["status"] == "DRAFT_STRUCTURE_ONLY":
            status_suffix = " [DRAFT]"
        elif node["status"] == "APPROVED_FROZEN_BY_OWNER":
            status_suffix = " [APPROVED_FROZEN]"
        lines.append(f"{indent}- {node['outline_number']} {node['title']}{status_suffix}")
    return "\n".join(lines) + "\n"


def artifact_paths(depth: int) -> tuple[Path, Path]:
    stem = f"MASTER_MANUSCRIPT_STRUCTURE_L{depth:02d}_1_3_3"
    return STRUCTURE_DIR / f"{stem}.json", STRUCTURE_DIR / f"{stem}.md"


def build_all_payloads() -> tuple[dict[int, dict[str, Any]], dict[str, Any], dict[str, str]]:
    nodes = build_nodes()
    payloads: dict[int, dict[str, Any]] = {}
    artifact_hashes: dict[str, str] = {}
    parent_payload: dict[str, Any] | None = None
    parent_hash: str | None = None
    for depth in range(1, MAX_DEPTH + 1):
        payload, artifact_hash = build_depth_payload(
            depth=depth,
            nodes=nodes,
            parent_payload=parent_payload,
            parent_hash=parent_hash,
        )
        json_path, md_path = artifact_paths(depth)
        payload["artifact_paths"] = {
            "json": str(json_path.relative_to(ROOT)).replace("\\", "/"),
            "markdown": str(md_path.relative_to(ROOT)).replace("\\", "/"),
        }
        if depth > 1:
            parent_json_path, _ = artifact_paths(depth - 1)
            payload["parent_artifact"] = str(parent_json_path.relative_to(ROOT)).replace("\\", "/")
            payload["artifact_hash"] = sha256_text(stable_json({k: v for k, v in payload.items() if k != "artifact_hash"}))
        payloads[depth] = payload
        artifact_hashes[f"L{depth:02d}"] = payload["artifact_hash"]
        parent_payload = payload
        parent_hash = payload["artifact_hash"]

    index_entries: list[dict[str, Any]] = []
    for depth, payload in payloads.items():
        index_entries.append(
            {
                "artifact_hash": payload["artifact_hash"],
                "depth": depth,
                "level_label": payload["cascade_depth_label"],
                "level_counts": payload["level_counts"],
                "node_total": payload["node_total"],
                "parent_hash": payload["parent_hash"],
                "paths": payload["artifact_paths"],
                "status": payload["status"],
            }
        )
    index_payload = {
        "artifact_kind": "MASTER_MANUSCRIPT_STRUCTURE_CASCADE_INDEX",
        "body_prose_included": False,
        "cascade_depth_total": MAX_DEPTH,
        "entries": index_entries,
        "release_id": RELEASE_ID,
        "release_payload_included": False,
        "structure_policy": {
            "l1_status": "APPROVED_FROZEN_BY_OWNER",
            "l2_to_l10_status": "DRAFT_STRUCTURE_ONLY",
            "deeper_levels_inherit_parent_nodes": True,
            "l1_owner_override_required_for_mutation": True,
        },
        "version": VERSION,
    }
    index_payload["artifact_hash"] = sha256_text(stable_json(index_payload))
    return payloads, index_payload, artifact_hashes


def render_index_md(index_payload: dict[str, Any]) -> str:
    lines = [
        "# OC Core 1.3.3 Master Manuscript Structure Cascade Index",
        "",
        f"Version: {index_payload['version']}",
        f"Artifact hash: `{index_payload['artifact_hash']}`",
        "",
        "This index records the L1-L10 structure-only cascade. L1 is approved and",
        "frozen by owner instruction. L2-L10 are draft structures.",
        "",
        "## Artifacts",
        "",
        "| Depth | Status | Nodes | Parent hash | Artifact hash |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for entry in index_payload["entries"]:
        lines.append(
            f"| {entry['level_label']} | {entry['status']} | {entry['node_total']} | "
            f"`{entry['parent_hash'] or 'NONE'}` | `{entry['artifact_hash']}` |"
        )
    return "\n".join(lines) + "\n"


def validate_payloads(payloads: dict[int, dict[str, Any]], index_payload: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    if payloads[1]["level_counts"].get("1") != EXPECTED_L1_TOTAL:
        failures.append("l1_total_mismatch")
    if payloads[2]["level_counts"].get("2") != EXPECTED_L2_TOTAL:
        failures.append("l2_total_mismatch")
    if payloads[1]["status"] != "APPROVED_FROZEN_BY_OWNER":
        failures.append("l1_status_not_approved_frozen")
    for depth in range(2, MAX_DEPTH + 1):
        if payloads[depth]["status"] != "DRAFT_STRUCTURE_ONLY":
            failures.append(f"depth_{depth}_status_not_draft")
        parent_nodes = payloads[depth - 1]["nodes"]
        current_parent_projection = [node for node in payloads[depth]["nodes"] if node["level"] <= depth - 1]
        if current_parent_projection != parent_nodes:
            failures.append(f"depth_{depth}_parent_nodes_not_byte_identical")
        if payloads[depth]["parent_hash"] != payloads[depth - 1]["artifact_hash"]:
            failures.append(f"depth_{depth}_parent_hash_mismatch")
    l10_nodes = [node for node in payloads[MAX_DEPTH]["nodes"] if node["level"] == 10]
    l3_nodes = [node for node in payloads[MAX_DEPTH]["nodes"] if node["level"] == 3]
    if len(l10_nodes) != len(l3_nodes):
        failures.append("l10_paragraph_slot_total_mismatch")
    for payload in payloads.values():
        for node in payload["nodes"]:
            if unsafe_reader_title(str(node["title"])):
                failures.append(f"unsafe_reader_title::{node['node_id']}")
    if len(index_payload["entries"]) != MAX_DEPTH:
        failures.append("index_depth_total_mismatch")
    return {
        "state": "PASS" if not failures else "FAIL",
        "failures": failures,
        "l1_total": payloads[1]["level_counts"].get("1"),
        "l2_total": payloads[2]["level_counts"].get("2"),
        "l10_paragraph_slot_total": len(l10_nodes),
    }


def expected_files() -> dict[Path, str]:
    payloads, index_payload, _ = build_all_payloads()
    validation = validate_payloads(payloads, index_payload)
    if validation["state"] != "PASS":
        raise RuntimeError(f"Generated cascade failed validation: {validation}")
    files: dict[Path, str] = {}
    for depth, payload in payloads.items():
        json_path, md_path = artifact_paths(depth)
        files[json_path] = stable_json(payload)
        files[md_path] = render_md(payload)
    index_json = STRUCTURE_DIR / "MASTER_MANUSCRIPT_STRUCTURE_CASCADE_INDEX_1_3_3.json"
    index_md = STRUCTURE_DIR / "MASTER_MANUSCRIPT_STRUCTURE_CASCADE_INDEX_1_3_3.md"
    files[index_json] = stable_json(index_payload)
    files[index_md] = render_index_md(index_payload)
    return files


def check_existing(files: dict[Path, str]) -> dict[str, Any]:
    missing: list[str] = []
    changed: list[str] = []
    for path, text in files.items():
        rel = str(path.relative_to(ROOT)).replace("\\", "/")
        if not path.exists():
            missing.append(rel)
            continue
        if path.read_text(encoding="utf-8", errors="replace") != text:
            changed.append(rel)
    return {
        "state": "PASS" if not missing and not changed else "FAIL",
        "missing": missing,
        "changed": changed,
        "file_total": len(files),
    }


def write_files(files: dict[Path, str]) -> list[str]:
    changed: list[str] = []
    for path, text in files.items():
        if write_text_if_changed(path, text):
            changed.append(str(path.relative_to(ROOT)).replace("\\", "/"))
    return changed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build/check OC Core 1.3.3 L1-L10 manuscript structure cascade.")
    parser.add_argument("--write", action="store_true", help="Write generated cascade artifacts.")
    parser.add_argument("--check", action="store_true", help="Check generated cascade artifacts without writing.")
    args = parser.parse_args(argv)
    if not args.write and not args.check:
        args.check = True

    files = expected_files()
    if args.write:
        changed = write_files(files)
        result = {"state": "PASS", "changed": changed, "file_total": len(files)}
    else:
        result = check_existing(files)
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0 if result["state"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
