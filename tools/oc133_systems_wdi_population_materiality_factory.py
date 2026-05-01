from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from validation.grand_science import evidence_pack_factory as grand_factory


RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
CAPABILITY_OWNER = "Research/EmpiricalScience"

OUTPUT_ROOT_REL = "validation/heldout/grand_science/systems/wdi_population_materiality"
RAW_SNAPSHOT_REL = f"{OUTPUT_ROOT_REL}/raw/world_bank_wdi_arg_population_total_1960_2024.json"
PACK_REL = f"{OUTPUT_ROOT_REL}/OC133_SYSTEMS_WDI_POPULATION_MATERIALITY_CANDIDATE_PACK.json"
REPORT_REL = f"{OUTPUT_ROOT_REL}/OC133_SYSTEMS_WDI_POPULATION_MATERIALITY_REPORT.json"
PROTOCOL_REL = f"{OUTPUT_ROOT_REL}/OC133_SYSTEMS_WDI_POPULATION_MATERIALITY_PROTOCOL.json"
TASKS_REL = f"{OUTPUT_ROOT_REL}/OC133_SYSTEMS_WDI_POPULATION_MATERIALITY_TASKS.json"
SOURCE_LOCK_REL = f"{OUTPUT_ROOT_REL}/OC133_SYSTEMS_WDI_POPULATION_MATERIALITY_SOURCE_LOCK.json"
SOURCE_LOCK_DECLARATION_REL = f"{OUTPUT_ROOT_REL}/OC133_SYSTEMS_WDI_POPULATION_MATERIALITY_SOURCE_LOCK_DECLARATION.json"
ACQUISITION_PACKET_REL = f"{OUTPUT_ROOT_REL}/OC133_SYSTEMS_WDI_POPULATION_MATERIALITY_ACQUISITION_PACKET.json"
HASHES_REL = f"{OUTPUT_ROOT_REL}/OC133_SYSTEMS_WDI_POPULATION_MATERIALITY_HASHES.json"
README_REL = f"{OUTPUT_ROOT_REL}/README.md"
REQUIREMENTS_REL = "benchmarks/grand_science/domain_requirements.json"

REPORT_SCHEMA_ID = "OC133_SYSTEMS_WDI_POPULATION_MATERIALITY_REPORT"
PROTOCOL_SCHEMA_ID = "OC133_SYSTEMS_WDI_POPULATION_MATERIALITY_PROTOCOL"
TASKS_SCHEMA_ID = "OC133_SYSTEMS_WDI_POPULATION_MATERIALITY_TASKS"
SOURCE_LOCK_SCHEMA_ID = "OC133_SYSTEMS_WDI_POPULATION_MATERIALITY_SOURCE_LOCK"
SOURCE_LOCK_DECLARATION_SCHEMA_ID = "OC133_SYSTEMS_WDI_POPULATION_MATERIALITY_SOURCE_LOCK_DECLARATION"
STRICT_SCHEMA_ID = "OC133_SYSTEMS_WDI_POPULATION_MATERIALITY_STRICT_SCHEMA"

TARGET_COUNTRY_CODE = "ARG"
TARGET_COUNTRY_NAME = "Argentina"
TARGET_INDICATOR_ID = "SP.POP.TOTL"
TARGET_INDICATOR_NAME = "Population, total"
TARGET_YEARS = tuple(range(1980, 2000))
API_URL = (
    "https://api.worldbank.org/v2/country/ARG/indicator/SP.POP.TOTL"
    "?format=json&per_page=20000&date=1960:2024"
)
SOURCE_CONTRACT = "world_bank_wdi"
SUPERSEDES = [
    "validation/heldout/grand_science/systems/wdi_predictive_search_v2/"
    "OC133_SYSTEMS_WDI_PREDICTIVE_SEARCH_V2_CANDIDATE_PACK.json"
]

OBJECT_HASH_POLICY = "sha256 over canonical JSON"
ROW_HASH_POLICY = "sha256 over canonical row JSON excluding row_hash"
SOURCE_LOCK_HASH_POLICY = "sha256 over canonical JSON source-lock declaration"
SOURCE_LOCK_ORDER_HASH_POLICY = "sha256 over canonical JSON source-lock materialization order"
SOURCE_LOCK_PROOF_TYPE = "internal_materialization_order_hash"
SCORING_STARTED_AT = "2026-05-01T00:00:00Z"
MATERIALITY_POLICY_ID = "OC133-SYSTEMS-WDI-POPULATION-MATERIALITY-POLICY"
MIN_TRAINING_YEARS = 20
MIN_VALIDATION_SCORE_ROWS = 10
MIN_AGGREGATE_MARGIN_FRACTION_OF_RESIDUAL_SCALE = 0.01
MIN_AGGREGATE_MARGIN_FRACTION_OF_UNCERTAINTY_UPPER = 0.01
MIN_ROW_MARGIN_FRACTION_OF_RESIDUAL_SCALE = 0.01
MIN_ROW_MARGIN_FRACTION_OF_UNCERTAINTY_UPPER = 0.01
MIN_MATERIALITY_MARGIN_ABSOLUTE = 1e-12
FORBIDDEN_DECLARATION_KEYS = {
    "value",
    "target_value",
    "heldout_value",
    "observed_value",
    "predicted_value",
    "model_residual",
    "best_comparator_residual",
    "absolute_residual",
    "row_hash",
}
TRIVIAL_COMPARATOR_IDS = {"constant_zero", "zero", "null", "identity_target", "target_echo"}

Predictor = Callable[[list[int], list[float], int], float | None]


@dataclass(frozen=True)
class Formula:
    id: str
    family: str
    rule: str
    min_history: int
    predictor: Predictor
    parameters: dict[str, Any] | None = None


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_object(payload: Any) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def ordered_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def resolve_under_root(root: Path, ref: str) -> Path:
    path = (root / ref).resolve()
    path.relative_to(root.resolve())
    return path


def load_requirements(root: Path) -> tuple[dict[str, Any], list[str]]:
    path = root / REQUIREMENTS_REL
    if not path.exists():
        return (
            {
                "minimum_per_domain_n": 20,
                "required_domains": ["systems"],
                "required_source_separation_modes": ["prospective", "target_blind"],
            },
            ["REQUIREMENTS_MISSING::using_defaults"],
        )
    try:
        payload = read_json(path)
    except Exception as exc:
        return ({}, [f"REQUIREMENTS_PARSE_FAILED::{exc.__class__.__name__}"])
    return (payload, []) if isinstance(payload, dict) else ({}, ["REQUIREMENTS_NOT_OBJECT"])


def _last_slope(years: list[int], values: list[float], target_year: int) -> float | None:
    if len(values) < 2:
        return None
    return values[-1] + (values[-1] - values[-2])


def _mean_slope_5(years: list[int], values: list[float], target_year: int) -> float | None:
    if len(values) < 6:
        return None
    slopes = [values[idx] - values[idx - 1] for idx in range(len(values) - 5, len(values))]
    return values[-1] + sum(slopes) / len(slopes)


def _ols_10(years: list[int], values: list[float], target_year: int) -> float | None:
    if len(values) < 10:
        return None
    xs = years[-10:]
    ys = values[-10:]
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    denom = sum((x - mean_x) ** 2 for x in xs)
    if denom == 0:
        return None
    slope = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys)) / denom
    return mean_y + slope * (target_year - mean_x)


FORMULAS: tuple[Formula, ...] = (
    Formula("last_slope", "linear_increment", "y_t = y_t-1 + (y_t-1 - y_t-2)", 2, _last_slope),
    Formula("mean_slope_5", "linear_increment", "y_t = y_t-1 + mean(last five annual slopes)", 6, _mean_slope_5),
    Formula("ols_10", "linear_regression", "ordinary least-squares line on the last ten prior annual values", 10, _ols_10),
)

COMPARATOR_BASELINES = (
    {
        "id": "carry_forward_last_observation",
        "name": "WDI carry-forward last-observation comparator",
        "prediction_rule": "predict the heldout year as the latest prior observed WDI population value",
        "pre_registered": True,
    },
    {
        "id": "prior_training_mean",
        "name": "WDI prior-years arithmetic-mean comparator",
        "prediction_rule": "predict the heldout year as the arithmetic mean of all prior WDI population values",
        "pre_registered": True,
    },
    {
        "id": "trailing_three_year_mean",
        "name": "WDI trailing-three-year mean comparator",
        "prediction_rule": "predict the heldout year as the arithmetic mean of the latest three prior WDI population values",
        "pre_registered": True,
    },
)


def materiality_policy() -> dict[str, Any]:
    return {
        "policy_id": MATERIALITY_POLICY_ID,
        "policy_version": "1.0",
        "pre_registered": True,
        "metric": "absolute residual advantage over best preregistered comparator",
        "aggregate_gate": {
            "minimum_margin_fraction_of_residual_scale": MIN_AGGREGATE_MARGIN_FRACTION_OF_RESIDUAL_SCALE,
            "minimum_margin_fraction_of_uncertainty_upper": MIN_AGGREGATE_MARGIN_FRACTION_OF_UNCERTAINTY_UPPER,
        },
        "row_gate": {
            "minimum_margin_fraction_of_residual_scale": MIN_ROW_MARGIN_FRACTION_OF_RESIDUAL_SCALE,
            "minimum_margin_fraction_of_uncertainty_upper": MIN_ROW_MARGIN_FRACTION_OF_UNCERTAINTY_UPPER,
        },
        "minimum_margin_absolute": MIN_MATERIALITY_MARGIN_ABSOLUTE,
        "near_tie_policy": "strict greater-than is insufficient; aggregate and row margins must clear this policy",
    }


def materiality_policy_hash() -> str:
    return sha256_object(materiality_policy())


def required_margin(
    residual_scale: float,
    uncertainty_upper: float,
    residual_scale_fraction: float,
    uncertainty_upper_fraction: float,
) -> float:
    return max(
        MIN_MATERIALITY_MARGIN_ABSOLUTE,
        residual_scale_fraction * max(1.0, residual_scale),
        uncertainty_upper_fraction * max(0.0, uncertainty_upper),
    )


def payload_rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list) and len(payload) >= 2 and isinstance(payload[1], list):
        return [row for row in payload[1] if isinstance(row, dict)]
    if isinstance(payload, dict) and isinstance(payload.get("rows"), list):
        return [row for row in payload["rows"] if isinstance(row, dict)]
    raise ValueError("Expected World Bank WDI payload [metadata, rows] or {'rows': [...]}")


def payload_metadata(payload: Any) -> dict[str, Any]:
    if isinstance(payload, list) and payload and isinstance(payload[0], dict):
        return payload[0]
    if isinstance(payload, dict) and isinstance(payload.get("metadata"), dict):
        return payload["metadata"]
    return payload if isinstance(payload, dict) else {}


def parse_series(payload: Any) -> dict[int, float]:
    series: dict[int, float] = {}
    for row in payload_rows(payload):
        indicator = row.get("indicator") if isinstance(row.get("indicator"), dict) else {}
        country = row.get("country") if isinstance(row.get("country"), dict) else {}
        country_code = str(row.get("countryiso3code") or country.get("id") or "")
        indicator_id = str(indicator.get("id") or "")
        if country_code != TARGET_COUNTRY_CODE or indicator_id != TARGET_INDICATOR_ID:
            continue
        value = row.get("value")
        if value in (None, ""):
            continue
        try:
            year = int(str(row.get("date", "")).strip())
            number = float(value)
        except (TypeError, ValueError):
            continue
        if math.isfinite(number):
            series[year] = number
    return series


def formula_manifest() -> list[dict[str, Any]]:
    return [
        {
            "formula_id": formula.id,
            "family": formula.family,
            "rule": formula.rule,
            "min_history": formula.min_history,
            "parameters": formula.parameters or {},
        }
        for formula in FORMULAS
    ]


def comparator_predictions(values: list[float]) -> dict[str, float]:
    return {
        "carry_forward_last_observation": values[-1],
        "prior_training_mean": sum(values) / len(values),
        "trailing_three_year_mean": sum(values[-3:]) / min(3, len(values)),
    }


def prediction_for_formula(formula: Formula, years: list[int], values: list[float], target_year: int) -> float | None:
    if len(values) < formula.min_history:
        return None
    try:
        prediction = formula.predictor(years, values, target_year)
    except Exception:
        return None
    return prediction if prediction is not None and math.isfinite(prediction) else None


def formula_validation_rows(series: dict[int, float], target_year: int, formula: Formula) -> list[dict[str, Any]]:
    available_years = sorted(year for year in series if year < target_year)
    rows: list[dict[str, Any]] = []
    for scoring_year in available_years:
        training_years = [year for year in available_years if year < scoring_year]
        if len(training_years) < MIN_VALIDATION_SCORE_ROWS:
            continue
        values = [series[year] for year in training_years]
        prediction = prediction_for_formula(formula, training_years, values, scoring_year)
        if prediction is None:
            continue
        observed = series[scoring_year]
        comparator_residuals = [
            abs(comparator_prediction - observed)
            for comparator_prediction in comparator_predictions(values).values()
        ]
        rows.append(
            {
                "scoring_year": scoring_year,
                "training_years": training_years,
                "absolute_residual": abs(prediction - observed),
                "best_comparator_residual": min(comparator_residuals),
            }
        )
    return rows


def select_formula(series: dict[int, float], target_year: int) -> tuple[Formula | None, dict[str, Any], list[str]]:
    scores: list[dict[str, Any]] = []
    failures: list[str] = []
    best: tuple[float, int, Formula] | None = None
    for tie_rank, formula in enumerate(FORMULAS):
        validation_rows = formula_validation_rows(series, target_year, formula)
        residuals = [float(row["absolute_residual"]) for row in validation_rows]
        comparator_residuals = [float(row["best_comparator_residual"]) for row in validation_rows]
        mean_residual = sum(residuals) / len(residuals) if residuals else math.inf
        mean_comparator = sum(comparator_residuals) / len(comparator_residuals) if comparator_residuals else math.inf
        validation_margin = mean_comparator - mean_residual
        validation_required = required_margin(
            max(1.0, mean_residual, mean_comparator),
            max(residuals) if residuals else 0.0,
            MIN_AGGREGATE_MARGIN_FRACTION_OF_RESIDUAL_SCALE,
            MIN_AGGREGATE_MARGIN_FRACTION_OF_UNCERTAINTY_UPPER,
        )
        eligible = len(validation_rows) >= MIN_VALIDATION_SCORE_ROWS and validation_margin >= validation_required
        scores.append(
            {
                "formula_id": formula.id,
                "family": formula.family,
                "rule": formula.rule,
                "training_score_row_count": len(validation_rows),
                "scoring_years": [row["scoring_year"] for row in validation_rows],
                "mean_abs_training_residual": None if mean_residual == math.inf else mean_residual,
                "mean_best_comparator_training_residual": None if mean_comparator == math.inf else mean_comparator,
                "training_materiality_margin": None if mean_residual == math.inf else validation_margin,
                "training_materiality_required_margin": validation_required,
                "eligible": eligible,
            }
        )
        if eligible and (best is None or mean_residual < best[0]):
            best = (mean_residual, tie_rank, formula)
    if best is None:
        failures.append(f"FORMULA_SELECTION_INSUFFICIENT_TRAINING_VALIDATION::{target_year}")
    return (
        best[2] if best else None,
        {
            "target_year": target_year,
            "target_rows_used_for_selection": False,
            "minimum_training_years": MIN_TRAINING_YEARS,
            "minimum_training_score_rows": MIN_VALIDATION_SCORE_ROWS,
            "selection_metric": "lowest mean absolute residual on strictly prior one-step validation rows",
            "scores": scores,
            "selected_formula_id": best[2].id if best else None,
        },
        failures,
    )


def row_materiality(model_residual: float, best_comparator_residual: float, uncertainty_upper: float) -> dict[str, Any]:
    margin = best_comparator_residual - model_residual
    scale = max(1.0, abs(model_residual), abs(best_comparator_residual))
    needed = required_margin(
        scale,
        uncertainty_upper,
        MIN_ROW_MARGIN_FRACTION_OF_RESIDUAL_SCALE,
        MIN_ROW_MARGIN_FRACTION_OF_UNCERTAINTY_UPPER,
    )
    return {
        "policy_id": MATERIALITY_POLICY_ID,
        "policy_sha256": materiality_policy_hash(),
        "margin": margin,
        "required_margin": needed,
        "residual_scale": scale,
        "uncertainty_upper": uncertainty_upper,
        "margin_fraction_of_residual_scale": margin / scale if scale else 0.0,
        "margin_fraction_of_uncertainty_upper": margin / uncertainty_upper if uncertainty_upper else None,
        "passed": margin >= needed,
    }


def build_rows(series: dict[int, float], snapshot_ref: str, snapshot_sha256: str, target_years: tuple[int, ...] = TARGET_YEARS) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    failures: list[str] = []
    for target_year in target_years:
        training_years = sorted(year for year in series if year < target_year)
        if target_year not in series:
            failures.append(f"TARGET_VALUE_MISSING::{target_year}")
            continue
        if len(training_years) < MIN_TRAINING_YEARS:
            failures.append(f"TRAINING_YEARS_BELOW_MINIMUM::{target_year}::{len(training_years)}/{MIN_TRAINING_YEARS}")
            continue
        values = [series[year] for year in training_years]
        formula, selection, selection_failures = select_formula(series, target_year)
        failures.extend(selection_failures)
        if formula is None:
            continue
        prediction = prediction_for_formula(formula, training_years, values, target_year)
        if prediction is None:
            failures.append(f"FORMULA_PREDICTION_FAILED::{target_year}")
            continue
        observed = series[target_year]
        model_residual = abs(prediction - observed)
        selected_score = next(
            (score for score in selection["scores"] if score.get("formula_id") == formula.id),
            {},
        )
        uncertainty_upper = float(selected_score.get("mean_abs_training_residual") or 0.0)
        comparators: list[dict[str, Any]] = []
        for comparator in COMPARATOR_BASELINES:
            comparator_id = str(comparator["id"])
            comparator_prediction = comparator_predictions(values)[comparator_id]
            comparator_residual = abs(comparator_prediction - observed)
            comparators.append(
                {
                    "comparator_id": comparator_id,
                    "name": comparator["name"],
                    "prediction": comparator_prediction,
                    "absolute_residual": comparator_residual,
                    "negative_control_id": f"systems-wdi-population-materiality::{comparator_id}",
                    "negative_control_rejected": comparator_residual > model_residual,
                }
            )
        best_comparator_residual = min(float(item["absolute_residual"]) for item in comparators)
        materiality = row_materiality(model_residual, best_comparator_residual, uncertainty_upper)
        row = {
            "observation_id": f"OC133-SYSTEMS-WDI-POPULATION-MATERIALITY-{TARGET_COUNTRY_CODE}-{target_year}",
            "country": f"{TARGET_COUNTRY_CODE}:{TARGET_COUNTRY_NAME}",
            "indicator": f"{TARGET_INDICATOR_ID}:{TARGET_INDICATOR_NAME}",
            "training_years": training_years,
            "heldout_year": target_year,
            "training_source": f"{snapshot_ref}::{TARGET_COUNTRY_CODE}:{TARGET_INDICATOR_ID}::training_years={','.join(str(year) for year in training_years)}",
            "target_source": f"{snapshot_ref}::{TARGET_COUNTRY_CODE}:{TARGET_INDICATOR_ID}::heldout_target_year={target_year}",
            "source_snapshot_sha256": snapshot_sha256,
            "training_source_sha256": sha256_object({"snapshot": snapshot_sha256, "years": training_years}),
            "target_source_sha256": sha256_object({"snapshot": snapshot_sha256, "target_year": target_year}),
            "selected_formula_id": formula.id,
            "selected_formula_family": formula.family,
            "formula": formula.rule,
            "formula_selection": selection,
            "predicted_value": prediction,
            "observed_value": observed,
            "model_residual": model_residual,
            "comparator_baselines": comparators,
            "best_comparator_residual": best_comparator_residual,
            "negative_controls_passed": all(item["negative_control_rejected"] is True for item in comparators),
            "uncertainty": {
                "metric": "absolute residual",
                "method": "selected-formula mean absolute residual over strictly prior validation rows",
                "interval": [0.0, uncertainty_upper],
            },
            "materiality": materiality,
            "falsifier": (
                "support fails if formula selection uses the heldout target, if any comparator beats or ties the model, "
                "if source hashes change, or if any aggregate/row materiality margin falls below policy"
            ),
            "row_hash_policy": ROW_HASH_POLICY,
        }
        row["row_hash"] = sha256_object({key: value for key, value in row.items() if key != "row_hash"})
        rows.append(row)
    return rows, ordered_unique(failures)


def residual_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    model_values = [float(row["model_residual"]) for row in rows if is_number(row.get("model_residual"))]
    comparator_values = [float(row["best_comparator_residual"]) for row in rows if is_number(row.get("best_comparator_residual"))]
    model = sum(model_values) / len(model_values) if model_values else 0.0
    comparator = sum(comparator_values) / len(comparator_values) if comparator_values else 0.0
    by_comparator: dict[str, float] = {}
    for comparator_def in COMPARATOR_BASELINES:
        comparator_id = str(comparator_def["id"])
        values = [
            float(comp["absolute_residual"])
            for row in rows
            for comp in row.get("comparator_baselines", [])
            if comp.get("comparator_id") == comparator_id and is_number(comp.get("absolute_residual"))
        ]
        by_comparator[comparator_id] = sum(values) / len(values) if values else 0.0
    return {
        "model": model,
        "comparator": comparator,
        "superiority_margin": comparator - model,
        "by_comparator": by_comparator,
    }


def uncertainty_interval(rows: list[dict[str, Any]], model_mean: float) -> list[float]:
    upper_values = [
        float(row.get("uncertainty", {}).get("interval", [0.0, 0.0])[-1])
        for row in rows
        if isinstance(row.get("uncertainty"), dict)
    ]
    return [0.0, max([model_mean, *upper_values] or [0.0])]


def materiality_audit(rows: list[dict[str, Any]], residuals: dict[str, Any] | None = None) -> dict[str, Any]:
    residuals = residuals or residual_summary(rows)
    model = float(residuals.get("model") or 0.0)
    comparator = float(residuals.get("comparator") or 0.0)
    margin = comparator - model
    uncertainty_upper = uncertainty_interval(rows, model)[-1]
    scale = max(1.0, abs(model), abs(comparator))
    needed = required_margin(
        scale,
        uncertainty_upper,
        MIN_AGGREGATE_MARGIN_FRACTION_OF_RESIDUAL_SCALE,
        MIN_AGGREGATE_MARGIN_FRACTION_OF_UNCERTAINTY_UPPER,
    )
    failed_rows = [
        {
            "observation_id": row.get("observation_id"),
            "heldout_year": row.get("heldout_year"),
            "margin": row.get("materiality", {}).get("margin"),
            "required_margin": row.get("materiality", {}).get("required_margin"),
        }
        for row in rows
        if row.get("materiality", {}).get("passed") is not True
    ]
    return {
        "policy": materiality_policy(),
        "policy_sha256": materiality_policy_hash(),
        "aggregate_margin": margin,
        "aggregate_required_margin": needed,
        "aggregate_residual_scale": scale,
        "aggregate_uncertainty_upper": uncertainty_upper,
        "aggregate_margin_fraction_of_residual_scale": margin / scale if scale else 0.0,
        "aggregate_margin_fraction_of_uncertainty_upper": margin / uncertainty_upper if uncertainty_upper else None,
        "aggregate_passed": bool(rows) and margin >= needed,
        "row_total": len(rows),
        "row_materiality_failed_total": len(failed_rows),
        "row_materiality_failures": failed_rows,
        "passed": bool(rows) and margin >= needed and not failed_rows,
    }


def target_split_declarations(target_years: tuple[int, ...] = TARGET_YEARS) -> list[dict[str, Any]]:
    return [
        {
            "observation_id": f"OC133-SYSTEMS-WDI-POPULATION-MATERIALITY-{TARGET_COUNTRY_CODE}-{year}",
            "country": f"{TARGET_COUNTRY_CODE}:{TARGET_COUNTRY_NAME}",
            "indicator": f"{TARGET_INDICATOR_ID}:{TARGET_INDICATOR_NAME}",
            "heldout_year": year,
            "target_value_excluded": True,
        }
        for year in target_years
    ]


def row_split_declarations(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "observation_id": row.get("observation_id"),
            "country": row.get("country"),
            "indicator": row.get("indicator"),
            "heldout_year": row.get("heldout_year"),
            "target_value_excluded": True,
        }
        for row in rows
    ]


def declaration_contains_forbidden_fields(value: Any) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key) in FORBIDDEN_DECLARATION_KEYS:
                return True
            if declaration_contains_forbidden_fields(child):
                return True
    if isinstance(value, list):
        return any(declaration_contains_forbidden_fields(item) for item in value)
    return False


def source_claim(snapshot_ref: str) -> dict[str, Any]:
    return {
        "mode": "target_blind",
        "pre_target_lock": True,
        "target_hidden_until_scoring": True,
        "declared_before_scoring": True,
        "source_ref": snapshot_ref,
    }


def build_source_lock_declaration(snapshot_ref: str, snapshot_sha256: str, snapshot_lastupdated: str | None, target_years: tuple[int, ...] = TARGET_YEARS) -> dict[str, Any]:
    scoring_policy = {
        "selection_scope": "per target row; WDI years strictly earlier than heldout_year",
        "selection_metric": "lowest mean absolute residual on prior one-step validation rows",
        "target_rows_used_for_selection": False,
        "minimum_training_years": MIN_TRAINING_YEARS,
        "minimum_training_score_rows": MIN_VALIDATION_SCORE_ROWS,
        "materiality_policy": materiality_policy(),
        "materiality_policy_sha256": materiality_policy_hash(),
        "support_gate_policy": "support requires source lock, N, target-hidden selection, nontrivial comparators, uncertainty, negative controls, falsifiers, source hashes, and materiality",
    }
    return {
        "schema_id": SOURCE_LOCK_DECLARATION_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "declaration_id": "OC133-SYSTEMS-WDI-POPULATION-MATERIALITY-PRE-TARGET-DECLARATION",
        "source_claim": source_claim(snapshot_ref),
        "snapshot_ref": snapshot_ref,
        "snapshot_sha256": snapshot_sha256,
        "snapshot_lastupdated": snapshot_lastupdated,
        "scoring_started_timestamp": SCORING_STARTED_AT,
        "target_rows_declared_before_scoring": target_split_declarations(target_years),
        "candidate_formulas_declared_before_scoring": formula_manifest(),
        "comparator_baselines_declared_before_scoring": list(COMPARATOR_BASELINES),
        "scoring_policy_declared_before_scoring": scoring_policy,
        "declaration_exclusion_policy": {
            "forbidden_score_fields": sorted(FORBIDDEN_DECLARATION_KEYS),
            "observed_target_values_excluded": True,
            "predictions_excluded": True,
            "residuals_excluded": True,
        },
    }


def build_source_lock(declaration: dict[str, Any]) -> dict[str, Any]:
    target_rows = declaration.get("target_rows_declared_before_scoring", [])
    formulas = declaration.get("candidate_formulas_declared_before_scoring", [])
    comparators = declaration.get("comparator_baselines_declared_before_scoring", [])
    scoring_policy = declaration.get("scoring_policy_declared_before_scoring", {})
    order = {
        "protocol_id": "OC133-SYSTEMS-WDI-POPULATION-MATERIALITY-SOURCE-LOCK-PROTOCOL",
        "proof_type": SOURCE_LOCK_PROOF_TYPE,
        "steps": [
            {"step_index": 1, "step_id": "snapshot_hash_materialized", "snapshot_sha256": declaration.get("snapshot_sha256")},
            {"step_index": 2, "step_id": "target_blind_declaration_materialized", "declaration_sha256": sha256_object(declaration), "target_values_excluded": not declaration_contains_forbidden_fields(declaration)},
            {"step_index": 3, "step_id": "model_comparator_policy_locked", "formula_sha256": sha256_object(formulas), "comparator_sha256": sha256_object(comparators), "scoring_policy_sha256": sha256_object(scoring_policy)},
            {"step_index": 4, "step_id": "heldout_scoring_permitted_after_lock", "scoring_started_timestamp": declaration.get("scoring_started_timestamp")},
        ],
    }
    order_hash = sha256_object(order)
    return {
        "schema_id": SOURCE_LOCK_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "source_lock_id": "OC133-SYSTEMS-WDI-POPULATION-MATERIALITY-SOURCE-LOCK",
        "lock_proof_type": SOURCE_LOCK_PROOF_TYPE,
        "internal_lock_id": f"OC133-SYSTEMS-WDI-POPULATION-MATERIALITY-INTERNAL-LOCK-{order_hash[:16]}",
        "declaration_ref": SOURCE_LOCK_DECLARATION_REL,
        "declaration_sha256": sha256_object(declaration),
        "declaration_hash_policy": SOURCE_LOCK_HASH_POLICY,
        "materialization_order": order,
        "materialization_order_hash": order_hash,
        "materialization_order_hash_policy": SOURCE_LOCK_ORDER_HASH_POLICY,
        "declared_before_scoring": True,
        "pre_target_lock": True,
        "target_hidden_until_scoring": not declaration_contains_forbidden_fields(declaration),
        "snapshot_ref": declaration.get("snapshot_ref"),
        "snapshot_sha256": declaration.get("snapshot_sha256"),
        "model_family_declared_before_scoring": True,
        "target_split_declared_before_scoring": True,
        "candidate_formulas_declared_before_scoring": True,
        "comparator_baselines_declared_before_scoring": True,
        "scoring_policy_declared_before_scoring": True,
        "target_split_sha256": sha256_object(target_rows),
        "candidate_formulas_sha256": sha256_object(formulas),
        "comparator_baselines_sha256": sha256_object(comparators),
        "scoring_policy_sha256": sha256_object(scoring_policy),
        "declaration_excludes_target_values": not declaration_contains_forbidden_fields(declaration),
    }


def validate_source_lock(source_lock: dict[str, Any], declaration: dict[str, Any], rows: list[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    if source_lock.get("schema_id") != SOURCE_LOCK_SCHEMA_ID:
        failures.append("SOURCE_LOCK_SCHEMA_ID_MISMATCH")
    if declaration.get("schema_id") != SOURCE_LOCK_DECLARATION_SCHEMA_ID:
        failures.append("SOURCE_LOCK_DECLARATION_SCHEMA_ID_MISMATCH")
    if source_lock.get("declaration_sha256") != sha256_object(declaration):
        failures.append("SOURCE_LOCK_DECLARATION_HASH_MISMATCH")
    if declaration_contains_forbidden_fields(declaration):
        failures.append("SOURCE_LOCK_DECLARATION_CONTAINS_TARGET_OR_SCORE_FIELDS")
    for field in (
        "declared_before_scoring",
        "pre_target_lock",
        "target_hidden_until_scoring",
        "model_family_declared_before_scoring",
        "target_split_declared_before_scoring",
        "candidate_formulas_declared_before_scoring",
        "comparator_baselines_declared_before_scoring",
        "scoring_policy_declared_before_scoring",
        "declaration_excludes_target_values",
    ):
        if source_lock.get(field) is not True:
            failures.append(f"SOURCE_LOCK_PREDICATE_NOT_TRUE::{field}")
    if source_lock.get("materialization_order_hash") != sha256_object(source_lock.get("materialization_order", {})):
        failures.append("SOURCE_LOCK_MATERIALIZATION_ORDER_HASH_MISMATCH")
    if source_lock.get("target_split_sha256") != sha256_object(declaration.get("target_rows_declared_before_scoring", [])):
        failures.append("SOURCE_LOCK_TARGET_SPLIT_HASH_MISMATCH")
    if source_lock.get("candidate_formulas_sha256") != sha256_object(declaration.get("candidate_formulas_declared_before_scoring", [])):
        failures.append("SOURCE_LOCK_CANDIDATE_FORMULAS_HASH_MISMATCH")
    if source_lock.get("comparator_baselines_sha256") != sha256_object(declaration.get("comparator_baselines_declared_before_scoring", [])):
        failures.append("SOURCE_LOCK_COMPARATOR_BASELINES_HASH_MISMATCH")
    scoring_policy = declaration.get("scoring_policy_declared_before_scoring", {})
    if source_lock.get("scoring_policy_sha256") != sha256_object(scoring_policy):
        failures.append("SOURCE_LOCK_SCORING_POLICY_HASH_MISMATCH")
    if scoring_policy.get("materiality_policy") != materiality_policy():
        failures.append("SOURCE_LOCK_MATERIALITY_POLICY_MISMATCH")
    if scoring_policy.get("materiality_policy_sha256") != materiality_policy_hash():
        failures.append("SOURCE_LOCK_MATERIALITY_POLICY_HASH_MISMATCH")
    if row_split_declarations(rows) != declaration.get("target_rows_declared_before_scoring", []):
        failures.append("SOURCE_LOCK_DECLARED_TARGET_ROWS_DO_NOT_MATCH_SCORED_ROWS")
    return ordered_unique(failures)


def comparator_triviality_failures(comparators: list[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    if len(comparators) < 2:
        failures.append("COMPARATOR_BASELINES_TOO_FEW")
    for comparator in comparators:
        comparator_id = str(comparator.get("id") or comparator.get("comparator_id") or "").lower()
        text = f"{comparator_id} {comparator.get('name', '')} {comparator.get('prediction_rule', '')}".lower()
        if comparator.get("pre_registered") is not True:
            failures.append(f"COMPARATOR_NOT_PREREGISTERED::{comparator_id}")
        if comparator_id in TRIVIAL_COMPARATOR_IDS or "constant zero" in text or "target" in comparator_id:
            failures.append(f"COMPARATOR_TRIVIAL::{comparator_id}")
    return ordered_unique(failures)


def validate_rows(rows: list[dict[str, Any]]) -> tuple[list[str], list[dict[str, Any]]]:
    failures: list[str] = []
    failure_rows: list[dict[str, Any]] = []
    for row in rows:
        row_failures: list[str] = []
        row_id = str(row.get("observation_id", "unknown"))
        heldout_year = int(row.get("heldout_year", -1))
        if any(int(year) >= heldout_year for year in row.get("training_years", [])):
            row_failures.append("TRAINING_YEAR_NOT_PRIOR")
        selection = row.get("formula_selection") if isinstance(row.get("formula_selection"), dict) else {}
        if selection.get("target_rows_used_for_selection") is not False:
            row_failures.append("FORMULA_SELECTION_TARGET_LEAKAGE")
        for score in selection.get("scores", []):
            if any(int(year) >= heldout_year for year in score.get("scoring_years", [])):
                row_failures.append(f"FORMULA_SELECTION_SCORE_NOT_PRIOR::{score.get('formula_id')}")
        if row.get("negative_controls_passed") is not True:
            row_failures.append("NEGATIVE_CONTROLS_NOT_ALL_REJECTED")
        if row.get("materiality", {}).get("passed") is not True:
            row_failures.append("ROW_MATERIALITY_NOT_MET")
        if not row.get("source_snapshot_sha256") or not row.get("training_source_sha256") or not row.get("target_source_sha256"):
            row_failures.append("SOURCE_HASHES_MISSING")
        expected_hash = sha256_object({key: value for key, value in row.items() if key != "row_hash"})
        if row.get("row_hash") != expected_hash:
            row_failures.append("ROW_HASH_MISMATCH")
        if row_failures:
            failures.extend(f"{failure}::{row_id}" for failure in row_failures)
            failure_rows.append(
                {
                    "observation_id": row_id,
                    "heldout_year": heldout_year,
                    "model_residual": row.get("model_residual"),
                    "best_comparator_residual": row.get("best_comparator_residual"),
                    "materiality": row.get("materiality"),
                    "failures": row_failures,
                }
            )
    return ordered_unique(failures), failure_rows


def aggregate_negative_controls(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    controls: list[dict[str, Any]] = []
    for row in rows:
        for comparator in row.get("comparator_baselines", []):
            controls.append(
                {
                    "control_id": f"{comparator.get('negative_control_id')}::{row.get('observation_id')}",
                    "description": "pre-registered comparator must have larger heldout absolute residual than the selected training-only model",
                    "rejected": comparator.get("negative_control_rejected") is True,
                    "observation_id": row.get("observation_id"),
                    "comparator_id": comparator.get("comparator_id"),
                }
            )
    return controls or [{"control_id": "systems-wdi-population-materiality-no-controls", "description": "no heldout rows available", "rejected": False}]


def build_pack(rows: list[dict[str, Any]], source_lock: dict[str, Any], support_allowed: bool) -> dict[str, Any]:
    residuals = residual_summary(rows)
    return {
        "schema_id": grand_factory.EVIDENCE_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "capability_owner": CAPABILITY_OWNER,
        "evidence_pack_id": "OC133-SYSTEMS-WDI-POPULATION-MATERIALITY-CANDIDATE",
        "evidence_family": "systems_wdi_population_materiality",
        "evidence_pack_version": "1.0.0",
        "source_contract": SOURCE_CONTRACT,
        "supersedes": SUPERSEDES,
        "domain": "systems",
        "source_separation": {
            "mode": "target_blind",
            "pre_target_lock": source_lock.get("pre_target_lock") is True,
            "target_hidden_until_scoring": source_lock.get("target_hidden_until_scoring") is True,
            "training_sources": ordered_unique([str(row["training_source"]) for row in rows]),
            "target_sources": ordered_unique([str(row["target_source"]) for row in rows]),
            "source_hashes": ordered_unique([str(row["source_snapshot_sha256"]) for row in rows]),
        },
        "n": len(rows),
        "model_under_test": "World Bank WDI Argentina population training-only formula-family selector over fixed 1980-1999 heldout panel",
        "comparator_baseline": {
            "name": "best-of WDI carry-forward, prior mean, and trailing-three-year mean comparators",
            "prediction_rule": "support requires the selected model to beat every preregistered comparator on every heldout row",
            "pre_registered": True,
            "baselines": list(COMPARATOR_BASELINES),
        },
        "uncertainty": {
            "metric": "mean absolute heldout residual",
            "method": "selected-formula prior validation residual envelope",
            "interval": uncertainty_interval(rows, float(residuals["model"])),
        },
        "residuals": residuals,
        "materiality_audit": materiality_audit(rows, residuals),
        "negative_controls": aggregate_negative_controls(rows),
        "falsifiers": ordered_unique([str(row["falsifier"]) for row in rows]),
        "grand_toe_support_allowed": bool(support_allowed),
    }


def strict_schema_failures(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for key in ("candidate_pack", "protocol", "tasks", "report", "source_lock", "source_lock_declaration"):
        if not isinstance(payload.get(key), dict):
            return [f"STRICT_SCHEMA_FIELD_INVALID::{key}"]
    pack = payload["candidate_pack"]
    report = payload["report"]
    tasks = payload["tasks"]
    source_lock = payload["source_lock"]
    declaration = payload["source_lock_declaration"]
    if report.get("strict_schema_id") != STRICT_SCHEMA_ID:
        failures.append("STRICT_REPORT_SCHEMA_MARKER_MISSING")
    failures.extend(f"STRICT_{failure}" for failure in validate_source_lock(source_lock, declaration, tasks.get("rows", [])))
    failures.extend(f"STRICT_{failure}" for failure in comparator_triviality_failures(pack.get("comparator_baseline", {}).get("baselines", [])))
    row_failures, _failure_rows = validate_rows(tasks.get("rows", []))
    failures.extend(f"STRICT_{failure}" for failure in row_failures)
    audit = pack.get("materiality_audit", {})
    if audit.get("passed") is not True:
        failures.append("STRICT_MATERIALITY_NOT_MET")
    if pack.get("grand_toe_support_allowed") is True and audit.get("passed") is not True:
        failures.append("STRICT_SUPPORT_REQUIRES_MATERIALITY")
    if report.get("candidate_pack_sha256") != sha256_object(pack):
        failures.append("STRICT_CANDIDATE_PACK_HASH_MISMATCH")
    return ordered_unique(failures)


def build_acquisition_packet(snapshot_ref: str, snapshot_sha256: str | None, status: str) -> dict[str, Any]:
    return {
        "schema_id": "OC133_SYSTEMS_WDI_POPULATION_MATERIALITY_ACQUISITION_PACKET",
        "release_id": RELEASE_ID,
        "capability_owner": CAPABILITY_OWNER,
        "no_send": True,
        "public_action_allowed": False,
        "official_source": "World Bank WDI API",
        "method": "read-only HTTPS GET",
        "url": API_URL,
        "snapshot_ref": snapshot_ref,
        "snapshot_sha256": snapshot_sha256,
        "status": status,
    }


def fetch_official_snapshot() -> Any:
    with urllib.request.urlopen(API_URL, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def ensure_snapshot(root: Path, snapshot_ref: str, acquire_official: bool) -> tuple[Any | None, str | None, list[str]]:
    path = resolve_under_root(root, snapshot_ref)
    if not path.exists():
        if not acquire_official:
            return None, None, [f"SNAPSHOT_MISSING::{snapshot_ref}"]
        payload = fetch_official_snapshot()
        write_json(path, payload)
    try:
        payload = read_json(path)
    except Exception as exc:
        return None, None, [f"SNAPSHOT_PARSE_FAILED::{exc.__class__.__name__}"]
    return payload, sha256_file(path), []


def build_payload(
    root: Path = ROOT,
    *,
    snapshot_ref: str = RAW_SNAPSHOT_REL,
    acquire_official: bool = False,
    target_years: tuple[int, ...] = TARGET_YEARS,
) -> dict[str, Any]:
    requirements, requirement_failures = load_requirements(root)
    minimum_n = int(requirements.get("minimum_per_domain_n", 20))
    raw_payload, snapshot_sha256, snapshot_failures = ensure_snapshot(root, snapshot_ref, acquire_official)
    blockers = ordered_unique([*requirement_failures, *snapshot_failures])
    series: dict[int, float] = {}
    if raw_payload is not None:
        try:
            series = parse_series(raw_payload)
        except Exception as exc:
            blockers.append(f"SNAPSHOT_PARSE_FAILED::{exc.__class__.__name__}")
    snapshot_sha256 = snapshot_sha256 or "missing"
    metadata = payload_metadata(raw_payload) if raw_payload is not None else {}
    declaration = build_source_lock_declaration(snapshot_ref, snapshot_sha256, metadata.get("lastupdated"), target_years)
    source_lock = build_source_lock(declaration)
    rows, row_build_failures = build_rows(series, snapshot_ref, snapshot_sha256, target_years)
    row_failures, failure_rows = validate_rows(rows)
    source_lock_failures = validate_source_lock(source_lock, declaration, rows)
    comparator_failures = comparator_triviality_failures(list(COMPARATOR_BASELINES))
    residuals = residual_summary(rows)
    audit = materiality_audit(rows, residuals)
    if len(rows) < minimum_n:
        blockers.append(f"N_BELOW_MINIMUM::{len(rows)}/{minimum_n}")
    if residuals["superiority_margin"] <= 0:
        blockers.append("HELDOUT_RESIDUAL_SUPERIORITY_NOT_MET")
    if audit["passed"] is not True:
        blockers.append("HELDOUT_RESIDUAL_MATERIALITY_NOT_MET")
    blockers = ordered_unique([*blockers, *row_build_failures, *row_failures, *source_lock_failures, *comparator_failures])
    support_pre_strict = not blockers
    pack = build_pack(rows, source_lock, support_pre_strict)
    gate_failures = grand_factory.pack_failure_reasons(build_pack(rows, source_lock, True), requirements)
    if gate_failures:
        pack = build_pack(rows, source_lock, False)
    pack_sha256 = sha256_object(pack)
    acquisition_packet = build_acquisition_packet(snapshot_ref, None if snapshot_sha256 == "missing" else snapshot_sha256, "ACQUIRED_OR_PRESENT" if raw_payload is not None else "BLOCKED_MISSING")
    lock_metadata = {
        "source_lock_ref": SOURCE_LOCK_REL,
        "source_lock_sha256": sha256_object(source_lock),
        "source_lock_declaration_ref": SOURCE_LOCK_DECLARATION_REL,
        "source_lock_declaration_sha256": sha256_object(declaration),
        "materialization_order_hash": source_lock.get("materialization_order_hash"),
        "snapshot_ref": snapshot_ref,
        "snapshot_sha256": snapshot_sha256,
    }
    protocol = {
        "schema_id": PROTOCOL_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "candidate_pack_ref": PACK_REL,
        "candidate_pack_sha256": pack_sha256,
        "snapshot_ref": snapshot_ref,
        "snapshot_sha256": snapshot_sha256,
        "acquisition_packet_ref": ACQUISITION_PACKET_REL,
        "pre_target_lock_metadata": lock_metadata,
        "target_panel": list(target_years),
        "formula_manifest": formula_manifest(),
        "comparator_baselines": list(COMPARATOR_BASELINES),
        "materiality_policy": materiality_policy(),
        "materiality_policy_sha256": materiality_policy_hash(),
        "blockers": [],
    }
    tasks = {
        "schema_id": TASKS_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "snapshot_ref": snapshot_ref,
        "snapshot_sha256": snapshot_sha256,
        "pre_target_lock_metadata": lock_metadata,
        "row_hashes_sha256": sha256_object([row.get("row_hash") for row in rows]),
        "rows": rows,
        "exact_failure_rows": failure_rows,
        "blockers": [],
    }
    report = {
        "schema_id": REPORT_SCHEMA_ID,
        "strict_schema_id": STRICT_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "candidate_pack_ref": PACK_REL,
        "candidate_pack_sha256": pack_sha256,
        "snapshot_ref": snapshot_ref,
        "snapshot_sha256": snapshot_sha256,
        "acquisition_packet_ref": ACQUISITION_PACKET_REL,
        "pre_target_lock_metadata": lock_metadata,
        "minimum_n": minimum_n,
        "candidate_n": len(rows),
        "series_year_total": len(series),
        "selected_formula_counts": selected_formula_counts(rows),
        "residuals": residuals,
        "materiality_audit": audit,
        "source_lock_failures": source_lock_failures,
        "row_validation_failures": row_failures,
        "candidate_gate_failures": gate_failures,
        "strict_schema_failures": [],
        "exact_failure_rows": failure_rows,
        "grand_toe_support_allowed": False,
        "verdict": "BLOCKED",
        "valid_pack_total": 0,
        "blockers": [],
        "no_send": True,
        "publish_allowed": False,
        "journal_submissions_allowed": False,
    }
    payload = {
        "candidate_pack": pack,
        "protocol": protocol,
        "tasks": tasks,
        "report": report,
        "source_lock": source_lock,
        "source_lock_declaration": declaration,
        "acquisition_packet": acquisition_packet,
    }
    strict_failures = strict_schema_failures(payload)
    support_allowed = support_pre_strict and not gate_failures and not strict_failures
    if support_allowed != pack.get("grand_toe_support_allowed"):
        payload["candidate_pack"] = build_pack(rows, source_lock, support_allowed)
        pack_sha256 = sha256_object(payload["candidate_pack"])
        payload["protocol"]["candidate_pack_sha256"] = pack_sha256
        payload["report"]["candidate_pack_sha256"] = pack_sha256
    final_pack_failures = grand_factory.pack_failure_reasons(payload["candidate_pack"], requirements)
    final_blockers = ordered_unique([*blockers, *gate_failures, *strict_failures, *final_pack_failures])
    if not support_allowed and "GRAND_TOE_SUPPORT_NOT_ALLOWED" not in final_blockers:
        final_blockers.append("GRAND_TOE_SUPPORT_NOT_ALLOWED")
    for section in ("protocol", "tasks"):
        payload[section]["blockers"] = final_blockers
    payload["report"].update(
        {
            "candidate_pack_sha256": sha256_object(payload["candidate_pack"]),
            "pack_failure_reasons": final_pack_failures,
            "strict_schema_failures": strict_failures,
            "blockers": final_blockers,
            "grand_toe_support_allowed": support_allowed,
            "verdict": "READY_FOR_PARENT_REGISTRY_REVIEW" if support_allowed else "BLOCKED",
            "valid_pack_total": 1 if support_allowed else 0,
        }
    )
    return payload


def selected_formula_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        formula_id = str(row.get("selected_formula_id", "unknown"))
        counts[formula_id] = counts.get(formula_id, 0) + 1
    return dict(sorted(counts.items()))


def readme(payload: dict[str, Any]) -> str:
    report = payload["report"]
    audit = report["materiality_audit"]
    return "\n".join(
        [
            "# Systems WDI Population Materiality",
            "",
            "Official no-send WDI lane for a fixed Argentina population-total heldout panel.",
            "",
            f"- Verdict: `{report['verdict']}`",
            f"- Candidate N: `{report['candidate_n']}`",
            f"- Materiality passed: `{audit['passed']}`",
            f"- Aggregate margin: `{audit['aggregate_margin']}`",
            f"- Required aggregate margin: `{audit['aggregate_required_margin']}`",
            f"- Source snapshot: `{report['snapshot_ref']}`",
            "",
        ]
    )


def write_outputs(root: Path = ROOT, *, snapshot_ref: str = RAW_SNAPSHOT_REL, acquire_official: bool = False) -> dict[str, Any]:
    payload = build_payload(root, snapshot_ref=snapshot_ref, acquire_official=acquire_official)
    write_json(root / PACK_REL, payload["candidate_pack"])
    write_json(root / PROTOCOL_REL, payload["protocol"])
    write_json(root / TASKS_REL, payload["tasks"])
    write_json(root / REPORT_REL, payload["report"])
    write_json(root / SOURCE_LOCK_REL, payload["source_lock"])
    write_json(root / SOURCE_LOCK_DECLARATION_REL, payload["source_lock_declaration"])
    write_json(root / ACQUISITION_PACKET_REL, payload["acquisition_packet"])
    hashes = {
        "schema_id": "OC133_SYSTEMS_WDI_POPULATION_MATERIALITY_HASHES",
        "release_id": RELEASE_ID,
        "capability_owner": CAPABILITY_OWNER,
        "hash_policy": OBJECT_HASH_POLICY,
        "artifacts": {
            PACK_REL: sha256_object(payload["candidate_pack"]),
            PROTOCOL_REL: sha256_object(payload["protocol"]),
            TASKS_REL: sha256_object(payload["tasks"]),
            REPORT_REL: sha256_object(payload["report"]),
            SOURCE_LOCK_REL: sha256_object(payload["source_lock"]),
            SOURCE_LOCK_DECLARATION_REL: sha256_object(payload["source_lock_declaration"]),
            ACQUISITION_PACKET_REL: sha256_object(payload["acquisition_packet"]),
        },
    }
    raw_path = root / (payload["report"]["snapshot_ref"])
    if raw_path.exists():
        hashes["artifacts"][payload["report"]["snapshot_ref"]] = sha256_file(raw_path)
    write_json(root / HASHES_REL, hashes)
    write_text(root / README_REL, readme(payload))
    return payload


def check_stored(root: Path = ROOT, *, snapshot_ref: str = RAW_SNAPSHOT_REL) -> list[str]:
    expected = build_payload(root, snapshot_ref=snapshot_ref, acquire_official=False)
    failures: list[str] = []
    for rel_path, key in (
        (PACK_REL, "candidate_pack"),
        (PROTOCOL_REL, "protocol"),
        (TASKS_REL, "tasks"),
        (REPORT_REL, "report"),
        (SOURCE_LOCK_REL, "source_lock"),
        (SOURCE_LOCK_DECLARATION_REL, "source_lock_declaration"),
        (ACQUISITION_PACKET_REL, "acquisition_packet"),
    ):
        path = root / rel_path
        if not path.exists():
            failures.append(f"MISSING::{rel_path}")
            continue
        if read_json(path) != expected[key]:
            failures.append(f"CONTENT_MISMATCH::{rel_path}")
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build OC133 systems WDI population materiality artifacts.")
    parser.add_argument("--snapshot-ref", default=RAW_SNAPSHOT_REL)
    parser.add_argument("--acquire-official", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if args.check:
        failures = check_stored(ROOT, snapshot_ref=args.snapshot_ref)
        if failures:
            print(json.dumps({"ok": False, "failures": failures}, indent=2))
            return 1
        print(json.dumps({"ok": True}, indent=2))
        return 0
    payload = write_outputs(ROOT, snapshot_ref=args.snapshot_ref, acquire_official=args.acquire_official)
    print(json.dumps({"verdict": payload["report"]["verdict"], "support": payload["report"]["grand_toe_support_allowed"], "n": payload["report"]["candidate_n"]}, indent=2))
    return 0 if payload["report"]["grand_toe_support_allowed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
