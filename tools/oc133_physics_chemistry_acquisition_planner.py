from __future__ import annotations

import argparse
import hashlib
import json
import math
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
CAPABILITY_OWNER = "Research/EmpiricalScience"
SCHEMA_ID = "OC133_PHYSICS_CHEMISTRY_ACQUISITION_PLAN_v1"
PROTOCOL_SCHEMA_ID = "OC133_PHYSICS_CHEMISTRY_ACQUISITION_PROTOCOL_v1"
BLOCKER_ID = "grand_toe_empirical_superiority"

OUTPUT_DIR_REL = "validation/heldout/acquisition_plans/physics_chemistry"
PLAN_JSON_REL = f"{OUTPUT_DIR_REL}/OC133_PHYSICS_CHEMISTRY_ACQUISITION_PLAN.json"
PROTOCOL_JSON_REL = f"{OUTPUT_DIR_REL}/OC133_PHYSICS_CHEMISTRY_ACQUISITION_PROTOCOL.json"
PLAN_MD_REL = f"{OUTPUT_DIR_REL}/README.md"

REQUIREMENTS_REL = "benchmarks/grand_science/domain_requirements.json"
EVIDENCE_SCHEMA_REL = "validation/grand_science/grand_empirical_evidence.schema.json"
PROTOCOL_SCHEMA_REL = "validation/grand_science/grand_empirical_protocol.schema.json"
TARGET_BLIND_REL = "validation/target_blind/OC133_TARGET_BLIND_PREDICTION_TABLE.json"
NUMERIC_REPLAY_REL = "validation/numeric_replay_qa/OC133_NUMERIC_REPLAY_QA_TABLE.json"
MANIFEST_REL = "data/OC_DATASET_SNAPSHOT_MANIFEST_1_3_3.json"

DOMAINS = ("physics", "chemistry")
OFFICIAL_SOURCE_IDS = {
    "physics": ("physics_nist_constants",),
    "chemistry": ("chemistry_pubchem_water", "chemistry_nist_webbook_water"),
}

DEFAULT_REQUIREMENTS: dict[str, Any] = {
    "schema_id": "OC133_GRAND_EMPIRICAL_DOMAIN_REQUIREMENTS_v1",
    "release_id": RELEASE_ID,
    "capability_owner": "Research/EmpiricalScience",
    "minimum_per_domain_n": 20,
    "required_domains": ["biology", "chemistry", "mathematics", "physics", "systems"],
    "required_source_separation_modes": ["prospective", "target_blind"],
    "criteria": {
        "pre_target_lock_required": True,
        "target_hidden_until_scoring_required": True,
        "negative_control_rejection_required": True,
        "falsifier_required": True,
        "uncertainty_interval_required": True,
        "current_target_blind_reconstructions_are_bounded_baseline_only": True,
    },
}
NO_SEND_POLICY = (
    "No support is emitted by this planner. "
    "Existing bounded target-blind reconstructions and replay QA rows are treated as blockers. "
    "Only a future preregistered candidate pack can drive grand TOE support."
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def ordered_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def canonical_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk.replace(b"\r\n", b"\n"))
    return h.hexdigest()


def as_float(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def requirements_from_root(root: Path) -> tuple[dict[str, Any], list[str]]:
    requirements = read_json(root / REQUIREMENTS_REL)
    if not requirements:
        return dict(DEFAULT_REQUIREMENTS), ["REQUIREMENTS_MISSING_USING_DEFAULTS"]
    return requirements, []


def read_manifest(root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    payload = read_json(root / MANIFEST_REL)
    rows = payload.get("rows", [])
    if not isinstance(rows, list):
        return [], [f"MANIFEST_ROWS_NOT_LIST::{MANIFEST_REL}"]
    return [row for row in rows if isinstance(row, dict)], []


def read_rows(path: Path, domain: str) -> list[dict[str, Any]]:
    payload = read_json(path)
    rows = payload.get("rows", [])
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict) and str(row.get("lane", "")) == domain]


def check_url(url: str, timeout: float) -> tuple[bool, str]:
    if not url:
        return False, "EMPTY_URL"
    try:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=timeout) as response:
            code = int(getattr(response, "status", 0))
            return 200 <= code < 400, str(code)
    except Exception as exc:  # pragma: no cover - network boundary
        return False, exc.__class__.__name__


def source_snapshot_rows(
    root: Path,
    domain: str,
    manifest_rows: list[dict[str, Any]],
    check_endpoints: bool,
    endpoint_timeout: float,
) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    blockers: list[str] = []
    expected_ids = set(OFFICIAL_SOURCE_IDS.get(domain, ()))
    found_ids: set[str] = set()
    for row in manifest_rows:
        if row.get("source_id") not in expected_ids:
            continue
        source_id = str(row.get("source_id", ""))
        found_ids.add(source_id)
        local_snapshot = str(row.get("local_snapshot", ""))
        if not local_snapshot:
            blockers.append(f"SOURCE_SNAPSHOT_REF_MISSING::{domain}::{source_id}")
            snapshot_exists = False
            snapshot_sha = ""
        else:
            path = root / local_snapshot
            path_in_root = True
            try:
                path.relative_to(root)
            except ValueError:
                blockers.append(f"SOURCE_SNAPSHOT_OUTSIDE_ROOT::{domain}::{source_id}::{local_snapshot}")
                path_in_root = False
            if not path_in_root or not path.exists():
                blockers.append(f"SOURCE_SNAPSHOT_MISSING::{domain}::{source_id}::{local_snapshot}")
                snapshot_exists = False
                snapshot_sha = ""
            else:
                snapshot_exists = True
                snapshot_sha = sha256_file(path)

        expected_sha = str(row.get("sha256", "") or row.get("source_sha256", ""))
        if expected_sha and snapshot_exists and expected_sha != snapshot_sha:
            blockers.append(f"SOURCE_SNAPSHOT_SHA_MISMATCH::{domain}::{source_id}")

        url = str(row.get("url", ""))
        if check_endpoints:
            ok, code = check_url(url, endpoint_timeout)
            if not ok:
                blockers.append(f"SOURCE_ENDPOINT_UNREACHABLE::{domain}::{source_id}::{code}")
            endpoint_ok = ok
            endpoint_code = code
        else:
            blockers.append(f"SOURCE_ENDPOINT_CHECK_SKIPPED::{domain}::{source_id}")
            endpoint_ok = None
            endpoint_code = None

        rows.append(
            {
                "domain": domain,
                "source_id": source_id,
                "url": url,
                "local_snapshot": local_snapshot,
                "status": row.get("status", ""),
                "bytes": int(row.get("bytes", 0)) if isinstance(row.get("bytes"), int) else 0,
                "sha256_expected": expected_sha,
                "sha256_actual": snapshot_sha,
                "sha256_match": bool(expected_sha and snapshot_sha and expected_sha == snapshot_sha),
                "exists": snapshot_exists,
                "endpoint_status": endpoint_ok,
                "endpoint_status_code": endpoint_code,
            }
        )

    for expected_id in sorted(expected_ids):
        if expected_id not in found_ids:
            blockers.append(f"SOURCE_ROW_MISSING_FROM_MANIFEST::{domain}::{expected_id}")
    if not expected_ids:
        blockers.append(f"NO_OFFICIAL_SOURCE_ROWS::{domain}")
    return rows, ordered_unique(blockers)


def validate_target_row(row: dict[str, Any], criteria: dict[str, Any]) -> tuple[bool, list[str], dict[str, Any]]:
    failures: list[str] = []
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
        "falsifier",
        "support_scope",
        "snapshot_sha256",
    )
    for field in required:
        if row.get(field) in (None, ""):
            failures.append(f"TARGET_BLIND_FIELD_MISSING::{field}")

    predicted = as_float(row.get("predicted_value"))
    observed = as_float(row.get("observed_value"))
    comparator_prediction = as_float(row.get("comparator_prediction"))
    residual = as_float(row.get("residual"))
    comparator_residual = as_float(row.get("comparator_residual"))
    uncertainty = as_float(row.get("uncertainty"))

    if predicted is None or observed is None or residual is None:
        failures.append("TARGET_BLIND_NUMERIC_FIELD_MISSING")
    elif abs(predicted - observed) != residual:
        failures.append("TARGET_BLIND_RESIDUAL_MISMATCH")

    if comparator_prediction is None or comparator_residual is None:
        failures.append("TARGET_BLIND_COMPARATOR_FIELD_MISSING")
    elif abs(comparator_prediction - observed) != comparator_residual:
        failures.append("TARGET_BLIND_COMPARATOR_RESIDUAL_MISMATCH")

    if uncertainty is None or uncertainty < 0:
        failures.append("TARGET_BLIND_UNCERTAINTY_INVALID")
    elif residual is not None and residual > uncertainty:
        failures.append("TARGET_BLIND_RESIDUAL_EXCEEDS_UNCERTAINTY")

    if residual is not None and comparator_residual is not None and comparator_residual <= residual:
        failures.append("TARGET_BLIND_COMPARATOR_NOT_WORSE")

    split = str(row.get("target_blind_split", "")).lower()
    if not split or ("withheld" not in split and "hidden" not in split):
        failures.append("TARGET_BLIND_TARGET_NOT_HIDDEN")

    if criteria.get("negative_control_rejection_required") and row.get("negative_control_rejected") is not True:
        failures.append("TARGET_BLIND_NEGATIVE_CONTROL_NOT_REJECTED")

    if criteria.get("pre_target_lock_required") and row.get("prediction_support_allowed") is not True:
        failures.append("TARGET_BLIND_PREDICTION_SUPPORT_NOT_TRUE")

    if criteria.get("target_hidden_until_scoring_required") and row.get("empirical_support_allowed") is not True:
        failures.append("TARGET_BLIND_EMPIRICAL_SUPPORT_NOT_TRUE")

    support_scope = str(row.get("support_scope", "")).lower()
    if criteria.get("current_target_blind_reconstructions_are_bounded_baseline_only", False):
        if "held-out" in support_scope or "baseline" in support_scope or "reconstruction" in support_scope:
            failures.append("TARGET_BLIND_CURRENT_BASELINE_BLOCKER")

    metrics = {
        "predicted_value": predicted,
        "observed_value": observed,
        "residual": residual,
        "comparator_residual": comparator_residual,
        "uncertainty": uncertainty,
        "snapshot_sha256": row.get("snapshot_sha256"),
    }
    return len(failures) == 0, failures, metrics


def validate_replay_row(row: dict[str, Any]) -> tuple[bool, list[str]]:
    failures: list[str] = []
    if row.get("numeric_replay") is not True:
        failures.append("REPLAY_ROW_NOT_FLAGGED")
    if row.get("prediction_support_allowed") is not False:
        failures.append("REPLAY_PREDICTION_SUPPORT_NOT_FALSE")
    if row.get("empirical_support_allowed") is not False:
        failures.append("REPLAY_EMPIRICAL_SUPPORT_NOT_FALSE")
    if not row.get("quarantine_reason"):
        failures.append("REPLAY_QUARANTINE_REASON_MISSING")
    return len(failures) == 0, failures


def build_domain_payload(
    root: Path,
    domain: str,
    requirements: dict[str, Any],
    manifest_rows: list[dict[str, Any]],
    target_rows: list[dict[str, Any]],
    replay_rows: list[dict[str, Any]],
    check_official_sources: bool,
    endpoint_timeout: float,
) -> tuple[dict[str, Any], list[str]]:
    minimum_n = int(requirements.get("minimum_per_domain_n", 20))
    criteria = requirements.get("criteria", {})
    source_rows, source_blockers = source_snapshot_rows(
        root,
        domain,
        manifest_rows,
        check_endpoints=check_official_sources,
        endpoint_timeout=endpoint_timeout,
    )
    blockers: list[str] = list(source_blockers)

    genuine_rows: list[dict[str, Any]] = []
    bounded_rows: list[dict[str, Any]] = []
    comparator_choices: list[str] = []
    negative_controls: list[str] = []
    falsifiers: list[str] = []
    residuals: list[float] = []
    comparator_residuals: list[float] = []
    uncertainties: list[float] = []

    for row in target_rows:
        usable, row_failures, metrics = validate_target_row(row, criteria)
        snapshot_ref = str(row.get("dataset_snapshot_ref", ""))
        if not snapshot_ref:
            row_failures.append("TARGET_BLIND_DATASET_SNAPSHOT_REF_MISSING")
        else:
            path = root / snapshot_ref
            path_in_root = True
            try:
                path.relative_to(root)
            except ValueError:
                row_failures.append(f"TARGET_BLIND_DATASET_SNAPSHOT_OUTSIDE_ROOT::{domain}::{snapshot_ref}")
                path_in_root = False
            if not path_in_root or not path.exists():
                row_failures.append(f"TARGET_BLIND_DATASET_SNAPSHOT_MISSING::{domain}::{snapshot_ref}")
            else:
                declared_snapshot_sha = str(row.get("snapshot_sha256") or "")
                if declared_snapshot_sha:
                    actual_snapshot_sha = sha256_file(path)
                    if declared_snapshot_sha != actual_snapshot_sha:
                        row_failures.append("TARGET_BLIND_DATASET_SNAPSHOT_SHA_MISMATCH")
                        metrics["snapshot_sha256"] = declared_snapshot_sha
        claim_id = str(row.get("claim_id", ""))
        tag = f"TARGET_BLIND::{domain}::{claim_id}"
        is_bounded_baseline = any("CURRENT_BASELINE_BLOCKER" in item for item in row_failures)
        if is_bounded_baseline:
            bounded_rows.append(
                {
                    "claim_id": claim_id,
                    "dataset_snapshot_ref": snapshot_ref,
                    "snapshot_sha256": metrics["snapshot_sha256"],
                    "blocking_reason": "current_target_blind_reconstruction",
                }
            )
            blockers.append(f"{tag}::CURRENT_TARGET_BLIND_RECONSTRUCTION_BOUNDARY")

        if usable and not is_bounded_baseline:
            comparator = str(row.get("comparator_baseline", "")).strip()
            if comparator:
                comparator_choices.append(f"TARGET_BLIND::{comparator}")
            negative = str(row.get("negative_control", "")).strip()
            if negative:
                negative_controls.append(negative)
            falsifier = str(row.get("falsifier", "")).strip()
            if falsifier:
                falsifiers.append(falsifier)

            if metrics["residual"] is not None:
                residuals.append(metrics["residual"])
            if metrics["comparator_residual"] is not None:
                comparator_residuals.append(metrics["comparator_residual"])
            if metrics["uncertainty"] is not None:
                uncertainties.append(metrics["uncertainty"])

            genuine_rows.append(
                {
                    "claim_id": claim_id,
                    "dataset_snapshot_ref": snapshot_ref,
                    "formula": row.get("formula"),
                    "model_residual": metrics["residual"],
                    "comparator_residual": metrics["comparator_residual"],
                    "uncertainty": metrics["uncertainty"],
                }
            )
            continue

        for item in row_failures:
            blockers.append(f"{tag}::{item}")

    for row in replay_rows:
        _, row_failures = validate_replay_row(row)
        for item in row_failures:
            blockers.append(f"NUMERIC_REPLAY::{domain}::{row.get('claim_id')}::{item}")

    if replay_rows:
        blockers.append(f"NUMERIC_REPLAY_QUARANTINED_NOT_DOMAIN_EVIDENCE::{domain}::{len(replay_rows)}")

    if minimum_n and len(genuine_rows) < minimum_n:
        blockers.append(f"N_BELOW_MINIMUM::{domain}::{len(genuine_rows)}/{minimum_n}")

    if criteria.get("negative_control_rejection_required") and not negative_controls:
        blockers.append(f"NO_NEGATIVE_CONTROLS::{domain}")

    if criteria.get("falsifier_required") and not falsifiers:
        blockers.append(f"NO_FALSIFIERS::{domain}")

    if not comparator_choices:
        comparators = [str(row.get("comparator_baseline", "")) for row in target_rows if str(row.get("comparator_baseline", ""))]
        comparator_choices.extend(f"TARGET_BLIND::{item}" for item in comparators)

    comparator_choices = ordered_unique(comparator_choices)
    negative_controls = ordered_unique(negative_controls)
    falsifiers = ordered_unique(falsifiers)
    blockers = ordered_unique(blockers)

    source_modes = list(requirements.get("required_source_separation_modes", ("prospective", "target_blind")))
    avg_model_residual = sum(residuals) / len(residuals) if residuals else 0.0
    avg_comparator_residual = sum(comparator_residuals) / len(comparator_residuals) if comparator_residuals else 0.0
    avg_uncertainty = sum(uncertainties) / len(uncertainties) if uncertainties else 0.0

    status = "BLOCKED_PENDING_GENUINE_ACQUISITION" if blockers else "READY_FOR_OFFICIAL_ACQUISITION_STEP"

    return (
        {
            "domain": domain,
            "status": status,
            "minimum_n": minimum_n,
            "required_n": minimum_n,
            "genuine_target_row_total": len(genuine_rows),
            "missing_n": max(0, minimum_n - len(genuine_rows)),
            "source_separation": {
                "mode_required": source_modes,
                "target_blind_allowed": "target_blind" in source_modes,
                "prospective_allowed": "prospective" in source_modes,
                "pre_target_lock_required": bool(criteria.get("pre_target_lock_required", True)),
                "target_hidden_until_scoring_required": bool(criteria.get("target_hidden_until_scoring_required", True)),
            },
            "official_sources": source_rows,
            "comparator_choices": comparator_choices,
            "residual_metric": {
                "metric_name": "mean_absolute_residual",
                "acceptance": "model residual <= declared uncertainty and comparator residual > model residual",
                "mean_model_residual": avg_model_residual,
                "mean_comparator_residual": avg_comparator_residual,
                "estimated_interval": [0.0, max(avg_uncertainty, avg_model_residual)],
            },
            "uncertainty_metric": {
                "metric_name": "declared_target_uncertainty",
                "required": bool(criteria.get("uncertainty_interval_required", True)),
                "mean_uncertainty": avg_uncertainty,
            },
            "genuine_rows": genuine_rows,
            "bounded_rows": bounded_rows,
            "negative_controls": negative_controls,
            "falsifiers": falsifiers,
            "required_protocol_steps": [
                "preregister comparator baseline, residual metric, uncertainty interval, negative controls, and falsifiers",
                "collect independent target-hidden or prospective rows from official snapshots with stable pre-target material locks",
                f"replay and collect at least {minimum_n} target rows per domain",
                "keep source separation disjoint and target fields hidden until scoring",
                "route candidate packs only after grand_factory and gate checks pass",
            ],
            "required_pack_fields": [
                "schema_id",
                "release_id",
                "capability_owner",
                "evidence_pack_id",
                "domain",
                "source_separation",
                "n",
                "model_under_test",
                "comparator_baseline",
                "uncertainty",
                "residuals",
                "negative_controls",
                "falsifiers",
                "grand_toe_support_allowed",
            ],
            "blockers": blockers,
            "check_official_sources": bool(check_official_sources),
            "source_endpoint_timeout_seconds": float(endpoint_timeout),
            "grand_toe_support_allowed": False,
            "protocol_row_hash": canonical_hash(blockers),
        },
        blockers,
    )


def build_protocol_payload(rows: list[dict[str, Any]], open_blockers: list[str], evidence_schema: dict[str, Any]) -> dict[str, Any]:
    protocol_rows: list[dict[str, Any]] = []
    for row in rows:
        protocol_rows.append(
            {
                "domain": row["domain"],
                "status": row["status"],
                "grand_toe_support_allowed": row["grand_toe_support_allowed"],
                "required_n": row["required_n"],
                "current_n": row["genuine_target_row_total"],
                "missing_n": row["missing_n"],
                "blockers": row["blockers"],
                "required_protocol_steps": row["required_protocol_steps"],
                "required_pack_fields": row["required_pack_fields"],
            }
        )
    return {
        "schema_id": PROTOCOL_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "blocker_id": BLOCKER_ID,
        "evidence_schema_ref": EVIDENCE_SCHEMA_REL,
        "protocol_schema_ref": PROTOCOL_SCHEMA_REL,
        "requirements_ref": REQUIREMENTS_REL,
        "plan_ref": PLAN_JSON_REL,
        "verdict": "BLOCKED" if open_blockers else "READY_FOR_CANDIDATE_BUILD",
        "blocked_domain_total": sum(1 for row in protocol_rows if row["status"] != "READY_FOR_OFFICIAL_ACQUISITION_STEP"),
        "queue_total": len(protocol_rows),
        "blocker_total": len(open_blockers),
        "open_blocker_total": len(open_blockers),
        "open_blocker_ids": open_blockers,
        "required_pack_fields": ordered_unique([str(field) for field in evidence_schema.get("required", [])]),
        "rows": protocol_rows,
        "no_fabricated_success_policy": NO_SEND_POLICY,
        "protocol_hash": canonical_hash(protocol_rows),
    }


def build_plan_payload(
    root: Path,
    *,
    check_official_sources: bool = False,
    source_timeout: float = 3.0,
) -> dict[str, Any]:
    requirements, req_blockers = requirements_from_root(root)
    manifest_rows, manifest_blockers = read_manifest(root)
    evidence_schema = read_json(root / EVIDENCE_SCHEMA_REL)
    schema_blockers: list[str] = []
    if not evidence_schema:
        schema_blockers.append(f"EVIDENCE_SCHEMA_MISSING::{EVIDENCE_SCHEMA_REL}")

    target_rows_by_domain = {domain: read_rows(root / TARGET_BLIND_REL, domain) for domain in DOMAINS}
    replay_rows_by_domain = {domain: read_rows(root / NUMERIC_REPLAY_REL, domain) for domain in DOMAINS}

    if not target_rows_by_domain.get("physics") and not target_rows_by_domain.get("chemistry"):
        req_blockers.append("TARGET_BLIND_ROWS_MISSING")

    domain_payloads: list[dict[str, Any]] = []
    blockers: list[str] = []
    blockers.extend(req_blockers)
    blockers.extend(manifest_blockers)
    blockers.extend(schema_blockers)

    for domain in DOMAINS:
        domain_payload, domain_blockers = build_domain_payload(
            root,
            domain=domain,
            requirements=requirements,
            manifest_rows=manifest_rows,
            target_rows=target_rows_by_domain.get(domain, []),
            replay_rows=replay_rows_by_domain.get(domain, []),
            check_official_sources=check_official_sources,
            endpoint_timeout=source_timeout,
        )
        domain_payloads.append(domain_payload)
        blockers.extend(domain_blockers)

    open_blockers = ordered_unique([item for item in blockers if item])
    blocked_domain_total = sum(1 for row in domain_payloads if row["status"] != "READY_FOR_OFFICIAL_ACQUISITION_STEP")
    required_pack_fields = [
        "schema_id",
        "release_id",
        "capability_owner",
        "evidence_pack_id",
        "domain",
        "source_separation",
        "n",
        "model_under_test",
        "comparator_baseline",
        "uncertainty",
        "residuals",
        "negative_controls",
        "falsifiers",
        "grand_toe_support_allowed",
    ]
    payload = {
        "schema_id": SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "blocker_id": BLOCKER_ID,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "requirements_ref": REQUIREMENTS_REL,
        "evidence_schema_ref": EVIDENCE_SCHEMA_REL,
        "protocol_schema_ref": PROTOCOL_SCHEMA_REL,
        "target_blind_ref": TARGET_BLIND_REL,
        "numeric_replay_ref": NUMERIC_REPLAY_REL,
        "manifest_ref": MANIFEST_REL,
        "minimum_per_domain_n": int(requirements.get("minimum_per_domain_n", 20)),
        "required_domains": list(DOMAINS),
        "source_timeout_seconds": float(source_timeout),
        "check_official_sources": bool(check_official_sources),
        "grand_toe_support_allowed": False,
        "blocker_total": len(open_blockers),
        "open_blocker_total": len(open_blockers),
        "open_blocker_ids": open_blockers,
        "blocked_domain_total": blocked_domain_total,
        "verdict": "BLOCKED_PENDING_GENUINE_ACQUISITION" if open_blockers else "READY",
        "domains": domain_payloads,
        "schema_fields_required_by_grand_schema": ordered_unique([field for field in evidence_schema.get("required", []) if str(field).strip()]),
        "required_pack_fields": required_pack_fields,
        "artifact_refs": {
            "plan": PLAN_JSON_REL,
            "protocol": PROTOCOL_JSON_REL,
            "readme": PLAN_MD_REL,
        },
        "no_fabricated_success_policy": NO_SEND_POLICY,
    }
    payload["protocol"] = build_protocol_payload(domain_payloads, open_blockers, evidence_schema)
    payload["plan_hash"] = canonical_hash(domain_payloads)
    return payload


def write_markdown(root: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# Physics + Chemistry Acquisition Plan",
        "",
        f"Verdict: `{payload['verdict']}`",
        f"Grand TOE support allowed: `{str(payload['grand_toe_support_allowed']).lower()}`",
        f"Open blocker total: `{payload['open_blocker_total']}`",
        f"Blocked domains: `{payload['blocked_domain_total']}/{len(payload['domains'])}`",
        "",
        "| Domain | Status | N | Missing | Blockers |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for row in payload["domains"]:
        lines.append(
            f"| `{row['domain']}` | `{row['status']}` | `{row['genuine_target_row_total']}` | "
            f"`{row['missing_n']}` | {len(row['blockers'])} |"
        )
    lines.extend(["", NO_SEND_POLICY, "", "Open blockers:"])
    for item in payload.get("open_blocker_ids", []):
        lines.append(f"- `{item}`")
    write_text(root / PLAN_MD_REL, "\n".join(lines) + "\n")


def _deterministic_plan_copy(payload: dict[str, Any]) -> dict[str, Any]:
    copy = dict(payload)
    copy.pop("generated_at", None)
    return copy


def write_outputs(
    root: Path,
    *,
    check_official_sources: bool = False,
    source_timeout: float = 3.0,
) -> dict[str, Any]:
    payload = build_plan_payload(
        root,
        check_official_sources=check_official_sources,
        source_timeout=source_timeout,
    )
    plan_payload = {k: v for k, v in payload.items() if k != "protocol"}
    protocol_payload = payload["protocol"]
    write_json(root / PLAN_JSON_REL, plan_payload)
    write_json(root / PROTOCOL_JSON_REL, protocol_payload)
    write_markdown(root, plan_payload)
    return payload


def check_stored(root: Path) -> list[str]:
    expected = build_plan_payload(root)
    expected_plan = _deterministic_plan_copy({k: v for k, v in expected.items() if k != "protocol"})
    expected_protocol = expected["protocol"]
    failures: list[str] = []
    if not (root / PLAN_JSON_REL).exists():
        failures.append(f"missing::{PLAN_JSON_REL}")
    elif _deterministic_plan_copy(read_json(root / PLAN_JSON_REL)) != expected_plan:
        failures.append(f"mismatch::{PLAN_JSON_REL}")
    if not (root / PROTOCOL_JSON_REL).exists():
        failures.append(f"missing::{PROTOCOL_JSON_REL}")
    elif read_json(root / PROTOCOL_JSON_REL) != expected_protocol:
        failures.append(f"mismatch::{PROTOCOL_JSON_REL}")
    if not (root / PLAN_MD_REL).exists():
        failures.append(f"missing::{PLAN_MD_REL}")
    return failures


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build physics and chemistry acquisition plan artifacts.")
    parser.add_argument("--write", action="store_true", help="write plan and protocol artifacts")
    parser.add_argument("--check", action="store_true", help="verify persisted plan artifacts are synchronized")
    parser.add_argument("--check-official-sources", action="store_true", help="perform read-only official endpoint checks")
    parser.add_argument("--source-timeout", type=float, default=3.0, help="endpoint check timeout in seconds")
    parser.add_argument("--allow-blocked-exit-zero", action="store_true", help="exit code 0 when blockers remain")
    parser.add_argument("--root", default=str(repo_root()), help="repository root")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    if args.check:
        failures = check_stored(root)
        if failures:
            for failure in failures:
                print(f"ERROR: {failure}")
            return 1
        print(json.dumps({"status": "ok", "checked": [PLAN_JSON_REL, PROTOCOL_JSON_REL]}, ensure_ascii=False, indent=2))
        return 0

    payload = write_outputs(
        root,
        check_official_sources=args.check_official_sources,
        source_timeout=args.source_timeout,
    ) if args.write else build_plan_payload(
        root,
        check_official_sources=args.check_official_sources,
        source_timeout=args.source_timeout,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if payload["open_blocker_total"] and not args.allow_blocked_exit_zero:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
