from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


EVIDENCE_SCHEMA_ID = "OC133_GRAND_EMPIRICAL_EVIDENCE_v1"
REPORT_SCHEMA_ID = "OC133_GRAND_EMPIRICAL_REPORT_v1"
FACTORY_SCAN_SCHEMA_ID = "OC133_GRAND_EMPIRICAL_CANDIDATE_SCAN_v1"
DECOMPOSITION_QUEUE_SCHEMA_ID = "OC133_GRAND_EMPIRICAL_DECOMPOSITION_QUEUE_v1"
RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
CAPABILITY_OWNER = "Research/EmpiricalScience"

REQUIREMENTS_REL = "benchmarks/grand_science/domain_requirements.json"
REGISTRY_REL = "validation/heldout/grand_science_evidence_registry.json"
TARGET_BLIND_REL = "validation/target_blind/OC133_TARGET_BLIND_PREDICTION_TABLE.json"
REPORT_JSON_REL = "reports/OC_CORE_1_3_3_GRAND_EMPIRICAL_REPORT.json"
REPORT_MD_REL = "reports/OC_CORE_1_3_3_GRAND_EMPIRICAL_REPORT.md"
SCAN_REL = "validation/heldout/OC133_GRAND_EMPIRICAL_CANDIDATE_SCAN.json"
QUEUE_REL = "validation/heldout/OC133_GRAND_EMPIRICAL_DECOMPOSITION_QUEUE.json"
SAMPLE_PACK_REL = "validation/heldout/samples/grand_empirical_evidence_pack.sample.json"
EVIDENCE_SCHEMA_REL = "validation/grand_science/grand_empirical_evidence.schema.json"
PROTOCOL_SCHEMA_REL = "validation/grand_science/grand_empirical_protocol.schema.json"

DEFAULT_CANDIDATE_ROOTS = (
    "validation/heldout",
    "validation/grand_science",
)

DISCOVERY_EXCLUDED_NAMES = {
    "grand_science_evidence_registry.json",
    "OC133_GRAND_EMPIRICAL_CANDIDATE_SCAN.json",
    "OC133_GRAND_EMPIRICAL_DECOMPOSITION_QUEUE.json",
}

DISCOVERY_EXCLUDED_SUFFIXES = (
    ".schema.json",
    ".sample.json",
)

REQUIRED_PACK_FIELDS = (
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
)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def sha256_object(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def ordered_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def resolve_under_root(root: Path, ref: str) -> Path | None:
    try:
        path = (root / ref).resolve()
        path.relative_to(root.resolve())
    except (OSError, ValueError):
        return None
    return path


def candidate_roots(requirements: dict[str, Any]) -> list[str]:
    configured = requirements.get("candidate_evidence_pack_roots", DEFAULT_CANDIDATE_ROOTS)
    if not isinstance(configured, list):
        return list(DEFAULT_CANDIDATE_ROOTS)
    roots = [str(item) for item in configured if str(item).strip()]
    return roots or list(DEFAULT_CANDIDATE_ROOTS)


def should_skip_discovered_path(path: Path) -> bool:
    name = path.name
    if name in DISCOVERY_EXCLUDED_NAMES:
        return True
    if any(name.endswith(suffix) for suffix in DISCOVERY_EXCLUDED_SUFFIXES):
        return True
    if "samples" in {part.lower() for part in path.parts}:
        return True
    return False


def looks_like_evidence_pack(payload: Any) -> bool:
    if not isinstance(payload, dict):
        return False
    return (
        payload.get("schema_id") == EVIDENCE_SCHEMA_ID
        or "evidence_pack_id" in payload
        or "grand_toe_support_allowed" in payload
    )


def load_candidate_records(
    root: Path,
    registry: dict[str, Any],
    requirements: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    records_by_ref: dict[str, dict[str, Any]] = {}
    failures: list[str] = []

    def add_ref(ref: str, origin: str) -> None:
        path = resolve_under_root(root, ref)
        if path is None:
            failures.append(f"EVIDENCE_PACK_REF_OUTSIDE_REPO::{ref}")
            return
        if not path.exists():
            failures.append(f"EVIDENCE_PACK_REF_MISSING::{ref}")
            return
        if not path.is_file():
            failures.append(f"EVIDENCE_PACK_REF_NOT_FILE::{ref}")
            return
        try:
            payload = read_json(path)
        except Exception as exc:
            failures.append(f"EVIDENCE_PACK_JSON_PARSE_FAILED::{ref}::{exc.__class__.__name__}")
            return
        if not isinstance(payload, dict):
            failures.append(f"EVIDENCE_PACK_NOT_OBJECT::{ref}")
            return
        if not looks_like_evidence_pack(payload):
            failures.append(f"EVIDENCE_PACK_REF_NOT_EVIDENCE_PACK::{ref}")
            return
        existing = records_by_ref.setdefault(
            ref,
            {
                "source_ref": ref,
                "origins": [],
                "payload": payload,
            },
        )
        existing["origins"] = ordered_unique([*existing["origins"], origin])

    for ref in registry.get("evidence_pack_refs", []):
        if not isinstance(ref, str) or not ref.strip():
            failures.append(f"EVIDENCE_PACK_REF_INVALID::{ref!r}")
            continue
        add_ref(ref.strip(), "registry")

    for root_ref in candidate_roots(requirements):
        root_path = resolve_under_root(root, root_ref)
        if root_path is None or not root_path.exists():
            continue
        for path in sorted(root_path.rglob("*.json")):
            if should_skip_discovered_path(path):
                continue
            try:
                ref = rel(root, path)
            except ValueError:
                continue
            try:
                payload = read_json(path)
            except Exception:
                continue
            if looks_like_evidence_pack(payload):
                existing = records_by_ref.setdefault(
                    ref,
                    {
                        "source_ref": ref,
                        "origins": [],
                        "payload": payload,
                    },
                )
                existing["origins"] = ordered_unique([*existing["origins"], "discovered"])

    return list(records_by_ref.values()), failures


def pack_failure_reasons(pack: dict[str, Any], requirements: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for field in REQUIRED_PACK_FIELDS:
        if field not in pack:
            failures.append(f"MISSING_FIELD::{field}")

    if pack.get("schema_id") != EVIDENCE_SCHEMA_ID:
        failures.append("SCHEMA_ID_MISMATCH")
    if pack.get("release_id") != RELEASE_ID:
        failures.append("RELEASE_ID_MISMATCH")
    if pack.get("capability_owner") != CAPABILITY_OWNER:
        failures.append("CAPABILITY_OWNER_MISMATCH")

    required_domains = set(requirements.get("required_domains", []))
    if pack.get("domain") not in required_domains:
        failures.append("UNKNOWN_DOMAIN")

    evidence_pack_id = str(pack.get("evidence_pack_id", ""))
    if "SAMPLE" in evidence_pack_id.upper() or pack.get("sample_only") is True:
        failures.append("SAMPLE_PACK_NOT_EVIDENCE")

    source = pack.get("source_separation", {})
    if not isinstance(source, dict):
        failures.append("SOURCE_SEPARATION_NOT_OBJECT")
        source = {}
    allowed_modes = set(requirements.get("required_source_separation_modes", []))
    if source.get("mode") not in allowed_modes:
        failures.append("SOURCE_SEPARATION_MODE_NOT_ALLOWED")
    if source.get("pre_target_lock") is not True:
        failures.append("PRE_TARGET_LOCK_REQUIRED")
    if source.get("target_hidden_until_scoring") is not True:
        failures.append("TARGET_HIDDEN_UNTIL_SCORING_REQUIRED")
    training_sources = source.get("training_sources", [])
    target_sources = source.get("target_sources", [])
    if not isinstance(training_sources, list) or not isinstance(target_sources, list):
        failures.append("TRAINING_AND_TARGET_SOURCES_MUST_BE_LISTS")
        training_sources = []
        target_sources = []
    elif not training_sources or not target_sources:
        failures.append("TRAINING_AND_TARGET_SOURCES_REQUIRED")
    elif not all(isinstance(item, str) and item.strip() for item in [*training_sources, *target_sources]):
        failures.append("TRAINING_AND_TARGET_SOURCES_MUST_BE_NONEMPTY_STRINGS")
    if len(set(training_sources)) != len(training_sources) or len(set(target_sources)) != len(target_sources):
        failures.append("TRAINING_OR_TARGET_SOURCE_DUPLICATE")
    if set(training_sources) & set(target_sources):
        failures.append("TRAINING_TARGET_SOURCE_OVERLAP")

    minimum_n = int(requirements.get("minimum_per_domain_n", 20))
    n = pack.get("n")
    if not isinstance(n, int) or isinstance(n, bool):
        failures.append("N_NOT_INTEGER")
    elif n < minimum_n:
        failures.append(f"N_BELOW_MINIMUM::{minimum_n}")

    comparator = pack.get("comparator_baseline", {})
    if not isinstance(comparator, dict):
        failures.append("COMPARATOR_BASELINE_NOT_OBJECT")
        comparator = {}
    if not comparator.get("name") or not comparator.get("prediction_rule"):
        failures.append("COMPARATOR_BASELINE_INCOMPLETE")
    if comparator.get("pre_registered") is not True:
        failures.append("COMPARATOR_BASELINE_NOT_PREREGISTERED")

    uncertainty = pack.get("uncertainty", {})
    if not isinstance(uncertainty, dict):
        failures.append("UNCERTAINTY_NOT_OBJECT")
        uncertainty = {}
    interval = uncertainty.get("interval")
    interval_valid = (
        bool(uncertainty.get("metric"))
        and bool(uncertainty.get("method"))
        and isinstance(interval, list)
        and len(interval) == 2
        and all(is_number(value) for value in interval)
    )
    if not interval_valid:
        failures.append("UNCERTAINTY_INTERVAL_INCOMPLETE")
        interval = None
    elif float(interval[0]) > float(interval[1]):
        failures.append("UNCERTAINTY_INTERVAL_NOT_ORDERED")

    residuals = pack.get("residuals", {})
    if not isinstance(residuals, dict):
        failures.append("RESIDUALS_NOT_OBJECT")
        residuals = {}
    missing_residual_fields = [
        field
        for field in ("model", "comparator", "superiority_margin")
        if field not in residuals
    ]
    if missing_residual_fields:
        failures.append(f"RESIDUAL_FIELDS_MISSING::{','.join(missing_residual_fields)}")
    model_residual = residuals.get("model")
    comparator_residual = residuals.get("comparator")
    superiority_margin = residuals.get("superiority_margin")
    if not is_number(model_residual) or float(model_residual) < 0:
        failures.append("MODEL_RESIDUAL_INVALID")
    if not is_number(comparator_residual) or float(comparator_residual) < 0:
        failures.append("COMPARATOR_RESIDUAL_INVALID")
    if not is_number(superiority_margin):
        failures.append("SUPERIORITY_MARGIN_INVALID")
    if is_number(model_residual) and is_number(comparator_residual):
        if float(comparator_residual) <= float(model_residual):
            failures.append("COMPARATOR_NOT_WORSE_THAN_MODEL")
        if interval_valid and float(interval[0]) <= float(interval[1]):
            if not (float(interval[0]) <= float(model_residual) <= float(interval[1])):
                failures.append("MODEL_RESIDUAL_OUTSIDE_UNCERTAINTY_INTERVAL")
    if is_number(model_residual) and is_number(comparator_residual) and is_number(superiority_margin):
        expected_margin = float(comparator_residual) - float(model_residual)
        if float(superiority_margin) <= 0:
            failures.append("SUPERIORITY_MARGIN_NOT_POSITIVE")
        if abs(float(superiority_margin) - expected_margin) > 1e-9:
            failures.append("SUPERIORITY_MARGIN_MISMATCH")

    negative_controls = pack.get("negative_controls", [])
    if not isinstance(negative_controls, list) or not negative_controls:
        failures.append("NEGATIVE_CONTROL_REQUIRED")
    else:
        for idx, row in enumerate(negative_controls):
            if not isinstance(row, dict):
                failures.append(f"NEGATIVE_CONTROL_NOT_OBJECT::{idx}")
                continue
            if not row.get("control_id") or not row.get("description"):
                failures.append(f"NEGATIVE_CONTROL_INCOMPLETE::{idx}")
            if row.get("rejected") is not True:
                failures.append(f"NEGATIVE_CONTROL_NOT_REJECTED::{idx}")

    falsifiers = pack.get("falsifiers", [])
    if not isinstance(falsifiers, list) or not falsifiers:
        failures.append("FALSIFIER_REQUIRED")
    elif not all(isinstance(row, str) and row.strip() for row in falsifiers):
        failures.append("FALSIFIER_REQUIRED")

    if "grand_toe_support_allowed" not in pack:
        failures.append("GRAND_TOE_SUPPORT_ALLOWED_NOT_EXPLICIT")
    elif not isinstance(pack.get("grand_toe_support_allowed"), bool):
        failures.append("GRAND_TOE_SUPPORT_ALLOWED_NOT_BOOLEAN")
    elif pack.get("grand_toe_support_allowed") is not True:
        failures.append("GRAND_TOE_SUPPORT_NOT_ALLOWED")

    return ordered_unique(failures)


def candidate_rows(records: list[dict[str, Any]], requirements: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen_ids: dict[str, int] = {}
    for record in records:
        pack = record["payload"]
        pack_id = str(pack.get("evidence_pack_id") or record["source_ref"])
        seen_ids[pack_id] = seen_ids.get(pack_id, 0) + 1

    for record in records:
        pack = record["payload"]
        pack_id = str(pack.get("evidence_pack_id") or record["source_ref"])
        failures = pack_failure_reasons(pack, requirements)
        if seen_ids.get(pack_id, 0) > 1:
            failures.append("DUPLICATE_EVIDENCE_PACK_ID")
        failures = ordered_unique(failures)
        residuals = pack.get("residuals", {}) if isinstance(pack.get("residuals"), dict) else {}
        row = {
            "source_ref": record["source_ref"],
            "origins": record["origins"],
            "evidence_pack_id": pack_id,
            "domain": pack.get("domain"),
            "n": pack.get("n"),
            "source_separation_mode": (pack.get("source_separation") or {}).get("mode") if isinstance(pack.get("source_separation"), dict) else None,
            "model_residual": residuals.get("model"),
            "comparator_residual": residuals.get("comparator"),
            "superiority_margin": residuals.get("superiority_margin"),
            "grand_toe_support_allowed": pack.get("grand_toe_support_allowed"),
            "candidate_sha256": sha256_object(pack),
            "valid_for_grand_support": not failures,
            "failure_total": len(failures),
            "failures": failures,
        }
        rows.append(row)
    return rows


def valid_packs_for_domain(
    domain: str,
    records: list[dict[str, Any]],
    candidate_report_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    valid_refs = {
        row["source_ref"]
        for row in candidate_report_rows
        if row.get("domain") == domain and row.get("valid_for_grand_support") is True
    }
    return [record["payload"] for record in records if record["source_ref"] in valid_refs]


def bounded_baseline_rows(root: Path) -> list[dict[str, Any]]:
    target_blind_path = root / TARGET_BLIND_REL
    if not target_blind_path.exists():
        return []
    payload = read_json(target_blind_path)
    rows: list[dict[str, Any]] = []
    for row in payload.get("rows", []):
        residual = as_float(row.get("residual"))
        comparator_residual = as_float(row.get("comparator_residual"))
        rows.append(
            {
                "evidence_pack_id": row.get("claim_id"),
                "domain": row.get("lane"),
                "source_ref": TARGET_BLIND_REL,
                "source_separation_mode": "target_blind",
                "n": 1,
                "model_under_test": row.get("formula"),
                "comparator_baseline": row.get("comparator_baseline"),
                "uncertainty": row.get("uncertainty"),
                "model_residual": residual,
                "comparator_residual": comparator_residual,
                "superiority_margin": comparator_residual - residual,
                "negative_control_rejected": row.get("negative_control_rejected") is True,
                "falsifier": row.get("falsifier"),
                "grand_toe_support_allowed": False,
                "support_scope": row.get("support_scope"),
                "classification": "BOUNDED_BASELINE_NOT_GRAND_SUPPORT",
            }
        )
    return rows


def summarize_domain(
    domain: str,
    records: list[dict[str, Any]],
    candidate_report_rows: list[dict[str, Any]],
    baseline_rows: list[dict[str, Any]],
    requirements: dict[str, Any],
) -> dict[str, Any]:
    domain_candidates = [row for row in candidate_report_rows if row.get("domain") == domain]
    valid_packs = valid_packs_for_domain(domain, records, candidate_report_rows)
    baseline = [row for row in baseline_rows if row.get("domain") == domain]
    valid_n = sum(int(pack.get("n", 0)) for pack in valid_packs)
    minimum_n = int(requirements.get("minimum_per_domain_n", 20))
    blockers: list[str] = []
    if valid_n < minimum_n:
        blockers.append(f"GENUINE_EVIDENCE_N_BELOW_MINIMUM::{valid_n}/{minimum_n}")
    if not valid_packs:
        blockers.append("NO_VALID_PROSPECTIVE_OR_TARGET_BLIND_EVIDENCE_PACK")
    if not domain_candidates:
        blockers.append("NO_CANDIDATE_EVIDENCE_PACK_DISCOVERED")
    else:
        invalid_total = sum(1 for row in domain_candidates if row.get("valid_for_grand_support") is not True)
        if invalid_total:
            blockers.append(f"CANDIDATE_EVIDENCE_PACKS_INVALID::{invalid_total}")
    if domain == "mathematics" and not valid_packs and baseline:
        blockers.append("CURRENT_FORMAL_CORPUS_BASELINE_IS_NOT_EMPIRICAL_GRAND_SCIENCE_EVIDENCE")

    support_allowed = not blockers and bool(valid_packs)
    return {
        "domain": domain,
        "candidate_pack_total": len(domain_candidates),
        "registered_pack_total": sum(1 for row in domain_candidates if "registry" in row.get("origins", [])),
        "discovered_pack_total": sum(1 for row in domain_candidates if "discovered" in row.get("origins", [])),
        "valid_pack_total": len(valid_packs),
        "valid_pack_refs": [
            row["source_ref"]
            for row in domain_candidates
            if row.get("valid_for_grand_support") is True
        ],
        "valid_n": valid_n,
        "minimum_n": minimum_n,
        "missing_n": max(0, minimum_n - valid_n),
        "bounded_baseline_row_total": len(baseline),
        "bounded_baseline_refs": [row["evidence_pack_id"] for row in baseline],
        "grand_toe_support_allowed": support_allowed,
        "status": "EVIDENCE_SUFFICIENT_PENDING_REVIEW" if support_allowed else "BLOCKED",
        "blockers": blockers,
    }


def decomposition_queue_rows(domains: list[dict[str, Any]], requirements: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for domain_row in domains:
        if domain_row.get("status") != "BLOCKED":
            continue
        domain = str(domain_row["domain"])
        rows.append(
            {
                "queue_id": f"OC133-GRAND-EMPIRICAL-DECOMP-{domain.upper()}",
                "blocker_id": "grand_toe_empirical_superiority",
                "domain": domain,
                "owner_capability": CAPABILITY_OWNER,
                "status": "BLOCKED_PENDING_GENUINE_EVIDENCE_PACK",
                "current_valid_n": domain_row.get("valid_n"),
                "minimum_n": domain_row.get("minimum_n"),
                "missing_n": domain_row.get("missing_n"),
                "domain_blockers": domain_row.get("blockers", []),
                "required_protocol_steps": [
                    "pre-register the OC model, comparator baseline, residual metric, uncertainty method, negative controls, and falsifiers before target scoring",
                    "freeze training/source-development material separately from target/held-out sources and record stable hashes",
                    "keep target values hidden until scoring is complete, or use a genuinely prospective target source",
                    "collect at least the configured per-domain N with no training/target source overlap",
                    "score OC residuals and comparator residuals under the same metric and uncertainty protocol",
                    "reject every declared negative control and retain falsifier conditions even when the candidate fails",
                    "register the final evidence pack in validation/heldout/grand_science_evidence_registry.json only after the pack is complete",
                ],
                "required_pack_fields": list(REQUIRED_PACK_FIELDS),
                "sample_pack_ref": SAMPLE_PACK_REL,
                "evidence_schema_ref": EVIDENCE_SCHEMA_REL,
                "protocol_schema_ref": PROTOCOL_SCHEMA_REL,
                "registry_ref": REGISTRY_REL,
            }
        )
    return rows


def build_grand_empirical_payload(root: Path) -> dict[str, Any]:
    requirements = read_json(root / REQUIREMENTS_REL)
    registry = read_json(root / REGISTRY_REL)
    records, registry_failures = load_candidate_records(root, registry, requirements)
    candidates = candidate_rows(records, requirements)
    baseline_rows = bounded_baseline_rows(root)
    domains = [
        summarize_domain(domain, records, candidates, baseline_rows, requirements)
        for domain in requirements.get("required_domains", [])
    ]
    queue_rows = decomposition_queue_rows(domains, requirements)
    blocked_total = sum(1 for row in domains if row["status"] == "BLOCKED")
    grand_toe_support_allowed = blocked_total == 0 and all(row["grand_toe_support_allowed"] is True for row in domains)
    pack_failures = {
        str(row["evidence_pack_id"]): row["failures"]
        for row in candidates
        if row.get("failures")
    }
    registered_refs = {
        str(ref)
        for ref in registry.get("evidence_pack_refs", [])
        if isinstance(ref, str)
    }
    payload = {
        "schema_id": REPORT_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_by": "validation/grand_science/run_grand_empirical_gate.py",
        "factory_module": "validation/grand_science/evidence_pack_factory.py",
        "capability_owner": CAPABILITY_OWNER,
        "requirements_ref": REQUIREMENTS_REL,
        "schema_ref": EVIDENCE_SCHEMA_REL,
        "protocol_schema_ref": PROTOCOL_SCHEMA_REL,
        "heldout_registry_ref": REGISTRY_REL,
        "candidate_scan_ref": SCAN_REL,
        "decomposition_queue_ref": QUEUE_REL,
        "sample_pack_ref": SAMPLE_PACK_REL,
        "bounded_baseline_ref": TARGET_BLIND_REL,
        "candidate_evidence_pack_roots": candidate_roots(requirements),
        "evidence_pack_total": len(candidates),
        "registered_evidence_pack_total": sum(1 for row in candidates if row["source_ref"] in registered_refs),
        "discovered_evidence_pack_total": sum(1 for row in candidates if "discovered" in row.get("origins", [])),
        "valid_evidence_pack_total": sum(1 for row in candidates if row.get("valid_for_grand_support") is True),
        "bounded_baseline_row_total": len(baseline_rows),
        "registry_failure_total": len(registry_failures),
        "registry_failures": registry_failures,
        "evidence_pack_failure_total": sum(1 for row in candidates if row.get("failure_total", 0)),
        "evidence_pack_failures": pack_failures,
        "candidate_rows": candidates,
        "domain_total": len(domains),
        "blocked_domain_total": blocked_total,
        "domains": domains,
        "bounded_baseline_rows": baseline_rows,
        "decomposition_queue_total": len(queue_rows),
        "decomposition_queue": queue_rows,
        "grand_toe_support_allowed": grand_toe_support_allowed,
        "domain_predictive_superiority_supported": grand_toe_support_allowed,
        "verdict": "GRAND_EMPIRICAL_SUPPORT_ALLOWED" if grand_toe_support_allowed else "BLOCKED_PENDING_GENUINE_PER_DOMAIN_EVIDENCE",
        "support_policy": requirements["support_policy"],
        "no_fabricated_pass_policy": "This factory/gate does not emit a grand empirical support allowance from bounded OC133 reconstructions, sample packs, or artifact existence. Unresolved domains remain BLOCKED until prospective or target-blind evidence packs clear the configured criteria.",
    }
    return payload


def candidate_scan_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_id": FACTORY_SCAN_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "requirements_ref": payload["requirements_ref"],
        "registry_ref": payload["heldout_registry_ref"],
        "candidate_evidence_pack_roots": payload["candidate_evidence_pack_roots"],
        "candidate_total": payload["evidence_pack_total"],
        "valid_candidate_total": payload["valid_evidence_pack_total"],
        "failure_total": payload["evidence_pack_failure_total"],
        "registry_failure_total": payload["registry_failure_total"],
        "registry_failures": payload["registry_failures"],
        "sample_pack_excluded_from_discovery": True,
        "sample_pack_ref": payload["sample_pack_ref"],
        "rows": payload["candidate_rows"],
    }


def decomposition_queue_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_id": DECOMPOSITION_QUEUE_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "blocker_id": "grand_toe_empirical_superiority",
        "verdict": payload["verdict"],
        "blocked_domain_total": payload["blocked_domain_total"],
        "queue_total": payload["decomposition_queue_total"],
        "requirements_ref": payload["requirements_ref"],
        "evidence_schema_ref": payload["schema_ref"],
        "protocol_schema_ref": payload["protocol_schema_ref"],
        "sample_pack_ref": payload["sample_pack_ref"],
        "rows": payload["decomposition_queue"],
    }


def write_markdown(root: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# OC Core 1.3.3 Grand Empirical Report",
        "",
        f"Verdict: `{payload['verdict']}`",
        f"Grand TOE support allowed: `{str(payload['grand_toe_support_allowed']).lower()}`",
        f"Candidate evidence packs: `{payload['evidence_pack_total']}`",
        f"Valid evidence packs: `{payload['valid_evidence_pack_total']}`",
        f"Bounded baseline rows: `{payload['bounded_baseline_row_total']}`",
        f"Blocked domains: `{payload['blocked_domain_total']}/{payload['domain_total']}`",
        f"Decomposition queue rows: `{payload['decomposition_queue_total']}`",
        "",
        payload["no_fabricated_pass_policy"],
        "",
        "| Domain | Status | Candidate packs | Valid packs | Valid N | Minimum N | Bounded baseline rows | Grand TOE support | Blockers |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for row in payload["domains"]:
        blockers = "; ".join(row["blockers"])
        lines.append(
            f"| `{row['domain']}` | `{row['status']}` | `{row['candidate_pack_total']}` | `{row['valid_pack_total']}` | "
            f"`{row['valid_n']}` | `{row['minimum_n']}` | `{row['bounded_baseline_row_total']}` | "
            f"`{str(row['grand_toe_support_allowed']).lower()}` | {blockers} |"
        )
    lines.extend(
        [
            "",
            "## Candidate Factory",
            "",
            f"Candidate scan: `{payload['candidate_scan_ref']}`",
            f"Decomposition queue: `{payload['decomposition_queue_ref']}`",
            f"Sample-only pack: `{payload['sample_pack_ref']}`",
            "",
            "## Bounded Baseline",
            "",
            "Current target-blind rows are retained as bounded reconstruction evidence only. They are not promoted to broad domain validation or grand TOE support.",
            "",
            "| Domain | Baseline ID | N | Model residual | Comparator residual | Support scope |",
            "| --- | --- | ---: | ---: | ---: | --- |",
        ]
    )
    for row in payload["bounded_baseline_rows"]:
        lines.append(
            f"| `{row['domain']}` | `{row['evidence_pack_id']}` | `{row['n']}` | "
            f"`{row['model_residual']}` | `{row['comparator_residual']}` | {row.get('support_scope') or ''} |"
        )
    (root / REPORT_MD_REL).write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def write_grand_empirical_outputs(root: Path, payload: dict[str, Any]) -> None:
    write_json(root / REPORT_JSON_REL, payload)
    write_json(root / SCAN_REL, candidate_scan_payload(payload))
    write_json(root / QUEUE_REL, decomposition_queue_payload(payload))
    write_markdown(root, payload)
