from __future__ import annotations

import hashlib
import json
import re
import sys
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

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


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
        text_ref.write_text(text, encoding="utf-8")
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
        if not path.exists():
            rows.append({"path": rel(path), "exists": False, "version_present": False, "stale_132": False})
            stale.append(rel(path))
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
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
    rows = index.get("packages", [])
    failures = []
    for row in rows:
        if row.get("package_status") != "OWNER_REVIEW_READY_NO_SEND":
            failures.append(f"{row.get('venue_id')}:bad_status")
        if row.get("submission_allowed") is not False or row.get("journal_submissions_allowed") is not False:
            failures.append(f"{row.get('venue_id')}:send_unlocked")
        components = row.get("required_components", [])
        for component in components:
            if component.get("status") != "READY_NO_SEND":
                failures.append(f"{row.get('venue_id')}:{component.get('component_id')}:not_ready")
    return {
        "state": "PASS" if index.get("package_total") == 8 and not failures else "FAIL",
        "index": rel(index_path),
        "package_total": index.get("package_total"),
        "package_status_counts": index.get("package_status_counts"),
        "failure_total": len(failures),
        "failures": failures,
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
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
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
        "",
        "## Boundary",
        "",
        "This audit certifies bounded external-review readiness only. Full-domain universal completion and global-superiority obligations remain in the background science program.",
        "",
        "## Blockers",
        "",
        *blocker_lines,
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not blockers else 1


if __name__ == "__main__":
    raise SystemExit(main())
