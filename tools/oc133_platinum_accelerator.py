from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPAIR_DIR = ROOT / "reviews" / "oc133_llm_cerberus" / "repair"
COCKPIT = REPAIR_DIR / "OC133_PLATINUM_ACCELERATOR_COCKPIT.json"
SUMMARY = ROOT / "reviews" / "oc133_llm_cerberus" / "OC133_LLM_CERBERUS_SUMMARY.json"
EVALUATE_LATEST = ROOT / "releases" / "oc_core_1_3_3" / "editorial" / "OC_CORE_1_3_3_RELEASE_SCORECARD_latest.json"
RUN_LEDGER = REPAIR_DIR / "OC133_AUTONOMOUS_RESEARCH_LOOP_LEDGER.json"
FINITE_REPORT = ROOT / "proofs" / "FINITE_MODEL_CHECKS_1_3_3.json"
VALIDATION_REPORT = ROOT / "reports" / "OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.json"
PRIVATE_BRIDGE_PACKET = REPAIR_DIR / "OC133_PRIVATE_BRIDGE_PACKET.sanitized.json"
PRIVATE_BRIDGE_SCHEMA = REPAIR_DIR / "OC133_PRIVATE_BRIDGE_PACKET_SCHEMA.json"


PRIVATE_BRIDGE_PACKET_SCHEMA_ID = "OC133_PUBLIC_PRIVATE_BRIDGE_PACKET_v1"
PRIVATE_BRIDGE_SCHEMA_ID = "OC133_PUBLIC_PRIVATE_BRIDGE_PACKET_SCHEMA_v1"
PRIVATE_BRIDGE_ALLOWED_HINT_FIELDS = [
    "hint_id",
    "profile",
    "role",
    "severity",
    "artifact_ref",
    "claim",
    "failure_mode",
    "required_repair",
    "rationale",
    "tags",
    "source_label",
]
PRIVATE_BRIDGE_FORBIDDEN_HINT_FIELDS = [
    "evidence",
    "evidence_ref",
    "evidence_refs",
    "release_evidence",
    "closure_evidence",
    "raw_output",
    "raw_output_ref",
    "private_ref",
    "private_path",
    "private_payload",
]


FRONTIER_REFS = [
    "tools/materialize_oc_core_1_3_3_v12_closure.py",
    "tools/oc133_autonomous_research_loop.py",
    "tools/oc133_capability_repair_executor.py",
    "tools/oc133_vulnerability_class_remediator.py",
    "tools/run_oc133_v12_cerberus.py",
    "tools/templates/OC133V12_hardened.lean",
    "tools/templates/run_finite_model_checks_hardened.py",
    "release_machine/oc133_v12.py",
    "formal/lean/OC133V12.lean",
    "proofs/finite_model_checks/OC133_FINITE_MODEL_INPUTS.json",
    "proofs/finite_model_checks/run_finite_model_checks.py",
    "claims/CLAIM_LEDGER_1_3_3.json",
    "review/OC_1_3_3_TOTAL_ATTACK_MATRIX.json",
    "docs/OC_1_3_3_PHENOMENON_COVERAGE_MATRIX.json",
    "reviews/oc133_llm_cerberus/OC133_LLM_CERBERUS_SUMMARY.json",
    "reviews/oc133_llm_cerberus/results",
    "reviews/oc133_llm_cerberus/repair/OC133_CERBERUS_REPAIR_WORK_ORDERS.json",
]

DETERMINISTIC_CHECKS = [
    {
        "stage": "python_compile",
        "cmd": [
            sys.executable,
            "-m",
            "py_compile",
            "tools/materialize_oc_core_1_3_3_v12_closure.py",
            "tools/oc133_platinum_accelerator.py",
            "tools/oc133_autonomous_research_loop.py",
            "tools/oc133_capability_repair_executor.py",
            "tools/oc133_vulnerability_class_remediator.py",
            "proofs/finite_model_checks/run_finite_model_checks.py",
            "validation/run_all.py",
        ],
        "timeout_attr": "compile_timeout",
        "write_scope": [],
    },
    {
        "stage": "finite_model_semantics",
        "cmd": [sys.executable, "proofs/finite_model_checks/run_finite_model_checks.py"],
        "timeout_attr": "finite_timeout",
        "write_scope": ["proofs/FINITE_MODEL_CHECKS_1_3_3.json", "proofs/finite_model_checks/FINITE_MODEL_REPLAY_REPORT.json"],
    },
    {
        "stage": "lean_named_target",
        "cmd": ["lake", "build", "OC133V12"],
        "timeout_attr": "lean_timeout",
        "write_scope": [".lake"],
    },
    {
        "stage": "validation_qa",
        "cmd": [sys.executable, "validation/run_all.py", "--qa-only"],
        "timeout_attr": "validation_timeout",
        "write_scope": ["reports/OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.json", "validation/numeric_predictions/OC133_NUMERIC_REPLAY_LOG.json"],
    },
]


PROFILE_TO_ROLES = {
    "v12_hybrid_operator_repair": {"dynamical_systems_reviewer", "theorem_theater_auditor"},
    "v12_lifecycle_invariant_repair": {"category_type_theory_reviewer", "claim_boundary_auditor", "clarity_didactic_reviewer"},
    "v12_empirical_quarantine_repair": {"empirical_statistician", "empirical_theater_auditor", "claim_boundary_auditor"},
    "v12_novelty_positioning_repair": {"prior_art_historian", "not_novel_attacker"},
    "v12_no_send_public_surface_repair": {"public_surface_auditor", "claim_boundary_auditor"},
    "v12_attack_matrix_binding_repair": {"hostile_journal_reviewer", "claim_boundary_auditor"},
    "v12_klevel_semantic_repair": {"formal_mathematician", "phenomenon_x_attacker", "theorem_theater_auditor"},
    "v12_minimality_tuple_repair": {"formal_mathematician", "theorem_theater_auditor"},
    "v12_kzero_semantic_repair": {"formal_mathematician", "theorem_theater_auditor"},
    "v12_k0_countermodel_repair": {"formal_mathematician", "clarity_didactic_reviewer"},
    "v12_lean_certificate_repair": {"reproducibility_auditor", "formal_mathematician"},
}

DEFAULT_FAST_ROLES = {
    "category_type_theory_reviewer",
    "dynamical_systems_reviewer",
    "empirical_statistician",
    "hostile_journal_reviewer",
    "claim_boundary_auditor",
    "clarity_didactic_reviewer",
    "public_surface_auditor",
    "reproducibility_auditor",
}


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def private_bridge_packet_schema() -> dict[str, Any]:
    hint_properties = {
        key: {"type": "string", "maxLength": 1200}
        for key in PRIVATE_BRIDGE_ALLOWED_HINT_FIELDS
        if key != "tags"
    }
    hint_properties["tags"] = {
        "type": "array",
        "maxItems": 20,
        "items": {"type": "string", "maxLength": 120},
    }
    return {
        "schema_id": PRIVATE_BRIDGE_SCHEMA_ID,
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "OC133 public-side sanitized private bridge packet",
        "description": "Public inbox contract for deterministic hint-only bridge ingest. The public accelerator never reads private roots or private scripts, and accepted rows are cockpit metadata only.",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "schema_id",
            "release_id",
            "version",
            "sanitized",
            "evidence_included",
            "candidate_work_order_hints",
        ],
        "properties": {
            "schema_id": {"const": PRIVATE_BRIDGE_PACKET_SCHEMA_ID},
            "release_id": {"const": "oc_core_1_3_3"},
            "version": {"const": "1.3.3"},
            "sanitized": {"const": True},
            "evidence_included": {"const": False},
            "producer": {"type": "string", "maxLength": 160},
            "packet_id": {"type": "string", "maxLength": 160},
            "candidate_work_order_hints": {
                "type": "array",
                "maxItems": 100,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": hint_properties,
                },
            },
        },
        "public_ingest_policy": {
            "packet_ref": rel(PRIVATE_BRIDGE_PACKET),
            "schema_ref": rel(PRIVATE_BRIDGE_SCHEMA),
            "accepted_surface": "candidate_work_order_hints only",
            "merge_target": "OC133_PLATINUM_ACCELERATOR_COCKPIT.json::private_bridge.candidate_work_order_hints",
            "release_evidence_policy": "NEVER_IMPORT_PRIVATE_RELEASE_EVIDENCE",
            "private_repo_policy": "NO_PRIVATE_ROOT_READS_NO_PRIVATE_SCRIPT_CALLS",
            "allowed_hint_fields": PRIVATE_BRIDGE_ALLOWED_HINT_FIELDS,
            "forbidden_hint_fields": PRIVATE_BRIDGE_FORBIDDEN_HINT_FIELDS,
        },
    }


def write_private_bridge_schema() -> None:
    write_json(PRIVATE_BRIDGE_SCHEMA, private_bridge_packet_schema())


def private_marker_present(value: Any) -> bool:
    if isinstance(value, str):
        lowered = value.replace("\\", "/").lower()
        return (
            ":/" in lowered
            or "estra-private-work" in lowered
            or "/logion/k" in lowered
        )
    if isinstance(value, list):
        return any(private_marker_present(item) for item in value)
    if isinstance(value, dict):
        return any(private_marker_present(item) for item in value.values())
    return False


def sanitize_bridge_hint(row: Any) -> tuple[dict[str, Any] | None, str | None]:
    if not isinstance(row, dict):
        return None, "hint_not_object"
    if any(key in row for key in PRIVATE_BRIDGE_FORBIDDEN_HINT_FIELDS):
        return None, "forbidden_evidence_field_present"
    sanitized: dict[str, Any] = {}
    for key in PRIVATE_BRIDGE_ALLOWED_HINT_FIELDS:
        value = row.get(key)
        if value is None:
            continue
        if key == "tags":
            if not isinstance(value, list):
                return None, "tags_not_list"
            tags = [str(item)[:120] for item in value if isinstance(item, (str, int, float))]
            if private_marker_present(tags):
                return None, "private_marker_present"
            sanitized[key] = tags[:20]
        elif isinstance(value, (str, int, float, bool)):
            text = str(value)[:1200]
            if private_marker_present(text):
                return None, "private_marker_present"
            sanitized[key] = text
        else:
            return None, f"{key}_not_scalar"
    if not sanitized:
        return None, "empty_hint"
    return sanitized, None


def private_bridge_metadata() -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "schema_id": "OC133_PUBLIC_PRIVATE_BRIDGE_INGEST_METADATA_v1",
        "request_stub": {
            "status": "PUBLIC_PACKET_INBOX_READY",
            "packet_ref": rel(PRIVATE_BRIDGE_PACKET),
            "schema_ref": rel(PRIVATE_BRIDGE_SCHEMA),
            "required_packet_schema_id": PRIVATE_BRIDGE_PACKET_SCHEMA_ID,
            "allowed_hint_fields": PRIVATE_BRIDGE_ALLOWED_HINT_FIELDS,
            "release_evidence_policy": "NEVER_IMPORT_PRIVATE_RELEASE_EVIDENCE",
            "private_repo_policy": "NO_PRIVATE_ROOT_READS_NO_PRIVATE_SCRIPT_CALLS",
        },
        "ingest_status": "PACKET_ABSENT",
        "candidate_work_order_hints": [],
        "accepted_hint_total": 0,
        "rejected_hint_total": 0,
        "rejection_reasons": {},
    }
    write_private_bridge_schema()
    if not PRIVATE_BRIDGE_PACKET.exists():
        return metadata
    metadata["packet_ref"] = rel(PRIVATE_BRIDGE_PACKET)
    metadata["packet_sha256"] = sha256_file(PRIVATE_BRIDGE_PACKET)
    packet = read_json(PRIVATE_BRIDGE_PACKET)
    if not packet:
        metadata["ingest_status"] = "PACKET_UNREADABLE_OR_NOT_OBJECT"
        return metadata
    if (
        packet.get("schema_id") != PRIVATE_BRIDGE_PACKET_SCHEMA_ID
        or packet.get("release_id") != "oc_core_1_3_3"
        or packet.get("version") != "1.3.3"
        or packet.get("sanitized") is not True
        or packet.get("evidence_included") is not False
    ):
        metadata["ingest_status"] = "PACKET_REJECTED_HEADER_POLICY"
        return metadata
    hints = packet.get("candidate_work_order_hints")
    if not isinstance(hints, list):
        metadata["ingest_status"] = "PACKET_REJECTED_HINTS_NOT_LIST"
        return metadata
    accepted = []
    rejection_reasons: dict[str, int] = {}
    for row in hints[:100]:
        sanitized, reason = sanitize_bridge_hint(row)
        if sanitized is None:
            reason = reason or "rejected"
            rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1
        else:
            accepted.append(sanitized)
    accepted.sort(key=lambda item: json.dumps(item, ensure_ascii=True, sort_keys=True))
    metadata["candidate_work_order_hints"] = accepted
    metadata["accepted_hint_total"] = len(accepted)
    metadata["rejected_hint_total"] = sum(rejection_reasons.values()) + max(0, len(hints) - 100)
    if len(hints) > 100:
        rejection_reasons["hint_limit_exceeded"] = len(hints) - 100
    metadata["rejection_reasons"] = dict(sorted(rejection_reasons.items()))
    metadata["ingest_status"] = "PACKET_INGESTED_HINTS_ONLY" if accepted else "PACKET_PRESENT_NO_ACCEPTED_HINTS"
    return metadata


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def frontier_hash(refs: list[str] | None = None) -> str:
    h = hashlib.sha256()
    for ref in sorted(refs or FRONTIER_REFS):
        path = ROOT / ref
        h.update(ref.encode("utf-8"))
        h.update(b"\0")
        if path.exists() and path.is_file():
            h.update(sha256_file(path).encode("ascii"))
        elif path.exists() and path.is_dir():
            child_hashes = []
            for child in sorted(path.rglob("*")):
                if child.is_file() and ".git" not in child.parts:
                    child_hashes.append(f"{rel(child)}:{sha256_file(child)}")
            h.update(hashlib.sha256("\n".join(child_hashes).encode("utf-8")).hexdigest().encode("ascii"))
        else:
            h.update(b"MISSING")
        h.update(b"\n")
    return h.hexdigest()


def command(cmd: list[str], *, timeout: int, stage: str = "", write_scope: list[str] | None = None) -> dict[str, Any]:
    started = time.time()
    frontier_before = frontier_hash()
    completed = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=timeout,
    )
    return {
        "stage": stage or "command",
        "cmd": cmd,
        "returncode": completed.returncode,
        "elapsed_seconds": round(time.time() - started, 3),
        "write_scope": write_scope or [],
        "frontier_hash_before": frontier_before,
        "frontier_hash_after": frontier_hash(),
        "dependency_policy": "sequential_if_write_scope_nonempty",
        "stdout_tail": completed.stdout[-2400:],
        "stderr_tail": completed.stderr[-2400:],
    }


def open_counts() -> dict[str, int]:
    summary = read_json(SUMMARY)
    return {
        "critical_open_total": int(summary.get("critical_open_total", 999) or 0),
        "high_open_total": int(summary.get("high_open_total", 999) or 0),
        "parse_failure_total": int(summary.get("parse_failure_total", 999) or 0),
        "execution_bad_total": int(summary.get("execution_bad_total", 999) or 0),
    }


def roles_with_open_findings() -> set[str]:
    roles: set[str] = set()
    result_dir = ROOT / "reviews" / "oc133_llm_cerberus" / "results"
    for path in sorted(result_dir.glob("*.json")):
        payload = read_json(path)
        critical = int(payload.get("critical_open_total", 0) or 0)
        high = int(payload.get("high_open_total", 0) or 0)
        if critical + high > 0:
            roles.add(str(payload.get("role") or path.stem))
    return roles


def selected_roles_from_work_orders() -> list[str]:
    work_orders = read_json(REPAIR_DIR / "OC133_CERBERUS_REPAIR_WORK_ORDERS.json")
    roles: set[str] = set()
    for row in work_orders.get("orders", []) if isinstance(work_orders.get("orders"), list) else []:
        profile = row.get("profile")
        roles.update(PROFILE_TO_ROLES.get(str(profile), set()))
        role = row.get("role")
        if isinstance(role, str) and role:
            roles.add(role)
    if not roles:
        roles.update(DEFAULT_FAST_ROLES)
    open_roles = roles_with_open_findings()
    if open_roles:
        roles = roles.intersection(open_roles) or open_roles
    return sorted(roles)


def current_gate_state() -> dict[str, Any]:
    payload = read_json(EVALUATE_LATEST)
    if payload.get("summary") and isinstance(payload.get("summary"), dict):
        payload = payload["summary"]
    return {
        "release_state": payload.get("release_state"),
        "master_verdict": payload.get("master_verdict") or payload.get("verdict"),
        "gate_counts": payload.get("gate_counts"),
        "publish_allowed": payload.get("publish_allowed"),
        "journal_submissions_allowed": payload.get("journal_submissions_allowed"),
    }


def build_role_arg(roles: list[str], *, full: bool) -> str:
    if full:
        return ""
    return ",".join(roles)


def skipped_command(stage: str, reason: str, dependency_stage: str | None = None) -> dict[str, Any]:
    return {
        "stage": stage,
        "cmd": [],
        "returncode": 0,
        "skipped": True,
        "skip_reason": reason,
        "dependency_stage": dependency_stage,
        "elapsed_seconds": 0,
        "write_scope": [],
        "frontier_hash_before": frontier_hash(),
        "stdout_tail": "",
        "stderr_tail": "",
    }


def previous_cockpit() -> dict[str, Any]:
    return read_json(COCKPIT)


def repair_cache_valid(current_frontier: str) -> bool:
    ledger = read_json(RUN_LEDGER)
    prior = previous_cockpit()
    return (
        ledger.get("verdict") == "PASS_AUTONOMOUS_REPAIR_APPLIED"
        and prior.get("frontier_hash_end") == current_frontier
        and int(ledger.get("unknown_repair_total", 1) or 0) == 0
        and int(ledger.get("repair_fail_total", 1) or 0) == 0
    )


def generated_surface_current(current_frontier: str) -> bool:
    prior = previous_cockpit()
    finite = read_json(FINITE_REPORT)
    validation = read_json(VALIDATION_REPORT)
    manifest = read_json(ROOT / "manifest.json")
    return (
        prior.get("frontier_hash_end") == current_frontier
        and manifest.get("release_id") == "oc_core_1_3_3"
        and manifest.get("version") == "1.3.3"
        and manifest.get("publish_allowed") is False
        and int(finite.get("failure_total", 1) or 0) == 0
        and int(finite.get("certificate_binding_failure_total", 1) or 0) == 0
        and validation.get("verdict") == "QA_REPLAY_COMPLETE_NOT_DOMAIN_VALIDATED"
    )


def run_deterministic_checks(args: argparse.Namespace, row: dict[str, Any]) -> bool:
    if args.skip_focused_checks:
        row["commands"].append(skipped_command("focused_checks", "disabled_by_cli"))
        return True
    ok = True
    failed_stage: str | None = None
    for spec in DETERMINISTIC_CHECKS:
        if not ok:
            row["commands"].append(skipped_command(spec["stage"], "dependency_failed", failed_stage))
            continue
        result = command(
            spec["cmd"],
            timeout=int(getattr(args, spec["timeout_attr"])),
            stage=spec["stage"],
            write_scope=list(spec.get("write_scope", [])),
        )
        row["commands"].append(result)
        if result["returncode"] != 0:
            ok = False
            failed_stage = spec["stage"]
    return ok


def iteration(iteration_id: int, args: argparse.Namespace) -> dict[str, Any]:
    row: dict[str, Any] = {
        "iteration": iteration_id,
        "no_send": True,
        "started_counts": open_counts(),
        "frontier_hash_start": frontier_hash(),
        "dependency_dag": [
            "capability_repair_apply",
            "materialize_sync",
            "python_compile",
            "finite_model_semantics",
            "lean_named_target",
            "validation_qa",
            "impacted_cerberus_roles",
            "post_cerberus_materialize_sync",
            "release_evaluate",
        ],
        "parallelism_policy": "Only Cerberus role calls may run in parallel; artifact-writing materialize/finite/validation/evaluate stages are serialized to avoid stale or racing evidence.",
        "commands": [],
    }
    repair_skipped = False
    if not args.force_repair_apply and repair_cache_valid(row["frontier_hash_start"]):
        repair_skipped = True
        row["commands"].append(skipped_command("capability_repair_apply", "cached_pass_autonomous_repair_for_unchanged_frontier"))
    else:
        row["commands"].append(command(
            [sys.executable, "tools/oc133_autonomous_research_loop.py", "--apply"],
            timeout=args.loop_timeout,
            stage="capability_repair_apply",
            write_scope=[
                "formal/lean/OC133V12.lean",
                "proofs",
                "claims",
                "review",
                "reviews/oc133_llm_cerberus/repair",
            ],
        ))
    if repair_skipped and not args.force_materialize and generated_surface_current(row["frontier_hash_start"]):
        row["commands"].append(skipped_command("materialize_sync", "cached_generated_surface_for_unchanged_frontier"))
    else:
        row["commands"].append(command(
            [sys.executable, "tools/materialize_oc_core_1_3_3_v12_closure.py"],
            timeout=args.materialize_timeout,
            stage="materialize_sync",
            write_scope=["formal", "proofs", "claims", "docs", "review", "reviews", "reports", "validation", "releases", "manifest.json", "checksums.txt", "ro-crate-metadata.jsonld"],
        ))
    checks_ok = run_deterministic_checks(args, row)
    roles = selected_roles_from_work_orders()
    row["selected_roles"] = roles
    row["selected_role_policy"] = "rerun only roles with open critical/high findings, expanded by current work-order profile mapping; use --full-cerberus for acceptance sweep"
    cerberus_ran = False
    if not checks_ok:
        row["commands"].append(skipped_command("impacted_cerberus_roles", "deterministic_checks_failed"))
    elif not args.skip_cerberus:
        role_arg = build_role_arg(roles, full=args.full_cerberus)
        cmd = [
            sys.executable,
            "tools/run_oc133_v12_cerberus.py",
            "--max-workers",
            str(args.max_workers),
            "--role-timeout",
            str(args.role_timeout),
        ]
        if role_arg:
            cmd.extend(["--roles", role_arg])
        row["commands"].append(command(cmd, timeout=args.cerberus_timeout, stage="impacted_cerberus_roles", write_scope=["reviews/oc133_llm_cerberus/results", "reviews/oc133_llm_cerberus/raw_v12", "reviews/oc133_llm_cerberus/OC133_LLM_CERBERUS_SUMMARY.json"]))
        cerberus_ran = True
        row["commands"].append(command(
            [sys.executable, "tools/materialize_oc_core_1_3_3_v12_closure.py"],
            timeout=args.materialize_timeout,
            stage="post_cerberus_materialize_sync",
            write_scope=["claims", "review", "reviews", "reports", "validation", "releases", "manifest.json", "checksums.txt", "ro-crate-metadata.jsonld"],
        ))
    else:
        row["commands"].append(skipped_command("impacted_cerberus_roles", "disabled_by_cli"))
    frontier_before_evaluate = frontier_hash()
    scorecard_exists = EVALUATE_LATEST.exists()
    counts_before_evaluate = open_counts()
    cerberus_zero_blockers = (
        counts_before_evaluate.get("critical_open_total") == 0
        and counts_before_evaluate.get("high_open_total") == 0
        and counts_before_evaluate.get("parse_failure_total") == 0
        and counts_before_evaluate.get("execution_bad_total") == 0
    )
    evaluate_needed = (
        args.force_evaluate
        or args.always_evaluate
        or not scorecard_exists
        or (cerberus_ran and cerberus_zero_blockers)
        or (row["frontier_hash_start"] != frontier_before_evaluate and not args.skip_cerberus and cerberus_zero_blockers)
    )
    row["evaluate_policy"] = {
        "scorecard_exists": scorecard_exists,
        "cerberus_ran": cerberus_ran,
        "cerberus_zero_blockers_before_evaluate": cerberus_zero_blockers,
        "counts_before_evaluate": counts_before_evaluate,
        "frontier_changed_before_evaluate": row["frontier_hash_start"] != frontier_before_evaluate,
        "skip_cerberus_fast_path_cached_evaluate": args.skip_cerberus and row["frontier_hash_start"] != frontier_before_evaluate and not (args.force_evaluate or args.always_evaluate),
        "skip_failed_cerberus_cached_evaluate": cerberus_ran and not cerberus_zero_blockers and not (args.force_evaluate or args.always_evaluate),
        "force_evaluate": args.force_evaluate or args.always_evaluate,
        "evaluate_needed": evaluate_needed,
    }
    if (checks_ok and evaluate_needed) or args.always_evaluate:
        row["commands"].append(command([sys.executable, "-m", "release_machine", "evaluate", "--release", "oc_core_1_3_3", "--channel", "all", "--mode", "dry-run"], timeout=args.evaluate_timeout, stage="release_evaluate", write_scope=["releases/oc_core_1_3_3"]))
    elif checks_ok:
        row["commands"].append(skipped_command("release_evaluate", "cached_scorecard_reused_for_unchanged_frontier"))
    else:
        row["commands"].append(skipped_command("release_evaluate", "deterministic_checks_failed"))
    row["ended_counts"] = open_counts()
    row["frontier_hash_end"] = frontier_hash()
    row["gate_state"] = current_gate_state()
    row["scientific_open_finding_command_total"] = sum(
        1
        for cmd in row["commands"]
        if cmd.get("stage") == "impacted_cerberus_roles"
        and cmd.get("returncode") != 0
        and row["ended_counts"].get("parse_failure_total") == 0
        and row["ended_counts"].get("execution_bad_total") == 0
    )
    row["command_failure_total"] = sum(
        1
        for cmd in row["commands"]
        if cmd.get("returncode") != 0
        and not (
            cmd.get("stage") == "impacted_cerberus_roles"
            and row["ended_counts"].get("parse_failure_total") == 0
            and row["ended_counts"].get("execution_bad_total") == 0
        )
    )
    row["blocker_delta"] = {
        key: row["ended_counts"].get(key, 0) - row["started_counts"].get(key, 0)
        for key in row["ended_counts"]
    }
    return row


def main() -> int:
    parser = argparse.ArgumentParser(description="Fast OC133 platinum no-send repair loop.")
    parser.add_argument("--iterations", type=int, default=1)
    parser.add_argument("--skip-cerberus", action="store_true")
    parser.add_argument("--full-cerberus", action="store_true")
    parser.add_argument("--max-workers", type=int, default=4)
    parser.add_argument("--role-timeout", type=int, default=900)
    parser.add_argument("--skip-focused-checks", action="store_true")
    parser.add_argument("--force-repair-apply", action="store_true")
    parser.add_argument("--force-materialize", action="store_true")
    parser.add_argument("--always-evaluate", action="store_true", help="Deprecated alias for --force-evaluate.")
    parser.add_argument("--force-evaluate", action="store_true", help="Run release evaluation even when the frontier hash did not change.")
    parser.add_argument("--print-full", action="store_true", help="Print the full cockpit JSON instead of a compact run summary.")
    parser.add_argument("--write-private-bridge-schema", action="store_true", help="Write the public sanitized private bridge packet schema and exit.")
    parser.add_argument("--compile-timeout", type=int, default=120)
    parser.add_argument("--finite-timeout", type=int, default=180)
    parser.add_argument("--lean-timeout", type=int, default=600)
    parser.add_argument("--validation-timeout", type=int, default=240)
    parser.add_argument("--materialize-timeout", type=int, default=900)
    parser.add_argument("--loop-timeout", type=int, default=1800)
    parser.add_argument("--cerberus-timeout", type=int, default=7200)
    parser.add_argument("--evaluate-timeout", type=int, default=600)
    args = parser.parse_args()
    if args.write_private_bridge_schema:
        write_private_bridge_schema()
        print(json.dumps({
            "schema_id": PRIVATE_BRIDGE_SCHEMA_ID,
            "schema_ref": rel(PRIVATE_BRIDGE_SCHEMA),
            "packet_ref": rel(PRIVATE_BRIDGE_PACKET),
        }, ensure_ascii=False, indent=2))
        return 0

    iterations = []
    start = open_counts()
    frontier_start = frontier_hash()
    for idx in range(1, max(1, args.iterations) + 1):
        item = iteration(idx, args)
        iterations.append(item)
        if (
            item["ended_counts"]["critical_open_total"] == 0
            and item["ended_counts"]["high_open_total"] == 0
            and item["ended_counts"]["parse_failure_total"] == 0
            and item["ended_counts"]["execution_bad_total"] == 0
            and item["gate_state"].get("master_verdict") == "PASS"
        ):
            break

    payload = {
        "schema_id": "OC133_PLATINUM_ACCELERATOR_COCKPIT_v1",
        "release_id": "oc_core_1_3_3",
        "version": "1.3.3",
        "no_send": True,
        "publication_forbidden": True,
        "goal": "OC_CORE_1_3_3_10_10_READY_NO_SEND",
        "strategy": "capability repair first, one materialize sync, serialized dependency-aware deterministic checks, rerun only impacted Cerberus roles unless full suite is requested",
        "frontier_hash_start": frontier_start,
        "frontier_hash_end": frontier_hash(),
        "start_counts": start,
        "end_counts": open_counts(),
        "iteration_total": len(iterations),
        "iterations": iterations,
        "gate_state": current_gate_state(),
        "private_bridge": private_bridge_metadata(),
    }
    payload["verdict"] = (
        "PLATINUM_READY_NO_SEND"
        if payload["end_counts"]["critical_open_total"] == 0
        and payload["end_counts"]["high_open_total"] == 0
        and payload["end_counts"]["parse_failure_total"] == 0
        and payload["end_counts"]["execution_bad_total"] == 0
        and payload["gate_state"].get("master_verdict") == "PASS"
        else "CONTINUE_AUTONOMOUS_HARDENING"
    )
    write_json(COCKPIT, payload)
    if args.print_full:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        compact = {
            "schema_id": payload["schema_id"],
            "release_id": payload["release_id"],
            "version": payload["version"],
            "verdict": payload["verdict"],
            "no_send": payload["no_send"],
            "iteration_total": payload["iteration_total"],
            "end_counts": payload["end_counts"],
            "gate_state": payload["gate_state"],
            "private_bridge_ingest_status": payload["private_bridge"]["ingest_status"],
            "private_bridge_accepted_hint_total": payload["private_bridge"]["accepted_hint_total"],
            "cockpit_ref": rel(COCKPIT),
            "last_iteration_command_failure_total": iterations[-1].get("command_failure_total") if iterations else None,
        }
        print(json.dumps(compact, ensure_ascii=False, indent=2))
    return 0 if payload["verdict"] == "PLATINUM_READY_NO_SEND" else 1


if __name__ == "__main__":
    raise SystemExit(main())
