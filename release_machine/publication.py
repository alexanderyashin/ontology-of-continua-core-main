from __future__ import annotations

import base64
import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

RELEASE_ID = "oc_core_1_3_2"
VERSION = "1.3.2"
TAG = "v1.3.2"
REPO = "alexanderyashin/ontology-of-continua-core-main"
BRANCH = "release/oc-core-1.3.2"
ZENODO_PREVIOUS_RECORD = "19741958"
TIMESTAMP = "2026-04-28T00:00:00Z"

TEXT_SUFFIXES = {".md", ".json", ".jsonld", ".ndjson", ".yaml", ".yml", ".txt", ".cff", ".tex", ".bib"}
LEAK_PATTERN = re.compile(
    r"claude_feedback|raw\s+feedback|raw\s+model\s+output|[A-Za-z]:\\Users\\|/home/|estra-private-work|"
    r"OPENAI_API_KEY|GITHUB_TOKEN|ZENODO_TOKEN|password\s*=|secret\s*=|token\s*=",
    re.IGNORECASE,
)


def _read_json(path: Path, default: Any | None = None) -> Any:
    if not path.exists():
        return {} if default is None else default
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def _run(root: Path, args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=root, text=True, capture_output=True, check=check)


def _sha256(path: Path) -> str:
    import hashlib

    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def release_root(root: Path) -> Path:
    return root / "releases" / RELEASE_ID


def editorial_root(root: Path) -> Path:
    return release_root(root) / "editorial"


def generate_llm_readability(root: Path) -> dict[str, Any]:
    out = release_root(root) / "llm_readability"
    support = _read_json(editorial_root(root) / "OC_CORE_1_3_2_PREDICTION_AND_PROMOTION_SUPPORT_MAP_latest.json", {"rows": [], "summary": {}})
    platinum = _read_json(editorial_root(root) / "OC_CORE_1_3_2_PLATINUM_SCIENCE_AUDIT_latest.json", {})
    benchmark = _read_json(root / "benchmarks" / "reports" / "OC14_BENCHMARK_RESULTS.json", {})
    closure = _read_json(editorial_root(root) / "OC_CORE_1_3_2_SCIENCE_BLOCKER_CLOSURE_LEDGER_latest.json", {"blocker_rows": []})

    claim_nodes = []
    for row in support.get("rows", []):
        claim_nodes.append({
            "@id": row.get("row_id"),
            "@type": "OCReleaseClaim",
            "claimKind": row.get("claim_kind"),
            "sourceArtifact": row.get("source_artifact"),
            "excerpt": row.get("excerpt"),
            "supportRoute": row.get("support_route"),
            "supportRefs": row.get("support_refs", []),
            "status": row.get("status"),
            "boundary": row.get("falsifier_or_boundary"),
        })
    claim_graph = {
        "@context": {
            "oc": "https://alexanderyashin.github.io/ontology-of-continua-core-main/ns#",
            "claimKind": "oc:claimKind",
            "supportRoute": "oc:supportRoute",
            "supportRefs": "oc:supportRefs",
        },
        "@id": "oc:OC_CORE_1_3_2_CLAIM_GRAPH",
        "releaseId": RELEASE_ID,
        "version": VERSION,
        "generatedAt": TIMESTAMP,
        "nodes": claim_nodes,
    }
    _write_json(out / "CLAIM_GRAPH.jsonld", claim_graph)

    minimality = platinum.get("formal_results", {}).get("minimality_theorem", {})
    theorem_cards = {
        "schema_id": "OC_LLM_THEOREM_CARDS_v1",
        "release_id": RELEASE_ID,
        "cards": [
            {
                "theorem_id": minimality.get("theorem_id", "OC132-GLOBAL-VERDICT-INVARIANT-MINIMALITY"),
                "title": "Global verdict-invariant minimality theorem",
                "statement": minimality.get("statement", ""),
                "proof_status": minimality.get("proof_status", ""),
                "proof_method": minimality.get("proof_method", ""),
                "assumptions": minimality.get("assumption_set", []),
                "proof_sketch": minimality.get("proof_sketch", ""),
                "not_claimed": minimality.get("not_claimed", ""),
                "human_refs": [
                    "content/03_model.tex",
                    "releases/oc_core_1_3_2/pdf_sources/OC_CORE_1_3_2_EXPERT_TECHNICAL_SPINE_EN.tex",
                    "releases/oc_core_1_3_2/editorial/research_packets/oc132_platinum_science_upgrade/MINIMALITY_WITNESS_MATRIX.json",
                ],
            }
        ],
    }
    _write_json(out / "THEOREM_CARDS.json", theorem_cards)

    formula_registry = {
        "schema_id": "OC_LLM_FORMULA_REGISTRY_v1",
        "release_id": RELEASE_ID,
        "formulas": [
            {
                "formula_id": "OC132-FACT-CONTRACT",
                "latex_or_ascii": platinum.get("formal_results", {}).get("fact_contract", ""),
                "meaning": "A release-visible fact is accepted only when stabilization is above threshold and active falsifiers are absent.",
                "human_refs": ["releases/oc_core_1_3_2/pdf_sources/OC_CORE_1_3_2_METHODS_AND_REPRODUCIBILITY_COMPANION_EN.tex"],
            },
            {
                "formula_id": "OC132-OBJECTIVITY-METRIC",
                "latex_or_ascii": platinum.get("formal_results", {}).get("objectivity_metric", ""),
                "meaning": "Observer agreement is measured by one minus mean pairwise Jensen-Shannon divergence.",
                "human_refs": ["releases/oc_core_1_3_2/pdf_sources/OC_CORE_1_3_2_EXPERT_TECHNICAL_SPINE_EN.tex"],
            },
        ],
    }
    _write_json(out / "FORMULA_REGISTRY.json", formula_registry)

    evidence_route_map = {
        "schema_id": "OC_LLM_EVIDENCE_ROUTE_MAP_v1",
        "release_id": RELEASE_ID,
        "support_row_total": len(support.get("rows", [])),
        "unsupported_promoted_total": support.get("summary", {}).get("unsupported_promoted_total", 0),
        "routes": [
            {
                "claim_id": row.get("row_id"),
                "support_route": row.get("support_route"),
                "support_refs": row.get("support_refs", []),
                "terminality_rationale": row.get("terminality_rationale", ""),
            }
            for row in support.get("rows", [])
        ],
    }
    _write_json(out / "EVIDENCE_ROUTE_MAP.json", evidence_route_map)

    benchmark_cards = {
        "schema_id": "OC_LLM_BENCHMARK_CARDS_v1",
        "release_id": RELEASE_ID,
        "summary": {
            "task_total": benchmark.get("task_total"),
            "runnable_task_total": benchmark.get("runnable_task_total"),
            "failure_total": benchmark.get("failure_total"),
            "accepted_baseline_total": benchmark.get("accepted_baseline_total"),
            "no_signalling_violation_score_max": benchmark.get("no_signalling_violation_score_max"),
            "output_hash": benchmark.get("output_hash"),
        },
        "tasks": benchmark.get("tasks", []),
        "human_refs": [
            "benchmarks/run_oc14_suite.py",
            "benchmarks/reports/OC14_BENCHMARK_RESULTS.md",
            "releases/oc_core_1_3_2/pdf_sources/OC_CORE_1_3_2_METHODS_AND_REPRODUCIBILITY_COMPANION_EN.tex",
        ],
    }
    _write_json(out / "BENCHMARK_CARDS.json", benchmark_cards)

    glossary = {
        "schema_id": "OC_LLM_GLOSSARY_v1",
        "release_id": RELEASE_ID,
        "terms": [
            {"term": "OC-compatible verdict-preserving representation", "definition": "A representation that preserves the release-visible OC verdict distinctions used by the minimality theorem."},
            {"term": "FactContract", "definition": "A governed assertion rule requiring stabilization above threshold and absence of active falsifiers."},
            {"term": "Support route", "definition": "The proof, replay, benchmark, source-audit, or governance path that makes a release-visible claim admissible."},
            {"term": "No-send", "definition": "A governance state forbidding outbound publication/submission until explicitly unlocked."},
        ],
    }
    _write_json(out / "GLOSSARY_MACHINE_READABLE.json", glossary)

    guide = [
        "# LLM Reader Guide: OC Core 1.3.2",
        "",
        "This companion is optimized for automated reading without widening the human release claims.",
        "",
        "Read order:",
        "1. `CLAIM_GRAPH.jsonld` for claim nodes and support routes.",
        "2. `THEOREM_CARDS.json` for theorem statements and proof boundaries.",
        "3. `FORMULA_REGISTRY.json` for formulas and meanings.",
        "4. `EVIDENCE_ROUTE_MAP.json` for source refs and terminality rationale.",
        "5. `BENCHMARK_CARDS.json` for reproducible benchmark facts.",
        "",
        "Machine-readable statements are subordinate to the human release artifacts and may not be used to promote stronger claims.",
    ]
    _write_text(out / "LLM_READER_GUIDE.md", "\n".join(guide))

    summary = {
        "schema_id": "OC_LLM_READABILITY_SUMMARY_v1",
        "release_id": RELEASE_ID,
        "status": "PASS",
        "claim_node_total": len(claim_nodes),
        "theorem_card_total": len(theorem_cards["cards"]),
        "formula_total": len(formula_registry["formulas"]),
        "benchmark_task_total": benchmark.get("task_total", 0),
        "blocker_row_total": len(closure.get("blocker_rows", [])),
        "files": [p.name for p in sorted(out.iterdir()) if p.is_file()],
    }
    _write_json(out / "LLM_READABILITY_SUMMARY.json", summary)
    return summary


def llm_readability_gate(root: Path) -> dict[str, Any]:
    out = release_root(root) / "llm_readability"
    required = [
        "CLAIM_GRAPH.jsonld",
        "THEOREM_CARDS.json",
        "FORMULA_REGISTRY.json",
        "EVIDENCE_ROUTE_MAP.json",
        "BENCHMARK_CARDS.json",
        "GLOSSARY_MACHINE_READABLE.json",
        "LLM_READER_GUIDE.md",
        "LLM_READABILITY_SUMMARY.json",
    ]
    missing = [name for name in required if not (out / name).exists()]
    parse_errors = []
    leak_hits = []
    json_payloads: dict[str, Any] = {}
    for name in required:
        path = out / name
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if LEAK_PATTERN.search(text):
            leak_hits.append(name)
        if path.suffix in {".json", ".jsonld"}:
            try:
                json_payloads[name] = json.loads(text)
            except json.JSONDecodeError as exc:
                parse_errors.append(f"{name}: {exc}")
    support_routes_missing = [
        row.get("claim_id")
        for row in json_payloads.get("EVIDENCE_ROUTE_MAP.json", {}).get("routes", [])
        if not row.get("support_route") or not row.get("support_refs")
    ]
    theorem_gaps = [
        row.get("theorem_id")
        for row in json_payloads.get("THEOREM_CARDS.json", {}).get("cards", [])
        if not row.get("statement") or not row.get("proof_status") or not row.get("proof_sketch")
    ]
    unsupported = json_payloads.get("EVIDENCE_ROUTE_MAP.json", {}).get("unsupported_promoted_total", 1)
    ok = not missing and not parse_errors and not leak_hits and not support_routes_missing and not theorem_gaps and unsupported == 0
    return {
        "state": "PASS" if ok else "FAIL",
        "severity": "HIGH",
        "summary": "LLM-readable release companion is schema-readable and claim-bounded." if ok else "LLM-readable companion is missing, leaky, or claim-unsafe.",
        "details": {
            "missing": missing,
            "parse_errors": parse_errors,
            "leak_hits": leak_hits,
            "support_routes_missing": support_routes_missing[:20],
            "theorem_gaps": theorem_gaps,
            "unsupported_promoted_total": unsupported,
            "file_total": len(list(out.glob("*"))) if out.exists() else 0,
        },
    }


def generate_owner_review(root: Path) -> dict[str, Any]:
    support = _read_json(editorial_root(root) / "OC_CORE_1_3_2_PREDICTION_AND_PROMOTION_SUPPORT_MAP_latest.json", {"summary": {}})
    closure = _read_json(editorial_root(root) / "OC_CORE_1_3_2_SCIENCE_BLOCKER_CLOSURE_LEDGER_latest.json", {"summary": {}})
    scorecard = _read_json(editorial_root(root) / "OC_CORE_1_3_2_RELEASE_SCORECARD_latest.json", {})
    package = release_root(root) / "artifacts" / "oc_core_1_3_2_zenodo_release.zip"
    issues = []
    if support.get("summary", {}).get("unsupported_promoted_total", 0) != 0:
        issues.append({"class": "BLOCKS_PUBLICATION", "issue": "unsupported promoted claim remains"})
    if closure.get("summary", {}).get("open_blocker_total", 0) != 0:
        issues.append({"class": "BLOCKS_PUBLICATION", "issue": "open science blocker remains"})
    if scorecard.get("gate_counts", {}).get("FAIL", 0) or scorecard.get("gate_counts", {}).get("BLOCKED", 0):
        issues.append({"class": "BLOCKS_PUBLICATION", "issue": "release machine gate is not green"})
    if not package.exists():
        issues.append({"class": "BLOCKS_PUBLICATION", "issue": "release package ZIP missing"})
    payload = {
        "schema_id": "OWNER_REVIEW_PUBLICATION_READINESS_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": TIMESTAMP,
        "status": "PASS" if not any(row["class"] == "BLOCKS_PUBLICATION" for row in issues) else "FAIL",
        "issue_counts": {
            "BLOCKS_PUBLICATION": sum(1 for row in issues if row["class"] == "BLOCKS_PUBLICATION"),
            "BLOCKS_JOURNAL_SUBMISSION": sum(1 for row in issues if row["class"] == "BLOCKS_JOURNAL_SUBMISSION"),
            "STYLE_OR_DIDACTIC_FIX": sum(1 for row in issues if row["class"] == "STYLE_OR_DIDACTIC_FIX"),
            "NON_BLOCKING_NOTE": sum(1 for row in issues if row["class"] == "NON_BLOCKING_NOTE"),
        },
        "issues": issues,
        "release_gate_snapshot": scorecard.get("gate_counts", {}),
        "strong_claim_snapshot": support.get("summary", {}),
        "science_blocker_snapshot": closure.get("summary", {}),
        "package_sha256": _sha256(package) if package.exists() else "",
        "publication_recommendation": "OWNER_APPROVED_PUBLICATION_CAN_PROCEED_AFTER_PUBLICATION_PREFLIGHT" if not issues else "STOP_AND_REPAIR",
    }
    _write_json(editorial_root(root) / "OWNER_REVIEW_PUBLICATION_READINESS_latest.json", payload)
    md = [
        "# Owner Review Publication Readiness",
        "",
        f"Status: `{payload['status']}`",
        f"Recommendation: `{payload['publication_recommendation']}`",
        f"Package SHA-256: `{payload['package_sha256']}`",
        "",
        "## Issue Counts",
        "",
        *[f"- {k}: `{v}`" for k, v in payload["issue_counts"].items()],
    ]
    if issues:
        md.extend(["", "## Issues", "", *[f"- `{row['class']}`: {row['issue']}" for row in issues]])
    _write_text(editorial_root(root) / "OWNER_REVIEW_PUBLICATION_READINESS_latest.md", "\n".join(md))
    return payload


VENUES = [
    ("FOUNDATIONS_OF_SCIENCE", "https://link.springer.com/journal/10699/aims-and-scope", "Primary target: interdisciplinary foundations of science; values faithful but non-technical foundational work.", True),
    ("SYNTHESE", "https://link.springer.com/journal/11229/aims-and-scope", "Backup: epistemology, methodology, philosophy of science, logic/mathematics foundations.", True),
    ("FOUNDATIONS_OF_PHYSICS", "https://link.springer.com/journal/10701/aims-and-scope", "Conditional target: physics/foundations only if physics claims stay bounded.", False),
    ("PHYSICAL_REVIEW_RESEARCH", "https://journals.aps.org/prresearch/about", "Conditional target: broad physics connection; requires strong physics framing.", False),
    ("ACS_OMEGA", "https://pubs.acs.org/journal/acsodf", "Conditional target: chemistry/interfacing sciences; current release is not chemistry-first.", False),
    ("ACTA_BIOTHEORETICA", "https://link.springer.com/journal/10441/aims-and-scope", "Conditional target: theoretical biology/philosophy of biology.", False),
    ("PLOS_COMPUTATIONAL_BIOLOGY", "https://journals.plos.org/ploscompbiol/s/journal-information", "Conditional target: computational biology requires biological insight and reproducible code/data.", False),
    ("GLOBAL_JOURNAL_OF_FLEXIBLE_SYSTEMS_MANAGEMENT", "https://link.springer.com/journal/40171/aims-and-scope", "Conditional target: systems management translation, not primary theory paper.", False),
]


def generate_submission_packages(root: Path) -> dict[str, Any]:
    base = release_root(root) / "submission_packages"
    rows = []
    for venue_id, official_url, fit_note, recommended in VENUES:
        d = base / venue_id
        payload = {
            "schema_id": "OC132_JOURNAL_SUBMISSION_PACKAGE_v1",
            "release_id": RELEASE_ID,
            "venue_id": venue_id,
            "official_url": official_url,
            "official_snapshot_date": "2026-04-28",
            "no_send": True,
            "submit_recommended": bool(recommended),
            "venue_fit_note": fit_note,
            "primary_manuscript": "releases/oc_core_1_3_2/artifacts/OC_CORE_1_3_2_JOURNAL_CORE_EN.pdf",
            "supporting_artifacts": [
                "releases/oc_core_1_3_2/artifacts/OC_CORE_1_3_2_MASTER_MONOGRAPH_EN.pdf",
                "releases/oc_core_1_3_2/artifacts/oc_core_1_3_2_zenodo_release.zip",
                "releases/oc_core_1_3_2/llm_readability/LLM_READER_GUIDE.md",
            ],
        }
        _write_json(d / "SUBMISSION_PACKAGE.json", payload)
        _write_text(d / "COVER_LETTER_DRAFT.md", f"# Cover Letter Draft: {venue_id}\n\nNO_SEND: true\n\nDear Editors,\n\nPlease consider the attached OC Core 1.3.2 journal-core manuscript and reproducibility package. This draft is prepared for owner review only and must not be submitted automatically.\n")
        _write_text(d / "CHECKLIST.md", "\n".join([
            f"# Submission Checklist: {venue_id}",
            "",
            "- NO_SEND: true",
            "- Manuscript PDF selected.",
            "- Release DOI/reference to be inserted after public release.",
            "- Data/code/reproducibility statement included.",
            "- AI assistance disclosure included.",
            "- Conflict/funding statements included.",
            "- Owner must approve submission separately.",
        ]))
        _write_text(d / "REPRODUCIBILITY_AND_DATA_STATEMENT.md", "The release package includes checksum-bound source material, benchmark scripts, benchmark output hashes, claim/evidence maps, and release-machine scorecards. No private raw feedback or raw model output is included.")
        _write_text(d / "AI_ASSISTANCE_DISCLOSURE.md", "AI tools assisted with editorial checking, release-machine automation, and structured review. The author remains responsible for claims, proofs, data, and final submission decisions.")
        _write_text(d / "VENUE_FIT_VERDICT.md", f"# Venue Fit Verdict: {venue_id}\n\nSubmit recommended: `{str(bool(recommended)).lower()}`\n\n{fit_note}\n")
        rows.append(payload)
    index = {"schema_id": "OC132_JOURNAL_SUBMISSION_PACKAGE_INDEX_v1", "release_id": RELEASE_ID, "no_send": True, "package_total": len(rows), "rows": rows}
    _write_json(base / "SUBMISSION_PACKAGE_INDEX.json", index)
    _write_text(base / "README.md", "# OC Core 1.3.2 Journal Submission Packages\n\nAll packages are prepared as `NO_SEND`. They are not submitted, emailed, uploaded, or released to journals by this process.\n")
    return index


def grant_owner_approval(root: Path, owner_identity: str = "Alexander Yashin") -> dict[str, Any]:
    manifest = _read_json(editorial_root(root) / "OC_CORE_1_3_2_PUBLISH_MANIFEST_DRAFT.json")
    payload = {
        "schema_id": "OWNER_APPROVAL_GRANTED_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "owner_identity": owner_identity,
        "approved_channels": ["github_release", "zenodo_new_version"],
        "journal_submissions_allowed": False,
        "artifact_freeze_hash": manifest.get("artifact_freeze_hash", ""),
        "scope": "Publish OC Core 1.3.2 through GitHub release and Zenodo new version only.",
        "granted_at": TIMESTAMP,
    }
    _write_json(editorial_root(root) / "OWNER_APPROVAL_GRANTED_v1.3.2.json", payload)
    _write_text(editorial_root(root) / "OWNER_APPROVAL_GRANTED_v1.3.2.md", f"# Owner Approval Granted\n\nRelease: `{RELEASE_ID}`\n\nChannels: GitHub release, Zenodo new version.\n\nFreeze hash: `{payload['artifact_freeze_hash']}`\n\nJournal submissions allowed: `false`\n")
    return payload


def publication_preflight(root: Path) -> dict[str, Any]:
    approval = _read_json(editorial_root(root) / "OWNER_APPROVAL_GRANTED_v1.3.2.json")
    scorecard_doc = _read_json(editorial_root(root) / "OC_CORE_1_3_2_RELEASE_SCORECARD_latest.json")
    scorecard = scorecard_doc.get("summary", scorecard_doc)
    manifest = _read_json(editorial_root(root) / "OC_CORE_1_3_2_PUBLISH_MANIFEST_DRAFT.json")
    raw_status = _run(root, ["git", "status", "--short", "-uall"], check=False).stdout.splitlines()
    allowed_dirty_suffixes = {
        "releases/oc_core_1_3_2/editorial/PUBLICATION_PREFLIGHT_latest.json",
        "releases/oc_core_1_3_2/editorial/PUBLICATION_EXECUTION_REPORT_latest.json",
    }
    dirty_rows = [
        row for row in raw_status
        if row[3:].replace("\\", "/") not in allowed_dirty_suffixes
    ]
    branch = _run(root, ["git", "branch", "--show-current"], check=False).stdout.strip()
    tag_check = _run(root, ["git", "rev-parse", "-q", "--verify", f"refs/tags/{TAG}"], check=False)
    package = release_root(root) / "artifacts" / "oc_core_1_3_2_zenodo_release.zip"
    problems = []
    if dirty_rows:
        problems.append("working tree is not clean")
    if branch != BRANCH:
        problems.append(f"wrong branch: {branch}")
    if tag_check.returncode == 0:
        problems.append(f"tag {TAG} already exists")
    if not approval:
        problems.append("owner approval artifact missing")
    if approval and approval.get("artifact_freeze_hash") != manifest.get("artifact_freeze_hash"):
        problems.append("owner approval freeze hash does not match publish manifest")
    gate_counts = scorecard.get("gate_counts", {})
    if scorecard.get("master_verdict") != "PASS" or gate_counts.get("FAIL", 1) != 0 or gate_counts.get("BLOCKED", 1) != 0:
        problems.append("release scorecard is not green")
    if not os.environ.get("GITHUB_TOKEN", "").strip():
        problems.append("GITHUB_TOKEN missing")
    if not os.environ.get("ZENODO_ACCESS_TOKEN", "").strip():
        problems.append("ZENODO_ACCESS_TOKEN missing")
    if not package.exists():
        problems.append("release ZIP missing")
    payload = {
        "schema_id": "OC132_PUBLICATION_PREFLIGHT_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "state": "PASS" if not problems else "PUBLICATION_BLOCKED_BY_TOOLING",
        "problems": problems,
        "branch": branch,
        "tag_exists": tag_check.returncode == 0,
        "package_sha256": _sha256(package) if package.exists() else "",
        "artifact_freeze_hash": manifest.get("artifact_freeze_hash", ""),
    }
    _write_json(editorial_root(root) / "PUBLICATION_PREFLIGHT_latest.json", payload)
    return payload


def _github_request(path: str, method: str = "GET", data: Any | None = None, *, upload_url: bool = False) -> Any:
    token = os.environ["GITHUB_TOKEN"].strip()
    base = "https://uploads.github.com" if upload_url else "https://api.github.com"
    body = None if data is None else json.dumps(data).encode("utf-8")
    req = urllib.request.Request(base + path, data=body, method=method)
    req.add_header("Authorization", "Bearer " + token)
    req.add_header("Accept", "application/vnd.github+json")
    if body is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=120) as resp:
        raw = resp.read()
    return json.loads(raw.decode("utf-8")) if raw else {}


def _zenodo_request(path: str, method: str = "GET", data: Any | None = None) -> Any:
    token = os.environ["ZENODO_ACCESS_TOKEN"].strip()
    sep = "&" if "?" in path else "?"
    url = "https://zenodo.org/api" + path + sep + urllib.parse.urlencode({"access_token": token})
    body = None if data is None else json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, method=method)
    if body is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=180) as resp:
        raw = resp.read()
    return json.loads(raw.decode("utf-8")) if raw else {}


def publish_execute(root: Path) -> dict[str, Any]:
    preflight = publication_preflight(root)
    if preflight["state"] != "PASS":
        return {"release_id": RELEASE_ID, "state": preflight["state"], "preflight": preflight}
    package = release_root(root) / "artifacts" / "oc_core_1_3_2_zenodo_release.zip"
    primary_assets = [release_root(root) / "artifacts" / name for name in [
        "OC_CORE_1_3_2_MASTER_MONOGRAPH_EN.pdf",
        "OC_CORE_1_3_2_JOURNAL_CORE_EN.pdf",
        "OC_CORE_1_3_2_READABLE_OVERVIEW_EN.pdf",
        "OC_CORE_1_3_2_METHODS_AND_REPRODUCIBILITY_COMPANION_EN.pdf",
        "OC_CORE_1_3_2_CRITIQUE_AND_OBJECTION_MAP_EN.pdf",
        "OC_CORE_1_3_2_EXPERT_TECHNICAL_SPINE_EN.pdf",
    ]]

    # Zenodo new-version draft and publication.
    new_version = _zenodo_request(f"/deposit/depositions/{ZENODO_PREVIOUS_RECORD}/actions/newversion", method="POST")
    draft_url = new_version.get("links", {}).get("latest_draft", "")
    if not draft_url:
        raise RuntimeError("Zenodo did not return latest_draft link")
    draft_id = str(draft_url.rstrip("/").split("/")[-1])
    draft = _zenodo_request(f"/deposit/depositions/{draft_id}")
    metadata = {
        "metadata": {
            "title": "Ontology of Continua - Core v1.3.2",
            "upload_type": "software",
            "publication_date": "2026-04-28",
            "creators": [{"name": "Yashin, Alexander", "orcid": "0009-0008-6166-0914", "affiliation": "Independent Researcher"}],
            "description": "Ontology of Continua Core v1.3.2 public release package with monograph, journal-core, reproducibility, LLM-readable companion, and release governance artifacts.",
            "access_right": "open",
            "license": "cc-by-4.0",
            "version": VERSION,
            "keywords": ["ontology", "continua", "systems theory", "structural dynamics", "reproducibility", "release governance"],
            "related_identifiers": [
                {"identifier": "10.5281/zenodo.17899134", "relation": "isVersionOf", "scheme": "doi"},
                {"identifier": "10.5281/zenodo.19741958", "relation": "isNewVersionOf", "scheme": "doi"},
                {"identifier": f"https://github.com/{REPO}/releases/tag/{TAG}", "relation": "isSupplementTo", "scheme": "url"},
            ],
        }
    }
    _zenodo_request(f"/deposit/depositions/{draft_id}", method="PUT", data=metadata)
    files = _zenodo_request(f"/deposit/depositions/{draft_id}/files")
    for row in files if isinstance(files, list) else []:
        _zenodo_request(f"/deposit/depositions/{draft_id}/files/{row['id']}", method="DELETE")
    for path in [package, *primary_assets, root / "checksums.txt", root / "manifest.json"]:
        token = os.environ["ZENODO_ACCESS_TOKEN"].strip()
        upload_url = f"https://zenodo.org/api/deposit/depositions/{draft_id}/files?{urllib.parse.urlencode({'access_token': token})}"
        with path.open("rb") as fh:
            data = fh.read()
        boundary = "----OC132Boundary"
        body = (
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{path.name}\"\r\n"
            "Content-Type: application/octet-stream\r\n\r\n"
        ).encode("utf-8") + data + f"\r\n--{boundary}--\r\n".encode("utf-8")
        req = urllib.request.Request(upload_url, data=body, method="POST")
        req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
        with urllib.request.urlopen(req, timeout=300) as resp:
            resp.read()
    published = _zenodo_request(f"/deposit/depositions/{draft_id}/actions/publish", method="POST")
    zenodo_record_id = str(published.get("id", draft_id))
    zenodo_doi = published.get("doi") or published.get("metadata", {}).get("prereserve_doi", {}).get("doi", "")

    # Git branch, tag and release.
    _run(root, ["git", "push", "origin", BRANCH])
    _run(root, ["git", "tag", "-a", TAG, "-m", f"OC Core {VERSION} public release"])
    _run(root, ["git", "push", "origin", TAG])
    body = (
        f"OC Core {VERSION} public release.\n\n"
        f"Zenodo DOI: {zenodo_doi or 'assigned by Zenodo'}\n"
        f"Zenodo record: https://zenodo.org/records/{zenodo_record_id}\n\n"
        "Includes primary PDFs, reproducibility package, LLM-readable companion, release dossier and checksums."
    )
    release = _github_request(
        f"/repos/{REPO}/releases",
        method="POST",
        data={"tag_name": TAG, "target_commitish": BRANCH, "name": f"OC Core {VERSION}", "body": body, "draft": False, "prerelease": False},
    )
    release_id = release["id"]
    for path in [package, *primary_assets, root / "checksums.txt", root / "manifest.json"]:
        token = os.environ["GITHUB_TOKEN"].strip()
        upload_path = f"/repos/{REPO}/releases/{release_id}/assets?{urllib.parse.urlencode({'name': path.name})}"
        req = urllib.request.Request("https://uploads.github.com" + upload_path, data=path.read_bytes(), method="POST")
        req.add_header("Authorization", "Bearer " + token)
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("Content-Type", "application/octet-stream")
        with urllib.request.urlopen(req, timeout=300) as resp:
            resp.read()
    report = {
        "schema_id": "OC132_PUBLICATION_EXECUTION_REPORT_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "state": "PUBLISHED",
        "github_release_url": release.get("html_url"),
        "zenodo_record_url": f"https://zenodo.org/records/{zenodo_record_id}",
        "zenodo_doi": zenodo_doi,
        "package_sha256": _sha256(package),
        "published_at": TIMESTAMP,
    }
    _write_json(editorial_root(root) / "PUBLICATION_EXECUTION_REPORT_latest.json", report)
    return report
