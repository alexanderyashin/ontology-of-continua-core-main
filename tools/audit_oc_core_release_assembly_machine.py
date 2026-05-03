from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from assemble_oc_core_release_package import (
    ACKNOWLEDGEMENT_NAMES,
    DEDICATION_TEXT,
    FRONTMATTER_REQUIRED_SECTIONS,
    TEXT_ARTIFACTS,
    assembly_paths,
    artifact_title,
)
from oc_core_release_assembly_lib import ROOT, artifact_hash, read_json, stable_json, validation_result

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from release_machine.versioning import version_from_release_id


CYRILLIC_RE = re.compile(r"[\u0400-\u04FF]")
FORBIDDEN_TEXT_RE = re.compile(
    r"("
    r"no_send|publish_allowed\s*[:=]\s*false|owner_approved\s*[:=]\s*false|"
    r"github release action|zenodo deposit action|tag movement|doi minting action|"
    r"route sheet|control sheet|raw ledger|checksum wall|"
    r"\bTODO\b|\bTBD\b|"
    r"бляд|хуй|ебан|ёбан|сука|мудак"
    r")",
    re.IGNORECASE,
)
LOCAL_PATH_RE = re.compile("|".join([r"C:" + r"\\Users\\", r"file:" + r"//", r"estra-" + r"private-work"]), re.IGNORECASE)
MISSING_CHAR_RE = re.compile(r"Missing character", re.IGNORECASE)
FRONTMATTER_BODY_LEAK_RE = re.compile(
    r"\b(Define|Bind|State limits and falsifiers for|Synthesize)\s+"
    r"(Title Page|Dedication|Abstract|Keywords|Citation, DOI|Table of Contents|List of Figures|Symbols|Author, Instrument)",
    re.IGNORECASE,
)
READER_SURFACE_CONTROL_RE = re.compile(
    r"review-space artifact is assembled|not a GitHub or Zenodo publication action|"
    r"terminal text contracts|deterministic transition rules|generated terminal prose",
    re.IGNORECASE,
)
BODY_MARKER_RE = re.compile(r"(^|\n)#\s+Body\b", re.IGNORECASE)


def machine_audit_paths(release_id: str, version: str, assembly_revision: str | None = None) -> dict[str, Path]:
    base = assembly_paths(release_id, version, assembly_revision)["assembly_json"].parent
    return {
        "audit_json": base / f"OC_CORE_RELEASE_ASSEMBLY_MACHINE_AUDIT_{version}.json",
        "audit_md": base / f"OC_CORE_RELEASE_ASSEMBLY_MACHINE_AUDIT_{version}.md",
    }


def scan_text(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return [{"kind": "missing_file", "path": str(path)}]
    text = path.read_text(encoding="utf-8", errors="replace")
    findings: list[dict[str, Any]] = []
    for regex, kind in [
        (CYRILLIC_RE, "cyrillic_public_surface_leak"),
        (FORBIDDEN_TEXT_RE, "forbidden_public_surface_phrase"),
        (LOCAL_PATH_RE, "local_or_private_path_leak"),
    ]:
        for match in regex.finditer(text):
            start = max(0, match.start() - 60)
            end = min(len(text), match.end() + 60)
            findings.append(
                {
                    "kind": kind,
                    "path": str(path.relative_to(ROOT)),
                    "offset": match.start(),
                    "match": match.group(0),
                    "context": text[start:end].replace("\n", " ")[:180],
                }
            )
            if len(findings) >= 20:
                return findings
    return findings


def pdf_text(path: Path, *, pages: int = 16) -> str:
    if not path.exists():
        return ""
    try:
        completed = subprocess.run(
            ["pdftotext", "-f", "1", "-l", str(pages), str(path), "-"],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=60,
        )
        return completed.stdout if completed.returncode == 0 else ""
    except Exception:
        return ""


def normalize_surface(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def frontmatter_cut(text: str) -> str:
    match = BODY_MARKER_RE.search(text)
    return text[: match.start()] if match else text[:12000]


def frontmatter_findings_for_source(path: Path, artifact_type_id: str, version: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    if not path.exists():
        return [{"kind": "reader_source_missing", "path": str(path.relative_to(ROOT)), "artifact_type_id": artifact_type_id}]
    text = path.read_text(encoding="utf-8", errors="replace")
    front = frontmatter_cut(text)
    normalized_front = normalize_surface(front)
    title = artifact_title(artifact_type_id, version)
    required_pairs = [
        ("title_page", title),
        ("dedication", DEDICATION_TEXT),
        ("acknowledgements", "Substantive review and idea acknowledgements."),
        ("acknowledgement_boundary", "does not imply authorship, endorsement, publication approval, or agreement"),
        ("abstract", "## Abstract"),
        ("reader_contract", "## Reader Contract"),
        ("table_of_contents", "## Table of Contents"),
        ("author_orcid", "ORCID 0009-0008-6166-0914"),
    ]
    for section_id, needle in required_pairs:
        if needle not in front:
            findings.append(
                {
                    "kind": "frontmatter_governance_missing_source_section",
                    "artifact_type_id": artifact_type_id,
                    "path": str(path.relative_to(ROOT)),
                    "section_id": section_id,
                    "needle": needle,
                }
            )
    for name in ACKNOWLEDGEMENT_NAMES:
        if name not in front:
            findings.append(
                {
                    "kind": "frontmatter_governance_missing_acknowledgement_name",
                    "artifact_type_id": artifact_type_id,
                    "path": str(path.relative_to(ROOT)),
                    "name": name,
                }
            )
    first_body_index = text.find("\n# Body")
    for label in ["## Dedication", "## Acknowledgements", "## Abstract", "## Reader Contract", "## Table of Contents"]:
        label_index = text.find(label)
        if label_index < 0 or (first_body_index >= 0 and label_index > first_body_index):
            findings.append(
                {
                    "kind": "frontmatter_governance_source_order_violation",
                    "artifact_type_id": artifact_type_id,
                    "path": str(path.relative_to(ROOT)),
                    "label": label,
                }
            )
    for regex, kind in [
        (FRONTMATTER_BODY_LEAK_RE, "frontmatter_l10_rendered_as_body_prose"),
        (READER_SURFACE_CONTROL_RE, "reader_surface_control_plane_leak"),
    ]:
        match = regex.search(text)
        if match:
            findings.append(
                {
                    "kind": kind,
                    "artifact_type_id": artifact_type_id,
                    "path": str(path.relative_to(ROOT)),
                    "match": match.group(0),
                    "context": normalized_front[max(0, match.start() - 80): match.end() + 120],
                }
            )
    return findings


def frontmatter_findings_for_pdf(path: Path, artifact_type_id: str, version: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    if not path.exists():
        return [{"kind": "reader_pdf_missing", "path": str(path.relative_to(ROOT)), "artifact_type_id": artifact_type_id}]
    text = pdf_text(path, pages=120)
    normalized = normalize_surface(text)
    title = artifact_title(artifact_type_id, version)
    required = [
        ("title_page", title),
        ("dedication", DEDICATION_TEXT),
        ("acknowledgements", "Substantive review and idea acknowledgements."),
        ("abstract", "Abstract"),
        ("reader_contract", "Reader Contract"),
        ("table_of_contents", "Table of Contents"),
        ("author_orcid", "ORCID 0009-0008-6166-0914"),
    ]
    for section_id, needle in required:
        if needle not in text:
            findings.append(
                {
                    "kind": "frontmatter_governance_missing_pdf_section",
                    "artifact_type_id": artifact_type_id,
                    "path": str(path.relative_to(ROOT)),
                    "section_id": section_id,
                    "needle": needle,
                }
            )
    for regex, kind in [
        (FRONTMATTER_BODY_LEAK_RE, "frontmatter_l10_rendered_as_pdf_body_prose"),
        (READER_SURFACE_CONTROL_RE, "reader_pdf_control_plane_leak"),
    ]:
        match = regex.search(text)
        if match:
            findings.append(
                {
                    "kind": kind,
                    "artifact_type_id": artifact_type_id,
                    "path": str(path.relative_to(ROOT)),
                    "match": match.group(0),
                    "context": normalized[max(0, match.start() - 80): match.end() + 120],
                }
            )
    return findings


def build_audit(release_id: str, assembly_revision: str | None = None) -> dict[str, Any]:
    version = version_from_release_id(release_id)
    paths = assembly_paths(release_id, version, assembly_revision)
    assembly = read_json(paths["assembly_json"])
    assembly_audit = read_json(paths["audit_json"])
    terminal_contracts = read_json(paths["terminal_contracts_json"])
    transitions = read_json(paths["transition_records_json"])
    findings: list[dict[str, Any]] = []

    if assembly.get("status") != "OC_CORE_RELEASE_PACKAGE_REVIEW_ARTIFACTS_ASSEMBLED":
        findings.append({"kind": "assembly_status_not_ready", "value": assembly.get("status")})
    if assembly_audit.get("status") != "PASS":
        findings.append({"kind": "assembly_audit_not_pass", "value": assembly_audit.get("status")})
    if assembly.get("publication_actions_performed") is not False:
        findings.append({"kind": "publication_action_flag_not_false", "value": assembly.get("publication_actions_performed")})
    if terminal_contracts.get("blocked_terminal_total", 0) != 0:
        findings.append({"kind": "blocked_terminal_contracts", "value": terminal_contracts.get("blocked_terminal_total")})
    if transitions.get("transition_record_total") != max(terminal_contracts.get("terminal_node_total", 0) - 1, 0):
        findings.append(
            {
                "kind": "transition_count_mismatch",
                "transition_record_total": transitions.get("transition_record_total"),
                "terminal_node_total": terminal_contracts.get("terminal_node_total"),
            }
        )

    scan_paths = [
        paths["terminal_contracts_json"],
        paths["terminal_contracts_md"],
        paths["transition_records_json"],
        paths["transition_records_md"],
        paths["assembly_json"],
        paths["assembly_md"],
        paths["manifest_json"],
        paths["checksums_txt"],
    ]
    for row in assembly.get("artifact_rows", []):
        if row.get("artifact_type_id") in TEXT_ARTIFACTS:
            source_path = ROOT / str(row.get("source_path"))
            pdf_path = ROOT / str(row.get("pdf_path"))
            findings.extend(frontmatter_findings_for_source(source_path, row["artifact_type_id"], version))
            findings.extend(frontmatter_findings_for_pdf(pdf_path, row["artifact_type_id"], version))
            if "frontmatter_body_excluded_total" not in row:
                findings.append(
                    {
                        "kind": "frontmatter_body_exclusion_metric_missing",
                        "artifact_type_id": row.get("artifact_type_id"),
                        "required_sections": FRONTMATTER_REQUIRED_SECTIONS,
                    }
                )
        for output in row.get("output_paths", []):
            path = ROOT / output
            if path.suffix.lower() in {".md", ".json", ".txt"}:
                scan_paths.append(path)
        pdf_build = row.get("pdf_build")
        if pdf_build:
            stderr_tail = str(pdf_build.get("stderr_tail") or "")
            stdout_tail = str(pdf_build.get("stdout_tail") or "")
            if MISSING_CHAR_RE.search(stderr_tail) or MISSING_CHAR_RE.search(stdout_tail):
                findings.append(
                    {
                        "kind": "pdf_engine_missing_character_warning",
                        "artifact_type_id": row.get("artifact_type_id"),
                        "stderr_tail": stderr_tail[-1000:],
                    }
                )
            if not pdf_build.get("ok"):
                findings.append({"kind": "pdf_build_not_ok", "artifact_type_id": row.get("artifact_type_id")})

    for path in sorted(set(scan_paths), key=lambda item: str(item)):
        findings.extend(scan_text(path))

    severity_counts: dict[str, int] = {}
    for finding in findings:
        severity = "CRITICAL" if finding["kind"] in {
            "cyrillic_public_surface_leak",
            "forbidden_public_surface_phrase",
            "local_or_private_path_leak",
            "pdf_engine_missing_character_warning",
            "frontmatter_governance_missing_source_section",
            "frontmatter_governance_missing_pdf_section",
            "frontmatter_l10_rendered_as_body_prose",
            "frontmatter_l10_rendered_as_pdf_body_prose",
            "reader_surface_control_plane_leak",
            "reader_pdf_control_plane_leak",
        } else "HIGH"
        finding["severity"] = severity
        severity_counts[severity] = severity_counts.get(severity, 0) + 1

    payload: dict[str, Any] = {
        "schema_id": "OC_CORE_RELEASE_ASSEMBLY_MACHINE_AUDIT_v1",
        "artifact_kind": "OC_CORE_RELEASE_ASSEMBLY_MACHINE_AUDIT",
        "status": "PASS" if not findings else "FAIL",
        "release_id": release_id,
        "version": version,
        "assembly_revision": assembly_revision,
        "structure_source": assembly.get("structure_source"),
        "source_hashes": {
            "release_package_assembly_hash": assembly.get("artifact_hash"),
            "release_package_assembly_audit_hash": assembly_audit.get("artifact_hash"),
            "terminal_contracts_hash": terminal_contracts.get("artifact_hash"),
            "transition_records_hash": transitions.get("artifact_hash"),
        },
        "summary": {
            "terminal_node_total": terminal_contracts.get("terminal_node_total"),
            "blocked_terminal_total": terminal_contracts.get("blocked_terminal_total"),
            "transition_record_total": transitions.get("transition_record_total"),
            "artifact_type_total": len(assembly.get("artifact_rows", [])),
            "finding_total": len(findings),
            "severity_counts": severity_counts,
        },
        "findings": findings,
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def render_md(payload: dict[str, Any]) -> str:
    lines = [
        f"# OC Core Release Assembly Machine Audit {payload['version']}",
        "",
        f"Status: `{payload['status']}`",
        f"Assembly revision: `{payload.get('assembly_revision') or 'default'}`",
        f"Structure source: `{payload.get('structure_source')}`",
        f"Artifact hash: `{payload['artifact_hash']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Findings", ""])
    if not payload["findings"]:
        lines.append("- none")
    for finding in payload["findings"][:200]:
        lines.append(f"- `{finding['severity']}` `{finding['kind']}`: `{finding.get('path') or finding.get('artifact_type_id') or 'assembly'}`")
    return "\n".join(lines).rstrip() + "\n"


def expected_files(release_id: str, assembly_revision: str | None = None) -> dict[Path, str]:
    version = version_from_release_id(release_id)
    audit = build_audit(release_id, assembly_revision)
    paths = machine_audit_paths(release_id, version, assembly_revision)
    return {
        paths["audit_json"]: stable_json(audit),
        paths["audit_md"]: render_md(audit),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit OC Core release assembly machine output for surface and process leaks.")
    parser.add_argument("--release", required=True)
    parser.add_argument("--assembly-revision")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if not args.write and not args.check:
        args.check = True
    result = validation_result(expected_files(args.release, args.assembly_revision), write=args.write)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    audit = build_audit(args.release, args.assembly_revision)
    return 0 if result["state"] == "PASS" and audit["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
