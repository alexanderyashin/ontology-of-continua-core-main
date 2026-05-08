from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any


RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
EVIDENCE_OWNER = "Research/EmpiricalScience"

EVIDENCE_SCHEMA_ID = "OC133_GRAND_EMPIRICAL_EVIDENCE_v1"
PROTOCOL_SCHEMA_ID = "OC133_PHYSICS_CHEMISTRY_EVIDENCE_PROTOCOL_v1"

DOMAINS = ("physics", "chemistry")

EXECUTOR_REL = "validation/heldout/domain_evidence/physics_chemistry_evidence_executor.py"
OUTPUT_DIR_REL = "validation/heldout/grand_science/physics_chemistry"
REQUIREMENTS_REL = "benchmarks/grand_science/domain_requirements.json"
TARGET_BLIND_REL = "validation/target_blind/OC133_TARGET_BLIND_PREDICTION_TABLE.json"
NUMERIC_REPLAY_QA_REL = "validation/numeric_replay_qa/OC133_NUMERIC_REPLAY_QA_TABLE.json"
NUMERIC_REPLAY_LOG_REL = "validation/numeric_predictions/OC133_NUMERIC_REPLAY_LOG.json"

MINIMUM_N_DEFAULT = 20
HASH_POLICY = "LF_NORMALIZED_TEXT_SNAPSHOT_HASH"
PACK_HASH_POLICY = "sha256 over sorted JSON evidence pack"

GRAND_SUPPORT_SCOPE_BLOCKERS = (
    "bounded",
    "not a novel",
    "not a new",
    "not a physics law",
    "not a chemistry law",
    "not broad",
    "qa only",
    "not a prediction",
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def sha256_object(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def lf_normalized_bytes(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n")


def sha256_lf_normalized_text(path: Path) -> str:
    return hashlib.sha256(lf_normalized_bytes(path)).hexdigest()


def rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def ordered_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def as_float(value: Any) -> float | None:
    if not is_number(value):
        return None
    return float(value)


def close_enough(left: float | None, right: float | None) -> bool:
    if left is None or right is None:
        return False
    scale = max(abs(left), abs(right), 1e-300)
    return abs(left - right) <= max(scale * 1e-12, 1e-40)


def contains_blocking_scope(scope: str) -> bool:
    lowered = scope.lower()
    return any(fragment in lowered for fragment in GRAND_SUPPORT_SCOPE_BLOCKERS)


def minimum_n(root: Path) -> int:
    requirements = read_json(root / REQUIREMENTS_REL)
    value = requirements.get("minimum_per_domain_n", MINIMUM_N_DEFAULT)
    return int(value) if isinstance(value, int) and not isinstance(value, bool) else MINIMUM_N_DEFAULT


def target_blind_rows(root: Path, domain: str) -> list[dict[str, Any]]:
    payload = read_json(root / TARGET_BLIND_REL)
    rows = payload.get("rows", [])
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict) and row.get("lane") == domain]


def numeric_replay_rows(root: Path, domain: str) -> list[dict[str, Any]]:
    payload = read_json(root / NUMERIC_REPLAY_QA_REL)
    rows = payload.get("rows", [])
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict) and row.get("lane") == domain]


def snapshot_hash_record(root: Path, snapshot_ref: str) -> dict[str, Any]:
    path = root / snapshot_ref
    exists = path.is_file()
    return {
        "source_ref": snapshot_ref,
        "exists": exists,
        "sha256": sha256_lf_normalized_text(path) if exists else None,
        "byte_count": len(lf_normalized_bytes(path)) if exists else 0,
        "hash_policy": HASH_POLICY,
    }


def row_hash(row: dict[str, Any]) -> str:
    stripped = {key: value for key, value in row.items() if key not in {"replay_hash", "replay_hash_policy"}}
    return sha256_object(stripped)


def row_source_separation(row: dict[str, Any]) -> dict[str, Any]:
    claim_id = str(row.get("claim_id") or "UNKNOWN")
    snapshot_ref = str(row.get("dataset_snapshot_ref") or "")
    split = str(row.get("target_blind_split") or "")
    split_lower = split.lower()
    target_hidden = "withheld" in split_lower or "hidden" in split_lower or "until scoring" in split_lower
    return {
        "mode": "target_blind",
        "pre_target_lock": bool(snapshot_ref and split),
        "target_hidden_until_scoring": target_hidden,
        "training_source": f"{snapshot_ref}::{claim_id}::visible-training-fields",
        "target_source": f"{snapshot_ref}::{claim_id}::withheld-target-field",
        "split_statement": split,
    }


def validate_target_blind_row(root: Path, row: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    warnings: list[str] = []
    required = (
        "claim_id",
        "dataset_snapshot_ref",
        "target_blind_split",
        "formula",
        "predicted_value",
        "observed_value",
        "uncertainty",
        "comparator_baseline",
        "comparator_prediction",
        "residual",
        "comparator_residual",
        "negative_control",
        "negative_control_rejected",
        "falsifier",
    )
    for field in required:
        if field not in row or row.get(field) in ("", None):
            failures.append(f"MISSING_FIELD::{field}")

    predicted = as_float(row.get("predicted_value"))
    observed = as_float(row.get("observed_value"))
    uncertainty = as_float(row.get("uncertainty"))
    comparator_prediction = as_float(row.get("comparator_prediction"))
    residual = as_float(row.get("residual"))
    comparator_residual = as_float(row.get("comparator_residual"))

    computed_residual = abs(predicted - observed) if predicted is not None and observed is not None else None
    computed_comparator_residual = (
        abs(comparator_prediction - observed)
        if comparator_prediction is not None and observed is not None
        else None
    )

    if uncertainty is None or uncertainty < 0:
        failures.append("UNCERTAINTY_INVALID")
    if residual is None or residual < 0:
        failures.append("MODEL_RESIDUAL_INVALID")
    if comparator_residual is None or comparator_residual < 0:
        failures.append("COMPARATOR_RESIDUAL_INVALID")
    if not close_enough(computed_residual, residual):
        failures.append("MODEL_RESIDUAL_MISMATCH")
    if not close_enough(computed_comparator_residual, comparator_residual):
        failures.append("COMPARATOR_RESIDUAL_MISMATCH")
    if residual is not None and comparator_residual is not None and comparator_residual <= residual:
        failures.append("COMPARATOR_NOT_WORSE_THAN_MODEL")
    if uncertainty is not None and residual is not None and residual > uncertainty:
        failures.append("MODEL_RESIDUAL_EXCEEDS_UNCERTAINTY")
    if row.get("negative_control_rejected") is not True:
        failures.append("NEGATIVE_CONTROL_NOT_REJECTED")
    if not str(row.get("formula") or "").strip():
        failures.append("FORMULA_MISSING")
    if not str(row.get("comparator_baseline") or "").strip():
        failures.append("COMPARATOR_BASELINE_MISSING")
    if not str(row.get("negative_control") or "").strip():
        failures.append("NEGATIVE_CONTROL_MISSING")
    if not str(row.get("falsifier") or "").strip():
        failures.append("FALSIFIER_MISSING")

    separation = row_source_separation(row)
    if separation["pre_target_lock"] is not True:
        failures.append("SOURCE_SEPARATION_PRE_TARGET_LOCK_NOT_VALIDATED")
    if separation["target_hidden_until_scoring"] is not True:
        failures.append("SOURCE_SEPARATION_TARGET_NOT_HIDDEN")
    if separation["training_source"] == separation["target_source"]:
        failures.append("SOURCE_SEPARATION_TRAINING_TARGET_OVERLAP")

    snapshot_ref = str(row.get("dataset_snapshot_ref") or "")
    hash_record = snapshot_hash_record(root, snapshot_ref) if snapshot_ref else {
        "source_ref": snapshot_ref,
        "exists": False,
        "sha256": None,
        "byte_count": 0,
        "hash_policy": HASH_POLICY,
    }
    declared_snapshot_sha = row.get("snapshot_sha256")
    if not hash_record["exists"]:
        failures.append("SNAPSHOT_SOURCE_MISSING")
    elif declared_snapshot_sha and declared_snapshot_sha != hash_record["sha256"]:
        failures.append("SNAPSHOT_SHA256_MISMATCH")
    elif not declared_snapshot_sha:
        warnings.append("SNAPSHOT_SHA256_NOT_DECLARED_BY_SOURCE_ROW")

    support_scope = str(row.get("support_scope") or "")
    scope_blocks = contains_blocking_scope(support_scope)
    if scope_blocks:
        warnings.append("SOURCE_SCOPE_LIMITS_GRAND_SUPPORT")

    tamper_tests = build_tamper_tests(row, hash_record)
    replay_hash = row_hash(row)
    return {
        "claim_id": row.get("claim_id"),
        "domain": row.get("lane"),
        "source_kind": "target_blind",
        "source_ref": f"{TARGET_BLIND_REL}::{row.get('claim_id')}",
        "dataset_snapshot_ref": snapshot_ref,
        "snapshot_hash": hash_record,
        "declared_snapshot_sha256": declared_snapshot_sha,
        "row_sha256": replay_hash,
        "row_sha256_policy": "sha256 over sorted JSON row excluding replay_hash fields",
        "formula": row.get("formula"),
        "predicted_value": predicted,
        "observed_value": observed,
        "uncertainty": uncertainty,
        "computed_residual": computed_residual,
        "declared_residual": residual,
        "comparator_baseline": row.get("comparator_baseline"),
        "comparator_prediction": comparator_prediction,
        "computed_comparator_residual": computed_comparator_residual,
        "declared_comparator_residual": comparator_residual,
        "negative_control": row.get("negative_control"),
        "negative_control_rejected": row.get("negative_control_rejected") is True,
        "falsifier": row.get("falsifier"),
        "source_separation": separation,
        "support_scope": support_scope,
        "grand_scope_blocked": scope_blocks,
        "grand_empirical_support_allowed_by_source": row.get("grand_empirical_support_allowed") is True,
        "prediction_support_allowed": row.get("prediction_support_allowed") is True,
        "empirical_support_allowed": row.get("empirical_support_allowed") is True,
        "field_failure_total": len(ordered_unique(failures)),
        "field_failures": ordered_unique(failures),
        "warnings": ordered_unique(warnings),
        "tamper_tests": tamper_tests,
        "usable_for_blocked_candidate_pack": not failures,
        "eligible_for_valid_grand_pack": (
            not failures
            and not scope_blocks
            and row.get("prediction_support_allowed") is True
            and row.get("empirical_support_allowed") is True
            and row.get("grand_empirical_support_allowed") is True
        ),
    }


def build_tamper_tests(row: dict[str, Any], hash_record: dict[str, Any]) -> list[dict[str, Any]]:
    predicted = as_float(row.get("predicted_value"))
    observed = as_float(row.get("observed_value"))
    uncertainty = as_float(row.get("uncertainty"))
    residual = as_float(row.get("residual"))
    comparator_residual = as_float(row.get("comparator_residual"))

    tests: list[dict[str, Any]] = []
    if hash_record.get("sha256"):
        tampered_hash = hashlib.sha256((str(hash_record["sha256"]) + "::tamper").encode("utf-8")).hexdigest()
        tests.append(
            {
                "test_id": f"{row.get('claim_id')}-snapshot-hash-tamper",
                "kind": "tamper",
                "passed": tampered_hash != hash_record["sha256"],
                "expected_rejection": "SNAPSHOT_SHA256_MISMATCH",
            }
        )

    comparator_equal_model_residual = residual if residual is not None else None
    tests.append(
        {
            "test_id": f"{row.get('claim_id')}-comparator-equals-model-control",
            "kind": "negative_control",
            "passed": (
                comparator_equal_model_residual is not None
                and comparator_residual is not None
                and comparator_equal_model_residual <= comparator_residual
                and comparator_equal_model_residual <= residual
            ),
            "expected_rejection": "COMPARATOR_NOT_WORSE_THAN_MODEL",
        }
    )

    if predicted is not None and observed is not None and uncertainty is not None:
        shift = uncertainty * 2 if uncertainty > 0 else 1.0
        tampered_observed = observed + shift
        tampered_residual = abs(predicted - tampered_observed)
        tests.append(
            {
                "test_id": f"{row.get('claim_id')}-target-shift-falsifier",
                "kind": "falsifier",
                "passed": tampered_residual > uncertainty,
                "expected_rejection": "MODEL_RESIDUAL_EXCEEDS_UNCERTAINTY",
            }
        )

    return tests


def audit_numeric_replay_row(root: Path, row: dict[str, Any]) -> dict[str, Any]:
    snapshot_ref = str(row.get("dataset_snapshot_ref") or "")
    hash_record = snapshot_hash_record(root, snapshot_ref) if snapshot_ref else {
        "source_ref": snapshot_ref,
        "exists": False,
        "sha256": None,
        "byte_count": 0,
        "hash_policy": HASH_POLICY,
    }
    blockers = ["NUMERIC_REPLAY_QA_QUARANTINED_NOT_GRAND_EVIDENCE"]
    if row.get("prediction_support_allowed") is not False:
        blockers.append("NUMERIC_REPLAY_PREDICTION_SUPPORT_FLAG_NOT_FALSE")
    if row.get("empirical_support_allowed") is not False:
        blockers.append("NUMERIC_REPLAY_EMPIRICAL_SUPPORT_FLAG_NOT_FALSE")
    return {
        "claim_id": row.get("claim_id"),
        "domain": row.get("lane"),
        "source_kind": "numeric_replay_qa",
        "source_ref": f"{NUMERIC_REPLAY_QA_REL}::{row.get('claim_id')}",
        "dataset_snapshot_ref": snapshot_ref,
        "snapshot_hash": hash_record,
        "replay_rule": row.get("replay_rule"),
        "split_policy": row.get("split_policy"),
        "replay_residual": row.get("replay_residual"),
        "comparator_residual": row.get("comparator_residual"),
        "negative_control": row.get("negative_control"),
        "falsifier": row.get("falsifier"),
        "performance_metric_allowed": row.get("performance_metric_allowed") is True,
        "blockers": blockers,
    }


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def candidate_pack(domain: str, cases: list[dict[str, Any]], min_n: int, support_allowed: bool) -> dict[str, Any]:
    usable = [case for case in cases if case.get("usable_for_blocked_candidate_pack")]
    n = len(usable)
    model_residuals = [float(case["declared_residual"]) for case in usable if is_number(case.get("declared_residual"))]
    comparator_residuals = [
        float(case["declared_comparator_residual"])
        for case in usable
        if is_number(case.get("declared_comparator_residual"))
    ]
    uncertainties = [float(case["uncertainty"]) for case in usable if is_number(case.get("uncertainty"))]
    aggregate_model = mean(model_residuals)
    aggregate_comparator = mean(comparator_residuals)
    interval_high = max([aggregate_model, *uncertainties], default=0.0)
    formulas = ordered_unique([str(case.get("formula")) for case in usable if str(case.get("formula") or "").strip()])
    comparators = ordered_unique(
        [str(case.get("comparator_baseline")) for case in usable if str(case.get("comparator_baseline") or "").strip()]
    )
    training_sources = ordered_unique(
        [str(case["source_separation"]["training_source"]) for case in usable if isinstance(case.get("source_separation"), dict)]
    )
    target_sources = ordered_unique(
        [str(case["source_separation"]["target_source"]) for case in usable if isinstance(case.get("source_separation"), dict)]
    )

    if not training_sources:
        training_sources = [f"{OUTPUT_DIR_REL}/{domain}_protocol.json::BLOCKED_NO_TRAINING_SOURCE"]
    if not target_sources:
        target_sources = [f"{OUTPUT_DIR_REL}/{domain}_protocol.json::BLOCKED_NO_TARGET_SOURCE"]

    if len(formulas) == 1:
        model_under_test = formulas[0]
    elif formulas:
        model_under_test = f"mean absolute residual over {n} pre-registered target-blind {domain} formulas"
    else:
        model_under_test = f"BLOCKED_NO_USABLE_{domain.upper()}_FORMULA"

    if len(comparators) == 1:
        comparator_name = comparators[0]
    elif comparators:
        comparator_name = f"per-row declared {domain} comparator baselines"
    else:
        comparator_name = f"BLOCKED_NO_USABLE_{domain.upper()}_COMPARATOR"

    negative_controls = [
        {
            "control_id": f"{case.get('claim_id')}-NEGATIVE-CONTROL",
            "description": str(case.get("negative_control")),
            "rejected": case.get("negative_control_rejected") is True,
        }
        for case in usable
        if str(case.get("negative_control") or "").strip()
    ]
    falsifiers = ordered_unique([str(case.get("falsifier")) for case in usable if str(case.get("falsifier") or "").strip()])

    if not negative_controls:
        negative_controls = [
            {
                "control_id": f"BLOCKED-{domain.upper()}-NEGATIVE-CONTROL-MISSING",
                "description": "No usable source row supplied a rejected negative control.",
                "rejected": False,
            }
        ]
    if not falsifiers:
        falsifiers = [f"BLOCKED_NO_USABLE_{domain.upper()}_FALSIFIER"]

    return {
        "schema_id": EVIDENCE_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "evidence_owner": EVIDENCE_OWNER,
        "evidence_pack_id": f"OC133-GRAND-{domain.upper()}-PHYSICS-CHEMISTRY-CANDIDATE",
        "domain": domain,
        "source_separation": {
            "mode": "target_blind",
            "pre_target_lock": bool(usable) and all(case["source_separation"]["pre_target_lock"] is True for case in usable),
            "target_hidden_until_scoring": bool(usable)
            and all(case["source_separation"]["target_hidden_until_scoring"] is True for case in usable),
            "training_sources": training_sources,
            "target_sources": target_sources,
        },
        "n": n,
        "model_under_test": model_under_test,
        "comparator_baseline": {
            "name": comparator_name,
            "prediction_rule": (
                "Use each row's pre-declared comparator_prediction against the same withheld target; "
                "aggregate by mean absolute residual."
            ),
            "pre_registered": bool(usable),
        },
        "uncertainty": {
            "metric": "mean absolute residual",
            "method": (
                "Target-blind row declared uncertainty; interval upper bound is max(row uncertainty, aggregate model residual). "
                "Pack remains blocked unless N and grand-scope predicates pass."
            ),
            "interval": [0.0, interval_high],
        },
        "residuals": {
            "model": aggregate_model,
            "comparator": aggregate_comparator,
            "superiority_margin": aggregate_comparator - aggregate_model,
        },
        "negative_controls": negative_controls,
        "falsifiers": falsifiers,
        "grand_toe_support_allowed": support_allowed,
    }


def grand_factory_failures(root: Path, pack: dict[str, Any]) -> list[str]:
    inserted = False
    root_text = str(root)
    if root_text not in sys.path:
        sys.path.insert(0, root_text)
        inserted = True
    try:
        from validation.grand_science import evidence_pack_factory

        requirements = read_json(root / REQUIREMENTS_REL)
        return evidence_pack_factory.pack_failure_reasons(pack, requirements)
    except Exception as exc:  # pragma: no cover - defensive CLI path
        return [f"GRAND_FACTORY_VALIDATION_UNAVAILABLE::{exc.__class__.__name__}"]
    finally:
        if inserted:
            try:
                sys.path.remove(root_text)
            except ValueError:
                pass


def domain_protocol(root: Path, domain: str, min_n: int) -> tuple[dict[str, Any], dict[str, Any]]:
    cases = [validate_target_blind_row(root, row) for row in target_blind_rows(root, domain)]
    numeric_audits = [audit_numeric_replay_row(root, row) for row in numeric_replay_rows(root, domain)]
    usable = [case for case in cases if case.get("usable_for_blocked_candidate_pack")]
    eligible = [case for case in cases if case.get("eligible_for_valid_grand_pack")]

    blockers: list[str] = []
    if len(eligible) < min_n:
        blockers.append(f"GENUINE_EVIDENCE_N_BELOW_MINIMUM::{len(eligible)}/{min_n}")
    if not eligible:
        blockers.append("NO_GRAND_ELIGIBLE_TARGET_BLIND_OR_PROSPECTIVE_ROWS")
    if any(case.get("field_failures") for case in cases):
        blockers.append(
            f"CANDIDATE_SOURCE_OR_FIELD_FAILURES::{sum(len(case.get('field_failures', [])) for case in cases)}"
        )
    if any(case.get("grand_scope_blocked") for case in cases):
        blockers.append("CURRENT_SOURCE_SCOPE_IS_BOUNDED_BASELINE_NOT_GRAND_DOMAIN_EVIDENCE")
    if numeric_audits:
        blockers.append(f"NUMERIC_REPLAY_QA_ROWS_QUARANTINED_NOT_PREDICTION::{len(numeric_audits)}")

    support_allowed = not blockers and len(eligible) >= min_n
    pack_cases = eligible if support_allowed else usable
    pack = candidate_pack(domain, pack_cases, min_n, support_allowed)
    pack_failures = grand_factory_failures(root, pack)
    pack_sha = sha256_object(pack)

    protocol = {
        "domain": domain,
        "minimum_n": min_n,
        "available_target_blind_case_total": len(cases),
        "usable_blocked_candidate_case_total": len(usable),
        "grand_eligible_case_total": len(eligible),
        "available_numeric_replay_qa_total": len(numeric_audits),
        "candidate_pack_ref": f"{OUTPUT_DIR_REL}/{domain}_candidate_evidence_pack.json",
        "candidate_pack_sha256": pack_sha,
        "candidate_pack_hash_policy": PACK_HASH_POLICY,
        "candidate_pack_valid_under_current_grand_schema": not pack_failures,
        "candidate_pack_grand_schema_failures": pack_failures,
        "grand_toe_support_allowed_by_executor": support_allowed,
        "status": "EVIDENCE_PACK_VALID_PENDING_PARENT_REVIEW" if support_allowed else "BLOCKED_PENDING_GENUINE_EVIDENCE_PACK",
        "blockers": ordered_unique(blockers),
        "target_blind_cases": cases,
        "numeric_replay_qa_audits": numeric_audits,
        "tamper_and_negative_control_tests": [
            test for case in cases for test in case.get("tamper_tests", [])
        ],
        "protocol_steps_to_unblock": [
            "pre-register physics/chemistry model, comparator, residual metric, uncertainty method, negative controls, and falsifiers before scoring",
            "use source snapshots whose target fields remain hidden until scoring or a genuinely prospective source",
            "record LF-normalized snapshot hashes and candidate-pack hashes",
            f"collect at least {min_n} eligible rows per domain; numeric replay QA rows do not count",
            "exclude rows whose own support scope says bounded, QA-only, or not a domain/novel-law claim",
            "route candidate packs to the parent registry only after grand schema validation is clean",
        ],
    }
    return pack, protocol


def render_readme(protocol: dict[str, Any]) -> str:
    lines = [
        "# Physics/Chemistry Grand Evidence Capability",
        "",
        "This directory is generated by `validation/heldout/domain_evidence/physics_chemistry_evidence_executor.py`.",
        "",
        "It contains schema-shaped candidate packs plus a sidecar protocol/audit packet. Current OC133 physics and chemistry rows are bounded target-blind or numeric replay evidence, so they are not promoted to grand empirical support.",
        "",
        "| Domain | Candidate pack | Valid under grand schema | Eligible N | Minimum N | Status |",
        "| --- | --- | --- | ---: | ---: | --- |",
    ]
    for row in protocol.get("domains", []):
        lines.append(
            "| `{domain}` | `{pack}` | `{valid}` | `{eligible}` | `{minimum}` | `{status}` |".format(
                domain=row.get("domain"),
                pack=row.get("candidate_pack_ref"),
                valid=str(row.get("candidate_pack_valid_under_current_grand_schema")).lower(),
                eligible=row.get("grand_eligible_case_total"),
                minimum=row.get("minimum_n"),
                status=row.get("status"),
            )
        )
    lines.extend(
        [
            "",
            "Do not register these packs as release evidence while the protocol status is blocked.",
            "",
        ]
    )
    return "\n".join(lines)


def build_all(root: Path | None = None) -> dict[str, dict[str, Any] | str]:
    root = root or repo_root()
    min_n = minimum_n(root)
    payloads: dict[str, dict[str, Any] | str] = {}
    domain_protocols: list[dict[str, Any]] = []
    for domain in DOMAINS:
        pack, protocol = domain_protocol(root, domain, min_n)
        payloads[f"{OUTPUT_DIR_REL}/{domain}_candidate_evidence_pack.json"] = pack
        domain_protocols.append(protocol)

    full_protocol: dict[str, Any] = {
        "schema_id": PROTOCOL_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "evidence_owner": EVIDENCE_OWNER,
        "executor": EXECUTOR_REL,
        "requirements_ref": REQUIREMENTS_REL,
        "evidence_schema_ref": "validation/grand_science/grand_empirical_evidence.schema.json",
        "target_blind_ref": TARGET_BLIND_REL,
        "numeric_replay_qa_ref": NUMERIC_REPLAY_QA_REL,
        "numeric_replay_log_ref": NUMERIC_REPLAY_LOG_REL,
        "minimum_per_domain_n": min_n,
        "domains": domain_protocols,
        "candidate_pack_total": len(domain_protocols),
        "valid_candidate_pack_total": sum(
            1 for row in domain_protocols if row.get("candidate_pack_valid_under_current_grand_schema") is True
        ),
        "blocked_candidate_pack_total": sum(
            1 for row in domain_protocols if row.get("candidate_pack_valid_under_current_grand_schema") is not True
        ),
        "no_fabricated_success_policy": (
            "This executor emits grand schema-valid packs only when source separation, fields, negative controls, "
            "falsifiers, N, and explicit grand-scope predicates pass. Current bounded target-blind and numeric replay "
            "rows are routed as blocked candidates/protocol evidence."
        ),
    }
    full_protocol["protocol_sha256"] = sha256_object({key: value for key, value in full_protocol.items() if key != "protocol_sha256"})
    payloads[f"{OUTPUT_DIR_REL}/OC133_PHYSICS_CHEMISTRY_EVIDENCE_PROTOCOL.json"] = full_protocol
    payloads[f"{OUTPUT_DIR_REL}/README.md"] = render_readme(full_protocol)
    return payloads


def write_outputs(root: Path | None = None) -> dict[str, dict[str, Any] | str]:
    root = root or repo_root()
    payloads = build_all(root)
    for rel_path, payload in payloads.items():
        path = root / rel_path
        if isinstance(payload, str):
            write_text(path, payload)
        else:
            write_json(path, payload)
    return payloads


def check_stored(root: Path | None = None) -> list[str]:
    root = root or repo_root()
    expected = build_all(root)
    failures: list[str] = []
    for rel_path, payload in expected.items():
        path = root / rel_path
        if isinstance(payload, str):
            actual = path.read_text(encoding="utf-8") if path.exists() else ""
            if actual != payload:
                failures.append(f"{rel_path} is not synchronized with {EXECUTOR_REL}")
        else:
            actual = read_json(path)
            if actual != payload:
                failures.append(f"{rel_path} is not synchronized with {EXECUTOR_REL}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Build or check physics/chemistry grand empirical candidate packs.")
    parser.add_argument("--write", action="store_true", help="Write candidate packs and protocol artifacts.")
    parser.add_argument("--check", action="store_true", help="Check stored artifacts against deterministic executor output.")
    args = parser.parse_args()
    root = repo_root()

    if args.write:
        payloads = write_outputs(root)
        protocol = payloads[f"{OUTPUT_DIR_REL}/OC133_PHYSICS_CHEMISTRY_EVIDENCE_PROTOCOL.json"]
        assert isinstance(protocol, dict)
        print(
            "physics/chemistry evidence artifacts materialized; "
            f"valid candidate packs: {protocol['valid_candidate_pack_total']}/{protocol['candidate_pack_total']}"
        )
        return 0

    errors = check_stored(root) if args.check else []
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    if args.check:
        print("physics/chemistry evidence artifact check passed")
        return 0

    protocol = build_all(root)[f"{OUTPUT_DIR_REL}/OC133_PHYSICS_CHEMISTRY_EVIDENCE_PROTOCOL.json"]
    assert isinstance(protocol, dict)
    print(json.dumps(protocol, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
