from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from validation.grand_science import evidence_pack_factory as grand_factory


RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
CAPABILITY_OWNER = "Research/EmpiricalScience"
SCHEMA_ID = "OC133_BIOLOGY_NCBI_BENCHMARK_v1"
TASKS_SCHEMA_ID = "OC133_BIOLOGY_NCBI_BENCHMARK_TASKS_v1"
REPORT_SCHEMA_ID = "OC133_BIOLOGY_NCBI_BENCHMARK_REPORT_v1"
PROTOCOL_SCHEMA_ID = "OC133_BIOLOGY_NCBI_BENCHMARK_PROTOCOL_v1"
PLANNER_REF = "tools/oc133_biology_ncbi_benchmark_factory.py"

REQUIREMENTS_REL = "benchmarks/grand_science/domain_requirements.json"
DEFAULT_REQUIREMENTS: dict[str, Any] = {
    "minimum_per_domain_n": 20,
    "required_source_separation_modes": ["target_blind", "prospective"],
}

OUTPUT_ROOT_REL = "validation/heldout/grand_science/biology/ncbi_benchmark"
TASKS_REL = f"{OUTPUT_ROOT_REL}/OC133_BIOLOGY_NCBI_BENCHMARK_TASKS.json"
REPORT_REL = f"{OUTPUT_ROOT_REL}/OC133_BIOLOGY_NCBI_BENCHMARK_REPORT.json"
PROTOCOL_REL = f"{OUTPUT_ROOT_REL}/OC133_BIOLOGY_NCBI_BENCHMARK_PROTOCOL.json"
CANDIDATE_PACK_REL = f"{OUTPUT_ROOT_REL}/OC133_BIOLOGY_NCBI_BENCHMARK_CANDIDATE_PACK.json"
README_REL = f"{OUTPUT_ROOT_REL}/README.md"

DEFAULT_SNAPSHOT_REF = "validation/_raw/biology_ncbi_geo_platform.txt"
SNAPSHOT_HASH_POLICY = "LF_NORMALIZED_TEXT_SNAPSHOT_HASH"
ROW_HASH_POLICY = "sha256 over sorted JSON row payload"
PACK_HASH_POLICY = "sha256 over canonical JSON"

DEFAULT_SUPPORT_POLICY = (
    "This benchmark emits only target-blind or prospective replay evidence. It does not support broad biological mechanism claims."
)


def repo_root() -> Path:
    return ROOT


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def resolve_under_root(root: Path, ref: str) -> Path:
    path = (root / ref).resolve()
    path.relative_to(root.resolve())
    return path


def lf_bytes(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_object(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def ordered_unique(values: list[Any]) -> list[Any]:
    seen: set[Any] = set()
    out: list[Any] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        if isinstance(value, bool):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def is_number(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def as_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def as_int(value: Any, default: int = 0) -> int:
    try:
        if isinstance(value, bool):
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def load_requirements(root: Path) -> tuple[dict[str, Any], list[str]]:
    path = root / REQUIREMENTS_REL
    if not path.exists():
        return {**DEFAULT_REQUIREMENTS}, ["REQUIREMENTS_MISSING::using_defaults"]
    payload = read_json(path)
    if not isinstance(payload, dict):
        return {**DEFAULT_REQUIREMENTS}, ["REQUIREMENTS_NOT_OBJECT::using_defaults"]
    requirements: dict[str, Any] = {**DEFAULT_REQUIREMENTS}
    requirements.update(payload)
    return requirements, []


def parse_idlist(raw_idlist: Any) -> tuple[list[str], list[str]]:
    if not isinstance(raw_idlist, list):
        return [], ["COUNT_TASK_IDLIST_MISSING_OR_INVALID"]
    parsed: list[str] = []
    blockers: list[str] = []
    for idx, value in enumerate(raw_idlist, start=1):
        try:
            parsed.append(as_str(value))
        except Exception:
            blockers.append(f"COUNT_TASK_IDLIST_ITEM_INVALID::{idx}")
    return parsed, blockers


def parse_count_task(snapshot_payload: dict[str, Any], snapshot_ref: str) -> tuple[dict[str, Any] | None, list[str]]:
    esearch = snapshot_payload.get("esearchresult")
    if not isinstance(esearch, dict):
        return None, ["COUNT_TASK_MISSING_ESearchresult"]
    idlist, idlist_blockers = parse_idlist(esearch.get("idlist"))
    retstart = as_int(esearch.get("retstart"), 0)
    retmax = as_int(esearch.get("retmax"), len(idlist))
    total_count = as_int(esearch.get("count"), retmax)
    visible = as_str(snapshot_payload.get("count_task", {}).get("formula"))
    if not visible:
        formula = "retstart + len(idlist)"
    else:
        formula = visible

    predicted = as_float(
        snapshot_payload.get("count_task", {}).get("predicted_value"),
        as_float(retstart + len(idlist), 0.0),
    )
    observed = as_float(snapshot_payload.get("count_task", {}).get("observed_value"), float(retmax))
    comparator_prediction = as_float(
        snapshot_payload.get("count_task", {}).get("comparator_prediction"),
        float(total_count) + 1.0,
    )
    uncertainty = as_float(snapshot_payload.get("count_task", {}).get("uncertainty"), 0.0)
    comparator_pre = bool(snapshot_payload.get("count_task", {}).get("comparator_pre_registered"))
    row: dict[str, Any] = {
        "observation_id": "BIOLOGY-NCBI-COUNT-001",
        "task_type": "count",
        "claim_id": "OC133-TB-NCBI-COUNT-001",
        "training_source": f"{snapshot_ref}::training::esearchresult::retstart+idlist",
        "target_source": f"{snapshot_ref}::target::esearchresult::retmax",
        "formula": formula,
        "predicted_value": predicted,
        "observed_value": observed,
        "comparator_prediction": comparator_prediction,
        "comparator_pre_registered": comparator_pre,
        "uncertainty": uncertainty,
        "negative_control_id": "BIOLOGY-NCBI-COUNT-CONTROL-REPLAY",
        "negative_control_description": "replace the GEO replay formula with a comparator and require strictly larger residual",
        "falsifier": "count replay residual exceeds declared uncertainty or comparator is not worse than model residual",
    }
    row["model_residual"] = abs(row["predicted_value"] - row["observed_value"])
    row["comparator_residual"] = abs(row["comparator_prediction"] - row["observed_value"])
    failures = [f"COUNT_TASK_INVALID_RETSTART::{retstart}"] if not isinstance(esearch.get("retstart"), (str, int)) else []
    if observed < 0:
        failures.append(f"COUNT_TASK_NEGATIVE_OBSERVED::{observed}")
    return row, ordered_unique([*idlist_blockers, *failures])


def parse_metadata_tasks(snapshot_payload: dict[str, Any], snapshot_ref: str) -> tuple[list[dict[str, Any]], list[str]]:
    raw_rows = snapshot_payload.get("metadata_rows")
    if not isinstance(raw_rows, list):
        return [], []
    rows: list[dict[str, Any]] = []
    failures: list[str] = []
    for idx, raw_row in enumerate(raw_rows, start=1):
        if not isinstance(raw_row, dict):
            failures.append(f"METADATA_TASK_NOT_OBJECT::{idx}")
            continue
        observed = as_float(raw_row.get("observed_value"), as_float(raw_row.get("value"), 0.0))
        predicted = as_float(
            raw_row.get("predicted_value"),
            as_float(len(as_str(raw_row.get("record_id"), "")) + len(as_str(raw_row.get("platform", "")))),
        )
        comparator_prediction = as_float(
            raw_row.get("comparator_prediction"),
            max(observed + 1.0, predicted + 1.0),
        )
        formula = as_str(raw_row.get("formula"), "len(record_id) + len(platform)")
        uncertainty = as_float(raw_row.get("uncertainty"), 0.0)
        comparator_pre_registered = bool(raw_row.get("comparator_pre_registered"))
        row = {
            "observation_id": as_str(raw_row.get("observation_id"), f"BIOLOGY-NCBI-METADATA-{idx:04d}"),
            "task_type": "metadata",
            "claim_id": f"OC133-TB-NCBI-METADATA-{idx:04d}",
            "training_source": as_str(
                raw_row.get("training_source"),
                f"{snapshot_ref}::training::metadata::{as_str(raw_row.get('record_id'), str(idx)):>04s}",
            ),
            "target_source": as_str(
                raw_row.get("target_source"),
                f"{snapshot_ref}::target::metadata::{as_str(raw_row.get('record_id'), str(idx)):>04s}",
            ),
            "formula": formula,
            "predicted_value": predicted,
            "observed_value": observed,
            "comparator_prediction": comparator_prediction,
            "comparator_pre_registered": comparator_pre_registered,
            "uncertainty": uncertainty,
            "negative_control_id": as_str(raw_row.get("negative_control_id"), f"BIOLOGY-NCBI-METADATA-CONTROL-{idx:04d}"),
            "negative_control_description": as_str(
                raw_row.get("negative_control_description"),
                "replace replay comparator prediction by a stronger comparator and require larger residual",
            ),
            "falsifier": as_str(
                raw_row.get("falsifier"),
                "metadata replay residual exceeds declared uncertainty or comparator is not worse",
            ),
        }
        row["model_residual"] = abs(row["predicted_value"] - row["observed_value"])
        row["comparator_residual"] = abs(row["comparator_prediction"] - row["observed_value"])
        rows.append(row)
    return rows, failures


def load_snapshot(
    root: Path,
    snapshot_ref: str | None,
) -> tuple[dict[str, Any] | None, list[str], Path | None]:
    ref = snapshot_ref or DEFAULT_SNAPSHOT_REF
    path = resolve_under_root(root, ref)
    if not path.exists():
        return None, [f"SNAPSHOT_MISSING::{ref}"], None
    try:
        payload = read_json(path)
    except Exception as exc:
        return None, [f"SNAPSHOT_PARSE_ERROR::{exc.__class__.__name__}"], path
    if not isinstance(payload, dict):
        return None, ["SNAPSHOT_NOT_OBJECT"], path
    return payload, [], path


def normalize_source_separation(snapshot_payload: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    raw = snapshot_payload.get("source_separation")
    if not isinstance(raw, dict):
        return (
            {
                "mode": "snapshot_replay",
                "pre_target_lock": False,
                "target_hidden_until_scoring": False,
                "kind": "snapshot_replay",
                "training_sources": [],
                "target_sources": [],
            },
            ["SOURCE_SEPARATION_MISSING::defaulting_to_snapshot_replay"],
        )
    return (
        {
            "mode": as_str(raw.get("mode"), "snapshot_replay"),
            "pre_target_lock": bool(raw.get("pre_target_lock")),
            "target_hidden_until_scoring": bool(raw.get("target_hidden_until_scoring")),
            "kind": as_str(raw.get("kind"), "snapshot_replay"),
            "training_sources": raw.get("training_sources", []),
            "target_sources": raw.get("target_sources", []),
        },
        [],
    )


def validate_source_separation(
    source: dict[str, Any],
    requirements: dict[str, Any],
    minimum_n: int,
    current_n: int,
) -> tuple[list[str], dict[str, Any]]:
    blockers: list[str] = []
    allowed_modes = [as_str(item) for item in requirements.get("required_source_separation_modes", ["target_blind", "prospective"])]
    normalized = {
        "mode": source.get("mode"),
        "pre_target_lock": bool(source.get("pre_target_lock")),
        "target_hidden_until_scoring": bool(source.get("target_hidden_until_scoring")),
        "kind": source.get("kind", "snapshot_replay"),
        "training_sources": ordered_unique([as_str(item) for item in source.get("training_sources", [])]),
        "target_sources": ordered_unique([as_str(item) for item in source.get("target_sources", [])]),
    }

    if normalized["mode"] not in allowed_modes:
        blockers.append(f"SOURCE_SEPARATION_MODE_NOT_ALLOWED::{normalized['mode']}")
    if normalized["pre_target_lock"] is not True:
        blockers.append("PRE_TARGET_LOCK_REQUIRED")
    if normalized["target_hidden_until_scoring"] is not True:
        blockers.append("TARGET_HIDDEN_UNTIL_SCORING_REQUIRED")
    if normalized["mode"] in {"snapshot_replay", "single_raw_snapshot", "snapshot_only"}:
        blockers.append(f"TARGET_SEPARATION_NOT_REAL::{normalized['mode']}")
    if normalized["kind"] in {"snapshot_replay", "single_raw_snapshot", "snapshot_only", "replay_only"}:
        blockers.append(f"TARGET_SEPARATION_NOT_REAL::{normalized['kind']}")
    if not isinstance(source.get("training_sources"), list) or not isinstance(source.get("target_sources"), list):
        blockers.append("SOURCE_REFERENCES_NOT_LISTS")
    elif not normalized["training_sources"] or not normalized["target_sources"]:
        blockers.append("SOURCE_REFERENCES_MISSING")
    elif not all(item for item in [*normalized["training_sources"], *normalized["target_sources"]]):
        blockers.append("SOURCE_REFERENCES_MUST_BE_NONEMPTY")
    if len(set(normalized["training_sources"])) != len(normalized["training_sources"]) or len(
        set(normalized["target_sources"])
    ) != len(normalized["target_sources"]):
        blockers.append("SOURCE_REFERENCES_DUPLICATE")
    if set(normalized["training_sources"]) & set(normalized["target_sources"]):
        blockers.append("TRAINING_TARGET_SOURCE_OVERLAP")
    if current_n < minimum_n:
        blockers.append(f"N_BELOW_MINIMUM::{current_n}/{minimum_n}")

    return blockers, normalized


def row_hash(row: dict[str, Any]) -> str:
    payload = {k: v for k, v in row.items() if k != "row_hash" and k != "row_hash_policy"}
    return sha256_object(payload)


def validate_rows(rows: list[dict[str, Any]]) -> list[str]:
    blockers: list[str] = []
    for row in rows:
        row_id = as_str(row.get("observation_id"), "unknown")
        required_fields = (
            "claim_id",
            "training_source",
            "target_source",
            "formula",
            "predicted_value",
            "observed_value",
            "comparator_prediction",
            "uncertainty",
            "negative_control_id",
            "negative_control_description",
            "falsifier",
        )
        for field in required_fields:
            if row.get(field) in (None, ""):
                blockers.append(f"ROW_MISSING_FIELD::{row_id}::{field}")

        if row.get("training_source") == row.get("target_source"):
            blockers.append(f"ROW_SOURCE_OVERLAP::{row_id}")

        for num_field in ("predicted_value", "observed_value", "comparator_prediction", "uncertainty", "model_residual", "comparator_residual"):
            if not is_number(row.get(num_field)):
                blockers.append(f"ROW_NUMERIC_INVALID::{row_id}::{num_field}")
        if as_float(row.get("uncertainty"), 0.0) < 0:
            blockers.append(f"ROW_UNCERTAINTY_NEGATIVE::{row_id}")
        if as_float(row.get("comparator_residual"), 0.0) <= as_float(row.get("model_residual"), 0.0):
            blockers.append(f"NEGATIVE_CONTROL_NOT_REJECTED::{row_id}")

        row["row_hash"] = row_hash(row)
        row["row_hash_policy"] = ROW_HASH_POLICY
    return ordered_unique(blockers)


def build_pack(rows: list[dict[str, Any]], source_sep: dict[str, Any], support_allowed: bool) -> dict[str, Any]:
    model_residuals = [float(row.get("model_residual", 0.0)) for row in rows if is_number(row.get("model_residual"))]
    comparator_residuals = [
        float(row.get("comparator_residual", 0.0)) for row in rows if is_number(row.get("comparator_residual"))
    ]
    uncertainties = [as_float(row.get("uncertainty"), 0.0) for row in rows if is_number(row.get("uncertainty"))]
    model_residual = sum(model_residuals) / len(model_residuals) if model_residuals else 0.0
    comparator_residual = sum(comparator_residuals) / len(comparator_residuals) if comparator_residuals else 0.0
    max_uncertainty = max(uncertainties) if uncertainties else 0.0
    interval = [max(0.0, model_residual - max_uncertainty / 2.0), model_residual + max_uncertainty]

    comparator_pre_registered = all(row.get("comparator_pre_registered") is True for row in rows)
    source = {
        "mode": source_sep.get("mode"),
        "pre_target_lock": bool(source_sep.get("pre_target_lock")),
        "target_hidden_until_scoring": bool(source_sep.get("target_hidden_until_scoring")),
        "training_sources": ordered_unique([as_str(item) for item in source_sep.get("training_sources", [])]),
        "target_sources": ordered_unique([as_str(item) for item in source_sep.get("target_sources", [])]),
    }

    return {
        "schema_id": grand_factory.EVIDENCE_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "capability_owner": CAPABILITY_OWNER,
        "evidence_pack_id": "OC133-BIOLOGY-NCBI-BENCHMARK-CANDIDATE",
        "domain": "biology",
        "source_separation": source,
        "n": len(rows),
        "model_under_test": rows[0].get("formula", "N/A") if rows else "N/A",
        "comparator_baseline": {
            "name": "NCBI benchmark comparator baseline",
            "prediction_rule": "declared comparator predictions are preregistered and held against row residuals",
            "pre_registered": bool(comparator_pre_registered),
        },
        "uncertainty": {
            "metric": "mean absolute residual",
            "method": "deterministic replay protocol with declared uncertainty",
            "interval": interval,
        },
        "residuals": {
            "model": model_residual,
            "comparator": comparator_residual,
            "superiority_margin": comparator_residual - model_residual,
        },
        "negative_controls": [
            {
                "control_id": row["negative_control_id"],
                "description": row["negative_control_description"],
                "rejected": as_float(row.get("comparator_residual"), 0.0) > as_float(row.get("model_residual"), 0.0),
            }
            for row in rows
        ],
        "falsifiers": ordered_unique([as_str(row.get("falsifier")) for row in rows]),
        "grand_toe_support_allowed": bool(support_allowed),
    }


def build_protocol(
    requirements: dict[str, Any],
    candidate_pack: dict[str, Any],
    blockers: list[str],
    minimum_n: int,
    current_n: int,
) -> dict[str, Any]:
    return {
        "schema_id": PROTOCOL_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "planner": PLANNER_REF,
        "evidence_pack_ref": CANDIDATE_PACK_REL,
        "required_source_modes": list(requirements.get("required_source_separation_modes", ["target_blind", "prospective"])),
        "minimum_n": minimum_n,
        "current_n": current_n,
        "candidate_pack_sha256": sha256_object(candidate_pack),
        "candidate_pack_hash_policy": PACK_HASH_POLICY,
        "blocker_total": len(blockers),
        "blockers": blockers,
        "rows": [
            {
                "domain": candidate_pack.get("domain"),
                "status": "READY_FOR_PARENT_REGISTRY_REVIEW" if candidate_pack.get("grand_toe_support_allowed") else "BLOCKED_PENDING_GENUINE_EVIDENCE",
                "candidate_pack_ref": CANDIDATE_PACK_REL,
                "candidate_pack_sha256": sha256_object(candidate_pack),
                "candidate_n": current_n,
                "minimum_n": minimum_n,
                "missing_n": max(0, minimum_n - current_n),
                "required_protocol_steps": [
                    "declare target-separated training and target sources before scoring",
                    "pre-register comparator baseline, residual metric, uncertainty policy, negative control, falsifier",
                    "require comparator residual greater than model residual on every row",
                    "require source separation mode target_blind or prospective",
                    "collect at least minimum_n heldout rows",
                ],
            }
        ],
    }


def build_payload(root: Path | None = None, snapshot_ref: str | None = None) -> dict[str, Any]:
    root = (root or repo_root()).resolve()
    requirements, req_failures = load_requirements(root)
    minimum_n = as_int(requirements.get("minimum_per_domain_n"), 20)

    snapshot_ref = snapshot_ref or DEFAULT_SNAPSHOT_REF
    snapshot_payload, snapshot_failures, snapshot_path = load_snapshot(root, snapshot_ref)
    blockers: list[str] = ordered_unique([*req_failures, *snapshot_failures])

    source_separation: dict[str, Any] = {}
    rows: list[dict[str, Any]] = []
    snapshot_sha256 = ""
    snapshot_byte_count = 0

    if snapshot_payload is None or not isinstance(snapshot_payload, dict):
        return {
            "tasks": {
                "schema_id": TASKS_SCHEMA_ID,
                "release_id": RELEASE_ID,
                "version": VERSION,
                "capability_owner": CAPABILITY_OWNER,
                "planner": PLANNER_REF,
                "snapshot_ref": snapshot_ref,
                "snapshot_sha256": "",
                "snapshot_hash_policy": SNAPSHOT_HASH_POLICY,
                "rows": [],
            },
            "candidate_pack": {},
            "protocol": {"schema_id": PROTOCOL_SCHEMA_ID, "release_id": RELEASE_ID, "version": VERSION},
            "report": {
                "schema_id": REPORT_SCHEMA_ID,
                "release_id": RELEASE_ID,
                "version": VERSION,
                "planner": PLANNER_REF,
                "support_policy": DEFAULT_SUPPORT_POLICY,
                "capability_owner": CAPABILITY_OWNER,
                "candidate_pack_ref": CANDIDATE_PACK_REL,
                "snapshot_ref": snapshot_ref,
                "snapshot_sha256": "",
                "snapshot_hash_policy": SNAPSHOT_HASH_POLICY,
                "snapshot_byte_count": 0,
                "candidate_pack_sha256": "",
                "open_blocker_total": len(blockers),
                "blocked_total": len(blockers),
                "blockers": blockers,
                "task_total": 0,
                "n": 0,
                "minimum_n": minimum_n,
                "missing_n": minimum_n,
                "support_scope": "target_blind_or_prospective_replay_only",
                "grand_toe_support_allowed": False,
                "verdict": "BLOCKED_MISSING_OR_INVALID_SNAPSHOT",
            },
        }

    source_separation, source_failures = normalize_source_separation(snapshot_payload)
    blockers.extend(source_failures)

    count_row, count_failures = parse_count_task(snapshot_payload, snapshot_ref)
    if count_row is not None:
        rows.append(count_row)
    if count_failures:
        blockers.extend(count_failures)
    metadata_rows, metadata_failures = parse_metadata_tasks(snapshot_payload, snapshot_ref)
    rows.extend(metadata_rows)
    if metadata_failures:
        blockers.extend(metadata_failures)

    if snapshot_path is not None:
        snapshot_sha256 = sha256_bytes(lf_bytes(snapshot_path))
        snapshot_byte_count = snapshot_path.stat().st_size

    row_validation_failures = validate_rows(rows)
    blockers.extend(row_validation_failures)

    source_blockers, source_sep_clean = validate_source_separation(source_separation, requirements, minimum_n, len(rows))
    blockers.extend(source_blockers)
    if not source_sep_clean["training_sources"] and source_separation.get("training_sources", ""):
        source_sep_clean["training_sources"] = [f"{snapshot_ref}::default-training"]
    if not source_sep_clean["target_sources"] and source_separation.get("target_sources", ""):
        source_sep_clean["target_sources"] = [f"{snapshot_ref}::default-target"]

    if not all(row.get("comparator_pre_registered") is True for row in rows):
        blockers.append("COMPARATOR_BASELINE_NOT_PREREGISTERED")

    all_failures = ordered_unique(blockers)
    gate_candidate_pack = build_pack(rows, source_sep_clean, support_allowed=True)
    gate_failures = grand_factory.pack_failure_reasons(gate_candidate_pack, requirements)
    all_failures.extend(gate_failures)
    all_failures = ordered_unique(all_failures)

    support_allowed = not all_failures
    pack = build_pack(rows, source_sep_clean, support_allowed=support_allowed)
    if not support_allowed and pack.get("grand_toe_support_allowed") is not False:
        pack["grand_toe_support_allowed"] = False

    protocol = build_protocol(requirements, pack, all_failures, minimum_n, len(rows))
    report = {
        "schema_id": REPORT_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "planner": PLANNER_REF,
        "support_policy": DEFAULT_SUPPORT_POLICY,
        "requirements_ref": REQUIREMENTS_REL,
        "candidate_pack_ref": CANDIDATE_PACK_REL,
        "protocol_ref": PROTOCOL_REL,
        "snapshot_ref": snapshot_ref,
        "snapshot_sha256": snapshot_sha256,
        "snapshot_sha256_policy": SNAPSHOT_HASH_POLICY,
        "snapshot_byte_count": snapshot_byte_count,
        "candidate_pack_sha256": sha256_object(pack),
        "candidate_pack_row_hashes": [row.get("row_hash") for row in rows],
        "candidate_pack_hash_policy": PACK_HASH_POLICY,
        "task_total": len(rows),
        "n": len(rows),
        "minimum_n": minimum_n,
        "missing_n": max(0, minimum_n - len(rows)),
        "open_blocker_total": len(all_failures),
        "blocked_total": len(all_failures),
        "blockers": all_failures,
        "support_scope": "target_blind_or_prospective_biology_replay",
        "snapshot_replay_only": source_sep_clean.get("mode", "").lower() == "snapshot_replay",
        "grand_toe_support_allowed": support_allowed,
        "verdict": "READY_FOR_PARENT_REGISTRY_REVIEW" if support_allowed else "BLOCKED_PENDING_GENUINE_BIOLOGY_REPLAY_EVIDENCE",
        "tasks_ref": TASKS_REL,
        "protocol_ref": PROTOCOL_REL,
        "no_send": True,
        "publish_allowed": False,
        "journal_submissions_allowed": False,
    }

    tasks = {
        "schema_id": TASKS_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "planner": PLANNER_REF,
        "snapshot_ref": snapshot_ref,
        "snapshot_sha256": snapshot_sha256,
        "snapshot_hash_policy": SNAPSHOT_HASH_POLICY,
        "snapshot_byte_count": snapshot_byte_count,
        "snapshot_task_count": sum(1 for row in rows if row.get("task_type") == "count"),
        "metadata_task_count": sum(1 for row in rows if row.get("task_type") == "metadata"),
        "rows": rows,
    }

    readme = build_readme(pack, tasks, report)
    return {
        "tasks": tasks,
        "candidate_pack": pack,
        "protocol": protocol,
        "report": report,
        "readme": readme,
    }


def build_readme(candidate_pack: dict[str, Any], tasks: dict[str, Any], report: dict[str, Any]) -> str:
    lines = [
        "# Biology NCBI Benchmark Factory",
        "",
        f"Verdict: `{report['verdict']}`",
        f"Grand TOE support allowed: `{report['grand_toe_support_allowed']}`",
        f"Task total: `{tasks['snapshot_task_count'] + tasks['metadata_task_count']}`",
        f"N: `{report['n']}`",
        f"Minimum N: `{report['minimum_n']}`",
        "",
        "## Open blockers",
    ]
    if report["blockers"]:
        lines.extend(f"- {item}" for item in report["blockers"])
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Evidence pack",
            f"Evidence pack SHA256: `{sha256_object(candidate_pack)}`",
            f"Source mode: `{candidate_pack.get('source_separation', {}).get('mode')}`",
            f"Grand TOE support allowed: `{candidate_pack.get('grand_toe_support_allowed')}`",
        ]
    )
    return "\n".join(lines) + "\n"


def write_outputs(root: Path | None = None, snapshot_ref: str | None = None) -> dict[str, Any]:
    root = (root or repo_root()).resolve()
    payload = build_payload(root, snapshot_ref=snapshot_ref)
    write_json(root / TASKS_REL, payload["tasks"])
    write_json(root / CANDIDATE_PACK_REL, payload["candidate_pack"])
    write_json(root / PROTOCOL_REL, payload["protocol"])
    write_json(root / REPORT_REL, payload["report"])
    write_text(root / README_REL, payload["readme"])
    return payload["report"]


def check_stored(root: Path | None = None, snapshot_ref: str | None = None) -> list[str]:
    root = (root or repo_root()).resolve()
    expected = build_payload(root, snapshot_ref=snapshot_ref)
    failures: list[str] = []
    checks = [
        (TASKS_REL, expected["tasks"]),
        (CANDIDATE_PACK_REL, expected["candidate_pack"]),
        (PROTOCOL_REL, expected["protocol"]),
        (REPORT_REL, expected["report"]),
    ]
    for rel, expected_payload in checks:
        path = root / rel
        if not path.exists():
            failures.append(f"missing::{rel}")
            continue
        if read_json(path) != expected_payload:
            failures.append(f"mismatch::{rel}")
    readme_path = root / README_REL
    if not readme_path.exists():
        failures.append(f"missing::{README_REL}")
    elif readme_path.read_text(encoding="utf-8") != expected["readme"]:
        failures.append(f"mismatch::{README_REL}")
    return failures


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build OC133 biology NCBI benchmark artifacts.")
    parser.add_argument("--root", default=str(repo_root()), help="repository root")
    parser.add_argument("--snapshot-ref", default=DEFAULT_SNAPSHOT_REF, help="NCBI-style snapshot ref")
    parser.add_argument("--write", action="store_true", help="write artifacts")
    parser.add_argument("--check", action="store_true", help="check persisted artifacts are exact")
    parser.add_argument("--allow-blocked-exit-zero", action="store_true", help="exit 0 when blocked")
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
                {"status": "ok", "checked": [TASKS_REL, CANDIDATE_PACK_REL, PROTOCOL_REL, REPORT_REL, README_REL]},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    if args.write:
        report = write_outputs(root, snapshot_ref=args.snapshot_ref)
    else:
        report = build_payload(root, snapshot_ref=args.snapshot_ref)["report"]
    print(json.dumps(report, ensure_ascii=True, indent=2))
    if report["grand_toe_support_allowed"] is not True and not args.allow_blocked_exit_zero:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
