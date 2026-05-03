from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from build_oc_core_current_release_aggregator import aggregator_paths
from build_oc_core_quality_metric_catalog import metric_catalog_paths
from oc_core_release_assembly_lib import ASSEMBLY_ROOT, artifact_hash, read_json, stable_json, validation_result


QUALITY_DIR = ASSEMBLY_ROOT / "quality_parameterization"
MATRIX_STATUS = "OC_CORE_L10_QUALITY_PROJECTION_MATRIX_READY"


def projection_paths() -> dict[str, Path]:
    return {
        "matrix_json": QUALITY_DIR / "OC_CORE_L10_QUALITY_PROJECTION_MATRIX.json",
        "matrix_md": QUALITY_DIR / "OC_CORE_L10_QUALITY_PROJECTION_MATRIX.md",
        "audit_json": QUALITY_DIR / "OC_CORE_L10_QUALITY_PARAMETERIZATION_AUDIT.json",
        "audit_md": QUALITY_DIR / "OC_CORE_L10_QUALITY_PARAMETERIZATION_AUDIT.md",
    }


def _contains_any(haystack: str, needles: list[str]) -> bool:
    folded = haystack.lower()
    return any(needle.lower() in folded for needle in needles)


def _node_text(node: dict[str, Any]) -> str:
    values = [
        str(node.get("title", "")),
        str(node.get("argument_role", "")),
        " ".join(str(item) for item in node.get("source_family_ids", [])),
        str(node.get("reader_task", "")),
        str(node.get("claim_boundary", "")),
    ]
    return " ".join(values).lower()


def _is_frontmatter(node: dict[str, Any]) -> bool:
    path = node.get("order_path", [])
    return bool(path and int(path[0]) == 1)


def applicability(node: dict[str, Any], metric: dict[str, Any]) -> tuple[bool, float, str]:
    if metric.get("metric_id") == "artifact.role_hygiene":
        return False, 0.0, "artifact-level metric; evaluated against release package artifact rows"
    reasons: list[str] = []
    scores: list[float] = []
    text = _node_text(node)
    if metric.get("required_for_all_l10"):
        reasons.append("required_for_all_l10")
        scores.append(1.0)
    if metric.get("required_for_text_l10"):
        reasons.append("required_for_text_l10")
        scores.append(0.95)
    if node.get("argument_role") in metric.get("argument_roles", []):
        reasons.append("argument_role_match")
        scores.append(0.85)
    if _contains_any(str(node.get("title", "")), metric.get("title_patterns", [])):
        reasons.append("title_pattern_match")
        scores.append(0.8)
    if _contains_any(" ".join(node.get("source_family_ids", [])), metric.get("source_family_patterns", [])):
        reasons.append("source_family_match")
        scores.append(0.8)
    if metric.get("metric_id") == "metadata.identity_citation" and _is_frontmatter(node):
        reasons.append("frontmatter_identity_context")
        scores.append(0.7)
    if metric.get("metric_id") == "visual.figure_table_operationalization" and _contains_any(text, ["figure", "table", "visual", "atlas", "map", "matrix"]):
        reasons.append("visual_or_table_context")
        scores.append(0.75)
    if reasons:
        return True, round(max(scores), 2), ";".join(reasons)
    return False, 0.0, "metric not relevant to this L10 node role, title, source families, or artifact class"


def severity_for(metric: dict[str, Any], applicable: bool) -> str:
    if not applicable:
        return "WAIVED"
    metric_id = metric["metric_id"]
    if metric_id == "public.no_overclaim_surface":
        return "CRITICAL"
    if metric["family"] in {"scientific_validity", "claim_evidence_trace", "formal_proof", "empirical_support", "public_surface_safety", "reproducibility"}:
        return "HIGH"
    if metric["family"] in {"didactics", "style", "structure", "reviewer_resilience"}:
        return "MEDIUM"
    return "LOW"


def build_projection_payload() -> dict[str, Any]:
    aggregator = read_json(aggregator_paths()["aggregator_json"])
    catalog = read_json(metric_catalog_paths()["catalog_json"])
    terminal_nodes = [node for node in aggregator["nodes"] if node.get("terminal_l10") is True]
    rows: list[dict[str, Any]] = []
    applicable_counter: Counter[str] = Counter()
    node_applicable_counter: Counter[str] = Counter()
    for node in terminal_nodes:
        short_node_id = node["aggregator_node_id"].replace("OC-CURRENT-AGG-", "")
        for metric in catalog["metrics"]:
            applies, relevance, reason = applicability(node, metric)
            if applies:
                applicable_counter[metric["metric_id"]] += 1
                node_applicable_counter[node["aggregator_node_id"]] += 1
            weight = round(float(metric["default_weight"]) * relevance, 4)
            rows.append(
                {
                    "projection_id": f"QPROJ-{short_node_id}-{metric['metric_id'].replace('.', '_')}",
                    "aggregator_node_id": node["aggregator_node_id"],
                    "target_node_id": node["target_node_id"],
                    "order_label": node["order_label"],
                    "node_title": node["title"],
                    "argument_role": node.get("argument_role"),
                    "metric_id": metric["metric_id"],
                    "metric_family": metric["family"],
                    "applicable": applies,
                    "relevance_score": relevance,
                    "weight": weight,
                    "auto_manual_mode": metric["default_mode"],
                    "scorer_id": metric["default_scorer_id"],
                    "severity_if_failed": severity_for(metric, applies),
                    "full_coverage_rule": metric["full_coverage_rule"] if applies else None,
                    "parameterization_rule": metric["parameterization_rule"] if applies else None,
                    "thresholds": metric["thresholds"] if applies else {},
                    "evidence_fields": metric["evidence_fields"] if applies else [],
                    "standard_source_ids": metric["standard_source_ids"] if applies else [],
                    "non_applicability_reason": None if applies else reason,
                }
            )
    payload: dict[str, Any] = {
        "schema_id": "OC_CORE_L10_QUALITY_PROJECTION_MATRIX_v1",
        "artifact_kind": "OC_CORE_L10_QUALITY_PROJECTION_MATRIX",
        "body_prose_included": False,
        "status": MATRIX_STATUS,
        "source_hashes": {
            "current_release_aggregator_hash": aggregator["artifact_hash"],
            "quality_metric_catalog_hash": catalog["artifact_hash"],
        },
        "terminal_l10_node_total": len(terminal_nodes),
        "metric_total": catalog["metric_total"],
        "projection_row_total": len(rows),
        "applicable_projection_total": sum(1 for row in rows if row["applicable"]),
        "waived_projection_total": sum(1 for row in rows if not row["applicable"]),
        "applicable_counts_by_metric": dict(sorted(applicable_counter.items())),
        "applicable_counts_by_node_min": min(node_applicable_counter.values()) if node_applicable_counter else 0,
        "projection_rows": rows,
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def validate_projection(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if payload.get("status") != MATRIX_STATUS:
        failures.append("bad_status")
    rows = payload.get("projection_rows", [])
    expected = payload.get("terminal_l10_node_total", 0) * payload.get("metric_total", 0)
    if len(rows) != expected or payload.get("projection_row_total") != len(rows):
        failures.append("projection_row_total_mismatch")
    by_node: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_node[row["aggregator_node_id"]].append(row)
        if row["applicable"]:
            for key in ["full_coverage_rule", "parameterization_rule", "scorer_id", "thresholds", "evidence_fields", "standard_source_ids"]:
                if not row.get(key):
                    failures.append(f"applicable_row_missing_{key}::{row.get('projection_id')}")
        elif not row.get("non_applicability_reason"):
            failures.append(f"waived_row_missing_reason::{row.get('projection_id')}")
    required_metric_ids = {
        "coverage.target_obligation",
        "trace.exact_source_binding",
        "claim.boundary_discipline",
        "didactic.reader_task_payoff",
        "structure.sequence_transition",
        "public.no_overclaim_surface",
    }
    for node_id, node_rows in by_node.items():
        applicable_ids = {row["metric_id"] for row in node_rows if row["applicable"]}
        missing = required_metric_ids - applicable_ids
        if missing:
            failures.append(f"node_missing_required_metrics::{node_id}::" + ",".join(sorted(missing)))
    if payload.get("applicable_counts_by_node_min", 0) <= 0:
        failures.append("some_l10_node_has_no_applicable_metric")
    if payload.get("artifact_hash") != artifact_hash(payload):
        failures.append("artifact_hash_mismatch")
    return sorted(set(failures))


def build_audit_payload(matrix: dict[str, Any]) -> dict[str, Any]:
    failures = validate_projection(matrix)
    family_counts: Counter[str] = Counter()
    waiver_counts: Counter[str] = Counter()
    for row in matrix["projection_rows"]:
        if row["applicable"]:
            family_counts[row["metric_family"]] += 1
        else:
            waiver_counts[row["metric_family"]] += 1
    payload: dict[str, Any] = {
        "schema_id": "OC_CORE_L10_QUALITY_PARAMETERIZATION_AUDIT_v1",
        "artifact_kind": "OC_CORE_L10_QUALITY_PARAMETERIZATION_AUDIT",
        "status": "PASS" if not failures else "FAIL",
        "failure_total": len(failures),
        "failures": failures,
        "matrix_hash": matrix["artifact_hash"],
        "terminal_l10_node_total": matrix["terminal_l10_node_total"],
        "metric_total": matrix["metric_total"],
        "projection_row_total": matrix["projection_row_total"],
        "applicable_projection_total": matrix["applicable_projection_total"],
        "waived_projection_total": matrix["waived_projection_total"],
        "applicable_family_counts": dict(sorted(family_counts.items())),
        "waived_family_counts": dict(sorted(waiver_counts.items())),
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def render_matrix_md(payload: dict[str, Any]) -> str:
    lines = [
        "# OC Core L10 Quality Projection Matrix",
        "",
        f"Status: `{payload['status']}`",
        f"Artifact hash: `{payload['artifact_hash']}`",
        f"Terminal L10 nodes: `{payload['terminal_l10_node_total']}`",
        f"Metrics: `{payload['metric_total']}`",
        f"Rows: `{payload['projection_row_total']}`",
        f"Applicable rows: `{payload['applicable_projection_total']}`",
        f"Waived rows: `{payload['waived_projection_total']}`",
        "",
        "## Projection Rows",
        "",
        "| Node | Metric | Applicable | Relevance | Weight | Mode | Scorer | Severity | Rule / Waiver |",
        "|---|---|---:|---:|---:|---|---|---|---|",
    ]
    for row in payload["projection_rows"]:
        rule = row["parameterization_rule"] if row["applicable"] else row["non_applicability_reason"]
        safe_rule = str(rule).replace("|", "/")
        lines.append(
            f"| `{row['order_label']}` | `{row['metric_id']}` | {str(row['applicable']).lower()} | "
            f"{row['relevance_score']} | {row['weight']} | `{row['auto_manual_mode']}` | `{row['scorer_id']}` | "
            f"`{row['severity_if_failed']}` | {safe_rule} |"
        )
    return "\n".join(lines)


def render_audit_md(payload: dict[str, Any]) -> str:
    lines = [
        "# OC Core L10 Quality Parameterization Audit",
        "",
        f"Status: `{payload['status']}`",
        f"Failures: `{payload['failure_total']}`",
        f"Matrix hash: `{payload['matrix_hash']}`",
        f"Terminal L10 nodes: `{payload['terminal_l10_node_total']}`",
        f"Projection rows: `{payload['projection_row_total']}`",
        f"Applicable rows: `{payload['applicable_projection_total']}`",
        f"Waived rows: `{payload['waived_projection_total']}`",
        "",
        "## Applicable Family Counts",
        "",
    ]
    for family, count in payload["applicable_family_counts"].items():
        lines.append(f"- `{family}`: {count}")
    if payload["failures"]:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in payload["failures"])
    return "\n".join(lines)


def expected_files() -> dict[Path, str]:
    matrix = build_projection_payload()
    failures = validate_projection(matrix)
    if failures:
        raise RuntimeError(f"L10 quality projection validation failed: {failures[:20]}")
    audit = build_audit_payload(matrix)
    paths = projection_paths()
    return {
        paths["matrix_json"]: stable_json(matrix),
        paths["matrix_md"]: render_matrix_md(matrix),
        paths["audit_json"]: stable_json(audit),
        paths["audit_md"]: render_audit_md(audit),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build OC Core L10 quality projection matrix.")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if not args.write and not args.check:
        args.check = True
    result = validation_result(expected_files(), write=args.write)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["state"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
