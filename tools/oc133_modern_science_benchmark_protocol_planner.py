from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
SCHEMA_ID = "OC133_MODERN_SCIENCE_BENCHMARK_PROTOCOL_v1"
INDEX_SCHEMA_ID = "OC133_MODERN_SCIENCE_BENCHMARK_PROTOCOL_INDEX_v1"

CAPABILITY_OWNER = "Logion Research/PriorArt"
BLOCKER_ID = "modern_science_comparator_superiority"

REGISTER_REL = "comparators/OC_1_3_3_MODERN_SCIENCE_SUPERIORITY_REGISTER.json"
LANES_REL = "benchmarks/modern_science/OC133_MODERN_SCIENCE_BENCHMARK_LANES.json"
REPORT_REL = "reports/OC_CORE_1_3_3_MODERN_SCIENCE_SUPERIORITY_REPORT.json"
GRAND_REPORT_REL = "reports/OC_CORE_1_3_3_GRAND_EMPIRICAL_REPORT.json"
COVERAGE_REGISTER_REL = "comparators/modern_science/OC133_MODERN_SCIENCE_COVERAGE_REGISTER.json"
TARGET_BLIND_REL = "validation/target_blind/OC133_TARGET_BLIND_PREDICTION_TABLE.json"
NUMERIC_REPLAY_REL = "validation/numeric_replay_qa/OC133_NUMERIC_REPLAY_QA_TABLE.json"
PROTOCOL_DIR_REL = "benchmarks/modern_science/protocols"

REPO_ROOT = Path(__file__).resolve().parents[1]

SPLIT_PREDICATES = (
    ("target_blind_split_declared_before_scoring", "heldout", "target_blind"),
    ("formula_snapshot_split_declared", "heldout", "target_blind"),
    ("api_snapshot_split_declared", "heldout", "target_blind"),
    ("heldout_year_split_declared", "heldout", "target_blind"),
    ("finite_aggregate_split_declared", "heldout", "target_blind"),
    ("prospective_or_time-locked_protocol_present", "prospective", "prospective"),
)


def repo_root() -> Path:
    return REPO_ROOT


def ordered_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def safe_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def row_by(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    return {str(row.get(key)): row for row in rows if isinstance(row, dict) and row.get(key) is not None}


def rows_by(rows: list[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        row_key = row.get(key)
        if row_key is None:
            continue
        grouped.setdefault(str(row_key), []).append(row)
    return grouped


def claim_id_from_ref(ref: str) -> str:
    return ref.rsplit("::", 1)[1] if "::" in ref else ref


def protocol_file_name(domain: str) -> str:
    safe = "".join((char if char.isalnum() else "_") for char in str(domain).lower())
    return f"OC133_MODERN_SCIENCE_BENCHMARK_PROTOCOL_{safe.upper()}.json"


def split_statement(target_row: dict[str, Any], mode: str, lane_row: dict[str, Any]) -> str:
    if mode == "heldout":
        return str(target_row.get("target_blind_split", "")).strip()
    return str(lane_row.get("task", "")).strip()


def build_split_profile(lane_row: dict[str, Any], target_row: dict[str, Any]) -> dict[str, Any]:
    predicates = [str(item) for item in lane_row.get("certification_predicates", []) if str(item)]
    status = lane_row.get("current_predicate_status", {})
    for predicate, mode, source_mode in SPLIT_PREDICATES:
        if predicate not in predicates:
            continue
        declared = bool(status.get(predicate))
        return {
            "mode": mode,
            "source_separation_mode": source_mode,
            "split_predicate": predicate,
            "declared": declared,
            "source_separation_declared": declared,
            "split_statement": split_statement(target_row, mode, lane_row),
        }
    declared = False
    split_predicate = ""
    if str(target_row.get("target_blind_split", "")).strip():
        declared = True
        return {
            "mode": "heldout",
            "source_separation_mode": "target_blind",
            "split_predicate": "target_blind_split_declared_before_scoring",
            "declared": declared,
            "source_separation_declared": declared,
            "split_statement": split_statement(target_row, "heldout", lane_row),
        }
    return {
        "mode": "unknown",
        "source_separation_mode": "",
        "split_predicate": split_predicate,
        "declared": declared,
        "source_separation_declared": False,
        "split_statement": split_statement(target_row, "heldout", lane_row),
    }


def build_fairness_criteria(
    lane_row: dict[str, Any], register_row: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[str]]:
    criteria: list[dict[str, Any]] = []
    failed: list[str] = []
    predicates = [str(item) for item in lane_row.get("certification_predicates", []) if str(item)]
    status = lane_row.get("current_predicate_status", {})
    for predicate in predicates:
        predicate_status = bool(status.get(predicate))
        criteria.append(
            {
                "predicate": predicate,
                "required": True,
                "status": predicate_status,
                "blocked": not predicate_status,
            }
        )
        if not predicate_status:
            failed.append(predicate)
    for predicate in register_row.get("blocking_predicates", []):
        if not predicate:
            continue
        failed.append(str(predicate))
    return criteria, ordered_unique(failed)


def build_uncertainty_bundle(
    lane_row: dict[str, Any],
    target_row: dict[str, Any],
) -> dict[str, Any]:
    model_residual = safe_float(target_row.get("residual"))
    model_uncertainty = safe_float(target_row.get("uncertainty"))
    within = (
        (model_residual is not None and model_uncertainty is not None and model_residual <= model_uncertainty)
    )
    declared = model_uncertainty is not None
    return {
        "declared": declared,
        "uncertainty": model_uncertainty,
        "model_residual": model_residual,
        "within_declared_uncertainty": within,
        "metric_family": str(lane_row.get("metric_family", "")),
        "prediction_supported": bool(target_row.get("prediction_support_allowed")),
        "empirical_supported": bool(target_row.get("empirical_support_allowed")),
    }


def build_residual_metric(
    lane_row: dict[str, Any],
    target_row: dict[str, Any],
) -> dict[str, Any]:
    model_residual = safe_float(target_row.get("residual"))
    comparator_residual = safe_float(target_row.get("comparator_residual"))
    superiority_margin = None
    if model_residual is not None and comparator_residual is not None:
        superiority_margin = comparator_residual - model_residual
    return {
        "metric_family": str(lane_row.get("metric_family", "")),
        "model_residual": model_residual,
        "comparator_residual": comparator_residual,
        "superiority_margin": superiority_margin,
        "model_predicted": target_row.get("predicted_value"),
        "model_observed": target_row.get("observed_value"),
    }


def build_negative_controls(
    target_row: dict[str, Any],
    numeric_rows: list[dict[str, Any]],
    domain: str,
) -> list[dict[str, Any]]:
    controls: list[dict[str, Any]] = []
    if target_row.get("negative_control"):
        controls.append(
            {
                "source": "target_blind",
                "claim_ref": f"{TARGET_BLIND_REL}::{target_row.get('claim_id', '')}".strip(":"),
                "control": target_row.get("negative_control"),
                "rejected": bool(target_row.get("negative_control_rejected")),
                "domain": domain,
            }
        )
    for row in numeric_rows:
        control = str(row.get("negative_control", "")).strip()
        claim_id = str(row.get("claim_id", "")).strip()
        if not claim_id or not control:
            continue
        controls.append(
            {
                "source": "numeric_replay_qa",
                "claim_ref": f"{NUMERIC_REPLAY_REL}::{claim_id}",
                "control": control,
                "rejected": None,
                "domain": domain,
            }
        )
    if not controls:
        controls.append(
            {
                "source": "planner",
                "claim_ref": "",
                "control": "",
                "rejected": None,
                "domain": domain,
            }
        )
    return controls


def build_falsifiers(
    target_row: dict[str, Any],
    numeric_rows: list[dict[str, Any]],
    domain: str,
) -> list[dict[str, Any]]:
    falsifiers: list[dict[str, Any]] = []
    if target_row.get("falsifier"):
        falsifiers.append(
            {
                "source": "target_blind",
                "claim_ref": f"{TARGET_BLIND_REL}::{target_row.get('claim_id', '')}".strip(":"),
                "falsifier": target_row.get("falsifier"),
                "domain": domain,
            }
        )
    for row in numeric_rows:
        if row.get("falsifier"):
            falsifiers.append(
                {
                    "source": "numeric_replay_qa",
                    "claim_ref": f"{NUMERIC_REPLAY_REL}::{row.get('claim_id', '')}".strip(":"),
                    "falsifier": row.get("falsifier"),
                    "domain": domain,
                }
            )
    if not falsifiers:
        falsifiers.append(
            {
                "source": "planner",
                "claim_ref": "",
                "falsifier": "No falsifier declaration recorded for this lane",
                "domain": domain,
            }
        )
    return falsifiers


def collect_blocker_predicates(
    lane_row: dict[str, Any],
    register_row: dict[str, Any],
    report_row: dict[str, Any],
    grand_row: dict[str, Any],
    fairness_failed: list[str],
) -> list[str]:
    blockers: list[str] = []
    blockers.extend([str(item) for item in lane_row.get("blocked_by", []) if str(item)])
    blockers.extend([str(item) for item in register_row.get("blocking_predicates", []) if str(item)])
    blocker_reason = report_row.get("blocker_reason", {})
    blockers.extend([str(item) for item in blocker_reason.get("blocked_by", []) if str(item)])
    blockers.extend([str(item) for item in grand_row.get("blockers", []) if str(item)])
    blockers.extend(fairness_failed)
    return ordered_unique(blockers)


def required_result_refs(
    register_row: dict[str, Any],
    target_row: dict[str, Any],
    lane_row: dict[str, Any],
) -> list[str]:
    refs: list[str] = []
    for ref in register_row.get("oc_current_evidence_refs", []):
        if str(ref).startswith(f"{TARGET_BLIND_REL}::"):
            refs.append(str(ref))
    if target_row.get("claim_id"):
        refs.append(f"{TARGET_BLIND_REL}::{target_row.get('claim_id')}")
    comparator_ref = lane_row.get("comparator_result", {})
    if isinstance(comparator_ref, str) and comparator_ref:
        refs.append(str(comparator_ref))
    return ordered_unique([item for item in refs if item and str(item).strip()])


def can_certify_superiority(protocol: dict[str, Any]) -> bool:
    if not protocol.get("required_result_refs"):
        return False
    decision = protocol.get("superiority_decision", {})
    blockers = [str(item) for item in decision.get("blocker_predicates", []) if str(item)]
    if blockers or int(decision.get("blocker_total", 0) or 0) != 0:
        return False
    fairness_criteria = protocol.get("fairness_criteria", [])
    if not fairness_criteria:
        return False
    return all(bool(item.get("status")) for item in fairness_criteria if isinstance(item, dict))


def build_domain_protocol(
    register_row: dict[str, Any],
    lane_row: dict[str, Any],
    report_row: dict[str, Any],
    grand_row: dict[str, Any],
    target_row: dict[str, Any],
    numeric_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    domain = str(register_row.get("domain", "")).strip()
    lane_id = str(register_row.get("lane_id", lane_row.get("lane_id", ""))).strip()
    split_profile = build_split_profile(lane_row, target_row)
    fairness_criteria, fairness_failed = build_fairness_criteria(lane_row, register_row)
    required_refs = required_result_refs(register_row, target_row, lane_row)
    comparator_refs = [
        ref for ref in required_refs if str(ref).startswith(TARGET_BLIND_REL) or str(ref).startswith("validation/")
    ]
    fairness_decision_blockers = collect_blocker_predicates(
        lane_row,
        register_row,
        report_row,
        grand_row,
        fairness_failed,
    )

    protocol = {
        "schema_id": SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_on": "2026-05-01",
        "capability_owner": CAPABILITY_OWNER,
        "blocker_id": BLOCKER_ID,
        "protocol_id": f"OC133-MODERN-SCIENCE-BENCHMARK-PROTOCOL-{domain.upper()}",
        "domain": domain,
        "lane_id": lane_id,
        "predicate_id": lane_row.get("predicate_id"),
        "evidence_refs": {
            "register_ref": REGISTER_REL,
            "lane_ref": LANES_REL,
            "modern_science_superiority_report_ref": REPORT_REL,
            "grand_empirical_report_ref": GRAND_REPORT_REL,
            "target_blind_ref": TARGET_BLIND_REL,
            "numeric_replay_qa_ref": NUMERIC_REPLAY_REL,
        },
        "incumbent_comparator": {
            "incumbent": register_row.get("incumbent_modern_science"),
            "accepted_capacity": register_row.get("accepted_incumbent_capacity"),
            "source_refs": [
                {
                    "title": source.get("title"),
                    "url": source.get("url"),
                    "source_date": source.get("source_date"),
                    "local_source_capsule_ref": source.get("local_source_capsule_ref"),
                    "local_source_capsule_sha256": source.get("local_source_capsule_sha256"),
                }
                for source in register_row.get("source_refs", [])
                if isinstance(source, dict)
            ],
        },
        "oc_model_under_test": {
            "result_ref": comparator_refs[0] if comparator_refs else "",
            "claim_id": target_row.get("claim_id"),
            "dataset_snapshot_ref": target_row.get("dataset_snapshot_ref"),
            "formula_or_model": target_row.get("formula"),
            "predicted_value": target_row.get("predicted_value"),
            "observed_value": target_row.get("observed_value"),
        "residual": target_row.get("residual"),
        "uncertainty": target_row.get("uncertainty"),
        "comparator_baseline": target_row.get("comparator_baseline"),
        "comparator_prediction": target_row.get("comparator_prediction"),
            "negative_control": target_row.get("negative_control"),
            "negative_control_rejected": target_row.get("negative_control_rejected"),
            "falsifier": target_row.get("falsifier"),
            "prediction_support_allowed": target_row.get("prediction_support_allowed"),
            "empirical_support_allowed": target_row.get("empirical_support_allowed"),
            "support_scope": target_row.get("support_scope"),
        },
        "heldout_or_prospective_split": {
            "mode": split_profile["mode"],
            "source_separation_mode": split_profile["source_separation_mode"],
            "split_predicate": split_profile["split_predicate"],
            "declared": split_profile["declared"],
            "source_separation_declared": split_profile["source_separation_declared"],
            "split_statement": split_profile["split_statement"],
        },
        "fairness_criteria": fairness_criteria,
        "uncertainty": build_uncertainty_bundle(lane_row, target_row),
        "residual_metric": build_residual_metric(lane_row, target_row),
        "negative_controls": build_negative_controls(target_row, numeric_rows, domain),
        "falsifiers": build_falsifiers(target_row, numeric_rows, domain),
        "blocker_predicates": fairness_decision_blockers,
        "required_result_refs": comparator_refs,
        "report": {
            "current_verdict": lane_row.get("current_verdict"),
            "superiority_task": lane_row.get("task"),
            "allowed_current_claim": lane_row.get("allowed_current_claim"),
            "superiority_claim_status": report_row.get("superiority_claim_status") or register_row.get("superiority_claim_status"),
            "release_effect": register_row.get("release_effect"),
            "oc_current_evidence_boundary": register_row.get("oc_current_evidence_boundary"),
        },
        "grand_empirical_context": {
            "minimum_n": grand_row.get("minimum_n"),
            "valid_n": grand_row.get("valid_n"),
            "status": grand_row.get("status"),
            "grand_toe_support_allowed": grand_row.get("grand_toe_support_allowed"),
            "blockers": grand_row.get("blockers"),
        },
        "no_send": True,
        "release_promotion_allowed": False,
    }
    protocol["superiority_decision"] = {
        "status": "NOT_CERTIFIED",
        "superiority_certified": False,
        "release_promotion_allowed": False,
        "can_be_certified_within_current_artifact_scope": can_certify_superiority(protocol),
        "blocker_total": len(protocol["blocker_predicates"]),
        "blocker_predicates": protocol["blocker_predicates"],
        "required_result_refs": protocol["required_result_refs"],
        "failure_reason": (
            "All incumbent/refined fairness predicates, zero blockers, and result bindings must be present for certification."
        ),
    }
    if protocol["superiority_decision"]["can_be_certified_within_current_artifact_scope"]:
        protocol["superiority_decision"]["status"] = "READY_FOR_REVIEW_BUT_NOT_CERTIFIED"
        protocol["superiority_decision"]["failure_reason"] = "All protocol obligations are present; final certification remains blocked by contract policy."
    return protocol


def build_formal_mathematics_protocol(root: Path, coverage_register: dict[str, Any]) -> dict[str, Any]:
    protocol_only_ref: dict[str, Any] = {}
    for row in coverage_register.get("domain_class_rows", []):
        if row.get("domain_class_id") == "formal_mathematics_and_logic":
            value = row.get("protocol_only_ref", {})
            if isinstance(value, dict):
                protocol_only_ref = value
            break
    source_capsule_ref = str(
        protocol_only_ref.get("source_capsule_ref", "comparators/modern_science/source_capsules/MS-SRC-MATH-LEAN4.txt")
    )
    source_capsule_path = root / source_capsule_ref
    source_capsule_sha256 = sha256_file(source_capsule_path) if source_capsule_path.exists() else ""
    blocker_predicates = [
        "FORMAL_ROUTE_PROTOCOL_ONLY_NO_EMPIRICAL_SUPERIORITY_PROTOCOL",
        "NO_STRICT_EMPIRICAL_EVIDENCE_PACK_FOR_FORMAL_MATHEMATICS",
        "COVERAGE_REGISTER_FORMAL_GAPS_REMAIN_OPEN",
        "BROAD_MODERN_SCIENCE_SUPERIORITY_BLOCKED",
    ]
    return {
        "schema_id": SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_on": "2026-05-01",
        "capability_owner": CAPABILITY_OWNER,
        "blocker_id": BLOCKER_ID,
        "protocol_id": "OC133-MODERN-SCIENCE-BENCHMARK-PROTOCOL-MATHEMATICS",
        "domain": "mathematics",
        "lane_id": "MS-LANE-MATHEMATICS-FORMAL-ROUTE-PROTOCOL-ONLY",
        "predicate_id": "MS-PRED-MATH-FORMAL-ROUTE-001",
        "route_type": "FORMAL_ROUTE_PROTOCOL_ONLY",
        "evidence_refs": {
            "register_ref": REGISTER_REL,
            "coverage_register_ref": COVERAGE_REGISTER_REL,
            "lane_ref": LANES_REL,
            "modern_science_superiority_report_ref": REPORT_REL,
            "source_capsule_ref": source_capsule_ref,
            "source_capsule_sha256": source_capsule_sha256,
        },
        "incumbent_comparator": {
            "incumbent": "Lean 4 theorem prover and formal mathematics ecosystem",
            "accepted_capacity": "Lean 4 is an interactive theorem prover and programming language for verified programs and formal mathematics.",
            "source_refs": [
                {
                    "title": "Lean 4 official site",
                    "url": "https://lean4.dev/",
                    "source_date": "reference",
                    "local_source_capsule_ref": source_capsule_ref,
                    "local_source_capsule_sha256": source_capsule_sha256,
                }
            ],
        },
        "oc_model_under_test": {
            "result_ref": "",
            "claim_id": "",
            "dataset_snapshot_ref": "",
            "formula_or_model": "",
            "prediction_support_allowed": False,
            "empirical_support_allowed": False,
            "support_scope": "formal route/protocol-only planning; no empirical benchmark or theorem-prover superiority protocol is asserted",
        },
        "formal_route": {
            "protocol_only": True,
            "empirical_protocol_required": False,
            "strict_empirical_pack_required": False,
            "coverage_gap_status": "OPEN",
            "allowed_current_claim": "bounded formal release-consistency and proof-route planning only",
            "forbidden_claims": [
                "superior to formal mathematics",
                "superior to theorem provers",
                "empirical mathematics superiority",
                "broad modern-science superiority",
            ],
        },
        "heldout_or_prospective_split": {
            "mode": "not_applicable_formal_route",
            "source_separation_mode": "protocol_only",
            "split_predicate": "FORMAL_ROUTE_PROTOCOL_ONLY_DECLARED",
            "declared": False,
            "source_separation_declared": False,
            "split_statement": "No target-blind empirical split is required or claimed for this formal route protocol.",
        },
        "fairness_criteria": [
            {
                "predicate": "formal_route_protocol_only_declared",
                "required": True,
                "status": True,
                "blocked": False,
            },
            {
                "predicate": "claim_text_excludes_theorem_prover_or_formal_math_superiority",
                "required": True,
                "status": True,
                "blocked": False,
            },
            {
                "predicate": "source_capsule_hash_bound",
                "required": True,
                "status": bool(source_capsule_sha256),
                "blocked": not bool(source_capsule_sha256),
            },
            {
                "predicate": "strict_empirical_evidence_pack_present",
                "required": False,
                "status": False,
                "blocked": False,
            },
            {
                "predicate": "coverage_register_gap_closed",
                "required": True,
                "status": False,
                "blocked": True,
            },
        ],
        "uncertainty": {
            "declared": False,
            "uncertainty": None,
            "model_residual": None,
            "within_declared_uncertainty": False,
            "metric_family": "formal route/protocol-only; no empirical residual metric",
            "prediction_supported": False,
            "empirical_supported": False,
        },
        "residual_metric": {
            "metric_family": "formal route/protocol-only; no empirical residual metric",
            "model_residual": None,
            "comparator_residual": None,
            "superiority_margin": None,
            "model_predicted": None,
            "model_observed": None,
        },
        "negative_controls": [],
        "falsifiers": [],
        "blocker_predicates": blocker_predicates,
        "required_result_refs": [],
        "report": {
            "current_verdict": "FORMAL_ROUTE_PROTOCOL_ONLY_NOT_EMPIRICAL_SUPERIORITY",
            "superiority_task": "Maintain formal-route protocol boundary for mathematics without fabricating an empirical protocol.",
            "allowed_current_claim": "bounded formal release-consistency and proof-route planning only",
            "superiority_claim_status": "NOT_CERTIFIED",
            "release_effect": "BLOCK_RELEASE_PROMOTION_FOR_SUPERIORITY",
            "oc_current_evidence_boundary": "No empirical mathematics superiority or theorem-prover superiority evidence is asserted.",
        },
        "grand_empirical_context": {
            "minimum_n": None,
            "valid_n": 0,
            "status": "NOT_APPLICABLE_FORMAL_ROUTE",
            "grand_toe_support_allowed": False,
            "blockers": blocker_predicates,
        },
        "no_send": True,
        "release_promotion_allowed": False,
        "superiority_decision": {
            "status": "NOT_CERTIFIED",
            "superiority_certified": False,
            "release_promotion_allowed": False,
            "can_be_certified_within_current_artifact_scope": False,
            "blocker_total": len(blocker_predicates),
            "blocker_predicates": blocker_predicates,
            "required_result_refs": [],
            "failure_reason": "Mathematics is represented as a formal route/protocol-only lane; no empirical result refs are required or sufficient for superiority certification.",
        },
    }


def build_protocols(root: Path | None = None) -> list[tuple[str, dict[str, Any]]]:
    root = root or repo_root()
    register = load_json(root / REGISTER_REL)
    lanes = load_json(root / LANES_REL)
    report = load_json(root / REPORT_REL)
    grand = load_json(root / GRAND_REPORT_REL)
    coverage_register = load_json(root / COVERAGE_REGISTER_REL)
    target_blind = load_json(root / TARGET_BLIND_REL)
    numeric_replay = load_json(root / NUMERIC_REPLAY_REL)

    lane_by_id = row_by(lanes.get("lanes", []), "lane_id")
    report_by_domain = row_by(report.get("domain_evidence_matrix", []), "domain")
    grand_by_domain = row_by(grand.get("domains", []), "domain")
    target_by_id = row_by(target_blind.get("rows", []), "claim_id")
    target_by_domain = row_by(target_blind.get("rows", []), "lane")
    numeric_by_domain = rows_by(numeric_replay.get("rows", []), "lane")

    protocols: list[tuple[str, dict[str, Any]]] = []
    seen_domains: set[str] = set()
    for row in register.get("rows", []):
        if not isinstance(row, dict):
            continue
        domain = str(row.get("domain", "")).strip()
        lane_row = lane_by_id.get(str(row.get("lane_id", "")), {})
        report_row = report_by_domain.get(domain, {})
        grand_row = grand_by_domain.get(domain, {})
        oc_ref = ""
        for ref in row.get("oc_current_evidence_refs", []):
            if str(ref).startswith(TARGET_BLIND_REL):
                oc_ref = str(ref)
                break
        target_row = (
            target_by_id.get(claim_id_from_ref(oc_ref), {})
            or target_by_domain.get(domain, {})
            or {}
        )
        numeric_rows = numeric_by_domain.get(domain, [])
        protocols.append((domain, build_domain_protocol(row, lane_row, report_row, grand_row, target_row, numeric_rows)))
        seen_domains.add(domain)
    if "mathematics" not in seen_domains:
        protocols.append(("mathematics", build_formal_mathematics_protocol(root, coverage_register)))
    return protocols


def build_all(root: Path | None = None) -> dict[str, Any]:
    root = root or repo_root()
    payloads: dict[str, Any] = {}
    protocol_rows: list[dict[str, Any]] = []
    for domain, protocol in build_protocols(root):
        rel = f"{PROTOCOL_DIR_REL}/{protocol_file_name(domain)}"
        payloads[rel] = protocol
        protocol_rows.append(
            {
                "domain": domain,
                "protocol_ref": rel,
                "protocol_sha256": hashlib.sha256(
                    json.dumps(protocol, sort_keys=True, separators=(",", ":")).encode("utf-8")
                ).hexdigest(),
            }
        )
    payloads[f"{PROTOCOL_DIR_REL}/index.json"] = {
        "schema_id": INDEX_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_on": "2026-05-01",
        "capability_owner": CAPABILITY_OWNER,
        "protocol_dir": PROTOCOL_DIR_REL,
        "protocol_total": len(protocol_rows),
        "protocols": protocol_rows,
        "protocol_rows": protocol_rows,
    }
    return payloads


def check_stored(root: Path | None = None) -> list[str]:
    root = root or repo_root()
    expected = build_all(root)
    errors: list[str] = []
    for rel, payload in expected.items():
        path = root / rel
        if not path.exists():
            errors.append(f"missing protocol artifact: {rel}")
            continue
        actual = load_json(path)
        if actual != payload:
            errors.append(f"{rel} is not synchronized with planner output")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build modern-science superiority benchmark protocol artifacts."
    )
    parser.add_argument("--write", action="store_true", help="Write per-domain protocol artifacts.")
    parser.add_argument("--check", action="store_true", help="Check generated artifacts are synchronized.")
    args = parser.parse_args(argv)

    root = repo_root()
    if args.write:
        payloads = build_all(root)
        for rel, payload in payloads.items():
            write_json(root / rel, payload)
        print(f"wrote {len(payloads)} modern-science benchmark protocol artifacts")
        return 0

    errors = check_stored(root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("modern-science benchmark protocol planner check passed; superiority remains blocked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
