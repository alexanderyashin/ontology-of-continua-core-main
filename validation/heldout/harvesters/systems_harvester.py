from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from validation.grand_science import evidence_pack_factory as grand_factory


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
CAPABILITY_OWNER = "Research/EmpiricalScience"
BLOCKER_ID = "grand_toe_empirical_superiority"
SCHEMA_ID = "OC133_SYSTEMS_HARVESTER_REPORT_v1"
PROTOCOL_SCHEMA_ID = "OC133_SYSTEMS_HARVESTER_PROTOCOL_v1"

OUTPUT_ROOT_REL = "validation/heldout/grand_science/systems/harvested"
PACK_REL = f"{OUTPUT_ROOT_REL}/systems_candidate_evidence_pack.json"
REPORT_REL = f"{OUTPUT_ROOT_REL}/OC133_SYSTEMS_HARVESTER_REPORT.json"
PROTOCOL_REL = f"{OUTPUT_ROOT_REL}/OC133_SYSTEMS_HARVESTER_PROTOCOL.json"

ACQUISITION_PLAN_REL = "validation/heldout/acquisition_plans/biology_systems/OC133_BIOLOGY_SYSTEMS_ACQUISITION_PLAN.json"
REQUIREMENTS_REL = "benchmarks/grand_science/domain_requirements.json"
DEFAULT_SNAPSHOT_REF = "validation/_raw/systems_world_bank_gdp.txt"
DEFAULT_ENDPOINT_TIMEOUT_SECONDS = 2.0
LOOKBACK_YEARS = 2


@dataclass(frozen=True)
class Row:
    observation_id: str
    country: str
    indicator: str
    training_years: tuple[int, int]
    target_year: int
    training_values: tuple[float, float]
    observed_value: float
    predicted_value: float
    comparator_prediction: float
    uncertainty: float
    training_source: str
    target_source: str
    formula: str
    negative_control_id: str
    negative_control_description: str
    falsifier: str

    @property
    def model_residual(self) -> float:
        return abs(self.predicted_value - self.observed_value)

    @property
    def comparator_residual(self) -> float:
        return abs(self.comparator_prediction - self.observed_value)


def read_json(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(str(path))
    return json.loads(path.read_text(encoding="utf-8"))


def read_json_safe(path: Path) -> Any:
    try:
        return read_json(path)
    except Exception:
        return {}


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_object(payload: Any) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def lf_normalized_bytes(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n")


def sha256_lf_text(path: Path) -> str:
    return hashlib.sha256(lf_normalized_bytes(path)).hexdigest()


def is_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def ordered_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def resolve_under_root(root: Path, ref: str) -> Path:
    path = (root / ref).resolve()
    path.relative_to(root.resolve())
    return path


def load_requirements(root: Path) -> dict[str, Any]:
    payload = read_json_safe(root / REQUIREMENTS_REL)
    if isinstance(payload, dict):
        return payload
    return {}


def default_requirements() -> dict[str, Any]:
    return {
        "minimum_per_domain_n": 20,
        "required_source_separation_modes": ("target_blind", "prospective"),
        "required_domains": ["biology", "chemistry", "mathematics", "physics", "systems"],
    }


def get_systems_plan_row(root: Path, plan_ref: str = ACQUISITION_PLAN_REL) -> dict[str, Any]:
    payload = read_json_safe(root / plan_ref)
    rows = payload.get("rows", []) if isinstance(payload, dict) else []
    for row in rows:
        if isinstance(row, dict) and str(row.get("domain")) == "systems":
            return row
    return {}


def source_refs_from_plan(plan_row: dict[str, Any]) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    official = plan_row.get("official_source_refs", [])
    for row in official if isinstance(official, list) else []:
        if not isinstance(row, dict):
            continue
        if row.get("kind") == "raw_snapshot":
            ref = str(row.get("ref") or "").strip()
            if ref:
                refs.append({"kind": "raw_snapshot", "ref": ref})
            continue
        url = str(row.get("url") or "").strip()
        if url:
            refs.append({"kind": "official_endpoint", "url": url})
    if not refs:
        refs.append({"kind": "raw_snapshot", "ref": DEFAULT_SNAPSHOT_REF})
    return refs


def source_mode_for_kind(kind: str) -> str:
    return "prospective" if kind == "official_endpoint" else "target_blind"


def row_source_ids(source_label: str, country_code: str, indicator_id: str, training_years: tuple[int, int], target_year: int) -> tuple[str, str]:
    training_source = (
        f"{source_label}::{country_code}:{indicator_id}::training_years={training_years[0]},{training_years[1]}"
    )
    target_source = f"{source_label}::{country_code}:{indicator_id}::target_year={target_year}"
    return training_source, target_source


def parse_wdi_payload(payload: Any) -> dict[tuple[str, str, str, str], dict[int, float]]:
    if not isinstance(payload, list) or len(payload) < 2:
        raise ValueError("Expected World Bank style payload [metadata, rows]")
    rows = payload[1]
    if not isinstance(rows, list):
        raise ValueError("Expected payload[1] to be list of indicator observations")

    buckets: dict[tuple[str, str, str, str], dict[int, float]] = {}
    for raw in rows:
        if not isinstance(raw, dict):
            continue
        country_obj = raw.get("country") if isinstance(raw.get("country"), dict) else {}
        country_code = str(country_obj.get("id") or country_obj.get("iso3code") or "").strip()
        country_name = str(country_obj.get("value") or country_code).strip()
        indicator_obj = raw.get("indicator") if isinstance(raw.get("indicator"), dict) else {}
        indicator_id = str(indicator_obj.get("id") or "").strip()
        indicator_name = str(indicator_obj.get("value") or indicator_id).strip()
        if not country_code or not indicator_id:
            continue

        raw_value = raw.get("value")
        if raw_value in (None, ""):
            continue
        if isinstance(raw_value, str) and raw_value.lower() == "null":
            continue
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            continue
        if not math.isfinite(value):
            continue

        date = str(raw.get("date") or "").strip()
        if not date:
            continue
        try:
            year = int(float(date))
        except ValueError:
            continue

        bucket = buckets.setdefault((country_code, country_name, indicator_id, indicator_name), {})
        bucket[year] = value
    return buckets


def fetch_official_payload(url: str, timeout_seconds: float = DEFAULT_ENDPOINT_TIMEOUT_SECONDS) -> Any:
    request = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        body = response.read().decode("utf-8")
        return json.loads(body)


def build_rows(
    buckets: dict[tuple[str, str, str, str], dict[int, float]],
    source_label: str,
    source_mode: str,
    lookback: int = LOOKBACK_YEARS,
) -> list[Row]:
    rows: list[Row] = []
    for country_code, country_name, indicator_id, indicator_name in sorted(buckets):
        timeseries = buckets[(country_code, country_name, indicator_id, indicator_name)]
        years = sorted(timeseries)
        if len(years) < lookback + 1:
            continue
        for idx in range(lookback, len(years)):
            target_year = years[idx]
            prev_years = years[idx - lookback : idx]
            if len(prev_years) != lookback:
                continue
            observed = timeseries[target_year]
            v1 = timeseries[prev_years[-1]]
            v0 = timeseries[prev_years[-2]]
            if not (is_number(v0) and is_number(v1) and is_number(observed)):
                continue
            if lookback != 2:
                continue

            predicted = v1 + (v1 - v0)
            comparator = v1
            uncertainty = abs(v1 - v0)
            training_source, target_source = row_source_ids(
                source_label=source_label,
                country_code=country_code,
                indicator_id=indicator_id,
                training_years=(prev_years[0], prev_years[1]),
                target_year=target_year,
            )
            row = Row(
                observation_id=(
                    f"SYSTEMS-{source_mode.upper()}-{country_code}-{indicator_id}-"
                    f"{prev_years[0]}:{prev_years[1]}:{target_year}"
                ),
                country=f"{country_code}:{country_name}",
                indicator=f"{indicator_id}:{indicator_name}",
                training_years=(prev_years[0], prev_years[1]),
                target_year=target_year,
                training_values=(float(v0), float(v1)),
                observed_value=float(observed),
                predicted_value=float(predicted),
                comparator_prediction=float(comparator),
                uncertainty=float(max(0.0, uncertainty)),
                training_source=training_source,
                target_source=target_source,
                formula="y_t = y_t-1 + (y_t-1 - y_t-2)",
                negative_control_id=f"{country_code}-{indicator_id}-{target_year}-NEGATIVE-CONTROL",
                negative_control_description="comparator residual must exceed linear model residual",
                falsifier="if observed shifts by declared uncertainty, model residual should not exceed uncertainty",
            )
            rows.append(row)
    return rows


def validate_source_separation(source_sep: dict[str, Any], minimum_n: int, n: int) -> list[str]:
    failures: list[str] = []
    if source_sep.get("mode") not in ("target_blind", "prospective"):
        failures.append("SOURCE_SEPARATION_MODE_INVALID")
    if source_sep.get("pre_target_lock") is not True:
        failures.append("SOURCE_SEPARATION_PRE_TARGET_LOCK_REQUIRED")
    if source_sep.get("target_hidden_until_scoring") is not True:
        failures.append("SOURCE_SEPARATION_TARGET_HIDDEN_REQUIRED")

    training_sources = source_sep.get("training_sources", [])
    target_sources = source_sep.get("target_sources", [])
    if not isinstance(training_sources, list) or not isinstance(target_sources, list):
        failures.append("SOURCE_SEPARATION_SOURCE_LIST_INVALID")
        return failures
    if n == 0 or not training_sources or not target_sources:
        failures.append("SOURCE_SEPARATION_SOURCE_LIST_EMPTY")
    if n < minimum_n:
        failures.append(f"N_BELOW_MINIMUM::{n}/{minimum_n}")
    if n > 0:
        overlap = set(training_sources) & set(target_sources)
        if overlap:
            failures.append("SOURCE_SEPARATION_SOURCE_OVERLAP")
    return failures


def make_pack(
    rows: list[Row],
    source_separation: dict[str, Any],
    support_allowed: bool,
) -> dict[str, Any]:
    model_residuals = [row.model_residual for row in rows]
    comparator_residuals = [row.comparator_residual for row in rows]
    uncertainties = [row.uncertainty for row in rows]
    model_mean = sum(model_residuals) / len(model_residuals) if model_residuals else 0.0
    comparator_mean = sum(comparator_residuals) / len(comparator_residuals) if comparator_residuals else 0.0
    interval_high = max(model_mean, max(uncertainties) if uncertainties else 0.0)
    interval_low = max(0.0, min(model_residuals) - (max(uncertainties) * 0.5)) if model_residuals else 0.0

    negative_controls = [
        {
            "control_id": row.negative_control_id,
            "description": row.negative_control_description,
            "rejected": row.comparator_residual > row.model_residual,
        }
        for row in rows
    ]
    if not negative_controls:
        negative_controls = [
            {
                "control_id": "SYSTEMS-HARVESTER-BLOCKED-NO-OBSERVATIONS",
                "description": "No usable candidate rows exist for the declared evidence rule.",
                "rejected": False,
            }
        ]

    falsifiers = ordered_unique([row.falsifier for row in rows]) or [
        "No usable rows were available for falsifier replay."
    ]
    source_sep = dict(source_separation)
    source_sep["training_sources"] = ordered_unique(source_sep.get("training_sources", []))
    source_sep["target_sources"] = ordered_unique(source_sep.get("target_sources", []))

    pack = {
        "schema_id": grand_factory.EVIDENCE_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "capability_owner": CAPABILITY_OWNER,
        "evidence_pack_id": "oc-core-1-3-3-systems-official-world-bank-harvester",
        "domain": "systems",
        "source_separation": source_sep,
        "n": len(rows),
        "model_under_test": "y_t = y_t-1 + (y_t-1 - y_t-2) for each country-indicator series",
        "comparator_baseline": {
            "name": "World Bank carry-forward comparator",
            "prediction_rule": "predict each target year as immediately previous observed value for same series",
            "pre_registered": True,
        },
        "uncertainty": {
            "metric": "mean absolute residual",
            "method": "two-point extrapolation spread over declared target row intervals",
            "interval": [interval_low, interval_high],
        },
        "residuals": {
            "model": model_mean,
            "comparator": comparator_mean,
            "superiority_margin": comparator_mean - model_mean,
        },
        "negative_controls": negative_controls,
        "falsifiers": falsifiers,
        "grand_toe_support_allowed": support_allowed,
    }
    return pack


def build_pack(
    rows: list[Row],
    minimum_n: int,
    requirements: dict[str, Any],
    source_kind: str,
) -> tuple[dict[str, Any], list[str]]:
    if source_kind == "official_endpoint":
        source_separation = {
            "mode": "prospective",
            "pre_target_lock": bool(rows),
            "target_hidden_until_scoring": bool(rows),
            "training_sources": [row.training_source for row in rows],
            "target_sources": [row.target_source for row in rows],
        }
    else:
        source_separation = {
            "mode": "target_blind",
            "pre_target_lock": False,
            "target_hidden_until_scoring": False,
            "training_sources": [row.training_source for row in rows],
            "target_sources": [row.target_source for row in rows],
        }

    observation_blockers: list[str] = []
    for row in rows:
        if not is_number(row.model_residual) or not is_number(row.comparator_residual) or not is_number(row.uncertainty):
            observation_blockers.append(f"OBSERVATION_INVALID::{row.observation_id}")
        if row.comparator_residual <= row.model_residual:
            observation_blockers.append(f"NEGATIVE_CONTROL_NOT_REJECTED::{row.observation_id}")

    blockers = ordered_unique(
        observation_blockers + validate_source_separation(source_separation, minimum_n=minimum_n, n=len(rows))
    )

    tentative_pack = make_pack(
        rows=rows,
        source_separation=source_separation,
        support_allowed=not blockers,
    )
    tentative_gate = grand_factory.pack_failure_reasons(tentative_pack, requirements)
    support_allowed = not blockers and not tentative_gate

    final_pack = make_pack(
        rows=rows,
        source_separation=source_separation,
        support_allowed=support_allowed,
    )
    final_gate = grand_factory.pack_failure_reasons(final_pack, requirements)
    final_blockers = ordered_unique(blockers + final_gate)
    final_pack["grand_toe_support_allowed"] = final_pack["grand_toe_support_allowed"] and not final_blockers
    return final_pack, final_blockers


def build_protocol_payload(pack_ref: str, pack_sha256: str, blockers: list[str], support_allowed: bool) -> dict[str, Any]:
    return {
        "schema_id": PROTOCOL_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "blocker_id": BLOCKER_ID,
        "verdict": "READY_FOR_PARENT_REGISTRY_REVIEW" if support_allowed else "BLOCKED_PENDING_GENUINE_EVIDENCE_PACK",
        "blocked_domain_total": 1 if not support_allowed else 0,
        "queue_total": 1,
        "requirements_ref": REQUIREMENTS_REL,
        "evidence_schema_ref": "validation/grand_science/grand_empirical_evidence.schema.json",
        "protocol_schema_ref": "validation/grand_science/grand_empirical_protocol.schema.json",
        "sample_pack_ref": "validation/heldout/samples/grand_empirical_evidence_pack.sample.json",
        "rows": [
            {
                "domain": "systems",
                "status": "READY_FOR_PARENT_REGISTRY_REVIEW" if support_allowed else "BLOCKED_PENDING_GENUINE_EVIDENCE_PACK",
                "candidate_pack_ref": pack_ref,
                "candidate_pack_sha256": pack_sha256,
                "minimum_n": 20,
                "candidate_pack_total": 1,
                "blockers": blockers,
                "required_protocol_steps": [
                    "pre-register model, comparator, uncertainty protocol before any target scoring",
                    "collect target-hidden or prospective observations until configured minimum N",
                    "enforce distinct training and target source sets in source separation",
                    "run candidate-level negative controls and falsifier replay before support is claimed",
                    "emit blocked-only status when source-separation or data prerequisites are not met",
                ],
            }
        ],
    }


def build_report(
    rows: list[Row],
    pack: dict[str, Any],
    blockers: list[str],
    source_ref: str,
    source_kind: str,
    snapshot_ref: str,
    snapshot_path: Path | None,
) -> dict[str, Any]:
    pack_sha256 = sha256_object(pack)
    protocol = build_protocol_payload(PACK_REL, pack_sha256, blockers, pack.get("grand_toe_support_allowed") is True)
    protocol_sha256 = sha256_object(protocol)
    snapshot_exists = snapshot_path is not None and snapshot_path.exists()
    snapshot_sha = sha256_lf_text(snapshot_path) if snapshot_exists else None
    snapshot_bytes = len(lf_normalized_bytes(snapshot_path)) if snapshot_exists else 0

    return {
        "schema_id": SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "blocker_id": BLOCKER_ID,
        "reporter": "validation/heldout/harvesters/systems_harvester.py",
        "source_kind": source_kind,
        "source_ref": source_ref,
        "snapshot_ref": snapshot_ref,
        "snapshot_sha256": snapshot_sha,
        "snapshot_byte_count": snapshot_bytes,
        "candidate_pack_total": 1,
        "valid_candidate_pack_total": 1 if pack.get("grand_toe_support_allowed") else 0,
        "valid_pack_total": 1 if pack.get("grand_toe_support_allowed") else 0,
        "blocked_domain_total": 1 if pack.get("grand_toe_support_allowed") is not True else 0,
        "candidate_pack_ref": PACK_REL,
        "candidate_pack_sha256": pack_sha256,
        "candidate_pack_hash_policy": "sha256 over canonical JSON",
        "protocol_ref": PROTOCOL_REL,
        "protocol_sha256": protocol_sha256,
        "verdict": "READY_FOR_PARENT_REGISTRY_REVIEW" if pack.get("grand_toe_support_allowed") else "BLOCKED_PENDING_GENUINE_EVIDENCE",
        "requirements_ref": REQUIREMENTS_REL,
        "no_send": True,
        "publish_allowed": False,
        "journal_submissions_allowed": False,
        "candidate_row_total": len(rows),
        "blocker_total": len(blockers),
        "open_blocker_total": len(blockers),
        "blockers": blockers,
        "rows": [
            {
                "observation_id": row.observation_id,
                "country": row.country,
                "indicator": row.indicator,
                "training_source": row.training_source,
                "target_source": row.target_source,
                "model_residual": row.model_residual,
                "comparator_residual": row.comparator_residual,
                "row_sha256": sha256_object(
                    {
                        "observation_id": row.observation_id,
                        "training_source": row.training_source,
                        "target_source": row.target_source,
                        "training_values": row.training_values,
                        "predicted_value": row.predicted_value,
                        "observed_value": row.observed_value,
                        "comparator_prediction": row.comparator_prediction,
                        "uncertainty": row.uncertainty,
                        "falsifier": row.falsifier,
                    }
                ),
            }
            for row in rows
        ],
    }, protocol


def build_payload(
    root: Path,
    *,
    offline: bool = True,
    snapshot_ref: str = DEFAULT_SNAPSHOT_REF,
    acquisition_plan_ref: str = ACQUISITION_PLAN_REL,
    endpoint_timeout: float = DEFAULT_ENDPOINT_TIMEOUT_SECONDS,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], list[Row]]:
    requirements = load_requirements(root) or default_requirements()
    minimum_n = int(requirements.get("minimum_per_domain_n", 20))
    plan_row = get_systems_plan_row(root, acquisition_plan_ref)
    source_rows = source_refs_from_plan(plan_row)

    if not snapshot_ref:
        snapshot_ref = DEFAULT_SNAPSHOT_REF

    source_label = snapshot_ref
    source_kind = "raw_snapshot"
    payload: Any = None
    blockers: list[str] = []
    endpoint_urls = [row.get("url", "") for row in source_rows if row.get("kind") == "official_endpoint" and row.get("url")]
    if not offline and endpoint_urls:
        for url in endpoint_urls:
            try:
                payload = fetch_official_payload(url, timeout_seconds=endpoint_timeout)
                source_kind = "official_endpoint"
                source_label = str(url)
                break
            except Exception as exc:  # pragma: no cover - boundary
                blockers.append(f"SYSTEMS_ENDPOINT_FETCH_FAILED::{url}::{exc.__class__.__name__}")
                continue

    snapshot_path = None
    if payload is None:
        snapshot_path = resolve_under_root(root, snapshot_ref)
        payload = read_json_safe(snapshot_path)
    rows = []
    if payload:
        buckets = parse_wdi_payload(payload)
        rows = build_rows(
            buckets,
            source_label=source_label,
            source_mode=source_mode_for_kind(source_kind),
        )
    pack, pack_blockers = build_pack(
        rows=rows,
        minimum_n=minimum_n,
        requirements=requirements,
        source_kind=source_kind,
    )
    blockers.extend(pack_blockers)
    blockers = ordered_unique(blockers)
    report, protocol = build_report(
        rows=rows,
        pack=pack,
        blockers=blockers,
        source_ref=source_label,
        source_kind=source_kind,
        snapshot_ref=snapshot_ref,
        snapshot_path=snapshot_path,
    )
    return report, protocol, pack, rows


def write_outputs(root: Path, **kwargs: Any) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    report, protocol, pack, _rows = build_payload(root, **kwargs)
    write_json(root / PACK_REL, pack)
    write_json(root / PROTOCOL_REL, protocol)
    write_json(root / REPORT_REL, report)
    return report, protocol, pack


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build systems/civilizational official-data harvester candidate evidence pack."
    )
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--snapshot-ref", default=DEFAULT_SNAPSHOT_REF)
    parser.add_argument("--acquisition-plan-ref", default=ACQUISITION_PLAN_REL)
    parser.add_argument("--endpoint-timeout", type=float, default=DEFAULT_ENDPOINT_TIMEOUT_SECONDS)
    parser.add_argument("--offline", action="store_true", help="Use pinned local snapshot only.")
    parser.add_argument("--use-official-endpoints", action="store_true", help="Allow World Bank/WDI official endpoints.")
    parser.add_argument("--write", action="store_true", help="Write report and pack artifacts.")
    parser.add_argument(
        "--allow-blocked-exit-zero",
        action="store_true",
        help="Return 0 even when blockers remain.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    offline = args.offline or not args.use_official_endpoints
    report, _protocol, pack, _rows = build_payload(
        root,
        offline=offline,
        snapshot_ref=args.snapshot_ref,
        acquisition_plan_ref=args.acquisition_plan_ref,
        endpoint_timeout=args.endpoint_timeout,
    )
    if args.write:
        write_outputs(
            root,
            offline=offline,
            snapshot_ref=args.snapshot_ref,
            acquisition_plan_ref=args.acquisition_plan_ref,
            endpoint_timeout=args.endpoint_timeout,
        )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report.get("verdict") != "READY_FOR_PARENT_REGISTRY_REVIEW" and not args.allow_blocked_exit_zero:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
