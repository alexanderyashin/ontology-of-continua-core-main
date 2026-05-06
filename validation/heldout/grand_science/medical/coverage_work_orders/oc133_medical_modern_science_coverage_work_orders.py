from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlencode


RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
SCHEMA_ID = "OC133_MEDICAL_MODERN_SCIENCE_COVERAGE_WORK_ORDERS_v1"
CAPABILITY_OWNER = "Logion Medical Evidence / Public Health Source Intake"

SCRIPT_REL = (
    "validation/heldout/grand_science/medical/coverage_work_orders/"
    "oc133_medical_modern_science_coverage_work_orders.py"
)
OUTPUT_REL = (
    "validation/heldout/grand_science/medical/coverage_work_orders/"
    "OC133_MEDICAL_MODERN_SCIENCE_COVERAGE_WORK_ORDERS.json"
)

NO_SEND_LOCKS = {
    "no_send": True,
    "public_release_action_allowed": False,
    "publish_allowed": False,
    "push_allowed": False,
    "registry_write_allowed": False,
    "journal_submission_allowed": False,
    "email_allowed": False,
    "doi_registration_allowed": False,
    "coverage_closure_allowed": False,
    "broad_modern_science_superiority_allowed": False,
}

REQUIRED_FIELDS = (
    "official_sources",
    "target_variable",
    "target_hidden_split",
    "formula_or_model",
    "incumbent_comparator",
    "uncertainty_and_residual",
    "negative_control",
    "falsifier",
    "N",
    "replay_command",
    "fail_closed_current_evidence",
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[5]


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def sha256_object(payload: Any) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8", newline="\n")


def no_send() -> dict[str, Any]:
    return dict(NO_SEND_LOCKS)


def with_hash(row: dict[str, Any]) -> dict[str, Any]:
    row = dict(row)
    row["row_sha256"] = sha256_object(row)
    return row


def clinicaltrials_url(params: dict[str, str]) -> str:
    return "https://clinicaltrials.gov/api/v2/studies?" + urlencode(params)


def openfda_url(endpoint: str, params: dict[str, str]) -> str:
    return f"https://api.fda.gov/{endpoint}?" + urlencode(params)


def cdc_url(path: str) -> str:
    return f"https://data.cdc.gov/resource/{path}"


def fail_closed_evidence(reason: str) -> dict[str, Any]:
    return {
        "current_status": "OPEN_FAIL_CLOSED_NO_EXECUTABLE_EVIDENCE",
        "executable_evidence_exists": False,
        "strict_evidence_pack_ref": None,
        "source_snapshot_hash_bound": False,
        "source_snapshot_ref": None,
        "source_snapshot_sha256": None,
        "reason": reason,
        "coverage_closure_allowed": False,
        "broad_modern_science_superiority_allowed": False,
        "scientific_pass": False,
    }


def common_acceptance_predicates() -> list[str]:
    return [
        "STRICT_PACK_SCHEMA_PASS",
        "OFFICIAL_SOURCE_SNAPSHOT_HASH_BOUND",
        "TARGET_VARIABLE_EXACTLY_DECLARED",
        "TARGET_HIDDEN_OR_PROSPECTIVE_LOCK_DECLARED",
        "FORMULA_OR_MODEL_PREREGISTERED",
        "COMPARATOR_PREREGISTERED_AND_TARGET_SEPARATED",
        "UNCERTAINTY_AND_RESIDUAL_DECLARED",
        "NEGATIVE_CONTROL_REJECTION_REQUIRED",
        "FALSIFIER_PREDICATES_EXECUTABLE",
        "INDEPENDENT_REPLAY_PASS",
        "COVERAGE_REGISTER_GAP_CLOSED_BY_REVIEW",
        "NO_BROAD_SUPERIORITY_CERTIFICATION",
    ]


def build_work_orders() -> list[dict[str, Any]]:
    rows = [
        {
            "work_order_id": "MS-COV-WO-MED-001",
            "domain_class_id": "medical_health_sciences",
            "phenomenon_class_id": "clinical_outcomes_and_biomarkers",
            "phenomenon_label": "clinical outcomes and biomarkers",
            "lane_status": "OPEN_FAIL_CLOSED_NO_EXECUTABLE_EVIDENCE",
            "coverage_closure_allowed": False,
            "support_allowed_for_broad_coverage": False,
            "official_sources": [
                {
                    "source_id": "CLINICALTRIALS_GOV_API_V2",
                    "source_name": "ClinicalTrials.gov API v2 study records",
                    "source_authority": "National Library of Medicine",
                    "official_documentation_url": "https://clinicaltrials.gov/data-api/about-api",
                    "official_endpoint_url": clinicaltrials_url({"query.cond": "hypertension", "pageSize": "100"}),
                    "access_mode": "read_only_https_get",
                    "runner_allowlist_status": "PENDING_GOVERNED_PACKET",
                }
            ],
            "target_variable": {
                "name": "heldout_trial_outcome_measure_direction_or_effect",
                "target_fields": ["protocolSection.identificationModule.nctId", "outcomesModule.outcomeMeasures"],
                "unit": "declared outcome direction/effect or missing-result class",
            },
            "target_hidden_split": {
                "target_hidden_until_scoring": True,
                "target_values_used_for_selection": False,
                "split_rule": "Lock study metadata and hide result/outcome fields until model and comparator outputs are materialized.",
            },
            "formula_or_model": {
                "model_id": "MED-TRIAL-DESIGN-RISK-OUTCOME-BOUNDED-SCORER",
                "rule": "Predict coarse outcome availability/direction from preregistered design metadata, enrollment, phase, intervention class, and condition tags.",
                "target_values_may_be_used_for_model_design": False,
            },
            "incumbent_comparator": {
                "baseline_name": "phase-condition majority baseline",
                "prediction_rule": "Use training-only outcome availability/direction majority by phase and condition stratum.",
                "pre_registered": True,
                "target_values_used_for_baseline_design": False,
            },
            "uncertainty_and_residual": {
                "metric": "macro classification error and calibration residual on hidden trial rows",
                "rule": "Wilson interval plus phase-stratified bootstrap declared before target unsealing.",
            },
            "negative_control": {
                "control_id": "MED-TRIAL-NCT-LABEL-PERMUTATION",
                "rule": "Permute NCT identifiers after source lock; replay must lose source/target consistency.",
            },
            "falsifier": {
                "falsifier_id": "MED-TRIAL-OUTCOME-FALSIFIER",
                "trigger": "target outcome text appears in visible features, N<20, source hash changes, or comparator ties/beats model within uncertainty.",
            },
            "N": {"minimum_n": 20, "unit": "trial outcome rows"},
            "replay_command": {
                "commands": [
                    "python validation/heldout/grand_science/medical/coverage_work_orders/oc133_medical_modern_science_coverage_work_orders.py --check",
                    "python tools/oc133_official_readonly_acquisition_runner.py --packet <generated_clinicaltrials_packet> --write-report --allow-blocked-exit-zero",
                ],
                "acceptance_predicates": common_acceptance_predicates(),
            },
            "fail_closed_current_evidence": fail_closed_evidence(
                "ClinicalTrials.gov source snapshot, target-hidden outcome scorer, comparator output, negative-control replay, and strict evidence pack are not yet bound."
            ),
            "no_send_locks": no_send(),
        },
        {
            "work_order_id": "MS-COV-WO-MED-002",
            "domain_class_id": "medical_health_sciences",
            "phenomenon_class_id": "epidemiological_transmission_and_risk",
            "phenomenon_label": "epidemiological transmission and risk",
            "lane_status": "OPEN_FAIL_CLOSED_NO_EXECUTABLE_EVIDENCE",
            "coverage_closure_allowed": False,
            "support_allowed_for_broad_coverage": False,
            "official_sources": [
                {
                    "source_id": "CDC_PUBLIC_HEALTH_TIME_SERIES",
                    "source_name": "CDC open public-health surveillance rows",
                    "source_authority": "Centers for Disease Control and Prevention",
                    "official_documentation_url": "https://dev.socrata.com/foundry/data.cdc.gov/",
                    "official_endpoint_url": cdc_url("9mfq-cb36.json?$limit=500"),
                    "access_mode": "read_only_https_get",
                    "runner_allowlist_status": "PENDING_GOVERNED_PACKET",
                }
            ],
            "target_variable": {
                "name": "heldout_incidence_or_risk_timeseries_value",
                "target_fields": ["date", "geography", "case_count_or_rate", "risk_stratum"],
                "unit": "count/rate by time and geography",
            },
            "target_hidden_split": {
                "target_hidden_until_scoring": True,
                "target_values_used_for_selection": False,
                "split_rule": "Lock source revision and hide later period incidence/risk values until prediction and comparator outputs are materialized.",
            },
            "formula_or_model": {
                "model_id": "MED-EPI-VISIBLE-LAG-STRATIFIED-SCORER",
                "rule": "Predict heldout incidence/risk from lagged visible time series and locked stratum metadata.",
                "target_values_may_be_used_for_model_design": False,
            },
            "incumbent_comparator": {
                "baseline_name": "seasonal naive lag baseline",
                "prediction_rule": "Use preregistered lagged value and geography/season stratum median on the same hidden target rows.",
                "pre_registered": True,
                "target_values_used_for_baseline_design": False,
            },
            "uncertainty_and_residual": {
                "metric": "absolute scaled error and calibration residual over hidden time rows",
                "rule": "Blocked time-series bootstrap declared before target opening.",
            },
            "negative_control": {
                "control_id": "MED-EPI-DATE-SHUFFLE",
                "rule": "Shuffle heldout dates after source lock; replay must reject temporal consistency.",
            },
            "falsifier": {
                "falsifier_id": "MED-EPI-RISK-FALSIFIER",
                "trigger": "source revision changes, target period is visible before scoring, N<20, or comparator ties/beats model within uncertainty.",
            },
            "N": {"minimum_n": 20, "unit": "time/geography rows"},
            "replay_command": {
                "commands": [
                    "python validation/heldout/grand_science/medical/coverage_work_orders/oc133_medical_modern_science_coverage_work_orders.py --check",
                    "python tools/oc133_official_readonly_acquisition_runner.py --packet <generated_cdc_packet> --write-report --allow-blocked-exit-zero",
                ],
                "acceptance_predicates": common_acceptance_predicates(),
            },
            "fail_closed_current_evidence": fail_closed_evidence(
                "CDC source snapshot, target-hidden risk scorer, comparator output, controls, and replay pack are not yet bound."
            ),
            "no_send_locks": no_send(),
        },
        {
            "work_order_id": "MS-COV-WO-MED-003",
            "domain_class_id": "medical_health_sciences",
            "phenomenon_class_id": "pharmacology_toxicology_and_dose_response",
            "phenomenon_label": "pharmacology, toxicology, and dose response",
            "lane_status": "OPEN_FAIL_CLOSED_NO_EXECUTABLE_EVIDENCE",
            "coverage_closure_allowed": False,
            "support_allowed_for_broad_coverage": False,
            "official_sources": [
                {
                    "source_id": "OPENFDA_DRUG_EVENT",
                    "source_name": "openFDA drug adverse event rows",
                    "source_authority": "US Food and Drug Administration",
                    "official_documentation_url": "https://open.fda.gov/apis/drug/event/",
                    "official_endpoint_url": openfda_url("drug/event.json", {"limit": "100"}),
                    "access_mode": "read_only_https_get",
                    "runner_allowlist_status": "PENDING_GOVERNED_PACKET",
                }
            ],
            "target_variable": {
                "name": "heldout_adverse_event_or_dose_response_count",
                "target_fields": ["patient.drug.medicinalproduct", "patient.reaction.reactionmeddrapt", "serious", "receivedate"],
                "unit": "event class/count or dose-response proxy",
            },
            "target_hidden_split": {
                "target_hidden_until_scoring": True,
                "target_values_used_for_selection": False,
                "split_rule": "Lock public event rows and hide target event-count/reaction summaries until preregistered scoring is materialized.",
            },
            "formula_or_model": {
                "model_id": "MED-DRUG-EVENT-VISIBLE-METADATA-SCORER",
                "rule": "Predict heldout event class/count from visible drug, date, demographic, and reporter metadata without target reaction fields.",
                "target_values_may_be_used_for_model_design": False,
            },
            "incumbent_comparator": {
                "baseline_name": "drug-class majority event baseline",
                "prediction_rule": "Use training-only event class/count medians by drug class and reporting stratum.",
                "pre_registered": True,
                "target_values_used_for_baseline_design": False,
            },
            "uncertainty_and_residual": {
                "metric": "count residual and macro classification error on hidden pharmacovigilance rows",
                "rule": "Poisson/binomial interval plus drug-class bootstrap declared before target opening.",
            },
            "negative_control": {
                "control_id": "MED-DRUG-REACTION-LABEL-PERMUTATION",
                "rule": "Permute reaction labels after lock; replay must reject target consistency.",
            },
            "falsifier": {
                "falsifier_id": "MED-DRUG-TOX-FALSIFIER",
                "trigger": "reaction target leaks into visible features, source hash changes, N<20, or comparator ties/beats model within uncertainty.",
            },
            "N": {"minimum_n": 20, "unit": "drug event rows"},
            "replay_command": {
                "commands": [
                    "python validation/heldout/grand_science/medical/coverage_work_orders/oc133_medical_modern_science_coverage_work_orders.py --check",
                    "python tools/oc133_official_readonly_acquisition_runner.py --packet <generated_openfda_packet> --write-report --allow-blocked-exit-zero",
                ],
                "acceptance_predicates": common_acceptance_predicates(),
            },
            "fail_closed_current_evidence": fail_closed_evidence(
                "openFDA source snapshot, target-hidden pharmacology scorer, comparator output, controls, and replay pack are not yet bound."
            ),
            "no_send_locks": no_send(),
        },
    ]
    return [with_hash(row) for row in rows]


def validate_payload(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    rows = payload.get("rows", [])
    if payload.get("schema_id") != SCHEMA_ID:
        failures.append("SCHEMA_ID_MISMATCH")
    if not isinstance(rows, list) or len(rows) != 3:
        failures.append("MEDICAL_WORK_ORDER_ROW_TOTAL_NOT_3")
        return failures
    for row in rows:
        missing = [field for field in REQUIRED_FIELDS if field not in row]
        if missing:
            failures.append(f"ROW_MISSING_FIELDS::{row.get('work_order_id')}::{','.join(missing)}")
        if row.get("coverage_closure_allowed") is not False:
            failures.append(f"COVERAGE_CLOSURE_ALLOWED::{row.get('work_order_id')}")
        if row.get("support_allowed_for_broad_coverage") is not False:
            failures.append(f"BROAD_SUPPORT_ALLOWED::{row.get('work_order_id')}")
        if row.get("fail_closed_current_evidence", {}).get("scientific_pass") is not False:
            failures.append(f"FAIL_CLOSED_EVIDENCE_NOT_FALSE::{row.get('work_order_id')}")
        if row.get("no_send_locks", {}).get("no_send") is not True:
            failures.append(f"NO_SEND_LOCK_MISSING::{row.get('work_order_id')}")
    return sorted(set(failures))


def build_payload() -> dict[str, Any]:
    rows = build_work_orders()
    payload = {
        "schema_id": SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "generated_by": SCRIPT_REL,
        "status": "OPEN_FAIL_CLOSED",
        "coverage_closure_allowed": False,
        "broad_modern_science_superiority_allowed": False,
        "row_total": len(rows),
        "rows": rows,
        "no_fake_closure_policy": (
            "These medical rows are executable source-intake/scorer obligations. "
            "They do not close broad modern-science superiority until governed acquisition, "
            "target-hidden scoring, comparator residuals, controls, and replay pass."
        ),
    }
    payload["artifact_hash"] = sha256_object({k: v for k, v in payload.items() if k != "artifact_hash"})
    return payload


def check_stored(root: Path | None = None) -> list[str]:
    root = root or repo_root()
    expected = build_payload()
    failures = validate_payload(expected)
    path = root / OUTPUT_REL
    if not path.exists():
        return [*failures, f"missing::{OUTPUT_REL}"]
    actual = read_json(path)
    if actual != expected:
        failures.append(f"mismatch::{OUTPUT_REL}")
    failures.extend(validate_payload(actual if isinstance(actual, dict) else {}))
    return sorted(set(failures))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build/check medical modern-science coverage work orders.")
    parser.add_argument("--root", default=str(repo_root()), help="repository root")
    parser.add_argument("--write", action="store_true", help="write deterministic fail-closed medical work orders")
    parser.add_argument("--check", action="store_true", help="check stored artifact synchronization")
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
        print(json.dumps({"status": "ok", "checked": OUTPUT_REL, "coverage_closure_allowed": False}, indent=2))
        return 0
    payload = build_payload()
    failures = validate_payload(payload)
    if args.write:
        write_json(root / OUTPUT_REL, payload)
    print(json.dumps({"status": "ok" if not failures else "failed", "output_ref": OUTPUT_REL, "failures": failures}, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
