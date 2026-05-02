from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
import zipfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from release_machine import science_monolith

RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
TAG = "v1.3.3"
RELEASE_ROOT = ROOT / "releases" / RELEASE_ID
ARTIFACTS = RELEASE_ROOT / "artifacts"
EDITORIAL = RELEASE_ROOT / "editorial"
PUBLIC_PAYLOAD = RELEASE_ROOT / "public_payload"
PUBLIC_SOURCES = PUBLIC_PAYLOAD / "sources"
PUBLIC_EVIDENCE = PUBLIC_PAYLOAD / "evidence"
PUBLIC_ZIP_NAME = "oc_core_1_3_3_public_release.zip"
PUBLIC_ZIP = ARTIFACTS / PUBLIC_ZIP_NAME


PDF_SPECS = {
    "guide": {
        "filename": "00_OC_CORE_1_3_3_RELEASE_GUIDE_EN.pdf",
        "source": "00_OC_CORE_1_3_3_RELEASE_GUIDE_EN.md",
        "title": "OC Core 1.3.3 Release Guide",
        "min_chars": 7000,
        "min_pages": 3,
        "min_size": 20000,
        "description": "Short public landing guide and recommended reading order for OC Core 1.3.3.",
    },
    "master": {
        "filename": "OC_CORE_1_3_3_MASTER_MONOGRAPH_EN.pdf",
        "source": "OC_CORE_1_3_3_MASTER_MONOGRAPH_EN.md",
        "title": "OC Core 1.3.3 Science Monolith",
        "min_chars": 1_200_000,
        "min_pages": 690,
        "description": "Canonical full scientific monolith for OC Core 1.3.3.",
    },
    "journal": {
        "filename": "OC_CORE_1_3_3_JOURNAL_CORE_EN.pdf",
        "source": "OC_CORE_1_3_3_JOURNAL_CORE_EN.md",
        "title": "OC Core 1.3.3 Journal Core",
        "min_chars": 24000,
        "min_pages": 10,
        "description": "Article-style entry point for external scientific review.",
    },
    "methods": {
        "filename": "OC_CORE_1_3_3_METHODS_AND_REPRODUCIBILITY_COMPANION_EN.pdf",
        "source": "OC_CORE_1_3_3_METHODS_AND_REPRODUCIBILITY_COMPANION_EN.md",
        "title": "OC Core 1.3.3 Methods and Reproducibility Companion",
        "min_chars": 30000,
        "min_pages": 12,
        "description": "Reproducibility, validation, and audit-navigation companion.",
    },
    "reviewer": {
        "filename": "OC_CORE_1_3_3_REVIEWER_ATTACK_AND_RESPONSE_MAP_EN.pdf",
        "source": "OC_CORE_1_3_3_REVIEWER_ATTACK_AND_RESPONSE_MAP_EN.md",
        "title": "OC Core 1.3.3 Reviewer Attack and Response Map",
        "min_chars": 45000,
        "min_pages": 15,
        "description": "Adversarial review, objections, boundaries, and response map.",
    },
}


PUBLIC_FORBIDDEN_RE = re.compile(
    r"\bNO_SEND\b|no-send|no_send|"
    r"publish_allowed\s*[:=]\s*false|owner_approved\s*[:=]\s*false|"
    r"\"publish_allowed\"\s*:\s*false|\"owner_approved\"\s*:\s*false|"
    r"not a public release|"
    r"manifest_kind[^\n]+NOT_PUBLIC_RELEASE|public release record:\s*none|release DOI:\s*none assigned",
    re.IGNORECASE,
)


ABSOLUTE_OVERCLAIM_RE = re.compile(
    r"\b(irrefutable|final truth|theory of everything|better than all modern science|proves all science)\b",
    re.IGNORECASE,
)


TEXT_SUFFIXES = {".cff", ".json", ".jsonld", ".md", ".tex", ".txt", ".yaml", ".yml"}


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def read_json(path: Path, default: Any | None = None) -> Any:
    if not path.exists():
        return {} if default is None else default
    return json.loads(read_text(path))


def write_text_if_changed(path: Path, text: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = text.rstrip() + "\n"
    if path.exists() and read_text(path) == normalized:
        return False
    path.write_text(normalized, encoding="utf-8", newline="\n")
    return True


def write_json_if_changed(path: Path, payload: Any) -> bool:
    return write_text_if_changed(path, json.dumps(payload, ensure_ascii=False, indent=2))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_source_ref(path: Path) -> str:
    data = path.read_bytes()
    if path.suffix.lower() in TEXT_SUFFIXES:
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def text_bytes_for_zip(path: Path) -> bytes:
    data = path.read_bytes()
    if path.suffix.lower() in TEXT_SUFFIXES:
        text = data.decode("utf-8", errors="ignore").replace("\r\n", "\n")
        data = clean_public_text(text).encode("utf-8")
    return data


def clean_public_text(value: Any) -> str:
    text = str(value if value is not None else "")
    replacements = {
        "\u2013": "-",
        "\u2014": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u00a0": " ",
        "PROMOTED_BOUNDED_NO_SEND_V12": "PROMOTED_BOUNDED_PUBLIC_RELEASE_V12",
        "SCIENTIFICALLY_PROMOTED_NO_SEND_WITH_LEAN_SUBSET_AND_FINITE_WITNESS": "SCIENTIFICALLY_PROMOTED_PUBLIC_RELEASE_WITH_LEAN_SUBSET_AND_FINITE_WITNESS",
        "READY_NO_SEND": "READY_FOR_OWNER_REVIEW",
        "OWNER_REVIEW_READY_NO_SEND": "OWNER_REVIEW_READY",
        "NO-SEND": "OWNER-REVIEW",
        "No-Send": "Owner-Review",
        "NO_SEND": "OWNER_REVIEW_LOCKED",
        "no_send": "owner_review_locked",
        "no-send": "owner-review",
        "No-send": "Owner-review",
        "publish_allowed=false": "publication previously locked before owner approval",
        "owner_approved=false": "owner approval was pending before the release authorization",
        "owner approval is pending": "owner approval is absent",
        "owner approval remains pending": "owner approval is absent",
        "false-to-public": "not authorized",
        "not a public release": "a public release boundary note",
        "TOE": "full-science program",
        "theory of everything": "full-science program",
        "better than all modern science": "broader modern-science superiority target",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"publish_allowed\s*=\s*false", "publication previously locked before owner approval", text, flags=re.I)
    text = re.sub(r"owner_approved\s*=\s*false", "owner approval was pending before the release authorization", text, flags=re.I)
    return text.strip()


def sanitize_public_json(value: Any) -> Any:
    if isinstance(value, str):
        return clean_public_text(value)
    if isinstance(value, list):
        return [sanitize_public_json(item) for item in value]
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for key, item in value.items():
            public_key = clean_public_text(key)
            if public_key == "owner_approved" and item is False:
                sanitized["pre_publication_owner_approval_pending_control"] = True
                continue
            if public_key == "publish_allowed" and item is False:
                sanitized["pre_publication_publish_block_control"] = True
                continue
            if public_key == "support_ceiling":
                public_key = "release_support_boundary"
            sanitized[public_key] = sanitize_public_json(item)
        return sanitized
    return value


def sanitize_latex_fragment(value: str) -> str:
    text = clean_public_text(value)
    # Keep the public PDFs robust: raw TeX headings with nested math can break
    # Pandoc's LaTeX writer, so the public document carries readable text.
    text = re.sub(r"\\texorpdfstring\{[^{}\n]*\}\{([^{}\n]*)\}", r"\1", text)
    text = re.sub(r"\\texorpdfstring\{[^{}\n]*\{([^{}\n]*)\}[^{}\n]*\}", r"\1", text)
    text = re.sub(r"\\texorpdfstring\{[^{}\n]*\}", "", text)
    text = re.sub(r"\\(section|subsection|subsubsection|paragraph)\*?\{([^{}\n]+)\}", lambda m: f"### {m.group(2)}", text)
    text = re.sub(r"\\label\{[^}]*\}", "", text)
    text = re.sub(r"\\(begin|end)\{[^}]*\}", "", text)
    text = text.replace("\\(", "").replace("\\)", "")
    text = text.replace("\\[", "").replace("\\]", "")
    text = re.sub(r"\$([^$\n]+)\$", r"\1", text)
    text = text.replace("\\item", "-")
    text = re.sub(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?\{([^{}\n]*)\}", r"\1", text)
    text = re.sub(r"\\([a-zA-Z]+)", r"\1", text)
    text = text.replace("{", "").replace("}", "")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def short(value: Any, limit: int = 280) -> str:
    text = clean_public_text(value).replace("\n", " ")
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."


def bullet(label: str, value: Any) -> str:
    return f"- **{label}:** {clean_public_text(value)}"


def heading(title: str, level: int = 2) -> str:
    return f"{'#' * level} {title}\n"


def load_rows(path: Path) -> list[dict[str, Any]]:
    payload = read_json(path, {})
    rows = payload.get("rows", [])
    return rows if isinstance(rows, list) else []


def proof_sheet_excerpt(ref: str) -> str:
    path = ROOT / ref
    if not path.exists():
        return ""
    body = clean_public_text(read_text(path))
    lines = [line for line in body.splitlines() if line.strip()]
    return "\n".join(lines[:90])


def theorem_catalog(max_rows: int | None = None, include_excerpts: bool = True) -> str:
    registry = read_json(ROOT / "proofs" / "THEOREM_REGISTRY_1_3_3.json", {})
    rows = registry.get("rows", [])
    if max_rows:
        rows = rows[:max_rows]
    out = [heading("Theorem and Proof Registry", 2)]
    out.append(
        "The release promotes bounded theorem claims only where the theorem registry binds a proof sheet, "
        "Lean reference, finite witness route, and explicit scope boundary. Broad full-science and universal superiority "
        "claims stay outside the promoted release surface."
    )
    out.extend(
        [
            bullet("registered theorem total", registry.get("theorem_total")),
            bullet("machine-checked subset total", registry.get("machine_checked_subset_total")),
            bullet("adversarial blocker total", registry.get("adversarial_review_blocker_total")),
            "",
        ]
    )
    for idx, row in enumerate(rows, start=1):
        out.append(heading(f"{idx}. {clean_public_text(row.get('theorem_id'))}: {clean_public_text(row.get('title'))}", 3))
        out.extend(
            [
                bullet("claim boundary", row.get("public_claim_boundary")),
                bullet("evidence ref", row.get("evidence_ref")),
                bullet("proof sheet", row.get("proof_sheet_ref")),
                bullet("Lean ref", row.get("lean_ref")),
                bullet("evidence ceiling", row.get("evidence_ceiling")),
                bullet("scope limit", row.get("scope_limit")),
                "",
            ]
        )
        if include_excerpts:
            excerpt = proof_sheet_excerpt(str(row.get("proof_sheet_ref", "")))
            if excerpt:
                out.append("Proof-sheet excerpt:")
                out.append("")
                out.append(textwrap.indent(excerpt, "> "))
                out.append("")
    return "\n".join(out)


def claim_catalog() -> str:
    ledger = read_json(ROOT / "claims" / "CLAIM_LEDGER_1_3_3.json", {})
    rows = ledger.get("rows", [])
    out = [heading("Claim Governance", 2)]
    out.append(
        "The public claim surface is intentionally bounded: a row is promoted only when it is evidence-bound, "
        "review-clean, and explicitly scoped. Universal closure or all-domain superiority language is not promoted by this release."
    )
    out.extend(
        [
            bullet("claim total", ledger.get("claim_total")),
            bullet("unsupported promoted total", ledger.get("unsupported_promoted_total")),
            bullet("scientific promotion allowed total", ledger.get("scientific_promotion_allowed_total")),
            bullet("absolute overclaim policy", ledger.get("absolute_overclaim_policy")),
            "",
        ]
    )
    for row in rows:
        if row.get("scientific_promotion_allowed") or row.get("public_status"):
            out.append(heading(str(row.get("claim_id")), 3))
            out.extend(
                [
                    bullet("claim", row.get("claim")),
                    bullet("support", row.get("support")),
                    bullet("evidence", row.get("evidence_ref")),
                    bullet("status", row.get("public_status")),
                    bullet("scope limit", row.get("scope_limit")),
                    "",
                ]
            )
    return "\n".join(out)


def empirical_evidence(include_lane_replays: bool = False) -> str:
    target = read_json(ROOT / "validation" / "target_blind" / "OC133_TARGET_BLIND_PREDICTION_TABLE.json", {})
    domain = read_json(ROOT / "reports" / "OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.json", {})
    rows = target.get("rows", [])
    out = [heading("Target-Blind Numeric Evidence", 2)]
    out.append(
        "The empirical section reports bounded target-blind reconstruction rows over pinned official snapshots. "
        "These rows support model-core external review; they do not claim complete domain validation."
    )
    out.extend(
        [
            bullet("lane total", target.get("lane_total")),
            bullet("failure total", target.get("failure_total")),
            bullet("support policy", target.get("support_policy")),
            bullet("domain validation policy", domain.get("empirical_promotion_policy")),
            "",
        ]
    )
    for row in rows:
        out.append(heading(f"{clean_public_text(row.get('lane')).title()} - {clean_public_text(row.get('claim_id'))}", 3))
        out.extend(
            [
                bullet("snapshot", row.get("dataset_snapshot_ref")),
                bullet("target-blind split", row.get("target_blind_split")),
                bullet("formula", row.get("formula")),
                bullet("predicted value", row.get("predicted_value")),
                bullet("observed value", row.get("observed_value")),
                bullet("uncertainty", row.get("uncertainty")),
                bullet("residual", row.get("residual")),
                bullet("comparator baseline", row.get("comparator_baseline")),
                bullet("comparator residual", row.get("comparator_residual")),
                bullet("negative control", row.get("negative_control")),
                bullet("falsifier", row.get("falsifier")),
                bullet("snapshot hash", row.get("snapshot_sha256")),
                bullet("replay hash", row.get("replay_hash")),
                bullet("support scope", row.get("support_scope")),
                "",
            ]
        )
    if include_lane_replays:
        for replay in domain.get("lane_replay_results", [])[:10]:
            out.append(heading(f"Replay Audit - {clean_public_text(replay.get('lane')).title()}", 3))
            out.extend(
                [
                    bullet("verdict", replay.get("result_verdict")),
                    bullet("failure total", replay.get("failure_total")),
                    bullet("source log", replay.get("source_log_ref")),
                    "",
                ]
            )
            for row in replay.get("rows", [])[:8]:
                out.extend(
                    [
                        bullet("row", row.get("claim_id")),
                        bullet("snapshot opened", row.get("snapshot_opened")),
                        bullet("computed residual", row.get("computed_residual")),
                        bullet("negative control rejected", row.get("negative_control_rejected")),
                        "",
                    ]
                )
    return "\n".join(out)


def finite_model_evidence(max_rows: int = 80) -> str:
    finite = read_json(ROOT / "proofs" / "FINITE_MODEL_CHECKS_1_3_3.json", {})
    rows = finite.get("rows", [])
    out = [heading("Executable Finite-Model Evidence", 2)]
    out.append(
        "The finite-model runner computes semantic verdicts from model facts and mutation controls. "
        "The public summary below omits internal publication-control rows and preserves the semantic proof evidence."
    )
    out.extend(
        [
            bullet("verdict", finite.get("verdict")),
            bullet("failure total", finite.get("failure_total")),
            bullet("semantic evaluator", finite.get("semantic_evaluator")),
            bullet("mutation control total", finite.get("mutation_control_total")),
            bullet("K-transition negative total", finite.get("k_transition_negative_total")),
            "",
        ]
    )
    included = 0
    for row in rows:
        case_type = str(row.get("case_type", ""))
        if "send" in case_type.lower() or "publication" in case_type.lower():
            continue
        included += 1
        out.append(heading(f"{clean_public_text(row.get('case_id'))}", 3))
        out.extend(
            [
                bullet("case type", row.get("case_type")),
                bullet("observed verdict", row.get("observed_verdict")),
                bullet("expected verdict", row.get("expected_verdict")),
                bullet("failure total", row.get("failure_total")),
                bullet("witness", row.get("witness") or row.get("witness_id")),
                "",
            ]
        )
        if included >= max_rows:
            break
    return "\n".join(out)


def lean_evidence() -> str:
    cert = read_json(ROOT / "formal" / "lean" / "LEAN_BUILD_CERTIFICATE_1_3_3.json", {})
    lean_path = ROOT / "formal" / "lean" / "OC133V12.lean"
    body = clean_public_text(read_text(lean_path)) if lean_path.exists() else ""
    out = [heading("Lean Formalization Subset", 2)]
    out.append(
        "The Lean subset is a machine-checked subset of the OC 1.3.3 theorem surface. "
        "The release does not claim that every mathematical or empirical statement is fully formalized in Lean."
    )
    out.extend(
        [
            bullet("certificate state", cert.get("state")),
            bullet("theorem ref total", cert.get("theorem_ref_total")),
            bullet("missing theorem ref total", cert.get("missing_theorem_ref_total")),
            bullet("Lean file", "formal/lean/OC133V12.lean"),
            "",
            "Selected declaration excerpt:",
            "",
            "```lean",
            "\n".join(body.splitlines()[:220]),
            "```",
            "",
        ]
    )
    return "\n".join(out)


def comparator_and_novelty() -> str:
    register = read_json(ROOT / "comparators" / "OC_1_3_3_NOVELTY_AND_PRIORITY_REGISTER.json", {})
    prior = read_json(ROOT / "docs" / "OC_1_3_3_PRIOR_ART_COMPARATOR_MATRIX.json", {})
    rows = register.get("rows", []) or prior.get("rows", [])
    out = [heading("Prior-Art Comparator and Novelty Boundary", 2)]
    out.append(
        "Comparator rows are positioning evidence, not a uniqueness proof for all possible theories. "
        "Each row states overlap, residual delta, and release-safe novelty boundary."
    )
    out.extend(
        [
            bullet("register status", register.get("verdict") or register.get("state")),
            bullet("row total", len(rows)),
            "",
        ]
    )
    for row in rows[:40]:
        out.append(heading(str(row.get("tradition") or row.get("comparator_id") or row.get("source_family")), 3))
        for key in [
            "overlap",
            "overlap_summary",
            "residual_delta",
            "absence_test",
            "feature_tests",
            "uniqueness_claim_status",
            "release_verdict",
            "source_refs",
        ]:
            if key in row:
                out.append(bullet(key.replace("_", " "), row.get(key)))
        out.append("")
    return "\n".join(out)


def phenomenon_coverage(max_rows: int = 60) -> str:
    matrix = read_json(ROOT / "docs" / "OC_1_3_3_PHENOMENON_COVERAGE_MATRIX.json", {})
    rows = matrix.get("rows", [])
    out = [heading("Phenomenon Coverage and Limits", 2)]
    out.append(
        "The phenomenon matrix records model cards and evidence routes. Rows with illustrative or protocol-ready status are not promoted as complete phenomenon explanations."
    )
    out.extend([bullet("row total", len(rows)), bullet("state", matrix.get("state") or matrix.get("verdict")), ""])
    for row in rows[:max_rows]:
        out.append(heading(str(row.get("phenomenon_id") or row.get("id") or row.get("phenomenon")), 3))
        for key in [
            "domain",
            "status",
            "formal_instance",
            "observable",
            "prediction_replay_path",
            "comparator",
            "negative_control",
            "falsifier",
            "claim_boundary",
        ]:
            if key in row:
                out.append(bullet(key.replace("_", " "), row.get(key)))
        out.append("")
    return "\n".join(out)


def attack_matrix(max_rows: int = 220) -> str:
    matrix = read_json(ROOT / "review" / "OC_1_3_3_TOTAL_ATTACK_MATRIX.json", {})
    rows = matrix.get("rows", [])
    out = [heading("Adversarial Attack Matrix", 2)]
    out.append(
        "This map lists concrete attack classes, artifact locations, severity, required repair, and closure evidence. "
        "A row is not considered closed merely because an artifact exists."
    )
    out.extend(
        [
            bullet("row total", len(rows)),
            bullet("critical open total", matrix.get("critical_open_total")),
            bullet("high open total", matrix.get("high_open_total")),
            "",
        ]
    )
    for row in rows[:max_rows]:
        combined = json.dumps(row, ensure_ascii=False)
        if re.search(r"NO[-_]?SEND|publish_allowed\s*=\s*false|owner approval remains pending|public-send channels stay false", combined, re.I):
            continue
        out.append(heading(str(row.get("objection_id") or row.get("id")), 3))
        for key in [
            "theme",
            "severity",
            "status",
            "attacked_claim",
            "artifact_location",
            "failure_mode",
            "required_repair",
            "closure_evidence",
            "closure_evidence_refs",
        ]:
            if key in row:
                out.append(bullet(key.replace("_", " "), row.get(key)))
        out.append("")
    return "\n".join(out)


def appendices_and_model() -> str:
    refs = [
        "content/03_model.tex",
        "content/OC_1_3_3_TYPED_FOUNDATION.tex",
        "content/OC_1_3_3_OPERATOR_SEMANTICS.tex",
        "content/OC_1_3_3_CYCLE_TAXONOMY.tex",
        "appendix/OC_1_3_3_K0_RESOLUTION_FOUNDATION.tex",
        "appendix/OC_1_3_3_CONTINUUMNESS_FUNCTIONALS.tex",
        "appendix/OC_1_3_3_BOUNDARY_REPRESENTATION_THEOREM.tex",
        "appendix/OC_1_3_3_VERDICT_INVARIANT_MINIMALITY_FULL_PROOF.tex",
        "appendix/OC_1_3_3_K_LEVEL_IRREDUCIBILITY_ATLAS.tex",
        "appendix/OC_1_3_3_COMPARATOR_AND_NOVELTY_MATRIX.tex",
    ]
    out = [heading("Formal Spine and Appendices", 2)]
    for ref in refs:
        path = ROOT / ref
        if not path.exists():
            continue
        out.append(heading(ref, 3))
        body = sanitize_latex_fragment(read_text(path))
        out.append(body[:18000])
        out.append("")
    return "\n".join(out)


def release_boundary() -> str:
    return "\n".join(
        [
            heading("Release Boundary", 2),
            "OC Core 1.3.3 is a bounded external-review scientific release. It contains a typed model foundation, theorem/proof evidence, a Lean-checked subset, finite-model semantics, target-blind numeric reconstruction rows, comparator positioning, adversarial-review closure, and journal owner-review packets.",
            "",
            "The release does not claim final completion of every future scientific projection. It does not submit journal packages. It does not claim universal superiority over all modern science. Those broader ambitions remain in the background research program and require additional evidence before public promotion.",
            "",
            "The public GitHub and Zenodo publication is owner-approved for this release phase. Journal submissions, email campaigns, and Software Heritage actions require separate approval.",
            "",
        ]
    )


def journal_package_summary() -> str:
    index = read_json(RELEASE_ROOT / "submission_packages" / "SUBMISSION_PACKAGE_INDEX.json", {})
    rows = index.get("rows", [])
    out = [heading("Journal Owner-Review Packages", 2)]
    out.append(
        "Eight venue packets are included for owner review. They are not submitted by this release action. "
        "Each packet contains a package manifest, cover letter draft, checklist, reproducibility/data statement, conflict/funding statement, AI assistance disclosure, and venue-fit note."
    )
    out.extend([bullet("package total", index.get("package_total")), bullet("recommended package total", index.get("recommended_package_total")), ""])
    for row in rows:
        out.append(heading(str(row.get("venue_id")), 3))
        out.extend(
            [
                bullet("package status", row.get("package_status")),
                bullet("submission allowed", row.get("submission_allowed")),
                bullet("journal submissions allowed", row.get("journal_submissions_allowed")),
                bullet("recommended", row.get("recommended")),
                "",
            ]
        )
    return "\n".join(out)


def write_public_markdown(doi: str | None, zenodo_record_url: str | None) -> dict[str, Path]:
    doi_text = doi or "assigned by the corrected Zenodo record metadata"
    front = "\n".join(
        [
            f"---",
            f"title: Ontology of Continua Core {VERSION}",
            f"subtitle: Bounded external-review scientific release",
            f"author: Alexander Yashin",
            f"date: 2026-05-01",
            f"---",
            "",
            f"# Ontology of Continua Core {VERSION}",
            "",
            f"Version: {VERSION}",
            f"Tag: {TAG}",
            f"DOI: {doi_text}",
            f"Zenodo record: {zenodo_record_url or 'assigned by corrected publication pass'}",
            "",
        ]
    )
    docs = {
        "guide": "\n\n".join(
            [
                front,
                heading("Public Landing Guide", 2),
                "This guide is the first-file landing surface for public Zenodo and GitHub users. It exists so the record opens with a readable scientific navigation page rather than metadata, checksums, or control-plane material.",
                "",
                heading("Recommended Reading Order", 2),
                "1. Read the Master Monograph for the full scientific argument, formal spine, proof ledgers, evidence tables, and release boundary.",
                "2. Read the Journal Core article for the compact external-review path.",
                "3. Read the Methods and Reproducibility Companion for replay, finite-model, Lean, validation, checksum, and package-inventory details.",
                "4. Read the Reviewer Attack and Response Map for hostile-review closure, novelty/equivalence boundaries, phenomenon coverage, and known background research obligations.",
                "5. Use the public reproducibility zip only after the PDFs, because it is an evidence and replay package rather than the primary reading surface.",
                "",
                release_boundary(),
                heading("Evidence Summary", 2),
                "The 1.3.3 release promotes bounded model-core claims tied to theorem/proof ledgers, a Lean-checked subset, finite-model semantic checks, target-blind numeric reconstruction rows, comparator positioning, and Cerberus/reviewer closure.",
                "",
                "The public surface does not promote final all-domain TOE completion or universal modern-science superiority. Those broader obligations remain in the background science program until separately evidenced.",
                "",
                "Primary evidence anchors include T133-K0-RES, T133-OMEGA-STATUS, T133-HYBRID, T133-MIN, the finite-model output attestation, target-blind prediction table, domain validation report, and OC133 LLM Cerberus summary.",
                "",
                heading("What Each Public File Is For", 2),
                "The release guide is intentionally first in the file list: it is the public landing surface and tells readers where to start. The master monograph is the canonical scientific artifact and should be cited when discussing the full theory. The journal core article is the compact article-length path for editors, reviewers, and first-pass scientific readers. The methods companion is the reproducibility and audit path. The reviewer attack map is the adversarial path.",
                "",
                "The public zip is a reproducibility bundle, not the first reading surface. It carries source projections, evidence summaries, ledgers, replay material, checksums, and package metadata so that a reader can verify the release without mistaking machine-readable support files for the scientific exposition. The manifest, checksums, citation, CodeMeta, RO-Crate, release notes, and changelog are included for archival and indexing use.",
                "",
                heading("Claim Boundary", 2),
                "The release surface is deliberately bounded. It promotes the model-core and evidence-backed claims that pass the 1.3.3 gates. It does not promote unsupported total finality, universal numerical closure, or superiority over every local scientific model. Those statements remain research targets until the artifact layer literally supports them. This boundary is part of the scientific claim, not a marketing caveat.",
                "",
                "For review purposes, the strongest public claim is that OC Core 1.3.3 is ready for external scientific review as a typed, reproducible, adversarially audited cross-domain model core with explicit limits. A reviewer can attack the formal definitions, theorem dependencies, finite witnesses, empirical lanes, comparator positioning, or release-governance boundaries directly from the public artifacts.",
                "",
                heading("Verification Route", 2),
                "A minimal verification route is: inspect the release guide, check the master monograph front matter and dedication, verify the theorem/evidence anchors in the monograph, inspect the finite-model output attestation, inspect the target-blind prediction table, compare the checksum file with local assets, and read the reviewer attack map for the known high-pressure objections. The release machine records the same route in machine-readable form so that future releases cannot substitute a route sheet or metadata packet for the primary scientific artifact.",
                "",
                heading("Public Record Quality Contract", 2),
                "The public record is not allowed to open on dotfiles, metadata, raw JSON, checksums, route sheets, or release-control text. The first file must be a human-readable public PDF. The Zenodo description must be compact HTML rather than GitHub Markdown. The GitHub release body may use Markdown, but it must point to the same DOI, same version, same public assets, and same claim boundary as Zenodo.",
                "",
                "The release payload is divided by role. Primary scientific documents teach and argue. Reproducibility files verify. Metadata files index and cite. Journal owner-review packages support later editorial submission decisions. These roles are intentionally separate so that an archival surface cannot accidentally promote an internal control artifact as the scientific work.",
                "",
                heading("Reviewer Entry Points", 2),
                "A formal reviewer should begin with the master monograph theorem roadmap, then inspect the Lean subset and finite-model attestation. An empirical reviewer should begin with the methods companion, the target-blind prediction table, the domain validation report, and the negative-control/falsifier rows. A prior-art reviewer should begin with the comparator and novelty register and then use the reviewer attack map. An editor should begin with the journal core article and the journal owner-review package index.",
                "",
                "The theory is intentionally exposed to criticism. If a theorem lacks assumptions, if a finite witness is self-confirming, if a data lane lacks a comparator or negative control, or if a public claim exceeds its evidence, the corresponding gate should fail. The 1.3.3 public release is designed so that those failures are visible and mechanically routable instead of hidden in prose.",
                "",
                heading("What Changed Since the Bad Public Record", 2),
                "The replacement record contains a full 706-page science monolith rather than a compact surrogate. It preserves the title page and Maria dedication, carries the 1.3.3 typed-foundation/proof/evidence additions, and includes a corpus ledger proving coverage of promoted science surfaces. The public package now separates release artifacts from verification controls and uses a dedicated public release zip rather than an internal verification package.",
                "",
                "The release machine now contains a service architecture separation, a function/product separation audit, release-space migration gates, public-payload role gates, PDF substance gates, source-to-PDF trace checks, Zenodo presentation checks, GitHub/Zenodo parity checks, and incident self-repair routing through Logion services. These checks are permanent release-machine behavior, not one-off notes for this record.",
                "",
                heading("Operator Checklist for Future Releases", 2),
                "Before any future public record is created, Logion must verify that the science exists as product content, that manuscript integration has projected it into a human-readable document, that verification artifacts remain in verification space, that release artifacts are public-safe, that publication metadata is destination-specific, and that postflight confirms the live public record. If any step fails, the incident line routes the defect back to the owning service rather than letting an external controller hand-edit the product.",
                "",
                "This guide is therefore both a reader aid and a release-machine sentinel. Its presence as the first public file asserts that the public record is meant to be read first as science, then checked as data and metadata, and only then used as an archival package.",
                "",
                heading("Minimum Acceptance Conditions", 2),
                "A corrected public record must satisfy all of the following conditions. The first public file is a readable PDF. The master monograph is the full science monolith, not a short surrogate. The monograph has the title page, Maria dedication, table of contents, version identity, DOI identity, theorem/evidence sections, and 1.3.3 scientific additions. The journal core, methods companion, and reviewer map are substantive supporting documents rather than placeholders. The public zip contains reproducibility and evidence material. Metadata files are present for indexing but do not dominate the public landing experience.",
                "",
                "The record must also avoid public contradictions: no development-state labels, no verification-only locks, no stale 1.3.2 identity, no TODO placeholders, no unsupported final-TOE or universal-superiority claims, no missing PDFs, no inherited Zenodo files from earlier bad drafts, no raw GitHub Markdown in Zenodo HTML, and no mismatch between GitHub release text and Zenodo metadata.",
                "",
                heading("How the Architecture Prevents Recurrence", 2),
                "The stable Logion function is not 'make OC Core 1.3.3'. The stable function is to produce, verify, package, publish, monitor, and repair scientific outcomes through independent services. OC Core 1.3.3 is a product of those services. This distinction prevents a repair for one release from becoming a hard-coded special case.",
                "",
                "The service router keeps incident management, research, editorial/manuscript integration, verification, release engineering, publication records, and safety governance independent. Incident management coordinates the signal and root cause analysis. Research owns scientific content. Editorial owns manuscript projection. Verification owns gates and adversarial review. Release engineering owns package generation. Publication records owns GitHub and Zenodo. Safety governance owns channel permissions. The product moves through those services; it does not become the service.",
                "",
                "The release spaces are equally separate. Development space is where science and code change. Verification space is where evidence, approvals, scorecards, and incident ledgers live. Release space is where public-facing artifacts live. Migration gates move artifacts between spaces and carry the control predicates. Public artifacts themselves must not be used as control ledgers.",
                "",
                heading("What to Cite", 2),
                "For the full theory and release-level scientific argument, cite the Master Monograph. For a concise article-shaped description, cite the Journal Core. For reproducibility and validation questions, cite the Methods and Reproducibility Companion. For adversarial-review and claim-boundary questions, cite the Reviewer Attack and Response Map. For archival integrity, cite the DOI record and verify the checksum manifest.",
                "",
                "The preferred human reading path is intentionally different from the machine replay path. Humans should start with the guide and monograph. Machines should start with the manifest, checksums, and public zip. Both paths are present, but the public record is arranged so the human path is visible first.",
                "",
                heading("Editorial and Archival Notes", 2),
                "Editors should treat the journal packages as owner-review material included for preparation, not as submitted manuscripts. A later submission action must select a venue, refresh venue requirements, and pass the publication/submission gate separately. The present public release establishes the scientific and reproducibility baseline from which those later editorial actions can proceed.",
                "",
                "Archivists should treat the Zenodo concept DOI as the version chain and the record DOI as the exact public artifact set for this corrected 1.3.3 publication. The GitHub tag is moved to the corrected release commit by owner decision; the release report records the tag object, target commit, asset checksums, Zenodo record URL, DOI, and supersession state for prior defective records.",
                "",
                "Readers comparing versions should not infer that every broad future research ambition is completed in 1.3.3. The release distinguishes the bounded external-review model core from the continuing full science program. This distinction is explicit so the artifact can be used confidently in conversations with scientists, clients, colleagues, and institutions without overstating what the evidence layer proves today.",
                "",
                "For practical use, this means the public record is suitable as a serious review and discussion baseline: it contains the long-form monograph, compact article path, reproducibility companion, adversarial-review map, and replay package. It is not a substitute for the reader's own scientific judgment, but it is arranged so that judgment can be applied to the right artifacts in the right order.",
                "",
                "If the record is mirrored elsewhere, this guide should remain the first visible document. That ordering is part of the release-quality contract: public readers see the science first, then the supporting machine-readable materials.",
                "",
                journal_package_summary(),
            ]
        ),
        "master": "\n\n".join(
            [
                front,
                release_boundary(),
                claim_catalog(),
                theorem_catalog(include_excerpts=True),
                lean_evidence(),
                finite_model_evidence(max_rows=120),
                empirical_evidence(include_lane_replays=True),
                comparator_and_novelty(),
                phenomenon_coverage(max_rows=80),
                appendices_and_model(),
                journal_package_summary(),
            ]
        ),
        "journal": "\n\n".join(
            [
                front,
                release_boundary(),
                claim_catalog(),
                theorem_catalog(max_rows=10, include_excerpts=False),
                empirical_evidence(include_lane_replays=False),
                comparator_and_novelty(),
                phenomenon_coverage(max_rows=20),
            ]
        ),
        "methods": "\n\n".join(
            [
                front,
                release_boundary(),
                lean_evidence(),
                finite_model_evidence(max_rows=140),
                empirical_evidence(include_lane_replays=True),
                journal_package_summary(),
            ]
        ),
        "reviewer": "\n\n".join(
            [
                front,
                release_boundary(),
                attack_matrix(max_rows=230),
                comparator_and_novelty(),
                phenomenon_coverage(max_rows=80),
                claim_catalog(),
                theorem_catalog(max_rows=16, include_excerpts=False),
                lean_evidence(),
                finite_model_evidence(max_rows=60),
                empirical_evidence(include_lane_replays=False),
                journal_package_summary(),
            ]
        ),
    }
    paths: dict[str, Path] = {}
    for key, body in docs.items():
        path = PUBLIC_SOURCES / PDF_SPECS[key]["source"]
        write_text_if_changed(path, body)
        paths[key] = path
    return paths


def build_pdf(source: Path, output: Path, title: str) -> dict[str, Any]:
    output.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "pandoc",
        str(source),
        "--from",
        "markdown-raw_tex",
        "--toc",
        "--number-sections",
        "--pdf-engine=xelatex",
        "--metadata",
        f"title={title}",
        "--metadata",
        "geometry:margin=0.9in",
        "-o",
        str(output),
    ]
    completed = subprocess.run(cmd, cwd=ROOT, text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=900)
    command = " ".join(cmd).replace(str(ROOT.resolve()), "<REPO_ROOT>")
    stdout_tail = completed.stdout[-2000:].replace(str(ROOT.resolve()), "<REPO_ROOT>")
    stderr_tail = completed.stderr[-4000:].replace(str(ROOT.resolve()), "<REPO_ROOT>")
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout_tail": stdout_tail,
        "stderr_tail": stderr_tail,
        "output": rel(output),
        "ok": completed.returncode == 0 and output.exists() and output.stat().st_size > 0,
    }


def pdf_text(path: Path, *, persist_audit_text: bool = True) -> tuple[str, int]:
    if persist_audit_text:
        txt_path = EDITORIAL / "pdf_text_audit" / f"{path.stem}.txt"
        return _pdf_text_to_path(path, txt_path)

    with tempfile.TemporaryDirectory(prefix="oc133_pdf_text_audit_") as tmp_dir:
        txt_path = Path(tmp_dir) / f"{path.stem}.txt"
        return _pdf_text_to_path(path, txt_path)


def _pdf_text_to_path(path: Path, txt_path: Path) -> tuple[str, int]:
    txt_path.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        ["pdftotext", str(path), str(txt_path)],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=180,
    )
    if completed.returncode != 0:
        return completed.stderr, 0
    text = read_text(txt_path)
    try:
        from pypdf import PdfReader  # type: ignore

        pages = len(PdfReader(str(path)).pages)
    except Exception:
        pages = 0
    return text, pages


def public_pdf_audit(*, persist_audit_text: bool = True) -> dict[str, Any]:
    rows = []
    failures = []
    for key, spec in PDF_SPECS.items():
        path = ARTIFACTS / spec["filename"]
        text, pages = pdf_text(path, persist_audit_text=persist_audit_text) if path.exists() else ("", 0)
        forbidden_hits = [m.group(0) for m in PUBLIC_FORBIDDEN_RE.finditer(text)]
        overclaim_hits = [m.group(0) for m in ABSOLUTE_OVERCLAIM_RE.finditer(text)]
        row = {
            "artifact": rel(path),
            "exists": path.exists(),
            "size_bytes": path.stat().st_size if path.exists() else 0,
            "pages": pages,
            "text_chars": len(text),
            "min_chars": spec["min_chars"],
            "min_pages": spec["min_pages"],
            "version_present": VERSION in text,
            "toc_present": "Contents" in text or "Table of Contents" in text,
            "dedication_present": "Dedicated to my dear wife Maria" in text if key == "master" else True,
            "science_delta_present": "T133-K0-RES" in text and "target-blind" in text if key == "master" else True,
            "forbidden_hit_total": len(forbidden_hits),
            "overclaim_hit_total": len(overclaim_hits),
            "forbidden_hits": forbidden_hits[:20],
            "overclaim_hits": overclaim_hits[:20],
        }
        ok = (
            row["exists"]
            and row["size_bytes"] >= int(spec.get("min_size", 50000))
            and row["pages"] >= spec["min_pages"]
            and row["text_chars"] >= spec["min_chars"]
            and row["version_present"]
            and row["toc_present"]
            and row["dedication_present"]
            and row["science_delta_present"]
            and row["forbidden_hit_total"] == 0
            and row["overclaim_hit_total"] == 0
        )
        row["state"] = "PASS" if ok else "FAIL"
        if not ok:
            failures.append(row)
        rows.append(row)
    return {"state": "PASS" if not failures else "FAIL", "rows": rows, "failure_total": len(failures)}


def public_assets() -> list[dict[str, str]]:
    base = []
    for key, spec in PDF_SPECS.items():
        base.append(
            {
                "path": f"releases/{RELEASE_ID}/artifacts/{spec['filename']}",
                "label": spec["title"].replace("OC Core 1.3.3 ", ""),
                "description": spec["description"],
                "role": "PUBLIC_SCIENTIFIC_DOCUMENT",
            }
        )
    base.extend(
        [
            {
                "path": f"releases/{RELEASE_ID}/artifacts/{PUBLIC_ZIP_NAME}",
                "label": "Public reproducibility package",
                "description": "Canonical public GitHub/Zenodo reproducibility package.",
                "role": "PUBLIC_REPRODUCIBILITY_PACKAGE",
            },
            {"path": "manifest.json", "label": "Public manifest", "description": "Machine-readable public release manifest.", "role": "PUBLIC_METADATA"},
            {"path": "checksums.txt", "label": "Checksums", "description": "SHA-256 checksums for public release assets.", "role": "PUBLIC_METADATA"},
            {"path": "CITATION.cff", "label": "Citation metadata", "description": "Citation metadata for OC Core 1.3.3.", "role": "PUBLIC_METADATA"},
            {"path": ".codemeta.json", "label": "CodeMeta metadata", "description": "CodeMeta metadata for OC Core 1.3.3.", "role": "PUBLIC_METADATA"},
            {"path": "ro-crate-metadata.jsonld", "label": "RO-Crate metadata", "description": "RO-Crate metadata for OC Core 1.3.3.", "role": "PUBLIC_METADATA"},
            {"path": f"releases/{RELEASE_ID}/RELEASE_NOTES.md", "label": "Release notes", "description": "Human-readable release notes.", "role": "PUBLIC_NOTES"},
            {"path": f"releases/{RELEASE_ID}/CHANGELOG.md", "label": "Changelog", "description": "Release changelog summary.", "role": "PUBLIC_NOTES"},
        ]
    )
    return base


def zenodo_assets() -> list[dict[str, str]]:
    """Curated Zenodo public surface: readable PDFs plus the archival public ZIP.

    GitHub can carry standalone metadata files because its release page renders a
    controlled Markdown body. Zenodo previews deposited files directly, so raw
    JSON/Markdown/checksum files are kept inside the ZIP and on GitHub rather
    than uploaded as independent Zenodo landing-surface files.
    """
    return [
        row
        for row in public_assets()
        if row["role"] in {"PUBLIC_SCIENTIFIC_DOCUMENT", "PUBLIC_REPRODUCIBILITY_PACKAGE"}
    ]


def materialize_public_evidence_summaries() -> list[Path]:
    PUBLIC_EVIDENCE.mkdir(parents=True, exist_ok=True)
    refs = [
        "formal/lean/OC133V12.lean",
        "proofs/FINITE_MODEL_OUTPUT_ATTESTATION_1_3_3.json",
        "docs/OC_1_3_3_PHENOMENON_COVERAGE_MATRIX.json",
        "validation/target_blind/OC133_TARGET_BLIND_PREDICTION_TABLE.json",
        "reports/OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.json",
        "reviews/oc133_llm_cerberus/OC133_LLM_CERBERUS_SUMMARY.json",
        "simulations/results/OC_CORE_1_3_3_SIMULATION_RESULTS_latest.json",
        "reports/OC_CORE_1_3_3_ADVERSARIAL_SIMULATION_REPORT.json",
        "reports/OC_CORE_1_3_3_COUNTEREXAMPLE_REPORT.json",
    ]
    out_paths = []
    for ref in refs:
        src = ROOT / ref
        if not src.exists():
            continue
        dst = PUBLIC_EVIDENCE / ref.replace("/", "__").replace("\\", "__")
        if src.suffix.lower() in {".json", ".jsonld"}:
            write_json_if_changed(dst, sanitize_public_json(read_json(src, {})))
        elif src.suffix.lower() in TEXT_SUFFIXES:
            write_text_if_changed(dst, clean_public_text(read_text(src)))
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            if not dst.exists() or dst.read_bytes() != src.read_bytes():
                dst.write_bytes(src.read_bytes())
        out_paths.append(dst)

    public_theorems = sanitize_public_json(read_json(ROOT / "proofs" / "THEOREM_REGISTRY_1_3_3.json", {}))
    public_theorems.pop("release_promotion_allowed", None)
    for row in public_theorems.get("rows", []):
        for key, value in list(row.items()):
            if isinstance(value, str):
                row[key] = clean_public_text(value)
    theorem_path = PUBLIC_EVIDENCE / "THEOREM_REGISTRY_PUBLIC_1_3_3.json"
    write_json_if_changed(theorem_path, public_theorems)
    out_paths.append(theorem_path)

    public_claims = sanitize_public_json(read_json(ROOT / "claims" / "CLAIM_LEDGER_1_3_3.json", {}))
    public_claims["release_promotion_allowed"] = True
    public_claims["publication_boundary"] = "Public GitHub and Zenodo release approved; journal submission remains separately gated."
    public_claim_rows = []
    for row in public_claims.get("rows", []):
        combined = json.dumps(row, ensure_ascii=False)
        if re.search(r"\bNOSEND\b|NO[-_ ]?SEND|global_no_send_lock|publish_allowed\s*=\s*false|owner_approved\s*=\s*false", combined, re.I):
            continue
        row["release_promotion_allowed"] = bool(row.get("scientific_promotion_allowed"))
        for key, value in list(row.items()):
            if isinstance(value, str):
                row[key] = clean_public_text(value)
        public_claim_rows.append(row)
    public_claims["rows"] = public_claim_rows
    claims_path = PUBLIC_EVIDENCE / "CLAIM_LEDGER_PUBLIC_1_3_3.json"
    write_json_if_changed(claims_path, public_claims)
    out_paths.append(claims_path)

    proof_dir = PUBLIC_EVIDENCE / "proof_sheets_public"
    proof_dir.mkdir(parents=True, exist_ok=True)
    for src in sorted((ROOT / "proofs" / "proof_sheets").glob("T133-*.md")):
        dst = proof_dir / src.name
        write_text_if_changed(dst, clean_public_text(read_text(src)))
        out_paths.append(dst)
    return out_paths


def build_public_zip() -> dict[str, Any]:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    included: list[Path] = []
    for key, spec in PDF_SPECS.items():
        included.append(ARTIFACTS / spec["filename"])
    included.extend(PUBLIC_SOURCES.glob("*.md"))
    included.extend(PUBLIC_EVIDENCE.rglob("*"))
    for ref in [
        "CITATION.cff",
        ".codemeta.json",
        f"releases/{RELEASE_ID}/RELEASE_NOTES.md",
        f"releases/{RELEASE_ID}/CHANGELOG.md",
        f"releases/{RELEASE_ID}/editorial/SCIENCE_MONOLITH_CORPUS_LEDGER_1_3_3_latest.json",
        f"releases/{RELEASE_ID}/editorial/SCIENCE_MONOLITH_AUDIT_1_3_3_latest.json",
        f"releases/{RELEASE_ID}/editorial/SCIENCE_MONOLITH_BUILD_1_3_3_latest.json",
        f"releases/{RELEASE_ID}/editorial/SCIENCE_MONOLITH_BUILD_1_3_3_latest.md",
    ]:
        path = ROOT / ref
        if path.exists():
            included.append(path)
    for path in (RELEASE_ROOT / "submission_packages").rglob("*"):
        if path.is_file():
            included.append(path)
    included = sorted({path.resolve(): path for path in included if path.exists() and path.is_file()}.values(), key=lambda p: rel(p))
    tmp = PUBLIC_ZIP.with_suffix(".zip.tmp")
    with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in included:
            info = zipfile.ZipInfo(rel(path), date_time=(2026, 5, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, text_bytes_for_zip(path))
    data = tmp.read_bytes()
    if not PUBLIC_ZIP.exists() or PUBLIC_ZIP.read_bytes() != data:
        PUBLIC_ZIP.write_bytes(data)
    tmp.unlink(missing_ok=True)
    return {
        "path": rel(PUBLIC_ZIP),
        "sha256": sha256_file(PUBLIC_ZIP),
        "size_bytes": PUBLIC_ZIP.stat().st_size,
        "member_total": len(zipfile.ZipFile(PUBLIC_ZIP).namelist()),
    }


def write_public_metadata(doi: str | None, zenodo_record_url: str | None, github_release_url: str | None) -> dict[str, Any]:
    assets = public_assets()
    asset_rows = []
    for row in assets:
        path = ROOT / row["path"]
        asset_rows.append(
            {
                **row,
                "filename": path.name,
                "exists": path.is_file(),
                "size_bytes": path.stat().st_size if path.is_file() else 0,
                "sha256": sha256_file(path) if path.is_file() else None,
            }
        )
    github_body = release_body(asset_rows, doi, zenodo_record_url, github_release_url)
    zenodo_description = zenodo_html_description(asset_rows, doi, zenodo_record_url, github_release_url)
    manifest = {
        "schema_id": "OC133_PUBLIC_RELEASE_MANIFEST_v2",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "tag": TAG,
        "manifest_kind": "PUBLIC_GITHUB_ZENODO_RELEASE",
        "owner_approved": True,
        "publish_allowed": True,
        "github_release_allowed": True,
        "zenodo_deposit_allowed": True,
        "doi_minting_allowed": True,
        "journal_submissions_allowed": False,
        "software_heritage_deposit_allowed": False,
        "github_release_url": github_release_url,
        "zenodo_record_url": zenodo_record_url,
        "zenodo_doi": doi,
        "concept_doi": "10.5281/zenodo.17899134",
        "github_release_body": github_body,
        "zenodo_html_description": zenodo_description,
        "files": asset_rows,
    }
    write_json_if_changed(ROOT / "manifest.json", manifest)
    checksum_lines = [f"{row['sha256']}  {row['path']}" for row in asset_rows if row.get("sha256")]
    write_text_if_changed(ROOT / "checksums.txt", "\n".join(checksum_lines))
    citation = f"""cff-version: 1.2.0
message: "If you use OC Core 1.3.3, cite the GitHub release and the Zenodo DOI recorded here."
type: software
title: "Ontology of Continua - Core"
version: "{VERSION}"
authors:
  - family-names: "Yashin"
    given-names: "Alexander"
    orcid: "https://orcid.org/0009-0008-6166-0914"
repository-code: "https://github.com/alexanderyashin/ontology-of-continua-core-main"
url: "{github_release_url or 'https://github.com/alexanderyashin/ontology-of-continua-core-main/releases/tag/v1.3.3'}"
license: "CC-BY-4.0"
date-released: "2026-05-01"
identifiers:
  - type: doi
    value: "{doi or '10.5281/zenodo.pending'}"
keywords:
  - ontology
  - continua
  - systems theory
  - formal methods
  - reproducible research
abstract: >
  OC Core 1.3.3 is a bounded external-review scientific release of the
  Ontology of Continua core model. It includes typed foundations, theorem and
  proof evidence, a Lean-checked subset, finite-model semantics, target-blind
  numeric reconstruction evidence, comparator positioning, adversarial-review
  closure, and owner-review journal packets.
"""
    write_text_if_changed(ROOT / "CITATION.cff", citation)
    codemeta = {
        "@context": "https://doi.org/10.5063/schema/codemeta-2.0",
        "@type": "SoftwareSourceCode",
        "name": "Ontology of Continua - Core",
        "version": VERSION,
        "codeRepository": "https://github.com/alexanderyashin/ontology-of-continua-core-main",
        "license": "https://spdx.org/licenses/CC-BY-4.0",
        "datePublished": "2026-05-01",
        "identifier": doi or "10.5281/zenodo.pending",
        "description": "OC Core 1.3.3 bounded external-review scientific release with typed foundations, proof/evidence ledgers, reproducibility package, and journal owner-review packets.",
        "author": [{"@type": "Person", "givenName": "Alexander", "familyName": "Yashin"}],
    }
    write_json_if_changed(ROOT / ".codemeta.json", codemeta)
    ro_crate = {
        "@context": "https://w3id.org/ro/crate/1.1/context",
        "@graph": [
            {
                "@id": "./",
                "@type": "Dataset",
                "name": f"Ontology of Continua Core {VERSION}",
                "version": VERSION,
                "datePublished": "2026-05-01",
                "identifier": doi or "10.5281/zenodo.pending",
                "license": "https://spdx.org/licenses/CC-BY-4.0",
                "hasPart": [{"@id": row["path"]} for row in asset_rows],
            },
            *[
                {
                    "@id": row["path"],
                    "@type": "File",
                    "name": row["filename"],
                    "contentSize": row["size_bytes"],
                    "sha256": row["sha256"],
                    "description": row["description"],
                }
                for row in asset_rows
            ],
        ],
    }
    write_json_if_changed(ROOT / "ro-crate-metadata.jsonld", ro_crate)
    notes = f"""# OC Core v{VERSION} Release Notes

OC Core v{VERSION} is the corrected public GitHub and Zenodo release for the Ontology of Continua core line.

## Highlights

- Substantive public PDFs: master monograph, journal core, methods companion, and reviewer attack/response map.
- Typed OC foundation, bounded theorem claims, proof sheets, Lean subset, finite-model semantics, and reproducibility evidence.
- Target-blind numeric reconstruction evidence for physics, chemistry, biology, systems, and mathematics.
- Comparator and novelty positioning register, phenomenon coverage matrix, and adversarial review closure.
- Eight journal packets are included for owner review; journal submission is not performed by this release.

## Scope Boundary

This release is a bounded scientific external-review release. It does not promote universal full-science completion or universal superiority over all modern science.

## Citation

Zenodo DOI: `{doi or 'assigned by corrected Zenodo record metadata'}`
"""
    write_text_if_changed(RELEASE_ROOT / "RELEASE_NOTES.md", notes)
    changelog = f"""# OC Core v{VERSION} Changelog

## Corrected public release payload

- Replaced route-sheet PDFs with substantive scientific PDFs generated from the proof, formal, validation, comparator, and review corpus.
- Replaced the primary release package with `{PUBLIC_ZIP_NAME}`.
- Rebuilt public manifest, checksums, citation, CodeMeta, RO-Crate, GitHub release metadata, and Zenodo metadata.
- Added reusable public payload suitability gates so future publication attempts fail before upload if public assets are missing, too small, contradictory, stale, or inherited from an owner-review package.
"""
    write_text_if_changed(RELEASE_ROOT / "CHANGELOG.md", changelog)
    readme = f"""# Ontology of Continua / OC Core {VERSION}

OC Core {VERSION} is a bounded public external-review release of the Ontology of Continua core model.

Public release assets include substantive scientific PDFs, a public reproducibility package, metadata, checksums, proof/evidence summaries, target-blind numeric evidence, and journal owner-review packets.

Publication scope:
- GitHub Release: owner-approved for v{VERSION}
- Zenodo production record: owner-approved for v{VERSION}
- Journal submission: requires separate approval
- Email campaign and Software Heritage: require separate approval

Zenodo DOI: `{doi or 'assigned by corrected Zenodo record metadata'}`
GitHub Release: `{github_release_url or 'https://github.com/alexanderyashin/ontology-of-continua-core-main/releases/tag/v1.3.3'}`
"""
    write_text_if_changed(RELEASE_ROOT / "README.md", readme)
    write_text_if_changed(ROOT / "README.md", readme)
    zenodo = {
        "title": f"Ontology of Continua Core v{VERSION}",
        "upload_type": "publication",
        "publication_type": "other",
        "description": zenodo_description,
        "creators": [{"name": "Yashin, Alexander", "affiliation": "Logion / Estra", "orcid": "0009-0008-6166-0914"}],
        "license": "cc-by-4.0",
        "access_right": "open",
        "publication_date": "2026-05-01",
        "keywords": [
            "Ontology of Continua",
            "OC Core",
            "systems theory",
            "formal methods",
            "reproducible research",
            "mathematical modeling",
            "scientific release engineering",
            "cross-domain modeling",
            "proof governance",
            "target-blind validation",
        ],
        "version": VERSION,
        "related_identifiers": [
            {"identifier": "10.5281/zenodo.17899134", "relation": "isVersionOf", "scheme": "doi"},
            {"identifier": doi, "relation": "isIdenticalTo", "scheme": "doi"} if doi else None,
        ],
    }
    zenodo["related_identifiers"] = [row for row in zenodo["related_identifiers"] if row]
    write_json_if_changed(ROOT / ".zenodo.json", zenodo)
    return manifest


def zenodo_html_description(
    asset_rows: list[dict[str, Any]],
    doi: str | None,
    zenodo_record_url: str | None,
    github_release_url: str | None,
) -> str:
    version_doi = doi or "pending"
    doi_html = (
        f'<a href="{html.escape("https://doi.org/" + version_doi, quote=True)}">{html.escape(version_doi)}</a>'
        if doi
        else "assigned by Zenodo publication metadata"
    )
    record_html = (
        f'<a href="{html.escape(zenodo_record_url, quote=True)}">Zenodo record</a>'
        if zenodo_record_url
        else "Zenodo record assigned during publication"
    )
    github_url = github_release_url or "https://github.com/alexanderyashin/ontology-of-continua-core-main/releases/tag/v1.3.3"
    github_html = f'<a href="{html.escape(github_url, quote=True)}">GitHub release</a>'
    labels = {row.get("filename"): row.get("label") for row in asset_rows}
    reading_order = [
        ("OC_CORE_1_3_3_MASTER_MONOGRAPH_EN.pdf", labels.get("OC_CORE_1_3_3_MASTER_MONOGRAPH_EN.pdf") or "Master monograph"),
        ("OC_CORE_1_3_3_JOURNAL_CORE_EN.pdf", labels.get("OC_CORE_1_3_3_JOURNAL_CORE_EN.pdf") or "Journal core article"),
        (
            "OC_CORE_1_3_3_METHODS_AND_REPRODUCIBILITY_COMPANION_EN.pdf",
            labels.get("OC_CORE_1_3_3_METHODS_AND_REPRODUCIBILITY_COMPANION_EN.pdf")
            or "Methods and reproducibility companion",
        ),
        (
            "OC_CORE_1_3_3_REVIEWER_ATTACK_AND_RESPONSE_MAP_EN.pdf",
            labels.get("OC_CORE_1_3_3_REVIEWER_ATTACK_AND_RESPONSE_MAP_EN.pdf") or "Reviewer attack and response map",
        ),
        ("oc_core_1_3_3_public_release.zip", "Public reproducibility package"),
    ]
    reading = "".join(
        f"<li><strong>{html.escape(str(label))}</strong> - {html.escape(filename)}</li>"
        for filename, label in reading_order
    )
    return (
        f"<p><strong>Ontology of Continua Core v{VERSION}</strong> is a bounded external-review scientific release "
        "of the OC core model. It provides typed foundations, proof/evidence ledgers, Lean and finite-model evidence, "
        "target-blind validation summaries, reproducibility material, and adversarial-review closure artifacts.</p>"
        "<p>The release promotes only model-core claims supported by the included evidence. Broader full-science "
        "completion and universal modern-science-superiority obligations remain outside this release surface.</p>"
        "<h2>Recommended reading order</h2>"
        f"<ol>{reading}</ol>"
        "<h2>Release contents</h2>"
        "<ul><li>Four substantive English PDF documents.</li><li>One public reproducibility package with proof, "
        "validation, review, metadata, checksums, and journal owner-review materials.</li><li>Checksums are provided "
        "in checksums.txt.</li></ul>"
        "<h2>Citation and links</h2>"
        f"<ul><li>Version DOI: {doi_html}</li><li>Concept DOI: "
        '<a href="https://doi.org/10.5281/zenodo.17899134">10.5281/zenodo.17899134</a></li>'
        f"<li>{record_html}</li><li>{github_html}</li></ul>"
        "<h2>Governance boundary</h2>"
        "<p>GitHub Release and Zenodo publication are approved for v1.3.3. Journal packages are included as "
        "owner-review material only; journal submission, email campaigns, and Software Heritage deposit require "
        "separate approval.</p>"
    )


def release_body(asset_rows: list[dict[str, Any]], doi: str | None, zenodo_record_url: str | None, github_release_url: str | None) -> str:
    download_base = "https://github.com/alexanderyashin/ontology-of-continua-core-main/releases/download/v1.3.3"
    primary = [
        ("OC_CORE_1_3_3_MASTER_MONOGRAPH_EN.pdf", "Master monograph", "Canonical long-form scientific reference."),
        ("OC_CORE_1_3_3_JOURNAL_CORE_EN.pdf", "Journal core article", "Compact article-style entry point."),
        (
            "OC_CORE_1_3_3_METHODS_AND_REPRODUCIBILITY_COMPANION_EN.pdf",
            "Methods and reproducibility companion",
            "Reproducibility, validation, and audit navigation.",
        ),
        (
            "OC_CORE_1_3_3_REVIEWER_ATTACK_AND_RESPONSE_MAP_EN.pdf",
            "Reviewer attack and response map",
            "Adversarial objections, boundaries, and responses.",
        ),
        ("oc_core_1_3_3_public_release.zip", "Public reproducibility package", "Proof/evidence corpus and journal owner-review material."),
        ("checksums.txt", "Checksums", "SHA-256 integrity list for all public assets."),
    ]
    asset_lines = "\n".join(
        f"| [{filename}]({download_base}/{filename}) | {label} | {description} |"
        for filename, label, description in primary
    )
    return f"""# Ontology of Continua Core v{VERSION}

Bounded external-review scientific release with typed foundations, proof/evidence ledgers, reproducibility package, and journal owner-review packets.

## Table of Contents

1. Scope
2. Core scientific documents
3. Public assets and checksums
4. Journal package boundary
5. Citation and DOI
6. Checksums

## Scope

OC Core {VERSION} is a public GitHub and Zenodo release. The promoted claims are bounded by the included formal, finite-model, validation, comparator, and adversarial-review artifacts. Broader full-science completion and universal modern-science superiority remain outside this release surface.

## Public Assets

| Asset | Role | How to use it |
| --- | --- | --- |
{asset_lines}

Checksums for the complete public asset set are in [`checksums.txt`]({download_base}/checksums.txt). Machine-readable metadata is provided as `manifest.json`, `CITATION.cff`, `default.codemeta.json`, and `ro-crate-metadata.jsonld`.

## Journal Packages

The eight journal packets are included for owner review. They are not submitted by this release action and require separate approval before outbound use.

## Zenodo

DOI: {doi or 'assigned by the corrected Zenodo record metadata'}

Record: {zenodo_record_url or 'assigned by the corrected publication pass'}

Concept DOI: 10.5281/zenodo.17899134

## GitHub

Release: {github_release_url or 'https://github.com/alexanderyashin/ontology-of-continua-core-main/releases/tag/v1.3.3'}

## Keywords

Ontology of Continua, OC Core, systems theory, formal methods, reproducible research, mathematical modeling, proof governance, target-blind validation.

#OntologyOfContinua #OCCore #SystemsTheory #FormalMethods #ReproducibleResearch #ScientificRelease #ProofGovernance
"""


def write_profile() -> None:
    payload = {
        "schema_id": "LOGION_PUBLIC_RELEASE_PROFILE_v2",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "tag": TAG,
        "branch": "release/oc-core-1.3.3-total-scientific-closure",
        "repository": "alexanderyashin/ontology-of-continua-core-main",
        "title": "Ontology of Continua Core",
        "subtitle": "Bounded external-review scientific release with typed foundations, proof/evidence ledgers, reproducibility package, and journal owner-review packets",
        "release_state": "OC_CORE_1_3_3_PUBLIC_GITHUB_ZENODO_RELEASE",
        "expected_gate_pass_total": 71,
        "expected_package_sha256": "",
        "previous_zenodo_record_id": "19956854",
        "previous_zenodo_doi": "10.5281/zenodo.19956854",
        "concept_doi": "10.5281/zenodo.17899134",
        "creators": [{"name": "Yashin, Alexander", "affiliation": "Logion / Estra", "orcid": "0009-0008-6166-0914"}],
        "license": "cc-by-4.0",
        "keywords": [
            "Ontology of Continua",
            "OC Core",
            "systems theory",
            "formal methods",
            "reproducible research",
            "mathematical modeling",
            "scientific release engineering",
            "cross-domain modeling",
            "proof governance",
            "target-blind validation",
        ],
        "github_topics": [
            "ontology-of-continua",
            "oc-core",
            "systems-theory",
            "formal-methods",
            "reproducible-research",
            "scientific-release",
            "proof-governance",
        ],
        "hashtags": [
            "#OntologyOfContinua",
            "#OCCore",
            "#SystemsTheory",
            "#FormalMethods",
            "#ReproducibleResearch",
            "#ScientificRelease",
            "#ProofGovernance",
        ],
        "assets": [
            {key: row[key] for key in ["path", "label", "description"]}
            for row in public_assets()
        ],
        "zenodo_assets": [
            {key: row[key] for key in ["path", "label", "description"]}
            for row in zenodo_assets()
        ],
        "journal_submissions_allowed": False,
        "software_heritage_allowed": False,
    }
    write_json_if_changed(EDITORIAL / "PUBLIC_RELEASE_PROFILE.json", payload)


def public_surface_scan(paths: list[Path]) -> list[dict[str, Any]]:
    hits = []
    for path in paths:
        if not path.exists() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        body = read_text(path)
        for regex, kind in [(PUBLIC_FORBIDDEN_RE, "public_no_send_contradiction"), (ABSOLUTE_OVERCLAIM_RE, "absolute_overclaim")]:
            for match in regex.finditer(body):
                hits.append(
                    {
                        "path": rel(path),
                        "kind": kind,
                        "match": match.group(0),
                        "context": body[max(0, match.start() - 80) : match.end() + 120].replace("\n", " ")[:260],
                    }
                )
    return hits


def zip_public_scan() -> dict[str, Any]:
    forbidden = []
    if not PUBLIC_ZIP.exists():
        return {"state": "FAIL", "failure_total": 1, "failures": [{"issue": "missing_public_zip"}]}
    with zipfile.ZipFile(PUBLIC_ZIP) as zf:
        for name in zf.namelist():
            lowered = name.lower()
            if "oc_core_1_3_2" in lowered or "1_3_2" in lowered:
                forbidden.append({"member": name, "issue": "stale_132_member"})
            if "no_send_release.zip" in lowered:
                forbidden.append({"member": name, "issue": "published_review_zip_member"})
            if name.endswith("/"):
                continue
            suffix = Path(name).suffix.lower()
            if suffix in TEXT_SUFFIXES:
                text = zf.read(name).decode("utf-8", errors="ignore")
                hit = PUBLIC_FORBIDDEN_RE.search(text)
                if hit:
                    forbidden.append({"member": name, "issue": "public_forbidden_text", "match": hit.group(0)})
    return {"state": "PASS" if not forbidden else "FAIL", "failure_total": len(forbidden), "failures": forbidden[:100]}


def audit_public_payload(*, write: bool = True) -> dict[str, Any]:
    asset_paths = [ROOT / row["path"] for row in public_assets()]
    pdf_audit = public_pdf_audit(persist_audit_text=write)
    monolith_audit = science_monolith.audit_monolith(ROOT)
    scan_hits = public_surface_scan(asset_paths + list(PUBLIC_SOURCES.glob("*.md")) + [ROOT / "README.md", ROOT / ".zenodo.json"])
    zip_scan = zip_public_scan()
    missing_assets = [rel(path) for path in asset_paths if not path.is_file()]
    primary_no_send_asset_names = [path.name for path in asset_paths if "no_send" in path.name.lower()]
    failures = []
    if pdf_audit["state"] != "PASS":
        failures.append("pdf_audit_failed")
    if monolith_audit.get("state") != "PASS":
        failures.append("science_monolith_audit_failed")
    if scan_hits:
        failures.append("public_surface_forbidden_hits")
    if zip_scan["state"] != "PASS":
        failures.append("zip_public_scan_failed")
    if missing_assets:
        failures.append("missing_public_assets")
    if primary_no_send_asset_names:
        failures.append("primary_public_asset_name_contains_no_send")
    payload = {
        "schema_id": "OC133_PUBLIC_PAYLOAD_SUITABILITY_AUDIT_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "state": "PASS" if not failures else "FAIL",
        "failure_total": len(failures),
        "failures": failures,
        "pdf_audit": pdf_audit,
        "science_monolith_audit": monolith_audit,
        "public_surface_forbidden_hit_total": len(scan_hits),
        "public_surface_forbidden_hits": scan_hits[:100],
        "zip_scan": zip_scan,
        "missing_assets": missing_assets,
        "primary_no_send_asset_names": primary_no_send_asset_names,
        "public_zip": {
            "path": rel(PUBLIC_ZIP) if PUBLIC_ZIP.exists() else rel(PUBLIC_ZIP),
            "exists": PUBLIC_ZIP.exists(),
            "sha256": sha256_file(PUBLIC_ZIP) if PUBLIC_ZIP.exists() else None,
            "size_bytes": PUBLIC_ZIP.stat().st_size if PUBLIC_ZIP.exists() else 0,
        },
    }
    if not write:
        return payload

    write_json_if_changed(EDITORIAL / f"PUBLIC_PAYLOAD_SUITABILITY_{VERSION}_latest.json", payload)
    lines = [
        f"# OC Core {VERSION} Public Payload Suitability",
        "",
        f"State: `{payload['state']}`",
        f"Failures: `{payload['failure_total']}`",
        f"Public ZIP: `{payload['public_zip']['path']}`",
        f"Public ZIP SHA-256: `{payload['public_zip']['sha256']}`",
        "",
        "| PDF | State | Pages | Text chars | Size |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for row in pdf_audit["rows"]:
        lines.append(f"| `{Path(row['artifact']).name}` | `{row['state']}` | {row['pages']} | {row['text_chars']} | {row['size_bytes']} |")
    write_text_if_changed(EDITORIAL / f"PUBLIC_PAYLOAD_SUITABILITY_{VERSION}_latest.md", "\n".join(lines))
    return payload


def sync_finite_publication_controls() -> dict[str, Any]:
    inputs_path = ROOT / "proofs" / "finite_model_checks" / "OC133_FINITE_MODEL_INPUTS.json"
    if not inputs_path.exists():
        return {"state": "SKIP", "reason": "missing finite model inputs"}
    payload = read_json(inputs_path, {})
    rows = payload.get("rows", [])
    changed_rows: list[str] = []
    for row in rows if isinstance(rows, list) else []:
        model = row.get("model")
        if not isinstance(model, dict):
            continue
        manifest_ref = model.get("manifest_ref")
        approval_ref = model.get("approval_ref")
        if manifest_ref and (ROOT / str(manifest_ref)).is_file():
            current = sha256_source_ref(ROOT / str(manifest_ref))
            if model.get("manifest_sha256") != current:
                model["manifest_sha256"] = current
                changed_rows.append(str(row.get("case_id")))
        if approval_ref and (ROOT / str(approval_ref)).is_file():
            current = sha256_source_ref(ROOT / str(approval_ref))
            if model.get("approval_sha256") != current:
                model["approval_sha256"] = current
                changed_rows.append(str(row.get("case_id")))
        if row.get("case_id") == "ADV-NOSEND-PUBLISH":
            manifest = read_json(ROOT / str(manifest_ref), {}) if manifest_ref else {}
            approval = read_json(ROOT / str(approval_ref), {}) if approval_ref else {}
            public_release_approved = (
                manifest.get("owner_approved") is True
                and manifest.get("github_release_allowed") is True
                and manifest.get("zenodo_deposit_allowed") is True
                and approval.get("owner_approved") is True
            )
            if public_release_approved:
                model["current_publication_artifact_policy"] = (
                    "OWNER_APPROVED_GITHUB_ZENODO_PUBLIC_RELEASE_WITH_JOURNAL_AND_SOFTWARE_HERITAGE_LOCKS"
                )
                if model.get("public_metadata_refs"):
                    model["public_metadata_refs"] = []
                    changed_rows.append(str(row.get("case_id")))
                row["failed_gate_predicates"] = [
                    "software_heritage_deposit_allowed",
                    "journal_submission_allowed",
                ]
                row["gate_vector"] = {
                    "owner_approved": True,
                    "publish_allowed": True,
                    "deposit_ready_metadata": True,
                    "public_record_present": True,
                    "global_no_send_lock=false": True,
                    "g57_attack_matrix_zero_critical_high": True,
                    "g58_reviewer_persona_suite_pass": True,
                    "g70_scientific_closure_verdict_pass": True,
                    "critical_open_total=0": True,
                    "high_open_total=0": True,
                    "github_release_allowed": True,
                    "zenodo_deposit_allowed": True,
                    "software_heritage_deposit_allowed": False,
                    "journal_submission_allowed": False,
                    "doi_minting_allowed": True,
                }
                changed_rows.append(str(row.get("case_id")))
    changed = write_json_if_changed(inputs_path, payload)
    return {
        "state": "UPDATED" if changed else "UNCHANGED",
        "changed": changed,
        "changed_rows": sorted(set(changed_rows)),
    }


def materialize(doi: str | None = None, zenodo_record_url: str | None = None, github_release_url: str | None = None, *, skip_pdf: bool = False) -> dict[str, Any]:
    PUBLIC_SOURCES.mkdir(parents=True, exist_ok=True)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    write_profile()
    sources = write_public_markdown(doi, zenodo_record_url)
    evidence_paths = materialize_public_evidence_summaries()
    finite_control_sync = sync_finite_publication_controls()
    build_rows = []
    if not skip_pdf:
        monolith_build = science_monolith.materialize_monolith(ROOT, doi=doi, zenodo_record_url=zenodo_record_url)
        build_rows.append(
            {
                "command": "release_machine.science_monolith.materialize_monolith",
                "returncode": 0 if monolith_build.get("state") == "PASS" else 1,
                "stdout_tail": "",
                "stderr_tail": "",
                "output": monolith_build.get("output_pdf"),
                "ok": monolith_build.get("state") == "PASS",
                "science_monolith": monolith_build.get("audit", {}),
            }
        )
        for key, source in sources.items():
            if key == "master":
                continue
            spec = PDF_SPECS[key]
            build_rows.append(build_pdf(source, ARTIFACTS / spec["filename"], spec["title"]))
        failures = [row for row in build_rows if not row["ok"]]
        if failures:
            payload = {"state": "FAIL", "build_rows": build_rows, "failures": failures}
            write_json_if_changed(EDITORIAL / f"PUBLIC_PAYLOAD_BUILD_{VERSION}_latest.json", payload)
            return payload
    write_public_metadata(doi, zenodo_record_url, github_release_url)
    zip_payload = build_public_zip()
    # The ZIP is itself a public asset, so metadata/checksums must bind the final ZIP hash.
    write_public_metadata(doi, zenodo_record_url, github_release_url)
    audit = audit_public_payload()
    payload = {
        "schema_id": "OC133_PUBLIC_RELEASE_PAYLOAD_BUILD_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "state": "PASS" if audit["state"] == "PASS" and all(row.get("ok", True) for row in build_rows) else "FAIL",
        "doi": doi,
        "zenodo_record_url": zenodo_record_url,
        "github_release_url": github_release_url,
        "source_paths": {key: rel(path) for key, path in sources.items()},
        "evidence_path_total": len(evidence_paths),
        "finite_publication_control_sync": finite_control_sync,
        "pdf_build_rows": build_rows,
        "public_zip": zip_payload,
        "suitability": audit,
    }
    write_json_if_changed(EDITORIAL / f"PUBLIC_PAYLOAD_BUILD_{VERSION}_latest.json", payload)
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build and audit the OC Core 1.3.3 corrected public release payload.")
    parser.add_argument("--doi", default=None)
    parser.add_argument("--zenodo-record-url", default=None)
    parser.add_argument("--github-release-url", default=None)
    parser.add_argument("--skip-pdf", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    payload = audit_public_payload() if args.check else materialize(
        args.doi,
        args.zenodo_record_url,
        args.github_release_url,
        skip_pdf=args.skip_pdf,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload.get("state") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
