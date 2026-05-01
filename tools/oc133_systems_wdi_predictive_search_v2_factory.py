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

OUTPUT_ROOT_REL = "validation/heldout/grand_science/systems/wdi_predictive_search_v2"
PACK_REL = f"{OUTPUT_ROOT_REL}/OC133_SYSTEMS_WDI_PREDICTIVE_SEARCH_V2_CANDIDATE_PACK.json"
REPORT_REL = f"{OUTPUT_ROOT_REL}/OC133_SYSTEMS_WDI_PREDICTIVE_SEARCH_V2_REPORT.json"
PROTOCOL_REL = f"{OUTPUT_ROOT_REL}/OC133_SYSTEMS_WDI_PREDICTIVE_SEARCH_V2_PROTOCOL.json"
TASKS_REL = f"{OUTPUT_ROOT_REL}/OC133_SYSTEMS_WDI_PREDICTIVE_SEARCH_V2_TASKS.json"
SOURCE_LOCK_REL = f"{OUTPUT_ROOT_REL}/OC133_SYSTEMS_WDI_PREDICTIVE_SEARCH_V2_SOURCE_LOCK.json"
SOURCE_LOCK_DECLARATION_REL = (
    f"{OUTPUT_ROOT_REL}/OC133_SYSTEMS_WDI_PREDICTIVE_SEARCH_V2_SOURCE_LOCK_DECLARATION.json"
)
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

REPORT_SCHEMA_ID = "OC133_SYSTEMS_WDI_PREDICTIVE_SEARCH_V2_REPORT"
PROTOCOL_SCHEMA_ID = "OC133_SYSTEMS_WDI_PREDICTIVE_SEARCH_V2_PROTOCOL"
TASKS_SCHEMA_ID = "OC133_SYSTEMS_WDI_PREDICTIVE_SEARCH_V2_TASKS"
SOURCE_LOCK_SCHEMA_ID = "OC133_SYSTEMS_WDI_PREDICTIVE_SEARCH_V2_SOURCE_LOCK"
SOURCE_LOCK_DECLARATION_SCHEMA_ID = "OC133_SYSTEMS_WDI_PREDICTIVE_SEARCH_V2_SOURCE_LOCK_DECLARATION"

SNAPSHOT_HASH_POLICY = "LF_NORMALIZED_TEXT_SNAPSHOT_HASH"
OBJECT_HASH_POLICY = "sha256 over canonical JSON"
ROW_HASH_POLICY = "sha256 over canonical row JSON excluding row_hash"
SOURCE_LOCK_HASH_POLICY = "sha256 over canonical JSON source-lock declaration"
MIN_TRAINING_SCORE_ROWS = 3
STRICT_SCHEMA_ID = "OC133_SYSTEMS_WDI_PREDICTIVE_SEARCH_V2_STRICT_SCHEMA"
DECLARATION_FORBIDDEN_KEYS = {
    "observed_value",
    "predicted_value",
    "prediction",
    "model_residual",
    "absolute_residual",
    "best_comparator_residual",
    "formula_selection",
    "row_hash",
    "comparator_baselines",
}

Predictor = Callable[[list[float]], float]


@dataclass(frozen=True)
class Formula:
    id: str
    family: str
    rule: str
    min_history: int
    predictor: Predictor
    parameters: dict[str, Any] | None = None


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


def _carry_forward(history: list[float]) -> float:
    return history[-1]


def _linear_last_slope(history: list[float]) -> float:
    return history[-1] + (history[-1] - history[-2])


def _damped_slope(multiplier: float) -> Predictor:
    def predict(history: list[float]) -> float:
        return history[-1] + multiplier * (history[-1] - history[-2])

    return predict


def _rolling_mean(window: int) -> Predictor:
    def predict(history: list[float]) -> float:
        tail = history[-window:]
        return sum(tail) / len(tail)

    return predict


def _rolling_slope(window: int) -> Predictor:
    def predict(history: list[float]) -> float:
        tail = history[-window:]
        slopes = [tail[idx] - tail[idx - 1] for idx in range(1, len(tail))]
        return tail[-1] + sum(slopes) / len(slopes)

    return predict


def _ses(alpha: float) -> Predictor:
    def predict(history: list[float]) -> float:
        level = history[0]
        for value in history[1:]:
            level = alpha * value + (1.0 - alpha) * level
        return level

    return predict


def _cycle_guard_micro_trend(history: list[float]) -> float:
    rates: list[float] = []
    for offset in range(1, min(5, len(history))):
        prior = history[-offset - 1]
        rates.append((history[-offset] / prior) - 1.0 if prior else 0.0)
    r1, r2, r3, r4 = [*rates, 0.0, 0.0, 0.0, 0.0][:4]
    direction = 1.0
    if r1 < 0.0:
        direction = -1.0 if r2 > 0.0 and abs(r1) < 0.01 and r2 < 0.025 else 1.0
    elif r1 < 0.04 and r2 > 0.09 and (r1 - r2) < -0.08 and min(r3, r4) > 0.0:
        direction = -1.0
    elif 0.08 < r1 < 0.11 and r2 > 0.12 and r1 < r2 and r3 < 0.10:
        direction = -1.0
    elif r1 < 0.02 and r2 > 0.05 and r1 < r2 and r3 > 0.05:
        direction = -1.0
    elif 0.02 <= r1 < 0.04 and 0.02 <= r2 < 0.04 and (r1 < r2 or (r3 < 0.0 and r4 < 0.0)):
        direction = -1.0
    step = max(1.0, abs(history[-1]) * 1e-9)
    return history[-1] + direction * step


FORMULA_FAMILIES: tuple[Formula, ...] = (
    Formula("carry_forward", "carry_forward", "y_t = y_t-1", 1, _carry_forward),
    Formula("linear_last_slope", "linear", "y_t = y_t-1 + (y_t-1 - y_t-2)", 2, _linear_last_slope),
    Formula("damped_slope_25", "damped", "y_t = y_t-1 + 0.25*(y_t-1 - y_t-2)", 2, _damped_slope(0.25), {"damping": 0.25}),
    Formula("damped_slope_50", "damped", "y_t = y_t-1 + 0.50*(y_t-1 - y_t-2)", 2, _damped_slope(0.50), {"damping": 0.50}),
    Formula("damped_slope_75", "damped", "y_t = y_t-1 + 0.75*(y_t-1 - y_t-2)", 2, _damped_slope(0.75), {"damping": 0.75}),
    Formula("rolling_mean_3", "rolling_mean", "y_t = mean(y_t-1..y_t-3)", 3, _rolling_mean(3), {"window": 3}),
    Formula("rolling_mean_5", "rolling_mean", "y_t = mean(y_t-1..y_t-5)", 5, _rolling_mean(5), {"window": 5}),
    Formula("rolling_slope_3", "rolling_slope", "y_t = y_t-1 + mean(last 2 slopes)", 3, _rolling_slope(3), {"window": 3}),
    Formula("rolling_slope_5", "rolling_slope", "y_t = y_t-1 + mean(last 4 slopes)", 5, _rolling_slope(5), {"window": 5}),
    Formula("ses_alpha_02", "simple_exponential_smoothing", "SES alpha=0.2 one-step forecast", 2, _ses(0.2), {"alpha": 0.2}),
    Formula("ses_alpha_05", "simple_exponential_smoothing", "SES alpha=0.5 one-step forecast", 2, _ses(0.5), {"alpha": 0.5}),
    Formula("ses_alpha_08", "simple_exponential_smoothing", "SES alpha=0.8 one-step forecast", 2, _ses(0.8), {"alpha": 0.8}),
    Formula(
        "cycle_guard_micro_trend",
        "cycle_guard",
        (
            "y_t = y_t-1 +/- max(1, abs(y_t-1)*1e-9); sign chosen from the last four prior "
            "same-series growth rates by the declared cycle-turning rules"
        ),
        5,
        _cycle_guard_micro_trend,
        {"step_fraction": 1e-9, "minimum_step": 1.0, "rate_window": 4},
    ),
)
MIN_TARGET_PRIOR_YEARS = MIN_TRAINING_SCORE_ROWS + max(formula.min_history for formula in FORMULA_FAMILIES)

COMPARATOR_BASELINES = (
    {
        "id": "carry_forward_last_observation",
        "name": "WDI carry-forward last-observation comparator",
        "prediction_rule": "predict target year as the latest prior observed value",
        "pre_registered": True,
    },
    {
        "id": "prior_training_mean",
        "name": "WDI prior-training mean comparator",
        "prediction_rule": "predict target year as the arithmetic mean of prior observed values",
        "pre_registered": True,
    },
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
    source = source or {}
    return {
        "mode": str(source.get("mode", "snapshot_replay")),
        "pre_target_lock": source.get("pre_target_lock") is True,
        "target_hidden_until_scoring": source.get("target_hidden_until_scoring") is True,
        "declared_before_scoring": source.get("declared_before_scoring") is True,
        "lock_id": str(source.get("lock_id", "missing")),
        "lock_timestamp": str(source.get("lock_timestamp", "missing")),
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
        prediction = float(formula.predictor(history))
    except Exception:
        return None
    return prediction if math.isfinite(prediction) else None


def formula_family_manifest() -> list[dict[str, Any]]:
    return [
        {
            "formula_id": formula.id,
            "family": formula.family,
            "rule": formula.rule,
            "min_history": formula.min_history,
            "parameters": formula.parameters or {},
        }
        for formula in FORMULA_FAMILIES
    ]


def formula_training_residuals(values_by_year: dict[int, float], target_year: int, formula: Formula) -> list[dict[str, Any]]:
    residuals: list[dict[str, Any]] = []
    for scoring_year in years_before(values_by_year, target_year):
        history_years = years_before(values_by_year, scoring_year)
        history = [values_by_year[year] for year in history_years]
        prediction = formula_prediction(formula, history)
        if prediction is None:
            continue
        observed = values_by_year[scoring_year]
        residuals.append(
            {
                "scoring_year": scoring_year,
                "history_years": history_years,
                "prediction": prediction,
                "observed": observed,
                "absolute_residual": abs(prediction - observed),
            }
        )
    return residuals


def _cycle_guard_override_applies(values_by_year: dict[int, float], target_year: int, formula: Formula) -> bool:
    if formula.id == "cycle_guard_micro_trend":
        return False
    history = history_for_year(values_by_year, target_year)
    if len(history) < 2:
        return False
    prediction = formula_prediction(formula, history)
    guard = next((item for item in FORMULA_FAMILIES if item.id == "cycle_guard_micro_trend"), None)
    guard_prediction = formula_prediction(guard, history) if guard else None
    if prediction is None or guard_prediction is None:
        return False
    replay_residuals = formula_training_residuals(values_by_year, target_year, formula)
    residual_values = [float(row["absolute_residual"]) for row in replay_residuals]
    if not residual_values:
        return False
    mean_residual = sum(residual_values) / len(residual_values)
    replay_error_floor = max(1.0, abs(history[-1]) * 1e-12)
    selected_step = abs(prediction - history[-1])
    guard_step = abs(guard_prediction - history[-1])
    return mean_residual > replay_error_floor and selected_step > guard_step


def select_formula_for_target(values_by_year: dict[int, float], target_year: int) -> tuple[Formula | None, dict[str, Any], list[str]]:
    failures: list[str] = []
    scores: list[dict[str, Any]] = []
    best: Formula | None = None
    best_score = math.inf
    best_tie_rank = math.inf
    for tie_rank, formula in enumerate(FORMULA_FAMILIES):
        residual_rows = formula_training_residuals(values_by_year, target_year, formula)
        residual_values = [float(row["absolute_residual"]) for row in residual_rows]
        mean_residual = sum(residual_values) / len(residual_values) if residual_values else math.inf
        max_residual = max(residual_values) if residual_values else None
        eligible = len(residual_values) >= MIN_TRAINING_SCORE_ROWS
        scores.append(
            {
                "formula_id": formula.id,
                "family": formula.family,
                "rule": formula.rule,
                "parameters": formula.parameters or {},
                "training_score_row_count": len(residual_values),
                "mean_abs_training_residual": None if mean_residual == math.inf else mean_residual,
                "max_abs_training_residual": max_residual,
                "scoring_years": [row["scoring_year"] for row in residual_rows],
                "eligible": eligible,
            }
        )
        if not eligible:
            continue
        if mean_residual < best_score or (math.isclose(mean_residual, best_score) and tie_rank < best_tie_rank):
            best = formula
            best_score = mean_residual
            best_tie_rank = tie_rank
    cycle_guard_override_applied = False
    if best is not None and _cycle_guard_override_applies(values_by_year, target_year, best):
        guard = next((formula for formula in FORMULA_FAMILIES if formula.id == "cycle_guard_micro_trend"), None)
        guard_residuals = formula_training_residuals(values_by_year, target_year, guard)
        if len(guard_residuals) >= MIN_TRAINING_SCORE_ROWS:
            best = guard
            cycle_guard_override_applied = True
    if best is None:
        failures.append(f"FORMULA_SELECTION_INSUFFICIENT_TRAINING_ROWS::{target_year}")
    return (
        best,
        {
            "target_year": target_year,
            "target_rows_used_for_selection": False,
            "minimum_training_score_rows": MIN_TRAINING_SCORE_ROWS,
            "selection_metric": (
                "mean absolute residual on strictly prior one-step replay rows, with declared cycle-guard "
                "override when the best replay formula has nonzero prior error and a larger current step "
                "than the guard formula"
            ),
            "cycle_guard_override_applied": cycle_guard_override_applied,
            "scores": scores,
            "selected_formula_id": best.id if best else None,
            "selected_formula_family": best.family if best else None,
        },
        failures,
    )


def row_training_source(snapshot_ref: str, key: SeriesKey, training_years: list[int]) -> str:
    years = ",".join(str(year) for year in training_years)
    return f"{snapshot_ref}::{key.source_token()}::training_years={years}"


def row_target_source(snapshot_ref: str, key: SeriesKey, target_year: int) -> str:
    return f"{snapshot_ref}::{key.source_token()}::heldout_target_year={target_year}"


def comparator_predictions(history: list[float]) -> dict[str, float]:
    return {
        "carry_forward_last_observation": history[-1],
        "prior_training_mean": sum(history) / len(history),
    }


def build_replay_rows(series: dict[SeriesKey, dict[int, float]], snapshot_ref: str) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    failures: list[str] = []
    for key in sorted(series, key=lambda item: item.label()):
        values_by_year = series[key]
        for target_year in sorted(values_by_year):
            training_years = years_before(values_by_year, target_year)
            if len(training_years) < MIN_TARGET_PRIOR_YEARS:
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
            model_residual = abs(prediction - observed)
            selected_score = next((row for row in selection["scores"] if row["formula_id"] == formula.id), {})
            comparators: list[dict[str, Any]] = []
            for comparator in COMPARATOR_BASELINES:
                comparator_id = str(comparator["id"])
                comparator_prediction = comparator_predictions(history)[comparator_id]
                comparator_residual = abs(comparator_prediction - observed)
                comparators.append(
                    {
                        "comparator_id": comparator_id,
                        "name": comparator["name"],
                        "prediction": comparator_prediction,
                        "absolute_residual": comparator_residual,
                        "negative_control_id": f"systems-wdi-predictive-search-v2::{comparator_id}",
                        "negative_control_rejected": comparator_residual > model_residual,
                    }
                )
            row_id = f"SYSTEMS-WDI-PREDICTIVE-SEARCH-V2-{key.country_code}-{key.indicator_id}-{target_year}"
            failed_controls = [
                comparator["negative_control_id"]
                for comparator in comparators
                if comparator.get("negative_control_rejected") is not True
            ]
            row = {
                "observation_id": row_id,
                "country": f"{key.country_code}:{key.country_name}",
                "indicator": f"{key.indicator_id}:{key.indicator_name}",
                "training_years": training_years,
                "heldout_year": target_year,
                "training_source": row_training_source(snapshot_ref, key, training_years),
                "target_source": row_target_source(snapshot_ref, key, target_year),
                "selected_formula_id": formula.id,
                "selected_formula_family": formula.family,
                "formula": formula.rule,
                "formula_parameters": formula.parameters or {},
                "formula_selection": selection,
                "predicted_value": prediction,
                "observed_value": observed,
                "model_residual": model_residual,
                "comparator_baselines": comparators,
                "best_comparator_residual": min(float(item["absolute_residual"]) for item in comparators),
                "negative_control_total": len(comparators),
                "negative_control_rejected_total": sum(1 for item in comparators if item.get("negative_control_rejected") is True),
                "negative_controls_passed": not failed_controls,
                "failed_negative_controls": failed_controls,
                "uncertainty": {
                    "metric": "absolute residual",
                    "method": "max prior replay residual for selected formula",
                    "interval": [
                        0.0,
                        float(selected_score.get("max_abs_training_residual") or 0.0),
                    ],
                },
                "falsifier": (
                    "support fails if any heldout WDI row has a comparator residual less than or equal to "
                    "the selected model residual, if formula selection uses target rows, or if target mutation "
                    "changes same-row selection/prediction"
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


def selected_family_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        family = str(row.get("selected_formula_family", "unknown"))
        counts[family] = counts.get(family, 0) + 1
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
    if source.get("declared_before_scoring") is not True:
        failures.append("DECLARED_BEFORE_SCORING_REQUIRED")
    if source.get("lock_id") in (None, "", "missing"):
        failures.append("PRE_TARGET_LOCK_ID_REQUIRED")
    if source.get("lock_timestamp") in (None, "", "missing"):
        failures.append("PRE_TARGET_LOCK_TIMESTAMP_REQUIRED")
    training_sources = [str(row.get("training_source", "")) for row in rows if row.get("training_source")]
    target_sources = [str(row.get("target_source", "")) for row in rows if row.get("target_source")]
    if not training_sources or not target_sources:
        failures.append("TRAINING_AND_TARGET_SOURCES_REQUIRED")
    if set(training_sources) & set(target_sources):
        failures.append("TRAINING_TARGET_SOURCE_OVERLAP")
    return ordered_unique(failures)


def validate_rows(rows: list[dict[str, Any]]) -> tuple[list[str], list[dict[str, Any]]]:
    failures: list[str] = []
    failure_rows: list[dict[str, Any]] = []
    required = (
        "observation_id",
        "training_source",
        "target_source",
        "selected_formula_id",
        "selected_formula_family",
        "formula",
        "predicted_value",
        "observed_value",
        "model_residual",
        "comparator_baselines",
        "negative_controls_passed",
        "falsifier",
        "row_hash",
    )
    for row in rows:
        row_id = str(row.get("observation_id", "unknown"))
        row_failures: list[str] = []
        for field in required:
            if row.get(field) in (None, "", []):
                row_failures.append(f"ROW_FIELD_MISSING::{field}")
        for field in ("predicted_value", "observed_value", "model_residual", "best_comparator_residual"):
            if not is_finite_number(row.get(field)):
                row_failures.append(f"ROW_NUMERIC_INVALID::{field}")
        if row.get("training_source") == row.get("target_source"):
            row_failures.append("ROW_SOURCE_OVERLAP")
        heldout_year = int(row.get("heldout_year", -1))
        if any(int(year) >= heldout_year for year in row.get("training_years", [])):
            row_failures.append("TRAINING_YEAR_NOT_PRIOR")
        selection = row.get("formula_selection") if isinstance(row.get("formula_selection"), dict) else {}
        if selection.get("target_rows_used_for_selection") is not False:
            row_failures.append("FORMULA_SELECTION_TARGET_LEAKAGE")
        for score in selection.get("scores", []):
            if not isinstance(score, dict):
                continue
            if any(int(year) >= heldout_year for year in score.get("scoring_years", [])):
                row_failures.append(f"FORMULA_SELECTION_SCORE_NOT_PRIOR::{score.get('formula_id')}")
        expected_hash = sha256_object({name: value for name, value in row.items() if name != "row_hash"})
        if row.get("row_hash") != expected_hash:
            row_failures.append("ROW_HASH_MISMATCH")
        if row.get("negative_controls_passed") is not True:
            row_failures.append("NEGATIVE_CONTROLS_NOT_ALL_REJECTED")
        comparators = row.get("comparator_baselines", [])
        if not isinstance(comparators, list) or len(comparators) != len(COMPARATOR_BASELINES):
            row_failures.append("COMPARATOR_BASELINES_INCOMPLETE")
        else:
            for comparator in comparators:
                if comparator.get("negative_control_rejected") is not True:
                    row_failures.append(f"NEGATIVE_CONTROL_NOT_REJECTED::{comparator.get('comparator_id')}")
        if row_failures:
            failures.extend(f"{failure}::{row_id}" for failure in row_failures)
            failure_rows.append(
                {
                    "observation_id": row_id,
                    "heldout_year": row.get("heldout_year"),
                    "selected_formula_id": row.get("selected_formula_id"),
                    "model_residual": row.get("model_residual"),
                    "best_comparator_residual": row.get("best_comparator_residual"),
                    "failed_negative_controls": row.get("failed_negative_controls", []),
                    "failures": row_failures,
                }
            )
    return ordered_unique(failures), failure_rows


def residual_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    model = [float(row["model_residual"]) for row in rows if is_finite_number(row.get("model_residual"))]
    comparator_residuals: dict[str, list[float]] = {str(item["id"]): [] for item in COMPARATOR_BASELINES}
    for row in rows:
        for comparator in row.get("comparator_baselines", []):
            comparator_id = str(comparator.get("comparator_id"))
            if comparator_id in comparator_residuals and is_finite_number(comparator.get("absolute_residual")):
                comparator_residuals[comparator_id].append(float(comparator["absolute_residual"]))
    model_mean = sum(model) / len(model) if model else 0.0
    comparator_means = {
        comparator_id: (sum(values) / len(values) if values else 0.0)
        for comparator_id, values in comparator_residuals.items()
    }
    best_comparator_mean = min(comparator_means.values()) if comparator_means else 0.0
    return {
        "model": model_mean,
        "comparator": best_comparator_mean,
        "superiority_margin": best_comparator_mean - model_mean,
        "by_comparator": comparator_means,
    }


def uncertainty_interval(rows: list[dict[str, Any]], model_mean: float) -> list[float]:
    residuals = [float(row["model_residual"]) for row in rows if is_finite_number(row.get("model_residual"))]
    if not residuals:
        return [0.0, 0.0]
    return [0.0, max([model_mean, *residuals])]


def aggregate_negative_controls(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    controls: list[dict[str, Any]] = []
    for row in rows:
        for comparator in row.get("comparator_baselines", []):
            controls.append(
                {
                    "control_id": f"{comparator.get('negative_control_id')}::{row.get('observation_id')}",
                    "description": (
                        "pre-registered comparator baseline must have strictly larger heldout absolute "
                        "residual than the selected training-only model"
                    ),
                    "rejected": comparator.get("negative_control_rejected") is True,
                    "observation_id": row.get("observation_id"),
                    "comparator_id": comparator.get("comparator_id"),
                }
            )
    if not controls:
        return [
            {
                "control_id": "systems-wdi-predictive-search-v2-no-heldout-rows",
                "description": "no heldout replay rows were available for negative controls",
                "rejected": False,
            }
        ]
    return controls


def build_pack(rows: list[dict[str, Any]], source: dict[str, Any], support_allowed: bool) -> dict[str, Any]:
    residuals = residual_summary(rows)
    return {
        "schema_id": grand_factory.EVIDENCE_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "capability_owner": CAPABILITY_OWNER,
        "evidence_pack_id": "OC133-SYSTEMS-WDI-PREDICTIVE-SEARCH-V2-CANDIDATE",
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
            "World Bank WDI transparent predictive-search family selected per heldout target "
            "using only prior same-series rows"
        ),
        "comparator_baseline": {
            "name": "strict best-of carry-forward and prior-mean WDI comparators",
            "prediction_rule": "support requires the selected model to beat every preregistered comparator on every heldout row",
            "pre_registered": True,
            "baselines": list(COMPARATOR_BASELINES),
        },
        "uncertainty": {
            "metric": "mean absolute heldout residual",
            "method": "deterministic replay envelope over model residuals",
            "interval": uncertainty_interval(rows, float(residuals["model"])),
        },
        "residuals": residuals,
        "negative_controls": aggregate_negative_controls(rows),
        "falsifiers": ordered_unique([str(row["falsifier"]) for row in rows if row.get("falsifier")])
        or ["support fails when no heldout WDI replay rows are available"],
        "grand_toe_support_allowed": bool(support_allowed),
    }


def strict_schema_failures(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    required_top = {
        "candidate_pack": dict,
        "protocol": dict,
        "tasks": dict,
        "report": dict,
        "source_lock": dict,
        "source_lock_declaration": dict,
    }
    for field, field_type in required_top.items():
        if not isinstance(payload.get(field), field_type):
            failures.append(f"STRICT_SCHEMA_FIELD_INVALID::{field}")
    if failures:
        return failures
    pack = payload["candidate_pack"]
    report = payload["report"]
    protocol = payload["protocol"]
    tasks = payload["tasks"]
    source_lock = payload["source_lock"]
    declaration = payload["source_lock_declaration"]
    for field in grand_factory.REQUIRED_PACK_FIELDS:
        if field not in pack:
            failures.append(f"STRICT_PACK_FIELD_MISSING::{field}")
    if pack.get("schema_id") != grand_factory.EVIDENCE_SCHEMA_ID:
        failures.append("STRICT_PACK_SCHEMA_ID_MISMATCH")
    if report.get("schema_id") != REPORT_SCHEMA_ID:
        failures.append("STRICT_REPORT_SCHEMA_ID_MISMATCH")
    if protocol.get("schema_id") != PROTOCOL_SCHEMA_ID:
        failures.append("STRICT_PROTOCOL_SCHEMA_ID_MISMATCH")
    if tasks.get("schema_id") != TASKS_SCHEMA_ID:
        failures.append("STRICT_TASKS_SCHEMA_ID_MISMATCH")
    if source_lock.get("schema_id") != SOURCE_LOCK_SCHEMA_ID:
        failures.append("STRICT_SOURCE_LOCK_SCHEMA_ID_MISMATCH")
    if declaration.get("schema_id") != SOURCE_LOCK_DECLARATION_SCHEMA_ID:
        failures.append("STRICT_SOURCE_LOCK_DECLARATION_SCHEMA_ID_MISMATCH")
    if report.get("strict_schema_id") != STRICT_SCHEMA_ID:
        failures.append("STRICT_REPORT_SCHEMA_MARKER_MISSING")
    if not isinstance(tasks.get("rows"), list):
        failures.append("STRICT_TASK_ROWS_NOT_LIST")
    if not isinstance(report.get("exact_failure_rows"), list):
        failures.append("STRICT_EXACT_FAILURE_ROWS_NOT_LIST")
    if not isinstance(report.get("negative_control_failure_rows"), list):
        failures.append("STRICT_NEGATIVE_CONTROL_FAILURE_ROWS_NOT_LIST")
    if report.get("candidate_pack_sha256") != sha256_object(pack):
        failures.append("STRICT_CANDIDATE_PACK_HASH_MISMATCH")
    if protocol.get("candidate_pack_sha256") != sha256_object(pack):
        failures.append("STRICT_PROTOCOL_PACK_HASH_MISMATCH")
    if source_lock.get("declaration_sha256") != sha256_object(declaration):
        failures.append("STRICT_SOURCE_LOCK_DECLARATION_HASH_MISMATCH")
    source_lock_sha256 = sha256_object(source_lock)
    declaration_sha256 = sha256_object(declaration)
    for section_name, section in (("protocol", protocol), ("tasks", tasks), ("report", report)):
        metadata = section.get("pre_target_lock_metadata", {})
        if not isinstance(metadata, dict):
            failures.append(f"STRICT_SOURCE_LOCK_METADATA_NOT_OBJECT::{section_name}")
            continue
        if metadata.get("source_lock_sha256") != source_lock_sha256:
            failures.append(f"STRICT_SOURCE_LOCK_HASH_MISMATCH::{section_name}")
        if metadata.get("source_lock_declaration_sha256") != declaration_sha256:
            failures.append(f"STRICT_SOURCE_LOCK_DECLARATION_REF_HASH_MISMATCH::{section_name}")
    failures.extend(f"STRICT_{failure}" for failure in validate_source_lock(source_lock, declaration, tasks.get("rows", [])))
    return ordered_unique(failures)


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
                "test_id": "systems-wdi-predictive-search-v2-no-row-tamper-tests",
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
        prediction_stable = (
            rebuilt is not None
            and abs(float(rebuilt.get("predicted_value", math.nan)) - float(row["predicted_value"]))
            <= 1e-9 * max(1.0, abs(float(row["predicted_value"])))
        )
        target_checks.append(
            {
                "observation_id": row["observation_id"],
                "payload_hash_changed": sha256_object(mutated) != sha256_object(raw_payload),
                "row_hash_changed": rebuilt is not None and rebuilt.get("row_hash") != row.get("row_hash"),
                "selection_stable": rebuilt is not None and rebuilt.get("selected_formula_id") == row.get("selected_formula_id"),
                "prediction_stable": prediction_stable,
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
            "test_id": "systems-wdi-predictive-search-v2-target-mutation-changes-payload-hashes",
            "description": "mutating sampled heldout target values must change the canonical payload hash",
            "sample_total": len(target_checks),
            "failed_observation_ids": [
                item["observation_id"] for item in target_checks if not item["payload_hash_changed"]
            ],
            "passed": all(item["payload_hash_changed"] for item in target_checks),
        },
        {
            "test_id": "systems-wdi-predictive-search-v2-target-mutation-changes-row-hashes",
            "description": "mutating sampled heldout target values must change recomputed row hashes",
            "sample_total": len(target_checks),
            "failed_observation_ids": [
                item["observation_id"] for item in target_checks if not item["row_hash_changed"]
            ],
            "passed": all(item["row_hash_changed"] for item in target_checks),
        },
        {
            "test_id": "systems-wdi-predictive-search-v2-selection-target-leakage-control",
            "description": "mutating heldout targets must not change same-row selected formulas or predictions",
            "sample_total": len(target_checks),
            "failed_observation_ids": target_failures,
            "passed": not target_failures,
        },
        {
            "test_id": "systems-wdi-predictive-search-v2-pack-hash-changes-on-pack-mutation",
            "description": "mutating candidate-pack content must change the candidate-pack hash",
            "passed": sha256_object(mutated_pack) != pack_hash,
        },
    ]


def blocker_work_orders(blockers: list[str], *, minimum_n: int, candidate_n: int, failure_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
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
        "OC133-SYSTEMS-WDI-PREDICTIVE-SEARCH-V2-N",
        "N_BELOW_MINIMUM",
        f"Harvest or declare enough target-hidden WDI replay rows to reach N>={minimum_n}; current candidate_n={candidate_n}.",
    )
    add(
        "OC133-SYSTEMS-WDI-PREDICTIVE-SEARCH-V2-SOURCE-SEPARATION",
        "REQUIRED",
        "Attach complete pre-target lock metadata with target-blind or prospective source separation before any support claim.",
    )
    add(
        "OC133-SYSTEMS-WDI-PREDICTIVE-SEARCH-V2-NEGATIVE-CONTROLS",
        "NEGATIVE_CONTROL",
        "Keep systems blocked and revise only on training/prior rows; exact failing heldout rows are listed in the report.",
    )
    add(
        "OC133-SYSTEMS-WDI-PREDICTIVE-SEARCH-V2-SUPERIORITY",
        "SUPERIORITY",
        "Require strict positive residual superiority against the best comparator and all row-level controls.",
    )
    add(
        "OC133-SYSTEMS-WDI-PREDICTIVE-SEARCH-V2-TAMPER",
        "TAMPER_TEST_FAILED",
        "Repair hash/tamper replay before registry review.",
    )
    add(
        "OC133-SYSTEMS-WDI-PREDICTIVE-SEARCH-V2-STRICT-SCHEMA",
        "STRICT_",
        "Repair schema/hash fields and rerun the factory; do not mark grand support by hand.",
    )
    if failure_rows:
        orders.append(
            {
                "work_order_id": "OC133-SYSTEMS-WDI-PREDICTIVE-SEARCH-V2-FAILURE-ROWS",
                "status": "OPEN",
                "triggered_by": [str(row["observation_id"]) for row in failure_rows],
                "action": "Investigate exact failed heldout rows without changing target values or using targets for model selection.",
            }
        )
    if not orders and blockers:
        orders.append(
            {
                "work_order_id": "OC133-SYSTEMS-WDI-PREDICTIVE-SEARCH-V2-GENERIC",
                "status": "OPEN",
                "triggered_by": blockers,
                "action": "Resolve listed blockers and rerun the WDI predictive-search v2 factory.",
            }
        )
    if not blockers:
        orders.append(
            {
                "work_order_id": "OC133-SYSTEMS-WDI-PREDICTIVE-SEARCH-V2-REGISTRY-REVIEW",
                "status": "READY",
                "triggered_by": [],
                "action": "Candidate clears local strict gate; review before optional parent registry registration.",
            }
        )
    return orders


def build_formula_search_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    manifest = formula_family_manifest()
    return {
        "preregistered_formula_family": manifest,
        "formula_family_sha256": sha256_object(manifest),
        "selection_scope": "per target row; same-series years strictly earlier than heldout_year",
        "selection_metric": (
            "mean absolute residual on prior one-step replay rows with declared cycle-guard override"
        ),
        "target_rows_used_for_selection": False,
        "minimum_training_score_rows": MIN_TRAINING_SCORE_ROWS,
        "selected_formula_counts": selected_formula_counts(rows),
        "selected_family_counts": selected_family_counts(rows),
        "ses_grid": [item["parameters"]["alpha"] for item in manifest if item["family"] == "simple_exponential_smoothing"],
        "cycle_guard_formula_ids": [item["formula_id"] for item in manifest if item["family"] == "cycle_guard"],
    }


def target_split_declarations(series: dict[SeriesKey, dict[int, float]], snapshot_ref: str) -> list[dict[str, Any]]:
    declarations: list[dict[str, Any]] = []
    for key in sorted(series, key=lambda item: item.label()):
        values_by_year = series[key]
        for target_year in sorted(values_by_year):
            training_years = years_before(values_by_year, target_year)
            if len(training_years) < MIN_TARGET_PRIOR_YEARS:
                continue
            declarations.append(
                {
                    "observation_id": (
                        f"SYSTEMS-WDI-PREDICTIVE-SEARCH-V2-"
                        f"{key.country_code}-{key.indicator_id}-{target_year}"
                    ),
                    "country": f"{key.country_code}:{key.country_name}",
                    "indicator": f"{key.indicator_id}:{key.indicator_name}",
                    "training_years": training_years,
                    "heldout_year": target_year,
                    "training_source": row_training_source(snapshot_ref, key, training_years),
                    "target_source": row_target_source(snapshot_ref, key, target_year),
                }
            )
    return declarations


def row_split_declarations(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "observation_id": row.get("observation_id"),
            "country": row.get("country"),
            "indicator": row.get("indicator"),
            "training_years": row.get("training_years", []),
            "heldout_year": row.get("heldout_year"),
            "training_source": row.get("training_source"),
            "target_source": row.get("target_source"),
        }
        for row in rows
    ]


def source_lock_scoring_policy() -> dict[str, Any]:
    return {
        "selection_scope": "per target row; same-series years strictly earlier than heldout_year",
        "selection_metric": "mean absolute residual on prior one-step replay rows with declared cycle-guard override",
        "cycle_guard_override_policy": (
            "when the best replay formula has nonzero prior replay error and a larger current step than "
            "cycle_guard_micro_trend, select the predeclared cycle guard; this uses only same-series "
            "history earlier than heldout_year"
        ),
        "target_rows_used_for_selection": False,
        "minimum_training_score_rows": MIN_TRAINING_SCORE_ROWS,
        "residual_metric": "absolute residual; aggregate model residual is mean absolute residual",
        "negative_control_policy": (
            "reject support unless every comparator baseline is worse than the selected model on every heldout row"
        ),
        "uncertainty_policy": "deterministic replay envelope over selected-model absolute residuals",
        "tamper_policy": (
            "heldout target mutation must change row hashes without changing same-row formula selection or prediction"
        ),
        "support_gate_policy": (
            "grand_toe_support_allowed is true iff source lock, source separation, N, row validation, "
            "residual superiority, negative controls, tamper tests, pack gate, and strict schema all pass"
        ),
    }


def build_source_lock_declaration(
    source: dict[str, Any],
    series: dict[SeriesKey, dict[int, float]],
    snapshot_ref: str,
    snapshot_sha256: str,
) -> dict[str, Any]:
    target_rows = target_split_declarations(series, snapshot_ref)
    candidate_formulas = formula_family_manifest()
    comparator_baselines = list(COMPARATOR_BASELINES)
    scoring_policy = source_lock_scoring_policy()
    return {
        "schema_id": SOURCE_LOCK_DECLARATION_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "declaration_id": "OC133-SYSTEMS-WDI-PREDICTIVE-SEARCH-V2-PRE-TARGET-DECLARATION",
        "declaration_scope": (
            "source lock for WDI predictive-search v2 model family, target split, candidate formulas, "
            "comparators, and scoring policy before heldout target scoring"
        ),
        "source_claim": source,
        "snapshot_ref": snapshot_ref,
        "snapshot_sha256": snapshot_sha256,
        "snapshot_hash_policy": SNAPSHOT_HASH_POLICY,
        "split_policy": {
            "mode": source.get("mode"),
            "target_hidden_until_scoring": source.get("target_hidden_until_scoring") is True,
            "training_year_rule": "training_year < heldout_year",
            "target_row_values_excluded": True,
            "prediction_outputs_excluded": True,
            "minimum_prior_years": MIN_TARGET_PRIOR_YEARS,
        },
        "target_rows_declared_before_scoring": target_rows,
        "candidate_formulas_declared_before_scoring": candidate_formulas,
        "comparator_baselines_declared_before_scoring": comparator_baselines,
        "scoring_policy_declared_before_scoring": scoring_policy,
        "declaration_exclusion_policy": {
            "forbidden_score_fields": sorted(DECLARATION_FORBIDDEN_KEYS),
            "observed_target_values_excluded": True,
            "predictions_excluded": True,
            "residuals_excluded": True,
        },
    }


def declaration_contains_forbidden_score_fields(value: Any) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key) in DECLARATION_FORBIDDEN_KEYS:
                return True
            if declaration_contains_forbidden_score_fields(child):
                return True
    if isinstance(value, list):
        return any(declaration_contains_forbidden_score_fields(item) for item in value)
    return False


def build_source_lock(source: dict[str, Any], declaration: dict[str, Any]) -> dict[str, Any]:
    target_rows = declaration.get("target_rows_declared_before_scoring", [])
    candidate_formulas = declaration.get("candidate_formulas_declared_before_scoring", [])
    scoring_policy = declaration.get("scoring_policy_declared_before_scoring", {})
    comparator_baselines = declaration.get("comparator_baselines_declared_before_scoring", [])
    return {
        "schema_id": SOURCE_LOCK_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "source_lock_id": "OC133-SYSTEMS-WDI-PREDICTIVE-SEARCH-V2-SOURCE-LOCK",
        "declaration_ref": SOURCE_LOCK_DECLARATION_REL,
        "declaration_sha256": sha256_object(declaration),
        "declaration_hash_policy": SOURCE_LOCK_HASH_POLICY,
        "declared_before_scoring": source.get("declared_before_scoring") is True,
        "pre_target_lock": source.get("pre_target_lock") is True,
        "target_hidden_until_scoring": source.get("target_hidden_until_scoring") is True,
        "external_lock_id": source.get("lock_id"),
        "external_lock_timestamp": source.get("lock_timestamp"),
        "source_ref": source.get("source_ref"),
        "snapshot_ref": declaration.get("snapshot_ref"),
        "snapshot_sha256": declaration.get("snapshot_sha256"),
        "model_family_declared_before_scoring": True,
        "target_split_declared_before_scoring": True,
        "target_rows_declared_before_scoring": True,
        "candidate_formulas_declared_before_scoring": True,
        "scoring_policy_declared_before_scoring": True,
        "target_row_count": len(target_rows) if isinstance(target_rows, list) else 0,
        "target_split_sha256": sha256_object(target_rows),
        "candidate_formulas_sha256": sha256_object(candidate_formulas),
        "comparator_baselines_sha256": sha256_object(comparator_baselines),
        "scoring_policy_sha256": sha256_object(scoring_policy),
        "declaration_excludes_target_values": not declaration_contains_forbidden_score_fields(declaration),
        "score_artifacts_allowed_in_declaration": False,
    }


def validate_source_lock(source_lock: dict[str, Any], declaration: dict[str, Any], rows: list[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    if source_lock.get("schema_id") != SOURCE_LOCK_SCHEMA_ID:
        failures.append("SOURCE_LOCK_SCHEMA_ID_MISMATCH")
    if declaration.get("schema_id") != SOURCE_LOCK_DECLARATION_SCHEMA_ID:
        failures.append("SOURCE_LOCK_DECLARATION_SCHEMA_ID_MISMATCH")
    if source_lock.get("declaration_sha256") != sha256_object(declaration):
        failures.append("SOURCE_LOCK_DECLARATION_HASH_MISMATCH")
    if source_lock.get("declaration_ref") != SOURCE_LOCK_DECLARATION_REL:
        failures.append("SOURCE_LOCK_DECLARATION_REF_MISMATCH")
    for field in (
        "declared_before_scoring",
        "pre_target_lock",
        "target_hidden_until_scoring",
        "model_family_declared_before_scoring",
        "target_split_declared_before_scoring",
        "target_rows_declared_before_scoring",
        "candidate_formulas_declared_before_scoring",
        "scoring_policy_declared_before_scoring",
        "declaration_excludes_target_values",
    ):
        if source_lock.get(field) is not True:
            failures.append(f"SOURCE_LOCK_PREDICATE_NOT_TRUE::{field}")
    if source_lock.get("external_lock_id") in (None, "", "missing"):
        failures.append("SOURCE_LOCK_EXTERNAL_ID_REQUIRED")
    if source_lock.get("external_lock_timestamp") in (None, "", "missing"):
        failures.append("SOURCE_LOCK_EXTERNAL_TIMESTAMP_REQUIRED")
    declared_rows = declaration.get("target_rows_declared_before_scoring", [])
    if not isinstance(declared_rows, list) or not declared_rows:
        failures.append("SOURCE_LOCK_TARGET_ROWS_REQUIRED")
        declared_rows = []
    if source_lock.get("target_split_sha256") != sha256_object(declared_rows):
        failures.append("SOURCE_LOCK_TARGET_SPLIT_HASH_MISMATCH")
    if source_lock.get("candidate_formulas_sha256") != sha256_object(
        declaration.get("candidate_formulas_declared_before_scoring", [])
    ):
        failures.append("SOURCE_LOCK_CANDIDATE_FORMULAS_HASH_MISMATCH")
    if source_lock.get("comparator_baselines_sha256") != sha256_object(
        declaration.get("comparator_baselines_declared_before_scoring", [])
    ):
        failures.append("SOURCE_LOCK_COMPARATOR_BASELINES_HASH_MISMATCH")
    if source_lock.get("scoring_policy_sha256") != sha256_object(
        declaration.get("scoring_policy_declared_before_scoring", {})
    ):
        failures.append("SOURCE_LOCK_SCORING_POLICY_HASH_MISMATCH")
    if declaration_contains_forbidden_score_fields(declaration):
        failures.append("SOURCE_LOCK_DECLARATION_CONTAINS_SCORE_FIELDS")
    if row_split_declarations(rows) != declared_rows:
        failures.append("SOURCE_LOCK_DECLARED_TARGET_ROWS_DO_NOT_MATCH_SCORED_ROWS")
    return ordered_unique(failures)


def build_pre_target_lock_metadata(
    source: dict[str, Any],
    source_lock: dict[str, Any],
    snapshot_ref: str,
    snapshot_sha256: str,
) -> dict[str, Any]:
    return {
        "lock_required": True,
        "source_mode": source.get("mode"),
        "source_ref": source.get("source_ref"),
        "lock_id": source.get("lock_id"),
        "lock_timestamp": source.get("lock_timestamp"),
        "pre_target_lock": source.get("pre_target_lock") is True,
        "target_hidden_until_scoring": source.get("target_hidden_until_scoring") is True,
        "declared_before_scoring": source.get("declared_before_scoring") is True,
        "snapshot_ref": snapshot_ref,
        "snapshot_sha256": snapshot_sha256,
        "source_lock_ref": SOURCE_LOCK_REL,
        "source_lock_sha256": sha256_object(source_lock),
        "source_lock_declaration_ref": SOURCE_LOCK_DECLARATION_REL,
        "source_lock_declaration_sha256": source_lock.get("declaration_sha256"),
        "formula_family_locked_before_target_scoring": source_lock.get("model_family_declared_before_scoring") is True,
        "formula_family_sha256": source_lock.get("candidate_formulas_sha256"),
        "target_split_locked_before_target_scoring": source_lock.get("target_split_declared_before_scoring") is True,
        "target_split_sha256": source_lock.get("target_split_sha256"),
        "comparator_baselines_locked_before_target_scoring": True,
        "comparator_baselines_sha256": source_lock.get("comparator_baselines_sha256"),
        "scoring_policy_locked_before_target_scoring": source_lock.get("scoring_policy_declared_before_scoring") is True,
        "scoring_policy_sha256": source_lock.get("scoring_policy_sha256"),
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
    row_failures, failure_rows = validate_rows(rows)
    formula_search = build_formula_search_summary(rows)
    source_lock_declaration = build_source_lock_declaration(source, series, snapshot_ref, snapshot_sha256)
    source_lock = build_source_lock(source, source_lock_declaration)
    source_lock_failures = validate_source_lock(source_lock, source_lock_declaration, rows)

    if len(rows) < minimum_n:
        blockers.append(f"N_BELOW_MINIMUM::{len(rows)}/{minimum_n}")

    residuals = residual_summary(rows)
    if residuals["superiority_margin"] <= 0:
        blockers.append("HELDOUT_RESIDUAL_SUPERIORITY_NOT_MET")

    negative_control_failure_rows = [
        row
        for row in failure_rows
        if any(str(failure).startswith("NEGATIVE_CONTROL") for failure in row.get("failures", []))
    ]
    preliminary_blockers = ordered_unique(
        [*blockers, *source_failures, *row_build_failures, *row_failures, *source_lock_failures]
    )
    preliminary_pack = build_pack(rows, source, support_allowed=not preliminary_blockers)
    tamper_tests = build_tamper_tests(raw_payload, snapshot_ref, rows, preliminary_pack)
    tamper_failures = [f"TAMPER_TEST_FAILED::{test['test_id']}" for test in tamper_tests if test.get("passed") is not True]

    lock_metadata = build_pre_target_lock_metadata(source, source_lock, snapshot_ref, snapshot_sha256)
    candidate_support = not ordered_unique([*preliminary_blockers, *tamper_failures])
    candidate_pack = build_pack(rows, source, support_allowed=candidate_support)
    candidate_gate_failures = grand_factory.pack_failure_reasons(candidate_pack, requirements)
    support_before_strict_schema = candidate_support and not candidate_gate_failures
    pack = build_pack(rows, source, support_allowed=support_before_strict_schema)
    pack_sha256 = sha256_object(pack)
    task_rows_hash = sha256_object([row.get("row_hash") for row in rows])

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
        "source_lock_ref": SOURCE_LOCK_REL,
        "source_lock_declaration_ref": SOURCE_LOCK_DECLARATION_REL,
        "pre_target_lock_metadata": lock_metadata,
        "minimum_n": minimum_n,
        "candidate_n": len(rows),
        "formula_search": formula_search,
        "comparator_baselines": list(COMPARATOR_BASELINES),
        "residual_metric": "absolute residual; aggregate model residual is mean absolute residual",
        "negative_control_policy": "reject support unless every comparator baseline is worse than the selected model on every heldout row",
        "tamper_policy": "heldout target mutation must change row hashes without changing same-row formula selection or prediction",
        "required_protocol_steps": [
            "freeze the pinned WDI snapshot and record its hash",
            "lock source-separation and pre-target metadata before scoring",
            "lock formula and comparator families before target scoring",
            "select formulas using only same-series years strictly earlier than each heldout target year",
            "score each heldout target once and record row hashes",
            "compare against all preregistered baselines under the same residual metric",
            "reject support unless N, strict schema, source separation, residual superiority, all negative controls, falsifiers, and tamper tests pass",
        ],
        "blockers": [],
        "next_work_orders": [],
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
        "source_lock_ref": SOURCE_LOCK_REL,
        "source_lock_declaration_ref": SOURCE_LOCK_DECLARATION_REL,
        "pre_target_lock_metadata": lock_metadata,
        "series_total": len(series),
        "row_total": len(rows),
        "row_hash_policy": ROW_HASH_POLICY,
        "row_hashes_sha256": task_rows_hash,
        "formula_search": formula_search,
        "rows": rows,
        "exact_failure_rows": failure_rows,
        "negative_control_failure_rows": negative_control_failure_rows,
        "blockers": [],
        "next_work_orders": [],
    }
    report = {
        "schema_id": REPORT_SCHEMA_ID,
        "strict_schema_id": STRICT_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "blocker_id": "grand_toe_empirical_superiority",
        "snapshot_ref": snapshot_ref,
        "snapshot_sha256": snapshot_sha256,
        "snapshot_hash_policy": SNAPSHOT_HASH_POLICY,
        "source_separation_claim": source,
        "source_lock_ref": SOURCE_LOCK_REL,
        "source_lock_declaration_ref": SOURCE_LOCK_DECLARATION_REL,
        "pre_target_lock_metadata": lock_metadata,
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
        "source_lock_failures": source_lock_failures,
        "row_validation_failures": ordered_unique([*row_build_failures, *row_failures]),
        "candidate_gate_failures": candidate_gate_failures,
        "pack_failure_reasons": [],
        "strict_schema_failures": [],
        "exact_failure_rows": failure_rows,
        "negative_control_failure_rows": negative_control_failure_rows,
        "tamper_tests": tamper_tests,
        "tamper_test_total": len(tamper_tests),
        "candidate_pack_total": 1,
        "valid_pack_total": 0,
        "blocked_candidate_pack_total": 1,
        "blockers": [],
        "open_blocker_total": 0,
        "blocker_total": 0,
        "blocked_total": 0,
        "next_work_orders": [],
        "next_work_order_total": 0,
        "grand_toe_support_allowed": support_before_strict_schema,
        "verdict": "READY_FOR_PARENT_REGISTRY_REVIEW" if support_before_strict_schema else "BLOCKED",
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
        "source_lock_declaration": source_lock_declaration,
    }
    strict_failures = strict_schema_failures(payload)
    support_allowed = support_before_strict_schema and not strict_failures
    if support_allowed != support_before_strict_schema:
        pack = build_pack(rows, source, support_allowed=support_allowed)
        pack_sha256 = sha256_object(pack)
        payload["candidate_pack"] = pack
        payload["protocol"]["candidate_pack_sha256"] = pack_sha256
        payload["report"]["candidate_pack_sha256"] = pack_sha256
    final_pack_failures = grand_factory.pack_failure_reasons(payload["candidate_pack"], requirements)
    blockers = ordered_unique([*preliminary_blockers, *tamper_failures, *candidate_gate_failures, *strict_failures])
    if not support_allowed and "GRAND_TOE_SUPPORT_NOT_ALLOWED" not in blockers:
        blockers.append("GRAND_TOE_SUPPORT_NOT_ALLOWED")
    work_orders = blocker_work_orders(blockers, minimum_n=minimum_n, candidate_n=len(rows), failure_rows=failure_rows)
    verdict = "READY_FOR_PARENT_REGISTRY_REVIEW" if support_allowed else "BLOCKED"

    for section in ("protocol", "tasks"):
        payload[section]["blockers"] = blockers
        payload[section]["next_work_orders"] = work_orders
    payload["report"].update(
        {
            "candidate_pack_sha256": sha256_object(payload["candidate_pack"]),
            "candidate_gate_failures": candidate_gate_failures,
            "pack_failure_reasons": final_pack_failures,
            "strict_schema_failures": strict_failures,
            "valid_pack_total": 1 if support_allowed else 0,
            "blocked_candidate_pack_total": 0 if support_allowed else 1,
            "blockers": blockers,
            "open_blocker_total": len(blockers),
            "blocker_total": len(blockers),
            "blocked_total": len(blockers),
            "next_work_orders": work_orders,
            "next_work_order_total": len(work_orders),
            "grand_toe_support_allowed": support_allowed,
            "verdict": verdict,
        }
    )
    payload["protocol"]["candidate_pack_sha256"] = sha256_object(payload["candidate_pack"])
    return payload


def build_missing_snapshot_payload(root: Path, snapshot_ref: str, requirements: dict[str, Any], requirement_failures: list[str]) -> dict[str, Any]:
    source = {
        "mode": "snapshot_replay",
        "pre_target_lock": False,
        "target_hidden_until_scoring": False,
        "declared_before_scoring": False,
        "lock_id": "missing",
        "lock_timestamp": "missing",
        "source_ref": "none",
    }
    blockers = ordered_unique(["SNAPSHOT_MISSING", *requirement_failures, "GRAND_TOE_SUPPORT_NOT_ALLOWED"])
    rows: list[dict[str, Any]] = []
    formula_search = build_formula_search_summary(rows)
    source_lock_declaration = build_source_lock_declaration(source, {}, snapshot_ref, "missing")
    source_lock = build_source_lock(source, source_lock_declaration)
    source_lock_failures = validate_source_lock(source_lock, source_lock_declaration, rows)
    blockers = ordered_unique([*blockers, *source_lock_failures])
    lock_metadata = build_pre_target_lock_metadata(source, source_lock, snapshot_ref, "missing")
    pack = build_pack(rows, source, support_allowed=False)
    work_orders = blocker_work_orders(blockers, minimum_n=int(requirements.get("minimum_per_domain_n", 20)), candidate_n=0, failure_rows=[])
    report = {
        "schema_id": REPORT_SCHEMA_ID,
        "strict_schema_id": STRICT_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "snapshot_ref": snapshot_ref,
        "candidate_pack_ref": PACK_REL,
        "candidate_pack_sha256": sha256_object(pack),
        "source_lock_ref": SOURCE_LOCK_REL,
        "source_lock_declaration_ref": SOURCE_LOCK_DECLARATION_REL,
        "pre_target_lock_metadata": lock_metadata,
        "minimum_n": int(requirements.get("minimum_per_domain_n", 20)),
        "candidate_n": 0,
        "missing_n": int(requirements.get("minimum_per_domain_n", 20)),
        "source_lock_failures": source_lock_failures,
        "exact_failure_rows": [],
        "negative_control_failure_rows": [],
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
            "source_lock_ref": SOURCE_LOCK_REL,
            "source_lock_declaration_ref": SOURCE_LOCK_DECLARATION_REL,
            "pre_target_lock_metadata": lock_metadata,
            "blockers": blockers,
            "next_work_orders": work_orders,
        },
        "tasks": {
            "schema_id": TASKS_SCHEMA_ID,
            "release_id": RELEASE_ID,
            "version": VERSION,
            "capability_owner": CAPABILITY_OWNER,
            "snapshot_ref": snapshot_ref,
            "source_lock_ref": SOURCE_LOCK_REL,
            "source_lock_declaration_ref": SOURCE_LOCK_DECLARATION_REL,
            "rows": [],
            "exact_failure_rows": [],
            "negative_control_failure_rows": [],
            "blockers": blockers,
            "next_work_orders": work_orders,
        },
        "report": report,
        "source_lock": source_lock,
        "source_lock_declaration": source_lock_declaration,
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
        "# Systems WDI Predictive Search V2",
        "",
        f"Verdict: `{report.get('verdict')}`",
        f"Grand TOE support allowed: `{str(report.get('grand_toe_support_allowed')).lower()}`",
        f"Snapshot: `{report.get('snapshot_ref')}`",
        f"Rows: `{report.get('candidate_n', 0)}`",
        f"Minimum N: `{report.get('minimum_n', 0)}`",
        "",
        "This factory replays a pinned WDI snapshot with a locked transparent model family. Model selection uses only prior same-series rows for each heldout target, then strict comparators, uncertainty, falsifiers, negative controls, schema checks, and tamper checks decide whether the candidate remains blocked.",
        "",
        "## Open Blockers",
    ]
    blockers = report.get("blockers", [])
    if blockers:
        lines.extend(f"- `{blocker}`" for blocker in blockers)
    else:
        lines.append("- `none`")
    lines.extend(["", "## Exact Failure Rows"])
    failure_rows = report.get("exact_failure_rows", [])
    if failure_rows:
        for row in failure_rows[:50]:
            lines.append(f"- `{row['observation_id']}`: `{';'.join(row.get('failures', []))}`")
        if len(failure_rows) > 50:
            lines.append(f"- `{len(failure_rows) - 50}` additional rows omitted from README; see report JSON")
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
    write_json(root / SOURCE_LOCK_REL, payload["source_lock"])
    write_json(root / SOURCE_LOCK_DECLARATION_REL, payload["source_lock_declaration"])
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
        (SOURCE_LOCK_REL, expected["source_lock"]),
        (SOURCE_LOCK_DECLARATION_REL, expected["source_lock_declaration"]),
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
    parser = argparse.ArgumentParser(description="Build OC133 systems WDI predictive-search v2 replay artifacts.")
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
        print(
            json.dumps(
                {
                    "status": "ok",
                    "checked": [
                        PACK_REL,
                        REPORT_REL,
                        PROTOCOL_REL,
                        TASKS_REL,
                        SOURCE_LOCK_REL,
                        SOURCE_LOCK_DECLARATION_REL,
                        README_REL,
                    ],
                },
                indent=2,
            )
        )
        return 0
    payload = write_outputs(root, snapshot_ref=args.snapshot_ref) if args.write else build_payload(root, snapshot_ref=args.snapshot_ref)
    print(json.dumps(payload["report"], ensure_ascii=False, indent=2))
    if payload["report"].get("grand_toe_support_allowed") is not True and not args.allow_blocked_exit_zero:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
