from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from build_oc133_science_to_l10_mapping import mapping_paths
from oc133_manuscript_structure_transfer_lib import (
    EDITORIAL,
    sha256_text,
    stable_json,
    write_text_if_changed,
)


ROOT = Path(__file__).resolve().parents[1]
QUALITY_DIR = EDITORIAL / "science_l10_mapping"


def quality_paths() -> dict[str, Path]:
    return {
        "quality_json": QUALITY_DIR / "OC_CORE_1_3_3_SCIENCE_TO_L10_MAPPING_QUALITY_AND_COVERAGE.json",
        "quality_md": QUALITY_DIR / "OC_CORE_1_3_3_SCIENCE_TO_L10_MAPPING_QUALITY_AND_COVERAGE.md",
        "audit_json": QUALITY_DIR / "OC_CORE_1_3_3_SCIENCE_TO_L10_MAPPING_QUALITY_AUDIT.json",
        "audit_md": QUALITY_DIR / "OC_CORE_1_3_3_SCIENCE_TO_L10_MAPPING_QUALITY_AUDIT.md",
    }


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def payload_without_hash(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if key != "artifact_hash"}


def path_prefixes(outline_number: str) -> list[str]:
    parts = outline_number.split(".")
    return [".".join(parts[:index]) for index in range(1, len(parts) + 1)]


def auto_quality_score(row: dict[str, Any]) -> dict[str, Any]:
    source_family_total = len(row.get("source_families", []))
    ready_source_family_total = sum(
        1
        for family in row.get("source_families", [])
        if int(family.get("matched_path_total", 0)) > 0
    )
    matched_path_total = sum(int(family.get("matched_path_total", 0)) for family in row.get("source_families", []))
    recovered_candidate_total = len(row.get("source_candidates_from_recovered_corpus", []))
    has_transformation_rule = bool(row.get("transformation_rule"))
    has_rules = all(row.get(key) for key in ["extraction_rule", "integration_rule", "verification_rule"])
    has_boundary = bool(row.get("claim_boundary"))
    has_reader_task = bool(row.get("reader_task"))

    source_family_score = ready_source_family_total / source_family_total if source_family_total else 0
    recovered_score = min(recovered_candidate_total, 3) / 3
    rule_score = 1.0 if has_transformation_rule and has_rules else 0.0
    boundary_score = 1.0 if has_boundary and has_reader_task else 0.0
    if ready_source_family_total == 0 and recovered_candidate_total == 0:
        assessed_coverage_status = "planned"
    elif ready_source_family_total == 0:
        assessed_coverage_status = "partial"
    elif (
        ready_source_family_total == source_family_total
        and recovered_candidate_total >= 2
        and has_transformation_rule
        and has_rules
        and has_boundary
        and has_reader_task
    ):
        assessed_coverage_status = "complete"
    else:
        assessed_coverage_status = "partial"
    coverage_status_score = 1.0 if assessed_coverage_status in {"complete", "partial"} else 0.5

    auto_index = round(
        (
            source_family_score * 0.25
            + recovered_score * 0.15
            + rule_score * 0.25
            + boundary_score * 0.25
            + coverage_status_score * 0.10
        )
        * 100,
        2,
    )
    flags = []
    if source_family_total == 0:
        flags.append("NO_SOURCE_FAMILY")
    if source_family_total and ready_source_family_total == 0:
        flags.append("NO_READY_SOURCE_FAMILY")
    if source_family_total and ready_source_family_total < source_family_total:
        flags.append("SOME_SOURCE_FAMILIES_EMPTY")
    if recovered_candidate_total == 0:
        flags.append("NO_RECOVERED_SOURCE_CANDIDATE")
    if not has_transformation_rule:
        flags.append("NO_TRANSFORMATION_RULE")
    if not has_rules:
        flags.append("MISSING_MAPPING_RULE")
    if assessed_coverage_status == "partial":
        flags.append("FILL_PARTIAL")
    if assessed_coverage_status == "planned":
        flags.append("FILL_PLANNED")
    return {
        "auto_quality_index": auto_index,
        "source_family_total": source_family_total,
        "ready_source_family_total": ready_source_family_total,
        "matched_path_total": matched_path_total,
        "recovered_candidate_total": recovered_candidate_total,
        "has_transformation_rule": has_transformation_rule,
        "has_extraction_integration_verification_rules": has_rules,
        "has_claim_boundary_and_reader_task": boundary_score == 1.0,
        "coverage_status": assessed_coverage_status,
        "mapping_declared_coverage_status": row.get("coverage_status"),
        "flags": flags,
    }


def build_quality_payload() -> dict[str, Any]:
    mapping_json = mapping_paths()["mapping_json"]
    mapping = read_json(mapping_json)
    l10_rows = []
    aggregate: dict[str, list[float]] = defaultdict(list)
    flag_counts: dict[str, int] = defaultdict(int)
    for row in mapping["mapping_rows"]:
        score = auto_quality_score(row)
        for flag in score["flags"]:
            flag_counts[flag] += 1
        l10_rows.append(
            {
                "mapping_id": row["mapping_id"],
                "l10_node_id": row["l10_node_id"],
                "outline_number": row["outline_number"],
                "title": row["l10_title"],
                "argument_role": row["argument_role"],
                **score,
                "manual_quality_status": "not_assessed",
                "manual_quality_note": "",
            }
        )
        for prefix in path_prefixes(row["outline_number"]):
            aggregate[prefix].append(score["auto_quality_index"])

    aggregate_rows = []
    for outline, scores in sorted(aggregate.items(), key=lambda item: [int(part) for part in item[0].split(".")]):
        aggregate_rows.append(
            {
                "outline_number": outline,
                "descendant_l10_total": len(scores),
                "auto_quality_index_mean": round(sum(scores) / len(scores), 2) if scores else 0,
                "auto_quality_index_min": round(min(scores), 2) if scores else 0,
                "auto_quality_index_max": round(max(scores), 2) if scores else 0,
            }
        )

    payload: dict[str, Any] = {
        "artifact_kind": "OC_CORE_1_3_3_SCIENCE_TO_L10_MAPPING_QUALITY_AND_COVERAGE",
        "body_prose_included": False,
        "status": "AUTO_QUALITY_INDEX_READY_FILL_NOT_ASSESSED",
        "source_mapping": {
            "json": relative(mapping_json),
            "artifact_hash": mapping["artifact_hash"],
        },
        "scoring_model": {
            "source_family_score_weight": 0.25,
            "recovered_candidate_score_weight": 0.15,
            "transformation_and_rule_score_weight": 0.25,
            "claim_boundary_reader_task_score_weight": 0.25,
            "manual_fill_status_score_weight": 0.10,
            "manual_status_default": "not_assessed",
            "coverage_assessment_policy": "r014 deterministic fill assessment converts mapping defaults into complete, partial, or planned statuses using ready source families, recovered candidates, transformation rules, reader task, and claim boundary evidence.",
        },
        "l10_quality_row_total": len(l10_rows),
        "l10_quality_rows": l10_rows,
        "aggregate_row_total": len(aggregate_rows),
        "aggregate_quality_rows": aggregate_rows,
        "flag_counts": dict(sorted(flag_counts.items())),
    }
    payload["artifact_hash"] = sha256_text(stable_json(payload_without_hash(payload)))
    return payload


def validate_quality_payload(payload: dict[str, Any]) -> list[str]:
    failures = []
    mapping = read_json(mapping_paths()["mapping_json"])
    if payload.get("source_mapping", {}).get("artifact_hash") != mapping.get("artifact_hash"):
        failures.append("source_mapping_hash_mismatch")
    if payload.get("l10_quality_row_total") != len(mapping.get("mapping_rows", [])):
        failures.append("quality_row_total_mismatch")
    for row in payload.get("l10_quality_rows", []):
        score = row.get("auto_quality_index")
        if not isinstance(score, (int, float)) or score < 0 or score > 100:
            failures.append(f"bad_auto_quality_index::{row.get('l10_node_id')}")
        if row.get("manual_quality_status") != "not_assessed":
            failures.append(f"manual_status_assessed_too_early::{row.get('l10_node_id')}")
        if row.get("coverage_status") == "not_assessed":
            failures.append(f"coverage_not_assessed_after_r014_policy::{row.get('l10_node_id')}")
    if payload.get("artifact_hash") != sha256_text(stable_json(payload_without_hash(payload))):
        failures.append("quality_hash_mismatch")
    return failures


def build_audit_payload(quality: dict[str, Any]) -> dict[str, Any]:
    failures = validate_quality_payload(quality)
    rows = quality["l10_quality_rows"]
    indices = [row["auto_quality_index"] for row in rows]
    payload: dict[str, Any] = {
        "artifact_kind": "OC_CORE_1_3_3_SCIENCE_TO_L10_MAPPING_QUALITY_AUDIT",
        "body_prose_included": False,
        "status": "PASS" if not failures else "FAIL",
        "failure_total": len(failures),
        "failures": failures,
        "quality_hash": quality["artifact_hash"],
        "l10_quality_row_total": len(rows),
        "auto_quality_index_mean": round(sum(indices) / len(indices), 2) if indices else 0,
        "auto_quality_index_min": round(min(indices), 2) if indices else 0,
        "auto_quality_index_max": round(max(indices), 2) if indices else 0,
        "flag_counts": quality["flag_counts"],
    }
    payload["artifact_hash"] = sha256_text(stable_json(payload_without_hash(payload)))
    return payload


def render_quality_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# OC Core 1.3.3 Science to L10 Mapping Quality and Coverage",
        "",
        f"Status: {payload['status']}",
        f"Artifact hash: `{payload['artifact_hash']}`",
        f"Source mapping hash: `{payload['source_mapping']['artifact_hash']}`",
        "",
        "This document computes automatic quality indices where data exists. Manual quality statuses remain not assessed, while r014 coverage status is deterministically assessed from source readiness and recovered-corpus evidence.",
        "",
        "## Scoring Model",
        "",
    ]
    for key, value in payload["scoring_model"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Aggregate Coverage Map", ""])
    for row in payload["aggregate_quality_rows"]:
        lines.append(
            f"- {row['outline_number']}: mean={row['auto_quality_index_mean']} "
            f"min={row['auto_quality_index_min']} max={row['auto_quality_index_max']} "
            f"l10={row['descendant_l10_total']}"
        )
    lines.extend(["", "## L10 Rows", ""])
    for row in payload["l10_quality_rows"]:
        lines.append(
            f"- {row['outline_number']} {row['title']} [{row['argument_role']}]: "
            f"auto_index={row['auto_quality_index']}; manual={row['manual_quality_status']}; "
            f"flags={','.join(row['flags']) if row['flags'] else 'NONE'}"
        )
    return "\n".join(lines) + "\n"


def render_audit_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# OC Core 1.3.3 Science to L10 Mapping Quality Audit",
        "",
        f"Status: {payload['status']}",
        f"Artifact hash: `{payload['artifact_hash']}`",
        f"Quality hash: `{payload['quality_hash']}`",
        f"L10 rows: {payload['l10_quality_row_total']}",
        f"Mean auto quality index: {payload['auto_quality_index_mean']}",
        f"Min auto quality index: {payload['auto_quality_index_min']}",
        f"Max auto quality index: {payload['auto_quality_index_max']}",
        "",
        "## Flag Counts",
        "",
    ]
    for flag, total in sorted(payload["flag_counts"].items()):
        lines.append(f"- {flag}: {total}")
    if payload["failures"]:
        lines.extend(["", "## Failures", ""])
        for failure in payload["failures"]:
            lines.append(f"- {failure}")
    return "\n".join(lines) + "\n"


def expected_files() -> dict[Path, str]:
    quality = build_quality_payload()
    failures = validate_quality_payload(quality)
    if failures:
        raise RuntimeError(f"Mapping quality validation failed: {failures}")
    audit = build_audit_payload(quality)
    if audit["status"] != "PASS":
        raise RuntimeError(f"Mapping quality audit failed: {audit['failures']}")
    paths = quality_paths()
    return {
        paths["quality_json"]: stable_json(quality),
        paths["quality_md"]: render_quality_markdown(quality),
        paths["audit_json"]: stable_json(audit),
        paths["audit_md"]: render_audit_markdown(audit),
    }


def check_files(files: dict[Path, str]) -> dict[str, Any]:
    missing = []
    changed = []
    for path, text in files.items():
        if not path.exists():
            missing.append(relative(path))
        elif path.read_text(encoding="utf-8", errors="replace") != text:
            changed.append(relative(path))
    return {"state": "PASS" if not missing and not changed else "FAIL", "missing": missing, "changed": changed}


def write_files(files: dict[Path, str]) -> list[str]:
    changed = []
    for path, text in files.items():
        if write_text_if_changed(path, text):
            changed.append(relative(path))
    return changed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build OC133 science-to-L10 mapping quality and coverage map.")
    parser.add_argument("--write", action="store_true", help="Write quality artifacts if changed.")
    parser.add_argument("--check", action="store_true", help="Check quality artifacts without writing.")
    args = parser.parse_args(argv)
    if not args.write and not args.check:
        args.check = True
    files = expected_files()
    result = {"changed": write_files(files), "missing": [], "state": "PASS"} if args.write else check_files(files)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["state"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
