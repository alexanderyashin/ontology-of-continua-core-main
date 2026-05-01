from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
REQUIREMENTS_PATH = ROOT / "benchmarks" / "grand_science" / "domain_requirements.json"
REGISTRY_PATH = ROOT / "validation" / "heldout" / "grand_science_evidence_registry.json"
TARGET_BLIND_PATH = ROOT / "validation" / "target_blind" / "OC133_TARGET_BLIND_PREDICTION_TABLE.json"
REPORT_JSON_PATH = ROOT / "reports" / "OC_CORE_1_3_3_GRAND_EMPIRICAL_REPORT.json"
REPORT_MD_PATH = ROOT / "reports" / "OC_CORE_1_3_3_GRAND_EMPIRICAL_REPORT.md"


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


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def pack_failure_reasons(pack: dict[str, Any], requirements: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for field in REQUIRED_PACK_FIELDS:
        if field not in pack:
            failures.append(f"MISSING_FIELD::{field}")

    if pack.get("schema_id") != "OC133_GRAND_EMPIRICAL_EVIDENCE_v1":
        failures.append("SCHEMA_ID_MISMATCH")
    if pack.get("release_id") != "oc_core_1_3_3":
        failures.append("RELEASE_ID_MISMATCH")
    if pack.get("capability_owner") != "Research/EmpiricalScience":
        failures.append("CAPABILITY_OWNER_MISMATCH")
    if pack.get("domain") not in set(requirements["required_domains"]):
        failures.append("UNKNOWN_DOMAIN")

    source = pack.get("source_separation", {})
    if not isinstance(source, dict):
        failures.append("SOURCE_SEPARATION_NOT_OBJECT")
        source = {}
    if source.get("mode") not in set(requirements["required_source_separation_modes"]):
        failures.append("SOURCE_SEPARATION_MODE_NOT_ALLOWED")
    if source.get("pre_target_lock") is not True:
        failures.append("PRE_TARGET_LOCK_REQUIRED")
    if source.get("target_hidden_until_scoring") is not True:
        failures.append("TARGET_HIDDEN_UNTIL_SCORING_REQUIRED")
    if not source.get("training_sources") or not source.get("target_sources"):
        failures.append("TRAINING_AND_TARGET_SOURCES_REQUIRED")
    if set(source.get("training_sources", [])) & set(source.get("target_sources", [])):
        failures.append("TRAINING_TARGET_SOURCE_OVERLAP")

    minimum_n = int(requirements["minimum_per_domain_n"])
    if not isinstance(pack.get("n"), int) or int(pack.get("n", 0)) < minimum_n:
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
    if (
        not uncertainty.get("metric")
        or not uncertainty.get("method")
        or not isinstance(interval, list)
        or len(interval) != 2
        or not all(isinstance(value, (int, float)) for value in interval)
    ):
        failures.append("UNCERTAINTY_INTERVAL_INCOMPLETE")

    residuals = pack.get("residuals", {})
    if not isinstance(residuals, dict):
        failures.append("RESIDUALS_NOT_OBJECT")
        residuals = {}
    model_residual = as_float(residuals.get("model"))
    comparator_residual = as_float(residuals.get("comparator"))
    superiority_margin = as_float(residuals.get("superiority_margin"))
    if comparator_residual <= model_residual:
        failures.append("COMPARATOR_NOT_WORSE_THAN_MODEL")
    if superiority_margin <= 0:
        failures.append("SUPERIORITY_MARGIN_NOT_POSITIVE")

    negative_controls = pack.get("negative_controls", [])
    if not isinstance(negative_controls, list) or not negative_controls:
        failures.append("NEGATIVE_CONTROL_REQUIRED")
    elif not all(isinstance(row, dict) and row.get("rejected") is True for row in negative_controls):
        failures.append("NEGATIVE_CONTROL_NOT_REJECTED")

    falsifiers = pack.get("falsifiers", [])
    if not isinstance(falsifiers, list) or not falsifiers or not all(str(row).strip() for row in falsifiers):
        failures.append("FALSIFIER_REQUIRED")

    if "grand_toe_support_allowed" not in pack:
        failures.append("GRAND_TOE_SUPPORT_ALLOWED_NOT_EXPLICIT")
    elif not isinstance(pack.get("grand_toe_support_allowed"), bool):
        failures.append("GRAND_TOE_SUPPORT_ALLOWED_NOT_BOOLEAN")

    return failures


def load_registered_packs(registry: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    packs: list[dict[str, Any]] = []
    failures: list[str] = []
    for ref in registry.get("evidence_pack_refs", []):
        path = ROOT / str(ref)
        if not path.exists():
            failures.append(f"EVIDENCE_PACK_REF_MISSING::{ref}")
            continue
        payload = read_json(path)
        if not isinstance(payload, dict):
            failures.append(f"EVIDENCE_PACK_NOT_OBJECT::{ref}")
            continue
        payload["_source_ref"] = str(ref)
        packs.append(payload)
    return packs, failures


def bounded_baseline_rows() -> list[dict[str, Any]]:
    if not TARGET_BLIND_PATH.exists():
        return []
    payload = read_json(TARGET_BLIND_PATH)
    rows: list[dict[str, Any]] = []
    for row in payload.get("rows", []):
        residual = as_float(row.get("residual"))
        comparator_residual = as_float(row.get("comparator_residual"))
        rows.append(
            {
                "evidence_pack_id": row.get("claim_id"),
                "domain": row.get("lane"),
                "source_ref": "validation/target_blind/OC133_TARGET_BLIND_PREDICTION_TABLE.json",
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
    packs: list[dict[str, Any]],
    pack_failures: dict[str, list[str]],
    baseline_rows: list[dict[str, Any]],
    requirements: dict[str, Any],
) -> dict[str, Any]:
    domain_packs = [pack for pack in packs if pack.get("domain") == domain]
    valid_packs = [
        pack
        for pack in domain_packs
        if not pack_failures.get(str(pack.get("evidence_pack_id")))
    ]
    baseline = [row for row in baseline_rows if row.get("domain") == domain]
    valid_n = sum(int(pack.get("n", 0)) for pack in valid_packs)
    minimum_n = int(requirements["minimum_per_domain_n"])
    blockers: list[str] = []
    if valid_n < minimum_n:
        blockers.append(f"GENUINE_EVIDENCE_N_BELOW_MINIMUM::{valid_n}/{minimum_n}")
    if not valid_packs:
        blockers.append("NO_VALID_PROSPECTIVE_OR_TARGET_BLIND_EVIDENCE_PACK")
    if domain == "mathematics" and not valid_packs and baseline:
        blockers.append("CURRENT_FORMAL_CORPUS_BASELINE_IS_NOT_EMPIRICAL_GRAND_SCIENCE_EVIDENCE")
    support_allowed = (
        not blockers
        and bool(valid_packs)
        and all(pack.get("grand_toe_support_allowed") is True for pack in valid_packs)
    )

    return {
        "domain": domain,
        "registered_pack_total": len(domain_packs),
        "valid_pack_total": len(valid_packs),
        "valid_n": valid_n,
        "minimum_n": minimum_n,
        "bounded_baseline_row_total": len(baseline),
        "bounded_baseline_refs": [row["evidence_pack_id"] for row in baseline],
        "grand_toe_support_allowed": support_allowed,
        "status": "EVIDENCE_SUFFICIENT_PENDING_REVIEW" if support_allowed else "BLOCKED",
        "blockers": blockers,
    }


def build_payload() -> dict[str, Any]:
    requirements = read_json(REQUIREMENTS_PATH)
    registry = read_json(REGISTRY_PATH)
    packs, registry_failures = load_registered_packs(registry)
    pack_failures = {
        str(pack.get("evidence_pack_id", f"PACK_{idx}")): pack_failure_reasons(pack, requirements)
        for idx, pack in enumerate(packs)
    }
    baseline_rows = bounded_baseline_rows()
    domains = [
        summarize_domain(domain, packs, pack_failures, baseline_rows, requirements)
        for domain in requirements["required_domains"]
    ]
    blocked_total = sum(1 for row in domains if row["status"] == "BLOCKED")
    grand_toe_support_allowed = blocked_total == 0 and all(row["grand_toe_support_allowed"] is True for row in domains)
    payload = {
        "schema_id": "OC133_GRAND_EMPIRICAL_REPORT_v1",
        "release_id": "oc_core_1_3_3",
        "version": "1.3.3",
        "generated_by": "validation/grand_science/run_grand_empirical_gate.py",
        "capability_owner": "Research/EmpiricalScience",
        "requirements_ref": "benchmarks/grand_science/domain_requirements.json",
        "schema_ref": "validation/grand_science/grand_empirical_evidence.schema.json",
        "heldout_registry_ref": "validation/heldout/grand_science_evidence_registry.json",
        "bounded_baseline_ref": "validation/target_blind/OC133_TARGET_BLIND_PREDICTION_TABLE.json",
        "evidence_pack_total": len(packs),
        "bounded_baseline_row_total": len(baseline_rows),
        "registry_failure_total": len(registry_failures),
        "registry_failures": registry_failures,
        "evidence_pack_failure_total": sum(1 for failures in pack_failures.values() if failures),
        "evidence_pack_failures": pack_failures,
        "domain_total": len(domains),
        "blocked_domain_total": blocked_total,
        "domains": domains,
        "bounded_baseline_rows": baseline_rows,
        "grand_toe_support_allowed": grand_toe_support_allowed,
        "domain_predictive_superiority_supported": grand_toe_support_allowed,
        "verdict": "GRAND_EMPIRICAL_SUPPORT_ALLOWED" if grand_toe_support_allowed else "BLOCKED_PENDING_GENUINE_PER_DOMAIN_EVIDENCE",
        "support_policy": requirements["support_policy"],
        "no_fabricated_pass_policy": "This gate does not emit a grand empirical support allowance from bounded OC133 reconstructions. Unresolved domains remain BLOCKED until prospective or target-blind evidence packs clear the configured criteria.",
    }
    return payload


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# OC Core 1.3.3 Grand Empirical Report",
        "",
        f"Verdict: `{payload['verdict']}`",
        f"Grand TOE support allowed: `{str(payload['grand_toe_support_allowed']).lower()}`",
        f"Registered evidence packs: `{payload['evidence_pack_total']}`",
        f"Bounded baseline rows: `{payload['bounded_baseline_row_total']}`",
        f"Blocked domains: `{payload['blocked_domain_total']}/{payload['domain_total']}`",
        "",
        payload["no_fabricated_pass_policy"],
        "",
        "| Domain | Status | Valid N | Minimum N | Bounded baseline rows | Grand TOE support | Blockers |",
        "| --- | --- | ---: | ---: | ---: | --- | --- |",
    ]
    for row in payload["domains"]:
        blockers = "; ".join(row["blockers"])
        lines.append(
            f"| `{row['domain']}` | `{row['status']}` | `{row['valid_n']}` | `{row['minimum_n']}` | "
            f"`{row['bounded_baseline_row_total']}` | `{str(row['grand_toe_support_allowed']).lower()}` | {blockers} |"
        )
    lines.extend(
        [
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
    REPORT_MD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the strict grand empirical support gate.")
    parser.add_argument(
        "--allow-blocked-exit-zero",
        action="store_true",
        help="Return zero after writing the report even when domains remain blocked.",
    )
    args = parser.parse_args()
    payload = build_payload()
    REPORT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    write_markdown(payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if payload["blocked_domain_total"] == 0 and payload["grand_toe_support_allowed"] is True:
        return 0
    return 0 if args.allow_blocked_exit_zero else 2


if __name__ == "__main__":
    raise SystemExit(main())
