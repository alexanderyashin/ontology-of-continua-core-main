from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from oc_core_release_assembly_lib import ASSEMBLY_ROOT, artifact_hash, stable_json, validation_result


QUALITY_DIR = ASSEMBLY_ROOT / "quality_parameterization"
CATALOG_STATUS = "OC_CORE_QUALITY_METRIC_CATALOG_READY"


STANDARD_SOURCES = [
    {
        "source_id": "nature_reporting_data_code_protocols",
        "title": "Nature Communications reporting standards and availability of data, materials, code and protocols",
        "url": "https://www.nature.com/ncomms/editorial-policies/reporting-standards",
        "requirements": ["replicability", "data availability", "code availability", "protocol availability", "transparent restrictions"],
    },
    {
        "source_id": "icmje_recommendations",
        "title": "ICMJE Recommendations",
        "url": "https://www.icmje.org/recommendations/",
        "requirements": ["authorship accountability", "manuscript responsibility", "AI-use boundary", "conflicts", "ethical reporting"],
    },
    {
        "source_id": "top_guidelines",
        "title": "Transparency and Openness Promotion Guidelines",
        "url": "https://incentivizingopen.org/projects2/transparency-and-openness-promotion-top-guidelines/",
        "requirements": ["data transparency", "analytic transparency", "materials transparency", "preregistration", "replication openness"],
    },
    {
        "source_id": "logion_toe_grade_internal_standard",
        "title": "Logion TOE-grade positive and negative release-quality standard",
        "url": "internal://logion/release_assembly/oc_core/text_fill_rules",
        "requirements": ["claim traceability", "reader payoff", "no overclaim", "delta-only remediation", "artifact role fidelity"],
    },
]


METRICS = [
    {
        "metric_id": "coverage.target_obligation",
        "family": "scientific_validity",
        "label": "Target obligation coverage",
        "polarity": "positive",
        "default_weight": 1.0,
        "default_mode": "auto_plus_manual",
        "default_scorer_id": "l10_coverage_status_scorer",
        "required_for_all_l10": True,
        "full_coverage_rule": "The L10 obligation has complete, partial, planned, missing, or not_assessed status with reason and source route.",
        "parameterization_rule": "Map aggregator coverage_status and mapping-quality row to a numeric coverage score; not_assessed remains unscored.",
        "thresholds": {"pass_min": 0.85, "warn_min": 0.6},
        "evidence_fields": ["coverage_status", "source_family_ids", "auto_quality_index"],
        "standard_source_ids": ["logion_toe_grade_internal_standard", "top_guidelines"],
    },
    {
        "metric_id": "trace.exact_source_binding",
        "family": "claim_evidence_trace",
        "label": "Exact source and provenance binding",
        "polarity": "positive",
        "default_weight": 1.0,
        "default_mode": "auto",
        "default_scorer_id": "source_family_binding_scorer",
        "required_for_all_l10": True,
        "full_coverage_rule": "Every claim-bearing or explanatory slot has exact source family candidates and later exact artifact paths.",
        "parameterization_rule": "Score source_family_ids, extraction_rule, integration_rule, and verification_rule completeness.",
        "thresholds": {"pass_min": 0.9, "warn_min": 0.7},
        "evidence_fields": ["source_family_ids", "extraction_rule", "integration_rule", "verification_rule"],
        "standard_source_ids": ["nature_reporting_data_code_protocols", "top_guidelines", "logion_toe_grade_internal_standard"],
    },
    {
        "metric_id": "claim.boundary_discipline",
        "family": "claim_evidence_trace",
        "label": "Claim boundary discipline",
        "polarity": "negative_guard",
        "default_weight": 1.0,
        "default_mode": "auto_plus_manual",
        "default_scorer_id": "claim_boundary_scorer",
        "required_for_all_l10": True,
        "full_coverage_rule": "The node states what may and may not be claimed from its support route.",
        "parameterization_rule": "Score claim_boundary specificity and scan generated artifact text for stronger language than supported.",
        "thresholds": {"forbidden_hit_max": 0, "pass_min": 0.95},
        "evidence_fields": ["claim_boundary", "artifact_text_scan_hits"],
        "standard_source_ids": ["icmje_recommendations", "logion_toe_grade_internal_standard"],
    },
    {
        "metric_id": "formal.proof_binding",
        "family": "formal_proof",
        "label": "Formal theorem/proof binding",
        "polarity": "positive",
        "default_weight": 0.9,
        "default_mode": "auto_plus_manual",
        "default_scorer_id": "formal_artifact_binding_scorer",
        "argument_roles": ["proof_evidence"],
        "title_patterns": ["theorem", "proof", "lean", "formal", "typed", "finite"],
        "source_family_patterns": ["formal", "machine_checked", "finite"],
        "full_coverage_rule": "Formal claims cite theorem/proof/Lean/finite-model evidence or are explicitly demoted.",
        "parameterization_rule": "Require theorem/proof artifact references for proof-bearing nodes; waive for non-formal nodes.",
        "thresholds": {"pass_min": 0.9, "warn_min": 0.7},
        "evidence_fields": ["theorem_ids", "proof_sheet_refs", "lean_refs", "finite_model_case_ids"],
        "standard_source_ids": ["logion_toe_grade_internal_standard"],
    },
    {
        "metric_id": "empirical.protocol_support",
        "family": "empirical_support",
        "label": "Empirical or computational protocol support",
        "polarity": "positive",
        "default_weight": 0.9,
        "default_mode": "auto_plus_manual",
        "default_scorer_id": "empirical_protocol_scorer",
        "argument_roles": ["proof_evidence"],
        "title_patterns": ["empirical", "validation", "simulation", "domain", "target-blind", "held-out", "evidence"],
        "source_family_patterns": ["empirical", "computational", "reproducibility"],
        "full_coverage_rule": "Empirical nodes declare formula, comparator, uncertainty/residual, negative control, falsifier, and replay hash when promoted.",
        "parameterization_rule": "Score protocol fields when empirical support is required; otherwise waive with reason.",
        "thresholds": {"pass_min": 0.9, "warn_min": 0.7},
        "evidence_fields": ["formula", "comparator", "uncertainty", "residual", "negative_control", "falsifier", "replay_hash"],
        "standard_source_ids": ["nature_reporting_data_code_protocols", "top_guidelines"],
    },
    {
        "metric_id": "didactic.reader_task_payoff",
        "family": "didactics",
        "label": "Reader task and payoff",
        "polarity": "positive",
        "default_weight": 0.85,
        "default_mode": "auto_plus_manual",
        "default_scorer_id": "reader_task_scorer",
        "required_for_text_l10": True,
        "full_coverage_rule": "The node tells the reader what to understand or do and why it matters in the argument.",
        "parameterization_rule": "Score reader_task presence, specificity, and downstream paragraph payoff.",
        "thresholds": {"pass_min": 0.85, "warn_min": 0.65},
        "evidence_fields": ["reader_task", "paragraph_payoff"],
        "standard_source_ids": ["logion_toe_grade_internal_standard"],
    },
    {
        "metric_id": "style.publication_grade_prose",
        "family": "style",
        "label": "Publication-grade prose and terminology",
        "polarity": "negative_guard",
        "default_weight": 0.8,
        "default_mode": "auto_plus_llm",
        "default_scorer_id": "publication_grade_text_scorer",
        "required_for_text_l10": True,
        "full_coverage_rule": "Generated prose is coherent, edited, terminology-stable, and not raw ledger/control text.",
        "parameterization_rule": "Scan generated text for placeholders, repeated boilerplate, control-plane language, malformed notation, and rough style.",
        "thresholds": {"forbidden_hit_max": 0, "boilerplate_ratio_max": 0.08},
        "evidence_fields": ["text_extract", "forbidden_hits", "boilerplate_ratio", "terminology_hits"],
        "standard_source_ids": ["icmje_recommendations", "logion_toe_grade_internal_standard"],
    },
    {
        "metric_id": "structure.sequence_transition",
        "family": "structure",
        "label": "Argument sequence and transition quality",
        "polarity": "positive",
        "default_weight": 0.75,
        "default_mode": "auto_plus_manual",
        "default_scorer_id": "sequence_transition_scorer",
        "required_for_all_l10": True,
        "full_coverage_rule": "The node preserves the frozen top-down sequence and has an explicit handoff where needed.",
        "parameterization_rule": "Score order_path consistency and transition role against surrounding nodes.",
        "thresholds": {"pass_min": 0.85, "warn_min": 0.65},
        "evidence_fields": ["order_path", "argument_role", "neighbor_transition"],
        "standard_source_ids": ["logion_toe_grade_internal_standard"],
    },
    {
        "metric_id": "visual.figure_table_operationalization",
        "family": "figures_tables",
        "label": "Figure/table operationalization",
        "polarity": "positive",
        "default_weight": 0.65,
        "default_mode": "manual_or_auto",
        "default_scorer_id": "figure_table_need_scorer",
        "title_patterns": ["figure", "table", "visual", "atlas", "map", "matrix"],
        "full_coverage_rule": "Visual/table-bearing nodes declare the intended operation, reader use, caption role, and source binding.",
        "parameterization_rule": "Apply to figure/table/atlas/matrix nodes; waive for prose-only nodes.",
        "thresholds": {"pass_min": 0.85, "warn_min": 0.65},
        "evidence_fields": ["figure_id", "table_id", "caption", "source_trace", "reader_task"],
        "standard_source_ids": ["nature_reporting_data_code_protocols", "logion_toe_grade_internal_standard"],
    },
    {
        "metric_id": "bibliography.prior_art_depth",
        "family": "bibliography_prior_art",
        "label": "Prior-art and literature depth",
        "polarity": "positive",
        "default_weight": 0.75,
        "default_mode": "auto_plus_manual",
        "default_scorer_id": "prior_art_depth_scorer",
        "title_patterns": ["prior art", "comparator", "novelty", "bibliography", "references", "literature"],
        "source_family_patterns": ["prior_art", "comparator"],
        "full_coverage_rule": "Prior-art nodes cite current scientific context, comparator method, overlap, residual delta, and limits.",
        "parameterization_rule": "Apply to prior-art/comparator/bibliography nodes; waive for frontmatter and purely formal nodes.",
        "thresholds": {"pass_min": 0.85, "warn_min": 0.65},
        "evidence_fields": ["reference_count", "comparator_rows", "novelty_register_refs"],
        "standard_source_ids": ["icmje_recommendations", "logion_toe_grade_internal_standard"],
    },
    {
        "metric_id": "artifact.role_hygiene",
        "family": "artifact_hygiene",
        "label": "Artifact role and file hygiene",
        "polarity": "negative_guard",
        "default_weight": 0.9,
        "default_mode": "auto",
        "default_scorer_id": "artifact_role_hygiene_scorer",
        "artifact_metric": True,
        "full_coverage_rule": "Each release artifact matches its role, exists, hashes cleanly, and has no stale/local/secret/control leakage.",
        "parameterization_rule": "Apply to package artifact rows, not prose-only L10 nodes.",
        "thresholds": {"missing_asset_max": 0, "leak_hit_max": 0},
        "evidence_fields": ["asset_path", "sha256", "size_bytes", "leak_scan"],
        "standard_source_ids": ["nature_reporting_data_code_protocols", "top_guidelines", "logion_toe_grade_internal_standard"],
    },
    {
        "metric_id": "public.no_overclaim_surface",
        "family": "public_surface_safety",
        "label": "No-overclaim and public-surface safety",
        "polarity": "negative_guard",
        "default_weight": 1.0,
        "default_mode": "auto_plus_llm",
        "default_scorer_id": "public_surface_safety_scorer",
        "required_for_all_l10": True,
        "full_coverage_rule": "Public surfaces do not claim final TOE/all-domain superiority unless the evidence literally supports it.",
        "parameterization_rule": "Scan claim_boundary and generated text; route broad unsupported claims to research obligations.",
        "thresholds": {"forbidden_hit_max": 0, "pass_min": 0.95},
        "evidence_fields": ["claim_boundary", "overclaim_hits", "external_positioning_contract"],
        "standard_source_ids": ["icmje_recommendations", "logion_toe_grade_internal_standard"],
    },
    {
        "metric_id": "repro.replay_trace",
        "family": "reproducibility",
        "label": "Reproducibility and replay trace",
        "polarity": "positive",
        "default_weight": 0.85,
        "default_mode": "auto",
        "default_scorer_id": "reproducibility_trace_scorer",
        "title_patterns": ["reproducibility", "replay", "checksums", "software", "data", "artifact", "traceability"],
        "source_family_patterns": ["reproducibility"],
        "full_coverage_rule": "Reproducibility nodes expose build/replay inputs, expected outputs, hashes, and failure interpretation.",
        "parameterization_rule": "Apply to reproducibility/data/software/artifact nodes; waive elsewhere with reason.",
        "thresholds": {"pass_min": 0.9, "warn_min": 0.7},
        "evidence_fields": ["command", "input_path", "output_path", "sha256", "failure_route"],
        "standard_source_ids": ["nature_reporting_data_code_protocols", "top_guidelines"],
    },
    {
        "metric_id": "review.resilience_response",
        "family": "reviewer_resilience",
        "label": "Reviewer resilience and objection closure",
        "polarity": "positive",
        "default_weight": 0.85,
        "default_mode": "auto_plus_llm",
        "default_scorer_id": "reviewer_resilience_scorer",
        "argument_roles": ["limits_falsifier", "synthesis_transition"],
        "title_patterns": ["review", "objection", "response", "falsifier", "limits", "risk", "caveat"],
        "source_family_patterns": ["review_attack", "limits"],
        "full_coverage_rule": "Reviewer-facing nodes state objection, threatened claim, evidence answer, residual risk, and reopening condition.",
        "parameterization_rule": "Apply to review/limits/falsifier nodes; waive for title metadata and purely definitional slots.",
        "thresholds": {"pass_min": 0.85, "warn_min": 0.65},
        "evidence_fields": ["objection", "response_evidence", "residual_risk", "reopen_condition"],
        "standard_source_ids": ["icmje_recommendations", "logion_toe_grade_internal_standard"],
    },
    {
        "metric_id": "metadata.identity_citation",
        "family": "metadata_identity",
        "label": "Identity, citation, authorship, instrument, and method metadata",
        "polarity": "positive",
        "default_weight": 0.8,
        "default_mode": "auto",
        "default_scorer_id": "metadata_identity_scorer",
        "title_patterns": ["title", "identity", "citation", "doi", "version", "author", "instrument", "method", "classification", "keyword"],
        "artifact_metric": True,
        "full_coverage_rule": "Identity nodes and metadata artifacts distinguish author, instrument, method, release version, citation, and license.",
        "parameterization_rule": "Apply to frontmatter/metadata nodes and citation artifacts; waive for scientific body paragraphs.",
        "thresholds": {"pass_min": 0.9, "warn_min": 0.7},
        "evidence_fields": ["author", "instrument", "method", "version", "doi", "license", "citation"],
        "standard_source_ids": ["icmje_recommendations", "logion_toe_grade_internal_standard"],
    },
]


def metric_catalog_paths() -> dict[str, Path]:
    return {
        "catalog_json": QUALITY_DIR / "OC_CORE_QUALITY_METRIC_CATALOG.json",
        "catalog_md": QUALITY_DIR / "OC_CORE_QUALITY_METRIC_CATALOG.md",
        "audit_json": QUALITY_DIR / "OC_CORE_QUALITY_METRIC_CATALOG_AUDIT.json",
        "audit_md": QUALITY_DIR / "OC_CORE_QUALITY_METRIC_CATALOG_AUDIT.md",
    }


def build_catalog_payload() -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_id": "OC_CORE_QUALITY_METRIC_CATALOG_v1",
        "artifact_kind": "OC_CORE_QUALITY_METRIC_CATALOG",
        "body_prose_included": False,
        "status": CATALOG_STATUS,
        "storage_policy": "JSON/MD canonical; SQLite is generated deterministic query cache only.",
        "standard_sources": STANDARD_SOURCES,
        "metric_total": len(METRICS),
        "metrics": METRICS,
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def validate_catalog(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if payload.get("status") != CATALOG_STATUS:
        failures.append("bad_status")
    metrics = payload.get("metrics", [])
    if payload.get("metric_total") != len(metrics) or len(metrics) < 12:
        failures.append("metric_total_too_low_or_mismatch")
    ids = [metric.get("metric_id") for metric in metrics]
    if len(ids) != len(set(ids)):
        failures.append("duplicate_metric_id")
    families = {metric.get("family") for metric in metrics}
    required = {
        "scientific_validity",
        "claim_evidence_trace",
        "formal_proof",
        "empirical_support",
        "didactics",
        "style",
        "structure",
        "figures_tables",
        "bibliography_prior_art",
        "artifact_hygiene",
        "public_surface_safety",
        "reproducibility",
        "reviewer_resilience",
    }
    missing_families = sorted(required - families)
    if missing_families:
        failures.append("missing_metric_families::" + ",".join(missing_families))
    for metric in metrics:
        for key in ["metric_id", "family", "label", "full_coverage_rule", "parameterization_rule", "thresholds", "evidence_fields", "standard_source_ids"]:
            if not metric.get(key):
                failures.append(f"metric_missing_{key}::{metric.get('metric_id')}")
    if payload.get("artifact_hash") != artifact_hash(payload):
        failures.append("artifact_hash_mismatch")
    return failures


def build_audit_payload(catalog: dict[str, Any]) -> dict[str, Any]:
    failures = validate_catalog(catalog)
    families: dict[str, int] = {}
    for metric in catalog["metrics"]:
        families[metric["family"]] = families.get(metric["family"], 0) + 1
    payload: dict[str, Any] = {
        "schema_id": "OC_CORE_QUALITY_METRIC_CATALOG_AUDIT_v1",
        "artifact_kind": "OC_CORE_QUALITY_METRIC_CATALOG_AUDIT",
        "status": "PASS" if not failures else "FAIL",
        "failure_total": len(failures),
        "failures": failures,
        "catalog_hash": catalog["artifact_hash"],
        "metric_total": catalog["metric_total"],
        "family_counts": dict(sorted(families.items())),
        "standard_source_total": len(catalog["standard_sources"]),
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def render_catalog_md(payload: dict[str, Any]) -> str:
    lines = [
        "# OC Core Quality Metric Catalog",
        "",
        f"Status: `{payload['status']}`",
        f"Artifact hash: `{payload['artifact_hash']}`",
        f"Metric total: `{payload['metric_total']}`",
        "",
        "Canonical storage is JSON/MD. SQLite is generated only as a deterministic query cache.",
        "",
        "## Standard Sources",
        "",
    ]
    for source in payload["standard_sources"]:
        lines.append(f"- `{source['source_id']}` {source['title']}: {source['url']}")
    lines.extend(["", "## Metrics", ""])
    for metric in payload["metrics"]:
        lines.append(f"### `{metric['metric_id']}` {metric['label']}")
        lines.append("")
        lines.append(f"- Family: `{metric['family']}`")
        lines.append(f"- Polarity: `{metric['polarity']}`")
        lines.append(f"- Default mode: `{metric['default_mode']}`")
        lines.append(f"- Scorer: `{metric['default_scorer_id']}`")
        lines.append(f"- Full coverage: {metric['full_coverage_rule']}")
        lines.append(f"- Parameterization: {metric['parameterization_rule']}")
        lines.append("")
    return "\n".join(lines)


def render_audit_md(payload: dict[str, Any]) -> str:
    lines = [
        "# OC Core Quality Metric Catalog Audit",
        "",
        f"Status: `{payload['status']}`",
        f"Failures: `{payload['failure_total']}`",
        f"Catalog hash: `{payload['catalog_hash']}`",
        "",
        "## Family Counts",
        "",
    ]
    for family, count in payload["family_counts"].items():
        lines.append(f"- `{family}`: {count}")
    if payload["failures"]:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in payload["failures"])
    return "\n".join(lines)


def expected_files() -> dict[Path, str]:
    catalog = build_catalog_payload()
    failures = validate_catalog(catalog)
    if failures:
        raise RuntimeError(f"Quality metric catalog validation failed: {failures}")
    audit = build_audit_payload(catalog)
    paths = metric_catalog_paths()
    return {
        paths["catalog_json"]: stable_json(catalog),
        paths["catalog_md"]: render_catalog_md(catalog),
        paths["audit_json"]: stable_json(audit),
        paths["audit_md"]: render_audit_md(audit),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build OC Core quality metric catalog.")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if not args.write and not args.check:
        args.check = True
    result = validation_result(expected_files(), write=args.write)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["state"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
