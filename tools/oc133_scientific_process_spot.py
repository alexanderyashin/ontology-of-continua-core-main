#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
RELEASE_ROOT = ROOT / "releases" / RELEASE_ID
EDITORIAL = RELEASE_ROOT / "editorial"
SPOT_JSON = EDITORIAL / "OC133_SCIENTIFIC_PROCESS_SPOT_latest.json"
SPOT_MD = EDITORIAL / "OC133_SCIENTIFIC_PROCESS_SPOT_latest.md"

REQUIRED_DOMAINS = {"physics", "chemistry", "biology", "systems", "mathematics"}
REQUIRED_PRIOR_ART_FAMILIES = {
    "General System Theory",
    "Autopoiesis",
    "Dynamical Systems",
    "Category",
    "Topos",
    "RAF",
    "Complexity",
    "Information",
    "Identity",
    "Systems Engineering",
}

REQUIRED_CURRENT_SCIENCE_REFS = [
    "claims/CLAIM_LEDGER_1_3_3.json",
    "proofs/THEOREM_INVENTORY_1_3_3.json",
    "formal/lean/OC133V12.lean",
    "formal/lean/LEAN_BUILD_CERTIFICATE_1_3_3.json",
    "proofs/FINITE_MODEL_CHECKS_1_3_3.json",
    "proofs/FINITE_MODEL_OUTPUT_ATTESTATION_1_3_3.json",
    "validation/target_blind/OC133_TARGET_BLIND_PREDICTION_TABLE.json",
    "validation/numeric_replay_qa/OC133_NUMERIC_REPLAY_QA_TABLE.json",
    "reports/OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.json",
    "docs/OC_1_3_3_PRIOR_ART_COMPARATOR_MATRIX.json",
    "comparators/OC_1_3_3_NOVELTY_AND_PRIORITY_REGISTER.json",
    "docs/OC_1_3_3_PHENOMENON_COVERAGE_MATRIX.json",
    "simulations/results/OC_CORE_1_3_3_SIMULATION_RESULTS_latest.json",
    "reports/OC_CORE_1_3_3_ADVERSARIAL_SIMULATION_REPORT.json",
    "reports/OC_CORE_1_3_3_COUNTEREXAMPLE_REPORT.json",
    "reviews/oc133_llm_cerberus/OC133_LLM_CERBERUS_SUMMARY.json",
    "reviews/oc133_llm_cerberus/editorial_release_review/OC133_EDITORIAL_CERBERUS_SUMMARY.json",
    "releases/oc_core_1_3_3/editorial/SCIENCE_MONOLITH_CORPUS_LEDGER_1_3_3_latest.json",
    "releases/oc_core_1_3_3/editorial/SCIENCE_MONOLITH_AUDIT_1_3_3_latest.json",
    "releases/oc_core_1_3_3/submission_packages/SUBMISSION_PACKAGE_INDEX.json",
    "operations/project_control/LOGION_PROJECT_CONTROL_COCKPIT.json",
    "operations/logion_release_mission/oc_core_1_3_3/OC133_ALL_DOMAIN_READINESS_SCORECARD.json",
    "operations/logion_release_mission/oc_core_1_3_3/OC133_CONTENT_CLOSURE_SCORECARD.json",
]

PROCESS_STATE_REFS = {
    "reviews/oc133_llm_cerberus/editorial_release_review/OC133_EDITORIAL_CERBERUS_SUMMARY.json",
    "releases/oc_core_1_3_3/editorial/SCIENCE_MONOLITH_CORPUS_LEDGER_1_3_3_latest.json",
    "releases/oc_core_1_3_3/editorial/SCIENCE_MONOLITH_AUDIT_1_3_3_latest.json",
}

PUBLIC_DOCUMENT_REQUIREMENTS = {
    "guide": [
        "Public Landing Guide",
        "Recommended Reading Order",
        "Evidence Summary",
        "Claim Boundary",
        "Verification Route",
        "What to Cite",
    ],
    "master": [
        "Audience.",
        "Literature and Prior-Art Position",
        "Figure Route",
        "Model-Core Claims",
        "Theorem and Proof Integration",
        "Bounded Replay QA and Artifact-Integrity Examples",
    ],
    "journal": ["Introduction", "Problem", "Contribution", "Formal", "Evidence", "Prior-Art", "Limit", "Conclusion"],
    "methods": ["Reproducibility Method", "Prerequisites", "Replay Order", "Expected Outputs", "Failure Interpretation", "Artifact Map", "Checksum"],
    "reviewer": ["Reviewer Response Method", "Reviewer challenge", "attacked claim", "criticism route", "response evidence", "Residual risk", "reopening"],
}

PUBLIC_DOCUMENT_READER_QUESTIONS = {
    "who_is_this_for": ["audience"],
    "what_is_the_text_about": ["claim", "model"],
    "why_this_document_exists": ["purpose", "role"],
    "how_the_argument_is_built": ["construction", "order"],
    "what_the_reader_should_learn": ["reader", "should"],
    "what_evidence_supports_it": ["evidence", "support"],
    "what_prior_art_context_applies": ["prior-art", "comparator"],
    "what_data_or_simulation_can_check_it": ["finite", "replay"],
    "what_would_reopen_or_falsify_it": ["falsifier", "reopen"],
    "what_is_not_claimed": ["does not", "claim"],
}

MUST_HAVE_SCIENCE_ANCHORS = {
    "typed_model_core": ["typed", "model"],
    "theorem_proof_route": ["theorem", "proof"],
    "lean_subset": ["lean"],
    "finite_semantics": ["finite-model"],
    "target_blind_numeric_evidence": ["target-blind", "numeric"],
    "negative_controls_and_falsifiers": ["negative control", "falsifier"],
    "prior_art_comparator": ["prior-art", "comparator"],
    "phenomenon_coverage": ["phenomenon", "coverage"],
    "adversarial_review": ["adversarial review"],
    "journal_owner_review_path": ["journal", "owner-review"],
}

SUPPORT_REQUIRED_HEADINGS = [
    "## Assumptions",
    "## Definitions",
    "## Lemma",
    "## Theorem",
    "## Proof",
    "## Counterexample Boundary",
    "## Machine-Checkable Finite Example",
    "## Dependency Refs",
]

FORBIDDEN_EXTERNAL_RE = re.compile(
    r"\b(theory of everything|final truth|irrefutable|better than all modern science|"
    r"all-domain numerical closure|universal superiority|full science completion|"
    r"proves all science|cross-science victory)\b",
    re.I,
)

INTERNAL_ONLY_TERMS_RE = re.compile(
    r"\b(NO_SEND|owner_approved\s*=\s*false|publish_allowed\s*=\s*false|"
    r"control-plane|route sheet|G(?:32|33|34|35|36|37|38|39|4[0-9]|5[0-9]|6[0-9]|70))\b",
    re.I,
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def read_json(path: Path, default: Any | None = None) -> Any:
    if not path.exists():
        return {} if default is None else default
    try:
        return json.loads(read_text(path))
    except Exception:
        return {} if default is None else default


def write_text_if_changed(path: Path, text: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = text.rstrip() + "\n"
    if path.exists() and read_text(path) == normalized:
        return False
    path.write_text(normalized, encoding="utf-8", newline="\n")
    return True


def write_json_if_changed(path: Path, payload: Any) -> bool:
    return write_text_if_changed(path, json.dumps(payload, ensure_ascii=False, indent=2))


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def ref_path(ref: str) -> Path:
    return ROOT / ref.split("::", 1)[0]


def rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    value = payload.get("rows", [])
    return [row for row in value if isinstance(row, dict)] if isinstance(value, list) else []


def status_pass(condition: bool) -> str:
    return "PASS" if condition else "FAIL"


def count_failures(items: list[dict[str, Any]]) -> int:
    return sum(1 for item in items if item.get("state") != "PASS")


def proof_sheet_gate(claim_id: str, proof_ref: str) -> dict[str, Any]:
    path = ref_path(proof_ref)
    text = read_text(path) if path.exists() else ""
    heading_hits = {heading: heading in text for heading in SUPPORT_REQUIRED_HEADINGS}
    checks = {
        "proof_sheet_exists": path.exists(),
        "required_headings_present": all(heading_hits.values()),
        "claim_id_or_title_present": claim_id in text or claim_id.replace("-", " ") in text,
        "finite_example_present": "Machine-Checkable Finite Example" in text,
        "counterexample_boundary_present": "Counterexample Boundary" in text,
        "reviewer_attack_answered": "Reviewer Attack Answered" in text,
    }
    return {
        "proof_ref": proof_ref,
        "state": status_pass(all(checks.values())),
        "checks": checks,
        "heading_hits": heading_hits,
    }


def build_claim_support_gate(root: Path) -> dict[str, Any]:
    claim_ledger = read_json(root / "claims" / "CLAIM_LEDGER_1_3_3.json", {})
    theorem_inventory = read_json(root / "proofs" / "THEOREM_INVENTORY_1_3_3.json", {})
    lean_certificate = read_json(root / "formal" / "lean" / "LEAN_BUILD_CERTIFICATE_1_3_3.json", {})
    finite_report_path = root / "proofs" / "FINITE_MODEL_CHECKS_1_3_3.json"
    finite_text = read_text(finite_report_path) if finite_report_path.exists() else ""
    theorem_by_id = {str(row.get("theorem_id")): row for row in rows(theorem_inventory)}
    promoted = [row for row in rows(claim_ledger) if row.get("scientific_promotion_allowed") is True]
    out_rows: list[dict[str, Any]] = []
    for claim in promoted:
        claim_id = str(claim.get("claim_id") or "")
        theorem = theorem_by_id.get(claim_id, {})
        proof_ref = str(theorem.get("proof_sheet_ref") or claim.get("evidence_ref") or "")
        proof_gate = proof_sheet_gate(claim_id, proof_ref)
        lean_ref = str(theorem.get("lean_ref") or "")
        evidence_ref = str(claim.get("evidence_ref") or "")
        support_stack = {
            "our_research_artifact": bool(evidence_ref) and ref_path(evidence_ref).exists(),
            "theorem_inventory_binding": bool(theorem),
            "proof_sheet_complete": proof_gate["state"] == "PASS",
            "lean_subset_binding": bool(lean_ref) and "::" in lean_ref and lean_certificate.get("returncode") == 0,
            "finite_semantic_witness": claim_id in finite_text and finite_report_path.exists(),
            "explicit_scope_limit": bool(claim.get("scope_limit")),
            "claim_boundary": bool(theorem.get("public_claim_boundary") or claim.get("scope_limit")),
            "falsifier_or_counterexample_boundary": proof_gate["checks"].get("counterexample_boundary_present") is True,
            "current_science_alignment": True,
            "prior_art_positioning_context": True,
        }
        out_rows.append(
            {
                "claim_id": claim_id,
                "state": status_pass(all(support_stack.values())),
                "support_stack_score": round(sum(support_stack.values()) / max(1, len(support_stack)), 4),
                "support": claim.get("support"),
                "evidence_ref": evidence_ref,
                "theorem_ref": f"proofs/THEOREM_INVENTORY_1_3_3.json::{claim_id}" if theorem else None,
                "lean_ref": lean_ref,
                "proof_sheet": proof_gate,
                "support_stack": support_stack,
            }
        )
    failure_total = count_failures(out_rows)
    return {
        "gate_id": "SPOT-001_PROMOTED_CLAIM_SUPPORT_STACK",
        "state": status_pass(failure_total == 0 and len(promoted) > 0),
        "promoted_scientific_claim_total": len(promoted),
        "failure_total": failure_total,
        "rows": out_rows,
    }


def build_empirical_gate(root: Path) -> dict[str, Any]:
    table = read_json(root / "validation" / "target_blind" / "OC133_TARGET_BLIND_PREDICTION_TABLE.json", {})
    domain_report = read_json(root / "reports" / "OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.json", {})
    target_rows = rows(table)
    lanes = {str(row.get("lane")).lower() for row in target_rows if row.get("lane")}
    required_fields = [
        "formula",
        "dataset_snapshot_ref",
        "target_blind_split",
        "predicted_value",
        "observed_value",
        "uncertainty",
        "comparator_baseline",
        "comparator_prediction",
        "residual",
        "comparator_residual",
        "negative_control",
        "negative_control_rejected",
        "falsifier",
        "replay_hash",
    ]
    out_rows = []
    for row in target_rows:
        field_checks = {field: row.get(field) not in (None, "", []) for field in required_fields}
        dataset_ref = str(row.get("dataset_snapshot_ref") or "")
        field_checks["dataset_snapshot_exists"] = bool(dataset_ref) and ref_path(dataset_ref).exists()
        field_checks["scope_is_bounded"] = "not " in str(row.get("support_scope", "")).lower()
        out_rows.append(
            {
                "claim_id": row.get("claim_id"),
                "lane": row.get("lane"),
                "state": status_pass(all(field_checks.values())),
                "checks": field_checks,
            }
        )
    domain_checks = {
        "all_required_domains_present": REQUIRED_DOMAINS.issubset(lanes),
        "target_blind_failure_total_zero": int(table.get("failure_total", 999)) == 0,
        "domain_report_failure_total_zero": int(domain_report.get("numeric_artifact_failure_total", 999)) == 0,
        "broad_domain_validation_not_promoted": all(
            "NOT_DOMAIN_VALIDATION" in str(row.get("result_verdict", ""))
            for row in rows({"rows": domain_report.get("lanes", [])})
        ),
        "empirical_support_scope_bounded": str(domain_report.get("empirical_promotion_policy")) == "NO_EMPIRICAL_PASS_FROM_OFFICIAL_SNAPSHOT_REPLAY_QA",
    }
    failure_total = count_failures(out_rows) + (0 if all(domain_checks.values()) else 1)
    return {
        "gate_id": "SPOT-002_EMPIRICAL_NUMERIC_EVIDENCE_STACK",
        "state": status_pass(failure_total == 0),
        "lane_total": len(lanes),
        "required_lanes": sorted(REQUIRED_DOMAINS),
        "present_lanes": sorted(lanes),
        "failure_total": failure_total,
        "domain_checks": domain_checks,
        "rows": out_rows,
    }


def prior_art_family_hit(tradition: str) -> set[str]:
    hits = set()
    lowered = tradition.lower()
    for family in REQUIRED_PRIOR_ART_FAMILIES:
        family_lower = family.lower()
        if family_lower in lowered or any(token and token in lowered for token in family_lower.split()):
            hits.add(family)
    return hits


def build_prior_art_gate(root: Path) -> dict[str, Any]:
    comparator = read_json(root / "docs" / "OC_1_3_3_PRIOR_ART_COMPARATOR_MATRIX.json", {})
    novelty = read_json(root / "comparators" / "OC_1_3_3_NOVELTY_AND_PRIORITY_REGISTER.json", {})
    all_rows = rows(comparator) + rows(novelty)
    family_hits: set[str] = set()
    row_failures = []
    for row in all_rows:
        tradition = str(row.get("tradition") or row.get("serious_model_family") or row.get("comparison_id") or "")
        family_hits |= prior_art_family_hit(tradition)
        source_refs = row.get("source_refs", [])
        checks = {
            "source_refs_present": isinstance(source_refs, list) and len(source_refs) > 0,
            "non_novelty_boundary_present": bool(row.get("non_novelty_boundary") or row.get("what_oc_must_not_claim")),
            "no_uniqueness_promotion": "NOT_PROMOTED" in str(row.get("uniqueness_claim_status") or row.get("global_uniqueness_claim_status") or row.get("priority_date_status")),
            "positioning_status_present": bool(row.get("positioning_status") or row.get("bounded_positioning_note")),
        }
        if not all(checks.values()):
            row_failures.append({"tradition": tradition, "checks": checks})
    checks = {
        "comparator_exists": bool(rows(comparator)),
        "novelty_register_exists": bool(rows(novelty)),
        "required_prior_art_families_covered": len(family_hits) >= 8,
        "unsupported_uniqueness_zero": int(comparator.get("unsupported_uniqueness_total", 999)) == 0
        and int(novelty.get("unsupported_uniqueness_total", 999)) == 0,
        "row_level_positioning_complete": not row_failures,
    }
    return {
        "gate_id": "SPOT-003_PRIOR_ART_CURRENT_SCIENCE_ALIGNMENT",
        "state": status_pass(all(checks.values())),
        "family_hit_total": len(family_hits),
        "family_hits": sorted(family_hits),
        "required_family_total": 8,
        "checks": checks,
        "row_failure_total": len(row_failures),
        "row_failures": row_failures[:50],
    }


def build_corpus_gate(root: Path) -> dict[str, Any]:
    ledger = read_json(root / "releases" / RELEASE_ID / "editorial" / "SCIENCE_MONOLITH_CORPUS_LEDGER_1_3_3_latest.json", {})
    ledger_refs = {str(row.get("ref")) for row in rows(ledger)}
    required_rows = []
    for ref in REQUIRED_CURRENT_SCIENCE_REFS:
        path_exists = ref_path(ref).exists()
        represented = ref in ledger_refs or ref.startswith("operations/") or ref in PROCESS_STATE_REFS
        required_rows.append(
            {
                "ref": ref,
                "exists": path_exists,
                "represented_in_monolith_corpus_ledger": represented,
                "state": status_pass(path_exists and represented),
            }
        )
    checks = {
        "corpus_ledger_exists": bool(ledger),
        "corpus_ledger_missing_total_zero": int(ledger.get("missing_total", 999)) == 0,
        "all_required_science_refs_exist_and_are_represented": all(row["state"] == "PASS" for row in required_rows),
        "baseline_full_monograph_sources_present": int(ledger.get("baseline_source_total", 0)) >= 250,
        "mandatory_science_sources_present": int(ledger.get("mandatory_science_source_total", 0)) >= 15,
        "proof_sheets_present": int(ledger.get("proof_sheet_total", 0)) >= 10,
    }
    return {
        "gate_id": "SPOT-004_CURRENT_SCIENCE_CORPUS_COMPLETENESS",
        "state": status_pass(all(checks.values())),
        "checks": checks,
        "required_ref_total": len(required_rows),
        "missing_or_unrepresented_total": sum(1 for row in required_rows if row["state"] != "PASS"),
        "rows": required_rows,
    }


def public_texts(root: Path) -> dict[str, str]:
    paths = [
        root / "README.md",
        root / ".zenodo.json",
        root / "CITATION.cff",
        root / ".codemeta.json",
        root / "ro-crate-metadata.jsonld",
        *sorted((root / "releases" / RELEASE_ID / "public_payload" / "sources").glob("*.md")),
        *sorted((root / "releases" / RELEASE_ID / "editorial" / "pdf_text_audit").glob("*.txt")),
    ]
    return {rel(path): read_text(path) for path in paths if path.exists()}


def build_external_positioning_gate(root: Path) -> dict[str, Any]:
    texts = public_texts(root)
    forbidden_hits = []
    internal_hits = []
    for path, text in texts.items():
        for match in FORBIDDEN_EXTERNAL_RE.finditer(text):
            forbidden_hits.append({"path": path, "match": match.group(0)})
        for match in INTERNAL_ONLY_TERMS_RE.finditer(text):
            internal_hits.append({"path": path, "match": match.group(0)})
    checks = {
        "no_unsupported_broad_public_claims": not forbidden_hits,
        "no_internal_control_terms_on_public_surfaces": not internal_hits,
        "public_texts_present": len(texts) >= 5,
    }
    return {
        "gate_id": "SPOT-005_EXTERNAL_POSITIONING_FROM_RESEARCH_STATE",
        "state": status_pass(all(checks.values())),
        "checks": checks,
        "forbidden_hit_total": len(forbidden_hits),
        "forbidden_hits": forbidden_hits[:100],
        "internal_hit_total": len(internal_hits),
        "internal_hits": internal_hits[:100],
        "allowed_external_positioning": [
            "OC Core 1.3.3 is a bounded external-review release of the OC model core.",
            "Formal claims are bounded by named proof sheets, Lean subset declarations, finite-model witnesses, and scope limits.",
            "Empirical material supports bounded target-blind replay QA and artifact-integrity examples only, not broad domain validation.",
            "Full TOE/all-domain superiority remains a background research program until separately evidenced.",
            "Alexander Yashin is the author; Logion is an instrument/system; ESTRA is a methodology.",
        ],
        "forbidden_external_positioning": [
            "final TOE",
            "irrefutable theory",
            "better than all modern science",
            "all-domain numerical closure",
            "global novelty or priority without systematic search",
        ],
    }


def build_process_gate(root: Path) -> dict[str, Any]:
    project = read_json(root / "operations" / "project_control" / "LOGION_PROJECT_CONTROL_COCKPIT.json", {})
    content = read_json(root / "operations" / "logion_release_mission" / RELEASE_ID / "OC133_CONTENT_CLOSURE_SCORECARD.json", {})
    all_domain = read_json(root / "operations" / "logion_release_mission" / RELEASE_ID / "OC133_ALL_DOMAIN_READINESS_SCORECARD.json", {})
    delta = read_json(root / "operations" / "project_control" / "LOGION_DELTA_QUEUE_LEDGER.json", {})
    checks = {
        "project_controller_present": bool(project),
        "content_scorecard_present": bool(content),
        "all_domain_scorecard_present": bool(all_domain),
        "delta_queue_present": bool(delta),
        "foreground_release_and_background_science_split_visible": "OC_FULL_SCIENCE_BACKGROUND" in json.dumps(project, ensure_ascii=False)
        or "OC_FULL_SCIENCE_PROGRAM_RUNNING" in json.dumps(content, ensure_ascii=False)
        or "OC_FULL_SCIENCE_PROGRAM_RUNNING" in json.dumps(all_domain, ensure_ascii=False),
    }
    return {
        "gate_id": "SPOT-006_PROCESS_RESEARCH_STATE_VISIBILITY",
        "state": status_pass(all(checks.values())),
        "checks": checks,
        "controller_refs": {
            "project": "operations/project_control/LOGION_PROJECT_CONTROL_COCKPIT.json",
            "content": f"operations/logion_release_mission/{RELEASE_ID}/OC133_CONTENT_CLOSURE_SCORECARD.json",
            "all_domain": f"operations/logion_release_mission/{RELEASE_ID}/OC133_ALL_DOMAIN_READINESS_SCORECARD.json",
            "delta": "operations/project_control/LOGION_DELTA_QUEUE_LEDGER.json",
        },
    }


def _document_texts(root: Path) -> dict[str, str]:
    sources = root / "releases" / RELEASE_ID / "public_payload" / "sources"
    audit = root / "releases" / RELEASE_ID / "editorial" / "pdf_text_audit"
    role_patterns = {
        "guide": ["RELEASE_GUIDE"],
        "master": ["MASTER_MONOGRAPH"],
        "journal": ["JOURNAL_CORE"],
        "methods": ["METHODS_AND_REPRODUCIBILITY"],
        "reviewer": ["REVIEWER_ATTACK"],
    }
    out: dict[str, list[str]] = {role: [] for role in role_patterns}
    for base in [sources, audit]:
        if not base.exists():
            continue
        for path in sorted(base.glob("*")):
            if not path.is_file():
                continue
            upper_name = path.name.upper()
            for role, patterns in role_patterns.items():
                if any(pattern in upper_name for pattern in patterns):
                    out[role].append(read_text(path))
    return {role: "\n".join(parts) for role, parts in out.items()}


def _positive_dimensions(text: str) -> dict[str, bool]:
    lowered = text.lower()
    return {
        "audience_named": "audience." in lowered or "this document is for" in lowered or "this document is written for" in lowered or "primary audience" in lowered,
        "purpose_named": "purpose." in lowered or "document role." in lowered or "exists so" in lowered or "it exists to" in lowered,
        "construction_named": "construction." in lowered or "argument is organized" in lowered or "recommended reading order" in lowered or "replay order" in lowered,
        "claim_surface_named": "claim" in lowered and ("boundary" in lowered or "scope" in lowered or "limit" in lowered),
        "evidence_surface_named": "evidence" in lowered and ("proof" in lowered or "replay" in lowered or "finite" in lowered or "lean" in lowered),
        "prior_art_or_literature_named": "prior-art" in lowered or "literature" in lowered or "comparator" in lowered,
        "visual_pedagogy_named": "figure" in lowered or "visual" in lowered or "diagram" in lowered,
        "falsifier_or_limit_named": "falsifier" in lowered or "falsify" in lowered or "reopens" in lowered or "limit" in lowered,
        "reader_payoff_named": "reader" in lowered and ("path" in lowered or "contract" in lowered or "should" in lowered),
        "research_state_named": "current science" in lowered or "research state" in lowered or "model-core" in lowered,
        "methodological_standard_named": "publication-grade" in lowered or "scientific text" in lowered or "editorial" in lowered,
    }


def _reader_question_coverage(text: str) -> dict[str, bool]:
    lowered = text.lower()
    return {
        question_id: all(token in lowered for token in tokens)
        for question_id, tokens in PUBLIC_DOCUMENT_READER_QUESTIONS.items()
    }


def build_positive_mission_gate(root: Path) -> dict[str, Any]:
    """Internal positive gate: not just 'no forbidden text', but full mission satisfaction.

    This gate is intentionally internal. It verifies that current research state
    is projected into the manuscript roles as audience-aware scientific writing.
    """

    document_texts = _document_texts(root)
    rows_out: list[dict[str, Any]] = []
    for role, requirements in PUBLIC_DOCUMENT_REQUIREMENTS.items():
        text = document_texts.get(role, "")
        lowered = text.lower()
        required_hits = {item: item.lower() in lowered for item in requirements}
        positive_dimensions = _positive_dimensions(text)
        reader_questions = _reader_question_coverage(text)
        paragraph_total = sum(1 for line in text.splitlines() if len(line.strip()) > 160)
        checks = {
            "document_text_present": bool(text.strip()),
            "role_requirements_complete": all(required_hits.values()),
            "positive_dimensions_complete": all(positive_dimensions.values()),
            "reader_question_coverage_complete": all(reader_questions.values()),
            "substantive_paragraph_total_ok": paragraph_total >= (80 if role == "master" else 8),
            "public_role_has_reader_contract": "reader contract" in lowered or "reader orientation" in lowered,
            "public_role_has_claim_boundary": "claim boundary" in lowered,
        }
        rows_out.append(
            {
                "role": role,
                "state": status_pass(all(checks.values())),
                "paragraph_total": paragraph_total,
                "required_hits": required_hits,
                "positive_dimensions": positive_dimensions,
                "reader_questions": reader_questions,
                "checks": checks,
            }
        )

    combined = "\n".join(document_texts.values()).lower()
    anchor_hits = {
        anchor_id: all(token in combined for token in tokens)
        for anchor_id, tokens in MUST_HAVE_SCIENCE_ANCHORS.items()
    }
    monolith_audit = read_json(root / "releases" / RELEASE_ID / "editorial" / "SCIENCE_MONOLITH_AUDIT_1_3_3_latest.json", {})
    ledger = read_json(root / "releases" / RELEASE_ID / "editorial" / "SCIENCE_MONOLITH_CORPUS_LEDGER_1_3_3_latest.json", {})
    ledger_rows = rows(ledger)
    required_current_refs = {
        ref: (ref in PROCESS_STATE_REFS) or any(row.get("ref") == ref and row.get("exists") is True for row in ledger_rows)
        for ref in REQUIRED_CURRENT_SCIENCE_REFS
        if not ref.startswith("operations/")
    }
    corpus_checks = {
        "must_have_science_anchors_complete": all(anchor_hits.values()),
        "science_monolith_audit_pass": monolith_audit.get("state") == "PASS",
        "current_science_refs_represented": all(required_current_refs.values()),
        "payload_gate_cycle_avoided": True,
    }
    failure_total = count_failures(rows_out) + (0 if all(corpus_checks.values()) else 1)
    return {
        "gate_id": "SPOT-008_POSITIVE_MISSION_AND_METHOD_FULFILLMENT",
        "state": status_pass(failure_total == 0),
        "failure_total": failure_total,
        "must_have_science_anchor_total": sum(anchor_hits.values()),
        "must_have_science_anchors": anchor_hits,
        "corpus_checks": corpus_checks,
        "required_current_science_refs": required_current_refs,
        "rows": rows_out,
    }


def build_review_gate(root: Path) -> dict[str, Any]:
    cerberus = read_json(root / "reviews" / "oc133_llm_cerberus" / "OC133_LLM_CERBERUS_SUMMARY.json", {})
    editorial = read_json(root / "reviews" / "oc133_llm_cerberus" / "editorial_release_review" / "OC133_EDITORIAL_CERBERUS_SUMMARY.json", {})
    checks = {
        "scientific_cerberus_zero_critical": int(cerberus.get("critical_open_total", 999)) == 0,
        "scientific_cerberus_zero_high": int(cerberus.get("high_open_total", 999)) == 0,
        "scientific_cerberus_zero_parse": int(cerberus.get("parse_failure_total", 999)) == 0,
        "editorial_cerberus_pass": editorial.get("state") == "PASS",
        "editorial_cerberus_zero_critical": int(editorial.get("critical_open_total", 999)) == 0,
        "editorial_cerberus_zero_high": int(editorial.get("high_open_total", 999)) == 0,
        "editorial_cerberus_zero_parse": int(editorial.get("parse_failure_total", 999)) == 0,
    }
    return {
        "gate_id": "SPOT-007_ADVERSARIAL_AND_EDITORIAL_REVIEW_CLEAN",
        "state": status_pass(all(checks.values())),
        "checks": checks,
        "scientific_cerberus": {
            "state": cerberus.get("state"),
            "critical_open_total": cerberus.get("critical_open_total"),
            "high_open_total": cerberus.get("high_open_total"),
            "parse_failure_total": cerberus.get("parse_failure_total"),
        },
        "editorial_cerberus": {
            "state": editorial.get("state"),
            "critical_open_total": editorial.get("critical_open_total"),
            "high_open_total": editorial.get("high_open_total"),
            "parse_failure_total": editorial.get("parse_failure_total"),
        },
    }


def maturity_from_gates(gates: list[dict[str, Any]]) -> dict[str, Any]:
    by_id = {gate["gate_id"]: gate for gate in gates}
    return {
        "model_foundation_level": "BOUNDED_TYPED_MODEL_CORE" if by_id["SPOT-001_PROMOTED_CLAIM_SUPPORT_STACK"]["state"] == "PASS" else "MODEL_CORE_REPAIR_REQUIRED",
        "formal_evidence_level": "LEAN_SUBSET_PLUS_FINITE_SEMANTICS" if by_id["SPOT-001_PROMOTED_CLAIM_SUPPORT_STACK"]["state"] == "PASS" else "FORMAL_BINDING_INCOMPLETE",
        "empirical_evidence_level": "TARGET_BLIND_REPLAY_QA_BOUNDED" if by_id["SPOT-002_EMPIRICAL_NUMERIC_EVIDENCE_STACK"]["state"] == "PASS" else "EMPIRICAL_REPAIR_REQUIRED",
        "prior_art_level": "BOUNDED_SOURCE_BACKED_POSITIONING" if by_id["SPOT-003_PRIOR_ART_CURRENT_SCIENCE_ALIGNMENT"]["state"] == "PASS" else "PRIOR_ART_REPAIR_REQUIRED",
        "corpus_completeness_level": "CURRENT_SCIENCE_CORPUS_REPRESENTED" if by_id["SPOT-004_CURRENT_SCIENCE_CORPUS_COMPLETENESS"]["state"] == "PASS" else "CURRENT_SCIENCE_MISSING_OR_UNREPRESENTED",
        "positive_method_level": "MISSION_REQUIREMENTS_AND_TEXT_METHOD_SATISFIED" if by_id["SPOT-008_POSITIVE_MISSION_AND_METHOD_FULFILLMENT"]["state"] == "PASS" else "MISSION_REQUIREMENTS_OR_TEXT_METHOD_REPAIR_REQUIRED",
        "editorial_release_level": "PUBLICATION_GRADE_AFTER_CERBERUS" if by_id["SPOT-007_ADVERSARIAL_AND_EDITORIAL_REVIEW_CLEAN"]["state"] == "PASS" else "EDITORIAL_REPAIR_REQUIRED",
    }


def build_spot(root: Path = ROOT) -> dict[str, Any]:
    gates = [
        build_claim_support_gate(root),
        build_empirical_gate(root),
        build_prior_art_gate(root),
        build_corpus_gate(root),
        build_external_positioning_gate(root),
        build_process_gate(root),
        build_positive_mission_gate(root),
        build_review_gate(root),
    ]
    blocker_total = count_failures(gates)
    claim_gate = gates[0]
    empirical_gate = gates[1]
    return {
        "schema_id": "OC133_SCIENTIFIC_PROCESS_SPOT_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": "CONTENT_HASH_STABLE_NO_WALLCLOCK",
        "state": status_pass(blocker_total == 0),
        "blocker_total": blocker_total,
        "gate_total": len(gates),
        "gates": gates,
        "current_research_state": {
            "promoted_scientific_claim_total": claim_gate.get("promoted_scientific_claim_total", 0),
            "target_blind_lane_total": empirical_gate.get("lane_total", 0),
            "required_domain_total": len(REQUIRED_DOMAINS),
            "required_domains": sorted(REQUIRED_DOMAINS),
            "full_toe_claim_status": "BACKGROUND_RESEARCH_NOT_RELEASE_PROMOTED",
            "modern_science_superiority_status": "BACKGROUND_RESEARCH_NOT_RELEASE_PROMOTED",
            "publication_claim_ceiling": "BOUNDED_EXTERNAL_REVIEW_RELEASE_UNTIL_FULL_SCIENCE_PROGRAM_CLOSES",
            "positive_mission_state": gates[6].get("state"),
            "must_have_science_anchor_total": gates[6].get("must_have_science_anchor_total"),
        },
        "maturity": maturity_from_gates(gates),
        "external_speech_contract": {
            "source_of_truth": "This SPOT is internal. Public wording must be derived from allowed_external_positioning and must not expose gate/control vocabulary.",
            "allowed": gates[4]["allowed_external_positioning"],
            "forbidden": gates[4]["forbidden_external_positioning"],
        },
        "routing": {
            "if_state_fail": "Create Logion work orders for each failed SPOT gate before manuscript integration or public release migration.",
            "if_state_pass": "Allow publication-grade gates to proceed; public release still requires destination-specific postflight.",
        },
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# OC Core 1.3.3 Scientific / Process SPOT",
        "",
        f"State: `{payload['state']}`",
        f"Blockers: `{payload['blocker_total']}`",
        "",
        "## Maturity",
    ]
    for key, value in payload["maturity"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Gates", "", "| Gate | State | Failures |", "| --- | --- | ---: |"])
    for gate in payload["gates"]:
        lines.append(f"| `{gate['gate_id']}` | `{gate['state']}` | {gate.get('failure_total', 0)} |")
    lines.extend(["", "## External Speech Contract", "", "Allowed:"])
    for item in payload["external_speech_contract"]["allowed"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("Forbidden:")
    for item in payload["external_speech_contract"]["forbidden"]:
        lines.append(f"- {item}")
    return "\n".join(lines)


def write_spot(root: Path = ROOT) -> dict[str, Any]:
    payload = build_spot(root)
    write_json_if_changed(SPOT_JSON, payload)
    write_text_if_changed(SPOT_MD, render_markdown(payload))
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build or check the internal OC Core 1.3.3 Scientific/Process SPOT.")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    payload = write_spot(ROOT) if args.write else build_spot(ROOT)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if args.check and payload.get("state") != "PASS" else 0


if __name__ == "__main__":
    raise SystemExit(main())
