from __future__ import annotations

import argparse
import json
import sqlite3
import tempfile
from pathlib import Path
from typing import Any

from build_oc_core_l10_quality_projection_matrix import projection_paths
from build_oc_core_quality_metric_catalog import metric_catalog_paths
from oc_core_release_assembly_lib import ASSEMBLY_ROOT, ROOT, read_json, relative


QUALITY_DIR = ASSEMBLY_ROOT / "quality_parameterization"
CACHE_PATH = QUALITY_DIR / "OC_CORE_QUALITY_PARAMETERIZATION_CACHE.sqlite"


def cache_path() -> Path:
    return CACHE_PATH


def build_cache(db_path: Path) -> dict[str, Any]:
    catalog = read_json(metric_catalog_paths()["catalog_json"])
    matrix = read_json(projection_paths()["matrix_json"])
    if db_path.exists():
        db_path.unlink()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(db_path))
    try:
        connection.execute("PRAGMA journal_mode=OFF")
        connection.execute("PRAGMA synchronous=OFF")
        connection.execute(
            """
            CREATE TABLE metric_catalog (
                metric_id TEXT PRIMARY KEY,
                family TEXT NOT NULL,
                label TEXT NOT NULL,
                default_mode TEXT NOT NULL,
                default_scorer_id TEXT NOT NULL,
                default_weight REAL NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE l10_metric_projection (
                projection_id TEXT PRIMARY KEY,
                aggregator_node_id TEXT NOT NULL,
                order_label TEXT NOT NULL,
                metric_id TEXT NOT NULL,
                metric_family TEXT NOT NULL,
                applicable INTEGER NOT NULL,
                relevance_score REAL NOT NULL,
                weight REAL NOT NULL,
                scorer_id TEXT NOT NULL,
                severity_if_failed TEXT NOT NULL,
                non_applicability_reason TEXT
            )
            """
        )
        connection.execute("CREATE INDEX idx_projection_node ON l10_metric_projection(aggregator_node_id)")
        connection.execute("CREATE INDEX idx_projection_metric ON l10_metric_projection(metric_id)")
        for metric in catalog["metrics"]:
            connection.execute(
                "INSERT INTO metric_catalog VALUES (?, ?, ?, ?, ?, ?)",
                (
                    metric["metric_id"],
                    metric["family"],
                    metric["label"],
                    metric["default_mode"],
                    metric["default_scorer_id"],
                    float(metric["default_weight"]),
                ),
            )
        for row in matrix["projection_rows"]:
            connection.execute(
                "INSERT INTO l10_metric_projection VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    row["projection_id"],
                    row["aggregator_node_id"],
                    row["order_label"],
                    row["metric_id"],
                    row["metric_family"],
                    1 if row["applicable"] else 0,
                    float(row["relevance_score"]),
                    float(row["weight"]),
                    row["scorer_id"],
                    row["severity_if_failed"],
                    row["non_applicability_reason"],
                ),
            )
        connection.commit()
        metric_total = connection.execute("SELECT COUNT(*) FROM metric_catalog").fetchone()[0]
        projection_total = connection.execute("SELECT COUNT(*) FROM l10_metric_projection").fetchone()[0]
        applicable_total = connection.execute("SELECT COUNT(*) FROM l10_metric_projection WHERE applicable=1").fetchone()[0]
        waived_total = connection.execute("SELECT COUNT(*) FROM l10_metric_projection WHERE applicable=0").fetchone()[0]
    finally:
        connection.close()
    return {
        "state": "PASS",
        "cache_path": relative(db_path) if db_path.resolve().is_relative_to(ROOT.resolve()) else "<temporary-cache>",
        "metric_total": metric_total,
        "projection_total": projection_total,
        "applicable_total": applicable_total,
        "waived_total": waived_total,
        "catalog_hash": catalog["artifact_hash"],
        "matrix_hash": matrix["artifact_hash"],
    }


def validate_cache_result(result: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    matrix = read_json(projection_paths()["matrix_json"])
    catalog = read_json(metric_catalog_paths()["catalog_json"])
    if result["metric_total"] != catalog["metric_total"]:
        failures.append("metric_total_mismatch")
    if result["projection_total"] != matrix["projection_row_total"]:
        failures.append("projection_total_mismatch")
    if result["applicable_total"] != matrix["applicable_projection_total"]:
        failures.append("applicable_total_mismatch")
    if result["waived_total"] != matrix["waived_projection_total"]:
        failures.append("waived_total_mismatch")
    return failures


def run_check() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="oc_core_quality_cache_") as directory:
        result = build_cache(Path(directory) / "cache.sqlite")
        result["cache_path"] = "<temporary-cache>"
        failures = validate_cache_result(result)
        result["state"] = "PASS" if not failures else "FAIL"
        result["failure_total"] = len(failures)
        result["failures"] = failures
        result["writes_tracked_files"] = False
        return result


def run_write() -> dict[str, Any]:
    result = build_cache(CACHE_PATH)
    failures = validate_cache_result(result)
    result["state"] = "PASS" if not failures else "FAIL"
    result["failure_total"] = len(failures)
    result["failures"] = failures
    result["writes_tracked_files"] = False
    result["cache_is_canonical"] = False
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build deterministic SQLite query cache for OC Core quality parameterization.")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if not args.write and not args.check:
        args.check = True
    result = run_write() if args.write else run_check()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["state"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
