from __future__ import annotations

import argparse
import ast
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_ID = "OC133_EMPIRICAL_CAPABILITY_REGISTRY_v1"
RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
CAPABILITY_OWNER = "Research/EmpiricalScience"
REPORT_JSON_REL = "reports/OC_CORE_1_3_3_EMPIRICAL_CAPABILITY_REGISTRY.json"
REPORT_MD_REL = "reports/OC_CORE_1_3_3_EMPIRICAL_CAPABILITY_REGISTRY.md"

HARVESTER_RUN_REPORT_REL = "reports/OC_CORE_1_3_3_HARVESTER_RUN.json"
EXECUTOR_RUN_REPORT_REL = "reports/OC_CORE_1_3_3_DOMAIN_EVIDENCE_EXECUTOR_RUN.json"
PLANNER_RUN_REPORT_REL = "reports/OC_CORE_1_3_3_ACQUISITION_PLANNER_RUN.json"
GRAND_EMPIRICAL_REPORT_REL = "reports/OC_CORE_1_3_3_GRAND_EMPIRICAL_REPORT.json"

EMPIRICAL_OWNERS = {
    "Research/EmpiricalScience",
    "Logion Research/EmpiricalScience",
    "Logion IT/Research",
}

RESOURCE_CLASS_RANK = {
    "factory": 3,
    "harvester": 2,
    "executor": 1,
    "planner": 0,
}

NO_SEND_LOCKS = {
    "no_send": True,
    "publish_allowed": False,
    "journal_submissions_allowed": False,
    "external_network_allowed": False,
    "automatic_dispatch_allowed": False,
    "owner_approval_required": True,
}

ALWAYS_INCLUDE_FACTORIES = {
    "oc133_grand_empirical_evidence_factory.py",
    "oc133_biology_ncbi_benchmark_factory.py",
    "oc133_systems_wdi_benchmark_factory.py",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def int_field(payload: dict[str, Any] | None, *keys: str) -> int:
    if not isinstance(payload, dict):
        return 0
    for key in keys:
        value = payload.get(key)
        if isinstance(value, bool):
            continue
        if isinstance(value, int):
            return value
    return 0


def normalize_ref(value: Any) -> str:
    return str(value).replace("\\", "/")


def _eval_constant_string(expr: ast.AST, constants: dict[str, str]) -> str | None:
    if isinstance(expr, ast.Constant) and isinstance(expr.value, str):
        return expr.value
    if isinstance(expr, ast.Name):
        return constants.get(expr.id)
    if isinstance(expr, ast.BinOp) and isinstance(expr.op, ast.Add):
        left = _eval_constant_string(expr.left, constants)
        if left is None:
            return None
        right = _eval_constant_string(expr.right, constants)
        if right is None:
            return None
        return left + right
    if isinstance(expr, ast.JoinedStr):
        parts: list[str] = []
        for value in expr.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                parts.append(value.value)
            elif isinstance(value, ast.FormattedValue):
                inner = _eval_constant_string(value.value, constants)
                if inner is None:
                    return None
                parts.append(inner)
            else:
                return None
        return "".join(parts)
    return None


def parse_module_constants(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    expressions: dict[str, ast.AST] = {}
    constants: dict[str, str] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            continue
        target = node.targets[0].id
        if not target.isidentifier():
            continue
        expressions[target] = node.value
    changed = True
    while changed:
        changed = False
        for name, expr in list(expressions.items()):
            if name in constants:
                continue
            value = _eval_constant_string(expr, constants)
            if value is None:
                continue
            constants[name] = value
            changed = True
    return constants


def _has_empirical_owner(metadata: dict[str, str]) -> bool:
    owner = metadata.get("CAPABILITY_OWNER", "")
    if owner in EMPIRICAL_OWNERS:
        return True
    if owner.startswith("Research/Empirical"):
        return True
    return False


def _is_empirical_factory(path: Path, metadata: dict[str, str]) -> bool:
    name = path.name
    if name == "oc133_empirical_capability_registry.py":
        return False
    if name in ALWAYS_INCLUDE_FACTORIES:
        return True
    if _has_empirical_owner(metadata):
        return True
    schema_id = metadata.get("SCHEMA_ID", "").upper()
    if "EMPIRICAL" in schema_id and "MODERN" not in schema_id:
        return True
    return name.startswith("oc133_") and ("grand_empirical" in name or "ncbi" in name or "wdi" in name)


def discover_factories(root: Path) -> list[Path]:
    tools = root / "tools"
    if not tools.exists():
        return []
    out = []
    for path in sorted(tools.glob("*_factory.py")):
        if not path.is_file():
            continue
        metadata = parse_module_constants(path)
        if _is_empirical_factory(path, metadata):
            out.append(path)
    return out


def discover_harvesters(root: Path) -> list[Path]:
    path = root / "validation" / "heldout" / "harvesters"
    if not path.exists():
        return []
    out = []
    for file in sorted(path.glob("*_harvester.py")):
        if not file.is_file():
            continue
        metadata = parse_module_constants(file)
        if _has_empirical_owner(metadata):
            out.append(file)
            continue
        # keep local harvested modules even when owner metadata is unavailable
        out.append(file)
    return out


def discover_executors(root: Path) -> list[Path]:
    path = root / "validation" / "heldout" / "domain_evidence"
    if not path.exists():
        return []
    out = []
    for file in sorted(path.glob("*_evidence_executor.py")):
        if not file.is_file():
            continue
        metadata = parse_module_constants(file)
        if _has_empirical_owner(metadata):
            out.append(file)
            continue
        out.append(file)
    return out


def discover_planners(root: Path) -> list[Path]:
    tools = root / "tools"
    if not tools.exists():
        return []
    out = []
    for file in sorted(tools.glob("oc133_*_acquisition_planner.py")):
        if file.name == "oc133_empirical_capability_registry.py":
            continue
        metadata = parse_module_constants(file)
        if _has_empirical_owner(metadata):
            out.append(file)
            continue
        # retain local acquisition-planner scripts that target empirical sources
        out.append(file)
    return out


def _row_payload_from_runner_report(
    root: Path,
    component_type: str,
    component_ref: str,
) -> dict[str, Any]:
    if component_type == "harvester":
        report = read_json(root / HARVESTER_RUN_REPORT_REL)
        key = "harvester_ref"
        payload_keys = ("parsed_payload",)
    elif component_type == "executor":
        report = read_json(root / EXECUTOR_RUN_REPORT_REL)
        key = "executor_ref"
        payload_keys = ("effective_payload", "parsed_payload")
    else:
        report = read_json(root / PLANNER_RUN_REPORT_REL)
        key = "planner_ref"
        payload_keys = ("parsed_payload",)
    rows = report.get("results", [])
    if not isinstance(rows, list):
        return {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        if normalize_ref(row.get(key)) == component_ref:
            for payload_key in payload_keys:
                payload = row.get(payload_key)
                if isinstance(payload, dict):
                    return payload
    return {}


def _candidate_factory_payloads(root: Path, constants: dict[str, str], module_name: str) -> list[dict[str, Any]]:
    if module_name == "oc133_grand_empirical_evidence_factory.py":
        payload = read_json(root / GRAND_EMPIRICAL_REPORT_REL)
        return [payload] if payload else []
    candidates: list[dict[str, Any]] = []
    for key, value in sorted(constants.items()):
        if not isinstance(value, str):
            continue
        if ".json" not in value.lower():
            continue
        if "REPORT" not in key and "REPORT" not in key.upper():
            continue
        payload = read_json(root / value)
        if payload:
            candidates.append(payload)
    if candidates:
        return candidates
    for key, value in sorted(constants.items()):
        if not isinstance(value, str):
            continue
        if not value.endswith(".json"):
            continue
        payload = read_json(root / value)
        if payload:
            candidates.append(payload)
    return candidates


def _pick_factory_payload(root: Path, path: Path, constants: dict[str, str]) -> dict[str, Any]:
    candidates = _candidate_factory_payloads(root, constants, path.name)
    for payload in candidates:
        if int_field(payload, "open_blocker_total", "blocker_total", "blocked_domain_total"):
            return payload
    if candidates:
        return candidates[0]
    return {}


def _extract_blocker_fields(payload: dict[str, Any] | None) -> dict[str, int]:
    if not isinstance(payload, dict):
        return {"open_blocker_total": 0, "blocker_total": 0, "blocked_domain_total": 0}
    open_blockers = int_field(
        payload,
        "open_blocker_total",
        "open_blockers",
        "blocked_total",
        "blocked",
    )
    blocker_total = int_field(payload, "blocker_total", "open_blocker_total", "open_blockers", "blocked_total")
    blocked_domain_total = int_field(
        payload,
        "blocked_domain_total",
        "blocked_domain_count",
        "blocked_total_domains",
    )
    return {
        "open_blocker_total": open_blockers,
        "blocker_total": blocker_total,
        "blocked_domain_total": blocked_domain_total,
    }


def _extract_pack_fields(payload: dict[str, Any] | None) -> dict[str, int]:
    if not isinstance(payload, dict):
        return {"candidate_pack_total": 0, "valid_pack_total": 0, "blocked_candidate_pack_total": 0}
    candidate = int_field(
        payload,
        "candidate_pack_total",
        "candidate_total",
        "task_total",
        "protocol_total",
    )
    valid = int_field(
        payload,
        "valid_pack_total",
        "valid_candidate_pack_total",
        "valid_under_current_grand_schema_total",
    )
    blocked_candidate = int_field(
        payload,
        "blocked_candidate_pack_total",
        "blocked_pack_total",
        "blocked_total",
    )
    return {
        "candidate_pack_total": candidate,
        "valid_pack_total": valid,
        "blocked_candidate_pack_total": blocked_candidate,
    }


def _is_blocked(payload: dict[str, Any] | None) -> bool:
    if not isinstance(payload, dict):
        return False
    verdict = str(payload.get("verdict", "")).upper()
    blockers = _extract_blocker_fields(payload)
    if blockers["open_blocker_total"] > 0:
        return True
    if blockers["blocker_total"] > 0:
        return True
    if blockers["blocked_domain_total"] > 0:
        return True
    candidate = _extract_pack_fields(payload)
    return candidate["candidate_pack_total"] > 0 and candidate["valid_pack_total"] == 0 and verdict.startswith("BLOCKED")


def _unblock_value(payload: dict[str, Any] | None) -> int:
    blockers = _extract_blocker_fields(payload)
    packs = _extract_pack_fields(payload)
    total = max(blockers["open_blocker_total"], blockers["blocker_total"])
    if total == 0:
        total = blockers["blocked_domain_total"]
    return (
        total * 100
        + packs["blocked_candidate_pack_total"] * 25
        + max(packs["candidate_pack_total"] - packs["valid_pack_total"], 0)
    )


def _command_for_component(root: Path, path: Path, component_type: str) -> str:
    component_ref = rel(root, path)
    if component_type == "harvester":
        return f"python {component_ref} --write --offline --allow-blocked-exit-zero"
    if component_type in {"executor", "planner"}:
        return f"python {component_ref} --write --allow-blocked-exit-zero"
    return f"python {component_ref} --write"


def _next_action(component_type: str, is_blocked: bool) -> str:
    if is_blocked:
        if component_type == "factory":
            return "Refresh empirical factory outputs after removing blockers."
        if component_type == "harvester":
            return "Run harvester offline and reconcile blocker causes."
        if component_type == "executor":
            return "Run evidence executor to regenerate candidate packs and gate status."
        return "Run acquisition planner, then schedule bounded protocol updates."
    return "Monitor for upstream input readiness; rerun to re-evaluate blockade."


def _compute_degradation_notes(component_type: str, blocked: bool, payload: dict[str, Any]) -> list[str]:
    notes = [
        "Registry mode is dispatcher-only: no component command is executed by this layer.",
        "Network access is locked off; only local reports, snapshots, protocols, and runner summaries are read.",
    ]
    if component_type == "harvester":
        notes.append("Harvester dispatch is constrained to offline/snapshot reruns until owner unlock.")
    elif component_type == "executor":
        notes.append("Executor dispatch uses existing effective payload summaries; heavy evidence regeneration is queued, not run.")
    elif component_type == "planner":
        notes.append("Planner dispatch produces protocol work orders only; acquisition is not launched automatically.")
    elif component_type == "factory":
        notes.append("Factory dispatch is report-refresh guidance only; upstream blocker removal remains manual/owned.")
    if blocked:
        notes.append("Blocked status means compute should degrade to blocker reconciliation before any full rerun.")
    elif not payload:
        notes.append("No local payload was found, so priority is degraded to discovery/monitoring.")
    else:
        notes.append("No open blocker was detected locally; keep the row in low-priority monitoring.")
    return notes


def _build_component_row(root: Path, path: Path, component_type: str) -> dict[str, Any]:
    component_ref = rel(root, path)
    metadata = parse_module_constants(path)
    owner = metadata.get("CAPABILITY_OWNER", "Research/EmpiricalScience")
    if component_type == "factory":
        payload = _pick_factory_payload(root, path, metadata)
    else:
        payload = _row_payload_from_runner_report(root, component_type, component_ref)
    if not payload and component_type == "planner":
        report_rel = metadata.get("PLAN_REL") or metadata.get("PLAN_JSON_REL")
        if report_rel:
            payload = read_json(root / report_rel)
    blockers = _extract_blocker_fields(payload)
    packs = _extract_pack_fields(payload)
    blocked = _is_blocked(payload)
    unblock_value = _unblock_value(payload)
    return {
        "component_ref": component_ref,
        "component_type": component_type,
        "resource_class": component_type,
        "resource_class_rank": RESOURCE_CLASS_RANK.get(component_type, 0),
        "command": _command_for_component(root, path, component_type),
        "capability_owner": owner,
        "verdict": payload.get("verdict") if isinstance(payload, dict) else None,
        "open_blocker_total": blockers["open_blocker_total"],
        "blocker_total": blockers["blocker_total"],
        "blocked_domain_total": blockers["blocked_domain_total"],
        "candidate_pack_total": packs["candidate_pack_total"],
        "valid_pack_total": packs["valid_pack_total"],
        "blocked_candidate_pack_total": packs["blocked_candidate_pack_total"],
        "is_blocked": blocked,
        "unblock_value": unblock_value,
        "next_action": _next_action(component_type, blocked),
        "no_send": NO_SEND_LOCKS["no_send"],
        "publish_allowed": NO_SEND_LOCKS["publish_allowed"],
        "journal_submissions_allowed": NO_SEND_LOCKS["journal_submissions_allowed"],
        "external_network_allowed": NO_SEND_LOCKS["external_network_allowed"],
        "automatic_dispatch_allowed": NO_SEND_LOCKS["automatic_dispatch_allowed"],
        "compute_degradation_notes": _compute_degradation_notes(component_type, blocked, payload),
        "effective_payload": payload if isinstance(payload, dict) else {},
        "payload_ref": None,
    }


def _sort_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        rows,
        key=lambda row: (-int(row["unblock_value"]), -int(row["resource_class_rank"]), row["component_ref"]),
    )


def build_payload(root: Path, *, write: bool) -> dict[str, Any]:
    components: list[dict[str, Any]] = []
    components.extend(_build_component_row(root, path, "factory") for path in discover_factories(root))
    components.extend(_build_component_row(root, path, "harvester") for path in discover_harvesters(root))
    components.extend(_build_component_row(root, path, "executor") for path in discover_executors(root))
    components.extend(_build_component_row(root, path, "planner") for path in discover_planners(root))
    components = _sort_rows(components)
    queue: list[dict[str, Any]] = []
    for idx, row in enumerate(components, start=1):
        queue.append(
            {
                "action_id": f"OC133-ECQ-{idx:03d}",
                "position": idx,
                "component_ref": row["component_ref"],
                "component_type": row["component_type"],
                "resource_class": row["resource_class"],
                "resource_class_rank": row["resource_class_rank"],
                "unblock_value": row["unblock_value"],
                "next_action": row["next_action"],
            }
        )
    blocked_total = sum(1 for row in components if row["is_blocked"])
    blocked_component_total = len([row for row in components if row["is_blocked"]])
    compute_degradation_notes = [
        "Capability registry ran in local-read dispatcher mode and did not call component commands.",
        "No-send and automatic-dispatch locks keep all next actions as queue entries, not executions.",
        "Rows with blockers are ranked for blocker reconciliation before compute-heavy reruns.",
        "Rows without local payloads or open blockers degrade to monitoring until upstream inputs change.",
    ]
    payload: dict[str, Any] = {
        "schema_id": SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "capability_owner": CAPABILITY_OWNER,
        "component_total": len(components),
        "component_type_totals": {
            "factory": len(discover_factories(root)),
            "harvester": len(discover_harvesters(root)),
            "executor": len(discover_executors(root)),
            "planner": len(discover_planners(root)),
        },
        "blocked_component_total": blocked_component_total,
        "blocked_component_refs": [row["component_ref"] for row in components if row["is_blocked"]],
        "command_failure_total": 0,
        "components": components,
        "next_action_queue": queue,
        "next_action_total": len(queue),
        "no_send_locks": dict(NO_SEND_LOCKS),
        "no_send": NO_SEND_LOCKS["no_send"],
        "publish_allowed": NO_SEND_LOCKS["publish_allowed"],
        "journal_submissions_allowed": NO_SEND_LOCKS["journal_submissions_allowed"],
        "external_network_allowed": NO_SEND_LOCKS["external_network_allowed"],
        "automatic_dispatch_allowed": NO_SEND_LOCKS["automatic_dispatch_allowed"],
        "compute_degradation_notes": compute_degradation_notes,
        "verdict": "CAPABILITY_REBALANCE_BLOCKED" if blocked_total else "EMPIRICAL_CAPABILITY_QUEUE_OPEN",
        "closure_policy": "Registry layer is dispatcher-only: it does not alter evidence payloads, only emits no-send ordered operational guidance.",
    }
    if write:
        write_json(root / REPORT_JSON_REL, payload)
        write_markdown(root / REPORT_MD_REL, payload)
    return payload


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# OC Core 1.3.3 Empirical Capability Registry",
        "",
        f"Verdict: `{payload['verdict']}`",
        f"Total components discovered: `{payload['component_total']}`",
        f"Blocked components: `{payload['blocked_component_total']}`",
        f"Factory rows: `{payload['component_type_totals']['factory']}`",
        f"Harvester rows: `{payload['component_type_totals']['harvester']}`",
        f"Executor rows: `{payload['component_type_totals']['executor']}`",
        f"Planner rows: `{payload['component_type_totals']['planner']}`",
        f"No-send lock: `{payload['no_send']}`",
        f"External network allowed: `{payload['external_network_allowed']}`",
        f"Automatic dispatch allowed: `{payload['automatic_dispatch_allowed']}`",
        "",
        "This registry does not execute external network calls; it only reads local artifacts and emits a deterministic no-send queue.",
        "",
        "## Cockpit Locks",
        "",
        "| Lock | Value |",
        "| --- | ---: |",
    ]
    for key, value in payload["no_send_locks"].items():
        lines.append(f"| `{key}` | `{value}` |")
    lines.extend(
        [
            "",
            "## Compute-Degradation Notes",
            "",
        ]
    )
    for note in payload["compute_degradation_notes"]:
        lines.append(f"- {note}")
    lines.extend(
        [
            "",
            "## Ranked Components",
            "",
            "| Position | Resource Class | Component | Blockers | Unblock Value | Next Action |",
            "| --- | --- | --- | ---: | ---: | --- |",
        ]
    )
    for row in payload["next_action_queue"]:
        row_ref = row["component_ref"]
        component_row = next(item for item in payload["components"] if item["component_ref"] == row_ref)
        blockers = max(
            int(component_row["open_blocker_total"]),
            int(component_row["blocker_total"]),
            int(component_row["blocked_domain_total"]),
        )
        lines.append(
            f"| `{row['action_id']}` | `{row['resource_class']}` | `{row_ref}` | "
            f"`{blockers}` | `{row['unblock_value']}` | `{row['next_action']}` |"
        )
    lines.extend(
        [
            "",
            "## Next-Action Queue",
            "",
            "| Action ID | Position | Component | Command |",
            "| --- | ---: | --- | --- |",
        ]
    )
    for row in payload["next_action_queue"]:
        component_row = next(item for item in payload["components"] if item["component_ref"] == row["component_ref"])
        lines.append(
            f"| `{row['action_id']}` | `{row['position']}` | `{row['component_ref']}` | "
            f"`{component_row['command']}` |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="OC133 empirical capability registry/dispatcher")
    parser.add_argument("--root", default=str(repo_root()))
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    payload = build_payload(Path(args.root).resolve(), write=args.write)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if payload["command_failure_total"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
