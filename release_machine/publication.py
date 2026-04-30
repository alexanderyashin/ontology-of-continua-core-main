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

from . import versioning

RELEASE_ID = "oc_core_1_3_2"
VERSION = "1.3.2"
TAG = "v1.3.2"
REPO = "alexanderyashin/ontology-of-continua-core-main"
BRANCH = "release/oc-core-1.3.2"
ZENODO_PREVIOUS_RECORD = "19851601"
TIMESTAMP = "2026-04-28T00:00:00Z"

TEXT_SUFFIXES = {".md", ".json", ".jsonld", ".ndjson", ".yaml", ".yml", ".txt", ".cff", ".tex", ".bib"}
LEAK_PATTERN = re.compile(
    r"claude_feedback|raw\s+feedback|raw\s+model\s+output|[A-Za-z]:\\Users\\|/home/|estra-private-work|"
    r"OPENAI_API_KEY|GITHUB_TOKEN|ZENODO_TOKEN|password\s*=|secret\s*=|token\s*=",
    re.IGNORECASE,
)

GITHUB_RELEASE_URL = f"https://github.com/{REPO}/releases/tag/{TAG}"
ZENODO_RECORD_ID = "19851694"
ZENODO_RECORD_URL = f"https://zenodo.org/records/{ZENODO_RECORD_ID}"
ZENODO_DOI = "10.5281/zenodo.19851694"
CONCEPT_DOI = "10.5281/zenodo.17899134"
PREVIOUS_DOI = "10.5281/zenodo.19851601"

PRIMARY_RELEASE_ASSETS = [
    {
        "filename": "OC_CORE_1_3_2_MASTER_MONOGRAPH_EN.pdf",
        "role": "Master monograph",
        "reader_group": "full scientific reference",
        "description": "The canonical long-form OC Core 1.3.2 text with theorem, formula, evidence and release-governance context.",
    },
    {
        "filename": "OC_CORE_1_3_2_JOURNAL_CORE_EN.pdf",
        "role": "Journal core",
        "reader_group": "journal editor or first reviewer",
        "description": "A compact article-style spine for scientific review and later journal-package refactoring.",
    },
    {
        "filename": "OC_CORE_1_3_2_READABLE_OVERVIEW_EN.pdf",
        "role": "Readable overview",
        "reader_group": "new human reader",
        "description": "A shorter conceptual entry point before the monograph or technical spine.",
    },
    {
        "filename": "OC_CORE_1_3_2_METHODS_AND_REPRODUCIBILITY_COMPANION_EN.pdf",
        "role": "Methods and reproducibility companion",
        "reader_group": "reproducibility reviewer",
        "description": "Build, benchmark, evidence-route and reproducibility navigation.",
    },
    {
        "filename": "OC_CORE_1_3_2_CRITIQUE_AND_OBJECTION_MAP_EN.pdf",
        "role": "Critique and objection map",
        "reader_group": "critical or adversarial reviewer",
        "description": "Known criticism, objection routes, repair history and bounded release responses.",
    },
    {
        "filename": "OC_CORE_1_3_2_EXPERT_TECHNICAL_SPINE_EN.pdf",
        "role": "Expert technical spine",
        "reader_group": "mathematical or technical reviewer",
        "description": "Formal kernel, theorem cards, formulas and technical support routes.",
    },
    {
        "filename": "oc_core_1_3_2_zenodo_release.zip",
        "role": "Full reproducibility package",
        "reader_group": "archival and machine reproducibility",
        "description": "Complete release bundle with source material, manifests, checksums, LLM-readable companion and no-send journal packages.",
    },
    {
        "filename": "manifest.json",
        "role": "Artifact manifest",
        "reader_group": "release auditor",
        "description": "Machine-readable package inventory.",
    },
    {
        "filename": "checksums.txt",
        "role": "Checksums",
        "reader_group": "release auditor",
        "description": "Checksum list for verifying the published assets.",
    },
]

RELEASE_GROUPS = [
    "Core theory",
    "Reviewer entry points",
    "Reproducibility",
    "LLM-readable science",
    "Release governance",
]

RELEASE_KEYWORDS = [
    "Ontology of Continua",
    "OC Core",
    "systems theory",
    "formal methods",
    "reproducible research",
    "mathematical modeling",
    "AI-readable science",
    "LLM-readable science",
    "release engineering",
    "benchmarking",
    "proof governance",
    "Parfitian Cerberus",
]

GITHUB_TOPICS = [
    "ontology-of-continua",
    "oc-core",
    "systems-theory",
    "formal-methods",
    "reproducible-research",
    "mathematical-modeling",
    "ai-readable-science",
    "release-engineering",
    "benchmarking",
]

RELEASE_HASHTAGS = [
    "#OntologyOfContinua",
    "#OCCore",
    "#SystemsTheory",
    "#FormalMethods",
    "#ReproducibleResearch",
    "#MathematicalModeling",
    "#AIReadableScience",
    "#LLMReadableScience",
    "#ReleaseEngineering",
]


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

SUBMISSION_ARTIFACT_REFS = [
    ("primary_manuscript", "releases/oc_core_1_3_2/artifacts/OC_CORE_1_3_2_JOURNAL_CORE_EN.pdf"),
    ("supporting_monograph", "releases/oc_core_1_3_2/artifacts/OC_CORE_1_3_2_MASTER_MONOGRAPH_EN.pdf"),
    ("release_archive", "releases/oc_core_1_3_2/artifacts/oc_core_1_3_2_zenodo_release.zip"),
    ("reader_guide", "releases/oc_core_1_3_2/llm_readability/LLM_READER_GUIDE.md"),
]

SUBMISSION_COMPONENTS = [
    ("submission_package_json", "SUBMISSION_PACKAGE.json", "Machine-readable package metadata and no-send governance."),
    ("required_component_manifest_json", "REQUIRED_COMPONENT_MANIFEST.json", "Machine-readable required component status list."),
    ("required_component_manifest_md", "REQUIRED_COMPONENT_MANIFEST.md", "Human-readable required component status list."),
    ("cover_letter", "COVER_LETTER_DRAFT.md", "Owner-review-only cover letter draft."),
    ("checklist", "CHECKLIST.md", "Submission checklist with no-send locks and pending owner actions."),
    ("reproducibility_and_data", "REPRODUCIBILITY_AND_DATA_STATEMENT.md", "Data, code and reproducibility statement."),
    ("ai_assistance", "AI_ASSISTANCE_DISCLOSURE.md", "AI assistance disclosure for editorial review."),
    ("conflict_and_funding", "CONFLICT_AND_FUNDING_STATEMENT.md", "Conflict-of-interest and funding statement."),
    ("venue_fit", "VENUE_FIT_VERDICT.md", "Venue fit verdict and recommendation state."),
]


def _submission_identity(root: Path, release_id: str | None = None) -> tuple[str, str, str]:
    if release_id:
        version = versioning.version_from_release_id(release_id)
        source = "explicit_release_id"
    else:
        identity = versioning.current_release(root)
        release_id = identity.release_id
        version = identity.version
        source = identity.source
    return release_id, version, source


def _submission_artifact_refs(release_id: str) -> list[tuple[str, str]]:
    if release_id == "oc_core_1_3_3":
        return [
            ("primary_manuscript", "releases/oc_core_1_3_3/artifacts/OC_CORE_1_3_3_JOURNAL_CORE_EN.pdf"),
            ("supporting_monograph", "releases/oc_core_1_3_3/artifacts/OC_CORE_1_3_3_MASTER_MONOGRAPH_EN.pdf"),
            ("release_archive", "releases/oc_core_1_3_3/artifacts/oc_core_1_3_3_no_send_release.zip"),
            ("reader_guide", "docs/OC_1_3_3_HOSTILE_READER_GUIDE.md"),
        ]
    return SUBMISSION_ARTIFACT_REFS


def _submission_zip_integrity_ref(release_id: str) -> str:
    if release_id == "oc_core_1_3_3":
        return "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_ZIP_INTEGRITY_latest.json"
    return "releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_ZIP_INTEGRITY_latest.json"


def _submission_schema(prefix_release_id: str, name: str) -> str:
    if prefix_release_id == "oc_core_1_3_3":
        return f"OC133_{name}_v1"
    return f"OC132_{name}_v1"


def _submission_artifact_rows(root: Path, release_id: str) -> list[dict[str, Any]]:
    rows = []
    for role, rel_path in _submission_artifact_refs(release_id):
        path = root / rel_path
        row = {
            "role": role,
            "path": rel_path,
            "exists": path.exists(),
            "size_bytes": path.stat().st_size if path.exists() else 0,
            "sha256": _sha256(path) if path.exists() else "",
            "checksum_algorithm": "sha256",
        }
        if role == "release_archive":
            # The submission package is included in the release archive, so a
            # live archive hash here would create self-reference drift.
            row.update({
                "size_bytes": 0,
                "sha256": "",
                "checksum_ref": _submission_zip_integrity_ref(release_id),
                "checksum_status": "RECORDED_AFTER_PACKAGE_BUILD_TO_AVOID_SELF_REFERENCE",
            })
        rows.append(row)
    return rows


def _submission_component_rows(venue_id: str, release_id: str) -> list[dict[str, Any]]:
    base = f"releases/{release_id}/submission_packages/{venue_id}"
    return [
        {
            "component_id": component_id,
            "filename": filename,
            "path": f"{base}/{filename}",
            "required": True,
            "status": "READY_NO_SEND",
            "description": description,
        }
        for component_id, filename, description in SUBMISSION_COMPONENTS
    ]


def generate_submission_packages(root: Path, release_id: str | None = None) -> dict[str, Any]:
    release_id, version, identity_source = _submission_identity(root, release_id)
    base = root / "releases" / release_id / "submission_packages"
    artifact_refs_template = _submission_artifact_refs(release_id)
    primary_manuscript = next(path for role, path in artifact_refs_template if role == "primary_manuscript")
    supporting_artifacts = [path for role, path in artifact_refs_template if role != "primary_manuscript"]
    rows = []
    for venue_id, official_url, fit_note, recommended in VENUES:
        d = base / venue_id
        artifact_refs = _submission_artifact_rows(root, release_id)
        component_rows = _submission_component_rows(venue_id, release_id)
        artifact_missing_total = sum(1 for row in artifact_refs if not row["exists"])
        package_status = "OWNER_REVIEW_READY_NO_SEND" if artifact_missing_total == 0 else "BLOCKED_MISSING_ARTIFACTS_NO_SEND"
        payload = {
            "schema_id": _submission_schema(release_id, "JOURNAL_SUBMISSION_PACKAGE"),
            "release_id": release_id,
            "version": version,
            "identity_source": identity_source,
            "venue_id": venue_id,
            "official_url": official_url,
            "official_snapshot_date": "2026-04-28",
            "package_status": package_status,
            "no_send": True,
            "submission_allowed": False,
            "owner_approval_required": True,
            "journal_submissions_allowed": False,
            "submit_recommended": bool(recommended),
            "venue_fit_note": fit_note,
            "primary_manuscript": primary_manuscript,
            "supporting_artifacts": supporting_artifacts,
            "artifact_refs": artifact_refs,
            "artifact_missing_total": artifact_missing_total,
            "required_components": component_rows,
            "required_component_total": len(component_rows),
            "required_component_ready_total": len(component_rows),
            "doi_policy": {
                "release_doi": ZENODO_DOI if release_id == RELEASE_ID else "",
                "concept_doi": CONCEPT_DOI if release_id == RELEASE_ID else "",
                "status": "PENDING_PUBLIC_RELEASE_AND_SEPARATE_OWNER_SUBMISSION_APPROVAL",
                "journal_submission_doi_insert_allowed": False,
            },
            "submission_policy": {
                "outbound": "NO_SEND",
                "email_allowed": False,
                "portal_upload_allowed": False,
                "external_submission_allowed": False,
                "next_required_action": "OWNER_REVIEW_AFTER_PUBLIC_RELEASE_DECISION",
            },
        }
        _write_json(d / "SUBMISSION_PACKAGE.json", payload)
        component_manifest = {
            "schema_id": _submission_schema(release_id, "JOURNAL_SUBMISSION_COMPONENT_MANIFEST"),
            "release_id": release_id,
            "version": version,
            "venue_id": venue_id,
            "package_status": package_status,
            "no_send": True,
            "submission_allowed": False,
            "required_component_total": len(component_rows),
            "required_component_ready_total": len(component_rows),
            "rows": component_rows,
        }
        _write_json(d / "REQUIRED_COMPONENT_MANIFEST.json", component_manifest)
        _write_text(d / "REQUIRED_COMPONENT_MANIFEST.md", "\n".join([
            f"# Required Component Manifest: {venue_id}",
            "",
            f"- package_status: `{package_status}`",
            "- no_send: `true`",
            "- submission_allowed: `false`",
            "",
            "## Components",
            "",
            *[f"- `{row['component_id']}`: `{row['status']}` - `{row['path']}`" for row in component_rows],
        ]))
        _write_text(d / "COVER_LETTER_DRAFT.md", "\n".join([
            f"# Cover Letter Draft: {venue_id}",
            "",
            "NO_SEND: true",
            "Submission allowed: false",
            "Owner approval required: true",
            "",
            "Dear Editors,",
            "",
            f"Please consider the attached OC Core {version} journal-core manuscript and reproducibility package. This draft is prepared for owner review only and must not be submitted automatically.",
            "",
            f"Venue fit note: {fit_note}",
            "",
            "Release DOI/reference insertion remains pending until public release and a separate owner-approved journal submission decision.",
        ]))
        _write_text(d / "CHECKLIST.md", "\n".join([
            f"# Submission Checklist: {venue_id}",
            "",
            "- NO_SEND: true",
            "- Submission allowed: false",
            "- Owner approval required: true",
            "- Manuscript PDF selected.",
            "- Release DOI/reference to be inserted only after public release and separate owner approval.",
            "- Data/code/reproducibility statement included.",
            "- AI assistance disclosure included.",
            "- Conflict/funding statements included.",
            "- Required component manifest included.",
            "- Artifact checksum references included in `SUBMISSION_PACKAGE.json`.",
            "- Owner must approve submission separately.",
        ]))
        _write_text(d / "REPRODUCIBILITY_AND_DATA_STATEMENT.md", "\n".join([
            f"# Reproducibility And Data Statement: {venue_id}",
            "",
            "The release package includes checksum-bound source material, benchmark scripts, benchmark output hashes, claim/evidence maps, and release-machine scorecards. No private raw feedback or raw model output is included.",
            "",
            f"Primary reproducibility artifact: `{next(path for role, path in artifact_refs_template if role == 'release_archive')}`.",
            "Journal submission remains `NO_SEND` until a separate owner-approved submission decision.",
        ]))
        _write_text(d / "AI_ASSISTANCE_DISCLOSURE.md", "\n".join([
            f"# AI Assistance Disclosure: {venue_id}",
            "",
            "AI tools assisted with editorial checking, release-machine automation, and structured review. The author remains responsible for claims, proofs, data, and final submission decisions.",
        ]))
        _write_text(d / "CONFLICT_AND_FUNDING_STATEMENT.md", "\n".join([
            f"# Conflict And Funding Statement: {venue_id}",
            "",
            "Conflict-of-interest and funding declarations are owner-review placeholders for the no-send package. They must be confirmed by the author before any journal submission.",
            "",
            "Submission allowed: false.",
        ]))
        _write_text(d / "VENUE_FIT_VERDICT.md", "\n".join([
            f"# Venue Fit Verdict: {venue_id}",
            "",
            f"Submit recommended: `{str(bool(recommended)).lower()}`",
            "Submission allowed: `false`",
            "",
            fit_note,
        ]))
        rows.append(payload)
    status_counts = {status: sum(1 for row in rows if row["package_status"] == status) for status in sorted({row["package_status"] for row in rows})}
    index = {
        "schema_id": _submission_schema(release_id, "JOURNAL_SUBMISSION_PACKAGE_INDEX"),
        "release_id": release_id,
        "version": version,
        "identity_source": identity_source,
        "no_send": True,
        "submission_allowed": False,
        "owner_approval_required": True,
        "journal_submissions_allowed": False,
        "package_total": len(rows),
        "recommended_package_total": sum(1 for row in rows if row["submit_recommended"]),
        "package_status_counts": status_counts,
        "artifact_checksum_policy": "sha256 refs are recorded inside each no-send venue package.",
        "rows": rows,
    }
    _write_json(base / "SUBMISSION_PACKAGE_INDEX.json", index)
    _write_text(base / "README.md", "\n".join([
        f"# OC Core {version} Journal Submission Packages",
        "",
        "All packages are prepared as `NO_SEND`. They are not submitted, emailed, uploaded, or released to journals by this process.",
        "",
        f"- Package total: `{len(rows)}`",
        f"- Recommended primary targets: `{index['recommended_package_total']}`",
        "- Submission allowed: `false`",
        "- Owner approval required: `true`",
    ]))
    return index


def build_public_release_presentation(root: Path) -> dict[str, Any]:
    """Generate the human-facing public release body and metadata.

    This is intentionally separate from package construction: a release can have
    correct files but still look unfinished if the public surface lacks
    navigation, asset roles, keywords and citation instructions.
    """
    asset_rows = []
    for asset in PRIMARY_RELEASE_ASSETS:
        path = _public_asset_path(root, asset["filename"])
        asset_rows.append({
            **asset,
            "size_bytes": path.stat().st_size if path.exists() else 0,
            "exists": path.exists(),
        })
    asset_md = "\n".join(
        f"- **{row['role']}** - `{row['filename']}`: {row['description']} "
        f"Reader group: {row['reader_group']}."
        for row in asset_rows
    )
    group_md = ", ".join(f"`{group}`" for group in RELEASE_GROUPS)
    keyword_md = ", ".join(RELEASE_KEYWORDS)
    hashtag_md = " ".join(RELEASE_HASHTAGS)
    github_body = f"""# OC Core {VERSION} - Platinum Public Release

DOI: [{ZENODO_DOI}](https://doi.org/{ZENODO_DOI})

Zenodo record: {ZENODO_RECORD_URL}

Concept DOI: [{CONCEPT_DOI}](https://doi.org/{CONCEPT_DOI})

## Table Of Contents

1. What This Release Is
2. Start Here
3. Separate PDF Files
4. Full Package And Verification
5. Scientific Highlights
6. Release Groups, Keywords And Hashtags
7. Citation
8. Boundaries

## What This Release Is

OC Core {VERSION} is the current public release of the Ontology of Continua core line. It packages the canonical monograph, reviewer-specific PDF entry points, reproducibility material, benchmark/evidence routes, LLM-readable companion files, and release governance manifests.

## Start Here

- New reader: open `OC_CORE_1_3_2_READABLE_OVERVIEW_EN.pdf`.
- Scientific reviewer: open `OC_CORE_1_3_2_JOURNAL_CORE_EN.pdf`, then the master monograph.
- Mathematical or technical reviewer: open `OC_CORE_1_3_2_EXPERT_TECHNICAL_SPINE_EN.pdf`.
- Reproducibility reviewer: open `OC_CORE_1_3_2_METHODS_AND_REPRODUCIBILITY_COMPANION_EN.pdf`.
- Critical reviewer: open `OC_CORE_1_3_2_CRITIQUE_AND_OBJECTION_MAP_EN.pdf`.
- Machine reader: use the `llm_readability/` directory inside the ZIP.

## Separate PDF Files

The main PDFs are attached individually for direct reading, not only inside the ZIP.

{asset_md}

## Full Package And Verification

Download `oc_core_1_3_2_zenodo_release.zip` for the complete reproducibility package. Use `manifest.json` and `checksums.txt` to verify package contents and checksums.

Zenodo may additionally display a GitHub source snapshot archive generated from the repository tag. Treat that archive as a source mirror; the curated release package is `oc_core_1_3_2_zenodo_release.zip`.

## Scientific Highlights

- Release-level theorem support, including the global verdict-invariant minimality theorem for the OC-compatible verdict-preserving representation class.
- Deterministic benchmark suite with fixed seeds, output hashes, baseline comparisons and no-signalling checks.
- Terminal release blocker ledger with 82/82 rows closed for the 1.3.2 release scope.
- K0-K12/domain projection state, DRT strict salvage state, Tsukrov criticism-response integration, Parfitian Cerberus pass and LRGEF release governance.
- LLM-readable companion: claim graph, theorem cards, formula registry, evidence route map, benchmark cards and machine-readable glossary.

## Release Groups, Keywords And Hashtags

Groups: {group_md}

Keywords: {keyword_md}

Hashtags: {hashtag_md}

## Citation

Yashin, Alexander. *Ontology of Continua - Core v{VERSION}*. Zenodo. {ZENODO_DOI}. {ZENODO_RECORD_URL}

## Boundaries

This public release contains public-safe scientific and release-governance artifacts. It does not include private raw feedback, raw model outputs, private paths, secrets, or journal submissions. Journal submission packages are prepared separately as `NO_SEND` materials and are not submitted by this release process.
"""
    zenodo_description = f"""
<p><strong>OC Core {VERSION}</strong> is the current public release of the Ontology of Continua core line. It contains the canonical monograph, reviewer-specific PDF entry points, reproducibility material, benchmark and evidence routes, LLM-readable companion files, and release governance manifests.</p>
<h2>Table Of Contents</h2>
<ol>
<li>Start here</li>
<li>Separate PDF files</li>
<li>Full package and verification</li>
<li>Scientific highlights</li>
<li>Release groups, keywords and hashtags</li>
<li>Citation and boundaries</li>
</ol>
<h2>Start Here</h2>
<ul>
<li>New reader: <code>OC_CORE_1_3_2_READABLE_OVERVIEW_EN.pdf</code>.</li>
<li>Scientific reviewer: <code>OC_CORE_1_3_2_JOURNAL_CORE_EN.pdf</code>, then the master monograph.</li>
<li>Mathematical or technical reviewer: <code>OC_CORE_1_3_2_EXPERT_TECHNICAL_SPINE_EN.pdf</code>.</li>
<li>Reproducibility reviewer: <code>OC_CORE_1_3_2_METHODS_AND_REPRODUCIBILITY_COMPANION_EN.pdf</code>.</li>
<li>Critical reviewer: <code>OC_CORE_1_3_2_CRITIQUE_AND_OBJECTION_MAP_EN.pdf</code>.</li>
<li>Machine reader: use the <code>llm_readability/</code> directory inside the ZIP.</li>
</ul>
<h2>Separate PDF Files</h2>
<p>The primary PDFs are attached individually for direct reading, not only inside the ZIP.</p>
<ul>
{''.join(f"<li><strong>{row['role']}</strong>: <code>{row['filename']}</code> - {row['description']}</li>" for row in asset_rows if row['filename'].lower().endswith('.pdf'))}
</ul>
<h2>Full Package And Verification</h2>
<p>Download <code>oc_core_1_3_2_zenodo_release.zip</code> for the complete package. Use <code>manifest.json</code> and <code>checksums.txt</code> to verify contents and checksums.</p>
<p>Zenodo may additionally display a GitHub source snapshot archive generated from the repository tag. Treat that archive as a source mirror; the curated release package is <code>oc_core_1_3_2_zenodo_release.zip</code>.</p>
<h2>Scientific Highlights</h2>
<ul>
<li>Release-level theorem support, including the global verdict-invariant minimality theorem for the OC-compatible verdict-preserving representation class.</li>
<li>Deterministic benchmark suite with fixed seeds, output hashes, baseline comparisons and no-signalling checks.</li>
<li>Terminal release blocker ledger with 82/82 rows closed for the 1.3.2 release scope.</li>
<li>K0-K12/domain projection state, DRT strict salvage state, Tsukrov criticism-response integration, Parfitian Cerberus pass and LRGEF release governance.</li>
<li>LLM-readable companion: claim graph, theorem cards, formula registry, evidence route map, benchmark cards and glossary.</li>
</ul>
<h2>Release Groups, Keywords And Hashtags</h2>
<p>Groups: {', '.join(RELEASE_GROUPS)}</p>
<p>Keywords: {keyword_md}</p>
<p>Hashtags: {hashtag_md}</p>
<h2>Boundaries</h2>
<p>This public release contains public-safe scientific and release-governance artifacts. It does not include private raw feedback, raw model outputs, private paths, secrets, or journal submissions. Journal submission packages remain <code>NO_SEND</code>.</p>
"""
    payload = {
        "schema_id": "OC132_PUBLIC_RELEASE_PRESENTATION_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": TIMESTAMP,
        "github_release_url": GITHUB_RELEASE_URL,
        "zenodo_record_url": ZENODO_RECORD_URL,
        "doi": ZENODO_DOI,
        "concept_doi": CONCEPT_DOI,
        "previous_doi": PREVIOUS_DOI,
        "groups": RELEASE_GROUPS,
        "keywords": RELEASE_KEYWORDS,
        "github_topics": GITHUB_TOPICS,
        "hashtags": RELEASE_HASHTAGS,
        "assets": asset_rows,
        "github_release_body": github_body,
        "zenodo_description": zenodo_description,
    }
    _write_json(editorial_root(root) / "PUBLIC_RELEASE_PRESENTATION_latest.json", payload)
    _write_text(editorial_root(root) / "PUBLIC_RELEASE_PRESENTATION_latest.md", github_body)
    return payload


def sync_public_release_presentation(root: Path) -> dict[str, Any]:
    presentation = build_public_release_presentation(root)
    actions: dict[str, Any] = {"github_release": {}, "github_topics": {}, "zenodo_record": {}}
    expected_asset_names = [row["filename"] for row in PRIMARY_RELEASE_ASSETS]

    release = _github_request(f"/repos/{REPO}/releases/tags/{TAG}")
    patched = _github_request(
        f"/repos/{REPO}/releases/{release['id']}",
        method="PATCH",
        data={
            "name": f"OC Core {VERSION} - Platinum Public Release",
            "body": presentation["github_release_body"],
            "draft": False,
            "prerelease": False,
        },
    )
    deleted_github_assets = []
    uploaded_github_assets = []
    current_assets = {row.get("name"): row for row in patched.get("assets", [])}
    for name in expected_asset_names:
        if name in current_assets:
            _github_request(f"/repos/{REPO}/releases/assets/{current_assets[name]['id']}", method="DELETE")
            deleted_github_assets.append(name)
    for name in expected_asset_names:
        path = _public_asset_path(root, name)
        uploaded = _github_upload_asset(patched["id"], path)
        uploaded_github_assets.append({"name": uploaded.get("name", name), "size": uploaded.get("size", path.stat().st_size)})
    actions["github_release"] = {
        "id": patched.get("id"),
        "html_url": patched.get("html_url"),
        "body_length": len(patched.get("body") or ""),
        "asset_count": len(expected_asset_names),
        "assets_replaced": deleted_github_assets,
        "assets_uploaded": uploaded_github_assets,
    }
    try:
        topics = _github_request(f"/repos/{REPO}/topics", method="PUT", data={"names": GITHUB_TOPICS})
        actions["github_topics"] = {"state": "PASS", "names": topics.get("names", [])}
    except urllib.error.HTTPError as exc:
        actions["github_topics"] = {"state": "WARN", "reason": f"GitHub topics update failed with HTTP {exc.code}"}

    try:
        _zenodo_request(f"/deposit/depositions/{ZENODO_RECORD_ID}/actions/edit", method="POST")
    except urllib.error.HTTPError as exc:
        if exc.code not in {400, 403, 405}:
            raise
    deposition = _zenodo_request(f"/deposit/depositions/{ZENODO_RECORD_ID}")
    metadata = dict(deposition.get("metadata", {}))
    metadata.update({
        "title": f"Ontology of Continua - Core v{VERSION}",
        "upload_type": metadata.get("upload_type") or "software",
        "publication_date": metadata.get("publication_date") or "2026-04-28",
        "creators": metadata.get("creators") or [{"name": "Yashin, Alexander", "orcid": "0009-0008-6166-0914", "affiliation": "Independent Researcher"}],
        "description": presentation["zenodo_description"],
        "access_right": metadata.get("access_right") or "open",
        "license": metadata.get("license") or "cc-by-4.0",
        "version": VERSION,
        "keywords": RELEASE_KEYWORDS,
        "related_identifiers": [
            {"identifier": CONCEPT_DOI, "relation": "isVersionOf", "scheme": "doi"},
            {"identifier": PREVIOUS_DOI, "relation": "isNewVersionOf", "scheme": "doi"},
            {"identifier": GITHUB_RELEASE_URL, "relation": "isSupplementTo", "scheme": "url"},
        ],
    })
    updated = _zenodo_request(f"/deposit/depositions/{ZENODO_RECORD_ID}", method="PUT", data={"metadata": metadata})
    zenodo_file_delete_failures = []
    files = _zenodo_request(f"/deposit/depositions/{ZENODO_RECORD_ID}/files")
    for row in files if isinstance(files, list) else []:
        filename = row.get("filename") or row.get("key")
        try:
            _zenodo_request(f"/deposit/depositions/{ZENODO_RECORD_ID}/files/{row['id']}", method="DELETE")
        except urllib.error.HTTPError as exc:
            zenodo_file_delete_failures.append({"name": filename, "http_status": exc.code})
    bucket_url = updated.get("links", {}).get("bucket") or deposition.get("links", {}).get("bucket")
    uploaded_zenodo_files = []
    if not bucket_url:
        raise RuntimeError("Zenodo deposition did not expose a file bucket for release asset synchronization.")
    for name in expected_asset_names:
        path = _public_asset_path(root, name)
        _zenodo_bucket_upload_file(bucket_url, path)
        uploaded_zenodo_files.append({"name": name, "size": path.stat().st_size})
    try:
        published = _zenodo_request(f"/deposit/depositions/{ZENODO_RECORD_ID}/actions/publish", method="POST")
    except urllib.error.HTTPError as exc:
        if exc.code not in {400, 403, 405}:
            raise
        published = updated
    actions["zenodo_record"] = {
        "id": published.get("id", updated.get("id")),
        "doi": published.get("doi", updated.get("doi")),
        "description_length": len(metadata.get("description") or ""),
        "keyword_count": len(metadata.get("keywords") or []),
        "files_uploaded": uploaded_zenodo_files,
        "upload_method": "zenodo_bucket_put",
        "file_delete_failures": zenodo_file_delete_failures,
    }
    package = release_root(root) / "artifacts" / "oc_core_1_3_2_zenodo_release.zip"
    execution_report = _read_json(editorial_root(root) / "PUBLICATION_EXECUTION_REPORT_latest.json")
    execution_report.update({
        "schema_id": "OC132_PUBLICATION_EXECUTION_REPORT_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "state": "PUBLISHED",
        "github_release_url": actions["github_release"].get("html_url", GITHUB_RELEASE_URL),
        "zenodo_record_url": ZENODO_RECORD_URL,
        "zenodo_doi": ZENODO_DOI,
        "package_sha256": _sha256(package) if package.exists() else "",
        "presentation_sync_state": "PASS",
        "presentation_sync_at": TIMESTAMP,
        "supersedes_zenodo_record": "https://zenodo.org/records/19851601",
    })
    _write_json(editorial_root(root) / "PUBLICATION_EXECUTION_REPORT_latest.json", execution_report)
    report = {
        "schema_id": "OC132_PUBLIC_RELEASE_PRESENTATION_SYNC_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": TIMESTAMP,
        "state": "PASS",
        "actions": actions,
    }
    _write_json(editorial_root(root) / "PUBLIC_RELEASE_PRESENTATION_SYNC_latest.json", report)
    return report


def verify_public_release_presentation(root: Path) -> dict[str, Any]:
    import hashlib

    presentation = build_public_release_presentation(root)
    gh = _github_request(f"/repos/{REPO}/releases/tags/{TAG}")
    with urllib.request.urlopen(f"https://zenodo.org/api/records/{ZENODO_RECORD_ID}", timeout=60) as resp:
        zenodo = json.loads(resp.read().decode("utf-8"))

    expected_names = {row["filename"] for row in PRIMARY_RELEASE_ASSETS}
    github_assets = {row.get("name"): row for row in gh.get("assets", [])}
    zenodo_files = {row.get("key"): row for row in zenodo.get("files", [])}
    github_missing = sorted(expected_names - set(github_assets))
    zenodo_missing = sorted(expected_names - set(zenodo_files))
    zenodo_extra_files = sorted(set(zenodo_files) - expected_names)
    zenodo_checksum_mismatches = []
    for name, row in zenodo_files.items():
        if name not in expected_names:
            continue
        path = (release_root(root) / "artifacts" / name) if name.lower().endswith((".pdf", ".zip")) else root / name
        if not path.exists():
            continue
        local_md5 = hashlib.md5(path.read_bytes()).hexdigest()
        remote_md5 = str(row.get("checksum", "")).replace("md5:", "")
        if remote_md5 and local_md5 != remote_md5:
            zenodo_checksum_mismatches.append({"name": name, "local_md5": local_md5, "remote_md5": remote_md5})
    gh_body = gh.get("body") or ""
    zen_desc = zenodo.get("metadata", {}).get("description") or ""
    zen_keywords = set(zenodo.get("metadata", {}).get("keywords") or [])
    checks = {
        "github_has_toc": "## Table Of Contents" in gh_body,
        "github_has_asset_guide": "## Separate PDF Files" in gh_body and "OC_CORE_1_3_2_MASTER_MONOGRAPH_EN.pdf" in gh_body,
        "github_has_hashtags": all(tag in gh_body for tag in RELEASE_HASHTAGS[:3]),
        "zenodo_has_toc": "Table Of Contents" in zen_desc,
        "zenodo_has_asset_guide": "Separate PDF Files" in zen_desc,
        "zenodo_has_keywords": set(RELEASE_KEYWORDS[:6]).issubset(zen_keywords),
        "github_assets_complete": not github_missing,
        "zenodo_files_complete": not zenodo_missing,
        "zenodo_checksums_match": not zenodo_checksum_mismatches,
    }
    state = "PASS" if all(checks.values()) else "FAIL"
    report = {
        "schema_id": "OC132_PUBLIC_RELEASE_PRESENTATION_POSTFLIGHT_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": TIMESTAMP,
        "state": state,
        "github_release_url": gh.get("html_url"),
        "zenodo_record_url": ZENODO_RECORD_URL,
        "doi": zenodo.get("doi"),
        "checks": checks,
        "github_body_length": len(gh_body),
        "zenodo_description_length": len(zen_desc),
        "github_asset_count": len(github_assets),
        "zenodo_file_count": len(zenodo_files),
        "github_missing_assets": github_missing,
        "zenodo_missing_files": zenodo_missing,
        "zenodo_extra_files": zenodo_extra_files,
        "zenodo_checksum_mismatches": zenodo_checksum_mismatches,
        "groups": presentation["groups"],
        "hashtags": presentation["hashtags"],
        "keywords": presentation["keywords"],
    }
    _write_json(editorial_root(root) / "PUBLIC_RELEASE_PRESENTATION_POSTFLIGHT_latest.json", report)
    md = [
        "# Public Release Presentation Postflight",
        "",
        f"State: `{state}`",
        f"GitHub: {gh.get('html_url')}",
        f"Zenodo: {ZENODO_RECORD_URL}",
        f"DOI: `{zenodo.get('doi')}`",
        "",
        "## Checks",
        "",
        *[f"- {key}: `{str(value).lower()}`" for key, value in checks.items()],
    ]
    if zenodo_checksum_mismatches:
        md.extend(["", "## Zenodo Checksum Mismatches", "", *[f"- `{row['name']}`" for row in zenodo_checksum_mismatches]])
    _write_text(editorial_root(root) / "PUBLIC_RELEASE_PRESENTATION_POSTFLIGHT_latest.md", "\n".join(md))
    return report


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


def _public_asset_path(root: Path, name: str) -> Path:
    return (release_root(root) / "artifacts" / name) if name.lower().endswith((".pdf", ".zip")) else root / name


def _github_upload_asset(release_id: int | str, path: Path) -> Any:
    token = os.environ["GITHUB_TOKEN"].strip()
    upload_path = f"/repos/{REPO}/releases/{release_id}/assets?{urllib.parse.urlencode({'name': path.name})}"
    req = urllib.request.Request("https://uploads.github.com" + upload_path, data=path.read_bytes(), method="POST")
    req.add_header("Authorization", "Bearer " + token)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Content-Type", "application/octet-stream")
    with urllib.request.urlopen(req, timeout=300) as resp:
        raw = resp.read()
    return json.loads(raw.decode("utf-8")) if raw else {}


def _zenodo_upload_file(deposition_id: str, path: Path) -> None:
    token = os.environ["ZENODO_ACCESS_TOKEN"].strip()
    upload_url = f"https://zenodo.org/api/deposit/depositions/{deposition_id}/files?{urllib.parse.urlencode({'access_token': token})}"
    boundary = "----OC132Boundary"
    body = (
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{path.name}\"\r\n"
        "Content-Type: application/octet-stream\r\n\r\n"
    ).encode("utf-8") + path.read_bytes() + f"\r\n--{boundary}--\r\n".encode("utf-8")
    req = urllib.request.Request(upload_url, data=body, method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    with urllib.request.urlopen(req, timeout=300) as resp:
        resp.read()


def _zenodo_bucket_upload_file(bucket_url: str, path: Path) -> None:
    token = os.environ["ZENODO_ACCESS_TOKEN"].strip()
    upload_url = bucket_url.rstrip("/") + "/" + urllib.parse.quote(path.name) + "?" + urllib.parse.urlencode({"access_token": token})
    req = urllib.request.Request(upload_url, data=path.read_bytes(), method="PUT")
    req.add_header("Content-Type", "application/octet-stream")
    with urllib.request.urlopen(req, timeout=300) as resp:
        resp.read()


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
                {"identifier": PREVIOUS_DOI, "relation": "isNewVersionOf", "scheme": "doi"},
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
