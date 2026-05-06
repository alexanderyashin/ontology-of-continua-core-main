from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen


SCRIPT_REL = (
    "validation/heldout/grand_science/wdi/coverage_work_orders/"
    "oc133_wdi_indicator_materializer.py"
)
HOLDOUT_YEARS = tuple(range(2010, 2020))
HISTORY_YEARS = 5

LANE_CONFIGS: dict[str, dict[str, Any]] = {
    "medical_clinical_life_expectancy": {
        "domain_class_id": "medical_health_sciences",
        "phenomenon_class_id": "clinical_outcomes_and_biomarkers",
        "indicator": "SP.DYN.LE00.IN",
        "indicator_label": "Life expectancy at birth, total (years)",
        "field": "life_expectancy_years",
        "unit": "years",
        "source_id": "world_bank_wdi_life_expectancy_v1",
        "model_id": "MED-WDI-LIFE-EXPECTANCY-MEDIAN-DELTA-v1",
        "comparator_id": "MED-WDI-LIFE-EXPECTANCY-LAST_OBSERVATION_BASELINE-v1",
        "negative_control_id": "MED-WDI-LIFE-EXPECTANCY-FIVE_YEAR_MEAN_CONTROL-v1",
        "model_rule": "Use the median recent annual change over a five-year visible history and extrapolate one year.",
        "comparator_rule": "Predict the held-out clinical/population outcome as the last visible pre-target value.",
        "material_margin": 0.001,
        "minimum_rows": 500,
    },
    "medical_epidemiology_child_mortality": {
        "domain_class_id": "medical_health_sciences",
        "phenomenon_class_id": "epidemiological_transmission_and_risk",
        "indicator": "SH.DYN.MORT",
        "indicator_label": "Mortality rate, under-5 (per 1,000 live births)",
        "field": "under_five_mortality_per_1000_live_births",
        "unit": "deaths per 1,000 live births",
        "source_id": "world_bank_wdi_under_five_mortality_v1",
        "model_id": "MED-WDI-UNDER-FIVE-MORTALITY-MEDIAN-DELTA-v1",
        "comparator_id": "MED-WDI-UNDER-FIVE-MORTALITY-LAST_OBSERVATION_BASELINE-v1",
        "negative_control_id": "MED-WDI-UNDER-FIVE-MORTALITY-FIVE_YEAR_MEAN_CONTROL-v1",
        "model_rule": "Use the median recent annual mortality-risk change over a five-year visible history and extrapolate one year.",
        "comparator_rule": "Predict the held-out epidemiological risk observable as the last visible pre-target value.",
        "material_margin": 0.001,
        "minimum_rows": 500,
    },
    "biology_ecology_forest_area": {
        "domain_class_id": "biological_life_sciences",
        "phenomenon_class_id": "ecology_population_and_biodiversity_observables",
        "indicator": "AG.LND.FRST.ZS",
        "indicator_label": "Forest area (% of land area)",
        "field": "forest_area_percent_land_area",
        "unit": "percent of land area",
        "source_id": "world_bank_wdi_forest_area_v1",
        "model_id": "BIO-WDI-FOREST-AREA-MEDIAN-DELTA-v1",
        "comparator_id": "BIO-WDI-FOREST-AREA-LAST_OBSERVATION_BASELINE-v1",
        "negative_control_id": "BIO-WDI-FOREST-AREA-FIVE_YEAR_MEAN_CONTROL-v1",
        "model_rule": "Use the median recent annual ecological-area change over visible history and extrapolate one year.",
        "comparator_rule": "Predict the held-out ecological observable as the last visible pre-target value.",
        "material_margin": 0.001,
        "minimum_rows": 500,
    },
    "engineering_electric_power_consumption": {
        "domain_class_id": "engineering_materials_sciences",
        "phenomenon_class_id": "energy_transport_and_manufacturing_processes",
        "indicator": "EG.USE.ELEC.KH.PC",
        "indicator_label": "Electric power consumption (kWh per capita)",
        "field": "electric_power_consumption_kwh_per_capita",
        "unit": "kWh per capita",
        "source_id": "world_bank_wdi_electric_power_consumption_v1",
        "model_id": "ENG-WDI-ELECTRIC-POWER-MEDIAN-DELTA-v1",
        "comparator_id": "ENG-WDI-ELECTRIC-POWER-LAST_OBSERVATION_BASELINE-v1",
        "negative_control_id": "ENG-WDI-ELECTRIC-POWER-FIVE_YEAR_MEAN_CONTROL-v1",
        "model_rule": "Use the median recent annual energy-consumption change over visible history and extrapolate one year.",
        "comparator_rule": "Predict the held-out energy/transport observable as the last visible pre-target value.",
        "material_margin": 0.001,
        "minimum_rows": 500,
    },
    "agriculture_cereal_yield": {
        "domain_class_id": "agricultural_food_sciences",
        "phenomenon_class_id": "crop_yield_soil_and_trait_observables",
        "indicator": "AG.YLD.CREL.KG",
        "indicator_label": "Cereal yield (kg per hectare)",
        "field": "cereal_yield_kg_per_hectare",
        "unit": "kg per hectare",
        "source_id": "world_bank_wdi_cereal_yield_v1",
        "model_id": "AGR-WDI-CEREAL-YIELD-MEDIAN-DELTA-v1",
        "comparator_id": "AGR-WDI-CEREAL-YIELD-LAST_OBSERVATION_BASELINE-v1",
        "negative_control_id": "AGR-WDI-CEREAL-YIELD-FIVE_YEAR_MEAN_CONTROL-v1",
        "model_rule": "Use the median recent annual crop-yield change over visible history and extrapolate one year.",
        "comparator_rule": "Predict the held-out crop-yield observable as the last visible pre-target value.",
        "material_margin": 0.05,
        "minimum_rows": 500,
    },
    "complex_systems_mobile_adoption": {
        "domain_class_id": "complex_systems_operations_science",
        "phenomenon_class_id": "multi_agent_system_dynamics",
        "indicator": "IT.CEL.SETS.P2",
        "indicator_label": "Mobile cellular subscriptions (per 100 people)",
        "field": "mobile_cellular_subscriptions_per_100",
        "unit": "subscriptions per 100 people",
        "source_id": "world_bank_wdi_mobile_cellular_subscriptions_v1",
        "model_id": "OPS-WDI-MOBILE-ADOPTION-MEDIAN-DELTA-v1",
        "comparator_id": "OPS-WDI-MOBILE-ADOPTION-LAST_OBSERVATION_BASELINE-v1",
        "negative_control_id": "OPS-WDI-MOBILE-ADOPTION-FIVE_YEAR_MEAN_CONTROL-v1",
        "model_rule": "Use the median recent annual adoption-flow change over visible history and extrapolate one year.",
        "comparator_rule": "Predict the held-out multi-agent adoption observable as the last visible pre-target value.",
        "material_margin": 0.005,
        "minimum_rows": 500,
    },
    "earth_hydrology_freshwater_resources": {
        "domain_class_id": "earth_space_environmental_sciences",
        "phenomenon_class_id": "geochemistry_and_hydrology_observables",
        "indicator": "ER.H2O.INTR.PC",
        "indicator_label": "Renewable internal freshwater resources per capita (cubic meters)",
        "field": "renewable_internal_freshwater_resources_cubic_meters_per_capita",
        "unit": "cubic meters per capita",
        "source_id": "world_bank_wdi_freshwater_resources_v1",
        "model_id": "EARTH-WDI-FRESHWATER-RESOURCES-MEDIAN-DELTA-v1",
        "comparator_id": "EARTH-WDI-FRESHWATER-RESOURCES-LAST_OBSERVATION_BASELINE-v1",
        "negative_control_id": "EARTH-WDI-FRESHWATER-RESOURCES-FIVE_YEAR_MEAN_CONTROL-v1",
        "model_rule": "Use the median recent annual hydrology-resource change over visible history and extrapolate one year.",
        "comparator_rule": "Predict the held-out hydrology observable as the last visible pre-target value.",
        "material_margin": 0.001,
        "minimum_rows": 500,
    },
    "agriculture_livestock_production": {
        "domain_class_id": "agricultural_food_sciences",
        "phenomenon_class_id": "animal_health_and_production_systems",
        "indicator": "AG.PRD.LVSK.XD",
        "indicator_label": "Livestock production index (2014-2016 = 100)",
        "field": "livestock_production_index",
        "unit": "index, 2014-2016 = 100",
        "source_id": "world_bank_wdi_livestock_production_index_v1",
        "model_id": "AGR-WDI-LIVESTOCK-MEDIAN-DELTA-v1",
        "comparator_id": "AGR-WDI-LIVESTOCK-LAST_OBSERVATION_BASELINE-v1",
        "negative_control_id": "AGR-WDI-LIVESTOCK-FIVE_YEAR_MEAN_CONTROL-v1",
        "model_rule": "Use the median recent annual livestock-production change over visible history and extrapolate one year.",
        "comparator_rule": "Predict the held-out animal-production observable as the last visible pre-target value.",
        "prediction_method": "median_delta",
        "material_margin": 0.0001,
        "minimum_rows": 500,
    },
    "agriculture_food_nutrition_undernourishment": {
        "domain_class_id": "agricultural_food_sciences",
        "phenomenon_class_id": "food_chemistry_safety_and_nutrition",
        "indicator": "SN.ITK.DEFC.ZS",
        "indicator_label": "Prevalence of undernourishment (% of population)",
        "field": "prevalence_of_undernourishment_percent",
        "unit": "percent of population",
        "source_id": "world_bank_wdi_prevalence_of_undernourishment_v1",
        "model_id": "AGR-WDI-UNDERNOURISHMENT-VISIBLE-CV-MOMENTUM-v1",
        "comparator_id": "AGR-WDI-UNDERNOURISHMENT-LAST_OBSERVATION_BASELINE-v1",
        "negative_control_id": "AGR-WDI-UNDERNOURISHMENT-FIVE_YEAR_MEAN_CONTROL-v1",
        "model_rule": "Use only the five visible annual observations to choose the best one-step predictor by internal visible-history cross-validation, then extrapolate one year.",
        "comparator_rule": "Predict the held-out nutrition observable as the last visible pre-target value.",
        "prediction_method": "visible_history_cv",
        "material_margin": 0.005,
        "minimum_rows": 500,
    },
}


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


def fetch_json(url: str, timeout: int = 90) -> Any:
    last_error: Exception | None = None
    for attempt in range(1, 4):
        try:
            request = Request(url, headers={"User-Agent": "Logion-OC133-Research-Cache/1.0"})
            with urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as error:  # World Bank occasionally drops chunked TLS reads.
            last_error = error
            if attempt < 3:
                time.sleep(float(attempt))
    assert last_error is not None
    raise last_error


def lane_root_rel(lane_id: str) -> str:
    return f"validation/heldout/grand_science/wdi/{lane_id}"


def refs(lane_id: str) -> dict[str, str]:
    prefix = lane_id.upper().replace("-", "_")
    root_rel = lane_root_rel(lane_id)
    return {
        "snapshot": f"{root_rel}/OC133_WDI_{prefix}_SOURCE.json",
        "lock": f"{root_rel}/OC133_WDI_{prefix}_SOURCE.lock.json",
        "task_table": f"{root_rel}/OC133_WDI_{prefix}_TARGET_HIDDEN_TASK_TABLE.json",
        "target_lock": f"{root_rel}/OC133-WDI-{prefix}-HIDDEN-TARGETS-0001.lock.json",
        "scoring_pack": f"{root_rel}/OC133_WDI_{prefix}_TARGET_HIDDEN_REPLAY_SCORER_EVIDENCE_PACK.json",
        "replay_report": f"{root_rel}/OC133_WDI_{prefix}_REPLAY_REPORT.json",
    }


def api_url(config: dict[str, Any]) -> str:
    return (
        "https://api.worldbank.org/v2/country/all/indicator/"
        f"{config['indicator']}?format=json&per_page=20000&date=2000:2019"
    )


def acquire(root: Path, lane_id: str, *, write: bool) -> dict[str, Any]:
    config = LANE_CONFIGS[lane_id]
    lane_refs = refs(lane_id)
    raw = fetch_json(api_url(config))
    if not isinstance(raw, list) or len(raw) < 2 or not isinstance(raw[1], list):
        raise RuntimeError("World Bank WDI API returned an unexpected payload shape")
    field = str(config["field"])
    source_rows = []
    for item in raw[1]:
        if not isinstance(item, dict):
            continue
        country_code = str(item.get("countryiso3code") or "")
        value = item.get("value")
        if len(country_code) != 3 or value is None:
            continue
        try:
            year = int(item.get("date"))
            numeric_value = float(value)
        except (TypeError, ValueError):
            continue
        if numeric_value <= 0:
            continue
        row = {
            "countryiso3code": country_code,
            "country_name": str((item.get("country") or {}).get("value") or ""),
            "indicator": config["indicator"],
            "indicator_label": config["indicator_label"],
            "year": year,
            field: numeric_value,
            "row_sha256": "",
        }
        row["row_sha256"] = sha256_object({key: value for key, value in row.items() if key != "row_sha256"})
        source_rows.append(row)
    source_rows.sort(key=lambda row: (row["countryiso3code"], row["year"]))
    snapshot = {
        "schema_id": "OC133_WDI_INDICATOR_SOURCE_SNAPSHOT_v1",
        "lane_id": lane_id,
        "domain_class_id": config["domain_class_id"],
        "phenomenon_class_id": config["phenomenon_class_id"],
        "source_id": config["source_id"],
        "source_name": "World Bank World Development Indicators API",
        "source_authority": "World Bank",
        "official_documentation_url": "https://datahelpdesk.worldbank.org/knowledgebase/topics/125589-developer-information",
        "official_endpoint_url": api_url(config),
        "indicator": config["indicator"],
        "indicator_label": config["indicator_label"],
        "unit": config["unit"],
        "year_range": "2000:2019",
        "row_count": len(source_rows),
        "minimum_rows_required": config["minimum_rows"],
        "target_values_scored": False,
        "target_hidden_until_scoring": True,
        "coverage_closure_allowed": False,
        "rows": source_rows,
        "rows_sha256": sha256_object(source_rows),
    }
    lock = {
        "schema_id": "OC133_WDI_INDICATOR_SOURCE_LOCK_v1",
        "lane_id": lane_id,
        "source_id": config["source_id"],
        "source_snapshot_ref": lane_refs["snapshot"],
        "source_snapshot_sha256": sha256_object(snapshot),
        "rows_sha256": snapshot["rows_sha256"],
        "row_count": len(source_rows),
        "visible_fields": ["countryiso3code", "country_name", "indicator", "indicator_label", "year"],
        "target_fields_hidden": [field],
        "target_values_scored": False,
        "target_hidden_until_scoring": True,
        "coverage_closure_allowed": False,
    }
    if write:
        write_json(root / lane_refs["snapshot"], snapshot)
        write_json(root / lane_refs["lock"], lock)
    return {"snapshot": snapshot, "lock": lock}


def rows_by_country(snapshot: dict[str, Any], field: str) -> dict[str, dict[int, float]]:
    grouped: dict[str, dict[int, float]] = {}
    for row in snapshot.get("rows", []):
        if not isinstance(row, dict):
            continue
        try:
            year = int(row.get("year"))
            value = float(row.get(field))
        except (TypeError, ValueError):
            continue
        country = str(row.get("countryiso3code") or "")
        if country and value > 0:
            grouped.setdefault(country, {})[year] = value
    return grouped


def build_task_table(lane_id: str, snapshot: dict[str, Any], lock: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    config = LANE_CONFIGS[lane_id]
    lane_refs = refs(lane_id)
    field = str(config["field"])
    by_country = rows_by_country(snapshot, field)
    source_hash_by_key = {
        (str(row.get("countryiso3code")), int(row.get("year"))): row.get("row_sha256")
        for row in snapshot.get("rows", [])
        if isinstance(row, dict) and row.get("year") is not None
    }
    visible_rows = []
    hidden_rows = []
    for country, yearly in sorted(by_country.items()):
        for target_year in HOLDOUT_YEARS:
            history = [
                {"year": year, field: yearly[year]}
                for year in range(target_year - HISTORY_YEARS, target_year)
                if yearly.get(year) is not None
            ]
            target = yearly.get(target_year)
            if len(history) != HISTORY_YEARS or target is None:
                continue
            task_id = f"WDI-{lane_id.upper()}-HOLDOUT-{country}-{target_year}"
            visible_rows.append(
                {
                    "task_id": task_id,
                    "countryiso3code": country,
                    "indicator": config["indicator"],
                    "target_year": target_year,
                    "history_window_years": HISTORY_YEARS,
                    "history_rows": history,
                    "source_row_sha256": source_hash_by_key.get((country, target_year)),
                }
            )
            hidden_rows.append(
                {
                    "task_id": task_id,
                    f"target_{field}": target,
                    "source_row_sha256": source_hash_by_key.get((country, target_year)),
                }
            )
    task_table = {
        "schema_id": "OC133_WDI_INDICATOR_TARGET_HIDDEN_TASK_TABLE_v1",
        "lane_id": lane_id,
        "source_snapshot_ref": lane_refs["snapshot"],
        "source_lock_ref": lane_refs["lock"],
        "row_count": len(visible_rows),
        "target_hidden_until_scoring": True,
        "coverage_closure_allowed": False,
        "model": {"model_id": config["model_id"], "rule": config["model_rule"]},
        "comparator": {"comparator_id": config["comparator_id"], "rule": config["comparator_rule"]},
        "visible_rows": visible_rows,
    }
    target_lock = {
        "schema_id": "OC133_WDI_INDICATOR_HIDDEN_TARGET_LOCK_v1",
        "lane_id": lane_id,
        "source_snapshot_ref": lane_refs["snapshot"],
        "source_lock_ref": lane_refs["lock"],
        "visible_task_table_ref": lane_refs["task_table"],
        "hidden_target_count": len(hidden_rows),
        "hidden_targets_sha256": sha256_object(hidden_rows),
        "target_hidden_until_scoring": True,
        "coverage_closure_allowed": False,
        "hidden_rows": hidden_rows,
    }
    return task_table, target_lock


def median_delta_predict(history_rows: list[dict[str, Any]], field: str) -> float:
    values = [float(row[field]) for row in history_rows]
    deltas = sorted(values[index] - values[index - 1] for index in range(1, len(values)))
    if len(deltas) % 2 == 0:
        delta = (deltas[len(deltas) // 2 - 1] + deltas[len(deltas) // 2]) / 2.0
    else:
        delta = deltas[len(deltas) // 2]
    return max(values[-1] + delta, 1e-12)


def _median(values: list[float]) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2.0


def _linear_predict(values: list[float]) -> float:
    n = len(values)
    xs = list(range(n))
    mean_x = sum(xs) / n
    mean_y = sum(values) / n
    denominator = sum((x - mean_x) ** 2 for x in xs)
    slope = (
        sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, values)) / denominator
        if denominator
        else 0.0
    )
    intercept = mean_y - slope * mean_x
    return max(intercept + slope * n, 1e-12)


def predict_values(values: list[float], method: str) -> float:
    if method == "last_observation":
        return max(values[-1], 1e-12)
    if method == "last_delta":
        return max(values[-1] + (values[-1] - values[-2]), 1e-12)
    if method == "damped_last_delta":
        return max(values[-1] + 0.5 * (values[-1] - values[-2]), 1e-12)
    if method == "mean_delta":
        delta = sum(values[index] - values[index - 1] for index in range(1, len(values))) / (len(values) - 1)
        return max(values[-1] + delta, 1e-12)
    if method == "linear":
        return _linear_predict(values)
    deltas = [values[index] - values[index - 1] for index in range(1, len(values))]
    return max(values[-1] + _median(deltas), 1e-12)


def visible_history_cv_predict(history_rows: list[dict[str, Any]], field: str) -> tuple[float, str, dict[str, float]]:
    values = [float(row[field]) for row in history_rows]
    candidate_methods = ("median_delta", "last_delta", "mean_delta", "damped_last_delta", "linear")
    method_errors: dict[str, float] = {}
    for method in candidate_methods:
        errors = []
        for index in range(3, len(values)):
            visible_prefix = values[:index]
            target = values[index]
            prediction = predict_values(visible_prefix, method)
            denominator = abs(target) if abs(target) > 1e-12 else 1.0
            errors.append(abs(prediction - target) / denominator)
        method_errors[method] = sum(errors) / len(errors) if errors else float("inf")
    selected = min(candidate_methods, key=lambda item: (method_errors[item], item))
    return predict_values(values, selected), selected, method_errors


def configured_model_predict(
    history_rows: list[dict[str, Any]],
    field: str,
    method: str,
) -> tuple[float, dict[str, Any]]:
    values = [float(row[field]) for row in history_rows]
    if method == "visible_history_cv":
        prediction, selected_method, method_errors = visible_history_cv_predict(history_rows, field)
        return prediction, {
            "prediction_method": method,
            "selected_visible_history_method": selected_method,
            "visible_history_cv_errors": {key: round(value, 12) for key, value in method_errors.items()},
        }
    return predict_values(values, method), {"prediction_method": method}


def score(root: Path, lane_id: str, *, write: bool) -> dict[str, Any]:
    config = LANE_CONFIGS[lane_id]
    lane_refs = refs(lane_id)
    field = str(config["field"])
    if not (root / lane_refs["snapshot"]).exists() or not (root / lane_refs["lock"]).exists():
        acquire(root, lane_id, write=True)
    snapshot = read_json(root / lane_refs["snapshot"])
    lock = read_json(root / lane_refs["lock"])
    task_table, target_lock = build_task_table(lane_id, snapshot, lock)
    hidden_by_id = {row["task_id"]: row for row in target_lock["hidden_rows"]}
    scored = []
    model_errors = []
    comparator_errors = []
    negative_control_errors = []
    for row in task_table["visible_rows"]:
        history = row["history_rows"]
        target = float(hidden_by_id[row["task_id"]][f"target_{field}"])
        prediction_method = str(config.get("prediction_method") or "median_delta")
        model_prediction, prediction_trace = configured_model_predict(history, field, prediction_method)
        comparator_prediction = float(history[-1][field])
        negative_control_prediction = sum(float(item[field]) for item in history) / len(history)
        denominator = abs(target) if abs(target) > 1e-12 else 1.0
        model_error = abs(model_prediction - target) / denominator
        comparator_error = abs(comparator_prediction - target) / denominator
        negative_control_error = abs(negative_control_prediction - target) / denominator
        model_errors.append(model_error)
        comparator_errors.append(comparator_error)
        negative_control_errors.append(negative_control_error)
        scored.append(
            {
                "task_id": row["task_id"],
                "countryiso3code": row["countryiso3code"],
                "target_year": row["target_year"],
                "model_prediction": round(model_prediction, 12),
                "comparator_prediction": round(comparator_prediction, 12),
                "negative_control_prediction": round(negative_control_prediction, 12),
                "prediction_trace": prediction_trace,
                "target_sha256": sha256_object(hidden_by_id[row["task_id"]]),
                "model_relative_error": round(model_error, 12),
                "comparator_relative_error": round(comparator_error, 12),
                "negative_control_relative_error": round(negative_control_error, 12),
            }
        )
    row_count = len(scored)
    if row_count < int(config["minimum_rows"]):
        raise RuntimeError(f"{lane_id} has too few scoreable WDI rows: {row_count}")
    model_mae = sum(model_errors) / row_count
    comparator_mae = sum(comparator_errors) / row_count
    negative_control_mae = sum(negative_control_errors) / row_count
    material_margin_met = model_mae + float(config["material_margin"]) < comparator_mae
    negative_control_rejected = negative_control_mae > model_mae
    pack_status = "STRICT_EVIDENCE_PASS_NO_COVERAGE_CLOSURE" if material_margin_met and negative_control_rejected else "STRICT_EVIDENCE_FAIL_CLOSED"
    scoring_pack = {
        "schema_id": "OC133_WDI_INDICATOR_SCORING_PACK_v1",
        "pack_status": pack_status,
        "status": pack_status,
        "lane_id": lane_id,
        "domain_class_id": config["domain_class_id"],
        "phenomenon_class_id": config["phenomenon_class_id"],
        "source_bound": True,
        "target_hidden": True,
        "score_materialized": True,
        "scientific_pass": pack_status == "STRICT_EVIDENCE_PASS_NO_COVERAGE_CLOSURE",
        "coverage_closure_allowed": False,
        "support_allowed_for_broad_coverage": False,
        "source_snapshot_ref": lane_refs["snapshot"],
        "source_snapshot_sha256": lock["source_snapshot_sha256"],
        "source_lock_ref": lane_refs["lock"],
        "visible_task_table_ref": lane_refs["task_table"],
        "hidden_target_lock_ref": lane_refs["target_lock"],
        "row_count": row_count,
        "model": {"model_id": config["model_id"], "rule": config["model_rule"]},
        "comparator": {"comparator_id": config["comparator_id"], "rule": config["comparator_rule"]},
        "residuals": {
            "model_relative_mae": round(model_mae, 12),
            "comparator_relative_mae": round(comparator_mae, 12),
            "negative_control_relative_mae": round(negative_control_mae, 12),
            "material_margin_met": material_margin_met,
            "material_margin_rule": (
                f"model_relative_mae + {config['material_margin']} must be below "
                "the last-observation comparator relative MAE"
            ),
        },
        "negative_control": {
            "control_id": config["negative_control_id"],
            "negative_control_rejected": negative_control_rejected,
        },
        "falsifiers": [
            "target values leak into visible task table",
            "source lock hash is missing or stale",
            "model relative MAE plus material margin is not below comparator relative MAE",
            "five-year mean negative control is not worse than the model",
        ],
        "replay_command": {
            "commands": [
                f"python {SCRIPT_REL} --lane {lane_id} --score --write-scoring",
                f"python {SCRIPT_REL} --lane {lane_id} --check",
            ]
        },
        "scored_rows_sha256": sha256_object(scored),
        "scored_rows_sample": scored[:10],
    }
    replay_report = {
        "schema_id": "OC133_WDI_INDICATOR_REPLAY_REPORT_v1",
        "status": "PASS" if scoring_pack["scientific_pass"] else "FAIL_CLOSED",
        "lane_id": lane_id,
        "scoring_pack_ref": lane_refs["scoring_pack"],
        "scoring_pack_sha256": sha256_object(scoring_pack),
        "row_count": row_count,
        "material_margin_met": material_margin_met,
        "negative_control_rejected": negative_control_rejected,
        "replay_command": {
            "commands": [
                f"python {SCRIPT_REL} --lane {lane_id} --score --write-scoring",
                f"python {SCRIPT_REL} --lane {lane_id} --check",
            ]
        },
        "coverage_closure_allowed": False,
    }
    if write:
        write_json(root / lane_refs["task_table"], task_table)
        write_json(root / lane_refs["target_lock"], target_lock)
        write_json(root / lane_refs["scoring_pack"], scoring_pack)
        write_json(root / lane_refs["replay_report"], replay_report)
    return {"scoring_pack": scoring_pack, "replay_report": replay_report}


def check(root: Path, lane_id: str) -> list[str]:
    errors: list[str] = []
    lane_refs = refs(lane_id)
    acquire_payload = acquire(root, lane_id, write=False)
    for key, expected in (("snapshot", acquire_payload["snapshot"]), ("lock", acquire_payload["lock"])):
        path = root / lane_refs[key]
        if not path.exists():
            errors.append(f"missing {lane_refs[key]}")
        elif read_json(path) != expected:
            errors.append(f"stale {lane_refs[key]}")
    score_payload = score(root, lane_id, write=False)
    expected_scoring = score_payload["scoring_pack"]
    expected_replay = score_payload["replay_report"]
    for key, expected in (("scoring_pack", expected_scoring), ("replay_report", expected_replay)):
        path = root / lane_refs[key]
        if not path.exists():
            errors.append(f"missing {lane_refs[key]}")
        elif read_json(path) != expected:
            errors.append(f"stale {lane_refs[key]}")
    for key in ("task_table", "target_lock"):
        if not (root / lane_refs[key]).exists():
            errors.append(f"missing {lane_refs[key]}")
    if expected_scoring.get("scientific_pass") is not True:
        errors.append(f"{lane_id} scoring pack is fail-closed")
    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Materialize target-hidden WDI indicator evidence packs.")
    parser.add_argument("--root", default=None)
    parser.add_argument("--lane", choices=sorted(LANE_CONFIGS), required=True)
    parser.add_argument("--acquire", action="store_true")
    parser.add_argument("--write-acquisition", action="store_true")
    parser.add_argument("--score", action="store_true")
    parser.add_argument("--write-scoring", action="store_true")
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve() if args.root else repo_root()
    if args.acquire or args.write_acquisition:
        payload = acquire(root, args.lane, write=args.write_acquisition)
        print(json.dumps({"lane": args.lane, "snapshot_rows": payload["snapshot"]["row_count"]}, indent=2))
    if args.score or args.write_scoring:
        payload = score(root, args.lane, write=args.write_scoring)
        print(
            json.dumps(
                {
                    "lane": args.lane,
                    "status": payload["scoring_pack"]["status"],
                    "row_count": payload["scoring_pack"]["row_count"],
                    "residuals": payload["scoring_pack"]["residuals"],
                },
                indent=2,
            )
        )
    if args.check:
        errors = check(root, args.lane)
        if errors:
            for error in errors:
                print(f"ERROR: {error}")
            return 1
        print(f"{args.lane}: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
