from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlencode


RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
GENERATED_ON = "2026-05-01"
SCHEMA_ID = "OC133_OPERATIONS_MODERN_SCIENCE_COVERAGE_WORK_ORDERS_v1"
CAPABILITY_OWNER = "Logion Operations Evidence / Intervention and Queueing Sources"

SCRIPT_REL = (
    "validation/heldout/grand_science/operations/coverage_work_orders/"
    "oc133_operations_modern_science_coverage_work_orders.py"
)
OUTPUT_REL = (
    "validation/heldout/grand_science/operations/coverage_work_orders/"
    "OC133_OPERATIONS_MODERN_SCIENCE_COVERAGE_WORK_ORDERS.json"
)
COVERAGE_REGISTER_REL = "comparators/modern_science/OC133_MODERN_SCIENCE_COVERAGE_REGISTER.json"
COVERAGE_QUEUE_REF = "reports/OC_CORE_1_3_3_MODERN_SCIENCE_COVERAGE_LANE_QUEUE.json"

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
    "all_domain_scientific_closure_allowed": False,
}

REQUIRED_ROW_FIELDS = (
    "official_sources",
    "acquisition_protocol",
    "target_variable",
    "split",
    "formula_or_model",
    "incumbent_comparator",
    "uncertainty_and_residual",
    "negative_control",
    "falsifier",
    "minimum_n",
    "replay_command",
    "current_evidence_status",
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
    if "minimum_n" in row and "N" not in row:
        row["N"] = {
            "minimum_required": row["minimum_n"],
            "observed": None,
            "status": "NOT_ACQUIRED_PROTOCOL_ONLY",
        }
    row["row_sha256"] = sha256_object(row)
    return row


def common_acceptance(extra: list[str] | None = None) -> list[str]:
    return [
        "STRICT_PACK_SCHEMA_PASS",
        "MINIMUM_N_GE_20_OR_FORMAL_EQUIVALENT_JUSTIFIED",
        "OFFICIAL_SOURCE_SNAPSHOT_LOCKED",
        "SOURCE_SEPARATION_PASS",
        "TARGET_VARIABLE_EXACTLY_DECLARED",
        "FORMULA_OR_MODEL_PREREGISTERED",
        "COMPARATOR_PREREGISTERED_AND_TARGET_SEPARATED",
        "UNCERTAINTY_POLICY_DECLARED",
        "RESIDUAL_METRIC_EXECUTABLE",
        "NEGATIVE_CONTROLS_EXECUTABLE_AND_REJECTED",
        "FALSIFIERS_EXECUTABLE_AND_NOT_TRIGGERED",
        "INDEPENDENT_REPLAY_PASS",
        "COVERAGE_REVIEW_REQUIRED",
        "NO_BROAD_SUPERIORITY_CERTIFICATION",
        "FAIL_CLOSED_UNLESS_EXECUTABLE_EVIDENCE_BOUND",
        *(extra or []),
    ]


def common_current_status(reason: str) -> dict[str, Any]:
    return {
        "status": "OPEN_FAIL_CLOSED_SPEC_DECLARED_NO_SOURCE_LOCK_NO_STRICT_PACK",
        "executable_evidence_exists": False,
        "coverage_closure_allowed": False,
        "broad_support_allowed": False,
        "reason": reason,
    }


def build_work_orders() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = [
        {
            "work_order_id": "MS-COV-WO-033",
            "stable_id": "MS-COV-WO-033::complex_systems_operations_science::multi_agent_system_dynamics",
            "coverage_gap_id": "MS-COV-GAP-COMPLEX_SYSTEMS_OPERATIONS_SCIENCE-MULTI_AGENT_SYSTEM_DYNAMICS",
            "domain_class_id": "complex_systems_operations_science",
            "phenomenon_class_id": "multi_agent_system_dynamics",
            "phenomenon_label": "multi agent system dynamics",
            "priority": "P0",
            "lane_status": "OPEN_FAIL_CLOSED_EXECUTABLE_SPEC_ONLY",
            "coverage_closure_allowed": False,
            "support_allowed_for_broad_coverage": False,
            "official_sources": [
                {
                    "source_id": "NYC_TLC_TRIP_RECORD_DATA",
                    "title": "New York City Taxi and Limousine Commission Trip Record Data",
                    "source_authority": "New York City Taxi and Limousine Commission",
                    "official_url": "https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page",
                    "official_documentation_url": "https://www.nyc.gov/assets/tlc/downloads/pdf/trip_record_user_guide.pdf",
                    "access_mode": "read_only_https_parquet_or_open_data_export",
                    "runner_allowlist_status": "NOT_ALLOWLISTED_FOR_THIS_SPEC",
                }
            ],
            "acquisition_protocol": {
                "mode": "bounded_protocol_only_no_network_fetch_performed",
                "steps": [
                    "Download a pinned month of official TLC trip parquet files and the matching taxi-zone lookup.",
                    "Record source URLs, object sizes, parquet metadata, and SHA-256 before aggregation.",
                    "Aggregate only after source lock into pickup-zone/dropoff-zone/hour targets with target hours hidden until scoring.",
                ],
                "example_official_endpoint_url": "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet",
                "required_local_snapshots": [
                    "validation/heldout/grand_science/operations/coverage_work_orders/raw/multi_agent_tlc/tlc_yellow_2024_01.lock.json",
                    "validation/heldout/grand_science/operations/coverage_work_orders/raw/multi_agent_tlc/tlc_zone_lookup.lock.json",
                ],
            },
            "target_variable": {
                "name": "heldout_zone_hour_trip_flow_count",
                "unit": "trip records per pickup zone, dropoff zone, and hour",
                "target_fields": [
                    "PULocationID",
                    "DOLocationID",
                    "pickup_hour",
                    "trip_count",
                ],
                "target_field": "tlc_flow[pickup_zone, dropoff_zone, heldout_hour].trip_count",
                "extraction_rule": (
                    "Trip records are aggregated into a zone-hour flow panel; heldout hours and route counts remain "
                    "sealed until graph-temporal predictions are written."
                ),
                "target_hidden_until_scoring": True,
            },
            "split": {
                "source_separation_mode": "chronological_hour_split_with_route_hash_guard",
                "train": "first 60 percent of locked hours plus route_hash strata",
                "validation": "next 20 percent of locked hours",
                "holdout": "final 20 percent of locked hours, target counts sealed until scoring",
                "target_values_visible_during_split": False,
            },
            "formula_or_model": {
                "model_id": "OPS-TLC-GRAPH-TEMPORAL-FLOW-MODEL",
                "formula_or_model": (
                    "Fit a training-only graph-temporal autoregressive count model using prior route counts, hour/day effects, "
                    "pickup/dropoff zone adjacency, and weather/calendar flags if locked before scoring."
                ),
                "inputs_visible_before_target": [
                    "prior route-hour counts",
                    "hour of day",
                    "day of week",
                    "pickup/dropoff zone IDs",
                    "training-only route adjacency",
                ],
                "target_values_used_for_model_design": False,
                "target_values_used_for_selection": False,
            },
            "incumbent_comparator": {
                "name": "seasonal carry-forward and route-hour mean comparator",
                "prediction_rule": "predict each heldout route-hour count from last visible count and training-only route/hour mean",
                "pre_registered": True,
                "target_values_used_for_baseline_design": False,
            },
            "uncertainty_and_residual": {
                "residual_metric": "absolute count residual and Poisson deviance per route-hour",
                "uncertainty_method": "rolling training residual envelope with count-scale Poisson interval",
                "superiority_predicate": "model_MAE + uncertainty_upper < best_comparator_MAE",
            },
            "negative_control": {
                "control_id": "OPS-TLC-ZONE-LABEL-SHUFFLE",
                "description": "Shuffle pickup/dropoff zone labels after source lock.",
                "rejection_predicate": "shuffled-zone replay must change row hashes and remove residual advantage",
            },
            "falsifier": {
                "falsifier_id": "OPS-TLC-MULTI-AGENT-FLOW-FALSIFIER",
                "trigger": (
                    "Heldout trip counts leak into formula selection, fewer than 20 route-hour rows are scored, source hashes drift, "
                    "or the seasonal comparator ties or beats the model within uncertainty."
                ),
            },
            "falsifier_predicates": [
                "TLC parquet/object hash changes between acquisition and replay",
                "heldout route-hour trip counts are read before prediction materialization",
                "holdout row count is below minimum_n",
                "zone-label shuffle is not rejected",
            ],
            "minimum_n": 200,
            "replay_command": (
                "python validation/heldout/grand_science/operations/coverage_work_orders/"
                "oc133_operations_modern_science_coverage_work_orders.py --check"
            ),
            "replay_protocol": {
                "commands": [
                    "python validation/heldout/grand_science/operations/coverage_work_orders/oc133_operations_modern_science_coverage_work_orders.py --check",
                    "python <future_tlc_multi_agent_flow_scorer.py> --source-lock <tlc_lock> --write-pack --fail-closed",
                ],
                "required_artifacts": [
                    "TLC trip parquet source lock",
                    "taxi-zone lookup source lock",
                    "target-hidden zone-hour flow task table",
                    "strict multi-agent flow evidence pack",
                ],
                "acceptance_predicates": common_acceptance(["TLC_MULTI_AGENT_FLOW_SCOPE_REVIEWED"]),
            },
            "current_evidence_status": common_current_status(
                "NYC TLC is identified as an official public mobility source, but no source lock, aggregation manifest, scorer, comparator output, or strict pack is present."
            ),
            "remaining_blockers": [
                "TLC_SOURCE_LOCK_NOT_ACQUIRED",
                "TARGET_HIDDEN_FLOW_TABLE_NOT_BUILT",
                "STRICT_MULTI_AGENT_FLOW_EVIDENCE_PACK_NOT_BUILT",
                "COVERAGE_REVIEW_NOT_PERFORMED",
            ],
            "no_send_locks": no_send(),
        },
        {
            "work_order_id": "MS-COV-WO-034",
            "stable_id": "MS-COV-WO-034::complex_systems_operations_science::queue_supply_chain_and_operations_observables",
            "coverage_gap_id": "MS-COV-GAP-COMPLEX_SYSTEMS_OPERATIONS_SCIENCE-QUEUE_SUPPLY_CHAIN_AND_OPERATIONS_OBSERVABLES",
            "domain_class_id": "complex_systems_operations_science",
            "phenomenon_class_id": "queue_supply_chain_and_operations_observables",
            "phenomenon_label": "queue supply chain and operations observables",
            "priority": "P0",
            "lane_status": "OPEN_FAIL_CLOSED_EXECUTABLE_SPEC_ONLY",
            "coverage_closure_allowed": False,
            "support_allowed_for_broad_coverage": False,
            "official_sources": [
                {
                    "source_id": "USDOT_BTS_TRANSTATS_ON_TIME_PERFORMANCE",
                    "title": "BTS TranStats Reporting Carrier On-Time Performance",
                    "source_authority": "U.S. Department of Transportation Bureau of Transportation Statistics",
                    "official_url": "https://www.transtats.bts.gov/TableInfo.asp?QO_fu146_anzr=b0-gvzr&gnoyr_VQ=FGJ",
                    "official_documentation_url": "https://transtats.bts.gov/ONTIME/Index.aspx",
                    "access_mode": "read_only_https_download",
                    "runner_allowlist_status": "NOT_ALLOWLISTED_FOR_THIS_SPEC",
                }
            ],
            "acquisition_protocol": {
                "mode": "bounded_protocol_only_no_network_fetch_performed",
                "steps": [
                    "Download a pinned month from BTS TranStats Reporting Carrier On-Time Performance.",
                    "Record requested fields, row count, BTS release metadata, and SHA-256 before aggregation.",
                    "Score airport/carrier/day delay and taxi-out targets after source and split locks exist.",
                ],
                "example_official_endpoint_url": (
                    "https://www.transtats.bts.gov/DL_SelectFields.aspx?Table_id=236&db_short_name=On-Time"
                ),
                "required_local_snapshots": [
                    "validation/heldout/grand_science/operations/coverage_work_orders/raw/queue_bts/bts_ontime_2024_01.lock.json",
                ],
            },
            "target_variable": {
                "name": "heldout_airport_carrier_queue_delay",
                "unit": "minutes",
                "target_fields": [
                    "Origin",
                    "Dest",
                    "Reporting_Airline",
                    "FlightDate",
                    "ArrDelayMinutes",
                    "TaxiOut",
                ],
                "target_field": "bts_ontime[carrier, origin, dest, flight_date].ArrDelayMinutes",
                "extraction_rule": (
                    "Flight records are grouped into airport/carrier/day queue-delay panels; heldout delay values "
                    "remain sealed until predictions and baselines are materialized."
                ),
                "target_hidden_until_scoring": True,
            },
            "split": {
                "source_separation_mode": "chronological_flight_date_split",
                "train": "first 60 percent of locked flight dates within carrier/origin strata",
                "validation": "next 20 percent of locked flight dates",
                "holdout": "final 20 percent of locked flight dates, delay targets sealed until scoring",
                "target_values_visible_during_split": False,
            },
            "formula_or_model": {
                "model_id": "OPS-BTS-QUEUE-DELAY-PRIOR-STATE-MODEL",
                "formula_or_model": (
                    "Fit a training-only queue-delay model from prior airport/carrier delays, scheduled departure time, "
                    "distance, day-of-week, and route frequency; predict heldout delay minutes once."
                ),
                "inputs_visible_before_target": [
                    "prior delay and taxi-out aggregates",
                    "carrier",
                    "origin/destination airport",
                    "scheduled departure time",
                    "distance",
                    "day of week",
                ],
                "target_values_used_for_model_design": False,
                "target_values_used_for_selection": False,
            },
            "incumbent_comparator": {
                "name": "carrier-airport trailing mean and scheduled-block comparator",
                "prediction_rule": "predict heldout delay from training-only carrier/origin trailing mean and last visible delay",
                "pre_registered": True,
                "target_values_used_for_baseline_design": False,
            },
            "uncertainty_and_residual": {
                "residual_metric": "absolute delay-minute residual and pinball loss for high-delay quantiles",
                "uncertainty_method": "rolling pre-holdout residual envelope stratified by carrier and airport",
                "superiority_predicate": "model_MAE + uncertainty_upper < best_preregistered_comparator_MAE",
            },
            "negative_control": {
                "control_id": "OPS-BTS-ROUTE-DATE-SHUFFLE",
                "description": "Shuffle route/date pairings after source lock.",
                "rejection_predicate": "shuffled-route/date replay must change row hashes and remove residual advantage",
            },
            "falsifier": {
                "falsifier_id": "OPS-BTS-QUEUE-DELAY-FALSIFIER",
                "trigger": (
                    "Heldout delay values leak into model selection, fewer than 20 rows are scored, source hashes drift, "
                    "or trailing-mean comparator ties or beats the model within uncertainty."
                ),
            },
            "falsifier_predicates": [
                "BTS source file hash changes between acquisition and replay",
                "heldout delay values are read before prediction materialization",
                "holdout row count is below minimum_n",
                "route/date shuffle is not rejected",
            ],
            "minimum_n": 1000,
            "replay_command": (
                "python validation/heldout/grand_science/operations/coverage_work_orders/"
                "oc133_operations_modern_science_coverage_work_orders.py --check"
            ),
            "replay_protocol": {
                "commands": [
                    "python validation/heldout/grand_science/operations/coverage_work_orders/oc133_operations_modern_science_coverage_work_orders.py --check",
                    "python <future_bts_queue_delay_scorer.py> --source-lock <bts_lock> --write-pack --fail-closed",
                ],
                "required_artifacts": [
                    "BTS TranStats source lock",
                    "requested-field manifest",
                    "target-hidden queue-delay task table",
                    "strict queue/operations evidence pack",
                ],
                "acceptance_predicates": common_acceptance(["BTS_QUEUE_OPERATIONS_SCOPE_REVIEWED"]),
            },
            "current_evidence_status": common_current_status(
                "BTS TranStats is identified as an official operations source, but no source lock, delay scorer, comparator output, or strict pack is present."
            ),
            "remaining_blockers": [
                "BTS_TRANSTATS_SOURCE_LOCK_NOT_ACQUIRED",
                "TARGET_HIDDEN_QUEUE_DELAY_TABLE_NOT_BUILT",
                "STRICT_QUEUE_OPERATIONS_EVIDENCE_PACK_NOT_BUILT",
                "COVERAGE_REVIEW_NOT_PERFORMED",
            ],
            "no_send_locks": no_send(),
        },
        {
            "work_order_id": "MS-COV-WO-035",
            "stable_id": "MS-COV-WO-035::complex_systems_operations_science::resilience_risk_and_intervention_response",
            "coverage_gap_id": "MS-COV-GAP-COMPLEX_SYSTEMS_OPERATIONS_SCIENCE-RESILIENCE_RISK_AND_INTERVENTION_RESPONSE",
            "domain_class_id": "complex_systems_operations_science",
            "phenomenon_class_id": "resilience_risk_and_intervention_response",
            "phenomenon_label": "resilience risk and intervention response",
            "priority": "P0",
            "lane_status": "OPEN_FAIL_CLOSED_EXECUTABLE_SPEC_ONLY",
            "coverage_closure_allowed": False,
            "support_allowed_for_broad_coverage": False,
            "official_sources": [
                {
                    "source_id": "FEMA_OPENFEMA_DISASTER_DECLARATIONS_V2",
                    "title": "OpenFEMA Disaster Declarations Summaries v2",
                    "source_authority": "Federal Emergency Management Agency",
                    "official_url": "https://www.fema.gov/openfema-data-page/disaster-declarations-summaries-v2",
                    "official_documentation_url": "https://www.fema.gov/about/openfema/api",
                    "access_mode": "read_only_https_get",
                    "runner_allowlist_status": "NOT_ALLOWLISTED_FOR_THIS_SPEC",
                }
            ],
            "acquisition_protocol": {
                "mode": "bounded_protocol_only_no_network_fetch_performed",
                "steps": [
                    "Fetch DisasterDeclarationsSummaries v2 for a pinned historical interval and selected fields.",
                    "Record query URL, FEMA metadata, returned row count, and SHA-256 before aggregation.",
                    "Aggregate state/county/month declaration and incident-type targets only after source hashing.",
                ],
                "example_official_endpoint_url": "https://www.fema.gov/api/open/v2/DisasterDeclarationsSummaries?"
                + urlencode(
                    {
                        "$select": "disasterNumber,state,designatedArea,declarationDate,incidentType,declarationType",
                        "$filter": "declarationDate ge '2020-01-01T00:00:00.000z'",
                        "$top": "5000",
                    }
                ),
                "required_local_snapshots": [
                    "validation/heldout/grand_science/operations/coverage_work_orders/raw/resilience_fema/fema_disaster_declarations_v2.lock.json",
                ],
            },
            "target_variable": {
                "name": "heldout_state_month_disaster_declaration_count",
                "unit": "FEMA declaration records per state/month/incident type",
                "target_fields": [
                    "state",
                    "incidentType",
                    "declaration_month",
                    "declaration_count",
                ],
                "target_field": "fema_declarations[state, incidentType, heldout_month].declaration_count",
                "extraction_rule": (
                    "Declaration rows are aggregated into state/month/incident panels; heldout month counts remain "
                    "sealed until response-risk predictions are materialized."
                ),
                "target_hidden_until_scoring": True,
            },
            "split": {
                "source_separation_mode": "chronological_event_month_split",
                "train": "declaration months before validation window",
                "validation": "months immediately before the heldout period",
                "holdout": "pinned future historical months sealed until scoring",
                "target_values_visible_during_split": False,
            },
            "formula_or_model": {
                "model_id": "OPS-FEMA-SEASONAL-RESILIENCE-RISK-MODEL",
                "formula_or_model": (
                    "Fit a training-only seasonal state/incident risk model from prior declaration counts, incident type, "
                    "state, month-of-year, and rolling trend terms; predict heldout monthly counts once."
                ),
                "inputs_visible_before_target": [
                    "prior declaration counts",
                    "state",
                    "incident type",
                    "month of year",
                    "rolling trend terms",
                ],
                "target_values_used_for_model_design": False,
                "target_values_used_for_selection": False,
            },
            "incumbent_comparator": {
                "name": "seasonal same-month mean and last-observation comparator",
                "prediction_rule": "predict heldout declaration count from prior same-month mean and last visible monthly count",
                "pre_registered": True,
                "target_values_used_for_baseline_design": False,
            },
            "uncertainty_and_residual": {
                "residual_metric": "absolute count residual and Poisson deviance per state/month/incident type",
                "uncertainty_method": "pre-holdout rolling seasonal residual envelope",
                "superiority_predicate": "model_count_residual + uncertainty_upper < best_comparator_count_residual",
            },
            "negative_control": {
                "control_id": "OPS-FEMA-MONTH-LABEL-SHUFFLE",
                "description": "Shuffle heldout month labels after source lock.",
                "rejection_predicate": "shuffled-month replay must change row hashes and remove residual advantage",
            },
            "falsifier": {
                "falsifier_id": "OPS-FEMA-RESILIENCE-RESPONSE-FALSIFIER",
                "trigger": (
                    "Heldout declaration counts leak into formula selection, fewer than 20 rows are scored, source hashes drift, "
                    "or seasonal comparator ties or beats the model within uncertainty."
                ),
            },
            "falsifier_predicates": [
                "OpenFEMA response hash changes between acquisition and replay",
                "heldout declaration counts are read before prediction materialization",
                "holdout row count is below minimum_n",
                "month-label shuffle is not rejected",
            ],
            "minimum_n": 100,
            "replay_command": (
                "python validation/heldout/grand_science/operations/coverage_work_orders/"
                "oc133_operations_modern_science_coverage_work_orders.py --check"
            ),
            "replay_protocol": {
                "commands": [
                    "python validation/heldout/grand_science/operations/coverage_work_orders/oc133_operations_modern_science_coverage_work_orders.py --check",
                    "python <future_fema_resilience_response_scorer.py> --source-lock <fema_lock> --write-pack --fail-closed",
                ],
                "required_artifacts": [
                    "OpenFEMA source lock",
                    "state/month aggregation manifest",
                    "target-hidden resilience response task table",
                    "strict resilience/risk evidence pack",
                ],
                "acceptance_predicates": common_acceptance(["FEMA_RESILIENCE_RESPONSE_SCOPE_REVIEWED"]),
            },
            "current_evidence_status": common_current_status(
                "OpenFEMA is identified as an official resilience source, but no operations-local source lock, scorer, comparator output, or strict pack is present."
            ),
            "remaining_blockers": [
                "OPENFEMA_SOURCE_LOCK_NOT_ACQUIRED",
                "TARGET_HIDDEN_RESILIENCE_TABLE_NOT_BUILT",
                "STRICT_RESILIENCE_EVIDENCE_PACK_NOT_BUILT",
                "COVERAGE_REVIEW_NOT_PERFORMED",
            ],
            "no_send_locks": no_send(),
        },
    ]
    return [with_hash(row) for row in rows]


def build_payload() -> dict[str, Any]:
    rows = build_work_orders()
    return {
        "schema_id": SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_on": GENERATED_ON,
        "capability_owner": CAPABILITY_OWNER,
        "generated_by": SCRIPT_REL,
        "coverage_register_ref": COVERAGE_REGISTER_REL,
        "coverage_queue_ref": COVERAGE_QUEUE_REF,
        "domain_class_id": "complex_systems_operations_science",
        "target_work_order_ids": ["MS-COV-WO-033", "MS-COV-WO-034", "MS-COV-WO-035"],
        "work_order_total": len(rows),
        "fail_closed_spec_total": len(rows),
        "coverage_closure_allowed": False,
        "broad_modern_science_superiority_allowed": False,
        "small_deterministic_replay_implemented": "SPEC_GENERATION_AND_SYNC_CHECK_ONLY",
        "official_data_acquired": False,
        "no_fake_pass": True,
        "no_send_locks": no_send(),
        "work_orders": rows,
    }


def validate_payload(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    rows = payload.get("work_orders", [])
    if payload.get("coverage_closure_allowed") is not False:
        failures.append("PAYLOAD_COVERAGE_CLOSURE_ALLOWED")
    if payload.get("broad_modern_science_superiority_allowed") is not False:
        failures.append("PAYLOAD_BROAD_SUPERIORITY_ALLOWED")
    if payload.get("official_data_acquired") is not False:
        failures.append("PAYLOAD_FALSE_DATA_ACQUISITION_CLAIM")
    if payload.get("no_fake_pass") is not True:
        failures.append("NO_FAKE_PASS_FLAG_MISSING")
    if not isinstance(rows, list) or payload.get("work_order_total") != len(rows):
        failures.append("WORK_ORDER_TOTAL_MISMATCH")
        return failures
    expected_ids = {"MS-COV-WO-033", "MS-COV-WO-034", "MS-COV-WO-035"}
    actual_ids = {str(row.get("work_order_id")) for row in rows if isinstance(row, dict)}
    if actual_ids != expected_ids:
        failures.append("OPERATIONS_WORK_ORDER_SET_MISMATCH")
    for row in rows:
        if not isinstance(row, dict):
            failures.append("WORK_ORDER_NOT_OBJECT")
            continue
        row_id = str(row.get("work_order_id", "unknown"))
        if row.get("coverage_closure_allowed") is not False:
            failures.append(f"COVERAGE_CLOSURE_ALLOWED::{row_id}")
        if row.get("support_allowed_for_broad_coverage") is not False:
            failures.append(f"BROAD_SUPPORT_ALLOWED::{row_id}")
        if "PASS" in str(row.get("lane_status", "")).upper():
            failures.append(f"FAKE_PASS_STATUS::{row_id}")
        for field in REQUIRED_ROW_FIELDS:
            if not row.get(field):
                failures.append(f"REQUIRED_FIELD_MISSING::{row_id}::{field}")
        if row.get("minimum_n", 0) < 20:
            failures.append(f"MINIMUM_N_TOO_SMALL::{row_id}")
        if not row.get("target_variable", {}).get("target_hidden_until_scoring"):
            failures.append(f"TARGET_NOT_HIDDEN::{row_id}")
        if row.get("split", {}).get("target_values_visible_during_split") is not False:
            failures.append(f"SPLIT_LEAKS_TARGET::{row_id}")
        if row.get("formula_or_model", {}).get("target_values_used_for_selection") is not False:
            failures.append(f"MODEL_SELECTION_USES_TARGET::{row_id}")
        if row.get("incumbent_comparator", {}).get("pre_registered") is not True:
            failures.append(f"COMPARATOR_NOT_PREREGISTERED::{row_id}")
        if not row.get("uncertainty_and_residual", {}).get("residual_metric"):
            failures.append(f"RESIDUAL_METRIC_MISSING::{row_id}")
        if not row.get("negative_control", {}).get("rejection_predicate"):
            failures.append(f"NEGATIVE_CONTROL_PREDICATE_MISSING::{row_id}")
        if not row.get("falsifier", {}).get("trigger"):
            failures.append(f"FALSIFIER_TRIGGER_MISSING::{row_id}")
        if not row.get("replay_protocol", {}).get("commands"):
            failures.append(f"REPLAY_COMMANDS_MISSING::{row_id}")
        if "NO_BROAD_SUPERIORITY_CERTIFICATION" not in row.get("replay_protocol", {}).get("acceptance_predicates", []):
            failures.append(f"NO_BROAD_SUPERIORITY_PREDICATE_MISSING::{row_id}")
        status = row.get("current_evidence_status", {})
        if status.get("executable_evidence_exists") is not False or status.get("coverage_closure_allowed") is not False:
            failures.append(f"CURRENT_STATUS_NOT_FAIL_CLOSED::{row_id}")
        if not all(str(source.get("official_url", "")).startswith("https://") for source in row.get("official_sources", [])):
            failures.append(f"OFFICIAL_SOURCE_URL_NOT_HTTPS::{row_id}")
        expected_hash = sha256_object({key: value for key, value in row.items() if key != "row_sha256"})
        if row.get("row_sha256") != expected_hash:
            failures.append(f"ROW_HASH_MISMATCH::{row_id}")
    return failures


def check_stored(root: Path | None = None) -> list[str]:
    root = root or repo_root()
    path = root / OUTPUT_REL
    expected = build_payload()
    failures = validate_payload(expected)
    if not path.exists():
        return [*failures, f"missing::{OUTPUT_REL}"]
    actual = read_json(path)
    if actual != expected:
        failures.append(f"mismatch::{OUTPUT_REL}")
    failures.extend(validate_payload(actual if isinstance(actual, dict) else {}))
    return sorted(set(failures))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build/check operations modern-science coverage work orders.")
    parser.add_argument("--root", default=str(repo_root()), help="repository root")
    parser.add_argument("--write", action="store_true", help="write the deterministic work-order artifact")
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
        print(json.dumps({"status": "ok", "checked": OUTPUT_REL}, indent=2))
        return 0
    payload = build_payload()
    failures = validate_payload(payload)
    if args.write:
        write_json(root / OUTPUT_REL, payload)
    print(json.dumps({"status": "ok" if not failures else "failed", "output_ref": OUTPUT_REL, "failures": failures}, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
