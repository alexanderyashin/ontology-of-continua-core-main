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

OUTPUT_ROOT_REL = "validation/heldout/grand_science/systems/wdi_benchmark"
PACK_REL = f"{OUTPUT_ROOT_REL}/systems_wdi_benchmark_candidate_evidence_pack.json"
REPORT_REL = f"{OUTPUT_ROOT_REL}/OC133_SYSTEMS_WDI_BENCHMARK_REPORT.json"
PROTOCOL_REL = f"{OUTPUT_ROOT_REL}/OC133_SYSTEMS_WDI_BENCHMARK_PROTOCOL.json"
TASKS_REL = f"{OUTPUT_ROOT_REL}/OC133_SYSTEMS_WDI_BENCHMARK_TASKS.json"
README_REL = f"{OUTPUT_ROOT_REL}/README.md"

SNAPSHOT_REF = "validation/_raw/systems_world_bank_gdp.txt"
REQUIREMENTS_REL = "benchmarks/grand_science/domain_requirements.json"
SNAPSHOT_HASH_POLICY = "LF_NORMALIZED_TEXT_SNAPSHOT_HASH"
ROW_HASH_POLICY = "sha256 over sorted row payload"
PACK_HASH_POLICY = "sha256 over canonical JSON"

REPORT_SCHEMA_ID = "OC133_SYSTEMS_WDI_BENCHMARK_REPORT_v2"
PROTOCOL_SCHEMA_ID = "OC133_SYSTEMS_WDI_BENCHMARK_PROTOCOL_v2"
TASKS_SCHEMA_ID = "OC133_SYSTEMS_WDI_BENCHMARK_TASKS_v2"

Predictor = Callable[[float, float], float]


@dataclass(frozen=True)
class Formula:
    id: str
    rule: str
    predictor: Predictor


FORMULA_FAMILIES: tuple[Formula, ...] = (
    Formula(
        id="linear_two_lag",
        rule="y_t = y_t-1 + (y_t-1 - y_t-2)",
        predictor=lambda older, newer: newer + (newer - older),
    ),
    Formula(
        id="damped_two_lag",
        rule="y_t = y_t-1 + 0.5*(y_t-1 - y_t-2)",
        predictor=lambda older, newer: newer + 0.5 * (newer - older),
    ),
    Formula(
        id="two_lag_mean",
        rule="y_t = (y_t-1 + y_t-2) / 2",
        predictor=lambda older, newer: 0.5 * (older + newer),
    ),
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


def lf_bytes(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n")


def sha256_file_text(path: Path) -> str:
    return hashlib.sha256(lf_bytes(path)).hexdigest()


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


def load_requirements(root: Path) -> tuple[dict[str, Any], list[str]]:
    path = root / REQUIREMENTS_REL
    if not path.exists():
        return (
            {
                "minimum_per_domain_n": 20,
                "required_domains": ["systems"],
                "required_source_separation_modes": ["target_blind", "prospective"],
            },
            ["REQUIREMENTS_MISSING::using_defaults"],
        )
    payload = read_json(path)
    if not isinstance(payload, dict):
        return ({}, ["REQUIREMENTS_PARSE_ERROR"])
    return payload, []


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
    raise ValueError("Expected World Bank WDI payload [metadata, rows] or {'rows': [...]}")


def extract_source_separation(payload: Any) -> dict[str, Any]:
    metadata = payload_metadata(payload)
    source = metadata.get("oc133_source_separation", metadata.get("source_separation", {}))
    if not isinstance(source, dict):
        source = {}
    return {
        "mode": str(source.get("mode", "snapshot_replay")),
        "pre_target_lock": source.get("pre_target_lock") is True,
        "target_hidden_until_scoring": source.get("target_hidden_until_scoring") is True,
        "declared_before_scoring": source.get("declared_before_scoring") is True,
        "split_policy": str(source.get("split_policy", "")),
    }


def parse_wdi_payload(payload: Any) -> dict[tuple[str, str, str, str], dict[int, float]]:
    series: dict[tuple[str, str, str, str], dict[int, float]] = {}
    for row in payload_rows(payload):
        if not isinstance(row, dict):
            continue
        country_obj = row.get("country") if isinstance(row.get("country"), dict) else {}
        country_code = str(row.get("countryiso3code") or country_obj.get("iso3code") or country_obj.get("id") or "").strip()
        country_name = str(country_obj.get("value") or country_code).strip()
        indicator_obj = row.get("indicator") if isinstance(row.get("indicator"), dict) else {}
        indicator_id = str(indicator_obj.get("id") or "").strip()
        indicator_name = str(indicator_obj.get("value") or indicator_id).strip()
        if not country_code or not indicator_id:
            continue
        raw_value = row.get("value")
        if raw_value in (None, "") or (isinstance(raw_value, str) and raw_value.lower() == "null"):
            continue
        try:
            value = float(raw_value)
            year = int(str(row.get("date", "")).strip())
        except (TypeError, ValueError):
            continue
        if not math.isfinite(value):
            continue
        key = (country_code, country_name, indicator_id, indicator_name)
        series.setdefault(key, {})[year] = value
    return series


def split_years(years: list[int]) -> tuple[list[int], int | None]:
    ordered = sorted(years)
    if len(ordered) < 4:
        return ordered, None
    return ordered[:-1], ordered[-1]


def formula_training_residuals(series: dict[tuple[str, str, str, str], dict[int, float]], formula: Formula) -> list[float]:
    residuals: list[float] = []
    for values_by_year in series.values():
        training_years, _target_year = split_years(list(values_by_year))
        if len(training_years) < 3:
            continue
        for idx in range(2, len(training_years)):
            older = values_by_year[training_years[idx - 2]]
            newer = values_by_year[training_years[idx - 1]]
            observed = values_by_year[training_years[idx]]
            residuals.append(abs(formula.predictor(older, newer) - observed))
    return residuals


def select_formula(series: dict[tuple[str, str, str, str], dict[int, float]]) -> tuple[Formula, dict[str, Any], list[str]]:
    failures: list[str] = []
    scores: list[dict[str, Any]] = []
    best = FORMULA_FAMILIES[0]
    best_score = math.inf
    for formula in FORMULA_FAMILIES:
        residuals = formula_training_residuals(series, formula)
        mean_residual = sum(residuals) / len(residuals) if residuals else math.inf
        scores.append(
            {
                "formula_id": formula.id,
                "rule": formula.rule,
                "training_row_count": len(residuals),
                "mean_abs_training_residual": None if mean_residual == math.inf else mean_residual,
            }
        )
        if mean_residual < best_score:
            best = formula
            best_score = mean_residual
    if best_score == math.inf:
        failures.append("FORMULA_SELECTION_NO_TRAINING_ROWS")
    return (
        best,
        {
            "selected_formula_id": best.id,
            "target_rows_used_for_selection": False,
            "selection_metric": "mean absolute residual on training years only",
            "scores": scores,
        },
        failures,
    )


def build_rows(
    series: dict[tuple[str, str, str, str], dict[int, float]],
    snapshot_ref: str,
    formula: Formula,
) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    failures: list[str] = []
    for key, values_by_year in sorted(series.items()):
        country_code, country_name, indicator_id, indicator_name = key
        training_years, target_year = split_years(list(values_by_year))
        if target_year is None or len(training_years) < 3:
            failures.append(f"INSUFFICIENT_SERIES_YEARS::{country_code}:{indicator_id}:{len(values_by_year)}")
            continue
        older_year, newer_year = training_years[-2], training_years[-1]
        older, newer = values_by_year[older_year], values_by_year[newer_year]
        predicted = float(formula.predictor(older, newer))
        observed = float(values_by_year[target_year])
        comparator = float(newer)
        model_residual = abs(predicted - observed)
        comparator_residual = abs(comparator - observed)
        row_id = f"OC133-SYSTEMS-WDI-{country_code}-{indicator_id}-{target_year}"
        row = {
            "observation_id": row_id,
            "country": f"{country_code}:{country_name}",
            "indicator": f"{indicator_id}:{indicator_name}",
            "training_years": training_years,
            "heldout_year": target_year,
            "training_source": f"{snapshot_ref}::{country_code}:{indicator_id}:training_years={','.join(str(y) for y in training_years)}",
            "target_source": f"{snapshot_ref}::{country_code}:{indicator_id}:heldout_year={target_year}",
            "formula_id": formula.id,
            "formula": formula.rule,
            "predicted_value": predicted,
            "observed_value": observed,
            "comparator_prediction": comparator,
            "uncertainty": 0.0,
            "model_residual": model_residual,
            "comparator_residual": comparator_residual,
            "negative_control_id": f"systems-wdi-carry-forward-control::{row_id}",
            "negative_control_description": "carry-forward baseline must have larger absolute residual than the selected formula on this heldout row",
            "negative_control_passed": comparator_residual > model_residual,
            "falsifier": "support fails if carry-forward residual is not larger than model residual on any heldout WDI row",
        }
        row["row_hash"] = sha256_object({key: value for key, value in row.items() if key != "row_hash"})
        row["row_hash_policy"] = ROW_HASH_POLICY
        rows.append(row)
    return rows, failures


def validate_source_separation(source: dict[str, Any], rows: list[dict[str, Any]], requirements: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    allowed_modes = {str(mode) for mode in requirements.get("required_source_separation_modes", ["target_blind", "prospective"])}
    if source.get("mode") not in allowed_modes:
        failures.append(f"SOURCE_SEPARATION_MODE_NOT_ALLOWED::{source.get('mode')}")
    if source.get("declared_before_scoring") is not True:
        failures.append("TARGET_SEPARATION_NOT_EXPLICIT_OR_NOT_LOCKED")
    if source.get("split_policy") != "last_year_heldout_per_series":
        failures.append("SPLIT_POLICY_NOT_EXPLICIT_LAST_YEAR_HELDOUT")
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
        "formula",
        "predicted_value",
        "observed_value",
        "comparator_prediction",
        "model_residual",
        "comparator_residual",
        "negative_control_id",
        "falsifier",
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
        if row.get("negative_control_passed") is not True:
            failures.append(f"NEGATIVE_CONTROL_NOT_REJECTED::{row_id}")
    return ordered_unique(failures)


def residual_summary(rows: list[dict[str, Any]]) -> dict[str, float]:
    model_residuals = [float(row["model_residual"]) for row in rows if is_finite_number(row.get("model_residual"))]
    comparator_residuals = [float(row["comparator_residual"]) for row in rows if is_finite_number(row.get("comparator_residual"))]
    model = sum(model_residuals) / len(model_residuals) if model_residuals else 0.0
    comparator = sum(comparator_residuals) / len(comparator_residuals) if comparator_residuals else 0.0
    return {
        "model": model,
        "comparator": comparator,
        "superiority_margin": comparator - model,
    }


def uncertainty_interval(rows: list[dict[str, Any]], model_mean: float) -> list[float]:
    residuals = [float(row["model_residual"]) for row in rows if is_finite_number(row.get("model_residual"))]
    if not residuals:
        return [0.0, 0.0]
    return [min(0.0, min(residuals), model_mean), max(residuals + [model_mean])]


def build_pack(rows: list[dict[str, Any]], source: dict[str, Any], formula: Formula, support_allowed: bool) -> dict[str, Any]:
    residuals = residual_summary(rows)
    source_separation = {
        "mode": source.get("mode", "snapshot_replay"),
        "pre_target_lock": source.get("pre_target_lock") is True,
        "target_hidden_until_scoring": source.get("target_hidden_until_scoring") is True,
        "training_sources": ordered_unique([str(row["training_source"]) for row in rows if row.get("training_source")]),
        "target_sources": ordered_unique([str(row["target_source"]) for row in rows if row.get("target_source")]),
    }
    negative_controls = [
        {
            "control_id": row["negative_control_id"],
            "description": row["negative_control_description"],
            "rejected": row.get("negative_control_passed") is True,
        }
        for row in rows
    ]
    if not negative_controls:
        negative_controls = [
            {
                "control_id": "systems-wdi-no-heldout-rows",
                "description": "no heldout WDI rows available for carry-forward control",
                "rejected": False,
            }
        ]
    return {
        "schema_id": grand_factory.EVIDENCE_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "capability_owner": CAPABILITY_OWNER,
        "evidence_pack_id": "OC133-SYSTEMS-WDI-BENCHMARK-CANDIDATE",
        "domain": "systems",
        "source_separation": source_separation,
        "n": len(rows),
        "model_under_test": f"World Bank WDI benchmark formula family selected on training years only: {formula.rule}",
        "comparator_baseline": {
            "name": "WDI carry-forward baseline",
            "prediction_rule": "predict heldout year as the immediately previous training year",
            "pre_registered": True,
        },
        "uncertainty": {
            "metric": "mean absolute residual",
            "method": "deterministic heldout residual envelope",
            "interval": uncertainty_interval(rows, residuals["model"]),
        },
        "residuals": residuals,
        "negative_controls": negative_controls,
        "falsifiers": ordered_unique([str(row["falsifier"]) for row in rows if row.get("falsifier")])
        or ["heldout rows missing; support blocked"],
        "grand_toe_support_allowed": bool(support_allowed),
    }


def mutate_heldout_values(payload: Any, delta: float = 1.0) -> Any:
    mutated = json.loads(json.dumps(payload, ensure_ascii=False))
    rows = payload_rows(mutated)
    latest_by_series: dict[tuple[str, str], int] = {}
    for idx, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        if not is_finite_number(row.get("value")):
            continue
        indicator_obj = row.get("indicator") if isinstance(row.get("indicator"), dict) else {}
        country_obj = row.get("country") if isinstance(row.get("country"), dict) else {}
        key = (
            str(row.get("countryiso3code") or country_obj.get("id") or ""),
            str(indicator_obj.get("id") or ""),
        )
        try:
            year = int(str(row.get("date", "")).strip())
        except ValueError:
            continue
        if key not in latest_by_series or year > int(rows[latest_by_series[key]].get("date")):
            latest_by_series[key] = idx
    for idx in latest_by_series.values():
        row = rows[idx]
        if isinstance(row, dict) and is_finite_number(row.get("value")):
            row["value"] = float(row["value"]) + delta
    return mutated


def build_tamper_tests(payload: Any, snapshot_ref: str, rows: list[dict[str, Any]], selected_formula: Formula) -> list[dict[str, Any]]:
    original_hash = sha256_object(payload)
    mutated = mutate_heldout_values(payload, delta=1.0)
    mutated_hash = sha256_object(mutated)
    try:
        mutated_series = parse_wdi_payload(mutated)
        mutated_formula, _selection, _failures = select_formula(mutated_series)
        mutated_rows, _row_failures = build_rows(mutated_series, snapshot_ref, selected_formula)
        row_hashes_changed = [row.get("row_hash") for row in rows] != [row.get("row_hash") for row in mutated_rows]
        formula_stable = mutated_formula.id == selected_formula.id
    except Exception:
        row_hashes_changed = False
        formula_stable = False
    return [
        {
            "test_id": "systems-wdi-payload-hash-changes-on-heldout-mutation",
            "description": "mutating heldout WDI values must alter canonical payload hash",
            "passed": mutated_hash != original_hash,
        },
        {
            "test_id": "systems-wdi-row-hashes-change-on-heldout-mutation",
            "description": "mutating heldout WDI values must alter recomputed heldout row hashes",
            "passed": row_hashes_changed,
        },
        {
            "test_id": "systems-wdi-formula-selection-target-leakage-control",
            "description": "selected formula must remain stable when only heldout values are mutated",
            "passed": formula_stable,
        },
        {
            "test_id": "systems-wdi-carry-forward-negative-controls",
            "description": "carry-forward baseline must be worse than the selected formula on every heldout row",
            "passed": all(row.get("negative_control_passed") is True for row in rows),
        },
    ]


def evaluate_wdi_payload(
    raw_payload: Any,
    *,
    snapshot_ref: str,
    snapshot_sha256: str,
    requirements: dict[str, Any],
    requirement_failures: list[str] | None = None,
) -> dict[str, Any]:
    requirement_failures = requirement_failures or []
    minimum_n = int(requirements.get("minimum_per_domain_n", 20))
    blockers: list[str] = list(requirement_failures)
    source = extract_source_separation(raw_payload)

    try:
        series = parse_wdi_payload(raw_payload)
    except Exception as exc:
        blockers.append(f"SNAPSHOT_PARSE_FAILED::{exc}")
        series = {}

    formula, formula_selection, formula_failures = select_formula(series)
    rows, row_build_failures = build_rows(series, snapshot_ref, formula)
    row_failures = validate_rows(rows)
    source_failures = validate_source_separation(source, rows, requirements)

    if len(rows) < minimum_n:
        blockers.append(f"N_BELOW_MINIMUM::{len(rows)}/{minimum_n}")
    if residual_summary(rows)["superiority_margin"] <= 0:
        blockers.append("HELDOUT_RESIDUAL_SUPERIORITY_NOT_MET")

    tamper_tests = build_tamper_tests(raw_payload, snapshot_ref, rows, formula) if rows else []
    tamper_failures = [f"TAMPER_TEST_FAILED::{test['test_id']}" for test in tamper_tests if test.get("passed") is not True]

    local_failures = ordered_unique(
        [
            *source_failures,
            *formula_failures,
            *row_build_failures,
            *row_failures,
            *tamper_failures,
        ]
    )
    blockers = ordered_unique([*blockers, *local_failures])

    candidate_support = not blockers
    candidate_pack = build_pack(rows, source, formula, support_allowed=candidate_support)
    candidate_gate_failures = grand_factory.pack_failure_reasons(candidate_pack, requirements)
    support_allowed = candidate_support and not candidate_gate_failures
    pack = build_pack(rows, source, formula, support_allowed=support_allowed)
    final_pack_failures = grand_factory.pack_failure_reasons(pack, requirements)
    blockers = ordered_unique([*blockers, *candidate_gate_failures])

    protocol = {
        "schema_id": PROTOCOL_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "candidate_pack_ref": PACK_REL,
        "candidate_pack_sha256": sha256_object(pack),
        "candidate_pack_hash_policy": PACK_HASH_POLICY,
        "snapshot_ref": snapshot_ref,
        "snapshot_sha256": snapshot_sha256,
        "snapshot_hash_policy": SNAPSHOT_HASH_POLICY,
        "minimum_n": minimum_n,
        "candidate_n": len(rows),
        "source_separation_claim": source,
        "formula_selection": formula_selection,
        "required_protocol_steps": [
            "freeze a WDI payload before scoring and record its hash",
            "declare last_year_heldout_per_series before scoring",
            "select formulas only from pre-heldout training years",
            "score the heldout year once per country/indicator series",
            "compare against a preregistered carry-forward baseline",
            "block support unless N>=20, explicit target separation, heldout superiority, and negative controls all pass",
        ],
        "blockers": blockers,
    }
    tasks = {
        "schema_id": TASKS_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "snapshot_ref": snapshot_ref,
        "snapshot_sha256": snapshot_sha256,
        "snapshot_hash_policy": SNAPSHOT_HASH_POLICY,
        "minimum_n": minimum_n,
        "series_total": len(series),
        "row_total": len(rows),
        "selected_formula": formula.id,
        "formula_selection": formula_selection,
        "rows": rows,
        "blockers": blockers,
    }
    report = {
        "schema_id": REPORT_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "snapshot_ref": snapshot_ref,
        "snapshot_sha256": snapshot_sha256,
        "snapshot_hash_policy": SNAPSHOT_HASH_POLICY,
        "candidate_pack_ref": PACK_REL,
        "candidate_pack_sha256": sha256_object(pack),
        "candidate_pack_hash_policy": PACK_HASH_POLICY,
        "protocol_ref": PROTOCOL_REL,
        "tasks_ref": TASKS_REL,
        "minimum_n": minimum_n,
        "candidate_n": len(rows),
        "missing_n": max(0, minimum_n - len(rows)),
        "selected_formula": {"id": formula.id, "rule": formula.rule},
        "formula_selection": formula_selection,
        "residuals": pack["residuals"],
        "source_validation_failures": source_failures,
        "row_validation_failures": ordered_unique([*row_build_failures, *row_failures]),
        "candidate_gate_failures": candidate_gate_failures,
        "pack_failure_reasons": final_pack_failures,
        "tamper_tests": tamper_tests,
        "tamper_test_total": len(tamper_tests),
        "blockers": blockers,
        "open_blocker_total": len(blockers),
        "blocked_total": len(blockers),
        "grand_toe_support_allowed": support_allowed,
        "verdict": "READY_FOR_PARENT_REGISTRY_REVIEW" if support_allowed else "BLOCKED_PENDING_GENUINE_WDI_BENCHMARK",
        "no_send": True,
        "publish_allowed": False,
    }
    return {
        "tasks": tasks,
        "protocol": protocol,
        "report": report,
        "candidate_pack": pack,
    }


def build_payload(root: Path | None = None, snapshot_ref: str | None = None) -> dict[str, Any]:
    root = (root or repo_root()).resolve()
    snapshot_ref = snapshot_ref or SNAPSHOT_REF
    requirements, requirement_failures = load_requirements(root)
    snapshot_path = resolve_under_root(root, snapshot_ref)
    if not snapshot_path.exists():
        blockers = ["SNAPSHOT_MISSING", *requirement_failures]
        empty_pack = build_pack([], {"mode": "snapshot_replay"}, FORMULA_FAMILIES[0], support_allowed=False)
        return {
            "tasks": {"schema_id": TASKS_SCHEMA_ID, "rows": [], "blockers": blockers},
            "protocol": {"schema_id": PROTOCOL_SCHEMA_ID, "blockers": blockers},
            "report": {
                "schema_id": REPORT_SCHEMA_ID,
                "release_id": RELEASE_ID,
                "version": VERSION,
                "capability_owner": CAPABILITY_OWNER,
                "snapshot_ref": snapshot_ref,
                "verdict": "BLOCKED_MISSING_SNAPSHOT",
                "grand_toe_support_allowed": False,
                "blockers": blockers,
                "open_blocker_total": len(blockers),
            },
            "candidate_pack": empty_pack,
        }
    raw_payload = read_json(snapshot_path)
    return evaluate_wdi_payload(
        raw_payload,
        snapshot_ref=snapshot_ref,
        snapshot_sha256=sha256_file_text(snapshot_path),
        requirements=requirements,
        requirement_failures=requirement_failures,
    )


def render_readme(payload: dict[str, Any]) -> str:
    report = payload["report"]
    lines = [
        "# Systems WDI Benchmark Factory",
        "",
        f"Verdict: `{report.get('verdict')}`",
        f"Grand TOE support allowed: `{report.get('grand_toe_support_allowed')}`",
        f"Rows: `{report.get('candidate_n', 0)}`",
        f"Minimum N: `{report.get('minimum_n', 0)}`",
        f"Selected formula: `{report.get('selected_formula', {}).get('id', 'unknown')}`",
        "",
        "This artifact is a deterministic WDI benchmark candidate. It blocks support unless the payload declares an explicit heldout split, formula selection uses training years only, heldout residuals beat carry-forward controls, N is sufficient, and tamper controls pass.",
        "",
        "## Open blockers",
    ]
    blockers = report.get("blockers", [])
    if blockers:
        lines.extend(f"- `{item}`" for item in blockers)
    else:
        lines.append("- `none`")
    lines.extend(["", "## Tamper tests"])
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
    for rel, payload in checks:
        path = root / rel
        if not path.exists():
            failures.append(f"missing::{rel}")
            continue
        if read_json(path) != payload:
            failures.append(f"mismatch::{rel}")
    readme_path = root / README_REL
    if not readme_path.exists():
        failures.append(f"missing::{README_REL}")
    elif readme_path.read_text(encoding="utf-8") != render_readme(expected):
        failures.append(f"mismatch::{README_REL}")
    return failures


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build systems/WDI benchmark artifacts.")
    parser.add_argument("--root", default=str(repo_root()), help="repository root")
    parser.add_argument("--snapshot-ref", default=SNAPSHOT_REF, help="World Bank WDI payload reference")
    parser.add_argument("--write", action="store_true", help="write report, protocol, tasks, pack, and README")
    parser.add_argument("--check", action="store_true", help="check persisted artifacts against recomputed payloads")
    parser.add_argument("--allow-blocked-exit-zero", action="store_true", help="exit zero when the candidate remains blocked")
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
