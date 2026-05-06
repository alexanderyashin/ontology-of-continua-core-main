from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
TOOLS_DIR = ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from oc_core_release_assembly_lib import artifact_hash, stable_json, validation_result

import oc133_toe_closure_factory as factory


SUPERVISOR_DIR = factory.FACTORY_DIR / "autonomous_supervisor"
STATE_NAME = "OC133_TOE_AUTONOMOUS_SUPERVISOR_STATE.json"
COCKPIT_NAME = "OC133_TOE_AUTONOMOUS_COCKPIT.json"
WAVE_LEDGER_NAME = "OC133_TOE_AUTONOMOUS_WAVE_LEDGER.json"
NEXT_ACTION_QUEUE_NAME = "OC133_TOE_AUTONOMOUS_NEXT_ACTION_QUEUE.json"
ESCALATION_LEDGER_NAME = "OC133_TOE_AUTONOMOUS_CAPABILITY_ESCALATION_LEDGER.json"
CAPABILITY_DEVELOPMENT_LEDGER_NAME = "OC133_TOE_AUTONOMOUS_CAPABILITY_DEVELOPMENT_LEDGER.json"
FRONTIER_HASHES_NAME = "OC133_TOE_AUTONOMOUS_FRONTIER_HASHES.json"
COMMIT_LEDGER_NAME = "OC133_TOE_AUTONOMOUS_COMMIT_LEDGER.json"
TERMINAL_VALIDATION_NAME = "OC133_TOE_AUTONOMOUS_TERMINAL_VALIDATION_REPORT.json"
HEARTBEAT_NAME = "OC133_TOE_AUTONOMOUS_HEARTBEAT.json"
BLOCKING_GRAPH_NAME = "OC133_TOE_BLOCKING_GRAPH.json"
SUPPORT_INDEX_NAME = "OC133_TOE_SUPPORT_REFERENCE_INDEX.json"

VOLATILE_KEYS = {
    "artifact_hash",
    "generated_at",
    "ts_utc",
    "stdout_tail",
    "stderr_tail",
    "commit_sha",
    "frontier_hash_before",
    "frontier_hash_after",
}

ALLOWED_DIRTY_PREFIXES = (
    "operations/logion_release_mission/oc_core_1_3_3/OC133_ALL_DOMAIN_READINESS_COCKPIT.md",
    "operations/logion_release_mission/oc_core_1_3_3/OC133_ALL_DOMAIN_READINESS_SCORECARD.json",
    "operations/logion_release_mission/oc_core_1_3_3/OC133_ALL_DOMAIN_WORK_ORDERS.json",
    "operations/logion_release_mission/oc_core_1_3_3/OC133_GRAND_SCIENCE_LOOP_latest.json",
    "operations/logion_release_mission/oc_core_1_3_3/OC133_GRAND_SCIENCE_LOOP_latest.md",
    "operations/logion_release_mission/oc_core_1_3_3/OC133_GRAND_SCIENCE_LOOP_STATE.json",
    "operations/logion_release_mission/oc_core_1_3_3/toe_closure_factory/",
    "benchmarks/modern_science/",
    "comparators/modern_science/",
    "content/generated/",
    "releases/oc_core_1_3/editorial/",
    "releases/oc_core_1_3/monograph/source/content/generated/",
    "validation/heldout/grand_science/",
    "tools/oc133_toe_autonomous_supervisor.py",
    "tools/oc133_toe_closure_factory.py",
    "release_machine/tests/test_release_assembly_machine.py",
)
IGNORED_STATUS_PREFIXES = ("?? _codex_r009_run/", "?? _codex_r010_run/")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def write_json(root: Path, rel_path: Path, payload: dict[str, Any]) -> str:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stable_json(payload), encoding="utf-8")
    return rel_path.as_posix()


def strip_volatile(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: strip_volatile(item)
            for key, item in sorted(value.items())
            if key not in VOLATILE_KEYS
        }
    if isinstance(value, list):
        return [strip_volatile(item) for item in value]
    return value


def git_status_rows(root: Path) -> list[str]:
    completed = subprocess.run(
        ["git", "status", "--short"],
        cwd=root,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=60,
    )
    if completed.returncode != 0:
        return []
    return sorted(line.strip() for line in completed.stdout.splitlines() if line.strip())


def normalized_status_path(row: str) -> str:
    parts = row.split(maxsplit=1)
    return parts[1].strip() if len(parts) == 2 else row


def worktree_gate(root: Path) -> dict[str, Any]:
    rows = git_status_rows(root)
    unexpected = []
    allowed = []
    ignored = []
    for row in rows:
        if row.startswith(IGNORED_STATUS_PREFIXES):
            ignored.append(row)
            continue
        path = normalized_status_path(row).replace("\\", "/")
        if path.startswith(ALLOWED_DIRTY_PREFIXES):
            allowed.append(row)
        else:
            unexpected.append(row)
    return {
        "status": "PASS" if not unexpected else "FAIL",
        "unexpected_dirty_total": len(unexpected),
        "unexpected_dirty_rows": unexpected,
        "allowed_dirty_total": len(allowed),
        "ignored_dirty_total": len(ignored),
        "allowed_dirty_prefixes": list(ALLOWED_DIRTY_PREFIXES),
        "ignored_status_prefixes": list(IGNORED_STATUS_PREFIXES),
    }


def semantic_payload(root: Path, rel_path: str | Path) -> Any:
    path = root / rel_path
    if path.is_dir():
        rows = []
        for child in sorted(path.rglob("*")):
            if child.is_file():
                rows.append(
                    {
                        "ref": child.relative_to(root).as_posix(),
                        "payload": semantic_payload(root, child.relative_to(root)),
                    }
                )
        return rows
    if not path.exists():
        return {"missing": True}
    if path.suffix.lower() == ".json":
        return strip_volatile(read_json(path))
    return {"text_hash": artifact_hash({"text": path.read_text(encoding="utf-8", errors="replace")})}


def semantic_frontier_hash(root: Path) -> str:
    refs = [
        "releases/oc_core_1_3/editorial/science_sources/toe_projection_lanes/ai.json",
        "releases/oc_core_1_3/editorial/science_sources/toe_projection_lanes/enterprise_architecture.json",
        factory.GRAND_SCORECARD,
        factory.GRAND_PROMOTION_REPORT,
        factory.COMPARATOR_REGISTER,
        factory.FINITE_CHECK_REPORT,
        factory.CERBERUS_ACCEPTANCE,
        factory.CERBERUS_FINDINGS,
    ]
    return artifact_hash(
        {
            "validator_parts": factory.current_validator_error_parts(root),
            "frontier_policy": "Scientific frontier excludes supervisor bookkeeping, blocking-graph, capability-backlog, and diagnostic artifacts so zero-delta waves cannot masquerade as progress.",
            "refs": {str(ref).replace("\\", "/"): semantic_payload(root, ref) for ref in refs},
        }
    )


def iter_json_files(root: Path) -> list[Path]:
    roots = [
        "claims",
        "proofs",
        "reports",
        "comparators",
        "benchmarks",
        "releases/oc_core_1_3/editorial/science_sources",
        "operations/logion_release_mission/oc_core_1_3_3/toe_closure_factory",
    ]
    files: list[Path] = []
    for rel_root in roots:
        base = root / rel_root
        if not base.exists():
            continue
        files.extend(path for path in base.rglob("*.json") if path.is_file())
    return sorted(set(files))


def collect_string_values(value: Any) -> list[str]:
    if isinstance(value, dict):
        rows: list[str] = []
        for item in value.values():
            rows.extend(collect_string_values(item))
        return rows
    if isinstance(value, list):
        rows = []
        for item in value:
            rows.extend(collect_string_values(item))
        return rows
    return [value] if isinstance(value, str) else []


def build_support_reference_index(root: Path, generated_at: str | None = None) -> dict[str, Any]:
    lean_path = root / "formal/lean/OC133V12.lean"
    lean_symbols = sorted(factory.declared_symbols(lean_path))
    finite_rows = factory.finite_case_rows_by_id(root)
    passing_finite = sorted(case_id for case_id, row in finite_rows.items() if row.get("passed") is True)
    json_files = iter_json_files(root)
    lean_ref_rows: dict[str, dict[str, Any]] = {}
    finite_ref_rows: dict[str, dict[str, Any]] = {}
    source_ref_rows: dict[str, dict[str, Any]] = {}
    for path in json_files:
        rel_path = path.relative_to(root).as_posix()
        payload = read_json(path)
        for text in collect_string_values(payload):
            if text.startswith("formal/lean/") and "::" in text:
                lean_ref_rows.setdefault(
                    text,
                    {
                        "ref": text,
                        "bound": factory.lean_ref_bound(root, text),
                        "source_refs": [],
                    },
                )["source_refs"].append(rel_path)
            if text.startswith("FM-"):
                row = finite_rows.get(text)
                finite_ref_rows.setdefault(
                    text,
                    {
                        "case_id": text,
                        "exists": bool(row),
                        "passed": bool(row and row.get("passed") is True),
                        "source_refs": [],
                    },
                )["source_refs"].append(rel_path)
            if "/" in text and (text.endswith(".json") or text.endswith(".md") or text.endswith(".tex") or text.endswith(".lean")):
                ref_path = factory.split_ref_path(text)
                source_ref_rows.setdefault(
                    ref_path,
                    {
                        "ref": ref_path,
                        "exists": bool(ref_path) and (root / ref_path).exists(),
                        "source_refs": [],
                    },
                )["source_refs"].append(rel_path)
    payload = {
        "schema_id": "OC133_TOE_SUPPORT_REFERENCE_INDEX_v1",
        "generated_at": generated_at or utc_now(),
        "status": "PASS",
        "lean_source_ref": "formal/lean/OC133V12.lean",
        "lean_symbol_total": len(lean_symbols),
        "lean_symbols_sample": lean_symbols[:50],
        "indexed_lean_ref_total": len(lean_ref_rows),
        "bound_lean_ref_total": sum(1 for row in lean_ref_rows.values() if row["bound"]),
        "unbound_lean_ref_total": sum(1 for row in lean_ref_rows.values() if not row["bound"]),
        "finite_case_total": len(finite_rows),
        "passing_finite_case_total": len(passing_finite),
        "indexed_finite_ref_total": len(finite_ref_rows),
        "passing_indexed_finite_ref_total": sum(1 for row in finite_ref_rows.values() if row["passed"]),
        "source_ref_total": len(source_ref_rows),
        "existing_source_ref_total": sum(1 for row in source_ref_rows.values() if row["exists"]),
        "json_source_file_total": len(json_files),
        "rows": {
            "lean_refs": sorted(lean_ref_rows.values(), key=lambda row: row["ref"])[:500],
            "finite_refs": sorted(finite_ref_rows.values(), key=lambda row: row["case_id"])[:500],
            "source_refs": sorted(source_ref_rows.values(), key=lambda row: row["ref"])[:500],
        },
        "no_fake_closure_policy": "No fake closure: the index only records available support; lane writers still require validator-bound PASS predicates before promotion.",
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def graph_node(node_id: str, node_type: str, status: str, **kwargs: Any) -> dict[str, Any]:
    defaults = {
        "why_it_failed": "This node remains open because its validator-bound closure predicate is not satisfied.",
        "repair_strategy": "Resolve the lowest unresolved dependency, then rerun the strict TOE validator.",
        "required_capability": "Research/TOEClosureFactory",
        "execution_command": [],
        "pass_predicate": "The node's validator-bound predicate returns PASS.",
        "next_escalation": "Split this node into narrower source-bound capability work if it produces zero validator delta.",
        "validator_binding": "validate_oc_core_1_3_science_spot.py --require-final-toe-pass --require-cerberus-clean",
    }
    payload = {"node_id": node_id, "node_type": node_type, "status": status}
    payload.update(defaults)
    payload.update(kwargs)
    if status == "PASS":
        for key in ["why_it_failed", "next_escalation"]:
            payload[key] = payload.get(key) or "Already closed."
    return payload


def graph_edge(source: str, target: str, edge_type: str) -> dict[str, str]:
    return {"source": source, "target": target, "edge_type": edge_type}


def lane_for_error(error: str) -> str:
    lowered = error.lower()
    if "enterprise_architecture" in lowered or "enterprise architecture" in lowered:
        return "ENTERPRISE_ARCHITECTURE"
    if "ai lane" in lowered or "ai row" in lowered:
        return "AI"
    if "modern_science_comparator_superiority" in lowered:
        return "MODERN_SCIENCE_COMPARATOR_SUPERIORITY"
    if "grand_toe_claim_ledger_evidence" in lowered or "all_domain_ready_no_send" in lowered:
        return "GRAND_TOE_CLAIM_LEDGER_EVIDENCE"
    if "cerberus" in lowered:
        return "CERBERUS_RELEASE_REVIEW_GATE"
    return "TOE_CLOSURE_FACTORY"


def build_blocking_graph(
    root: Path,
    queue: dict[str, Any],
    support_index: dict[str, Any],
    generated_at: str | None = None,
    capability_development_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    parts = factory.current_validator_error_parts(root)
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, str]] = []
    gate_id = "promotion_gate:recovery_r017"
    nodes[gate_id] = graph_node(
        gate_id,
        "r017_promotion_gate",
        "PASS" if factory.validator_error_total(parts) == 0 else "OPEN",
        why_it_failed="Strict final TOE validator still reports open blockers.",
        repair_strategy="Close all science blockers, refresh Cerberus only after science PASS, then assemble r017.",
        required_capability="Research/TOEClosureFactory",
        execution_command=[sys.executable, "tools/validate_oc_core_1_3_science_spot.py", "--require-final-toe-pass", "--require-cerberus-clean"],
        pass_predicate="validator_error_total == 0",
        next_escalation="Continue resolving the lowest unresolved graph dependency; do not assemble r017.",
        validator_binding="strict_final_toe_validator",
    )
    for index, error in enumerate(parts["science_errors"] + parts["cerberus_errors"], start=1):
        lane_id = lane_for_error(error)
        error_id = f"validator_error:{index:03d}"
        nodes[error_id] = graph_node(
            error_id,
            "validator_error",
            "OPEN",
            symptom=error,
            lane_id=lane_id,
            why_it_failed=error,
            repair_strategy="Route this validator error to its owning lane and close the required support artifacts.",
            required_capability=factory.lane_registry_by_id().get(lane_id, {}).get("owner_capability", "Research/TOEClosureFactory"),
            execution_command=factory.lane_registry_by_id().get(lane_id, {}).get("execution_command", []),
            pass_predicate="This exact validator error disappears from the strict validator output.",
            validator_binding=f"strict_final_toe_validator::{lane_id}",
        )
        edges.append(graph_edge(error_id, gate_id, "blocks"))
        lane_node_id = f"lane:{lane_id}"
        if lane_node_id not in nodes:
            nodes[lane_node_id] = graph_node(
                lane_node_id,
                "closure_lane",
                "OPEN",
                lane_id=lane_id,
                why_it_failed=f"{lane_id} has one or more open validator errors.",
                repair_strategy="Close required artifacts and rerun the guarded lane writer.",
                required_capability=factory.lane_registry_by_id().get(lane_id, {}).get("owner_capability", "Research/TOEClosureFactory"),
                execution_command=factory.lane_registry_by_id().get(lane_id, {}).get("execution_command", []),
                pass_predicate=f"{lane_id} lane status == PASS and final_toe_support_allowed == true where applicable.",
                validator_binding=f"lane_result::{lane_id}",
            )
        edges.append(graph_edge(lane_node_id, error_id, "validated_by"))

    for action in queue.get("rows", []) or []:
        lane_id = str(action.get("lane_id") or "TOE_CLOSURE_FACTORY")
        lane_node_id = f"lane:{lane_id}"
        action_id = str(action.get("action_id") or artifact_hash(action)[:12])
        capability_id = f"capability:{action_id}"
        status = "OPEN" if action.get("execution_command") and not action.get("already_attempted_on_frontier") else str(action.get("status") or "OPEN")
        nodes[capability_id] = graph_node(
            capability_id,
            "executor_capability",
            status,
            lane_id=lane_id,
            executor_type=action.get("executor_type"),
            why_it_failed=action.get("why_it_failed"),
            repair_strategy=action.get("repair_strategy"),
            required_capability=action.get("required_capability"),
            execution_command=action.get("execution_command", []),
            pass_predicate=action.get("pass_predicate"),
            next_escalation=action.get("next_escalation"),
            validator_binding=f"action::{action_id}",
        )
        edges.append(graph_edge(capability_id, lane_node_id, "produces"))
        if action.get("required_artifact"):
            artifact_id = (
                f"required_artifact:{lane_id}:{action.get('gap_id')}:{action.get('required_artifact')}"
                if action.get("gap_id")
                else f"required_artifact:{lane_id}:{action.get('required_artifact')}"
            )
            nodes.setdefault(
                artifact_id,
                graph_node(
                    artifact_id,
                    "required_artifact",
                    "OPEN",
                    lane_id=lane_id,
                    gap_id=action.get("gap_id"),
                    artifact_key=action.get("required_artifact"),
                    why_it_failed=f"{lane_id} lacks required artifact `{action.get('required_artifact')}`.",
                    repair_strategy="Create or bind this artifact from canonical source/evidence surfaces.",
                    required_capability=action.get("required_capability"),
                    execution_command=action.get("execution_command", []),
                    pass_predicate=f"{action.get('required_artifact')} exists and passes lane static validation.",
                    validator_binding=f"support_artifact::{lane_id}::{action.get('required_artifact')}",
                ),
            )
            edges.append(graph_edge(lane_node_id, artifact_id, "requires"))
            edges.append(graph_edge(artifact_id, capability_id, "needs_capability"))
        for artifact_key in action.get("missing_artifacts") or []:
            artifact_id = f"required_artifact:{lane_id}:{action.get('gap_id')}:{artifact_key}"
            nodes.setdefault(
                artifact_id,
                graph_node(
                    artifact_id,
                    "required_artifact",
                    "OPEN",
                    lane_id=lane_id,
                    gap_id=action.get("gap_id"),
                    artifact_key=artifact_key,
                    why_it_failed=f"Comparator gap `{action.get('gap_id')}` lacks `{artifact_key}`.",
                    repair_strategy="Bind source capsule, benchmark, comparator, score, uncertainty, falsifier, and replay evidence for this gap.",
                    required_capability=action.get("required_capability"),
                    execution_command=action.get("execution_command", []),
                    pass_predicate=f"Comparator gap `{action.get('gap_id')}` has `{artifact_key}` and gap status PASS.",
                    validator_binding=f"comparator_gap::{action.get('gap_id')}::{artifact_key}",
                ),
            )
            edges.append(graph_edge(lane_node_id, artifact_id, "requires"))
            edges.append(graph_edge(artifact_id, capability_id, "needs_capability"))

    capability_rows_for_graph = capability_development_rows if capability_development_rows is not None else load_capability_development_rows(root)
    for row in capability_rows_for_graph:
        capability_id = str(row.get("capability_development_id") or row.get("capability_escalation_id") or artifact_hash(row)[:16])
        node_id = f"capability_development:{capability_id}"
        source_node_id = str(row.get("source_graph_node_id") or "")
        lane_id = str(row.get("lane_id") or "TOE_CLOSURE_FACTORY")
        nodes[node_id] = graph_node(
            node_id,
            "capability_development",
            str(row.get("status") or "OPEN"),
            lane_id=lane_id,
            source_graph_node_id=source_node_id,
            source_action_id=row.get("source_action_id"),
            missing_artifact_type=row.get("missing_artifact_type"),
            implementation_gap_class=row.get("implementation_gap_class"),
            capability_executor_ready=bool(row.get("capability_executor_ready")),
            why_it_failed=row.get("why_it_failed"),
            repair_strategy=row.get("repair_strategy"),
            required_capability=row.get("required_capability"),
            execution_command=row.get("execution_command", []),
            implementation_command=row.get("implementation_command", []),
            pass_predicate=row.get("pass_predicate"),
            next_escalation=row.get("next_escalation"),
            validator_binding=row.get("validator_binding") or f"capability_development::{capability_id}",
        )
        lane_node_id = f"lane:{lane_id}"
        if lane_node_id in nodes:
            edges.append(graph_edge(node_id, lane_node_id, "produces"))
        if source_node_id and source_node_id in nodes:
            edges.append(graph_edge(source_node_id, node_id, "needs_capability"))
            edges.append(graph_edge(node_id, source_node_id, "supersedes"))

    support_id = "support_index:canonical_refs"
    nodes[support_id] = graph_node(
        support_id,
        "generated_evidence",
        "PASS",
        why_it_failed="Already indexed.",
        repair_strategy="Keep this index fresh before lane writers run.",
        required_capability="Research/SupportIndex",
        execution_command=[sys.executable, "tools/oc133_toe_autonomous_supervisor.py", "--write", "--max-iterations", "0"],
        pass_predicate="support index generated and non-empty.",
        validator_binding="support_reference_index",
        support_summary={
            "lean_symbol_total": support_index.get("lean_symbol_total"),
            "passing_finite_case_total": support_index.get("passing_finite_case_total"),
            "existing_source_ref_total": support_index.get("existing_source_ref_total"),
        },
    )
    for node_id, node in list(nodes.items()):
        if node.get("node_type") in {"required_artifact", "closure_lane"}:
            edges.append(graph_edge(node_id, support_id, "validated_by"))

    open_nodes = [node for node in nodes.values() if node.get("status") != "PASS"]
    next_nodes = [
        node["node_id"]
        for node in open_nodes
        if node.get("node_type") in {"required_artifact", "executor_capability", "capability_development"}
    ][:25]
    payload = {
        "schema_id": "OC133_TOE_BLOCKING_GRAPH_v1",
        "generated_at": generated_at or utc_now(),
        "status": "OPEN" if open_nodes else "PASS",
        "validator_error_total": factory.validator_error_total(parts),
        "science_validator_error_total": len(parts["science_errors"]),
        "cerberus_error_total": len(parts["cerberus_errors"]),
        "node_total": len(nodes),
        "open_node_total": len(open_nodes),
        "edge_total": len(edges),
        "edge_type_total": {edge_type: sum(1 for edge in edges if edge["edge_type"] == edge_type) for edge_type in sorted({edge["edge_type"] for edge in edges})},
        "next_executable_node_ids": next_nodes,
        "graph_frontier_hash": artifact_hash({"nodes": strip_volatile(list(nodes.values())), "edges": edges}),
        "zero_delta_policy": "Zero validator delta updates this graph and selects narrower unresolved dependency nodes; it never mints r017.",
        "nodes": sorted(nodes.values(), key=lambda row: row["node_id"]),
        "edges": sorted(edges, key=lambda row: (row["source"], row["edge_type"], row["target"])),
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def load_state(root: Path) -> dict[str, Any]:
    return read_json(root / SUPERVISOR_DIR / STATE_NAME)


def load_capability_development_rows(root: Path) -> list[dict[str, Any]]:
    payload = read_json(root / SUPERVISOR_DIR / CAPABILITY_DEVELOPMENT_LEDGER_NAME)
    rows = payload.get("rows") or []
    open_lanes = factory.current_open_validator_lanes(root)
    registry = read_json(root / factory.FACTORY_DIR / factory.CAPABILITY_IMPLEMENTATION_REGISTRY_NAME)
    by_source_id = {
        str(row.get("source_capability_development_id")): row
        for row in registry.get("rows", []) or []
        if isinstance(row, dict) and row.get("source_capability_development_id")
    }
    by_key = {
        str(row.get("capability_development_key")): row
        for row in registry.get("rows", []) or []
        if isinstance(row, dict) and row.get("capability_development_key")
    }
    enriched: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        payload = dict(row)
        key = payload.get("capability_development_key") or factory.capability_development_key(payload)
        lane_id = str(payload.get("lane_id") or "")
        if lane_id and lane_id not in open_lanes:
            payload["status"] = "PASS"
            payload["superseded_by_current_validator"] = True
            payload["capability_executor_ready"] = False
            payload["execution_command"] = []
            payload["next_escalation"] = "Lane no longer appears in the strict validator; stale capability-development row is retained as evidence but not executable."
            enriched.append(payload)
            continue
        compiled = by_source_id.get(str(payload.get("capability_development_id"))) or by_key.get(str(key))
        if compiled:
            payload["capability_development_key"] = compiled.get("capability_development_key") or key
            payload["capability_id"] = compiled.get("capability_id") or compiled.get("compiled_capability_id")
            payload["capability_class"] = compiled.get("capability_class") or compiled.get("executor_type")
            payload["compiled_capability_id"] = compiled.get("compiled_capability_id")
            payload["capability_executor_ready"] = compiled.get("capability_executor_ready") is True
            payload["execution_command"] = compiled.get("execution_command", payload.get("execution_command", []))
            payload["implementation_command"] = compiled.get("executor_command", payload.get("implementation_command", []))
            payload["compiled_capability_ref"] = (factory.FACTORY_DIR / factory.CAPABILITY_IMPLEMENTATION_REGISTRY_NAME).as_posix()
            payload["scientific_frontier_hash"] = compiled.get("scientific_frontier_hash") or payload.get("scientific_frontier_hash")
        else:
            payload["capability_development_key"] = key
        enriched.append(payload)
    return enriched


def existing_attempt_signatures(state: dict[str, Any]) -> set[str]:
    rows = state.get("attempted_action_signatures") or []
    return {str(row) for row in rows if row}


def action_defaults(action_id: str, lane_id: str, executor_type: str, command: list[str] | None) -> dict[str, Any]:
    return {
        "action_id": action_id,
        "lane_id": lane_id,
        "executor_type": executor_type,
        "execution_command": command or [],
        "status": "OPEN",
        "why_it_failed": "The strict final TOE validator still reports this lane as open.",
        "repair_strategy": "Execute this action, sync SPOT/projections, rerun validators, and keep r017 blocked unless the strict terminal gate passes.",
        "required_capability": {
            "AI": "Research/AIProjection",
            "ENTERPRISE_ARCHITECTURE": "Research/EnterpriseArchitectureProjection",
            "MODERN_SCIENCE_COMPARATOR_SUPERIORITY": "Research/PriorArt",
            "GRAND_TOE_CLAIM_LEDGER_EVIDENCE": "Research/FormalScience",
            "CERBERUS_RELEASE_REVIEW_GATE": "Review/Cerberus",
        }.get(lane_id, "Research/TOEClosureFactory"),
        "pass_predicate": "The referenced lane disappears from strict TOE validator errors without weakening gates.",
        "next_escalation": "If this action produces no validator delta, split the missing artifact class into a narrower capability work order.",
    }


def projection_actions(root: Path, lane_id: str) -> list[dict[str, Any]]:
    prefix = factory.projection_lane_prefix(lane_id)
    work_orders = read_json(root / factory.lane_execution_base(lane_id) / f"OC133_{prefix}_SOURCE_INTAKE_WORK_ORDERS.json")
    rows = work_orders.get("rows") or []
    actions = []
    for index, row in enumerate(rows, start=1):
        work_order_id = str(row.get("work_order_id") or f"R017-{lane_id}-SOURCE-INTAKE-{index:03d}")
        action = action_defaults(
            f"AUTO-{work_order_id}",
            lane_id,
            "source_intake_work_order",
            [sys.executable, "tools/oc133_toe_closure_factory.py", "--execute-source-intake-work-order", work_order_id, "--write"],
        )
        action.update(
            {
                "work_order_id": work_order_id,
                "required_artifact": row.get("required_artifact"),
                "missing_support_key": row.get("missing_support_key"),
                "source_ref": row.get("source_ref"),
            }
        )
        actions.append(action)
    if not actions:
        action = action_defaults(
            f"AUTO-R017-{lane_id}-SOURCE-DISCOVERY-CAPABILITY",
            lane_id,
            "capability_escalation",
            None,
        )
        action.update(
            {
                "status": "CAPABILITY_BACKLOG_OPEN",
                "why_it_failed": f"{lane_id} has no source-intake work orders to execute.",
                "repair_strategy": "Add source discovery/mining capability for this projection lane before attempting guarded PASS.",
            }
        )
        actions.append(action)
    return actions


def comparator_actions(root: Path) -> list[dict[str, Any]]:
    actions = []
    seen_action_ids: set[str] = set()
    for payload in sorted(factory.comparator_execution_gap_rows(root), key=lambda row: str(row.get("gap_id"))):
        if payload.get("status") == "PASS":
            continue
        gap_id = str(payload.get("gap_id") or "")
        if not gap_id:
            continue
        missing_artifacts = list(payload.get("missing_artifacts") or [])
        for artifact_key in sorted(missing_artifacts, key=lambda key: ARTIFACT_PRIORITY.get(str(key), 80)):
            if artifact_key == "oc_prediction_scoring_row":
                command = [sys.executable, "tools/oc133_toe_closure_factory.py", "--execute-comparator-scoring-work-order", gap_id, "--write"]
                executor_type = "comparator_scoring_work_order"
                repair_strategy = "Build the exact scoring work order before attempting broad superiority; this narrows the source/target/model/comparator/falsifier/replay gap without faking evidence."
            else:
                command = [sys.executable, "tools/oc133_toe_closure_factory.py", "--execute-comparator-gap-artifact", gap_id, str(artifact_key), "--write"]
                executor_type = "comparator_gap_artifact"
                repair_strategy = "Create the exact comparator gap artifact work packet before rerunning broad-coverage closure."
            action = action_defaults(
                f"AUTO-R017-COMPARATOR-GAP-{artifact_hash({'gap_id': gap_id, 'artifact_key': artifact_key})[:12]}",
                "MODERN_SCIENCE_COMPARATOR_SUPERIORITY",
                executor_type,
                command,
            )
            action.update(
                {
                    "gap_id": gap_id,
                    "required_artifact": artifact_key,
                    "missing_artifact_type": artifact_key,
                    "missing_artifact_total": len(missing_artifacts),
                    "source_ref": "live::factory.comparator_execution_gap_rows",
                    "why_it_failed": f"Comparator gap `{gap_id}` lacks `{artifact_key}`.",
                    "repair_strategy": repair_strategy,
                    "pass_predicate": f"Comparator gap `{gap_id}` has `{artifact_key}` and strict coverage register no longer lists it as missing.",
                    "next_escalation": "If this exact artifact action produces zero validator delta, compile a narrower capability-development work order for its failed validation field.",
                }
            )
            seen_action_ids.add(str(action["action_id"]))
            actions.append(action)
    for row in sorted(
        factory.comparator_scoring_backlog_rows(root),
        key=lambda item: (str(item.get("gap_id")), str(item.get("scoring_subartifact_id"))),
    ):
        if row.get("status") == "PASS":
            continue
        gap_id = str(row.get("gap_id") or "")
        subartifact_id = str(row.get("scoring_subartifact_id") or "")
        if not gap_id or not subartifact_id:
            continue
        action_id = f"AUTO-R017-COMPARATOR-SCORING-SUBARTIFACT-{artifact_hash({'gap_id': gap_id, 'subartifact_id': subartifact_id})[:12]}"
        if action_id in seen_action_ids:
            continue
        action = action_defaults(
            action_id,
            "MODERN_SCIENCE_COMPARATOR_SUPERIORITY",
            "comparator_scoring_subartifact",
            [sys.executable, "tools/oc133_toe_closure_factory.py", "--execute-comparator-scoring-subartifact", gap_id, subartifact_id, "--write"],
        )
        action.update(
            {
                "gap_id": gap_id,
                "required_artifact": subartifact_id,
                "missing_artifact_type": subartifact_id,
                "scoring_subartifact_id": subartifact_id,
                "root_cause_class": row.get("root_cause_class"),
                "source_ref": row.get("source_work_order_ref"),
                "why_it_failed": row.get("why_it_failed"),
                "repair_strategy": row.get("repair_strategy"),
                "required_capability": row.get("required_capability"),
                "pass_predicate": row.get("pass_predicate"),
                "next_escalation": "If this subartifact packet produces zero validator delta, implement the exact source acquisition/scoring executor named in required_source_block.",
                "validator_binding": row.get("validator_binding"),
            }
        )
        seen_action_ids.add(action_id)
        actions.append(action)
    return actions


def grand_actions() -> list[dict[str, Any]]:
    action = action_defaults(
        "AUTO-R017-GRAND-PROMOTION-DERIVATION",
        "GRAND_TOE_CLAIM_LEDGER_EVIDENCE",
        "grand_promotion_derivation",
        [sys.executable, "tools/oc133_toe_closure_factory.py", "--execute-lane", "GRAND_TOE_CLAIM_LEDGER_EVIDENCE", "--write"],
    )
    return [action]


def cerberus_actions(science_error_total: int) -> list[dict[str, Any]]:
    lane = factory.lane_registry_by_id()["CERBERUS_RELEASE_REVIEW_GATE"]
    action = action_defaults(
        "AUTO-R017-CERBERUS-CLEAN-REFRESH",
        "CERBERUS_RELEASE_REVIEW_GATE",
        "cerberus_gate",
        lane["execution_command"],
    )
    if science_error_total:
        action.update(
            {
                "status": "BLOCKED_BY_SCIENCE_ERRORS",
                "executor_type": "skip_until_science_pass",
                "execution_command": [],
                "why_it_failed": "Science validator errors remain, so Cerberus is deliberately not run.",
                "repair_strategy": "Close deterministic science lanes before spending external/Cerberus review compute.",
            }
        )
    return [action]


def seed_actions_from_validator(root: Path, parts: dict[str, list[str]]) -> list[dict[str, Any]]:
    science_errors = parts["science_errors"]
    cerberus_errors = parts["cerberus_errors"]
    actions: list[dict[str, Any]] = []
    science_text = "\n".join(science_errors).lower()
    if "ai lane" in science_text or "ai row" in science_text:
        actions.extend(projection_actions(root, "AI"))
    if "enterprise_architecture" in science_text or "enterprise architecture" in science_text:
        actions.extend(projection_actions(root, "ENTERPRISE_ARCHITECTURE"))
    if "modern_science_comparator_superiority" in science_text:
        actions.extend(comparator_actions(root))
    if "grand_toe_claim_ledger_evidence" in science_text or "all_domain_ready_no_send" in science_text:
        actions.extend(grand_actions())
    if cerberus_errors:
        actions.extend(cerberus_actions(len(science_errors)))
    return actions


LANE_PRIORITY = {
    "AI": 10,
    "ENTERPRISE_ARCHITECTURE": 20,
    "MODERN_SCIENCE_COMPARATOR_SUPERIORITY": 30,
    "GRAND_TOE_CLAIM_LEDGER_EVIDENCE": 40,
    "TOE_CLOSURE_FACTORY": 50,
    "CERBERUS_RELEASE_REVIEW_GATE": 80,
}

NODE_TYPE_PRIORITY = {
    "capability_development": 5,
    "required_artifact": 10,
    "executor_capability": 20,
    "closure_lane": 40,
    "validator_error": 50,
}

ARTIFACT_PRIORITY = {
    "source_grounded_non_blocker_candidate": 10,
    "non_blocker_public_claim_scope": 20,
    "lean_refs": 30,
    "finite_case_refs": 40,
    "evidence_or_simulation_refs": 50,
    "comparator_refs": 60,
    "falsifier_refs": 70,
    "verified_open_source_capsule": 10,
    "benchmark_case": 20,
    "incumbent_comparator": 30,
    "oc_prediction_scoring_row": 40,
    "uncertainty_row": 50,
    "falsifier_row": 60,
    "replay_record": 70,
}


def graph_priority_tuple(node: dict[str, Any], science_error_total: int) -> tuple[int, int, int, str]:
    lane_id = str(node.get("lane_id") or "TOE_CLOSURE_FACTORY")
    lane_priority = LANE_PRIORITY.get(lane_id, 60)
    if lane_id == "CERBERUS_RELEASE_REVIEW_GATE" and science_error_total:
        lane_priority = 90
    node_priority = NODE_TYPE_PRIORITY.get(str(node.get("node_type")), 90)
    artifact_key = str(node.get("artifact_key") or node.get("missing_artifact_type") or "")
    artifact_priority = ARTIFACT_PRIORITY.get(artifact_key, 80)
    return (lane_priority, artifact_priority, node_priority, str(node.get("node_id")))


def action_by_id(actions: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(action.get("action_id")): action for action in actions}


def capability_targets_for_required_artifact(graph: dict[str, Any], node_id: str) -> list[str]:
    return [
        edge["target"]
        for edge in graph.get("edges", []) or []
        if edge.get("source") == node_id
        and edge.get("edge_type") == "needs_capability"
        and str(edge.get("target", "")).startswith("capability:")
    ]


def graph_action_for_node(
    graph: dict[str, Any],
    node: dict[str, Any],
    seed_actions: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    node_id = str(node.get("node_id"))
    node_type = str(node.get("node_type"))
    capability_node_ids: list[str] = []
    if node_type == "executor_capability" and node_id.startswith("capability:"):
        capability_node_ids = [node_id]
    elif node_type == "required_artifact":
        capability_node_ids = capability_targets_for_required_artifact(graph, node_id)
    elif (
        node_type == "capability_development"
        and node.get("execution_command")
        and node.get("capability_executor_ready") is True
    ):
        action = action_defaults(
            f"AUTO-{node_id.replace(':', '-').replace('/', '-')}",
            str(node.get("lane_id") or "TOE_CLOSURE_FACTORY"),
            "capability_development",
            list(node.get("execution_command") or []),
        )
        action.update(
            {
                "graph_node_id": node_id,
                "graph_node_type": node_type,
                "graph_dependency_path": [node_id],
                "source_graph_node_id": node.get("source_graph_node_id"),
                "missing_artifact_type": node.get("missing_artifact_type"),
                "why_it_failed": node.get("why_it_failed"),
                "repair_strategy": node.get("repair_strategy"),
                "required_capability": node.get("required_capability"),
                "pass_predicate": node.get("pass_predicate"),
                "next_escalation": node.get("next_escalation"),
                "validator_binding": node.get("validator_binding"),
            }
        )
        return action
    for capability_node_id in capability_node_ids:
        action_id = capability_node_id.removeprefix("capability:")
        action = seed_actions.get(action_id)
        if not action:
            continue
        payload = dict(action)
        payload.update(
            {
                "graph_node_id": node_id,
                "graph_node_type": node_type,
                "graph_dependency_path": [node_id, capability_node_id] if node_id != capability_node_id else [node_id],
                "required_artifact": node.get("artifact_key") or payload.get("required_artifact"),
                "gap_id": node.get("gap_id") or payload.get("gap_id"),
                "missing_artifact_type": node.get("artifact_key") or payload.get("missing_artifact_type"),
                "validator_binding": node.get("validator_binding") or payload.get("validator_binding"),
            }
        )
        return payload
    return None


def resolve_actions_from_graph(
    graph: dict[str, Any],
    seed_actions: list[dict[str, Any]],
    science_error_total: int,
) -> list[dict[str, Any]]:
    seed_by_id = action_by_id(seed_actions)
    resolved: list[dict[str, Any]] = []
    seen_action_ids: set[str] = set()
    open_nodes = [node for node in graph.get("nodes", []) or [] if node.get("status") != "PASS"]
    for node in sorted(open_nodes, key=lambda row: graph_priority_tuple(row, science_error_total)):
        if node.get("node_type") not in {"required_artifact", "executor_capability", "capability_development"}:
            continue
        action = graph_action_for_node(graph, node, seed_by_id)
        if not action:
            continue
        action_id = str(action.get("action_id"))
        if action_id in seen_action_ids:
            continue
        action["planner_mode"] = "GRAPH_RESOLVER"
        action["graph_priority"] = list(graph_priority_tuple(node, science_error_total))
        seen_action_ids.add(action_id)
        resolved.append(action)
    if resolved:
        return resolved
    for action in seed_actions:
        payload = dict(action)
        payload["planner_mode"] = "LEGACY_FALLBACK_NO_GRAPH_ACTION"
        payload["graph_node_id"] = None
        payload["graph_node_type"] = None
        payload["graph_dependency_path"] = []
        resolved.append(payload)
    return resolved


def plan_next_actions(root: Path, state: dict[str, Any], frontier_hash: str) -> dict[str, Any]:
    parts = factory.current_validator_error_parts(root)
    science_errors = parts["science_errors"]
    cerberus_errors = parts["cerberus_errors"]
    seed_actions = seed_actions_from_validator(root, parts)
    support_index = build_support_reference_index(root)
    seed_queue = {"rows": seed_actions}
    planning_graph = build_blocking_graph(root, seed_queue, support_index)
    actions = resolve_actions_from_graph(planning_graph, seed_actions, len(science_errors))

    attempted = existing_attempt_signatures(state)
    for action in actions:
        signature = f"{frontier_hash}::{action['action_id']}"
        action["frontier_signature"] = signature
        action["already_attempted_on_frontier"] = signature in attempted
        action["selected_for_execution"] = False
        if action["already_attempted_on_frontier"] and action["executor_type"] != "skip_until_science_pass":
            action["status"] = "CAPABILITY_ESCALATION_REQUIRED"
            action["next_escalation"] = "This exact action has already been tried on this semantic frontier; create a narrower capability work order instead of rerunning it."

    payload = {
        "schema_id": "OC133_TOE_AUTONOMOUS_NEXT_ACTION_QUEUE_v1",
        "generated_at": utc_now(),
        "status": "OPEN" if actions else "PASS",
        "frontier_hash": frontier_hash,
        "planner_mode": "GRAPH_RESOLVER",
        "blocking_graph_ref": (factory.FACTORY_DIR / BLOCKING_GRAPH_NAME).as_posix(),
        "blocking_graph_frontier_hash": planning_graph.get("graph_frontier_hash"),
        "support_reference_index_ref": (factory.FACTORY_DIR / SUPPORT_INDEX_NAME).as_posix(),
        "validator_error_total": factory.validator_error_total(parts),
        "science_validator_error_total": len(science_errors),
        "cerberus_error_total": len(cerberus_errors),
        "graph_candidate_node_total": len([
            node for node in planning_graph.get("nodes", []) or []
            if node.get("status") != "PASS"
            and node.get("node_type") in {"required_artifact", "executor_capability", "capability_development"}
        ]),
        "selected_graph_node_ids": [
            str(action.get("graph_node_id"))
            for action in actions
            if action.get("graph_node_id")
        ],
        "action_total": len(actions),
        "executable_action_total": sum(
            1
            for action in actions
            if action["execution_command"] and not action.get("already_attempted_on_frontier")
        ),
        "zero_delta_continue_policy": "PASS",
        "terminal_stop_on_zero_delta": False,
        "rows": actions,
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def select_actions(queue: dict[str, Any], max_actions: int) -> list[dict[str, Any]]:
    selected = []
    for action in queue.get("rows", []) or []:
        if not action.get("execution_command"):
            continue
        if action.get("already_attempted_on_frontier"):
            continue
        selected.append(action)
        if max_actions > 0 and len(selected) >= max_actions:
            break
    return selected


def run_action(root: Path, action: dict[str, Any], timeout: int) -> dict[str, Any]:
    before_parts = factory.current_validator_error_parts(root)
    before_frontier = semantic_frontier_hash(root)
    result = factory.safe_run_command(root, list(action["execution_command"]), timeout)
    after_parts = factory.current_validator_error_parts(root)
    after_frontier = semantic_frontier_hash(root)
    before_total = factory.validator_error_total(before_parts)
    after_total = factory.validator_error_total(after_parts)
    return {
        "action_id": action["action_id"],
        "lane_id": action["lane_id"],
        "executor_type": action["executor_type"],
        "planner_mode": action.get("planner_mode"),
        "graph_node_id": action.get("graph_node_id"),
        "graph_node_type": action.get("graph_node_type"),
        "graph_dependency_path": action.get("graph_dependency_path", []),
        "status": "PASS" if result["returncode"] == 0 else "FAIL_CLOSED",
        "frontier_signature": action["frontier_signature"],
        "frontier_hash_before": before_frontier,
        "frontier_hash_after": after_frontier,
        "before_validator_error_total": before_total,
        "after_validator_error_total": after_total,
        "validator_error_delta": before_total - after_total,
        "result": result,
        "why_it_failed": action["why_it_failed"],
        "repair_strategy": action["repair_strategy"],
        "required_capability": action["required_capability"],
        "execution_command": action["execution_command"],
        "pass_predicate": action["pass_predicate"],
        "next_escalation": action["next_escalation"],
    }


def sync_and_validate(root: Path, timeout: int) -> list[dict[str, Any]]:
    rows = []
    commands = [
        ("sync_spot", [sys.executable, "tools/build_oc_core_1_3_science_spot.py"]),
        ("grand_science_scorecard_sync", [sys.executable, "tools/oc133_grand_science_research_loop.py", "--execute", "--allow-blocked-exit-zero"]),
        ("science_validator_before_cerberus", [sys.executable, "tools/validate_oc_core_1_3_science_spot.py", "--require-final-toe-pass"]),
    ]
    for purpose, cmd in commands:
        result = factory.safe_run_command(root, cmd, timeout)
        rows.append({"purpose": purpose, "status": "PASS" if result["returncode"] == 0 else "FAIL_CLOSED", "result": result})
    if rows[-1]["status"] == "PASS":
        cerberus_cmd = factory.lane_registry_by_id()["CERBERUS_RELEASE_REVIEW_GATE"]["execution_command"]
        result = factory.safe_run_command(root, cerberus_cmd, timeout)
        rows.append({"purpose": "canonical_cerberus_after_science_clear", "status": "PASS" if result["returncode"] == 0 else "FAIL_CLOSED", "result": result})
    else:
        rows.append(
            {
                "purpose": "canonical_cerberus_after_science_clear",
                "status": "SKIPPED_DETERMINISTIC_SCIENCE_BLOCKERS_REMAIN",
                "result": {
                    "cmd": factory.lane_registry_by_id()["CERBERUS_RELEASE_REVIEW_GATE"]["execution_command"],
                    "returncode": None,
                    "stdout_tail": "",
                    "stderr_tail": "Skipped because science validator remains red; expensive Cerberus/LLM gate is not run.",
                },
            }
        )
    final_cmd = [sys.executable, "tools/validate_oc_core_1_3_science_spot.py", "--require-final-toe-pass", "--require-cerberus-clean"]
    result = factory.safe_run_command(root, final_cmd, timeout)
    rows.append({"purpose": "final_validator", "status": "PASS" if result["returncode"] == 0 else "FAIL_CLOSED", "result": result})
    return rows


def terminal_validation(root: Path, timeout: int, final_validator_passed: bool) -> dict[str, Any]:
    rows = []
    if final_validator_passed:
        commands = [
            ("assemble_recovery_r017", [sys.executable, "tools/assemble_oc_core_release_package.py", "--release", factory.RELEASE_ID, "--structure-source", "recovered_l10c", "--assembly-revision", "recovery_r017", "--write"]),
            ("machine_audit_write", [sys.executable, "tools/audit_oc_core_release_assembly_machine.py", "--release", factory.RELEASE_ID, "--assembly-revision", "recovery_r017", "--write"]),
            ("machine_audit_check", [sys.executable, "tools/audit_oc_core_release_assembly_machine.py", "--release", factory.RELEASE_ID, "--assembly-revision", "recovery_r017", "--check"]),
            ("quality_audit_write", [sys.executable, "tools/audit_oc_core_release_quality.py", "--release", factory.RELEASE_ID, "--assembly-revision", "recovery_r017", "--write"]),
            ("quality_audit_check", [sys.executable, "tools/audit_oc_core_release_quality.py", "--release", factory.RELEASE_ID, "--assembly-revision", "recovery_r017", "--check"]),
            ("compare_r016_r017_write", [sys.executable, "tools/compare_oc_core_assembly_revisions.py", "--release", factory.RELEASE_ID, "--baseline-revision", "recovery_r016", "--candidate-revision", "recovery_r017", "--write"]),
            ("compare_r016_r017_check", [sys.executable, "tools/compare_oc_core_assembly_revisions.py", "--release", factory.RELEASE_ID, "--baseline-revision", "recovery_r016", "--candidate-revision", "recovery_r017", "--check"]),
            ("release_machine_pytest", [sys.executable, "-m", "pytest", "release_machine/tests/test_release_assembly_machine.py", "-q"]),
        ]
        for purpose, cmd in commands:
            result = factory.safe_run_command(root, cmd, timeout)
            rows.append({"purpose": purpose, "status": "PASS" if result["returncode"] == 0 else "FAIL_CLOSED", "result": result})
            if result["returncode"] != 0:
                break
    payload = {
        "schema_id": "OC133_TOE_AUTONOMOUS_TERMINAL_VALIDATION_REPORT_v1",
        "generated_at": utc_now(),
        "status": "PASS" if final_validator_passed and rows and all(row["status"] == "PASS" for row in rows) else "BLOCKED",
        "final_validator_passed": final_validator_passed,
        "terminal_command_total": len(rows),
        "r017_assembly_attempted": bool(rows),
        "no_fake_closure_policy": "Terminal r017 assembly is attempted only after strict final TOE validator PASS.",
        "rows": rows,
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def escalation_rows(queue: dict[str, Any], action_results: list[dict[str, Any]], frontier_repeated: bool) -> list[dict[str, Any]]:
    rows = []
    attempted_ids = {row["action_id"] for row in action_results}
    for index, action in enumerate(queue.get("rows", []) or [], start=1):
        needs_escalation = action.get("already_attempted_on_frontier") or action["action_id"] in attempted_ids
        if not needs_escalation:
            continue
        missing_artifact_type = (
            action.get("required_artifact")
            or action.get("missing_artifact_type")
            or (action.get("missing_artifacts") or [None])[0]
            or action.get("executor_type")
        )
        row = {
            "capability_escalation_id": f"AUTO-R017-CAPABILITY-ESCALATION-{index:04d}",
            "capability_development_id": f"AUTO-R017-CAPABILITY-DEVELOPMENT-{index:04d}-{artifact_hash(action)[:8]}",
            "source_action_id": action["action_id"],
            "source_graph_node_id": action.get("source_graph_node_id") or action.get("graph_node_id"),
            "source_graph_node_type": action.get("graph_node_type"),
            "graph_dependency_path": action.get("graph_dependency_path", []),
            "lane_id": action["lane_id"],
            "executor_type": action["executor_type"],
            "missing_artifact_type": missing_artifact_type,
            "implementation_gap_class": "ZERO_DELTA_GRAPH_DEPENDENCY",
            "capability_executor_ready": False,
            "scientific_frontier_hash": queue.get("frontier_hash"),
            "capability_development_key": factory.capability_development_key(
                {
                    "lane_id": action["lane_id"],
                    "source_graph_node_id": action.get("source_graph_node_id") or action.get("graph_node_id"),
                    "missing_artifact_type": missing_artifact_type,
                    "scientific_frontier_hash": queue.get("frontier_hash"),
                }
            ),
            "status": "OPEN",
            "frontier_repeated": frontier_repeated,
            "why_it_failed": "The action did not reduce strict validator errors on this semantic frontier.",
            "repair_strategy": "Create a narrower source-bound executor for the exact missing artifact class before rerunning the same action.",
            "required_capability": action["required_capability"],
            "execution_command": action.get("execution_command", []),
            "implementation_command": [
                sys.executable,
                "tools/oc133_toe_autonomous_supervisor.py",
                "--write",
                "--until-r017-pass",
                "--max-iterations",
                "0",
                "--resume",
            ],
            "pass_predicate": action["pass_predicate"],
            "next_escalation": action["next_escalation"],
            "validator_binding": action.get("validator_binding") or f"action::{action['action_id']}",
        }
        rows.append(row)
    return rows


def run_supervisor(root: Path, args: argparse.Namespace) -> dict[str, dict[str, Any]]:
    run_started_monotonic = time.monotonic()
    generated_at = utc_now()
    prior_state = load_state(root) if args.resume else {}
    attempted = existing_attempt_signatures(prior_state)
    gate = worktree_gate(root)
    if gate["status"] != "PASS":
        parts = factory.current_validator_error_parts(root)
        state = {
            "schema_id": "OC133_TOE_AUTONOMOUS_SUPERVISOR_STATE_v1",
            "generated_at": generated_at,
            "status": "REFUSED_UNEXPECTED_DIRTY_WORKTREE",
            "current_promotion_gate": "R017_BLOCKED_BY_UNEXPECTED_DIRTY_WORKTREE",
            "r017_promotion_allowed": False,
            "iteration_total": 0,
            "latest_wave_id": None,
            "validator_error_total": factory.validator_error_total(parts),
            "science_validator_error_total": len(parts["science_errors"]),
            "cerberus_error_total": len(parts["cerberus_errors"]),
            "capability_escalation_total": 0,
            "current_graph_node_id": None,
            "active_executor": None,
            "last_validator_delta": 0,
            "elapsed_runtime_seconds": int(time.monotonic() - run_started_monotonic),
            "last_commit_sha": factory.git_head(root),
            "next_escalation": "Clean unexpected tracked worktree dirt before autonomous TOE closure can continue.",
            "last_heartbeat_at": utc_now(),
            "worktree_gate": gate,
            "attempted_action_signatures": sorted(attempted),
            "attempted_action_signature_total": len(attempted),
            "zero_delta_continue_policy": "PASS",
            "terminal_stop_on_zero_delta": False,
            "terminal_validation_status": "BLOCKED",
            "commit_checkpoint_requested": bool(args.commit_checkpoints),
            "no_publication_action_policy": "No Zenodo, DOI, GitHub release, journal submission, or public upload action is performed.",
        }
        state["artifact_hash"] = artifact_hash(state)
        outputs = build_outputs(root, state, [], {}, [], [], [], terminal_validation(root, args.timeout, False), gate)
        if args.write:
            write_outputs(root, outputs)
        return outputs

    wave_rows = []
    frontier_rows = []
    all_action_results = []
    all_escalations = load_capability_development_rows(root) if args.resume else []
    commit_rows: list[dict[str, Any]] = []
    terminal_report = terminal_validation(root, args.timeout, False)
    iteration = 0
    max_iterations = int(args.max_iterations)
    while True:
        iteration += 1
        if args.write:
            factory.compile_capability_backlog(root, write=True)
        before_parts = factory.current_validator_error_parts(root)
        before_total = factory.validator_error_total(before_parts)
        frontier_before = semantic_frontier_hash(root)
        queue = plan_next_actions(root, {"attempted_action_signatures": sorted(attempted)}, frontier_before)
        selected = select_actions(queue, int(args.max_actions_per_iteration))
        if not args.write:
            selected = []
        for action in queue["rows"]:
            action["selected_for_execution"] = action["action_id"] in {row["action_id"] for row in selected}
        action_results = [run_action(root, action, args.timeout) for action in selected]
        attempted.update(row["frontier_signature"] for row in action_results if row.get("frontier_signature"))
        validation_rows = sync_and_validate(root, args.timeout) if args.write else [
            {
                "purpose": "dry_run_no_write",
                "status": "SKIPPED_DRY_RUN",
                "result": {
                    "cmd": [],
                    "returncode": None,
                    "stdout_tail": "",
                    "stderr_tail": "Autonomous supervisor was run without --write; no mutation or validators were executed.",
                },
            }
        ]
        after_parts = factory.current_validator_error_parts(root)
        after_total = factory.validator_error_total(after_parts)
        frontier_after = semantic_frontier_hash(root)
        final_passed = validation_rows[-1]["status"] == "PASS"
        if final_passed:
            terminal_report = terminal_validation(root, args.timeout, True)
        frontier_repeated = frontier_before == frontier_after
        escalations = escalation_rows(queue, action_results, frontier_repeated or before_total - after_total <= 0)
        all_escalations.extend(escalations)
        if args.write and all_escalations:
            live_capability_development = build_capability_development_ledger(all_escalations, generated_at)
            write_json(root, SUPERVISOR_DIR / CAPABILITY_DEVELOPMENT_LEDGER_NAME, live_capability_development)
            factory.compile_capability_backlog(root, write=True)
        all_action_results.extend(action_results)
        wave_id = f"R017-AUTO-WAVE-{iteration + 5:03d}"
        wave_rows.append(
            {
                "wave_id": wave_id,
                "iteration": iteration,
                "status": "PASS" if final_passed else "INTERNAL_AUTONOMOUS_RUN_STATE_OPEN",
                "frontier_hash_before": frontier_before,
                "frontier_hash_after": frontier_after,
                "frontier_repeated": frontier_repeated,
                "before_validator_error_total": before_total,
                "after_validator_error_total": after_total,
                "validator_error_delta": before_total - after_total,
                "next_action_ids": [action["action_id"] for action in queue["rows"]],
                "next_graph_node_ids": [action.get("graph_node_id") for action in queue["rows"] if action.get("graph_node_id")],
                "selected_action_ids": [action["action_id"] for action in selected],
                "selected_graph_node_ids": [action.get("graph_node_id") for action in selected if action.get("graph_node_id")],
                "executor_selected": "graph_resolver",
                "active_executor": selected[0].get("executor_type") if selected else None,
                "capability_escalation_ids": [row["capability_escalation_id"] for row in escalations],
                "commit_sha": factory.git_head(root),
                "terminal_gate": "R017_READY_TO_ASSEMBLE" if final_passed else "R017_BLOCKED_BY_TOE_AUTONOMOUS_SUPERVISOR",
                "action_results": action_results,
                "validation_rows": validation_rows,
            }
        )
        frontier_rows.append(
            {
                "wave_id": wave_id,
                "frontier_hash_before": frontier_before,
                "frontier_hash_after": frontier_after,
                "frontier_repeated": frontier_repeated,
                "validator_error_delta": before_total - after_total,
            }
        )
        if final_passed and terminal_report["status"] == "PASS":
            break
        if max_iterations > 0 and iteration >= max_iterations:
            break
        if max_iterations == 0 and not selected:
            time.sleep(max(0, int(args.sleep_on_cooldown_seconds)))
        if not args.until_r017_pass and iteration >= 1:
            break

    current_parts = factory.current_validator_error_parts(root)
    current_total = factory.validator_error_total(current_parts)
    latest_wave = wave_rows[-1] if wave_rows else {}
    latest_selected = (latest_wave.get("action_results") or [{}])[0] if latest_wave.get("action_results") else {}
    latest_queue_action = (queue.get("rows") or [{}])[0] if isinstance(queue, dict) and queue.get("rows") else {}
    current_graph_node_id = latest_selected.get("graph_node_id") or latest_queue_action.get("graph_node_id")
    active_executor = latest_selected.get("executor_type") or latest_queue_action.get("executor_type")
    last_validator_delta = latest_wave.get("validator_error_delta", 0)
    latest_escalation = all_escalations[-1] if all_escalations else {}
    state = {
        "schema_id": "OC133_TOE_AUTONOMOUS_SUPERVISOR_STATE_v1",
        "generated_at": generated_at,
        "status": "PASS" if terminal_report.get("status") == "PASS" else "INTERNAL_AUTONOMOUS_RUN_STATE_OPEN",
        "release_id": factory.RELEASE_ID,
        "version": factory.VERSION,
        "r017_promotion_allowed": terminal_report.get("status") == "PASS",
        "current_promotion_gate": "R017_READY_TO_ASSEMBLE" if terminal_report.get("status") == "PASS" else "R017_BLOCKED_BY_TOE_AUTONOMOUS_SUPERVISOR",
        "iteration_total": len(wave_rows),
        "latest_wave_id": wave_rows[-1]["wave_id"] if wave_rows else None,
        "validator_error_total": current_total,
        "science_validator_error_total": len(current_parts["science_errors"]),
        "cerberus_error_total": len(current_parts["cerberus_errors"]),
        "attempted_action_signatures": sorted(attempted),
        "attempted_action_signature_total": len(attempted),
        "capability_escalation_total": len(all_escalations),
        "current_graph_node_id": current_graph_node_id,
        "active_executor": active_executor,
        "last_validator_delta": last_validator_delta,
        "elapsed_runtime_seconds": int(time.monotonic() - run_started_monotonic),
        "last_commit_sha": factory.git_head(root),
        "next_escalation": latest_escalation.get("next_escalation") or latest_queue_action.get("next_escalation"),
        "last_heartbeat_at": utc_now(),
        "graph_resolver_status": "PASS",
        "zero_delta_continue_policy": "PASS",
        "terminal_stop_on_zero_delta": False,
        "worktree_gate": gate,
        "terminal_validation_status": terminal_report.get("status"),
        "commit_checkpoint_requested": bool(args.commit_checkpoints),
        "no_publication_action_policy": "No Zenodo, DOI, GitHub release, journal submission, or public upload action is performed.",
    }
    state["artifact_hash"] = artifact_hash(state)
    outputs = build_outputs(root, state, wave_rows, queue if wave_rows else {}, all_action_results, all_escalations, frontier_rows, terminal_report, gate)
    if args.write:
        write_outputs(root, outputs)
    if args.commit_checkpoints and args.write:
        commit_rows.append(commit_checkpoint(root))
        outputs[SUPERVISOR_DIR / COMMIT_LEDGER_NAME] = build_commit_ledger(commit_rows)
    return outputs


def build_outputs(
    root: Path,
    state: dict[str, Any],
    wave_rows: list[dict[str, Any]],
    queue: dict[str, Any],
    action_results: list[dict[str, Any]],
    escalation_rows_payload: list[dict[str, Any]],
    frontier_rows: list[dict[str, Any]],
    terminal_report: dict[str, Any],
    gate: dict[str, Any],
) -> dict[Path, dict[str, Any]]:
    support_index = build_support_reference_index(root, state["generated_at"])
    scientific_frontier = factory.build_scientific_frontier(root, generated_at=state["generated_at"])
    capability_development = build_capability_development_ledger(escalation_rows_payload, state["generated_at"])
    blocking_graph = build_blocking_graph(
        root,
        queue or {},
        support_index,
        state["generated_at"],
        capability_development.get("rows", []),
    )
    wave_ledger = {
        "schema_id": "OC133_TOE_AUTONOMOUS_WAVE_LEDGER_v1",
        "generated_at": state["generated_at"],
        "status": "PASS" if state["r017_promotion_allowed"] else "INTERNAL_AUTONOMOUS_RUN_STATE_OPEN",
        "wave_total": len(wave_rows),
        "zero_delta_continue_policy": "PASS",
        "terminal_stop_on_zero_delta": False,
        "rows": wave_rows,
    }
    wave_ledger["artifact_hash"] = artifact_hash(wave_ledger)
    queue_payload = queue or {
        "schema_id": "OC133_TOE_AUTONOMOUS_NEXT_ACTION_QUEUE_v1",
        "generated_at": state["generated_at"],
        "status": "MISSING",
        "rows": [],
    }
    queue_payload["artifact_hash"] = artifact_hash(queue_payload)
    escalation = {
        "schema_id": "OC133_TOE_AUTONOMOUS_CAPABILITY_ESCALATION_LEDGER_v1",
        "generated_at": state["generated_at"],
        "status": "OPEN" if escalation_rows_payload else "PASS",
        "capability_escalation_total": len(escalation_rows_payload),
        "zero_delta_creates_capability_work": True,
        "rows": escalation_rows_payload,
    }
    escalation["artifact_hash"] = artifact_hash(escalation)
    frontier = {
        "schema_id": "OC133_TOE_AUTONOMOUS_FRONTIER_HASHES_v1",
        "generated_at": state["generated_at"],
        "status": "PASS",
        "frontier_row_total": len(frontier_rows),
        "rows": frontier_rows,
    }
    frontier["artifact_hash"] = artifact_hash(frontier)
    commit_ledger = build_commit_ledger([])
    cockpit = {
        "schema_id": "OC133_TOE_AUTONOMOUS_COCKPIT_v1",
        "generated_at": state["generated_at"],
        "status": state["status"],
        "current_promotion_gate": state["current_promotion_gate"],
        "r017_promotion_allowed": state["r017_promotion_allowed"],
        "validator_error_total": state["validator_error_total"],
        "science_validator_error_total": state["science_validator_error_total"],
        "cerberus_error_total": state["cerberus_error_total"],
        "iteration_total": state["iteration_total"],
        "latest_wave_id": state["latest_wave_id"],
        "next_action_total": int(queue_payload.get("action_total") or 0),
        "executable_action_total": int(queue_payload.get("executable_action_total") or 0),
        "capability_escalation_total": state["capability_escalation_total"],
        "capability_development_total": capability_development["capability_development_total"],
        "open_capability_development_total": capability_development["open_capability_development_total"],
        "blocking_graph_status": blocking_graph["status"],
        "blocking_graph_open_node_total": blocking_graph["open_node_total"],
        "blocking_graph_frontier_hash": blocking_graph["graph_frontier_hash"],
        "support_reference_index_status": support_index["status"],
        "indexed_lean_ref_total": support_index["indexed_lean_ref_total"],
        "passing_finite_case_total": support_index["passing_finite_case_total"],
        "heartbeat_ref": (SUPERVISOR_DIR / HEARTBEAT_NAME).as_posix(),
        "current_graph_node_id": state.get("current_graph_node_id"),
        "active_executor": state.get("active_executor"),
        "last_validator_delta": state.get("last_validator_delta"),
        "elapsed_runtime_seconds": state.get("elapsed_runtime_seconds"),
        "last_commit_sha": state.get("last_commit_sha"),
        "next_escalation": state.get("next_escalation"),
        "worktree_gate_status": gate["status"],
        "terminal_validation_status": terminal_report["status"],
        "zero_delta_continue_policy": "PASS",
        "terminal_stop_on_zero_delta": False,
        "local_external_compute_policy": "deterministic/static first; governed local LLM only through Logion service; external Cerberus only after deterministic science blockers are zero",
        "no_publication_action_policy": state["no_publication_action_policy"],
    }
    cockpit["artifact_hash"] = artifact_hash(cockpit)
    return {
        factory.FACTORY_DIR / SUPPORT_INDEX_NAME: support_index,
        factory.FACTORY_DIR / factory.SCIENTIFIC_FRONTIER_NAME: scientific_frontier,
        factory.FACTORY_DIR / BLOCKING_GRAPH_NAME: blocking_graph,
        SUPERVISOR_DIR / STATE_NAME: state,
        SUPERVISOR_DIR / COCKPIT_NAME: cockpit,
        SUPERVISOR_DIR / WAVE_LEDGER_NAME: wave_ledger,
        SUPERVISOR_DIR / NEXT_ACTION_QUEUE_NAME: queue_payload,
        SUPERVISOR_DIR / ESCALATION_LEDGER_NAME: escalation,
        SUPERVISOR_DIR / CAPABILITY_DEVELOPMENT_LEDGER_NAME: capability_development,
        SUPERVISOR_DIR / FRONTIER_HASHES_NAME: frontier,
        SUPERVISOR_DIR / COMMIT_LEDGER_NAME: commit_ledger,
        SUPERVISOR_DIR / TERMINAL_VALIDATION_NAME: terminal_report,
        SUPERVISOR_DIR / HEARTBEAT_NAME: build_heartbeat(state),
    }


def build_commit_ledger(rows: list[dict[str, Any]]) -> dict[str, Any]:
    payload = {
        "schema_id": "OC133_TOE_AUTONOMOUS_COMMIT_LEDGER_v1",
        "generated_at": utc_now(),
        "status": "PASS" if rows else "NO_CHECKPOINT_COMMIT_REQUESTED_OR_CREATED",
        "commit_total": len(rows),
        "rows": rows,
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def build_capability_development_ledger(rows: list[dict[str, Any]], generated_at: str) -> dict[str, Any]:
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    current_scientific_frontier_hash = factory.build_scientific_frontier(ROOT, generated_at=generated_at)["scientific_frontier_hash"]
    open_lanes = factory.current_open_validator_lanes(ROOT)
    source_rows_by_capability_id = {
        str(row.get("capability_development_id")): row
        for row in rows
        if isinstance(row, dict) and row.get("capability_development_id")
    }

    def root_source_graph_node(row: dict[str, Any]) -> str | None:
        source_node = row.get("source_graph_node_id")
        visited: set[str] = set()
        while isinstance(source_node, str) and source_node.startswith("capability_development:"):
            capability_id = source_node.removeprefix("capability_development:")
            if capability_id in visited:
                break
            visited.add(capability_id)
            parent = source_rows_by_capability_id.get(capability_id)
            if not parent:
                break
            source_node = parent.get("source_graph_node_id")
        return str(source_node) if source_node else None

    registry = read_json(ROOT / factory.FACTORY_DIR / factory.CAPABILITY_IMPLEMENTATION_REGISTRY_NAME)
    registry_by_key = {
        str(row.get("capability_development_key")): row
        for row in registry.get("rows", []) or []
        if isinstance(row, dict) and row.get("capability_development_key")
    }
    registry_by_source = {
        str(row.get("source_capability_development_id")): row
        for row in registry.get("rows", []) or []
        if isinstance(row, dict) and row.get("source_capability_development_id")
    }
    for row in rows:
        capability_id = str(row.get("capability_development_id") or row.get("capability_escalation_id") or artifact_hash(row)[:16])
        payload = dict(row)
        payload["capability_development_id"] = capability_id
        root_source = root_source_graph_node(payload)
        if root_source:
            payload["source_graph_node_id"] = root_source
        if isinstance(root_source, str) and root_source.startswith("required_artifact:MODERN_SCIENCE_COMPARATOR_SUPERIORITY:"):
            parts = root_source.split(":")
            if len(parts) >= 4:
                gap_id = parts[2]
                artifact_key = parts[3]
                payload["gap_id"] = gap_id
                payload["missing_artifact_type"] = artifact_key
                if factory.comparator_gap_research_artifact_passes(ROOT, gap_id, artifact_key):
                    payload["status"] = "PASS"
                    payload["superseded_by_research_artifact"] = True
                    payload["capability_executor_ready"] = False
                    payload["execution_command"] = []
                    payload["implementation_command"] = []
                    payload["next_escalation"] = "Comparator research artifact now exists and passes at this scope; advance to the next missing artifact."
        lane_id = str(payload.get("lane_id") or "")
        if lane_id and lane_id not in open_lanes:
            payload["status"] = "PASS"
            payload["superseded_by_current_validator"] = True
            payload["capability_executor_ready"] = False
            payload["execution_command"] = []
            payload["implementation_command"] = []
            payload["next_escalation"] = "Lane no longer appears in the strict validator; stale zero-delta row is closed as superseded evidence."
        payload["scientific_frontier_hash"] = current_scientific_frontier_hash
        payload["capability_development_key"] = factory.capability_development_key(payload)
        dedupe_key = str(payload["capability_development_key"])
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        compiled = registry_by_key.get(dedupe_key) or registry_by_source.get(capability_id)
        if compiled and not payload.get("superseded_by_current_validator"):
            payload["capability_id"] = compiled.get("capability_id") or compiled.get("compiled_capability_id")
            payload["capability_class"] = compiled.get("capability_class") or compiled.get("executor_type")
            payload["compiled_capability_id"] = compiled.get("compiled_capability_id")
            payload["capability_executor_ready"] = compiled.get("capability_executor_ready") is True
            payload["execution_command"] = compiled.get("execution_command", payload.get("execution_command", []))
            payload["implementation_command"] = compiled.get("executor_command", payload.get("implementation_command", []))
            payload["compiled_capability_ref"] = (factory.FACTORY_DIR / factory.CAPABILITY_IMPLEMENTATION_REGISTRY_NAME).as_posix()
            payload["scientific_frontier_hash"] = compiled.get("scientific_frontier_hash") or payload.get("scientific_frontier_hash")
        payload.setdefault("status", "OPEN")
        payload.setdefault("why_it_failed", "A graph-selected action produced zero validator delta.")
        payload.setdefault("repair_strategy", "Implement a narrower source-bound capability for this exact missing artifact.")
        payload.setdefault("required_capability", "Research/TOEClosureFactory")
        payload.setdefault("execution_command", [])
        payload.setdefault("implementation_command", [])
        payload.setdefault("capability_executor_ready", False)
        payload.setdefault("pass_predicate", "The source-bound capability executes and removes its validator-bound blocker.")
        payload.setdefault("next_escalation", "Split this capability again by lower-level source/evidence dependency.")
        payload.setdefault("validator_binding", payload.get("source_action_id") or "strict_final_toe_validator")
        normalized.append(payload)
    payload = {
        "schema_id": "OC133_TOE_AUTONOMOUS_CAPABILITY_DEVELOPMENT_LEDGER_v1",
        "generated_at": generated_at,
        "status": "OPEN" if normalized else "PASS",
        "capability_development_total": len(normalized),
        "open_capability_development_total": sum(1 for row in normalized if row.get("status") != "PASS"),
        "zero_delta_creates_capability_work": True,
        "same_frontier_rerun_policy": "Repeated frontier actions become capability-development graph nodes; the supervisor must not rerun the identical action blindly.",
        "rows": normalized,
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def build_heartbeat(state: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "schema_id": "OC133_TOE_AUTONOMOUS_HEARTBEAT_v1",
        "generated_at": utc_now(),
        "status": state.get("status"),
        "current_promotion_gate": state.get("current_promotion_gate"),
        "latest_wave_id": state.get("latest_wave_id"),
        "current_graph_node_id": state.get("current_graph_node_id"),
        "active_executor": state.get("active_executor"),
        "validator_error_total": state.get("validator_error_total"),
        "last_validator_delta": state.get("last_validator_delta"),
        "elapsed_runtime_seconds": state.get("elapsed_runtime_seconds"),
        "last_commit_sha": state.get("last_commit_sha"),
        "next_escalation": state.get("next_escalation"),
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def write_outputs(root: Path, outputs: dict[Path, dict[str, Any]]) -> dict[str, Any]:
    files = {root / path: stable_json(payload) for path, payload in outputs.items()}
    return validation_result(files, write=True)


def commit_checkpoint(root: Path) -> dict[str, Any]:
    add_paths = [
        "operations/logion_release_mission/oc_core_1_3_3/OC133_ALL_DOMAIN_READINESS_COCKPIT.md",
        "operations/logion_release_mission/oc_core_1_3_3/OC133_ALL_DOMAIN_READINESS_SCORECARD.json",
        "operations/logion_release_mission/oc_core_1_3_3/OC133_ALL_DOMAIN_WORK_ORDERS.json",
        "operations/logion_release_mission/oc_core_1_3_3/OC133_GRAND_SCIENCE_LOOP_latest.json",
        "operations/logion_release_mission/oc_core_1_3_3/OC133_GRAND_SCIENCE_LOOP_latest.md",
        "operations/logion_release_mission/oc_core_1_3_3/OC133_GRAND_SCIENCE_LOOP_STATE.json",
        "operations/logion_release_mission/oc_core_1_3_3/toe_closure_factory",
        "content/generated",
        "releases/oc_core_1_3/editorial",
        "releases/oc_core_1_3/monograph/source/content/generated",
        "tools/oc133_toe_autonomous_supervisor.py",
        "tools/oc133_toe_closure_factory.py",
        "release_machine/tests/test_release_assembly_machine.py",
    ]
    checks = [
        factory.safe_run_command(root, [sys.executable, "-m", "py_compile", "tools/oc133_toe_autonomous_supervisor.py", "tools/oc133_toe_closure_factory.py"], 120),
        factory.safe_run_command(root, [sys.executable, "tools/oc133_toe_closure_factory.py", "--check"], 300),
    ]
    if any(row["returncode"] != 0 for row in checks):
        return {
            "status": "SKIPPED_CHECKS_FAILED",
            "checks": checks,
            "commit_sha": None,
        }
    add = factory.safe_run_command(root, ["git", "add", *add_paths], 120)
    diff = factory.safe_run_command(root, ["git", "diff", "--cached", "--quiet"], 120)
    if diff["returncode"] == 0:
        return {"status": "SKIPPED_NO_STAGED_CHANGES", "checks": checks, "git_add": add, "commit_sha": None}
    commit = factory.safe_run_command(root, ["git", "commit", "-m", "Advance r017 autonomous TOE closure supervisor"], 120)
    return {
        "status": "PASS" if commit["returncode"] == 0 else "FAIL",
        "checks": checks,
        "git_add": add,
        "git_commit": commit,
        "commit_sha": factory.git_head(root) if commit["returncode"] == 0 else None,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Autonomously supervise OC Core 1.3.3 r017 TOE closure waves.")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--until-r017-pass", action="store_true")
    parser.add_argument("--max-iterations", type=int, default=1, help="0 means unlimited/resumable.")
    parser.add_argument("--max-actions-per-iteration", type=int, default=12)
    parser.add_argument("--commit-checkpoints", action="store_true")
    parser.add_argument("--sleep-on-cooldown-seconds", type=int, default=300)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args(argv)
    if args.check:
        paths = [
            factory.FACTORY_DIR / SUPPORT_INDEX_NAME,
            factory.FACTORY_DIR / factory.SCIENTIFIC_FRONTIER_NAME,
            factory.FACTORY_DIR / factory.CAPABILITY_IMPLEMENTATION_REGISTRY_NAME,
            factory.FACTORY_DIR / BLOCKING_GRAPH_NAME,
            SUPERVISOR_DIR / STATE_NAME,
            SUPERVISOR_DIR / COCKPIT_NAME,
            SUPERVISOR_DIR / WAVE_LEDGER_NAME,
            SUPERVISOR_DIR / NEXT_ACTION_QUEUE_NAME,
            SUPERVISOR_DIR / ESCALATION_LEDGER_NAME,
            SUPERVISOR_DIR / CAPABILITY_DEVELOPMENT_LEDGER_NAME,
            SUPERVISOR_DIR / FRONTIER_HASHES_NAME,
            SUPERVISOR_DIR / COMMIT_LEDGER_NAME,
            SUPERVISOR_DIR / TERMINAL_VALIDATION_NAME,
            SUPERVISOR_DIR / HEARTBEAT_NAME,
        ]
        files = {
            ROOT / path: stable_json(read_json(ROOT / path))
            for path in paths
            if (ROOT / path).exists()
        }
        result = validation_result(files | {ROOT / path: files.get(ROOT / path, "") for path in paths if not (ROOT / path).exists()}, write=False)
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 1 if result["state"] != "PASS" else 0
    outputs = run_supervisor(ROOT, args)
    print(json.dumps(outputs[SUPERVISOR_DIR / COCKPIT_NAME], ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
