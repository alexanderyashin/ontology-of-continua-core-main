from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import zipfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
EDITORIAL = ROOT / "releases" / RELEASE_ID / "editorial"
ARTIFACTS = ROOT / "releases" / RELEASE_ID / "artifacts"
OUT_JSON = EDITORIAL / "OC_CORE_1_3_3_PERSONAL_RELEASE_AUDIT_latest.json"
OUT_MD = EDITORIAL / "OC_CORE_1_3_3_PERSONAL_RELEASE_AUDIT_latest.md"

PDFS = [
    "OC_CORE_1_3_3_MASTER_MONOGRAPH_EN.pdf",
    "OC_CORE_1_3_3_JOURNAL_CORE_EN.pdf",
    "OC_CORE_1_3_3_METHODS_AND_REPRODUCIBILITY_COMPANION_EN.pdf",
    "OC_CORE_1_3_3_REVIEWER_ATTACK_AND_RESPONSE_MAP_EN.pdf",
]

CLAIM_SURFACE_REFS = [
    "claims/CLAIM_LEDGER_1_3_3.json",
    "claims/CLAIM_LEDGER_FULL.json",
    "claims/CLAIM_LEDGER_FULL.md",
    "claims/CLAIM_EVIDENCE_MATRIX.md",
    "claims/CLAIM_EVIDENCE_MATRIX_1_3_3.md",
    "claims/PROMOTED_CLAIMS.md",
    "claims/SUPPORT_ONLY_CLAIMS.md",
    "claims/DEMOTED_CLAIMS.md",
    "claims/FRONTIER_OR_FUTURE_WORK.md",
    "claims/STRONG_STATEMENT_TO_CLAIM_MAP.json",
]

TEXT_SUFFIXES = {".cff", ".json", ".jsonld", ".md", ".py", ".tex", ".txt", ".yaml", ".yml"}
STALE_RELEASE_RE = re.compile(r"\b(?:v?1\.3\.2|oc_core_1_3_2)\b", re.I)
ABSOLUTE_OVERCLAIM_RE = re.compile(
    r"\b(irrefutable|final truth|theory of everything|all modern science|better than all modern science|proves all science)\b",
    re.I,
)
REQUIRED_JOURNAL_COMPONENT_IDS = {
    "submission_package_json",
    "required_component_manifest_json",
    "required_component_manifest_md",
    "cover_letter",
    "checklist",
    "reproducibility_and_data",
    "conflict_and_funding",
    "ai_assistance",
}
STALE_CONTEXT_SAFE_REFS = {
    "proofs/finite_model_checks/OC133_FINITE_MODEL_INPUTS.json",
    "proofs/finite_model_checks/run_finite_model_checks.py",
    "proofs/FINITE_MODEL_CHECKS_1_3_3.json",
}
OVERCLAIM_CONTEXT_SAFE_REFS = {
    # This executable contains detector tokens and rejection reasons used to
    # block grand-TOE/all-domain promotion; it is not a promoted claim surface.
    "proofs/finite_model_checks/run_finite_model_checks.py",
}

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def long_fs_path(path: Path) -> str:
    value = str(path if path.is_absolute() else path.resolve())
    if os.name != "nt" or value.startswith("\\\\?\\"):
        return value
    if value.startswith("\\\\"):
        return "\\\\?\\UNC\\" + value[2:]
    return "\\\\?\\" + value


def path_exists(path: Path) -> bool:
    return os.path.exists(long_fs_path(path))


def is_file(path: Path) -> bool:
    return os.path.isfile(long_fs_path(path))


def read_bytes(path: Path) -> bytes:
    with open(long_fs_path(path), "rb") as handle:
        return handle.read()


def read_text(path: Path) -> str:
    with open(long_fs_path(path), "r", encoding="utf-8", errors="ignore") as handle:
        return handle.read()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(read_text(path))


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(long_fs_path(path), "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_text_if_changed(path: Path, text: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = text.encode("utf-8")
    if path_exists(path) and read_bytes(path) == data:
        return False
    with open(long_fs_path(path), "wb") as handle:
        handle.write(data)
    return True


def write_json_if_changed(path: Path, payload: Any) -> bool:
    return write_text_if_changed(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def pdf_audit() -> dict[str, Any]:
    from release_machine import oc133_v12

    quality = oc133_v12.pdf_text_quality(ROOT)
    forbidden = re.compile(
        r"\b(TODO|TBD|FIXME|PLACEHOLDER|Lorem ipsum|1\.3\.2|oc_core_1_3_2|irrefutable|final truth|theory of everything|all modern science|better than all modern science|proves all science)\b",
        re.I,
    )
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on local toolchain
        return {"state": "FAIL", "error": f"pypdf_unavailable:{exc}", "quality": quality}

    rows = []
    text_dir = EDITORIAL / "pdf_text_audit"
    text_dir.mkdir(parents=True, exist_ok=True)
    for name in PDFS:
        path = ARTIFACTS / name
        reader = PdfReader(str(path))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        text_ref = text_dir / f"{path.stem}.txt"
        write_text_if_changed(text_ref, text)
        rows.append(
            {
                "artifact": rel(path),
                "text_ref": rel(text_ref),
                "pages": len(reader.pages),
                "text_chars": len(text),
                "version_present": VERSION in text,
                "forbidden_hit_total": len(list(forbidden.finditer(text))),
            }
        )
    failed = [row for row in rows if not row["version_present"] or row["forbidden_hit_total"]]
    return {
        "state": "PASS" if quality.get("state") == "PASS" and not failed else "FAIL",
        "quality": quality,
        "rows": rows,
        "failure_total": len(failed) + int(quality.get("state") != "PASS"),
    }


def metadata_audit() -> dict[str, Any]:
    paths = [
        ROOT / "VERSION",
        ROOT / "manifest.json",
        ROOT / "CITATION.cff",
        ROOT / ".codemeta.json",
        ROOT / "ro-crate-metadata.jsonld",
        EDITORIAL / "metadata_drafts" / "zenodo.no_send.draft.json",
    ]
    rows = []
    stale = []
    for path in paths:
        if not path_exists(path):
            rows.append({"path": rel(path), "exists": False, "version_present": False, "stale_132": False})
            stale.append(rel(path))
            continue
        text = read_text(path)
        row = {
            "path": rel(path),
            "exists": True,
            "version_present": VERSION in text,
            "stale_132": bool(re.search(r"1\.3\.2|oc_core_1_3_2", text, re.I)),
            "no_send_present": ("NO_SEND" in text or "no-send" in text.lower() or "no_send" in text.lower()) if "zenodo" in path.name.lower() else None,
        }
        rows.append(row)
        if not row["version_present"] or row["stale_132"]:
            stale.append(rel(path))
    return {"state": "PASS" if not stale else "FAIL", "rows": rows, "failure_total": len(stale), "failures": stale}


def zip_audit() -> dict[str, Any]:
    zip_path = ARTIFACTS / "oc_core_1_3_3_no_send_release.zip"
    manifest_path = EDITORIAL / "OC_CORE_1_3_3_ZIP_INTEGRITY_latest.json"
    manifest = read_json(manifest_path)
    actual = sha256_file(zip_path)
    expected = manifest.get("package_sha256") or manifest.get("zip_sha256") or manifest.get("sha256")
    return {
        "state": "PASS" if actual == expected else "FAIL",
        "zip": rel(zip_path),
        "manifest": rel(manifest_path),
        "actual_sha256": actual,
        "manifest_sha256": expected,
    }


def journal_package_audit() -> dict[str, Any]:
    index_path = ROOT / "releases" / RELEASE_ID / "submission_packages" / "SUBMISSION_PACKAGE_INDEX.json"
    index = read_json(index_path)
    rows = index.get("rows", index.get("packages", []))
    failures = []
    for row in rows:
        venue = row.get("venue_id")
        if row.get("package_status") != "OWNER_REVIEW_READY_NO_SEND":
            failures.append(f"{venue}:bad_status")
        if row.get("submission_allowed") is not False or row.get("journal_submissions_allowed") is not False:
            failures.append(f"{venue}:send_unlocked")
        components = row.get("required_components", [])
        component_ids = {component.get("component_id") for component in components if isinstance(component, dict)}
        missing_component_ids = sorted(REQUIRED_JOURNAL_COMPONENT_IDS - component_ids)
        for component_id in missing_component_ids:
            failures.append(f"{venue}:{component_id}:missing")
        for component in components:
            if component.get("status") != "READY_NO_SEND":
                failures.append(f"{venue}:{component.get('component_id')}:not_ready")
            component_path = ROOT / str(component.get("path", ""))
            if component.get("required") is True and not is_file(component_path):
                failures.append(f"{venue}:{component.get('component_id')}:missing_file")
            if component_path.suffix.lower() in TEXT_SUFFIXES and is_file(component_path):
                text = read_text(component_path)
                if STALE_RELEASE_RE.search(text):
                    failures.append(f"{venue}:{component.get('component_id')}:stale_132")
                if has_unsafe_absolute_overclaim(text):
                    failures.append(f"{venue}:{component.get('component_id')}:absolute_overclaim")
    return {
        "state": "PASS" if index.get("package_total") == 8 and len(rows) == 8 and not failures else "FAIL",
        "index": rel(index_path),
        "package_total": index.get("package_total"),
        "row_total": len(rows),
        "package_status_counts": index.get("package_status_counts"),
        "failure_total": len(failures),
        "failures": failures,
    }


def claim_surface_audit() -> dict[str, Any]:
    failures = []
    rows = []
    ledger = read_json(ROOT / "claims" / "CLAIM_LEDGER_1_3_3.json")
    if ledger.get("release_id") != RELEASE_ID or ledger.get("version") != VERSION:
        failures.append("claim_ledger_version_or_release_id")
    for key in ["unsupported_promoted_total", "adversarial_review_blocker_total", "scientific_promotion_wording_violation_total"]:
        if ledger.get(key) != 0:
            failures.append(f"claim_ledger_{key}")
    if ledger.get("release_promotion_allowed") is not False:
        failures.append("claim_ledger_release_promotion_unlocked")
    for item in ledger.get("rows", []):
        claim_id = item.get("claim_id")
        evidence_ref = str(item.get("evidence_ref", ""))
        evidence_path = ROOT / evidence_ref.split("::", 1)[0]
        if not evidence_ref or not path_exists(evidence_path):
            failures.append(f"{claim_id}:missing_evidence_ref")
        if not item.get("scope_limit"):
            failures.append(f"{claim_id}:missing_scope_limit")
        if is_promoted_public_status(item.get("public_status")) and item.get("scientific_promotion_allowed") is not True:
            failures.append(f"{claim_id}:promoted_without_scientific_allowed")
    for ref in CLAIM_SURFACE_REFS:
        path = ROOT / ref
        text = read_text(path) if path_exists(path) else ""
        row = {
            "path": ref,
            "exists": path_exists(path),
            "version_present": VERSION in text,
            "stale_132": bool(STALE_RELEASE_RE.search(text)),
            "absolute_overclaim": has_unsafe_absolute_overclaim(text),
        }
        rows.append(row)
        if not row["exists"]:
            failures.append(f"{ref}:missing")
        if not row["version_present"]:
            failures.append(f"{ref}:version_missing")
        if row["stale_132"]:
            failures.append(f"{ref}:stale_132")
        if row["absolute_overclaim"]:
            failures.append(f"{ref}:absolute_overclaim")
    return {
        "state": "PASS" if not failures else "FAIL",
        "claim_total": ledger.get("claim_total"),
        "surface_total": len(rows),
        "failure_total": len(failures),
        "failures": failures,
        "rows": rows,
    }


def is_promoted_public_status(value: Any) -> bool:
    status = str(value or "")
    return status == "PROMOTED" or status.startswith("PROMOTED_")


def has_unsafe_absolute_overclaim(text: str) -> bool:
    safe_markers = [
        "not ",
        "no ",
        "blocked",
        "disallow",
        "false",
        "quarantine",
        "background",
        "unless separately proved",
        "without promoting",
        "not_",
    ]
    for line in text.splitlines():
        if not ABSOLUTE_OVERCLAIM_RE.search(line):
            continue
        lowered = line.lower()
        if not any(marker in lowered for marker in safe_markers):
            return True
    return False


def packaged_surface_audit() -> dict[str, Any]:
    inventory = read_json(EDITORIAL / "OC_CORE_1_3_3_ARTIFACT_INVENTORY.json")
    failures = []
    scanned_total = 0
    stale_hits = []
    overclaim_hits = []
    missing = []
    for row in inventory.get("rows", []):
        ref = str(row.get("path", ""))
        path = ROOT / ref
        if not path_exists(path):
            missing.append(ref)
            failures.append(f"{ref}:missing")
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        scanned_total += 1
        text = read_text(path)
        if ref not in STALE_CONTEXT_SAFE_REFS and STALE_RELEASE_RE.search(text):
            stale_hits.append(ref)
            failures.append(f"{ref}:stale_132")
        if ref not in OVERCLAIM_CONTEXT_SAFE_REFS and has_unsafe_absolute_overclaim(text):
            overclaim_hits.append(ref)
            failures.append(f"{ref}:absolute_overclaim")
    zip_path = ARTIFACTS / "oc_core_1_3_3_no_send_release.zip"
    zip_self_ref_failures = []
    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()
        for forbidden in [
            "OC_CORE_1_3_3_PERSONAL_RELEASE_AUDIT_latest.json",
            "OC_CORE_1_3_3_POST_GENERATION_REPRODUCIBILITY_MANIFEST.json",
            "OC_CORE_1_3_3_ZIP_INTEGRITY_latest.json",
            "OC_CORE_1_3_3_SHA256SUMS",
        ]:
            if any(name.endswith(forbidden) for name in names):
                zip_self_ref_failures.append(forbidden)
                failures.append(f"zip_self_ref:{forbidden}")
    return {
        "state": "PASS" if not failures else "FAIL",
        "inventory_artifact_total": inventory.get("artifact_total"),
        "text_scanned_total": scanned_total,
        "stale_hit_total": len(stale_hits),
        "stale_hits": stale_hits[:50],
        "absolute_overclaim_hit_total": len(overclaim_hits),
        "absolute_overclaim_hits": overclaim_hits[:50],
        "missing_total": len(missing),
        "zip_self_ref_failure_total": len(zip_self_ref_failures),
        "failure_total": len(failures),
        "failures": failures[:100],
    }


def main() -> int:
    scorecard_doc = read_json(EDITORIAL / "OC_CORE_1_3_3_RELEASE_SCORECARD_latest.json")
    scorecard = scorecard_doc.get("summary", scorecard_doc)
    cerberus = read_json(ROOT / "reviews" / "oc133_llm_cerberus" / "OC133_LLM_CERBERUS_SUMMARY.json")
    publish_manifest = read_json(EDITORIAL / "OC_CORE_1_3_3_PUBLISH_MANIFEST_DRAFT.json")
    pdf = pdf_audit()
    metadata = metadata_audit()
    zip_report = zip_audit()
    journal = journal_package_audit()
    claims = claim_surface_audit()
    packaged = packaged_surface_audit()
    checks = {
        "scorecard_pass": scorecard.get("master_verdict") == "PASS" and scorecard.get("gate_counts", {}).get("FAIL", 0) == 0 and scorecard.get("gate_counts", {}).get("BLOCKED", 0) == 0,
        "external_review_ready_no_send": scorecard.get("external_review_ready_no_send") is True,
        "all_domain_ready_no_send_false": scorecard.get("all_domain_ready_no_send") is False,
        "no_send_locked": publish_manifest.get("publish_allowed") is False and publish_manifest.get("journal_submissions_allowed") is False and publish_manifest.get("owner_approved") is False,
        "cerberus_zero_critical_high": cerberus.get("critical_open_total") == 0 and cerberus.get("high_open_total") == 0 and cerberus.get("parse_failure_total") == 0,
        "pdf_quality_pass": pdf.get("state") == "PASS",
        "zip_integrity_pass": zip_report.get("state") == "PASS",
        "journal_packages_pass": journal.get("state") == "PASS",
        "metadata_pass": metadata.get("state") == "PASS",
        "claim_surface_pass": claims.get("state") == "PASS",
        "packaged_surface_pass": packaged.get("state") == "PASS",
    }
    blockers = [name for name, ok in checks.items() if not ok]
    payload = {
        "schema_id": "OC_CORE_1_3_3_PERSONAL_RELEASE_AUDIT_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "verdict": "READY_FOR_FINAL_OWNER_APPROVAL_NO_SEND" if not blockers else "RELEASE_REPAIR_REQUIRED_NO_SEND",
        "public_release_allowed": False,
        "zenodo_allowed": False,
        "journal_submission_allowed": False,
        "github_tag_or_release_allowed": False,
        "checks": checks,
        "blockers": blockers,
        "scorecard": {
            "master_verdict": scorecard.get("master_verdict"),
            "release_state": scorecard.get("release_state"),
            "gate_counts": scorecard.get("gate_counts"),
            "all_domain_blocker_ids": scorecard.get("all_domain_blocker_ids"),
        },
        "cerberus": {
            "critical_open_total": cerberus.get("critical_open_total"),
            "high_open_total": cerberus.get("high_open_total"),
            "parse_failure_total": cerberus.get("parse_failure_total"),
        },
        "pdf": pdf,
        "metadata": metadata,
        "zip": zip_report,
        "journal_packages": journal,
        "claim_surface": claims,
        "packaged_surface": packaged,
    }
    write_json_if_changed(OUT_JSON, payload)
    blocker_lines = [f"- `{blocker}`" for blocker in blockers] if blockers else ["- none"]
    lines = [
        "# OC Core 1.3.3 Personal Release Audit",
        "",
        f"- verdict: `{payload['verdict']}`",
        "- public release: `BLOCKED_PENDING_SEPARATE_OWNER_APPROVAL`",
        f"- release_state: `{payload['scorecard']['release_state']}`",
        f"- gate_counts: `{payload['scorecard']['gate_counts']}`",
        f"- Cerberus critical/high/parse: `{payload['cerberus']['critical_open_total']}/{payload['cerberus']['high_open_total']}/{payload['cerberus']['parse_failure_total']}`",
        f"- package SHA-256: `{zip_report['actual_sha256']}`",
        f"- journal packages: `{journal['package_total']}` packages, `{journal['package_status_counts']}`",
        f"- claim surface: `{claims['state']}` failures=`{claims['failure_total']}`",
        f"- packaged surface: `{packaged['state']}` failures=`{packaged['failure_total']}`",
        "",
        "## Boundary",
        "",
        "This audit certifies bounded external-review readiness only. Full-domain universal completion and global-superiority obligations remain in the background science program.",
        "",
        "## Blockers",
        "",
        *blocker_lines,
    ]
    write_text_if_changed(OUT_MD, "\n".join(lines) + "\n")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not blockers else 1


if __name__ == "__main__":
    raise SystemExit(main())
