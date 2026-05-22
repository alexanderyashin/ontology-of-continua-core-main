from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


PACKAGE_ID = "035"
PACKAGE_NAME = "continuous_evidence_packet_execution"


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
        raise SystemExit(f"package id mismatch: {manifest.get('package_id')} != {PACKAGE_ID}")
    if manifest.get("package_name") != PACKAGE_NAME:
        raise SystemExit(f"package name mismatch: {manifest.get('package_name')} != {PACKAGE_NAME}")

    repo_root = package_root.parents[4]
    for row in manifest.get("included_files", []):
        public_path = row.get("public_path")
        expected_sha = row.get("public_sha256")
        if not public_path or not expected_sha:
            raise SystemExit(f"invalid manifest row: {row}")
        path = repo_root / public_path
        if not path.exists():
            raise SystemExit(f"missing included file: {public_path}")
        actual_sha = sha256_file(path)
        if actual_sha != expected_sha:
            raise SystemExit(f"sha mismatch for {public_path}: {actual_sha} != {expected_sha}")

    raw_sqlite = [p for p in package_root.rglob("*.sqlite") if p.is_file()]
    if raw_sqlite:
        raise SystemExit(f"raw sqlite must not be public: {raw_sqlite[0]}")

    table_exports = 0
    for json_path in sorted((package_root / "db_exports").rglob("*.json")):
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        if payload.get("schema_id") != "OC_CORE_1_4_PUBLIC_SCIENCE_SPOT_TABLE_EXPORT_v1":
            raise SystemExit(f"bad table export schema: {json_path}")
        rows = payload.get("rows", [])
        if payload.get("row_total") != len(rows):
            raise SystemExit(f"row_total mismatch: {json_path}")
        csv_path = json_path.with_suffix(".csv")
        if not csv_path.exists():
            raise SystemExit(f"missing csv export: {csv_path}")
        with csv_path.open("r", encoding="utf-8", newline="") as fh:
            csv_rows = list(csv.DictReader(fh))
        if len(csv_rows) != len(rows):
            raise SystemExit(f"csv row_total mismatch: {csv_path}")
        if not payload.get("source_db_sha256"):
            raise SystemExit(f"missing source db hash: {json_path}")
        table_exports += 1

    print(
        "PASS public source packet export validator: "
        f"package={PACKAGE_ID} name={PACKAGE_NAME} included={manifest.get('included_file_total')} "
        f"excluded={manifest.get('excluded_total')} tables={table_exports}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
