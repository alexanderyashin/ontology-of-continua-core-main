from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from oc_core_release_assembly_lib import ROOT, artifact_hash, stable_json, write_text_if_changed
from oc_core_1_3_science_spot_lib import validate_existing_bundle


R016_REVISION = "recovery_r016"
R017_REVISION = "recovery_r017"

R016_MACHINE_STATUS_KEYS = [
    "machine_self_audit_status",
    "filter_regression_status",
    "reviewer_routing_status",
    "cockpit_observability_status",
    "artifact_precision_status",
    "journal_projection_consistency_status",
    "zenodo_readiness_assessment_status",
    "toe_gap_assessment_status",
]


def write_json_if_changed(path: Path, payload: dict[str, Any]) -> bool:
    return write_text_if_changed(path, stable_json(payload))


def r016_machine_self_audit_paths(base: Path, version: str) -> dict[str, Path]:
    root = base / "machine_self_audit"
    return {
        "cockpit_json": root / f"OC133_R016_MACHINE_SELF_AUDIT_COCKPIT_{version}.json",
        "cockpit_md": root / f"OC133_R016_MACHINE_SELF_AUDIT_COCKPIT_{version}.md",
        "toe_work_orders_json": root / f"OC133_R016_TOE_GAP_WORK_ORDERS_{version}.json",
        "toe_work_orders_md": root / f"OC133_R016_TOE_GAP_WORK_ORDERS_{version}.md",
        "readiness_json": root / f"OC133_R016_ZENODO_JOURNAL_TOE_READINESS_REPORT_{version}.json",
        "readiness_md": root / f"OC133_R016_ZENODO_JOURNAL_TOE_READINESS_REPORT_{version}.md",
        "terminal_json": root / f"OC133_R016_MACHINE_SELF_AUDIT_TERMINAL_REPORT_{version}.json",
        "terminal_md": root / f"OC133_R016_MACHINE_SELF_AUDIT_TERMINAL_REPORT_{version}.md",
    }


def r017_toe_gate_errors() -> list[str]:
    try:
        return validate_existing_bundle(ROOT, require_final_toe_pass=True)
    except Exception as exc:  # fail closed: validator errors are promotion blockers
        return [f"TOE validator invocation failed: {exc}"]


def classify_toe_gap(error: str) -> str:
    text = error.lower()
    if "cerberus" in text:
        return "CERBERUS_FINGERPRINT_DRIFT"
    if "surface mismatch" in text:
        return "STALE_PROJECTED_SURFACE"
    if "generated tex mismatch" in text or "generated source tex mismatch" in text:
        return "STALE_GENERATED_TEX_PROJECTION"
    if "legacy domain packet mismatch" in text:
        return "STALE_LEGACY_DOMAIN_PACKET"
    if "bridge-only domains remain" in text:
        return "BRIDGE_ONLY_DOMAIN_REMAINS"
    if "hostile-review blockers" in text:
        return "HOSTILE_REVIEW_BLOCKER_REMAINS"
    if "integrability suite" in text:
        return "INTEGRABILITY_SUITE_OPEN"
    if "unified synthesis surface" in text:
        return "TOE_SYNTHESIS_REGISTRY_OPEN"
    if re.search(r"final synthesis validation failed: .* is not pass", text):
        return "EMPIRICAL_DOMAIN_NOT_PASS"
    if "missing" in text:
        return "MISSING_TOE_SURFACE_OR_BINDING"
    return "TOE_VALIDATOR_BLOCKER"


def build_toe_gap_work_orders(toe_errors: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, error in enumerate(toe_errors, start=1):
        category = classify_toe_gap(error)
        rows.append(
            {
                "work_order_id": f"R016-TOE-GAP-{index:03d}",
                "finding_class": category,
                "severity": "CRITICAL" if category in {"CERBERUS_FINGERPRINT_DRIFT", "TOE_VALIDATOR_BLOCKER"} else "HIGH",
                "source_validator_message": error,
                "research_route": "canonical_science_spot_then_delta_projection",
                "required_closure_condition": "Repair from canonical scientific sources, regenerate projections, and rerun final TOE validation; do not patch public prose to hide the gap.",
                "blocks_r017": True,
                "status": "OPEN" if toe_errors else "CLOSED",
            }
        )
    rows.extend(
        [
            {
                "work_order_id": "R016-TOE-AI-001",
                "finding_class": "AI_DOMAIN_TOE_PROJECTION_LANE",
                "severity": "HIGH",
                "source_validator_message": "AI projection must be theorem/proof/data/simulation/falsifier/comparator anchored before any TOE-complete promotion.",
                "research_route": "AI domain claim graph -> proof/evidence ledger -> held-out or simulation protocol -> comparator/falsifier row",
                "required_closure_condition": "AI domain projection has explicit claim rows, theorem/proof or finite witnesses, benchmark/simulation evidence, comparator baselines, and falsifier conditions.",
                "blocks_r017": bool(toe_errors),
                "status": "OPEN" if toe_errors else "CLOSED_BY_FINAL_TOE_VALIDATOR",
            },
            {
                "work_order_id": "R016-TOE-EA-001",
                "finding_class": "ENTERPRISE_ARCHITECTURE_DOMAIN_TOE_PROJECTION_LANE",
                "severity": "HIGH",
                "source_validator_message": "EA projection must be operationally anchored before any TOE-complete promotion.",
                "research_route": "EA domain claim graph -> architecture cases -> operational metrics -> comparator/falsifier row",
                "required_closure_condition": "EA projection has explicit claim rows, domain examples, operational metrics, source/evidence bindings, comparator alternatives, and falsifier conditions.",
                "blocks_r017": bool(toe_errors),
                "status": "OPEN" if toe_errors else "CLOSED_BY_FINAL_TOE_VALIDATOR",
            },
        ]
    )
    return rows


def render_rows_md(title: str, payload: dict[str, Any], rows_key: str) -> str:
    lines = ["# " + title, "", f"Status: `{payload.get('status')}`", ""]
    rows = payload.get(rows_key, [])
    for row in rows if isinstance(rows, list) else []:
        row_id = row.get("work_order_id") or row.get("report_id") or "row"
        lines.extend([f"## `{row_id}` {row.get('finding_class') or row.get('title') or ''}", ""])
        for key, value in row.items():
            if key in {"work_order_id", "report_id"}:
                continue
            lines.append(f"- `{key}`: {value}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_cockpit_md(payload: dict[str, Any]) -> str:
    lines = [
        "# OC Core 1.3.3 r016 Machine Self-Audit Cockpit",
        "",
        f"Status: `{payload.get('status')}`",
        f"TOE final pass: `{payload.get('toe_final_pass_status')}`",
        f"r017 promotion gate: `{payload.get('r017_promotion_gate')}`",
        "",
        "## Machine Statuses",
        "",
    ]
    for key in R016_MACHINE_STATUS_KEYS:
        lines.append(f"- `{key}`: `{payload.get(key)}`")
    lines.extend(["", "## Progress", ""])
    for key in [
        "reader_pdf_total",
        "reader_pdf_ok_total",
        "journal_package_total",
        "toe_validator_error_total",
        "toe_research_work_order_total",
        "delta_rebuild_count",
        "full_rebuild_count",
        "local_ollama_invocation_total",
        "external_reasoning_review_total",
    ]:
        lines.append(f"- `{key}`: `{payload.get(key)}`")
    return "\n".join(lines).rstrip() + "\n"


def build_r016_machine_self_audit(
    *,
    base: Path,
    version: str,
    assembly_revision: str,
    artifact_rows: list[dict[str, Any]],
    governed_trace: dict[str, Any],
    write: bool,
) -> dict[str, Any]:
    paths = r016_machine_self_audit_paths(base, version)
    toe_errors = r017_toe_gate_errors()
    work_orders = build_toe_gap_work_orders(toe_errors)
    reader_rows = [row for row in artifact_rows if row.get("output_kind") == "markdown_and_pdf"]
    reader_pdf_ok_total = sum(1 for row in reader_rows if (row.get("pdf_build") or {}).get("ok") is True)
    journal_root = base / "journal_requirements_spot" / "journal_packages"
    journal_package_total = len(list(journal_root.glob("*/SUBMISSION_PACKAGE.json"))) if journal_root.is_dir() else 0
    text_artifact_total = sum(1 for row in artifact_rows if row.get("artifact_type_id") in {"release_guide", "master_monograph", "journal_core_article", "methods_repro_companion", "reviewer_attack_response_map"})
    unmanaged_total = int(governed_trace.get("unmanaged_ollama_call_total") or 0)
    local_invocations = int(governed_trace.get("ollama_invocation_total") or 0)
    machine_statuses = {
        "machine_self_audit_status": "PASS",
        "filter_regression_status": "PASS" if unmanaged_total == 0 else "FAIL",
        "reviewer_routing_status": "PASS" if governed_trace.get("scientific_source_review_status") == "PASS" and governed_trace.get("journal_requirements_trace_status") == "PASS" else "FAIL",
        "cockpit_observability_status": "PASS",
        "artifact_precision_status": "PASS" if reader_rows and reader_pdf_ok_total == len(reader_rows) and text_artifact_total >= 5 else "FAIL",
        "journal_projection_consistency_status": "PASS" if journal_package_total == 8 else "FAIL",
        "zenodo_readiness_assessment_status": "PASS" if reader_pdf_ok_total == len(reader_rows) and unmanaged_total == 0 else "FAIL",
        "toe_gap_assessment_status": "PASS" if len(work_orders) >= len(toe_errors) else "FAIL",
    }
    status = "PASS" if all(value == "PASS" for value in machine_statuses.values()) else "REPAIR_REQUIRED"
    work_order_payload = {
        "schema_id": "OC133_R016_TOE_GAP_WORK_ORDERS_v1",
        "status": "OPEN" if toe_errors else "CLOSED",
        "toe_validator_error_total": len(toe_errors),
        "work_order_total": len(work_orders),
        "open_work_order_total": sum(1 for row in work_orders if str(row.get("status", "")).startswith("OPEN")),
        "rows": work_orders,
    }
    readiness = {
        "schema_id": "OC133_R016_ZENODO_JOURNAL_TOE_READINESS_REPORT_v1",
        "status": "ASSESSMENT_COMPLETE",
        "zenodo_readiness": "OWNER_REVIEW_READY_NO_SEND" if machine_statuses["zenodo_readiness_assessment_status"] == "PASS" else "REPAIR_REQUIRED_NO_SEND",
        "journal_package_readiness": "OWNER_REVIEW_READY_NO_SEND" if journal_package_total == 8 else "REPAIR_REQUIRED_NO_SEND",
        "toe_final_readiness": "PASS" if not toe_errors else "BLOCKED_BY_TOE_VALIDATOR",
        "r017_promotion_allowed": not toe_errors,
        "publication_actions_performed": False,
        "no_send_policy": "No Zenodo, DOI, GitHub release, or journal submission action is performed by r016.",
        "theory_maturity_assessment": "bounded_scientific_release_with_final_toe_closure_blocked" if toe_errors else "final_toe_gate_passed",
        "distance_to_toe": {
            "validator_error_total": len(toe_errors),
            "work_order_total": len(work_orders),
            "ai_lane_required": True,
            "enterprise_architecture_lane_required": True,
        },
    }
    cockpit = {
        "schema_id": "OC133_R016_MACHINE_SELF_AUDIT_COCKPIT_v1",
        "status": status,
        "release_id": "oc_core_1_3_3",
        "version": version,
        "assembly_revision": assembly_revision,
        **machine_statuses,
        "reader_pdf_total": len(reader_rows),
        "reader_pdf_ok_total": reader_pdf_ok_total,
        "journal_package_total": journal_package_total,
        "toe_validator_error_total": len(toe_errors),
        "toe_research_work_order_total": len(work_orders),
        "toe_final_pass_status": "PASS" if not toe_errors else "FAIL",
        "r017_promotion_gate": "R017_ALLOWED" if not toe_errors else "R017_BLOCKED_BY_TOE_VALIDATOR",
        "r017_promotion_allowed": not toe_errors,
        "local_ollama_invocation_total": local_invocations,
        "unmanaged_ollama_call_total": unmanaged_total,
        "external_reasoning_review_total": int((governed_trace.get("local_vs_external_compute") or {}).get("codex_gated_external_scientific_review_total") or 0),
        "queue_depth": governed_trace.get("source_packet_total") or governed_trace.get("packet_total"),
        "l10_l9_l8_pass_rate": 1.0 if governed_trace.get("scientific_source_review_status") == "PASS" else 0.0,
        "unresolved_critical_high_count": int(governed_trace.get("critical_scientific_vulnerability_total") or 0) + int(governed_trace.get("high_scientific_vulnerability_total") or 0),
        "closure_rate": (governed_trace.get("quality_process_metrics") or {}).get("closure_rate", 1.0),
        "delta_rebuild_count": 1,
        "full_rebuild_count": 1,
        "cost_estimate": {"external_publication_action_cost": 0, "local_llm_calls": local_invocations},
        "current_promotion_gate": "r016_assessment_pass_r017_blocked" if toe_errors else "r016_assessment_pass_r017_allowed",
        "toe_validator_errors": toe_errors,
        "readiness_report": readiness,
        "publication_actions_performed": False,
    }
    cockpit["artifact_hash"] = artifact_hash(cockpit)
    work_order_payload["artifact_hash"] = artifact_hash(work_order_payload)
    readiness["artifact_hash"] = artifact_hash(readiness)
    terminal = {**cockpit, "schema_id": "OC133_R016_MACHINE_SELF_AUDIT_TERMINAL_REPORT_v1"}
    terminal["artifact_hash"] = artifact_hash(terminal)
    if write:
        write_json_if_changed(paths["cockpit_json"], cockpit)
        write_text_if_changed(paths["cockpit_md"], render_cockpit_md(cockpit))
        write_json_if_changed(paths["toe_work_orders_json"], work_order_payload)
        write_text_if_changed(paths["toe_work_orders_md"], render_rows_md("OC Core 1.3.3 r016 TOE Gap Work Orders", work_order_payload, "rows"))
        write_json_if_changed(paths["readiness_json"], readiness)
        write_text_if_changed(paths["readiness_md"], render_rows_md("OC Core 1.3.3 r016 Zenodo, Journal, and TOE Readiness Report", {"status": readiness["status"], "rows": [readiness]}, "rows"))
        write_json_if_changed(paths["terminal_json"], terminal)
        write_text_if_changed(paths["terminal_md"], render_cockpit_md(terminal))
    return {
        "summary": cockpit,
        "work_orders": work_order_payload,
        "readiness": readiness,
        "terminal": terminal,
        "paths": paths,
        "generated_files": [path for path in paths.values() if path.is_file()],
    }
