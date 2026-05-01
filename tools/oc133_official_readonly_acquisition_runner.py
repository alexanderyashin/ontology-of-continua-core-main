from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
CAPABILITY_OWNER = "Research/EmpiricalScience"

DEFAULT_PACKET_GLOB = "validation/heldout/grand_science/**/*ACQUISITION_PACKET.json"
RUN_ROOT_REL = "validation/heldout/acquisition_runs/oc133_official_readonly"
SNAPSHOT_ROOT_REL = f"{RUN_ROOT_REL}/snapshots"
LOCK_ROOT_REL = f"{RUN_ROOT_REL}/locks"
ORDER_ROOT_REL = f"{RUN_ROOT_REL}/order_records"
RUN_REPORT_REL = f"{RUN_ROOT_REL}/OC133_OFFICIAL_READONLY_ACQUISITION_RUN.json"
PUBLIC_REPORT_REL = "reports/OC133_OFFICIAL_READONLY_ACQUISITION_RUN.json"
REPORT_JSON_REL = PUBLIC_REPORT_REL

REPORT_SCHEMA_ID = "OC133_OFFICIAL_READONLY_ACQUISITION_RUN_v1"
REQUEST_TIMEOUT_SECONDS = 30
MAX_RESPONSE_BYTES = 25 * 1024 * 1024
HASH_POLICY = "sha256 over acquired response bytes as stored"
TRANSIENT_HTTP_STATUSES = {408, 425, 429, 500, 502, 503, 504}
DEFAULT_RETRY_DELAYS_SECONDS = (1.0, 5.0)
MAX_RETRY_DELAY_SECONDS = 60.0

NO_SEND_LOCKS = {
    "no_send": True,
    "publish_allowed": False,
    "push_allowed": False,
    "journal_submissions_allowed": False,
    "doi_registration_allowed": False,
    "zenodo_upload_allowed": False,
    "registry_write_allowed": False,
    "release_promotion_allowed": False,
}

SENSITIVE_QUERY_KEYS = {
    "access_token",
    "api_key",
    "apikey",
    "auth",
    "authorization",
    "bearer",
    "client_secret",
    "doi_token",
    "github_token",
    "key",
    "password",
    "passwd",
    "publish_token",
    "push_token",
    "secret",
    "token",
    "zenodo_token",
}


@dataclass(frozen=True)
class AllowRule:
    name: str
    host: str
    path_prefix: str
    exact_path: bool = False
    required_query_params: tuple[tuple[str, str], ...] = ()
    allowed_query_keys: tuple[str, ...] = ()


ALLOWLIST: tuple[AllowRule, ...] = (
    AllowRule("NCBI EUtils", "eutils.ncbi.nlm.nih.gov", "/entrez/eutils/"),
    AllowRule("PubChem PUG REST", "pubchem.ncbi.nlm.nih.gov", "/rest/pug/"),
    AllowRule("World Bank API", "api.worldbank.org", "/v2/"),
    AllowRule("NIST physics constants", "physics.nist.gov", "/cuu/Constants/"),
    AllowRule(
        "NIST ASD hydrogen Balmer lines TSV",
        "physics.nist.gov",
        "/cgi-bin/ASD/lines1.pl",
        exact_path=True,
        required_query_params=(
            ("spectra", "H"),
            ("limits_type", "0"),
            ("low_w", ""),
            ("upp_w", ""),
            ("unit", "1"),
            ("de", "0"),
            ("format", "3"),
            ("line_out", "0"),
            ("remove_js", "on"),
            ("en_unit", "1"),
            ("output", "0"),
            ("page_size", "50"),
            ("show_obs_wl", "1"),
            ("show_calc_wl", "1"),
            ("show_wn", "1"),
        ),
        allowed_query_keys=(
            "spectra",
            "limits_type",
            "low_w",
            "upp_w",
            "unit",
            "de",
            "format",
            "line_out",
            "remove_js",
            "en_unit",
            "output",
            "page_size",
            "show_obs_wl",
            "show_calc_wl",
            "show_wn",
        ),
    ),
    AllowRule("NIST Chemistry WebBook", "webbook.nist.gov", "/cgi/cbook.cgi"),
)

DEFAULT_PROSPECTIVE_LOCK_METADATA: dict[str, Any] = {
    "schema_id": "OC133_OFFICIAL_READONLY_PROSPECTIVE_LOCK_METADATA_v1",
    "source_snapshot_pre_target_lock": True,
    "target_hidden_until_scoring": True,
    "target_projection_unsealed_for_scoring": False,
    "scoring_started": False,
    "prediction_materialization_required_before_scoring": True,
    "target_projection_read_before_prediction_materialization": False,
    "public_release_action_allowed": False,
    "publish_allowed": False,
    "push_allowed": False,
}


def repo_root() -> Path:
    return ROOT


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_object(payload: Any) -> str:
    return sha256_bytes(canonical_json(payload).encode("utf-8"))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def resolve_under_root(root: Path, rel_path: str) -> Path:
    path = (root / rel_path).resolve()
    path.relative_to(root.resolve())
    return path


def is_safe_relative_ref(ref: str) -> bool:
    if not ref or "\x00" in ref:
        return False
    parsed = urllib.parse.urlparse(ref)
    if parsed.scheme or parsed.netloc:
        return False
    path = Path(ref)
    if path.is_absolute():
        return False
    return ".." not in path.parts


def sanitize_filename(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip())
    safe = safe.strip("._")
    return safe[:120] or "snapshot"


def suffix_for_ref(ref: str) -> str:
    suffix = Path(ref).suffix.lower()
    if suffix in {".json", ".txt", ".html", ".htm", ".tsv", ".csv", ".xml"}:
        return suffix
    return ".bin"


def packet_paths_from_args(root: Path, packet_args: list[str]) -> list[Path]:
    if packet_args:
        return [resolve_under_root(root, packet) for packet in packet_args]
    return sorted(root.glob(DEFAULT_PACKET_GLOB))


def sensitive_query_keys(url: str) -> list[str]:
    parsed = urllib.parse.urlsplit(url)
    keys = []
    for key, _ in urllib.parse.parse_qsl(parsed.query, keep_blank_values=True):
        if key.lower() in SENSITIVE_QUERY_KEYS or key.lower().endswith("_token"):
            keys.append(key)
    return sorted(set(keys))


def redacted_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    netloc = parsed.hostname or ""
    if parsed.port:
        netloc = f"{netloc}:{parsed.port}"
    query_pairs = []
    for key, value in urllib.parse.parse_qsl(parsed.query, keep_blank_values=True):
        if key.lower() in SENSITIVE_QUERY_KEYS or key.lower().endswith("_token"):
            query_pairs.append((key, "REDACTED"))
        else:
            query_pairs.append((key, value))
    query = urllib.parse.urlencode(query_pairs, doseq=True)
    return urllib.parse.urlunsplit((parsed.scheme, netloc, parsed.path, query, parsed.fragment))


def rule_path_matches(rule: AllowRule, path: str) -> bool:
    if rule.exact_path:
        return path == rule.path_prefix
    return path.startswith(rule.path_prefix)


def query_blockers_for_rule(rule: AllowRule, parsed: urllib.parse.SplitResult) -> list[str]:
    if not rule.required_query_params and not rule.allowed_query_keys:
        return []
    pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    seen: dict[str, list[str]] = {}
    for key, value in pairs:
        seen.setdefault(key, []).append(value)
    blockers: list[str] = []
    allowed_keys = set(rule.allowed_query_keys)
    if allowed_keys:
        unexpected = sorted(key for key in seen if key not in allowed_keys)
        if unexpected:
            blockers.append(f"QUERY_PARAM_NOT_ALLOWED::{','.join(unexpected)}")
    for key, values in sorted(seen.items()):
        if len(values) > 1:
            blockers.append(f"QUERY_PARAM_DUPLICATE_NOT_ALLOWED::{key}")
    for key, expected in rule.required_query_params:
        values = seen.get(key)
        if values is None:
            blockers.append(f"QUERY_PARAM_REQUIRED::{key}")
        elif values != [expected]:
            blockers.append(f"QUERY_PARAM_VALUE_NOT_ALLOWED::{key}")
    return blockers


def allowlist_match(url: str) -> tuple[bool, str, list[str]]:
    parsed = urllib.parse.urlsplit(url)
    blockers: list[str] = []
    if parsed.scheme != "https":
        blockers.append("URL_SCHEME_NOT_HTTPS")
    if parsed.username or parsed.password:
        blockers.append("URL_CREDENTIALS_NOT_ALLOWED")
    host = (parsed.hostname or "").lower().rstrip(".")
    if not host:
        blockers.append("URL_HOST_MISSING")
    sensitive_keys = sensitive_query_keys(url)
    if sensitive_keys:
        blockers.append(f"SENSITIVE_QUERY_TOKEN_NOT_ALLOWED::{','.join(sensitive_keys)}")
    for rule in ALLOWLIST:
        if host == rule.host and rule_path_matches(rule, parsed.path):
            rule_blockers = query_blockers_for_rule(rule, parsed)
            blockers.extend(rule_blockers)
            return not blockers, rule.name, blockers
    blockers.append(f"URL_NOT_IN_OFFICIAL_ALLOWLIST::{host}{parsed.path}")
    return False, "", blockers


def packet_acquisition_rows(packet: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("missing_official_snapshots", "official_snapshots", "acquisition_requests", "snapshots"):
        rows = packet.get(key)
        if isinstance(rows, list):
            return [row for row in rows if isinstance(row, dict)]
    if "official_endpoint_url" in packet and "expected_local_snapshot_ref" in packet:
        return [packet]
    return []


def load_packet_requests(root: Path, packet_paths: list[Path]) -> list[dict[str, Any]]:
    requests: list[dict[str, Any]] = []
    for packet_path in packet_paths:
        payload = read_json(packet_path)
        if not isinstance(payload, dict):
            raise ValueError(f"packet is not a JSON object: {packet_path}")
        packet_rel = packet_path.relative_to(root).as_posix()
        for index, row in enumerate(packet_acquisition_rows(payload), start=1):
            official_url = str(row.get("official_endpoint_url") or "")
            expected_ref = str(row.get("expected_local_snapshot_ref") or "")
            acquisition_id = str(row.get("acquisition_id") or f"{packet_path.stem}-{index:04d}")
            requests.append(
                {
                    "packet_ref": packet_rel,
                    "packet_schema_id": str(payload.get("schema_id") or ""),
                    "acquisition_id": acquisition_id,
                    "official_source": str(row.get("official_source") or ""),
                    "network_official_endpoint_url": official_url,
                    "official_endpoint_url": redacted_url(official_url),
                    "redacted_official_endpoint_url": redacted_url(official_url),
                    "expected_local_snapshot_ref": expected_ref,
                    "packet_no_send_lock": bool(row.get("no_send_lock", payload.get("no_send", True))),
                    "required_fields": row.get("required_fields", []),
                    "query_params": row.get("query_params", {}),
                    "prospective_lock_metadata": row.get(
                        "prospective_lock_metadata",
                        row.get("source_separation_lock_metadata", row.get("execution_lock_metadata", {})),
                    ),
                }
            )
    return requests


def prospective_lock_metadata_blockers(row: dict[str, Any], *, require_execution_metadata: bool) -> list[str]:
    metadata = row.get("prospective_lock_metadata")
    if not require_execution_metadata:
        return []
    if not isinstance(metadata, dict) or not metadata:
        return ["PROSPECTIVE_LOCK_METADATA_MISSING"]
    blockers: list[str] = []
    required_values = {
        "source_snapshot_pre_target_lock": True,
        "target_hidden_until_scoring": True,
        "target_projection_unsealed_for_scoring": False,
        "scoring_started": False,
        "prediction_materialization_required_before_scoring": True,
        "target_projection_read_before_prediction_materialization": False,
        "public_release_action_allowed": False,
        "publish_allowed": False,
        "push_allowed": False,
    }
    for key, expected in required_values.items():
        if metadata.get(key) is not expected:
            blockers.append(f"PROSPECTIVE_LOCK_METADATA_INVALID::{key}")
    if metadata.get("scoring_started_at"):
        blockers.append("POST_SCORING_ACQUISITION_NOT_ALLOWED")
    if metadata.get("target_projection_unsealed_for_scoring_at"):
        blockers.append("TARGET_UNSEALED_BEFORE_ACQUISITION_NOT_ALLOWED")
    return blockers


def validate_request(row: dict[str, Any], *, require_execution_metadata: bool = False) -> dict[str, Any]:
    blockers: list[str] = []
    official_url = row["network_official_endpoint_url"]
    expected_ref = row["expected_local_snapshot_ref"]
    allowed, allowlist_rule, url_blockers = allowlist_match(official_url)
    blockers.extend(url_blockers)
    blockers.extend(prospective_lock_metadata_blockers(row, require_execution_metadata=require_execution_metadata))
    if not expected_ref:
        blockers.append("EXPECTED_LOCAL_SNAPSHOT_REF_MISSING")
    elif not is_safe_relative_ref(expected_ref):
        blockers.append("EXPECTED_LOCAL_SNAPSHOT_REF_UNSAFE")
    if not row.get("packet_no_send_lock"):
        blockers.append("PACKET_NO_SEND_LOCK_MISSING")
    acquisition_id = sanitize_filename(row["acquisition_id"])
    suffix = suffix_for_ref(expected_ref)
    snapshot_ref = f"{SNAPSHOT_ROOT_REL}/{acquisition_id}{suffix}"
    lock_ref = f"{LOCK_ROOT_REL}/{acquisition_id}.lock.json"
    order_ref = f"{ORDER_ROOT_REL}/{acquisition_id}.order.json"
    meta_ref = f"{SNAPSHOT_ROOT_REL}/{acquisition_id}.metadata.json"
    return {
        **row,
        "allowlist_allowed": allowed,
        "allowlist_rule": allowlist_rule,
        "validation_blockers": blockers,
        "validated_for_network": not blockers,
        "snapshot_ref": snapshot_ref,
        "snapshot_metadata_ref": meta_ref,
        "lock_ref": lock_ref,
        "order_record_ref": order_ref,
        "hash_policy": HASH_POLICY,
    }


def response_status(response: Any) -> int:
    status = getattr(response, "status", None)
    if isinstance(status, int):
        return status
    getcode = getattr(response, "getcode", None)
    if callable(getcode):
        code = getcode()
        if isinstance(code, int):
            return code
    return 0


def response_headers(response: Any) -> dict[str, str]:
    info = getattr(response, "headers", None)
    if info is None:
        info_call = getattr(response, "info", None)
        if callable(info_call):
            info = info_call()
    items = getattr(info, "items", None)
    if callable(items):
        return {str(key).lower(): str(value) for key, value in items()}
    return {}


def fetch_official_url(url: str, timeout: int = REQUEST_TIMEOUT_SECONDS) -> tuple[int, dict[str, str], bytes]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "*/*",
            "User-Agent": "Logion-OC133-official-readonly-acquisition/1.0",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = response.read(MAX_RESPONSE_BYTES + 1)
            if len(data) > MAX_RESPONSE_BYTES:
                raise ValueError("response exceeds MAX_RESPONSE_BYTES")
            return response_status(response), response_headers(response), data
    except urllib.error.HTTPError as exc:
        data = exc.read(MAX_RESPONSE_BYTES + 1)
        if len(data) > MAX_RESPONSE_BYTES:
            raise ValueError("response exceeds MAX_RESPONSE_BYTES")
        return int(exc.code), response_headers(exc), data


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_order_record(record: dict[str, Any], *, acquired_at_utc: str) -> dict[str, Any]:
    metadata = record.get("prospective_lock_metadata")
    if not isinstance(metadata, dict):
        metadata = {}
    order_record = {
        "schema_id": "OC133_OFFICIAL_READONLY_ACQUISITION_ORDER_RECORD_v1",
        "release_id": RELEASE_ID,
        "acquisition_id": record["acquisition_id"],
        "official_endpoint_url": record["redacted_official_endpoint_url"],
        "snapshot_ref": record["snapshot_ref"],
        "snapshot_sha256": record["sha256"],
        "source_bytes_sha256": record["sha256"],
        "source_bytes_byte_count": record["byte_count"],
        "acquired_at_utc": acquired_at_utc,
        "event_order": [
            {
                "event_index": 1,
                "event": "source_snapshot_locked",
                "timestamp_utc": acquired_at_utc,
                "status": "completed_by_official_readonly_runner",
            },
            {
                "event_index": 2,
                "event": "source_separation_declared",
                "status": "required_by_packet_before_scoring",
            },
            {
                "event_index": 3,
                "event": "visible_projection_locked",
                "status": "required_after_source_lock_before_prediction_materialization",
            },
            {
                "event_index": 4,
                "event": "prediction_materialized",
                "status": "required_before_target_projection_unsealed_for_scoring",
            },
            {
                "event_index": 5,
                "event": "target_projection_unsealed_for_scoring",
                "status": "not_performed_by_acquisition_runner",
            },
            {
                "event_index": 6,
                "event": "scoring_started",
                "status": "not_performed_by_acquisition_runner",
            },
        ],
        "sequence_proof": {
            "source_snapshot_locked_before_scoring": True,
            "source_snapshot_pre_target_lock": metadata.get("source_snapshot_pre_target_lock") is True,
            "target_hidden_until_scoring": metadata.get("target_hidden_until_scoring") is True,
            "target_projection_unsealed_for_scoring": False,
            "scoring_started": False,
            "prediction_materialization_required_before_scoring": (
                metadata.get("prediction_materialization_required_before_scoring") is True
            ),
            "target_projection_read_before_prediction_materialization": False,
            "prediction_before_scoring_sequence_required": (
                "prediction_materialized < target_projection_unsealed_for_scoring <= scoring_started"
            ),
        },
        "locks": NO_SEND_LOCKS,
        "scientific_pass": False,
        "policy": "Order record is a pre-target acquisition lock only; it does not unseal targets or start scoring.",
    }
    order_record["order_record_sha256"] = sha256_object(
        {key: value for key, value in order_record.items() if key != "order_record_sha256"}
    )
    return order_record


def parse_retry_after_seconds(headers: dict[str, str]) -> float | None:
    value = headers.get("retry-after", "").strip()
    if not value:
        return None
    try:
        seconds = float(value)
    except ValueError:
        return None
    if seconds < 0:
        return None
    return min(seconds, MAX_RETRY_DELAY_SECONDS)


def retry_delay_seconds(headers: dict[str, str], retry_delays: tuple[float, ...], retry_index: int) -> float:
    retry_after = parse_retry_after_seconds(headers)
    configured = retry_delays[min(retry_index, len(retry_delays) - 1)] if retry_delays else 0.0
    return min(max(retry_after if retry_after is not None else configured, configured), MAX_RETRY_DELAY_SECONDS)


def build_lock(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_id": "OC133_OFFICIAL_READONLY_ACQUISITION_NO_SEND_LOCK_v1",
        "release_id": RELEASE_ID,
        "acquisition_id": record["acquisition_id"],
        "official_endpoint_url": record["redacted_official_endpoint_url"],
        "expected_local_snapshot_ref": record["expected_local_snapshot_ref"],
        "snapshot_ref": record["snapshot_ref"],
        "snapshot_sha256": record["sha256"],
        "source_bytes_sha256": record["sha256"],
        "byte_count": record["byte_count"],
        "http_status": record["http_status"],
        "order_record_ref": record["order_record_ref"],
        "order_record_sha256": record["order_record_sha256"],
        "hash_policy": HASH_POLICY,
        "pre_target_sequence_proof": record["pre_target_sequence_proof"],
        "locks": NO_SEND_LOCKS,
        "scientific_pass": False,
        "policy": "Acquisition success only pins official bytes for strict evidence factories; it is not a scientific PASS.",
    }


def base_execution_record(row: dict[str, Any]) -> dict[str, Any]:
    return {
        **{key: value for key, value in row.items() if key != "network_official_endpoint_url"},
        "network_executed": True,
        "resume_reused_existing_acquisition": False,
        "network_skipped_reason": "",
        "http_status": 0,
        "byte_count": 0,
        "sha256": "",
        "content_type": "",
        "status": "FETCH_FAILED",
        "fetch_error": "",
        "network_attempt_total": 0,
        "retry_attempts": [],
        "retry_queue_eligible": False,
        "order_record_sha256": "",
        "pre_target_sequence_proof": {},
    }


def existing_acquired_record(root: Path, row: dict[str, Any]) -> dict[str, Any] | None:
    snapshot_path = resolve_under_root(root, row["snapshot_ref"])
    metadata_path = resolve_under_root(root, row["snapshot_metadata_ref"])
    lock_path = resolve_under_root(root, row["lock_ref"])
    order_path = resolve_under_root(root, row["order_record_ref"])
    if not (snapshot_path.is_file() and metadata_path.is_file() and lock_path.is_file() and order_path.is_file()):
        return None
    try:
        data = snapshot_path.read_bytes()
        metadata = read_json(metadata_path)
        lock = read_json(lock_path)
        order_record = read_json(order_path)
    except Exception:
        return None
    if not isinstance(metadata, dict) or not isinstance(lock, dict) or not isinstance(order_record, dict):
        return None
    digest = sha256_bytes(data)
    byte_count = len(data)
    order_record_sha256 = sha256_object({key: value for key, value in order_record.items() if key != "order_record_sha256"})
    if order_record.get("order_record_sha256") != order_record_sha256:
        return None
    sequence_proof = order_record.get("sequence_proof")
    if not isinstance(sequence_proof, dict):
        return None
    if not (
        sequence_proof.get("source_snapshot_locked_before_scoring") is True
        and sequence_proof.get("source_snapshot_pre_target_lock") is True
        and sequence_proof.get("target_hidden_until_scoring") is True
        and sequence_proof.get("prediction_materialization_required_before_scoring") is True
        and sequence_proof.get("target_projection_unsealed_for_scoring") is False
        and sequence_proof.get("scoring_started") is False
        and sequence_proof.get("target_projection_read_before_prediction_materialization") is False
    ):
        return None
    required_metadata = {
        "release_id": RELEASE_ID,
        "status": "ACQUIRED_READONLY",
        "official_endpoint_url": row["redacted_official_endpoint_url"],
        "snapshot_ref": row["snapshot_ref"],
        "expected_local_snapshot_ref": row["expected_local_snapshot_ref"],
        "sha256": digest,
        "source_bytes_sha256": digest,
        "byte_count": byte_count,
        "order_record_ref": row["order_record_ref"],
        "order_record_sha256": order_record_sha256,
        "locks": NO_SEND_LOCKS,
        "scientific_pass": False,
    }
    required_lock = {
        "release_id": RELEASE_ID,
        "official_endpoint_url": row["redacted_official_endpoint_url"],
        "snapshot_ref": row["snapshot_ref"],
        "expected_local_snapshot_ref": row["expected_local_snapshot_ref"],
        "snapshot_sha256": digest,
        "source_bytes_sha256": digest,
        "byte_count": byte_count,
        "order_record_ref": row["order_record_ref"],
        "order_record_sha256": order_record_sha256,
        "pre_target_sequence_proof": sequence_proof,
        "locks": NO_SEND_LOCKS,
        "scientific_pass": False,
    }
    if any(metadata.get(key) != value for key, value in required_metadata.items()):
        return None
    if any(lock.get(key) != value for key, value in required_lock.items()):
        return None
    http_status = int(metadata.get("http_status") or lock.get("http_status") or 0)
    if not 200 <= http_status < 300:
        return None
    record = base_execution_record(row)
    record.update(
        {
            "network_executed": False,
            "resume_reused_existing_acquisition": True,
            "network_skipped_reason": "VALID_EXISTING_ACQUIRED_READONLY_LOCK",
            "http_status": http_status,
            "byte_count": byte_count,
            "sha256": digest,
            "content_type": str(metadata.get("content_type") or ""),
            "status": "ACQUIRED_READONLY",
            "fetch_error": "",
            "order_record_sha256": order_record_sha256,
            "pre_target_sequence_proof": sequence_proof,
        }
    )
    return record


def execute_request(
    root: Path,
    row: dict[str, Any],
    *,
    force_refetch: bool = False,
    retry_delays: tuple[float, ...] = DEFAULT_RETRY_DELAYS_SECONDS,
    max_attempts: int | None = None,
    sleeper: Any = time.sleep,
) -> dict[str, Any]:
    record = base_execution_record(row)
    if not row["validated_for_network"]:
        record["network_executed"] = False
        record["status"] = "VALIDATION_BLOCKED"
        return record

    if not force_refetch:
        existing = existing_acquired_record(root, row)
        if existing is not None:
            return existing

    attempts_allowed = max(1, max_attempts if max_attempts is not None else len(retry_delays) + 1)
    attempts: list[dict[str, Any]] = []
    for attempt_number in range(1, attempts_allowed + 1):
        headers: dict[str, str] = {}
        data = b""
        fetch_error = ""
        try:
            status, headers, data = fetch_official_url(row["network_official_endpoint_url"])
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            status = 0
            fetch_error = f"{exc.__class__.__name__}: {exc}"
        transient = bool(fetch_error) or status in TRANSIENT_HTTP_STATUSES
        attempt = {
            "attempt_number": attempt_number,
            "http_status": status,
            "transient": transient,
            "fetch_error": fetch_error,
            "retry_after_seconds": parse_retry_after_seconds(headers),
            "content_type": headers.get("content-type", ""),
            "byte_count": len(data),
        }
        attempts.append(attempt)
        record.update(
            {
                "http_status": status,
                "byte_count": len(data),
                "sha256": sha256_bytes(data) if data else "",
                "content_type": headers.get("content-type", ""),
                "fetch_error": fetch_error,
                "network_attempt_total": attempt_number,
                "retry_attempts": attempts,
            }
        )
        if 200 <= status < 300:
            digest = sha256_bytes(data)
            acquired_at_utc = utc_now_iso()
            record.update(
                {
                    "sha256": digest,
                    "status": "ACQUIRED_READONLY",
                    "fetch_error": "",
                    "retry_queue_eligible": False,
                }
            )
            order_record = build_order_record(record, acquired_at_utc=acquired_at_utc)
            record["order_record_sha256"] = order_record["order_record_sha256"]
            record["pre_target_sequence_proof"] = order_record["sequence_proof"]
            write_bytes(resolve_under_root(root, row["snapshot_ref"]), data)
            write_json(resolve_under_root(root, row["order_record_ref"]), order_record)
            metadata = {
                "schema_id": "OC133_OFFICIAL_READONLY_ACQUISITION_SNAPSHOT_METADATA_v1",
                "release_id": RELEASE_ID,
                "acquisition_id": record["acquisition_id"],
                "official_endpoint_url": record["redacted_official_endpoint_url"],
                "allowlist_rule": record["allowlist_rule"],
                "expected_local_snapshot_ref": record["expected_local_snapshot_ref"],
                "snapshot_ref": record["snapshot_ref"],
                "status": record["status"],
                "http_status": record["http_status"],
                "byte_count": record["byte_count"],
                "sha256": record["sha256"],
                "source_bytes_sha256": record["sha256"],
                "content_type": record["content_type"],
                "order_record_ref": record["order_record_ref"],
                "order_record_sha256": record["order_record_sha256"],
                "pre_target_sequence_proof": record["pre_target_sequence_proof"],
                "hash_policy": HASH_POLICY,
                "locks": NO_SEND_LOCKS,
                "scientific_pass": False,
            }
            write_json(resolve_under_root(root, row["snapshot_metadata_ref"]), metadata)
            write_json(resolve_under_root(root, row["lock_ref"]), build_lock(record))
            return record
        if not transient or attempt_number == attempts_allowed:
            record["status"] = "FETCH_FAILED" if fetch_error else "HTTP_STATUS_NOT_SUCCESS"
            record["retry_queue_eligible"] = transient
            return record
        delay = retry_delay_seconds(headers, retry_delays, attempt_number - 1)
        attempts[-1]["applied_retry_delay_seconds"] = delay
        sleeper(delay)
    return record


def dry_run_record(row: dict[str, Any]) -> dict[str, Any]:
    return {
        **{key: value for key, value in row.items() if key != "network_official_endpoint_url"},
        "network_executed": False,
        "resume_reused_existing_acquisition": False,
        "network_skipped_reason": "",
        "http_status": 0,
        "byte_count": 0,
        "sha256": "",
        "content_type": "",
        "status": "DRY_RUN_NETWORK_NOT_EXECUTED" if row["validated_for_network"] else "VALIDATION_BLOCKED",
        "fetch_error": "",
        "network_attempt_total": 0,
        "retry_attempts": [],
        "retry_queue_eligible": False,
        "order_record_sha256": "",
        "pre_target_sequence_proof": {},
    }


def build_retry_queue(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    queue = []
    for record in records:
        if not record.get("retry_queue_eligible"):
            continue
        queue.append(
            {
                "acquisition_id": record["acquisition_id"],
                "packet_ref": record["packet_ref"],
                "official_endpoint_url": record["redacted_official_endpoint_url"],
                "snapshot_ref": record["snapshot_ref"],
                "status": record["status"],
                "http_status": record["http_status"],
                "network_attempt_total": record["network_attempt_total"],
                "fetch_error": record["fetch_error"],
                "next_action": "retry later with --execute-network after official source cool-down; do not infer scientific PASS",
            }
        )
    return queue


def build_report(
    root: Path,
    packet_paths: list[Path],
    *,
    execute_network: bool,
    force_refetch: bool = False,
    retry_delays: tuple[float, ...] = DEFAULT_RETRY_DELAYS_SECONDS,
    max_attempts: int | None = None,
    sleeper: Any = time.sleep,
) -> dict[str, Any]:
    raw_rows = load_packet_requests(root, packet_paths)
    validated_rows = [validate_request(row, require_execution_metadata=execute_network) for row in raw_rows]
    execution_readiness_rows = [validate_request(row, require_execution_metadata=True) for row in raw_rows]
    records = [
        execute_request(
            root,
            row,
            force_refetch=force_refetch,
            retry_delays=retry_delays,
            max_attempts=max_attempts,
            sleeper=sleeper,
        )
        if execute_network
        else dry_run_record(row)
        for row in validated_rows
    ]
    blockers = sorted({blocker for row in records for blocker in row["validation_blockers"]})
    acquired_total = sum(1 for row in records if row["status"] == "ACQUIRED_READONLY")
    blocked_total = sum(1 for row in records if row["status"] == "VALIDATION_BLOCKED")
    failed_total = sum(1 for row in records if row["status"] in {"FETCH_FAILED", "HTTP_STATUS_NOT_SUCCESS"})
    retry_queue = build_retry_queue(records)
    execution_blockers = sorted(
        {
            blocker
            for row in execution_readiness_rows
            for blocker in row["validation_blockers"]
            if blocker.startswith("PROSPECTIVE_LOCK_METADATA")
            or blocker
            in {
                "POST_SCORING_ACQUISITION_NOT_ALLOWED",
                "TARGET_UNSEALED_BEFORE_ACQUISITION_NOT_ALLOWED",
            }
        }
    )
    attempts_allowed = max(1, max_attempts if max_attempts is not None else len(retry_delays) + 1)
    report = {
        "schema_id": REPORT_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "generated_by": "tools/oc133_official_readonly_acquisition_runner.py",
        "mode": "execute_network_readonly" if execute_network else "dry_run_check",
        "packet_refs": [path.relative_to(root).as_posix() for path in packet_paths],
        "run_root_ref": RUN_ROOT_REL,
        "request_total": len(records),
        "validated_for_network_total": sum(1 for row in records if row["validated_for_network"]),
        "validation_blocked_total": blocked_total,
        "acquired_readonly_total": acquired_total,
        "resumed_acquired_readonly_total": sum(1 for row in records if row.get("resume_reused_existing_acquisition")),
        "network_failure_total": failed_total,
        "retry_queue_total": len(retry_queue),
        "open_blocker_total": len(blockers),
        "blockers": blockers,
        "retry_policy": {
            "max_attempts": attempts_allowed,
            "retry_delay_seconds": list(retry_delays),
            "transient_http_statuses": sorted(TRANSIENT_HTTP_STATUSES),
            "max_retry_delay_seconds": MAX_RETRY_DELAY_SECONDS,
            "force_refetch": force_refetch,
        },
        "retry_queue": retry_queue,
        "execution_blocker_packet": {
            "schema_id": "OC133_OFFICIAL_READONLY_ACQUISITION_EXECUTION_BLOCKER_PACKET_v1",
            "status": "BLOCKED" if execution_blockers or failed_total else "CLEAR",
            "remaining_execution_blockers": execution_blockers,
            "execution_ready_request_total": sum(1 for row in execution_readiness_rows if row["validated_for_network"]),
            "execution_validation_blocked_total": sum(
                1 for row in execution_readiness_rows if not row["validated_for_network"]
            ),
            "network_failure_total": failed_total,
            "policy": "Do not fake snapshots; execute only after packet-level prospective lock metadata is present and no public action is enabled.",
        },
        "retry_report": {
            "schema_id": "OC133_OFFICIAL_READONLY_ACQUISITION_RETRY_REPORT_v1",
            "queue_total": len(retry_queue),
            "success_after_retry_total": sum(
                1 for row in records if row["status"] == "ACQUIRED_READONLY" and row["network_attempt_total"] > 1
            ),
            "exhausted_retry_total": len(retry_queue),
            "scientific_pass": False,
            "policy": "Retry exhaustion is an acquisition work queue only; it is not a scientific PASS or FAIL.",
        },
        "records": records,
        "locks": NO_SEND_LOCKS,
        "scientific_pass": False,
        "grand_toe_support_allowed": False,
        "registry_write_allowed": False,
        "publish_allowed": False,
        "push_allowed": False,
        "policy": "Read-only acquisition pins official source bytes for later strict evidence factories; acquisition success is not scientific PASS.",
    }
    report["report_sha256"] = sha256_object({k: v for k, v in report.items() if k != "report_sha256"})
    return report


def write_reports(root: Path, report: dict[str, Any]) -> None:
    write_json(resolve_under_root(root, RUN_REPORT_REL), report)
    write_json(resolve_under_root(root, PUBLIC_REPORT_REL), report)


def check_stored(root: Path, packet_paths: list[Path]) -> list[str]:
    expected = build_report(root, packet_paths, execute_network=False)
    failures: list[str] = []
    for rel_path in (RUN_REPORT_REL, PUBLIC_REPORT_REL):
        path = resolve_under_root(root, rel_path)
        if not path.exists():
            failures.append(f"missing::{rel_path}")
            continue
        try:
            actual = read_json(path)
        except Exception as exc:
            failures.append(f"parse_error::{rel_path}::{exc.__class__.__name__}")
            continue
        if actual != expected:
            failures.append(f"mismatch::{rel_path}")
    return failures


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read-only official data acquisition runner for OC133 packets.")
    parser.add_argument("--root", default=str(repo_root()), help="repository root")
    parser.add_argument("--packet", action="append", default=[], help="acquisition packet path relative to root")
    parser.add_argument("--write", action="store_true", help="standard Logion capability alias for --write-report")
    parser.add_argument("--write-report", action="store_true", help="write dry-run or execute report artifacts")
    parser.add_argument("--check", action="store_true", help="check stored dry-run reports against current packets")
    parser.add_argument("--execute-network", action="store_true", help="perform explicit read-only HTTPS GET acquisition")
    parser.add_argument("--allow-blocked-exit-zero", action="store_true", help="return zero even with validation/fetch blockers")
    parser.add_argument("--force-refetch", "--force", action="store_true", help="refetch even when a valid acquired lock exists")
    parser.add_argument("--max-attempts", type=int, default=None, help="bounded network attempts per request")
    parser.add_argument(
        "--retry-delay-seconds",
        action="append",
        type=float,
        default=None,
        help="retry backoff delay; repeat to provide a sequence",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    packet_paths = packet_paths_from_args(root, args.packet)
    if not packet_paths:
        print(json.dumps({"status": "error", "error": "NO_ACQUISITION_PACKETS_FOUND"}, indent=2))
        return 1
    if args.check:
        failures = check_stored(root, packet_paths)
        if failures:
            for failure in failures:
                print(f"ERROR: {failure}")
            return 1
        print(json.dumps({"status": "ok", "checked": [RUN_REPORT_REL, PUBLIC_REPORT_REL]}, indent=2))
        return 0
    retry_delays = tuple(args.retry_delay_seconds) if args.retry_delay_seconds is not None else DEFAULT_RETRY_DELAYS_SECONDS
    report = build_report(
        root,
        packet_paths,
        execute_network=bool(args.execute_network),
        force_refetch=bool(args.force_refetch),
        retry_delays=retry_delays,
        max_attempts=args.max_attempts,
    )
    if args.write or args.write_report or args.execute_network:
        write_reports(root, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    has_blockers = bool(report["blockers"] or report["network_failure_total"])
    if has_blockers and not args.allow_blocked_exit_zero:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
