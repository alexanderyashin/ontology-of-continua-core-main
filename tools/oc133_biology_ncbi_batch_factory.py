from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from validation.grand_science import evidence_pack_factory as grand_factory


RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
CAPABILITY_OWNER = "Research/EmpiricalScience"
PLANNER_REF = "tools/oc133_biology_ncbi_batch_factory.py"

SCHEMA_ID = "OC133_BIOLOGY_NCBI_BATCH_FACTORY_v1"
TASKS_SCHEMA_ID = "OC133_BIOLOGY_NCBI_BATCH_TASKS_v1"
PROTOCOL_SCHEMA_ID = "OC133_BIOLOGY_NCBI_BATCH_PROTOCOL_v1"
REPORT_SCHEMA_ID = "OC133_BIOLOGY_NCBI_BATCH_REPORT_v1"
ACQUISITION_SCHEMA_ID = "OC133_BIOLOGY_NCBI_BATCH_ACQUISITION_PACKET_v1"
HASHES_SCHEMA_ID = "OC133_BIOLOGY_NCBI_BATCH_HASHES_v1"

OUTPUT_ROOT_REL = "validation/heldout/grand_science/biology/ncbi_batch"
TASKS_REL = f"{OUTPUT_ROOT_REL}/OC133_BIOLOGY_NCBI_BATCH_TASKS.json"
PROTOCOL_REL = f"{OUTPUT_ROOT_REL}/OC133_BIOLOGY_NCBI_BATCH_PROTOCOL.json"
CANDIDATE_PACK_REL = f"{OUTPUT_ROOT_REL}/OC133_BIOLOGY_NCBI_BATCH_CANDIDATE_PACK.json"
REPORT_REL = f"{OUTPUT_ROOT_REL}/OC133_BIOLOGY_NCBI_BATCH_REPORT.json"
ACQUISITION_REL = f"{OUTPUT_ROOT_REL}/OC133_BIOLOGY_NCBI_BATCH_ACQUISITION_PACKET.json"
HASHES_REL = f"{OUTPUT_ROOT_REL}/OC133_BIOLOGY_NCBI_BATCH_HASHES.json"
README_REL = f"{OUTPUT_ROOT_REL}/README.md"

REQUIREMENTS_REL = "benchmarks/grand_science/domain_requirements.json"
DEFAULT_SNAPSHOT_REF = "validation/_raw/biology_ncbi_geo_platform.txt"
DEFAULT_DISCOVERY_ROOTS = (
    "validation/_raw",
    "data/biology",
    "empirical/biology",
    f"{OUTPUT_ROOT_REL}/raw",
)
OFFICIAL_ACQUISITION_RUN_ROOT_REL = "validation/heldout/acquisition_runs/oc133_official_readonly"
OFFICIAL_ACQUISITION_LOCKS_REL = f"{OFFICIAL_ACQUISITION_RUN_ROOT_REL}/locks"
OFFICIAL_ACQUISITION_SNAPSHOTS_REL = f"{OFFICIAL_ACQUISITION_RUN_ROOT_REL}/snapshots"

SNAPSHOT_HASH_POLICY = "LF_NORMALIZED_TEXT_SNAPSHOT_HASH"
OFFICIAL_ACQUISITION_HASH_POLICY = "sha256 over acquired response bytes as stored"
ROW_HASH_POLICY = "sha256 over canonical row JSON before row_hash insertion"
PACK_HASH_POLICY = "sha256 over canonical JSON"
OFFICIAL_ESEARCH_ENDPOINT = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
DEFAULT_GEO_TERM = "GPL96[Accession]"
DEFAULT_RETMAX = 20
NCBI_GEO_HINTS = ("ncbi", "geo", "gds", "gse", "gsm", "gpl")
GENERATED_NAME_PREFIX = "OC133_BIOLOGY_NCBI_BATCH_"
SUPPORT_POLICY = (
    "Grand support is emitted only for an N>=20 NCBI/GEO batch with explicit source separation, "
    "pre-target lock, hidden target manifest, official NCBI/GEO provenance, preregistered comparator, "
    "residual superiority, rejected negative controls, and falsifiers. Existing single raw snapshots "
    "remain acquisition-ready blockers."
)


def repo_root() -> Path:
    return ROOT


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def sha256_object(payload: Any) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def sha256_text(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def lf_bytes(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n")


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


def rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def ordered_unique(values: list[Any]) -> list[Any]:
    seen: set[str] = set()
    out: list[Any] = []
    for value in values:
        key = canonical_json(value) if isinstance(value, (dict, list)) else str(value)
        if key in seen:
            continue
        seen.add(key)
        out.append(value)
    return out


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


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        if isinstance(value, bool):
            return default
        result = float(value)
    except (TypeError, ValueError):
        return default
    return result if math.isfinite(result) else default


def is_number(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def load_requirements(root: Path) -> tuple[dict[str, Any], list[str]]:
    fallback = {
        "minimum_per_domain_n": 20,
        "required_domains": ["biology"],
        "required_source_separation_modes": ["target_blind", "prospective"],
    }
    path = root / REQUIREMENTS_REL
    if not path.exists():
        return fallback, ["REQUIREMENTS_MISSING::using_defaults"]
    try:
        payload = read_json(path)
    except Exception as exc:
        return fallback, [f"REQUIREMENTS_PARSE_ERROR::{exc.__class__.__name__}"]
    if not isinstance(payload, dict):
        return fallback, ["REQUIREMENTS_NOT_OBJECT::using_defaults"]
    merged = {**fallback, **payload}
    return merged, []


def has_ncbi_geo_hint(path: Path) -> bool:
    lowered = path.as_posix().lower()
    return any(hint in lowered for hint in NCBI_GEO_HINTS)


def is_generated_artifact(path: Path) -> bool:
    name = path.name
    return name == "README.md" or name.startswith(GENERATED_NAME_PREFIX)


def discover_snapshot_refs(root: Path, explicit_refs: list[str] | None = None) -> list[str]:
    if explicit_refs:
        return ordered_unique([ref.replace("\\", "/") for ref in explicit_refs if ref.strip()])

    refs: list[str] = []
    default_path = root / DEFAULT_SNAPSHOT_REF
    if default_path.exists():
        refs.append(DEFAULT_SNAPSHOT_REF)

    for base_ref in DEFAULT_DISCOVERY_ROOTS:
        base = root / base_ref
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file() or is_generated_artifact(path):
                continue
            if path.suffix.lower() not in {".json", ".txt", ".ndjson"}:
                continue
            if not has_ncbi_geo_hint(path):
                continue
            try:
                refs.append(rel(root, path))
            except ValueError:
                continue
    return ordered_unique(refs)


def parse_json_or_ndjson(path: Path) -> tuple[Any | None, list[str]]:
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text), []
    except json.JSONDecodeError as json_exc:
        rows: list[Any] = []
        for line_number, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                rows.append(json.loads(stripped))
            except json.JSONDecodeError:
                return None, [f"SNAPSHOT_PARSE_ERROR::{path.name}::line={line_number}::{json_exc.__class__.__name__}"]
        if rows:
            return rows, []
        return None, [f"SNAPSHOT_PARSE_ERROR::{path.name}::{json_exc.__class__.__name__}"]


def load_snapshot(root: Path, ref: str) -> dict[str, Any]:
    path = resolve_under_root(root, ref)
    if not path.exists():
        return {
            "ref": ref,
            "exists": False,
            "payload": None,
            "sha256": "",
            "byte_count": 0,
            "failures": [f"SNAPSHOT_MISSING::{ref}"],
        }
    if not path.is_file():
        return {
            "ref": ref,
            "exists": False,
            "payload": None,
            "sha256": "",
            "byte_count": 0,
            "failures": [f"SNAPSHOT_NOT_FILE::{ref}"],
        }
    payload, failures = parse_json_or_ndjson(path)
    return {
        "ref": ref,
        "exists": True,
        "payload": payload,
        "sha256": sha256_bytes(lf_bytes(path)),
        "byte_count": path.stat().st_size,
        "failures": failures,
        "acquisition": {},
    }


def packet_acquisition_rows(packet: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("source_acquisition_requests", "missing_official_snapshots", "official_snapshots", "acquisition_requests", "snapshots"):
        rows = packet.get(key)
        if isinstance(rows, list):
            return [row for row in rows if isinstance(row, dict)]
    return []


def load_packet_requests(root: Path) -> list[dict[str, Any]]:
    path = root / ACQUISITION_REL
    if not path.exists():
        return []
    try:
        packet = read_json(path)
    except Exception:
        return []
    if not isinstance(packet, dict):
        return []
    requests: list[dict[str, Any]] = []
    for index, row in enumerate(packet_acquisition_rows(packet), start=1):
        acquisition_id = as_str(row.get("acquisition_id"), f"OC133-NCBI-GEO-OFFICIAL-SNAPSHOT-{index:04d}")
        requests.append(
            {
                **row,
                "acquisition_id": acquisition_id,
                "packet_ref": ACQUISITION_REL,
                "packet_schema_id": as_str(packet.get("schema_id")),
            }
        )
    return requests


def request_key(row: dict[str, Any]) -> str:
    return as_str(row.get("acquisition_id")) or as_str(row.get("expected_local_snapshot_ref"))


def load_official_acquisition_snapshots(root: Path, packet_requests: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    requests_by_id = {request_key(row): row for row in packet_requests if request_key(row)}
    requests_by_expected_ref = {
        as_str(row.get("expected_local_snapshot_ref")): row
        for row in packet_requests
        if as_str(row.get("expected_local_snapshot_ref"))
    }
    locks_dir = root / OFFICIAL_ACQUISITION_LOCKS_REL
    if not locks_dir.exists():
        return [], []

    snapshots: list[dict[str, Any]] = []
    failures: list[str] = []
    for lock_path in sorted(locks_dir.glob("*.lock.json")):
        try:
            lock = read_json(lock_path)
        except Exception as exc:
            failures.append(f"OFFICIAL_ACQUISITION_LOCK_PARSE_FAILED::{rel(root, lock_path)}::{exc.__class__.__name__}")
            continue
        if not isinstance(lock, dict):
            failures.append(f"OFFICIAL_ACQUISITION_LOCK_NOT_OBJECT::{rel(root, lock_path)}")
            continue
        acquisition_id = as_str(lock.get("acquisition_id"))
        expected_ref = as_str(lock.get("expected_local_snapshot_ref"))
        request = requests_by_id.get(acquisition_id) or requests_by_expected_ref.get(expected_ref)
        if request is None:
            continue
        snapshot_ref = as_str(lock.get("snapshot_ref"))
        if not snapshot_ref.startswith(OFFICIAL_ACQUISITION_SNAPSHOTS_REL):
            failures.append(f"OFFICIAL_ACQUISITION_SNAPSHOT_REF_UNEXPECTED::{acquisition_id}::{snapshot_ref}")
            continue
        snapshot_path = resolve_under_root(root, snapshot_ref)
        if not snapshot_path.exists() or not snapshot_path.is_file():
            failures.append(f"OFFICIAL_ACQUISITION_SNAPSHOT_MISSING::{acquisition_id}::{snapshot_ref}")
            continue
        raw_bytes = snapshot_path.read_bytes()
        actual_sha = sha256_bytes(raw_bytes)
        declared_sha = as_str(lock.get("snapshot_sha256"))
        if actual_sha != declared_sha:
            failures.append(f"OFFICIAL_ACQUISITION_SNAPSHOT_HASH_MISMATCH::{acquisition_id}")
            continue
        if as_int(lock.get("http_status")) < 200 or as_int(lock.get("http_status")) >= 300:
            failures.append(f"OFFICIAL_ACQUISITION_HTTP_STATUS_NOT_SUCCESS::{acquisition_id}::{lock.get('http_status')}")
            continue
        if dict_or_empty(lock.get("locks")).get("no_send") is not True:
            failures.append(f"OFFICIAL_ACQUISITION_NO_SEND_LOCK_MISSING::{acquisition_id}")
            continue
        try:
            payload = json.loads(raw_bytes.decode("utf-8"))
        except Exception as exc:
            failures.append(f"OFFICIAL_ACQUISITION_SNAPSHOT_PARSE_FAILED::{acquisition_id}::{exc.__class__.__name__}")
            continue
        lock_ref = rel(root, lock_path)
        snapshots.append(
            {
                "ref": snapshot_ref,
                "exists": True,
                "payload": payload,
                "sha256": actual_sha,
                "byte_count": len(raw_bytes),
                "failures": [],
                "acquisition": {
                    "acquisition_id": acquisition_id,
                    "packet_ref": as_str(request.get("packet_ref"), ACQUISITION_REL),
                    "packet_schema_id": as_str(request.get("packet_schema_id")),
                    "expected_local_snapshot_ref": expected_ref,
                    "official_endpoint_url": as_str(lock.get("official_endpoint_url"), as_str(request.get("official_endpoint_url"))),
                    "lock_ref": lock_ref,
                    "lock_sha256": sha256_bytes(lock_path.read_bytes()),
                    "declared_before_scoring_lock": True,
                    "hash_policy": as_str(lock.get("hash_policy"), OFFICIAL_ACQUISITION_HASH_POLICY),
                    "required_fields": request.get("required_fields", []),
                    "query_params": request.get("query_params", {}),
                },
            }
        )
    return snapshots, failures


def dict_or_empty(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def list_of_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def source_separation_from_payload(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    raw = payload.get("source_separation", payload.get("oc133_source_separation", {}))
    return dict_or_empty(raw)


def comparator_from_payload(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    raw = payload.get("comparator_baseline", payload.get("oc133_comparator_baseline", {}))
    return dict_or_empty(raw)


def provenance_from_payload(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    raw = payload.get("snapshot_provenance", payload.get("provenance", {}))
    return dict_or_empty(raw)


def normalize_source_separation(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "mode": as_str(raw.get("mode"), "snapshot_replay"),
        "kind": as_str(raw.get("kind"), "snapshot_replay"),
        "pre_target_lock": raw.get("pre_target_lock") is True,
        "target_hidden_until_scoring": raw.get("target_hidden_until_scoring") is True,
        "declared_before_scoring": raw.get("declared_before_scoring") is True,
        "training_sources": ordered_unique(list_of_strings(raw.get("training_sources"))),
        "target_sources": ordered_unique(list_of_strings(raw.get("target_sources"))),
        "training_manifest_sha256": as_str(raw.get("training_manifest_sha256")),
        "target_manifest_sha256": as_str(raw.get("target_manifest_sha256")),
    }


def iter_payload_records(payload: Any) -> list[tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]]:
    records: list[tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]] = []
    batch_source = source_separation_from_payload(payload)
    batch_comparator = comparator_from_payload(payload)
    batch_provenance = provenance_from_payload(payload)

    def append(raw_record: Any) -> None:
        if not isinstance(raw_record, dict):
            return
        record_source = source_separation_from_payload(raw_record) or batch_source
        record_comparator = comparator_from_payload(raw_record) or batch_comparator
        record_provenance = provenance_from_payload(raw_record) or batch_provenance
        records.append((raw_record, record_source, record_comparator, record_provenance))

    if isinstance(payload, dict):
        for key in ("snapshots", "records", "rows"):
            if isinstance(payload.get(key), list):
                for item in payload[key]:
                    append(item)
                return records
        append(payload)
    elif isinstance(payload, list):
        for item in payload:
            append(item)
    return records


def esearch_result(record: dict[str, Any]) -> dict[str, Any]:
    esearch = record.get("esearchresult", record.get("eSearchResult", {}))
    return dict_or_empty(esearch)


def parse_idlist(esearch: dict[str, Any]) -> tuple[list[str], list[str]]:
    raw = esearch.get("idlist")
    if not isinstance(raw, list):
        return [], ["IDLIST_MISSING_OR_INVALID"]
    out: list[str] = []
    failures: list[str] = []
    for idx, value in enumerate(raw, start=1):
        if value is None:
            failures.append(f"IDLIST_ITEM_INVALID::{idx}")
            continue
        out.append(str(value))
    return out, failures


def official_url_is_ncbi_geo(url: str) -> bool:
    lowered = url.lower()
    return lowered.startswith(OFFICIAL_ESEARCH_ENDPOINT) or lowered.startswith(
        "https://www.ncbi.nlm.nih.gov/geo/"
    ) or lowered.startswith("https://ftp.ncbi.nlm.nih.gov/geo/")


def provenance_status(provenance: dict[str, Any], ref: str) -> tuple[bool, str, str]:
    source = as_str(provenance.get("official_source"), as_str(provenance.get("source"), ""))
    url = as_str(provenance.get("official_url"), as_str(provenance.get("source_url"), ""))
    source_ok = "ncbi" in source.lower() or "geo" in source.lower()
    url_ok = official_url_is_ncbi_geo(url)
    if source_ok and url_ok:
        return True, source, url
    return False, source, url or f"{ref}::NO_OFFICIAL_SOURCE_URL_DECLARED"


def row_hash(row: dict[str, Any]) -> str:
    clean = {key: value for key, value in row.items() if key not in {"row_hash", "row_hash_policy"}}
    return sha256_object(clean)


def build_row(
    *,
    record: dict[str, Any],
    source_ref: str,
    source_sha256: str,
    record_index: int,
    comparator: dict[str, Any],
    provenance: dict[str, Any],
    acquisition: dict[str, Any] | None = None,
) -> tuple[dict[str, Any] | None, list[str]]:
    acquisition = acquisition or {}
    esearch = esearch_result(record)
    if not esearch:
        return None, [f"SNAPSHOT_RECORD_NOT_NCBI_ESEARCH::{source_ref}::{record_index}"]

    idlist, idlist_failures = parse_idlist(esearch)
    retstart = as_int(esearch.get("retstart"), 0)
    retmax = as_int(esearch.get("retmax"), len(idlist))
    count = as_int(esearch.get("count"), retmax)
    if retmax < 0:
        idlist_failures.append(f"RETMAX_NEGATIVE::{source_ref}::{record_index}")
    if count < 0:
        idlist_failures.append(f"COUNT_NEGATIVE::{source_ref}::{record_index}")

    predicted = float(len(idlist))
    observed = float(retmax)
    comparator_prediction = float(count)
    model_residual = abs(predicted - observed)
    comparator_residual = abs(comparator_prediction - observed)
    term = as_str(esearch.get("querytranslation"), DEFAULT_GEO_TERM) or DEFAULT_GEO_TERM
    if acquisition:
        provenance = {
            **provenance,
            "official_source": "NCBI E-utilities ESearch",
            "official_url": acquisition.get("official_endpoint_url"),
        }
        comparator = {
            **comparator,
            "name": as_str(comparator.get("name"), "GEO total-hit-count page-size negative control"),
            "prediction_rule": as_str(
                comparator.get("prediction_rule"), "use esearchresult.count as the retmax prediction"
            ),
            "pre_registered": comparator.get("pre_registered", True),
        }
    official_ok, official_source, official_url = provenance_status(provenance, source_ref)
    comparator_pre_registered = comparator.get("pre_registered") is True
    row_id_hash = sha256_object({"source_ref": source_ref, "record_index": record_index, "term": term})[:12].upper()
    row_id = f"BIOLOGY-NCBI-GEO-BATCH-{record_index:04d}-{row_id_hash}"
    row = {
        "observation_id": row_id,
        "claim_id": f"OC133-BIOLOGY-NCBI-BATCH-{record_index:04d}",
        "task_type": "geo_esearch_page_size_reconstruction",
        "snapshot_ref": source_ref,
        "snapshot_sha256": source_sha256,
        "source_snapshot_hash": source_sha256,
        "source_snapshot_hash_policy": acquisition.get("hash_policy", SNAPSHOT_HASH_POLICY),
        "acquisition_id": as_str(acquisition.get("acquisition_id")),
        "expected_local_snapshot_ref": as_str(acquisition.get("expected_local_snapshot_ref")),
        "lock_ref": as_str(acquisition.get("lock_ref")),
        "lock_sha256": as_str(acquisition.get("lock_sha256")),
        "declared_before_scoring_lock": acquisition.get("declared_before_scoring_lock") is True,
        "acquisition_packet_ref": as_str(acquisition.get("packet_ref")),
        "record_index": record_index,
        "official_source_confirmed": official_ok,
        "official_source": official_source or "UNDECLARED_NCBI_GEO_PROVENANCE",
        "official_source_url": official_url,
        "query_term": term,
        "retstart": retstart,
        "retmax": retmax,
        "idlist_count": len(idlist),
        "training_source": f"{source_ref}::record={record_index}::visible_fields(retstart,idlist,querytranslation)",
        "target_source": f"{source_ref}::record={record_index}::target_field(retmax)",
        "formula": "len(esearchresult.idlist)",
        "formula_inputs": {
            "idlist": idlist,
            "idlist_count": len(idlist),
            "retstart": retstart,
            "querytranslation": term,
        },
        "prediction_inputs": {
            "visible_fields": ["esearchresult.idlist", "esearchresult.retstart", "esearchresult.querytranslation"],
            "target_field": "esearchresult.retmax",
        },
        "predicted_value": predicted,
        "observed_value": observed,
        "comparator_baseline_name": as_str(
            comparator.get("name"), "GEO total-hit-count page-size negative control"
        ),
        "comparator_prediction_rule": as_str(
            comparator.get("prediction_rule"), "use esearchresult.count as the retmax prediction"
        ),
        "comparator_pre_registered": comparator_pre_registered,
        "comparator_prediction": comparator_prediction,
        "uncertainty": 0.0,
        "model_residual": model_residual,
        "comparator_residual": comparator_residual,
        "negative_control_id": f"biology-ncbi-total-count-control::{row_id}",
        "negative_control_description": "replace the page-size reconstruction with GEO total hit count and require a larger residual",
        "negative_control_rejected": comparator_residual > model_residual,
        "negative_control_status": "REJECTED" if comparator_residual > model_residual else "NOT_REJECTED",
        "falsifier": "retmax differs from returned idlist length, or the GEO total-count control is not worse",
        "falsifier_status": "TRIGGERED" if (model_residual != 0 or comparator_residual <= model_residual) else "NOT_TRIGGERED",
    }
    row["row_hash"] = row_hash(row)
    row["row_hash_policy"] = ROW_HASH_POLICY
    return row, idlist_failures


def select_source_separation(candidates: list[dict[str, Any]]) -> tuple[dict[str, Any], list[str]]:
    normalized = [normalize_source_separation(candidate) for candidate in candidates if candidate]
    non_default = [candidate for candidate in normalized if candidate["mode"] != "snapshot_replay"]
    if not non_default:
        return normalize_source_separation({}), ["SOURCE_SEPARATION_MISSING::defaulting_to_snapshot_replay"]
    unique = ordered_unique(non_default)
    failures: list[str] = []
    if len(unique) > 1:
        failures.append("SOURCE_SEPARATION_CONFLICT_ACROSS_SNAPSHOTS")
    return unique[0], failures


def validate_source_separation(source: dict[str, Any], requirements: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    allowed_modes = {str(mode) for mode in requirements.get("required_source_separation_modes", ["target_blind", "prospective"])}
    if source.get("mode") not in allowed_modes:
        failures.append(f"SOURCE_SEPARATION_MODE_NOT_ALLOWED::{source.get('mode')}")
    if source.get("kind") in {"snapshot_replay", "single_raw_snapshot", "snapshot_only", "replay_only"}:
        failures.append(f"TARGET_SEPARATION_NOT_REAL::{source.get('kind')}")
    if source.get("pre_target_lock") is not True:
        failures.append("PRE_TARGET_LOCK_REQUIRED")
    if source.get("target_hidden_until_scoring") is not True:
        failures.append("TARGET_HIDDEN_UNTIL_SCORING_REQUIRED")
    if source.get("declared_before_scoring") is not True:
        failures.append("SOURCE_SEPARATION_NOT_DECLARED_BEFORE_SCORING")
    training_sources = list_of_strings(source.get("training_sources"))
    target_sources = list_of_strings(source.get("target_sources"))
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
        "source_snapshot_hash",
        "lock_ref",
        "formula",
        "formula_inputs",
        "prediction_inputs",
        "predicted_value",
        "observed_value",
        "comparator_prediction",
        "model_residual",
        "comparator_residual",
        "negative_control_id",
        "negative_control_description",
        "negative_control_status",
        "falsifier",
        "falsifier_status",
        "row_hash",
    )
    for row in rows:
        row_id = as_str(row.get("observation_id"), "unknown")
        for field in required:
            if row.get(field) in (None, ""):
                failures.append(f"ROW_FIELD_MISSING::{row_id}::{field}")
        for field in ("predicted_value", "observed_value", "comparator_prediction", "model_residual", "comparator_residual", "uncertainty"):
            if not is_number(row.get(field)):
                failures.append(f"ROW_NUMERIC_INVALID::{row_id}::{field}")
        if row.get("training_source") == row.get("target_source"):
            failures.append(f"ROW_SOURCE_OVERLAP::{row_id}")
        if row.get("official_source_confirmed") is not True:
            failures.append(f"OFFICIAL_NCBI_GEO_PROVENANCE_MISSING::{row_id}")
        if row.get("declared_before_scoring_lock") is not True:
            failures.append(f"DECLARED_BEFORE_SCORING_LOCK_MISSING::{row_id}")
        if row.get("comparator_pre_registered") is not True:
            failures.append(f"COMPARATOR_BASELINE_NOT_PREREGISTERED::{row_id}")
        if row.get("negative_control_rejected") is not True:
            failures.append(f"NEGATIVE_CONTROL_NOT_REJECTED::{row_id}")
        if as_float(row.get("comparator_residual")) <= as_float(row.get("model_residual")):
            failures.append(f"COMPARATOR_NOT_WORSE_THAN_MODEL::{row_id}")
    if rows and not all(row.get("comparator_pre_registered") is True for row in rows):
        failures.append("COMPARATOR_BASELINE_NOT_PREREGISTERED")
    if rows and not all(row.get("negative_control_rejected") is True for row in rows):
        failures.append("NEGATIVE_CONTROL_REJECTION_CRITERION_FAILED")
    if rows and not all(row.get("official_source_confirmed") is True for row in rows):
        failures.append("OFFICIAL_NCBI_GEO_PROVENANCE_REQUIRED")
    if rows and not all(row.get("declared_before_scoring_lock") is True for row in rows):
        failures.append("DECLARED_BEFORE_SCORING_LOCK_REQUIRED")
    return ordered_unique(failures)


def residual_summary(rows: list[dict[str, Any]]) -> dict[str, float]:
    model_values = [as_float(row.get("model_residual")) for row in rows if is_number(row.get("model_residual"))]
    comparator_values = [as_float(row.get("comparator_residual")) for row in rows if is_number(row.get("comparator_residual"))]
    model = sum(model_values) / len(model_values) if model_values else 0.0
    comparator = sum(comparator_values) / len(comparator_values) if comparator_values else 0.0
    return {
        "model": model,
        "comparator": comparator,
        "superiority_margin": comparator - model,
    }


def uncertainty_interval(rows: list[dict[str, Any]], model_mean: float) -> list[float]:
    residuals = [as_float(row.get("model_residual")) for row in rows if is_number(row.get("model_residual"))]
    if not residuals:
        return [0.0, 0.0]
    lower = min([0.0, model_mean, *residuals])
    upper = max([0.0, model_mean, *residuals])
    return [lower, upper]


def build_pack(rows: list[dict[str, Any]], source: dict[str, Any], support_allowed: bool) -> dict[str, Any]:
    residuals = residual_summary(rows)
    training_sources = list_of_strings(source.get("training_sources")) or ordered_unique(
        [as_str(row.get("training_source")) for row in rows if row.get("training_source")]
    )
    target_sources = list_of_strings(source.get("target_sources")) or ordered_unique(
        [as_str(row.get("target_source")) for row in rows if row.get("target_source")]
    )
    return {
        "schema_id": grand_factory.EVIDENCE_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "capability_owner": CAPABILITY_OWNER,
        "evidence_pack_id": "OC133-BIOLOGY-NCBI-BATCH-CANDIDATE",
        "domain": "biology",
        "source_separation": {
            "mode": source.get("mode", "snapshot_replay"),
            "pre_target_lock": source.get("pre_target_lock") is True,
            "target_hidden_until_scoring": source.get("target_hidden_until_scoring") is True,
            "training_sources": training_sources,
            "target_sources": target_sources,
        },
        "n": len(rows),
        "model_under_test": "NCBI/GEO ESearch batch page-size reconstruction: len(esearchresult.idlist)",
        "comparator_baseline": {
            "name": "GEO total-hit-count page-size negative control",
            "prediction_rule": "use esearchresult.count as the retmax prediction for every batch row",
            "pre_registered": bool(rows) and all(row.get("comparator_pre_registered") is True for row in rows),
        },
        "uncertainty": {
            "metric": "mean absolute residual",
            "method": "deterministic NCBI/GEO ESearch batch replay with exact integer target",
            "interval": uncertainty_interval(rows, residuals["model"]),
        },
        "residuals": residuals,
        "negative_controls": [
            {
                "control_id": row["negative_control_id"],
                "description": row["negative_control_description"],
                "rejected": row.get("negative_control_rejected") is True,
            }
            for row in rows
        ]
        or [
            {
                "control_id": "biology-ncbi-batch-no-rows",
                "description": "no NCBI/GEO batch rows were available for a negative-control test",
                "rejected": False,
            }
        ],
        "falsifiers": ordered_unique([as_str(row.get("falsifier")) for row in rows if row.get("falsifier")])
        or ["no scored NCBI/GEO batch rows; support blocked"],
        "grand_toe_support_allowed": bool(support_allowed),
    }


def slugify_query(term: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", term).strip("_").lower()
    return cleaned or "geo_query"


def official_esearch_url(term: str, retstart: int, retmax: int) -> str:
    params = {
        "db": "gds",
        "term": term,
        "retmode": "json",
        "retstart": str(retstart),
        "retmax": str(retmax),
    }
    return f"{OFFICIAL_ESEARCH_ENDPOINT}?{urlencode(params)}"


def missing_official_snapshots(
    rows: list[dict[str, Any]],
    minimum_n: int,
    packet_requests: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    missing_n = max(0, minimum_n - len(rows))
    if missing_n == 0:
        return []
    packet_requests = packet_requests or []
    acquired_ids = {as_str(row.get("acquisition_id")) for row in rows if row.get("acquisition_id")}
    acquired_expected_refs = {
        as_str(row.get("expected_local_snapshot_ref")) for row in rows if row.get("expected_local_snapshot_ref")
    }
    missing: list[dict[str, Any]] = []
    for request in packet_requests:
        if len(missing) >= missing_n:
            break
        acquisition_id = as_str(request.get("acquisition_id"))
        expected_ref = as_str(request.get("expected_local_snapshot_ref"))
        if acquisition_id in acquired_ids or expected_ref in acquired_expected_refs:
            continue
        missing.append(
            {
                "acquisition_id": acquisition_id,
                "official_source": as_str(request.get("official_source"), "NCBI E-utilities ESearch"),
                "official_endpoint_url": as_str(request.get("official_endpoint_url")),
                "expected_local_snapshot_ref": expected_ref,
                "query_params": request.get("query_params", {}),
                "required_fields": request.get("required_fields", []),
                "target_policy": as_str(
                    request.get("target_policy"),
                    "retmax is a target field and must remain hidden from the scoring worker until the batch lock is closed",
                ),
                "missing_reason": "pinned official acquisition lock/snapshot is absent or failed validation",
                "no_send_lock": True,
            }
        )
    if len(missing) >= missing_n:
        return missing

    term = DEFAULT_GEO_TERM
    retmax = DEFAULT_RETMAX
    existing_retstarts: set[int] = set()
    if rows:
        term = as_str(rows[0].get("query_term"), term) or term
        positive_retmax = [as_int(row.get("retmax"), 0) for row in rows if as_int(row.get("retmax"), 0) > 0]
        retmax = positive_retmax[0] if positive_retmax else retmax
        existing_retstarts = {as_int(row.get("retstart"), -1) for row in rows}

    cursor = 0
    while len(missing) < missing_n:
        if cursor in existing_retstarts:
            cursor += retmax
            continue
        slug = slugify_query(term)
        missing.append(
            {
                "acquisition_id": f"OC133-NCBI-GEO-OFFICIAL-SNAPSHOT-{len(missing) + 1:04d}",
                "official_source": "NCBI E-utilities ESearch",
                "official_endpoint_url": official_esearch_url(term, cursor, retmax),
                "expected_local_snapshot_ref": (
                    f"validation/_raw/biology_ncbi_geo_{slug}_retstart_{cursor:06d}_retmax_{retmax}.json"
                ),
                "query_params": {
                    "db": "gds",
                    "term": term,
                    "retmode": "json",
                    "retstart": cursor,
                    "retmax": retmax,
                },
                "required_fields": [
                    "header.type",
                    "esearchresult.count",
                    "esearchresult.retmax",
                    "esearchresult.retstart",
                    "esearchresult.idlist",
                    "esearchresult.querytranslation",
                ],
                "target_policy": "retmax is a target field and must remain hidden from the scoring worker until the batch lock is closed",
                "no_send_lock": True,
            }
        )
        cursor += retmax
    return missing


def build_tamper_tests(rows: list[dict[str, Any]], snapshot_hashes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not rows:
        return [
            {
                "test_id": "biology-ncbi-batch-no-row-tamper-test",
                "description": "no rows exist to mutate",
                "passed": False,
            }
        ]
    mutated_rows = json.loads(json.dumps(rows, ensure_ascii=True))
    mutated_rows[0]["observed_value"] = as_float(mutated_rows[0].get("observed_value")) + 1.0
    for row in mutated_rows:
        row["row_hash"] = row_hash(row)
    return [
        {
            "test_id": "biology-ncbi-row-hashes-change-on-target-mutation",
            "description": "mutating a target value must alter row hashes",
            "passed": [row["row_hash"] for row in rows] != [row["row_hash"] for row in mutated_rows],
        },
        {
            "test_id": "biology-ncbi-snapshot-hashes-present",
            "description": "every parsed local NCBI/GEO snapshot has an LF-normalized SHA256",
            "passed": bool(snapshot_hashes) and all(row.get("snapshot_sha256") for row in snapshot_hashes),
        },
        {
            "test_id": "biology-ncbi-negative-controls-rejected",
            "description": "every row-level total-count negative control must be worse than the model residual",
            "passed": all(row.get("negative_control_rejected") is True for row in rows),
        },
    ]


def build_acquisition_packet(
    *,
    rows: list[dict[str, Any]],
    minimum_n: int,
    blockers: list[str],
    snapshot_refs: list[str],
    packet_requests: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    missing = missing_official_snapshots(rows, minimum_n, packet_requests)
    return {
        "schema_id": ACQUISITION_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "planner": PLANNER_REF,
        "status": "ACQUISITION_REQUIRED" if blockers else "ACQUISITION_NOT_REQUIRED",
        "current_snapshot_refs": snapshot_refs,
        "official_acquisition_run_root_ref": OFFICIAL_ACQUISITION_RUN_ROOT_REL,
        "source_acquisition_requests": packet_requests or [],
        "current_usable_row_total": len(rows),
        "minimum_n": minimum_n,
        "missing_n": max(0, minimum_n - len(rows)),
        "missing_official_snapshot_total": len(missing),
        "missing_official_snapshots": missing,
        "missing_protocol_material": [
            {
                "material_id": "OC133-NCBI-GEO-PRETARGET-LOCK-MANIFEST",
                "required": True,
                "description": "pre-target manifest freezing visible fields, formula, comparator baseline, row inclusion rule, residual metric, and target-hidden protocol before scoring",
            },
            {
                "material_id": "OC133-NCBI-GEO-TARGET-HIDDEN-MANIFEST",
                "required": True,
                "description": "manifest proving target retmax fields were hidden from formula/comparator selection until scoring",
            },
            {
                "material_id": "OC133-NCBI-GEO-COMPARATOR-REGISTRATION",
                "required": True,
                "description": "preregister the total-hit-count baseline and rejection criterion before scoring",
            },
        ],
        "blockers": blockers,
        "no_send": True,
        "publish_allowed": False,
        "journal_submissions_allowed": False,
        "registry_write_allowed": False,
        "release_promotion_allowed": False,
    }


def build_protocol(
    *,
    candidate_pack: dict[str, Any],
    rows: list[dict[str, Any]],
    blockers: list[str],
    source: dict[str, Any],
    minimum_n: int,
    snapshot_hashes: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "schema_id": PROTOCOL_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "planner": PLANNER_REF,
        "requirements_ref": REQUIREMENTS_REL,
        "candidate_pack_ref": CANDIDATE_PACK_REL,
        "candidate_pack_sha256": sha256_object(candidate_pack),
        "candidate_pack_hash_policy": PACK_HASH_POLICY,
        "tasks_ref": TASKS_REL,
        "report_ref": REPORT_REL,
        "acquisition_packet_ref": ACQUISITION_REL,
        "snapshot_hashes": snapshot_hashes,
        "source_separation_claim": source,
        "minimum_n": minimum_n,
        "candidate_n": len(rows),
        "criteria": {
            "n_at_least_minimum": len(rows) >= minimum_n,
            "source_separation_mode_allowed": source.get("mode") in {"target_blind", "prospective"},
            "pre_target_lock_required": source.get("pre_target_lock") is True,
            "target_hidden_until_scoring_required": source.get("target_hidden_until_scoring") is True,
            "comparator_preregistered_required": bool(rows)
            and all(row.get("comparator_pre_registered") is True for row in rows),
            "negative_controls_rejected_required": bool(rows)
            and all(row.get("negative_control_rejected") is True for row in rows),
            "official_ncbi_geo_provenance_required": bool(rows)
            and all(row.get("official_source_confirmed") is True for row in rows),
        },
        "required_protocol_steps": [
            "discover only local raw/pinned NCBI/GEO snapshots inside the public repo",
            "hash every raw snapshot with LF-normalized SHA256 before scoring",
            "freeze source separation, visible fields, target fields, comparator, residual metric, negative controls, and falsifiers before scoring",
            "construct one row per official NCBI/GEO ESearch snapshot record",
            "score retmax/page-size reconstruction from visible idlist length only",
            "compare against the preregistered GEO total-hit-count baseline",
            "block grand_toe_support_allowed unless N>=20 and every strict criterion passes",
            "emit acquisition-ready missing official snapshots when current raw data are too thin",
        ],
        "blockers": blockers,
        "no_send": True,
        "publish_allowed": False,
    }


def build_tasks(
    *,
    rows: list[dict[str, Any]],
    blockers: list[str],
    snapshot_hashes: list[dict[str, Any]],
    source: dict[str, Any],
    minimum_n: int,
) -> dict[str, Any]:
    return {
        "schema_id": TASKS_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "planner": PLANNER_REF,
        "snapshot_hash_policy": SNAPSHOT_HASH_POLICY,
        "row_hash_policy": ROW_HASH_POLICY,
        "minimum_n": minimum_n,
        "candidate_n": len(rows),
        "missing_n": max(0, minimum_n - len(rows)),
        "source_separation": source,
        "snapshot_manifest": snapshot_hashes,
        "rows": rows,
        "comparator_baselines": ordered_unique(
            [
                {
                    "name": row.get("comparator_baseline_name"),
                    "prediction_rule": row.get("comparator_prediction_rule"),
                    "pre_registered": row.get("comparator_pre_registered") is True,
                }
                for row in rows
            ]
        ),
        "residuals": residual_summary(rows),
        "negative_controls": [
            {
                "control_id": row["negative_control_id"],
                "description": row["negative_control_description"],
                "rejected": row.get("negative_control_rejected") is True,
            }
            for row in rows
        ],
        "falsifiers": ordered_unique([as_str(row.get("falsifier")) for row in rows if row.get("falsifier")]),
        "blockers": blockers,
    }


def build_report(
    *,
    candidate_pack: dict[str, Any],
    rows: list[dict[str, Any]],
    blockers: list[str],
    local_blockers: list[str],
    pack_gate_failures: list[str],
    final_pack_failures: list[str],
    tamper_tests: list[dict[str, Any]],
    source: dict[str, Any],
    minimum_n: int,
    snapshot_refs: list[str],
    snapshot_hashes: list[dict[str, Any]],
) -> dict[str, Any]:
    support_allowed = candidate_pack.get("grand_toe_support_allowed") is True
    return {
        "schema_id": REPORT_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "planner": PLANNER_REF,
        "support_policy": SUPPORT_POLICY,
        "requirements_ref": REQUIREMENTS_REL,
        "candidate_pack_ref": CANDIDATE_PACK_REL,
        "candidate_pack_sha256": sha256_object(candidate_pack),
        "candidate_pack_hash_policy": PACK_HASH_POLICY,
        "protocol_ref": PROTOCOL_REL,
        "tasks_ref": TASKS_REL,
        "acquisition_packet_ref": ACQUISITION_REL,
        "hashes_ref": HASHES_REL,
        "snapshot_refs": snapshot_refs,
        "snapshot_hashes": snapshot_hashes,
        "snapshot_hash_policy": SNAPSHOT_HASH_POLICY,
        "row_hash_policy": ROW_HASH_POLICY,
        "row_hashes": [row.get("row_hash") for row in rows],
        "minimum_n": minimum_n,
        "candidate_n": len(rows),
        "missing_n": max(0, minimum_n - len(rows)),
        "source_separation": source,
        "residuals": candidate_pack.get("residuals", {}),
        "comparator_baseline": candidate_pack.get("comparator_baseline", {}),
        "negative_controls": candidate_pack.get("negative_controls", []),
        "falsifiers": candidate_pack.get("falsifiers", []),
        "tamper_tests": tamper_tests,
        "local_blockers": local_blockers,
        "candidate_gate_failures": pack_gate_failures,
        "final_pack_failure_reasons": final_pack_failures,
        "blockers": blockers,
        "open_blocker_total": len(blockers),
        "blocked_total": len(blockers),
        "grand_toe_support_allowed": support_allowed,
        "verdict": "READY_FOR_PARENT_REGISTRY_REVIEW" if support_allowed else "BLOCKED_ACQUISITION_READY_NCBI_GEO_BATCH",
        "support_scope": "strict NCBI/GEO batch page-size reconstruction; not a biological mechanism superiority claim",
        "no_fabricated_pass_policy": SUPPORT_POLICY,
        "no_send": True,
        "publish_allowed": False,
        "journal_submissions_allowed": False,
        "registry_write_allowed": False,
        "release_promotion_allowed": False,
    }


def build_hashes(
    *,
    tasks: dict[str, Any],
    protocol: dict[str, Any],
    candidate_pack: dict[str, Any],
    report: dict[str, Any],
    acquisition_packet: dict[str, Any],
    readme: str,
    snapshot_hashes: list[dict[str, Any]],
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "schema_id": HASHES_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "hash_policy": PACK_HASH_POLICY,
        "artifact_hashes": [
            {"artifact_ref": TASKS_REL, "sha256": sha256_object(tasks), "hash_policy": PACK_HASH_POLICY},
            {"artifact_ref": PROTOCOL_REL, "sha256": sha256_object(protocol), "hash_policy": PACK_HASH_POLICY},
            {"artifact_ref": CANDIDATE_PACK_REL, "sha256": sha256_object(candidate_pack), "hash_policy": PACK_HASH_POLICY},
            {"artifact_ref": REPORT_REL, "sha256": sha256_object(report), "hash_policy": PACK_HASH_POLICY},
            {"artifact_ref": ACQUISITION_REL, "sha256": sha256_object(acquisition_packet), "hash_policy": PACK_HASH_POLICY},
            {"artifact_ref": README_REL, "sha256": sha256_text(readme), "hash_policy": "sha256 over UTF-8 README text"},
        ],
        "snapshot_hashes": snapshot_hashes,
        "row_hashes": [
            {
                "observation_id": row.get("observation_id"),
                "row_hash": row.get("row_hash"),
                "row_hash_policy": ROW_HASH_POLICY,
            }
            for row in rows
        ],
    }


def render_readme(report: dict[str, Any], acquisition_packet: dict[str, Any]) -> str:
    lines = [
        "# Biology NCBI/GEO Batch Factory",
        "",
        f"Verdict: `{report.get('verdict')}`",
        f"Grand TOE support allowed: `{report.get('grand_toe_support_allowed')}`",
        f"Rows: `{report.get('candidate_n')}`",
        f"Minimum N: `{report.get('minimum_n')}`",
        f"Missing official snapshots: `{acquisition_packet.get('missing_official_snapshot_total')}`",
        "",
        "## Open blockers",
    ]
    blockers = report.get("blockers", [])
    if blockers:
        lines.extend(f"- `{blocker}`" for blocker in blockers)
    else:
        lines.append("- `none`")
    lines.extend(
        [
            "",
            "## No-Send Locks",
            f"- `no_send`: `{report.get('no_send')}`",
            f"- `publish_allowed`: `{report.get('publish_allowed')}`",
            f"- `registry_write_allowed`: `{report.get('registry_write_allowed')}`",
            "",
            "## Acquisition",
        ]
    )
    for item in acquisition_packet.get("missing_official_snapshots", [])[:5]:
        lines.append(f"- `{item['expected_local_snapshot_ref']}` from `{item['official_endpoint_url']}`")
    remaining = max(0, len(acquisition_packet.get("missing_official_snapshots", [])) - 5)
    if remaining:
        lines.append(f"- `{remaining}` additional official snapshot requests listed in the acquisition packet")
    return "\n".join(lines) + "\n"


def build_payload(root: Path | None = None, snapshot_refs: list[str] | None = None) -> dict[str, Any]:
    root = (root or repo_root()).resolve()
    requirements, requirement_failures = load_requirements(root)
    minimum_n = as_int(requirements.get("minimum_per_domain_n"), 20)
    discovered_refs = discover_snapshot_refs(root, snapshot_refs)
    packet_requests = load_packet_requests(root)

    loaded_snapshots = [load_snapshot(root, ref) for ref in discovered_refs]
    official_snapshots: list[dict[str, Any]] = []
    official_failures: list[str] = []
    if snapshot_refs is None:
        official_snapshots, official_failures = load_official_acquisition_snapshots(root, packet_requests)
        loaded_snapshots.extend(official_snapshots)
        discovered_refs = ordered_unique([*discovered_refs, *[item["ref"] for item in official_snapshots]])
    snapshot_hashes = [
        {
            "snapshot_ref": item["ref"],
            "snapshot_sha256": item["sha256"],
            "source_snapshot_hash": item["sha256"],
            "snapshot_hash_policy": item.get("acquisition", {}).get("hash_policy", SNAPSHOT_HASH_POLICY),
            "snapshot_byte_count": item["byte_count"],
            "parsed": not item["failures"],
            "failures": item["failures"],
            "acquisition_id": item.get("acquisition", {}).get("acquisition_id", ""),
            "expected_local_snapshot_ref": item.get("acquisition", {}).get("expected_local_snapshot_ref", ""),
            "lock_ref": item.get("acquisition", {}).get("lock_ref", ""),
            "declared_before_scoring_lock": item.get("acquisition", {}).get("declared_before_scoring_lock") is True,
        }
        for item in loaded_snapshots
    ]

    rows: list[dict[str, Any]] = []
    local_blockers: list[str] = [*requirement_failures, *official_failures]
    source_candidates: list[dict[str, Any]] = []
    record_index = 0
    for snapshot in loaded_snapshots:
        local_blockers.extend(snapshot["failures"])
        payload = snapshot.get("payload")
        acquisition = dict_or_empty(snapshot.get("acquisition"))
        if payload is None:
            continue
        for record, source_candidate, comparator, provenance in iter_payload_records(payload):
            if acquisition:
                source_candidate = {
                    "mode": "official_readonly_snapshot_replay",
                    "kind": "official_readonly_acquisition_lock",
                    "pre_target_lock": True,
                    "target_hidden_until_scoring": False,
                    "declared_before_scoring": True,
                    "training_sources": [f"{ACQUISITION_REL}::visible_fields(retstart,idlist,querytranslation)"],
                    "target_sources": [f"{ACQUISITION_REL}::target_field(retmax)"],
                    "training_manifest_sha256": "",
                    "target_manifest_sha256": "",
                }
            source_candidates.append(source_candidate)
            record_index += 1
            row, row_failures = build_row(
                record=record,
                source_ref=snapshot["ref"],
                source_sha256=snapshot["sha256"],
                record_index=record_index,
                comparator=comparator,
                provenance=provenance,
                acquisition=acquisition,
            )
            local_blockers.extend(row_failures)
            if row is not None:
                rows.append(row)

    if not discovered_refs:
        local_blockers.append("NO_LOCAL_NCBI_GEO_SNAPSHOTS_DISCOVERED")
    if loaded_snapshots and not rows:
        local_blockers.append("NO_SCORABLE_NCBI_GEO_ESEARCH_ROWS")

    source, source_selection_failures = select_source_separation(source_candidates)
    local_blockers.extend(source_selection_failures)
    local_blockers.extend(validate_source_separation(source, requirements))
    local_blockers.extend(validate_rows(rows))

    if len(rows) < minimum_n:
        local_blockers.append(f"N_BELOW_MINIMUM::{len(rows)}/{minimum_n}")
        local_blockers.append("CURRENT_RAW_DATA_TOO_THIN_FOR_NCBI_GEO_BATCH")
    if residual_summary(rows)["superiority_margin"] <= 0:
        local_blockers.append("RESIDUAL_SUPERIORITY_NOT_MET")

    local_blockers = ordered_unique(local_blockers)
    gate_pack = build_pack(rows, source, support_allowed=True)
    pack_gate_failures = grand_factory.pack_failure_reasons(gate_pack, requirements)
    support_allowed = not ordered_unique([*local_blockers, *pack_gate_failures])
    candidate_pack = build_pack(rows, source, support_allowed=support_allowed)
    final_pack_failures = grand_factory.pack_failure_reasons(candidate_pack, requirements)
    blockers = ordered_unique([*local_blockers, *pack_gate_failures])
    if not support_allowed:
        blockers = ordered_unique([*blockers, "GRAND_TOE_SUPPORT_NOT_ALLOWED"])

    tamper_tests = build_tamper_tests(rows, snapshot_hashes)
    tasks = build_tasks(rows=rows, blockers=blockers, snapshot_hashes=snapshot_hashes, source=source, minimum_n=minimum_n)
    acquisition_packet = build_acquisition_packet(
        rows=rows,
        minimum_n=minimum_n,
        blockers=blockers,
        snapshot_refs=discovered_refs,
        packet_requests=packet_requests,
    )
    protocol = build_protocol(
        candidate_pack=candidate_pack,
        rows=rows,
        blockers=blockers,
        source=source,
        minimum_n=minimum_n,
        snapshot_hashes=snapshot_hashes,
    )
    report = build_report(
        candidate_pack=candidate_pack,
        rows=rows,
        blockers=blockers,
        local_blockers=local_blockers,
        pack_gate_failures=pack_gate_failures,
        final_pack_failures=final_pack_failures,
        tamper_tests=tamper_tests,
        source=source,
        minimum_n=minimum_n,
        snapshot_refs=discovered_refs,
        snapshot_hashes=snapshot_hashes,
    )
    readme = render_readme(report, acquisition_packet)
    hashes = build_hashes(
        tasks=tasks,
        protocol=protocol,
        candidate_pack=candidate_pack,
        report=report,
        acquisition_packet=acquisition_packet,
        readme=readme,
        snapshot_hashes=snapshot_hashes,
        rows=rows,
    )

    return {
        "tasks": tasks,
        "protocol": protocol,
        "candidate_pack": candidate_pack,
        "report": report,
        "acquisition_packet": acquisition_packet,
        "hashes": hashes,
        "readme": readme,
    }


def write_outputs(root: Path | None = None, snapshot_refs: list[str] | None = None) -> dict[str, Any]:
    root = (root or repo_root()).resolve()
    payload = build_payload(root, snapshot_refs=snapshot_refs)
    write_json(root / TASKS_REL, payload["tasks"])
    write_json(root / PROTOCOL_REL, payload["protocol"])
    write_json(root / CANDIDATE_PACK_REL, payload["candidate_pack"])
    write_json(root / REPORT_REL, payload["report"])
    write_json(root / ACQUISITION_REL, payload["acquisition_packet"])
    write_json(root / HASHES_REL, payload["hashes"])
    write_text(root / README_REL, payload["readme"])
    return payload


def check_stored(root: Path | None = None, snapshot_refs: list[str] | None = None) -> list[str]:
    root = (root or repo_root()).resolve()
    expected = build_payload(root, snapshot_refs=snapshot_refs)
    checks = [
        (TASKS_REL, expected["tasks"]),
        (PROTOCOL_REL, expected["protocol"]),
        (CANDIDATE_PACK_REL, expected["candidate_pack"]),
        (REPORT_REL, expected["report"]),
        (ACQUISITION_REL, expected["acquisition_packet"]),
        (HASHES_REL, expected["hashes"]),
    ]
    failures: list[str] = []
    for rel_path, payload in checks:
        path = root / rel_path
        if not path.exists():
            failures.append(f"missing::{rel_path}")
            continue
        if read_json(path) != payload:
            failures.append(f"mismatch::{rel_path}")
    readme_path = root / README_REL
    if not readme_path.exists():
        failures.append(f"missing::{README_REL}")
    elif readme_path.read_text(encoding="utf-8") != expected["readme"]:
        failures.append(f"mismatch::{README_REL}")
    return failures


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build strict OC133 biology NCBI/GEO batch artifacts.")
    parser.add_argument("--root", default=str(repo_root()), help="repository root")
    parser.add_argument("--snapshot-ref", action="append", default=None, help="explicit local NCBI/GEO snapshot ref")
    parser.add_argument("--write", action="store_true", help="write artifacts")
    parser.add_argument("--check", action="store_true", help="check persisted artifacts")
    parser.add_argument("--allow-blocked-exit-zero", action="store_true", help="exit zero when the honest result is blocked")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    if args.check:
        failures = check_stored(root, snapshot_refs=args.snapshot_ref)
        if failures:
            for failure in failures:
                print(f"ERROR: {failure}")
            return 1
        print(json.dumps({"status": "ok", "checked": [TASKS_REL, PROTOCOL_REL, CANDIDATE_PACK_REL, REPORT_REL, ACQUISITION_REL, HASHES_REL, README_REL]}, indent=2))
        return 0

    payload = write_outputs(root, snapshot_refs=args.snapshot_ref) if args.write else build_payload(root, snapshot_refs=args.snapshot_ref)
    print(json.dumps(payload["report"], ensure_ascii=True, indent=2))
    if payload["report"].get("grand_toe_support_allowed") is not True and not args.allow_blocked_exit_zero:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
