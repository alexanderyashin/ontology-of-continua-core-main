from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
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
RUN_REPORT_REL = f"{RUN_ROOT_REL}/OC133_OFFICIAL_READONLY_ACQUISITION_RUN.json"
PUBLIC_REPORT_REL = "reports/OC133_OFFICIAL_READONLY_ACQUISITION_RUN.json"
REPORT_JSON_REL = PUBLIC_REPORT_REL

REPORT_SCHEMA_ID = "OC133_OFFICIAL_READONLY_ACQUISITION_RUN_v1"
REQUEST_TIMEOUT_SECONDS = 30
MAX_RESPONSE_BYTES = 25 * 1024 * 1024
HASH_POLICY = "sha256 over acquired response bytes as stored"

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


ALLOWLIST: tuple[AllowRule, ...] = (
    AllowRule("NCBI EUtils", "eutils.ncbi.nlm.nih.gov", "/entrez/eutils/"),
    AllowRule("PubChem PUG REST", "pubchem.ncbi.nlm.nih.gov", "/rest/pug/"),
    AllowRule("World Bank API", "api.worldbank.org", "/v2/"),
    AllowRule("NIST physics constants", "physics.nist.gov", "/cuu/Constants/"),
    AllowRule("NIST Chemistry WebBook", "webbook.nist.gov", "/cgi/cbook.cgi"),
)


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
        if host == rule.host and parsed.path.startswith(rule.path_prefix):
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
                }
            )
    return requests


def validate_request(row: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    official_url = row["network_official_endpoint_url"]
    expected_ref = row["expected_local_snapshot_ref"]
    allowed, allowlist_rule, url_blockers = allowlist_match(official_url)
    blockers.extend(url_blockers)
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
    with urllib.request.urlopen(request, timeout=timeout) as response:
        data = response.read(MAX_RESPONSE_BYTES + 1)
        if len(data) > MAX_RESPONSE_BYTES:
            raise ValueError("response exceeds MAX_RESPONSE_BYTES")
        return response_status(response), response_headers(response), data


def build_lock(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_id": "OC133_OFFICIAL_READONLY_ACQUISITION_NO_SEND_LOCK_v1",
        "release_id": RELEASE_ID,
        "acquisition_id": record["acquisition_id"],
        "official_endpoint_url": record["redacted_official_endpoint_url"],
        "expected_local_snapshot_ref": record["expected_local_snapshot_ref"],
        "snapshot_ref": record["snapshot_ref"],
        "snapshot_sha256": record["sha256"],
        "byte_count": record["byte_count"],
        "http_status": record["http_status"],
        "hash_policy": HASH_POLICY,
        "locks": NO_SEND_LOCKS,
        "scientific_pass": False,
        "policy": "Acquisition success only pins official bytes for strict evidence factories; it is not a scientific PASS.",
    }


def execute_request(root: Path, row: dict[str, Any]) -> dict[str, Any]:
    record = {
        **{key: value for key, value in row.items() if key != "network_official_endpoint_url"},
        "network_executed": True,
        "http_status": 0,
        "byte_count": 0,
        "sha256": "",
        "content_type": "",
        "status": "FETCH_FAILED",
        "fetch_error": "",
    }
    if not row["validated_for_network"]:
        record["network_executed"] = False
        record["status"] = "VALIDATION_BLOCKED"
        return record
    try:
        status, headers, data = fetch_official_url(row["network_official_endpoint_url"])
    except (urllib.error.URLError, OSError, ValueError) as exc:
        record["fetch_error"] = f"{exc.__class__.__name__}: {exc}"
        return record
    digest = sha256_bytes(data)
    record.update(
        {
            "http_status": status,
            "byte_count": len(data),
            "sha256": digest,
            "content_type": headers.get("content-type", ""),
            "status": "ACQUIRED_READONLY" if 200 <= status < 300 else "HTTP_STATUS_NOT_SUCCESS",
        }
    )
    write_bytes(resolve_under_root(root, row["snapshot_ref"]), data)
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
        "content_type": record["content_type"],
        "hash_policy": HASH_POLICY,
        "locks": NO_SEND_LOCKS,
        "scientific_pass": False,
    }
    write_json(resolve_under_root(root, row["snapshot_metadata_ref"]), metadata)
    write_json(resolve_under_root(root, row["lock_ref"]), build_lock(record))
    return record


def dry_run_record(row: dict[str, Any]) -> dict[str, Any]:
    return {
        **{key: value for key, value in row.items() if key != "network_official_endpoint_url"},
        "network_executed": False,
        "http_status": 0,
        "byte_count": 0,
        "sha256": "",
        "content_type": "",
        "status": "DRY_RUN_NETWORK_NOT_EXECUTED" if row["validated_for_network"] else "VALIDATION_BLOCKED",
        "fetch_error": "",
    }


def build_report(root: Path, packet_paths: list[Path], *, execute_network: bool) -> dict[str, Any]:
    raw_rows = load_packet_requests(root, packet_paths)
    validated_rows = [validate_request(row) for row in raw_rows]
    records = [execute_request(root, row) if execute_network else dry_run_record(row) for row in validated_rows]
    blockers = sorted({blocker for row in records for blocker in row["validation_blockers"]})
    acquired_total = sum(1 for row in records if row["status"] == "ACQUIRED_READONLY")
    blocked_total = sum(1 for row in records if row["status"] == "VALIDATION_BLOCKED")
    failed_total = sum(1 for row in records if row["status"] in {"FETCH_FAILED", "HTTP_STATUS_NOT_SUCCESS"})
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
        "network_failure_total": failed_total,
        "open_blocker_total": len(blockers),
        "blockers": blockers,
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
    report = build_report(root, packet_paths, execute_network=bool(args.execute_network))
    if args.write or args.write_report or args.execute_network:
        write_reports(root, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    has_blockers = bool(report["blockers"] or report["network_failure_total"])
    if has_blockers and not args.allow_blocked_exit_zero:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
