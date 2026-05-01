from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROJECT_CONTROL_REL = "operations/project_control"
REPORT_REL = f"{PROJECT_CONTROL_REL}/LOGION_PROCESS_COHERENCE_GUARD.json"
REPORT_MD_REL = f"{PROJECT_CONTROL_REL}/LOGION_PROCESS_COHERENCE_GUARD.md"

RELEASE_SCORECARD_REL = "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_RELEASE_SCORECARD_latest.json"
PUBLISH_MANIFEST_REL = "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_PUBLISH_MANIFEST_DRAFT.json"
OWNER_APPROVAL_REL = "releases/oc_core_1_3_3/editorial/OWNER_RELEASE_APPROVAL_v1.3.3.json"
JOURNAL_INDEX_REL = "releases/oc_core_1_3_3/submission_packages/SUBMISSION_PACKAGE_INDEX.json"
ZIP_INTEGRITY_REL = "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_ZIP_INTEGRITY_latest.json"
ARTIFACT_INVENTORY_REL = "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_ARTIFACT_INVENTORY.json"
DIRTY_LEDGER_REL = f"{PROJECT_CONTROL_REL}/LOGION_DIRTY_TREE_GOVERNANCE_LEDGER.json"
DELTA_LEDGER_REL = f"{PROJECT_CONTROL_REL}/LOGION_DELTA_QUEUE_LEDGER.json"
CONTROLLER_REL = f"{PROJECT_CONTROL_REL}/LOGION_PROJECT_CONTROL_COCKPIT.json"
V12_MATERIALIZER_REL = "tools/materialize_oc_core_1_3_3_v12_closure.py"

SELF_REFERENTIAL_RELEASE_REFS = {
    "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_ARTIFACT_INVENTORY.json",
    "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_RELEASE_SCORECARD_latest.json",
    "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_RELEASE_SCORECARD_latest.md",
    "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_SHA256SUMS",
    "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_ZIP_INTEGRITY_latest.json",
    "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_PERSONAL_RELEASE_AUDIT_latest.json",
    "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_PERSONAL_RELEASE_AUDIT_latest.md",
}

PACKAGE_OUTPUT_REFS = {
    "releases/oc_core_1_3_3/artifacts/oc_core_1_3_3_no_send_release.zip",
    "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_ARTIFACT_INVENTORY.json",
    "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_SHA256SUMS",
    "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_ZIP_INTEGRITY_latest.json",
}

ROOT_NO_SEND_SURFACE_REFS = [
    "manifest.json",
    "checksums.txt",
    "ro-crate-metadata.jsonld",
    "CITATION.cff",
    ".codemeta.json",
    "README.md",
    "RELEASE_NOTES.md",
    "VERSION",
]

ROOT_STALE_TOKENS = ["1.3.2", "v1.3.2", "oc_core_1_3_2", "10.5281/zenodo."]


def read_json(path: Path) -> Any:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_json_if_changed(path: Path, payload: Any) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if path.exists() and path.read_bytes() == data:
        return False
    path.write_bytes(data)
    return True


def write_text_if_changed(path: Path, text: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not text.endswith("\n"):
        text += "\n"
    data = text.encode("utf-8")
    if path.exists() and path.read_bytes() == data:
        return False
    path.write_bytes(data)
    return True


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rows_from_inventory(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    rows = payload.get("rows", [])
    return rows if isinstance(rows, list) else []


def materializer_clear_refs(root: Path) -> set[str]:
    path = root / V12_MATERIALIZER_REL
    if not path.exists():
        return set()
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return set()
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "REPRODUCIBLE_GENERATED_OUTPUTS_TO_CLEAR" for target in node.targets)
            and isinstance(node.value, ast.List)
        ):
            refs = set()
            for item in node.value.elts:
                if isinstance(item, ast.Constant) and isinstance(item.value, str):
                    refs.add(item.value)
            return refs
    return set()


def issue(
    issue_id: str,
    severity: str,
    contradiction: str,
    resolution_axis: str,
    evidence: dict[str, Any],
) -> dict[str, Any]:
    return {
        "issue_id": issue_id,
        "severity": severity,
        "contradiction": contradiction,
        "resolution_axis": resolution_axis,
        "evidence": evidence,
    }


def build_report(root: Path = ROOT) -> dict[str, Any]:
    scorecard_doc = read_json(root / RELEASE_SCORECARD_REL)
    scorecard = scorecard_doc.get("summary", scorecard_doc) if isinstance(scorecard_doc, dict) else {}
    manifest = read_json(root / PUBLISH_MANIFEST_REL)
    approval = read_json(root / OWNER_APPROVAL_REL)
    journal = read_json(root / JOURNAL_INDEX_REL)
    integrity = read_json(root / ZIP_INTEGRITY_REL)
    inventory = read_json(root / ARTIFACT_INVENTORY_REL)
    dirty = read_json(root / DIRTY_LEDGER_REL)
    delta = read_json(root / DELTA_LEDGER_REL)
    controller = read_json(root / CONTROLLER_REL)

    issues: list[dict[str, Any]] = []

    no_send_locked = (
        manifest.get("publish_allowed") is False
        and manifest.get("journal_submissions_allowed") is False
        and manifest.get("owner_approved") is False
        and approval.get("decision") == "PENDING"
        and approval.get("publish_allowed") is False
        and journal.get("submission_allowed") is False
        and journal.get("journal_submissions_allowed") is False
    )
    if not no_send_locked:
        issues.append(
            issue(
                "COHERENCE-NOSEND-LOCK",
                "CRITICAL",
                "No-send/publication locks disagree across manifest, owner approval, and journal index.",
                "Governance lock axis: block publication and regenerate lock manifests before release work continues.",
                {
                    "manifest": {
                        "publish_allowed": manifest.get("publish_allowed"),
                        "journal_submissions_allowed": manifest.get("journal_submissions_allowed"),
                        "owner_approved": manifest.get("owner_approved"),
                    },
                    "approval": approval,
                    "journal": {
                        "submission_allowed": journal.get("submission_allowed"),
                        "journal_submissions_allowed": journal.get("journal_submissions_allowed"),
                    },
                },
            )
        )

    release_external_ready = scorecard.get("release_state") == "OC_CORE_1_3_3_EXTERNAL_REVIEW_READY_NO_SEND"
    if release_external_ready and scorecard.get("all_domain_ready_no_send") is True:
        issues.append(
            issue(
                "COHERENCE-EXTERNAL-VS-ALLDOMAIN",
                "HIGH",
                "Bounded external-review release state is combined with all-domain-ready=true.",
                "Claim-boundary axis: split bounded release readiness from full-science program readiness.",
                {
                    "release_state": scorecard.get("release_state"),
                    "all_domain_ready_no_send": scorecard.get("all_domain_ready_no_send"),
                },
            )
        )

    zip_path = root / str(integrity.get("package", ""))
    zip_ok = zip_path.exists() and integrity.get("package_sha256") == sha256_file(zip_path)
    if not zip_ok:
        issues.append(
            issue(
                "COHERENCE-ZIP-INTEGRITY",
                "CRITICAL",
                "ZIP integrity manifest does not bind to the actual package file.",
                "Package-integrity axis: rebuild or restore package before any release verdict.",
                {
                    "package": integrity.get("package"),
                    "manifest_sha256": integrity.get("package_sha256"),
                    "actual_sha256": sha256_file(zip_path) if zip_path.exists() else None,
                },
            )
        )

    inventory_refs = {str(row.get("path")) for row in rows_from_inventory(inventory)}
    self_refs = sorted(ref for ref in inventory_refs if ref in SELF_REFERENTIAL_RELEASE_REFS or "/pdf_text_audit/" in ref)
    if self_refs:
        issues.append(
            issue(
                "COHERENCE-SELF-REFERENTIAL-PACKAGE",
                "CRITICAL",
                "Release package inventory includes post-package verification/self-referential artifacts.",
                "Delta Queue packaging axis: exclude post-package audit outputs from the release zip and keep them as external verification artifacts.",
                {"self_referential_refs": self_refs},
            )
        )

    clear_owns_package_outputs = sorted(materializer_clear_refs(root) & PACKAGE_OUTPUT_REFS)
    if clear_owns_package_outputs:
        issues.append(
            issue(
                "COHERENCE-MATERIALIZER-PACKAGE-OWNERSHIP",
                "CRITICAL",
                "V12 source materializer clears release package outputs that are owned by the package builder.",
                "Capability-ownership axis: keep source materialization, package generation, and verification outputs disjoint; strict temp-tree reproducibility may delete package outputs only inside its isolated workspace.",
                {"forbidden_clear_refs": clear_owns_package_outputs},
            )
        )

    stale_root_refs: list[dict[str, Any]] = []
    if (root / ".zenodo.json").exists():
        stale_root_refs.append({"path": ".zenodo.json", "reason": "root Zenodo metadata must be absent in no-send 1.3.3 state"})
    for ref in ROOT_NO_SEND_SURFACE_REFS:
        path = root / ref
        if not path.exists():
            stale_root_refs.append({"path": ref, "reason": "required root no-send surface is missing"})
            continue
        body = path.read_text(encoding="utf-8", errors="ignore")
        hits = [token for token in ROOT_STALE_TOKENS if token.lower() in body.lower()]
        if "1.3.3" not in body or hits:
            stale_root_refs.append({"path": ref, "missing_current_version": "1.3.3" not in body, "stale_hits": hits})
    if stale_root_refs:
        issues.append(
            issue(
                "COHERENCE-ROOT-METADATA-STALE",
                "CRITICAL",
                "Root public/no-send metadata surface is stale or points at an older release.",
                "Metadata-parity axis: regenerate the 1.3.3 no-send root surface before finite checks, package reuse, or release verdicts.",
                {"stale_root_refs": stale_root_refs},
            )
        )

    if dirty.get("public_unclassified_total", 0) not in {0, None} or dirty.get("private_unknown_total", 0) not in {0, None}:
        issues.append(
            issue(
                "COHERENCE-DIRTY-GOVERNANCE",
                "HIGH",
                "Dirty tree contains unclassified public/private rows.",
                "Dirty-tree governance axis: classify, commit, or explicitly ledger rows before release closeout.",
                {
                    "public_unclassified_total": dirty.get("public_unclassified_total"),
                    "private_unknown_total": dirty.get("private_unknown_total"),
                },
            )
        )

    controller_delta = controller.get("portfolio", {}).get("delta_queue", {}) if isinstance(controller.get("portfolio"), dict) else {}
    if delta and controller_delta.get("semantic_fingerprint") != delta.get("semantic_fingerprint"):
        issues.append(
            issue(
                "COHERENCE-CONTROLLER-DELTA-SNAPSHOT",
                "MEDIUM",
                "Project controller cockpit is not synchronized with the Delta Queue ledger.",
                "Controller-sync axis: refresh project control after Delta Queue updates.",
                {
                    "controller_fingerprint": controller_delta.get("semantic_fingerprint"),
                    "delta_fingerprint": delta.get("semantic_fingerprint"),
                },
            )
        )

    critical_high = [row for row in issues if row["severity"] in {"CRITICAL", "HIGH"}]
    return {
        "schema_id": "LOGION_PROCESS_COHERENCE_GUARD_v1",
        "state": "PASS" if not critical_high else "FAIL",
        "critical_high_total": len(critical_high),
        "issue_total": len(issues),
        "issues": issues,
        "policy": {
            "no_self_interference": True,
            "delta_queue_required": True,
            "new_axis_policy": "If a contradiction is not repairable locally, emit a resolution_axis row naming the smallest governance/router/observer/orchestrator needed.",
            "release_publication_allowed": False,
        },
        "refs": {
            "scorecard": RELEASE_SCORECARD_REL,
            "publish_manifest": PUBLISH_MANIFEST_REL,
            "owner_approval": OWNER_APPROVAL_REL,
            "journal_index": JOURNAL_INDEX_REL,
            "zip_integrity": ZIP_INTEGRITY_REL,
            "artifact_inventory": ARTIFACT_INVENTORY_REL,
            "dirty_ledger": DIRTY_LEDGER_REL,
            "delta_ledger": DELTA_LEDGER_REL,
            "controller": CONTROLLER_REL,
            "v12_materializer": V12_MATERIALIZER_REL,
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Logion Process Coherence Guard",
        "",
        f"- State: `{report['state']}`",
        f"- Critical/high issues: `{report['critical_high_total']}`",
        f"- Issue total: `{report['issue_total']}`",
        "",
        "## Issues",
        "",
    ]
    if not report["issues"]:
        lines.append("- none")
    for row in report["issues"]:
        lines.append(
            f"- `{row['severity']}` `{row['issue_id']}`: {row['contradiction']} Resolution axis: `{row['resolution_axis']}`"
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    report = build_report(root)
    if args.write:
        write_json_if_changed(root / REPORT_REL, report)
        write_text_if_changed(root / REPORT_MD_REL, render_markdown(report))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.check and report["critical_high_total"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
