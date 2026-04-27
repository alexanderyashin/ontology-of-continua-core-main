from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from .audit_engine import audit_candidate_bundle, markdown_report, rel, write_json, write_text


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def release_root(root: Path, release_id: str) -> Path:
    return root / "releases" / release_id


def parfit_editorial_dir(root: Path, release_id: str) -> Path:
    return release_root(root, release_id) / "editorial" / "parfit"


def _claims_for_bundle(root: Path) -> list[dict[str, Any]]:
    ledger = _read_json(root / "claims" / "CLAIM_LEDGER_FULL.json")
    rows = []
    for claim in ledger.get("claims", []):
        row = dict(claim)
        row.setdefault("id", row.get("claim_id") or row.get("id"))
        row.setdefault("burden_owner", "OC science/release steward")
        rows.append(row)
    return rows


def derive_candidate_bundle(root: Path, release_id: str) -> dict[str, Any]:
    ed = parfit_editorial_dir(root, release_id)
    manifests = {
        "relation_r_manifest": rel(root, ed / "relation_r_manifest.yaml"),
        "future_stakeholder_manifest": rel(root, ed / "future_stakeholder_manifest.yaml"),
        "five_part_decision_matrix": rel(root, ed / "five_part_decision_matrix.yaml"),
        "repugnant_output_assessment": rel(root, ed / "repugnant_output_assessment.yaml"),
    }
    publish_manifest = _read_json(release_root(root, release_id) / "editorial" / "OC_CORE_1_3_2_PUBLISH_MANIFEST_DRAFT.json")
    if not publish_manifest:
        publish_manifest = _read_json(root / "releases" / "oc_core_1_3_2" / "editorial" / "OC_CORE_1_3_2_PUBLISH_MANIFEST_DRAFT.json")
    return {
        "schema_id": "ReleaseCandidateBundle_v1",
        "candidate_id": release_id,
        "program_id": "OC_PARFITIAN_CERBERUS_20260427",
        "release_target": release_id,
        "publication_state": "NO_SEND",
        "publish_allowed": False,
        "outbound_send_allowed": False,
        "owner_gate": {
            "approval_status": "pending",
            "publication_owner_unlock": False,
            "owner_approval_packet": rel(root, release_root(root, release_id) / "editorial"),
        },
        "claims": _claims_for_bundle(root),
        "manifests": manifests,
        "publication_boundary_refs": [
            rel(root, root / "RELEASE_CONTRACT.md"),
            rel(root, release_root(root, release_id) / "README.md"),
            rel(root, release_root(root, release_id) / "editorial"),
        ],
        "evidence_manifest_refs": [
            "claims/CLAIM_LEDGER_FULL.json",
            "claims/CLAIM_EVIDENCE_MATRIX.md",
            "manifest.json",
            "checksums.txt",
        ],
        "transparency": {
            "hidden_strategy_required": False,
            "uncertainty_visible": True,
            "claim_ceiling_visible": True,
        },
        "release_machine_refs": {
            "publish_manifest": publish_manifest.get("release_id", release_id),
            "global_no_send_lock": publish_manifest.get("global_no_send_lock", True),
        },
    }


def load_or_derive_bundle(root: Path, release_id: str) -> dict[str, Any]:
    bundle_path = parfit_editorial_dir(root, release_id) / "candidate_bundle.yaml"
    if bundle_path.exists():
        bundle = _read_yaml(bundle_path)
        if bundle:
            return bundle
    return derive_candidate_bundle(root, release_id)


def ensure_release_audit(root: Path, release_id: str, write: bool = True) -> dict[str, Any]:
    bundle = load_or_derive_bundle(root, release_id)
    report = audit_candidate_bundle(root, bundle)
    if write:
        reports_dir = root / "reports" / "parfit"
        report_json = reports_dir / f"{release_id}.json"
        report_md = reports_dir / f"{release_id}.md"
        write_json(report_json, report)
        write_text(report_md, markdown_report(report))
        ed = parfit_editorial_dir(root, release_id)
        write_json(ed / f"PARFITIAN_CERBERUS_AUDIT_{release_id}.json", report)
        write_text(ed / f"PARFITIAN_CERBERUS_AUDIT_{release_id}.md", markdown_report(report))
        write_text(ed / "candidate_bundle.generated.yaml", yaml.safe_dump(bundle, sort_keys=False, allow_unicode=False))
        write_text(ed / "README.md", "\n".join([
            f"# Parfitian Cerberus Audit Inputs: {release_id}",
            "",
            "This directory stores release-local Parfitian Cerberus manifests and the generated blocking audit report.",
            "",
            "- Publication and outbound actions remain disabled.",
            "- High+ findings block `RELEASE_READY_NO_SEND`.",
            "- Blocker findings are not waivable by release audit output.",
        ]))
    return report


def release_gate_result(root: Path, release_id: str) -> dict[str, Any]:
    report = ensure_release_audit(root, release_id, write=True)
    summary = report.get("summary", {})
    high_plus = int(summary.get("high_plus_total", 0))
    blockers = int(summary.get("blocker_total", 0))
    if blockers:
        state = "BLOCKED"
        severity = "CRITICAL"
    elif high_plus:
        state = "FAIL"
        severity = "HIGH"
    else:
        state = "PASS"
        severity = "HIGH"
    return {
        "state": state,
        "severity": severity,
        "summary": "Parfitian Cerberus release-critical gate checked self-defeat, moral mathematics, Relation R, future stakeholders, transparency and evidence burden.",
        "details": {
            "report": f"reports/parfit/{release_id}.json",
            "status": report.get("status"),
            "release_ready_no_send_allowed": report.get("release_ready_no_send_allowed"),
            "high_plus_total": high_plus,
            "blocker_total": blockers,
            "relation_r": summary.get("relation_r", {}),
            "top_findings": report.get("findings", [])[:5],
            "no_send_release_gate": report.get("no_send_release_gate", {}),
        },
    }
