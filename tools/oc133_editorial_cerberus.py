from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
ARTIFACTS = ROOT / "releases" / RELEASE_ID / "artifacts"
OUT_DIR = ROOT / "reviews" / "oc133_llm_cerberus" / "editorial_release_review"
SUMMARY = OUT_DIR / "OC133_EDITORIAL_CERBERUS_SUMMARY.json"

PDFS = {
    "guide": "00_OC_CORE_1_3_3_RELEASE_GUIDE_EN.pdf",
    "master": "OC_CORE_1_3_3_MASTER_MONOGRAPH_EN.pdf",
    "journal": "OC_CORE_1_3_3_JOURNAL_CORE_EN.pdf",
    "methods": "OC_CORE_1_3_3_METHODS_AND_REPRODUCIBILITY_COMPANION_EN.pdf",
    "reviewer": "OC_CORE_1_3_3_REVIEWER_ATTACK_AND_RESPONSE_MAP_EN.pdf",
}

ROLES = {
    "scientific_copyeditor": "Read as a senior scientific copyeditor. Ask who the target reader is, what each section teaches, whether the prose is coherent paragraph by paragraph, and whether grammar, diction, transitions, and terminology are publication-grade.",
    "technical_editor": "Read as a technical editor. Attack structure, theorem/evidence navigation, notation, formulas, cross-references, reproducibility path, and whether the science flows into the manuscript rather than being dumped as ledgers.",
    "journal_editor": "Read as a journal editor deciding whether to send for peer review. Ask what the text is about, why it exists, whether the argument is ordered correctly, whether claims are defensible, and whether the manuscript set is suitable for external review.",
    "layout_toc_page_flow_reviewer": "Read as a layout and document-design reviewer. Inspect title pages, dedication, abstracts, TOC, page flow, section hierarchy, list/table balance, figure use, visual route, and whether each PDF looks like a serious scientific document.",
    "hostile_reader": "Read as an antagonistic expert. Find places where the document feels glued, evasive, inflated, incomplete, unreadable, underexplained, insufficiently illustrated, or not publication-grade.",
    "bibliography_metadata_editor": "Read as a bibliography, literature, and metadata editor. Check whether literature coverage is adequate for the claims, whether prior-art positioning is serious, and whether DOI, version, ORCID, title, keywords, and public-record metadata are consistent.",
    "claim_evidence_prosecutor": "Read as a claim/evidence prosecutor. Find any public claim, implication, title, abstract, heading, or summary sentence that is stronger than the visible theorem/proof/data/reviewer evidence.",
}

SEVERITY_PHASES = {
    "release_blockers": {
        "allowed_severities": ["CRITICAL", "HIGH"],
        "blocking_severities": ["CRITICAL", "HIGH"],
        "instruction": (
            "Phase 1: report only defects that should block public replacement of v1.3.3. "
            "Do not report medium, low, optional, taste, wording-polish, or nice-to-have issues. "
            "A finding is CRITICAL only if it makes the release scientifically false, misleading, non-publication-grade, "
            "or structurally invalid. A finding is HIGH only if a serious journal editor or hostile expert would reasonably "
            "stop the release until repaired. If the issue can wait for post-release polish, omit it entirely in this phase."
        ),
    },
    "major_editorial": {
        "allowed_severities": ["HIGH", "MEDIUM"],
        "blocking_severities": ["HIGH"],
        "instruction": (
            "Phase 2: the CRITICAL class is already presumed clean. Report major editorial defects that still materially "
            "affect publication quality. Do not report low-level copy edits or optional preferences."
        ),
    },
    "polish_backlog": {
        "allowed_severities": ["MEDIUM", "LOW"],
        "blocking_severities": [],
        "instruction": (
            "Phase 3: collect non-blocking polish backlog only. These findings do not block release unless they reveal a "
            "new CRITICAL/HIGH class, in which case mark that row as severity_escalation_required instead of pretending it is polish."
        ),
    },
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def write_text_if_changed(path: Path, text: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = text.rstrip() + "\n"
    if path.exists() and read_text(path) == normalized:
        return False
    path.write_text(normalized, encoding="utf-8", newline="\n")
    return True


def write_json_if_changed(path: Path, payload: Any) -> bool:
    return write_text_if_changed(path, json.dumps(payload, ensure_ascii=False, indent=2))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def pdf_text(path: Path) -> str:
    with tempfile.TemporaryDirectory(prefix="oc133_editorial_pdf_text_") as tmp:
        txt = Path(tmp) / f"{path.stem}.txt"
        completed = subprocess.run(
            ["pdftotext", str(path), str(txt)],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=240,
        )
        if completed.returncode != 0:
            return completed.stderr
        return read_text(txt)


def window(text: str, needle: str, radius: int = 3500) -> str:
    idx = text.lower().find(needle.lower())
    if idx < 0:
        return ""
    return text[max(0, idx - radius) : min(len(text), idx + len(needle) + radius)]


def compact_bundle() -> dict[str, Any]:
    docs: dict[str, Any] = {}
    for key, filename in PDFS.items():
        path = ARTIFACTS / filename
        text = pdf_text(path) if path.exists() else ""
        excerpts = [text[:18000]]
        for needle in [
            "Abstract and Reader Contract",
            "Dedicated to my dear wife Maria",
            "ManuscriptIntegration",
            "Publication-grade text gate",
            "T133-K0-RES",
            "T133-OMEGA-STATUS",
            "target-blind",
            "Cerberus",
            "Journal Owner-Review",
            "Release Boundary",
            "Editorial Passport",
            "Literature and Prior-Art Position",
            "Visual and Design Review",
            "Audience.",
            "Purpose.",
        ]:
            item = window(text, needle)
            if item:
                excerpts.append(item)
        excerpts.append(text[-12000:])
        deduped: list[str] = []
        seen = set()
        for item in excerpts:
            digest = hashlib.sha256(item.encode("utf-8", errors="ignore")).hexdigest()
            if item and digest not in seen:
                seen.add(digest)
                deduped.append(item)
        docs[key] = {
            "filename": filename,
            "exists": path.exists(),
            "sha256": sha256_file(path) if path.exists() else None,
            "text_chars": len(text),
            "line_total": len([line for line in text.splitlines() if line.strip()]),
            "excerpt_total": len(deduped),
            "excerpts": deduped,
        }
    return {
        "release_id": RELEASE_ID,
        "version": VERSION,
        "review_scope": "publication-grade public PDF manuscript set; deterministic full-text hashes plus representative LLM editorial excerpts",
        "pdfs": docs,
    }


def extract_json(text: str) -> dict[str, Any]:
    stripped = text.strip()
    stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
    stripped = re.sub(r"\s*```$", "", stripped)
    decoder = json.JSONDecoder()
    errors: list[str] = []
    for match in re.finditer(r"\{", stripped):
        candidate = stripped[match.start() :]
        try:
            parsed, _end = decoder.raw_decode(candidate)
        except Exception as exc:
            errors.append(str(exc))
            continue
        if isinstance(parsed, dict):
            if parsed.get("role_id") or parsed.get("verdict") or parsed.get("findings") is not None:
                return parsed
    raise ValueError("no valid editorial JSON object in Codex output; parse attempts=" + "; ".join(errors[:5]))


def run_role(role_id: str, role_prompt: str, bundle: dict[str, Any], *, timeout: int, phase: str) -> dict[str, Any]:
    phase_policy = SEVERITY_PHASES[phase]
    prompt = {
        "task": "You are an Editorial Cerberus reviewer for OC Core 1.3.3. Review the supplied public-release manuscript bundle adversarially.",
        "role_id": role_id,
        "role_prompt": role_prompt,
        "severity_phase": phase,
        "severity_phase_policy": phase_policy,
        "acceptance_standard": [
            "Every public PDF must read as coherent scientific prose, not a route/control sheet or raw ledger dump.",
            "Every public PDF must answer: audience, topic, purpose, structure, didactic path, evidence boundary, and intended reviewer use.",
            "Every public PDF must have title/frontmatter, version, DOI, dedication to Maria, abstract/reader contract, and readable flow.",
            "The master monograph must be one integrated manuscript, not old PDF plus delta appendix.",
            "The manuscript set must contain explicit literature/prior-art positioning and a visual/figure route; inadequate references or inadequate figures are HIGH or CRITICAL if they affect publication readiness.",
            "Unsupported TOE/all-domain/superiority claims are critical findings.",
            "Follow severity_phase_policy exactly. Do not use severities outside allowed_severities for this phase.",
        ],
        "return_json_schema": {
            "role_id": role_id,
            "verdict": "PASS or FAIL",
            "severity_phase": phase,
            "critical_open_total": 0,
            "high_open_total": 0,
            "findings": [
                {
                    "finding_id": "string",
                    "severity": "|".join(phase_policy["allowed_severities"]),
                    "status": "OPEN|CLOSED",
                    "artifact": "filename",
                    "issue": "specific issue",
                    "evidence": "short evidence",
                    "required_repair": "specific repair",
                }
            ],
            "notes": "brief",
        },
        "bundle": bundle,
    }
    started = time.time()
    with tempfile.TemporaryDirectory(prefix="oc133_editorial_last_message_") as tmp:
        last_message = Path(tmp) / f"{role_id}_last_message.json"
        command = [
            "codex",
            "exec",
            "--sandbox",
            "read-only",
            "--skip-git-repo-check",
            "--output-last-message",
            str(last_message),
            "-",
        ]
        completed = subprocess.run(
            command,
            cwd=ROOT,
            input=json.dumps(prompt, ensure_ascii=False),
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=timeout,
        )
        last_text = read_text(last_message) if last_message.exists() else ""
    raw = last_text.strip() or ((completed.stdout or "") + "\n" + (completed.stderr or ""))
    parsed: dict[str, Any] | None = None
    parse_error = None
    try:
        parsed = extract_json(raw)
    except Exception as exc:
        parse_error = str(exc)
    payload = {
        "role_id": role_id,
        "severity_phase": phase,
        "command": "codex exec --sandbox read-only --skip-git-repo-check - <editorial-review-json-prompt>",
        "returncode": completed.returncode,
        "elapsed_seconds": round(time.time() - started, 3),
        "raw_output_tail": raw[-6000:],
        "transport_stdout_tail": (completed.stdout or "")[-2000:],
        "transport_stderr_tail": (completed.stderr or "")[-2000:],
        "parsed": parsed,
        "parse_error": parse_error,
        "parse_ok": parsed is not None and parse_error is None,
    }
    write_json_if_changed(OUT_DIR / f"{role_id}.json", payload)
    return payload


def summarize(rows: list[dict[str, Any]], bundle: dict[str, Any]) -> dict[str, Any]:
    critical = 0
    high = 0
    parse_failures = 0
    role_ids: list[str] = []
    findings: list[dict[str, Any]] = []
    omitted_out_of_phase: list[dict[str, Any]] = []
    phases = sorted({str(row.get("severity_phase", "release_blockers")) for row in rows})
    for row in rows:
        row_phase = str(row.get("severity_phase", "release_blockers"))
        allowed_severities = {
            item.upper()
            for item in SEVERITY_PHASES.get(row_phase, SEVERITY_PHASES["release_blockers"])["allowed_severities"]
        }
        parsed = row.get("parsed") if isinstance(row.get("parsed"), dict) else {}
        if not row.get("parse_ok"):
            parse_failures += 1
        role_id = str(row.get("role_id"))
        role_ids.append(role_id)
        for finding in parsed.get("findings", []) if isinstance(parsed.get("findings"), list) else []:
            severity = str(finding.get("severity", "")).upper()
            status = str(finding.get("status", "OPEN")).upper()
            finding["role_id"] = role_id
            finding["severity_phase"] = row_phase
            if severity not in allowed_severities:
                omitted_out_of_phase.append(
                    {
                        "role_id": role_id,
                        "severity_phase": row_phase,
                        "severity": severity,
                        "issue": finding.get("issue"),
                        "omission_reason": "outside_current_severity_phase",
                    }
                )
                continue
            findings.append(finding)
            if status == "OPEN" and severity == "CRITICAL":
                critical += 1
            if status == "OPEN" and severity == "HIGH":
                high += 1
    pdf_hashes = {key: doc.get("sha256") for key, doc in bundle["pdfs"].items()}
    summary = {
        "schema_id": "OC133_EDITORIAL_CERBERUS_SUMMARY_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "state": "PASS" if critical == 0 and high == 0 and parse_failures == 0 else "FAIL",
        "severity_phases": phases,
        "severity_policy": {phase: SEVERITY_PHASES.get(phase) for phase in phases},
        "role_ids": sorted(role_ids),
        "role_total": len(role_ids),
        "critical_open_total": critical,
        "high_open_total": high,
        "parse_failure_total": parse_failures,
        "finding_total": len(findings),
        "findings": findings,
        "omitted_out_of_phase_total": len(omitted_out_of_phase),
        "omitted_out_of_phase": omitted_out_of_phase[:50],
        "waterfall_policy": {
            "active_phases": phases,
            "current_release_blocker_rule": "CRITICAL/HIGH first; no MEDIUM/LOW or taste-polish may enter the release-blocking queue.",
            "next_phase_allowed": critical == 0 and high == 0 and parse_failures == 0,
        },
        "pdf_hashes": pdf_hashes,
        "pdf_text_chars": {key: doc.get("text_chars") for key, doc in bundle["pdfs"].items()},
        "coverage_note": bundle["review_scope"],
    }
    write_json_if_changed(SUMMARY, summary)
    write_text_if_changed(
        OUT_DIR / "OC133_EDITORIAL_CERBERUS_SUMMARY.md",
        "\n".join(
            [
                "# OC Core 1.3.3 Editorial Cerberus",
                "",
                f"State: `{summary['state']}`",
                f"Roles: `{summary['role_total']}`",
                f"Critical open: `{critical}`",
                f"High open: `{high}`",
                f"Parse failures: `{parse_failures}`",
            ]
        ),
    )
    return summary


def aggregate_existing() -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    bundle = compact_bundle()
    write_json_if_changed(OUT_DIR / "OC133_EDITORIAL_CERBERUS_CONTEXT_BUNDLE.json", bundle)
    rows: list[dict[str, Any]] = []
    for role_id in ROLES:
        path = OUT_DIR / f"{role_id}.json"
        if not path.exists():
            rows.append(
                {
                    "role_id": role_id,
                    "parse_ok": False,
                    "parsed": None,
                    "parse_error": "missing role review file",
                }
            )
            continue
        rows.append(json.loads(read_text(path)))
    return summarize(rows, bundle)


def run(*, roles: list[str] | None = None, timeout: int = 900, phase: str = "release_blockers") -> dict[str, Any]:
    if phase not in SEVERITY_PHASES:
        raise ValueError(f"Unknown editorial Cerberus severity phase: {phase}")
    selected = roles or list(ROLES)
    unknown = sorted(set(selected) - set(ROLES))
    if unknown:
        raise ValueError(f"Unknown editorial Cerberus roles: {', '.join(unknown)}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    bundle = compact_bundle()
    write_json_if_changed(OUT_DIR / "OC133_EDITORIAL_CERBERUS_CONTEXT_BUNDLE.json", bundle)
    rows = [run_role(role_id, ROLES[role_id], bundle, timeout=timeout, phase=phase) for role_id in selected]
    return summarize(rows, bundle)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run OC Core 1.3.3 editorial Cerberus LLM review.")
    parser.add_argument("--role", action="append", default=[])
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--phase", choices=sorted(SEVERITY_PHASES), default="release_blockers")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--aggregate-existing", action="store_true")
    args = parser.parse_args(argv)
    if args.check:
        payload = json.loads(read_text(SUMMARY)) if SUMMARY.exists() else {"state": "FAIL", "reason": "missing summary"}
    elif args.aggregate_existing:
        payload = aggregate_existing()
    else:
        payload = run(roles=args.role or None, timeout=args.timeout, phase=args.phase)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload.get("state") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
