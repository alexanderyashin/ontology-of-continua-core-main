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
from tools import oc133_target_projection_lock_factory as target_projection_factory


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
TARGET_PROJECTION_DECLARATION_REL = f"{OUTPUT_ROOT_REL}/OC133_BIOLOGY_NCBI_BATCH_TARGET_PROJECTION_DECLARATION.json"
VISIBLE_PROJECTION_LOCK_REL = f"{OUTPUT_ROOT_REL}/OC133_BIOLOGY_NCBI_BATCH_VISIBLE_PROJECTION_LOCK.json"
PREDICTION_MATERIALIZATION_LOCK_REL = (
    f"{OUTPUT_ROOT_REL}/OC133_BIOLOGY_NCBI_BATCH_PREDICTION_MATERIALIZATION_LOCK.json"
)
TARGET_PROJECTION_LOCK_REL = f"{OUTPUT_ROOT_REL}/OC133_BIOLOGY_NCBI_BATCH_TARGET_PROJECTION_LOCK.json"
LEGACY_SEED_LOCK_ROOT_REL = f"{OUTPUT_ROOT_REL}/legacy_seed_locks"
LEGACY_SEED_LOCK_SCHEMA_ID = "OC133_BIOLOGY_NCBI_LEGACY_SEED_TARGET_PROJECTION_LOCK_v1"

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
BIOLOGY_TARGET_LOCK_ID = "OC133-BIOLOGY-NCBI-BATCH-TARGET-PROJECTION-LOCK"
BIOLOGY_VISIBLE_FIELDS = [
    "esearchresult.idlist",
    "esearchresult.retstart",
    "esearchresult.querytranslation",
]
BIOLOGY_TARGET_FIELDS = ["esearchresult.retmax"]
PROJECTION_NO_SEND_LOCKS = target_projection_factory.NO_SEND_LOCKS
SUPPORT_POLICY = (
    "NCBI/GEO page-size reconstruction is bounded acquisition QA only. It may verify official bytes, "
    "target-projection locks, hashes, residuals, and negative controls, but it cannot close grand biology "
    "support. Grand biology remains blocked until a successor pack contains biological target rows, "
    "non-pagination biological comparator evidence, uncertainty/residuals, negative controls, falsifiers, "
    "and source hashes."
)
PAGINATION_QA_BLOCKER = "BIOLOGY_PAGINATION_QA_NOT_GRAND_EVIDENCE"


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
        legacy_status = dict_or_empty(acquisition.get("target_projection_lock"))
        legacy_upgrade_invalid = acquisition.get("legacy_seed_upgrade") is True and legacy_status.get("verified") is not True
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
            "pre_registered": False if legacy_upgrade_invalid else comparator.get("pre_registered", True),
        }
    official_ok, official_source, official_url = provenance_status(provenance, source_ref)
    comparator_pre_registered = comparator.get("pre_registered") is True
    row_id = biology_row_id(source_ref, record_index, term)
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
    if acquisition.get("legacy_seed_upgrade") is True:
        target_projection_status = dict_or_empty(acquisition.get("target_projection_lock"))
        row["legacy_seed_upgrade"] = True
        row["target_projection_lock_verified"] = target_projection_status.get("verified") is True
        row["target_projection_lock_refs"] = target_projection_status.get("refs", {})
        row["target_projection_lock_hashes"] = target_projection_status.get("hashes", {})
        row["target_projection_lock_status"] = target_projection_status
    row["row_hash"] = row_hash(row)
    row["row_hash_policy"] = ROW_HASH_POLICY
    return row, idlist_failures


def biology_row_id(source_ref: str, record_index: int, term: str) -> str:
    row_id_hash = sha256_object({"source_ref": source_ref, "record_index": record_index, "term": term})[:12].upper()
    return f"BIOLOGY-NCBI-GEO-BATCH-{record_index:04d}-{row_id_hash}"


def comparator_preregistration_contract() -> dict[str, Any]:
    contract = {
        "name": "GEO total-hit-count page-size negative control",
        "prediction_rule": "use esearchresult.count as the retmax prediction",
        "pre_registered": True,
        "residual_metric": "absolute_error_retmax",
        "rejection_criterion": "comparator_residual must be strictly greater than model_residual",
        "declared_before_scoring": True,
    }
    return {**contract, "baseline_sha256": sha256_object(contract)}


def legacy_seed_metadata(record: dict[str, Any]) -> dict[str, Any]:
    for key in ("legacy_seed_lock", "legacy_seed_target_projection_lock", "target_projection_seed_lock"):
        value = record.get(key)
        if isinstance(value, dict):
            return value
    return {}


def is_legacy_seed_candidate(
    *,
    source_ref: str,
    record: dict[str, Any],
    acquisition: dict[str, Any],
) -> bool:
    if acquisition:
        return False
    esearch = esearch_result(record)
    if not esearch:
        return False
    return source_ref == DEFAULT_SNAPSHOT_REF or bool(legacy_seed_metadata(record))


def legacy_seed_lock_id(source_ref: str, source_sha256: str, record_index: int, record: dict[str, Any]) -> str:
    esearch = esearch_result(record)
    term = as_str(esearch.get("querytranslation"), DEFAULT_GEO_TERM) or DEFAULT_GEO_TERM
    token = sha256_object(
        {
            "source_ref": source_ref,
            "source_sha256": source_sha256,
            "record_index": record_index,
            "term": term,
            "visible_fields": BIOLOGY_VISIBLE_FIELDS,
            "target_fields": BIOLOGY_TARGET_FIELDS,
        }
    )[:16].upper()
    return f"OC133-BIOLOGY-NCBI-LEGACY-SEED-{token}"


def build_legacy_seed_projection_status(
    *,
    source_ref: str,
    source_sha256: str,
    record_index: int,
    record: dict[str, Any],
) -> dict[str, Any]:
    esearch = esearch_result(record)
    idlist, idlist_failures = parse_idlist(esearch)
    retstart = as_int(esearch.get("retstart"), 0)
    retmax = as_int(esearch.get("retmax"), len(idlist))
    count = as_int(esearch.get("count"), retmax)
    term = as_str(esearch.get("querytranslation"), DEFAULT_GEO_TERM) or DEFAULT_GEO_TERM
    row_id = biology_row_id(source_ref, record_index, term)
    lock_id = legacy_seed_lock_id(source_ref, source_sha256, record_index, record)
    lock_ref = f"{LEGACY_SEED_LOCK_ROOT_REL}/{lock_id}.lock.json"
    declaration_ref = f"{LEGACY_SEED_LOCK_ROOT_REL}/{lock_id}.declaration.json"
    visible_ref = f"{LEGACY_SEED_LOCK_ROOT_REL}/{lock_id}.visible_projection_lock.json"
    prediction_ref = f"{LEGACY_SEED_LOCK_ROOT_REL}/{lock_id}.prediction_materialization_lock.json"
    target_ref = f"{LEGACY_SEED_LOCK_ROOT_REL}/{lock_id}.target_projection_lock.json"
    comparator_contract = comparator_preregistration_contract()
    blockers = [f"LEGACY_SEED_{failure}::{source_ref}::{record_index}" for failure in idlist_failures]
    if retmax < 0:
        blockers.append(f"LEGACY_SEED_TARGET_INVALID::{source_ref}::{record_index}")
    official_url = official_esearch_url(term, retstart, retmax)
    declaration = {
        "schema_id": "OC133_BIOLOGY_NCBI_LEGACY_SEED_TARGET_PROJECTION_DECLARATION_v1",
        "release_id": RELEASE_ID,
        "generated_by": PLANNER_REF,
        "lock_id": lock_id,
        "declared_before_scoring": True,
        "source_snapshot_ref": source_ref,
        "source_snapshot_sha256": source_sha256,
        "row_index": record_index,
        "row_id": row_id,
        "visible_fields": BIOLOGY_VISIBLE_FIELDS,
        "target_fields": BIOLOGY_TARGET_FIELDS,
        "model_declaration": {
            "kind": "geo_esearch_page_size_reconstruction",
            "formula": "len(esearchresult.idlist)",
            "visible_inputs": BIOLOGY_VISIBLE_FIELDS,
        },
        "comparator_declaration": {
            "kind": "geo_total_hit_count_negative_control",
            "baseline_sha256": comparator_contract["baseline_sha256"],
        },
        "residual_metric": "absolute_error_retmax",
        "official_provenance_classification": {
            "official_source": "NCBI E-utilities ESearch",
            "official_url": official_url,
            "classification_method": "deterministically reconstructed from raw ESearch querytranslation, retstart, and retmax fields",
        },
        "locks": dict(PROJECTION_NO_SEND_LOCKS),
        "support_policy": "Legacy seed upgrade proves target-blind row projection only; grand support remains gated by all biology requirements.",
    }
    declaration_sha = sha256_object(declaration)
    visible = {
        "esearchresult.idlist": [str(item) for item in idlist],
        "esearchresult.retstart": retstart,
        "esearchresult.querytranslation": term,
    }
    target = {"esearchresult.retmax": retmax}
    visible_row = {"row_index": record_index, "row_id": row_id, "visible": visible}
    target_row = {"row_index": record_index, "row_id": row_id, "target": target}
    visible_row_sha = sha256_object(visible_row)
    target_row_sha = sha256_object(target_row)
    visible_projection_lock = {
        "schema_id": target_projection_factory.VISIBLE_LOCK_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "lock_id": lock_id,
        "declaration_ref": declaration_ref,
        "snapshot_ref": source_ref,
        "snapshot_sha256": source_sha256,
        "declaration_sha256": declaration_sha,
        "visible_fields": BIOLOGY_VISIBLE_FIELDS,
        "row_count": 1,
        "rows": [{**visible_row, "visible_row_sha256": visible_row_sha}],
        "locks": dict(PROJECTION_NO_SEND_LOCKS),
    }
    visible_sha = sha256_object(visible_projection_lock)
    prediction_materialization_lock = {
        "schema_id": target_projection_factory.PREDICTION_LOCK_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "lock_id": lock_id,
        "declaration_ref": declaration_ref,
        "declaration_sha256": declaration_sha,
        "visible_projection_sha256": visible_sha,
        "model_declaration": declaration["model_declaration"],
        "comparator_declaration": declaration["comparator_declaration"],
        "prediction_rows": [
            {
                "row_index": record_index,
                "row_id": row_id,
                "visible_row_sha256": visible_row_sha,
                "declaration_sha256": declaration_sha,
                "model_prediction": float(len(idlist)),
                "comparator_prediction": float(count),
                "target_opened": False,
            }
        ],
        "algorithmic_target_separation": {
            "prediction_inputs": "raw ESearch idlist, retstart, and querytranslation visible projection plus locked declarations only",
            "target_projection_read_before_prediction_materialization": False,
            "target_opened_after_prediction_materialization": True,
        },
        "locks": dict(PROJECTION_NO_SEND_LOCKS),
    }
    prediction_sha = sha256_object(prediction_materialization_lock)
    target_projection_lock = {
        "schema_id": target_projection_factory.TARGET_LOCK_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "lock_id": lock_id,
        "declaration_ref": declaration_ref,
        "snapshot_ref": source_ref,
        "snapshot_sha256": source_sha256,
        "declaration_sha256": declaration_sha,
        "visible_projection_sha256": visible_sha,
        "prediction_materialization_sha256": prediction_sha,
        "target_fields": BIOLOGY_TARGET_FIELDS,
        "row_count": 1,
        "rows": [
            {
                **target_row,
                "target_row_sha256": target_row_sha,
                "source_row_sha256": sha256_object(record),
            }
        ],
        "target_opened_after_prediction_materialization": True,
        "locks": dict(PROJECTION_NO_SEND_LOCKS),
    }
    target_sha = sha256_object(target_projection_lock)
    seed_lock = {
        "schema_id": LEGACY_SEED_LOCK_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "generated_by": PLANNER_REF,
        "lock_id": lock_id,
        "lock_ref": lock_ref,
        "source_snapshot_ref": source_ref,
        "source_snapshot_sha256": source_sha256,
        "record_index": record_index,
        "row_id": row_id,
        "official_source": "NCBI E-utilities ESearch",
        "official_url": official_url,
        "declaration_ref": declaration_ref,
        "declaration_sha256": declaration_sha,
        "visible_projection_lock_ref": visible_ref,
        "visible_projection_lock_sha256": visible_sha,
        "prediction_materialization_lock_ref": prediction_ref,
        "prediction_materialization_lock_sha256": prediction_sha,
        "target_projection_lock_ref": target_ref,
        "target_projection_lock_sha256": target_sha,
        "comparator_baseline": comparator_contract,
        "locks": dict(PROJECTION_NO_SEND_LOCKS),
        "support_policy": "Legacy seed upgrade proves target-blind row projection only; grand support remains gated by all biology requirements.",
    }
    seed_lock_sha = sha256_object(seed_lock)
    status = {
        "required": True,
        "verified": not blockers,
        "valid": not blockers,
        "source_separation_derived": True,
        "source_kind": "legacy_seed_auto_projection",
        "generated_by": PLANNER_REF,
        "standard_factory": PLANNER_REF,
        "refs": {
            "legacy_seed_lock_ref": lock_ref,
            "declaration_ref": declaration_ref,
            "visible_projection_lock_ref": visible_ref,
            "prediction_materialization_lock_ref": prediction_ref,
            "target_projection_lock_ref": target_ref,
        },
        "hashes": {
            "legacy_seed_lock_sha256": seed_lock_sha,
            "declaration_sha256": declaration_sha,
            "snapshot_sha256": source_sha256,
            "visible_projection_lock_sha256": visible_sha,
            "prediction_materialization_lock_sha256": prediction_sha,
            "target_projection_lock_sha256": target_sha,
            "comparator_baseline_sha256": comparator_contract["baseline_sha256"],
        },
        "visible_fields": BIOLOGY_VISIBLE_FIELDS,
        "target_fields": BIOLOGY_TARGET_FIELDS,
        "blockers": blockers,
        "locks": dict(PROJECTION_NO_SEND_LOCKS),
    }
    return {
        "lock_ref": lock_ref,
        "lock_sha256": seed_lock_sha,
        "lock_payload": seed_lock,
        "artifacts": {
            declaration_ref: declaration,
            visible_ref: visible_projection_lock,
            prediction_ref: prediction_materialization_lock,
            target_ref: target_projection_lock,
            lock_ref: seed_lock,
        },
        "target_projection_lock": status,
        "comparator_baseline": comparator_contract,
        "official_url": official_url,
        "blockers": blockers,
    }


def validate_declared_legacy_seed_metadata(
    metadata: dict[str, Any],
    upgrade: dict[str, Any],
    *,
    source_ref: str,
    record_index: int,
) -> list[str]:
    if not metadata:
        return []
    status = dict_or_empty(upgrade.get("target_projection_lock"))
    refs = dict_or_empty(status.get("refs"))
    hashes = dict_or_empty(status.get("hashes"))
    failures: list[str] = []
    expected_lock_ref = as_str(metadata.get("lock_ref"), as_str(metadata.get("legacy_seed_lock_ref")))
    if expected_lock_ref and expected_lock_ref != as_str(upgrade.get("lock_ref")):
        failures.append(f"LEGACY_SEED_LOCK_REF_MISMATCH::{source_ref}::{record_index}")
    expected_lock_sha = as_str(metadata.get("lock_sha256"), as_str(metadata.get("legacy_seed_lock_sha256")))
    if expected_lock_sha and expected_lock_sha != as_str(upgrade.get("lock_sha256")):
        failures.append(f"LEGACY_SEED_LOCK_HASH_MISMATCH::{source_ref}::{record_index}")
    expected_comparator_sha = as_str(metadata.get("comparator_baseline_sha256"))
    if expected_comparator_sha and expected_comparator_sha != as_str(hashes.get("comparator_baseline_sha256")):
        failures.append(f"LEGACY_SEED_COMPARATOR_BASELINE_STALE::{source_ref}::{record_index}")
    ref_map = (
        ("declaration_ref", "declaration_sha256", "DECLARATION"),
        ("visible_projection_lock_ref", "visible_projection_lock_sha256", "VISIBLE_PROJECTION_LOCK"),
        ("prediction_materialization_lock_ref", "prediction_materialization_lock_sha256", "PREDICTION_MATERIALIZATION_LOCK"),
        ("target_projection_lock_ref", "target_projection_lock_sha256", "TARGET_PROJECTION_LOCK"),
    )
    for ref_key, hash_key, label in ref_map:
        expected_ref = as_str(metadata.get(ref_key))
        expected_sha = as_str(metadata.get(hash_key))
        if expected_ref and expected_ref != as_str(refs.get(ref_key)):
            failures.append(f"LEGACY_SEED_{label}_REF_MISMATCH::{source_ref}::{record_index}")
        if expected_sha and expected_sha != as_str(hashes.get(hash_key)):
            failures.append(f"LEGACY_SEED_{label}_HASH_MISMATCH::{source_ref}::{record_index}")
    declared_visible_fields = list_of_strings(metadata.get("visible_fields"))
    if declared_visible_fields:
        if declared_visible_fields != BIOLOGY_VISIBLE_FIELDS:
            failures.append(f"LEGACY_SEED_VISIBLE_FIELDS_UNEXPECTED::{source_ref}::{record_index}")
        if set(declared_visible_fields) & set(BIOLOGY_TARGET_FIELDS):
            failures.append(f"LEGACY_SEED_TARGET_FIELD_IN_VISIBLE_PROJECTION::{source_ref}::{record_index}")
    if "locks" in metadata and dict_or_empty(metadata.get("locks")) != PROJECTION_NO_SEND_LOCKS:
        failures.append(f"LEGACY_SEED_NO_SEND_LOCKS_MISSING_OR_WEAK::{source_ref}::{record_index}")
    return failures


def legacy_seed_upgrade_for_record(
    *,
    source_ref: str,
    source_sha256: str,
    record_index: int,
    record: dict[str, Any],
    acquisition: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], list[str]]:
    if not is_legacy_seed_candidate(source_ref=source_ref, record=record, acquisition=acquisition):
        return acquisition, {}, {}, []
    upgrade = build_legacy_seed_projection_status(
        source_ref=source_ref,
        source_sha256=source_sha256,
        record_index=record_index,
        record=record,
    )
    metadata_failures = validate_declared_legacy_seed_metadata(
        legacy_seed_metadata(record),
        upgrade,
        source_ref=source_ref,
        record_index=record_index,
    )
    status = dict_or_empty(upgrade.get("target_projection_lock"))
    blockers = ordered_unique([*list_of_strings(status.get("blockers")), *metadata_failures])
    if blockers:
        status = {**status, "verified": False, "valid": False, "blockers": blockers}
        upgrade = {**upgrade, "target_projection_lock": status}
    source = (
        {
            "mode": "target_blind",
            "kind": "legacy_seed_target_projection_lock",
            "pre_target_lock": True,
            "target_hidden_until_scoring": True,
            "declared_before_scoring": True,
            "training_sources": [dict_or_empty(status.get("refs")).get("visible_projection_lock_ref", "")],
            "target_sources": [dict_or_empty(status.get("refs")).get("target_projection_lock_ref", "")],
            "training_manifest_sha256": dict_or_empty(status.get("hashes")).get("visible_projection_lock_sha256", ""),
            "target_manifest_sha256": dict_or_empty(status.get("hashes")).get("target_projection_lock_sha256", ""),
        }
        if status.get("verified") is True
        else {}
    )
    upgraded_acquisition = {
        "acquisition_id": as_str(dict_or_empty(status.get("refs")).get("legacy_seed_lock_ref")),
        "packet_ref": "",
        "packet_schema_id": "",
        "expected_local_snapshot_ref": source_ref,
        "official_endpoint_url": as_str(upgrade.get("official_url")),
        "lock_ref": as_str(upgrade.get("lock_ref")),
        "lock_sha256": as_str(upgrade.get("lock_sha256")),
        "declared_before_scoring_lock": status.get("verified") is True,
        "hash_policy": "sha256 over deterministic legacy seed target-projection contract",
        "required_fields": [*BIOLOGY_VISIBLE_FIELDS, *BIOLOGY_TARGET_FIELDS],
        "target_projection_lock": status,
        "legacy_seed_upgrade": True,
        "legacy_seed_artifacts": dict_or_empty(upgrade.get("artifacts")),
    }
    comparator = dict_or_empty(upgrade.get("comparator_baseline")) if status.get("verified") is True else {}
    return upgraded_acquisition, source, comparator, blockers


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


def target_projection_refs() -> dict[str, str]:
    return {
        "declaration_ref": (
            f"validation/heldout/target_projection_locks/declarations/biology_ncbi_batch/{BIOLOGY_TARGET_LOCK_ID}.json"
        ),
        "visible_lock_ref": (
            f"validation/heldout/target_projection_locks/locks/{BIOLOGY_TARGET_LOCK_ID}.visible_projection_lock.json"
        ),
        "prediction_lock_ref": (
            f"validation/heldout/target_projection_locks/locks/{BIOLOGY_TARGET_LOCK_ID}.prediction_materialization_lock.json"
        ),
        "target_lock_ref": (
            f"validation/heldout/target_projection_locks/locks/{BIOLOGY_TARGET_LOCK_ID}.target_projection_lock.json"
        ),
    }


def target_projection_refs_from_attachment(status: dict[str, Any]) -> dict[str, str]:
    refs = dict_or_empty(status.get("refs"))
    expected_refs = dict_or_empty(status.get("expected_refs"))
    return {
        "declaration_ref": as_str(refs.get("declaration_ref"), as_str(expected_refs.get("declaration_ref"))),
        "visible_lock_ref": as_str(
            refs.get("visible_projection_lock_ref"),
            as_str(refs.get("visible_lock_ref"), as_str(expected_refs.get("visible_lock_ref"))),
        ),
        "prediction_lock_ref": as_str(
            refs.get("prediction_materialization_lock_ref"),
            as_str(refs.get("prediction_lock_ref"), as_str(expected_refs.get("prediction_lock_ref"))),
        ),
        "target_lock_ref": as_str(
            refs.get("target_projection_lock_ref"),
            as_str(refs.get("target_lock_ref"), as_str(expected_refs.get("target_lock_ref"))),
        ),
    }


def packet_target_projection_lock(root: Path) -> dict[str, Any] | None:
    path = root / ACQUISITION_REL
    if not path.exists():
        return None
    try:
        packet = read_json(path)
    except Exception:
        return None
    if not isinstance(packet, dict) or "target_projection_lock" not in packet:
        return None
    status = dict_or_empty(packet.get("target_projection_lock"))
    hashes = dict_or_empty(status.get("hashes"))
    if not hashes:
        return None
    refs = target_projection_refs_from_attachment(status)
    if refs == target_projection_refs() and not as_str(hashes.get("snapshot_sha256")):
        return None
    return status


def projection_payload(row: dict[str, Any], fields: list[str]) -> dict[str, Any]:
    values = {
        "esearchresult.idlist": [str(item) for item in row.get("formula_inputs", {}).get("idlist", [])],
        "esearchresult.retstart": as_int(row.get("retstart")),
        "esearchresult.querytranslation": as_str(row.get("query_term")),
        "esearchresult.retmax": as_int(row.get("retmax"), as_int(row.get("observed_value"))),
    }
    return {field: values[field] for field in fields if field in values}


def normalized_projection(payload: Any, fields: list[str]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    normalized: dict[str, Any] = {}
    for field in fields:
        value = payload.get(field)
        if field == "esearchresult.idlist":
            normalized[field] = [str(item) for item in value] if isinstance(value, list) else []
        elif field in {"esearchresult.retstart", "esearchresult.retmax"}:
            normalized[field] = as_int(value)
        elif field == "esearchresult.querytranslation":
            normalized[field] = as_str(value)
        else:
            normalized[field] = value
    return normalized


def target_lock_locks_valid(payload: Any) -> bool:
    locks = payload.get("locks") if isinstance(payload, dict) else None
    return isinstance(locks, dict) and all(locks.get(key) is expected for key, expected in PROJECTION_NO_SEND_LOCKS.items())


def read_projection_artifact(root: Path, ref: str, failures: list[str]) -> dict[str, Any]:
    if not ref:
        failures.append("TARGET_PROJECTION_LOCK_ARTIFACT_REF_MISSING")
        return {}
    try:
        path = resolve_under_root(root, ref)
    except ValueError:
        failures.append(f"TARGET_PROJECTION_LOCK_ARTIFACT_REF_OUTSIDE_REPO::{ref}")
        return {}
    if not path.exists():
        failures.append(f"TARGET_PROJECTION_LOCK_ARTIFACT_MISSING::{ref}")
        return {}
    try:
        payload = read_json(path)
    except Exception as exc:
        failures.append(f"TARGET_PROJECTION_LOCK_ARTIFACT_PARSE_FAILED::{ref}::{exc.__class__.__name__}")
        return {}
    if not isinstance(payload, dict):
        failures.append(f"TARGET_PROJECTION_LOCK_ARTIFACT_NOT_OBJECT::{ref}")
        return {}
    return payload


def expected_hash_matches(declaration: dict[str, Any], key: str, actual: str, failures: list[str]) -> None:
    expected = as_str(declaration.get(key))
    if not expected:
        failures.append(f"TARGET_PROJECTION_LOCK_EXPECTED_HASH_MISSING::{key}")
    elif expected != actual:
        failures.append(f"TARGET_PROJECTION_LOCK_EXPECTED_HASH_MISMATCH::{key}")


def official_acquisition_id_from_ref(ref: str) -> str:
    name = Path(ref.replace("\\", "/")).stem
    if re.fullmatch(r"OC133-NCBI-GEO-OFFICIAL-SNAPSHOT-\d{4}", name):
        return name
    return ""


def projection_row_id(row: dict[str, Any]) -> str:
    return as_str(row.get("observation_id")) or as_str(row.get("acquisition_id"))


def projection_row_identity_candidates(row: dict[str, Any]) -> list[str]:
    return ordered_unique(
        [
            as_str(row.get("acquisition_id")),
            official_acquisition_id_from_ref(as_str(row.get("snapshot_ref"))),
            as_str(row.get("observation_id")),
        ]
    )


def projection_source_key(row: dict[str, Any]) -> tuple[str, str]:
    return as_str(row.get("snapshot_ref")), as_str(row.get("snapshot_sha256"), as_str(row.get("source_snapshot_hash")))


def snapshot_row_id(row: dict[str, Any]) -> str:
    return as_str(row.get("acquisition_id")) or as_str(row.get("observation_id"))


def snapshot_source_key(row: dict[str, Any]) -> tuple[str, str]:
    return as_str(row.get("source_snapshot_ref")), as_str(row.get("source_snapshot_sha256"))


def snapshot_projection_payload(row: dict[str, Any], fields: list[str]) -> dict[str, Any]:
    esearch = dict_or_empty(row.get("esearchresult"))
    values = {
        "esearchresult.idlist": [str(item) for item in esearch.get("idlist", [])] if isinstance(esearch.get("idlist"), list) else [],
        "esearchresult.retstart": as_int(esearch.get("retstart")),
        "esearchresult.querytranslation": as_str(esearch.get("querytranslation")),
        "esearchresult.retmax": as_int(esearch.get("retmax")),
    }
    return {field: values[field] for field in fields if field in values}


def projection_signature(row: dict[str, Any]) -> str:
    return sha256_object(
        {
            "visible": projection_payload(row, BIOLOGY_VISIBLE_FIELDS),
            "target": projection_payload(row, BIOLOGY_TARGET_FIELDS),
        }
    )


def snapshot_projection_signature(row: dict[str, Any]) -> str:
    return sha256_object(
        {
            "visible": snapshot_projection_payload(row, BIOLOGY_VISIBLE_FIELDS),
            "target": snapshot_projection_payload(row, BIOLOGY_TARGET_FIELDS),
        }
    )


def validate_packet_projection_hashes(
    status: dict[str, Any],
    *,
    declaration_hash: str,
    visible_sha256: str,
    prediction_sha256: str,
    target_sha256: str,
    failures: list[str],
) -> None:
    hashes = dict_or_empty(status.get("hashes"))
    expected = {
        "declaration_sha256": declaration_hash,
        "visible_projection_lock_sha256": visible_sha256,
        "prediction_materialization_lock_sha256": prediction_sha256,
        "target_projection_lock_sha256": target_sha256,
    }
    for key, actual in expected.items():
        declared = as_str(hashes.get(key))
        if not declared:
            failures.append(f"TARGET_PROJECTION_LOCK_PACKET_HASH_MISSING::{key}")
        elif declared != actual:
            failures.append(f"TARGET_PROJECTION_LOCK_PACKET_HASH_MISMATCH::{key}")


def packet_projection_refs_for_status(refs: dict[str, str], packet_status: dict[str, Any] | None) -> dict[str, str]:
    packet_refs = dict_or_empty(packet_status.get("refs")) if packet_status is not None else {}
    if packet_refs:
        return {key: as_str(value) for key, value in packet_refs.items()}
    return {
        "declaration_ref": refs["declaration_ref"],
        "visible_projection_lock_ref": refs["visible_lock_ref"],
        "prediction_materialization_lock_ref": refs["prediction_lock_ref"],
        "target_projection_lock_ref": refs["target_lock_ref"],
    }


def validate_projection_snapshot(
    root: Path,
    *,
    declaration: dict[str, Any],
    visible_lock: dict[str, Any],
    target_lock: dict[str, Any],
    rows: list[dict[str, Any]],
    packet_status: dict[str, Any] | None,
    failures: list[str],
) -> list[dict[str, Any]]:
    snapshot_ref = as_str(declaration.get("snapshot_ref"))
    if not snapshot_ref:
        return []
    try:
        snapshot_path = resolve_under_root(root, snapshot_ref)
    except ValueError:
        failures.append(f"TARGET_PROJECTION_SNAPSHOT_REF_OUTSIDE_REPO::{snapshot_ref}")
        return []
    if not snapshot_path.exists() or not snapshot_path.is_file():
        failures.append(f"TARGET_PROJECTION_SNAPSHOT_MISSING::{snapshot_ref}")
        return []
    snapshot_sha256 = sha256_bytes(snapshot_path.read_bytes())
    expected_snapshot_sha = as_str(declaration.get("expected_snapshot_sha256"))
    if expected_snapshot_sha and expected_snapshot_sha != snapshot_sha256:
        failures.append("TARGET_PROJECTION_SNAPSHOT_HASH_MISMATCH")
    for lock_payload, label in ((visible_lock, "VISIBLE_PROJECTION_LOCK"), (target_lock, "TARGET_PROJECTION_LOCK")):
        if as_str(lock_payload.get("snapshot_ref")) != snapshot_ref:
            failures.append(f"{label}_SNAPSHOT_REF_MISMATCH")
        if as_str(lock_payload.get("snapshot_sha256")) != snapshot_sha256:
            failures.append(f"{label}_SNAPSHOT_HASH_MISMATCH")
    if packet_status is not None:
        declared_packet_snapshot_sha = as_str(dict_or_empty(packet_status.get("hashes")).get("snapshot_sha256"))
        if not declared_packet_snapshot_sha:
            failures.append("TARGET_PROJECTION_LOCK_PACKET_HASH_MISSING::snapshot_sha256")
        elif declared_packet_snapshot_sha != snapshot_sha256:
            failures.append("TARGET_PROJECTION_LOCK_PACKET_HASH_MISMATCH::snapshot_sha256")

    try:
        snapshot_payload = read_json(snapshot_path)
    except Exception as exc:
        failures.append(f"TARGET_PROJECTION_SNAPSHOT_PARSE_FAILED::{exc.__class__.__name__}")
        return []
    snapshot_rows = snapshot_payload.get("rows") if isinstance(snapshot_payload, dict) else None
    if not isinstance(snapshot_rows, list):
        return []
    return [item for item in snapshot_rows if isinstance(item, dict)]


def add_unique_binding(index: dict[Any, dict[str, Any] | None], key: Any, row: dict[str, Any]) -> None:
    if not key or (isinstance(key, tuple) and not all(key)):
        return
    if key in index:
        index[key] = None
    else:
        index[key] = row


def unique_bound(index: dict[Any, dict[str, Any] | None], key: Any) -> dict[str, Any] | None:
    row = index.get(key)
    return row if isinstance(row, dict) else None


def build_snapshot_binding_indexes(snapshot_rows: list[dict[str, Any]]) -> dict[str, dict[Any, dict[str, Any] | None]]:
    by_id: dict[Any, dict[str, Any] | None] = {}
    by_source: dict[Any, dict[str, Any] | None] = {}
    by_projection: dict[Any, dict[str, Any] | None] = {}
    for row in snapshot_rows:
        add_unique_binding(by_id, snapshot_row_id(row), row)
        add_unique_binding(by_source, snapshot_source_key(row), row)
        add_unique_binding(by_projection, snapshot_projection_signature(row), row)
    return {"id": by_id, "source": by_source, "projection": by_projection}


def bind_projection_snapshot_row(
    row: dict[str, Any],
    snapshot_indexes: dict[str, dict[Any, dict[str, Any] | None]],
) -> dict[str, Any] | None:
    for candidate in projection_row_identity_candidates(row):
        bound = unique_bound(snapshot_indexes["id"], candidate)
        if bound is not None:
            return bound
    bound = unique_bound(snapshot_indexes["source"], projection_source_key(row))
    if bound is not None:
        return bound
    return unique_bound(snapshot_indexes["projection"], projection_signature(row))


def projection_lock_row_id(row: dict[str, Any], snapshot_row: dict[str, Any] | None) -> str:
    if snapshot_row is not None:
        snapshot_id = snapshot_row_id(snapshot_row)
        if snapshot_id:
            return snapshot_id
    for candidate in projection_row_identity_candidates(row):
        if candidate:
            return candidate
    return "unknown"


def load_target_projection_lock_source(
    root: Path,
    rows: list[dict[str, Any]],
    packet_status: dict[str, Any] | None = None,
) -> dict[str, Any]:
    refs = target_projection_refs_from_attachment(packet_status) if packet_status is not None else target_projection_refs()
    failures: list[str] = []
    source_kind = "packet_attachment" if packet_status is not None else "legacy_artifacts"
    if not rows:
        return {
            "valid": False,
            "source_separation_derived": False,
            "failures": [],
            "refs": packet_projection_refs_for_status(refs, packet_status),
            "expected_refs": refs,
            "hashes": dict_or_empty(packet_status.get("hashes")) if packet_status is not None else {},
            "locks": dict_or_empty(packet_status.get("locks")) if packet_status is not None else PROJECTION_NO_SEND_LOCKS,
            "source_kind": source_kind,
            "source_separation": {},
        }

    if packet_status is not None:
        if dict_or_empty(packet_status.get("locks")) != PROJECTION_NO_SEND_LOCKS:
            failures.append("TARGET_PROJECTION_LOCK_PACKET_NO_SEND_LOCKS_MISSING_OR_WEAK")
        for key, ref in refs.items():
            if not ref:
                failures.append(f"TARGET_PROJECTION_LOCK_PACKET_REF_MISSING::{key}")

    declaration = read_projection_artifact(root, refs["declaration_ref"], failures)
    visible_lock = read_projection_artifact(root, refs["visible_lock_ref"], failures)
    prediction_lock = read_projection_artifact(root, refs["prediction_lock_ref"], failures)
    target_lock = read_projection_artifact(root, refs["target_lock_ref"], failures)
    if failures:
        return {
            "valid": False,
            "source_separation_derived": False,
            "failures": ordered_unique(failures),
            "refs": packet_projection_refs_for_status(refs, packet_status),
            "expected_refs": refs,
            "hashes": dict_or_empty(packet_status.get("hashes")) if packet_status is not None else {},
            "locks": dict_or_empty(packet_status.get("locks")) if packet_status is not None else PROJECTION_NO_SEND_LOCKS,
            "source_kind": source_kind,
            "source_separation": {},
        }

    declaration_hash = sha256_object(
        {
            key: value
            for key, value in declaration.items()
            if key not in target_projection_factory.EXPECTED_HASH_KEYS
        }
    )
    visible_sha256 = sha256_object(visible_lock)
    prediction_sha256 = sha256_object(prediction_lock)
    target_sha256 = sha256_object(target_lock)
    if packet_status is not None:
        validate_packet_projection_hashes(
            packet_status,
            declaration_hash=declaration_hash,
            visible_sha256=visible_sha256,
            prediction_sha256=prediction_sha256,
            target_sha256=target_sha256,
            failures=failures,
        )

    if declaration.get("declared_before_scoring") is not True:
        failures.append("TARGET_PROJECTION_LOCK_DECLARATION_NOT_PRETARGET")
    if as_str(declaration.get("lock_id")) != BIOLOGY_TARGET_LOCK_ID:
        failures.append("TARGET_PROJECTION_LOCK_ID_MISMATCH")
    if list_of_strings(declaration.get("visible_fields")) != BIOLOGY_VISIBLE_FIELDS:
        failures.append("TARGET_PROJECTION_LOCK_VISIBLE_FIELDS_UNEXPECTED")
    if list_of_strings(declaration.get("target_fields")) != BIOLOGY_TARGET_FIELDS:
        failures.append("TARGET_PROJECTION_LOCK_TARGET_FIELDS_UNEXPECTED")
    if not target_lock_locks_valid(declaration):
        failures.append("TARGET_PROJECTION_DECLARATION_NO_SEND_LOCKS_WEAK")
    for visible in list_of_strings(declaration.get("visible_fields")):
        for target in list_of_strings(declaration.get("target_fields")):
            if target_projection_factory.paths_overlap(visible, target):
                failures.append(f"TARGET_FIELD_IN_VISIBLE_PROJECTION::{target}")

    expected_hash_matches(declaration, "expected_declaration_sha256", declaration_hash, failures)
    expected_hash_matches(declaration, "expected_visible_projection_sha256", visible_sha256, failures)
    expected_hash_matches(declaration, "expected_prediction_materialization_sha256", prediction_sha256, failures)
    expected_hash_matches(declaration, "expected_target_projection_sha256", target_sha256, failures)

    if visible_lock.get("schema_id") != target_projection_factory.VISIBLE_LOCK_SCHEMA_ID:
        failures.append("VISIBLE_PROJECTION_LOCK_SCHEMA_MISMATCH")
    if prediction_lock.get("schema_id") != target_projection_factory.PREDICTION_LOCK_SCHEMA_ID:
        failures.append("PREDICTION_MATERIALIZATION_LOCK_SCHEMA_MISMATCH")
    if target_lock.get("schema_id") != target_projection_factory.TARGET_LOCK_SCHEMA_ID:
        failures.append("TARGET_PROJECTION_LOCK_SCHEMA_MISMATCH")
    if visible_lock.get("declaration_sha256") != declaration_hash:
        failures.append("VISIBLE_PROJECTION_DECLARATION_HASH_MISMATCH")
    if prediction_lock.get("declaration_sha256") != declaration_hash:
        failures.append("PREDICTION_MATERIALIZATION_DECLARATION_HASH_MISMATCH")
    if target_lock.get("declaration_sha256") != declaration_hash:
        failures.append("TARGET_PROJECTION_DECLARATION_HASH_MISMATCH")
    if prediction_lock.get("visible_projection_sha256") != visible_sha256:
        failures.append("PREDICTION_VISIBLE_PROJECTION_HASH_MISMATCH")
    if target_lock.get("visible_projection_sha256") != visible_sha256:
        failures.append("TARGET_VISIBLE_PROJECTION_HASH_MISMATCH")
    if target_lock.get("prediction_materialization_sha256") != prediction_sha256:
        failures.append("TARGET_PREDICTION_MATERIALIZATION_HASH_MISMATCH")
    for lock_payload, label in (
        (visible_lock, "VISIBLE_PROJECTION_LOCK"),
        (prediction_lock, "PREDICTION_MATERIALIZATION_LOCK"),
        (target_lock, "TARGET_PROJECTION_LOCK"),
    ):
        if as_str(lock_payload.get("declaration_ref")) != refs["declaration_ref"]:
            failures.append(f"{label}_DECLARATION_REF_MISMATCH")
    for lock_name, lock_payload in (
        ("VISIBLE_PROJECTION_LOCK", visible_lock),
        ("PREDICTION_MATERIALIZATION_LOCK", prediction_lock),
        ("TARGET_PROJECTION_LOCK", target_lock),
    ):
        if as_str(lock_payload.get("lock_id")) != BIOLOGY_TARGET_LOCK_ID:
            failures.append(f"{lock_name}_ID_MISMATCH")
        if not target_lock_locks_valid(lock_payload):
            failures.append(f"{lock_name}_NO_SEND_LOCKS_WEAK")

    separation = dict_or_empty(prediction_lock.get("algorithmic_target_separation"))
    if separation.get("target_projection_read_before_prediction_materialization") is not False:
        failures.append("TARGET_PROJECTION_READ_BEFORE_PREDICTION_MATERIALIZATION")
    if separation.get("target_opened_after_prediction_materialization") is not True:
        failures.append("TARGET_PROJECTION_OPEN_AFTER_PREDICTION_NOT_ATTESTED")
    if target_lock.get("target_opened_after_prediction_materialization") is not True:
        failures.append("TARGET_LOCK_OPEN_AFTER_PREDICTION_NOT_ATTESTED")
    projection_snapshot_rows = validate_projection_snapshot(
        root,
        declaration=declaration,
        visible_lock=visible_lock,
        target_lock=target_lock,
        rows=rows,
        packet_status=packet_status,
        failures=failures,
    )

    visible_rows_raw = visible_lock.get("rows")
    target_rows_raw = target_lock.get("rows")
    prediction_rows_raw = prediction_lock.get("prediction_rows")
    if not isinstance(visible_rows_raw, list):
        failures.append("VISIBLE_PROJECTION_LOCK_ROWS_MISSING")
        visible_rows_raw = []
    if not isinstance(target_rows_raw, list):
        failures.append("TARGET_PROJECTION_LOCK_ROWS_MISSING")
        target_rows_raw = []
    if not isinstance(prediction_rows_raw, list):
        failures.append("PREDICTION_MATERIALIZATION_ROWS_MISSING")
        prediction_rows_raw = []
    declared_row_count = as_int(declaration.get("row_count"), len(visible_rows_raw))
    for lock_name, lock_payload, lock_rows in (
        ("VISIBLE_PROJECTION_LOCK", visible_lock, visible_rows_raw),
        ("TARGET_PROJECTION_LOCK", target_lock, target_rows_raw),
        ("PREDICTION_MATERIALIZATION", prediction_lock, prediction_rows_raw),
    ):
        if as_int(lock_payload.get("row_count"), len(lock_rows)) != len(lock_rows):
            failures.append(f"{lock_name}_ROW_COUNT_FIELD_MISMATCH")
        if declared_row_count != len(lock_rows):
            failures.append(f"{lock_name}_DECLARED_ROW_COUNT_MISMATCH")

    visible_by_id = {as_str(item.get("row_id")): item for item in visible_rows_raw if isinstance(item, dict)}
    target_by_id = {as_str(item.get("row_id")): item for item in target_rows_raw if isinstance(item, dict)}
    prediction_by_id = {as_str(item.get("row_id")): item for item in prediction_rows_raw if isinstance(item, dict)}
    snapshot_indexes = build_snapshot_binding_indexes(projection_snapshot_rows)
    bound_lock_row_ids: set[str] = set()
    for row in rows:
        row_label = projection_row_id(row)
        snapshot_row = bind_projection_snapshot_row(row, snapshot_indexes) if projection_snapshot_rows else None
        if projection_snapshot_rows and snapshot_row is None:
            failures.append(f"TARGET_PROJECTION_SNAPSHOT_ROW_MISSING::{row_label}")
            continue
        if snapshot_row is not None:
            snapshot_id = snapshot_row_id(snapshot_row)
            if projection_source_key(row)[0] and snapshot_source_key(snapshot_row)[0] != projection_source_key(row)[0]:
                failures.append(f"TARGET_PROJECTION_SNAPSHOT_SOURCE_REF_MISMATCH::{row_label}")
            if projection_source_key(row)[1] and snapshot_source_key(snapshot_row)[1] != projection_source_key(row)[1]:
                failures.append(f"TARGET_PROJECTION_SNAPSHOT_SOURCE_HASH_MISMATCH::{row_label}")
            if snapshot_projection_payload(snapshot_row, BIOLOGY_VISIBLE_FIELDS) != projection_payload(row, BIOLOGY_VISIBLE_FIELDS):
                failures.append(f"TARGET_PROJECTION_SNAPSHOT_VISIBLE_FACT_MISMATCH::{row_label}")
            if snapshot_projection_payload(snapshot_row, BIOLOGY_TARGET_FIELDS) != projection_payload(row, BIOLOGY_TARGET_FIELDS):
                failures.append(f"TARGET_PROJECTION_SNAPSHOT_TARGET_FACT_MISMATCH::{row_label}")
            if snapshot_id not in projection_row_identity_candidates(row):
                row_label = f"{row_label}=>{snapshot_id}"
        row_id = projection_lock_row_id(row, snapshot_row)
        bound_lock_row_ids.add(row_id)
        visible_row = visible_by_id.get(row_id)
        target_row = target_by_id.get(row_id)
        prediction_row = prediction_by_id.get(row_id)
        if visible_row is None:
            failures.append(f"VISIBLE_PROJECTION_ROW_MISSING::{row_label}")
            continue
        if target_row is None:
            failures.append(f"TARGET_PROJECTION_ROW_MISSING::{row_label}")
            continue
        if prediction_row is None:
            failures.append(f"PREDICTION_MATERIALIZATION_ROW_MISSING::{row_label}")
            continue
        expected_visible = projection_payload(row, BIOLOGY_VISIBLE_FIELDS)
        expected_target = projection_payload(row, BIOLOGY_TARGET_FIELDS)
        actual_visible = normalized_projection(visible_row.get("visible"), BIOLOGY_VISIBLE_FIELDS)
        actual_target = normalized_projection(target_row.get("target"), BIOLOGY_TARGET_FIELDS)
        if actual_visible != expected_visible:
            failures.append(f"VISIBLE_PROJECTION_ROW_MISMATCH::{row_label}")
        if actual_target != expected_target:
            failures.append(f"TARGET_PROJECTION_ROW_MISMATCH::{row_label}")
        visible_row_hash = sha256_object(
            {
                "row_index": as_int(visible_row.get("row_index")),
                "row_id": row_id,
                "visible": actual_visible,
            }
        )
        target_row_hash = sha256_object(
            {
                "row_index": as_int(target_row.get("row_index")),
                "row_id": row_id,
                "target": actual_target,
            }
        )
        if as_str(visible_row.get("visible_row_sha256")) != visible_row_hash:
            failures.append(f"VISIBLE_PROJECTION_ROW_HASH_MISMATCH::{row_label}")
        if as_str(target_row.get("target_row_sha256")) != target_row_hash:
            failures.append(f"TARGET_PROJECTION_ROW_HASH_MISMATCH::{row_label}")
        if prediction_row.get("target_opened") is not False:
            failures.append(f"PREDICTION_ROW_TARGET_OPENED_BEFORE_MATERIALIZATION::{row_label}")

    visible_ids = set(visible_by_id)
    target_ids = set(target_by_id)
    prediction_ids = set(prediction_by_id)
    if visible_ids - bound_lock_row_ids:
        failures.append(f"VISIBLE_PROJECTION_LOCK_UNBOUND_ROWS::{len(visible_ids - bound_lock_row_ids)}")
    if target_ids - bound_lock_row_ids:
        failures.append(f"TARGET_PROJECTION_LOCK_UNBOUND_ROWS::{len(target_ids - bound_lock_row_ids)}")
    if prediction_ids - bound_lock_row_ids:
        failures.append(f"PREDICTION_MATERIALIZATION_UNBOUND_ROWS::{len(prediction_ids - bound_lock_row_ids)}")

    valid = not failures
    source_separation = (
        {
            "mode": "target_blind",
            "kind": "target_projection_lock",
            "pre_target_lock": True,
            "target_hidden_until_scoring": True,
            "declared_before_scoring": True,
            "training_sources": [refs["visible_lock_ref"]],
            "target_sources": [refs["target_lock_ref"]],
            "training_manifest_sha256": visible_sha256,
            "target_manifest_sha256": target_sha256,
        }
        if valid
        else {}
    )
    return {
        "valid": valid,
        "source_separation_derived": valid,
        "failures": ordered_unique(failures),
        "refs": packet_projection_refs_for_status(refs, packet_status),
        "expected_refs": refs,
        "hashes": {
            "declaration_sha256": declaration_hash,
            "visible_projection_lock_sha256": visible_sha256,
            "prediction_materialization_lock_sha256": prediction_sha256,
            "target_projection_lock_sha256": target_sha256,
            **(
                {"snapshot_sha256": as_str(declaration.get("expected_snapshot_sha256"))}
                if as_str(declaration.get("expected_snapshot_sha256"))
                else {}
            ),
            **(
                {
                    "snapshot_sha256": as_str(dict_or_empty(packet_status.get("hashes")).get("snapshot_sha256"))
                }
                if packet_status is not None and as_str(dict_or_empty(packet_status.get("hashes")).get("snapshot_sha256"))
                else {}
            ),
        },
        "locks": dict_or_empty(packet_status.get("locks")) if packet_status is not None else PROJECTION_NO_SEND_LOCKS,
        "source_kind": source_kind,
        "declaration_sha256": declaration_hash,
        "visible_projection_sha256": visible_sha256,
        "prediction_materialization_sha256": prediction_sha256,
        "target_projection_sha256": target_sha256,
        "source_separation": source_separation,
    }


def apply_target_projection_lock(rows: list[dict[str, Any]], projection_status: dict[str, Any]) -> None:
    if projection_status.get("valid") is not True:
        return
    refs = dict_or_empty(projection_status.get("expected_refs"))
    for row in rows:
        row["lock_ref"] = as_str(refs.get("target_lock_ref"))
        row["lock_sha256"] = as_str(projection_status.get("target_projection_sha256"))
        row["declared_before_scoring_lock"] = True
        row["target_projection_lock_verified"] = True
        row["target_projection_lock_refs"] = projection_status.get("refs", {})
        row["target_projection_lock_hashes"] = projection_status.get("hashes", {})
        row["row_hash"] = row_hash(row)


def combine_target_projection_status(
    *,
    batch_status: dict[str, Any],
    batch_rows: list[dict[str, Any]],
    legacy_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    legacy_statuses = [dict_or_empty(row.get("target_projection_lock_hashes")) for row in legacy_rows]
    legacy_failures = ordered_unique(
        [
            failure
            for row in legacy_rows
            for failure in list_of_strings(
                dict_or_empty(row.get("target_projection_lock_status")).get("blockers")
            )
        ]
    )
    legacy_valid = not legacy_rows or all(row.get("target_projection_lock_verified") is True for row in legacy_rows)
    batch_valid = not batch_rows or batch_status.get("valid") is True
    failures = ordered_unique([*list_of_strings(batch_status.get("failures")), *legacy_failures])
    visible_sources = []
    target_sources = []
    visible_hashes = []
    target_hashes = []
    if batch_rows and batch_status.get("valid") is True:
        batch_source = dict_or_empty(batch_status.get("source_separation"))
        visible_sources.extend(list_of_strings(batch_source.get("training_sources")))
        target_sources.extend(list_of_strings(batch_source.get("target_sources")))
        visible_hashes.append(as_str(batch_source.get("training_manifest_sha256")))
        target_hashes.append(as_str(batch_source.get("target_manifest_sha256")))
    for row in legacy_rows:
        refs = dict_or_empty(row.get("target_projection_lock_refs"))
        hashes = dict_or_empty(row.get("target_projection_lock_hashes"))
        visible_sources.append(as_str(refs.get("visible_projection_lock_ref")))
        target_sources.append(as_str(refs.get("target_projection_lock_ref")))
        visible_hashes.append(as_str(hashes.get("visible_projection_lock_sha256")))
        target_hashes.append(as_str(hashes.get("target_projection_lock_sha256")))
    valid = batch_valid and legacy_valid and not failures
    source_separation = (
        {
            "mode": "target_blind",
            "kind": "target_projection_lock_with_legacy_seed_upgrade"
            if batch_rows and legacy_rows
            else ("legacy_seed_target_projection_lock" if legacy_rows else "target_projection_lock"),
            "pre_target_lock": True,
            "target_hidden_until_scoring": True,
            "declared_before_scoring": True,
            "training_sources": ordered_unique([source for source in visible_sources if source]),
            "target_sources": ordered_unique([source for source in target_sources if source]),
            "training_manifest_sha256": sha256_object(ordered_unique([value for value in visible_hashes if value])),
            "target_manifest_sha256": sha256_object(ordered_unique([value for value in target_hashes if value])),
        }
        if valid
        else {}
    )
    if not legacy_rows:
        return batch_status
    return {
        **batch_status,
        "valid": valid,
        "source_separation_derived": valid,
        "failures": failures,
        "source_kind": "batch_projection_plus_legacy_seed" if batch_rows else "legacy_seed_auto_projection",
        "legacy_seed_row_total": len(legacy_rows),
        "legacy_seed_hashes": legacy_statuses,
        "source_separation": source_separation,
    }


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
        "evidence_family": "biology-ncbi-geo-pagination-qa",
        "pack_version": "1.0",
        "support_scope": "bounded NCBI/GEO API page-size reconstruction QA; not biological grand support",
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
    projection_status: dict[str, Any],
    packet_requests: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    missing = missing_official_snapshots(rows, minimum_n, packet_requests)
    target_projection_lock = {
        "required": True,
        "valid": projection_status.get("valid") is True,
        "source_separation_derived": projection_status.get("source_separation_derived") is True,
        "expected_refs": projection_status.get("expected_refs", target_projection_refs()),
        "failures": projection_status.get("failures", []),
    }
    if dict_or_empty(projection_status.get("refs")) or dict_or_empty(projection_status.get("hashes")):
        target_projection_lock.update(
            {
                "refs": projection_status.get("refs", packet_projection_refs_for_status(target_projection_refs(), None)),
                "hashes": projection_status.get("hashes", {}),
                "locks": projection_status.get("locks", PROJECTION_NO_SEND_LOCKS),
            }
        )
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
        "target_projection_lock": target_projection_lock,
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
    projection_status: dict[str, Any],
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
        "target_projection_lock": projection_status,
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
    projection_status: dict[str, Any],
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
        "target_projection_lock": projection_status,
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
    projection_status: dict[str, Any],
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
        "target_projection_lock": projection_status,
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
    legacy_seed_artifacts: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    legacy_seed_artifacts = legacy_seed_artifacts or {}
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
            *[
                {"artifact_ref": ref, "sha256": sha256_object(artifact), "hash_policy": PACK_HASH_POLICY}
                for ref, artifact in sorted(legacy_seed_artifacts.items())
            ],
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
        "legacy_seed_artifact_hashes": [
            {"artifact_ref": ref, "sha256": sha256_object(artifact), "hash_policy": PACK_HASH_POLICY}
            for ref, artifact in sorted(legacy_seed_artifacts.items())
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
    legacy_seed_artifacts: dict[str, dict[str, Any]] = {}
    record_index = 0
    for snapshot in loaded_snapshots:
        local_blockers.extend(snapshot["failures"])
        payload = snapshot.get("payload")
        acquisition = dict_or_empty(snapshot.get("acquisition"))
        if payload is None:
            continue
        for record, source_candidate, comparator, provenance in iter_payload_records(payload):
            row_acquisition = acquisition
            if row_acquisition:
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
            else:
                row_acquisition, legacy_source, legacy_comparator, legacy_failures = legacy_seed_upgrade_for_record(
                    source_ref=snapshot["ref"],
                    source_sha256=snapshot["sha256"],
                    record_index=record_index + 1,
                    record=record,
                    acquisition=row_acquisition,
                )
                if row_acquisition:
                    source_candidate = legacy_source
                    comparator = legacy_comparator
                    provenance = {
                        **provenance,
                        "official_source": "NCBI E-utilities ESearch",
                        "official_url": as_str(row_acquisition.get("official_endpoint_url")),
                    }
                    legacy_seed_artifacts.update(dict_or_empty(row_acquisition.get("legacy_seed_artifacts")))
                local_blockers.extend(legacy_failures)
            source_candidates.append(source_candidate)
            record_index += 1
            row, row_failures = build_row(
                record=record,
                source_ref=snapshot["ref"],
                source_sha256=snapshot["sha256"],
                record_index=record_index,
                comparator=comparator,
                provenance=provenance,
                acquisition=row_acquisition,
            )
            local_blockers.extend(row_failures)
            if row is not None:
                rows.append(row)

    if not discovered_refs:
        local_blockers.append("NO_LOCAL_NCBI_GEO_SNAPSHOTS_DISCOVERED")
    if loaded_snapshots and not rows:
        local_blockers.append("NO_SCORABLE_NCBI_GEO_ESEARCH_ROWS")
    rows_by_snapshot: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        rows_by_snapshot.setdefault(as_str(row.get("snapshot_ref")), []).append(row)
    for item in snapshot_hashes:
        if item.get("lock_ref"):
            continue
        snapshot_rows = rows_by_snapshot.get(as_str(item.get("snapshot_ref")), [])
        if snapshot_rows and all(row.get("declared_before_scoring_lock") is True for row in snapshot_rows):
            item["lock_ref"] = as_str(snapshot_rows[0].get("lock_ref"))
            item["declared_before_scoring_lock"] = True
            item["target_projection_lock_verified"] = all(
                row.get("target_projection_lock_verified") is True for row in snapshot_rows
            )
            item["legacy_seed_upgrade"] = all(row.get("legacy_seed_upgrade") is True for row in snapshot_rows)

    legacy_rows = [row for row in rows if row.get("legacy_seed_upgrade") is True]
    batch_projection_rows = [row for row in rows if row.get("legacy_seed_upgrade") is not True]
    batch_projection_status = load_target_projection_lock_source(
        root, batch_projection_rows, packet_target_projection_lock(root)
    )
    projection_status = combine_target_projection_status(
        batch_status=batch_projection_status,
        batch_rows=batch_projection_rows,
        legacy_rows=legacy_rows,
    )
    if rows and projection_status.get("valid") is not True:
        local_blockers.extend(projection_status.get("failures", []))
        local_blockers.append("TARGET_PROJECTION_LOCK_REQUIRED")
    if projection_status.get("valid") is True:
        apply_target_projection_lock(batch_projection_rows, batch_projection_status)
        source_candidates = [dict_or_empty(projection_status.get("source_separation"))]

    source, source_selection_failures = select_source_separation(source_candidates)
    local_blockers.extend(source_selection_failures)
    local_blockers.extend(validate_source_separation(source, requirements))
    local_blockers.extend(validate_rows(rows))

    if len(rows) < minimum_n:
        local_blockers.append(f"N_BELOW_MINIMUM::{len(rows)}/{minimum_n}")
        local_blockers.append("CURRENT_RAW_DATA_TOO_THIN_FOR_NCBI_GEO_BATCH")
    if residual_summary(rows)["superiority_margin"] <= 0:
        local_blockers.append("RESIDUAL_SUPERIORITY_NOT_MET")
    local_blockers.append(PAGINATION_QA_BLOCKER)

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
    tasks = build_tasks(
        rows=rows,
        blockers=blockers,
        snapshot_hashes=snapshot_hashes,
        source=source,
        minimum_n=minimum_n,
        projection_status=projection_status,
    )
    acquisition_packet = build_acquisition_packet(
        rows=rows,
        minimum_n=minimum_n,
        blockers=blockers,
        snapshot_refs=discovered_refs,
        projection_status=projection_status,
        packet_requests=packet_requests,
    )
    protocol = build_protocol(
        candidate_pack=candidate_pack,
        rows=rows,
        blockers=blockers,
        source=source,
        minimum_n=minimum_n,
        snapshot_hashes=snapshot_hashes,
        projection_status=projection_status,
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
        projection_status=projection_status,
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
        legacy_seed_artifacts=legacy_seed_artifacts,
    )

    return {
        "tasks": tasks,
        "protocol": protocol,
        "candidate_pack": candidate_pack,
        "report": report,
        "acquisition_packet": acquisition_packet,
        "hashes": hashes,
        "readme": readme,
        "legacy_seed_artifacts": legacy_seed_artifacts,
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
    for rel_path, artifact in sorted(dict_or_empty(payload.get("legacy_seed_artifacts")).items()):
        write_json(root / rel_path, artifact)
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
        *sorted(dict_or_empty(expected.get("legacy_seed_artifacts")).items()),
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
