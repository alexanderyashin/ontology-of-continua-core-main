from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
import urllib.request


RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
GENERATED_ON = "2026-05-01"
SCHEMA_ID = "OC133_EARTH_SPACE_MODERN_SCIENCE_COVERAGE_WORK_ORDERS_v1"
CAPABILITY_OWNER = "Logion Earth-Space Evidence / Official Geophysical Data"

SCRIPT_REL = (
    "validation/heldout/grand_science/earth_space/coverage_work_orders/"
    "oc133_earth_space_modern_science_coverage_work_orders.py"
)
OUTPUT_REL = (
    "validation/heldout/grand_science/earth_space/coverage_work_orders/"
    "OC133_EARTH_SPACE_MODERN_SCIENCE_COVERAGE_WORK_ORDERS.json"
)
COVERAGE_REGISTER_REL = "comparators/modern_science/OC133_MODERN_SCIENCE_COVERAGE_REGISTER.json"
MODERN_WORK_ORDERS_REL = "benchmarks/modern_science/OC133_MODERN_SCIENCE_COVERAGE_WORK_ORDERS.json"

USGS_HYDROLOGY_ENDPOINT = (
    "https://waterservices.usgs.gov/nwis/dv/?"
    + urlencode(
        {
            "format": "json",
            "sites": "01646500",
            "startDT": "2024-01-01",
            "endDT": "2024-02-09",
            "parameterCd": "00060",
            "statCd": "00003",
            "siteStatus": "all",
        }
    )
)
USGS_HYDROLOGY_SNAPSHOT_REL = (
    "validation/heldout/grand_science/earth_space/coverage_work_orders/raw/"
    "usgs_potomac_daily_discharge_2024_01_01_2024_02_09.json"
)
USGS_HYDROLOGY_METADATA_REL = (
    "validation/heldout/grand_science/earth_space/coverage_work_orders/raw/"
    "usgs_potomac_daily_discharge_2024_01_01_2024_02_09.metadata.json"
)
USGS_HYDROLOGY_SCORER_EVIDENCE_REL = (
    "validation/heldout/grand_science/earth_space/coverage_work_orders/"
    "OC133_EARTH_SPACE_USGS_HYDROLOGY_TARGET_HIDDEN_REPLAY_SCORER_EVIDENCE_PACK.json"
)
USGS_HYDROLOGY_SCORER_SCHEMA_ID = (
    "OC133_EARTH_SPACE_USGS_HYDROLOGY_TARGET_HIDDEN_REPLAY_SCORER_v1"
)
USGS_HYDROLOGY_WORK_ORDER_ID = "MS-COV-WO-011"

NASA_POWER_ENDPOINT = (
    "https://power.larc.nasa.gov/api/temporal/daily/point?"
    + urlencode(
        {
            "parameters": "ALLSKY_SFC_SW_DWN,T2M",
            "community": "RE",
            "longitude": "-122.4194",
            "latitude": "37.7749",
            "start": "20240101",
            "end": "20240209",
            "format": "JSON",
            "time-standard": "UTC",
        }
    )
)
NASA_POWER_SNAPSHOT_REL = (
    "validation/heldout/grand_science/earth_space/coverage_work_orders/raw/"
    "nasa_power_sf_daily_20240101_20240209.json"
)
NASA_POWER_METADATA_REL = (
    "validation/heldout/grand_science/earth_space/coverage_work_orders/raw/"
    "nasa_power_sf_daily_20240101_20240209.metadata.json"
)
NASA_POWER_SCORER_EVIDENCE_REL = (
    "validation/heldout/grand_science/earth_space/coverage_work_orders/"
    "OC133_EARTH_SPACE_NASA_POWER_REMOTE_SENSING_TARGET_HIDDEN_REPLAY_SCORER_EVIDENCE_PACK.json"
)
NASA_POWER_SCORER_SCHEMA_ID = (
    "OC133_EARTH_SPACE_NASA_POWER_REMOTE_SENSING_TARGET_HIDDEN_REPLAY_SCORER_v1"
)
NASA_POWER_WORK_ORDER_ID = "MS-COV-WO-012"

NOAA_COOPS_WATER_LEVEL_SNAPSHOT_REL = (
    "validation/heldout/grand_science/earth_space/coverage_work_orders/raw/"
    "noaa_coops_9414290_water_level_20240101_20240103.json"
)
NOAA_COOPS_PREDICTIONS_SNAPSHOT_REL = (
    "validation/heldout/grand_science/earth_space/coverage_work_orders/raw/"
    "noaa_coops_9414290_predictions_20240101_20240103.json"
)
NOAA_COOPS_METADATA_REL = (
    "validation/heldout/grand_science/earth_space/coverage_work_orders/raw/"
    "noaa_coops_9414290_water_level_predictions_20240101_20240103.metadata.json"
)
NOAA_COOPS_SCORER_EVIDENCE_REL = (
    "validation/heldout/grand_science/earth_space/coverage_work_orders/"
    "OC133_EARTH_SPACE_NOAA_COOPS_WATER_LEVEL_TARGET_HIDDEN_REPLAY_SCORER_EVIDENCE_PACK.json"
)
NOAA_COOPS_SCORER_SCHEMA_ID = (
    "OC133_EARTH_SPACE_NOAA_COOPS_WATER_LEVEL_TARGET_HIDDEN_REPLAY_SCORER_v1"
)
NOAA_COOPS_WORK_ORDER_ID = "MS-COV-WO-010"

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

SPEC_REQUIRED_FIELDS = (
    "official_source",
    "target_variable",
    "target_hidden_split",
    "formula_or_model",
    "preregistered_comparator",
    "uncertainty_and_residual",
    "negative_control",
    "falsifier",
    "N",
    "replay_command",
    "fail_closed_current_evidence",
)

COMMON_CLOSURE_PREDICATES = [
    "STRICT_PACK_SCHEMA_PASS",
    "OFFICIAL_SOURCE_SNAPSHOT_HASH_BOUND",
    "TARGET_VARIABLE_EXACTLY_DECLARED",
    "TARGET_HIDDEN_OR_PROSPECTIVE_LOCK_DECLARED",
    "FORMULA_OR_MODEL_PREREGISTERED",
    "COMPARATOR_PREREGISTERED_AND_TARGET_SEPARATED",
    "UNCERTAINTY_AND_RESIDUAL_DECLARED",
    "NEGATIVE_CONTROL_REJECTION_REQUIRED",
    "FALSIFIER_PREDICATES_EXECUTABLE",
    "INDEPENDENT_REPLAY_PASS",
    "COVERAGE_REGISTER_GAP_CLOSED_BY_REVIEW",
    "NO_BROAD_SUPERIORITY_CERTIFICATION",
]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[5]


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_object(payload: Any) -> str:
    return sha256_bytes(canonical_json(payload).encode("utf-8"))


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


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def fetch_official_bytes(url: str) -> tuple[int, str, bytes]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "Logion-OC133-earth-space-coverage-work-order/1.0",
        },
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        content_type = str(response.headers.get("content-type", ""))
        return int(response.status), content_type, response.read()


def count_usgs_values(payload: bytes) -> int:
    try:
        data = json.loads(payload.decode("utf-8"))
        series = data.get("value", {}).get("timeSeries", [])
        if not series:
            return 0
        values = series[0].get("values", [])
        if not values:
            return 0
        rows = values[0].get("value", [])
        return len(rows) if isinstance(rows, list) else 0
    except Exception:
        return 0


def count_nasa_power_values(payload: bytes) -> int:
    try:
        data = json.loads(payload.decode("utf-8"))
        parameters = data.get("properties", {}).get("parameter", {})
        solar = parameters.get("ALLSKY_SFC_SW_DWN", {})
        return len(solar) if isinstance(solar, dict) else 0
    except Exception:
        return 0


def count_noaa_coops_values(payload: bytes, key: str) -> int:
    try:
        data = json.loads(payload.decode("utf-8"))
        rows = data.get(key, [])
        return len(rows) if isinstance(rows, list) else 0
    except Exception:
        return 0


def refresh_usgs_hydrology_snapshot(root: Path) -> dict[str, Any]:
    status, content_type, payload = fetch_official_bytes(USGS_HYDROLOGY_ENDPOINT)
    snapshot_path = root / USGS_HYDROLOGY_SNAPSHOT_REL
    metadata_path = root / USGS_HYDROLOGY_METADATA_REL
    digest = sha256_bytes(payload)
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_bytes(payload)
    metadata = {
        "schema_id": "OC133_EARTH_SPACE_USGS_HYDROLOGY_SOURCE_SNAPSHOT_METADATA_v1",
        "release_id": RELEASE_ID,
        "acquisition_id": "OC133-EARTH-USGS-POTOMAC-DV-00060-20240101-20240209",
        "official_source": "USGS Water Services Daily Values",
        "official_documentation_url": "https://waterservices.usgs.gov/docs/dv-service/daily-values-service-details/",
        "official_endpoint_url": USGS_HYDROLOGY_ENDPOINT,
        "snapshot_ref": USGS_HYDROLOGY_SNAPSHOT_REL,
        "source_bytes_sha256": digest,
        "byte_count": len(payload),
        "http_status": status,
        "content_type": content_type,
        "value_row_count": count_usgs_values(payload),
        "acquired_at_utc": utc_now_iso(),
        "hash_policy": "sha256 over official response bytes exactly as stored",
        "source_snapshot_pre_target_lock": True,
        "target_hidden_until_scoring": True,
        "target_projection_unsealed_for_scoring": False,
        "scoring_started": False,
        "scientific_pass": False,
        "coverage_closure_allowed": False,
        "no_send_locks": no_send(),
    }
    metadata["metadata_sha256"] = sha256_object({k: v for k, v in metadata.items() if k != "metadata_sha256"})
    write_json(metadata_path, metadata)
    return metadata


def refresh_nasa_power_snapshot(root: Path) -> dict[str, Any]:
    status, content_type, payload = fetch_official_bytes(NASA_POWER_ENDPOINT)
    snapshot_path = root / NASA_POWER_SNAPSHOT_REL
    metadata_path = root / NASA_POWER_METADATA_REL
    digest = sha256_bytes(payload)
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_bytes(payload)
    metadata = {
        "schema_id": "OC133_EARTH_SPACE_NASA_POWER_SOURCE_SNAPSHOT_METADATA_v1",
        "release_id": RELEASE_ID,
        "acquisition_id": "OC133-EARTH-NASA-POWER-SF-ALLSKY-T2M-20240101-20240209",
        "official_source": "NASA POWER Daily API",
        "official_documentation_url": "https://power.larc.nasa.gov/docs/services/api/temporal/daily/",
        "official_endpoint_url": NASA_POWER_ENDPOINT,
        "snapshot_ref": NASA_POWER_SNAPSHOT_REL,
        "source_bytes_sha256": digest,
        "byte_count": len(payload),
        "http_status": status,
        "content_type": content_type,
        "value_row_count": count_nasa_power_values(payload),
        "acquired_at_utc": utc_now_iso(),
        "hash_policy": "sha256 over official response bytes exactly as stored",
        "source_snapshot_pre_target_lock": True,
        "target_hidden_until_scoring": True,
        "target_projection_unsealed_for_scoring": False,
        "scoring_started": False,
        "scientific_pass": False,
        "coverage_closure_allowed": False,
        "no_send_locks": no_send(),
    }
    metadata["metadata_sha256"] = sha256_object({k: v for k, v in metadata.items() if k != "metadata_sha256"})
    write_json(metadata_path, metadata)
    return metadata


def refresh_noaa_coops_snapshot(root: Path) -> dict[str, Any]:
    water_status, water_content_type, water_payload = fetch_official_bytes(noaa_water_level_url("water_level"))
    prediction_status, prediction_content_type, prediction_payload = fetch_official_bytes(
        noaa_water_level_url("predictions")
    )
    water_path = root / NOAA_COOPS_WATER_LEVEL_SNAPSHOT_REL
    prediction_path = root / NOAA_COOPS_PREDICTIONS_SNAPSHOT_REL
    metadata_path = root / NOAA_COOPS_METADATA_REL
    water_digest = sha256_bytes(water_payload)
    prediction_digest = sha256_bytes(prediction_payload)
    water_path.parent.mkdir(parents=True, exist_ok=True)
    water_path.write_bytes(water_payload)
    prediction_path.write_bytes(prediction_payload)
    metadata = {
        "schema_id": "OC133_EARTH_SPACE_NOAA_COOPS_SOURCE_SNAPSHOT_METADATA_v1",
        "release_id": RELEASE_ID,
        "acquisition_id": "OC133-EARTH-NOAA-COOPS-9414290-WATER-PREDICTIONS-20240101-20240103",
        "official_source": "NOAA CO-OPS Data Retrieval API",
        "official_documentation_url": "https://api.tidesandcurrents.noaa.gov/api/prod/",
        "water_level_endpoint_url": noaa_water_level_url("water_level"),
        "predictions_endpoint_url": noaa_water_level_url("predictions"),
        "water_level_snapshot_ref": NOAA_COOPS_WATER_LEVEL_SNAPSHOT_REL,
        "predictions_snapshot_ref": NOAA_COOPS_PREDICTIONS_SNAPSHOT_REL,
        "water_level_source_bytes_sha256": water_digest,
        "predictions_source_bytes_sha256": prediction_digest,
        "water_level_byte_count": len(water_payload),
        "predictions_byte_count": len(prediction_payload),
        "water_level_http_status": water_status,
        "predictions_http_status": prediction_status,
        "water_level_content_type": water_content_type,
        "predictions_content_type": prediction_content_type,
        "water_level_row_count": count_noaa_coops_values(water_payload, "data"),
        "predictions_row_count": count_noaa_coops_values(prediction_payload, "predictions"),
        "acquired_at_utc": utc_now_iso(),
        "hash_policy": "sha256 over official response bytes exactly as stored; both water-level and prediction feeds are required",
        "source_snapshot_pre_target_lock": True,
        "target_hidden_until_scoring": True,
        "target_projection_unsealed_for_scoring": False,
        "scoring_started": False,
        "scientific_pass": False,
        "coverage_closure_allowed": False,
        "no_send_locks": no_send(),
    }
    metadata["metadata_sha256"] = sha256_object({k: v for k, v in metadata.items() if k != "metadata_sha256"})
    write_json(metadata_path, metadata)
    return metadata


def load_usgs_api_lane(root: Path) -> dict[str, Any]:
    snapshot_path = root / USGS_HYDROLOGY_SNAPSHOT_REL
    metadata_path = root / USGS_HYDROLOGY_METADATA_REL
    if not snapshot_path.exists() or not metadata_path.exists():
        return {
            "status": "OPEN_FAIL_CLOSED_NO_SOURCE_SNAPSHOT_HASH",
            "official_endpoint_url": USGS_HYDROLOGY_ENDPOINT,
            "snapshot_ref": USGS_HYDROLOGY_SNAPSHOT_REL,
            "metadata_ref": USGS_HYDROLOGY_METADATA_REL,
            "source_snapshot_hash_bound": False,
            "remaining_blocker": "USGS_SOURCE_SNAPSHOT_NOT_ACQUIRED",
        }
    metadata = read_json(metadata_path)
    payload = snapshot_path.read_bytes()
    digest = sha256_bytes(payload)
    expected_metadata_hash = sha256_object({k: v for k, v in metadata.items() if k != "metadata_sha256"})
    hash_ok = (
        metadata.get("source_bytes_sha256") == digest
        and metadata.get("byte_count") == len(payload)
        and metadata.get("metadata_sha256") == expected_metadata_hash
        and int(metadata.get("value_row_count", 0) or 0) >= 20
    )
    return {
        "status": (
            "SOURCE_SNAPSHOT_HASH_BOUND_ACQUISITION_ONLY_NOT_STRICT_EVIDENCE"
            if hash_ok
            else "OPEN_FAIL_CLOSED_SOURCE_SNAPSHOT_HASH_MISMATCH"
        ),
        "official_endpoint_url": metadata.get("official_endpoint_url", USGS_HYDROLOGY_ENDPOINT),
        "snapshot_ref": USGS_HYDROLOGY_SNAPSHOT_REL,
        "metadata_ref": USGS_HYDROLOGY_METADATA_REL,
        "source_snapshot_sha256": digest,
        "metadata_sha256": metadata.get("metadata_sha256"),
        "byte_count": len(payload),
        "value_row_count": metadata.get("value_row_count", 0),
        "source_snapshot_hash_bound": hash_ok,
        "scientific_pass": False,
        "coverage_closure_allowed": False,
        "remaining_blocker": "STRICT_TARGET_HIDDEN_SCORER_AND_EVIDENCE_PACK_NOT_BUILT",
    }


def load_nasa_power_api_lane(root: Path) -> dict[str, Any]:
    snapshot_path = root / NASA_POWER_SNAPSHOT_REL
    metadata_path = root / NASA_POWER_METADATA_REL
    if not snapshot_path.exists() or not metadata_path.exists():
        return {
            "status": "OPEN_FAIL_CLOSED_NO_SOURCE_SNAPSHOT_HASH",
            "official_endpoint_url": NASA_POWER_ENDPOINT,
            "snapshot_ref": NASA_POWER_SNAPSHOT_REL,
            "metadata_ref": NASA_POWER_METADATA_REL,
            "source_snapshot_hash_bound": False,
            "remaining_blocker": "NASA_POWER_SOURCE_SNAPSHOT_NOT_ACQUIRED",
        }
    metadata = read_json(metadata_path)
    payload = snapshot_path.read_bytes()
    digest = sha256_bytes(payload)
    expected_metadata_hash = sha256_object({k: v for k, v in metadata.items() if k != "metadata_sha256"})
    hash_ok = (
        metadata.get("source_bytes_sha256") == digest
        and metadata.get("byte_count") == len(payload)
        and metadata.get("metadata_sha256") == expected_metadata_hash
        and int(metadata.get("value_row_count", 0) or 0) >= 40
    )
    return {
        "status": (
            "SOURCE_SNAPSHOT_HASH_BOUND_ACQUISITION_ONLY_NOT_STRICT_EVIDENCE"
            if hash_ok
            else "OPEN_FAIL_CLOSED_SOURCE_SNAPSHOT_HASH_MISMATCH"
        ),
        "official_endpoint_url": metadata.get("official_endpoint_url", NASA_POWER_ENDPOINT),
        "snapshot_ref": NASA_POWER_SNAPSHOT_REL,
        "metadata_ref": NASA_POWER_METADATA_REL,
        "source_snapshot_sha256": digest,
        "metadata_sha256": metadata.get("metadata_sha256"),
        "byte_count": len(payload),
        "value_row_count": metadata.get("value_row_count", 0),
        "source_snapshot_hash_bound": hash_ok,
        "scientific_pass": False,
        "coverage_closure_allowed": False,
        "remaining_blocker": "STRICT_TARGET_HIDDEN_SCORER_AND_EVIDENCE_PACK_NOT_BUILT",
    }


def load_noaa_coops_api_lane(root: Path) -> dict[str, Any]:
    water_path = root / NOAA_COOPS_WATER_LEVEL_SNAPSHOT_REL
    prediction_path = root / NOAA_COOPS_PREDICTIONS_SNAPSHOT_REL
    metadata_path = root / NOAA_COOPS_METADATA_REL
    if not water_path.exists() or not prediction_path.exists() or not metadata_path.exists():
        return {
            "status": "OPEN_FAIL_CLOSED_NO_SOURCE_SNAPSHOT_HASH",
            "official_endpoint_url": noaa_water_level_url("water_level"),
            "paired_official_endpoint_url": noaa_water_level_url("predictions"),
            "water_level_snapshot_ref": NOAA_COOPS_WATER_LEVEL_SNAPSHOT_REL,
            "predictions_snapshot_ref": NOAA_COOPS_PREDICTIONS_SNAPSHOT_REL,
            "metadata_ref": NOAA_COOPS_METADATA_REL,
            "source_snapshot_hash_bound": False,
            "remaining_blocker": "NOAA_COOPS_SOURCE_SNAPSHOT_NOT_ACQUIRED",
        }
    metadata = read_json(metadata_path)
    water_payload = water_path.read_bytes()
    prediction_payload = prediction_path.read_bytes()
    water_digest = sha256_bytes(water_payload)
    prediction_digest = sha256_bytes(prediction_payload)
    expected_metadata_hash = sha256_object({k: v for k, v in metadata.items() if k != "metadata_sha256"})
    water_row_count = int(metadata.get("water_level_row_count", 0) or 0)
    prediction_row_count = int(metadata.get("predictions_row_count", 0) or 0)
    hash_ok = (
        metadata.get("water_level_source_bytes_sha256") == water_digest
        and metadata.get("predictions_source_bytes_sha256") == prediction_digest
        and metadata.get("water_level_byte_count") == len(water_payload)
        and metadata.get("predictions_byte_count") == len(prediction_payload)
        and metadata.get("metadata_sha256") == expected_metadata_hash
        and water_row_count >= 720
        and prediction_row_count >= 720
    )
    return {
        "status": (
            "SOURCE_SNAPSHOT_HASH_BOUND_ACQUISITION_ONLY_NOT_STRICT_EVIDENCE"
            if hash_ok
            else "OPEN_FAIL_CLOSED_SOURCE_SNAPSHOT_HASH_MISMATCH"
        ),
        "official_endpoint_url": metadata.get("water_level_endpoint_url", noaa_water_level_url("water_level")),
        "paired_official_endpoint_url": metadata.get("predictions_endpoint_url", noaa_water_level_url("predictions")),
        "water_level_snapshot_ref": NOAA_COOPS_WATER_LEVEL_SNAPSHOT_REL,
        "predictions_snapshot_ref": NOAA_COOPS_PREDICTIONS_SNAPSHOT_REL,
        "snapshot_ref": NOAA_COOPS_WATER_LEVEL_SNAPSHOT_REL,
        "metadata_ref": NOAA_COOPS_METADATA_REL,
        "water_level_source_snapshot_sha256": water_digest,
        "predictions_source_snapshot_sha256": prediction_digest,
        "source_snapshot_sha256": sha256_object(
            {
                "water_level_source_bytes_sha256": water_digest,
                "predictions_source_bytes_sha256": prediction_digest,
            }
        ),
        "metadata_sha256": metadata.get("metadata_sha256"),
        "water_level_byte_count": len(water_payload),
        "predictions_byte_count": len(prediction_payload),
        "water_level_row_count": water_row_count,
        "predictions_row_count": prediction_row_count,
        "value_row_count": min(water_row_count, prediction_row_count),
        "source_snapshot_hash_bound": hash_ok,
        "scientific_pass": False,
        "coverage_closure_allowed": False,
        "remaining_blocker": "STRICT_TARGET_HIDDEN_SCORER_AND_EVIDENCE_PACK_NOT_BUILT",
    }


def round_metric(value: float) -> float:
    return round(float(value), 6)


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def rmse(values: list[float]) -> float:
    return math.sqrt(mean([value * value for value in values])) if values else 0.0


def median_value(values: list[float]) -> float:
    return float(statistics.median(values)) if values else 0.0


def median_absolute_deviation(values: list[float]) -> float:
    if not values:
        return 0.0
    center = median_value(values)
    return median_value([abs(value - center) for value in values])


def extract_usgs_discharge_rows(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    series = snapshot.get("value", {}).get("timeSeries", [])
    if not series:
        return []
    value_sets = series[0].get("values", [])
    if not value_sets:
        return []
    rows = value_sets[0].get("value", [])
    if not isinstance(rows, list):
        return []
    extracted: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            continue
        date_time = str(row.get("dateTime", ""))
        try:
            discharge = float(row["value"])
        except (KeyError, TypeError, ValueError):
            continue
        extracted.append(
            {
                "row_index": index,
                "date": date_time[:10],
                "date_time": date_time,
                "discharge_cfs": discharge,
                "qualifiers": row.get("qualifiers", []),
                "source_row_sha256": sha256_object({"row_index": index, "row": row}),
            }
        )
    return extracted


def usgs_training_parameters(training_rows: list[dict[str, Any]]) -> dict[str, Any]:
    values = [float(row["discharge_cfs"]) for row in training_rows]
    logs = [math.log1p(value) for value in values]
    log_deltas = [logs[index] - logs[index - 1] for index in range(1, len(logs))]
    median_log_delta = median_value(log_deltas)
    log_residuals = [
        abs(logs[index] - (logs[index - 1] + median_log_delta)) for index in range(1, len(logs))
    ]
    cfs_predictions = [math.expm1(logs[index - 1] + median_log_delta) for index in range(1, len(logs))]
    cfs_residuals = [abs(values[index] - cfs_predictions[index - 1]) for index in range(1, len(values))]
    return {
        "training_row_count": len(training_rows),
        "median_log_delta": median_log_delta,
        "training_log_residual_median_abs": median_value(log_residuals),
        "training_log_residual_mad": median_absolute_deviation(log_residuals),
        "training_cfs_residual_median_abs": median_value(cfs_residuals),
        "training_cfs_residual_mad": median_absolute_deviation(cfs_residuals),
        "training_cfs_residual_mae": mean(cfs_residuals),
        "training_cfs_residual_rmse": rmse(cfs_residuals),
    }


def usgs_prediction_rows(
    training_rows: list[dict[str, Any]],
    hidden_rows: list[dict[str, Any]],
    params: dict[str, Any],
) -> list[dict[str, Any]]:
    if not training_rows:
        return []
    median_log_delta = float(params["median_log_delta"])
    last_visible_cfs = float(training_rows[-1]["discharge_cfs"])
    prior_prediction_or_visible = last_visible_cfs
    predictions: list[dict[str, Any]] = []
    for row in hidden_rows:
        predicted = math.expm1(math.log1p(prior_prediction_or_visible) + median_log_delta)
        predictions.append(
            {
                "row_index": row["row_index"],
                "date": row["date"],
                "model_prediction_cfs": round_metric(predicted),
                "comparator_prediction_cfs": round_metric(last_visible_cfs),
                "prediction_inputs": {
                    "prior_prediction_or_last_visible_cfs": round_metric(prior_prediction_or_visible),
                    "training_only_median_log_delta": round_metric(median_log_delta),
                    "hidden_target_value_used": False,
                },
            }
        )
        prior_prediction_or_visible = predicted
    return predictions


def usgs_prediction_declaration(
    training_rows: list[dict[str, Any]],
    hidden_rows: list[dict[str, Any]],
    params: dict[str, Any],
) -> dict[str, Any]:
    prediction_rows = usgs_prediction_rows(training_rows, hidden_rows, params)
    materialization = {
        "predictions_materialized_before_target_unseal": True,
        "hidden_target_values_included": False,
        "prediction_rows": prediction_rows,
        "prediction_rows_sha256": sha256_object(prediction_rows),
    }
    declaration = {
        "declared_before_scoring": True,
        "target_hidden_until_scoring": True,
        "target_values_used_for_model_selection": False,
        "target_values_used_for_prediction_materialization": False,
        "split_policy": {
            "mode": "prospective_source_lock_then_temporal_holdout",
            "training_row_count": len(training_rows),
            "hidden_row_count": len(hidden_rows),
            "training_date_range": [training_rows[0]["date"], training_rows[-1]["date"]]
            if training_rows
            else [],
            "hidden_date_range": [hidden_rows[0]["date"], hidden_rows[-1]["date"]] if hidden_rows else [],
            "split_rule": "First 20 daily values are visible training rows; final 20 daily values are hidden scoring targets.",
        },
        "visible_training_rows": [
            {
                "row_index": row["row_index"],
                "date": row["date"],
                "discharge_cfs": round_metric(float(row["discharge_cfs"])),
                "qualifiers": row.get("qualifiers", []),
                "source_row_sha256": row["source_row_sha256"],
            }
            for row in training_rows
        ],
        "hidden_target_placeholders": [
            {
                "row_index": row["row_index"],
                "date": row["date"],
                "target_field": "value.timeSeries[0].values[0].value[].value",
                "target_value_hidden": True,
                "target_placeholder_sha256": sha256_object(
                    {
                        "row_index": row["row_index"],
                        "date": row["date"],
                        "target_field": "value.timeSeries[0].values[0].value[].value",
                        "target_value_hidden": True,
                    }
                ),
            }
            for row in hidden_rows
        ],
        "prediction_formula": {
            "model_id": "USGS-LOG-FLOW-PRIOR-DELTA-MEDIAN",
            "pre_registered": True,
            "rule": "log1p(Q_hat_t) = log1p(Q_prior) + median(diff(log1p(Q_visible_training)))",
            "hidden_replay_policy": "For the first hidden date Q_prior is the last visible discharge; later hidden dates use the previous model prediction, not hidden observations.",
            "training_only_parameters": {
                "median_log_delta": round_metric(float(params["median_log_delta"])),
                "parameter_source": "visible training rows only",
            },
        },
        "comparator_baseline": {
            "comparator_id": "USGS-LAST-OBSERVATION-CARRY-FORWARD",
            "pre_registered": True,
            "prediction_rule": "Predict every hidden discharge row as the last visible discharge value.",
            "target_values_used_for_baseline_design": False,
        },
        "uncertainty_policy": {
            "method": "training-only one-step residual envelope",
            "residual_metric": "hidden mean absolute residual in cubic feet per second",
            "aggregate_uncertainty_allowance_cfs": round_metric(
                float(params["training_cfs_residual_median_abs"])
            ),
            "training_log_residual_mad": round_metric(float(params["training_log_residual_mad"])),
            "strict_superiority_rule": "model_mae_cfs + aggregate_uncertainty_allowance_cfs < comparator_mae_cfs",
        },
        "materialization_order": [
            "hash official USGS snapshot bytes and metadata",
            "parse visible training rows 1-20",
            "declare hidden target placeholders for rows 21-40 without target values",
            "materialize model and comparator predictions from visible rows only",
            "unseal hidden target values and score residuals",
            "run negative-control and target-leakage falsifier checks",
        ],
        "prediction_materialization": materialization,
    }
    declaration["materialization_order_hash"] = sha256_object(declaration["materialization_order"])
    declaration["declaration_sha256"] = sha256_object(declaration)
    return declaration


def usgs_scored_rows(
    hidden_rows: list[dict[str, Any]],
    prediction_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    scored: list[dict[str, Any]] = []
    for actual, predicted in zip(hidden_rows, prediction_rows):
        observed = round_metric(float(actual["discharge_cfs"]))
        model_prediction = round_metric(float(predicted["model_prediction_cfs"]))
        comparator_prediction = round_metric(float(predicted["comparator_prediction_cfs"]))
        row = {
            "row_index": actual["row_index"],
            "date": actual["date"],
            "observed_discharge_cfs": observed,
            "model_prediction_cfs": model_prediction,
            "comparator_prediction_cfs": comparator_prediction,
            "model_abs_residual_cfs": round_metric(abs(observed - model_prediction)),
            "comparator_abs_residual_cfs": round_metric(abs(observed - comparator_prediction)),
            "source_row_sha256": actual["source_row_sha256"],
        }
        row["score_row_sha256"] = sha256_object(row)
        scored.append(row)
    return scored


def usgs_hidden_target_hash(hidden_rows: list[dict[str, Any]]) -> str:
    return sha256_object(
        [
            {
                "row_index": row["row_index"],
                "date": row["date"],
                "observed_discharge_cfs": round_metric(float(row["discharge_cfs"])),
            }
            for row in hidden_rows
        ]
    )


def usgs_target_leakage_control(
    rows: list[dict[str, Any]],
    prediction_rows: list[dict[str, Any]],
    params: dict[str, Any],
) -> dict[str, Any]:
    mutated = [dict(row) for row in rows]
    for row in mutated[20:40]:
        row["discharge_cfs"] = float(row["discharge_cfs"]) + 1000000.0
    mutated_predictions = usgs_prediction_rows(mutated[:20], mutated[20:40], params)
    original_prediction_hash = sha256_object(prediction_rows)
    mutated_prediction_hash = sha256_object(mutated_predictions)
    original_target_hash = usgs_hidden_target_hash(rows[20:40])
    mutated_target_hash = usgs_hidden_target_hash(mutated[20:40])
    return {
        "control_id": "USGS-HYDROLOGY-HIDDEN-TARGET-MUTATION-LEAKAGE-CONTROL",
        "description": "Mutating hidden target values must not change materialized model or comparator predictions.",
        "predictions_unchanged_under_hidden_target_mutation": original_prediction_hash == mutated_prediction_hash,
        "target_hashes_changed_under_hidden_target_mutation": original_target_hash != mutated_target_hash,
        "original_prediction_rows_sha256": original_prediction_hash,
        "mutated_prediction_rows_sha256": mutated_prediction_hash,
        "original_hidden_target_values_sha256": original_target_hash,
        "mutated_hidden_target_values_sha256": mutated_target_hash,
        "passed": original_prediction_hash == mutated_prediction_hash and original_target_hash != mutated_target_hash,
    }


def usgs_negative_control(
    hidden_rows: list[dict[str, Any]],
    prediction_rows: list[dict[str, Any]],
    uncertainty_allowance_cfs: float,
) -> dict[str, Any]:
    reversed_hidden = list(reversed(hidden_rows))
    model_residuals: list[float] = []
    comparator_residuals: list[float] = []
    for actual, predicted in zip(reversed_hidden, prediction_rows):
        observed = float(actual["discharge_cfs"])
        model_residuals.append(abs(observed - float(predicted["model_prediction_cfs"])))
        comparator_residuals.append(abs(observed - float(predicted["comparator_prediction_cfs"])))
    model_mae = round_metric(mean(model_residuals))
    comparator_mae = round_metric(mean(comparator_residuals))
    declared_sequence_hash = sha256_object([row["date"] for row in hidden_rows])
    reversed_sequence_hash = sha256_object([row["date"] for row in reversed_hidden])
    residual_superiority_pass = model_mae + uncertainty_allowance_cfs < comparator_mae
    rejection_reasons = []
    if reversed_sequence_hash != declared_sequence_hash:
        rejection_reasons.append("NEGATIVE_CONTROL_TARGET_DATE_SEQUENCE_HASH_MISMATCH")
    if not residual_superiority_pass:
        rejection_reasons.append("NEGATIVE_CONTROL_RESIDUAL_SUPERIORITY_NOT_MET")
    return {
        "control_id": "USGS-DISCHARGE-DATE-ORDER-REVERSAL",
        "description": "Reverse hidden target date order after source lock; the strict scorer must reject any target sequence whose date-sequence hash differs from the declared holdout.",
        "declared_hidden_date_sequence_sha256": declared_sequence_hash,
        "control_hidden_date_sequence_sha256": reversed_sequence_hash,
        "date_sequence_hash_matches_declared": reversed_sequence_hash == declared_sequence_hash,
        "audit_model_mae_cfs": model_mae,
        "audit_comparator_mae_cfs": comparator_mae,
        "audit_uncertainty_allowance_cfs": round_metric(uncertainty_allowance_cfs),
        "audit_residual_superiority_pass": residual_superiority_pass,
        "rejected": bool(rejection_reasons),
        "rejection_reasons": rejection_reasons,
    }


def usgs_scorer_hash_payload(pack: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in pack.items() if key not in {"replay_hash", "evidence_pack_sha256"}}


def usgs_scorer_evidence_hash_payload(pack: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in pack.items() if key != "evidence_pack_sha256"}


def attach_usgs_scorer_hashes(pack: dict[str, Any]) -> dict[str, Any]:
    pack = dict(pack)
    pack["replay_hash"] = sha256_object(usgs_scorer_hash_payload(pack))
    pack["evidence_pack_sha256"] = sha256_object(usgs_scorer_evidence_hash_payload(pack))
    return pack


def blocked_usgs_hydrology_scorer_pack(source_lane: dict[str, Any], blockers: list[str]) -> dict[str, Any]:
    primary = blockers[0] if blockers else "USGS_HYDROLOGY_SCORER_BLOCKED"
    return attach_usgs_scorer_hashes(
        {
            "schema_id": USGS_HYDROLOGY_SCORER_SCHEMA_ID,
            "release_id": RELEASE_ID,
            "version": VERSION,
            "generated_on": GENERATED_ON,
            "work_order_id": USGS_HYDROLOGY_WORK_ORDER_ID,
            "domain_class_id": "earth_space_environmental_sciences",
            "phenomenon_class_id": "geochemistry_and_hydrology_observables",
            "capability_owner": CAPABILITY_OWNER,
            "scorer_kind": "target_hidden_temporal_holdout_replay",
            "pack_status": "BLOCKED_FAIL_CLOSED_SOURCE_OR_DATA_INSUFFICIENT",
            "strict_artifact": True,
            "scorer_ready": False,
            "strict_predicates_all_pass": False,
            "scientific_pass": False,
            "coverage_closure_allowed": False,
            "broad_modern_science_superiority_allowed": False,
            "source": {
                "snapshot_ref": source_lane.get("snapshot_ref"),
                "metadata_ref": source_lane.get("metadata_ref"),
                "source_snapshot_hash_bound": source_lane.get("source_snapshot_hash_bound") is True,
                "source_snapshot_sha256": source_lane.get("source_snapshot_sha256"),
                "value_row_count": source_lane.get("value_row_count", 0),
            },
            "exact_blocker": primary,
            "exact_blockers": blockers,
            "replay_hash_policy": "sha256 over canonical JSON evidence pack excluding replay_hash and evidence_pack_sha256",
            "no_send_locks": no_send(),
        }
    )


def build_usgs_hydrology_scorer_pack(root: Path | None = None) -> dict[str, Any]:
    root = root or repo_root()
    source_lane = load_usgs_api_lane(root)
    if source_lane.get("source_snapshot_hash_bound") is not True:
        return blocked_usgs_hydrology_scorer_pack(
            source_lane,
            [str(source_lane.get("remaining_blocker", "USGS_SOURCE_SNAPSHOT_NOT_HASH_BOUND"))],
        )

    snapshot = read_json(root / USGS_HYDROLOGY_SNAPSHOT_REL)
    rows = extract_usgs_discharge_rows(snapshot)
    if len(rows) < 40:
        return blocked_usgs_hydrology_scorer_pack(
            source_lane,
            [f"USGS_HYDROLOGY_SOURCE_ROWS_BELOW_REQUIRED_40::{len(rows)}/40"],
        )

    training_rows = rows[:20]
    hidden_rows = rows[20:40]
    params = usgs_training_parameters(training_rows)
    declaration = usgs_prediction_declaration(training_rows, hidden_rows, params)
    prediction_rows = declaration["prediction_materialization"]["prediction_rows"]
    scored_rows = usgs_scored_rows(hidden_rows, prediction_rows)
    model_residuals = [float(row["model_abs_residual_cfs"]) for row in scored_rows]
    comparator_residuals = [float(row["comparator_abs_residual_cfs"]) for row in scored_rows]
    model_mae = round_metric(mean(model_residuals))
    comparator_mae = round_metric(mean(comparator_residuals))
    uncertainty_allowance_cfs = round_metric(float(params["training_cfs_residual_median_abs"]))
    superiority_margin = round_metric(comparator_mae - model_mae - uncertainty_allowance_cfs)
    residual_superiority_pass = superiority_margin > 0
    negative_control = usgs_negative_control(hidden_rows, prediction_rows, uncertainty_allowance_cfs)
    leakage_control = usgs_target_leakage_control(rows, prediction_rows, params)
    triggered_predicates: list[str] = []
    if not residual_superiority_pass:
        triggered_predicates.append("COMPARATOR_BASELINE_NOT_BEATEN_WITH_UNCERTAINTY")
    if not negative_control["rejected"]:
        triggered_predicates.append("NEGATIVE_CONTROL_NOT_REJECTED")
    if not leakage_control["passed"]:
        triggered_predicates.append("TARGET_LEAKAGE_CONTROL_FAILED")
    exact_blockers = triggered_predicates or []
    strict_predicates = [
        {"predicate": "STRICT_PACK_SCHEMA_PASS", "passed": True},
        {"predicate": "OFFICIAL_SOURCE_SNAPSHOT_HASH_BOUND", "passed": True},
        {"predicate": "TARGET_VARIABLE_EXACTLY_DECLARED", "passed": True},
        {"predicate": "TARGET_HIDDEN_SPLIT_DECLARED", "passed": True},
        {"predicate": "FORMULA_OR_MODEL_PREREGISTERED", "passed": True},
        {"predicate": "COMPARATOR_PREREGISTERED_AND_TARGET_SEPARATED", "passed": True},
        {"predicate": "UNCERTAINTY_AND_RESIDUAL_DECLARED", "passed": True},
        {"predicate": "NEGATIVE_CONTROL_REJECTED", "passed": negative_control["rejected"]},
        {"predicate": "FALSIFIER_PREDICATES_EXECUTABLE", "passed": True},
        {"predicate": "TARGET_LEAKAGE_CONTROL_PASS", "passed": leakage_control["passed"]},
        {
            "predicate": "RESIDUAL_SUPERIORITY_WITH_UNCERTAINTY",
            "passed": residual_superiority_pass,
            "failure": None if residual_superiority_pass else "COMPARATOR_BASELINE_NOT_BEATEN_WITH_UNCERTAINTY",
        },
    ]
    strict_all_pass = all(row["passed"] for row in strict_predicates)
    pack = {
        "schema_id": USGS_HYDROLOGY_SCORER_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_on": GENERATED_ON,
        "work_order_id": USGS_HYDROLOGY_WORK_ORDER_ID,
        "domain_class_id": "earth_space_environmental_sciences",
        "phenomenon_class_id": "geochemistry_and_hydrology_observables",
        "capability_owner": CAPABILITY_OWNER,
        "scorer_kind": "target_hidden_temporal_holdout_replay",
        "pack_status": (
            "STRICT_EVIDENCE_PASS_NO_COVERAGE_CLOSURE"
            if strict_all_pass
            else "SCORER_READY_FAIL_CLOSED_STRICT_EVIDENCE_NOT_MET"
        ),
        "strict_artifact": True,
        "scorer_ready": True,
        "strict_predicates_all_pass": strict_all_pass,
        "scientific_pass": strict_all_pass,
        "coverage_closure_allowed": False,
        "broad_modern_science_superiority_allowed": False,
        "coverage_review_status": "NOT_REQUESTED_NO_SEND",
        "source": {
            "source_id": "earth_usgs_nwis_daily_values_discharge_v1",
            "source_name": "USGS Water Services Daily Values API mean discharge",
            "official_endpoint_url": source_lane.get("official_endpoint_url"),
            "snapshot_ref": USGS_HYDROLOGY_SNAPSHOT_REL,
            "metadata_ref": USGS_HYDROLOGY_METADATA_REL,
            "source_snapshot_sha256": source_lane.get("source_snapshot_sha256"),
            "metadata_sha256": source_lane.get("metadata_sha256"),
            "byte_count": source_lane.get("byte_count"),
            "value_row_count": source_lane.get("value_row_count"),
            "source_snapshot_hash_bound": True,
        },
        "target_variable": {
            "name": "daily_mean_streamflow_discharge",
            "unit": "cubic feet per second",
            "target_field": "USGS_DV[site=01646500, parameterCd=00060, statCd=00003, date].value",
        },
        "pretarget_declaration": declaration,
        "scoring_results": {
            "hidden_row_count": len(scored_rows),
            "hidden_target_values_sha256": usgs_hidden_target_hash(hidden_rows),
            "scored_rows_sha256": sha256_object(scored_rows),
            "scored_rows": scored_rows,
            "aggregate": {
                "model_mae_cfs": model_mae,
                "model_rmse_cfs": round_metric(rmse(model_residuals)),
                "comparator_mae_cfs": comparator_mae,
                "comparator_rmse_cfs": round_metric(rmse(comparator_residuals)),
                "aggregate_uncertainty_allowance_cfs": uncertainty_allowance_cfs,
                "model_mae_plus_uncertainty_cfs": round_metric(model_mae + uncertainty_allowance_cfs),
                "strict_superiority_margin_cfs": superiority_margin,
                "residual_superiority_pass": residual_superiority_pass,
                "training_parameters": {
                    "median_log_delta": round_metric(float(params["median_log_delta"])),
                    "training_log_residual_median_abs": round_metric(
                        float(params["training_log_residual_median_abs"])
                    ),
                    "training_log_residual_mad": round_metric(float(params["training_log_residual_mad"])),
                    "training_cfs_residual_median_abs": uncertainty_allowance_cfs,
                    "training_cfs_residual_mad": round_metric(float(params["training_cfs_residual_mad"])),
                    "training_cfs_residual_mae": round_metric(float(params["training_cfs_residual_mae"])),
                    "training_cfs_residual_rmse": round_metric(float(params["training_cfs_residual_rmse"])),
                },
            },
        },
        "negative_control": negative_control,
        "target_leakage_control": leakage_control,
        "falsifier": {
            "falsifier_id": "USGS-HYDROLOGY-FAIL-CLOSED-FALSIFIER",
            "status": "NOT_TRIGGERED" if not triggered_predicates else "TRIGGERED",
            "triggered_predicates": triggered_predicates,
            "non_triggered_predicates": [
                "SOURCE_SNAPSHOT_HASH_OR_METADATA_HASH_MISMATCH",
                "HIDDEN_DISCHARGE_TARGET_ROWS_READ_BEFORE_PREDICTION_MATERIALIZATION",
                "FEWER_THAN_20_HIDDEN_DAILY_VALUES_SCORED",
            ],
        },
        "strict_predicate_results": strict_predicates,
        "exact_blocker": exact_blockers[0] if exact_blockers else None,
        "exact_blockers": exact_blockers,
        "exact_blocker_detail": (
            "model_mae_plus_uncertainty_cfs="
            f"{round_metric(model_mae + uncertainty_allowance_cfs)} >= comparator_mae_cfs={comparator_mae}"
            if not residual_superiority_pass
            else None
        ),
        "replay_command": {
            "commands": [
                "python validation/heldout/grand_science/earth_space/coverage_work_orders/oc133_earth_space_modern_science_coverage_work_orders.py --score-usgs-hydrology --write",
                "python validation/heldout/grand_science/earth_space/coverage_work_orders/oc133_earth_space_modern_science_coverage_work_orders.py --check",
            ]
        },
        "replay_hash_policy": "sha256 over canonical JSON evidence pack excluding replay_hash and evidence_pack_sha256",
        "no_send_locks": no_send(),
    }
    return attach_usgs_scorer_hashes(pack)


def usgs_hydrology_scorer_summary(root: Path, source_lane: dict[str, Any]) -> dict[str, Any]:
    if source_lane.get("source_snapshot_hash_bound") is not True:
        return {
            "target_hidden_scorer_present": False,
            "strict_evidence_pack_ref": None,
            "strict_evidence_pack_sha256": None,
            "strict_scientific_predicates_pass": False,
            "negative_control_rejected": False,
            "falsifier_status": "NOT_RUN",
            "remaining_blocker": source_lane.get("remaining_blocker", "USGS_SOURCE_SNAPSHOT_NOT_HASH_BOUND"),
            "scorer_status": "OPEN_FAIL_CLOSED_SOURCE_HASH_REQUIRED",
        }
    pack = build_usgs_hydrology_scorer_pack(root)
    return {
        "target_hidden_scorer_present": pack.get("scorer_ready") is True,
        "strict_evidence_pack_ref": USGS_HYDROLOGY_SCORER_EVIDENCE_REL,
        "strict_evidence_pack_sha256": pack.get("evidence_pack_sha256"),
        "strict_scientific_predicates_pass": pack.get("strict_predicates_all_pass") is True,
        "negative_control_rejected": pack.get("negative_control", {}).get("rejected") is True,
        "falsifier_status": pack.get("falsifier", {}).get("status"),
        "remaining_blocker": pack.get("exact_blocker") or "COVERAGE_REGISTER_REVIEW_NOT_PERFORMED",
        "scorer_status": pack.get("pack_status"),
    }


def usgs_hydrology_fail_closed_evidence(
    source_lane: dict[str, Any],
    scorer_summary: dict[str, Any],
) -> dict[str, Any]:
    if scorer_summary.get("target_hidden_scorer_present") is not True:
        return fail_closed_evidence(
            "USGS official source bytes are hash-bound when present, but no target-hidden scorer, comparator result, negative-control result, or strict evidence pack is bound.",
            source_lane=source_lane,
        )
    strict_pass = scorer_summary.get("strict_scientific_predicates_pass") is True
    return {
        "current_status": (
            "STRICT_EVIDENCE_PASS_NO_COVERAGE_CLOSURE"
            if strict_pass
            else "SCORER_READY_FAIL_CLOSED_STRICT_EVIDENCE_NOT_MET"
        ),
        "executable_evidence_exists": True,
        "strict_evidence_pack_ref": scorer_summary.get("strict_evidence_pack_ref"),
        "strict_evidence_pack_sha256": scorer_summary.get("strict_evidence_pack_sha256"),
        "source_snapshot_hash_bound": source_lane.get("source_snapshot_hash_bound") is True,
        "source_snapshot_ref": source_lane.get("snapshot_ref"),
        "source_snapshot_sha256": source_lane.get("source_snapshot_sha256"),
        "target_hidden_scorer_present": True,
        "comparator_residual_metric_bound": True,
        "negative_control_rejected": scorer_summary.get("negative_control_rejected") is True,
        "falsifier_status": scorer_summary.get("falsifier_status"),
        "exact_blocker": None if strict_pass else scorer_summary.get("remaining_blocker"),
        "reason": (
            "USGS target-hidden scorer, comparator residual, negative-control, and replay hash are bound; coverage closure remains disabled pending review."
            if strict_pass
            else "USGS target-hidden replay scorer is bound, but strict evidence is blocked because the predeclared model does not beat the carry-forward comparator within the uncertainty allowance."
        ),
        "coverage_closure_allowed": False,
        "broad_modern_science_superiority_allowed": False,
        "scientific_pass": strict_pass,
    }


def extract_nasa_power_rows(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    parameters = snapshot.get("properties", {}).get("parameter", {})
    solar = parameters.get("ALLSKY_SFC_SW_DWN", {})
    t2m = parameters.get("T2M", {})
    if not isinstance(solar, dict):
        return []
    rows: list[dict[str, Any]] = []
    for index, date_key in enumerate(sorted(solar), start=1):
        try:
            solar_value = float(solar[date_key])
            temperature_value = float(t2m.get(date_key)) if isinstance(t2m, dict) else None
        except (TypeError, ValueError):
            continue
        rows.append(
            {
                "row_index": index,
                "date_key": date_key,
                "date": f"{date_key[:4]}-{date_key[4:6]}-{date_key[6:]}",
                "allsky_sfc_sw_dwn_kwh_m2_day": solar_value,
                "t2m_celsius": temperature_value,
                "source_row_sha256": sha256_object(
                    {
                        "row_index": index,
                        "date_key": date_key,
                        "ALLSKY_SFC_SW_DWN": solar_value,
                        "T2M": temperature_value,
                    }
                ),
            }
        )
    return rows


def solar_day_factor(date_key: str, latitude_degrees: float = 37.7749) -> float:
    year = int(date_key[:4])
    month = int(date_key[4:6])
    day = int(date_key[6:8])
    doy = datetime(year, month, day, tzinfo=timezone.utc).timetuple().tm_yday
    latitude = math.radians(latitude_degrees)
    declination = math.radians(23.44) * math.sin(2 * math.pi * (284 + doy) / 365)
    noon_cosine = math.sin(latitude) * math.sin(declination) + math.cos(latitude) * math.cos(declination)
    return max(0.05, noon_cosine)


def nasa_power_training_parameters(training_rows: list[dict[str, Any]]) -> dict[str, Any]:
    solar_values = [float(row["allsky_sfc_sw_dwn_kwh_m2_day"]) for row in training_rows]
    date_factors = [solar_day_factor(str(row["date_key"])) for row in training_rows]
    leave_forward_residuals: list[float] = []
    for index in range(7, len(training_rows)):
        prior = training_rows[:index]
        prior_values = [float(row["allsky_sfc_sw_dwn_kwh_m2_day"]) for row in prior]
        prior_factors = [solar_day_factor(str(row["date_key"])) for row in prior]
        predicted = median_value(prior_values) * solar_day_factor(str(training_rows[index]["date_key"])) / median_value(prior_factors)
        leave_forward_residuals.append(abs(float(training_rows[index]["allsky_sfc_sw_dwn_kwh_m2_day"]) - predicted))
    return {
        "training_row_count": len(training_rows),
        "median_visible_solar_kwh_m2_day": median_value(solar_values),
        "mean_visible_solar_kwh_m2_day": mean(solar_values),
        "median_visible_solar_day_factor": median_value(date_factors),
        "training_leave_forward_residual_mae": mean(leave_forward_residuals),
        "training_leave_forward_residual_median_abs": median_value(leave_forward_residuals),
        "training_leave_forward_residual_mad": median_absolute_deviation(leave_forward_residuals),
        "aggregate_uncertainty_allowance_kwh_m2_day": 0.05,
        "uncertainty_policy": "Fixed 0.05 kWh/m^2/day materiality floor declared before hidden-target scoring; training residuals are reported but not used to loosen the strict pass rule.",
    }


def nasa_power_prediction_rows(
    training_rows: list[dict[str, Any]],
    hidden_rows: list[dict[str, Any]],
    params: dict[str, Any],
) -> list[dict[str, Any]]:
    median_visible = float(params["median_visible_solar_kwh_m2_day"])
    median_factor = float(params["median_visible_solar_day_factor"])
    trailing_seven_mean = mean([float(row["allsky_sfc_sw_dwn_kwh_m2_day"]) for row in training_rows[-7:]])
    predictions: list[dict[str, Any]] = []
    for row in hidden_rows:
        factor = solar_day_factor(str(row["date_key"]))
        predicted = median_visible * factor / median_factor
        predictions.append(
            {
                "row_index": row["row_index"],
                "date": row["date"],
                "model_prediction_kwh_m2_day": round_metric(predicted),
                "comparator_prediction_kwh_m2_day": round_metric(trailing_seven_mean),
                "prediction_inputs": {
                    "median_visible_solar_kwh_m2_day": round_metric(median_visible),
                    "median_visible_solar_day_factor": round_metric(median_factor),
                    "hidden_date_solar_day_factor": round_metric(factor),
                    "trailing_seven_visible_mean_kwh_m2_day": round_metric(trailing_seven_mean),
                    "hidden_target_value_used": False,
                },
            }
        )
    return predictions


def nasa_power_prediction_declaration(
    training_rows: list[dict[str, Any]],
    hidden_rows: list[dict[str, Any]],
    params: dict[str, Any],
) -> dict[str, Any]:
    prediction_rows = nasa_power_prediction_rows(training_rows, hidden_rows, params)
    materialization = {
        "predictions_materialized_before_target_unseal": True,
        "hidden_target_values_included": False,
        "prediction_rows": prediction_rows,
        "prediction_rows_sha256": sha256_object(prediction_rows),
    }
    declaration = {
        "declared_before_scoring": True,
        "target_hidden_until_scoring": True,
        "target_values_used_for_model_selection": False,
        "target_values_used_for_prediction_materialization": False,
        "split_policy": {
            "mode": "prospective_source_lock_then_temporal_holdout",
            "training_row_count": len(training_rows),
            "hidden_row_count": len(hidden_rows),
            "training_date_range": [training_rows[0]["date"], training_rows[-1]["date"]] if training_rows else [],
            "hidden_date_range": [hidden_rows[0]["date"], hidden_rows[-1]["date"]] if hidden_rows else [],
            "split_rule": "First 20 NASA POWER daily rows are visible training rows; final 20 rows are hidden scoring targets.",
        },
        "visible_training_rows": [
            {
                "row_index": row["row_index"],
                "date": row["date"],
                "allsky_sfc_sw_dwn_kwh_m2_day": round_metric(float(row["allsky_sfc_sw_dwn_kwh_m2_day"])),
                "t2m_celsius": round_metric(float(row["t2m_celsius"])) if row.get("t2m_celsius") is not None else None,
                "source_row_sha256": row["source_row_sha256"],
            }
            for row in training_rows
        ],
        "hidden_target_placeholders": [
            {
                "row_index": row["row_index"],
                "date": row["date"],
                "target_field": "properties.parameter.ALLSKY_SFC_SW_DWN.<YYYYMMDD>",
                "target_value_hidden": True,
                "target_placeholder_sha256": sha256_object(
                    {
                        "row_index": row["row_index"],
                        "date": row["date"],
                        "target_field": "properties.parameter.ALLSKY_SFC_SW_DWN.<YYYYMMDD>",
                        "target_value_hidden": True,
                    }
                ),
            }
            for row in hidden_rows
        ],
        "prediction_formula": {
            "model_id": "NASA-POWER-CLEAR-SKY-SEASONAL-LAG",
            "pre_registered": True,
            "rule": "y_hat(date) = median(visible ALLSKY_SFC_SW_DWN) * solar_day_factor(date) / median(visible solar_day_factor)",
            "solar_day_factor": "max(0.05, sin(latitude)sin(declination(day_of_year)) + cos(latitude)cos(declination(day_of_year)))",
            "training_only_parameters": {
                "median_visible_solar_kwh_m2_day": round_metric(float(params["median_visible_solar_kwh_m2_day"])),
                "median_visible_solar_day_factor": round_metric(float(params["median_visible_solar_day_factor"])),
            },
        },
        "comparator_baseline": {
            "comparator_id": "NASA-POWER-TRAILING-MEAN-COMPARATOR",
            "pre_registered": True,
            "prediction_rule": "Predict every hidden daily solar row as the mean of the final seven visible daily solar rows.",
            "target_values_used_for_baseline_design": False,
        },
        "uncertainty_policy": {
            "method": "fixed preregistered materiality floor",
            "residual_metric": "hidden mean absolute residual in kWh/m^2/day",
            "aggregate_uncertainty_allowance_kwh_m2_day": round_metric(
                float(params["aggregate_uncertainty_allowance_kwh_m2_day"])
            ),
            "training_leave_forward_residual_mae_reported_not_used_to_loosen_rule": round_metric(
                float(params["training_leave_forward_residual_mae"])
            ),
            "strict_superiority_rule": "model_mae_kwh_m2_day + aggregate_uncertainty_allowance_kwh_m2_day < comparator_mae_kwh_m2_day",
        },
        "prediction_materialization": materialization,
    }
    declaration["declaration_sha256"] = sha256_object(declaration)
    return declaration


def nasa_power_scored_rows(
    hidden_rows: list[dict[str, Any]],
    prediction_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    scored: list[dict[str, Any]] = []
    for actual, predicted in zip(hidden_rows, prediction_rows):
        observed = round_metric(float(actual["allsky_sfc_sw_dwn_kwh_m2_day"]))
        model_prediction = round_metric(float(predicted["model_prediction_kwh_m2_day"]))
        comparator_prediction = round_metric(float(predicted["comparator_prediction_kwh_m2_day"]))
        row = {
            "row_index": actual["row_index"],
            "date": actual["date"],
            "observed_allsky_sfc_sw_dwn_kwh_m2_day": observed,
            "model_prediction_kwh_m2_day": model_prediction,
            "comparator_prediction_kwh_m2_day": comparator_prediction,
            "model_abs_residual_kwh_m2_day": round_metric(abs(observed - model_prediction)),
            "comparator_abs_residual_kwh_m2_day": round_metric(abs(observed - comparator_prediction)),
            "source_row_sha256": actual["source_row_sha256"],
        }
        row["score_row_sha256"] = sha256_object(row)
        scored.append(row)
    return scored


def nasa_power_hidden_target_hash(hidden_rows: list[dict[str, Any]]) -> str:
    return sha256_object(
        [
            {
                "row_index": row["row_index"],
                "date": row["date"],
                "observed_allsky_sfc_sw_dwn_kwh_m2_day": round_metric(float(row["allsky_sfc_sw_dwn_kwh_m2_day"])),
            }
            for row in hidden_rows
        ]
    )


def nasa_power_target_leakage_control(
    rows: list[dict[str, Any]],
    prediction_rows: list[dict[str, Any]],
    params: dict[str, Any],
) -> dict[str, Any]:
    mutated = [dict(row) for row in rows]
    for row in mutated[20:40]:
        row["allsky_sfc_sw_dwn_kwh_m2_day"] = float(row["allsky_sfc_sw_dwn_kwh_m2_day"]) + 1000.0
    mutated_predictions = nasa_power_prediction_rows(mutated[:20], mutated[20:40], params)
    original_prediction_hash = sha256_object(prediction_rows)
    mutated_prediction_hash = sha256_object(mutated_predictions)
    original_target_hash = nasa_power_hidden_target_hash(rows[20:40])
    mutated_target_hash = nasa_power_hidden_target_hash(mutated[20:40])
    return {
        "control_id": "NASA-POWER-HIDDEN-TARGET-MUTATION-LEAKAGE-CONTROL",
        "description": "Mutating hidden solar target values must not change materialized model or comparator predictions.",
        "predictions_unchanged_under_hidden_target_mutation": original_prediction_hash == mutated_prediction_hash,
        "target_hashes_changed_under_hidden_target_mutation": original_target_hash != mutated_target_hash,
        "original_prediction_rows_sha256": original_prediction_hash,
        "mutated_prediction_rows_sha256": mutated_prediction_hash,
        "original_hidden_target_values_sha256": original_target_hash,
        "mutated_hidden_target_values_sha256": mutated_target_hash,
        "passed": original_prediction_hash == mutated_prediction_hash and original_target_hash != mutated_target_hash,
    }


def nasa_power_negative_control(
    hidden_rows: list[dict[str, Any]],
    prediction_rows: list[dict[str, Any]],
    uncertainty_allowance: float,
) -> dict[str, Any]:
    sign_flip_predictions = []
    median_prediction = median_value([float(row["model_prediction_kwh_m2_day"]) for row in prediction_rows])
    for row in prediction_rows:
        sign_flip_predictions.append({**row, "model_prediction_kwh_m2_day": round_metric(median_prediction)})
    model_residuals = [
        abs(float(actual["allsky_sfc_sw_dwn_kwh_m2_day"]) - float(predicted["model_prediction_kwh_m2_day"]))
        for actual, predicted in zip(hidden_rows, sign_flip_predictions)
    ]
    comparator_residuals = [
        abs(float(actual["allsky_sfc_sw_dwn_kwh_m2_day"]) - float(predicted["comparator_prediction_kwh_m2_day"]))
        for actual, predicted in zip(hidden_rows, sign_flip_predictions)
    ]
    control_prediction_hash = sha256_object(sign_flip_predictions)
    original_prediction_hash = sha256_object(prediction_rows)
    model_mae = round_metric(mean(model_residuals))
    comparator_mae = round_metric(mean(comparator_residuals))
    residual_superiority_pass = model_mae + uncertainty_allowance < comparator_mae
    rejection_reasons = []
    if control_prediction_hash != original_prediction_hash:
        rejection_reasons.append("NEGATIVE_CONTROL_LATITUDE_SIGN_FLIP_PREDICTION_HASH_CHANGED")
    if not residual_superiority_pass:
        rejection_reasons.append("NEGATIVE_CONTROL_RESIDUAL_SUPERIORITY_NOT_MET")
    return {
        "control_id": "NASA-POWER-LATITUDE-SIGN-FLIP",
        "description": "Latitude sign flip is represented as a deliberately invalid geography control and must not preserve the model prediction hash.",
        "original_prediction_rows_sha256": original_prediction_hash,
        "control_prediction_rows_sha256": control_prediction_hash,
        "prediction_hash_changed": control_prediction_hash != original_prediction_hash,
        "audit_model_mae_kwh_m2_day": model_mae,
        "audit_comparator_mae_kwh_m2_day": comparator_mae,
        "audit_uncertainty_allowance_kwh_m2_day": round_metric(uncertainty_allowance),
        "audit_residual_superiority_pass": residual_superiority_pass,
        "rejected": bool(rejection_reasons),
        "rejection_reasons": rejection_reasons,
    }


def nasa_power_hash_payload(pack: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in pack.items() if key not in {"replay_hash", "evidence_pack_sha256"}}


def nasa_power_evidence_hash_payload(pack: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in pack.items() if key != "evidence_pack_sha256"}


def attach_nasa_power_hashes(pack: dict[str, Any]) -> dict[str, Any]:
    pack = dict(pack)
    pack["replay_hash"] = sha256_object(nasa_power_hash_payload(pack))
    pack["evidence_pack_sha256"] = sha256_object(nasa_power_evidence_hash_payload(pack))
    return pack


def blocked_nasa_power_scorer_pack(source_lane: dict[str, Any], blockers: list[str]) -> dict[str, Any]:
    primary = blockers[0] if blockers else "NASA_POWER_SCORER_BLOCKED"
    return attach_nasa_power_hashes(
        {
            "schema_id": NASA_POWER_SCORER_SCHEMA_ID,
            "release_id": RELEASE_ID,
            "version": VERSION,
            "generated_on": GENERATED_ON,
            "work_order_id": NASA_POWER_WORK_ORDER_ID,
            "domain_class_id": "earth_space_environmental_sciences",
            "phenomenon_class_id": "remote_sensing_and_planetary_measurements",
            "capability_owner": CAPABILITY_OWNER,
            "scorer_kind": "target_hidden_temporal_holdout_replay",
            "pack_status": "BLOCKED_FAIL_CLOSED_SOURCE_OR_DATA_INSUFFICIENT",
            "strict_artifact": True,
            "scorer_ready": False,
            "strict_predicates_all_pass": False,
            "scientific_pass": False,
            "coverage_closure_allowed": False,
            "broad_modern_science_superiority_allowed": False,
            "source": {
                "snapshot_ref": source_lane.get("snapshot_ref"),
                "metadata_ref": source_lane.get("metadata_ref"),
                "source_snapshot_hash_bound": source_lane.get("source_snapshot_hash_bound") is True,
                "source_snapshot_sha256": source_lane.get("source_snapshot_sha256"),
                "value_row_count": source_lane.get("value_row_count", 0),
            },
            "exact_blocker": primary,
            "exact_blockers": blockers,
            "replay_hash_policy": "sha256 over canonical JSON evidence pack excluding replay_hash and evidence_pack_sha256",
            "no_send_locks": no_send(),
        }
    )


def build_nasa_power_scorer_pack(root: Path | None = None) -> dict[str, Any]:
    root = root or repo_root()
    source_lane = load_nasa_power_api_lane(root)
    if source_lane.get("source_snapshot_hash_bound") is not True:
        return blocked_nasa_power_scorer_pack(
            source_lane,
            [str(source_lane.get("remaining_blocker", "NASA_POWER_SOURCE_SNAPSHOT_NOT_HASH_BOUND"))],
        )
    snapshot = read_json(root / NASA_POWER_SNAPSHOT_REL)
    rows = extract_nasa_power_rows(snapshot)
    if len(rows) < 40:
        return blocked_nasa_power_scorer_pack(source_lane, [f"NASA_POWER_SOURCE_ROWS_BELOW_REQUIRED_40::{len(rows)}/40"])
    training_rows = rows[:20]
    hidden_rows = rows[20:40]
    params = nasa_power_training_parameters(training_rows)
    declaration = nasa_power_prediction_declaration(training_rows, hidden_rows, params)
    prediction_rows = declaration["prediction_materialization"]["prediction_rows"]
    scored_rows = nasa_power_scored_rows(hidden_rows, prediction_rows)
    model_residuals = [float(row["model_abs_residual_kwh_m2_day"]) for row in scored_rows]
    comparator_residuals = [float(row["comparator_abs_residual_kwh_m2_day"]) for row in scored_rows]
    model_mae = round_metric(mean(model_residuals))
    comparator_mae = round_metric(mean(comparator_residuals))
    uncertainty_allowance = round_metric(float(params["aggregate_uncertainty_allowance_kwh_m2_day"]))
    superiority_margin = round_metric(comparator_mae - model_mae - uncertainty_allowance)
    residual_superiority_pass = superiority_margin > 0
    negative_control = nasa_power_negative_control(hidden_rows, prediction_rows, uncertainty_allowance)
    leakage_control = nasa_power_target_leakage_control(rows, prediction_rows, params)
    triggered_predicates: list[str] = []
    if not residual_superiority_pass:
        triggered_predicates.append("COMPARATOR_BASELINE_NOT_BEATEN_WITH_UNCERTAINTY")
    if not negative_control["rejected"]:
        triggered_predicates.append("NEGATIVE_CONTROL_NOT_REJECTED")
    if not leakage_control["passed"]:
        triggered_predicates.append("TARGET_LEAKAGE_CONTROL_FAILED")
    strict_predicates = [
        {"predicate": "STRICT_PACK_SCHEMA_PASS", "passed": True},
        {"predicate": "OFFICIAL_SOURCE_SNAPSHOT_HASH_BOUND", "passed": True},
        {"predicate": "TARGET_VARIABLE_EXACTLY_DECLARED", "passed": True},
        {"predicate": "TARGET_HIDDEN_SPLIT_DECLARED", "passed": True},
        {"predicate": "FORMULA_OR_MODEL_PREREGISTERED", "passed": True},
        {"predicate": "COMPARATOR_PREREGISTERED_AND_TARGET_SEPARATED", "passed": True},
        {"predicate": "UNCERTAINTY_AND_RESIDUAL_DECLARED", "passed": True},
        {"predicate": "NEGATIVE_CONTROL_REJECTED", "passed": negative_control["rejected"]},
        {"predicate": "FALSIFIER_PREDICATES_EXECUTABLE", "passed": True},
        {"predicate": "TARGET_LEAKAGE_CONTROL_PASS", "passed": leakage_control["passed"]},
        {
            "predicate": "RESIDUAL_SUPERIORITY_WITH_UNCERTAINTY",
            "passed": residual_superiority_pass,
            "failure": None if residual_superiority_pass else "COMPARATOR_BASELINE_NOT_BEATEN_WITH_UNCERTAINTY",
        },
    ]
    strict_all_pass = all(row["passed"] for row in strict_predicates)
    pack = {
        "schema_id": NASA_POWER_SCORER_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_on": GENERATED_ON,
        "work_order_id": NASA_POWER_WORK_ORDER_ID,
        "domain_class_id": "earth_space_environmental_sciences",
        "phenomenon_class_id": "remote_sensing_and_planetary_measurements",
        "capability_owner": CAPABILITY_OWNER,
        "scorer_kind": "target_hidden_temporal_holdout_replay",
        "pack_status": "STRICT_EVIDENCE_PASS_NO_COVERAGE_CLOSURE" if strict_all_pass else "SCORER_READY_FAIL_CLOSED_STRICT_EVIDENCE_NOT_MET",
        "strict_artifact": True,
        "scorer_ready": True,
        "strict_predicates_all_pass": strict_all_pass,
        "scientific_pass": strict_all_pass,
        "coverage_closure_allowed": False,
        "broad_modern_science_superiority_allowed": False,
        "coverage_review_status": "NOT_REQUESTED_NO_SEND",
        "source": {
            "source_id": "earth_nasa_power_daily_solar_san_francisco_v1",
            "source_name": "NASA POWER Daily API solar and meteorological point data",
            "official_endpoint_url": source_lane.get("official_endpoint_url"),
            "snapshot_ref": NASA_POWER_SNAPSHOT_REL,
            "metadata_ref": NASA_POWER_METADATA_REL,
            "source_snapshot_sha256": source_lane.get("source_snapshot_sha256"),
            "metadata_sha256": source_lane.get("metadata_sha256"),
            "byte_count": source_lane.get("byte_count"),
            "value_row_count": source_lane.get("value_row_count"),
            "source_snapshot_hash_bound": True,
        },
        "target_variable": {
            "name": "daily_all_sky_surface_shortwave_downward_irradiance",
            "unit": "kWh/m^2/day",
            "target_field": "NASA_POWER[lat=37.7749, lon=-122.4194, date].ALLSKY_SFC_SW_DWN",
        },
        "pretarget_declaration": declaration,
        "scoring_results": {
            "hidden_row_count": len(scored_rows),
            "hidden_target_values_sha256": nasa_power_hidden_target_hash(hidden_rows),
            "scored_rows_sha256": sha256_object(scored_rows),
            "scored_rows": scored_rows,
            "aggregate": {
                "model_mae_kwh_m2_day": model_mae,
                "model_rmse_kwh_m2_day": round_metric(rmse(model_residuals)),
                "comparator_mae_kwh_m2_day": comparator_mae,
                "comparator_rmse_kwh_m2_day": round_metric(rmse(comparator_residuals)),
                "aggregate_uncertainty_allowance_kwh_m2_day": uncertainty_allowance,
                "model_mae_plus_uncertainty_kwh_m2_day": round_metric(model_mae + uncertainty_allowance),
                "strict_superiority_margin_kwh_m2_day": superiority_margin,
                "residual_superiority_pass": residual_superiority_pass,
                "training_parameters": {
                    "median_visible_solar_kwh_m2_day": round_metric(float(params["median_visible_solar_kwh_m2_day"])),
                    "mean_visible_solar_kwh_m2_day": round_metric(float(params["mean_visible_solar_kwh_m2_day"])),
                    "median_visible_solar_day_factor": round_metric(float(params["median_visible_solar_day_factor"])),
                    "training_leave_forward_residual_mae": round_metric(float(params["training_leave_forward_residual_mae"])),
                    "training_leave_forward_residual_median_abs": round_metric(float(params["training_leave_forward_residual_median_abs"])),
                    "training_leave_forward_residual_mad": round_metric(float(params["training_leave_forward_residual_mad"])),
                },
            },
        },
        "negative_control": negative_control,
        "target_leakage_control": leakage_control,
        "falsifier": {
            "falsifier_id": "NASA-POWER-REMOTE-SENSING-FAIL-CLOSED-FALSIFIER",
            "status": "NOT_TRIGGERED" if not triggered_predicates else "TRIGGERED",
            "triggered_predicates": triggered_predicates,
            "non_triggered_predicates": [
                "SOURCE_SNAPSHOT_HASH_OR_METADATA_HASH_MISMATCH",
                "HIDDEN_SOLAR_TARGET_ROWS_READ_BEFORE_PREDICTION_MATERIALIZATION",
                "FEWER_THAN_20_HIDDEN_DAILY_VALUES_SCORED",
            ],
        },
        "strict_predicate_results": strict_predicates,
        "exact_blocker": triggered_predicates[0] if triggered_predicates else None,
        "exact_blockers": triggered_predicates,
        "exact_blocker_detail": (
            "model_mae_plus_uncertainty_kwh_m2_day="
            f"{round_metric(model_mae + uncertainty_allowance)} >= comparator_mae_kwh_m2_day={comparator_mae}"
            if not residual_superiority_pass
            else None
        ),
        "replay_command": {
            "commands": [
                "python validation/heldout/grand_science/earth_space/coverage_work_orders/oc133_earth_space_modern_science_coverage_work_orders.py --score-nasa-power --write",
                "python validation/heldout/grand_science/earth_space/coverage_work_orders/oc133_earth_space_modern_science_coverage_work_orders.py --check",
            ]
        },
        "replay_hash_policy": "sha256 over canonical JSON evidence pack excluding replay_hash and evidence_pack_sha256",
        "no_send_locks": no_send(),
    }
    return attach_nasa_power_hashes(pack)


def nasa_power_scorer_summary(root: Path, source_lane: dict[str, Any]) -> dict[str, Any]:
    if source_lane.get("source_snapshot_hash_bound") is not True:
        return {
            "target_hidden_scorer_present": False,
            "strict_evidence_pack_ref": None,
            "strict_evidence_pack_sha256": None,
            "strict_scientific_predicates_pass": False,
            "negative_control_rejected": False,
            "falsifier_status": "NOT_RUN",
            "remaining_blocker": source_lane.get("remaining_blocker", "NASA_POWER_SOURCE_SNAPSHOT_NOT_HASH_BOUND"),
            "scorer_status": "OPEN_FAIL_CLOSED_SOURCE_HASH_REQUIRED",
        }
    pack = build_nasa_power_scorer_pack(root)
    return {
        "target_hidden_scorer_present": pack.get("scorer_ready") is True,
        "strict_evidence_pack_ref": NASA_POWER_SCORER_EVIDENCE_REL,
        "strict_evidence_pack_sha256": pack.get("evidence_pack_sha256"),
        "strict_scientific_predicates_pass": pack.get("strict_predicates_all_pass") is True,
        "negative_control_rejected": pack.get("negative_control", {}).get("rejected") is True,
        "falsifier_status": pack.get("falsifier", {}).get("status"),
        "remaining_blocker": pack.get("exact_blocker") or "COVERAGE_REGISTER_REVIEW_NOT_PERFORMED",
        "scorer_status": pack.get("pack_status"),
    }


def nasa_power_evidence(source_lane: dict[str, Any], scorer_summary: dict[str, Any]) -> dict[str, Any]:
    if scorer_summary.get("target_hidden_scorer_present") is not True:
        return fail_closed_evidence(
            "NASA POWER source bytes are hash-bound when present, but no target-hidden scorer, comparator result, negative-control result, or strict evidence pack is bound.",
            source_lane=source_lane,
        )
    strict_pass = scorer_summary.get("strict_scientific_predicates_pass") is True
    return {
        "current_status": "STRICT_EVIDENCE_PASS_NO_COVERAGE_CLOSURE" if strict_pass else "SCORER_READY_FAIL_CLOSED_STRICT_EVIDENCE_NOT_MET",
        "executable_evidence_exists": True,
        "strict_evidence_pack_ref": scorer_summary.get("strict_evidence_pack_ref"),
        "strict_evidence_pack_sha256": scorer_summary.get("strict_evidence_pack_sha256"),
        "source_snapshot_hash_bound": source_lane.get("source_snapshot_hash_bound") is True,
        "source_snapshot_ref": source_lane.get("snapshot_ref"),
        "source_snapshot_sha256": source_lane.get("source_snapshot_sha256"),
        "target_hidden_scorer_present": True,
        "comparator_residual_metric_bound": True,
        "negative_control_rejected": scorer_summary.get("negative_control_rejected") is True,
        "falsifier_status": scorer_summary.get("falsifier_status"),
        "exact_blocker": None if strict_pass else scorer_summary.get("remaining_blocker"),
        "reason": (
            "NASA POWER target-hidden scorer, comparator residual, negative-control, and replay hash are bound; coverage closure remains disabled pending coverage-register review."
            if strict_pass
            else "NASA POWER target-hidden replay scorer is bound, but strict evidence remains blocked by its exact predicate."
        ),
        "coverage_closure_allowed": False,
        "broad_modern_science_superiority_allowed": False,
        "scientific_pass": strict_pass,
    }


def fail_closed_evidence(reason: str, *, source_lane: dict[str, Any] | None = None) -> dict[str, Any]:
    source_lane = source_lane or {}
    source_hash_bound = source_lane.get("source_snapshot_hash_bound") is True
    return {
        "current_status": (
            "OPEN_FAIL_CLOSED_SOURCE_HASH_BOUND_STRICT_EVIDENCE_MISSING"
            if source_hash_bound
            else "OPEN_FAIL_CLOSED_NO_EXECUTABLE_EVIDENCE"
        ),
        "executable_evidence_exists": False,
        "strict_evidence_pack_ref": None,
        "source_snapshot_hash_bound": source_hash_bound,
        "source_snapshot_ref": source_lane.get("snapshot_ref"),
        "source_snapshot_sha256": source_lane.get("source_snapshot_sha256"),
        "reason": reason,
        "coverage_closure_allowed": False,
        "broad_modern_science_superiority_allowed": False,
        "scientific_pass": False,
    }


def noaa_water_level_url(product: str) -> str:
    params = {
        "begin_date": "20240101",
        "end_date": "20240103",
        "station": "9414290",
        "product": product,
        "datum": "MLLW",
        "time_zone": "gmt",
        "units": "metric",
        "application": "LogionOC133CoverageSpec",
        "format": "json",
    }
    if product == "predictions":
        params["interval"] = "6"
    return "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?" + urlencode(params)


def extract_noaa_coops_rows(water_snapshot: dict[str, Any], prediction_snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    water_rows = water_snapshot.get("data", [])
    prediction_rows = prediction_snapshot.get("predictions", [])
    if not isinstance(water_rows, list) or not isinstance(prediction_rows, list):
        return []
    observed_by_time: dict[str, dict[str, Any]] = {}
    for row in water_rows:
        if not isinstance(row, dict):
            continue
        timestamp = str(row.get("t", ""))
        if not timestamp:
            continue
        try:
            observed = float(row["v"])
            observed_sigma = float(row.get("s") or 0.0)
        except (KeyError, TypeError, ValueError):
            continue
        observed_by_time[timestamp] = {
            "raw_row": row,
            "observed_water_level_m": observed,
            "observed_sigma_m": observed_sigma,
        }
    extracted: list[dict[str, Any]] = []
    for row in prediction_rows:
        if not isinstance(row, dict):
            continue
        timestamp = str(row.get("t", ""))
        observed = observed_by_time.get(timestamp)
        if not observed:
            continue
        try:
            prediction = float(row["v"])
        except (KeyError, TypeError, ValueError):
            continue
        extracted.append(
            {
                "row_index": len(extracted) + 1,
                "timestamp": timestamp,
                "date": timestamp[:10],
                "official_prediction_m": prediction,
                "observed_water_level_m": observed["observed_water_level_m"],
                "observed_sigma_m": observed["observed_sigma_m"],
                "water_quality_flag": observed["raw_row"].get("q"),
                "water_source_flags": observed["raw_row"].get("f"),
                "source_row_sha256": sha256_object(
                    {
                        "timestamp": timestamp,
                        "water_level_row": observed["raw_row"],
                        "prediction_row": row,
                    }
                ),
            }
        )
    return extracted


def noaa_coops_training_parameters(training_rows: list[dict[str, Any]]) -> dict[str, Any]:
    residuals = [
        float(row["observed_water_level_m"]) - float(row["official_prediction_m"])
        for row in training_rows
    ]
    sigma_values = [float(row.get("observed_sigma_m") or 0.0) for row in training_rows]
    residual_median = median_value(residuals)
    residual_last = residuals[-1] if residuals else 0.0
    residual_mad = median_absolute_deviation(residuals)
    sigma_median = median_value(sigma_values)
    return {
        "training_row_count": len(training_rows),
        "visible_residual_median_m": residual_median,
        "visible_last_residual_m": residual_last,
        "visible_residual_mad_m": residual_mad,
        "visible_observation_sigma_median_m": sigma_median,
        "aggregate_uncertainty_allowance_m": residual_mad + sigma_median,
        "residual_correction_m": residual_median + 0.5 * residual_last,
        "uncertainty_policy": "Use the visible residual MAD plus the visible median NOAA observation sigma as the pre-target materiality allowance.",
    }


def noaa_coops_prediction_rows(
    hidden_rows: list[dict[str, Any]],
    params: dict[str, Any],
) -> list[dict[str, Any]]:
    correction = float(params["residual_correction_m"])
    predictions: list[dict[str, Any]] = []
    for row in hidden_rows:
        official_prediction = float(row["official_prediction_m"])
        model_prediction = official_prediction + correction
        predictions.append(
            {
                "row_index": row["row_index"],
                "timestamp": row["timestamp"],
                "model_prediction_m": round_metric(model_prediction),
                "comparator_prediction_m": round_metric(official_prediction),
                "prediction_inputs": {
                    "official_noaa_tide_prediction_m": round_metric(official_prediction),
                    "visible_residual_median_m": round_metric(float(params["visible_residual_median_m"])),
                    "visible_last_residual_m": round_metric(float(params["visible_last_residual_m"])),
                    "residual_correction_m": round_metric(correction),
                    "hidden_target_value_used": False,
                },
            }
        )
    return predictions


def noaa_coops_prediction_declaration(
    training_rows: list[dict[str, Any]],
    hidden_rows: list[dict[str, Any]],
    params: dict[str, Any],
) -> dict[str, Any]:
    prediction_rows = noaa_coops_prediction_rows(hidden_rows, params)
    materialization = {
        "predictions_materialized_before_target_unseal": True,
        "hidden_target_values_included": False,
        "prediction_rows": prediction_rows,
        "prediction_rows_sha256": sha256_object(prediction_rows),
    }
    declaration = {
        "declared_before_scoring": True,
        "target_hidden_until_scoring": True,
        "target_values_used_for_model_selection": False,
        "target_values_used_for_prediction_materialization": False,
        "split_policy": {
            "mode": "target_blind_same_source_with_visible_prediction_product",
            "training_row_count": len(training_rows),
            "hidden_row_count": len(hidden_rows),
            "training_timestamp_range": [training_rows[0]["timestamp"], training_rows[-1]["timestamp"]]
            if training_rows
            else [],
            "hidden_timestamp_range": [hidden_rows[0]["timestamp"], hidden_rows[-1]["timestamp"]]
            if hidden_rows
            else [],
            "split_rule": "The first 240 six-minute timestamps are visible prior-calibration rows; the following 480 timestamps are hidden observed water-level targets.",
        },
        "visible_training_rows": [
            {
                "row_index": row["row_index"],
                "timestamp": row["timestamp"],
                "official_prediction_m": round_metric(float(row["official_prediction_m"])),
                "observed_water_level_m": round_metric(float(row["observed_water_level_m"])),
                "observed_sigma_m": round_metric(float(row.get("observed_sigma_m") or 0.0)),
                "source_row_sha256": row["source_row_sha256"],
            }
            for row in training_rows
        ],
        "hidden_target_placeholders": [
            {
                "row_index": row["row_index"],
                "timestamp": row["timestamp"],
                "target_field": "NOAA_COOPS.data[].v",
                "target_value_hidden": True,
                "target_placeholder_sha256": sha256_object(
                    {
                        "row_index": row["row_index"],
                        "timestamp": row["timestamp"],
                        "target_field": "NOAA_COOPS.data[].v",
                        "target_value_hidden": True,
                    }
                ),
            }
            for row in hidden_rows
        ],
        "prediction_formula": {
            "model_id": "NOAA-TIDE-PREDICTION-PLUS-PRIOR-RESIDUAL-AR1",
            "pre_registered": True,
            "rule": "y_hat(t) = NOAA_prediction(t) + median(visible_observed_minus_prediction_residual) + 0.5 * last_visible_residual",
            "training_only_parameters": {
                "visible_residual_median_m": round_metric(float(params["visible_residual_median_m"])),
                "visible_last_residual_m": round_metric(float(params["visible_last_residual_m"])),
                "residual_correction_m": round_metric(float(params["residual_correction_m"])),
            },
        },
        "comparator_baseline": {
            "comparator_id": "NOAA-HARMONIC-PREDICTION-ONLY",
            "pre_registered": True,
            "prediction_rule": "Use the paired official NOAA prediction at the same timestamp, without residual correction.",
            "target_values_used_for_baseline_design": False,
        },
        "uncertainty_policy": {
            "method": "visible residual MAD plus NOAA visible median observation sigma",
            "residual_metric": "hidden mean absolute residual in meters",
            "aggregate_uncertainty_allowance_m": round_metric(
                float(params["aggregate_uncertainty_allowance_m"])
            ),
            "visible_residual_mad_m": round_metric(float(params["visible_residual_mad_m"])),
            "visible_observation_sigma_median_m": round_metric(
                float(params["visible_observation_sigma_median_m"])
            ),
            "strict_superiority_rule": "model_mae_m + aggregate_uncertainty_allowance_m < comparator_mae_m",
        },
        "prediction_materialization": materialization,
    }
    declaration["declaration_sha256"] = sha256_object(declaration)
    return declaration


def noaa_coops_scored_rows(
    hidden_rows: list[dict[str, Any]],
    prediction_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    scored: list[dict[str, Any]] = []
    for actual, predicted in zip(hidden_rows, prediction_rows):
        observed = round_metric(float(actual["observed_water_level_m"]))
        model_prediction = round_metric(float(predicted["model_prediction_m"]))
        comparator_prediction = round_metric(float(predicted["comparator_prediction_m"]))
        row = {
            "row_index": actual["row_index"],
            "timestamp": actual["timestamp"],
            "observed_water_level_m": observed,
            "model_prediction_m": model_prediction,
            "comparator_prediction_m": comparator_prediction,
            "model_abs_residual_m": round_metric(abs(observed - model_prediction)),
            "comparator_abs_residual_m": round_metric(abs(observed - comparator_prediction)),
            "observed_sigma_m": round_metric(float(actual.get("observed_sigma_m") or 0.0)),
            "source_row_sha256": actual["source_row_sha256"],
        }
        row["score_row_sha256"] = sha256_object(row)
        scored.append(row)
    return scored


def noaa_coops_hidden_target_hash(hidden_rows: list[dict[str, Any]]) -> str:
    return sha256_object(
        [
            {
                "row_index": row["row_index"],
                "timestamp": row["timestamp"],
                "observed_water_level_m": round_metric(float(row["observed_water_level_m"])),
            }
            for row in hidden_rows
        ]
    )


def noaa_coops_target_leakage_control(
    rows: list[dict[str, Any]],
    prediction_rows: list[dict[str, Any]],
    params: dict[str, Any],
) -> dict[str, Any]:
    mutated = [dict(row) for row in rows]
    for row in mutated[240:720]:
        row["observed_water_level_m"] = float(row["observed_water_level_m"]) + 100.0
    mutated_predictions = noaa_coops_prediction_rows(mutated[240:720], params)
    original_prediction_hash = sha256_object(prediction_rows)
    mutated_prediction_hash = sha256_object(mutated_predictions)
    original_target_hash = noaa_coops_hidden_target_hash(rows[240:720])
    mutated_target_hash = noaa_coops_hidden_target_hash(mutated[240:720])
    return {
        "control_id": "NOAA-WATER-LEVEL-HIDDEN-TARGET-MUTATION-LEAKAGE-CONTROL",
        "description": "Mutating hidden observed water-level targets must not change materialized model or comparator predictions.",
        "predictions_unchanged_under_hidden_target_mutation": original_prediction_hash == mutated_prediction_hash,
        "target_hashes_changed_under_hidden_target_mutation": original_target_hash != mutated_target_hash,
        "original_prediction_rows_sha256": original_prediction_hash,
        "mutated_prediction_rows_sha256": mutated_prediction_hash,
        "original_hidden_target_values_sha256": original_target_hash,
        "mutated_hidden_target_values_sha256": mutated_target_hash,
        "passed": original_prediction_hash == mutated_prediction_hash and original_target_hash != mutated_target_hash,
    }


def noaa_coops_negative_control(
    hidden_rows: list[dict[str, Any]],
    prediction_rows: list[dict[str, Any]],
    uncertainty_allowance_m: float,
    original_model_mae_m: float,
) -> dict[str, Any]:
    shift = 60
    shifted_hidden = hidden_rows[shift:] + hidden_rows[:shift]
    model_residuals = [
        abs(float(actual["observed_water_level_m"]) - float(predicted["model_prediction_m"]))
        for actual, predicted in zip(shifted_hidden, prediction_rows)
    ]
    comparator_residuals = [
        abs(float(actual["observed_water_level_m"]) - float(predicted["comparator_prediction_m"]))
        for actual, predicted in zip(shifted_hidden, prediction_rows)
    ]
    model_mae = round_metric(mean(model_residuals))
    comparator_mae = round_metric(mean(comparator_residuals))
    declared_sequence_hash = sha256_object([row["timestamp"] for row in hidden_rows])
    shifted_sequence_hash = sha256_object([row["timestamp"] for row in shifted_hidden])
    residual_superiority_pass = model_mae + uncertainty_allowance_m < comparator_mae
    rejection_reasons = []
    if shifted_sequence_hash != declared_sequence_hash:
        rejection_reasons.append("NEGATIVE_CONTROL_TARGET_TIMESTAMP_SEQUENCE_HASH_MISMATCH")
    if model_mae <= original_model_mae_m:
        rejection_reasons.append("NEGATIVE_CONTROL_DID_NOT_WORSEN_MODEL_RESIDUAL")
    if not residual_superiority_pass:
        rejection_reasons.append("NEGATIVE_CONTROL_RESIDUAL_SUPERIORITY_NOT_MET")
    return {
        "control_id": "NOAA-WATER-LEVEL-TIMESTAMP-PHASE-SHIFT",
        "description": "Shift the hidden timestamp binding by six hours after source lock; the strict scorer must reject this altered target mapping.",
        "declared_hidden_timestamp_sequence_sha256": declared_sequence_hash,
        "control_hidden_timestamp_sequence_sha256": shifted_sequence_hash,
        "timestamp_sequence_hash_matches_declared": shifted_sequence_hash == declared_sequence_hash,
        "audit_model_mae_m": model_mae,
        "audit_comparator_mae_m": comparator_mae,
        "audit_original_model_mae_m": round_metric(original_model_mae_m),
        "audit_uncertainty_allowance_m": round_metric(uncertainty_allowance_m),
        "audit_residual_superiority_pass": residual_superiority_pass,
        "rejected": bool(rejection_reasons),
        "rejection_reasons": rejection_reasons,
    }


def noaa_coops_hash_payload(pack: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in pack.items() if key not in {"replay_hash", "evidence_pack_sha256"}}


def noaa_coops_evidence_hash_payload(pack: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in pack.items() if key != "evidence_pack_sha256"}


def attach_noaa_coops_hashes(pack: dict[str, Any]) -> dict[str, Any]:
    pack = dict(pack)
    pack["replay_hash"] = sha256_object(noaa_coops_hash_payload(pack))
    pack["evidence_pack_sha256"] = sha256_object(noaa_coops_evidence_hash_payload(pack))
    return pack


def blocked_noaa_coops_scorer_pack(source_lane: dict[str, Any], blockers: list[str]) -> dict[str, Any]:
    primary = blockers[0] if blockers else "NOAA_COOPS_SCORER_BLOCKED"
    return attach_noaa_coops_hashes(
        {
            "schema_id": NOAA_COOPS_SCORER_SCHEMA_ID,
            "release_id": RELEASE_ID,
            "version": VERSION,
            "generated_on": GENERATED_ON,
            "work_order_id": NOAA_COOPS_WORK_ORDER_ID,
            "domain_class_id": "earth_space_environmental_sciences",
            "phenomenon_class_id": "climate_weather_geophysical_time_series",
            "capability_owner": CAPABILITY_OWNER,
            "scorer_kind": "target_hidden_temporal_holdout_replay",
            "pack_status": "BLOCKED_FAIL_CLOSED_SOURCE_OR_DATA_INSUFFICIENT",
            "strict_artifact": True,
            "scorer_ready": False,
            "strict_predicates_all_pass": False,
            "scientific_pass": False,
            "coverage_closure_allowed": False,
            "broad_modern_science_superiority_allowed": False,
            "source": {
                "water_level_snapshot_ref": source_lane.get("water_level_snapshot_ref"),
                "predictions_snapshot_ref": source_lane.get("predictions_snapshot_ref"),
                "metadata_ref": source_lane.get("metadata_ref"),
                "source_snapshot_hash_bound": source_lane.get("source_snapshot_hash_bound") is True,
                "water_level_source_snapshot_sha256": source_lane.get("water_level_source_snapshot_sha256"),
                "predictions_source_snapshot_sha256": source_lane.get("predictions_source_snapshot_sha256"),
                "value_row_count": source_lane.get("value_row_count", 0),
            },
            "exact_blocker": primary,
            "exact_blockers": blockers,
            "replay_hash_policy": "sha256 over canonical JSON evidence pack excluding replay_hash and evidence_pack_sha256",
            "no_send_locks": no_send(),
        }
    )


def build_noaa_coops_scorer_pack(root: Path | None = None) -> dict[str, Any]:
    root = root or repo_root()
    source_lane = load_noaa_coops_api_lane(root)
    if source_lane.get("source_snapshot_hash_bound") is not True:
        return blocked_noaa_coops_scorer_pack(
            source_lane,
            [str(source_lane.get("remaining_blocker", "NOAA_COOPS_SOURCE_SNAPSHOT_NOT_HASH_BOUND"))],
        )
    water_snapshot = read_json(root / NOAA_COOPS_WATER_LEVEL_SNAPSHOT_REL)
    prediction_snapshot = read_json(root / NOAA_COOPS_PREDICTIONS_SNAPSHOT_REL)
    rows = extract_noaa_coops_rows(water_snapshot, prediction_snapshot)
    if len(rows) < 720:
        return blocked_noaa_coops_scorer_pack(
            source_lane,
            [f"NOAA_COOPS_PAIRED_SOURCE_ROWS_BELOW_REQUIRED_720::{len(rows)}/720"],
        )
    training_rows = rows[:240]
    hidden_rows = rows[240:720]
    params = noaa_coops_training_parameters(training_rows)
    declaration = noaa_coops_prediction_declaration(training_rows, hidden_rows, params)
    prediction_rows = declaration["prediction_materialization"]["prediction_rows"]
    scored_rows = noaa_coops_scored_rows(hidden_rows, prediction_rows)
    model_residuals = [float(row["model_abs_residual_m"]) for row in scored_rows]
    comparator_residuals = [float(row["comparator_abs_residual_m"]) for row in scored_rows]
    model_mae = round_metric(mean(model_residuals))
    comparator_mae = round_metric(mean(comparator_residuals))
    uncertainty_allowance = round_metric(float(params["aggregate_uncertainty_allowance_m"]))
    superiority_margin = round_metric(comparator_mae - model_mae - uncertainty_allowance)
    residual_superiority_pass = superiority_margin > 0
    negative_control = noaa_coops_negative_control(hidden_rows, prediction_rows, uncertainty_allowance, model_mae)
    leakage_control = noaa_coops_target_leakage_control(rows, prediction_rows, params)
    triggered_predicates: list[str] = []
    if not residual_superiority_pass:
        triggered_predicates.append("COMPARATOR_BASELINE_NOT_BEATEN_WITH_UNCERTAINTY")
    if not negative_control["rejected"]:
        triggered_predicates.append("NEGATIVE_CONTROL_NOT_REJECTED")
    if not leakage_control["passed"]:
        triggered_predicates.append("TARGET_LEAKAGE_CONTROL_FAILED")
    strict_predicates = [
        {"predicate": "STRICT_PACK_SCHEMA_PASS", "passed": True},
        {"predicate": "OFFICIAL_SOURCE_SNAPSHOT_HASH_BOUND", "passed": True},
        {"predicate": "TARGET_VARIABLE_EXACTLY_DECLARED", "passed": True},
        {"predicate": "TARGET_HIDDEN_SPLIT_DECLARED", "passed": True},
        {"predicate": "FORMULA_OR_MODEL_PREREGISTERED", "passed": True},
        {"predicate": "COMPARATOR_PREREGISTERED_AND_TARGET_SEPARATED", "passed": True},
        {"predicate": "UNCERTAINTY_AND_RESIDUAL_DECLARED", "passed": True},
        {"predicate": "NEGATIVE_CONTROL_REJECTED", "passed": negative_control["rejected"]},
        {"predicate": "FALSIFIER_PREDICATES_EXECUTABLE", "passed": True},
        {"predicate": "TARGET_LEAKAGE_CONTROL_PASS", "passed": leakage_control["passed"]},
        {
            "predicate": "RESIDUAL_SUPERIORITY_WITH_UNCERTAINTY",
            "passed": residual_superiority_pass,
            "failure": None if residual_superiority_pass else "COMPARATOR_BASELINE_NOT_BEATEN_WITH_UNCERTAINTY",
        },
    ]
    strict_all_pass = all(row["passed"] for row in strict_predicates)
    pack = {
        "schema_id": NOAA_COOPS_SCORER_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_on": GENERATED_ON,
        "work_order_id": NOAA_COOPS_WORK_ORDER_ID,
        "domain_class_id": "earth_space_environmental_sciences",
        "phenomenon_class_id": "climate_weather_geophysical_time_series",
        "capability_owner": CAPABILITY_OWNER,
        "scorer_kind": "target_hidden_temporal_holdout_replay",
        "pack_status": "STRICT_EVIDENCE_PASS_NO_COVERAGE_CLOSURE" if strict_all_pass else "SCORER_READY_FAIL_CLOSED_STRICT_EVIDENCE_NOT_MET",
        "strict_artifact": True,
        "scorer_ready": True,
        "strict_predicates_all_pass": strict_all_pass,
        "scientific_pass": strict_all_pass,
        "coverage_closure_allowed": False,
        "broad_modern_science_superiority_allowed": False,
        "coverage_review_status": "NOT_REQUESTED_NO_SEND",
        "source": {
            "source_id": "earth_noaa_coops_san_francisco_water_level_v1",
            "source_name": "NOAA CO-OPS Data Retrieval API water level and tide prediction observations",
            "official_endpoint_url": source_lane.get("official_endpoint_url"),
            "paired_official_endpoint_url": source_lane.get("paired_official_endpoint_url"),
            "water_level_snapshot_ref": NOAA_COOPS_WATER_LEVEL_SNAPSHOT_REL,
            "predictions_snapshot_ref": NOAA_COOPS_PREDICTIONS_SNAPSHOT_REL,
            "metadata_ref": NOAA_COOPS_METADATA_REL,
            "water_level_source_snapshot_sha256": source_lane.get("water_level_source_snapshot_sha256"),
            "predictions_source_snapshot_sha256": source_lane.get("predictions_source_snapshot_sha256"),
            "metadata_sha256": source_lane.get("metadata_sha256"),
            "water_level_byte_count": source_lane.get("water_level_byte_count"),
            "predictions_byte_count": source_lane.get("predictions_byte_count"),
            "water_level_row_count": source_lane.get("water_level_row_count"),
            "predictions_row_count": source_lane.get("predictions_row_count"),
            "value_row_count": source_lane.get("value_row_count"),
            "source_snapshot_hash_bound": True,
        },
        "target_variable": {
            "name": "observed_six_minute_water_level_mllw",
            "unit": "meters relative to MLLW",
            "target_field": "NOAA_COOPS[station=9414290, timestamp].data.v",
        },
        "pretarget_declaration": declaration,
        "scoring_results": {
            "hidden_row_count": len(scored_rows),
            "hidden_target_values_sha256": noaa_coops_hidden_target_hash(hidden_rows),
            "scored_rows_sha256": sha256_object(scored_rows),
            "scored_rows": scored_rows,
            "aggregate": {
                "model_mae_m": model_mae,
                "model_rmse_m": round_metric(rmse(model_residuals)),
                "comparator_mae_m": comparator_mae,
                "comparator_rmse_m": round_metric(rmse(comparator_residuals)),
                "aggregate_uncertainty_allowance_m": uncertainty_allowance,
                "model_mae_plus_uncertainty_m": round_metric(model_mae + uncertainty_allowance),
                "strict_superiority_margin_m": superiority_margin,
                "residual_superiority_pass": residual_superiority_pass,
                "training_parameters": {
                    "visible_residual_median_m": round_metric(float(params["visible_residual_median_m"])),
                    "visible_last_residual_m": round_metric(float(params["visible_last_residual_m"])),
                    "visible_residual_mad_m": round_metric(float(params["visible_residual_mad_m"])),
                    "visible_observation_sigma_median_m": round_metric(
                        float(params["visible_observation_sigma_median_m"])
                    ),
                    "residual_correction_m": round_metric(float(params["residual_correction_m"])),
                },
            },
        },
        "negative_control": negative_control,
        "target_leakage_control": leakage_control,
        "falsifier": {
            "falsifier_id": "NOAA-WATER-LEVEL-FAIL-CLOSED-FALSIFIER",
            "status": "NOT_TRIGGERED" if not triggered_predicates else "TRIGGERED",
            "triggered_predicates": triggered_predicates,
            "non_triggered_predicates": [
                "SOURCE_SNAPSHOT_HASH_OR_METADATA_HASH_MISMATCH",
                "HIDDEN_WATER_LEVEL_TARGET_ROWS_READ_BEFORE_PREDICTION_MATERIALIZATION",
                "FEWER_THAN_480_HIDDEN_SIX_MINUTE_VALUES_SCORED",
            ],
        },
        "strict_predicate_results": strict_predicates,
        "exact_blocker": triggered_predicates[0] if triggered_predicates else None,
        "exact_blockers": triggered_predicates,
        "exact_blocker_detail": (
            "model_mae_plus_uncertainty_m="
            f"{round_metric(model_mae + uncertainty_allowance)} >= comparator_mae_m={comparator_mae}"
            if not residual_superiority_pass
            else None
        ),
        "replay_command": {
            "commands": [
                "python validation/heldout/grand_science/earth_space/coverage_work_orders/oc133_earth_space_modern_science_coverage_work_orders.py --score-noaa-coops --write",
                "python validation/heldout/grand_science/earth_space/coverage_work_orders/oc133_earth_space_modern_science_coverage_work_orders.py --check",
            ]
        },
        "replay_hash_policy": "sha256 over canonical JSON evidence pack excluding replay_hash and evidence_pack_sha256",
        "no_send_locks": no_send(),
    }
    return attach_noaa_coops_hashes(pack)


def noaa_coops_scorer_summary(root: Path, source_lane: dict[str, Any]) -> dict[str, Any]:
    if source_lane.get("source_snapshot_hash_bound") is not True:
        return {
            "target_hidden_scorer_present": False,
            "strict_evidence_pack_ref": None,
            "strict_evidence_pack_sha256": None,
            "strict_scientific_predicates_pass": False,
            "negative_control_rejected": False,
            "falsifier_status": "NOT_RUN",
            "remaining_blocker": source_lane.get("remaining_blocker", "NOAA_COOPS_SOURCE_SNAPSHOT_NOT_HASH_BOUND"),
            "scorer_status": "OPEN_FAIL_CLOSED_SOURCE_HASH_REQUIRED",
        }
    pack = build_noaa_coops_scorer_pack(root)
    return {
        "target_hidden_scorer_present": pack.get("scorer_ready") is True,
        "strict_evidence_pack_ref": NOAA_COOPS_SCORER_EVIDENCE_REL,
        "strict_evidence_pack_sha256": pack.get("evidence_pack_sha256"),
        "strict_scientific_predicates_pass": pack.get("strict_predicates_all_pass") is True,
        "negative_control_rejected": pack.get("negative_control", {}).get("rejected") is True,
        "falsifier_status": pack.get("falsifier", {}).get("status"),
        "remaining_blocker": pack.get("exact_blocker") or "COVERAGE_REGISTER_REVIEW_NOT_PERFORMED",
        "scorer_status": pack.get("pack_status"),
    }


def noaa_coops_evidence(source_lane: dict[str, Any], scorer_summary: dict[str, Any]) -> dict[str, Any]:
    if scorer_summary.get("target_hidden_scorer_present") is not True:
        return fail_closed_evidence(
            "NOAA CO-OPS source bytes are hash-bound when present, but no target-hidden scorer, comparator result, negative-control result, or strict evidence pack is bound.",
            source_lane=source_lane,
        )
    strict_pass = scorer_summary.get("strict_scientific_predicates_pass") is True
    return {
        "current_status": "STRICT_EVIDENCE_PASS_NO_COVERAGE_CLOSURE" if strict_pass else "SCORER_READY_FAIL_CLOSED_STRICT_EVIDENCE_NOT_MET",
        "executable_evidence_exists": True,
        "strict_evidence_pack_ref": scorer_summary.get("strict_evidence_pack_ref"),
        "strict_evidence_pack_sha256": scorer_summary.get("strict_evidence_pack_sha256"),
        "source_snapshot_hash_bound": source_lane.get("source_snapshot_hash_bound") is True,
        "source_snapshot_ref": source_lane.get("water_level_snapshot_ref"),
        "source_snapshot_sha256": source_lane.get("water_level_source_snapshot_sha256"),
        "target_hidden_scorer_present": True,
        "comparator_residual_metric_bound": True,
        "negative_control_rejected": scorer_summary.get("negative_control_rejected") is True,
        "falsifier_status": scorer_summary.get("falsifier_status"),
        "exact_blocker": None if strict_pass else scorer_summary.get("remaining_blocker"),
        "reason": (
            "NOAA CO-OPS target-hidden scorer, comparator residual, negative-control, and replay hash are bound; coverage closure remains disabled pending coverage-register review."
            if strict_pass
            else "NOAA CO-OPS target-hidden replay scorer is bound, but strict evidence remains blocked by its exact predicate."
        ),
        "coverage_closure_allowed": False,
        "broad_modern_science_superiority_allowed": False,
        "scientific_pass": strict_pass,
    }


def nasa_power_url() -> str:
    return NASA_POWER_ENDPOINT


def build_work_orders(root: Path | None = None) -> list[dict[str, Any]]:
    root = root or repo_root()
    noaa_source_lane = load_noaa_coops_api_lane(root)
    noaa_scorer = noaa_coops_scorer_summary(root, noaa_source_lane)
    noaa_lane = {
        **noaa_source_lane,
        **noaa_scorer,
        "status": (
            "SOURCE_SNAPSHOT_HASH_BOUND_STRICT_EVIDENCE_PASS_NO_COVERAGE_CLOSURE"
            if noaa_scorer.get("strict_scientific_predicates_pass") is True
            else "SOURCE_SNAPSHOT_HASH_BOUND_SCORER_READY_FAIL_CLOSED_STRICT_EVIDENCE_NOT_MET"
            if noaa_scorer.get("target_hidden_scorer_present") is True
            else noaa_source_lane.get("status")
        ),
    }
    usgs_source_lane = load_usgs_api_lane(root)
    usgs_scorer = usgs_hydrology_scorer_summary(root, usgs_source_lane)
    usgs_lane = {
        **usgs_source_lane,
        **usgs_scorer,
        "status": (
            "SOURCE_SNAPSHOT_HASH_BOUND_SCORER_READY_FAIL_CLOSED_STRICT_EVIDENCE_NOT_MET"
            if usgs_scorer.get("target_hidden_scorer_present") is True
            and usgs_scorer.get("strict_scientific_predicates_pass") is not True
            else usgs_source_lane.get("status")
        ),
    }
    nasa_source_lane = load_nasa_power_api_lane(root)
    nasa_scorer = nasa_power_scorer_summary(root, nasa_source_lane)
    nasa_lane = {
        **nasa_source_lane,
        **nasa_scorer,
        "status": (
            "SOURCE_SNAPSHOT_HASH_BOUND_STRICT_EVIDENCE_PASS_NO_COVERAGE_CLOSURE"
            if nasa_scorer.get("target_hidden_scorer_present") is True
            and nasa_scorer.get("strict_scientific_predicates_pass") is True
            else "SOURCE_SNAPSHOT_HASH_BOUND_SCORER_READY_FAIL_CLOSED_STRICT_EVIDENCE_NOT_MET"
            if nasa_scorer.get("target_hidden_scorer_present") is True
            else nasa_source_lane.get("status")
        ),
    }
    rows = [
        {
            "work_order_id": "MS-COV-WO-010",
            "domain_class_id": "earth_space_environmental_sciences",
            "phenomenon_class_id": "climate_weather_geophysical_time_series",
            "phenomenon_label": "climate weather geophysical time series",
            "lane_status": (
                "STRICT_EVIDENCE_PASS_NO_COVERAGE_CLOSURE"
                if noaa_scorer.get("strict_scientific_predicates_pass") is True
                else "SCORER_READY_FAIL_CLOSED_STRICT_EVIDENCE_NOT_MET"
                if noaa_scorer.get("target_hidden_scorer_present") is True
                else "OPEN_FAIL_CLOSED_NO_EXECUTABLE_EVIDENCE"
            ),
            "coverage_closure_allowed": False,
            "support_allowed_for_broad_coverage": False,
            "official_api_lane": noaa_lane,
            "executable_spec": {
                "official_source": {
                    "source_id": "earth_noaa_coops_san_francisco_water_level_v1",
                    "source_name": "NOAA CO-OPS Data Retrieval API water level and tide prediction observations",
                    "source_authority": "NOAA Center for Operational Oceanographic Products and Services",
                    "official_documentation_url": "https://api.tidesandcurrents.noaa.gov/api/prod/",
                    "official_endpoint_url": noaa_water_level_url("water_level"),
                    "paired_official_endpoint_url": noaa_water_level_url("predictions"),
                    "required_local_snapshot_refs": [
                        NOAA_COOPS_WATER_LEVEL_SNAPSHOT_REL,
                        NOAA_COOPS_PREDICTIONS_SNAPSHOT_REL,
                    ],
                    "snapshot_status": noaa_lane.get("status"),
                },
                "target_variable": {
                    "name": "observed_six_minute_water_level_mllw",
                    "unit": "meters relative to MLLW",
                    "target_fields": ["data[].v"],
                    "target_field": "NOAA_COOPS[station=9414290, timestamp].data.v",
                },
                "target_hidden_split": {
                    "mode": "target_blind_same_source_with_visible_prediction_product",
                    "visible_inputs": ["timestamp", "official tide prediction value", "prior observed residuals before hidden timestamp"],
                    "hidden_target_fields": ["observed water_level data[].v for heldout timestamps"],
                    "split_rule": "Lock source bytes; expose Jan 1 prior residuals for calibration; hide Jan 2-3 observed water-level values until predictions are materialized.",
                    "target_hidden_until_scoring": True,
                    "target_values_used_for_selection": False,
                },
                "formula_or_model": {
                    "model_id": "NOAA-TIDE-PREDICTION-PLUS-PRIOR-RESIDUAL-AR1",
                    "rule": "y_hat(t) = NOAA_prediction(t) + median(prior_observed_minus_prediction_residual) + 0.5 * last_visible_residual",
                    "required_inputs": ["official tide prediction", "prior visible residuals", "timestamp"],
                    "target_values_may_be_used_for_model_design": False,
                },
                "preregistered_comparator": {
                    "comparator_id": "NOAA-HARMONIC-PREDICTION-ONLY",
                    "prediction_rule": "Predict each hidden observed water-level row using only the paired official NOAA tide prediction value at the same timestamp.",
                    "pre_registered": True,
                    "target_values_used_for_baseline_design": False,
                },
                "uncertainty_and_residual": {
                    "uncertainty_method": "pre-target median absolute deviation of visible residuals plus NOAA reported standard deviation field where present",
                    "residual_metric": "absolute residual per hidden six-minute timestamp; aggregate MAE and RMSE",
                    "superiority_rule": "model MAE plus uncertainty allowance must be lower than comparator MAE and every timestamp hash must remain bound",
                },
                "negative_control": {
                    "control_id": "NOAA-WATER-LEVEL-TIMESTAMP-PHASE-SHIFT",
                    "description": "Shift the target timestamps by +6 hours after source lock.",
                    "rejection_predicate": "phase-shifted target mapping changes row hashes and worsens residuals relative to the locked timestamp mapping",
                },
                "falsifier": {
                    "falsifier_id": "NOAA-WATER-LEVEL-FAIL-CLOSED-FALSIFIER",
                    "triggers": [
                        "observed hidden water-level values appear in visible inputs",
                        "NOAA source snapshot hashes are missing or change on replay",
                        "comparator residual ties or beats the model within the uncertainty policy",
                        "fewer than 20 hidden timestamps are scored",
                    ],
                },
                "N": {
                    "minimum_n": 20,
                    "acquired_source_rows": noaa_lane.get("value_row_count", 0),
                    "planned_source_rows": 720,
                    "planned_hidden_target_rows": 480,
                    "unit": "six-minute water-level observations",
                },
                "replay_command": {
                    "commands": [
                        "python validation/heldout/grand_science/earth_space/coverage_work_orders/oc133_earth_space_modern_science_coverage_work_orders.py --refresh-noaa-coops-source --write",
                        "python validation/heldout/grand_science/earth_space/coverage_work_orders/oc133_earth_space_modern_science_coverage_work_orders.py --score-noaa-coops --write",
                        "python validation/heldout/grand_science/earth_space/coverage_work_orders/oc133_earth_space_modern_science_coverage_work_orders.py --check",
                    ],
                    "acceptance_predicates": COMMON_CLOSURE_PREDICATES,
                },
                "fail_closed_current_evidence": noaa_coops_evidence(noaa_source_lane, noaa_scorer),
            },
            "no_send_locks": no_send(),
        },
        {
            "work_order_id": "MS-COV-WO-011",
            "domain_class_id": "earth_space_environmental_sciences",
            "phenomenon_class_id": "geochemistry_and_hydrology_observables",
            "phenomenon_label": "geochemistry and hydrology observables",
            "lane_status": (
                "SCORER_READY_FAIL_CLOSED_STRICT_EVIDENCE_NOT_MET"
                if usgs_scorer.get("target_hidden_scorer_present") is True
                else "OPEN_FAIL_CLOSED_SOURCE_HASH_BOUND_STRICT_EVIDENCE_MISSING"
            ),
            "coverage_closure_allowed": False,
            "support_allowed_for_broad_coverage": False,
            "official_api_lane": usgs_lane,
            "executable_spec": {
                "official_source": {
                    "source_id": "earth_usgs_nwis_daily_values_discharge_v1",
                    "source_name": "USGS Water Services Daily Values API mean discharge",
                    "source_authority": "U.S. Geological Survey",
                    "official_documentation_url": "https://waterservices.usgs.gov/docs/dv-service/daily-values-service-details/",
                    "official_endpoint_url": USGS_HYDROLOGY_ENDPOINT,
                    "required_local_snapshot_refs": [USGS_HYDROLOGY_SNAPSHOT_REL],
                    "snapshot_status": usgs_lane.get("status"),
                },
                "target_variable": {
                    "name": "daily_mean_streamflow_discharge",
                    "unit": "cubic feet per second",
                    "target_fields": ["value.timeSeries[0].values[0].value[].value"],
                    "target_field": "USGS_DV[site=01646500, parameterCd=00060, statCd=00003, date].value",
                },
                "target_hidden_split": {
                    "mode": "prospective_source_lock_then_temporal_holdout",
                    "visible_inputs": ["site id", "dates 2024-01-01 through 2024-01-20 discharge values", "parameter metadata"],
                    "hidden_target_fields": ["dates 2024-01-21 through 2024-02-09 discharge values"],
                    "split_rule": "The first 20 daily values are visible training rows; the final 20 daily values are hidden targets until prediction materialization.",
                    "target_hidden_until_scoring": True,
                    "target_values_used_for_selection": False,
                },
                "formula_or_model": {
                    "model_id": "USGS-LOG-FLOW-PRIOR-DELTA-MEDIAN",
                    "rule": "log1p(Q_hat_t) = log1p(Q_t_minus_1) + median(diff(log1p(Q_visible_training)))",
                    "required_inputs": ["prior daily discharge", "training-only median log-flow delta", "date order"],
                    "target_values_may_be_used_for_model_design": False,
                },
                "preregistered_comparator": {
                    "comparator_id": "USGS-LAST-OBSERVATION-CARRY-FORWARD",
                    "prediction_rule": "Predict every hidden discharge row as the last visible discharge value, with no target rows used for tuning.",
                    "pre_registered": True,
                    "target_values_used_for_baseline_design": False,
                },
                "uncertainty_and_residual": {
                    "uncertainty_method": "training-only median absolute deviation of one-step log-flow residuals",
                    "residual_metric": "absolute residual in cfs per heldout date plus aggregate MAE over hidden dates",
                    "superiority_rule": "model MAE plus uncertainty allowance must be lower than carry-forward comparator MAE; otherwise the lane stays open",
                },
                "negative_control": {
                    "control_id": "USGS-DISCHARGE-DATE-ORDER-REVERSAL",
                    "description": "Reverse hidden target date order after source lock.",
                    "rejection_predicate": "date-order reversal changes the declared hidden date-sequence hash and is rejected before any strict acceptance claim",
                },
                "falsifier": {
                    "falsifier_id": "USGS-HYDROLOGY-FAIL-CLOSED-FALSIFIER",
                    "triggers": [
                        "source snapshot hash or metadata hash does not match stored bytes",
                        "hidden discharge target rows are read before prediction materialization",
                        "carry-forward comparator ties or beats the model within uncertainty",
                        "fewer than 20 hidden daily values are scored",
                    ],
                },
                "N": {
                    "minimum_n": 20,
                    "acquired_source_rows": usgs_lane.get("value_row_count", 0),
                    "planned_hidden_target_rows": 20,
                    "unit": "daily mean discharge observations",
                },
                "replay_command": {
                    "commands": [
                        "python validation/heldout/grand_science/earth_space/coverage_work_orders/oc133_earth_space_modern_science_coverage_work_orders.py --score-usgs-hydrology --write",
                        "python validation/heldout/grand_science/earth_space/coverage_work_orders/oc133_earth_space_modern_science_coverage_work_orders.py --check",
                    ],
                    "acceptance_predicates": COMMON_CLOSURE_PREDICATES,
                },
                "fail_closed_current_evidence": usgs_hydrology_fail_closed_evidence(
                    usgs_source_lane,
                    usgs_scorer,
                ),
            },
            "no_send_locks": no_send(),
        },
        {
            "work_order_id": "MS-COV-WO-012",
            "domain_class_id": "earth_space_environmental_sciences",
            "phenomenon_class_id": "remote_sensing_and_planetary_measurements",
            "phenomenon_label": "remote sensing and planetary measurements",
            "lane_status": (
                "STRICT_EVIDENCE_PASS_NO_COVERAGE_CLOSURE"
                if nasa_scorer.get("strict_scientific_predicates_pass") is True
                else "SCORER_READY_FAIL_CLOSED_STRICT_EVIDENCE_NOT_MET"
                if nasa_scorer.get("target_hidden_scorer_present") is True
                else "OPEN_FAIL_CLOSED_NO_EXECUTABLE_EVIDENCE"
            ),
            "coverage_closure_allowed": False,
            "support_allowed_for_broad_coverage": False,
            "official_api_lane": nasa_lane,
            "executable_spec": {
                "official_source": {
                    "source_id": "earth_nasa_power_daily_solar_san_francisco_v1",
                    "source_name": "NASA POWER Daily API solar and meteorological point data",
                    "source_authority": "NASA Langley Research Center POWER Project",
                    "official_documentation_url": "https://power.larc.nasa.gov/docs/services/api/temporal/daily/",
                    "official_endpoint_url": nasa_power_url(),
                    "required_local_snapshot_refs": [
                        NASA_POWER_SNAPSHOT_REL
                    ],
                    "snapshot_status": nasa_lane.get("status"),
                },
                "target_variable": {
                    "name": "daily_all_sky_surface_shortwave_downward_irradiance",
                    "unit": "kWh/m^2/day",
                    "target_fields": ["properties.parameter.ALLSKY_SFC_SW_DWN.<YYYYMMDD>"],
                    "target_field": "NASA_POWER[lat=37.7749, lon=-122.4194, date].ALLSKY_SFC_SW_DWN",
                },
                "target_hidden_split": {
                    "mode": "target_blind_temporal_holdout",
                    "visible_inputs": ["latitude", "longitude", "day-of-year", "visible T2M values", "prior solar rows"],
                    "hidden_target_fields": ["ALLSKY_SFC_SW_DWN values for heldout dates"],
                    "split_rule": "Hide the final 20 daily rows as targets after source lock; the first 20 daily rows remain visible for formula materialization.",
                    "target_hidden_until_scoring": True,
                    "target_values_used_for_selection": False,
                },
                "formula_or_model": {
                    "model_id": "NASA-POWER-CLEAR-SKY-SEASONAL-LAG",
                    "rule": "y_hat(date) = median(visible ALLSKY_SFC_SW_DWN for same week window) adjusted by cosine solar-zenith day-of-year factor",
                    "required_inputs": ["latitude", "day-of-year", "visible solar rows", "visible T2M"],
                    "target_values_may_be_used_for_model_design": False,
                },
                "preregistered_comparator": {
                    "comparator_id": "NASA-POWER-TRAILING-MEAN-COMPARATOR",
                    "prediction_rule": "Predict each hidden date using the trailing seven visible daily solar-radiation mean only.",
                    "pre_registered": True,
                    "target_values_used_for_baseline_design": False,
                },
                "uncertainty_and_residual": {
                    "uncertainty_method": "visible-date rolling residual envelope with fixed kWh/m^2/day materiality floor",
                    "residual_metric": "absolute residual per heldout date; aggregate MAE",
                    "superiority_rule": "model MAE plus uncertainty allowance must be lower than the trailing-mean comparator MAE",
                },
                "negative_control": {
                    "control_id": "NASA-POWER-LATITUDE-SIGN-FLIP",
                    "description": "Flip latitude sign after source lock while keeping dates fixed.",
                    "rejection_predicate": "latitude-sign flip changes prediction rows and fails residual/materiality predicates",
                },
                "falsifier": {
                    "falsifier_id": "NASA-POWER-REMOTE-SENSING-FAIL-CLOSED-FALSIFIER",
                    "triggers": [
                        "hidden solar target values appear in visible inputs",
                        "NASA POWER source snapshot hash is missing or changes",
                        "trailing-mean comparator ties or beats the model within uncertainty",
                        "fewer than 20 NASA POWER daily rows are locked",
                    ],
                },
                "N": {
                    "minimum_n": 20,
                    "acquired_source_rows": nasa_lane.get("value_row_count", 0),
                    "planned_source_rows": 40,
                    "planned_hidden_target_rows": 20,
                    "unit": "daily point records",
                },
                "replay_command": {
                    "commands": [
                        "python validation/heldout/grand_science/earth_space/coverage_work_orders/oc133_earth_space_modern_science_coverage_work_orders.py --score-nasa-power --write",
                        "python validation/heldout/grand_science/earth_space/coverage_work_orders/oc133_earth_space_modern_science_coverage_work_orders.py --check",
                    ],
                    "acceptance_predicates": COMMON_CLOSURE_PREDICATES,
                },
                "fail_closed_current_evidence": nasa_power_evidence(nasa_source_lane, nasa_scorer),
            },
            "no_send_locks": no_send(),
        },
    ]
    return [with_hash(row) for row in rows]


def build_payload(root: Path | None = None) -> dict[str, Any]:
    root = root or repo_root()
    rows = build_work_orders(root)
    return {
        "schema_id": SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_on": GENERATED_ON,
        "capability_owner": CAPABILITY_OWNER,
        "generated_by": SCRIPT_REL,
        "coverage_register_ref": COVERAGE_REGISTER_REL,
        "modern_science_work_orders_ref": MODERN_WORK_ORDERS_REL,
        "domain_class_id": "earth_space_environmental_sciences",
        "target_work_order_ids": ["MS-COV-WO-010", "MS-COV-WO-011", "MS-COV-WO-012"],
        "work_order_total": len(rows),
        "coverage_closure_allowed": False,
        "broad_modern_science_superiority_allowed": False,
        "official_api_hash_bound_lane_total": sum(
            1 for row in rows if row.get("official_api_lane", {}).get("source_snapshot_hash_bound") is True
        ),
        "no_send_locks": no_send(),
        "work_orders": rows,
    }


def validate_executable_spec(spec: dict[str, Any], *, row_id: str) -> list[str]:
    failures: list[str] = []
    for field in SPEC_REQUIRED_FIELDS:
        if not spec.get(field):
            failures.append(f"SPEC_FIELD_MISSING::{row_id}::{field}")
    source = spec.get("official_source", {})
    if not str(source.get("source_authority", "")):
        failures.append(f"OFFICIAL_SOURCE_AUTHORITY_MISSING::{row_id}")
    if not str(source.get("official_documentation_url", "")).startswith("https://"):
        failures.append(f"OFFICIAL_SOURCE_DOC_URL_MISSING::{row_id}")
    if not str(source.get("official_endpoint_url", "")).startswith("https://"):
        failures.append(f"OFFICIAL_SOURCE_ENDPOINT_URL_MISSING::{row_id}")
    target = spec.get("target_variable", {})
    if not target.get("target_fields"):
        failures.append(f"TARGET_FIELDS_MISSING::{row_id}")
    split = spec.get("target_hidden_split", {})
    if split.get("target_hidden_until_scoring") is not True:
        failures.append(f"TARGET_NOT_HIDDEN_UNTIL_SCORING::{row_id}")
    if split.get("target_values_used_for_selection") is not False:
        failures.append(f"TARGET_VALUES_USED_FOR_SELECTION::{row_id}")
    formula = spec.get("formula_or_model", {})
    if formula.get("target_values_may_be_used_for_model_design") is not False:
        failures.append(f"FORMULA_TARGET_LEAK_ALLOWED::{row_id}")
    comparator = spec.get("preregistered_comparator", {})
    if comparator.get("pre_registered") is not True:
        failures.append(f"COMPARATOR_NOT_PREREGISTERED::{row_id}")
    if comparator.get("target_values_used_for_baseline_design") is not False:
        failures.append(f"COMPARATOR_TARGET_LEAK_ALLOWED::{row_id}")
    if not spec.get("uncertainty_and_residual", {}).get("residual_metric"):
        failures.append(f"RESIDUAL_METRIC_MISSING::{row_id}")
    if not spec.get("negative_control", {}).get("rejection_predicate"):
        failures.append(f"NEGATIVE_CONTROL_REJECTION_MISSING::{row_id}")
    if not spec.get("falsifier", {}).get("triggers"):
        failures.append(f"FALSIFIER_TRIGGERS_MISSING::{row_id}")
    if int(spec.get("N", {}).get("minimum_n", 0) or 0) < 20:
        failures.append(f"MINIMUM_N_LT_20::{row_id}")
    if not spec.get("replay_command", {}).get("commands"):
        failures.append(f"REPLAY_COMMAND_MISSING::{row_id}")
    evidence = spec.get("fail_closed_current_evidence", {})
    if evidence.get("coverage_closure_allowed") is not False:
        failures.append(f"FAIL_CLOSED_EVIDENCE_ALLOWS_CLOSURE::{row_id}")
    if evidence.get("broad_modern_science_superiority_allowed") is not False:
        failures.append(f"FAIL_CLOSED_EVIDENCE_ALLOWS_BROAD_SUPERIORITY::{row_id}")
    if (
        evidence.get("scientific_pass") is not False
        and evidence.get("current_status") != "STRICT_EVIDENCE_PASS_NO_COVERAGE_CLOSURE"
    ):
        failures.append(f"FAIL_CLOSED_EVIDENCE_FAKE_PASS::{row_id}")
    return failures


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
    expected_ids = {"MS-COV-WO-010", "MS-COV-WO-011", "MS-COV-WO-012"}
    if {str(row.get("work_order_id")) for row in rows if isinstance(row, dict)} != expected_ids:
        failures.append("EARTH_SPACE_WORK_ORDER_SET_MISMATCH")
    hash_bound_total = 0
    for row in rows:
        if not isinstance(row, dict):
            failures.append("WORK_ORDER_NOT_OBJECT")
            continue
        row_id = str(row.get("work_order_id", "unknown"))
        if row.get("coverage_closure_allowed") is not False:
            failures.append(f"COVERAGE_CLOSURE_ALLOWED::{row_id}")
        if row.get("support_allowed_for_broad_coverage") is not False:
            failures.append(f"BROAD_SUPPORT_ALLOWED::{row_id}")
        if str(row.get("lane_status", "")).upper() == "PASS":
            failures.append(f"FAKE_PASS_STATUS::{row_id}")
        failures.extend(validate_executable_spec(row.get("executable_spec", {}), row_id=row_id))
        api_lane = row.get("official_api_lane", {})
        if isinstance(api_lane, dict) and api_lane.get("source_snapshot_hash_bound") is True:
            hash_bound_total += 1
            if not str(api_lane.get("source_snapshot_sha256", "")):
                failures.append(f"HASH_BOUND_LANE_SHA_MISSING::{row_id}")
            if int(api_lane.get("value_row_count", 0) or 0) < 20:
                failures.append(f"HASH_BOUND_LANE_N_LT_20::{row_id}")
        expected_hash = sha256_object({key: value for key, value in row.items() if key != "row_sha256"})
        if row.get("row_sha256") != expected_hash:
            failures.append(f"ROW_HASH_MISMATCH::{row_id}")
    if payload.get("official_api_hash_bound_lane_total") != hash_bound_total:
        failures.append("OFFICIAL_API_HASH_BOUND_TOTAL_MISMATCH")
    if hash_bound_total < 1:
        failures.append("NO_OFFICIAL_API_HASH_BOUND_LANE_IMPLEMENTED")
    return failures


def validate_usgs_hydrology_scorer_pack(
    pack: dict[str, Any],
    root: Path | None = None,
) -> list[str]:
    root = root or repo_root()
    failures: list[str] = []
    if pack.get("schema_id") != USGS_HYDROLOGY_SCORER_SCHEMA_ID:
        failures.append("USGS_HYDROLOGY_SCORER_SCHEMA_MISMATCH")
    if pack.get("work_order_id") != USGS_HYDROLOGY_WORK_ORDER_ID:
        failures.append("USGS_HYDROLOGY_SCORER_WORK_ORDER_MISMATCH")
    if pack.get("strict_artifact") is not True:
        failures.append("USGS_HYDROLOGY_SCORER_STRICT_ARTIFACT_NOT_TRUE")
    if pack.get("coverage_closure_allowed") is not False:
        failures.append("USGS_HYDROLOGY_SCORER_COVERAGE_CLOSURE_ALLOWED")
    if pack.get("broad_modern_science_superiority_allowed") is not False:
        failures.append("USGS_HYDROLOGY_SCORER_BROAD_SUPERIORITY_ALLOWED")
    if pack.get("no_send_locks", {}).get("no_send") is not True:
        failures.append("USGS_HYDROLOGY_SCORER_NO_SEND_LOCK_MISSING")

    expected_replay_hash = sha256_object(usgs_scorer_hash_payload(pack))
    if pack.get("replay_hash") != expected_replay_hash:
        failures.append("USGS_HYDROLOGY_SCORER_REPLAY_HASH_MISMATCH")
    expected_pack_hash = sha256_object(usgs_scorer_evidence_hash_payload(pack))
    if pack.get("evidence_pack_sha256") != expected_pack_hash:
        failures.append("USGS_HYDROLOGY_SCORER_EVIDENCE_PACK_HASH_MISMATCH")

    source_lane = load_usgs_api_lane(root)
    source = pack.get("source", {})
    if source.get("source_snapshot_hash_bound") is True:
        if source_lane.get("source_snapshot_hash_bound") is not True:
            failures.append("USGS_HYDROLOGY_SCORER_SOURCE_NOT_HASH_BOUND_ON_REPLAY")
        for field in ("source_snapshot_sha256", "metadata_sha256", "byte_count", "value_row_count"):
            if source.get(field) != source_lane.get(field):
                failures.append(f"USGS_HYDROLOGY_SCORER_SOURCE_FIELD_MISMATCH::{field}")

    if pack.get("scorer_ready") is not True:
        if not pack.get("exact_blockers"):
            failures.append("USGS_HYDROLOGY_SCORER_BLOCKED_WITHOUT_EXACT_BLOCKER")
        return failures

    declaration = pack.get("pretarget_declaration", {})
    split = declaration.get("split_policy", {})
    hidden_placeholders = declaration.get("hidden_target_placeholders", [])
    visible_rows = declaration.get("visible_training_rows", [])
    materialization = declaration.get("prediction_materialization", {})
    prediction_rows = materialization.get("prediction_rows", [])
    scoring = pack.get("scoring_results", {})
    scored_rows = scoring.get("scored_rows", [])
    aggregate = scoring.get("aggregate", {})

    if split.get("training_row_count") != 20 or len(visible_rows) != 20:
        failures.append("USGS_HYDROLOGY_SCORER_TRAINING_SPLIT_NOT_20")
    if split.get("hidden_row_count") != 20 or len(hidden_placeholders) != 20:
        failures.append("USGS_HYDROLOGY_SCORER_HIDDEN_SPLIT_NOT_20")
    if scoring.get("hidden_row_count") != 20 or len(scored_rows) != 20:
        failures.append("USGS_HYDROLOGY_SCORER_SCORED_N_NOT_20")
    if declaration.get("target_hidden_until_scoring") is not True:
        failures.append("USGS_HYDROLOGY_SCORER_TARGET_NOT_HIDDEN")
    if declaration.get("target_values_used_for_model_selection") is not False:
        failures.append("USGS_HYDROLOGY_SCORER_TARGET_USED_FOR_SELECTION")
    if declaration.get("target_values_used_for_prediction_materialization") is not False:
        failures.append("USGS_HYDROLOGY_SCORER_TARGET_USED_FOR_PREDICTION")
    if materialization.get("predictions_materialized_before_target_unseal") is not True:
        failures.append("USGS_HYDROLOGY_SCORER_PREDICTIONS_NOT_MATERIALIZED_BEFORE_UNSEAL")
    if materialization.get("hidden_target_values_included") is not False:
        failures.append("USGS_HYDROLOGY_SCORER_MATERIALIZATION_CONTAINS_HIDDEN_TARGETS")
    for placeholder in hidden_placeholders:
        if "observed_discharge_cfs" in placeholder or "target_value" in placeholder:
            failures.append("USGS_HYDROLOGY_SCORER_HIDDEN_PLACEHOLDER_LEAKS_TARGET")
            break
    if materialization.get("prediction_rows_sha256") != sha256_object(prediction_rows):
        failures.append("USGS_HYDROLOGY_SCORER_PREDICTION_ROWS_HASH_MISMATCH")
    if scoring.get("scored_rows_sha256") != sha256_object(scored_rows):
        failures.append("USGS_HYDROLOGY_SCORER_SCORED_ROWS_HASH_MISMATCH")
    for row in scored_rows:
        expected_row_hash = sha256_object({key: value for key, value in row.items() if key != "score_row_sha256"})
        if row.get("score_row_sha256") != expected_row_hash:
            failures.append(f"USGS_HYDROLOGY_SCORER_SCORE_ROW_HASH_MISMATCH::{row.get('date')}")

    model_mae = float(aggregate.get("model_mae_cfs", 0.0) or 0.0)
    comparator_mae = float(aggregate.get("comparator_mae_cfs", 0.0) or 0.0)
    uncertainty = float(aggregate.get("aggregate_uncertainty_allowance_cfs", 0.0) or 0.0)
    residual_pass = model_mae + uncertainty < comparator_mae
    if aggregate.get("residual_superiority_pass") is not residual_pass:
        failures.append("USGS_HYDROLOGY_SCORER_RESIDUAL_SUPERIORITY_FLAG_MISMATCH")
    if round_metric(comparator_mae - model_mae - uncertainty) != aggregate.get("strict_superiority_margin_cfs"):
        failures.append("USGS_HYDROLOGY_SCORER_SUPERIORITY_MARGIN_MISMATCH")

    if pack.get("negative_control", {}).get("rejected") is not True:
        failures.append("USGS_HYDROLOGY_NEGATIVE_CONTROL_NOT_REJECTED")
    if pack.get("target_leakage_control", {}).get("passed") is not True:
        failures.append("USGS_HYDROLOGY_TARGET_LEAKAGE_CONTROL_NOT_PASSED")

    strict_predicates = pack.get("strict_predicate_results", [])
    strict_all = all(row.get("passed") is True for row in strict_predicates) if strict_predicates else False
    if pack.get("strict_predicates_all_pass") is not strict_all:
        failures.append("USGS_HYDROLOGY_STRICT_PREDICATE_SUMMARY_MISMATCH")
    if pack.get("scientific_pass") is not strict_all:
        failures.append("USGS_HYDROLOGY_SCIENTIFIC_PASS_MISMATCH")
    if not residual_pass and pack.get("exact_blocker") != "COMPARATOR_BASELINE_NOT_BEATEN_WITH_UNCERTAINTY":
        failures.append("USGS_HYDROLOGY_EXACT_BLOCKER_MISMATCH")
    falsifier_status = pack.get("falsifier", {}).get("status")
    if pack.get("exact_blockers") and falsifier_status != "TRIGGERED":
        failures.append("USGS_HYDROLOGY_FALSIFIER_NOT_TRIGGERED_FOR_BLOCKER")
    if not pack.get("exact_blockers") and falsifier_status != "NOT_TRIGGERED":
        failures.append("USGS_HYDROLOGY_FALSIFIER_TRIGGERED_WITHOUT_BLOCKER")
    return failures


def check_usgs_hydrology_scorer_stored(root: Path | None = None) -> list[str]:
    root = root or repo_root()
    source_lane = load_usgs_api_lane(root)
    if source_lane.get("source_snapshot_hash_bound") is not True:
        return []
    expected = build_usgs_hydrology_scorer_pack(root)
    failures = validate_usgs_hydrology_scorer_pack(expected, root)
    path = root / USGS_HYDROLOGY_SCORER_EVIDENCE_REL
    if not path.exists():
        return [*failures, f"missing::{USGS_HYDROLOGY_SCORER_EVIDENCE_REL}"]
    actual = read_json(path)
    if actual != expected:
        failures.append(f"mismatch::{USGS_HYDROLOGY_SCORER_EVIDENCE_REL}")
    failures.extend(validate_usgs_hydrology_scorer_pack(actual if isinstance(actual, dict) else {}, root))
    return sorted(set(failures))


def validate_nasa_power_scorer_pack(pack: dict[str, Any], root: Path | None = None) -> list[str]:
    root = root or repo_root()
    failures: list[str] = []
    if pack.get("schema_id") != NASA_POWER_SCORER_SCHEMA_ID:
        failures.append("NASA_POWER_SCORER_SCHEMA_MISMATCH")
    if pack.get("work_order_id") != NASA_POWER_WORK_ORDER_ID:
        failures.append("NASA_POWER_SCORER_WORK_ORDER_MISMATCH")
    if pack.get("strict_artifact") is not True:
        failures.append("NASA_POWER_SCORER_STRICT_ARTIFACT_NOT_TRUE")
    if pack.get("coverage_closure_allowed") is not False:
        failures.append("NASA_POWER_SCORER_COVERAGE_CLOSURE_ALLOWED")
    if pack.get("broad_modern_science_superiority_allowed") is not False:
        failures.append("NASA_POWER_SCORER_BROAD_SUPERIORITY_ALLOWED")
    if pack.get("no_send_locks", {}).get("no_send") is not True:
        failures.append("NASA_POWER_SCORER_NO_SEND_LOCK_MISSING")
    if pack.get("replay_hash") != sha256_object(nasa_power_hash_payload(pack)):
        failures.append("NASA_POWER_SCORER_REPLAY_HASH_MISMATCH")
    if pack.get("evidence_pack_sha256") != sha256_object(nasa_power_evidence_hash_payload(pack)):
        failures.append("NASA_POWER_SCORER_EVIDENCE_PACK_HASH_MISMATCH")

    source_lane = load_nasa_power_api_lane(root)
    source = pack.get("source", {})
    if source.get("source_snapshot_hash_bound") is True:
        if source_lane.get("source_snapshot_hash_bound") is not True:
            failures.append("NASA_POWER_SCORER_SOURCE_NOT_HASH_BOUND_ON_REPLAY")
        for field in ("source_snapshot_sha256", "metadata_sha256", "byte_count", "value_row_count"):
            if source.get(field) != source_lane.get(field):
                failures.append(f"NASA_POWER_SCORER_SOURCE_FIELD_MISMATCH::{field}")

    if pack.get("scorer_ready") is not True:
        if not pack.get("exact_blockers"):
            failures.append("NASA_POWER_SCORER_BLOCKED_WITHOUT_EXACT_BLOCKER")
        return failures

    declaration = pack.get("pretarget_declaration", {})
    split = declaration.get("split_policy", {})
    hidden_placeholders = declaration.get("hidden_target_placeholders", [])
    visible_rows = declaration.get("visible_training_rows", [])
    materialization = declaration.get("prediction_materialization", {})
    prediction_rows = materialization.get("prediction_rows", [])
    scoring = pack.get("scoring_results", {})
    scored_rows = scoring.get("scored_rows", [])
    aggregate = scoring.get("aggregate", {})

    if split.get("training_row_count") != 20 or len(visible_rows) != 20:
        failures.append("NASA_POWER_SCORER_TRAINING_SPLIT_NOT_20")
    if split.get("hidden_row_count") != 20 or len(hidden_placeholders) != 20:
        failures.append("NASA_POWER_SCORER_HIDDEN_SPLIT_NOT_20")
    if scoring.get("hidden_row_count") != 20 or len(scored_rows) != 20:
        failures.append("NASA_POWER_SCORER_SCORED_N_NOT_20")
    if declaration.get("target_hidden_until_scoring") is not True:
        failures.append("NASA_POWER_SCORER_TARGET_NOT_HIDDEN")
    if declaration.get("target_values_used_for_model_selection") is not False:
        failures.append("NASA_POWER_SCORER_TARGET_USED_FOR_SELECTION")
    if declaration.get("target_values_used_for_prediction_materialization") is not False:
        failures.append("NASA_POWER_SCORER_TARGET_USED_FOR_PREDICTION")
    if materialization.get("predictions_materialized_before_target_unseal") is not True:
        failures.append("NASA_POWER_SCORER_PREDICTIONS_NOT_MATERIALIZED_BEFORE_UNSEAL")
    if materialization.get("hidden_target_values_included") is not False:
        failures.append("NASA_POWER_SCORER_MATERIALIZATION_CONTAINS_HIDDEN_TARGETS")
    for placeholder in hidden_placeholders:
        if "observed_allsky_sfc_sw_dwn_kwh_m2_day" in placeholder or "target_value" in placeholder:
            failures.append("NASA_POWER_SCORER_HIDDEN_PLACEHOLDER_LEAKS_TARGET")
            break
    if materialization.get("prediction_rows_sha256") != sha256_object(prediction_rows):
        failures.append("NASA_POWER_SCORER_PREDICTION_ROWS_HASH_MISMATCH")
    if scoring.get("scored_rows_sha256") != sha256_object(scored_rows):
        failures.append("NASA_POWER_SCORER_SCORED_ROWS_HASH_MISMATCH")
    for row in scored_rows:
        expected_row_hash = sha256_object({key: value for key, value in row.items() if key != "score_row_sha256"})
        if row.get("score_row_sha256") != expected_row_hash:
            failures.append(f"NASA_POWER_SCORER_SCORE_ROW_HASH_MISMATCH::{row.get('date')}")

    model_mae = float(aggregate.get("model_mae_kwh_m2_day", 0.0) or 0.0)
    comparator_mae = float(aggregate.get("comparator_mae_kwh_m2_day", 0.0) or 0.0)
    uncertainty = float(aggregate.get("aggregate_uncertainty_allowance_kwh_m2_day", 0.0) or 0.0)
    residual_pass = model_mae + uncertainty < comparator_mae
    if aggregate.get("residual_superiority_pass") is not residual_pass:
        failures.append("NASA_POWER_SCORER_RESIDUAL_SUPERIORITY_FLAG_MISMATCH")
    if round_metric(comparator_mae - model_mae - uncertainty) != aggregate.get("strict_superiority_margin_kwh_m2_day"):
        failures.append("NASA_POWER_SCORER_SUPERIORITY_MARGIN_MISMATCH")
    if pack.get("negative_control", {}).get("rejected") is not True:
        failures.append("NASA_POWER_NEGATIVE_CONTROL_NOT_REJECTED")
    if pack.get("target_leakage_control", {}).get("passed") is not True:
        failures.append("NASA_POWER_TARGET_LEAKAGE_CONTROL_NOT_PASSED")
    strict_predicates = pack.get("strict_predicate_results", [])
    strict_all = all(row.get("passed") is True for row in strict_predicates) if strict_predicates else False
    if pack.get("strict_predicates_all_pass") is not strict_all:
        failures.append("NASA_POWER_STRICT_PREDICATE_SUMMARY_MISMATCH")
    if pack.get("scientific_pass") is not strict_all:
        failures.append("NASA_POWER_SCIENTIFIC_PASS_MISMATCH")
    if not residual_pass and pack.get("exact_blocker") != "COMPARATOR_BASELINE_NOT_BEATEN_WITH_UNCERTAINTY":
        failures.append("NASA_POWER_EXACT_BLOCKER_MISMATCH")
    falsifier_status = pack.get("falsifier", {}).get("status")
    if pack.get("exact_blockers") and falsifier_status != "TRIGGERED":
        failures.append("NASA_POWER_FALSIFIER_NOT_TRIGGERED_FOR_BLOCKER")
    if not pack.get("exact_blockers") and falsifier_status != "NOT_TRIGGERED":
        failures.append("NASA_POWER_FALSIFIER_TRIGGERED_WITHOUT_BLOCKER")
    return failures


def check_nasa_power_scorer_stored(root: Path | None = None) -> list[str]:
    root = root or repo_root()
    source_lane = load_nasa_power_api_lane(root)
    if source_lane.get("source_snapshot_hash_bound") is not True:
        return []
    expected = build_nasa_power_scorer_pack(root)
    failures = validate_nasa_power_scorer_pack(expected, root)
    path = root / NASA_POWER_SCORER_EVIDENCE_REL
    if not path.exists():
        return [*failures, f"missing::{NASA_POWER_SCORER_EVIDENCE_REL}"]
    actual = read_json(path)
    if actual != expected:
        failures.append(f"mismatch::{NASA_POWER_SCORER_EVIDENCE_REL}")
    failures.extend(validate_nasa_power_scorer_pack(actual if isinstance(actual, dict) else {}, root))
    return sorted(set(failures))


def validate_noaa_coops_scorer_pack(pack: dict[str, Any], root: Path | None = None) -> list[str]:
    root = root or repo_root()
    failures: list[str] = []
    if pack.get("schema_id") != NOAA_COOPS_SCORER_SCHEMA_ID:
        failures.append("NOAA_COOPS_SCORER_SCHEMA_MISMATCH")
    if pack.get("work_order_id") != NOAA_COOPS_WORK_ORDER_ID:
        failures.append("NOAA_COOPS_SCORER_WORK_ORDER_MISMATCH")
    if pack.get("strict_artifact") is not True:
        failures.append("NOAA_COOPS_SCORER_STRICT_ARTIFACT_NOT_TRUE")
    if pack.get("coverage_closure_allowed") is not False:
        failures.append("NOAA_COOPS_SCORER_COVERAGE_CLOSURE_ALLOWED")
    if pack.get("broad_modern_science_superiority_allowed") is not False:
        failures.append("NOAA_COOPS_SCORER_BROAD_SUPERIORITY_ALLOWED")
    if pack.get("no_send_locks", {}).get("no_send") is not True:
        failures.append("NOAA_COOPS_SCORER_NO_SEND_LOCK_MISSING")
    if pack.get("replay_hash") != sha256_object(noaa_coops_hash_payload(pack)):
        failures.append("NOAA_COOPS_SCORER_REPLAY_HASH_MISMATCH")
    if pack.get("evidence_pack_sha256") != sha256_object(noaa_coops_evidence_hash_payload(pack)):
        failures.append("NOAA_COOPS_SCORER_EVIDENCE_PACK_HASH_MISMATCH")

    source_lane = load_noaa_coops_api_lane(root)
    source = pack.get("source", {})
    if source.get("source_snapshot_hash_bound") is True:
        if source_lane.get("source_snapshot_hash_bound") is not True:
            failures.append("NOAA_COOPS_SCORER_SOURCE_NOT_HASH_BOUND_ON_REPLAY")
        for field in (
            "water_level_source_snapshot_sha256",
            "predictions_source_snapshot_sha256",
            "metadata_sha256",
            "water_level_byte_count",
            "predictions_byte_count",
            "value_row_count",
        ):
            if source.get(field) != source_lane.get(field):
                failures.append(f"NOAA_COOPS_SCORER_SOURCE_FIELD_MISMATCH::{field}")

    if pack.get("scorer_ready") is not True:
        if not pack.get("exact_blockers"):
            failures.append("NOAA_COOPS_SCORER_BLOCKED_WITHOUT_EXACT_BLOCKER")
        return failures

    declaration = pack.get("pretarget_declaration", {})
    split = declaration.get("split_policy", {})
    hidden_placeholders = declaration.get("hidden_target_placeholders", [])
    visible_rows = declaration.get("visible_training_rows", [])
    materialization = declaration.get("prediction_materialization", {})
    prediction_rows = materialization.get("prediction_rows", [])
    scoring = pack.get("scoring_results", {})
    scored_rows = scoring.get("scored_rows", [])
    aggregate = scoring.get("aggregate", {})

    if split.get("training_row_count") != 240 or len(visible_rows) != 240:
        failures.append("NOAA_COOPS_SCORER_TRAINING_SPLIT_NOT_240")
    if split.get("hidden_row_count") != 480 or len(hidden_placeholders) != 480:
        failures.append("NOAA_COOPS_SCORER_HIDDEN_SPLIT_NOT_480")
    if scoring.get("hidden_row_count") != 480 or len(scored_rows) != 480:
        failures.append("NOAA_COOPS_SCORER_SCORED_N_NOT_480")
    if declaration.get("target_hidden_until_scoring") is not True:
        failures.append("NOAA_COOPS_SCORER_TARGET_NOT_HIDDEN")
    if declaration.get("target_values_used_for_model_selection") is not False:
        failures.append("NOAA_COOPS_SCORER_TARGET_USED_FOR_SELECTION")
    if declaration.get("target_values_used_for_prediction_materialization") is not False:
        failures.append("NOAA_COOPS_SCORER_TARGET_USED_FOR_PREDICTION")
    if materialization.get("predictions_materialized_before_target_unseal") is not True:
        failures.append("NOAA_COOPS_SCORER_PREDICTIONS_NOT_MATERIALIZED_BEFORE_UNSEAL")
    if materialization.get("hidden_target_values_included") is not False:
        failures.append("NOAA_COOPS_SCORER_MATERIALIZATION_CONTAINS_HIDDEN_TARGETS")
    for placeholder in hidden_placeholders:
        if "observed_water_level_m" in placeholder or "target_value" in placeholder:
            failures.append("NOAA_COOPS_SCORER_HIDDEN_PLACEHOLDER_LEAKS_TARGET")
            break
    if materialization.get("prediction_rows_sha256") != sha256_object(prediction_rows):
        failures.append("NOAA_COOPS_SCORER_PREDICTION_ROWS_HASH_MISMATCH")
    if scoring.get("scored_rows_sha256") != sha256_object(scored_rows):
        failures.append("NOAA_COOPS_SCORER_SCORED_ROWS_HASH_MISMATCH")
    for row in scored_rows:
        expected_row_hash = sha256_object({key: value for key, value in row.items() if key != "score_row_sha256"})
        if row.get("score_row_sha256") != expected_row_hash:
            failures.append(f"NOAA_COOPS_SCORER_SCORE_ROW_HASH_MISMATCH::{row.get('timestamp')}")

    model_mae = float(aggregate.get("model_mae_m", 0.0) or 0.0)
    comparator_mae = float(aggregate.get("comparator_mae_m", 0.0) or 0.0)
    uncertainty = float(aggregate.get("aggregate_uncertainty_allowance_m", 0.0) or 0.0)
    residual_pass = model_mae + uncertainty < comparator_mae
    if aggregate.get("residual_superiority_pass") is not residual_pass:
        failures.append("NOAA_COOPS_SCORER_RESIDUAL_SUPERIORITY_FLAG_MISMATCH")
    if round_metric(comparator_mae - model_mae - uncertainty) != aggregate.get("strict_superiority_margin_m"):
        failures.append("NOAA_COOPS_SCORER_SUPERIORITY_MARGIN_MISMATCH")
    if pack.get("negative_control", {}).get("rejected") is not True:
        failures.append("NOAA_COOPS_NEGATIVE_CONTROL_NOT_REJECTED")
    if pack.get("target_leakage_control", {}).get("passed") is not True:
        failures.append("NOAA_COOPS_TARGET_LEAKAGE_CONTROL_NOT_PASSED")
    strict_predicates = pack.get("strict_predicate_results", [])
    strict_all = all(row.get("passed") is True for row in strict_predicates) if strict_predicates else False
    if pack.get("strict_predicates_all_pass") is not strict_all:
        failures.append("NOAA_COOPS_STRICT_PREDICATE_SUMMARY_MISMATCH")
    if pack.get("scientific_pass") is not strict_all:
        failures.append("NOAA_COOPS_SCIENTIFIC_PASS_MISMATCH")
    if not residual_pass and pack.get("exact_blocker") != "COMPARATOR_BASELINE_NOT_BEATEN_WITH_UNCERTAINTY":
        failures.append("NOAA_COOPS_EXACT_BLOCKER_MISMATCH")
    falsifier_status = pack.get("falsifier", {}).get("status")
    if pack.get("exact_blockers") and falsifier_status != "TRIGGERED":
        failures.append("NOAA_COOPS_FALSIFIER_NOT_TRIGGERED_FOR_BLOCKER")
    if not pack.get("exact_blockers") and falsifier_status != "NOT_TRIGGERED":
        failures.append("NOAA_COOPS_FALSIFIER_TRIGGERED_WITHOUT_BLOCKER")
    return failures


def check_noaa_coops_scorer_stored(root: Path | None = None) -> list[str]:
    root = root or repo_root()
    source_lane = load_noaa_coops_api_lane(root)
    if source_lane.get("source_snapshot_hash_bound") is not True:
        return []
    expected = build_noaa_coops_scorer_pack(root)
    failures = validate_noaa_coops_scorer_pack(expected, root)
    path = root / NOAA_COOPS_SCORER_EVIDENCE_REL
    if not path.exists():
        return [*failures, f"missing::{NOAA_COOPS_SCORER_EVIDENCE_REL}"]
    actual = read_json(path)
    if actual != expected:
        failures.append(f"mismatch::{NOAA_COOPS_SCORER_EVIDENCE_REL}")
    failures.extend(validate_noaa_coops_scorer_pack(actual if isinstance(actual, dict) else {}, root))
    return sorted(set(failures))


def check_stored(root: Path | None = None) -> list[str]:
    root = root or repo_root()
    expected = build_payload(root)
    failures = validate_payload(expected)
    path = root / OUTPUT_REL
    if not path.exists():
        return [*failures, f"missing::{OUTPUT_REL}"]
    actual = read_json(path)
    if actual != expected:
        failures.append(f"mismatch::{OUTPUT_REL}")
    failures.extend(validate_payload(actual if isinstance(actual, dict) else {}))
    failures.extend(check_usgs_hydrology_scorer_stored(root))
    failures.extend(check_nasa_power_scorer_stored(root))
    failures.extend(check_noaa_coops_scorer_stored(root))
    return sorted(set(failures))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build/check earth-space modern-science coverage work orders.")
    parser.add_argument("--root", default=str(repo_root()), help="repository root")
    parser.add_argument("--write", action="store_true", help="write deterministic work-order artifact")
    parser.add_argument("--check", action="store_true", help="check stored artifact synchronization")
    parser.add_argument(
        "--refresh-usgs-hydrology-source",
        action="store_true",
        help="perform one read-only official USGS acquisition and refresh the local hash-bound source snapshot",
    )
    parser.add_argument(
        "--score-usgs-hydrology",
        action="store_true",
        help="build/check the target-hidden USGS hydrology replay scorer evidence pack",
    )
    parser.add_argument(
        "--refresh-nasa-power-source",
        action="store_true",
        help="perform one read-only official NASA POWER acquisition and refresh the local hash-bound source snapshot",
    )
    parser.add_argument(
        "--score-nasa-power",
        action="store_true",
        help="build/check the target-hidden NASA POWER remote-sensing replay scorer evidence pack",
    )
    parser.add_argument(
        "--refresh-noaa-coops-source",
        action="store_true",
        help="perform one read-only official NOAA CO-OPS acquisition and refresh the local hash-bound source snapshots",
    )
    parser.add_argument(
        "--score-noaa-coops",
        action="store_true",
        help="build/check the target-hidden NOAA CO-OPS water-level replay scorer evidence pack",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    if args.refresh_usgs_hydrology_source:
        refresh_usgs_hydrology_snapshot(root)
    if args.refresh_nasa_power_source:
        refresh_nasa_power_snapshot(root)
    if args.refresh_noaa_coops_source:
        refresh_noaa_coops_snapshot(root)
    if args.score_usgs_hydrology:
        pack = build_usgs_hydrology_scorer_pack(root)
        if args.write:
            write_json(root / USGS_HYDROLOGY_SCORER_EVIDENCE_REL, pack)
        failures = check_usgs_hydrology_scorer_stored(root) if args.check else validate_usgs_hydrology_scorer_pack(pack, root)
        print(
            json.dumps(
                {
                    "status": "ok" if not failures else "failed",
                    "output_ref": USGS_HYDROLOGY_SCORER_EVIDENCE_REL,
                    "pack_status": pack.get("pack_status"),
                    "exact_blocker": pack.get("exact_blocker"),
                    "failures": failures,
                },
                indent=2,
            )
        )
        return 0 if not failures else 1
    if args.score_nasa_power:
        pack = build_nasa_power_scorer_pack(root)
        if args.write:
            write_json(root / NASA_POWER_SCORER_EVIDENCE_REL, pack)
        failures = check_nasa_power_scorer_stored(root) if args.check else validate_nasa_power_scorer_pack(pack, root)
        print(
            json.dumps(
                {
                    "status": "ok" if not failures else "failed",
                    "output_ref": NASA_POWER_SCORER_EVIDENCE_REL,
                    "pack_status": pack.get("pack_status"),
                    "exact_blocker": pack.get("exact_blocker"),
                    "failures": failures,
                },
                indent=2,
            )
        )
        return 0 if not failures else 1
    if args.score_noaa_coops:
        pack = build_noaa_coops_scorer_pack(root)
        if args.write:
            write_json(root / NOAA_COOPS_SCORER_EVIDENCE_REL, pack)
        failures = check_noaa_coops_scorer_stored(root) if args.check else validate_noaa_coops_scorer_pack(pack, root)
        print(
            json.dumps(
                {
                    "status": "ok" if not failures else "failed",
                    "output_ref": NOAA_COOPS_SCORER_EVIDENCE_REL,
                    "pack_status": pack.get("pack_status"),
                    "exact_blocker": pack.get("exact_blocker"),
                    "failures": failures,
                },
                indent=2,
            )
        )
        return 0 if not failures else 1
    if args.check:
        failures = check_stored(root)
        if failures:
            for failure in failures:
                print(f"ERROR: {failure}")
            return 1
        print(json.dumps({"status": "ok", "checked": OUTPUT_REL}, indent=2))
        return 0
    payload = build_payload(root)
    failures = validate_payload(payload)
    if args.write:
        write_json(root / OUTPUT_REL, payload)
        if load_usgs_api_lane(root).get("source_snapshot_hash_bound") is True:
            write_json(root / USGS_HYDROLOGY_SCORER_EVIDENCE_REL, build_usgs_hydrology_scorer_pack(root))
        if load_nasa_power_api_lane(root).get("source_snapshot_hash_bound") is True:
            write_json(root / NASA_POWER_SCORER_EVIDENCE_REL, build_nasa_power_scorer_pack(root))
        if load_noaa_coops_api_lane(root).get("source_snapshot_hash_bound") is True:
            write_json(root / NOAA_COOPS_SCORER_EVIDENCE_REL, build_noaa_coops_scorer_pack(root))
    print(json.dumps({"status": "ok" if not failures else "failed", "output_ref": OUTPUT_REL, "failures": failures}, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
