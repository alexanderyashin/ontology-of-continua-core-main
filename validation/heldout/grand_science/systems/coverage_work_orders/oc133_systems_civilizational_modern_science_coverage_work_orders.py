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
SCHEMA_ID = "OC133_SYSTEMS_CIVILIZATIONAL_MODERN_SCIENCE_COVERAGE_WORK_ORDERS_v1"
CAPABILITY_OWNER = "Logion Research/Systems Civilizational Coverage"

SCRIPT_REL = (
    "validation/heldout/grand_science/systems/coverage_work_orders/"
    "oc133_systems_civilizational_modern_science_coverage_work_orders.py"
)
OUTPUT_REL = (
    "validation/heldout/grand_science/systems/coverage_work_orders/"
    "OC133_SYSTEMS_CIVILIZATIONAL_MODERN_SCIENCE_COVERAGE_WORK_ORDERS.json"
)
COVERAGE_REGISTER_REL = "comparators/modern_science/OC133_MODERN_SCIENCE_COVERAGE_REGISTER.json"
MODERN_PROTOCOL_REL = "benchmarks/modern_science/protocols/OC133_MODERN_SCIENCE_BENCHMARK_PROTOCOL_SYSTEMS.json"
WDI_POPULATION_PACK_REL = (
    "validation/heldout/grand_science/systems/wdi_population_materiality/"
    "OC133_SYSTEMS_WDI_POPULATION_MATERIALITY_CANDIDATE_PACK.json"
)
WDI_POPULATION_PROTOCOL_REL = (
    "validation/heldout/grand_science/systems/wdi_population_materiality/"
    "OC133_SYSTEMS_WDI_POPULATION_MATERIALITY_PROTOCOL.json"
)
WDI_MODEL_SEARCH_REPORT_REL = (
    "validation/heldout/grand_science/systems/wdi_model_search/"
    "OC133_SYSTEMS_WDI_MODEL_SEARCH_REPORT.json"
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

REQUIRED_ROW_FIELDS = (
    "official_sources",
    "target_variable",
    "prediction_formula",
    "incumbent_comparator",
    "uncertainty_and_residual",
    "negative_control",
    "falsifier_predicates",
    "replay_protocol",
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


def world_bank_wdi_url(country: str, indicator: str, date_range: str = "1960:2024") -> str:
    return (
        f"https://api.worldbank.org/v2/country/{country}/indicator/{indicator}?"
        + urlencode({"format": "json", "per_page": "20000", "date": date_range})
    )


def no_send() -> dict[str, Any]:
    return dict(NO_SEND_LOCKS)


def with_hash(row: dict[str, Any]) -> dict[str, Any]:
    row = dict(row)
    row["row_sha256"] = sha256_object(row)
    return row


def wdi_source(source_id: str = "WORLD_BANK_WDI_API") -> dict[str, Any]:
    return {
        "source_id": source_id,
        "title": "World Bank World Development Indicators API",
        "official_url": "https://api.worldbank.org/v2/",
        "local_source_capsule_ref": "comparators/modern_science/source_capsules/MS-SRC-SYS-WORLD-BANK-WDI.txt",
        "access_mode": "read_only_https_get",
        "runner_allowlist_status": "ALLOWLISTED",
    }


def common_formula() -> dict[str, Any]:
    return {
        "formula_id": "SYSTEMS-WDI-TRAINING-ONLY-FORMULA-SELECTOR",
        "rule": (
            "select, using only years earlier than heldout_year, the lowest prior validation residual among "
            "carry_forward, linear_last_slope, damped_slope_25/50/75, rolling_mean_3/5, rolling_slope_3/5, "
            "and simple exponential smoothing; then score the heldout target once"
        ),
        "inputs_visible_before_target": [
            "country code",
            "indicator id",
            "strictly prior annual values",
            "pre-registered formula manifest",
            "pre-registered comparator manifest",
        ],
        "target_values_used_for_selection": False,
    }


def common_comparator(label: str) -> dict[str, Any]:
    return {
        "name": f"{label} best-of carry-forward, prior-mean, and trailing-mean comparators",
        "prediction_rule": (
            "score each heldout target against preregistered last-observation carry-forward, "
            "prior-training mean, and trailing-three-year mean baselines on the same source snapshot"
        ),
        "pre_registered": True,
    }


def common_uncertainty() -> dict[str, Any]:
    return {
        "residual_metric": "absolute residual per heldout country/indicator/year; aggregate mean absolute residual",
        "uncertainty_method": "selected-formula prior validation residual envelope declared before target unsealing",
        "superiority_predicate": "every row and aggregate residual margin must exceed preregistered materiality thresholds",
    }


def common_negative_control(control_id: str) -> dict[str, Any]:
    return {
        "control_id": control_id,
        "description": "every preregistered comparator must have larger heldout absolute residual than the selected training-only model",
        "rejection_predicate": "all comparator_residual values are strictly greater than model_residual for every accepted row",
    }


def common_falsifiers() -> list[str]:
    return [
        "source-lock declaration contains observed target values, predictions, residuals, or row hashes",
        "formula selection uses heldout target rows or non-prior validation rows",
        "any comparator beats or ties the selected model within uncertainty/materiality policy",
        "target mutation fails to change the candidate-pack or row hash",
        "official source snapshot hash changes between acquisition and replay",
    ]


def common_acceptance(extra: list[str] | None = None) -> list[str]:
    return [
        "OFFICIAL_SOURCE_SNAPSHOT_HASH_BOUND",
        "TARGET_VARIABLE_DECLARED",
        "TARGET_HIDDEN_OR_PROSPECTIVE_LOCK_DECLARED",
        "PREDICTION_FORMULA_DECLARED_BEFORE_SCORING",
        "COMPARATOR_PREREGISTERED_AND_NONTRIVIAL",
        "UNCERTAINTY_AND_RESIDUAL_DECLARED",
        "NEGATIVE_CONTROL_REJECTION_REQUIRED",
        "FALSIFIER_PREDICATES_EXECUTABLE",
        "INDEPENDENT_REPLAY_REQUIRED",
        "COVERAGE_GAP_REMAINS_OPEN_UNTIL_REVIEW",
        "NO_BROAD_SUPERIORITY_CERTIFICATION",
        *(extra or []),
    ]


def wdi_request(request_id: str, country: str, indicator: str, expected_name: str, date_range: str = "1960:2024") -> dict[str, Any]:
    return {
        "request_id": request_id,
        "http_method": "GET",
        "official_endpoint_url": world_bank_wdi_url(country, indicator, date_range),
        "expected_local_snapshot_ref": (
            "validation/heldout/grand_science/systems/coverage_work_orders/raw/"
            f"{expected_name}.json"
        ),
        "country": country,
        "indicator": indicator,
        "date_range": date_range,
        "hash_required": True,
        "no_send_lock": True,
    }


def build_work_orders() -> list[dict[str, Any]]:
    rows = [
        {
            "work_order_id": "OC133-SYSTEMS-COVERAGE-ECONOMIC-INDICATOR-MARKET-OBSERVABLES",
            "coverage_gap_id": "MS-COV-GAP-SOCIAL_ECONOMIC_POLITICAL_SCIENCES-ECONOMIC_INDICATOR_AND_MARKET_OBSERVABLES",
            "domain_class_id": "social_economic_political_sciences",
            "phenomenon_class_id": "economic_indicator_and_market_observables",
            "phenomenon_label": "economic indicator and market observables",
            "lane_status": "FAIL_CLOSED_PENDING_GENERALIZED_WDI_INDICATOR_REPLAY",
            "coverage_closure_allowed": False,
            "support_allowed_for_broad_coverage": False,
            "current_evidence_assessment": (
                "The current WDI population materiality lane proves the target-hidden machinery for one "
                "demographic series. It does not close economic or market coverage until GDP/market "
                "indicator rows replay with all comparators and materiality predicates."
            ),
            "existing_official_lane_refs": [
                WDI_POPULATION_PACK_REL,
                WDI_POPULATION_PROTOCOL_REL,
                WDI_MODEL_SEARCH_REPORT_REL,
            ],
            "official_sources": [wdi_source()],
            "acquisition_requests": [
                wdi_request(
                    "OC133-SYS-COV-WDI-GDP-WLD-0001",
                    "WLD",
                    "NY.GDP.MKTP.CD",
                    "world_bank_wdi_wld_gdp_current_usd_1960_2024",
                )
            ],
            "target_variable": {
                "name": "heldout_world_gdp_current_usd",
                "unit": "current US dollars",
                "target_field": "WDI[WLD, NY.GDP.MKTP.CD, heldout_year].value",
                "minimum_target_rows": 20,
                "target_hidden_until_scoring": True,
            },
            "prediction_formula": common_formula(),
            "incumbent_comparator": common_comparator("WDI GDP"),
            "uncertainty_and_residual": common_uncertainty(),
            "negative_control": common_negative_control("SYSTEMS-WDI-GDP-COMPARATOR-NEGATIVE-CONTROL"),
            "falsifier_predicates": common_falsifiers(),
            "replay_protocol": {
                "commands": [
                    "python tools/oc133_official_readonly_acquisition_runner.py --packet <generated_wdi_gdp_acquisition_packet> --write-report --allow-blocked-exit-zero",
                    "python tools/oc133_systems_wdi_predictive_search_v2_factory.py --snapshot-ref <locked_wdi_gdp_snapshot> --write --allow-blocked-exit-zero",
                    "python validation/heldout/grand_science/systems/coverage_work_orders/oc133_systems_civilizational_modern_science_coverage_work_orders.py --check",
                ],
                "required_artifacts": [
                    "WDI GDP source snapshot",
                    "pre-target WDI source lock",
                    "target-hidden GDP task rows",
                    "strict WDI economic indicator candidate pack",
                ],
                "acceptance_predicates": common_acceptance(["WDI_ECONOMIC_INDICATOR_SCOPE_REVIEWED"]),
            },
            "remaining_blockers": [
                "GENERALIZED_WDI_GDP_REPLAY_NOT_MATERIALIZED",
                "CURRENT_WDI_MODEL_SEARCH_HAS_NEGATIVE_CONTROL_FAILURES",
                "COVERAGE_REVIEW_NOT_PERFORMED",
            ],
            "no_send_locks": no_send(),
        },
        {
            "work_order_id": "OC133-SYSTEMS-COVERAGE-INSTITUTIONAL-SOCIAL-NETWORK-POLICY-OUTCOMES",
            "coverage_gap_id": "MS-COV-GAP-SOCIAL_ECONOMIC_POLITICAL_SCIENCES-INSTITUTIONAL_SOCIAL_NETWORK_AND_POLICY_OUTCOMES",
            "domain_class_id": "social_economic_political_sciences",
            "phenomenon_class_id": "institutional_social_network_and_policy_outcomes",
            "phenomenon_label": "institutional social network and policy outcomes",
            "lane_status": "FAIL_CLOSED_PENDING_WDI_WGI_POLICY_REPLAY",
            "coverage_closure_allowed": False,
            "support_allowed_for_broad_coverage": False,
            "current_evidence_assessment": "No current strict pack covers institutional, governance, policy, or social-network outcome targets.",
            "official_sources": [wdi_source("WORLD_BANK_WGI_VIA_WDI_API")],
            "acquisition_requests": [
                wdi_request(
                    "OC133-SYS-COV-WDI-WGI-GE-0001",
                    "all",
                    "GE.EST",
                    "world_bank_wgi_government_effectiveness_estimate",
                    "1996:2024",
                ),
                wdi_request(
                    "OC133-SYS-COV-WDI-WGI-RL-0001",
                    "all",
                    "RL.EST",
                    "world_bank_wgi_rule_of_law_estimate",
                    "1996:2024",
                ),
            ],
            "target_variable": {
                "name": "heldout_country_year_governance_estimate",
                "unit": "World Bank WGI estimate units",
                "target_field": "WDI[country, GE.EST or RL.EST, heldout_year].value",
                "minimum_target_rows": 20,
                "target_hidden_until_scoring": True,
            },
            "prediction_formula": common_formula(),
            "incumbent_comparator": common_comparator("WGI governance"),
            "uncertainty_and_residual": common_uncertainty(),
            "negative_control": common_negative_control("SYSTEMS-WGI-POLICY-COMPARATOR-NEGATIVE-CONTROL"),
            "falsifier_predicates": common_falsifiers(),
            "replay_protocol": {
                "commands": [
                    "python tools/oc133_official_readonly_acquisition_runner.py --packet <generated_wgi_acquisition_packet> --write-report --allow-blocked-exit-zero",
                    "python tools/oc133_systems_wdi_predictive_search_v2_factory.py --snapshot-ref <locked_wgi_snapshot> --write --allow-blocked-exit-zero",
                    "python validation/heldout/grand_science/systems/coverage_work_orders/oc133_systems_civilizational_modern_science_coverage_work_orders.py --check",
                ],
                "required_artifacts": [
                    "WGI source snapshot through WDI API",
                    "policy/governance target-hidden source lock",
                    "strict institutional-policy candidate pack",
                ],
                "acceptance_predicates": common_acceptance(["WGI_POLICY_SCOPE_REVIEWED"]),
            },
            "remaining_blockers": [
                "WGI_SOURCE_SNAPSHOTS_NOT_ACQUIRED",
                "STRICT_POLICY_OUTCOME_EVIDENCE_PACK_NOT_BUILT",
                "COVERAGE_REVIEW_NOT_PERFORMED",
            ],
            "no_send_locks": no_send(),
        },
        {
            "work_order_id": "OC133-SYSTEMS-COVERAGE-MULTI-AGENT-SYSTEM-DYNAMICS",
            "coverage_gap_id": "MS-COV-GAP-COMPLEX_SYSTEMS_OPERATIONS_SCIENCE-MULTI_AGENT_SYSTEM_DYNAMICS",
            "domain_class_id": "complex_systems_operations_science",
            "phenomenon_class_id": "multi_agent_system_dynamics",
            "phenomenon_label": "multi agent system dynamics",
            "lane_status": "FAIL_CLOSED_PENDING_WDI_FLOW_DYNAMICS_REPLAY",
            "coverage_closure_allowed": False,
            "support_allowed_for_broad_coverage": False,
            "current_evidence_assessment": "No current strict pack covers multi-agent flow, migration, network, or interaction dynamics.",
            "official_sources": [wdi_source()],
            "acquisition_requests": [
                wdi_request(
                    "OC133-SYS-COV-WDI-NET-MIGRATION-0001",
                    "all",
                    "SM.POP.NETM",
                    "world_bank_wdi_net_migration_country_year",
                ),
                wdi_request(
                    "OC133-SYS-COV-WDI-URBAN-POP-SHARE-0001",
                    "all",
                    "SP.URB.TOTL.IN.ZS",
                    "world_bank_wdi_urban_population_share_country_year",
                ),
            ],
            "target_variable": {
                "name": "heldout_country_year_net_migration",
                "unit": "people",
                "target_field": "WDI[country, SM.POP.NETM, heldout_year].value",
                "minimum_target_rows": 20,
                "target_hidden_until_scoring": True,
            },
            "prediction_formula": common_formula(),
            "incumbent_comparator": common_comparator("WDI flow-dynamics"),
            "uncertainty_and_residual": common_uncertainty(),
            "negative_control": common_negative_control("SYSTEMS-MULTI-AGENT-FLOW-COMPARATOR-NEGATIVE-CONTROL"),
            "falsifier_predicates": common_falsifiers(),
            "replay_protocol": {
                "commands": [
                    "python tools/oc133_official_readonly_acquisition_runner.py --packet <generated_wdi_flow_acquisition_packet> --write-report --allow-blocked-exit-zero",
                    "python tools/oc133_systems_wdi_predictive_search_v2_factory.py --snapshot-ref <locked_wdi_flow_snapshot> --write --allow-blocked-exit-zero",
                    "python validation/heldout/grand_science/systems/coverage_work_orders/oc133_systems_civilizational_modern_science_coverage_work_orders.py --check",
                ],
                "required_artifacts": [
                    "WDI migration/urbanization source snapshots",
                    "target-hidden flow-dynamics task rows",
                    "strict multi-agent systems candidate pack",
                ],
                "acceptance_predicates": common_acceptance(["MULTI_AGENT_FLOW_SCOPE_REVIEWED"]),
            },
            "remaining_blockers": [
                "WDI_FLOW_DYNAMICS_SOURCE_SNAPSHOTS_NOT_ACQUIRED",
                "STRICT_MULTI_AGENT_FLOW_EVIDENCE_PACK_NOT_BUILT",
            ],
            "no_send_locks": no_send(),
        },
        {
            "work_order_id": "OC133-SYSTEMS-COVERAGE-QUEUE-SUPPLY-CHAIN-OPERATIONS-OBSERVABLES",
            "coverage_gap_id": "MS-COV-GAP-COMPLEX_SYSTEMS_OPERATIONS_SCIENCE-QUEUE_SUPPLY_CHAIN_AND_OPERATIONS_OBSERVABLES",
            "domain_class_id": "complex_systems_operations_science",
            "phenomenon_class_id": "queue_supply_chain_and_operations_observables",
            "phenomenon_label": "queue supply chain and operations observables",
            "lane_status": "FAIL_CLOSED_PENDING_WDI_OPERATIONS_REPLAY",
            "coverage_closure_allowed": False,
            "support_allowed_for_broad_coverage": False,
            "current_evidence_assessment": "No current strict pack covers queue, logistics, supply-chain, or operations-measurement targets.",
            "official_sources": [wdi_source()],
            "acquisition_requests": [
                wdi_request(
                    "OC133-SYS-COV-WDI-CONTAINER-PORT-TRAFFIC-0001",
                    "all",
                    "IS.SHP.GOOD.TU",
                    "world_bank_wdi_container_port_traffic_country_year",
                ),
                wdi_request(
                    "OC133-SYS-COV-WDI-AIR-PASSENGERS-0001",
                    "all",
                    "IS.AIR.PSGR",
                    "world_bank_wdi_air_transport_passengers_country_year",
                ),
            ],
            "target_variable": {
                "name": "heldout_country_year_container_port_traffic",
                "unit": "TEU",
                "target_field": "WDI[country, IS.SHP.GOOD.TU, heldout_year].value",
                "minimum_target_rows": 20,
                "target_hidden_until_scoring": True,
            },
            "prediction_formula": common_formula(),
            "incumbent_comparator": common_comparator("WDI logistics/operations"),
            "uncertainty_and_residual": common_uncertainty(),
            "negative_control": common_negative_control("SYSTEMS-OPERATIONS-COMPARATOR-NEGATIVE-CONTROL"),
            "falsifier_predicates": common_falsifiers(),
            "replay_protocol": {
                "commands": [
                    "python tools/oc133_official_readonly_acquisition_runner.py --packet <generated_wdi_operations_acquisition_packet> --write-report --allow-blocked-exit-zero",
                    "python tools/oc133_systems_wdi_predictive_search_v2_factory.py --snapshot-ref <locked_wdi_operations_snapshot> --write --allow-blocked-exit-zero",
                    "python validation/heldout/grand_science/systems/coverage_work_orders/oc133_systems_civilizational_modern_science_coverage_work_orders.py --check",
                ],
                "required_artifacts": [
                    "WDI logistics/transport source snapshots",
                    "target-hidden operations task rows",
                    "strict queue/supply-chain candidate pack",
                ],
                "acceptance_predicates": common_acceptance(["OPERATIONS_LOGISTICS_SCOPE_REVIEWED"]),
            },
            "remaining_blockers": [
                "WDI_OPERATIONS_SOURCE_SNAPSHOTS_NOT_ACQUIRED",
                "STRICT_OPERATIONS_EVIDENCE_PACK_NOT_BUILT",
            ],
            "no_send_locks": no_send(),
        },
        {
            "work_order_id": "OC133-SYSTEMS-COVERAGE-RESILIENCE-RISK-INTERVENTION-RESPONSE",
            "coverage_gap_id": "MS-COV-GAP-COMPLEX_SYSTEMS_OPERATIONS_SCIENCE-RESILIENCE_RISK_AND_INTERVENTION_RESPONSE",
            "domain_class_id": "complex_systems_operations_science",
            "phenomenon_class_id": "resilience_risk_and_intervention_response",
            "phenomenon_label": "resilience risk and intervention response",
            "lane_status": "FAIL_CLOSED_PENDING_OFFICIAL_DISASTER_SOURCE_ALLOWLIST_AND_REPLAY",
            "coverage_closure_allowed": False,
            "support_allowed_for_broad_coverage": False,
            "current_evidence_assessment": "No current strict pack covers disaster resilience, intervention timing, or post-event response observables.",
            "official_sources": [
                {
                    "source_id": "FEMA_OPENFEMA_DISASTER_DECLARATIONS",
                    "title": "FEMA OpenFEMA Disaster Declarations Summaries",
                    "official_url": "https://www.fema.gov/openfema-data-page/disaster-declarations-summaries-v2",
                    "access_mode": "read_only_https_get",
                    "runner_allowlist_status": "BLOCKED_PENDING_ALLOWLIST_ENTRY_AND_SOURCE_CAPSULE",
                }
            ],
            "acquisition_requests": [
                {
                    "request_id": "OC133-SYS-COV-FEMA-DISASTER-DECLARATIONS-0001",
                    "http_method": "GET",
                    "official_endpoint_url": (
                        "https://www.fema.gov/openfema-data-hub/arcgis/rest/services/"
                        "FEMA_Disaster_Declarations_Summaries_v2/FeatureServer/0/query?"
                        + urlencode(
                            {
                                "where": "declarationDate >= DATE '2000-01-01'",
                                "outFields": "disasterNumber,state,declarationDate,incidentType,designatedArea",
                                "f": "json",
                                "resultRecordCount": "2000",
                            }
                        )
                    ),
                    "expected_local_snapshot_ref": (
                        "validation/heldout/grand_science/systems/coverage_work_orders/raw/"
                        "resilience_risk/fema_disaster_declarations_2000_present.json"
                    ),
                    "hash_required": True,
                    "no_send_lock": True,
                    "blocked_until": "official_readonly_runner_allowlist_adds_FEMA_OpenFEMA_endpoint",
                }
            ],
            "target_variable": {
                "name": "heldout_state_month_disaster_declaration_count",
                "unit": "declaration records per state/month",
                "target_field": "OpenFEMA[state, incidentType, heldout_month].declaration_count",
                "minimum_target_rows": 20,
                "target_hidden_until_scoring": True,
            },
            "prediction_formula": {
                "formula_id": "SYSTEMS-RESILIENCE-SEASONAL-RISK-SLOPE",
                "rule": "y_hat(state, month) = trailing_same_month_mean_5yr + mean(last three monthly deltas)",
                "inputs_visible_before_target": [
                    "state",
                    "incident type",
                    "prior monthly declaration counts",
                    "pre-registered seasonal window",
                ],
                "target_values_used_for_selection": False,
            },
            "incumbent_comparator": {
                "name": "OpenFEMA seasonal carry-forward response-risk comparator",
                "prediction_rule": "predict heldout declaration count from prior same-month mean and previous-month count",
                "pre_registered": True,
            },
            "uncertainty_and_residual": {
                "residual_metric": "absolute count residual per state/month; aggregate mean absolute residual",
                "uncertainty_method": "pre-event rolling seasonal residual envelope",
                "superiority_predicate": "model residual plus uncertainty is smaller than best preregistered comparator residual",
            },
            "negative_control": {
                "control_id": "SYSTEMS-RESILIENCE-MONTH-SHUFFLE-CONTROL",
                "description": "shuffle heldout month labels after source lock; replay must reject the shuffled intervention timeline",
                "rejection_predicate": "shuffled month mapping changes row hashes and worsens residuals relative to locked targets",
            },
            "falsifier_predicates": [
                "OpenFEMA source snapshot cannot be hashed or replayed",
                "heldout declaration counts leak into formula selection",
                "seasonal carry-forward comparator ties or beats the model within uncertainty",
                "month-shuffle control does not change row hashes",
            ],
            "replay_protocol": {
                "commands": [
                    "extend official_readonly_acquisition_runner allowlist for the OpenFEMA ArcGIS query endpoint",
                    "python tools/oc133_official_readonly_acquisition_runner.py --packet <generated_fema_acquisition_packet> --write-report --allow-blocked-exit-zero",
                    "python validation/heldout/grand_science/systems/coverage_work_orders/oc133_systems_civilizational_modern_science_coverage_work_orders.py --check",
                ],
                "required_artifacts": [
                    "OpenFEMA source capsule and allowlist entry",
                    "target-hidden state/month declaration task rows",
                    "strict resilience/intervention response candidate pack",
                ],
                "acceptance_predicates": common_acceptance(["OPENFEMA_ALLOWLIST_AND_SOURCE_CAPSULE_REVIEWED"]),
            },
            "remaining_blockers": [
                "FEMA_SOURCE_CAPSULE_NOT_PRESENT",
                "FEMA_RUNNER_ALLOWLIST_NOT_PRESENT",
                "STRICT_RESILIENCE_RESPONSE_EVIDENCE_PACK_NOT_BUILT",
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
        "modern_science_protocol_ref": MODERN_PROTOCOL_REL,
        "domain_family": "systems_civilizational",
        "domain_class_ids": [
            "social_economic_political_sciences",
            "complex_systems_operations_science",
        ],
        "work_order_total": len(rows),
        "fail_closed_or_review_pending_total": len(rows),
        "coverage_closure_allowed": False,
        "broad_modern_science_superiority_allowed": False,
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
    if not isinstance(rows, list) or payload.get("work_order_total") != len(rows):
        failures.append("WORK_ORDER_TOTAL_MISMATCH")
        return failures
    expected_phenomena = {
        "economic_indicator_and_market_observables",
        "institutional_social_network_and_policy_outcomes",
        "multi_agent_system_dynamics",
        "queue_supply_chain_and_operations_observables",
        "resilience_risk_and_intervention_response",
    }
    actual_phenomena = {str(row.get("phenomenon_class_id")) for row in rows if isinstance(row, dict)}
    if actual_phenomena != expected_phenomena:
        failures.append("SYSTEMS_CIVILIZATIONAL_PHENOMENON_SET_MISMATCH")
    for row in rows:
        if not isinstance(row, dict):
            failures.append("WORK_ORDER_NOT_OBJECT")
            continue
        row_id = str(row.get("work_order_id", "unknown"))
        if row.get("coverage_closure_allowed") is not False:
            failures.append(f"COVERAGE_CLOSURE_ALLOWED::{row_id}")
        if row.get("support_allowed_for_broad_coverage") is not False:
            failures.append(f"BROAD_SUPPORT_ALLOWED::{row_id}")
        if str(row.get("lane_status")).upper() == "PASS":
            failures.append(f"FAKE_PASS_STATUS::{row_id}")
        for field in REQUIRED_ROW_FIELDS:
            if not row.get(field):
                failures.append(f"REQUIRED_FIELD_MISSING::{row_id}::{field}")
        if not row.get("target_variable", {}).get("name"):
            failures.append(f"TARGET_VARIABLE_NAME_MISSING::{row_id}")
        if not row.get("prediction_formula", {}).get("rule"):
            failures.append(f"PREDICTION_FORMULA_RULE_MISSING::{row_id}")
        if not row.get("incumbent_comparator", {}).get("prediction_rule"):
            failures.append(f"COMPARATOR_RULE_MISSING::{row_id}")
        if not row.get("uncertainty_and_residual", {}).get("residual_metric"):
            failures.append(f"RESIDUAL_METRIC_MISSING::{row_id}")
        if not row.get("negative_control", {}).get("rejection_predicate"):
            failures.append(f"NEGATIVE_CONTROL_PREDICATE_MISSING::{row_id}")
        if not row.get("falsifier_predicates"):
            failures.append(f"FALSIFIER_PREDICATES_MISSING::{row_id}")
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
    parser = argparse.ArgumentParser(description="Build/check systems/civilizational modern-science coverage work orders.")
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
