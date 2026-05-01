from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
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

OUTPUT_ROOT_REL = "validation/heldout/grand_science/systems/wdi_model_search"
PACK_REL = f"{OUTPUT_ROOT_REL}/OC133_SYSTEMS_WDI_MODEL_SEARCH_CANDIDATE_PACK.json"
REPORT_REL = f"{OUTPUT_ROOT_REL}/OC133_SYSTEMS_WDI_MODEL_SEARCH_REPORT.json"
PROTOCOL_REL = f"{OUTPUT_ROOT_REL}/OC133_SYSTEMS_WDI_MODEL_SEARCH_PROTOCOL.json"
TASKS_REL = f"{OUTPUT_ROOT_REL}/OC133_SYSTEMS_WDI_MODEL_SEARCH_TASKS.json"
README_REL = f"{OUTPUT_ROOT_REL}/README.md"

DEFAULT_SNAPSHOT_REF = (
    "validation/heldout/grand_science/systems/harvested/"
    "systems_world_bank_wdi_official_endpoint_snapshot.json"
)
FALLBACK_SNAPSHOT_REFS = (
    DEFAULT_SNAPSHOT_REF,
    "validation/_raw/systems_world_bank_gdp.txt",
)
HARVESTED_SOURCE_PACK_REL = "validation/heldout/grand_science/systems/harvested/systems_candidate_evidence_pack.json"
REQUIREMENTS_REL = "benchmarks/grand_science/domain_requirements.json"

REPORT_SCHEMA_ID = "OC133_SYSTEMS_WDI_MODEL_SEARCH_REPORT_v1"
PROTOCOL_SCHEMA_ID = "OC133_SYSTEMS_WDI_MODEL_SEARCH_PROTOCOL_v1"
TASKS_SCHEMA_ID = "OC133_SYSTEMS_WDI_MODEL_SEARCH_TASKS_v1"

SNAPSHOT_HASH_POLICY = "LF_NORMALIZED_TEXT_SNAPSHOT_HASH"
OBJECT_HASH_POLICY = "sha256 over canonical JSON"
ROW_HASH_POLICY = "sha256 over canonical row JSON excluding row_hash"
MIN_TRAINING_SCORE_ROWS = 3


Predictor = Callable[[list[float]], float]


@dataclass(frozen=True)
class Formula:
    id: str
    rule: str
    min_history: int
    predictor: Predictor


@dataclass(frozen=True)
class SeriesKey:
    country_code: str
    country_name: str
    indicator_id: str
    indicator_name: str

    def source_token(self) -> str:
        return f"{self.country_code}:{self.indicator_id}"

    def label(self) -> str:
        return f"{self.country_code}:{self.country_name}::{self.indicator_id}:{self.indicator_name}"


def _linear_two_lag(history: list[float]) -> float:
    return history[-1] + (history[-1] - history[-2])


def _damped_two_lag_75(history: list[float]) -> float:
    return history[-1] + 0.75 * (history[-1] - history[-2])


def _damped_two_lag_50(history: list[float]) -> float:
    return history[-1] + 0.5 * (history[-1] - history[-2])


def _damped_two_lag_25(history: list[float]) -> float:
    return history[-1] + 0.25 * (history[-1] - history[-2])


def _mean_slope_three(history: list[float]) -> float:
    slopes = [history[-1] - history[-2], history[-2] - history[-3]]
    return history[-1] + sum(slopes) / len(slopes)


def _mean_slope_five(history: list[float]) -> float:
    tail = history[-5:]
    slopes = [tail[idx] - tail[idx - 1] for idx in range(1, len(tail))]
    return tail[-1] + sum(slopes) / len(slopes)


def _three_year_level_mean(history: list[float]) -> float:
    return sum(history[-3:]) / 3.0


def _log_growth_two_lag(history: list[float]) -> float:
    older, newer = history[-2], history[-1]
    if older > 0.0 and newer > 0.0:
        return newer * (newer / older)
    return _linear_two_lag(history)


FORMULA_FAMILIES: tuple[Formula, ...] = (
    Formula("linear_two_lag", "y_t = y_t-1 + (y_t-1 - y_t-2)", 2, _linear_two_lag),
    Formula("damped_two_lag_75", "y_t = y_t-1 + 0.75*(y_t-1 - y_t-2)", 2, _damped_two_lag_75),
    Formula("damped_two_lag_50", "y_t = y_t-1 + 0.5*(y_t-1 - y_t-2)", 2, _damped_two_lag_50),
    Formula("damped_two_lag_25", "y_t = y_t-1 + 0.25*(y_t-1 - y_t-2)", 2, _damped_two_lag_25),
    Formula("mean_slope_three", "y_t = y_t-1 + mean(two previous annual slopes)", 3, _mean_slope_three),
    Formula("mean_slope_five", "y_t = y_t-1 + mean(four previous annual slopes)", 5, _mean_slope_five),
    Formula("three_year_level_mean", "y_t = mean(y_t-1, y_t-2, y_t-3)", 3, _three_year_level_mean),
    Formula("log_growth_two_lag", "y_t = y_t-1 * (y_t-1 / y_t-2), positive series only", 2, _log_growth_two_lag),
)


def repo_root() -> Path:
    return ROOT


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_object(payload: Any) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def sha256_file_text(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def resolve_under_root(root: Path, ref: str) -> Path:
    path = (root / ref).resolve()
    path.relative_to(root.resolve())
    return path


def ordered_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def is_finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def as_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


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
    if not isinstance(payload, dict):
        return ({}, ["REQUIREMENTS_NOT_OBJECT"])
    return payload, []


def choose_snapshot_ref(root: Path, snapshot_ref: str | None = None) -> str:
    if snapshot_ref:
        return snapshot_ref
    for candidate in FALLBACK_SNAPSHOT_REFS:
        if (root / candidate).exists():
            return candidate
    return DEFAULT_SNAPSHOT_REF


def payload_metadata(payload: Any) -> dict[str, Any]:
    if isinstance(payload, list) and payload and isinstance(payload[0], dict):
        return payload[0]
    if isinstance(payload, dict):
        metadata = payload.get("metadata")
        return metadata if isinstance(metadata, dict) else payload
    return {}


def payload_rows(payload: Any) -> list[Any]:
    if isinstance(payload, list) and len(payload) >= 2 and isinstance(payload[1], list):
        return payload[1]
    if isinstance(payload, dict) and isinstance(payload.get("rows"), list):
        return payload["rows"]
    raise ValueError("Expected WDI payload [metadata, rows] or {'rows': [...]}")


def parse_wdi_payload(payload: Any) -> dict[SeriesKey, dict[int, float]]:
    series: dict[SeriesKey, dict[int, float]] = {}
    for row in payload_rows(payload):
        if not isinstance(row, dict):
            continue
        country_obj = row.get("country") if isinstance(row.get("country"), dict) else {}
        indicator_obj = row.get("indicator") if isinstance(row.get("indicator"), dict) else {}
        country_code = str(row.get("countryiso3code") or country_obj.get("iso3code") or country_obj.get("id") or "").strip()
        country_name = str(country_obj.get("value") or country_code).strip()
        indicator_id = str(indicator_obj.get("id") or "").strip()
        indicator_name = str(indicator_obj.get("value") or indicator_id).strip()
        value = as_float(row.get("value"))
        try:
            year = int(str(row.get("date", "")).strip())
        except (TypeError, ValueError):
            continue
        if not country_code or not indicator_id or value is None:
            continue
        key = SeriesKey(country_code, country_name, indicator_id, indicator_name)
        series.setdefault(key, {})[year] = value
    return series


def _source_from_payload(payload: Any) -> tuple[dict[str, Any], str | None]:
    metadata = payload_metadata(payload)
    source = metadata.get("oc133_source_separation", metadata.get("source_separation", {}))
    if isinstance(source, dict) and source:
        return dict(source), "snapshot_metadata"
    return {}, None


def _source_from_harvested_pack(root: Path) -> tuple[dict[str, Any], str | None]:
    path = root / HARVESTED_SOURCE_PACK_REL
    if not path.exists():
        return {}, None
    try:
        pack = read_json(path)
    except Exception:
        return {}, None
    if not isinstance(pack, dict):
        return {}, None
    source = pack.get("source_separation", {})
    if isinstance(source, dict) and source:
        return dict(source), HARVESTED_SOURCE_PACK_REL
    return {}, None


def extract_source_separation(root: Path, payload: Any) -> dict[str, Any]:
    source, source_ref = _source_from_payload(payload)
    if not source:
        source, source_ref = _source_from_harvested_pack(root)
    if not source:
        source = {}
        source_ref = None
    return {
        "mode": str(source.get("mode", "snapshot_replay")),
        "pre_target_lock": source.get("pre_target_lock") is True,
        "target_hidden_until_scoring": source.get("target_hidden_until_scoring") is True,
        "declared_before_scoring": source.get("declared_before_scoring") is True,
        "source_ref": source_ref or "none",
    }


def years_before(values_by_year: dict[int, float], target_year: int) -> list[int]:
    return sorted(year for year in values_by_year if year < target_year)


def history_for_year(values_by_year: dict[int, float], target_year: int) -> list[float]:
    return [values_by_year[year] for year in years_before(values_by_year, target_year)]


def formula_prediction(formula: Formula, history: list[float]) -> float | None:
    if len(history) < formula.min_history:
        return None
    try:
        value = float(formula.predictor(history))
    except Exception:
        return None
    return value if math.isfinite(value) else None


def formula_training_residuals(
    values_by_year: dict[int, float],
    target_year: int,
    formula: Formula,
) -> list[dict[str, Any]]:
    residuals: list[dict[str, Any]] = []
    for scoring_year in years_before(values_by_year, target_year):
        history = history_for_year(values_by_year, scoring_year)
        prediction = formula_prediction(formula, history)
        if prediction is None:
            continue
        observed = values_by_year[scoring_year]
        residuals.append(
            {
                "scoring_year": scoring_year,
                "prediction": prediction,
                "observed": observed,
                "absolute_residual": abs(prediction - observed),
            }
        )
    return residuals


def select_formula_for_target(
    values_by_year: dict[int, float],
    target_year: int,
) -> tuple[Formula | None, dict[str, Any], list[str]]:
    failures: list[str] = []
    scores: list[dict[str, Any]] = []
    best: Formula | None = None
    best_score = math.inf
    for formula in FORMULA_FAMILIES:
        residual_rows = formula_training_residuals(values_by_year, target_year, formula)
        residual_values = [float(row["absolute_residual"]) for row in residual_rows]
        mean_residual = sum(residual_values) / len(residual_values) if residual_values else math.inf
        max_residual = max(residual_values) if residual_values else None
        scores.append(
            {
                "formula_id": formula.id,
                "rule": formula.rule,
                "training_score_row_count": len(residual_values),
                "mean_abs_training_residual": None if mean_residual == math.inf else mean_residual,
                "max_abs_training_residual": max_residual,
            }
        )
        if len(residual_values) < MIN_TRAINING_SCORE_ROWS:
            continue
        if mean_residual < best_score:
            best = formula
            best_score = mean_residual
    if best is None:
        failures.append(f"FORMULA_SELECTION_INSUFFICIENT_TRAINING_ROWS::{target_year}")
    return (
        best,
        {
            "target_year": target_year,
            "target_rows_used_for_selection": False,
            "minimum_training_score_rows": MIN_TRAINING_SCORE_ROWS,
            "selection_metric": "mean absolute residual on strictly prior-year replay rows",
            "scores": scores,
            "selected_formula_id": best.id if best else None,
        },
        failures,
    )


def row_training_source(snapshot_ref: str, key: SeriesKey, training_years: list[int]) -> str:
    years = ",".join(str(year) for year in training_years)
    return f"{snapshot_ref}::{key.source_token()}::model_search_training_years={years}"


def row_target_source(snapshot_ref: str, key: SeriesKey, target_year: int) -> str:
    return f"{snapshot_ref}::{key.source_token()}::heldout_target_year={target_year}"


def build_replay_rows(
    series: dict[SeriesKey, dict[int, float]],
    snapshot_ref: str,
) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    failures: list[str] = []
    for key in sorted(series, key=lambda item: item.label()):
        values_by_year = series[key]
        for target_year in sorted(values_by_year):
            training_years = years_before(values_by_year, target_year)
            if len(training_years) < 2:
                continue
            formula, selection, selection_failures = select_formula_for_target(values_by_year, target_year)
            if formula is None:
                if len(training_years) >= max(item.min_history for item in FORMULA_FAMILIES):
                    failures.extend(f"{failure}::{key.source_token()}" for failure in selection_failures)
                continue
            history = history_for_year(values_by_year, target_year)
            prediction = formula_prediction(formula, history)
            if prediction is None:
                failures.append(f"FORMULA_PREDICTION_FAILED::{key.source_token()}::{target_year}::{formula.id}")
                continue
            observed = values_by_year[target_year]
            comparator_prediction = values_by_year[training_years[-1]]
            model_residual = abs(prediction - observed)
            comparator_residual = abs(comparator_prediction - observed)
            selected_training_scores = [
                row
                for row in selection["scores"]
                if row["formula_id"] == formula.id
            ]
            selected_score = selected_training_scores[0] if selected_training_scores else {}
            row_id = f"SYSTEMS-WDI-MODEL-SEARCH-{key.country_code}-{key.indicator_id}-{target_year}"
            row = {
                "observation_id": row_id,
                "country": f"{key.country_code}:{key.country_name}",
                "indicator": f"{key.indicator_id}:{key.indicator_name}",
                "training_years": training_years,
                "heldout_year": target_year,
                "training_source": row_training_source(snapshot_ref, key, training_years),
                "target_source": row_target_source(snapshot_ref, key, target_year),
                "selected_formula_id": formula.id,
                "formula": formula.rule,
                "formula_selection": selection,
                "predicted_value": prediction,
                "observed_value": observed,
                "comparator_baseline_id": "carry_forward_last_observation",
                "comparator_prediction": comparator_prediction,
                "model_residual": model_residual,
                "comparator_residual": comparator_residual,
                "uncertainty": {
                    "metric": "absolute residual",
                    "method": "max prior replay residual for selected formula",
                    "interval": [
                        0.0,
                        float(selected_score.get("max_abs_training_residual") or 0.0),
                    ],
                },
                "negative_control_id": f"systems-wdi-model-search-carry-forward::{row_id}",
                "negative_control_description": (
                    "pre-registered carry-forward comparator must have strictly larger absolute "
                    "heldout residual than the training-selected formula"
                ),
                "negative_control_rejected": comparator_residual > model_residual,
                "falsifier": (
                    "support fails if any heldout WDI row has comparator_residual <= model_residual "
                    "or if target mutation changes the selected formula"
                ),
                "row_hash_policy": ROW_HASH_POLICY,
            }
            row["row_hash"] = sha256_object({name: value for name, value in row.items() if name != "row_hash"})
            rows.append(row)
    return rows, ordered_unique(failures)


def selected_formula_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        formula_id = str(row.get("selected_formula_id", "unknown"))
        counts[formula_id] = counts.get(formula_id, 0) + 1
    return dict(sorted(counts.items()))


def validate_source_separation(source: dict[str, Any], rows: list[dict[str, Any]], requirements: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    allowed_modes = {str(mode) for mode in requirements.get("required_source_separation_modes", [])}
    if source.get("mode") not in allowed_modes:
        failures.append(f"SOURCE_SEPARATION_MODE_NOT_ALLOWED::{source.get('mode')}")
    if source.get("pre_target_lock") is not True:
        failures.append("PRE_TARGET_LOCK_REQUIRED")
    if source.get("target_hidden_until_scoring") is not True:
        failures.append("TARGET_HIDDEN_UNTIL_SCORING_REQUIRED")
    training_sources = [str(row.get("training_source", "")) for row in rows if row.get("training_source")]
    target_sources = [str(row.get("target_source", "")) for row in rows if row.get("target_source")]
    if not training_sources or not target_sources:
        failures.append("TRAINING_AND_TARGET_SOURCES_REQUIRED")
    if set(training_sources) & set(target_sources):
        failures.append("TRAINING_TARGET_SOURCE_OVERLAP")
    return ordered_unique(failures)


def validate_rows(rows: list[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    required = (
        "observation_id",
        "training_source",
        "target_source",
        "selected_formula_id",
        "formula",
        "predicted_value",
        "observed_value",
        "comparator_prediction",
        "model_residual",
        "comparator_residual",
        "negative_control_id",
        "falsifier",
        "row_hash",
    )
    for row in rows:
        row_id = str(row.get("observation_id", "unknown"))
        for field in required:
            if row.get(field) in (None, ""):
                failures.append(f"ROW_FIELD_MISSING::{row_id}::{field}")
        for field in ("predicted_value", "observed_value", "comparator_prediction", "model_residual", "comparator_residual"):
            if not is_finite_number(row.get(field)):
                failures.append(f"ROW_NUMERIC_INVALID::{row_id}::{field}")
        if row.get("training_source") == row.get("target_source"):
            failures.append(f"ROW_SOURCE_OVERLAP::{row_id}")
        if ((row.get("formula_selection") or {}).get("target_rows_used_for_selection")) is not False:
            failures.append(f"FORMULA_SELECTION_TARGET_LEAKAGE::{row_id}")
        expected_hash = sha256_object({name: value for name, value in row.items() if name != "row_hash"})
        if row.get("row_hash") != expected_hash:
            failures.append(f"ROW_HASH_MISMATCH::{row_id}")
        if row.get("negative_control_rejected") is not True:
            failures.append(f"NEGATIVE_CONTROL_NOT_REJECTED::{row_id}")
    return ordered_unique(failures)


def residual_summary(rows: list[dict[str, Any]]) -> dict[str, float]:
    model = [float(row["model_residual"]) for row in rows if is_finite_number(row.get("model_residual"))]
    comparator = [float(row["comparator_residual"]) for row in rows if is_finite_number(row.get("comparator_residual"))]
    model_mean = sum(model) / len(model) if model else 0.0
    comparator_mean = sum(comparator) / len(comparator) if comparator else 0.0
    return {
        "model": model_mean,
        "comparator": comparator_mean,
        "superiority_margin": comparator_mean - model_mean,
    }


def uncertainty_interval(rows: list[dict[str, Any]], model_mean: float) -> list[float]:
    residuals = [float(row["model_residual"]) for row in rows if is_finite_number(row.get("model_residual"))]
    if not residuals:
        return [0.0, 0.0]
    return [0.0, max([model_mean, *residuals])]


def build_pack(
    rows: list[dict[str, Any]],
    source: dict[str, Any],
    support_allowed: bool,
) -> dict[str, Any]:
    residuals = residual_summary(rows)
    negative_controls = [
        {
            "control_id": str(row["negative_control_id"]),
            "description": str(row["negative_control_description"]),
            "rejected": row.get("negative_control_rejected") is True,
        }
        for row in rows
    ]
    if not negative_controls:
        negative_controls = [
            {
                "control_id": "systems-wdi-model-search-no-heldout-rows",
                "description": "no replay rows were available for carry-forward negative control",
                "rejected": False,
            }
        ]
    return {
        "schema_id": grand_factory.EVIDENCE_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "capability_owner": CAPABILITY_OWNER,
        "evidence_pack_id": "OC133-SYSTEMS-WDI-MODEL-SEARCH-CANDIDATE",
        "domain": "systems",
        "source_separation": {
            "mode": source.get("mode", "snapshot_replay"),
            "pre_target_lock": source.get("pre_target_lock") is True,
            "target_hidden_until_scoring": source.get("target_hidden_until_scoring") is True,
            "training_sources": ordered_unique([str(row["training_source"]) for row in rows if row.get("training_source")]),
            "target_sources": ordered_unique([str(row["target_source"]) for row in rows if row.get("target_source")]),
        },
        "n": len(rows),
        "model_under_test": (
            "World Bank WDI preregistered formula-family search with per-target selection "
            "on strictly prior replay rows only"
        ),
        "comparator_baseline": {
            "name": "WDI carry-forward last-observation comparator",
            "prediction_rule": "predict each heldout target year as the immediately previous observed year",
            "pre_registered": True,
        },
        "uncertainty": {
            "metric": "mean absolute heldout residual",
            "method": "deterministic replay envelope over model residuals",
            "interval": uncertainty_interval(rows, residuals["model"]),
        },
        "residuals": residuals,
        "negative_controls": negative_controls,
        "falsifiers": ordered_unique([str(row["falsifier"]) for row in rows if row.get("falsifier")])
        or ["support fails when no heldout WDI replay rows are available"],
        "grand_toe_support_allowed": bool(support_allowed),
    }


def mutate_target_value(payload: Any, country_code: str, indicator_id: str, target_year: int, delta: float) -> Any:
    mutated = json.loads(json.dumps(payload, ensure_ascii=False))
    for row in payload_rows(mutated):
        if not isinstance(row, dict):
            continue
        country_obj = row.get("country") if isinstance(row.get("country"), dict) else {}
        indicator_obj = row.get("indicator") if isinstance(row.get("indicator"), dict) else {}
        row_country = str(row.get("countryiso3code") or country_obj.get("iso3code") or country_obj.get("id") or "").strip()
        row_indicator = str(indicator_obj.get("id") or "").strip()
        try:
            row_year = int(str(row.get("date", "")).strip())
        except (TypeError, ValueError):
            continue
        if row_country == country_code and row_indicator == indicator_id and row_year == target_year:
            value = as_float(row.get("value"))
            if value is not None:
                row["value"] = value + delta
                return mutated
    return mutated


def rebuild_matching_row(raw_payload: Any, snapshot_ref: str, original_row: dict[str, Any]) -> dict[str, Any] | None:
    series = parse_wdi_payload(raw_payload)
    target_year = int(original_row["heldout_year"])
    country_code = str(original_row["country"]).split(":", 1)[0]
    indicator_id = str(original_row["indicator"]).split(":", 1)[0]
    for key, values_by_year in series.items():
        if key.country_code == country_code and key.indicator_id == indicator_id:
            rows, _failures = build_replay_rows({key: values_by_year}, snapshot_ref)
            for row in rows:
                if int(row["heldout_year"]) == target_year:
                    return row
    return None


def build_tamper_tests(raw_payload: Any, snapshot_ref: str, rows: list[dict[str, Any]], pack: dict[str, Any]) -> list[dict[str, Any]]:
    if not rows:
        return [
            {
                "test_id": "systems-wdi-model-search-no-row-tamper-tests",
                "description": "tamper tests require at least one replay row",
                "passed": False,
            }
        ]
    target_checks: list[dict[str, Any]] = []
    sample_rows = rows if len(rows) <= 80 else [rows[0], rows[len(rows) // 2], rows[-1]]
    for row in sample_rows:
        observed = float(row["observed_value"])
        delta = max(1.0, abs(observed) * 1e-12)
        country_code = str(row["country"]).split(":", 1)[0]
        indicator_id = str(row["indicator"]).split(":", 1)[0]
        mutated = mutate_target_value(raw_payload, country_code, indicator_id, int(row["heldout_year"]), delta)
        rebuilt = rebuild_matching_row(mutated, snapshot_ref, row)
        target_checks.append(
            {
                "observation_id": row["observation_id"],
                "payload_hash_changed": sha256_object(mutated) != sha256_object(raw_payload),
                "row_hash_changed": rebuilt is not None and rebuilt.get("row_hash") != row.get("row_hash"),
                "selection_stable": rebuilt is not None and rebuilt.get("selected_formula_id") == row.get("selected_formula_id"),
                "prediction_stable": rebuilt is not None
                and abs(float(rebuilt.get("predicted_value", math.nan)) - float(row["predicted_value"])) <= 1e-9 * max(1.0, abs(float(row["predicted_value"]))),
            }
        )
    target_failures = [
        item["observation_id"]
        for item in target_checks
        if not (
            item["payload_hash_changed"]
            and item["row_hash_changed"]
            and item["selection_stable"]
            and item["prediction_stable"]
        )
    ]
    pack_hash = sha256_object(pack)
    mutated_pack = json.loads(json.dumps(pack, ensure_ascii=False))
    mutated_pack["n"] = int(mutated_pack.get("n", 0)) + 1
    return [
        {
            "test_id": "systems-wdi-model-search-target-mutation-changes-payload-hashes",
            "description": "mutating each sampled heldout target must change the canonical payload hash",
            "sample_total": len(target_checks),
            "failed_observation_ids": [
                item["observation_id"] for item in target_checks if not item["payload_hash_changed"]
            ],
            "passed": all(item["payload_hash_changed"] for item in target_checks),
        },
        {
            "test_id": "systems-wdi-model-search-target-mutation-changes-row-hashes",
            "description": "mutating each sampled heldout target must change the recomputed row hash",
            "sample_total": len(target_checks),
            "failed_observation_ids": [
                item["observation_id"] for item in target_checks if not item["row_hash_changed"]
            ],
            "passed": all(item["row_hash_changed"] for item in target_checks),
        },
        {
            "test_id": "systems-wdi-model-search-selection-target-leakage-control",
            "description": "mutating heldout target values must not change selected formulas or predictions for those same rows",
            "sample_total": len(target_checks),
            "failed_observation_ids": target_failures,
            "passed": not target_failures,
        },
        {
            "test_id": "systems-wdi-model-search-pack-hash-changes-on-pack-mutation",
            "description": "mutating candidate-pack content must change the candidate-pack hash",
            "passed": sha256_object(mutated_pack) != pack_hash,
        },
    ]


def blocker_work_orders(blockers: list[str], *, minimum_n: int, candidate_n: int) -> list[dict[str, Any]]:
    orders: list[dict[str, Any]] = []

    def add(order_id: str, blocker_match: str, action: str) -> None:
        matched = [blocker for blocker in blockers if blocker_match in blocker]
        if matched:
            orders.append(
                {
                    "work_order_id": order_id,
                    "status": "OPEN",
                    "triggered_by": matched,
                    "action": action,
                }
            )

    add(
        "OC133-SYSTEMS-WDI-MODEL-SEARCH-N",
        "N_BELOW_MINIMUM",
        f"Harvest or declare enough target-hidden WDI replay rows to reach N>={minimum_n}; current candidate_n={candidate_n}.",
    )
    add(
        "OC133-SYSTEMS-WDI-MODEL-SEARCH-SOURCE-SEPARATION",
        "SOURCE_SEPARATION",
        "Acquire or attach a source-separation declaration accepted by the grand gate before claiming support.",
    )
    add(
        "OC133-SYSTEMS-WDI-MODEL-SEARCH-NEGATIVE-CONTROLS",
        "NEGATIVE_CONTROL_NOT_REJECTED",
        "Revise the pre-registered systems formula family on training-only data or harvest broader systems targets; do not promote while any carry-forward control wins.",
    )
    add(
        "OC133-SYSTEMS-WDI-MODEL-SEARCH-COMPARATOR",
        "COMPARATOR_NOT_WORSE_THAN_MODEL",
        "Require aggregate comparator residual to remain strictly worse than model residual under the same metric.",
    )
    add(
        "OC133-SYSTEMS-WDI-MODEL-SEARCH-SUPERIORITY",
        "SUPERIORITY",
        "Keep the systems-domain blocker open until the candidate has positive residual superiority and all row controls pass.",
    )
    add(
        "OC133-SYSTEMS-WDI-MODEL-SEARCH-TAMPER",
        "TAMPER_TEST_FAILED",
        "Repair hash/tamper replay before any registry promotion.",
    )
    if not orders and blockers:
        orders.append(
            {
                "work_order_id": "OC133-SYSTEMS-WDI-MODEL-SEARCH-GENERIC",
                "status": "OPEN",
                "triggered_by": blockers,
                "action": "Resolve listed blockers and rerun the WDI model-search factory.",
            }
        )
    if not blockers:
        orders.append(
            {
                "work_order_id": "OC133-SYSTEMS-WDI-MODEL-SEARCH-REGISTRY-REVIEW",
                "status": "READY",
                "triggered_by": [],
                "action": "Candidate clears local gate; review before optional parent registry registration.",
            }
        )
    return orders


def build_formula_search_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "preregistered_formula_family": [
            {
                "formula_id": formula.id,
                "rule": formula.rule,
                "min_history": formula.min_history,
            }
            for formula in FORMULA_FAMILIES
        ],
        "selection_scope": "per target row; same-series years strictly earlier than heldout_year",
        "selection_metric": "mean absolute residual on prior replay rows",
        "target_rows_used_for_selection": False,
        "minimum_training_score_rows": MIN_TRAINING_SCORE_ROWS,
        "selected_formula_counts": selected_formula_counts(rows),
    }


def evaluate_wdi_payload(
    raw_payload: Any,
    *,
    root: Path,
    snapshot_ref: str,
    snapshot_sha256: str,
    requirements: dict[str, Any],
    requirement_failures: list[str] | None = None,
) -> dict[str, Any]:
    requirement_failures = requirement_failures or []
    minimum_n = int(requirements.get("minimum_per_domain_n", 20))
    blockers: list[str] = list(requirement_failures)
    source = extract_source_separation(root, raw_payload)

    try:
        series = parse_wdi_payload(raw_payload)
    except Exception as exc:
        series = {}
        blockers.append(f"SNAPSHOT_PARSE_FAILED::{exc}")

    rows, row_build_failures = build_replay_rows(series, snapshot_ref)
    source_failures = validate_source_separation(source, rows, requirements)
    row_failures = validate_rows(rows)

    if len(rows) < minimum_n:
        blockers.append(f"N_BELOW_MINIMUM::{len(rows)}/{minimum_n}")

    summary = residual_summary(rows)
    if summary["superiority_margin"] <= 0:
        blockers.append("HELDOUT_RESIDUAL_SUPERIORITY_NOT_MET")

    preliminary_blockers = ordered_unique([*blockers, *source_failures, *row_build_failures, *row_failures])
    preliminary_pack = build_pack(rows, source, support_allowed=not preliminary_blockers)
    tamper_tests = build_tamper_tests(raw_payload, snapshot_ref, rows, preliminary_pack)
    tamper_failures = [f"TAMPER_TEST_FAILED::{test['test_id']}" for test in tamper_tests if test.get("passed") is not True]

    candidate_support = not ordered_unique([*preliminary_blockers, *tamper_failures])
    candidate_pack = build_pack(rows, source, support_allowed=candidate_support)
    candidate_gate_failures = grand_factory.pack_failure_reasons(candidate_pack, requirements)
    support_allowed = candidate_support and not candidate_gate_failures
    pack = build_pack(rows, source, support_allowed=support_allowed)
    final_pack_failures = grand_factory.pack_failure_reasons(pack, requirements)
    blockers = ordered_unique([*preliminary_blockers, *tamper_failures, *candidate_gate_failures])
    formula_search = build_formula_search_summary(rows)
    pack_sha256 = sha256_object(pack)
    task_rows_hash = sha256_object([row.get("row_hash") for row in rows])
    work_orders = blocker_work_orders(blockers, minimum_n=minimum_n, candidate_n=len(rows))

    protocol = {
        "schema_id": PROTOCOL_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "blocker_id": "grand_toe_empirical_superiority",
        "candidate_pack_ref": PACK_REL,
        "candidate_pack_sha256": pack_sha256,
        "candidate_pack_hash_policy": OBJECT_HASH_POLICY,
        "snapshot_ref": snapshot_ref,
        "snapshot_sha256": snapshot_sha256,
        "snapshot_hash_policy": SNAPSHOT_HASH_POLICY,
        "source_separation_claim": source,
        "minimum_n": minimum_n,
        "candidate_n": len(rows),
        "formula_search": formula_search,
        "comparator_baseline": {
            "name": "WDI carry-forward last-observation comparator",
            "pre_registered": True,
        },
        "residual_metric": "absolute residual; aggregate is mean absolute residual",
        "negative_control_policy": "reject support unless every heldout row has comparator_residual > model_residual",
        "tamper_policy": "heldout target mutation must change row hashes without changing same-row formula selection",
        "required_protocol_steps": [
            "freeze the WDI snapshot and record its hash",
            "load the formula family before any target scoring",
            "select formulas using only same-series years strictly earlier than each heldout target year",
            "score each heldout target once and record row hashes",
            "compare against the preregistered carry-forward baseline under the same residual metric",
            "reject support unless N, source separation, residual superiority, all negative controls, falsifiers, and tamper tests pass",
        ],
        "blockers": blockers,
        "next_work_orders": work_orders,
    }
    tasks = {
        "schema_id": TASKS_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "snapshot_ref": snapshot_ref,
        "snapshot_sha256": snapshot_sha256,
        "snapshot_payload_sha256": sha256_object(raw_payload),
        "source_separation_claim": source,
        "series_total": len(series),
        "row_total": len(rows),
        "row_hash_policy": ROW_HASH_POLICY,
        "row_hashes_sha256": task_rows_hash,
        "formula_search": formula_search,
        "rows": rows,
        "blockers": blockers,
        "next_work_orders": work_orders,
    }
    report = {
        "schema_id": REPORT_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "blocker_id": "grand_toe_empirical_superiority",
        "snapshot_ref": snapshot_ref,
        "snapshot_sha256": snapshot_sha256,
        "snapshot_hash_policy": SNAPSHOT_HASH_POLICY,
        "source_separation_claim": source,
        "candidate_pack_ref": PACK_REL,
        "candidate_pack_sha256": pack_sha256,
        "candidate_pack_hash_policy": OBJECT_HASH_POLICY,
        "protocol_ref": PROTOCOL_REL,
        "tasks_ref": TASKS_REL,
        "minimum_n": minimum_n,
        "candidate_n": len(rows),
        "missing_n": max(0, minimum_n - len(rows)),
        "series_total": len(series),
        "formula_search": formula_search,
        "residuals": pack["residuals"],
        "negative_control_total": len(pack["negative_controls"]),
        "negative_control_rejected_total": sum(1 for row in pack["negative_controls"] if row.get("rejected") is True),
        "source_validation_failures": source_failures,
        "row_validation_failures": ordered_unique([*row_build_failures, *row_failures]),
        "candidate_gate_failures": candidate_gate_failures,
        "pack_failure_reasons": final_pack_failures,
        "tamper_tests": tamper_tests,
        "tamper_test_total": len(tamper_tests),
        "candidate_pack_total": 1,
        "valid_pack_total": 1 if support_allowed else 0,
        "blocked_candidate_pack_total": 0 if support_allowed else 1,
        "blockers": blockers,
        "open_blocker_total": len(blockers),
        "blocker_total": len(blockers),
        "blocked_total": len(blockers),
        "next_work_orders": work_orders,
        "next_work_order_total": len(work_orders),
        "grand_toe_support_allowed": support_allowed,
        "verdict": "READY_FOR_PARENT_REGISTRY_REVIEW" if support_allowed else "BLOCKED",
        "no_send": True,
        "publish_allowed": False,
        "journal_submissions_allowed": False,
    }
    return {
        "candidate_pack": pack,
        "protocol": protocol,
        "tasks": tasks,
        "report": report,
    }


def build_missing_snapshot_payload(root: Path, snapshot_ref: str, requirements: dict[str, Any], requirement_failures: list[str]) -> dict[str, Any]:
    source = {
        "mode": "snapshot_replay",
        "pre_target_lock": False,
        "target_hidden_until_scoring": False,
        "declared_before_scoring": False,
        "source_ref": "none",
    }
    blockers = ordered_unique(["SNAPSHOT_MISSING", *requirement_failures])
    pack = build_pack([], source, support_allowed=False)
    work_orders = blocker_work_orders(blockers, minimum_n=int(requirements.get("minimum_per_domain_n", 20)), candidate_n=0)
    report = {
        "schema_id": REPORT_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "snapshot_ref": snapshot_ref,
        "candidate_pack_ref": PACK_REL,
        "candidate_pack_sha256": sha256_object(pack),
        "minimum_n": int(requirements.get("minimum_per_domain_n", 20)),
        "candidate_n": 0,
        "missing_n": int(requirements.get("minimum_per_domain_n", 20)),
        "candidate_pack_total": 1,
        "valid_pack_total": 0,
        "blocked_candidate_pack_total": 1,
        "blockers": blockers,
        "open_blocker_total": len(blockers),
        "blocker_total": len(blockers),
        "next_work_orders": work_orders,
        "grand_toe_support_allowed": False,
        "verdict": "BLOCKED",
        "no_send": True,
        "publish_allowed": False,
    }
    return {
        "candidate_pack": pack,
        "protocol": {
            "schema_id": PROTOCOL_SCHEMA_ID,
            "release_id": RELEASE_ID,
            "version": VERSION,
            "capability_owner": CAPABILITY_OWNER,
            "snapshot_ref": snapshot_ref,
            "blockers": blockers,
            "next_work_orders": work_orders,
        },
        "tasks": {
            "schema_id": TASKS_SCHEMA_ID,
            "release_id": RELEASE_ID,
            "version": VERSION,
            "capability_owner": CAPABILITY_OWNER,
            "snapshot_ref": snapshot_ref,
            "rows": [],
            "blockers": blockers,
            "next_work_orders": work_orders,
        },
        "report": report,
    }


def build_payload(root: Path | None = None, snapshot_ref: str | None = None) -> dict[str, Any]:
    root = (root or repo_root()).resolve()
    selected_snapshot_ref = choose_snapshot_ref(root, snapshot_ref)
    requirements, requirement_failures = load_requirements(root)
    snapshot_path = resolve_under_root(root, selected_snapshot_ref)
    if not snapshot_path.exists():
        return build_missing_snapshot_payload(root, selected_snapshot_ref, requirements, requirement_failures)
    raw_payload = read_json(snapshot_path)
    return evaluate_wdi_payload(
        raw_payload,
        root=root,
        snapshot_ref=selected_snapshot_ref,
        snapshot_sha256=sha256_file_text(snapshot_path),
        requirements=requirements,
        requirement_failures=requirement_failures,
    )


def render_readme(payload: dict[str, Any]) -> str:
    report = payload["report"]
    lines = [
        "# Systems WDI Model-Search Factory",
        "",
        f"Verdict: `{report.get('verdict')}`",
        f"Grand TOE support allowed: `{str(report.get('grand_toe_support_allowed')).lower()}`",
        f"Snapshot: `{report.get('snapshot_ref')}`",
        f"Rows: `{report.get('candidate_n', 0)}`",
        f"Minimum N: `{report.get('minimum_n', 0)}`",
        "",
        "This replay factory locks a WDI formula family, selects formulas on prior-year training rows only, scores heldout target years, checks carry-forward comparator residuals, emits row/candidate hashes, and blocks support unless the existing grand empirical gate is satisfied.",
        "",
        "## Open Blockers",
    ]
    blockers = report.get("blockers", [])
    if blockers:
        lines.extend(f"- `{blocker}`" for blocker in blockers)
    else:
        lines.append("- `none`")
    lines.extend(["", "## Next Work Orders"])
    for order in report.get("next_work_orders", []):
        lines.append(f"- `{order['work_order_id']}`: {order['action']}")
    lines.extend(["", "## Tamper Tests"])
    for test in report.get("tamper_tests", []):
        lines.append(f"- `{test['test_id']}`: `{test['passed']}`")
    return "\n".join(lines) + "\n"


def write_outputs(root: Path | None = None, snapshot_ref: str | None = None) -> dict[str, Any]:
    root = (root or repo_root()).resolve()
    payload = build_payload(root, snapshot_ref=snapshot_ref)
    write_json(root / PACK_REL, payload["candidate_pack"])
    write_json(root / REPORT_REL, payload["report"])
    write_json(root / PROTOCOL_REL, payload["protocol"])
    write_json(root / TASKS_REL, payload["tasks"])
    write_text(root / README_REL, render_readme(payload))
    return payload


def check_stored(root: Path | None = None, snapshot_ref: str | None = None) -> list[str]:
    root = (root or repo_root()).resolve()
    expected = build_payload(root, snapshot_ref=snapshot_ref)
    checks = [
        (PACK_REL, expected["candidate_pack"]),
        (REPORT_REL, expected["report"]),
        (PROTOCOL_REL, expected["protocol"]),
        (TASKS_REL, expected["tasks"]),
    ]
    failures: list[str] = []
    for rel_path, expected_payload in checks:
        path = root / rel_path
        if not path.exists():
            failures.append(f"missing::{rel_path}")
            continue
        if read_json(path) != expected_payload:
            failures.append(f"mismatch::{rel_path}")
    readme_path = root / README_REL
    if not readme_path.exists():
        failures.append(f"missing::{README_REL}")
    elif readme_path.read_text(encoding="utf-8") != render_readme(expected):
        failures.append(f"mismatch::{README_REL}")
    return failures


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build OC133 systems WDI model-search replay artifacts.")
    parser.add_argument("--root", default=str(repo_root()), help="repository root")
    parser.add_argument("--snapshot-ref", default=None, help="WDI official snapshot reference")
    parser.add_argument("--write", action="store_true", help="write report, protocol, tasks, pack, and README")
    parser.add_argument("--check", action="store_true", help="check persisted artifacts against recomputation")
    parser.add_argument("--allow-blocked-exit-zero", action="store_true", help="exit zero when the candidate is blocked")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    if args.check:
        failures = check_stored(root, snapshot_ref=args.snapshot_ref)
        if failures:
            for failure in failures:
                print(f"ERROR: {failure}")
            return 1
        print(json.dumps({"status": "ok", "checked": [PACK_REL, REPORT_REL, PROTOCOL_REL, TASKS_REL, README_REL]}, indent=2))
        return 0
    payload = write_outputs(root, snapshot_ref=args.snapshot_ref) if args.write else build_payload(root, snapshot_ref=args.snapshot_ref)
    print(json.dumps(payload["report"], ensure_ascii=False, indent=2))
    if payload["report"].get("grand_toe_support_allowed") is not True and not args.allow_blocked_exit_zero:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
