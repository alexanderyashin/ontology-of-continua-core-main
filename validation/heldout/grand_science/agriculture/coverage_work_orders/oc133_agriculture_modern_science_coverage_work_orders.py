from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
GENERATED_ON = "2026-05-01"
SCHEMA_ID = "OC133_AGRICULTURE_MODERN_SCIENCE_COVERAGE_WORK_ORDERS_v1"
ACQUISITION_SCHEMA_ID = "OC133_AGRICULTURE_FDC_READONLY_ACQUISITION_v1"
LOCK_SCHEMA_ID = "OC133_AGRICULTURE_FDC_SOURCE_LOCK_v1"
REPORT_SCHEMA_ID = "OC133_AGRICULTURE_FDC_REPLAY_REPORT_v1"
FDC_TASK_TABLE_SCHEMA_ID = "OC133_AGRICULTURE_FDC_SODIUM_TARGET_HIDDEN_TASK_TABLE_v1"
FDC_HIDDEN_TARGET_LOCK_SCHEMA_ID = "OC133_AGRICULTURE_FDC_SODIUM_HIDDEN_TARGET_LOCK_v1"
FDC_SCORING_PACK_SCHEMA_ID = "OC133_AGRICULTURE_FDC_SODIUM_SCORING_PACK_v1"
FDC_SCORING_BLOCKER_SCHEMA_ID = "OC133_AGRICULTURE_FDC_SODIUM_SCORING_BLOCKER_v1"
CAPABILITY_OWNER = "Logion Agriculture Evidence / Food, Crop, and Veterinary Sources"

SCRIPT_REL = (
    "validation/heldout/grand_science/agriculture/coverage_work_orders/"
    "oc133_agriculture_modern_science_coverage_work_orders.py"
)
OUTPUT_REL = (
    "validation/heldout/grand_science/agriculture/coverage_work_orders/"
    "OC133_AGRICULTURE_MODERN_SCIENCE_COVERAGE_WORK_ORDERS.json"
)
FDC_SNAPSHOT_REL = (
    "validation/heldout/grand_science/agriculture/coverage_work_orders/raw/"
    "OC133_AGRICULTURE_FDC_FOUNDATION_FOODS_LIST_25.compact.json"
)
FDC_LOCK_REL = (
    "validation/heldout/grand_science/agriculture/coverage_work_orders/locks/"
    "OC133-AGRI-FDC-FOUNDATION-FOODS-LIST-0001.lock.json"
)
FDC_REPORT_REL = (
    "validation/heldout/grand_science/agriculture/coverage_work_orders/"
    "OC133_AGRICULTURE_FDC_REPLAY_REPORT.json"
)
FDC_TASK_TABLE_REL = (
    "validation/heldout/grand_science/agriculture/coverage_work_orders/"
    "OC133_AGRICULTURE_FDC_SODIUM_TARGET_HIDDEN_TASK_TABLE.json"
)
FDC_HIDDEN_TARGET_LOCK_REL = (
    "validation/heldout/grand_science/agriculture/coverage_work_orders/locks/"
    "OC133-AGRI-FDC-SODIUM-HIDDEN-TARGETS-0001.lock.json"
)
FDC_SCORING_PACK_REL = (
    "validation/heldout/grand_science/agriculture/coverage_work_orders/"
    "OC133_AGRICULTURE_FDC_SODIUM_SCORING_PACK.json"
)
FDC_SCORING_BLOCKER_REL = (
    "validation/heldout/grand_science/agriculture/coverage_work_orders/"
    "OC133_AGRICULTURE_FDC_SODIUM_SCORING_BLOCKER.json"
)
COVERAGE_REGISTER_REL = "comparators/modern_science/OC133_MODERN_SCIENCE_COVERAGE_REGISTER.json"

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
    "target_variable",
    "target_hidden_split",
    "formula_model",
    "preregistered_comparator",
    "uncertainty_residual_metric",
    "negative_control",
    "falsifier",
    "minimum_n",
    "replay_command",
    "current_evidence_status",
)

FDC_SELECTED_NUTRIENT_NUMBERS = {
    "203": "Protein",
    "204": "Total lipid (fat)",
    "205": "Carbohydrate, by difference",
    "207": "Ash",
    "208": "Energy",
    "301": "Calcium, Ca",
    "307": "Sodium, Na",
}
FDC_VISIBLE_NUTRIENT_NUMBERS = tuple(number for number in FDC_SELECTED_NUTRIENT_NUMBERS if number != "307")
FDC_REQUIRED_SCORING_NUTRIENTS = ("207", "301", "307")
FDC_SODIUM_ASH_NACL_FACTOR_MG_PER_G = 393.37
FDC_SODIUM_MODEL_ID = "AGRI-FDC-VISIBLE-ASH-SODIUM-PROXY-v1"
FDC_SODIUM_MODEL_RULE = (
    "predict sodium_mg_per_100g = max(0, 393.37 * visible_ash_g_per_100g), using the sodium mass "
    "fraction of sodium chloride as a fixed visible-ash proxy; nutrient 307 is excluded from visible "
    "inputs and is unsealed only for scoring"
)
FDC_SODIUM_COMPARATOR_ID = "AGRI-FDC-VISIBLE-CALCIUM-MINERAL-BASELINE-v1"
FDC_SODIUM_COMPARATOR_RULE = (
    "predict sodium_mg_per_100g = visible calcium_mg_per_100g from nutrient 301"
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[5]


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_object(payload: Any) -> str:
    return sha256_text(canonical_json(payload))


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


def usda_quickstats_url(params: dict[str, str]) -> str:
    return "https://quickstats.nass.usda.gov/api/api_GET/?" + urlencode(params)


def fdc_foods_list_url(page_size: int = 25, api_key: str = "DEMO_KEY") -> str:
    return "https://api.nal.usda.gov/fdc/v1/foods/list?" + urlencode(
        {
            "api_key": api_key,
            "dataType": "Foundation",
            "pageSize": str(page_size),
            "sortBy": "fdcId",
            "sortOrder": "asc",
        }
    )


def faostat_bulk_qcl_url() -> str:
    return "https://fenixservices.fao.org/faostat/static/bulkdownloads/Production_Crops_Livestock_E_All_Data.zip"


def common_acceptance_predicates(extra: list[str] | None = None) -> list[str]:
    return [
        "OFFICIAL_SOURCE_URL_DECLARED",
        "OFFICIAL_SOURCE_SNAPSHOT_HASH_BOUND",
        "TARGET_VARIABLE_DECLARED",
        "TARGET_HIDDEN_OR_PROSPECTIVE_SPLIT_DECLARED",
        "FORMULA_OR_MODEL_PREREGISTERED_BEFORE_SCORING",
        "COMPARATOR_PREREGISTERED_AND_TARGET_SEPARATED",
        "UNCERTAINTY_AND_RESIDUAL_METRIC_DECLARED",
        "NEGATIVE_CONTROL_EXECUTABLE",
        "FALSIFIER_EXECUTABLE",
        "MINIMUM_N_GE_20",
        "INDEPENDENT_REPLAY_COMMAND_DECLARED",
        "COVERAGE_CLOSURE_ALLOWED_FALSE",
        "NO_BROAD_SUPERIORITY_CERTIFICATION",
        *(extra or []),
    ]


def official_source(
    source_id: str,
    title: str,
    official_url: str,
    *,
    documentation_url: str | None = None,
    access_mode: str = "read_only_https_get",
    runner_status: str = "OPEN_FAIL_CLOSED_SOURCE_NOT_YET_BOUND",
    local_snapshot_ref: str | None = None,
    lock_ref: str | None = None,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "source_id": source_id,
        "title": title,
        "official_url": official_url,
        "access_mode": access_mode,
        "runner_allowlist_status": runner_status,
    }
    if documentation_url:
        row["official_documentation_url"] = documentation_url
    if local_snapshot_ref:
        row["local_snapshot_ref"] = local_snapshot_ref
    if lock_ref:
        row["lock_ref"] = lock_ref
    return row


def build_work_orders() -> list[dict[str, Any]]:
    rows = [
        {
            "work_order_id": "MS-COV-WO-019",
            "coverage_gap_id": "MS-COV-GAP-AGRICULTURAL_FOOD_SCIENCES-CROP_YIELD_SOIL_AND_TRAIT_OBSERVABLES",
            "domain_class_id": "agricultural_food_sciences",
            "phenomenon_class_id": "crop_yield_soil_and_trait_observables",
            "phenomenon_label": "crop yield soil and trait observables",
            "lane_status": "OPEN_FAIL_CLOSED_NO_EXECUTABLE_EVIDENCE",
            "coverage_closure_allowed": False,
            "support_allowed_for_broad_coverage": False,
            "official_sources": [
                official_source(
                    "USDA_NASS_QUICKSTATS_API",
                    "USDA National Agricultural Statistics Service Quick Stats API",
                    "https://quickstats.nass.usda.gov/api",
                    documentation_url="https://www.nass.usda.gov/developer/",
                    runner_status="BLOCKED_REQUIRES_USDA_NASS_API_KEY_AND_SOURCE_LOCK",
                ),
                official_source(
                    "USDA_NRCS_SOIL_DATA_ACCESS",
                    "USDA NRCS Soil Data Access tabular REST service",
                    "https://SDMDataAccess.sc.egov.usda.gov/Tabular/post.rest",
                    documentation_url="https://sdmdataaccess.nrcs.usda.gov/WebServiceHelp.aspx",
                    access_mode="read_only_https_post",
                    runner_status="BLOCKED_PENDING_SDA_QUERY_LOCK_AND_COUNTY_JOIN",
                ),
            ],
            "acquisition_requests": [
                {
                    "request_id": "OC133-AGRI-CROP-NASS-CORN-YIELD-IA-STATE-2000-2024",
                    "http_method": "GET",
                    "official_endpoint_url_template": usda_quickstats_url(
                        {
                            "key": "${USDA_QUICKSTATS_API_KEY}",
                            "source_desc": "SURVEY",
                            "sector_desc": "CROPS",
                            "group_desc": "FIELD CROPS",
                            "commodity_desc": "CORN",
                            "statisticcat_desc": "YIELD",
                            "agg_level_desc": "STATE",
                            "state_alpha": "IA",
                            "year__GE": "2000",
                            "format": "JSON",
                        }
                    ),
                    "expected_local_snapshot_ref": (
                        "validation/heldout/grand_science/agriculture/coverage_work_orders/raw/"
                        "crop_yield_soil_traits/usda_nass_ia_corn_yield_2000_2024.json"
                    ),
                    "hash_required": True,
                    "blocked_until": "USDA_QUICKSTATS_API_KEY_AND_TARGET_LOCK_PRESENT",
                    "no_send_lock": True,
                },
                {
                    "request_id": "OC133-AGRI-CROP-NRCS-SDA-IA-SOIL-COMPONENTS",
                    "http_method": "POST",
                    "official_endpoint_url": "https://SDMDataAccess.sc.egov.usda.gov/Tabular/post.rest",
                    "expected_local_snapshot_ref": (
                        "validation/heldout/grand_science/agriculture/coverage_work_orders/raw/"
                        "crop_yield_soil_traits/usda_nrcs_sda_ia_soil_components.json"
                    ),
                    "hash_required": True,
                    "blocked_until": "USDA_NRCS_SDA_SQL_QUERY_AND_COUNTY_JOIN_PREREGISTERED",
                    "no_send_lock": True,
                },
            ],
            "target_variable": {
                "name": "heldout_county_or_state_year_corn_yield",
                "unit": "bushels per acre",
                "target_fields": ["Value", "year", "state_alpha", "county_code_or_state_alpha"],
                "official_target_source": "USDA_NASS_QUICKSTATS_API",
                "minimum_target_rows": 20,
            },
            "target_hidden_split": {
                "source_separation_mode": "target_blind",
                "training_visible": "QuickStats crop-yield rows with year <= 2018 plus locked NRCS soil attributes",
                "target_hidden_until_scoring": "QuickStats crop-yield rows with year >= 2019 are sealed until predictions and comparator outputs are materialized",
                "split_key": "state_or_county x year",
                "target_values_used_for_selection": False,
            },
            "formula_model": {
                "formula_id": "AGRI-CROP-SOIL-TRAIT-TRAINING-ONLY-TREND-MODEL",
                "rule": (
                    "y_hat(location, year) = training-only location intercept + pre-2019 linear year trend "
                    "+ locked soil available-water/slope terms + lagged visible yield residual adjustment"
                ),
                "visible_inputs": [
                    "pre-target QuickStats yield rows",
                    "NRCS Soil Data Access soil attributes",
                    "locked location identifiers",
                    "pre-registered crop/soil feature manifest",
                ],
                "target_values_used_for_model_design": False,
            },
            "preregistered_comparator": {
                "name": "USDA QuickStats trailing-mean and linear-trend agronomic baseline",
                "prediction_rule": "predict each heldout yield row using the better pre-2019 five-year trailing mean or pre-2019 linear trend for the same location",
                "pre_registered": True,
                "target_values_used_for_baseline_design": False,
            },
            "uncertainty_residual_metric": {
                "residual_metric": "absolute yield residual in bushels per acre; aggregate MAE over heldout location/year rows",
                "uncertainty_method": "pre-2019 rolling-origin residual envelope by location and crop",
                "superiority_predicate": "model_MAE + uncertainty_margin < comparator_MAE on the same heldout rows",
            },
            "negative_control": {
                "control_id": "AGRI-CROP-YEAR-SHUFFLE-CONTROL",
                "description": "shuffle heldout years within location after source lock",
                "rejection_predicate": "shuffled-year target mapping must change row hashes and worsen the residual envelope relative to locked targets",
            },
            "falsifier": {
                "falsifier_id": "AGRI-CROP-QUICKSTATS-SOIL-FALSIFIER",
                "triggers": [
                    "QuickStats or Soil Data Access snapshot hash is missing or changes during replay",
                    "heldout yield values appear in visible inputs, formula selection, or comparator selection",
                    "N is below 20",
                    "trailing-mean or trend comparator ties or beats the model within uncertainty",
                    "year-shuffle negative control is not rejected",
                ],
            },
            "minimum_n": 20,
            "replay_command": (
                "python validation/heldout/grand_science/agriculture/coverage_work_orders/"
                "oc133_agriculture_modern_science_coverage_work_orders.py --check"
            ),
            "replay_protocol": {
                "commands": [
                    "obtain a USDA NASS QuickStats API key through the official registration path before acquisition",
                    (
                        "python validation/heldout/grand_science/agriculture/coverage_work_orders/"
                        "oc133_agriculture_modern_science_coverage_work_orders.py --check"
                    ),
                ],
                "required_artifacts": [
                    "USDA QuickStats crop-yield source snapshot and lock",
                    "USDA NRCS Soil Data Access source snapshot and lock",
                    "target-hidden crop-yield task table",
                    "strict crop/soil/trait evidence candidate pack",
                ],
                "acceptance_predicates": common_acceptance_predicates(),
            },
            "current_evidence_status": {
                "status_code": "OPEN_FAIL_CLOSED_NO_EXECUTABLE_EVIDENCE",
                "coverage_closure_allowed": False,
                "executable_evidence_exists": False,
                "reason": "No locked QuickStats yield snapshot, NRCS soil snapshot, target-hidden task table, scorer, comparator outputs, or strict evidence pack is present.",
            },
            "remaining_blockers": [
                "USDA_QUICKSTATS_API_KEY_NOT_BOUND",
                "NRCS_SDA_QUERY_LOCK_NOT_BUILT",
                "TARGET_HIDDEN_CROP_SOIL_EVIDENCE_PACK_NOT_BUILT",
                "NO_INDEPENDENT_REPLAY_OF_SCORING",
            ],
            "no_send_locks": no_send(),
        },
        {
            "work_order_id": "MS-COV-WO-020",
            "coverage_gap_id": "MS-COV-GAP-AGRICULTURAL_FOOD_SCIENCES-FOOD_CHEMISTRY_SAFETY_AND_NUTRITION",
            "domain_class_id": "agricultural_food_sciences",
            "phenomenon_class_id": "food_chemistry_safety_and_nutrition",
            "phenomenon_label": "food chemistry safety and nutrition",
            "lane_status": "OPEN_FAIL_CLOSED_SCORER_READY_STRICT_EVIDENCE_PACK_NO_COVERAGE_CLOSURE",
            "coverage_closure_allowed": False,
            "support_allowed_for_broad_coverage": False,
            "official_sources": [
                official_source(
                    "USDA_FOODDATA_CENTRAL_API",
                    "USDA FoodData Central API",
                    "https://api.nal.usda.gov/fdc/v1/foods/list",
                    documentation_url="https://fdc.nal.usda.gov/api-guide",
                    runner_status="READONLY_REPLAY_AND_TARGET_HIDDEN_SCORER_IMPLEMENTED_WITH_DEMO_KEY_RATE_LIMIT",
                    local_snapshot_ref=FDC_SNAPSHOT_REL,
                    lock_ref=FDC_LOCK_REL,
                )
            ],
            "acquisition_requests": [
                {
                    "request_id": "OC133-AGRI-FDC-FOUNDATION-FOODS-LIST-0001",
                    "http_method": "GET",
                    "official_endpoint_url": fdc_foods_list_url(),
                    "expected_local_snapshot_ref": FDC_SNAPSHOT_REL,
                    "expected_lock_ref": FDC_LOCK_REL,
                    "hash_required": True,
                    "no_send_lock": True,
                    "implemented_replay_command": (
                        "python validation/heldout/grand_science/agriculture/coverage_work_orders/"
                        "oc133_agriculture_modern_science_coverage_work_orders.py --acquire-fdc --write-acquisition"
                    ),
                }
            ],
            "target_variable": {
                "name": "heldout_food_sodium_content",
                "unit": "mg per 100 g edible portion",
                "target_fields": ["foodNutrients[number=307].amount"],
                "official_target_source": "USDA_FOODDATA_CENTRAL_API",
                "minimum_target_rows": 20,
            },
            "target_hidden_split": {
                "source_separation_mode": "target_blind",
                "training_visible": "Foundation-food identifiers, descriptions, publication dates, and non-sodium nutrient fields from the locked FDC response",
                "target_hidden_until_scoring": "Sodium, Na nutrient number 307 is hidden until predictions and comparator outputs are materialized",
                "split_key": "fdcId",
                "target_values_used_for_selection": False,
            },
            "formula_model": {
                "formula_id": FDC_SODIUM_MODEL_ID,
                "rule": FDC_SODIUM_MODEL_RULE,
                "visible_inputs": [
                    "fdcId",
                    "description",
                    "dataType",
                    "publicationDate",
                    "ndbNumber",
                    "selected_nutrients[203,204,205,207,208,301]",
                    "pre-registered nutrient selector excluding number 307",
                ],
                "target_values_used_for_model_design": False,
            },
            "preregistered_comparator": {
                "name": "FoodData Central visible calcium mineral baseline",
                "comparator_id": FDC_SODIUM_COMPARATOR_ID,
                "prediction_rule": FDC_SODIUM_COMPARATOR_RULE,
                "pre_registered": True,
                "target_values_used_for_baseline_design": False,
            },
            "uncertainty_residual_metric": {
                "residual_metric": "absolute sodium residual in mg per 100 g; aggregate MAE across heldout FDC food rows",
                "uncertainty_method": "deterministic jackknife interval over row-level absolute sodium residuals after prediction materialization",
                "superiority_predicate": "model_MAE must beat comparator_MAE by a material predeclared margin and every negative control must be rejected; this work order does not permit coverage closure from the compact scorer alone",
            },
            "negative_control": {
                "control_id": "AGRI-FDC-FDCID-SODIUM-SHUFFLE-CONTROL",
                "description": "rotate the hidden fdcId-to-sodium target mapping by one row after visible predictions are materialized",
                "rejection_predicate": "rotated target map hash must differ from the locked target map hash and the rotated-control model MAE must be larger than the locked-target model MAE",
            },
            "falsifier": {
                "falsifier_id": "AGRI-FDC-FOOD-CHEMISTRY-FALSIFIER",
                "triggers": [
                    "FDC source snapshot hash is missing or changes during replay",
                    "nutrient number 307 appears in visible model or comparator inputs",
                    "visible ash nutrient 207 or calcium nutrient 301 is missing",
                    "N is below 20",
                    "target-hidden task table, hidden target lock, scoring pack, or replay hash is missing or changes during replay",
                    "sodium shuffle negative control is not rejected",
                ],
            },
            "minimum_n": 20,
            "replay_command": (
                "python validation/heldout/grand_science/agriculture/coverage_work_orders/"
                "oc133_agriculture_modern_science_coverage_work_orders.py --score-fdc --write-scoring"
            ),
            "replay_protocol": {
                "commands": [
                    (
                        "python validation/heldout/grand_science/agriculture/coverage_work_orders/"
                        "oc133_agriculture_modern_science_coverage_work_orders.py --acquire-fdc --write-acquisition"
                    ),
                    (
                        "python validation/heldout/grand_science/agriculture/coverage_work_orders/"
                        "oc133_agriculture_modern_science_coverage_work_orders.py --score-fdc --write-scoring"
                    ),
                    (
                        "python validation/heldout/grand_science/agriculture/coverage_work_orders/"
                        "oc133_agriculture_modern_science_coverage_work_orders.py --check"
                    ),
                ],
                "required_artifacts": [
                    FDC_SNAPSHOT_REL,
                    FDC_LOCK_REL,
                    FDC_TASK_TABLE_REL,
                    FDC_HIDDEN_TARGET_LOCK_REL,
                    FDC_SCORING_PACK_REL,
                    FDC_REPORT_REL,
                ],
                "acceptance_predicates": common_acceptance_predicates(
                    [
                        "READONLY_FDC_ACQUISITION_HASH_BOUND",
                        "TARGET_HIDDEN_FDC_SODIUM_SCORER_READY",
                        "STRICT_FDC_SCORING_PACK_HASH_BOUND",
                        "FDC_SODIUM_NEGATIVE_CONTROL_REJECTED",
                    ]
                ),
            },
            "current_evidence_status": {
                "status_code": "OPEN_FAIL_CLOSED_SCORER_READY_STRICT_EVIDENCE_PACK_NO_COVERAGE_CLOSURE",
                "coverage_closure_allowed": False,
                "executable_evidence_exists": True,
                "readonly_acquisition_lane_implemented": True,
                "target_hidden_scorer_present": True,
                "implemented_snapshot_ref": FDC_SNAPSHOT_REL,
                "implemented_lock_ref": FDC_LOCK_REL,
                "implemented_task_table_ref": FDC_TASK_TABLE_REL,
                "implemented_hidden_target_lock_ref": FDC_HIDDEN_TARGET_LOCK_REL,
                "implemented_scoring_pack_ref": FDC_SCORING_PACK_REL,
                "reason": "The compact FDC snapshot supplies the visible ash/calcium fields and hidden sodium target needed for an executable target-hidden sodium scorer, comparator residual table, negative-control result, replay hash, and strict fail-closed evidence pack. Coverage closure remains prohibited.",
            },
            "remaining_blockers": [
                "COVERAGE_CLOSURE_NOT_CLAIMED_FAIL_CLOSED",
                "BROAD_SUPERIORITY_CERTIFICATION_STILL_PROHIBITED",
            ],
            "no_send_locks": no_send(),
        },
        {
            "work_order_id": "MS-COV-WO-021",
            "coverage_gap_id": "MS-COV-GAP-AGRICULTURAL_FOOD_SCIENCES-ANIMAL_HEALTH_AND_PRODUCTION_SYSTEMS",
            "domain_class_id": "agricultural_food_sciences",
            "phenomenon_class_id": "animal_health_and_production_systems",
            "phenomenon_label": "animal health and production systems",
            "lane_status": "OPEN_FAIL_CLOSED_NO_EXECUTABLE_EVIDENCE",
            "coverage_closure_allowed": False,
            "support_allowed_for_broad_coverage": False,
            "official_sources": [
                official_source(
                    "WOAH_WAHIS_PUBLIC_INTERFACE",
                    "WOAH World Animal Health Information System",
                    "https://wahis.woah.org/#/home",
                    documentation_url="https://www.woah.org/en/animal-health-in-the-world/the-oie-wahis-project/",
                    runner_status="BLOCKED_PENDING_PUBLIC_EXPORT_OR_API_LOCK",
                ),
                official_source(
                    "FAOSTAT_QCL_CROPS_LIVESTOCK_PRODUCTS",
                    "FAOSTAT Crops and livestock products bulk download",
                    faostat_bulk_qcl_url(),
                    documentation_url="https://www.fao.org/faostat/en/#data/QCL",
                    runner_status="BLOCKED_PENDING_FAOSTAT_LIVESTOCK_SOURCE_LOCK_AND_TARGET_PACK",
                ),
            ],
            "acquisition_requests": [
                {
                    "request_id": "OC133-AGRI-ANIMAL-FAOSTAT-QCL-LIVESTOCK-0001",
                    "http_method": "GET",
                    "official_endpoint_url": faostat_bulk_qcl_url(),
                    "expected_local_snapshot_ref": (
                        "validation/heldout/grand_science/agriculture/coverage_work_orders/raw/"
                        "animal_health_production/faostat_qcl_livestock.zip"
                    ),
                    "hash_required": True,
                    "blocked_until": "FAOSTAT_QCL_LIVESTOCK_TARGET_SCHEMA_AND_PARSER_LOCKED",
                    "no_send_lock": True,
                },
                {
                    "request_id": "OC133-AGRI-ANIMAL-WOAH-WAHIS-HPAI-0001",
                    "http_method": "OFFICIAL_EXPORT_OR_REVIEWED_API",
                    "official_endpoint_url": "https://wahis.woah.org/#/home",
                    "expected_local_snapshot_ref": (
                        "validation/heldout/grand_science/agriculture/coverage_work_orders/raw/"
                        "animal_health_production/woah_wahis_hpai_public_export.json"
                    ),
                    "hash_required": True,
                    "blocked_until": "WOAH_PUBLIC_EXPORT_OR_API_ENDPOINT_DOCUMENTED_AND_LOCKED",
                    "no_send_lock": True,
                },
            ],
            "target_variable": {
                "name": "heldout_country_year_livestock_production_and_notifiable_disease_burden",
                "unit": "FAOSTAT livestock head/count or production quantity; WOAH outbreak/event count",
                "target_fields": ["FAOSTAT Value", "WOAH outbreak_count", "area", "item", "year"],
                "official_target_source": "FAOSTAT_QCL_CROPS_LIVESTOCK_PRODUCTS + WOAH_WAHIS_PUBLIC_INTERFACE",
                "minimum_target_rows": 20,
            },
            "target_hidden_split": {
                "source_separation_mode": "target_blind",
                "training_visible": "country/item/year rows earlier than the heldout years plus predeclared disease-history covariates",
                "target_hidden_until_scoring": "later country/year livestock production and WOAH disease-burden targets are sealed until model and comparator outputs are materialized",
                "split_key": "country x livestock_item_or_disease x year",
                "target_values_used_for_selection": False,
            },
            "formula_model": {
                "formula_id": "AGRI-ANIMAL-LAGGED-PRODUCTION-HEALTH-MODEL",
                "rule": (
                    "y_hat(country, item, year) = training-only lagged livestock level + rolling growth trend "
                    "+ predeclared disease-burden lag adjustment where WOAH source rows are locked"
                ),
                "visible_inputs": [
                    "pre-heldout FAOSTAT livestock rows",
                    "pre-heldout WOAH disease burden rows",
                    "country and species identifiers",
                    "pre-registered lag window",
                ],
                "target_values_used_for_model_design": False,
            },
            "preregistered_comparator": {
                "name": "FAOSTAT carry-forward and rolling-mean livestock baseline",
                "prediction_rule": "predict heldout livestock/health target with last observation carried forward and trailing five-year mean on the same official source snapshot",
                "pre_registered": True,
                "target_values_used_for_baseline_design": False,
            },
            "uncertainty_residual_metric": {
                "residual_metric": "absolute residual for count/production rows; aggregate scaled MAE by country/species/year",
                "uncertainty_method": "rolling-origin residual envelope by species and country before target unsealing",
                "superiority_predicate": "model_scaled_MAE + uncertainty_margin < comparator_scaled_MAE and disease-label controls are rejected",
            },
            "negative_control": {
                "control_id": "AGRI-ANIMAL-COUNTRY-YEAR-DISEASE-SHUFFLE",
                "description": "shuffle country/year disease-burden rows after source lock",
                "rejection_predicate": "shuffled disease covariates must change row hashes and fail to improve heldout livestock/health residuals",
            },
            "falsifier": {
                "falsifier_id": "AGRI-ANIMAL-FAOSTAT-WOAH-FALSIFIER",
                "triggers": [
                    "FAOSTAT or WOAH snapshot hash is missing or changes during replay",
                    "heldout livestock or disease values leak into formula selection",
                    "N is below 20",
                    "carry-forward or rolling-mean comparator ties or beats the model within uncertainty",
                    "country/year disease shuffle is not rejected",
                ],
            },
            "minimum_n": 20,
            "replay_command": (
                "python validation/heldout/grand_science/agriculture/coverage_work_orders/"
                "oc133_agriculture_modern_science_coverage_work_orders.py --check"
            ),
            "replay_protocol": {
                "commands": [
                    "document and lock an official WOAH public export or reviewed API endpoint before replay",
                    (
                        "python validation/heldout/grand_science/agriculture/coverage_work_orders/"
                        "oc133_agriculture_modern_science_coverage_work_orders.py --check"
                    ),
                ],
                "required_artifacts": [
                    "FAOSTAT QCL livestock source snapshot and lock",
                    "WOAH WAHIS source snapshot/export and lock",
                    "target-hidden animal production/health task table",
                    "strict animal-health/production evidence candidate pack",
                ],
                "acceptance_predicates": common_acceptance_predicates(),
            },
            "current_evidence_status": {
                "status_code": "OPEN_FAIL_CLOSED_NO_EXECUTABLE_EVIDENCE",
                "coverage_closure_allowed": False,
                "executable_evidence_exists": False,
                "reason": "No locked FAOSTAT livestock parser, WOAH public export/API lock, target-hidden task table, scorer, controls, or strict evidence pack is present.",
            },
            "remaining_blockers": [
                "WOAH_PUBLIC_EXPORT_OR_API_LOCK_NOT_PRESENT",
                "FAOSTAT_QCL_LIVESTOCK_PARSER_NOT_LOCKED",
                "TARGET_HIDDEN_ANIMAL_HEALTH_PRODUCTION_PACK_NOT_BUILT",
                "NO_INDEPENDENT_REPLAY_OF_SCORING",
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
        "domain_class_id": "agricultural_food_sciences",
        "work_order_ids": [row["work_order_id"] for row in rows],
        "work_order_total": len(rows),
        "fail_closed_or_acquisition_only_total": len(rows),
        "coverage_closure_allowed": False,
        "broad_modern_science_superiority_allowed": False,
        "readonly_acquisition_lane_implemented": True,
        "target_hidden_scorer_ready_work_order_ids": ["MS-COV-WO-020"],
        "implemented_acquisition_refs": [FDC_SNAPSHOT_REL, FDC_LOCK_REL, FDC_REPORT_REL],
        "implemented_scoring_refs": [FDC_TASK_TABLE_REL, FDC_HIDDEN_TARGET_LOCK_REL, FDC_SCORING_PACK_REL],
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
    expected_ids = {"MS-COV-WO-019", "MS-COV-WO-020", "MS-COV-WO-021"}
    actual_ids = {str(row.get("work_order_id")) for row in rows if isinstance(row, dict)}
    if actual_ids != expected_ids:
        failures.append("AGRICULTURE_WORK_ORDER_SET_MISMATCH")
    expected_phenomena = {
        "crop_yield_soil_and_trait_observables",
        "food_chemistry_safety_and_nutrition",
        "animal_health_and_production_systems",
    }
    actual_phenomena = {str(row.get("phenomenon_class_id")) for row in rows if isinstance(row, dict)}
    if actual_phenomena != expected_phenomena:
        failures.append("AGRICULTURE_PHENOMENON_SET_MISMATCH")
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
        if not str(row.get("lane_status", "")).startswith("OPEN_FAIL_CLOSED"):
            failures.append(f"LANE_NOT_FAIL_CLOSED::{row_id}")
        for field in REQUIRED_ROW_FIELDS:
            if not row.get(field):
                failures.append(f"REQUIRED_FIELD_MISSING::{row_id}::{field}")
        if int(row.get("minimum_n", 0) or 0) < 20:
            failures.append(f"MINIMUM_N_LT_20::{row_id}")
        if row.get("target_hidden_split", {}).get("target_values_used_for_selection") is not False:
            failures.append(f"TARGET_VALUES_USED_FOR_SELECTION::{row_id}")
        if row.get("target_hidden_split", {}).get("target_hidden_until_scoring") in {None, False, ""}:
            failures.append(f"TARGET_HIDDEN_SPLIT_MISSING::{row_id}")
        if row.get("formula_model", {}).get("target_values_used_for_model_design") is not False:
            failures.append(f"FORMULA_TARGET_LEAK_ALLOWED::{row_id}")
        comparator = row.get("preregistered_comparator", {})
        if comparator.get("pre_registered") is not True:
            failures.append(f"COMPARATOR_NOT_PREREGISTERED::{row_id}")
        if comparator.get("target_values_used_for_baseline_design") is not False:
            failures.append(f"COMPARATOR_TARGET_LEAK_ALLOWED::{row_id}")
        if not row.get("uncertainty_residual_metric", {}).get("residual_metric"):
            failures.append(f"RESIDUAL_METRIC_MISSING::{row_id}")
        if not row.get("negative_control", {}).get("rejection_predicate"):
            failures.append(f"NEGATIVE_CONTROL_PREDICATE_MISSING::{row_id}")
        if not row.get("falsifier", {}).get("triggers"):
            failures.append(f"FALSIFIER_TRIGGERS_MISSING::{row_id}")
        evidence = row.get("current_evidence_status", {})
        if evidence.get("coverage_closure_allowed") is not False:
            failures.append(f"EVIDENCE_CLOSURE_ALLOWED::{row_id}")
        if row_id == "MS-COV-WO-020":
            if evidence.get("executable_evidence_exists") is not True:
                failures.append(f"FDC_SCORER_READY_EVIDENCE_MISSING::{row_id}")
            if evidence.get("target_hidden_scorer_present") is not True:
                failures.append(f"FDC_TARGET_HIDDEN_SCORER_NOT_DECLARED::{row_id}")
        elif evidence.get("executable_evidence_exists") is not False:
            failures.append(f"EXECUTABLE_EVIDENCE_PRETENDED::{row_id}")
        if not str(evidence.get("status_code", "")).startswith("OPEN_FAIL_CLOSED"):
            failures.append(f"EVIDENCE_STATUS_NOT_FAIL_CLOSED::{row_id}")
        for source in row.get("official_sources", []):
            if not str(source.get("official_url", "")).startswith("https://"):
                failures.append(f"OFFICIAL_SOURCE_HTTPS_URL_MISSING::{row_id}::{source.get('source_id')}")
        acceptance = row.get("replay_protocol", {}).get("acceptance_predicates", [])
        if "NO_BROAD_SUPERIORITY_CERTIFICATION" not in acceptance:
            failures.append(f"NO_BROAD_SUPERIORITY_PREDICATE_MISSING::{row_id}")
        expected_hash = sha256_object({key: value for key, value in row.items() if key != "row_sha256"})
        if row.get("row_sha256") != expected_hash:
            failures.append(f"ROW_HASH_MISMATCH::{row_id}")
    return failures


def normalize_fdc_food(food: dict[str, Any]) -> dict[str, Any]:
    nutrients: dict[str, dict[str, Any]] = {}
    for nutrient in food.get("foodNutrients", []):
        if not isinstance(nutrient, dict):
            continue
        number = str(nutrient.get("number") or nutrient.get("nutrientNumber") or "")
        if number not in FDC_SELECTED_NUTRIENT_NUMBERS:
            continue
        amount = nutrient.get("amount", nutrient.get("value"))
        nutrients[number] = {
            "name": str(nutrient.get("name") or nutrient.get("nutrientName") or FDC_SELECTED_NUTRIENT_NUMBERS[number]),
            "amount": amount,
            "unitName": str(nutrient.get("unitName", "")),
            "derivationCode": str(nutrient.get("derivationCode", "")),
            "derivationDescription": str(nutrient.get("derivationDescription", "")),
        }
    row = {
        "fdcId": food.get("fdcId"),
        "description": str(food.get("description", "")),
        "dataType": str(food.get("dataType", "")),
        "publicationDate": str(food.get("publicationDate") or food.get("publishedDate") or ""),
        "ndbNumber": str(food.get("ndbNumber", "")),
        "selected_nutrients": dict(sorted(nutrients.items())),
    }
    row["row_sha256"] = sha256_object(row)
    return row


def build_fdc_snapshot(raw_payload: Any, *, official_endpoint_url: str) -> dict[str, Any]:
    if not isinstance(raw_payload, list):
        raise ValueError("FDC foods/list response must be a JSON list")
    rows = [normalize_fdc_food(row) for row in raw_payload if isinstance(row, dict)]
    rows = sorted(rows, key=lambda row: int(row.get("fdcId") or 0))
    payload = {
        "schema_id": ACQUISITION_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_on": GENERATED_ON,
        "source_id": "USDA_FOODDATA_CENTRAL_API",
        "source_title": "USDA FoodData Central API Foundation Foods list",
        "official_documentation_url": "https://fdc.nal.usda.gov/api-guide",
        "official_endpoint_url": official_endpoint_url,
        "api_key_policy": "DEMO_KEY is an official FoodData Central sample key with lower rate limits; replace with a private data.gov key for production replay.",
        "target_work_order_id": "MS-COV-WO-020",
        "target_variable_hidden": "foodNutrients[number=307].amount (Sodium, Na)",
        "coverage_closure_allowed": False,
        "minimum_n_required": 20,
        "row_count": len(rows),
        "selected_nutrient_numbers": dict(sorted(FDC_SELECTED_NUTRIENT_NUMBERS.items())),
        "raw_response_sha256": sha256_object(raw_payload),
        "normalized_rows_sha256": sha256_object(rows),
        "rows": rows,
    }
    payload["snapshot_sha256"] = sha256_object(payload)
    return payload


def build_fdc_lock(snapshot: dict[str, Any]) -> dict[str, Any]:
    lock = {
        "schema_id": LOCK_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_on": GENERATED_ON,
        "lock_id": "OC133-AGRI-FDC-FOUNDATION-FOODS-LIST-0001",
        "source_snapshot_ref": FDC_SNAPSHOT_REL,
        "source_id": snapshot.get("source_id"),
        "official_endpoint_url": snapshot.get("official_endpoint_url"),
        "snapshot_sha256": snapshot.get("snapshot_sha256"),
        "raw_response_sha256": snapshot.get("raw_response_sha256"),
        "normalized_rows_sha256": snapshot.get("normalized_rows_sha256"),
        "row_count": snapshot.get("row_count"),
        "minimum_n_required": snapshot.get("minimum_n_required"),
        "target_work_order_id": "MS-COV-WO-020",
        "target_hidden_until_scoring": True,
        "target_values_scored": False,
        "coverage_closure_allowed": False,
        "current_evidence_status": "OPEN_FAIL_CLOSED_READONLY_ACQUISITION_ONLY_NO_TARGET_HIDDEN_SCORING",
        "no_send_locks": no_send(),
    }
    lock["lock_sha256"] = sha256_object(lock)
    return lock


def finite_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def rounded(value: float) -> float:
    return round(float(value), 6)


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def median(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[midpoint]
    return (ordered[midpoint - 1] + ordered[midpoint]) / 2


def fdc_visible_field_paths() -> list[str]:
    fields = ["fdcId", "description", "dataType", "publicationDate", "ndbNumber"]
    for number in FDC_VISIBLE_NUTRIENT_NUMBERS:
        fields.extend(
            [
                f"selected_nutrients[{number}].name",
                f"selected_nutrients[{number}].amount",
                f"selected_nutrients[{number}].unitName",
                f"selected_nutrients[{number}].derivationCode",
                f"selected_nutrients[{number}].derivationDescription",
            ]
        )
    return fields


def fdc_scoring_field_failures(snapshot: Any) -> list[str]:
    failures: list[str] = []
    if not isinstance(snapshot, dict):
        return ["snapshot"]
    rows = snapshot.get("rows")
    if not isinstance(rows, list):
        return ["rows"]
    if len(rows) < int(snapshot.get("minimum_n_required", 20) or 20):
        failures.append(f"rows::N_BELOW_MINIMUM::{len(rows)}/{snapshot.get('minimum_n_required', 20)}")
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            failures.append(f"rows[{index}]")
            continue
        prefix = f"rows[fdcId={row.get('fdcId', index)}]"
        for field in ("fdcId", "description", "dataType", "publicationDate", "ndbNumber"):
            if field not in row or row.get(field) in {None, ""}:
                failures.append(f"{prefix}.{field}")
        nutrients = row.get("selected_nutrients")
        if not isinstance(nutrients, dict):
            failures.append(f"{prefix}.selected_nutrients")
            continue
        for number in [*FDC_VISIBLE_NUTRIENT_NUMBERS, "307"]:
            nutrient = nutrients.get(number)
            if not isinstance(nutrient, dict):
                failures.append(f"{prefix}.selected_nutrients[{number}]")
                continue
            if finite_float(nutrient.get("amount")) is None:
                failures.append(f"{prefix}.selected_nutrients[{number}].amount")
            for field in ("name", "unitName", "derivationCode", "derivationDescription"):
                if field not in nutrient:
                    failures.append(f"{prefix}.selected_nutrients[{number}].{field}")
        for number in FDC_REQUIRED_SCORING_NUTRIENTS:
            nutrient = nutrients.get(number)
            if isinstance(nutrient, dict) and finite_float(nutrient.get("amount")) is None:
                failures.append(f"{prefix}.selected_nutrients[{number}].amount")
    return sorted(set(failures))


def fdc_visible_row(row: dict[str, Any], index: int) -> dict[str, Any]:
    nutrients = row["selected_nutrients"]
    visible_nutrients = {
        number: {
            "name": str(nutrients[number].get("name", FDC_SELECTED_NUTRIENT_NUMBERS[number])),
            "amount": finite_float(nutrients[number].get("amount")),
            "unitName": str(nutrients[number].get("unitName", "")),
            "derivationCode": str(nutrients[number].get("derivationCode", "")),
            "derivationDescription": str(nutrients[number].get("derivationDescription", "")),
        }
        for number in FDC_VISIBLE_NUTRIENT_NUMBERS
    }
    visible = {
        "task_id": f"AGRI-FDC-SODIUM-{index:04d}",
        "fdcId": row.get("fdcId"),
        "description": row.get("description"),
        "dataType": row.get("dataType"),
        "publicationDate": row.get("publicationDate"),
        "ndbNumber": row.get("ndbNumber"),
        "visible_selected_nutrients": visible_nutrients,
        "source_row_sha256": row.get("row_sha256"),
    }
    visible["visible_row_sha256"] = sha256_object(visible)
    return visible


def fdc_model_prediction(visible_row: dict[str, Any]) -> float:
    ash = finite_float(visible_row["visible_selected_nutrients"]["207"]["amount"]) or 0.0
    return rounded(max(0.0, FDC_SODIUM_ASH_NACL_FACTOR_MG_PER_G * ash))


def fdc_comparator_prediction(visible_row: dict[str, Any]) -> float:
    calcium = finite_float(visible_row["visible_selected_nutrients"]["301"]["amount"]) or 0.0
    return rounded(max(0.0, calcium))


def build_fdc_task_table(snapshot: dict[str, Any], lock: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for index, source_row in enumerate(snapshot.get("rows", []), start=1):
        visible = fdc_visible_row(source_row, index)
        row = {
            **visible,
            "model_prediction_mg_per_100g": fdc_model_prediction(visible),
            "comparator_prediction_mg_per_100g": fdc_comparator_prediction(visible),
        }
        row["task_row_sha256"] = sha256_object(row)
        rows.append(row)
    table = {
        "schema_id": FDC_TASK_TABLE_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_on": GENERATED_ON,
        "target_work_order_id": "MS-COV-WO-020",
        "source_snapshot_ref": FDC_SNAPSHOT_REL,
        "source_snapshot_sha256": snapshot.get("snapshot_sha256"),
        "source_lock_ref": FDC_LOCK_REL,
        "source_lock_sha256": lock.get("lock_sha256"),
        "target_hidden_until_scoring": True,
        "target_values_present": False,
        "target_values_used_for_selection": False,
        "target_values_used_for_model_design": False,
        "predeclared_visible_fields": fdc_visible_field_paths(),
        "hidden_target_fields": [
            "selected_nutrients[307].amount",
            "selected_nutrients[307].unitName",
            "selected_nutrients[307].derivationCode",
            "selected_nutrients[307].derivationDescription",
        ],
        "formula_model": {
            "formula_id": FDC_SODIUM_MODEL_ID,
            "rule": FDC_SODIUM_MODEL_RULE,
            "target_values_used_for_model_design": False,
        },
        "comparator_baseline": {
            "comparator_id": FDC_SODIUM_COMPARATOR_ID,
            "name": "FoodData Central visible calcium mineral baseline",
            "prediction_rule": FDC_SODIUM_COMPARATOR_RULE,
            "pre_registered": True,
            "target_values_used_for_baseline_design": False,
        },
        "prediction_materialization": {
            "predictions_materialized_before_target_unseal": True,
            "materialization_rule": "task rows contain visible-only model and comparator predictions before hidden sodium targets are opened",
            "hidden_target_ref": FDC_HIDDEN_TARGET_LOCK_REL,
        },
        "row_count": len(rows),
        "rows_sha256": sha256_object(rows),
        "rows": rows,
        "coverage_closure_allowed": False,
        "no_send_locks": no_send(),
    }
    table["task_table_sha256"] = sha256_object(table)
    return table


def build_fdc_hidden_target_lock(snapshot: dict[str, Any], task_table: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for index, source_row in enumerate(snapshot.get("rows", []), start=1):
        sodium = source_row["selected_nutrients"]["307"]
        row = {
            "target_id": f"AGRI-FDC-SODIUM-TARGET-{index:04d}",
            "fdcId": source_row.get("fdcId"),
            "sodium_mg_per_100g": finite_float(sodium.get("amount")),
            "unitName": str(sodium.get("unitName", "")),
            "derivationCode": str(sodium.get("derivationCode", "")),
            "derivationDescription": str(sodium.get("derivationDescription", "")),
            "source_row_sha256": source_row.get("row_sha256"),
        }
        row["target_row_sha256"] = sha256_object(row)
        rows.append(row)
    target_map = [{"fdcId": row["fdcId"], "sodium_mg_per_100g": row["sodium_mg_per_100g"]} for row in rows]
    lock = {
        "schema_id": FDC_HIDDEN_TARGET_LOCK_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_on": GENERATED_ON,
        "lock_id": "OC133-AGRI-FDC-SODIUM-HIDDEN-TARGETS-0001",
        "target_work_order_id": "MS-COV-WO-020",
        "source_snapshot_ref": FDC_SNAPSHOT_REL,
        "source_snapshot_sha256": snapshot.get("snapshot_sha256"),
        "visible_task_table_ref": FDC_TASK_TABLE_REL,
        "visible_task_table_sha256": task_table.get("task_table_sha256"),
        "target_hidden_until_scoring": True,
        "target_values_used_for_selection": False,
        "target_values_used_for_model_design": False,
        "target_unsealed_for_scoring": True,
        "hidden_target_fields": [
            "selected_nutrients[307].amount",
            "selected_nutrients[307].unitName",
            "selected_nutrients[307].derivationCode",
            "selected_nutrients[307].derivationDescription",
        ],
        "row_count": len(rows),
        "target_map_sha256": sha256_object(target_map),
        "hidden_targets_sha256": sha256_object(rows),
        "rows": rows,
        "coverage_closure_allowed": False,
        "no_send_locks": no_send(),
    }
    lock["hidden_target_lock_sha256"] = sha256_object(lock)
    return lock


def fdc_residual_summary(values: list[float]) -> dict[str, float]:
    if not values:
        return {"mean_absolute_error": 0.0, "median_absolute_error": 0.0, "max_absolute_error": 0.0}
    return {
        "mean_absolute_error": rounded(mean(values)),
        "median_absolute_error": rounded(median(values)),
        "max_absolute_error": rounded(max(values)),
    }


def fdc_jackknife_interval(values: list[float]) -> dict[str, float]:
    if len(values) <= 1:
        value = rounded(mean(values))
        return {"lower_mean_absolute_error": value, "upper_mean_absolute_error": value}
    estimates = []
    for index in range(len(values)):
        estimates.append(mean([value for idx, value in enumerate(values) if idx != index]))
    return {
        "lower_mean_absolute_error": rounded(min(estimates)),
        "upper_mean_absolute_error": rounded(max(estimates)),
    }


def build_fdc_scoring_pack(
    snapshot: dict[str, Any],
    lock: dict[str, Any],
    task_table: dict[str, Any],
    hidden_target_lock: dict[str, Any],
) -> dict[str, Any]:
    targets_by_fdc_id = {target["fdcId"]: target for target in hidden_target_lock.get("rows", [])}
    row_results = []
    model_residuals: list[float] = []
    comparator_residuals: list[float] = []
    for task_row in task_table.get("rows", []):
        target = targets_by_fdc_id[task_row["fdcId"]]
        observed = finite_float(target.get("sodium_mg_per_100g")) or 0.0
        model_prediction = finite_float(task_row.get("model_prediction_mg_per_100g")) or 0.0
        comparator_prediction = finite_float(task_row.get("comparator_prediction_mg_per_100g")) or 0.0
        model_residual = abs(model_prediction - observed)
        comparator_residual = abs(comparator_prediction - observed)
        row = {
            "task_id": task_row["task_id"],
            "fdcId": task_row["fdcId"],
            "visible_row_sha256": task_row["visible_row_sha256"],
            "hidden_target_row_sha256": target["target_row_sha256"],
            "model_prediction_mg_per_100g": rounded(model_prediction),
            "comparator_prediction_mg_per_100g": rounded(comparator_prediction),
            "observed_sodium_mg_per_100g": rounded(observed),
            "model_absolute_residual_mg_per_100g": rounded(model_residual),
            "comparator_absolute_residual_mg_per_100g": rounded(comparator_residual),
        }
        row["row_result_sha256"] = sha256_object(row)
        row_results.append(row)
        model_residuals.append(model_residual)
        comparator_residuals.append(comparator_residual)

    sodium_targets = [target["sodium_mg_per_100g"] for target in hidden_target_lock.get("rows", [])]
    rotated_targets = sodium_targets[1:] + sodium_targets[:1]
    control_rows = []
    control_residuals: list[float] = []
    for task_row, rotated_target in zip(task_table.get("rows", []), rotated_targets):
        prediction = finite_float(task_row.get("model_prediction_mg_per_100g")) or 0.0
        observed = finite_float(rotated_target) or 0.0
        residual = abs(prediction - observed)
        control_rows.append(
            {
                "fdcId": task_row["fdcId"],
                "rotated_sodium_mg_per_100g": rounded(observed),
                "model_prediction_mg_per_100g": rounded(prediction),
                "control_absolute_residual_mg_per_100g": rounded(residual),
            }
        )
        control_residuals.append(residual)

    model_summary = fdc_residual_summary(model_residuals)
    comparator_summary = fdc_residual_summary(comparator_residuals)
    control_summary = fdc_residual_summary(control_residuals)
    model_mae = model_summary["mean_absolute_error"]
    comparator_mae = comparator_summary["mean_absolute_error"]
    control_mae = control_summary["mean_absolute_error"]
    target_map_sha = hidden_target_lock.get("target_map_sha256")
    control_target_map_sha = sha256_object(
        [{"fdcId": row["fdcId"], "sodium_mg_per_100g": row["rotated_sodium_mg_per_100g"]} for row in control_rows]
    )
    negative_control_rejected = control_target_map_sha != target_map_sha and control_mae > model_mae
    residual_scale = max(1.0, model_mae, comparator_mae)
    superiority_margin = rounded(comparator_mae - model_mae)
    material_margin_required = rounded(0.05 * residual_scale)
    material_margin_met = superiority_margin >= material_margin_required
    coverage_closure_failures = [
        "NO_BROAD_SUPERIORITY_CERTIFICATION",
        "COVERAGE_CLOSURE_ALLOWED_FALSE_BY_POLICY",
    ]
    if not material_margin_met:
        coverage_closure_failures.append("MATERIAL_SUPERIORITY_MARGIN_NOT_MET_BY_COMPACT_FDC_SCORER")

    replay_inputs = {
        "source_snapshot_sha256": snapshot.get("snapshot_sha256"),
        "source_lock_sha256": lock.get("lock_sha256"),
        "task_table_sha256": task_table.get("task_table_sha256"),
        "hidden_target_lock_sha256": hidden_target_lock.get("hidden_target_lock_sha256"),
        "row_results_sha256": sha256_object(row_results),
        "negative_control_target_map_sha256": control_target_map_sha,
        "model": FDC_SODIUM_MODEL_ID,
        "comparator": FDC_SODIUM_COMPARATOR_ID,
    }
    pack = {
        "schema_id": FDC_SCORING_PACK_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_on": GENERATED_ON,
        "capability_owner": CAPABILITY_OWNER,
        "target_work_order_id": "MS-COV-WO-020",
        "source_snapshot_ref": FDC_SNAPSHOT_REL,
        "source_lock_ref": FDC_LOCK_REL,
        "visible_task_table_ref": FDC_TASK_TABLE_REL,
        "hidden_target_lock_ref": FDC_HIDDEN_TARGET_LOCK_REL,
        "source_snapshot_sha256": snapshot.get("snapshot_sha256"),
        "source_lock_sha256": lock.get("lock_sha256"),
        "visible_task_table_sha256": task_table.get("task_table_sha256"),
        "hidden_target_lock_sha256": hidden_target_lock.get("hidden_target_lock_sha256"),
        "source_separation": {
            "mode": "target_blind",
            "target_hidden_until_scoring": True,
            "target_values_used_for_selection": False,
            "target_values_used_for_model_design": False,
            "predictions_materialized_before_target_unseal": True,
            "visible_fields": fdc_visible_field_paths(),
            "hidden_target_fields": task_table["hidden_target_fields"],
        },
        "formula_model": {
            "formula_id": FDC_SODIUM_MODEL_ID,
            "rule": FDC_SODIUM_MODEL_RULE,
            "target_values_used_for_model_design": False,
        },
        "comparator_baseline": task_table["comparator_baseline"],
        "uncertainty_residual_metric": {
            "residual_metric": "absolute sodium residual in mg per 100 g; aggregate MAE across heldout FDC food rows",
            "uncertainty_method": "deterministic jackknife interval over row-level absolute sodium residuals",
            "model_jackknife_interval": fdc_jackknife_interval(model_residuals),
            "comparator_jackknife_interval": fdc_jackknife_interval(comparator_residuals),
        },
        "residuals": {
            "model": model_summary,
            "comparator": comparator_summary,
            "superiority_margin_mg_per_100g": superiority_margin,
            "material_margin_required_mg_per_100g": material_margin_required,
            "material_margin_met": material_margin_met,
        },
        "negative_control": {
            "control_id": "AGRI-FDC-FDCID-SODIUM-SHUFFLE-CONTROL",
            "description": "rotate the hidden fdcId-to-sodium target mapping by one row after visible predictions are materialized",
            "locked_target_map_sha256": target_map_sha,
            "control_target_map_sha256": control_target_map_sha,
            "model_control_residual": control_summary,
            "rejection_predicate": "control target map hash differs from locked target map and control model MAE exceeds locked-target model MAE",
            "rejected": negative_control_rejected,
        },
        "falsifier": {
            "falsifier_id": "AGRI-FDC-FOOD-CHEMISTRY-FALSIFIER",
            "triggers": [
                "FDC source snapshot hash is missing or changes during replay",
                "nutrient number 307 appears in visible model or comparator inputs",
                "visible ash nutrient 207 or calcium nutrient 301 is missing",
                "N is below 20",
                "target-hidden task table, hidden target lock, scoring pack, or replay hash is missing or changes during replay",
                "sodium shuffle negative control is not rejected",
            ],
            "triggered": [] if negative_control_rejected else ["sodium shuffle negative control is not rejected"],
        },
        "row_count": len(row_results),
        "row_results_sha256": sha256_object(row_results),
        "row_results": row_results,
        "replay_hash_inputs": replay_inputs,
        "replay_sha256": sha256_object(replay_inputs),
        "strict_evidence_pack": {
            "scorer_ready": negative_control_rejected,
            "fail_closed": True,
            "coverage_closure_allowed": False,
            "support_allowed_for_broad_coverage": False,
            "coverage_closure_failures": coverage_closure_failures,
        },
        "coverage_closure_allowed": False,
        "support_allowed_for_broad_coverage": False,
        "no_send_locks": no_send(),
    }
    pack["scoring_pack_sha256"] = sha256_object(pack)
    return pack


def build_fdc_scoring_blocker(snapshot: Any, lock: Any | None = None) -> dict[str, Any]:
    missing_fields = fdc_scoring_field_failures(snapshot)
    validation_errors = validate_fdc_snapshot(snapshot)
    if isinstance(snapshot, dict) and isinstance(lock, dict):
        validation_errors.extend(validate_fdc_lock(snapshot, lock))
    blocker = {
        "schema_id": FDC_SCORING_BLOCKER_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_on": GENERATED_ON,
        "capability_owner": CAPABILITY_OWNER,
        "target_work_order_id": "MS-COV-WO-020",
        "source_snapshot_ref": FDC_SNAPSHOT_REL,
        "source_lock_ref": FDC_LOCK_REL,
        "blocked_status": "OPEN_FAIL_CLOSED_BLOCKED_MISSING_REQUIRED_FDC_SCORING_FIELDS",
        "coverage_closure_allowed": False,
        "target_hidden_scorer_present": False,
        "missing_fields": missing_fields,
        "validation_errors": sorted(set(validation_errors)),
        "required_visible_fields": fdc_visible_field_paths(),
        "required_hidden_target_fields": [
            "selected_nutrients[307].amount",
            "selected_nutrients[307].unitName",
            "selected_nutrients[307].derivationCode",
            "selected_nutrients[307].derivationDescription",
        ],
        "acquisition_next_action": (
            "Re-acquire an official USDA FDC Foundation Foods snapshot with fdcId, description, dataType, "
            "publicationDate, ndbNumber, visible nutrient numbers 203/204/205/207/208/301, and hidden sodium "
            "nutrient number 307 amount/unit/derivation fields for at least 20 rows; then rerun "
            "python validation/heldout/grand_science/agriculture/coverage_work_orders/"
            "oc133_agriculture_modern_science_coverage_work_orders.py --score-fdc --write-scoring."
        ),
        "no_send_locks": no_send(),
    }
    blocker["blocker_sha256"] = sha256_object(blocker)
    return blocker


def build_fdc_scoring_outputs(snapshot: dict[str, Any], lock: dict[str, Any]) -> dict[str, Any]:
    base_errors = validate_fdc_snapshot(snapshot)
    base_errors.extend(validate_fdc_lock(snapshot, lock))
    missing_fields = fdc_scoring_field_failures(snapshot)
    if base_errors or missing_fields:
        blocker = build_fdc_scoring_blocker(snapshot, lock)
        return {
            "status": "blocked",
            "errors": sorted(set([*base_errors, *missing_fields])),
            "blocker": blocker,
        }
    task_table = build_fdc_task_table(snapshot, lock)
    hidden_target_lock = build_fdc_hidden_target_lock(snapshot, task_table)
    scoring_pack = build_fdc_scoring_pack(snapshot, lock, task_table, hidden_target_lock)
    return {
        "status": "scorer_ready",
        "errors": [],
        "task_table": task_table,
        "hidden_target_lock": hidden_target_lock,
        "scoring_pack": scoring_pack,
    }


def build_fdc_report(snapshot: dict[str, Any], lock: dict[str, Any]) -> dict[str, Any]:
    errors = validate_fdc_snapshot(snapshot)
    errors.extend(validate_fdc_lock(snapshot, lock))
    scoring = build_fdc_scoring_outputs(snapshot, lock) if not errors else {"status": "blocked", "errors": errors}
    scoring_pack = scoring.get("scoring_pack") if scoring.get("status") == "scorer_ready" else None
    scorer_ready = isinstance(scoring_pack, dict) and scoring_pack.get("strict_evidence_pack", {}).get("scorer_ready") is True
    report = {
        "schema_id": REPORT_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_on": GENERATED_ON,
        "capability_owner": CAPABILITY_OWNER,
        "target_work_order_id": "MS-COV-WO-020",
        "source_snapshot_ref": FDC_SNAPSHOT_REL,
        "source_lock_ref": FDC_LOCK_REL,
        "row_count": snapshot.get("row_count"),
        "minimum_n_required": snapshot.get("minimum_n_required"),
        "readonly_acquisition_hash_bound": len(errors) == 0,
        "target_hidden_scorer_present": scorer_ready,
        "comparator_scores_present": scorer_ready,
        "negative_control_rejected": scoring_pack.get("negative_control", {}).get("rejected") is True
        if isinstance(scoring_pack, dict)
        else False,
        "strict_evidence_pack_present": scorer_ready,
        "target_hidden_task_table_ref": FDC_TASK_TABLE_REL if scorer_ready else None,
        "hidden_target_lock_ref": FDC_HIDDEN_TARGET_LOCK_REL if scorer_ready else None,
        "scoring_pack_ref": FDC_SCORING_PACK_REL if scorer_ready else None,
        "scoring_pack_sha256": scoring_pack.get("scoring_pack_sha256") if isinstance(scoring_pack, dict) else None,
        "replay_sha256": scoring_pack.get("replay_sha256") if isinstance(scoring_pack, dict) else None,
        "coverage_closure_allowed": False,
        "current_evidence_status": "OPEN_FAIL_CLOSED_SCORER_READY_STRICT_EVIDENCE_PACK_NO_COVERAGE_CLOSURE"
        if scorer_ready
        else "OPEN_FAIL_CLOSED_BLOCKED_MISSING_REQUIRED_FDC_SCORING_FIELDS",
        "errors": sorted(set([*errors, *scoring.get("errors", [])])),
        "blockers": [] if scorer_ready else scoring.get("errors", []),
        "coverage_closure_failures": scoring_pack.get("strict_evidence_pack", {}).get("coverage_closure_failures", [])
        if isinstance(scoring_pack, dict)
        else ["TARGET_HIDDEN_FDC_SODIUM_SCORER_NOT_READY"],
        "no_send_locks": no_send(),
    }
    report["report_sha256"] = sha256_object(report)
    return report


def validate_fdc_snapshot(snapshot: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(snapshot, dict):
        return ["FDC_SNAPSHOT_NOT_OBJECT"]
    if snapshot.get("schema_id") != ACQUISITION_SCHEMA_ID:
        errors.append("FDC_SNAPSHOT_SCHEMA_MISMATCH")
    if snapshot.get("coverage_closure_allowed") is not False:
        errors.append("FDC_SNAPSHOT_CLOSURE_ALLOWED")
    if int(snapshot.get("row_count", 0) or 0) < int(snapshot.get("minimum_n_required", 20) or 20):
        errors.append("FDC_SNAPSHOT_MINIMUM_N_NOT_MET")
    rows = snapshot.get("rows", [])
    if not isinstance(rows, list) or len(rows) != snapshot.get("row_count"):
        errors.append("FDC_SNAPSHOT_ROW_COUNT_MISMATCH")
        rows = []
    if snapshot.get("normalized_rows_sha256") != sha256_object(rows):
        errors.append("FDC_SNAPSHOT_NORMALIZED_ROWS_HASH_MISMATCH")
    stored_snapshot_hash = snapshot.get("snapshot_sha256")
    without_hash = {key: value for key, value in snapshot.items() if key != "snapshot_sha256"}
    if stored_snapshot_hash != sha256_object(without_hash):
        errors.append("FDC_SNAPSHOT_HASH_MISMATCH")
    for row in rows:
        if not isinstance(row, dict):
            errors.append("FDC_SNAPSHOT_ROW_NOT_OBJECT")
            continue
        expected = sha256_object({key: value for key, value in row.items() if key != "row_sha256"})
        if row.get("row_sha256") != expected:
            errors.append(f"FDC_SNAPSHOT_ROW_HASH_MISMATCH::{row.get('fdcId')}")
        nutrients = row.get("selected_nutrients", {})
        if "307" not in nutrients:
            errors.append(f"FDC_SNAPSHOT_SODIUM_TARGET_MISSING::{row.get('fdcId')}")
    return errors


def validate_fdc_lock(snapshot: dict[str, Any], lock: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(lock, dict):
        return ["FDC_LOCK_NOT_OBJECT"]
    if lock.get("schema_id") != LOCK_SCHEMA_ID:
        errors.append("FDC_LOCK_SCHEMA_MISMATCH")
    if lock.get("coverage_closure_allowed") is not False:
        errors.append("FDC_LOCK_CLOSURE_ALLOWED")
    for field in ("snapshot_sha256", "raw_response_sha256", "normalized_rows_sha256", "row_count", "minimum_n_required"):
        if lock.get(field) != snapshot.get(field):
            errors.append(f"FDC_LOCK_FIELD_MISMATCH::{field}")
    if lock.get("target_hidden_until_scoring") is not True:
        errors.append("FDC_LOCK_TARGET_NOT_HIDDEN")
    if lock.get("target_values_scored") is not False:
        errors.append("FDC_LOCK_PRETENDS_TARGET_VALUES_SCORED")
    stored_lock_hash = lock.get("lock_sha256")
    without_hash = {key: value for key, value in lock.items() if key != "lock_sha256"}
    if stored_lock_hash != sha256_object(without_hash):
        errors.append("FDC_LOCK_HASH_MISMATCH")
    return errors


def check_fdc_scoring_artifacts(root: Path, snapshot: dict[str, Any], lock: dict[str, Any]) -> list[str]:
    scoring = build_fdc_scoring_outputs(snapshot, lock)
    errors: list[str] = []
    if scoring.get("status") == "blocked":
        blocker_path = root / FDC_SCORING_BLOCKER_REL
        if not blocker_path.exists():
            return [f"missing::{FDC_SCORING_BLOCKER_REL}"]
        if read_json(blocker_path) != scoring.get("blocker"):
            errors.append(f"mismatch::{FDC_SCORING_BLOCKER_REL}")
        return errors
    expected_artifacts = [
        (FDC_TASK_TABLE_REL, scoring["task_table"]),
        (FDC_HIDDEN_TARGET_LOCK_REL, scoring["hidden_target_lock"]),
        (FDC_SCORING_PACK_REL, scoring["scoring_pack"]),
    ]
    for rel_path, expected in expected_artifacts:
        path = root / rel_path
        if not path.exists():
            errors.append(f"missing::{rel_path}")
            continue
        if read_json(path) != expected:
            errors.append(f"mismatch::{rel_path}")
    return errors


def check_acquisition_artifacts(root: Path) -> list[str]:
    snapshot_path = root / FDC_SNAPSHOT_REL
    lock_path = root / FDC_LOCK_REL
    report_path = root / FDC_REPORT_REL
    errors: list[str] = []
    if not (snapshot_path.exists() or lock_path.exists() or report_path.exists()):
        return errors
    if not snapshot_path.exists():
        errors.append(f"missing::{FDC_SNAPSHOT_REL}")
        return errors
    if not lock_path.exists():
        errors.append(f"missing::{FDC_LOCK_REL}")
        return errors
    if not report_path.exists():
        errors.append(f"missing::{FDC_REPORT_REL}")
        return errors
    snapshot = read_json(snapshot_path)
    lock = read_json(lock_path)
    report = read_json(report_path)
    errors.extend(validate_fdc_snapshot(snapshot))
    errors.extend(validate_fdc_lock(snapshot if isinstance(snapshot, dict) else {}, lock))
    expected_report = build_fdc_report(snapshot, lock) if isinstance(snapshot, dict) and isinstance(lock, dict) else {}
    if report != expected_report:
        errors.append(f"mismatch::{FDC_REPORT_REL}")
    if isinstance(report, dict) and report.get("coverage_closure_allowed") is not False:
        errors.append("FDC_REPORT_CLOSURE_ALLOWED")
    if isinstance(snapshot, dict) and isinstance(lock, dict):
        errors.extend(check_fdc_scoring_artifacts(root, snapshot, lock))
    return sorted(set(errors))


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
    failures.extend(check_acquisition_artifacts(root))
    return sorted(set(failures))


def fetch_json(url: str) -> Any:
    request = Request(url, headers={"User-Agent": "oc133-agriculture-coverage-replay/1.0"})
    with urlopen(request, timeout=30) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return json.loads(response.read().decode(charset))


def write_fdc_scoring_artifacts(root: Path, scoring: dict[str, Any]) -> None:
    if scoring.get("status") == "blocked":
        write_json(root / FDC_SCORING_BLOCKER_REL, scoring["blocker"])
        return
    write_json(root / FDC_TASK_TABLE_REL, scoring["task_table"])
    write_json(root / FDC_HIDDEN_TARGET_LOCK_REL, scoring["hidden_target_lock"])
    write_json(root / FDC_SCORING_PACK_REL, scoring["scoring_pack"])


def score_fdc(root: Path, *, write: bool) -> dict[str, Any]:
    snapshot = read_json(root / FDC_SNAPSHOT_REL)
    lock = read_json(root / FDC_LOCK_REL)
    scoring = build_fdc_scoring_outputs(snapshot, lock)
    report = build_fdc_report(snapshot, lock)
    if write:
        write_fdc_scoring_artifacts(root, scoring)
        write_json(root / FDC_REPORT_REL, report)
    return {
        "snapshot": snapshot,
        "lock": lock,
        "report": report,
        **scoring,
    }


def acquire_fdc(root: Path, *, write: bool, api_key: str) -> dict[str, Any]:
    url = fdc_foods_list_url(api_key=api_key)
    raw_payload = fetch_json(url)
    snapshot = build_fdc_snapshot(raw_payload, official_endpoint_url=url)
    lock = build_fdc_lock(snapshot)
    scoring = build_fdc_scoring_outputs(snapshot, lock)
    report = build_fdc_report(snapshot, lock)
    if write:
        write_json(root / FDC_SNAPSHOT_REL, snapshot)
        write_json(root / FDC_LOCK_REL, lock)
        write_fdc_scoring_artifacts(root, scoring)
        write_json(root / FDC_REPORT_REL, report)
    return {
        "snapshot": snapshot,
        "lock": lock,
        "report": report,
        **scoring,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build/check agriculture modern-science coverage work orders.")
    parser.add_argument("--root", default=str(repo_root()), help="repository root")
    parser.add_argument("--write", action="store_true", help="write the deterministic work-order artifact")
    parser.add_argument("--check", action="store_true", help="check stored artifact synchronization")
    parser.add_argument("--acquire-fdc", action="store_true", help="run the small read-only USDA FDC acquisition replay")
    parser.add_argument("--write-acquisition", action="store_true", help="write FDC acquisition snapshot, lock, and report")
    parser.add_argument("--score-fdc", action="store_true", help="score the stored FDC compact snapshot with target-hidden sodium")
    parser.add_argument("--write-scoring", action="store_true", help="write FDC scoring task table, target lock, pack, and report")
    parser.add_argument("--fdc-api-key", default="DEMO_KEY", help="FoodData Central API key; defaults to official DEMO_KEY")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    if args.acquire_fdc:
        result = acquire_fdc(root, write=args.write_acquisition, api_key=args.fdc_api_key)
        report = result["report"]
        print(
            json.dumps(
                {
                    "status": "ok" if not report["errors"] else "failed",
                    "current_evidence_status": report["current_evidence_status"],
                    "coverage_closure_allowed": report["coverage_closure_allowed"],
                    "row_count": report["row_count"],
                    "snapshot_ref": FDC_SNAPSHOT_REL if args.write_acquisition else None,
                    "lock_ref": FDC_LOCK_REL if args.write_acquisition else None,
                    "scoring_pack_ref": FDC_SCORING_PACK_REL
                    if args.write_acquisition and report["target_hidden_scorer_present"]
                    else None,
                    "errors": report["errors"],
                },
                indent=2,
            )
        )
        return 0 if not report["errors"] else 1
    if args.score_fdc:
        result = score_fdc(root, write=args.write_scoring)
        report = result["report"]
        print(
            json.dumps(
                {
                    "status": "ok" if report["target_hidden_scorer_present"] and not report["errors"] else "blocked",
                    "current_evidence_status": report["current_evidence_status"],
                    "coverage_closure_allowed": report["coverage_closure_allowed"],
                    "row_count": report["row_count"],
                    "target_hidden_scorer_present": report["target_hidden_scorer_present"],
                    "negative_control_rejected": report["negative_control_rejected"],
                    "scoring_pack_ref": FDC_SCORING_PACK_REL if args.write_scoring else None,
                    "blockers": report["blockers"],
                    "errors": report["errors"],
                },
                indent=2,
            )
        )
        return 0 if report["target_hidden_scorer_present"] and not report["errors"] else 1
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
    print(
        json.dumps(
            {
                "status": "ok" if not failures else "failed",
                "output_ref": OUTPUT_REL,
                "coverage_closure_allowed": False,
                "failures": failures,
            },
            indent=2,
        )
    )
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
