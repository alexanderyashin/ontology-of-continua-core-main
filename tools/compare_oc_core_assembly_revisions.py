from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from assemble_oc_core_release_package import OLD_MASTER_BASELINE_PAGES, assembly_paths
from build_oc133_recovery_structures import recovery_paths
from audit_oc_core_release_assembly_machine import machine_audit_paths
from oc_core_release_assembly_lib import ROOT, artifact_hash, read_json, stable_json, validation_result

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from release_machine.versioning import version_from_release_id


def comparison_paths(release_id: str, version: str, candidate_revision: str | None = None) -> dict[str, Path]:
    base = assembly_paths(release_id, version, candidate_revision)["assembly_json"].parent
    suffix = candidate_revision or "default"
    return {
        "comparison_json": base / f"OC_CORE_RELEASE_ASSEMBLY_REVISION_COMPARISON_{version}.{suffix}.json",
        "comparison_md": base / f"OC_CORE_RELEASE_ASSEMBLY_REVISION_COMPARISON_{version}.{suffix}.md",
    }


def load_assembly(release_id: str, version: str, revision: str | None) -> dict[str, Any]:
    path = assembly_paths(release_id, version, revision)["assembly_json"]
    if not path.exists():
        raise FileNotFoundError(path)
    return read_json(path)


def machine_audit(release_id: str, version: str, revision: str | None) -> dict[str, Any] | None:
    path = machine_audit_paths(release_id, version, revision)["audit_json"]
    return read_json(path) if path.exists() else None


def pages_by_artifact(assembly: dict[str, Any]) -> dict[str, int]:
    rows: dict[str, int] = {}
    for row in assembly.get("artifact_rows", []):
        pdf_build = row.get("pdf_build")
        if pdf_build:
            rows[row["artifact_type_id"]] = int(pdf_build.get("pages") or 0)
    return rows


def old_public_pages() -> dict[str, int]:
    path = recovery_paths()["comparison_json"]
    if not path.exists():
        return {"master_monograph": OLD_MASTER_BASELINE_PAGES}
    comparison = read_json(path)
    rows = {}
    for row in comparison.get("artifact_rows", []):
        rows[row["artifact_type_id"]] = int(row.get("old_pdf", {}).get("pages") or 0)
    return rows


def metric_row(metric_id: str, baseline: Any, candidate: Any, status: str, rule: str) -> dict[str, Any]:
    return {
        "metric_id": metric_id,
        "baseline_value": baseline,
        "candidate_value": candidate,
        "status": status,
        "rule": rule,
    }


def build_comparison(release_id: str, candidate_revision: str | None, baseline_revision: str | None = None) -> dict[str, Any]:
    version = version_from_release_id(release_id)
    baseline = load_assembly(release_id, version, baseline_revision)
    candidate = load_assembly(release_id, version, candidate_revision)
    candidate_audit = machine_audit(release_id, version, candidate_revision)
    baseline_pages = pages_by_artifact(baseline)
    candidate_pages = pages_by_artifact(candidate)
    old_pages = old_public_pages()
    metric_rows: list[dict[str, Any]] = []
    frontmatter_body_separation_active = int(candidate.get("summary", {}).get("frontmatter_body_excluded_total") or 0) > 0

    metric_rows.append(
        metric_row(
            "terminal_node_total",
            baseline.get("summary", {}).get("terminal_node_total"),
            candidate.get("summary", {}).get("terminal_node_total"),
            "PASS" if int(candidate.get("summary", {}).get("terminal_node_total", 0)) >= int(baseline.get("summary", {}).get("terminal_node_total", 0)) else "FAIL",
            "candidate must not reduce terminal coverage relative to the previous assembly unless a source-intake rejection report explains it",
        )
    )
    metric_rows.append(
        metric_row(
            "blocked_terminal_total",
            baseline.get("summary", {}).get("blocked_terminal_total"),
            candidate.get("summary", {}).get("blocked_terminal_total"),
            "PASS" if int(candidate.get("summary", {}).get("blocked_terminal_total", 1)) == 0 else "FAIL",
            "candidate blocked terminal count must be zero",
        )
    )
    metric_rows.append(
        metric_row(
            "transition_record_coverage",
            baseline.get("summary", {}).get("transition_record_total"),
            candidate.get("summary", {}).get("transition_record_total"),
            "PASS"
            if int(candidate.get("summary", {}).get("transition_record_total", -1))
            == max(int(candidate.get("summary", {}).get("terminal_node_total", 0)) - 1, 0)
            else "FAIL",
            "candidate transition count must equal terminal_node_total - 1",
        )
    )
    for artifact_id, old_value in sorted(old_pages.items()):
        if artifact_id not in candidate_pages:
            continue
        metric_rows.append(
            metric_row(
                f"old_public_page_baseline::{artifact_id}",
                old_value,
                candidate_pages[artifact_id],
                "PASS" if candidate_pages[artifact_id] >= old_value else "FAIL",
                "candidate PDF pages must not regress below old public package baseline",
            )
        )
    for artifact_id, baseline_value in sorted(baseline_pages.items()):
        if artifact_id not in candidate_pages:
            continue
        page_delta_status = "PASS" if candidate_pages[artifact_id] >= baseline_value else "WARN"
        page_delta_rule = "candidate should grow or explain reductions against previous generated assembly"
        if (
            page_delta_status == "WARN"
            and frontmatter_body_separation_active
            and candidate_pages[artifact_id] >= old_pages.get(artifact_id, 0)
        ):
            page_delta_status = "PASS_EXPLAINED"
            page_delta_rule = "candidate page reduction is explained by frontmatter/body separation and remains above old public baseline"
        metric_rows.append(
            metric_row(
                f"assembly_page_delta::{artifact_id}",
                baseline_value,
                candidate_pages[artifact_id],
                page_delta_status,
                page_delta_rule,
            )
        )
    metric_rows.append(
        metric_row(
            "machine_audit_status",
            None,
            None if candidate_audit is None else candidate_audit.get("status"),
            "PASS" if candidate_audit and candidate_audit.get("status") == "PASS" else "FAIL",
            "candidate assembly machine audit must exist and pass before artifact review",
        )
    )
    metric_rows.append(
        metric_row(
            "publication_action_total",
            baseline.get("publication_actions_performed"),
            candidate.get("publication_actions_performed"),
            "PASS" if candidate.get("publication_actions_performed") is False else "FAIL",
            "review-space assembly must not perform public release actions",
        )
    )
    failures = [row for row in metric_rows if row["status"] == "FAIL"]
    warnings = [row for row in metric_rows if row["status"] == "WARN"]
    payload: dict[str, Any] = {
        "schema_id": "OC_CORE_RELEASE_ASSEMBLY_REVISION_COMPARISON_v1",
        "artifact_kind": "OC_CORE_RELEASE_ASSEMBLY_REVISION_COMPARISON",
        "status": "PASS" if not failures else "FAIL",
        "release_id": release_id,
        "version": version,
        "baseline_revision": baseline_revision or "default",
        "candidate_revision": candidate_revision or "default",
        "source_hashes": {
            "baseline_assembly_hash": baseline.get("artifact_hash"),
            "candidate_assembly_hash": candidate.get("artifact_hash"),
            "candidate_machine_audit_hash": None if candidate_audit is None else candidate_audit.get("artifact_hash"),
        },
        "summary": {
            "metric_total": len(metric_rows),
            "failure_total": len(failures),
            "warning_total": len(warnings),
            "baseline_terminal_node_total": baseline.get("summary", {}).get("terminal_node_total"),
            "candidate_terminal_node_total": candidate.get("summary", {}).get("terminal_node_total"),
            "old_public_master_pages": old_pages.get("master_monograph"),
            "candidate_master_pages": candidate_pages.get("master_monograph"),
            "frontmatter_body_excluded_total": candidate.get("summary", {}).get("frontmatter_body_excluded_total"),
            "explained_page_reduction_total": sum(1 for row in metric_rows if row["status"] == "PASS_EXPLAINED"),
        },
        "metric_rows": metric_rows,
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def render_md(payload: dict[str, Any]) -> str:
    lines = [
        f"# OC Core Release Assembly Revision Comparison {payload['version']}",
        "",
        f"Status: `{payload['status']}`",
        f"Baseline revision: `{payload['baseline_revision']}`",
        f"Candidate revision: `{payload['candidate_revision']}`",
        f"Artifact hash: `{payload['artifact_hash']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Metrics", ""])
    for row in payload["metric_rows"]:
        lines.append(
            f"- `{row['status']}` `{row['metric_id']}`: baseline=`{row['baseline_value']}` candidate=`{row['candidate_value']}`"
        )
    return "\n".join(lines).rstrip() + "\n"


def expected_files(release_id: str, candidate_revision: str | None, baseline_revision: str | None = None) -> dict[Path, str]:
    version = version_from_release_id(release_id)
    payload = build_comparison(release_id, candidate_revision, baseline_revision)
    paths = comparison_paths(release_id, version, candidate_revision)
    return {
        paths["comparison_json"]: stable_json(payload),
        paths["comparison_md"]: render_md(payload),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare OC Core assembly revisions and block quantitative regressions.")
    parser.add_argument("--release", required=True)
    parser.add_argument("--candidate-revision")
    parser.add_argument("--baseline-revision")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if not args.write and not args.check:
        args.check = True
    result = validation_result(expected_files(args.release, args.candidate_revision, args.baseline_revision), write=args.write)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    payload = build_comparison(args.release, args.candidate_revision, args.baseline_revision)
    return 0 if result["state"] == "PASS" and payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
