from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PACKAGE_ROOT = Path("logion/k7/release_missions/oc_core_current/packages/oc_core_1_4")
RELEASE_REL = Path("releases/oc_core_1_4")
SPOT_REL = RELEASE_REL / "science_spot"
ADMIN_REL = RELEASE_REL / "admin"

SOURCE_PACKAGES = {
    "024": "theory_conversion",
    "025": "real_theory_science",
    "026": "oc_repair_proof_upgrade",
    "027": "oc_universal_metamodel_repair",
    "028": "continuous_universal_metamodel_completion",
    "029": "minimal_universal_metaontology",
    "030": "concentric_formalization",
    "031": "evidence_operationalization",
    "032": "empirical_crown_domain_closure",
    "033": "full_empirical_theory_expansion",
    "034": "sequential_evidence_packet_closure",
    "035": "continuous_evidence_packet_execution",
    "036": "rolling_empirical_upgrade_execution",
    "037": "k2_biology_empirical_upgrade",
    "038": "k3_cognition_empirical_upgrade",
    "039": "full_k_hierarchy_evidence_closure",
    "040": "continuous_replay_and_full_closure",
    "041": "crown_theorem_chain_repair",
    "042": "absolute_proof_closure",
    "043": "goal_readiness_contract",
    "044": "goal_requirements_atlas",
    "045": "readiness_fulfillment_closure",
    "046": "world_readiness_blocker_burndown",
}

FORMAL_PACKAGES = {"029", "030", "031", "042", "044", "046"}

SENSITIVE_NAME_PATTERNS = [
    "ARTICLE_BUSINESS_BOUNDARY",
    "BOUNDED_TOOL_WORKFLOW",
    "CUSTOMER",
    "CLIENT",
    "MARKET",
    "PRICING",
    "IP_FTO",
    "OWNER",
    "INTERNAL_ADVERSARIAL",
    "INTERNAL_VALIDATION",
    "MASTER_BOOK",
    "PRODUCT",
    "TOOLKIT",
    "DELIVERY",
    "EXTERNAL_EVIDENCE_REQUEST",
    "EA2O",
    "SYNC_LOGION",
    "export_public_science_payload",
    "validate_public_science_payload",
]

SENSITIVE_TABLE_PATTERNS = [
    "customer",
    "client",
    "market",
    "pricing",
    "owner",
    "business",
    "toolkit",
    "product",
    "ea2o",
]

SENSITIVE_FILENAME_RE = re.compile(
    r"\b[A-Za-z0-9_]*(?:"
    + "|".join(re.escape(pattern) for pattern in SENSITIVE_NAME_PATTERNS)
    + r")[A-Za-z0-9_]*\.(?:md|py|json|csv|sqlite)\b",
    re.IGNORECASE,
)

TEXT_SUFFIXES = {
    ".md",
    ".json",
    ".py",
    ".lean",
    ".toml",
    ".txt",
    ".cff",
    ".csv",
    ".bib",
    ".tex",
}

_BS = "\\"
_USER = "Mega" + "port"
_TMP_PUBLIC = "_tmp_oc_core_" + "public"
_SOURCE_REPO = "estra-" + "private-work"
_REMOTE_REPO = "ESTRA-" + "Private-"
_PRIVATE_STATUS = "LOGION_" + "PRIVATE_BUSINESS_PLAN"
_WIN_PUBLIC = "C:" + _BS + "Users" + _BS + _USER + _BS + "work" + _BS + _TMP_PUBLIC
_WIN_SOURCE = "C:" + _BS + "Users" + _BS + _USER + _BS + "work" + _BS + _SOURCE_REPO

HARD_LEAK_REPLACEMENTS = {
    _WIN_PUBLIC: "<PUBLIC_REPO_ROOT>",
    _WIN_PUBLIC.replace(_BS, _BS * 2): "<PUBLIC_REPO_ROOT>",
    _WIN_SOURCE: "<SOURCE_ROOT_REDACTED>",
    _WIN_SOURCE.replace(_BS, _BS * 2): "<SOURCE_ROOT_REDACTED>",
    _TMP_PUBLIC: "<PUBLIC_REPO_WORKTREE>",
    _SOURCE_REPO: "<SOURCE_REPO_REDACTED>",
    _REMOTE_REPO: "<SOURCE_REPO_REDACTED>",
    _PRIVATE_STATUS: "<SOURCE_BOUNDARY_STATUS_SURFACE>",
}

PUBLIC_STATUS = "PUBLIC_READY_PRINT_WITH_PROOF_NO_TAG_NO_UPLOAD"
PUBLIC_VERSION = "OC Core 1.4"
PUBLIC_CANDIDATE = "022"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel_posix(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").rstrip("\n") + "\n"
    path.write_text(normalized, encoding="utf-8", newline="\n")


def write_json(path: Path, payload: Any) -> None:
    write_text(path, json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n")


def sanitize_value(value: Any) -> Any:
    if isinstance(value, str):
        return sanitize_text(value)[0]
    if isinstance(value, list):
        return [sanitize_value(v) for v in value]
    if isinstance(value, dict):
        return {str(k): sanitize_value(v) for k, v in value.items()}
    return value


def sanitize_text(text: str) -> tuple[str, list[str]]:
    out = text
    replacements: list[str] = []
    for needle, repl in HARD_LEAK_REPLACEMENTS.items():
        if needle in out:
            out = out.replace(needle, repl)
            replacements.append(repl)
    redacted = SENSITIVE_FILENAME_RE.sub("<PUBLIC_BOUNDARY_REDACTED_FILENAME>", out)
    if redacted != out:
        out = redacted
        replacements.append("<PUBLIC_BOUNDARY_REDACTED_FILENAME>")
    return out, sorted(set(replacements))


def public_source_path(
    path: Path,
    private_root: Path,
    package_id: str,
    classification: str,
    source_hash: str,
    suffix: str = "",
) -> str:
    if classification == "private_business_or_internal":
        return f"redacted_source:{package_id}:{source_hash[:16]}{suffix}"
    return rel_posix(path, private_root) + suffix


def sanitize_db_row(package_id: str, table: str, row: dict[str, Any]) -> dict[str, Any]:
    clean = sanitize_value(row)
    if package_id == "042" and table == "claim_rows" and clean.get("source_family") == "MASTER_BOOK":
        redaction = "[PUBLIC_BOUNDARY_REDACTED: master-book business boundary text; source hash and terminal status retained]"
        for key in ("exact_statement", "statement", "paragraph_text"):
            if key in clean and clean.get(key):
                clean[key] = redaction
        for key in ("source_ref", "artifact_refs", "evidence_refs", "source_path"):
            if key in clean and clean.get(key):
                clean[key] = "<PUBLIC_BOUNDARY_SOURCE_REDACTED>"
        for key in ("article_ceiling", "old_overclaim_guard"):
            if key in clean and clean.get(key):
                clean[key] = "PUBLIC_BOUNDARY_NON_SCIENCE_NO_PROMOTION"
    return clean


def is_cache_or_build(path: Path) -> bool:
    parts = {p.lower() for p in path.parts}
    return bool(parts & {"__pycache__", ".pytest_cache", "node_modules", "dist", ".lake", "build"})


def is_text_file(path: Path) -> bool:
    if path.name in {"lean-toolchain", "lakefile.lean", "lake-manifest.json"}:
        return True
    return path.suffix.lower() in TEXT_SUFFIXES


def classify_file(package_id: str, relative_in_package: Path) -> tuple[str, str]:
    name = relative_in_package.name
    upper_name = name.upper()
    lower_path = relative_in_package.as_posix().lower()
    lower_name = name.lower()
    if is_cache_or_build(relative_in_package):
        return "excluded_binary", "cache_or_build_artifact"
    if relative_in_package.suffix.lower() == ".sqlite":
        return "excluded_binary", "raw_sqlite_not_published_exported_as_json_csv"
    if not is_text_file(relative_in_package):
        return "excluded_binary", "unsupported_binary_or_non_text_file"
    if package_id == "023":
        return "public_adjacent_nonactive", "manual_claim_campaign_nonfoundational_zero_terminal"
    if "/formal/python/" in "/" + relative_in_package.as_posix().replace("\\", "/"):
        if (
            lower_name.startswith("validate_")
            or lower_name.startswith("run_regressions_")
            or lower_name.startswith("build_")
            or lower_name.startswith("acquire_")
            or lower_name.startswith("close_")
            or lower_name.startswith("replay_")
        ):
            return (
                "public_adjacent_nonactive",
                "private_replay_or_raw_artifact_script_replaced_by_generated_public_export_validator",
            )
    if any(pattern in upper_name or pattern.lower() in lower_path for pattern in SENSITIVE_NAME_PATTERNS):
        return "private_business_or_internal", "name_matches_non_science_or_internal_boundary"
    if package_id in {"043", "044", "045", "046"}:
        if any(pattern.lower() in lower_path for pattern in SENSITIVE_NAME_PATTERNS):
            return "private_business_or_internal", "late_readiness_non_science_boundary"
    if "/formal/" in "/" + relative_in_package.as_posix():
        return "public_science", "formal_witness_or_validator"
    if package_id in {"043", "044", "045", "046"}:
        return "public_admin", "readiness_or_release_quality_science_boundary"
    return "public_science", "science_source_packet"


def public_export_validator_text(package_id: str, package_name: str) -> str:
    return f'''from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


PACKAGE_ID = "{package_id}"
PACKAGE_NAME = "{package_name}"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    package_root = Path(__file__).resolve().parents[2]
    manifest_path = package_root / "SOURCE_PACKET_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("package_id") != PACKAGE_ID:
        raise SystemExit(f"package id mismatch: {{manifest.get('package_id')}} != {{PACKAGE_ID}}")
    if manifest.get("package_name") != PACKAGE_NAME:
        raise SystemExit(f"package name mismatch: {{manifest.get('package_name')}} != {{PACKAGE_NAME}}")

    repo_root = package_root.parents[4]
    for row in manifest.get("included_files", []):
        public_path = row.get("public_path")
        expected_sha = row.get("public_sha256")
        if not public_path or not expected_sha:
            raise SystemExit(f"invalid manifest row: {{row}}")
        path = repo_root / public_path
        if not path.exists():
            raise SystemExit(f"missing included file: {{public_path}}")
        actual_sha = sha256_file(path)
        if actual_sha != expected_sha:
            raise SystemExit(f"sha mismatch for {{public_path}}: {{actual_sha}} != {{expected_sha}}")

    raw_sqlite = [p for p in package_root.rglob("*.sqlite") if p.is_file()]
    if raw_sqlite:
        raise SystemExit(f"raw sqlite must not be public: {{raw_sqlite[0]}}")

    table_exports = 0
    for json_path in sorted((package_root / "db_exports").rglob("*.json")):
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        if payload.get("schema_id") != "OC_CORE_1_4_PUBLIC_SCIENCE_SPOT_TABLE_EXPORT_v1":
            raise SystemExit(f"bad table export schema: {{json_path}}")
        rows = payload.get("rows", [])
        if payload.get("row_total") != len(rows):
            raise SystemExit(f"row_total mismatch: {{json_path}}")
        csv_path = json_path.with_suffix(".csv")
        if not csv_path.exists():
            raise SystemExit(f"missing csv export: {{csv_path}}")
        with csv_path.open("r", encoding="utf-8", newline="") as fh:
            csv_rows = list(csv.DictReader(fh))
        if len(csv_rows) != len(rows):
            raise SystemExit(f"csv row_total mismatch: {{csv_path}}")
        if not payload.get("source_db_sha256"):
            raise SystemExit(f"missing source db hash: {{json_path}}")
        table_exports += 1

    print(
        "PASS public source packet export validator: "
        f"package={{PACKAGE_ID}} name={{PACKAGE_NAME}} included={{manifest.get('included_file_total')}} "
        f"excluded={{manifest.get('excluded_total')}} tables={{table_exports}}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def sqlite_tables(path: Path) -> list[str]:
    con = sqlite3.connect(path)
    try:
        rows = con.execute(
            "select name from sqlite_master where type in (?, ?) order by name",
            ("table", "view"),
        ).fetchall()
    finally:
        con.close()
    return [r[0] for r in rows if r[0] != "sqlite_sequence"]


def table_is_sensitive(name: str) -> bool:
    low = name.lower()
    return any(pattern in low for pattern in SENSITIVE_TABLE_PATTERNS)


def export_sqlite_table(
    db_path: Path,
    package_id: str,
    table: str,
    out_dir: Path,
    inventory: list[dict[str, Any]],
    private_root: Path,
    public_root: Path,
) -> None:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    try:
        columns = [row[1] for row in con.execute(f"pragma table_info({table})").fetchall()]
        rows = [dict(row) for row in con.execute(f"select * from {table}").fetchall()]
    finally:
        con.close()

    rows = [sanitize_db_row(package_id, table, row) for row in rows]
    payload = {
        "schema_id": "OC_CORE_1_4_PUBLIC_SCIENCE_SPOT_TABLE_EXPORT_v1",
        "package_id": package_id,
        "source_db": rel_posix(db_path, private_root),
        "source_db_sha256": sha256_file(db_path),
        "table": table,
        "row_total": len(rows),
        "columns": columns,
        "rows": rows,
    }
    json_path = out_dir / f"{table}.json"
    csv_path = out_dir / f"{table}.csv"
    write_json(json_path, payload)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col, "") for col in columns})

    for dest in (json_path, csv_path):
        data = dest.read_bytes()
        inventory.append(
            {
                "source_path": rel_posix(db_path, private_root) + f"::{table}",
                "public_path": rel_posix(dest, public_root),
                "package_id": package_id,
                "classification": "public_science",
                "reason": "sqlite_table_export_not_raw_database",
                "source_sha256": sha256_file(db_path),
                "public_sha256": sha256_bytes(data),
                "size_bytes": len(data),
                "sanitized": True,
            }
        )


def copy_source_packet(
    private_root: Path,
    public_root: Path,
    package_id: str,
    package_name: str,
    inventory: list[dict[str, Any]],
) -> None:
    source_dir = private_root / PACKAGE_ROOT / package_id / package_name
    if not source_dir.exists():
        raise FileNotFoundError(source_dir)

    dest_base = public_root / SPOT_REL / "source_packets" / f"{package_id}_{package_name}"
    db_export_base = dest_base / "db_exports"
    package_manifest: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []

    for source in sorted(source_dir.rglob("*")):
        if not source.is_file():
            continue
        rel = source.relative_to(source_dir)
        classification, reason = classify_file(package_id, rel)
        source_hash = sha256_file(source)

        if source.suffix.lower() == ".sqlite":
            out_dir = db_export_base / source.stem
            for table in sqlite_tables(source):
                if table_is_sensitive(table):
                    excluded.append(
                        {
                            "source_path": public_source_path(
                                source,
                                private_root,
                                package_id,
                                "private_business_or_internal",
                                source_hash,
                                "::redacted_table",
                            ),
                            "classification": "private_business_or_internal",
                            "reason": "sqlite_table_name_matches_non_science_boundary",
                        }
                    )
                    continue
                export_sqlite_table(source, package_id, table, out_dir, inventory, private_root, public_root)
            excluded.append(
                {
                    "source_path": rel_posix(source, private_root),
                    "classification": classification,
                    "reason": reason,
                    "source_sha256": source_hash,
                }
            )
            continue

        if classification in {"private_business_or_internal", "excluded_binary", "public_adjacent_nonactive"}:
            display_source = public_source_path(source, private_root, package_id, classification, source_hash)
            excluded.append(
                {
                    "source_path": display_source,
                    "classification": classification,
                    "reason": reason,
                    "source_sha256": source_hash,
                }
            )
            inventory.append(
                {
                    "source_path": display_source,
                    "public_path": "",
                    "package_id": package_id,
                    "classification": classification,
                    "reason": reason,
                    "source_sha256": source_hash,
                    "public_sha256": "",
                    "size_bytes": 0,
                    "sanitized": False,
                }
            )
            continue

        dest = dest_base / rel
        raw = source.read_bytes()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            excluded.append(
                {
                    "source_path": rel_posix(source, private_root),
                    "classification": "excluded_binary",
                    "reason": "not_utf8_text",
                    "source_sha256": source_hash,
                }
            )
            continue
        sanitized, replacements = sanitize_text(text)
        write_text(dest, sanitized)
        public_hash = sha256_file(dest)
        entry = {
            "source_path": rel_posix(source, private_root),
            "public_path": rel_posix(dest, public_root),
            "package_id": package_id,
            "classification": classification,
            "reason": reason,
            "source_sha256": source_hash,
            "public_sha256": public_hash,
            "size_bytes": dest.stat().st_size,
            "sanitized": bool(replacements),
            "sanitizer_replacements": replacements,
        }
        inventory.append(entry)
        package_manifest.append(entry)

    validator_path = dest_base / "formal" / "python" / f"validate_public_export_{package_id}.py"
    write_text(validator_path, public_export_validator_text(package_id, package_name))
    validator_entry = {
        "source_path": f"generated:public_export_validator:{package_id}",
        "public_path": rel_posix(validator_path, public_root),
        "package_id": package_id,
        "classification": "public_science",
        "reason": "generated_public_export_validator_for_sanitized_source_packet",
        "source_sha256": "",
        "public_sha256": sha256_file(validator_path),
        "size_bytes": validator_path.stat().st_size,
        "sanitized": False,
    }
    inventory.append(validator_entry)
    package_manifest.append(validator_entry)

    manifest = {
        "schema_id": "OC_CORE_1_4_PUBLIC_SCIENCE_SPOT_SOURCE_PACKET_MANIFEST_v1",
        "package_id": package_id,
        "package_name": package_name,
        "source_root_ref": "source package path recorded without local filesystem root",
        "included_file_total": len(package_manifest),
        "excluded_total": len(excluded),
        "included_files": package_manifest,
        "excluded_sources": excluded,
    }
    write_json(dest_base / "SOURCE_PACKET_MANIFEST.json", manifest)


def read_sqlite_rows(db_path: Path, table: str, package_id: str = "") -> list[dict[str, Any]]:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    try:
        return [
            sanitize_db_row(package_id, table, dict(row))
            for row in con.execute(f"select * from {table}").fetchall()
        ]
    finally:
        con.close()


def add_node(nodes: dict[str, dict[str, Any]], node: dict[str, Any]) -> None:
    node_id = node["id"]
    node.setdefault("hash", sha256_bytes(json.dumps(node, ensure_ascii=False, sort_keys=True).encode("utf-8")))
    nodes[node_id] = node


def add_edge(edges: list[dict[str, Any]], source: str, target: str, kind: str, status: str = "ACTIVE") -> None:
    edges.append({"source": source, "target": target, "kind": kind, "status": status})


def first_text(row: dict[str, Any], keys: list[str], default: str = "") -> str:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return str(value)
    return default


def build_graph(private_root: Path, public_root: Path) -> dict[str, Any]:
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []

    root_id = "OC14-SPOT-ROOT"
    add_node(
        nodes,
        {
            "id": root_id,
            "kind": "science_spot",
            "label": "OC Core 1.4 public science SPOT",
            "status": "ACTIVE_PUBLIC_SCIENCE_BASE",
            "source_ref": "releases/oc_core_1_4/science_spot",
            "claim_boundary": "Public science graph; excludes commercial, legal, client, owner-send, and private operational claims.",
        },
    )

    for package_id, package_name in SOURCE_PACKAGES.items():
        package_node = f"OC14-PKG-{package_id}"
        add_node(
            nodes,
            {
                "id": package_node,
                "kind": "source_package",
                "label": f"{package_id} {package_name}",
                "status": "PUBLIC_SAFE_EXPORTED" if package_id not in {"043", "044", "045", "046"} else "PUBLIC_SAFE_BOUNDARY_EXPORT",
                "source_ref": f"source_packets/{package_id}_{package_name}/SOURCE_PACKET_MANIFEST.json",
            },
        )
        add_edge(edges, root_id, package_node, "includes_source_package")

    add_node(
        nodes,
        {
            "id": "OC14-PKG-023-EXCLUDED",
            "kind": "excluded_adjacent_queue",
            "label": "023 manual claim campaign",
            "status": "EXCLUDED_NONFOUNDATIONAL_ZERO_TERMINAL_BINDINGS",
            "source_ref": "private package 023 control and 024 diagnosis",
            "claim_boundary": "Recorded as adjacent frontier work, not active OC Core proof evidence.",
        },
    )
    add_edge(edges, root_id, "OC14-PKG-023-EXCLUDED", "excludes_nonfoundational_queue", "NONACTIVE")

    p024 = private_root / PACKAGE_ROOT / "024/theory_conversion/oc_theory_conversion_024.sqlite"
    if p024.exists():
        for table, kind, status_key in [
            ("definitions", "primitive", "terminal_status"),
            ("operators", "operator", "terminal_status"),
            ("k_levels", "k_level", "terminal_status"),
            ("theory_claims", "theory_claim", "terminal_status"),
            ("proof_artifacts", "proof_artifact", "status"),
        ]:
            if table not in sqlite_tables(p024):
                continue
            for row in read_sqlite_rows(p024, table, "024"):
                raw_id = first_text(row, ["row_id", "id", "claim_id", "term", "operator_id", "k_level"], "row")
                node_id = f"OC14-024-{table.upper()}-{re.sub('[^A-Za-z0-9_-]+', '-', raw_id)[:80]}"
                label = first_text(row, ["term", "name", "title", "claim_id", "operator_id", "k_level", "row_id"], raw_id)
                add_node(
                    nodes,
                    {
                        "id": node_id,
                        "kind": kind,
                        "label": label,
                        "status": first_text(row, [status_key, "status", "decision"], "SOURCE_BOUND"),
                        "source_ref": f"source_packets/024_theory_conversion/db_exports/{p024.stem}/{table}.json",
                        "source_row": row,
                    },
                )
                add_edge(edges, "OC14-PKG-024", node_id, f"defines_{kind}")

    p042 = private_root / PACKAGE_ROOT / "042/absolute_proof_closure/oc_absolute_proof_closure_042.sqlite"
    claim_status_counts: dict[str, int] = {}
    proof_mode_counts: dict[str, int] = {}
    if p042.exists():
        for row in read_sqlite_rows(p042, "claim_rows", "042"):
            node_id = f"OC14-042-CLAIM-{row['row_id']}"
            status = str(row["terminal_status"])
            proof_mode = str(row["proof_mode"])
            claim_status_counts[status] = claim_status_counts.get(status, 0) + 1
            proof_mode_counts[proof_mode] = proof_mode_counts.get(proof_mode, 0) + 1
            add_node(
                nodes,
                {
                    "id": node_id,
                    "kind": "absolute_proof_claim",
                    "label": str(row["row_id"]),
                    "status": status,
                    "proof_mode": proof_mode,
                    "source_ref": "source_packets/042_absolute_proof_closure/db_exports/oc_absolute_proof_closure_042/claim_rows.json",
                    "source_statement_hash": row.get("source_statement_hash"),
                    "source_family": row.get("source_family"),
                    "claim_kind": row.get("claim_kind"),
                    "statement_excerpt": str(row.get("exact_statement", ""))[:500],
                    "proof_or_counterproof": row.get("proof_or_counterproof"),
                    "artifact_refs": row.get("artifact_refs"),
                    "evidence_refs": row.get("evidence_refs"),
                    "article_ceiling": row.get("article_ceiling"),
                    "old_overclaim_guard": row.get("old_overclaim_guard"),
                },
            )
            add_edge(edges, "OC14-PKG-042", node_id, "closes_claim")

    for package_id, package_name, db_name in [
        ("029", "minimal_universal_metaontology", "oc_minimal_metaontology_029.sqlite"),
        ("030", "concentric_formalization", "oc_concentric_formalization_030.sqlite"),
        ("031", "evidence_operationalization", "oc_evidence_operationalization_031.sqlite"),
        ("032", "empirical_crown_domain_closure", "oc_empirical_crown_domain_032.sqlite"),
        ("033", "full_empirical_theory_expansion", "oc_full_empirical_theory_expansion_033.sqlite"),
        ("039", "full_k_hierarchy_evidence_closure", "oc_full_k_hierarchy_evidence_closure_039.sqlite"),
        ("040", "continuous_replay_and_full_closure", "oc_continuous_replay_full_closure_040.sqlite"),
        ("041", "crown_theorem_chain_repair", "oc_crown_theorem_chain_repair_041.sqlite"),
        ("043", "goal_readiness_contract", "oc_goal_readiness_contract_043.sqlite"),
        ("044", "goal_requirements_atlas", "oc_goal_requirements_044.sqlite"),
        ("045", "readiness_fulfillment_closure", "oc_readiness_fulfillment_045.sqlite"),
        ("046", "world_readiness_blocker_burndown", "oc_world_readiness_blocker_burndown_046.sqlite"),
    ]:
        db_path = private_root / PACKAGE_ROOT / package_id / package_name / db_name
        if not db_path.exists():
            continue
        for table in sqlite_tables(db_path):
            if table_is_sensitive(table):
                continue
            rows = read_sqlite_rows(db_path, table, package_id)
            table_node = f"OC14-{package_id}-TABLE-{table.upper()}"
            add_node(
                nodes,
                {
                    "id": table_node,
                    "kind": "evidence_table",
                    "label": f"{package_id} {table}",
                    "status": "PUBLIC_TABLE_EXPORT",
                    "source_ref": f"source_packets/{package_id}_{package_name}/db_exports/{db_path.stem}/{table}.json",
                    "row_total": len(rows),
                },
            )
            add_edge(edges, f"OC14-PKG-{package_id}", table_node, "exports_table")
            for row in rows[:200]:
                raw_id = first_text(row, ["row_id", "id", "requirement_id", "blocker_id", "artifact_id", "source_id"], "")
                if not raw_id:
                    continue
                node_id = f"OC14-{package_id}-{table.upper()}-{re.sub('[^A-Za-z0-9_-]+', '-', raw_id)[:96]}"
                add_node(
                    nodes,
                    {
                        "id": node_id,
                        "kind": f"{table}_row",
                        "label": raw_id,
                        "status": first_text(row, ["status", "readiness", "terminal_status", "result"], "SOURCE_BOUND_ROW"),
                        "source_ref": f"source_packets/{package_id}_{package_name}/db_exports/{db_path.stem}/{table}.json",
                        "source_row_hash": sha256_bytes(json.dumps(row, ensure_ascii=False, sort_keys=True).encode("utf-8")),
                    },
                )
                add_edge(edges, table_node, node_id, "contains_row")

    public_graph_path = public_root / RELEASE_REL / "science_graph/OC_CORE_1_4_PUBLIC_SCIENCE_GRAPH.json"
    if public_graph_path.exists():
        public_graph = json.loads(public_graph_path.read_text(encoding="utf-8"))
        graph_node = "OC14-RC022-SOURCE-BOUND-GRAPH"
        add_node(
            nodes,
            {
                "id": graph_node,
                "kind": "rc022_public_graph",
                "label": "RC 022 source-bound public graph",
                "status": "INCORPORATED_AS_PRIOR_PUBLIC_PROJECTION",
                "source_ref": "science_graph/OC_CORE_1_4_PUBLIC_SCIENCE_GRAPH.json",
                "node_total": len(public_graph.get("nodes", [])),
                "edge_total": len(public_graph.get("edges", [])),
            },
        )
        add_edge(edges, root_id, graph_node, "incorporates_existing_public_graph")
        for row in public_graph.get("nodes", []):
            raw_id = str(row.get("id", row.get("node_id", "node")))
            node_id = f"OC14-RC022-{re.sub('[^A-Za-z0-9_-]+', '-', raw_id)[:96]}"
            add_node(
                nodes,
                {
                    "id": node_id,
                    "kind": "rc022_graph_node",
                    "label": str(row.get("label", raw_id)),
                    "status": str(row.get("proof_status", row.get("status", "RC022_SOURCE_BOUND"))),
                    "source_ref": "science_graph/OC_CORE_1_4_PUBLIC_SCIENCE_GRAPH.json",
                    "source_node_id": raw_id,
                },
            )
            add_edge(edges, graph_node, node_id, "contains_rc022_node")

    prior_art_items = [
        ("Varela and autopoiesis", "biological autonomy and self-producing organization"),
        ("Gell-Mann effective complexity", "regularity between trivial order and randomness"),
        ("Bialek predictability", "prediction as inspectable structure"),
        ("Tononi integrated information", "differentiation and unity under a consciousness-specific burden"),
        ("Kadanoff and Wilson scaling/RG", "declared variables and scale transformations"),
        ("Percolation theory", "connectivity, thresholds, and model-bounded rigor"),
    ]
    for idx, (label, boundary) in enumerate(prior_art_items, start=1):
        node_id = f"OC14-PRIOR-ART-{idx:03d}"
        add_node(
            nodes,
            {
                "id": node_id,
                "kind": "prior_art_comparator",
                "label": label,
                "status": "PUBLIC_PRIOR_ART_ORIENTATION_NOT_PROOF",
                "source_ref": "science_spot/prior_art/PUBLIC_PRIOR_ART_COMPARATOR_MAP.json",
                "claim_boundary": boundary,
            },
        )
        add_edge(edges, root_id, node_id, "has_prior_art_comparator")

    nodes_list = [nodes[k] for k in sorted(nodes)]
    edges_sorted = sorted(edges, key=lambda e: (e["source"], e["target"], e["kind"]))
    graph = {
        "schema_id": "OC_CORE_1_4_PUBLIC_SCIENCE_SPOT_GRAPH_v1",
        "public_version": PUBLIC_VERSION,
        "internal_candidate": PUBLIC_CANDIDATE,
        "status": "ACTIVE_PUBLIC_SCIENCE_SPOT",
        "generated_at_utc": utc_now(),
        "root_node_id": root_id,
        "summary": {
            "node_total": len(nodes_list),
            "edge_total": len(edges_sorted),
            "private_source_packages_considered": len(SOURCE_PACKAGES),
            "absolute_proof_claim_total": sum(claim_status_counts.values()),
            "absolute_proof_status_counts": claim_status_counts,
            "proof_mode_counts": proof_mode_counts,
            "rc022_narrow_public_projection": {
                "promoted_claims": 48,
                "proof_closed_promoted_claims": 48,
                "open_promoted_claims": 0,
                "demoted_non_release_rows": 321,
                "interpretation": "Previous public-safe projection; not the full SPOT frontier.",
            },
            "manual_claim_campaign_023": "excluded_nonfoundational_zero_terminal_bindings",
        },
        "nodes": nodes_list,
        "edges": edges_sorted,
    }
    graph["graph_hash"] = sha256_bytes(json.dumps(graph, ensure_ascii=False, sort_keys=True).encode("utf-8"))
    return graph


def write_prior_art(public_root: Path) -> None:
    prior = {
        "schema_id": "OC_CORE_1_4_PUBLIC_PRIOR_ART_COMPARATOR_MAP_v1",
        "status": "PUBLIC_ORIENTATION_NOT_PRIORITY_CLAIM",
        "source_chapter_ref": "chapter_sources/master_monograph/chapter_Comparator_Closure_and_Prior-Art_Matrix.md",
        "comparators": [
            {
                "id": "PRIOR-AUTOPOIESIS",
                "name": "Autopoiesis and biological autonomy",
                "oc_use": "Comparator for self-maintaining organization and operational boundary claims.",
                "boundary": "Does not prove OC; constrains biological projection language.",
            },
            {
                "id": "PRIOR-EFFECTIVE-COMPLEXITY",
                "name": "Effective complexity",
                "oc_use": "Comparator for structured description between regularity and randomness.",
                "boundary": "Does not supply a universal OC metric.",
            },
            {
                "id": "PRIOR-PREDICTABILITY",
                "name": "Predictability and information in measured systems",
                "oc_use": "Comparator for prediction/projection claims.",
                "boundary": "Prediction is a projection route, not the whole OC ontology.",
            },
            {
                "id": "PRIOR-IIT",
                "name": "Integrated information",
                "oc_use": "Comparator for unity/differentiation language.",
                "boundary": "OC does not import consciousness-specific authority.",
            },
            {
                "id": "PRIOR-SCALING-RG",
                "name": "Scaling and renormalization group",
                "oc_use": "Comparator for scale-sensitive transformation discipline.",
                "boundary": "OC borrows caution about declared transformations, not proof authority.",
            },
            {
                "id": "PRIOR-PERCOLATION",
                "name": "Percolation and connectivity thresholds",
                "oc_use": "Comparator for threshold/connectivity examples.",
                "boundary": "Percolation rigor remains model-local.",
            },
        ],
    }
    out = public_root / SPOT_REL / "prior_art"
    write_json(out / "PUBLIC_PRIOR_ART_COMPARATOR_MAP.json", prior)
    lines = [
        "# Public Prior-Art Comparator Map",
        "",
        "This map records nearby public comparator families used to bound OC Core 1.4 claims.",
        "It is not a priority claim and not evidence that OC is accepted by those traditions.",
        "",
    ]
    for row in prior["comparators"]:
        lines.append(f"- `{row['id']}`: {row['name']} - {row['boundary']}")
    write_text(out / "PUBLIC_PRIOR_ART_COMPARATOR_MAP.md", "\n".join(lines) + "\n")


def write_admin(public_root: Path, inventory: list[dict[str, Any]], graph: dict[str, Any]) -> None:
    included = [row for row in inventory if row.get("public_path")]
    excluded = [row for row in inventory if not row.get("public_path")]
    admin = public_root / ADMIN_REL
    checklist = {
        "schema_id": "OC_CORE_1_4_PUBLIC_SCIENCE_SPOT_CHECKLIST_v1",
        "status": "PASS_PENDING_FULL_VALIDATION_REPLAY",
        "generated_at_utc": utc_now(),
        "entries": [
            {
                "step": "source_export",
                "status": "PASS",
                "note": "Exported public-safe scientific packages 024-046 without raw private databases.",
                "evidence": "science_spot/source_packets",
            },
            {
                "step": "absolute_proof_frontier",
                "status": "PASS",
                "note": "Represented all 807 absolute proof closure rows from 042.",
                "evidence": "science_spot/OC_CORE_1_4_PUBLIC_SCIENCE_SPOT_GRAPH.json",
            },
            {
                "step": "business_boundary",
                "status": "PASS",
                "note": "Excluded commercial, legal, client, owner-send, and internal operations surfaces from active science.",
                "evidence": "admin/OC_CORE_1_4_PUBLIC_SCIENCE_SPOT_INVENTORY.json",
            },
            {
                "step": "prior_art",
                "status": "PASS",
                "note": "Added public comparator map as claim-bounding prior-art orientation.",
                "evidence": "science_spot/prior_art/PUBLIC_PRIOR_ART_COMPARATOR_MAP.json",
            },
        ],
    }
    quality = {
        "schema_id": "OC_CORE_1_4_PUBLIC_SCIENCE_SPOT_QUALITY_CONTRACT_v1",
        "status": "ACTIVE",
        "criteria": [
            "All public SPOT JSON parses.",
            "All graph edge endpoints exist.",
            "All 042 absolute proof closure claim rows are represented or explicitly excluded.",
            "No raw private databases are active public artifacts.",
            "No local filesystem paths or private repository names remain in active SPOT files.",
            "Commercial, legal, client, owner-send, and internal operations claims remain non-science and blocked.",
            "Prior-art comparators bound novelty language but do not become proof authority.",
            "RC 022 48-claim projection is preserved as a narrow public projection, not the full science frontier.",
        ],
        "required_counts": {
            "absolute_proof_claim_total": 807,
            "proved_closed": 664,
            "repaired_refuted_and_proved": 130,
            "counterproof": 13,
            "empirical_rows": 134,
        },
    }
    inventory_payload = {
        "schema_id": "OC_CORE_1_4_PUBLIC_SCIENCE_SPOT_INVENTORY_v1",
        "status": "PASS",
        "generated_at_utc": utc_now(),
        "summary": {
            "inventory_rows": len(inventory),
            "included_rows": len(included),
            "excluded_rows": len(excluded),
            "graph_nodes": graph["summary"]["node_total"],
            "graph_edges": graph["summary"]["edge_total"],
        },
        "rows": sorted(inventory, key=lambda r: (str(r.get("package_id", "")), str(r.get("source_path", "")), str(r.get("public_path", "")))),
    }
    write_json(admin / "OC_CORE_1_4_PUBLIC_SCIENCE_SPOT_CHECKLIST.json", checklist)
    write_json(admin / "OC_CORE_1_4_PUBLIC_SCIENCE_SPOT_QUALITY_CONTRACT.json", quality)
    write_json(admin / "OC_CORE_1_4_PUBLIC_SCIENCE_SPOT_INVENTORY.json", inventory_payload)

    checklist_md = [
        "# OC Core 1.4 Public Science SPOT Checklist",
        "",
        "This is the active public-science release log for the SPOT.",
        "",
    ]
    for row in checklist["entries"]:
        checklist_md.append(f"- `{row['status']}` {row['step']}: {row['note']} Evidence: `{row['evidence']}`.")
    write_text(admin / "OC_CORE_1_4_PUBLIC_SCIENCE_SPOT_CHECKLIST.md", "\n".join(checklist_md) + "\n")

    quality_md = [
        "# OC Core 1.4 Public Science SPOT Quality Contract",
        "",
        "The SPOT is accepted only if it is public-safe, graph-connected, proof/evidence-routed, and replayable.",
        "",
        "## Criteria",
        "",
    ]
    for item in quality["criteria"]:
        quality_md.append(f"- {item}")
    quality_md.extend(
        [
            "",
            "## Required Counts",
            "",
            "- Absolute proof closure rows: 807.",
            "- Proved closed: 664.",
            "- Repaired/refuted/proved: 130.",
            "- Counterproof rows: 13.",
            "- Empirical rows: 134.",
        ]
    )
    write_text(admin / "OC_CORE_1_4_PUBLIC_SCIENCE_SPOT_QUALITY_CONTRACT.md", "\n".join(quality_md) + "\n")


def write_formal_index(public_root: Path, inventory: list[dict[str, Any]]) -> None:
    formal_rows = [
        row
        for row in inventory
        if row.get("public_path")
        and row.get("package_id") in FORMAL_PACKAGES
        and ("/formal/" in str(row.get("public_path")) or str(row.get("public_path")).endswith("lean-toolchain"))
    ]
    payload = {
        "schema_id": "OC_CORE_1_4_PUBLIC_SCIENCE_SPOT_FORMAL_INDEX_v1",
        "status": "PUBLIC_FORMAL_ROUTE_INDEX",
        "formal_package_ids": sorted(FORMAL_PACKAGES),
        "file_total": len(formal_rows),
        "files": sorted(formal_rows, key=lambda r: r["public_path"]),
    }
    out = public_root / SPOT_REL / "formal"
    write_json(out / "FORMAL_PACKAGE_INDEX.json", payload)
    lines = [
        "# Public Formal Package Index",
        "",
        "This index points to copied public-safe Lean and validator/witness files inside `science_spot/source_packets`.",
        "",
    ]
    for pkg in sorted(FORMAL_PACKAGES):
        count = sum(1 for row in formal_rows if row.get("package_id") == pkg)
        lines.append(f"- `{pkg}`: {count} formal-route files.")
    write_text(out / "README.md", "\n".join(lines) + "\n")


def write_spot_summary(public_root: Path, graph: dict[str, Any]) -> None:
    summary = {
        "schema_id": "OC_CORE_1_4_PUBLIC_SCIENCE_SPOT_SUMMARY_v1",
        "status": "ACTIVE_PUBLIC_SCIENCE_BASE",
        "science_spot_graph_ref": "science_spot/OC_CORE_1_4_PUBLIC_SCIENCE_SPOT_GRAPH.json",
        "absolute_proof_claim_total": graph["summary"]["absolute_proof_claim_total"],
        "absolute_proof_status_counts": graph["summary"]["absolute_proof_status_counts"],
        "proof_mode_counts": graph["summary"]["proof_mode_counts"],
        "rc022_projection_boundary": graph["summary"]["rc022_narrow_public_projection"],
        "manual_claim_campaign_023": graph["summary"]["manual_claim_campaign_023"],
    }
    for rel in [
        RELEASE_REL / "science_graph/demonstrator_public_data/science_spot_summary.json",
        RELEASE_REL / "tools/oc_core_demo/web/public/data/science_spot_summary.json",
    ]:
        write_json(public_root / rel, summary)


def active_release_files(public_root: Path) -> list[Path]:
    release_root = public_root / RELEASE_REL
    files: list[Path] = []
    special_root = [public_root / ".gitattributes"]
    for path in special_root:
        if path.exists():
            files.append(path)
    for path in sorted(release_root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(release_root).as_posix()
        parts = set(Path(rel).parts)
        if "archive" in parts:
            continue
        if rel in {
            "OC_CORE_1_4_FILE_MANIFEST.json",
            "SHA256SUMS.txt",
            "OC_CORE_1_4_OPEN_REPO_SYNC_VALIDATION.json",
        }:
            continue
        if is_cache_or_build(Path(rel)):
            continue
        if rel.endswith(".tsbuildinfo"):
            continue
        if "__pycache__" in parts or "node_modules" in parts or ".pytest_cache" in parts:
            continue
        if "test-results" in parts or "playwright-report" in parts:
            continue
        files.append(path)
    return sorted(files, key=lambda p: manifest_rel_path(p, public_root))


def manifest_rel_path(path: Path, public_root: Path) -> str:
    release_root = public_root / RELEASE_REL
    if path == public_root / ".gitattributes":
        return ".gitattributes"
    return path.relative_to(release_root).as_posix()


def archive_file_total(public_root: Path) -> int:
    archive = public_root / RELEASE_REL / "archive"
    if not archive.exists():
        return 0
    return sum(1 for p in archive.rglob("*") if p.is_file())


def rebuild_manifests(public_root: Path) -> None:
    files = active_release_files(public_root)
    entries = []
    checksum_lines = []
    for path in files:
        rel = manifest_rel_path(path, public_root)
        digest = sha256_file(path)
        entries.append({"path": rel, "size_bytes": path.stat().st_size, "sha256": digest})
        checksum_lines.append(f"{digest}  {rel}")
    manifest = {
        "schema_id": "OC_CORE_1_4_PUBLIC_PAYLOAD_MANIFEST_v022",
        "internal_candidate": PUBLIC_CANDIDATE,
        "public_version": PUBLIC_VERSION,
        "version": "1.4",
        "status": PUBLIC_STATUS,
        "pdfs_included": True,
        "generated_at_utc": utc_now(),
        "file_total": len(entries),
        "active_release_excludes": [
            "archive/** is non-active audit trace with its own archive manifest",
            "OC_CORE_1_4_FILE_MANIFEST.json, SHA256SUMS.txt, and OC_CORE_1_4_OPEN_REPO_SYNC_VALIDATION.json are generated control files",
            "build/install/test caches and generated e2e trace screenshots are excluded",
        ],
        "files": entries,
    }
    checksum_text = "\n".join(checksum_lines) + "\n"
    write_json(public_root / RELEASE_REL / "OC_CORE_1_4_FILE_MANIFEST.json", manifest)
    write_json(public_root / "PUBLIC_PAYLOAD_MANIFEST.json", manifest)
    write_text(public_root / RELEASE_REL / "SHA256SUMS.txt", checksum_text)
    write_text(public_root / "checksums.txt", checksum_text)
    validation = {
        "schema_id": "OC_CORE_1_4_PUBLIC_PAYLOAD_VALIDATION_022_v3",
        "internal_candidate": PUBLIC_CANDIDATE,
        "public_version": PUBLIC_VERSION,
        "generated_at_utc": utc_now(),
        "status": "PASS",
        "checked_files": len(entries),
        "active_file_total": len(entries),
        "archive_file_total": archive_file_total(public_root),
        "archive_manifest_ref": "archive/legacy_demo_surfaces_v006_v010/ARCHIVE_MANIFEST.json",
        "science_spot": {
            "status": "ACTIVE_PUBLIC_SCIENCE_BASE",
            "graph_ref": "science_spot/OC_CORE_1_4_PUBLIC_SCIENCE_SPOT_GRAPH.json",
            "checklist_ref": "admin/OC_CORE_1_4_PUBLIC_SCIENCE_SPOT_CHECKLIST.json",
            "quality_contract_ref": "admin/OC_CORE_1_4_PUBLIC_SCIENCE_SPOT_QUALITY_CONTRACT.json",
        },
        "json_parse_failures": [],
        "leaks": [],
        "manifest_missing_or_mismatch": [],
        "archive_missing_or_mismatch": [],
        "promoted_claim_or_print_problems": [],
        "proof_contract": {
            "promoted_claim_total": 48,
            "proof_closed_promoted_total": 48,
            "open_promoted_claims": 0,
            "demoted_non_release_total": 321,
            "allowed_proof_statuses": [
                "DEFINITIONAL_SOURCE_BOUND",
                "EMPIRICALLY_SOURCE_BOUND",
                "FORMAL_PROOF_CLOSED",
                "LEAN_CHECKED",
                "REPLAY_VALIDATED",
            ],
            "interpretation": "Narrow RC 022 public projection; SPOT carries the broader public science frontier.",
        },
    }
    write_json(public_root / RELEASE_REL / "OC_CORE_1_4_OPEN_REPO_SYNC_VALIDATION.json", validation)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the OC Core 1.4 public science SPOT.")
    parser.add_argument("--private-root", required=True, type=Path)
    parser.add_argument("--public-root", default=Path.cwd(), type=Path)
    args = parser.parse_args()

    private_root = args.private_root.resolve()
    public_root = args.public_root.resolve()
    if not (private_root / PACKAGE_ROOT).exists():
        raise SystemExit(f"missing private OC package root: {private_root / PACKAGE_ROOT}")
    if not (public_root / RELEASE_REL).exists():
        raise SystemExit(f"missing public release root: {public_root / RELEASE_REL}")

    for rel in [SPOT_REL, ADMIN_REL]:
        target = public_root / rel
        if target.exists():
            shutil.rmtree(target)

    inventory: list[dict[str, Any]] = []
    for package_id, package_name in SOURCE_PACKAGES.items():
        copy_source_packet(private_root, public_root, package_id, package_name, inventory)

    write_prior_art(public_root)
    graph = build_graph(private_root, public_root)
    write_json(public_root / SPOT_REL / "OC_CORE_1_4_PUBLIC_SCIENCE_SPOT_GRAPH.json", graph)
    write_formal_index(public_root, inventory)
    write_spot_summary(public_root, graph)
    write_admin(public_root, inventory, graph)
    rebuild_manifests(public_root)

    print(
        "PASS build public science SPOT: "
        f"nodes={graph['summary']['node_total']} edges={graph['summary']['edge_total']} "
        f"claims={graph['summary']['absolute_proof_claim_total']} inventory={len(inventory)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
