from __future__ import annotations

import argparse
import copy
import json
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from release_machine import oc133_platinum  # noqa: E402


EXECUTION_LEDGER_REL = f"{oc133_platinum.MISSION_DIR_REL}/OC133_ALL_DOMAIN_EXECUTION_LEDGER.json"
EXECUTION_LEDGER = ROOT / EXECUTION_LEDGER_REL
COVERAGE_LANE_QUEUE_REL = "reports/OC_CORE_1_3_3_MODERN_SCIENCE_COVERAGE_LANE_QUEUE.json"
COVERAGE_LANE_TELEMETRY_REL = "reports/OC_CORE_1_3_3_MODERN_SCIENCE_COVERAGE_LANE_TELEMETRY.json"
COVERAGE_REGISTER_REL = "comparators/modern_science/OC133_MODERN_SCIENCE_COVERAGE_REGISTER.json"
COVERAGE_WORK_ORDERS_REL = "benchmarks/modern_science/OC133_MODERN_SCIENCE_COVERAGE_WORK_ORDERS.json"
COVERAGE_LANE_DISPATCHER_REL = "benchmarks/modern_science/coverage_lane_dispatcher.py"
DOMAIN_LOCAL_COVERAGE_ROOT_REL = "validation/heldout/grand_science"
DOMAIN_LOCAL_COVERAGE_WORK_ORDER_GLOB = "*/coverage_work_orders/*COVERAGE_WORK_ORDERS.json"
DOMAIN_LOCAL_COVERAGE_ARTIFACT_GLOB = "*/coverage_work_orders/**/*.json"
ALL_DOMAIN_ORDERING_POLICY = (
    "no-send/safety, blocker severity, gate unblock value, dependency unblock value, stable ID"
)

SEVERITY_RANK = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}

NO_SEND_LOCKS = {
    "no_send": True,
    "public_release_action_allowed": False,
    "publish_allowed": False,
    "push_allowed": False,
    "registry_write_allowed": False,
    "journal_submission_allowed": False,
    "email_allowed": False,
    "coverage_closure_allowed": False,
    "broad_modern_science_superiority_allowed": False,
    "all_domain_scientific_closure_allowed": False,
}

FORMAL_CLAIM_ARTIFACTS = [
    "claims/CLAIM_LEDGER_1_3_3.json",
    oc133_platinum.GRAND_TOE_FORMAL_OBLIGATION_LEDGER_REL,
    oc133_platinum.GRAND_PROMOTION_CONTRACT_REL,
    "proofs/THEOREM_INVENTORY_1_3_3.json",
    "proofs/proof_sheets/",
    "formal/lean/",
    "proofs/FINITE_MODEL_CHECKS_1_3_3.json",
]

MODERN_SCIENCE_ARTIFACTS = [
    oc133_platinum.MODERN_SCIENCE_COMPARATOR_REGISTER_REL,
    COVERAGE_REGISTER_REL,
    COVERAGE_WORK_ORDERS_REL,
    COVERAGE_LANE_QUEUE_REL,
    "benchmarks/modern_science/OC133_MODERN_SCIENCE_BENCHMARK_LANES.json",
    "reports/OC_CORE_1_3_3_MODERN_SCIENCE_SUPERIORITY_REPORT.json",
]

COVERAGE_LANE_ARTIFACTS = [
    COVERAGE_REGISTER_REL,
    COVERAGE_WORK_ORDERS_REL,
    COVERAGE_LANE_QUEUE_REL,
    COVERAGE_LANE_TELEMETRY_REL,
    "benchmarks/modern_science/protocols/",
    "comparators/modern_science/source_capsules/",
    "validation/heldout/grand_science/",
]


PROFILE_BY_CAPABILITY = {
    "Research/FormalScience": "v12_grand_formal_science_research_program",
    "Research/EmpiricalScience": "v12_all_domain_empirical_readiness_repair",
    "Research/PriorArt": "v12_modern_science_comparator_research_program",
    "Review/ClaimBoundary": "v12_claim_boundary_overclaim_repair",
    "Publication/JournalPackages": "v12_journal_package_readiness_repair",
}


def display_command(argv: list[str]) -> str:
    return " ".join("python" if item == sys.executable else item for item in argv)


def python_argv(*args: str) -> list[str]:
    return ["python", *args]


def runtime_argv(argv: list[Any]) -> list[str]:
    result = [str(item) for item in argv]
    if result and result[0] == "python":
        result[0] = sys.executable
    return result


def sanitized_recorded_argv(argv: list[Any]) -> list[str]:
    return ["python" if str(item) == sys.executable else str(item) for item in argv]


def no_send_safety_rank(row: dict[str, Any]) -> int:
    locks = row.get("no_send_locks", {})
    if not isinstance(locks, dict):
        locks = {}
    locked = locks.get("no_send", row.get("no_send")) is True
    forbidden_keys = [key for key in NO_SEND_LOCKS if key != "no_send"]
    forbidden_closed = all(locks.get(key, NO_SEND_LOCKS[key]) is False for key in forbidden_keys)
    return 0 if locked and forbidden_closed else 1


def ranking_for(
    *,
    stable_id: str,
    severity: str,
    gate_unblock_value: int,
    dependency_unblock_value: int,
    no_send_rank: int = 0,
) -> dict[str, Any]:
    return {
        "policy": ALL_DOMAIN_ORDERING_POLICY,
        "no_send_safety_rank": no_send_rank,
        "blocker_severity_rank": SEVERITY_RANK.get(severity, 99),
        "gate_unblock_value": gate_unblock_value,
        "dependency_unblock_value": dependency_unblock_value,
        "stable_id": stable_id,
    }


def work_order_sort_key(row: dict[str, Any]) -> tuple[int, int, int, int, int, int, str]:
    ranking = row.get("ranking", {})
    return (
        int(ranking.get("no_send_safety_rank", no_send_safety_rank(row))),
        int(ranking.get("blocker_severity_rank", SEVERITY_RANK.get(str(row.get("severity", "")), 99))),
        int(ranking.get("domain_local_evidence_priority_rank", 50)),
        int(ranking.get("domain_local_missing_predicate_count", 999)),
        -int(ranking.get("gate_unblock_value", 0)),
        -int(ranking.get("dependency_unblock_value", 0)),
        str(ranking.get("stable_id", row.get("stable_id", row.get("work_order_id", "")))),
    )


def normalize_predicates(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    if isinstance(value, str) and value:
        return [value]
    return []


def rel_ref(path: Path, root: Path = ROOT) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def walk_values(value: Any) -> list[Any]:
    values = [value]
    if isinstance(value, dict):
        for item in value.values():
            values.extend(walk_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(walk_values(item))
    return values


def walk_dicts(value: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if isinstance(value, dict):
        rows.append(value)
        for item in value.values():
            rows.extend(walk_dicts(item))
    elif isinstance(value, list):
        for item in value:
            rows.extend(walk_dicts(item))
    return rows


def nested_dict(value: Any, *keys: str) -> dict[str, Any]:
    current = value
    for key in keys:
        if not isinstance(current, dict):
            return {}
        current = current.get(key)
    return current if isinstance(current, dict) else {}


def truthy_key(payloads: list[dict[str, Any]], keys: set[str]) -> bool:
    for payload in payloads:
        for row in walk_dicts(payload):
            for key in keys:
                if row.get(key) is True:
                    return True
    return False


def nonempty_key(payloads: list[dict[str, Any]], keys: set[str]) -> bool:
    for payload in payloads:
        for row in walk_dicts(payload):
            for key in keys:
                value = row.get(key)
                if value not in (None, "", [], {}):
                    return True
    return False


def status_text(payloads: list[dict[str, Any]]) -> str:
    fields = []
    for payload in payloads:
        for key in (
            "lane_status",
            "status",
            "status_code",
            "current_status",
            "current_evidence_status",
            "pack_status",
            "verdict",
        ):
            value = payload.get(key)
            if isinstance(value, str):
                fields.append(value)
        current = payload.get("current_evidence_status")
        if isinstance(current, dict):
            fields.extend(str(current.get(key, "")) for key in ("status", "status_code"))
        fail_closed = nested_dict(payload, "executable_spec", "fail_closed_current_evidence")
        fields.extend(str(fail_closed.get(key, "")) for key in ("current_status", "exact_blocker"))
        api_lane = payload.get("official_api_lane")
        if isinstance(api_lane, dict):
            fields.extend(str(api_lane.get(key, "")) for key in ("status", "scorer_status", "remaining_blocker"))
    return " ".join(item for item in fields if item).upper()


def collect_refs(payloads: list[dict[str, Any]], root: Path, keys: set[str]) -> list[str]:
    refs: set[str] = set()
    for payload in payloads:
        for row in walk_dicts(payload):
            for key in keys:
                value = row.get(key)
                if isinstance(value, str) and value:
                    refs.add(value.replace("\\", "/"))
                elif isinstance(value, list):
                    refs.update(str(item).replace("\\", "/") for item in value if str(item))
    return sorted(ref for ref in refs if (root / ref).exists())


def command_tokens(value: str) -> list[str]:
    try:
        return shlex.split(value)
    except ValueError:
        return []


def safe_domain_local_replay_command(value: Any, root: Path) -> dict[str, Any] | None:
    commands: list[str] = []
    if isinstance(value, str) and value:
        commands.append(value)
    elif isinstance(value, dict):
        raw_commands = value.get("commands")
        if isinstance(raw_commands, list):
            commands.extend(str(item) for item in raw_commands if isinstance(item, str) and item)
        raw_command = value.get("command")
        if isinstance(raw_command, str) and raw_command:
            commands.append(raw_command)

    for command_text in commands:
        argv = command_tokens(command_text)
        if len(argv) < 2:
            continue
        if argv[0] not in {"python", sys.executable}:
            continue
        script_ref = argv[1].replace("\\", "/")
        if not script_ref.startswith(f"{DOMAIN_LOCAL_COVERAGE_ROOT_REL}/"):
            continue
        if not (root / script_ref).is_file():
            continue
        if any(token in {"&&", "||", ";", "|", ">", ">>", "<"} for token in argv):
            continue
        return {
            "command": display_command(argv),
            "argv": ["python", *argv[1:]],
            "script_ref": script_ref,
        }
    return None


def collect_safe_replay_command(payloads: list[dict[str, Any]], root: Path) -> dict[str, Any] | None:
    for payload in payloads:
        for row in walk_dicts(payload):
            for key in ("replay_command", "implemented_replay_command"):
                replay = safe_domain_local_replay_command(row.get(key), root)
                if replay:
                    return replay
    return None


def read_domain_local_artifacts(root: Path = ROOT) -> tuple[list[tuple[str, dict[str, Any]]], list[Path]]:
    base = root / DOMAIN_LOCAL_COVERAGE_ROOT_REL
    if not base.exists():
        return [], []
    artifact_paths = sorted(path for path in base.glob(DOMAIN_LOCAL_COVERAGE_ARTIFACT_GLOB) if path.is_file())
    payloads: list[tuple[str, dict[str, Any]]] = []
    for path in artifact_paths:
        payload = read_json(path)
        if payload:
            payloads.append((rel_ref(path, root), payload))
    return payloads, artifact_paths


def evidence_payloads_by_work_order(
    artifact_payloads: list[tuple[str, dict[str, Any]]],
) -> dict[str, list[dict[str, Any]]]:
    evidence_by_id: dict[str, list[dict[str, Any]]] = {}
    for artifact_ref, payload in artifact_payloads:
        if isinstance(payload.get("work_orders"), list):
            continue
        ids = [
            payload.get("target_work_order_id"),
            payload.get("work_order_id"),
            payload.get("coverage_work_order_id"),
        ]
        for work_order_id in ids:
            if not isinstance(work_order_id, str) or not work_order_id:
                continue
            enriched = dict(payload)
            enriched["artifact_ref"] = artifact_ref
            evidence_by_id.setdefault(work_order_id, []).append(enriched)
    return evidence_by_id


def domain_local_lane_stable_id(row: dict[str, Any]) -> str:
    domain = str(row.get("domain_class_id", "unknown_domain"))
    phenomenon = str(row.get("phenomenon_class_id", "unknown_phenomenon"))
    work_order_id = str(row.get("work_order_id", row.get("coverage_gap_id", "unknown_work_order")))
    return f"domain_local_coverage::{domain}::{phenomenon}::{work_order_id}"


def status_implies_ready_for_review(text: str) -> bool:
    return "READY_FOR_REPLAY_REVIEW" in text or "SCORER_READY" in text


def negative_control_ready(payloads: list[dict[str, Any]]) -> bool:
    if truthy_key(payloads, {"negative_control_rejected", "nontrivial_negative_controls_rejected"}):
        return True
    for payload in payloads:
        for row in walk_dicts(payload):
            if row.get("rejected") is True and "NEGATIVE" in json.dumps(row, sort_keys=True).upper():
                return True
    return False


def domain_local_lane_summary(
    *,
    row: dict[str, Any],
    artifact_ref: str,
    ancillary_payloads: list[dict[str, Any]],
    root: Path,
) -> dict[str, Any]:
    current = row.get("current_evidence_status") if isinstance(row.get("current_evidence_status"), dict) else {}
    fail_closed = nested_dict(row, "executable_spec", "fail_closed_current_evidence")
    api_lane = row.get("official_api_lane") if isinstance(row.get("official_api_lane"), dict) else {}
    payloads = [row, current, fail_closed, api_lane, *ancillary_payloads]
    text = status_text(payloads)
    existing_refs = normalize_predicates(row.get("existing_official_lane_refs"))
    existing_refs_present = bool(existing_refs) and all((root / ref).exists() for ref in existing_refs)
    source_refs = collect_refs(
        payloads,
        root,
        {
            "implemented_snapshot_ref",
            "source_snapshot_ref",
            "snapshot_ref",
            "local_snapshot_ref",
            "expected_local_snapshot_ref",
        },
    )
    strict_refs = collect_refs(
        payloads,
        root,
        {
            "strict_evidence_pack_ref",
            "implemented_scoring_pack_ref",
            "scoring_pack_ref",
            "candidate_pack_ref",
        },
    )
    replay_command = collect_safe_replay_command(payloads, root)
    replay_evidence_refs = sorted(set(source_refs + strict_refs))
    source_acquired = (
        truthy_key(
            payloads,
            {
                "source_snapshot_hash_bound",
                "readonly_acquisition_hash_bound",
                "readonly_acquisition_lane_implemented",
                "source_snapshot_pre_target_lock",
            },
        )
        or bool(source_refs)
        or ("READY_FOR_REPLAY_REVIEW" in text and existing_refs_present)
    )
    scorer_ready = (
        truthy_key(payloads, {"target_hidden_scorer_present", "scorer_ready", "executable_evidence_exists"})
        or status_implies_ready_for_review(text)
    )
    comparator_ready = truthy_key(
        payloads,
        {
            "comparator_scores_present",
            "comparator_residual_metric_bound",
            "strict_scientific_predicates_pass",
        },
    ) or ("READY_FOR_REPLAY_REVIEW" in text and existing_refs_present)
    negative_ready = negative_control_ready(payloads) or ("READY_FOR_REPLAY_REVIEW" in text and existing_refs_present)
    replay_ready = nonempty_key(
        payloads,
        {"replay_hash", "replay_sha256", "evidence_pack_sha256", "scoring_pack_sha256", "candidate_pack_sha256"},
    ) or ("READY_FOR_REPLAY_REVIEW" in text and existing_refs_present)
    strict_pack = (
        truthy_key(payloads, {"strict_evidence_pack_present", "strict_artifact"})
        or nonempty_key(payloads, {"strict_evidence_pack_ref", "strict_evidence_pack", "evidence_pack_id"})
        or bool(strict_refs)
        or ("STRICT_EVIDENCE_PACK" in text)
        or ("READY_FOR_REPLAY_REVIEW" in text and existing_refs_present)
    )
    strict_scientific_pass = truthy_key(payloads, {"strict_predicates_all_pass", "strict_scientific_predicates_pass"})
    coverage_closed = (
        row.get("coverage_closure_allowed") is True
        or row.get("support_allowed_for_broad_coverage") is True
        or ("COVERAGE_CLOSED" in text and "NOT_COVERAGE_CLOSED" not in text and "NO_COVERAGE_CLOSURE" not in text)
        or "PASS_COVERAGE" in text
    )
    predicate_state = {
        "OFFICIAL_SOURCE_SNAPSHOT_HASH_BOUND": source_acquired,
        "TARGET_HIDDEN_SCORER_READY": scorer_ready,
        "COMPARATOR_RESULT_BOUND": comparator_ready,
        "NEGATIVE_CONTROL_REJECTED": negative_ready,
        "INDEPENDENT_REPLAY_BOUND": replay_ready,
        "STRICT_EVIDENCE_PACK_BOUND": strict_pack,
        "STRICT_SCIENTIFIC_PREDICATES_PASS": strict_scientific_pass,
        "COVERAGE_REVIEWED_OR_CLOSED": coverage_closed,
    }
    missing_predicates = [predicate for predicate, passed in predicate_state.items() if not passed]
    evidence_priority = 50
    if source_acquired and scorer_ready:
        evidence_priority = 0
    elif source_acquired:
        evidence_priority = 1
    elif scorer_ready or strict_pack:
        evidence_priority = 5
    lane_status = str(row.get("lane_status") or current.get("status_code") or fail_closed.get("current_status") or "UNKNOWN")
    return {
        "stable_id": domain_local_lane_stable_id(row),
        "artifact_ref": artifact_ref,
        "work_order_id": row.get("work_order_id"),
        "coverage_gap_id": row.get("coverage_gap_id"),
        "domain_class_id": row.get("domain_class_id"),
        "phenomenon_class_id": row.get("phenomenon_class_id"),
        "phenomenon_label": row.get("phenomenon_label"),
        "lane_status": lane_status,
        "source_acquired": source_acquired,
        "scorer_ready": scorer_ready,
        "strict_evidence_pack_present": strict_pack,
        "coverage_closed": coverage_closed,
        "coverage_closure_allowed": False,
        "broad_modern_science_superiority_allowed": False,
        "missing_predicate_count": len(missing_predicates),
        "missing_predicates": missing_predicates,
        "domain_local_evidence_priority_rank": evidence_priority,
        "source_snapshot_refs": source_refs,
        "strict_evidence_pack_refs": strict_refs,
        "replay_command": replay_command,
        "replay_evidence_refs": replay_evidence_refs,
        "domain_local_replay_ready": bool(replay_command and replay_evidence_refs),
        "remaining_blockers": normalize_predicates(row.get("remaining_blockers")),
        "closure_policy": "Domain-local artifacts are evidence state only; all coverage lanes remain open until reviewed closure.",
    }


def load_domain_local_coverage_summary(root: Path = ROOT) -> dict[str, Any]:
    artifact_payloads, artifact_paths = read_domain_local_artifacts(root)
    evidence_by_id = evidence_payloads_by_work_order(artifact_payloads)
    lanes: list[dict[str, Any]] = []
    manifest_refs: list[str] = []
    for artifact_ref, payload in artifact_payloads:
        work_orders = payload.get("work_orders")
        if not isinstance(work_orders, list):
            continue
        manifest_refs.append(artifact_ref)
        for row in work_orders:
            if not isinstance(row, dict):
                continue
            work_order_id = str(row.get("work_order_id", ""))
            lanes.append(
                domain_local_lane_summary(
                    row=row,
                    artifact_ref=artifact_ref,
                    ancillary_payloads=evidence_by_id.get(work_order_id, []),
                    root=root,
                )
            )
    lanes = sorted(lanes, key=lambda lane: str(lane.get("stable_id", "")))
    nearest = sorted(
        lanes,
        key=lambda lane: (
            int(lane.get("missing_predicate_count", 999)),
            str(lane.get("stable_id", "")),
        ),
    )
    return {
        "schema_id": "OC133_DOMAIN_LOCAL_COVERAGE_ARTIFACT_SUMMARY_v1",
        "artifact_root": DOMAIN_LOCAL_COVERAGE_ROOT_REL,
        "domain_local_coverage_artifact_total": len(artifact_paths),
        "domain_local_coverage_work_order_artifact_total": len(manifest_refs),
        "domain_local_coverage_lane_total": len(lanes),
        "source_acquired_lane_total": sum(1 for lane in lanes if lane.get("source_acquired") is True),
        "scorer_ready_lane_total": sum(1 for lane in lanes if lane.get("scorer_ready") is True),
        "strict_evidence_pack_total": sum(1 for lane in lanes if lane.get("strict_evidence_pack_present") is True),
        "coverage_closed_total": sum(1 for lane in lanes if lane.get("coverage_closed") is True),
        "coverage_closure_allowed": False,
        "broad_modern_science_superiority_allowed": False,
        "artifact_refs": sorted(rel_ref(path, root) for path in artifact_paths),
        "work_order_artifact_refs": sorted(manifest_refs),
        "nearest_to_closure": nearest[:10],
        "lanes": lanes,
    }


def domain_local_lane_index(domain_local: dict[str, Any]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for lane in domain_local.get("lanes", []):
        if not isinstance(lane, dict):
            continue
        candidate_keys = [
            lane.get("work_order_id"),
            lane.get("coverage_gap_id"),
            f"{lane.get('domain_class_id')}::{lane.get('phenomenon_class_id')}",
        ]
        for key in candidate_keys:
            if not key:
                continue
            key_s = str(key)
            current = index.get(key_s)
            if current is None or (
                int(lane.get("domain_local_evidence_priority_rank", 50)),
                int(lane.get("missing_predicate_count", 999)),
                str(lane.get("stable_id", "")),
            ) < (
                int(current.get("domain_local_evidence_priority_rank", 50)),
                int(current.get("missing_predicate_count", 999)),
                str(current.get("stable_id", "")),
            ):
                index[key_s] = lane
    return index


def find_domain_local_lane(lane: dict[str, Any], domain_local: dict[str, Any]) -> dict[str, Any] | None:
    index = domain_local_lane_index(domain_local)
    keys = [
        lane.get("work_order_id"),
        lane.get("coverage_gap_id"),
        f"{lane.get('domain_class_id')}::{lane.get('phenomenon_class_id')}",
    ]
    for key in keys:
        if key and str(key) in index:
            return index[str(key)]
    return None


def capability_executor(
    *,
    owner_capability: str,
    profile: str | None,
    mode: str,
    argv: list[str],
    closure_policy: str,
) -> dict[str, Any]:
    return {
        "owner_capability": owner_capability,
        "executor_id": f"{mode}::{profile or Path(argv[1]).stem if len(argv) > 1 else 'unknown'}",
        "mode": mode,
        "profile": profile,
        "entrypoint": argv[1] if len(argv) > 1 else argv[0],
        "argv": argv,
        "command": display_command(argv),
        "closure_policy": closure_policy,
    }


def profile_executor(owner_capability: str, profile: str, closure_policy: str) -> dict[str, Any]:
    return capability_executor(
        owner_capability=owner_capability,
        profile=profile,
        mode="capability_profile",
        argv=python_argv("tools/oc133_capability_repair_executor.py", "--profile", profile),
        closure_policy=closure_policy,
    )


def coverage_lane_executor(owner_capability: str) -> dict[str, Any]:
    return capability_executor(
        owner_capability=owner_capability,
        profile=None,
        mode="planning_queue_validation",
        argv=python_argv(COVERAGE_LANE_DISPATCHER_REL, "--check"),
        closure_policy=(
            "Planning/check execution is not scientific closure; the lane remains open until the "
            "evidence pack, comparator, controls, falsifiers, and reviewed coverage predicates pass."
        ),
    )


def domain_local_replay_executor(owner_capability: str, replay_command: dict[str, Any]) -> dict[str, Any]:
    return capability_executor(
        owner_capability=owner_capability,
        profile=None,
        mode="domain_local_replay",
        argv=[str(item) for item in replay_command.get("argv", [])],
        closure_policy=(
            "Domain-local replay execution is evidence replay only; it preserves no-send and does not mark "
            "coverage closed without independent review and re-audit PASS."
        ),
    )


def formal_predicate_spec(predicate_id: str) -> dict[str, Any]:
    specs: dict[str, dict[str, Any]] = {
        "dedicated_claim_row": {
            "title": "Create or explicitly reject a dedicated promoted grand TOE/all-domain claim row",
            "owner_capability": "Research/FormalScience",
            "closure_evidence_type": "promoted_grand_claim_ledger_row",
            "before_predicates": ["dedicated_claim_row == false"],
            "after_predicates": [
                "A dedicated claim row exists only if promotion is intended and evidence-supported",
                "Unsupported grand promotion remains demoted when evidence is absent",
            ],
            "closure_evidence_required": [
                "claim ledger row ID",
                "requested claim classes",
                "explicit promotion or non-promotion verdict",
            ],
            "gate_unblock_value": 90,
            "dependency_unblock_value": 70,
            "resource_estimate": {"planning_points": 5, "expected_worker_roles": ["formal claim owner", "claim-boundary reviewer"]},
        },
        "release_promotion_allowed": {
            "title": "Bind release-promotion permission to the grand claim evidence gate",
            "owner_capability": "Review/ClaimBoundary",
            "closure_evidence_type": "claim_boundary_promotion_gate",
            "before_predicates": ["release_promotion_allowed == false"],
            "after_predicates": ["release_promotion_allowed is true only after every grand promotion predicate passes"],
            "closure_evidence_required": ["claim boundary review row", "promotion gate vector", "no-send lock attestation"],
            "gate_unblock_value": 86,
            "dependency_unblock_value": 65,
            "resource_estimate": {"planning_points": 3, "expected_worker_roles": ["claim-boundary reviewer"]},
        },
        "scientific_promotion_allowed": {
            "title": "Bind scientific-promotion permission to theorem and evidence references",
            "owner_capability": "Research/FormalScience",
            "closure_evidence_type": "scientific_promotion_gate",
            "before_predicates": ["scientific_promotion_allowed == false"],
            "after_predicates": ["scientific_promotion_allowed is true only on a fully evidenced grand claim row"],
            "closure_evidence_required": ["scientific promotion gate vector", "theorem/proof/Lean/finite refs"],
            "gate_unblock_value": 87,
            "dependency_unblock_value": 66,
            "resource_estimate": {"planning_points": 5, "expected_worker_roles": ["formal science owner"]},
        },
        "public_status_promoted": {
            "title": "Keep public promoted status locked until grand evidence gates pass",
            "owner_capability": "Review/ClaimBoundary",
            "closure_evidence_type": "public_status_claim_boundary_gate",
            "before_predicates": ["public_status_promoted == false"],
            "after_predicates": ["public status may be promoted only after scientific and release promotion gates pass"],
            "closure_evidence_required": ["claim ledger public status row", "owner no-send approval lock"],
            "gate_unblock_value": 84,
            "dependency_unblock_value": 60,
            "resource_estimate": {"planning_points": 2, "expected_worker_roles": ["claim-boundary reviewer"]},
        },
        "promotion_theorem_ids_bound": {
            "title": "Bind grand promotion theorem IDs distinct from bounded theorem rows",
            "owner_capability": "Research/FormalScience",
            "closure_evidence_type": "theorem_inventory_binding",
            "before_predicates": ["promotion_theorem_ids_bound == false"],
            "after_predicates": ["grand claim row names theorem inventory IDs proving the promoted grand statement"],
            "closure_evidence_required": ["theorem inventory IDs", "claim ledger theorem refs"],
            "gate_unblock_value": 89,
            "dependency_unblock_value": 70,
            "resource_estimate": {"planning_points": 8, "expected_worker_roles": ["formal theorem owner", "proof reviewer"]},
        },
        "proof_sheet_refs_bound": {
            "title": "Bind proof sheet references for the promoted grand claim",
            "owner_capability": "Research/FormalScience",
            "closure_evidence_type": "proof_sheet_binding",
            "before_predicates": ["proof_sheet_refs_bound == false"],
            "after_predicates": ["proof sheets cite assumptions, proof obligations, and falsifier boundaries for the grand claim"],
            "closure_evidence_required": ["proof sheet refs", "assumption and falsifier boundary section"],
            "gate_unblock_value": 88,
            "dependency_unblock_value": 68,
            "resource_estimate": {"planning_points": 5, "expected_worker_roles": ["proof-sheet owner", "formal reviewer"]},
        },
        "lean_theorem_ids_bound": {
            "title": "Bind Lean theorem obligations for the promoted grand statement",
            "owner_capability": "Research/FormalScience",
            "closure_evidence_type": "lean_theorem_binding",
            "before_predicates": ["lean_theorem_ids_bound == false"],
            "after_predicates": ["Lean theorem IDs prove the promoted grand statement or keep non-promotion machine-proved"],
            "closure_evidence_required": ["Lean theorem refs", "lake build log", "claim ledger Lean refs"],
            "gate_unblock_value": 88,
            "dependency_unblock_value": 68,
            "resource_estimate": {"planning_points": 8, "expected_worker_roles": ["Lean/formal methods owner"]},
        },
        "finite_case_ids_bound": {
            "title": "Bind finite-model witness cases for the promoted grand claim",
            "owner_capability": "Research/FormalScience",
            "closure_evidence_type": "finite_model_case_binding",
            "before_predicates": ["finite_case_ids_bound == false"],
            "after_predicates": ["finite positive, current-reject, and negative cases are bound to the grand claim theorem IDs"],
            "closure_evidence_required": ["finite case IDs", "finite input refs", "finite output refs"],
            "gate_unblock_value": 88,
            "dependency_unblock_value": 68,
            "resource_estimate": {"planning_points": 5, "expected_worker_roles": ["finite-model owner", "formal reviewer"]},
        },
        "finite_positive_negative_controls_bound": {
            "title": "Bind finite positive and negative controls for grand promotion",
            "owner_capability": "Research/FormalScience",
            "closure_evidence_type": "finite_positive_negative_control_binding",
            "before_predicates": ["finite_positive_negative_controls_bound == false"],
            "after_predicates": ["finite controls include a positive accept case and mutation/negative reject cases"],
            "closure_evidence_required": ["positive control finite case ID", "negative control finite case IDs", "mutation verdicts"],
            "gate_unblock_value": 88,
            "dependency_unblock_value": 68,
            "resource_estimate": {"planning_points": 5, "expected_worker_roles": ["finite-model owner", "formal reviewer"]},
        },
    }
    return specs.get(
        predicate_id,
        {
            "title": f"Close broad-claim predicate {predicate_id}",
            "owner_capability": "Research/FormalScience",
            "closure_evidence_type": "broad_claim_gate_predicate",
            "before_predicates": [f"{predicate_id} == false"],
            "after_predicates": [f"{predicate_id} == true or the grand claim remains explicitly demoted"],
            "closure_evidence_required": ["predicate gate row", "reviewed evidence refs"],
            "gate_unblock_value": 80,
            "dependency_unblock_value": 50,
            "resource_estimate": {"planning_points": 3, "expected_worker_roles": ["formal science owner"]},
        },
    )


def build_formal_predicate_work_order(predicate_id: str, check: dict[str, Any]) -> dict[str, Any]:
    spec = formal_predicate_spec(predicate_id)
    owner = str(spec["owner_capability"])
    profile = PROFILE_BY_CAPABILITY.get(owner, PROFILE_BY_CAPABILITY["Research/FormalScience"])
    stable_id = f"broad_claim_gap::grand_toe_claim_ledger_evidence::{predicate_id}"
    severity = "CRITICAL"
    verification_commands = [
        "lake build OC133V12",
        "python proofs/finite_model_checks/run_finite_model_checks.py",
        "python tools/oc133_grand_toe_formal_obligations.py --write",
        "python tools/oc133_logion_all_domain_readiness.py --write --allow-blocked-exit-zero",
    ]
    return {
        "work_order_id": f"OC133-ALLDOMAIN-BROAD-GAP-{predicate_id.upper().replace('_', '-')}",
        "stable_id": stable_id,
        "mission_id": oc133_platinum.MISSION_ID,
        "dispatch_class": "broad_claim_evidence_gap",
        "blocker_id": "grand_toe_claim_ledger_evidence",
        "broad_claim_evidence_gap_id": predicate_id,
        "owner_capability": owner,
        "title": str(spec["title"]),
        "severity": severity,
        "priority": 1000 - SEVERITY_RANK[severity],
        "ranking": ranking_for(
            stable_id=stable_id,
            severity=severity,
            gate_unblock_value=int(spec["gate_unblock_value"]),
            dependency_unblock_value=int(spec["dependency_unblock_value"]),
        ),
        "executor": profile_executor(
            owner,
            profile,
            "Executor output is evidence only; closure requires the predicate to re-audit PASS without unlocking no-send.",
        ),
        "artifacts": list(FORMAL_CLAIM_ARTIFACTS),
        "owned_artifacts": list(FORMAL_CLAIM_ARTIFACTS),
        "before_predicates": list(spec["before_predicates"]),
        "after_predicates": list(spec["after_predicates"]),
        "before_predicate": "; ".join(spec["before_predicates"]),
        "after_predicate": "; ".join(spec["after_predicates"]),
        "verification_commands": verification_commands,
        "verification_command": " && ".join(verification_commands),
        "resource_estimate": spec["resource_estimate"],
        "closure_evidence_type": str(spec["closure_evidence_type"]),
        "closure_evidence_required": list(spec["closure_evidence_required"]),
        "closure_control": {
            "current_check_state": check.get("state"),
            "mark_closed_allowed_in_this_dispatch": False,
            "blocked_item_closed": False,
            "requires_reaudit_pass": True,
        },
        "dependency_ids": [],
        "dependency_blocker_ids": ["modern_science_comparator_superiority"]
        if predicate_id == "modern_science_superiority_certified"
        else [],
        "implementation_policy": "Execute through Logion capability worker; planning output cannot close the scientific blocker by itself.",
        "no_send_locks": dict(NO_SEND_LOCKS),
        "no_send": True,
        "publish_allowed": False,
        "journal_submissions_allowed": False,
    }


def build_modern_science_broad_work_order(check: dict[str, Any], coverage_queue: dict[str, Any]) -> dict[str, Any]:
    predicate_id = "modern_science_superiority_certified"
    stable_id = f"broad_claim_gap::modern_science_comparator_superiority::{predicate_id}"
    severity = "CRITICAL"
    coverage_total = int(coverage_queue.get("open_lane_total", coverage_queue.get("queue_size", 0)) or 0)
    verification_commands = [
        "python benchmarks/modern_science/coverage_lane_dispatcher.py --check",
        "python tools/oc133_modern_science_comparator_factory.py --check",
        "python tools/oc133_logion_all_domain_readiness.py --write --allow-blocked-exit-zero",
    ]
    return {
        "work_order_id": "OC133-ALLDOMAIN-BROAD-GAP-MODERN-SCIENCE-SUPERIORITY-CERTIFIED",
        "stable_id": stable_id,
        "mission_id": oc133_platinum.MISSION_ID,
        "dispatch_class": "broad_claim_evidence_gap",
        "blocker_id": "modern_science_comparator_superiority",
        "broad_claim_evidence_gap_id": predicate_id,
        "owner_capability": "Research/PriorArt",
        "title": "Certify or keep blocked the broad modern-science superiority predicate",
        "severity": severity,
        "priority": 1000 - SEVERITY_RANK[severity],
        "ranking": ranking_for(
            stable_id=stable_id,
            severity=severity,
            gate_unblock_value=94,
            dependency_unblock_value=85,
        ),
        "executor": profile_executor(
            "Research/PriorArt",
            PROFILE_BY_CAPABILITY["Research/PriorArt"],
            "Executor may refresh comparator artifacts, but closure requires all coverage lanes and broad predicates to pass.",
        ),
        "artifacts": list(MODERN_SCIENCE_ARTIFACTS),
        "owned_artifacts": list(MODERN_SCIENCE_ARTIFACTS),
        "before_predicates": [
            "modern_science_comparator_superiority == FAIL",
            f"open_modern_science_coverage_lane_total == {coverage_total}",
            "broad_modern_science_superiority_certified == false",
        ],
        "after_predicates": [
            "modern_science comparator register certifies broad superiority only after every declared coverage lane passes",
            "unsupported broad superiority wording remains blocked if any lane or comparator predicate is open",
        ],
        "before_predicate": (
            f"modern_science_comparator_superiority == FAIL and open_modern_science_coverage_lane_total == {coverage_total}"
        ),
        "after_predicate": "broad modern-science superiority is certified only after every declared coverage and comparator predicate passes",
        "verification_commands": verification_commands,
        "verification_command": " && ".join(verification_commands),
        "resource_estimate": {
            "planning_points": 8,
            "open_coverage_lane_total": coverage_total,
            "expected_worker_roles": ["prior-art owner", "coverage lane owners", "clean replay reviewer"],
        },
        "closure_evidence_type": "broad_modern_science_comparator_certification",
        "closure_evidence_required": [
            "coverage register with zero open gaps",
            "per-lane source-backed benchmark refs",
            "preregistered incumbent comparator refs",
            "OC/comparator residuals and uncertainty",
            "clean-checkout replay bound to the broad comparator register",
        ],
        "closure_control": {
            "current_check_state": check.get("state"),
            "mark_closed_allowed_in_this_dispatch": False,
            "blocked_item_closed": False,
            "requires_reaudit_pass": True,
        },
        "dependency_ids": [
            row.get("stable_id")
            for row in coverage_queue.get("lanes", [])
            if isinstance(row, dict) and row.get("coverage_closure", {}).get("current_status") == "OPEN"
        ],
        "dependency_blocker_ids": ["coverage_extends_to_all_of_modern_science"],
        "implementation_policy": "Do not certify broad modern-science superiority while coverage gaps remain open.",
        "no_send_locks": dict(NO_SEND_LOCKS),
        "no_send": True,
        "publish_allowed": False,
        "journal_submissions_allowed": False,
    }


def build_coverage_lane_work_order(
    lane: dict[str, Any],
    domain_local_lane: dict[str, Any] | None = None,
) -> dict[str, Any]:
    domain = str(lane.get("domain_class_id", ""))
    phenomenon = str(lane.get("phenomenon_class_id", ""))
    source_work_order_id = str(lane.get("work_order_id", "MS-COV-WO-UNKNOWN"))
    stable_id = f"coverage_gap::{domain}::{phenomenon}::{source_work_order_id}"
    severity = "CRITICAL"
    priority_label = str(lane.get("priority", "P1"))
    route = str(lane.get("lane_route", "EMPIRICAL_SOURCE_BACKED_BENCHMARK"))
    gate_unblock = 100 if priority_label == "P0" else 95
    owner = str(lane.get("owner_capability", "Logion Coverage Evidence Planning"))
    phenomenon_label = str(lane.get("phenomenon_label") or phenomenon.replace("_", " "))
    domain_local_lane = domain_local_lane or {}
    replay_command = domain_local_lane.get("replay_command") if isinstance(domain_local_lane.get("replay_command"), dict) else {}
    replay_ready = bool(domain_local_lane.get("domain_local_replay_ready") and replay_command)
    missing_predicate_count = int(domain_local_lane.get("missing_predicate_count", 999))
    evidence_priority_rank = int(domain_local_lane.get("domain_local_evidence_priority_rank", 50))
    verification_commands = [
        "python benchmarks/modern_science/coverage_lane_dispatcher.py --check",
        "python tools/oc133_modern_science_comparator_factory.py --check",
        "python tools/oc133_logion_all_domain_readiness.py --write --allow-blocked-exit-zero",
    ]
    row = {
        "work_order_id": f"OC133-ALLDOMAIN-COVERAGE-{source_work_order_id}",
        "stable_id": stable_id,
        "source_work_order_id": source_work_order_id,
        "source_dispatch_id": lane.get("dispatch_id"),
        "source_queue_rank": lane.get("queue_rank"),
        "mission_id": oc133_platinum.MISSION_ID,
        "dispatch_class": "uncovered_phenomenon_class",
        "blocker_id": "coverage_extends_to_all_of_modern_science",
        "parent_blocker_id": "modern_science_comparator_superiority",
        "coverage_gap_id": lane.get("coverage_gap_id"),
        "domain_class_id": domain,
        "phenomenon_class_id": phenomenon,
        "phenomenon_label": phenomenon_label,
        "coverage_lane_route": route,
        "coverage_priority": priority_label,
        "owner_capability": owner,
        "title": f"Build reviewed modern-science coverage lane for {domain} / {phenomenon_label}",
        "severity": severity,
        "priority": 1000 - SEVERITY_RANK[severity],
        "ranking": ranking_for(
            stable_id=stable_id,
            severity=severity,
            gate_unblock_value=gate_unblock,
            dependency_unblock_value=100,
        ),
        "executor": domain_local_replay_executor(owner, replay_command) if replay_ready else coverage_lane_executor(owner),
        "artifacts": list(COVERAGE_LANE_ARTIFACTS),
        "owned_artifacts": list(COVERAGE_LANE_ARTIFACTS),
        "before_predicates": [
            f"{lane.get('coverage_gap_id')} current_status == OPEN",
            f"{domain}/{phenomenon} lacks reviewed source-backed benchmark coverage",
        ],
        "after_predicates": [
            "source capsule or formal corpus hash is bound",
            "target-blind/prospective acquisition or formal-equivalent route is reviewed",
            "incumbent comparator is preregistered",
            "OC scoring, uncertainty, controls, falsifiers, and clean replay are bound",
            "coverage register gap may close only after independent review",
        ],
        "before_predicate": (
            f"{lane.get('coverage_gap_id')} is OPEN and no reviewed source-backed lane covers {domain}/{phenomenon}"
        ),
        "after_predicate": "all lane acceptance predicates pass under review; broad superiority remains blocked until all lanes pass",
        "verification_commands": verification_commands,
        "verification_command": " && ".join(verification_commands),
        "resource_estimate": lane.get("resource_estimate", {}),
        "closure_evidence_type": "formal_route_coverage_protocol_review"
        if route == "FORMAL_ROUTE_PROTOCOL_ONLY"
        else "source_backed_benchmark_coverage_evidence_pack",
        "closure_evidence_required": [
            *normalize_predicates(lane.get("expected_acceptance_predicates")),
            "reviewed coverage register update",
            "no broad superiority certification from this single lane",
        ],
        "required_data_lanes": lane.get("required_data_lanes", []),
        "required_proof_lanes": lane.get("required_proof_lanes", []),
        "dependencies": lane.get("dependencies", []),
        "dependency_ids": [
            str(item.get("dependency_id"))
            for item in lane.get("dependencies", [])
            if isinstance(item, dict) and item.get("state") == "OPEN"
        ],
        "dependency_blocker_ids": ["modern_science_comparator_superiority"],
        "domain_local_coverage_evidence": domain_local_lane or None,
        "closure_control": {
            "current_status": lane.get("coverage_closure", {}).get("current_status", "OPEN"),
            "mark_closed_allowed_in_this_dispatch": False,
            "blocked_item_closed": False,
            "requires_reaudit_pass": True,
        },
        "implementation_policy": "Create evidence only through capability-owned lane work; this dispatch row does not close coverage.",
        "no_send_locks": dict(NO_SEND_LOCKS),
        "no_send": True,
        "publish_allowed": False,
        "journal_submissions_allowed": False,
    }
    row["ranking"]["domain_local_evidence_priority_rank"] = evidence_priority_rank
    row["ranking"]["domain_local_missing_predicate_count"] = missing_predicate_count
    if domain_local_lane:
        row["before_predicates"].append(
            "domain-local coverage artifact state: "
            f"source_acquired={str(domain_local_lane.get('source_acquired')).lower()}, "
            f"scorer_ready={str(domain_local_lane.get('scorer_ready')).lower()}, "
            f"missing_predicate_count={missing_predicate_count}"
        )
        row["closure_control"]["domain_local_artifact_exists_is_not_closure"] = True
        row["closure_control"]["domain_local_coverage_closed"] = False
        if replay_ready:
            row["verification_commands"].insert(0, str(replay_command.get("command")))
            row["verification_command"] = " && ".join(row["verification_commands"])
            row["closure_control"]["domain_local_replay_exists_is_not_closure"] = True
    return row


def load_coverage_lane_queue(root: Path = ROOT) -> dict[str, Any]:
    return read_json(root / COVERAGE_LANE_QUEUE_REL)


def build_autonomous_work_orders(
    audit: dict[str, Any],
    root: Path = ROOT,
    domain_local_coverage: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    checks = audit.get("checks", {}) if isinstance(audit.get("checks"), dict) else {}
    coverage_queue = load_coverage_lane_queue(root)
    domain_local_coverage = domain_local_coverage or load_domain_local_coverage_summary(root)
    orders: list[dict[str, Any]] = []

    for lane in coverage_queue.get("lanes", []):
        if not isinstance(lane, dict):
            continue
        if lane.get("coverage_closure", {}).get("current_status") == "OPEN":
            orders.append(build_coverage_lane_work_order(lane, find_domain_local_lane(lane, domain_local_coverage)))

    grand_claim = checks.get("grand_toe_claim_ledger_evidence", {})
    if isinstance(grand_claim, dict) and grand_claim.get("state") != "PASS":
        failed_predicates = [
            predicate
            for predicate in normalize_predicates(grand_claim.get("failed_gate_predicates"))
            if predicate != "modern_science_superiority_certified"
        ]
        if not failed_predicates:
            failed_predicates = ["grand_toe_claim_ledger_evidence"]
        for predicate in failed_predicates:
            orders.append(build_formal_predicate_work_order(predicate, grand_claim))

    modern_science = checks.get("modern_science_comparator_superiority", {})
    if isinstance(modern_science, dict) and modern_science.get("state") != "PASS":
        orders.append(build_modern_science_broad_work_order(modern_science, coverage_queue))

    for index, row in enumerate(sorted(orders, key=work_order_sort_key), start=1):
        row["queue_rank"] = index
        row["ranking"] = dict(row["ranking"])
        row["ranking"]["queue_rank"] = index
        row["open_dependency_blocker_ids"] = [
            str(item) for item in row.get("dependency_blocker_ids", []) if str(item)
        ]
        row["blocked_by_open_dependency_total"] = len(row["open_dependency_blocker_ids"])
    return sorted(orders, key=lambda row: int(row["queue_rank"]))


def dispatch_summary(
    work_orders: list[dict[str, Any]],
    coverage_queue: dict[str, Any],
    domain_local_coverage: dict[str, Any],
) -> dict[str, Any]:
    broad = [row for row in work_orders if row.get("dispatch_class") == "broad_claim_evidence_gap"]
    coverage = [row for row in work_orders if row.get("dispatch_class") == "uncovered_phenomenon_class"]
    nearest_to_closure = domain_local_coverage.get("nearest_to_closure", [])
    return {
        "schema_id": "OC133_ALL_DOMAIN_AUTONOMOUS_DISPATCH_SUMMARY_v1",
        "ordering_policy": ALL_DOMAIN_ORDERING_POLICY,
        "work_order_total": len(work_orders),
        "uncovered_phenomenon_class_work_order_total": len(coverage),
        "broad_claim_evidence_gap_work_order_total": len(broad),
        "coverage_lane_queue_ref": COVERAGE_LANE_QUEUE_REL,
        "coverage_lane_queue_size": coverage_queue.get("queue_size", 0),
        "coverage_lane_open_total": coverage_queue.get("open_lane_total", 0),
        "domain_local_coverage_artifact_total": domain_local_coverage.get("domain_local_coverage_artifact_total", 0),
        "domain_local_coverage_lane_total": domain_local_coverage.get("domain_local_coverage_lane_total", 0),
        "source_acquired_lane_total": domain_local_coverage.get("source_acquired_lane_total", 0),
        "scorer_ready_lane_total": domain_local_coverage.get("scorer_ready_lane_total", 0),
        "strict_evidence_pack_total": domain_local_coverage.get("strict_evidence_pack_total", 0),
        "coverage_closed_total": domain_local_coverage.get("coverage_closed_total", 0),
        "nearest_to_closure": nearest_to_closure,
        "no_send_locked_work_order_total": sum(1 for row in work_orders if no_send_safety_rank(row) == 0),
        "closure_policy": "No dispatch row marks blocked scientific items closed; closure requires evidence artifacts and re-audit PASS.",
    }


def enrich_readiness_dispatch(audit: dict[str, Any], root: Path = ROOT) -> dict[str, Any]:
    enriched = copy.deepcopy(audit)
    coverage_queue = load_coverage_lane_queue(root)
    domain_local_coverage = load_domain_local_coverage_summary(root)
    work_orders = build_autonomous_work_orders(enriched, root, domain_local_coverage)
    enriched["dispatch_schema_id"] = "OC133_ALL_DOMAIN_AUTONOMOUS_DISPATCH_v2"
    enriched["ordering_policy"] = ALL_DOMAIN_ORDERING_POLICY
    enriched["domain_local_coverage"] = domain_local_coverage
    enriched["autonomous_dispatch"] = dispatch_summary(work_orders, coverage_queue, domain_local_coverage)
    enriched["work_orders"] = work_orders
    enriched["work_order_total"] = len(work_orders)
    enriched["work_order_queue_sha256"] = oc133_platinum.sha256_object(work_orders)
    enriched["next_automatic_action"] = work_orders[0]["work_order_id"] if work_orders else "OWNER_REVIEW_NO_SEND"
    return enriched


def command(cmd: list[str], *, timeout: int = 900) -> dict[str, Any]:
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
        "cmd": sanitized_recorded_argv(cmd),
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout[-4000:],
        "stderr_tail": completed.stderr[-4000:],
    }


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def append_ledger(row: dict[str, Any]) -> dict[str, Any]:
    ledger = read_json(EXECUTION_LEDGER)
    rows = ledger.get("rows", []) if isinstance(ledger.get("rows"), list) else []
    normalized_rows = []
    for item in rows:
        if (
            isinstance(item, dict)
            and item.get("execution_state") == "PASS"
            and item.get("after_final_readiness_state") == "SCIENTIFIC_BLOCKERS_REMAIN"
            and item.get("artifact_exists_is_not_closure") is True
        ):
            item = dict(item)
            item["execution_state"] = "SCIENTIFIC_BLOCKERS_REMAIN"
            item["legacy_execution_state_normalized_from"] = "PASS"
        if isinstance(item, dict) and isinstance(item.get("command"), dict):
            command_row = dict(item["command"])
            cmd = command_row.get("cmd")
            if isinstance(cmd, list):
                command_row["cmd"] = sanitized_recorded_argv(cmd)
                item = dict(item)
                item["command"] = command_row
        normalized_rows.append(item)
    rows = normalized_rows
    rows.append(row)
    payload = {
        "schema_id": "OC133_ALL_DOMAIN_EXECUTION_LEDGER_v1",
        "mission_id": oc133_platinum.MISSION_ID,
        "release_id": oc133_platinum.RELEASE_ID,
        "version": oc133_platinum.VERSION,
        "row_total": len(rows),
        "pass_total": sum(1 for item in rows if item.get("execution_state") == "PASS"),
        "fail_total": sum(1 for item in rows if item.get("execution_state") != "PASS"),
        "scientific_blocked_total": sum(1 for item in rows if item.get("execution_state") == "SCIENTIFIC_BLOCKERS_REMAIN"),
        "latest_work_order_id": row.get("work_order_id"),
        "latest_execution_state": row.get("execution_state"),
        "no_send": True,
        "publish_allowed": False,
        "journal_submissions_allowed": False,
        "rows": rows,
    }
    oc133_platinum.write_json(EXECUTION_LEDGER, payload)
    return payload


def render_all_domain_cockpit(audit: dict[str, Any]) -> str:
    empirical = audit["checks"].get("all_domain_empirical_predictions", {})
    mathematics_formal = audit["checks"].get("mathematics_formal_support", {})
    journal = audit["checks"].get("journal_owner_review_packages", {})
    dispatch = audit.get("autonomous_dispatch", {})
    domain_local = audit.get("domain_local_coverage", {}) if isinstance(audit.get("domain_local_coverage"), dict) else {}
    lines = [
        "# OC Core 1.3.3 All-Domain Scientific Readiness Cockpit",
        "",
        f"Mission: `{oc133_platinum.MISSION_ID}`",
        f"State: `{audit['state']}`",
        f"Final readiness state: `{audit['final_readiness_state']}`",
        f"All-domain ready no-send: `{str(audit['all_domain_ready_no_send']).lower()}`",
        f"Blockers: `{audit['blocker_total']}`",
        f"Next automatic action: `{audit['next_automatic_action']}`",
        "Public action allowed: `false`",
        "Journal submissions allowed: `false`",
        "",
        "## Dispatch",
        "",
        f"- Ordering policy: `{ALL_DOMAIN_ORDERING_POLICY}`",
        f"- Work orders: `{dispatch.get('work_order_total', audit.get('work_order_total', 0))}`",
        f"- Coverage lane work orders: `{dispatch.get('uncovered_phenomenon_class_work_order_total', 0)}`",
        f"- Broad-claim evidence-gap work orders: `{dispatch.get('broad_claim_evidence_gap_work_order_total', 0)}`",
        f"- Coverage open lanes: `{dispatch.get('coverage_lane_open_total', 0)}`",
        f"- Domain-local coverage artifacts: `{dispatch.get('domain_local_coverage_artifact_total', 0)}`",
        "- Closure policy: `blocked items remain open until evidence artifacts and re-audit PASS`",
        "",
        "## Counters",
        "",
        f"- Required empirical domains: `{len(oc133_platinum.REQUIRED_EMPIRICAL_DOMAINS)}`",
        f"- Passed empirical domains: `{empirical.get('passed_domain_total', 0)}`",
        f"- Missing empirical domains: `{empirical.get('missing_domain_total', 0)}`",
        f"- Mathematics formal support: `{mathematics_formal.get('state', 'FAIL')}`",
        f"- Journal owner-review packages: `{journal.get('package_total', 0)}`",
        f"- domain_local_coverage_artifact_total: `{dispatch.get('domain_local_coverage_artifact_total', 0)}`",
        f"- source_acquired_lane_total: `{dispatch.get('source_acquired_lane_total', 0)}`",
        f"- scorer_ready_lane_total: `{dispatch.get('scorer_ready_lane_total', 0)}`",
        f"- strict_evidence_pack_total: `{dispatch.get('strict_evidence_pack_total', 0)}`",
        f"- coverage_closed_total: `{dispatch.get('coverage_closed_total', 0)}`",
        "",
        "## Nearest To Closure",
        "",
    ]
    nearest_to_closure = domain_local.get("nearest_to_closure", dispatch.get("nearest_to_closure", []))
    if not nearest_to_closure:
        lines.append("- none")
    for lane in nearest_to_closure[:8]:
        if not isinstance(lane, dict):
            continue
        lines.append(
            "- `{stable}` missing=`{missing}` source=`{source}` scorer=`{scorer}` strict_pack=`{strict}` closed=`{closed}`".format(
                stable=lane.get("stable_id"),
                missing=lane.get("missing_predicate_count"),
                source=str(lane.get("source_acquired")).lower(),
                scorer=str(lane.get("scorer_ready")).lower(),
                strict=str(lane.get("strict_evidence_pack_present")).lower(),
                closed=str(lane.get("coverage_closed")).lower(),
            )
        )
    lines.extend([
        "",
        "## Capability Checks",
        "",
        "| Check | State | Key Counter |",
        "| --- | --- | --- |",
    ])
    for key, row in audit["checks"].items():
        counter = ""
        for candidate in (
            "missing_domain_total",
            "theorem_ref_total",
            "hit_total",
            "package_total",
            "bad_send_unlock_total",
            "theorem_total",
            "critical_open_total",
            "coverage_gap_total",
            "superiority_certified_total",
        ):
            if candidate in row:
                counter = f"`{candidate}={row[candidate]}`"
                break
        lines.append(f"| `{key}` | `{row.get('state')}` | {counter} |")
    lines.extend(["", "## Active Work Orders", ""])
    if not audit["work_orders"]:
        lines.append("- none")
    for row in audit["work_orders"][:20]:
        lines.append(
            "- `#{rank}` `{wid}` `{owner}` `{severity}` `{closure}`: {title}".format(
                rank=row.get("queue_rank"),
                wid=row["work_order_id"],
                owner=row["owner_capability"],
                severity=row["severity"],
                closure=row.get("closure_evidence_type", "closure_evidence"),
                title=row["title"],
            )
        )
        commands = row.get("verification_commands") or [row.get("verification_command")]
        if commands and commands[0]:
            lines.append(f"  Verification: `{commands[0]}`")
    if len(audit["work_orders"]) > 20:
        lines.append(f"- ... `{len(audit['work_orders']) - 20}` additional work orders in JSON dispatch")
    return "\n".join(lines) + "\n"


def write_all_domain_outputs(audit: dict[str, Any] | None = None) -> dict[str, str]:
    base_audit = oc133_platinum.content_closure_audit(ROOT)
    audit = enrich_readiness_dispatch(audit or oc133_platinum.all_domain_readiness_audit(ROOT, base_audit))
    base = oc133_platinum.mission_dir(ROOT)
    dispatch = {
        "schema_id": "OC133_ALL_DOMAIN_WORK_ORDERS_v2",
        "mission_id": oc133_platinum.MISSION_ID,
        "release_id": oc133_platinum.RELEASE_ID,
        "version": oc133_platinum.VERSION,
        "generated_at": oc133_platinum.TIMESTAMP,
        "queue_sha256": audit["work_order_queue_sha256"],
        "state": "ACTIVE" if audit["work_orders"] else "EMPTY_OWNER_REVIEW_NO_SEND",
        "ordering_policy": ALL_DOMAIN_ORDERING_POLICY,
        "work_order_total": audit["work_order_total"],
        "autonomous_dispatch": audit.get("autonomous_dispatch", {}),
        "domain_local_coverage": audit.get("domain_local_coverage", {}),
        "no_send_locks": dict(NO_SEND_LOCKS),
        "closure_policy": "No generated work order marks a blocked item closed; closure requires evidence artifacts and re-audit PASS.",
        "rows": audit["work_orders"],
    }
    oc133_platinum.write_json(base / "OC133_ALL_DOMAIN_READINESS_SCORECARD.json", audit)
    oc133_platinum.write_json(base / "OC133_ALL_DOMAIN_WORK_ORDERS.json", dispatch)
    oc133_platinum.write_text(base / "OC133_ALL_DOMAIN_READINESS_COCKPIT.md", render_all_domain_cockpit(audit))
    return {
        "all_domain_scorecard_ref": f"{oc133_platinum.MISSION_DIR_REL}/OC133_ALL_DOMAIN_READINESS_SCORECARD.json",
        "all_domain_dispatch_ref": f"{oc133_platinum.MISSION_DIR_REL}/OC133_ALL_DOMAIN_WORK_ORDERS.json",
        "all_domain_cockpit_ref": f"{oc133_platinum.MISSION_DIR_REL}/OC133_ALL_DOMAIN_READINESS_COCKPIT.md",
    }


def execute_next() -> dict[str, Any]:
    before = enrich_readiness_dispatch(
        oc133_platinum.all_domain_readiness_audit(ROOT, oc133_platinum.content_closure_audit(ROOT))
    )
    work_orders = before.get("work_orders", [])
    if not work_orders:
        refs = write_all_domain_outputs(before)
        result = {
            "schema_id": "OC133_ALL_DOMAIN_EXECUTE_NEXT_RESULT_v1",
            "mission_id": oc133_platinum.MISSION_ID,
            "selected_work_order_id": "OWNER_REVIEW_NO_SEND",
            "execution_state": "NOOP",
            "after_state": before.get("state"),
            "after_final_readiness_state": before.get("final_readiness_state"),
            "refs": refs,
            "no_send": True,
            "publish_allowed": False,
            "journal_submissions_allowed": False,
        }
        append_ledger(result)
        return result

    work_order = work_orders[0]
    profile = PROFILE_BY_CAPABILITY.get(str(work_order.get("owner_capability")))
    executor = work_order.get("executor", {}) if isinstance(work_order.get("executor"), dict) else {}
    executor_argv = executor.get("argv") if isinstance(executor.get("argv"), list) else []
    if (
        work_order.get("owner_capability") == "Research/EmpiricalScience"
        and "grand_toe_empirical_superiority" in str(work_order.get("before_predicate", ""))
    ):
        profile = "v12_grand_empirical_superiority_research_program"
    if (
        work_order.get("owner_capability") == "Research/EmpiricalScience"
        and "strict per-domain predictive superiority" in str(work_order.get("title", "")).lower()
    ):
        profile = "v12_grand_empirical_superiority_research_program"
    if executor_argv or profile:
        argv = runtime_argv(executor_argv) if executor_argv else [
            sys.executable,
            "tools/oc133_capability_repair_executor.py",
            "--profile",
            str(profile),
        ]
        result_cmd = command(argv, timeout=1500)
        after = enrich_readiness_dispatch(
            oc133_platinum.all_domain_readiness_audit(ROOT, oc133_platinum.content_closure_audit(ROOT))
        )
        refs = write_all_domain_outputs(after)
        after_blocker_ids = after.get("blocker_ids", [])
        same_work_order_remains = any(
            str(row.get("work_order_id")) == str(work_order.get("work_order_id"))
            for row in after.get("work_orders", [])
        )
        closure_policy = str(executor.get("closure_policy", ""))
        planning_only = executor.get("mode") == "planning_queue_validation" or "not scientific closure" in closure_policy
        if result_cmd["returncode"] != 0:
            execution_state = "FAIL"
        elif planning_only or same_work_order_remains or after.get("final_readiness_state") == "SCIENTIFIC_BLOCKERS_REMAIN":
            execution_state = "SCIENTIFIC_BLOCKERS_REMAIN"
        else:
            execution_state = "PASS"
        row = {
            "schema_id": "OC133_ALL_DOMAIN_EXECUTION_ROW_v1",
            "work_order_id": work_order.get("work_order_id"),
            "owner_capability": work_order.get("owner_capability"),
            "profile": profile,
            "executor": executor,
            "execution_state": execution_state,
            "before_state": before.get("state"),
            "before_final_readiness_state": before.get("final_readiness_state"),
            "after_state": after.get("state"),
            "after_final_readiness_state": after.get("final_readiness_state"),
            "after_blocker_ids": after_blocker_ids,
            "command": result_cmd,
            "refs": refs,
            "artifact_exists_is_not_closure": True,
            "no_send": True,
            "publish_allowed": False,
            "journal_submissions_allowed": False,
        }
        ledger = append_ledger(row)
        return {
            "schema_id": "OC133_ALL_DOMAIN_EXECUTE_NEXT_RESULT_v1",
            "mission_id": oc133_platinum.MISSION_ID,
            "selected_work_order_id": work_order.get("work_order_id"),
            "owner_capability": work_order.get("owner_capability"),
            "profile": profile,
            "executor": executor,
            "execution_state": row["execution_state"],
            "ledger_ref": EXECUTION_LEDGER_REL,
            "ledger_latest_state": ledger.get("latest_execution_state"),
            "after_state": after.get("state"),
            "after_final_readiness_state": after.get("final_readiness_state"),
            "after_blocker_ids": after.get("blocker_ids", []),
            "no_send": True,
            "publish_allowed": False,
            "journal_submissions_allowed": False,
        }

    row = {
        "schema_id": "OC133_ALL_DOMAIN_EXECUTION_ROW_v1",
        "work_order_id": work_order.get("work_order_id"),
        "owner_capability": work_order.get("owner_capability"),
        "execution_state": "BLOCKED_NO_CAPABILITY_PROFILE",
        "required_repair": "Register a Logion capability profile before direct artifact edits.",
        "no_send": True,
        "publish_allowed": False,
        "journal_submissions_allowed": False,
    }
    append_ledger(row)
    return row


def main() -> int:
    parser = argparse.ArgumentParser(description="Logion all-domain scientific readiness controller for OC Core 1.3.3.")
    parser.add_argument("--write", action="store_true", help="Write all-domain scorecard, work orders, and cockpit.")
    parser.add_argument("--execute-next", action="store_true", help="Execute the highest-priority all-domain work order via a Logion capability profile.")
    parser.add_argument(
        "--allow-blocked-exit-zero",
        action="store_true",
        help="Return zero when the controller ran correctly but scientific blockers remain.",
    )
    args = parser.parse_args()

    execute_result = execute_next() if args.execute_next else None
    audit = enrich_readiness_dispatch(
        oc133_platinum.all_domain_readiness_audit(ROOT, oc133_platinum.content_closure_audit(ROOT))
    )
    refs = write_all_domain_outputs(audit) if args.write else {}
    payload = {
        "schema_id": "OC133_LOGION_ALL_DOMAIN_READINESS_RUN_v1",
        "mission_id": oc133_platinum.MISSION_ID,
        "release_id": oc133_platinum.RELEASE_ID,
        "version": oc133_platinum.VERSION,
        "state": audit["state"],
        "final_readiness_state": audit["final_readiness_state"],
        "external_review_ready_no_send": audit.get("external_review_ready_no_send", False),
        "full_science_program_state": audit.get("full_science_program_state"),
        "blocker_total": audit["blocker_total"],
        "blocker_ids": audit["blocker_ids"],
        "next_automatic_action": audit["next_automatic_action"],
        "execute_result": execute_result,
        "refs": refs,
        "no_send": True,
        "publish_allowed": False,
        "journal_submissions_allowed": False,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if execute_result is not None and execute_result.get("execution_state") not in {"PASS", "NOOP"}:
        if execute_result.get("execution_state") != "SCIENTIFIC_BLOCKERS_REMAIN":
            return 1
    if audit["all_domain_ready_no_send"] or audit.get("external_review_ready_no_send") is True:
        return 0
    return 0 if args.allow_blocked_exit_zero else 2


if __name__ == "__main__":
    raise SystemExit(main())
