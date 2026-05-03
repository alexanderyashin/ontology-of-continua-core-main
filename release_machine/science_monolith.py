from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from pypdf import PdfReader

from . import complete


RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
RELEASE_ROOT = Path("releases") / RELEASE_ID
ARTIFACTS_REF = RELEASE_ROOT / "artifacts"
EDITORIAL_REF = RELEASE_ROOT / "editorial"
MASTER_PDF_NAME = "OC_CORE_1_3_3_MASTER_MONOGRAPH_EN.pdf"
BASE_SOURCE_REF = Path("releases/oc_core_1_3/monograph/source")
BASE_ENTRYPOINT = "oc_core_1_3_master_monograph.tex"
DELTA_SOURCE_REF = RELEASE_ROOT / "public_payload/sources/OC_CORE_1_3_3_MASTER_MONOGRAPH_EN.md"
BUILD_REF = Path("build_oc_core_1_3_3_science_monolith")
INTEGRATED_MODEL_REF = Path("content/27a_oc_core_1_3_3_typed_foundation_and_claims.tex")
INTEGRATED_PROOF_REF = Path("content/27b_oc_core_1_3_3_proof_and_formalization.tex")
INTEGRATED_EVIDENCE_REF = Path("content/27c_oc_core_1_3_3_methods_evidence_and_comparators.tex")
INTEGRATED_REVIEW_REF = Path("content/27d_oc_core_1_3_3_review_boundaries_and_journal_map.tex")
INTEGRATED_APPENDIX_REF = Path("appendix/T_oc_core_1_3_3_science_monolith_trace.tex")
INTEGRATED_AUTO_CORE_REF = Path("content/_auto_core_inputs_1_3_3_integrated.tex")
POSITIVE_STANDARD_APPENDIX_REF = Path("appendix/U_oc_core_1_3_3_public_scientific_quality_standard.tex")
HISTORICAL_CORE12_ANNEX_REF = Path("appendix/V_oc_core_1_3_3_historical_core_12_provenance_annex.tex")
INTEGRATED_CONTENT_REFS = [
    INTEGRATED_MODEL_REF,
    INTEGRATED_PROOF_REF,
    INTEGRATED_EVIDENCE_REF,
    INTEGRATED_REVIEW_REF,
]

BASELINE_FULL_MONOGRAPH_REFERENCE_PAGES = 650
BASELINE_FULL_MONOGRAPH_REFERENCE_TEXT_CHARS = 1_200_000
ANTI_SURROGATE_MIN_MONOLITH_PAGES = BASELINE_FULL_MONOGRAPH_REFERENCE_PAGES
ANTI_SURROGATE_MIN_MONOLITH_TEXT_CHARS = BASELINE_FULL_MONOGRAPH_REFERENCE_TEXT_CHARS
MONOLITH_SIZE_POLICY = "NO_MAXIMUM_TEXT_LIMIT_COVERAGE_FIRST"
MONOLITH_VOLUME_POLICY = "FULL_CORPUS_PLUS_133_INTEGRATION_NO_TRUNCATION_NO_PADDING"
MONOLITH_STRUCTURE_POLICY = "TOP_DOWN_FROZEN_LEVELS_APPEND_ONLY_NO_REDUCTION"

FROZEN_TOP_LEVEL_BLOCKS = [
    "Reader Orientation",
    "Complete Scientific Argument",
    "Scientific Closure and Use Boundaries",
    "Scientific Evidence and Review Appendices",
]

FROZEN_ENTRYPOINT_INPUT_REFS = [
    "content/frontmatter_oc_core_1_3_master.tex",
    "content/17_oc_core_1_3_reader_guide.tex",
    INTEGRATED_AUTO_CORE_REF.as_posix(),
    "content/18_oc_core_1_3_source_audit.tex",
    "content/19_oc_core_1_3_foundational_consistency.tex",
    "content/20_oc_core_1_3_theorem_roadmap.tex",
    "content/21_oc_core_1_3_worked_examples.tex",
    "content/22_oc_core_1_3_operationalization_program.tex",
    "content/23_oc_core_1_3_empirical_execution_protocols.tex",
    "content/24_oc_core_1_3_proof_machinery.tex",
    "content/25_oc_core_1_3_toe_synthesis.tex",
    "content/26_oc_core_1_3_practical_utility.tex",
    "appendix/A_notation",
    "appendix/B_axioms_full",
    "appendix/C_klevels_tables",
    "appendix/D_oc_core_1_3_source_audit_appendix",
    "appendix/E_oc_core_1_3_journal_core_bridge",
    "appendix/F_oc_core_1_3_reviewer_navigation_matrix",
    "appendix/S_oc_core_1_3_external_criticism_closure",
    "appendix/G_oc_core_1_3_empirical_validation_matrix",
    "appendix/H_oc_core_1_3_institute_run_measurement_program",
    "appendix/I_oc_core_1_3_domain_benchmark_manifest",
    "appendix/L_oc_core_1_3_domain_benchmark_caseset",
    "appendix/J_oc_core_1_3_domain_replay_reports",
    "appendix/K_oc_core_1_3_domain_execution_board",
    "appendix/M_oc_core_1_3_proof_machinery_appendix.tex",
    "appendix/N_oc_core_1_3_figure_atlas.tex",
    "appendix/O_oc_core_1_3_technical_derivation_atlas.tex",
    "appendix/P_oc_core_1_3_reference_benchmark_atlas.tex",
    "appendix/Q_oc_core_1_3_toe_support_dossiers.tex",
    "appendix/R_oc_core_1_3_practical_utility_model_comparison_atlas.tex",
]

FROZEN_AUTO_CORE_ALLOWED_RELOCATIONS = {
    "content/07_figures.tex": "appendix/N_oc_core_1_3_figure_atlas.tex",
    "content/axioms_full.tex": HISTORICAL_CORE12_ANNEX_REF.as_posix(),
    "content/theorems_master.tex": HISTORICAL_CORE12_ANNEX_REF.as_posix(),
    "content/toe/toe_master.tex": "content/25_oc_core_1_3_toe_synthesis.tex",
}

MANDATORY_REFS = [
    "claims/CLAIM_LEDGER_1_3_3.json",
    "proofs/THEOREM_INVENTORY_1_3_3.json",
    "proofs/THEOREM_REGISTRY_1_3_3.json",
    "proofs/PROOF_DEPENDENCY_GRAPH_1_3_3.json",
    "proofs/FINITE_MODEL_CHECKS_1_3_3.json",
    "proofs/FINITE_MODEL_OUTPUT_ATTESTATION_1_3_3.json",
    "formal/lean/OC133V12.lean",
    "formal/lean/LEAN_BUILD_CERTIFICATE_1_3_3.json",
    "validation/target_blind/OC133_TARGET_BLIND_PREDICTION_TABLE.json",
    "validation/numeric_replay_qa/OC133_NUMERIC_REPLAY_QA_TABLE.json",
    "reports/OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.json",
    "reports/OC_CORE_1_3_3_COUNTEREXAMPLE_REPORT.json",
    "docs/OC_1_3_3_PRIOR_ART_COMPARATOR_MATRIX.json",
    "comparators/OC_1_3_3_NOVELTY_AND_PRIORITY_REGISTER.json",
    "docs/OC_1_3_3_PHENOMENON_COVERAGE_MATRIX.json",
    "simulations/results/OC_CORE_1_3_3_SIMULATION_RESULTS_latest.json",
    "reports/OC_CORE_1_3_3_ADVERSARIAL_SIMULATION_REPORT.json",
    "reviews/oc133_llm_cerberus/OC133_LLM_CERBERUS_SUMMARY.json",
    "releases/oc_core_1_3_3/submission_packages/SUBMISSION_PACKAGE_INDEX.json",
    "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_RELEASE_SCORECARD_latest.json",
    DELTA_SOURCE_REF.as_posix(),
]

ANCHORS = [
    "Dedicated to my dear wife Maria",
    "Core 1.3.3",
    "OC Core 1.3.3",
    "T133-K0-RES",
    "T133-OMEGA-STATUS",
    "T133-HYBRID",
    "T133-MIN",
    "Lean",
    "finite-model",
    "target-blind",
    "adversarial review",
    "Journal",
    "publication-grade manuscript",
]

FORBIDDEN_ASSEMBLY_TEXT = re.compile(
    r"Science Delta Appendix|full monograph plus science delta appendix|delta appendix|old PDF plus detached delta|"
    r"old PDF plus delta|integration bridge|generated by the Logion|Core 1\.3\.3 Integrated Closure|"
    r"ManuscriptIntegration|Publication-grade text gate|updates the long-form OC manuscript|"
    r"Model, Proof, and Evidence Integration",
    re.IGNORECASE,
)

STALE_PUBLIC_IDENTITY = re.compile(r"\bv1\.3\.2\b|\bversion\s+1\.3\.2\b|oc_core_1_3_2", re.I)


def repo_root(start: Path | None = None) -> Path:
    return complete.repo_root(start)


def rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def read_json(path: Path, default: Any | None = None) -> Any:
    if not path.exists():
        return {} if default is None else default
    try:
        return json.loads(read_text(path))
    except json.JSONDecodeError:
        return {} if default is None else default


def _public_clean(value: Any) -> str:
    text = str(value if value is not None else "")
    replacements = {
        "PROMOTED_BOUNDED_NO_SEND_V12": "bounded promoted release claim",
        "PROMOTED_BOUNDED_PUBLIC_RELEASE_V12": "bounded promoted release claim",
        "no-send formal release-consistency check": "bounded formal consistency check",
        "no-send formal release-consistency fields": "bounded formal consistency fields",
        "no-send scientific theorem": "bounded scientific theorem",
        "OWNER_REVIEW_READY_NO_SEND": "ready for owner review",
        "READY_NO_SEND": "ready for owner review",
        "GOVERNANCE_CONTROL_NO_SEND_NOT_SCIENTIFIC_PROMOTION": "governance note, not a scientific promotion",
        "OWNER_GATED_NO_SEND_CONTROL_PLANE": "publication authorization boundary",
        "NO_SEND": "journal submission requires separate approval",
        "NO-SEND": "journal submission requires separate approval",
        "No-Send": "journal submission requires separate approval",
        "no_send": "journal submission requires separate approval",
        "no-send": "journal submission requires separate approval",
        "no-send unlock": "publication unlock",
        "It is not promoted as an independent novelty or scientific theorem in current formal profile.": "It is promoted only as a bounded model-core theorem claim, not as an independent novelty or unrestricted theory-wide theorem.",
        "It is not promoted as an independent novelty or scientific theorem in v12.": "It is promoted only as a bounded model-core theorem claim, not as an independent novelty or unrestricted theory-wide theorem.",
        "false-to-public": "not authorized",
        "global_no_send_lock": "global_publication_lock",
        "NO_EMPIRICAL_PASS_FROM_OFFICIAL_SNAPSHOT_REPLAY_QA": "official snapshots are inputs, not empirical promotion by themselves",
        "NUMERIC_REPLAY_QA_NOT_DOMAIN_VALIDATION": "numeric replay QA, not complete domain validation",
        "Cerberus": "adversarial review",
        "claim ledger": "claim register",
        "proof ledger": "proof register",
        "proof/evidence ledgers": "proof and evidence registers",
        "machine-readable ledgers": "machine-readable registers",
        "ledgers": "registers",
        "ledger": "register",
        "THEOREM_NATIVE": "bounded theorem route",
        "theorem-native promotion": "bounded theorem-route support",
        "theorem-native empirical": "bounded theorem-routed replay",
        "held-out prediction review": "bounded replay review",
        "verdict PASS": "bounded evidence available",
        "What OC closes or adds": "What OC contributes within stated limits",
        "What prior science could do, what remained fragmented, and what OC closes": "What prior science provided, what remained fragmented, and what OC contributes within stated limits",
        "closes or adds": "contributes within stated limits",
        "Practical Consequences, Predictive Power, and Use of OC Core": "Practical Consequences, Bounded Replay Use, and Limits of OC Core",
        "Predictive Power": "Bounded Replay Use",
        "What OC predicts across the closed empirical domains": "Bounded replay examples and domain protocol boundaries",
        "closed-domain": "bounded domain-lane",
        "Closed-domain": "Bounded domain-lane",
        "closed empirical domains": "bounded replay lanes",
        "closed empirical domain": "bounded replay lane",
        "closed packets": "bounded protocol packets",
        "closed packet": "bounded protocol packet",
        "lawful closed science": "bounded research protocol",
        "Current closure status: PASS. Promotion blockers: none.": "Current release posture: bounded support is recorded; broader promotion requires explicit additional evidence.",
        "Current closure status": "Current release posture",
        "Promotion blockers": "broader-promotion limits",
        "theorem packet COMPLETE": "theorem packet recorded",
        "theorem packet is COMPLETE": "theorem packet is recorded",
        "parameter law COMPLETE": "parameter law recorded",
        "parameter law is COMPLETE": "parameter law is recorded",
        "FINAL_UNIFIED_SYNTHESIS_VALIDATOR_PASS": "BOUNDED_SYNTHESIS_REVIEW_RECORDED",
        "final unified-science synthesis": "bounded synthesis layer",
        "final unified--science synthesis": "bounded synthesis layer",
        "universal structural results": "declared structural results",
        "universal structure": "declared model structure",
        "universal structures": "declared model structures",
        "Universal structure": "Declared model structure",
        "Core 2.x": "archival source corpus",
        "Core~2.x": "archival source corpus",
        "originally distributed across": "drawn from archived source modules across",
        "developed in Core 2.x": "developed in prior internal drafts",
        "developed in Core~2.x": "developed in prior internal drafts",
        "target-blind validation": "target-blind replay QA",
        "Target-blind validation": "Target-blind replay QA",
        "domain validation report": "domain evidence-boundary report",
        "Domain validation report": "Domain evidence-boundary report",
        "process-control packet": "process packet",
        "control packet": "process packet",
        "complete domain validation": "whole-domain proof",
        "full validation bar": "bounded replay QA bar",
        "Benchmark against serious alternatives": "Positioning against selected alternatives",
        "NO_SIMPLER_SUPERIOR_BASELINE_FOUND": "NO_SUPERIORITY_CLAIM_POSITIONING_ONLY",
        "NO_COMPARATOR_MAY_WIN_ON_SAME_CLAIM_CLASS_AFTER_COST_NORMALIZATION": "NO_GLOBAL_COMPARATOR_SUPERIORITY_CLAIM",
        "trace-closed, replay-closed, and comparator-clean": "traceable, replayable as bounded QA, and comparator-positioned",
        "trace-closed": "traceable",
        "replay-closed": "replayable as bounded QA",
        "comparator-clean": "comparator-positioned",
        "unify all domains of reality under one mathematical framework": "provide a bounded cross-domain modeling grammar where assumptions and evidence are declared",
        "Unify all domains of reality under one mathematical framework": "Provide a bounded cross-domain modeling grammar where assumptions and evidence are declared",
        "global minimality": "component witness independence for the declared semantic verdict suite",
        "Global Minimality": "Component witness independence for the declared semantic verdict suite",
        "global verdict-invariant minimality": "component witness independence for the declared semantic verdict suite",
        "Global verdict-invariant minimality": "Component witness independence for the declared semantic verdict suite",
        "component-wise witness independence for the declared semantic verdict suite": "component-witness independence",
        "Component-wise witness independence for the declared semantic verdict suite": "Component-witness independence",
        "domain-independent at the level of formal vocabulary": "shared at the level of declared model vocabulary",
        "domain-independent irreducibility theorem": "unrestricted irreducibility theorem",
        "logical superiority": "comparative parsimony under declared assumptions",
        "all-domain numerical closure": "universal numeric closure",
        "final all-domain completion": "complete scientific coverage",
        "all-domain": "full-scope",
        "superiority": "unrestricted comparative claim",
        "universal rules": "declared structural rules",
        "Universal rules": "Declared structural rules",
        "K0-K12 hierarchy": "K0-K12 witness taxonomy",
        "K0-K12 Hierarchy": "K0-K12 Witness Taxonomy",
        "Final Unified Synthesis": "Bounded Synthesis",
        "FINAL_UNIFIED_SYNTHESIS_VALIDATOR_PASS": "BOUNDED_SYNTHESIS_REVIEW_RECORDED",
        "final unified-science synthesis": "bounded synthesis layer",
        "universal structural results": "declared structural results",
        "Formal statements of universal structural results": "Formal statements of declared structural results",
        "universal structure": "declared model structure",
        "Universal structure": "Declared model structure",
        "universal axis": "declared model axis",
        "Universal axis": "Declared model axis",
        "universal admissibility": "declared admissibility",
        "universal structural laws": "declared structural laws",
        "universal flows": "declared model flows",
        "Global semantic coherence": "Declared semantic coherence",
        "global semantic coherence": "declared semantic coherence",
        "closed domain atlas": "bounded domain-lane atlas",
        "closed-domain": "bounded domain-lane",
        "Closed-domain": "Bounded domain-lane",
        "Current closure status: PASS. Promotion blockers: none.": "Current release posture: bounded support is recorded; broader promotion requires explicit additional evidence.",
        "Current closure status": "Current release posture",
        "Promotion blockers": "broader-promotion limits",
        "theorem packet COMPLETE": "theorem packet recorded",
        "theorem packet is COMPLETE": "theorem packet is recorded",
        "parameter law COMPLETE": "parameter law recorded",
        "parameter law is COMPLETE": "parameter law is recorded",
        "Core 2.x": "archival source corpus",
        "Core~2.x": "archival source corpus",
        "originally distributed across": "drawn from archived source modules across",
        "developed in Core 2.x": "developed in prior internal drafts",
        "developed in Core~2.x": "developed in prior internal drafts",
        "complete reconstructed description": "working structured description",
        "current hard validation matrix": "current bounded replay QA matrix",
        "full validation bar": "bounded replay QA bar",
        "Experimental validation:": "Experimental review protocol:",
        "universal validation": "bounded review protocol",
        "target-blind validation": "target-blind replay QA",
        "Target-blind validation": "Target-blind replay QA",
        "domain validation": "domain evidence-boundary review",
        "unified synthesis": "bounded synthesis",
        "Unified Synthesis": "Bounded Synthesis",
        "one explicit kernel": "one declared model-core kernel",
        "one K-level ladder": "one declared K-level ladder",
        "one theorem-to-observable grammar": "one declared theorem-to-observable grammar",
        "release criterion/release criterion": "release criterion",
        "review pressure": "review priority",
        "release boundary": "claim boundary",
        "failure mode": "criticism route",
        "closure evidence": "response evidence",
        "required repair": "required scientific repair",
        "LEAN_SUBSET_STRUCTURED_PROOF_FINITE_WITNESS": "Lean subset, structured proof sheet, and finite witness",
        "NUMERIC_REPLAY_QA_WITH_BASELINE_NEGATIVE_CONTROL_FALSIFIER": "numeric replay QA with baseline, negative control, and falsifier",
        "complete mathematical proofs of all theorems stated in Section~\\ref{sec:results}": "expanded public proof sheets and mechanized proof coverage for claims not covered by the current Lean subset",
        "universal evolution operators": "general evolution operators",
        "Universal Evolution Operators": "General Evolution Operators",
        "universal evolution axiom": "general evolution axiom",
        "Universal evolution axiom": "General evolution axiom",
        "universal operators": "general operators",
        "Universal operators": "General operators",
        "This ontology applies uniformly from K0 through K12": "This ontology is staged from K0 through K12 under declared assumptions",
        "finalises the publicationready version": "stabilises the publication-ready version",
        "finalises the publication-ready version": "stabilises the publication-ready version",
        "A complete taxonomy of thresholds": "A working taxonomy of thresholds",
        "the complete structure needed": "the working structure needed",
        "three threshold classes appear universally": "three threshold classes recur across declared cases",
        "Thresholds are universal": "Thresholds are treated as cross-domain model motifs",
        "universal classes of thresholds": "recurring classes of thresholds",
        "No single embedding space Mx is universal for all possible continua": "No single embedding space Mx is sufficient for every declared continuum class",
        "Process Schema Under scoped": "Process Schema Under Declared Scope",
        "source route": "source record",
        "Source route": "Source record",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"\bDelta Queue\b", "delta-stable verification", text, flags=re.I)
    text = re.sub(
        r"\breplaces?\s+disparate\s+domain[\-–— ]specific\s+mechanisms\s+with\s+(?:a\s+)?(?:universal|declared)\s+(?:structure|model\s+structure)\b",
        "relates selected domain mechanisms to a declared model structure under explicit assumptions",
        text,
        flags=re.I,
    )
    text = re.sub(r"proofs/proof_sheets/(T133-[A-Za-z0-9-]+)\.md", r"public proof sheet \1", text)
    proof_sheet_labels = {
        "T133-K0-RES": "K0 resolution theorem",
        "T133-OMEGA-STATUS": "lifecycle status theorem",
        "T133-K-ZERO": "K-zero boundary theorem",
        "T133-BOUNDARY": "boundary representation theorem",
        "T133-HYBRID": "hybrid semantics theorem",
        "T133-DIM": "dimension semantics theorem",
        "T133-CYCLE": "cycle-mode theorem",
        "T133-ID": "identity and rebirth theorem",
        "T133-MIN": "minimality witness theorem",
        "T133-KLEVEL": "K-level witness theorem",
    }
    for theorem_id, theorem_label in proof_sheet_labels.items():
        text = text.replace(f"public proof sheet {theorem_id}", f"public proof sheet for the {theorem_label}")
    text = text.replace("public proof sheet T133K0-RES", "public proof sheet for the K0 resolution theorem")
    text = text.replace("public proof sheet T133DIM", "public proof sheet for the dimension semantics theorem")
    text = re.sub(r"proofs/FINITE_MODEL_CHECKS_1_3_3\.json", "finite-model semantic report", text)
    text = re.sub(r"validation/_raw/[A-Za-z0-9_.-]+", "pinned public validation snapshot", text)
    text = re.sub(r"formal/lean/OC133V12\.lean::([A-Za-z0-9_'.-]+)", r"Lean declaration \1", text)
    text = re.sub(
        r"\bappendix/OC_1_3_3_[A-Za-z0-9_./-]+\.tex\b",
        lambda match: _public_artifact_phrase(match.group(0)),
        text,
    )
    text = re.sub(
        r"\b(?:claims|proofs|validation|reports|reviews|docs|comparators|releases)/[A-Za-z0-9_./-]+\.(?:json|md|tex|txt)\b",
        lambda match: _public_artifact_phrase(match.group(0)),
        text,
    )
    text = re.sub(r"\brepository path\s+repository path\s+", "repository path ", text, flags=re.I)
    text = re.sub(r"\bProcess Schema Under scoped\b", "Process Schema Under Declared Scope", text, flags=re.I)
    text = re.sub(
        r"\b[A-Za-z0-9_ -]*(?:bundle|catalog|latest|matrix|report|registry|certificate)[A-Za-z0-9_ -]*\.json\b",
        "the corresponding public evidence-package record",
        text,
        flags=re.I,
    )
    text = re.sub(r"\bpassed\s*=\s*true\b", "the executable check passes", text, flags=re.I)
    text = re.sub(r"\bG(?:32|33|34|35|36|37|38|39|4[0-9]|5[0-9]|6[0-9]|70)\b", "release criterion", text)
    text = re.sub(r"\bv12 gate\b", "current verification criterion", text, flags=re.I)
    text = re.sub(r"\bv12 release tuple\b", "current release tuple", text, flags=re.I)
    text = re.sub(r"\bv12\b", "current formal profile", text, flags=re.I)
    text = re.sub(
        r"Sections?~\\ref\{[^}]+\}(?:\s*(?:,|and|--)\s*\\ref\{[^}]+\})*",
        "the relevant public sections",
        text,
        flags=re.I,
    )
    text = re.sub(
        r"Appendices?~\\ref\{[^}]+\}(?:\s*(?:,|and|--)\s*\\ref\{[^}]+\})*",
        "the relevant public appendices or evidence package",
        text,
        flags=re.I,
    )
    text = re.sub(r"\\ref\{[^}]+\}", "the cited location", text)
    text = re.sub(r"internal gate predicates", "machine-verification predicates", text, flags=re.I)
    text = re.sub(r"internal gate", "machine-verification criterion", text, flags=re.I)
    text = re.sub(r"\buniversal\s+structural\b", "declared structural", text, flags=re.I)
    text = re.sub(r"\buniversal\s+structure\b", "declared model structure", text, flags=re.I)
    text = re.sub(r"\bglobal\s+semantic\s+coherence\b", "declared semantic coherence", text, flags=re.I)
    text = re.sub(r"\bclosed\s+domain\s+atlas\b", "bounded domain-lane atlas", text, flags=re.I)
    text = re.sub(r"\btheorem[- ]native\b", "proof-routed", text, flags=re.I)
    text = re.sub(r"\bempirical\s+hard[- ]closure\s+lane\b", "bounded replay lane", text, flags=re.I)
    text = re.sub(r"\bempirical\s+(?:hard[- ]closure|closure)\s+(?:program|backlog|surface|surfaces|lane|lanes)\b", "bounded replay QA program", text, flags=re.I)
    text = re.sub(r"\bbounded\s+empirical\s+closure(s)?\b", "bounded replay QA surface", text, flags=re.I)
    text = re.sub(r"\bempirical\s+closure\b", "bounded replay QA", text, flags=re.I)
    text = re.sub(r"\blogical\s+superiority\b", "comparative parsimony under declared assumptions", text, flags=re.I)
    text = re.sub(r"\bfinal\s+unified[- ]science\s+envelope\b", "bounded synthesis envelope", text, flags=re.I)
    text = re.sub(r"\buniversal\s+formalism\s+for\s+deriving\s+predictions\s+at\s+all\s+K-levels\b", "formal route for deriving scoped predictions at declared K-levels", text, flags=re.I)
    text = re.sub(r"\bunified\s+theory\s+of\s+dimensional\s+transitions\b", "bounded account of dimensional transitions", text, flags=re.I)
    text = re.sub(r"\bcomplete\s+mathematical\s+proofs\s+of\s+all\s+theorems\s+stated\s+in\s+Section~\\ref\{sec:results\}\b", "expanded public proof sheets and mechanized proof coverage for claims not covered by the current Lean subset", text, flags=re.I)
    text = re.sub(r"\bcomplete\s+mathematical\s+proofs\s+of\s+all\s+theorems\s+stated\s+in\s+Section~\\ref\{sec:results\}", "expanded public proof sheets and mechanized proof coverage for claims not covered by the current Lean subset", text, flags=re.I)
    text = re.sub(r"\buniversal\s+\(independent\s+of\s+domain\)", "declared across the scoped model domain", text, flags=re.I)
    text = re.sub(r"\bindependent\s+of\s+domain-specific\s+interpretations\b", "stated at the model-vocabulary level before domain-specific interpretation", text, flags=re.I)
    text = re.sub(r"\bdomain-independent\b", "model-vocabulary-level", text, flags=re.I)
    text = re.sub(r"\bacross\s+all\s+domains\b", "across the declared release domains", text, flags=re.I)
    text = re.sub(r"\ball\s+domains\b", "the declared release domains", text, flags=re.I)
    text = re.sub(r"\ball\s+continuum\s+levels\b", "the declared K-level sequence", text, flags=re.I)
    text = re.sub(r"\buniversal\s+thresholds\b", "declared threshold motifs", text, flags=re.I)
    text = re.sub(r"\bthresholds\s+are\s+universal\b", "threshold motifs recur under declared assumptions", text, flags=re.I)
    text = re.sub(r"\buniversal\s+falsifiability\s+programme\b", "scoped falsifiability programme", text, flags=re.I)
    text = re.sub(r"\buniversal\s+falsifiability\s+conditions\b", "scoped falsifiability conditions", text, flags=re.I)
    text = re.sub(r"\bthe\s+impossibility\s+of\s+any\s+coherent\s+universe\s+of\s+continua\b", "failure of coherence inside the declared continuum universe", text, flags=re.I)
    text = re.sub(r"\blimiting\s+all\s+structure\b", "limiting declared structure", text, flags=re.I)
    text = re.sub(r"\bclassification\s+of\s+all\s+possible\s+structures\b", "classification of declared structural-possibility candidates", text, flags=re.I)
    text = re.sub(r"\ball\s+possible\s+structures\b", "declared structural-possibility candidates", text, flags=re.I)
    text = re.sub(r"\bno\s+structure\s+beyond\s+K12\s+is\s+definable\b", "no additional public level is promoted beyond the declared K12 taxonomy in this release", text, flags=re.I)
    text = re.sub(r"\bno\s+structure\s+beyond\s+\$?K_\{?12\}?\$?\s+is\s+definable\b", "no additional public level is promoted beyond the declared K12 taxonomy in this release", text, flags=re.I)
    text = re.sub(r"\bno\s+beyond[- ]K12\s+continuum\s+exists\b", "no additional public level is promoted beyond the declared K12 taxonomy in this release", text, flags=re.I)
    text = re.sub(r"\bK([0-9]{1,2})\s+Run\s+[0-9]+\b", r"the K\1 construction route", text)
    text = re.sub(r"\bK\s*\$?\\?_?\{?([0-9]{1,2})\}?\$?\s+Run(?:~|\s)*[0-9]*\b", r"the K\1 construction route", text)
    text = re.sub(r"\bmemory\s+#[0-9]+(?:\s*,\s*#[0-9]+)*", "the corresponding derivation note", text, flags=re.I)
    text = re.sub(r"\bmemory(?:~|\s)*\\#[0-9]+(?:(?:\s*,|\s+and)\s*\\#[0-9]+)*", "the corresponding derivation note", text, flags=re.I)
    text = re.sub(r"\bgenerated\s+from\s+master_core_structure\.yaml\b", "organized by the canonical experiment taxonomy", text, flags=re.I)
    text = re.sub(r"\bgenerated\s+from\s+\\texttt\{master\\_core\\_structure\.yaml\}", "organized by the canonical experiment taxonomy", text, flags=re.I)
    text = re.sub(r"\bmaster_core_structure\.yaml\b", "the canonical experiment taxonomy", text, flags=re.I)
    text = re.sub(r"\\texttt\{master\\_core\\_structure\.yaml\}", "the canonical experiment taxonomy", text, flags=re.I)
    text = re.sub(r"\bexperiments_k([0-9]{1,2})\.tex\b", r"K\1 experiment design", text, flags=re.I)
    text = re.sub(r"\\texttt\{experiments\\_k([0-9]{1,2})\.tex\}", r"K\1 experiment design", text, flags=re.I)
    text = re.sub(r"\\texttt\{experiments\\_kX\.tex\}", "the K-level experiment design series", text, flags=re.I)
    # Public wording normalization must never mutate TeX include paths.
    text = re.sub(
        r"(\\input\{content/experiments/)K([0-9]{1,2}) experiment design(\})",
        r"\1experiments_k\2\3",
        text,
        flags=re.I,
    )
    text = re.sub(
        r"(content/experiments/)K([0-9]{1,2}) experiment design\b",
        r"\1experiments_k\2",
        text,
        flags=re.I,
    )
    text = re.sub(r"\bdeclared[- ]scope\b", "scoped", text, flags=re.I)
    text = re.sub(r"\\paragraph\{Predictions validated:\}", r"\\paragraph{Prediction protocol:}", text, flags=re.I)
    text = re.sub(r"\bPredictions\s+validated:", "Prediction protocol:", text, flags=re.I)
    text = re.sub(r"\bvalidated\s+predictions\b", "protocol-backed prediction routes", text, flags=re.I)
    text = re.sub(r"\bvalidated\s+in\s+physics\b", "supported in the scoped physics replay lane", text, flags=re.I)
    text = re.sub(r"\bmust\s+have\s+a\s+corresponding\s+instantiation\b", "may be tested for a corresponding scoped instantiation", text, flags=re.I)
    text = re.sub(r"\bestablish(?:es)?\s+the\s+empirical\s+basis\b", "states the protocol basis", text, flags=re.I)
    text = re.sub(r"\bguarantees\s+to\s+later\s+artifacts\b", "provides to later artifacts", text, flags=re.I)
    text = re.sub(r"\bguarantee(?:s)?\s+the\s+coherence\b", "support the coherence", text, flags=re.I)
    text = re.sub(r"\bguarantee\s+uniformity\b", "support uniformity", text, flags=re.I)
    text = re.sub(r"\bguarantee\s+that\b", "support the claim that", text, flags=re.I)
    text = re.sub(r"\bcollapse\s+is\s+guaranteed\b", "collapse follows under the declared model", text, flags=re.I)
    text = re.sub(r"\benforcement\s+guarantee\b", "enforcement assurance", text, flags=re.I)
    text = re.sub(r"\bthe\s+entire\s+ontology\b", "the declared model", text, flags=re.I)
    text = re.sub(r"\bentire\s+ontology\b", "declared model", text, flags=re.I)
    text = re.sub(r"\bdefinition\s+of\s+the\s+global\s+limit\b", "definition of the upper-coherence boundary", text, flags=re.I)
    text = re.sub(r"\bglobal\s+limit\b", "upper-coherence boundary", text, flags=re.I)
    text = re.sub(r"\bThis\s+master\s+file\s+summari[sz]es\b", "This chapter summarizes", text, flags=re.I)
    text = re.sub(r"\bRun~?[0-9]+\b", "the corresponding construction route", text)
    text = re.sub(r"\bPhysics\s+Run\b", "physics construction route", text, flags=re.I)
    text = re.sub(r"\bChemistry\s+Run\b", "chemistry construction route", text, flags=re.I)
    text = re.sub(r"\bthe\s+named\s+section\s+on\s+", "the section on ", text, flags=re.I)
    text = re.sub(r"\bthe\s+named\s+sections\s+on\s+", "the sections on ", text, flags=re.I)
    text = re.sub(r"\bthe\s+named\s+appendix\s+on\s+", "the appendix on ", text, flags=re.I)
    text = re.sub(r"\bthe\s+named\s+appendices\s+on\s+", "the appendices on ", text, flags=re.I)
    text = re.sub(r"\bpublicevidencereplayroute\b", "the public evidence replay route", text, flags=re.I)
    text = text.replace(r"\occode{public evidence replay route}", "the public evidence replay route")
    text = text.replace(r"\occode{repository checksum}", "the repository checksum field")
    text = re.sub(r"\brepositorychecksum\b", "the repository checksum field", text, flags=re.I)
    text = re.sub(r"\bmetadata\.ts_utc\b", "the release timestamp field", text, flags=re.I)
    text = re.sub(r"\bRelease\s+mirror:\b", "Public mirror:", text, flags=re.I)
    text = re.sub(r"\bUse-case\s+id\b", "Use case", text, flags=re.I)
    text = re.sub(r"\bnamed\s+evidence-package\s+record::([A-Za-z0-9_-]+)\s+route\s+row\b", r"the \1 evidence route", text, flags=re.I)
    text = re.sub(r"\bnamed\s+evidence-package\s+record::([A-Za-z0-9_-]+)\s+public\s+status=bounded\s+promoted\s+release\s+claim\b", r"the \1 public claim boundary", text, flags=re.I)
    text = re.sub(r"\bthe\s+([A-Za-z0-9_-]+)\s+evidence\s+record\s+public\s+status=bounded\s+promoted\s+release\s+claim\b", r"the \1 public claim boundary", text, flags=re.I)
    text = re.sub(r"\bnamed\s+evidence-package\s+record::([A-Za-z0-9_-]+)\b", r"the \1 evidence record", text, flags=re.I)
    text = re.sub(r"\bOC\s+CORE\s+1\s+3\s+3\s+PUBLISH\s+MANIFEST\s+DRAFT\b", "the public release manifest", text, flags=re.I)
    text = re.sub(r"\bTHEOREM\s+INVENTORY\s+1\s+3\s+3\b", "the theorem inventory", text, flags=re.I)
    text = re.sub(r"\bPHENOMENON\s+COVERAGE\s+MATRIX\b", "the phenomenon coverage matrix", text, flags=re.I)
    text = re.sub(r"\bCurrent\s+status:\s*BOUNDED_EQUIVALENCE_POSITIONING_COMPLETED_NO_PRIORITY_CLAIM\.?", "Current boundary: bounded equivalence positioning; no priority claim.", text, flags=re.I)
    text = re.sub(r"\bResidual\s+contribution\s+allowed\s+here\.?", "The residual contribution claimed here is:", text, flags=re.I)
    text = re.sub(r"\brelease\s+owner-review\s+gated\s+locks\b", "publication governance checks", text, flags=re.I)
    text = re.sub(r"\bowner-review\s+gated\s+scientific\s+promotion\b", "evidence-bound scientific promotion", text, flags=re.I)
    text = re.sub(r"\bowner-gated\s+publication\s+authorization\b", "publication authorization boundary", text, flags=re.I)
    text = re.sub(r"\bowner-gated\b", "authorization-bounded", text, flags=re.I)
    text = re.sub(r"\bpackage\s+release\s+permission\b", "public release boundary", text, flags=re.I)
    text = re.sub(r"\bevidence-bound\s+scientific\s+promotion\s+and\s+public\s+claim\s+boundary\s+must\s+not\s+be\s+conflated\.\s+at\s+the\s+point\s+where\b", "evidence-bound scientific promotion and public claim boundary are conflated where", text, flags=re.I)
    text = re.sub(r"\bOC\s+1\s+3\s+3\s+the\s+the\s+the\s+phenomenon\s+coverage\s+matrix\b", "the OC Core 1.3.3 phenomenon coverage matrix", text, flags=re.I)
    text = re.sub(r"\bboundedtheoremroute(?:_HELD_OUT_VALIDATED)?\b", "bounded theorem route", text, flags=re.I)
    text = re.sub(r"\bframe-onlysupportrow\b", "support-only row", text, flags=re.I)
    text = re.sub(r"\bfrontierextensionrow\b", "future-work support row", text, flags=re.I)
    text = re.sub(r"\bcurrentboundedsciencesurface\b", "current bounded science surface", text, flags=re.I)
    text = re.sub(r"\bproofrouted\b", "proof-routed", text, flags=re.I)
    text = re.sub(r"\bCore[~\s]+1\.2\s+and\s+subsequent\s+work\s+are\s+expected\s+to\s+develop\b", "Core 1.3.3 records the current route for", text, flags=re.I)
    text = re.sub(r"\bCore[~\s]+1\.3\.3\s+provides\s+the\s+structural\s+basis\s+for\s+an\s+explicit\s+validation\s+pipeline\s+in\s+Core[~\s]+1\.2\b", "Core 1.3.3 states the current structural basis for an explicit validation pipeline", text, flags=re.I)
    text = re.sub(r"\bwithin\s+Core~?1\.2\b", "within the bounded Core 1.3.3 release scope", text, flags=re.I)
    text = re.sub(r"\bfull\s+hierarchy\s+K0\s*[–—-]\s*K10\b", "declared hierarchy K0--K12", text, flags=re.I)
    text = re.sub(r"\bthe\s+full\s+hierarchy\s+\\?\(K_0\\?\)\s*[–—-]\s*\\?\(K_\{?10\}?\\?\)\b", "the declared hierarchy K0--K12", text, flags=re.I)
    text = re.sub(r"\bTheorem~?0\.0\s*\(embedding\s+constraint\)", "the embedding-constraint falsifier", text, flags=re.I)
    text = re.sub(r"\bTheorem\s+0\.0\s*\(embedding\s+constraint\)", "the embedding-constraint falsifier", text, flags=re.I)
    text = re.sub(
        r"\\occode\{SERIOUS_COMPARATOR::([A-Z_]+)::([A-Z0-9_]+)\}",
        lambda match: f"{match.group(1).replace('_', ' ').title()} {match.group(2).replace('_', ' ').title()} comparator",
        text,
    )
    text = text.replace(r"\occode{PASS_ACTIVE_NUMERICAL_PACKET}", "active bounded numeric packet")
    text = text.replace(r"\occode{PASS_REPLAYABLE}", "replayable in the bounded public protocol")
    text = text.replace(r"\occode{EMPIRICAL_HARD_CLOSED}", "bounded empirical replay packet active")
    text = text.replace(r"\occode{VALIDATED_ANCHOR_ACTIVE}", "validated anchor active")
    text = text.replace(r"\occode{MAINTAIN_REPLAY_DISCIPLINE}", "maintain replay discipline")
    text = text.replace(r"\occode{NOT_REQUIRED}", "not required")
    text = text.replace(r"\occode{PASS}", "bounded evidence recorded")
    text = text.replace(r"\occode{bounded theorem route}", "bounded theorem route")
    text = text.replace(r"\occode{frame-only support row}", "support-only row")
    text = text.replace(r"\occode{frontier extension row}", "future-work support row")
    text = text.replace(r"\occode{current bounded science surface}", "current bounded science surface")
    text = text.replace(r"\occode{bridge-only support row}", "bridge-only support row")
    text = text.replace(r"\occode{negative-control rejection row}", "negative-control rejection row")
    text = re.sub(r"\bAppendix~?the\s+section\s+on\s+oc\s+core\s+1\s+3\s+practical\s+utility\s+atlas\b", "the Applied Boundary and Model Comparison Appendix", text, flags=re.I)
    text = re.sub(r"\bAppendix\s+the\s+section\s+on\s+oc\s+core\s+1\s+3\s+practical\s+utility\s+atlas\b", "the Applied Boundary and Model Comparison Appendix", text, flags=re.I)
    text = re.sub(r"\bthe\s+section\s+on\s+oc\s+core\s+1\s+3\s+practical\s+utility\b", "the practical utility chapter", text, flags=re.I)
    text = re.sub(r"\bsection\s+oc13\s+theorem\s+roadmap\b", "the theorem roadmap", text, flags=re.I)
    text = re.sub(r"\bsection\s+oc13\s+worked\s+examples\b", "the worked examples chapter", text, flags=re.I)
    text = re.sub(r"\bsection\s+oc13\s+public\s+claim\s+boundary\b", "the public claim-boundary chapter", text, flags=re.I)
    section_replacements = {
        "model": "the formal model chapter",
        "results": "the historical result-boundary chapter",
        "operators full": "the operator semantics chapter",
        "klevels full": "the K-level witness taxonomy chapter",
        "klevels master": "the K-level overview chapter",
        "boundary extended": "the boundary geometry chapter",
        "thresholds extended": "the threshold landscape chapter",
        "collapse rebirth": "the lifecycle and rebirth chapter",
        "branching topology": "the branching-topology chapter",
        "operators": "the operator semantics chapter",
        "theorem spontaneous dimension creation": "the spontaneous-dimension theorem discussion",
        "oc13 foundational consistency": "the foundational-consistency chapter",
        "oc13 theorem roadmap": "the theorem roadmap",
        "oc13 worked examples": "the worked examples chapter",
        "oc13 public claim boundary": "the public claim-boundary chapter",
        "mspaces overview": "the M-space overview chapter",
        "crossk master": "the cross-level structure chapter",
        "processes master": "the process taxonomy chapter",
        "cycles master": "the cycle taxonomy chapter",
        "predictions master": "the bounded prediction-route chapter",
        "experiments master": "the experiment-design chapter",
        "falsifiability master": "the falsifiability chapter",
        "falsifiability extended": "the falsifiability chapter",
        "jets master": "the local-evolution chapter",
        "k3 collapse": "the K3 collapse discussion",
    }
    for label, replacement in section_replacements.items():
        text = re.sub(rf"\bthe\s+section\s+on\s+{re.escape(label)}\b", replacement, text, flags=re.I)
        text = re.sub(rf"\bsection\s+on\s+{re.escape(label)}\b", replacement, text, flags=re.I)
    text = re.sub(
        r"\bthe\s+section\s+on\s+([a-z][a-z0-9 _-]{2,60})\b",
        lambda match: "the " + re.sub(r"\s+", " ", match.group(1)).strip().replace("_", " ") + " discussion",
        text,
        flags=re.I,
    )
    text = re.sub(
        r"\bsection\s+on\s+([a-z][a-z0-9 _-]{2,60})\b",
        lambda match: "the " + re.sub(r"\s+", " ", match.group(1)).strip().replace("_", " ") + " discussion",
        text,
        flags=re.I,
    )
    text = re.sub(r"\bAppendix\s+the\s+section\s+on\s+oc13\s+external\s+criticism\s+closure\b", "the external-criticism closure appendix", text, flags=re.I)
    text = re.sub(r"\bAppendix\s+the\s+section\s+on\s+oc13\s+journal\s+core\s+bridge\b", "the journal-core bridge appendix", text, flags=re.I)
    text = re.sub(r"\\occode\{WAVE_([0-9A-Z_]+)\}", lambda match: "wave " + match.group(1).replace("_", " ").lower(), text)
    text = re.sub(r"\bno[- ]send\b", "owner-review", text, flags=re.IGNORECASE)
    text = re.sub(r"publish_allowed\s*=\s*false", "publication not authorized", text, flags=re.IGNORECASE)
    text = re.sub(r"owner_approved\s*=\s*false", "owner approval absent", text, flags=re.IGNORECASE)

    # Final release-blocker surface pass.  These patterns are produced after
    # label anonymisation, TeX escaping, and appendix wrapper generation; keep
    # them late so the public manuscript cannot leak route tokens as prose.
    text = text.replace(r"\occode{FORMALLY_PROVED}", "formally proved")
    text = text.replace(r"\occode{OPERATIONALLY_SUPPORTED_WITHIN_BOUNDS}", "operationally supported within bounds")
    text = text.replace(r"\occode{bounded theorem route_HELD_OUT_VALIDATED}", "bounded theorem route with held-out validation")
    text = text.replace(r"\occode{bounded theorem route}", "bounded theorem route")
    text = text.replace(r"\occode{frame-only support row}", "support-only row")
    text = text.replace(r"\occode{frontier extension row}", "future-work support row")
    text = text.replace(r"\occode{current bounded science surface}", "current bounded science surface")
    text = re.sub(r"\bFORMALLY_PROVED\b", "formally proved", text, flags=re.I)
    text = re.sub(r"\bOPERATIONALLY_SUPPORTED_WITHIN_BOUNDS\b", "operationally supported within bounds", text, flags=re.I)
    text = re.sub(r"\bboundedtheoremroute(?:_HELD_OUT_VALIDATED|_H)?\b", "bounded theorem route", text, flags=re.I)
    text = re.sub(r"\bframe[- ]?onlysupportrow\b", "support-only row", text, flags=re.I)
    text = re.sub(r"\bfrontierextensionrow\b", "future-work support row", text, flags=re.I)
    text = re.sub(r"\bcurrentboundedsciencesurface\b", "current bounded science surface", text, flags=re.I)
    text = re.sub(r"\bAppendix~?the\s+section\s+on\s+oc13\s+external\s+criticism\s+closure\b", "the external-criticism closure appendix", text, flags=re.I)
    text = re.sub(r"\bAppendix~?the\s+section\s+on\s+oc13\s+journal\s+core\s+bridge\b", "the journal-core bridge appendix", text, flags=re.I)
    text = re.sub(r"\bAppendix~?the\s+section\s+on\s+oc13\b", "the relevant OC Core 1.3.3 appendix", text, flags=re.I)
    text = re.sub(r"\bAppendix~?the\s+section\b", "the relevant appendix", text, flags=re.I)
    text = re.sub(r"\bsection\s+oc13\s+theorem\s+roadmap\b", "the theorem roadmap", text, flags=re.I)
    text = re.sub(r"\bsection\s+oc13\s+worked\s+examples\b", "the worked examples chapter", text, flags=re.I)
    text = re.sub(r"\bsection\s+oc13\s+public\s+claim\s+boundary\b", "the public claim-boundary chapter", text, flags=re.I)
    text = re.sub(r"\bthe\s+full\s+hierarchy\s+\\?\(?K_0\\?\)?\s*[–—-]\s*\\?\(?K_\{?10\}?\\?\)?", "the declared hierarchy K0--K12", text, flags=re.I)
    text = re.sub(r"\bfull\s+hierarchy\s+K0\s*[–—-]\s*K10\b", "declared hierarchy K0--K12", text, flags=re.I)
    text = re.sub(
        r"\bphysics,\s*chemistry,\s*biology,\s*cognition,\s*society,\s*and\s*metatheory\s+can\s+be\s+treated\s+as\s+continua\b",
        "selected structures in physics, chemistry, biology, cognition, society, and metatheory can be modeled as continua only under stated assumptions",
        text,
        flags=re.I,
    )
    text = re.sub(r"\bglobal-coherence continua\b", "upper-coherence taxonomy candidates", text, flags=re.I)
    text = re.sub(r"\bfull\s+K0\s*[–—-]\s*K12\s+hierarchy\b", "declared K0--K12 witness taxonomy", text, flags=re.I)
    text = re.sub(r"\bactive\s+parts\s+of\s+the\s+public\s+hierarchy\b", "declared taxonomy candidates in the public witness hierarchy", text, flags=re.I)
    text = re.sub(r"\bTheir\s+role\s+is\s+to\s+close\s+the\s+metatheoretical\s+and\s+global\s+integrability\s+work\b", "Their role is to state the metatheoretical and global-integrability obligations", text, flags=re.I)
    text = re.sub(r"\bupper-level\s+coherence\s+and\s+unified-science\s+integration\b", "upper-level coherence and bounded cross-model integration", text, flags=re.I)
    return text


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


def _tex_input_refs(text: str) -> list[str]:
    return re.findall(r"\\input\{([^}]+)\}", text)


def _top_down_structure_freeze_gate(
    *,
    entrypoint_text: str,
    source_auto_core_text: str,
    integrated_auto_core_text: str,
) -> dict[str, Any]:
    """Enforce the waterfall manuscript rule: frozen levels are append-only.

    This gate is intentionally structural rather than stylistic. It permits
    lower-level additions, but it blocks deletion of an already-frozen block,
    source input, or appendix role.
    """
    entrypoint_inputs = _tex_input_refs(entrypoint_text)
    source_auto_core_inputs = _tex_input_refs(source_auto_core_text)
    integrated_auto_core_inputs = _tex_input_refs(integrated_auto_core_text)
    top_blocks = re.findall(r"\\ocvolumeblock\{([^}]+)\}", entrypoint_text)

    missing_blocks = [block for block in FROZEN_TOP_LEVEL_BLOCKS if block not in top_blocks]
    missing_entrypoint_inputs = [ref for ref in FROZEN_ENTRYPOINT_INPUT_REFS if ref not in entrypoint_inputs]
    removed_auto_core_inputs = [
        ref
        for ref in source_auto_core_inputs
        if ref not in integrated_auto_core_inputs and ref not in FROZEN_AUTO_CORE_ALLOWED_RELOCATIONS
    ]
    relocation_missing = [
        {"source_ref": source_ref, "relocated_to": relocated_to}
        for source_ref, relocated_to in FROZEN_AUTO_CORE_ALLOWED_RELOCATIONS.items()
        if source_ref in source_auto_core_inputs
        and source_ref not in integrated_auto_core_inputs
        and relocated_to not in entrypoint_inputs
    ]
    failures = []
    if missing_blocks:
        failures.append("frozen_top_level_block_removed")
    if missing_entrypoint_inputs:
        failures.append("frozen_entrypoint_input_removed")
    if removed_auto_core_inputs:
        failures.append("source_auto_core_input_removed_without_relocation")
    if relocation_missing:
        failures.append("declared_relocation_target_missing")
    return {
        "gate_id": "TOP_DOWN_STRUCTURE_FREEZE_GATE",
        "policy": MONOLITH_STRUCTURE_POLICY,
        "state": "PASS" if not failures else "FAIL",
        "failure_total": len(failures),
        "failures": failures,
        "frozen_top_level_blocks": FROZEN_TOP_LEVEL_BLOCKS,
        "observed_top_level_blocks": top_blocks,
        "missing_top_level_blocks": missing_blocks,
        "frozen_entrypoint_input_total": len(FROZEN_ENTRYPOINT_INPUT_REFS),
        "missing_entrypoint_inputs": missing_entrypoint_inputs,
        "source_auto_core_input_total": len(source_auto_core_inputs),
        "integrated_auto_core_input_total": len(integrated_auto_core_inputs),
        "allowed_relocations": FROZEN_AUTO_CORE_ALLOWED_RELOCATIONS,
        "removed_auto_core_inputs_without_relocation": removed_auto_core_inputs,
        "relocation_missing": relocation_missing,
        "append_only_rule": "Frozen top-level structure and frozen input roles may be extended but not reduced.",
    }


def _safe_clear_build_dir(root: Path, build_dir: Path) -> None:
    resolved_root = root.resolve()
    resolved_build = build_dir.resolve()
    if resolved_root not in resolved_build.parents:
        raise RuntimeError(f"Refusing to clear build directory outside repo: {resolved_build}")
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir(parents=True, exist_ok=True)


def _replace_version_tokens(path: Path) -> None:
    if path.suffix.lower() not in {"", ".tex", ".bib", ".md", ".txt", ".yaml", ".yml"}:
        return
    text = read_text(path)
    replacements = {
        "Core~1.3.2": "Core~1.3.3",
        "Core 1.3.2": "Core 1.3.3",
        "Core v1.3.2": "Core v1.3.3",
        "v1.3.2": "v1.3.3",
        "Version 1.3.2": "Version 1.3.3",
        "OC_CORE_1_3_2": "OC_CORE_1_3_3",
        "oc_core_1_3_2": "oc_core_1_3_3",
        "1_3_2": "1_3_3",
        r"OC\_CORE\_1\_3\_2": r"OC\_CORE\_1\_3\_3",
        r"oc\_core\_1\_3\_2": r"oc\_core\_1\_3\_3",
        r"1\_3\_2": r"1\_3\_3",
        "1.3.2": "1.3.3",
        "10.5281/zenodo.17903912": "10.5281/zenodo.19967310",
        "Unified Science Synthesis": "Bounded Science Synthesis",
        "Structural Conditions for Any Universe": "Structural Conditions for Declared Model Contexts",
        "Global Semantic Coherence": "Declared Semantic Coherence",
        "Universal law of complexity growth": "Bounded complexity-growth hypothesis",
        "universal superiority over all modern science": "unbounded cross-science superiority claim",
        "universal superiority": "unbounded cross-science superiority",
        "terminal unified-science layer": "bounded synthesis layer",
        "Terminal unified-science layer": "Bounded synthesis layer",
        "global unified-science layer": "bounded synthesis layer",
        "Global unified-science layer": "Bounded synthesis layer",
        "OC claims universality": "OC claims bounded cross-domain applicability where assumptions and evidence hold",
        "universal modern-science-superiority": "unbounded cross-science comparison",
        "modern-science-superiority": "cross-science comparison",
        "propagates across all domains": "is routed across declared domain packets",
        "logical superiority": "comparative parsimony under declared assumptions",
        "all-domain numerical closure": "universal numeric closure",
        "final all-domain completion": "complete scientific coverage",
        "all-domain": "full-scope",
        "superiority": "unrestricted comparative claim",
        "unify all domains of reality under one mathematical framework": "provide a bounded cross-domain modeling grammar where assumptions and evidence are declared",
        "Unify all domains of reality under one mathematical framework": "Provide a bounded cross-domain modeling grammar where assumptions and evidence are declared",
        "global minimality": "component witness independence for the declared semantic verdict suite",
        "Global Minimality": "Component witness independence for the declared semantic verdict suite",
        "universal rules": "declared structural rules",
        "Universal rules": "Declared structural rules",
        "K0-K12 hierarchy": "K0-K12 witness taxonomy",
        "K0-K12 Hierarchy": "K0-K12 Witness Taxonomy",
        "EMPIRICAL_HARD_CLOSED": "bounded replay-supported",
        "Held-out case total": "Held-out case count",
        "Cerberus": "adversarial review",
        "NO_EMPIRICAL_PASS_FROM_OFFICIAL_SNAPSHOT_REPLAY_QA": "official snapshots are inputs, not empirical promotion by themselves",
        "NO_SEND": "journal submission requires separate approval",
        "NO-SEND": "journal submission requires separate approval",
        "No-Send": "journal submission requires separate approval",
        "no-send": "journal submission requires separate approval",
        "no_send": "journal submission requires separate approval",
        "28.04.2026": "01.05.2026",
        "28 April 2026": "1 May 2026",
        "XeLaTeX with OC Core 1.3.2 build scripts": "XeLaTeX with OC Core 1.3.3 monolith build scripts",
        "Scope of Core 1.3": "Scope of OC Core 1.3.3",
        "Summary of the Core 1.3 contributions": "Summary of the OC Core 1.3.3 contributions",
        "Summary of Core 1.3 contributions": "Summary of OC Core 1.3.3 contributions",
        "Observed universe as a structured continuum": "Declared observation domain as a structured continuum",
        "Level K0: structural conditions for any universe": "Level K0: structural conditions for declared model contexts",
        "Level K0: structural conditions for any Universe": "Level K0: structural conditions for declared model contexts",
        "universal applicability": "bounded cross-domain applicability",
        "Universal applicability": "Bounded cross-domain applicability",
        "universality of thresholds for all levels": "recurrence of threshold behavior under declared assumptions",
        "universality of threshold behaviour across": "recurrence of threshold behavior across declared examples",
        "Knowledge systems exhibit universal growth–collapse–renewal cycles": "Knowledge systems can exhibit growth-collapse-renewal cycles under declared conditions",
        "Knowledge systems exhibit universal growth-collapse-renewal cycles": "Knowledge systems can exhibit growth-collapse-renewal cycles under declared conditions",
        "Final Unified Synthesis Release Gate": "Bounded Synthesis Research Boundary",
        "Final unified-synthesis release status": "Bounded synthesis research status",
        "What prior science could do, what remained fragmented, and what OC closes": "What prior science provided, what remained fragmented, and what OC contributes within stated limits",
        "What OC closes or adds": "What OC contributes within stated limits",
        "closes or adds": "contributes within stated limits",
        "Practical Consequences, Predictive Power, and Use of OC Core": "Practical Consequences, Bounded Replay Use, and Limits of OC Core",
        "Predictive Power": "Bounded Replay Use",
        "What OC predicts across the closed empirical domains": "Bounded replay examples and domain protocol boundaries",
        "closed empirical domains": "bounded replay lanes",
        "closed empirical domain": "bounded replay lane",
        "closed packets": "bounded protocol packets",
        "closed packet": "bounded protocol packet",
        "lawful closed science": "bounded research protocol",
        "Benchmark against serious alternatives": "Positioning against selected alternatives",
        "NO_SIMPLER_SUPERIOR_BASELINE_FOUND": "NO_SUPERIORITY_CLAIM_POSITIONING_ONLY",
        "NO_COMPARATOR_MAY_WIN_ON_SAME_CLAIM_CLASS_AFTER_COST_NORMALIZATION": "NO_GLOBAL_COMPARATOR_SUPERIORITY_CLAIM",
        "trace-closed, replay-closed, and comparator-clean": "traceable, replayable as bounded QA, and comparator-positioned",
        "trace-closed": "traceable",
        "replay-closed": "replayable as bounded QA",
        "comparator-clean": "comparator-positioned",
        "closed as THEOREM_NATIVE with verdict PASS": "represented as bounded model-core evidence",
        "is closed as boundedtheoremroute with verdict PASS": "has a bounded theorem-route support row",
        "is closed as bounded theorem route with bounded evidence available": "has a bounded theorem-route support row",
        "is closed as FRAME_ONLY with verdict PASS": "has a frame-only support row",
        "is closed as FRAME_ONLY with bounded evidence available": "has a frame-only support row",
        "THEOREM_NATIVE": "bounded theorem route",
        "verdict PASS": "bounded evidence available",
        "theorem packet is COMPLETE": "theorem packet is recorded",
        "parameter law is COMPLETE": "parameter law is recorded",
        "Promotion blockers": "broader-promotion limits",
        "campaign status PASS": "campaign support recorded",
        "currently PASS": "currently recorded as supported",
        "Core~2.x": "archival source corpus",
        "Core 2.x": "archival source corpus",
        "developed in Core~2.x": "developed in prior internal drafts",
        "developed in Core 2.x": "developed in prior internal drafts",
        "originally distributed across": "drawn from archived source modules across",
        "full validation bar": "bounded replay QA bar",
        "held-out prediction review": "bounded replay review",
        "theorem-native promotion": "bounded theorem-route support",
        "theorem-native empirical": "bounded theorem-routed replay",
        "Final Unified Synthesis": "Bounded Synthesis",
        "unified synthesis": "bounded synthesis",
        "Unified Synthesis": "Bounded Synthesis",
        "one explicit kernel": "one declared model-core kernel",
        "one K-level ladder": "one declared K-level ladder",
        "one theorem-to-observable grammar": "one declared theorem-to-observable grammar",
        "release criterion/release criterion": "release criterion",
        "claim ledger": "claim register",
        "proof ledger": "proof register",
        "proof/evidence ledgers": "proof and evidence registers",
        "machine-readable ledgers": "machine-readable registers",
        "ledgers": "registers",
        "ledger": "register",
        "review pressure": "review priority",
        "release boundary": "claim boundary",
        "failure mode": "criticism route",
        "closure evidence": "response evidence",
        "required repair": "required scientific repair",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = text.replace(
        r"complete mathematical proofs of all theorems stated in Section~\ref{sec:results}",
        "expanded public proof sheets and mechanized proof coverage for claims not covered by the current Lean subset",
    )
    text = text.replace("universal evolution operators", "general evolution operators")
    text = text.replace("Universal Evolution Operators", "General Evolution Operators")
    text = text.replace("universal evolution axiom", "general evolution axiom")
    text = text.replace("Universal evolution axiom", "General evolution axiom")
    text = text.replace("universal operators", "general operators")
    text = text.replace("Universal operators", "General operators")
    text = text.replace(
        "This ontology applies uniformly from K0 through K12",
        "This ontology is staged from K0 through K12 under declared assumptions",
    )
    text = text.replace("finalises the publicationready version", "stabilises the publication-ready version")
    text = text.replace("finalises the publication-ready version", "stabilises the publication-ready version")
    text = text.replace("A complete taxonomy of thresholds", "A working taxonomy of thresholds")
    text = text.replace("the complete structure needed", "the working structure needed")
    text = text.replace("three threshold classes appear universally", "three threshold classes recur across declared cases")
    text = text.replace("Thresholds are universal", "Thresholds are treated as cross-domain model motifs")
    text = text.replace("universal classes of thresholds", "recurring classes of thresholds")
    text = text.replace(
        "No single embedding space Mx is universal for all possible continua",
        "No single embedding space Mx is sufficient for every declared continuum class",
    )
    text = text.replace(
        r"Appendix~\ref{sec:oc-core-1-3-figure-atlas} and the Technical Derivation Atlas",
        "the visual route and technical derivation material in the public evidence package",
    )
    text = re.sub(
        r"defer\s+Appendices~\\ref\{sec:oc-core-1-3-figure-atlas\}--\\ref\{sec:oc-core-1-3-practical-utility-atlas\}",
        "defer detailed atlas material to the public evidence package",
        text,
        flags=re.I,
    )
    text = re.sub(r"\bG(?:32|33|34|35|36|37|38|39|4[0-9]|5[0-9]|6[0-9]|70)\b", "release criterion", text)
    text = re.sub(r"\bv12 gate\b", "current verification criterion", text, flags=re.I)
    text = re.sub(r"\bv12 release tuple\b", "current release tuple", text, flags=re.I)
    text = re.sub(r"\bv12\b", "current formal profile", text, flags=re.I)
    text = re.sub(r"internal gate predicates", "machine-verification predicates", text, flags=re.I)
    text = re.sub(r"internal gate", "machine-verification criterion", text, flags=re.I)
    text = re.sub(r"\buniversal\s+structural\b", "declared structural", text, flags=re.I)
    text = re.sub(r"\buniversal\s+structure\b", "declared model structure", text, flags=re.I)
    text = re.sub(r"\buniversal\s+structures\b", "declared model structures", text, flags=re.I)
    text = re.sub(r"\buniversal\s+axis\b", "declared model axis", text, flags=re.I)
    text = re.sub(r"\buniversal\s+admissibility\b", "declared admissibility", text, flags=re.I)
    text = re.sub(r"\buniversal\s+applicability\b", "bounded cross-domain applicability", text, flags=re.I)
    text = re.sub(r"\buniversal\s+growth[-–—]collapse[-–—]renewal\s+cycles\b", "growth-collapse-renewal cycles under declared conditions", text, flags=re.I)
    text = re.sub(r"\buniversal\s+flow(s)?\b", r"declared model flow\1", text, flags=re.I)
    text = re.sub(r"\buniversality\s+of\s+thresholds\s+for\s+all\s+levels\b", "recurrence of threshold behavior under declared assumptions", text, flags=re.I)
    text = re.sub(r"\buniversality\s+of\s+threshold\s+behaviou?r\s+across\b", "recurrence of threshold behavior across declared examples", text, flags=re.I)
    text = re.sub(r"\bglobal\s+semantic\s+coherence\b", "declared semantic coherence", text, flags=re.I)
    text = re.sub(r"\bclosed\s+domain\s+atlas\b", "bounded domain-lane atlas", text, flags=re.I)
    text = re.sub(r"\bCore\s+1\.3\s+Source[- ]Audit\s+Appendix\b", "Core 1.3.3 Provenance and Corpus Appendix", text, flags=re.I)
    text = re.sub(r"\bSource[- ]Audit\s+Appendix\b", "Provenance and Corpus Appendix", text, flags=re.I)
    text = re.sub(r"\bJournal[- ]Core\s+Extraction\s+Bridge\b", "Journal Article Extraction Appendix", text, flags=re.I)
    text = re.sub(r"\bReviewer\s+Navigation\s+Matrix\s+and\s+Audit\s+Checklist\b", "Reviewer Objection Navigation Appendix", text, flags=re.I)
    text = re.sub(r"\bReviewer\s+Navigation\s+Matrix\b", "Reviewer Objection Navigation Appendix", text, flags=re.I)
    text = re.sub(r"\bEmpirical\s+Validation\s+Matrix\s+and\s+Replay\s+Ledger\b", "Empirical Replay Evidence Appendix", text, flags=re.I)
    text = re.sub(r"\bDomain\s+Hard[- ]Closure\s+Command\s+Board\b", "Domain Evidence Workplan Appendix", text, flags=re.I)
    text = re.sub(r"\bTechnical\s+Derivation\s+Atlas\b", "Technical Derivation Appendix", text, flags=re.I)
    text = re.sub(r"\bPractical\s+Utility\s+and\s+Model\s+Comparison\s+Atlas\b", "Applied Boundary and Model Comparison Appendix", text, flags=re.I)
    text = re.sub(r"\bTOE\s+Support\s+Dossiers\b", "Synthesis Support Appendix", text, flags=re.I)
    text = re.sub(r"\bsource[- ]audit\s+appendix\b", "provenance and corpus appendix", text, flags=re.I)
    text = re.sub(r"\breviewer\s+navigation\s+matrix\b", "reviewer response map", text, flags=re.I)
    text = re.sub(r"\btechnical\s+derivation\s+atlas\b", "technical derivation material", text, flags=re.I)
    text = re.sub(r"\bfoundational\s+consistency\s+dossier\b", "foundational consistency discussion", text, flags=re.I)
    text = re.sub(r"\bcommand\s+board\b", "workplan appendix", text, flags=re.I)
    text = re.sub(r"\bcontrol\s+matrix\b", "review matrix", text, flags=re.I)
    text = re.sub(r"\bsource\s+stamp\b", "source provenance marker", text, flags=re.I)
    text = re.sub(r"\bJSON\s+surface\b", "machine-readable evidence surface", text, flags=re.I)
    text = re.sub(r"\bFAIL_CLOSED\b", "repair-required boundary", text, flags=re.I)
    text = re.sub(r"\bFAIL\\_CLOSED\b", "repair-required boundary", text, flags=re.I)
    text = re.sub(r"\bFRAME_CLOSED\b", "frame-only support boundary", text, flags=re.I)
    text = re.sub(r"\bFRAME\\_CLOSED\b", "frame-only support boundary", text, flags=re.I)
    text = re.sub(r"\bFRAME_ONLY\b", "frame-only support row", text, flags=re.I)
    text = re.sub(r"\bFRAME\\_ONLY\b", "frame-only support row", text, flags=re.I)
    text = re.sub(r"\bBRIDGE_ONLY\b", "bridge-only support row", text, flags=re.I)
    text = re.sub(r"\bBRIDGE\\_ONLY\b", "bridge-only support row", text, flags=re.I)
    text = re.sub(r"\bEXTENSION\b", "frontier extension row", text)
    text = re.sub(r"\bREFUTED\b", "negative-control rejection row", text)
    text = re.sub(r"\bCORE_1_3_SCIENCE_ONLY\b", "current bounded science surface", text)
    text = re.sub(r"\bCORE\\_1\\_3\\_SCIENCE\\_ONLY\b", "current bounded science surface", text)
    text = re.sub(r"\bDRT:\s*class\s+negative-control rejection row,\s*verdict\s+repair-required boundary\b", "Domain replay taxonomy: this row is a negative-control rejection boundary.", text, flags=re.I)
    text = re.sub(r"\bDRT:\s*class\s+REFUTED,\s*verdict\s+FAIL_CLOSED\b", "Domain replay taxonomy: this row is a negative-control rejection boundary.", text, flags=re.I)
    text = re.sub(r"\bcovered_case_total\s*=\s*([0-9]+)", r"covered case total \1", text)
    text = re.sub(r"\bcovered\\_case\\_total\s*=\s*([0-9]+)", r"covered case total \1", text)
    text = re.sub(r"\bcovered_held_out_case_total\s*=\s*([0-9]+)", r"held-out case total \1", text)
    text = re.sub(r"\bcovered\\_held\\_out\\_case\\_total\s*=\s*([0-9]+)", r"held-out case total \1", text)
    text = re.sub(r"\bnormalized_error_mean_abs\s*=\s*([0-9.]+)", r"mean absolute normalized residual \1", text)
    text = re.sub(r"\bnormalized\\_error\\_mean\\_abs\s*=\s*([0-9.]+)", r"mean absolute normalized residual \1", text)
    text = re.sub(r"\bnormalized_error_p95\s*=\s*([0-9.]+)", r"95th-percentile normalized residual \1", text)
    text = re.sub(r"\bnormalized\\_error\\_p95\s*=\s*([0-9.]+)", r"95th-percentile normalized residual \1", text)
    text = re.sub(r"\bnormalized_error_max\s*=\s*([0-9.]+)", r"maximum normalized residual \1", text)
    text = re.sub(r"\bnormalized\\_error\\_max\s*=\s*([0-9.]+)", r"maximum normalized residual \1", text)
    text = re.sub(r"\btail_breach_count\s*=\s*([0-9]+)", r"tail-breach count \1", text)
    text = re.sub(r"\btail\\_breach\\_count\s*=\s*([0-9]+)", r"tail-breach count \1", text)
    text = re.sub(
        r"\bCurrent\s+closure\s+status\s*:\s*\\occode\{PASS\}\.\s*Promotion\s+blockers\s*:\s*none\.?",
        "Current release posture: bounded support is recorded; broader promotion requires explicit additional evidence.",
        text,
        flags=re.I,
    )
    text = re.sub(r"\bCurrent\s+closure\s+status\b", "Current release posture", text, flags=re.I)
    text = re.sub(r"\bClosed-domain\s+bindings\b", "Bounded domain-lane bindings", text, flags=re.I)
    text = re.sub(r"\bverdict\s+passes\s+the\s+bounded\s+check\b", "bounded evidence is recorded", text, flags=re.I)
    text = re.sub(r"\bpasses\s+the\s+bounded\s+check\b", "bounded support is recorded", text, flags=re.I)
    text = re.sub(r"\btheorem\s+packet\s+\\occode\{COMPLETE\}", "theorem packet recorded", text, flags=re.I)
    text = re.sub(r"\btheorem\s+packet\s+is\s+\\occode\{COMPLETE\}", "theorem packet is recorded", text, flags=re.I)
    text = re.sub(r"\bparameter\s+law\s+\\occode\{COMPLETE\}", "parameter law recorded", text, flags=re.I)
    text = re.sub(r"\bparameter\s+law\s+is\s+\\occode\{COMPLETE\}", "parameter law is recorded", text, flags=re.I)
    text = re.sub(r"\bverdict\s+PASS\b", "bounded evidence recorded", text, flags=re.I)
    text = re.sub(r"\bPromotion\s+blockers\b", "broader-promotion limits", text, flags=re.I)
    text = re.sub(r"\bFINAL_UNIFIED_SYNTHESIS\b", "BOUNDED_SYNTHESIS_REVIEW", text, flags=re.I)
    text = re.sub(r"final\s+unified[-–—]+\s*science\s+synthesis", "bounded synthesis", text, flags=re.I)
    text = re.sub(r"\bfinal\s+unified[- ]science\s+envelope\b", "bounded synthesis envelope", text, flags=re.I)
    text = re.sub(r"\bCore~?2\.x\b", "archival source corpus", text, flags=re.I)
    text = re.sub(r"\bcomplete\s+reconstructed\s+description\b", "working structured description", text, flags=re.I)
    text = re.sub(r"\boriginally\s+distributed\s+across\b", "drawn from archived source modules across", text, flags=re.I)
    text = re.sub(r"\btheorem[- ]native\b", "proof-routed", text, flags=re.I)
    text = re.sub(r"\bempirical\s+(?:hard[- ]closure|closure)\s+(?:program|backlog|surface|surfaces)\b", "bounded replay QA program", text, flags=re.I)
    text = re.sub(r"\bbounded\s+empirical\s+closure(s)?\b", "bounded replay QA surface", text, flags=re.I)
    text = re.sub(r"\bempirical\s+closure\b", "bounded replay QA", text, flags=re.I)
    text = re.sub(r"\blogical\s+superiority\b", "comparative parsimony under declared assumptions", text, flags=re.I)
    text = re.sub(
        r"\blogical\s+unrestricted\s+comparative\s+claim\s*\(Axiom(?:\s|~)*0\.3\)",
        "bounded logical substrate conditions (Axiom 0.3)",
        text,
        flags=re.I,
    )
    text = re.sub(
        r"\bunrestricted\s+comparative\s+claim\s+claim\b",
        "unrestricted comparative claim",
        text,
        flags=re.I,
    )
    text = re.sub(r"\bpublic_promotion/release_promotion_allowed\b", "public-promotion and release-permission", text)
    text = re.sub(r"\bpublic_promotion\b", "public promotion", text)
    text = re.sub(r"\bpublic-promotion\b", "public promotion", text, flags=re.I)
    text = re.sub(r"\brelease_promotion_allowed\b", "release promotion permission", text)
    text = re.sub(r"\bprediction_support_allowed\b", "prediction support permission", text)
    text = re.sub(r"\bempirical_support_allowed\b", "empirical support permission", text)
    text = re.sub(r"public\\_promotion/release\\_promotion\\_allowed", "public-promotion and release-permission", text)
    text = re.sub(r"public\\_promotion", "public promotion", text)
    text = re.sub(r"release\\_promotion\\_allowed", "release promotion permission", text)
    text = re.sub(r"prediction\\_support\\_allowed", "prediction support permission", text)
    text = re.sub(r"empirical\\_support\\_allowed", "empirical support permission", text)
    text = re.sub(r"\bprediction\s+support\s+allowed=false\b", "prediction support remains outside the promoted empirical claim", text, flags=re.I)
    text = re.sub(r"\bempirical\s+support\s+allowed=false\b", "empirical support remains outside the promoted empirical claim", text, flags=re.I)
    text = re.sub(r"\bowner-gated\s+owner-review\s+gated\s+publication\s+controls\b", "release-governed publication controls", text, flags=re.I)
    text = re.sub(r"\bis\s+explicitly\s+blocks\b", "explicitly blocks", text, flags=re.I)
    text = re.sub(
        r"\btotal[- ]unrestricted\s+comparative\s+claim\b",
        "unrestricted comparative claim",
        text,
        flags=re.I,
    )
    text = re.sub(r"\bTOE\b", "full-scope synthesis", text, flags=re.I)
    text = text.replace("content/full-scope synthesis/", "content/toe/")
    text = text.replace("content/full-scope synthesis\\", "content/toe\\")
    text = re.sub(r"\ball[- ]domain\s+numerical\s+closure\b", "universal numeric closure", text, flags=re.I)
    text = re.sub(r"\bfinal\s+all[- ]domain\s+completion\b", "complete scientific coverage", text, flags=re.I)
    text = re.sub(r"\ball[- ]domain\b", "full-scope", text, flags=re.I)
    text = re.sub(r"\bsuperiority\b", "unrestricted comparative claim", text, flags=re.I)
    text = re.sub(r"\bFull\s+Hierarchy\s+of\s+Continua\b", "K0-K12 Witness Taxonomy of Continua", text, flags=re.I)
    text = re.sub(r"\buniversal\s+formalism\s+for\s+deriving\s+predictions\s+at\s+all\s+K-levels\b", "formal route for deriving scoped predictions at declared K-levels", text, flags=re.I)
    text = re.sub(r"\bunified\s+theory\s+of\s+dimensional\s+transitions\b", "bounded account of dimensional transitions", text, flags=re.I)
    text = re.sub(r"\bcomplete\s+mathematical\s+proofs\s+of\s+all\s+theorems\s+stated\s+in\s+Section~\\ref\{sec:results\}\b", "expanded public proof sheets and mechanized proof coverage for claims not covered by the current Lean subset", text, flags=re.I)
    text = re.sub(r"\bcomplete\s+mathematical\s+proofs\s+of\s+all\s+theorems\s+stated\s+in\s+Section\s*10\b", "expanded public proof sheets and mechanized proof coverage for claims not covered by the current Lean subset", text, flags=re.I)
    text = re.sub(r"\bcomplete\s+falsification\s+toolkit\b", "bounded falsification route", text, flags=re.I)
    text = re.sub(r"\bOC\s+introduces\s+universal\s+measurement\s+protocols\s+applicable\s+to\s+any\s+continuum\b", "OC proposes scoped measurement protocols for declared continuum instances", text, flags=re.I)
    text = re.sub(r"\bFunctorial\s+collapse\s+patterns\s+are\s+universal\s+across\s+disciplines\b", "Functorial collapse patterns are compared across declared disciplines", text, flags=re.I)
    text = re.sub(r"\bpredicting\s+that\s+cognitive\s+update\s+behaviours\s+universally\s+seek\s+to\s+minimise\s+\$?e\$?\b", "modeling cognitive update behaviours as tending to reduce declared error terms under the stated protocol", text, flags=re.I)
    text = text.replace(
        "modeling cognitive update behaviours as tending to reduce declared error terms under the stated protocol$.",
        "modeling cognitive update behaviours as tending to reduce declared error terms under the stated protocol.",
    )
    text = re.sub(r"\bThese\s+consequences\s+hold\s+uniformly\s+for\s+all\s+levels\s+\$?K_?0\$?\s*[–-]\s*\$?K_?\{?10\}?\$?\b", "These consequences are evaluated level by level under the declared witness obligations", text, flags=re.I)
    text = re.sub(r"\$K_\{12\}\$\s+is\s+the\s+final\s+definable\s+continuum\s*:\s*the\s+space\s+of\s+all\s+possible\s+structural\s+laws\s+that\s+any\s+\$K\$\s*-?level\s+must\s+obey\.?", "$K_{12}$ is a high-level coherence representation under declared assumptions; it represents declared structural-law candidates in the current taxonomy.", text, flags=re.I)
    text = re.sub(r"\bK12\s+is\s+the\s+final\s+definable\s+continuum\s*:\s*the\s+space\s+of\s+all\s+possible\s+structural\s+laws\s+that\s+any\s+K-level\s+must\s+obey\.?", "K12 is a high-level coherence representation under declared assumptions; it represents declared structural-law candidates in the current taxonomy.", text, flags=re.I)
    text = re.sub(r"\bthe\s+space\s+of\s+all\s+possible\s+structural\s+laws\s+that\s+any\s+\$?K\$?\s*-?level\s+must\s+obey\b", "a representation space for declared structural-law candidates in the current taxonomy", text, flags=re.I)
    text = re.sub(r"\bpositive\s+standard\b", "evidence-inclusion rule", text, flags=re.I)
    text = re.sub(r"\bcorrectness\s+is\s+not\s+deferred\b", "proof obligations are routed to named proof surfaces", text, flags=re.I)
    text = re.sub(r"\bconstrain\s+all\s+continua\b", "constrain declared continuum instances", text, flags=re.I)
    text = re.sub(r"\bapply\s+across\s+the\s+entire\s+continuum\s+hierarchy\b", "apply across the declared continuum hierarchy", text, flags=re.I)
    text = re.sub(r"\bmust\s+expand\s+to\s+K12\b", "may require K12-style representation under the declared model", text, flags=re.I)
    text = re.sub(r"\bK12\s+emerges\s+to\s+absorb\b", "a K12-style representation may model", text, flags=re.I)
    text = re.sub(r"\bK12\s+is\s+falsified\s+by\s+violations\s+of\b", "The K12-style claim is reopened by failures of", text, flags=re.I)
    text = re.sub(
        r"\bComplete\s+Axiomatic\s+System\s+of\s+Core\s+1\.2\b",
        "Historical Core 1.2 Provenance: Complete Axiomatic System (Non-Promoted Baseline)",
        text,
        flags=re.I,
    )
    text = re.sub(
        r"\bMaster\s+Theorems\s+of\s+Core\s+1\.2\b",
        "Historical Core 1.2 Provenance: Master Theorems (Non-Promoted Baseline)",
        text,
        flags=re.I,
    )
    text = re.sub(
        r"This\s+section\s+presents\s+the\s+full\s+axiomatics\s+of\s+Core(?:\s|~)*1\.2\b[^.]*\.",
        "This provenance appendix preserves the archived Core 1.2 axiomatics as source history for continua K embedded in meta-domains M; it is not the current promoted 1.3.3 claim surface.",
        text,
        flags=re.I,
    )
    text = re.sub(
        r"This\s+section\s+collects\s+the\s+key\s+theorems\s+of\s+Core(?:\s|~)*1\.2\b[^.]*\.",
        "This provenance appendix preserves archived Core 1.2 theorem statements as source history; it is not the current promoted 1.3.3 theorem surface.",
        text,
        flags=re.I,
    )
    text = re.sub(
        r"\bsatisfying\s+the\s+axioms\s+of\s+Core(?:\s|~)*1\.2\b",
        "satisfying the archived Core 1.2 axioms",
        text,
        flags=re.I,
    )
    def _label_anchor(label: str) -> str:
        cleaned = re.sub(r"[^A-Za-z0-9:_-]+", " ", label).strip()
        cleaned = cleaned.replace("sec:", "section ").replace("app:", "appendix ").replace("fig:", "figure ")
        cleaned = cleaned.replace("tab:", "table ").replace("thm:", "theorem ").replace("lem:", "lemma ")
        cleaned = cleaned.replace("_", " ").replace("-", " ")
        return re.sub(r"\s+", " ", cleaned).strip() or "named source label"

    def _replace_ref_sequence(match: re.Match[str]) -> str:
        label_word = match.group("label")
        refs = [_label_anchor(item) for item in re.findall(r"\{([^}]+)\}", match.group("refs"))]
        if not refs:
            return f"{label_word} named source label"
        if len(refs) == 1:
            return f"{label_word} {refs[0]}"
        return f"{label_word} " + ", ".join(refs[:-1]) + f", and {refs[-1]}"

    text = re.sub(
        r"\b(?P<label>Sections?|Appendices?|Tables?|Figures?|Theorems?)~(?P<refs>\\(?:ref|pageref|autoref|nameref|Cref|cref)\{[^}]+\}(?:\s*(?:,|and|--|–|—)\s*\\(?:ref|pageref|autoref|nameref|Cref|cref)\{[^}]+\})*)",
        _replace_ref_sequence,
        text,
        flags=re.I,
    )
    text = re.sub(
        r"\\(?:ref|pageref|autoref|nameref|Cref|cref)\{([^}]+)\}",
        lambda match: f"source label {_label_anchor(match.group(1))}",
        text,
    )
    text = re.sub(r"\bAppendix\s+source label\b", "appendix source label", text, flags=re.I)
    text = re.sub(r"\bSection\s+source label\b", "section source label", text, flags=re.I)
    text = re.sub(r"\bthe relevant sections?\b", "the named section anchors", text, flags=re.I)
    text = re.sub(r"\bthe relevant appendices\b", "the named appendix anchors", text, flags=re.I)
    text = re.sub(r"\bthe cited location\b", "the named source label", text, flags=re.I)
    text = re.sub(r"\bSection\s+section\s+", "Section anchor ", text, flags=re.I)
    text = re.sub(r"\bSection\s+source label\s+", "Section anchor ", text, flags=re.I)
    text = re.sub(r"\bsource label\s+section\s+", "section anchor ", text, flags=re.I)
    text = re.sub(r"\bAppendix\s+source label\s*", "Appendix anchor ", text, flags=re.I)
    text = re.sub(r"Appendix~source label\s+([A-Za-z0-9 ]+)", lambda m: "the named appendix on " + m.group(1).strip(), text, flags=re.I)
    text = re.sub(r"Appendix~the named section on\s+([A-Za-z0-9 ]+)", lambda m: "the named appendix on " + m.group(1).strip(), text, flags=re.I)
    text = re.sub(r"Sections?\s+section\s+([A-Za-z0-9 ]+)", lambda m: "the named sections on " + m.group(1).strip(), text, flags=re.I)
    text = re.sub(r"Tables?\s+source label\s+([A-Za-z0-9 ]+)", lambda m: "the named table on " + m.group(1).strip(), text, flags=re.I)
    text = re.sub(r"Table~source label\s+([A-Za-z0-9 ]+)", lambda m: "the named table on " + m.group(1).strip(), text, flags=re.I)
    text = re.sub(r"\bSection\s+anchor\s+([A-Za-z0-9 ]+)", lambda m: "the named section on " + m.group(1).strip(), text, flags=re.I)
    text = re.sub(r"\bsection\s+anchor\s+([A-Za-z0-9 ]+)", lambda m: "the named section on " + m.group(1).strip(), text, flags=re.I)
    text = re.sub(r"\bAppendix\s+anchor\s+([A-Za-z0-9 ]+)", lambda m: "the named appendix on " + m.group(1).strip(), text, flags=re.I)
    text = re.sub(r"\bappendix\s+source\s+label\s+([A-Za-z0-9 ]+)", lambda m: "the named appendix on " + m.group(1).strip(), text, flags=re.I)
    text = re.sub(r"\bTable\s+table\s+([A-Za-z0-9 ]+)", lambda m: "the named table on " + m.group(1).strip(), text, flags=re.I)
    text = re.sub(r"\btable\s+table\s+([A-Za-z0-9 ]+)", lambda m: "the named table on " + m.group(1).strip(), text, flags=re.I)
    text = re.sub(r"\bAppendix\s+source\s+label\b", "the named appendix", text, flags=re.I)
    text = re.sub(r"\bSection\s+anchor\b", "the named section", text, flags=re.I)
    text = re.sub(r"\bTable\s+table\b", "the named table", text, flags=re.I)
    text = re.sub(r"\bfull recursive technical subtree\b", "curated technical appendix sequence", text, flags=re.I)
    text = re.sub(r"\bfull recursive reference subtree\b", "curated reference appendix sequence", text, flags=re.I)
    text = re.sub(r"\brecursive technical subtree\b", "technical appendix sequence", text, flags=re.I)
    text = re.sub(r"\brecursive reference subtree\b", "reference appendix sequence", text, flags=re.I)
    text = re.sub(r"\bexhaustive atlases\b", "curated public atlases", text, flags=re.I)
    text = re.sub(r"\bgenerated dossiers\b", "curated evidence dossiers", text, flags=re.I)
    text = re.sub(r"\braw support matrices\b", "evidence-package support matrices", text, flags=re.I)
    text = re.sub(
        r"\b(?:complete|full|vertical|dimensional)\s+(?:vertical\s+)?hierarchy\s+\\?\(?K_0\\?\)?\s*[–—-]{1,2}\s*\\?\(?K_\{?10\}?\\?\)?",
        "declared hierarchy K0--K12",
        text,
        flags=re.I,
    )
    text = re.sub(
        r"\bhierarchy\s+\\?\(?K_0\\?\)?\s*[–—-]{1,2}\s*\\?\(?K_\{?10\}?\\?\)?",
        "hierarchy K0--K12",
        text,
        flags=re.I,
    )
    text = re.sub(
        r"\bvertical\s+hierarchy\s+of\s+continua\s+from\s+\\texorpdfstring\{\\\(K_0\\\)\}\{K_0\}\s+to\s+\\\(K_\{10\}\\\)",
        lambda _match: r"vertical hierarchy of continua from \texorpdfstring{\(K_0\)}{K_0} to \texorpdfstring{\(K_{12}\)}{K12}",
        text,
        flags=re.I,
    )
    text = text.replace(r"\input{figures/levels_hierarchy}", r"\input{figures/levels_hierarchy_k12}")
    text = re.sub(r"\bVertical\s+hierarchy\s+K0--K10\b", "Vertical hierarchy K0--K12", text, flags=re.I)
    text = text.replace(
        r"\foreach \i/\j in {K0/K1, K1/K2, K2/K3, K3/K4, K4/K5, K5/K6, K6/K7, K7/K8, K8/K9, K9/K10}",
        r"\foreach \i/\j in {K0/K1, K1/K2, K2/K3, K3/K4, K4/K5, K5/K6, K6/K7, K7/K8, K8/K9, K9/K10, K10/K11, K11/K12}",
    )
    text = re.sub(r"\bcanonical science SPOT\b", "internal science-state register", text, flags=re.I)
    text = re.sub(r"\bcanonical SPOT\b", "internal science-state register", text, flags=re.I)
    text = re.sub(r"\bcurrent-science SPOT\b", "current science-state register", text, flags=re.I)
    text = re.sub(r"\bprocess-research SPOT\b", "process research-state register", text, flags=re.I)
    text = re.sub(r"\bscience SPOT\b", "science-state register", text, flags=re.I)
    text = re.sub(r"\bSPOT\b", "science-state register", text)
    text = re.sub(r"\bmetadata\.repo_s\s*ha\b", "repository checksum", text, flags=re.I)
    text = re.sub(r"\bmetadata\.repo_sha\b", "repository checksum", text, flags=re.I)
    text = re.sub(
        r"\bThe canonical scientific authority of the release is the internal science-state register\b",
        "The public scientific authority of the release is this monograph together with the curated evidence package",
        text,
        flags=re.I,
    )
    text = re.sub(
        r"\bThe canonical scientific authority of the release is the science-state register projection[^.]*\.",
        "The public scientific authority of the release is this monograph together with the curated evidence package and checksum-bound evidence records.",
        text,
        flags=re.I | re.S,
    )
    text = re.sub(
        r"\bThe internal science-state register is the scientific authority of the release\b",
        "The internal research-state provenance record supports release governance; the public scientific authority is the monograph plus evidence package",
        text,
        flags=re.I,
    )
    text = re.sub(
        r"\b(?:the\s+)?science-state register remains the canonical projection authority for release surfaces\b",
        "the research-state provenance record remains an internal consistency input for generated release surfaces",
        text,
        flags=re.I,
    )
    text = re.sub(
        r"\bdoes not displace (?:the\s+)?science-state register as the final authority\b",
        "does not replace the curated evidence package as the provenance record",
        text,
        flags=re.I,
    )
    text = re.sub(
        r"The public scientific authority of the release is this monograph together with the curated evidence package and checksum-bound evidence records\.json\}\s*\(surface id[^.]*?field\)\.",
        "The public scientific authority of the release is this monograph together with the curated evidence package and checksum-bound evidence records.",
        text,
        flags=re.I | re.S,
    )
    text = re.sub(r"\bK12\s+represents\s+the\s+highest\s+definable\s+level\b", "K12 is treated here as a high-level research-taxonomy candidate", text, flags=re.I)
    text = re.sub(r"\bthe highest definable level\b", "a high-level research-taxonomy candidate", text, flags=re.I)
    text = re.sub(r"\bgoverning all possible meta-theoretical systems\b", "governing declared meta-theoretical systems under the current taxonomy", text, flags=re.I)
    text = re.sub(r"\ball possible continua\b", "declared continuum classes under the current taxonomy", text, flags=re.I)
    text = re.sub(r"\ball continua\b", "declared continuum classes", text, flags=re.I)
    text = re.sub(r"\barbitrary continua\b", "declared continuum instances", text, flags=re.I)
    text = re.sub(r"\bembedding all continua\b", "embedding declared continuum classes", text, flags=re.I)
    text = re.sub(r"\bacross arbitrary continua\b", "across declared continuum classes", text, flags=re.I)
    text = re.sub(r"\buniversal meta-space\b", "declared-scope meta-space", text, flags=re.I)
    text = re.sub(r"\buniversal operator\b", "declared-scope operator", text, flags=re.I)
    text = re.sub(r"\buniversal invariants\b", "declared-scope invariants", text, flags=re.I)
    text = re.sub(r"\bcategorical universality\b", "categorical generality under declared assumptions", text, flags=re.I)
    text = re.sub(r"\btrans-universal\b", "cross-taxonomy", text, flags=re.I)
    text = re.sub(r"\bcross-universal\b", "cross-taxonomy", text, flags=re.I)
    text = re.sub(r"\buniversal\s+boundaries\b", "declared-scope boundaries", text, flags=re.I)
    text = re.sub(r"\buniversal\s+boundary\b", "declared-scope boundary", text, flags=re.I)
    text = re.sub(r"\buniversal\s+role\b", "high-level taxonomy role", text, flags=re.I)
    text = re.sub(r"\buniversal\s+natural(?:ity)?\b", "declared-scope naturality", text, flags=re.I)
    text = re.sub(r"\buniversal\s+representability\b", "declared-scope representability", text, flags=re.I)
    text = re.sub(r"\buniversal\s+coherence\b", "declared-scope coherence", text, flags=re.I)
    text = re.sub(r"\buniversal\s+thresholds\b", "declared-scope thresholds", text, flags=re.I)
    text = re.sub(r"\buniversal\s+rule set\b", "declared rule set", text, flags=re.I)
    text = re.sub(r"\buniversal\s+tension\b", "declared-scope tension", text, flags=re.I)
    text = re.sub(r"\buniversal\s+domain\b", "declared domain", text, flags=re.I)
    text = re.sub(r"\buniversality\b", "declared-scope generality", text, flags=re.I)
    text = re.sub(r"\buniversal\b", "declared-scope", text, flags=re.I)
    k0_token = r"(?:\\\(?\$?)?K(?:_\{?|\{)?0\}?(?:\\\)?\$?)?"
    k12_token = r"(?:\\\(?\$?)?K(?:_\{?|\{)?12\}?(?:\\\)?\$?)?"
    text = re.sub(
        rf"\bThis\s+ontology\s+applies\s+uniformly\s+from\s+{k0_token}\s+through\s+{k12_token}",
        "This ontology is staged from K0 through K12 under declared assumptions",
        text,
        flags=re.I,
    )
    text = re.sub(
        rf"(?:\$?{k12_token}\$?)\s+[-–—]\s+meta-ontological\s+continua\s+governing\s+the\s+possibility\s+space\s+of\s+all\s+lower\s+levels",
        "K12 - upper-coherence taxonomy candidates for declared lower-level architectures",
        text,
        flags=re.I,
    )
    text = re.sub(r"\bK12\s+is\s+the\s+limit\s+continuum\b", "K12 is treated as an upper-coherence taxonomy marker", text, flags=re.I)
    text = re.sub(r"\bthe\s+limit\s+continuum\s+contains\s+all\s+admissible\s+structural\s+possibilities\b", "the upper-coherence taxonomy records declared structural-possibility candidates rather than completed total possibility", text, flags=re.I)
    text = re.sub(r"\bcontains\s+all\s+admissible\s+embeddings\s+of\s+K0\s*(?:->|→|--)\s*K11\b", "records declared embedding families from K0 through K11", text, flags=re.I)
    text = re.sub(r"\bAll\s+thresholds\s+become\s+globally\s+stable\s+constants\s+for\s+the\s+limit\s+continuum\b", "Threshold motifs are recorded as candidate stability constraints for the upper-coherence taxonomy", text, flags=re.I)
    text = re.sub(r"\bK12\s+governs\s+the\s+constraints\s+that\s+any\s+architecture\b", "K12 records candidate constraints for declared architectures", text, flags=re.I)
    text = re.sub(r"\bWhile\s+K11\s+governs\s+the\s+evolution\s+of\s+mechanisms\s+of\s+evolution,\s+K12\s+governs\b", "K11 is used for reflexive mechanism evolution, while K12 is used as an upper-coherence taxonomy for", text, flags=re.I)
    text = re.sub(r"\bacross\s+all\s+lower-level\s+architectures\b", "across declared lower-level architecture examples", text, flags=re.I)
    text = re.sub(r"\bthe\s+space\s+of\s+all\s+admissible\s+continua\b", "the declared continuum-class space", text, flags=re.I)
    text = re.sub(r"\ball\s+admissible\s+structural\s+possibilities\b", "declared structural-possibility candidates", text, flags=re.I)
    text = re.sub(r"\bclassification\s+of\s+all\s+possible\s+structures\b", "classification of declared structural-possibility candidates", text, flags=re.I)
    text = re.sub(r"\ball\s+possible\s+structures\b", "declared structural-possibility candidates", text, flags=re.I)
    text = re.sub(r"\bno\s+structure\s+beyond\s+K12\s+is\s+definable\b", "no additional public level is promoted beyond the declared K12 taxonomy in this release", text, flags=re.I)
    text = re.sub(r"\bno\s+structure\s+beyond\s+\$?K_\{?12\}?\$?\s+is\s+definable\b", "no additional public level is promoted beyond the declared K12 taxonomy in this release", text, flags=re.I)
    text = re.sub(r"\bno\s+beyond[- ]K12\s+continuum\s+exists\b", "no additional public level is promoted beyond the declared K12 taxonomy in this release", text, flags=re.I)
    text = re.sub(r"\bK([0-9]{1,2})\s+Run\s+[0-9]+\b", r"the K\1 construction route", text)
    text = re.sub(r"\bK\s*\$?\\?_?\{?([0-9]{1,2})\}?\$?\s+Run(?:~|\s)*[0-9]*\b", r"the K\1 construction route", text)
    text = re.sub(r"\bmemory\s+#[0-9]+(?:\s*,\s*#[0-9]+)*", "the corresponding derivation note", text, flags=re.I)
    text = re.sub(r"\bmemory(?:~|\s)*\\#[0-9]+(?:(?:\s*,|\s+and)\s*\\#[0-9]+)*", "the corresponding derivation note", text, flags=re.I)
    text = re.sub(r"\bgenerated\s+from\s+master_core_structure\.yaml\b", "organized by the canonical experiment taxonomy", text, flags=re.I)
    text = re.sub(r"\bgenerated\s+from\s+\\texttt\{master\\_core\\_structure\.yaml\}", "organized by the canonical experiment taxonomy", text, flags=re.I)
    text = re.sub(r"\bmaster_core_structure\.yaml\b", "the canonical experiment taxonomy", text, flags=re.I)
    text = re.sub(r"\\texttt\{master\\_core\\_structure\.yaml\}", "the canonical experiment taxonomy", text, flags=re.I)
    text = re.sub(r"\bexperiments_k([0-9]{1,2})\.tex\b", r"K\1 experiment design", text, flags=re.I)
    text = re.sub(r"\\texttt\{experiments\\_k([0-9]{1,2})\.tex\}", r"K\1 experiment design", text, flags=re.I)
    text = re.sub(r"\\texttt\{experiments\\_kX\.tex\}", "the K-level experiment design series", text, flags=re.I)
    # Public wording normalization must never mutate TeX include paths.
    text = re.sub(
        r"(\\input\{content/experiments/)K([0-9]{1,2}) experiment design(\})",
        r"\1experiments_k\2\3",
        text,
        flags=re.I,
    )
    text = re.sub(
        r"(content/experiments/)K([0-9]{1,2}) experiment design\b",
        r"\1experiments_k\2",
        text,
        flags=re.I,
    )
    text = re.sub(r"\bdeclared[- ]scope\b", "scoped", text, flags=re.I)
    text = re.sub(r"\\paragraph\{Predictions validated:\}", r"\\paragraph{Prediction protocol:}", text, flags=re.I)
    text = re.sub(r"\bPredictions\s+validated:", "Prediction protocol:", text, flags=re.I)
    text = re.sub(r"\bvalidated\s+predictions\b", "protocol-backed prediction routes", text, flags=re.I)
    text = re.sub(r"\bvalidated\s+in\s+physics\b", "supported in the scoped physics replay lane", text, flags=re.I)
    text = re.sub(r"\bmust\s+have\s+a\s+corresponding\s+instantiation\b", "may be tested for a corresponding scoped instantiation", text, flags=re.I)
    text = re.sub(r"\bestablish(?:es)?\s+the\s+empirical\s+basis\b", "states the protocol basis", text, flags=re.I)
    text = re.sub(r"\bguarantees\s+to\s+later\s+artifacts\b", "provides to later artifacts", text, flags=re.I)
    text = re.sub(r"\bguarantee(?:s)?\s+the\s+coherence\b", "support the coherence", text, flags=re.I)
    text = re.sub(r"\bguarantee\s+uniformity\b", "support uniformity", text, flags=re.I)
    text = re.sub(r"\bguarantee\s+that\b", "support the claim that", text, flags=re.I)
    text = re.sub(r"\bcollapse\s+is\s+guaranteed\b", "collapse follows under the declared model", text, flags=re.I)
    text = re.sub(r"\benforcement\s+guarantee\b", "enforcement assurance", text, flags=re.I)
    text = re.sub(r"\bthe\s+entire\s+ontology\b", "the declared model", text, flags=re.I)
    text = re.sub(r"\bentire\s+ontology\b", "declared model", text, flags=re.I)
    text = re.sub(r"\bdefinition\s+of\s+the\s+global\s+limit\b", "definition of the upper-coherence boundary", text, flags=re.I)
    text = re.sub(r"\bglobal\s+limit\b", "upper-coherence boundary", text, flags=re.I)
    text = re.sub(r"\bThis\s+master\s+file\s+summari[sz]es\b", "This chapter summarizes", text, flags=re.I)
    text = re.sub(r"\bRun~?[0-9]+\b", "the corresponding construction route", text)
    text = re.sub(r"\bPhysics\s+Run\b", "physics construction route", text, flags=re.I)
    text = re.sub(r"\bChemistry\s+Run\b", "chemistry construction route", text, flags=re.I)
    text = re.sub(r"\bthe\s+named\s+section\s+on\s+", "the section on ", text, flags=re.I)
    text = re.sub(r"\bthe\s+named\s+sections\s+on\s+", "the sections on ", text, flags=re.I)
    text = re.sub(r"\bthe\s+named\s+appendix\s+on\s+", "the appendix on ", text, flags=re.I)
    text = re.sub(r"\bthe\s+named\s+appendices\s+on\s+", "the appendices on ", text, flags=re.I)
    text = re.sub(r"\bpublicevidencereplayroute\b", "the public evidence replay route", text, flags=re.I)
    text = text.replace(r"\occode{public evidence replay route}", "the public evidence replay route")
    text = text.replace(r"\occode{repository checksum}", "the repository checksum field")
    text = re.sub(r"\brepositorychecksum\b", "the repository checksum field", text, flags=re.I)
    text = re.sub(r"\bmetadata\.ts_utc\b", "the release timestamp field", text, flags=re.I)
    text = re.sub(r"\bRelease\s+mirror:\b", "Public mirror:", text, flags=re.I)
    text = re.sub(r"\bUse-case\s+id\b", "Use case", text, flags=re.I)
    text = re.sub(r"\bnamed\s+evidence-package\s+record::([A-Za-z0-9_-]+)\s+route\s+row\b", r"the \1 evidence route", text, flags=re.I)
    text = re.sub(r"\bnamed\s+evidence-package\s+record::([A-Za-z0-9_-]+)\s+public\s+status=bounded\s+promoted\s+release\s+claim\b", r"the \1 public claim boundary", text, flags=re.I)
    text = re.sub(r"\bthe\s+([A-Za-z0-9_-]+)\s+evidence\s+record\s+public\s+status=bounded\s+promoted\s+release\s+claim\b", r"the \1 public claim boundary", text, flags=re.I)
    text = re.sub(r"\bnamed\s+evidence-package\s+record::([A-Za-z0-9_-]+)\b", r"the \1 evidence record", text, flags=re.I)
    text = re.sub(r"\bOC\s+CORE\s+1\s+3\s+3\s+PUBLISH\s+MANIFEST\s+DRAFT\b", "the public release manifest", text, flags=re.I)
    text = re.sub(r"\bTHEOREM\s+INVENTORY\s+1\s+3\s+3\b", "the theorem inventory", text, flags=re.I)
    text = re.sub(r"\bPHENOMENON\s+COVERAGE\s+MATRIX\b", "the phenomenon coverage matrix", text, flags=re.I)
    text = re.sub(r"\bCurrent\s+status:\s*BOUNDED_EQUIVALENCE_POSITIONING_COMPLETED_NO_PRIORITY_CLAIM\.?", "Current boundary: bounded equivalence positioning; no priority claim.", text, flags=re.I)
    text = re.sub(r"\bResidual\s+contribution\s+allowed\s+here\.?", "The residual contribution claimed here is:", text, flags=re.I)
    text = re.sub(r"\brelease\s+owner-review\s+gated\s+locks\b", "publication governance checks", text, flags=re.I)
    text = re.sub(r"\bowner-review\s+gated\s+scientific\s+promotion\b", "evidence-bound scientific promotion", text, flags=re.I)
    text = re.sub(r"\bpackage\s+release\s+permission\b", "public release boundary", text, flags=re.I)
    text = re.sub(r"\bevidence-bound\s+scientific\s+promotion\s+and\s+public\s+claim\s+boundary\s+must\s+not\s+be\s+conflated\.\s+at\s+the\s+point\s+where\b", "evidence-bound scientific promotion and public claim boundary are conflated where", text, flags=re.I)
    text = re.sub(r"\bOC\s+1\s+3\s+3\s+the\s+the\s+the\s+phenomenon\s+coverage\s+matrix\b", "the OC Core 1.3.3 phenomenon coverage matrix", text, flags=re.I)
    text = re.sub(r"\bboundedtheoremroute(?:_HELD_OUT_VALIDATED)?\b", "bounded theorem route", text, flags=re.I)
    text = re.sub(r"\bframe-onlysupportrow\b", "support-only row", text, flags=re.I)
    text = re.sub(r"\bfrontierextensionrow\b", "future-work support row", text, flags=re.I)
    text = re.sub(r"\bcurrentboundedsciencesurface\b", "current bounded science surface", text, flags=re.I)
    text = re.sub(r"\bproofrouted\b", "proof-routed", text, flags=re.I)
    text = re.sub(r"\bCore[~\s]+1\.2\s+and\s+subsequent\s+work\s+are\s+expected\s+to\s+develop\b", "Core 1.3.3 records the current route for", text, flags=re.I)
    text = re.sub(r"\bCore[~\s]+1\.3\.3\s+provides\s+the\s+structural\s+basis\s+for\s+an\s+explicit\s+validation\s+pipeline\s+in\s+Core[~\s]+1\.2\b", "Core 1.3.3 states the current structural basis for an explicit validation pipeline", text, flags=re.I)
    text = re.sub(r"\bwithin\s+Core~?1\.2\b", "within the bounded Core 1.3.3 release scope", text, flags=re.I)
    text = re.sub(r"\bfull\s+hierarchy\s+K0\s*[–—-]\s*K10\b", "declared hierarchy K0--K12", text, flags=re.I)
    text = re.sub(r"\bthe\s+full\s+hierarchy\s+\\?\(K_0\\?\)\s*[–—-]\s*\\?\(K_\{?10\}?\\?\)\b", "the declared hierarchy K0--K12", text, flags=re.I)
    text = re.sub(r"\bTheorem~?0\.0\s*\(embedding\s+constraint\)", "the embedding-constraint falsifier", text, flags=re.I)
    text = re.sub(r"\bTheorem\s+0\.0\s*\(embedding\s+constraint\)", "the embedding-constraint falsifier", text, flags=re.I)
    text = re.sub(r"\bGoverning\s+surface\b", "Evidence route", text, flags=re.I)
    text = re.sub(r"\brepository\s+SHA\b", "repository checksum", text, flags=re.I)
    text = re.sub(r"\bthe mapped public anchors?\b", "the relevant cited locations", text, flags=re.I)
    text = re.sub(r"\bthe cited location\s*(?:,|and|--|–|—)\s*the cited location\b", "the cited locations", text)
    text = re.sub(r"\bCore~1\.3(?!\.\d)", r"Core~1.3.3", text)
    text = re.sub(r"\bCore 1\.3(?!\.\d)", r"Core 1.3.3", text)
    text = re.sub(r"\bCore v1\.3(?!\.\d)", r"Core v1.3.3", text)
    text = re.sub(r"logion/k[0-9]/[A-Za-z0-9_./\\:-]+", "public evidence replay route", text, flags=re.I)
    text = re.sub(
        r"\\occode\{SERIOUS_COMPARATOR::([A-Z_]+)::([A-Z0-9_]+)\}",
        lambda match: (
            f"{match.group(1).replace('_', ' ').title()} "
            f"{match.group(2).replace('_', ' ').title()} comparator"
        ),
        text,
    )
    text = re.sub(
        r"\\occode\{((?:releases|content|appendix|docs|proofs|validation|reviews|reports)/[^}]+)\}",
        lambda match: "evidence-package record "
        + Path(match.group(1).replace("\\", "/")).name.replace("_", " "),
        text,
    )
    code_replacements = {
        "PASS_ACTIVE_NUMERICAL_PACKET": "active bounded numeric packet",
        "PASS_REPLAYABLE": "replayable under the bounded public protocol",
        "EMPIRICAL_HARD_CLOSED": "bounded replay packet active",
        "VALIDATED_ANCHOR_ACTIVE": "validated anchor active",
        "MAINTAIN_REPLAY_DISCIPLINE": "maintain replay discipline",
        "NOT_REQUIRED": "not required",
        "PASS": "bounded evidence recorded",
    }
    for old, new in code_replacements.items():
        text = text.replace(rf"\occode{{{old}}}", new)
        if "_" in old:
            text = re.sub(
                rf"(?<![A-Z0-9_]){re.escape(old)}(?![A-Z0-9_])",
                new,
                text,
            )
            text = re.sub(
                rf"(?<![A-Z0-9\\]){re.escape(old.replace('_', r'\_'))}(?![A-Z0-9\\])",
                new,
                text,
            )
        else:
            text = re.sub(r"(?<![A-Z0-9_])PASS(?![A-Z0-9_])", new, text)
    text = re.sub(r"\bverdict\s+passes\s+the\s+bounded\s+check\b", "bounded evidence is recorded", text, flags=re.I)
    text = re.sub(r"\bpasses\s+the\s+bounded\s+check\b", "bounded support is recorded", text, flags=re.I)
    text = re.sub(
        r"\\occode\{INSTITUTE_RUN::([A-Z_]+)::WAVE_([0-9A-Z_]+)\}",
        lambda match: f"{match.group(1).replace('_', ' ').title()} institute-run wave "
        + match.group(2).replace("_", " ").lower(),
        text,
    )
    text = re.sub(
        r"\\occode\{WAVE_([0-9A-Z_]+)\}",
        lambda match: "wave " + match.group(1).replace("_", " ").lower(),
        text,
    )
    text = re.sub(
        r"WAVE\\?_([0-9A-Z](?:[0-9A-Z]|\\?_)+)",
        lambda match: "wave " + match.group(1).replace(r"\_", " ").replace("_", " ").lower(),
        text,
    )
    path.write_text(text, encoding="utf-8", newline="\n")


def _run(args: list[str], cwd: Path, *, timeout: int) -> dict[str, Any]:
    completed = subprocess.run(
        args,
        cwd=cwd,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=timeout,
    )
    command = " ".join(args)
    for token in {str(repo_root().resolve()), str(cwd.resolve())}:
        command = command.replace(token, "<REPO_ROOT>")
    stdout_tail = completed.stdout[-3000:].replace(str(repo_root().resolve()), "<REPO_ROOT>").replace(str(cwd.resolve()), "<REPO_ROOT>")
    stderr_tail = completed.stderr[-3000:].replace(str(repo_root().resolve()), "<REPO_ROOT>").replace(str(cwd.resolve()), "<REPO_ROOT>")
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout_tail": stdout_tail,
        "stderr_tail": stderr_tail,
        "ok": completed.returncode == 0,
    }


def _frontmatter_133(doi: str | None, zenodo_record_url: str | None) -> str:
    doi_text = doi or "assigned by the corrected Zenodo publication record"
    zenodo_text = zenodo_record_url or "assigned by the corrected publication pass"
    return rf"""\begin{{titlepage}}
\phantomsection
\label{{sec:oc133-title-page}}
\thispagestyle{{empty}}
\definecolor{{ocTitleBlue}}{{HTML}}{{173B57}}
\definecolor{{ocTitleGold}}{{HTML}}{{A77D2A}}
\begin{{tikzpicture}}[remember picture,overlay]
\draw[ocTitleBlue,line width=0.75pt]
  ([xshift=1.35cm,yshift=-1.35cm]current page.north west)
  rectangle
  ([xshift=-1.35cm,yshift=1.35cm]current page.south east);
\draw[ocTitleGold,line width=0.35pt]
  ([xshift=1.55cm,yshift=-1.55cm]current page.north west)
  rectangle
  ([xshift=-1.55cm,yshift=1.55cm]current page.south east);
\end{{tikzpicture}}
\begin{{center}}
\vspace*{{1.0cm}}
{{\sffamily\Large\color{{ocTitleBlue}}\textsc{{Ontology of Continua}}}}\\[0.38cm]
{{\sffamily\Huge\bfseries Core~1.3.3}}\\[0.28cm]
{{\sffamily\Large Master Monograph}}\\[0.75cm]
{{\color{{ocTitleGold}}\rule{{0.42\textwidth}}{{0.5pt}}}}\\[0.95cm]

{{\Large Alexander Yashin}}\\[0.2cm]
{{\normalsize Independent Researcher, Leipzig/Halle, Germany}}\\[0.2cm]
{{\normalsize \href{{https://orcid.org/0009-0008-6166-0914}}{{ORCID 0009-0008-6166-0914}}}}\\[1.0cm]

{{\normalsize Version v1.3.3; release date: 1 May 2026}}\\[0.35cm]
{{\normalsize Version DOI: \href{{https://doi.org/{_tex_escape(doi_text)}}}{{{_tex_escape(doi_text)}}}}}\\[0.2cm]
{{\normalsize Zenodo record: \href{{{_tex_escape(zenodo_text)}}}{{{_tex_escape(zenodo_text)}}}}}\\[0.2cm]
{{\normalsize Concept DOI: \href{{https://doi.org/10.5281/zenodo.17899134}}{{10.5281/zenodo.17899134}}}}\\[0.2cm]
{{\normalsize GitHub release: \href{{https://github.com/alexanderyashin/ontology-of-continua-core-main/releases/tag/v1.3.3}}{{v1.3.3}}}}\\[0.9cm]

\vfill

% DEDICATION_REQUIRED_DO_NOT_REMOVE
% OC_CORE_PUBLICATION_DEDICATION
{{\small\itshape Dedicated to my dear wife Maria, without whom this work would have been impossible.}}\\[0.8cm]

\begin{{minipage}}{{0.86\textwidth}}
\centering\scriptsize
This public monograph is the canonical OC Core~1.3.3 scientific artifact.
Earlier source witnesses and archived releases are provenance history only; they are not the current release identity.
\end{{minipage}}
\end{{center}}
\end{{titlepage}}

\begin{{abstract}}
Ontology of Continua (OC) Core~1.3.3 is a bounded external-review release of the
OC model core. It presents typed carriers and realizations, liveness and death
conditions, residue, morphisms, generalized boundaries, hybrid operators,
cycle modes, historical/effective dimension, K-level witnesses, proof
boundaries, a Lean-checked subset, executable finite semantic checks,
bounded target-blind replay QA examples, prior-art comparison, and adversarial-review
closure.

The monograph is written as one continuous scientific manuscript rather than as
a prior volume followed by an update packet. The 1.3.3 additions are integrated
into the model, proof, evidence, comparison, and reviewer-boundary chapters.
Machine-readable registers remain in the evidence package; the public text
teaches the claims, assumptions, evidence routes, and limits before pointing to
the replay artifacts.

The scope is explicit. This release promotes only evidence-bound model-core
claims. It does not claim final completion of every future scientific
projection, complete numerical closure for all domains, or an unbounded
comparison victory over contemporary science. Those obligations remain in the
background research program until separately evidenced.
\end{{abstract}}

\clearpage
\noindent\textbf{{Document role.}}
This PDF is the canonical master monograph for OC Core~1.3.3. It is the
long-form scientific text that teaches the model, records the proof/evidence
route, and defines the public claim boundary before readers consult
machine-readable evidence.

\medskip
\noindent\textbf{{Reader Contract.}}
This monograph is a publication-grade manuscript, not an internal routing memo,
process packet, or raw register dump. Every promoted claim is either
argued in the prose, tied to a proof/evidence artifact, or explicitly bounded
as future research.

\medskip
\noindent\textbf{{Main-argument boundary.}}
The continuous scientific argument is the model, proof, evidence,
comparison, limitation, and discussion path. Long theorem registers,
finite-case rows, replay inventories, source-provenance tables, reviewer
matrices, and journal-package maps are evidence appendices: they preserve the
full corpus for auditability, but they are not the narrative spine and they do
not promote broader claims merely by appearing in the monograph.

\clearpage
\noindent\textbf{{Keywords.}}
Ontology of Continua; typed model core; formal methods; proof governance;
finite semantic checks; target-blind replay QA; reproducible research;
scientific release engineering.

\clearpage
\noindent\textbf{{Reproducibility and citation note.}}
\begin{{itemize}}[leftmargin=1.6em,nosep]
\item Current version DOI: \href{{https://doi.org/{_tex_escape(doi_text)}}}{{{_tex_escape(doi_text)}}}.
\item Current Zenodo record: \href{{{_tex_escape(zenodo_text)}}}{{{_tex_escape(zenodo_text)}}}.
\item GitHub release tag: \href{{https://github.com/alexanderyashin/ontology-of-continua-core-main/releases/tag/v1.3.3}}{{v1.3.3}}.
\item Logion is the research-instrument and institute-automation system used to prepare, check, package, and audit the work; it is not an author.
\item ESTRA is the methodological framework used in the work; it is not an author or affiliation.
\end{{itemize}}

\noindent\textbf{{Substantive review and idea acknowledgements.}}
The following public acknowledgements record review challenge, ideas, or criticism
that improved the release route. They are sorted by surname in English
transcription and do not imply authorship, endorsement, publication approval, or
agreement with the theory's release form:
\begin{{itemize}}
    \item G.~V.~Apostolov --- substantive review and idea input.
    \item Eduard Fadeev --- Parfit idea and release-governance pressure.
    \item Gennady Alekseevich Nosov --- substantive review and idea input.
    \item Sergey Shpadyrev --- substantive review and idea input.
    \item Stanislav Tsukrov --- substantive external criticism and Core~1.3 criticism-response pressure.
\end{{itemize}}

\clearpage
"""


def _rewrite_frontmatter_for_133(source_dir: Path, *, doi: str | None, zenodo_record_url: str | None) -> None:
    frontmatter = source_dir / "content" / "frontmatter_oc_core_1_3_master.tex"
    write_text_if_changed(frontmatter, _frontmatter_133(doi, zenodo_record_url))


def _rewrite_raw_synthesis_support_inputs(source_dir: Path) -> None:
    """Replace generated raw K-dossier inputs with a reader-facing synthesis note.

    The historical 1.3 source contains generated K0-K12 dossier fragments with
    pass/fail/status rows. Those rows belong in evidence files, not in the
    public monograph reading path. The monolith still keeps a K-level synthesis
    appendix, but as prose that states claim scope, evidence class, and reopening
    conditions.
    """
    chapter_ref = Path("content/oc133_bounded_synthesis_chapter.tex")
    chapter_path = source_dir / chapter_ref
    chapter_lines = [
        r"\section{Bounded Synthesis of the K-Level Model Core}",
        r"\label{sec:oc-core-1-3-unified-synthesis}",
        _tex_paragraph(
            "This chapter replaces the historical generated synthesis status sheet with a publication-grade exposition. "
            "The scientific task is not to announce that every domain has been completed. The task is to show how the "
            "K-level witness taxonomy, typed carriers, realization predicates, finite witnesses, proof sheets, and "
            "bounded replay rows fit together as one model-core route."
        ),
        _tex_paragraph(
            "The chapter should be read with three limits in mind. First, a K-level distinction is promoted only where "
            "a witness or theorem route makes the distinction do work. Second, numerical rows are reconstruction and "
            "target-blind replay evidence inside declared protocols, not a claim that the whole scientific domain has "
            "been proved. Third, complete scientific coverage and unrestricted cross-science comparison are outside "
            "the promoted 1.3.3 public claim surface."
        ),
        r"\subsection{How the synthesis is organized}",
        _tex_paragraph(
            "The synthesis follows a reader-facing order rather than a machine-log order. Each level states its role, "
            "its current evidence class, the kind of reviewer challenge it answers, and the condition that would reopen "
            "the claim. Exhaustive hashes, verdict fields, and case rows remain in the evidence package and are cited "
            "from the monolith rather than pasted into the main prose."
        ),
    ]
    level_rows = [
        (0, "proto-continuum and zero-continuumness boundary", "the K-zero boundary theorem, the K0 resolution theorem, and finite semantic witnesses", "whether the model can distinguish absence of live realization from low-level structure"),
        (1, "minimal separability and first structured distinction", "typed carrier definitions and boundary predicates", "whether a lower projection can preserve the declared distinction"),
        (2, "early organization above separability", "operator semantics and low-level finite checks", "whether update rules add anything beyond static classification"),
        (3, "organized physical structures", "bounded replay rows and proof-boundary conditions", "whether physical examples are merely relabeled standard quantities"),
        (4, "chemical binding and composition routes", "chemistry replay rows, comparator notes, and operator boundaries", "whether composition is explained or just renamed"),
        (5, "excitable and biological organization", "biology replay rows and lifecycle semantics", "whether liveness, residue, and rebirth are formally separable"),
        (6, "cognitive and agent-scale organization", "phenomenon model cards and identity-boundary rules", "whether identity claims preserve declared invariants"),
        (7, "institutional and social organization", "systems model cards and falsifier routes", "whether social examples become metaphor rather than model instances"),
        (8, "civilizational and multi-layer coordination", "systems/civilizational replay rows and comparator boundaries", "whether aggregate patterns remain tied to observable protocols"),
        (9, "theory-level self-description", "claim/evidence governance and proof-register links", "whether the release can distinguish public claims from research targets"),
        (10, "meta-theoretic comparison", "novelty register and source-backed comparator matrix", "whether the work is only a reframing of prior art"),
        (11, "methodological and publication quality", "editorial criteria, science-state summaries, and reproducibility checks", "whether the artifact pipeline can prevent unsupported publication surfaces"),
        (12, "cross-model coherence under declared assumptions", "bounded synthesis evidence and adversarial review", "whether the declared model grammar remains coherent when projected across domains"),
    ]
    for level, role, evidence, challenge in level_rows:
        chapter_lines.extend(
            [
                rf"\subsection{{K{level}: {_tex_escape(role)}}}",
                _tex_paragraph(
                    f"K{level} contributes {role}. Its public release evidence is {evidence}. "
                    f"The reviewer challenge is {challenge}. The release claim is therefore scoped: the level is part "
                    "of the OC model-core grammar where its declared witness obligations are met."
                ),
                _tex_paragraph(
                    f"For K{level}, the claim reopens if a lower-level projection preserves every declared witness, if the "
                    "cited proof sheet loses an assumption, if the finite semantic case can be tampered with without failing, "
                    "or if a domain row no longer reproduces its stated observable under the pinned protocol. This is the "
                    "evidence-inclusion rule for this level: it must explain what it adds, how the evidence binds it, and "
                    "what would make the wording too strong."
                ),
            ]
        )
    chapter_lines.extend(
        [
            r"\subsection{What the bounded synthesis licenses}",
            _tex_paragraph(
                "The bounded synthesis licenses model-core claims about typed continuants, lawful realization, liveness, "
                "residue, boundary classification, hybrid update/flow structure, K-level witness distinctions, and "
                "selected target-blind replay rows. It does not license a public statement that all phenomena in all "
                "domains are already numerically predicted, nor a statement that all prior science has been surpassed."
            ),
            _tex_paragraph(
                "This distinction is a release requirement rather than a rhetorical caution. The public manuscript must "
                "teach the synthesis, cite the evidence, and preserve the ambition, while keeping the broader research "
                "obligations visible as obligations. That is the standard used by the 1.3.3 editorial and release gates."
            ),
        ]
    )
    write_text_if_changed(chapter_path, "\n\n".join(chapter_lines))
    write_text_if_changed(
        source_dir / "content" / "25_oc_core_1_3_toe_synthesis.tex",
        "\n".join(
            [
                "% OC Core 1.3.3 public monolith uses an integrated bounded synthesis chapter.",
                "% Generated status rows remain in the public evidence package and are not main prose.",
                rf"\input{{{chapter_ref.as_posix()}}}",
            ]
        ),
    )

    summary_ref = Path("content/oc133_bounded_synthesis_support_summary.tex")
    summary_path = source_dir / summary_ref
    lines = [
        r"\section{Bounded K-Level Synthesis Support Summary}",
        r"\label{sec:oc133-bounded-klevel-synthesis-support-summary}",
        _tex_paragraph(
            "This appendix replaces raw generated K-level status dossiers with a reader-facing synthesis summary. "
            "The machine-readable evidence package remains the place for exhaustive rows, hashes, and verdict fields. "
            "The public monograph keeps the scientific question visible: what structural role does each K-level play, "
            "what evidence class supports it, and what would reopen the claim?"
        ),
    ]
    for level in range(13):
        if level == 0:
            role = "proto-continuum and zero-continuumness boundary"
            evidence = "K0 proof route and finite semantic witness"
        elif level <= 2:
            role = "low-level structure, separation, and early organization"
            evidence = "typed model definitions, boundary predicates, and representative finite checks"
        elif level <= 5:
            role = "organized physical, chemical, and excitable structures"
            evidence = "bounded reconstruction rows and formal boundary conditions"
        elif level <= 8:
            role = "cognitive, social, institutional, and systems-scale organization"
            evidence = "model-card routes, replay QA rows, and comparator boundaries"
        else:
            role = "theory, meta-theory, and cross-model coherence under declared assumptions"
            evidence = "proof/evidence governance, comparator positioning, and adversarial reopening rules"
        lines.extend(
            [
                rf"\subsection{{K{level}: {_tex_escape(role)}}}",
                _tex_paragraph(
                    f"K{level} is included as a declared witness-taxonomy level, not as an unbounded domain-completion claim. "
                    f"Its current release role is {role}. The supporting evidence class is {evidence}. "
                    "A reviewer should read the level as a scoped part of the model grammar and should not infer that "
                    "every possible phenomenon at this level has already been explained or numerically predicted."
                ),
                _tex_paragraph(
                    f"The K{level} reopening condition is local. If the claimed level distinction can be projected away "
                    "without changing any declared witness, proof route, replay row, comparator boundary, or phenomenon "
                    "model card, then the level-specific public wording is too strong and must be repaired or demoted."
                ),
            ]
        )
    lines.append(
        _tex_paragraph(
            "This summary preserves the scientific content needed for the monograph while preventing generated status "
            "fields from becoming public prose. Exhaustive K-level rows remain available in the public evidence package "
            "for reviewers who need to inspect them mechanically."
        )
    )
    write_text_if_changed(summary_path, "\n\n".join(lines))
    auto_inputs = source_dir / "content" / "_auto_core_platinum_toe_support_inputs.tex"
    write_text_if_changed(
        auto_inputs,
        "\n".join(
            [
                "% OC Core 1.3.3 public monolith uses a prose K-level synthesis summary.",
                "% Exhaustive generated status rows remain in the evidence package.",
                rf"\input{{{summary_ref.as_posix()}}}",
            ]
        ),
    )


def _rewrite_public_appendix_wrappers(source_dir: Path) -> None:
    """Replace legacy process-oriented appendix wrappers with scholarly prose."""
    def input_refs(input_ref: str) -> list[str]:
        input_path = source_dir / input_ref
        if not input_path.exists():
            return []
        refs = re.findall(r"\\input\{([^}]+)\}", read_text(input_path))
        excluded_generated = (
            "oc133_bounded_synthesis_support_summary",
            "_auto_core_platinum",
            "_auto_core_inputs",
        )
        return [
            ref for ref in refs
            if not any(token in ref.lower() for token in excluded_generated)
        ]

    def digest_title(ref: str) -> str:
        parts = Path(ref).parts
        family = parts[-2].replace("_", " ").replace("-", " ").title() if len(parts) > 1 else "Source"
        stem = Path(ref).stem.replace("_", " ").replace("-", " ").title()
        return f"{family}: {stem}"

    def digest_paragraphs(ref: str) -> list[str]:
        lowered = ref.lower()
        if "k_levels" in lowered:
            role = "K-level role, axes, thresholds, and adjacent-level witness obligations"
            reviewer_use = "ask whether the level adds a non-inert observable and whether lawful demotion is available when it does not"
        elif "m_spaces" in lowered:
            role = "embedding-space assumptions and host conditions for the level vocabulary"
            reviewer_use = "ask whether a claimed realization has the host assumptions needed for the stated live or boundary status"
        elif "crossk" in lowered:
            role = "cross-level transition semantics and reduction-failure pressure"
            reviewer_use = "ask whether the proposed transition preserves a retained witness or collapses under a lower-level projection"
        elif "cycles" in lowered:
            role = "cycle, maintenance, and recurrence conditions"
            reviewer_use = "ask whether liveness is supported by an explicit cycle mode or non-vacuous maintenance predicate"
        elif "jets" in lowered:
            role = "flow/update information and local process structure"
            reviewer_use = "ask whether the public claim needs smooth dynamics, discrete update semantics, or only typed transition evidence"
        elif "processes" in lowered:
            role = "process schema, ordering, and change conditions"
            reviewer_use = "ask whether the process claim names the state, transition, boundary, and endpoint condition that make it testable"
        elif "operators" in lowered:
            role = "operator semantics and update admissibility"
            reviewer_use = "ask whether the operator is a smooth flow, a guard/reset update, a rewrite, or a typed non-smooth transformation"
        elif "theorems" in lowered:
            role = "historical theorem route and theorem-boundary pressure"
            reviewer_use = "ask whether the theorem label is current proof, historical route, definition, or future proof obligation"
        elif "complexity" in lowered:
            role = "complexity-functional vocabulary and limits"
            reviewer_use = "ask whether a complexity statement names the functional and transition before claiming increase or comparison"
        elif "experiments" in lowered:
            role = "experiment design and operational test route"
            reviewer_use = "ask whether the test has input, observable, comparator, expected output, and failure interpretation"
        elif "falsifiability" in lowered:
            role = "falsifier grammar and reopening condition"
            reviewer_use = "ask whether the claimed phenomenon would actually reopen under the stated falsifier"
        elif "predictions" in lowered:
            role = "prediction-route grammar and empirical promotion boundary"
            reviewer_use = "ask whether the row has formula, snapshot, comparator, uncertainty, residual, negative control, falsifier, and replay hash"
        else:
            role = "supporting module for the public scientific argument"
            reviewer_use = "ask whether the module is cited, bounded, and placed in the correct evidence class"
        label = digest_title(ref)
        return [
            f"For {label}, the scholarly synthesis contributes {role}, explains why this module exists, shows how it connects to the current 1.3.3 argument, and prevents stronger inherited language from being promoted without the current proof, replay, comparator, and falsifier surfaces.",
            f"For {label}, reader use is to {reviewer_use}; if that source-specific question cannot be answered from the promoted theorem, proof sheet, finite semantic case, replay table, comparator row, or claim-boundary section, the source remains background support rather than public theorem evidence.",
            f"For {label}, the audit route keeps the full file `{ref}` indexed by the science monolith corpus ledger and the public evidence package. The science is therefore not discarded, while the PDF avoids becoming a raw source dump. A line-level reviewer follows the ledger; a scientific reader follows this digest and the main chapter.",
            f"{label} reader checkpoint is satisfied only when the main manuscript tells the reader which claim class this module can support, which evidence class limits it, which prior-art or comparator boundary applies, and which failure would reopen the claim. This fourth check is deliberately positive: the module must contribute intelligibility, not merely avoid forbidden wording.",
            f"For {label}, the external wording boundary allows public language to say that the route helps organize, test, or constrain a bounded OC claim. It may not say that the route proves full-domain closure, final TOE status, universal superiority, or a domain result absent from the current proof and evidence layer. This boundary is part of the source's scientific content, not a marketing caveat.",
        ]

    def digest_block(title: str, intro: str, refs: list[str]) -> str:
        body = [rf"\subsection{{{_tex_escape(title)}}}", _tex_paragraph(intro)]
        current_family = ""
        for idx, ref in enumerate(refs, start=1):
            family = Path(ref).parts[-2] if len(Path(ref).parts) > 1 else "source"
            if family != current_family:
                current_family = family
                body.append(rf"\subsubsection{{{_tex_escape(family.replace('_', ' ').title())}}}")
            body.append(rf"\paragraph{{{_tex_escape(digest_title(ref))}}}")
            for paragraph in digest_paragraphs(ref):
                body.append(_tex_paragraph(paragraph))
            if idx % 12 == 0:
                body.append(
                    _tex_paragraph(
                        f"Synthesis checkpoint after {idx} indexed modules in {current_family}. The preceding modules teach inspection logic; they do not inflate "
                        "claim strength. The release remains bounded by the current proof and evidence surface."
                    )
                )
        return "\n\n".join(body)

    summary_appendices = {
        "G_oc_core_1_3_empirical_validation_matrix.tex": (
            "Empirical Evidence Boundary Appendix",
            "sec:oc-core-1-3-empirical-evidence-boundary-appendix",
            "This appendix summarizes the empirical evidence boundary for the public monograph. Executed target-blind and replay-QA rows are cited in the methods companion and distributed in the public evidence package. Planned or pending rows are not promoted as empirical validation.",
            "A promoted empirical row must carry formula, source snapshot, split or target-blind role, observed value, residual or uncertainty, comparator, negative control, falsifier, and replay hash. Rows without that complete stack remain protocol-ready or background research.",
        ),
        "H_oc_core_1_3_institute_run_measurement_program.tex": (
            "Institute Run Measurement Program Summary",
            "sec:oc-core-1-3-institute-run-measurement-program-summary",
            "This appendix records the measurement-program role without printing internal run boards. The public scientific point is that future research lanes are measured by evidence production, replay cleanliness, blocker closure, and claim-boundary discipline.",
            "Internal operational rows remain outside the public monograph. They can support governance and reproducibility reports, but they do not become scientific evidence unless routed through the public proof, data, comparator, or reviewer evidence stack.",
        ),
        "I_oc_core_1_3_domain_benchmark_manifest.tex": (
            "Domain Benchmark Manifest Summary",
            "sec:oc-core-1-3-domain-benchmark-manifest-summary",
            "This appendix explains benchmark selection at a reader-facing level. Physics, chemistry, biology, systems, and mathematics lanes are included as bounded replay and artifact-integrity examples, not as completed domain sciences.",
            "The full benchmark manifest is distributed in the evidence package. The monograph retains the selection rule, evidence ceiling, and reopening rule so a reviewer can distinguish executed lanes from planned benchmark expansion.",
        ),
        "L_oc_core_1_3_domain_benchmark_caseset.tex": (
            "Domain Benchmark Case-Set Summary",
            "sec:oc-core-1-3-domain-benchmark-caseset-summary",
            "This appendix deliberately does not print the raw case-set table because raw pending rows can make planned work look executed. Executed public rows are summarized in the methods companion and bound to the target-blind/replay evidence files.",
            "A pending case remains a research work order. It may be useful for the background science program, but it is not allowed to support release-promoted empirical wording until the replay stack is complete.",
        ),
        "J_oc_core_1_3_domain_replay_reports.tex": (
            "Domain Replay Report Summary",
            "sec:oc-core-1-3-domain-replay-report-summary",
            "This appendix summarizes the replay-report role. A replay report supports public evidence only when the replay result, comparator, residual, negative control, falsifier, and hash are present and consistent with the claim boundary.",
            "The complete replay reports remain machine-readable artifacts in the evidence package. This public summary prevents report status fields from being mistaken for completed empirical science.",
        ),
        "K_oc_core_1_3_domain_execution_board.tex": (
            "Domain Execution Board Summary",
            "sec:oc-core-1-3-domain-execution-board-summary",
            "This appendix records the boundary between execution management and public science. Execution boards schedule lanes and track work; they do not promote claims by themselves.",
            "The release promotes only the bounded rows that have completed evidence stacks. Future domain execution remains a background program governed by the same proof/data/comparator/reopening standard.",
        ),
    }
    for filename, (title, label, paragraph_one, paragraph_two) in summary_appendices.items():
        write_text_if_changed(
            source_dir / "appendix" / filename,
            "\n\n".join(
                [
                    rf"\section{{{title}}}",
                    rf"\label{{{label}}}",
                    _tex_paragraph(paragraph_one),
                    _tex_paragraph(paragraph_two),
                ]
            ),
        )
    write_text_if_changed(
        source_dir / "content" / "26_oc_core_1_3_practical_utility.tex",
        "\n\n".join(
            [
                r"\section{Practical Consequences, Bounded Replay Use, and Model-Comparison Limits}",
                r"\label{sec:oc-core-1-3-practical-utility}",
                _tex_paragraph(
                    "This chapter explains what a reader can practically do with OC Core 1.3.3 without turning practical "
                    "use into an unrestricted superiority claim. The practical use is not that OC replaces local physics, "
                    "chemistry, biological, systems, mathematical, or engineering methods. The use is that OC gives a "
                    "typed route for asking which claim is being made, which evidence can carry it, which comparator is "
                    "being respected, and which falsifier would reopen the statement."
                ),
                _tex_paragraph(
                    "The executable public use cases are bounded. Formal and finite-model rows help reviewers inspect "
                    "the model-core theorem surface. Target-blind and replay-QA rows help reviewers inspect selected "
                    "artifact-integrity and reconstruction examples. Comparator rows help reviewers distinguish overlap, "
                    "residual delta, and forbidden priority language. None of these rows is allowed to become a claim "
                    "that all science is numerically solved or that every modern model has been defeated."
                ),
                r"\subsection{Use-case families}",
                _tex_paragraph(
                    "Mathematics use is centered on exact question terminalization, finite semantic witnesses, proof-sheet "
                    "boundaries, and counterexample search. Physics and chemistry use is centered on pinned replay examples "
                    "where formula, observation, residual, comparator, negative control, falsifier, and hash can be inspected. "
                    "Biology and systems use is more explicitly model-bound, because the public rows depend on stronger "
                    "interpretive assumptions and therefore carry narrower claims. Cross-domain use is claim routing rather "
                    "than global replacement."
                ),
                r"\subsection{Comparator discipline}",
                _tex_paragraph(
                    "A comparator row is read as a same-claim boundary. If a local model family already carries the same "
                    "claim at the same assumptions, evidence strength, and cost boundary, OC receives no priority credit "
                    "for that claim. OC may still contribute by integrating the claim into a typed model-core package with "
                    "proof governance and replay discipline, but the wording must say integration rather than victory."
                ),
                r"\subsection{Practical audit route}",
                _tex_paragraph(
                    "The practical audit route is deliberately simple. Select a use case, identify the public claim boundary, "
                    "open the proof sheet or replay row, check the comparator and negative control, read the falsifier, and "
                    "then decide whether the public sentence is still within the evidence. The public evidence package "
                    "contains the complete machine-readable tables; this chapter preserves the scientific interpretation "
                    "without printing dense generated tables that damage page flow and text extraction."
                ),
                r"\subsection{Transition to the atlas}",
                _tex_paragraph(
                    "The Practical Utility and Model Comparison Atlas repeats the same boundary in appendix form. It is a "
                    "reader-facing digest, not a raw table wall. If the evidence package and this prose disagree, the claim "
                    "is reopened and repaired before any public release update."
                ),
            ]
        ),
    )
    write_text_if_changed(
        source_dir / "appendix" / "F_oc_core_1_3_reviewer_navigation_matrix.tex",
        "\n\n".join(
            [
                r"\section{Reviewer Objection Navigation Appendix}",
                r"\label{sec:oc13-reviewer-navigation}",
                _tex_paragraph(
                    "This appendix replaces the legacy compact route table with prose navigation. The old table was useful "
                    "as an internal checklist, but in a public monograph it produced broken text extraction and forced the "
                    "reader to reconstruct sentence order from narrow cells. The publication-grade route below keeps the "
                    "same reviewer questions while making the reading path explicit."
                ),
                r"\subsection{Core theorem route and scope}",
                _tex_paragraph(
                    "A reviewer should begin with the central defended result: bounded post-collapse identity classification "
                    "with no general lift theorem. The proof-bearing route begins in the results chapter and theorem roadmap, "
                    "then continues through the proof sheets and finite semantic witnesses. Collapse is formal only when "
                    "admissible-state emptiness, k-to-zero behavior, and threshold failure are tied to the stated assumptions. "
                    "Residue is a post-collapse structural trace, not a continuing live identity. Rebirth is a later live "
                    "continuum grounded in residue and treated as numerically new unless endpoint-bound identity evidence is supplied."
                ),
                r"\subsection{Upper-level and hierarchy questions}",
                _tex_paragraph(
                    "The K-level hierarchy is reviewed by asking whether the upper-level roles can be losslessly reduced. "
                    "If K11 and K12 collapse to K10 without loss of witness, boundary, or reflection behavior, the upper-level "
                    "claim reopens. If they preserve distinct declared roles, the hierarchy remains a witness taxonomy under "
                    "the current release scope. This is a reviewer test, not a claim of completed total metaphysics."
                ),
                r"\subsection{Journal-core and monograph relation}",
                _tex_paragraph(
                    "The monograph is larger than the journal core because it carries the didactic shell, formal architecture, "
                    "proof-route explanation, evidence-boundary method, and repair logic. The journal core is smaller because "
                    "it is an extraction, not a replacement. If the journal core changes theorem scope or hides a required "
                    "boundary, the extraction fails and must be repaired."
                ),
                r"\subsection{External criticism route}",
                _tex_paragraph(
                    "External criticism is treated as pressure on the manuscript, bibliography, evidence rows, replay method, "
                    "theorem fate, tuple/K rigor, and release package. Acknowledgement of a reviewer records substantive "
                    "pressure; it never implies endorsement. Predictive claims remain bounded unless the public artifact "
                    "contains protocol, data or code, output, comparator, and falsifier."
                ),
                r"\subsection{Decisive release-failure checks}",
                _tex_paragraph(
                    "A decisive failure is not a vague dislike of style. It is a continuing-identity claim after lawful death, "
                    "an excluded theorem family quietly entering the proof route, an empirical row without comparator or "
                    "falsifier being promoted as validation, a same-claim comparator absorbing the residual delta, a broken "
                    "public PDF, stale metadata, or a public claim that says more than its evidence can carry."
                ),
            ]
        ),
    )
    write_text_if_changed(
        source_dir / "appendix" / "M_oc_core_1_3_proof_machinery_appendix.tex",
        "\n\n".join(
            [
                r"\section{Proof Machinery Appendix}",
                r"\label{sec:oc13-proof-machinery-appendix}",
                _tex_paragraph(
                    "This appendix explains how proof obligations are read in the public monograph. It does not ask the "
                    "reader to treat release-status rows as mathematical evidence. The proof route has four layers: a "
                    "prose theorem statement with assumptions, a proof sheet with dependency references, a selected Lean "
                    "or finite semantic witness where applicable, and a reopening condition that states what would make "
                    "the wording too strong."
                ),
                r"\subsection{Proof-route authority}",
                _tex_paragraph(
                    "A promoted theorem-like statement is public only when the statement, assumptions, dependency route, "
                    "and boundary are visible. If a later empirical replay or comparator result contradicts a claimed "
                    "support route, the empirical or comparator repair is attempted first; if the contradiction persists, "
                    "the theorem scope is narrowed or reopened. This order protects the model core without hiding failed "
                    "evidence behind terminology."
                ),
                r"\subsection{Minimality and irreducibility reading rule}",
                _tex_paragraph(
                    "Minimality and K-level irreducibility are read as witness obligations. A component cannot be removed "
                    "if removal changes the declared semantic verdict, loses a retained witness, breaks a liveness or "
                    "boundary distinction, or collapses a theorem dependency. Conversely, an added observable may be "
                    "lawfully demoted when it is inert under the declared verdict suite. The finite-model evidence package "
                    "records executable cases for these distinctions."
                ),
                r"\subsection{Comparator and compression boundary}",
                _tex_paragraph(
                    "The release compares model-core structure against selected alternatives under declared assumptions. "
                    "It does not claim that every possible alternative has been defeated. A comparator statement is valid "
                    "only at the same claim class and cost boundary named in the comparator register. This keeps proof "
                    "machinery separate from rhetorical superiority."
                ),
                r"\subsection{Reader checklist}",
                r"\begin{itemize}[leftmargin=1.8em]",
                _tex_item("Theorem statement", "the public sentence must state the claim and its assumptions"),
                _tex_item("Dependency route", "the proof sheet, Lean declaration, finite case, or replay row must be named where it carries support"),
                _tex_item("Boundary", "the counterexample or reopening condition must be explicit"),
                _tex_item("No status substitution", "a status word, release row, or package flag is never a proof"),
                r"\end{itemize}",
            ]
        ),
    )
    write_text_if_changed(
        source_dir / "appendix" / "Q_oc_core_1_3_toe_support_dossiers.tex",
        "\n\n".join(
            [
                r"\section{Synthesis Support Digest}",
                r"\label{sec:oc-core-1-3-synthesis-support-dossiers}",
                _tex_paragraph(
                    "This digest explains how to inspect the bounded K-level synthesis without importing raw generated "
                    "dossiers into the public monograph. The main synthesis chapter states the scientific claim. The "
                    "evidence package carries the full machine-readable support rows and checksums."
                ),
                _tex_paragraph(
                    "A reader should inspect this route by asking whether a K-level row names its role, proof route, "
                    "replay boundary, comparator boundary, and reopening condition. If a raw dossier row is needed, the "
                    "corpus ledger points to it outside the reading path so the PDF remains a coherent manuscript."
                ),
                r"\subsection{Scholarly integration essay}",
                _tex_paragraph(
                    "The synthesis support material has a simple editorial purpose: it prevents a long cross-domain "
                    "model from becoming a sequence of disconnected demonstrations. The reader should see the same "
                    "discipline at every scale. A formal claim names the object grammar and its assumptions. A proof "
                    "claim names the theorem boundary. A computational claim names the finite or executable witness. "
                    "An empirical claim names the observable, comparator, uncertainty, negative control, and falsifier. "
                    "A prior-art claim names the overlap and the bounded residual difference. These are not separate "
                    "habits; together they are the reading grammar of the release."
                ),
                _tex_paragraph(
                    "The first integration burden is conceptual. OC Core 1.3.3 uses typed carriers, realizations, "
                    "lawful possibility, time-indexed liveness, residue, morphism, boundary, operator, cycle, dimension, "
                    "and K-level vocabulary. The support material is useful only if it makes those terms harder to misuse. "
                    "A reader should be able to ask, at any point in the monograph, which typed object is under discussion, "
                    "which relation preserves it, which boundary separates it, and which condition would make the statement "
                    "false or overbroad."
                ),
                _tex_paragraph(
                    "The second integration burden is evidential. The release is ambitious precisely because it refuses "
                    "to let ambition float free from evidence. The finite semantic checks do not prove every empirical "
                    "domain. The target-blind and replay rows do not mechanize every theorem. The comparator register does "
                    "not establish global priority. Each evidence family has its own authority and its own ceiling. The "
                    "scientific strength comes from making those ceilings visible and from refusing to promote a sentence "
                    "when the corresponding evidence family cannot carry it."
                ),
                _tex_paragraph(
                    "The third integration burden is didactic. A hostile reader should not have to guess why an appendix "
                    "exists. The appendix should lower the cost of verification: it should tell the reader which kind of "
                    "question to ask, which artifact class to open, and which failure would reopen the public wording. "
                    "That is why long machine rows are kept in the evidence package while the manuscript explains their "
                    "scientific role. The monograph is the argument; the package is the inspection apparatus."
                ),
                _tex_paragraph(
                    "The fourth integration burden is comparative. OC is not presented as a vocabulary that erases systems "
                    "theory, autopoiesis, dynamical systems, category-style formalisms, RAF closure, complexity measures, "
                    "identity theories, or reproducible-research standards. It is presented as a typed model-core release "
                    "that packages selected claims with proof boundaries, executable witnesses, replay discipline, and "
                    "explicit reopening rules. Where a predecessor already carries the same claim under the same assumptions, "
                    "OC receives no priority credit for that sentence."
                ),
                _tex_paragraph(
                    "The fifth integration burden is lifecycle clarity. The reader should not confuse death, residue, "
                    "rebirth, and identity. A dead continuum is not live by vocabulary alone. A residue is not the same "
                    "token as a continuing live identity. A rebirth relation is evidence-bound and target-bound. An identity "
                    "claim must preserve the declared invariant. These distinctions are central because they make the model "
                    "criticizable: a reviewer can attack the invariant, the endpoint relation, the admissibility condition, "
                    "or the evidence row instead of arguing against a vague metaphysical label."
                ),
                _tex_paragraph(
                    "The sixth integration burden is empirical humility without empirical retreat. The public replay rows "
                    "are included because they force the package to demonstrate source discipline, numeric reconstruction, "
                    "comparators, residuals, controls, and falsifiers. They are not included to pretend that all science has "
                    "already been numerically exhausted. This is a stronger public posture than overclaiming: it gives a "
                    "critic exact handles, and it gives future research a precise path for promotion."
                ),
                _tex_paragraph(
                    "The seventh integration burden is release accountability. A scientific release can fail even when "
                    "its code compiles if the public PDF is unreadable, the title page is absent, the bibliography is thin, "
                    "the theorem boundary is hidden, the evidence rows are printed without interpretation, or the archive "
                    "metadata misleads the reader. The synthesis support material therefore belongs to the manuscript only "
                    "where it improves the reader's understanding. Everything else belongs in the evidence package."
                ),
                _tex_paragraph(
                    "The final integration burden is continuity from this release to later work. OC Core 1.3.3 is a bounded "
                    "external-review release, while the larger all-domain science program remains active. This distinction "
                    "does not weaken the release. It protects it. A later release may promote stronger claims only by adding "
                    "the missing proof, replay, comparator, and falsifier layers. Until then, the public monograph must show "
                    "both the current achievement and the exact boundary of what has not yet been earned."
                ),
                _tex_paragraph(
                    "A practical reading exercise makes this concrete. Take any strong sentence in the release and ask four "
                    "questions in order. First, what is the typed object or relation named by the sentence? Second, which "
                    "proof, finite witness, replay row, or comparator row is allowed to support it? Third, what is the "
                    "strongest adjacent sentence that the evidence does not support? Fourth, what observation, countermodel, "
                    "failed build, failed replay, or stronger comparator would reopen it? If the reader can answer all four, "
                    "the sentence belongs in the release. If not, it belongs in the research backlog or evidence package."
                ),
                _tex_paragraph(
                    "This exercise also explains why the manuscript and the machine-readable package have different jobs. "
                    "The manuscript teaches the scientific object and the boundaries of its current evidence. The package "
                    "lets a reviewer inspect exact rows, hashes, and files. Confusing the two was the failure mode corrected "
                    "in the 1.3.3 repair: rows and hashes are necessary for reproducibility, but they do not become a readable "
                    "scientific argument until the manuscript explains their conceptual role, their evidential ceiling, and "
                    "their reopening condition."
                ),
                _tex_paragraph(
                    "The editorial consequence is that every major document in the release must answer the same set of "
                    "reader questions from a different distance. The guide answers what to open first and why. The journal "
                    "core answers what the central contribution is. The monograph answers how the model, proof surface, "
                    "evidence surface, comparison boundary, and reviewer response cohere. The methods companion answers "
                    "how to reproduce or challenge the evidence. The reviewer map answers where the strongest objections "
                    "land. A defect in any one document is therefore not a cosmetic issue; it weakens the whole public "
                    "scientific surface unless the other documents still give a coherent route to the same claim boundary."
                ),
                _tex_paragraph(
                    "A second practical exercise is to read the release backward. Start with a hostile objection, move to "
                    "the attacked claim, then to the proof sheet or replay row, then to the formal definition that makes the "
                    "claim meaningful. If the backward path breaks, the objection has found a real weakness. If the path "
                    "holds, the reader can see exactly why the release is bounded but still strong. This backward reading "
                    "is especially important for claims about liveness, residue, rebirth, K-level witnesses, operator "
                    "semantics, and empirical replay, because each of those areas is easy to overstate when presented only "
                    "as narrative."
                ),
                _tex_paragraph(
                    "The support synthesis also protects future work from drift. When a later release expands empirical "
                    "lanes or promotes a stronger theorem, the new claim should enter through the same gates: typed object, "
                    "assumption set, proof or executable witness, comparator boundary, negative control where empirical, "
                    "and falsifier. This means that the 1.3.3 monograph is not merely a document about the current model; "
                    "it is a public example of how OC claims must be promoted if they are to remain scientifically inspectable."
                ),
                r"\subsection{Inspection route}",
                _tex_paragraph(
                    "Start with the current T133 proof surface, then compare the relevant K-level role with the finite "
                    "semantic case and lawful-demotion rule. Use the public comparator rows only for positioning, not for "
                    "priority. Treat future full-domain synthesis as a background research obligation unless a later "
                    "release supplies theorem, replay, comparator, negative-control, and falsifier evidence."
                ),
                digest_block(
                    "K-level synthesis source digest",
                    "The full synthesis support route is represented here as a reading digest. The exact source and "
                    "checksum remain in the evidence package; this text explains how a reviewer should use the source "
                    "without turning the monograph into a generated dossier.",
                    input_refs("content/_auto_core_platinum_toe_support_inputs.tex"),
                ),
            ]
        ),
    )
    write_text_if_changed(
        source_dir / "appendix" / "R_oc_core_1_3_practical_utility_model_comparison_atlas.tex",
        "\n\n".join(
            [
                r"\section{Practical Utility and Model Comparison Atlas}",
                r"\label{sec:oc-core-1-3-practical-utility-atlas}",
                _tex_paragraph(
                    "This appendix gives a reader-facing map from OC Core 1.3.3 to practical use cases and "
                    "same-claim model-comparison boundaries. The complete machine-readable tables remain in the "
                    "public evidence package; the monograph carries the scholarly digest: what can be used, what "
                    "must be checked, what remains open, and how a reviewer can reopen an overstated comparison."
                ),
                _tex_paragraph(
                    "The comparison rule is deliberately strict. A row may say that OC provides a typed route, a "
                    "proof-to-observable bridge, a replay discipline, or a claim-boundary mechanism. It may not say "
                    "that OC defeats a comparator family unless the same public row supplies the comparator baseline, "
                    "replay result, uncertainty or residual, negative control, and falsifier."
                ),
                r"\subsection{Reader-facing comparison rows}",
                _tex_paragraph(
                    "The atlas should be read as positioning plus operational guidance. For mathematics, the current "
                    "use case is exact-question terminalization and counterexample search. For physics, chemistry, "
                    "biology, and systems lanes, the use case is bounded replay QA against pinned public evidence rows. "
                    "For cross-domain coordination, the use case is disciplined claim routing rather than global "
                    "comparative superiority."
                ),
                r"\subsection{Audit trail}",
                _tex_paragraph(
                    "The evidence package contains the full comparison table, trace anchors, and readiness/frontier "
                    "rows. The public bundle records checksums in checksums.txt and manifest.json. If the evidence "
                    "package and the prose disagree, the prose is reopened and repaired before publication."
                ),
                r"\subsection{Machine-readable table reference}",
                _tex_paragraph(
                    "The generated comparison table is distributed in the evidence package instead of being printed as "
                    "a dense table wall in the monograph. This keeps the public PDF readable while preserving the exact "
                    "rows, checksums, and audit trail for reviewers who need machine-level inspection."
                ),
            ]
        ),
    )
    write_text_if_changed(
        source_dir / "appendix" / "O_oc_core_1_3_technical_derivation_atlas.tex",
        "\n\n".join(
            [
                r"\section{Technical Derivation Digest}",
                r"\label{sec:oc-core-1-3-technical-derivation-atlas}",
                _tex_paragraph(
                    "The technical derivation corpus is preserved in the evidence package and corpus ledger. The public "
                    "monograph prints only the reader-facing digest because a scientific manuscript should not ask the "
                    "reader to traverse hundreds of generated derivation leaves before the main argument is clear."
                ),
                r"\subsection{How the technical corpus is used}",
                _tex_paragraph(
                    "The derivation corpus supports definitions, operator semantics, K-level examples, and falsifier "
                    "routes. It is not the promoted theorem surface by itself. A promoted theorem still has to point to "
                    "a proof sheet, Lean declaration when present, finite semantic witness where relevant, and a stated "
                    "counterexample boundary."
                ),
                r"\subsection{Where the full corpus lives}",
                _tex_paragraph(
                    "The full technical derivation files remain in the release source tree and are indexed by the science "
                    "monolith corpus ledger with hashes and inclusion roles. Reviewers who need the raw derivations should "
                    "use that ledger and the public evidence package rather than the prose PDF."
                ),
                digest_block(
                    "Technical scholarly synthesis",
                    "The technical scholarly synthesis replaces the earlier raw atlas. It walks the same source families "
                    "top-down, but each entry now states scientific role, reader use, and audit route instead of dumping "
                    "unintegrated source text into the public PDF.",
                    input_refs("content/_auto_core_platinum_technical_appendix_inputs.tex"),
                ),
            ]
        ),
    )
    write_text_if_changed(
        source_dir / "appendix" / "P_oc_core_1_3_reference_benchmark_atlas.tex",
        "\n\n".join(
            [
                r"\section{Reference and Benchmark Digest}",
                r"\label{sec:oc-core-1-3-reference-benchmark-atlas}",
                _tex_paragraph(
                    "The experiment, falsifiability, and prediction corpus is preserved as evidence, not printed as a "
                    "large raw atlas in the monograph. The public PDF gives the reading method and the boundaries; the "
                    "evidence package carries the exact rows, source files, and hashes."
                ),
                r"\subsection{Prediction and falsifier reading rule}",
                _tex_paragraph(
                    "A prediction row is public only when it names a formula or reconstruction rule, a source snapshot, "
                    "a comparator, an uncertainty or residual, a negative control, a falsifier, and a replay hash. Older "
                    "prediction language that lacks those fields remains an archival route and cannot promote a release claim."
                ),
                r"\subsection{Benchmark evidence route}",
                _tex_paragraph(
                    "The benchmark rows are useful because they show how a claim would be checked. They do not imply that "
                    "every domain has been completed. The corpus ledger records the full benchmark tree so reviewers can "
                    "audit coverage without turning the monograph into an index dump."
                ),
                digest_block(
                    "Reference, falsifier, and prediction scholarly synthesis",
                    "The reference scholarly synthesis replaces the earlier benchmark atlas dump. It keeps the same "
                    "experiment, falsifier, and prediction corpus visible while forcing each route to state what it can "
                    "support, how it would be checked, and what would reopen it.",
                    input_refs("content/_auto_core_platinum_reference_appendix_inputs.tex"),
                ),
            ]
        ),
    )


def _rewrite_legacy_theorem_results_for_public_boundary(source_dir: Path) -> None:
    """Project legacy theorem material into the current bounded claim surface.

    The full 1.3 corpus remains included, but the public 1.3.3 monograph must
    not let older theorem labels outrun the current T133 proof/evidence
    boundary. This rewrite preserves the chapter and its order while making the
    claim status explicit in the prose and TOC.
    """
    path = source_dir / "content" / "04_results.tex"
    if not path.exists():
        return
    routes = [
        (
            "dimension-birth route",
            "The historical text used monotonic dimensionality as a universal theorem. In the 1.3.3 public surface this is read only as a declared witness route: if a promoted case says that a new axis is born, the proof or finite witness must identify the added axis, the retained lower-level observable, and the condition under which the lower representation loses the relevant verdict.",
        ),
        (
            "axis-availability route",
            "The historical text said that spontaneous dimension creation is impossible. In the 1.3.3 public surface the promoted claim is narrower: a declared dimensional lift must name an admissible axis or mark the lift as unsupported. This is a model-boundary rule, not an unrestricted physical law.",
        ),
        (
            "death and residue route",
            "The historical death theorem is retained as a lifecycle route. The promoted 1.3.3 claim is the typed one: liveness, death, residue, and rebirth are separated by the stated status predicates and source-target relations. Any stronger empirical reading requires a domain-specific observable and falsifier.",
        ),
        (
            "embedding-compatibility route",
            "The historical embedding statements are read as compatibility obligations. A continuum instance may not claim a live realization unless the carrier, realization, boundary, and admissible-space assumptions have been stated. This does not assert a completed ontology of all possible embedding spaces.",
        ),
        (
            "threshold-transition route",
            "The historical tension-and-threshold language is preserved as a modeling grammar. A promoted theorem or prediction must still define the threshold, the measured or formal quantity compared with it, and the reopening condition. Otherwise the row remains a route, not a finished theorem.",
        ),
        (
            "complexity-growth route",
            "The historical universal complexity-growth statement is not promoted as an unrestricted law. In 1.3.3 it is a scoped route: complexity growth may be claimed only for a declared complexity functional, a declared transition, and a proof or replay path showing that the functional changes as stated.",
        ),
        (
            "stabilization route",
            "The historical no-eternal-stabilization statement is not a public claim about every live system. It is a stress-test route: if a model claims permanent stabilization, it must specify the flows, thresholds, embedding assumptions, and invariant-preservation conditions that make the claim meaningful.",
        ),
        (
            "cycle-support route",
            "The historical cycle-collapse statements are retained where cycle support is part of the typed model. A promoted claim must distinguish absence of a cycle, failure of a supporting flow, boundary contact, and status change; these are not interchangeable failure modes.",
        ),
        (
            "expressivity route",
            "The historical threshold-expressivity route is a useful reviewer test: a representation that cannot express a required distinction cannot carry the corresponding verdict. In 1.3.3 this route is used through theorem-specific assumptions and finite semantic witnesses.",
        ),
        (
            "incompleteness route",
            "The historical incompleteness-of-embedding-space language is retained only as a boundary discipline. It prevents overclaiming a fixed representation as universal; it is not itself a proof of universal OC priority.",
        ),
        (
            "operator route",
            "The historical operator consequences are promoted only where the current operator semantics, hybrid laws, guard/reset cases, or lifecycle morphisms support the exact public wording.",
        ),
        (
            "cross-level route",
            "The historical cross-level consequences are read as a K-level witness-taxonomy route. They do not by themselves prove that every adjacent level is ontologically irreducible; irreducibility requires the named retained witness, reduction-failure criterion, demotion criterion, and executable case.",
        ),
    ]
    lines = [
        r"% FILE: content/04_results.tex",
        r"\section{Historical Legacy Result Routes and Current Claim Boundaries}",
        r"\label{sec:results}",
        _tex_paragraph(
            "This chapter preserves the result routes inherited from the full Core corpus while preventing those routes "
            "from outrunning the current OC Core 1.3.3 proof surface. A legacy theorem route is not automatically a "
            "promoted theorem. It becomes release-promoted only where the current claim register, proof sheet, Lean "
            "subset, finite semantic witness, comparator row, or bounded replay row supports the exact wording and assumptions."
        ),
        _tex_paragraph(
            "The public reading is therefore explicit. Broad domain-independent, all-level, universal, or total-science "
            "readings remain historical ambitions unless they are matched by the T133 evidence surface. The routes below "
            "are kept because they explain how the model developed and because they give reviewers a map of what has to "
            "be checked before a stronger claim may be promoted."
        ),
        _tex_paragraph(
            "For each route the release asks four questions: what distinction is being attempted, which typed OC "
            "construction carries it, which current evidence class can support it, and what condition would reopen it. "
            "This turns the older result chapter into a claim-boundary instrument rather than a list of unrestricted theorems."
        ),
    ]
    for idx, (title, body) in enumerate(routes, start=1):
        lines.extend(
            [
                rf"\subsection{{Legacy route {idx}: {_tex_escape(title)}}}",
                _tex_paragraph(body),
                _tex_paragraph(
                    "Promotion rule. The route may appear as a public theorem only when the promoted statement names "
                    "its assumptions, proof route, executable witness or replay row when relevant, comparator boundary, "
                    "and falsifier. Without those items it remains a background route in the monograph and cannot be used "
                    "as evidence for final TOE, full-domain prediction, or superiority over all modern science."
                ),
                _tex_paragraph(
                    f"For legacy route {idx}, reviewer reopening occurs if the visible public wording is stronger than the "
                    "current proof sheet, if the finite witness is only self-confirming, if the comparator row absorbs the "
                    "claimed residual delta, or if a domain example lacks an observable, uncertainty or falsifier."
                ),
            ]
        )
    lines.extend(
        [
            r"\subsection{Current promoted theorem surface}",
            _tex_paragraph(
                "The current promoted theorem surface is the T133 proof suite and its supporting artifacts: typed "
                "foundation, proof sheets, Lean subset, finite semantic checks, and claim-boundary records. The historical "
                "routes in this chapter help explain the origin of the questions, but the T133 artifacts carry the current "
                "release claims."
            ),
        ]
    )
    write_text_if_changed(path, "\n\n".join(lines))


def _rewrite_klevel_and_prediction_boundaries(source_dir: Path) -> None:
    """Demote unsupported K-level/K13/global-minimality overclaims in copied sources."""
    model = source_dir / "content" / "03_model.tex"
    if model.exists():
        text = read_text(model)
        text = text.replace(
            "All definitions in this section are\nmodel-vocabulary-level at the level of formal vocabulary.",
            "All definitions in this section provide a shared model vocabulary."
        )
        text = text.replace(
            "The tuple above is minimal in the following verdict-invariant sense.",
            "The tuple above is nonredundant only in the declared component-wise verdict-witness sense used by OC Core 1.3.3."
        )
        text = text.replace(
            r"\paragraph{Theorem (global verdict-invariant minimality).}",
            r"\paragraph{Claim-boundary result (component-wise witness independence).}"
        )
        text = text.replace(
            "For the class of OC-compatible verdict-preserving representations, each\n"
            "primitive distinction represented by the OC interface is necessary up to\n"
            "definitional equivalence.",
            "Within the declared finite semantic verdict suite, each primitive distinction represented by the current OC release tuple has a keep/drop witness. The result does not claim unrestricted global minimality among all possible theories or representations."
        )
        text = text.replace(
            "Hence every\nverdict-preserving OC representation must preserve \\(\\pi_p\\) up to definitional\n"
            "equivalence.",
            "Hence a representation that claims to preserve this declared verdict suite must preserve the tested distinction \\(\\pi_p\\), or else supply an explicitly equivalent invariant."
        )
        write_text_if_changed(model, text)

    klevel = source_dir / "content" / "10_klevels_full.tex"
    if klevel.exists():
        text = read_text(klevel)
        text = re.sub(
            r"\\section\{Full Hierarchy of Continua.*?\}",
            r"\\section{K0--K12 Witness Taxonomy and Claim Boundaries}",
            text,
            count=1,
            flags=re.S,
        )
        text = re.sub(
            r"This chapter provides the complete reconstructed description.*?present chapter expands each level into its full structural definition\.",
            (
                "This chapter gives the public K0--K12 witness taxonomy used by OC Core 1.3.3. "
                "The levels are declared modeling roles with axes, observables, thresholds, and witness obligations. "
                "They are not promoted here as a completed ontological proof that every adjacent level is irreducible in every domain. "
                "Irreducibility is promoted only where the current K-level proof sheet, finite transition semantics, reduction-failure criterion, and lawful-demotion criterion support the exact adjacent transition."
            ),
            text,
            count=1,
            flags=re.S,
        )
        text = re.sub(
            r"Core~?1\.3 fixes the hierarchy.*?leave the\s+monograph internally inconsistent\.",
            (
                "OC Core 1.3.3 retains K0--K12 because the source corpus contains upper-level modules and because the "
                "current public release needs a stable vocabulary for upper-taxonomy review. Retention is not the same "
                "thing as unrestricted proof. A level is scientifically active only where its witness burden is named and checked."
            ),
            text,
            count=1,
            flags=re.S,
        )
        text = re.sub(
            r"The vertical hierarchy of continua is monotonic:.*?that cannot be reduced to those of lower\s+levels\.",
            lambda _match: (
                "The vertical ordering is read as a witness taxonomy:\n"
                "\\[\n"
                "    K_0 \\leadsto K_1 \\leadsto K_2 \\leadsto \\dots\n"
                "    \\leadsto K_{10} \\leadsto K_{11} \\leadsto K_{12}.\n"
                "\\]\n"
                "A transition may be promoted as irreducible only when a retained witness is lost under the proposed "
                "lower-level reduction and when the added observable is not inert. If the added observable is inert, the "
                "lawful demotion rule sends the row back to the lower level."
            ),
            text,
            count=1,
            flags=re.S,
        )
        text = text.replace(
            r"A global summary is shown in Table~\ref{tab:klevels-summary}.",
            r"A reviewer-facing witness summary is shown in Table~\ref{tab:klevels-summary}.",
        )
        text = text.replace(
            r"\caption{Global overview of continua \texorpdfstring{\(K_0\)}{K0}–\(K_{12}\).}",
            r"\caption{Reviewer-facing witness taxonomy for \texorpdfstring{\(K_0\)}{K0}--\(K_{12}\).}",
        )
        text = re.sub(
            r"Each level requires an embedding space.*?to host the continua of that level\.",
            lambda _match: (
                "The corresponding embedding-space notation records declared host assumptions. It is a modeling "
                "constraint, not a public proof that the listed spaces form a universal chain for all possible continua."
            ),
            text,
            count=1,
            flags=re.S,
        )
        write_text_if_changed(klevel, text)

    # K13 language is not part of the promoted 1.3.3 release. Keep the section
    # slot but replace the prediction with an explicit background-research boundary.
    for pred in (source_dir / "content" / "predictions").glob("predictions_k12*.tex"):
        text = read_text(pred)
        text = re.sub(
            r"\\subsubsection\{P7: Predictions for Transition Beyond.*?\\subsubsection\{Summary\}",
            lambda _match: (
                "\\subsubsection{P7: Boundary of Public K12 Claims}\n\n"
                "OC Core 1.3.3 does not promote a public K13 prediction. The older source corpus used a beyond-K12 "
                "section as a speculative pressure test for model-dynamics. In the corrected public release this material "
                "is retained only as a background research obligation: any future level beyond K12 would require its own "
                "carrier, observable, added axis, reduction-failure witness, lawful-demotion rule, comparator boundary, "
                "negative control, and falsifier before it could become a promoted claim.\n\n"
                "\\subsubsection{Summary}"
            ),
            text,
            count=1,
            flags=re.S,
        )
        text = re.sub(r"predictable transitions toward hypothetical\s+\$K_\{13\}\$\.?", "no promoted beyond-K12 transition claim in this release.", text)
        text = re.sub(r"\\exists\\\s*K_\{13\}.*?(?=\\paragraph|\\subsubsection|%|\Z)", "No public K13 existence claim is promoted in OC Core 1.3.3.\n\n", text, flags=re.S)
        write_text_if_changed(pred, text)

    for path in list((source_dir / "content").rglob("*.tex")) + list((source_dir / "appendix").rglob("*.tex")):
        text = read_text(path)
        original = text
        text = re.sub(r"\bglobal verdict-invariant minimality theorem\b", "component-wise witness independence result for the declared semantic verdict suite", text, flags=re.I)
        text = re.sub(r"\bglobal verdict-invariant minimality\b", "component-wise witness independence for the declared semantic verdict suite", text, flags=re.I)
        text = re.sub(r"\bglobal minimality theorem\b", "component-wise witness independence result for the declared semantic verdict suite", text, flags=re.I)
        text = re.sub(r"\bglobal minimality\b", "component-wise witness independence for the declared semantic verdict suite", text, flags=re.I)
        text = re.sub(r"\bdomain-independent at the level of formal vocabulary\b", "shared at the level of declared model vocabulary", text, flags=re.I)
        text = re.sub(r"\bglobal lower bound\b", "component-wise lower-bound route under declared witnesses", text, flags=re.I)
        text = re.sub(r"\blower bound on every OC-compatible representation\b", "component-wise lower-bound route for the declared semantic verdict suite", text, flags=re.I)
        text = re.sub(r"\bdomain[-–— ]independent theorem\b", "bounded model-route claim", text, flags=re.I)
        text = re.sub(r"\bdomain[-–— ]independent consequences\b", "scoped model-route consequences", text, flags=re.I)
        text = re.sub(r"\bUniversal law of complexity growth\b", "Scoped complexity-growth route", text, flags=re.I)
        text = re.sub(r"\bNo Stable Termination of Model-Dynamics\b", "Background model-dynamics termination question", text, flags=re.I)
        text = re.sub(r"\bpredicts that K12 cannot serve\s+as a final level\b", "records, as a background research question, that K12 may not be the final possible modeling vocabulary", text, flags=re.I)
        text = re.sub(r"\bpredictable transitions toward hypothetical\s+K13\b", "no promoted beyond-K12 transition claim in this release", text, flags=re.I)
        text = re.sub(r"\\subsection\{(?:Universal|scoped)\s+Falsifiability\s+Criteria\}", r"\\subsection{Bounded Falsifiability Criteria}", text, flags=re.I)
        text = re.sub(r"\\subsection\{(?:Universal|scoped)\s+Prediction\s+Constraints\}", r"\\subsection{Bounded Prediction Constraints}", text, flags=re.I)
        text = re.sub(r"\\subsection\{(?:Universal|scoped)\s+Schema\s+of\s+a\s+Process\}", r"\\subsection{Process Schema Under Declared Scope}", text, flags=re.I)
        text = re.sub(r"\\subsection\{Process\s+Schema\s+Under\s+scoped\}", r"\\subsection{Process Schema Under Declared Scope}", text, flags=re.I)
        if text != original:
            write_text_if_changed(path, text)


def _rewrite_public_criticism_appendix(source_dir: Path) -> None:
    """Replace raw criticism closure tables with public prose review synthesis."""
    path = source_dir / "appendix" / "S_oc_core_1_3_external_criticism_closure.tex"
    if not path.exists():
        return
    rows = [
        ("Citations and prior art", "The release now treats prior traditions as scientific context rather than decorative naming. Public wording is narrowed to typed OC packaging, collapse/residue/rebirth grammar, and explicit claim-boundary discipline."),
        ("Civilization and systems examples", "Systems language is bounded to scenario replay, diagnostic signatures, or held-out benchmark rows. Unsupported civilization-scale explanation remains a research obligation."),
        ("General systems theory and autopoiesis", "The comparator route states overlap and residual delta rather than claiming that OC replaces the source traditions."),
        ("Higher-order mathematics", "Higher-order notation is useful where it clarifies the model, but it is not promoted as a prediction engine until proof and calibration routes are present."),
        ("K-level necessity", "K-level roles require lossless-reduction tests, witnesses, and falsifiers. Upper levels remain bounded taxonomy unless the evidence class makes their additional work visible."),
        ("Observables and prediction", "Observable language is public only when the observable has a definition, success condition, comparator, and proof or replay route."),
        ("Physics and empirical claims", "Physics wording is tied to structural/operator signatures unless a row supplies formula, data route, predicted value, uncertainty, comparator, and falsifier."),
        ("Theorem labels", "The release distinguishes historical theorem routes, promoted T133 proof sheets, definitions, axioms, and future proof obligations."),
        ("Tuple criticism", "Tuple components carry primitive or derived roles only where ablation consequences and proof obligations make that role visible."),
    ]
    lines = [
        r"\section{External Criticism Closure Synthesis}",
        r"\label{sec:oc13-external-criticism-closure}",
        _tex_paragraph(
            "This appendix records the scientific response to the external criticism corpus as prose. Raw source files, "
            "status tokens, changed-file lists, and duplicate-resolution rows remain in the evidence package. The public "
            "monograph keeps the reviewer-relevant result: what criticism was raised, how the claim boundary changed, "
            "and what would reopen the issue."
        ),
        r"\subsection{How to read this appendix}",
        _tex_paragraph(
            "A criticism row is closed only as far as the named claim boundary and evidence class allow. A response may "
            "repair a definition, demote a claim, add a proof route, add a replay protocol, or mark an obligation as "
            "future research. None of those actions is a claim of complete scientific coverage."
        ),
    ]
    for title, body in rows:
        lines.extend(
            [
                rf"\subsection{{{_tex_escape(title)}}}",
                _tex_paragraph(body),
                _tex_paragraph(
                    f"The reopening condition for {title} is direct: if a cited proof route, comparator boundary, replay "
                    "row, or claim demotion no longer matches the public wording, the response is no longer closed and "
                    "the public text must be repaired before publication."
                ),
            ]
        )
    write_text_if_changed(path, "\n\n".join(lines))


def _rewrite_public_science_projection_sources(source_dir: Path) -> None:
    """Apply the public-scientific projection layer to copied build sources."""
    _rewrite_legacy_theorem_results_for_public_boundary(source_dir)
    _rewrite_klevel_and_prediction_boundaries(source_dir)
    _rewrite_public_criticism_appendix(source_dir)
    replacements = {
        "Reviewer Response and Journal Preparation": "Reviewer Objections and Scientific Response",
        "Source Witnessing, Theorem Fate, and Publication Boundary": "Corpus Provenance and Claim-Boundary Narrative",
        "publication boundary": "public claim boundary",
        "Publication boundary": "Public claim boundary",
        "release-blocking conditions": "scientific reopening conditions",
        "release-control": "claim-boundary",
        "release control": "claim-boundary",
        "journal preparation": "journal-facing reader route",
        "Journal Preparation": "Journal-Facing Reader Route",
        "exposes their structural substrate": "offers a structural description under declared assumptions",
        "replace disparate domain-specific mechanisms with a declared model structure": "relate selected domain mechanisms to a declared model structure",
        "replaces disparate domain-specific mechanisms with a declared model structure": "relates selected domain mechanisms to a declared model structure",
        "K11/K12 now stand under a locked irreducibility result beyond K10": "K11/K12 remain upper-taxonomy obligations under bounded witness review",
        "PROVED_NECESSARY_BEYOND_K10": "UPPER_TAXONOMY_REVIEW_REQUIRED",
        "K11 captures meta-theoretical reflexivity as irreducible scientific work beyond K10 across the bounded domain-lane atlas.": "K11 is retained as a meta-theoretical witness-taxonomy level where reflexive structure is explicitly used by the declared claim route.",
        "K12 packages declared semantic coherence across the bounded domain-lane atlas because cross-domain meaning remains jointly interpretable and no surviving global falsifier breaks the bounded synthesis.": "K12 is retained as an upper-coherence taxonomy marker under declared assumptions; it does not by itself assert completed all-domain semantic closure.",
        "K12 packages global semantic coherence across the closed domain atlas because cross-domain meaning remains jointly interpretable and no surviving global falsifier breaks the unified synthesis.": "K12 is retained as an upper-coherence taxonomy marker under declared assumptions; it does not by itself assert completed all-domain semantic closure.",
        "Q, R, S, and U bind semantic coherence, global compatibility, and reference stability into the final unified-science synthesis layer.": "The support appendices bind semantic-coherence candidates, compatibility checks, and reference stability into the bounded synthesis layer.",
        "This chapter states the promoted synthesis projected from the canonical science SPOT.": "This chapter states the bounded synthesis projected from the current science state.",
        "lawfully promoted unified synthesis": "bounded synthesis",
        "Cross-domain /\\allowbreak unified science": "Cross-domain /\\allowbreak coordination",
        "cross-domain/unified science": "cross-domain coordination",
        "unified science": "bounded synthesis",
        "Unified science": "Bounded synthesis",
        "unified promotion discipline": "shared claim-boundary discipline",
        "cross-domain scientific planning and explanation": "cross-domain coordination under declared evidence limits",
        "cross-domain integration and multiscale explanation": "cross-domain coordination and multiscale positioning under declared evidence limits",
        "one declared model-core kernel, one declared K-level ladder, one declared theorem-to-observable grammar, and one atlas": "a declared model-core kernel, a K-level witness taxonomy, a theorem-to-observable grammar, and a bounded comparison atlas",
        "The final promotion rule is parallel": "The bounded promotion rule is parallel",
        "hostile-review blocker total must be zero": "adversarial-review blocker total must be zero before the corresponding wording is promoted",
        "The minimality ledger currently records `2` components marked necessary under the current proof stack and `2` frontier components whose strict irreducibility is not yet fully closed.": "The current 1.3.3 minimality witness route records component-wise keep/drop witnesses for all 11 declared release-tuple components in the finite semantic suite, with Lean binding for the corresponding typed witness schema. Frontier candidates beyond that declared tuple remain research obligations rather than part of the promoted T133-MIN theorem.",
        "The minimality register currently records `2` components marked necessary under the current proof stack and `2` frontier components whose strict irreducibility is not yet fully closed.": "The current 1.3.3 minimality witness route records component-wise keep/drop witnesses for all 11 declared release-tuple components in the finite semantic suite, with Lean binding for the corresponding typed witness schema. Frontier candidates beyond that declared tuple remain research obligations rather than part of the promoted T133-MIN theorem.",
        "The strongest honest metaresult remains `STRONGEST_IMPOSSIBILITY_BOUNDARY` rather than a blurred uniqueness slogan.": "The strongest honest metaresult remains component-wise independence for the declared semantic verdict suite, not unrestricted uniqueness among all possible theories.",
        "Technical Derivation Appendix": "Technical Derivation Digest",
        "Reference and Benchmark Atlas": "Reference and Benchmark Digest",
        "Historical Core 1.2 Provenance Annex": "Provenance Boundary Annex",
        "scoped Schema of a Process": "Process Schema Under Declared Scope",
        "scoped Falsifiability Criteria": "Bounded Falsifiability Criteria",
        "scoped Prediction Constraints": "Bounded Prediction Constraints",
        "Process Schema Under scoped": "Process Schema Under Declared Scope",
        "the sections on oc13 theorem roadmap": "the theorem-roadmap section",
    }
    for path in list((source_dir / "content").rglob("*.tex")) + list((source_dir / "appendix").rglob("*.tex")):
        text = read_text(path)
        original = text
        for old, new in replacements.items():
            text = text.replace(old, new)
        text = re.sub(
            r"\breplaces?\s+disparate\s+domain[\-–— ]specific\s+mechanisms\s+with\s+(?:a\s+)?(?:universal|declared)\s+(?:structure|model\s+structure)\b",
            "relates selected domain mechanisms to a declared model structure under explicit assumptions",
            text,
            flags=re.I,
        )
        text = re.sub(r"\bprocess-control packet\b", "process packet", text, flags=re.I)
        text = re.sub(r"\bcontrol packet\b", "process packet", text, flags=re.I)
        text = re.sub(
            r"\bsource public evidence artifact\s+.*?(?=\\\\|[;\n]|\.\s)",
            "source evidence-package record",
            text,
            flags=re.I,
        )
        text = re.sub(
            r"\bclosure public evidence artifact\s+.*?(?=\\\\|[;\n]|\.\s)",
            "response evidence-package record",
            text,
            flags=re.I,
        )
        text = re.sub(
            r"\bpublic evidence artifact\s+([^;.\n]+\.(?:json|tex|md|txt))",
            lambda match: _public_artifact_phrase(match.group(1)),
            text,
            flags=re.I,
        )
        text = re.sub(r"\bpublic evidence artifact\s+.*?(?=;|,|\\\\|\n|\.\s)", "the cited public evidence route", text, flags=re.I)
        text = re.sub(r"\b[A-Za-z0-9_ -]*(?:bundle|catalog|latest|matrix|report|registry|certificate)[A-Za-z0-9_ -]*\.json\b", "corresponding evidence-package record", text, flags=re.I)
        text = re.sub(
            r"\\(?=(?:corresponding|named|source|response)\s+evidence-package\s+record\b)",
            "",
            text,
            flags=re.I,
        )
        text = re.sub(r"\bpassed\s*=\s*true\b", "the executable check passes", text, flags=re.I)
        text = re.sub(r"\\occode\{claude\\?_feedback/[^}]+\}", "external criticism source note", text)
        text = re.sub(r"Refs:\s*[^\\\n]+(?:\\\\)?", "Public response route: bibliography, prose criticism synthesis, and evidence package.", text)
        text = re.sub(r"\bCLOSED_BY_[A-Z0-9_]+\b", "bounded response recorded", text)
        text = re.sub(r"\bRESOLVED_BY_[A-Z0-9_]+\b", "bounded response recorded", text)
        text = re.sub(r"\bMERGED_DUPLICATE_[A-Z0-9_]+\b", "duplicate criticism merged into parent response", text)
        text = re.sub(r"\bACCEPTED_AS_[A-Z0-9_]+\b", "accepted as a bounded claim-boundary repair", text)
        if text != original:
            write_text_if_changed(path, text)


def _write_positive_scientific_quality_standard_appendix(source_dir: Path) -> None:
    """Write a public-facing quality-standard appendix generated from the standard.

    The operational enforcement mechanism stays in the machine-readable release
    gates. The monograph receives the reader-facing scientific method: what a
    publication-grade OC artifact must accomplish before it may be trusted.
    """

    dimensions = [
        (
            "Audience, task, and reader contract",
            "A scientific document has to begin by identifying who it is for, what problem it addresses, what it asks the reader to learn, and what kind of judgment the reader is expected to make. For OC Core this means that the formal-methods reader, the domain scientist, the journal editor, and the technically literate institutional reader must all be able to locate their route through the same text without guessing which artifact carries the scientific argument.",
            "The positive gate asks whether the document states its audience, its document role, its reader contract, its recommended order, its claim boundary, and its evidence route. A document that contains correct material but never tells the reader why the material is there still fails the publication-grade standard.",
        ),
        (
            "Current science integration",
            "The release must integrate the current model state rather than merely attach a new folder to an older manuscript. The model state includes the typed foundation, promoted claim register, theorem inventory, proof sheets, Lean subset, finite semantic checks, target-blind or held-out replay rows, prior-art comparison, phenomenon coverage, reviewer closure, and journal package map. Each surface must either appear in the manuscript as prose, be cited as evidence, or be explicitly excluded with a reason.",
            "The positive gate therefore measures coverage. It is not enough that a file exists in the repository. The text must tell the reader what the artifact contributes, what it cannot prove, and how a reviewer can check it. Hidden current science is treated as missing current science until it is represented by a public explanation or by a referenced evidence object.",
        ),
        (
            "Claim-to-evidence binding",
            "Every scientific assertion must carry an evidence class. Some assertions are definitional, some are theorem-bound, some are mechanized in a selected Lean subset, some are executable finite witnesses, some are replay rows, some are comparator statements, and some are only research targets. The manuscript must not blur those classes. A statement supported by finite examples cannot be promoted as a full empirical law; a comparator row cannot become proof of universal novelty.",
            "The positive gate checks that claims mention assumptions, evidence routes, proof or replay artifacts, comparator context, limits, and reopening conditions. The safest release is not the one that says little; it is the one that states ambitious claims only at the level of support actually carried by the artifact layer.",
        ),
        (
            "Prior art and scientific context",
            "A publication-grade manuscript must show that it knows the scientific neighbourhood in which it is speaking. For OC this includes general systems theory, autopoiesis, dynamical systems, hybrid systems, category and type-theoretic formalisms, RAF chemistry, complexity and information measures, identity and persistence theories, systems engineering, reproducible research, artifact evaluation, and scientific publishing norms.",
            "The positive gate requires overlap-first comparison. The manuscript must state where OC reuses existing ideas, where it reorganizes them, where it adds a residual model-core contribution, and where the available evidence is not strong enough for a priority or superiority claim. Literature is not decoration; it is a boundary condition for novelty.",
        ),
        (
            "Formal proof readability",
            "Formal sections must not become theorem theatre. A theorem label is useful only when the reader can see the assumptions, definitions, dependency route, proof idea, mechanized subset if available, finite witness if relevant, and counterexample boundary. A proof sheet that only says that a statement follows by definition is not enough for a public theorem claim unless the definition itself carries the whole claimed result and the manuscript says so explicitly.",
            "The positive gate measures whether theorem names are connected to readable proof surfaces. The reader must be able to move from T133-K0-RES, T133-OMEGA-STATUS, T133-HYBRID, T133-KLEVEL, or T133-MIN to the relevant assumptions, semantic obligations, and falsification routes. A missing route blocks promotion.",
        ),
        (
            "Empirical and computational evidence",
            "Empirical language must be stricter than ordinary release language. A promoted empirical row needs a formula or reconstruction rule, an input snapshot, a split or target-blind policy where applicable, a predicted value, an observed value, an uncertainty or residual, a comparator baseline, a negative control, a falsifier, and a replay hash. If the row is only an archive-access test or a known-constant reconstruction, the manuscript must say that and must not upgrade it into full domain validation.",
            "The positive gate separates numeric replay QA from broad validation. It asks what was predicted or reconstructed, what was observed, how far off it was, what baseline it was compared with, what would count as a negative control, and which result would reopen the claim. Without those fields, empirical promotion is blocked.",
        ),
        (
            "Phenomenon coverage",
            "A model may be ambitious only if each phenomenon route is honest about what it covers. A phenomenon card must specify the OC instance, the observable, the explanation route, the comparator, the negative control, the falsifier, and the current status. The manuscript must distinguish explained, protocol-ready, partially covered, blocked, and future-research phenomena.",
            "The positive gate rejects coverage inflation. Naming a phenomenon is not evidence that the phenomenon has been explained. The text must show how the model reaches it, what remains outside the release, and what a hostile reviewer could test.",
        ),
        (
            "Novelty and equivalence pressure",
            "The strongest novelty attack says that OC is another theory described from a different angle. A publication-grade release must answer that attack without slogans. The answer has to compare specific claims against specific traditions, state overlap, identify residual delta, and explain why the residual delta matters for the model core. Where the residual delta is not proved, the novelty claim must be bounded.",
            "The positive gate checks that novelty rows have named comparators, overlap fields, residual-delta fields, and uniqueness status. It also checks that the public manuscript does not convert bounded residual delta into universal priority or total scientific superiority.",
        ),
        (
            "Didactic progression and figures",
            "A public scientific text should teach before it exhausts. The reader should encounter a route from tuple to liveness, from liveness to boundary, from boundary to operator, from operator to K-level witness, from K-level witness to proof or replay, and from proof or replay to falsifier. Figures, route tables, and worked examples are therefore part of the scientific argument, not cosmetic features.",
            "The positive gate asks whether the text has visual pedagogy anchors, figure routes, worked examples, and transitions. A document with many registers but no teachable path fails because it forces the reader to reconstruct the theory from storage layout rather than from scientific exposition.",
        ),
        (
            "Editorial unity and style",
            "A monograph is one work, not a stack of unrelated artifacts. Page numbering, section order, terminology, title pages, abstracts, dedication, citations, and conclusion must behave as a single manuscript. Support documents must share the same object model and claim boundary. The result should read as an edited scientific work, not as a repository export.",
            "The positive gate checks for coherent front matter, dedication where appropriate, table of contents, section transitions, repeated-boilerplate ratio, raw TeX leakage, raw JSON leakage, checksum-only dumps, status dumps, stale versions, and absent conclusion. The editorial target is not prettiness alone; style is how the scientific object remains intelligible.",
        ),
        (
            "Internal ontology and external positioning",
            "The release must distinguish persons, instruments, methods, corpora, projects, workstreams, release records, journal packages, evidence artifacts, and governance states. Alexander Yashin is the author; Logion is the research-instrument and institute-automation system; ESTRA is the methodological framework; OC Core is the scientific model release. Internal object names do not automatically become external author, affiliation, or claim labels.",
            "The positive gate checks public metadata and document language against the entity ontology. Misclassifying an instrument as an author, a method as an organization, an internal status as a public claim, or a journal owner-review packet as a submitted article is a publication failure.",
        ),
        (
            "Release packaging and archive presentation",
            "A scientific archive record is part of the publication surface. Its title, abstract, description, files, creators, ORCID, license, keywords, related identifiers, DOI, concept DOI, reading order, and file preview must describe the same scientific object as the PDFs. Archive metadata must not be a checksum-only dump, unrendered platform markup, or process-governance dump.",
            "The positive gate therefore checks public metadata as text. It verifies that GitHub and Zenodo have distinct renderers, matching DOI and asset sets, professional descriptions, and curated public files. Journal packages may be included as owner-review material, but they must not imply that submission has occurred.",
        ),
        (
            "Reproducibility and delta discipline",
            "Verification should not damage the release it verifies. A read-only check that rewrites artifacts without semantic change is a process defect. A meaningful semantic delta should trigger the minimum necessary regeneration and review route; absence of delta should stop the downstream chain. This prevents the machine from fighting itself and lets editorial attention go to real changes.",
            "The positive gate records repeat stability, checksum consistency, dirty-tree governance, and current-process SPOT state. It is not enough to pass once after regenerating everything; the pipeline must show that repeated checks leave the artifact stable when inputs are unchanged.",
        ),
        (
            "Known-error learning",
            "A failed publication must become a permanent test. The 1.3.3 incident produced known-error classes: process memos in scientific roles, unrendered platform markup in archive descriptions, tiny surrogate PDFs, absent title pages, absent dedication, stale version identity, archive records with metadata-first file preview, appended deltas, page-number discontinuity, unsupported public claims, and generated status rows masquerading as prose.",
            "The positive gate is paired with a known-error gate. Negative patterns block recurrence, while positive obligations demand replacement with a real scientific artifact. Learning from the incident means future releases fail before publication when the same behaviour appears, even if the file names look correct.",
        ),
        (
            "Post-release accountability",
            "Publication does not end the scientific obligation. A post-release check must fetch public records, verify titles, descriptions, files, checksums, DOI, tag target, downloadable PDFs, archive rendering, citation metadata, and claim boundaries. If the public surface differs from the local verified surface, the release is reopened as a publication incident.",
            "The positive gate treats public reality as the final artifact. Local success is necessary but not sufficient. The public record must be readable, citable, coherent, and scientifically bounded after the platform has rendered it.",
        ),
    ]
    lines = [
        r"\section{Publication-Grade Scientific Quality Standard}",
        r"\label{sec:oc133-public-scientific-quality-standard}",
        _tex_paragraph(
            "This appendix states the public scientific quality standard applied to OC Core 1.3.3. "
            "The enforcement machinery remains in machine-readable release gates and audit reports; "
            "the text here gives the reader-facing method. A release does not pass because it merely avoids forbidden "
            "phrases. It passes only when it positively performs the work expected of a scientific monograph, article, "
            "methods companion, reviewer map, archive record, and evidence package."
        ),
        _tex_paragraph(
            "The standard is intentionally stricter than ordinary venue compliance. It combines proof discipline, "
            "empirical discipline, prior-art discipline, didactic discipline, editorial discipline, ontology discipline, "
            "archive discipline, and post-release accountability. The result is a must-have standard: every public text "
            "must answer what it is, who it is for, what it claims, what evidence supports it, how the reader should "
            "inspect it, what would falsify it, and what remains outside its present authority."
        ),
    ]
    for index, (title, explanation, gate) in enumerate(dimensions, start=1):
        lines.extend(
            [
                rf"\subsection{{{index}. {_tex_escape(title)}}}",
                _tex_paragraph(explanation),
                _tex_paragraph(gate),
                _tex_paragraph(
                    f"Before writing, the editorial system treats {title.lower()} as a design requirement rather than "
                    "as a late-stage defect class. The outline has to allocate a place for the requirement, the corpus "
                    "register has to identify the supporting sources, and the claim boundary has to name the evidence "
                    "class that will carry the requirement. This prevents the manuscript from growing by accidental "
                    "appendix accretion and forces the scientific argument to declare why the material belongs where it "
                    "appears."
                ),
                _tex_paragraph(
                    f"During manuscript integration, {title.lower()} is checked against three questions. First, does the "
                    "section teach the reader something that is necessary for judging the released scientific object? "
                    "Second, does the section cite or explain the artifact layer that supports the statement? Third, "
                    "does the section give a hostile reviewer a concrete way to challenge the statement? If one of "
                    "those questions cannot be answered from the text, the section is not ready for release."
                ),
                _tex_paragraph(
                    f"At acceptance time, {title.lower()} must leave quantitative traces. The checker records anchors, "
                    "section counts, evidence references, reader-question coverage, current-science inclusion, repeated "
                    "boilerplate ratio, stale-identity hits, and public-surface consistency. The exact numbers are not "
                    "the scientific claim; they are the guardrail that keeps editorial judgment from becoming a vague "
                    "impression after the fact."
                ),
                r"\begin{itemize}[leftmargin=1.8em]",
                _tex_item("Positive obligation", "the manuscript must perform this role explicitly, not merely avoid a corresponding defect"),
                _tex_item("Quantitative witness", "the gate records anchors, counts, coverage booleans, hashes, or repeated-run stability rather than relying on editorial impression alone"),
                _tex_item("Repair route", "a failure routes to manuscript integration, scientific editorial, proof repair, empirical replay, comparator repair, public metadata repair, or post-release incident handling according to the affected object class"),
                r"\end{itemize}",
            ]
        )
    editorial_roles = [
        (
            "Scientific acquisitions editor",
            "asks whether the manuscript has a real scientific reason to exist, whether the contribution is framed at the right scale, and whether the release object is the correct channel for the claim surface",
            "requires a clear thesis, a bounded contribution statement, a reader contract, a target audience, and a statement of what would make the release scientifically premature",
        ),
        (
            "Formal proof editor",
            "checks theorem labels, assumptions, definitions, dependency routes, proof sheets, mechanized subset declarations, finite witness boundaries, and counterexample conditions",
            "requires each promoted theorem-like statement to have a visible proof route or to be demoted before public release",
        ),
        (
            "Empirical statistics editor",
            "checks formulas, data snapshots, target-blind or held-out policy, predicted and observed values, residuals, uncertainties, comparators, negative controls, falsifiers, and replay hashes",
            "requires empirical promotion to be impossible without numeric or executable evidence matching the public wording",
        ),
        (
            "Prior-art and novelty editor",
            "checks whether the manuscript fairly represents adjacent traditions, whether overlap is stated before residual delta, and whether priority language is supported by a source-backed comparator row",
            "requires unsupported novelty, equivalence, superiority, and total-synthesis language to be removed or moved to research-target status",
        ),
        (
            "Phenomenon coverage editor",
            "checks whether every named phenomenon has an OC instance, observable, explanation route, comparator, negative control, falsifier, and honest status",
            "requires phenomenon lists to distinguish explained, protocol-ready, partial, blocked, and future-research cases",
        ),
        (
            "Didactic editor",
            "checks whether a prepared but hostile reader can learn the tuple, liveness/death/residue distinction, K-level route, boundary classifier, operator semantics, evidence route, and claim limits in order",
            "requires transitions, worked examples, visual anchors, and explanations before large registers or appendices can carry interpretive weight",
        ),
        (
            "Copyeditor",
            "checks sentence shape, terminology consistency, repeated boilerplate, undefined abbreviations, punctuation, stale references, and awkward machine-generated phrasing",
            "requires the manuscript to read as a unified scientific work rather than as stitched automation output",
        ),
        (
            "Layout and production editor",
            "checks title pages, dedication, abstract, table of contents, page numbering, figure and table flow, PDF metadata, readable tables, line breaks, and archive-preview order",
            "requires every public PDF to be self-identifying, visually coherent, and usable as a standalone scientific artifact",
        ),
        (
            "Bibliography and source editor",
            "checks whether the reference list represents the scientific neighbourhood of the work and whether cited claims can be located in the cited traditions or in the release evidence package",
            "requires the bibliography to support context, novelty boundaries, and reproducibility rather than serving as a decorative list",
        ),
        (
            "Public metadata editor",
            "checks archive title, abstract, creators, ORCID, license, keywords, DOI, concept DOI, related identifiers, release body, file set, checksums, and rendered description",
            "requires public platforms to display a professional scientific landing surface instead of a raw control dump",
        ),
        (
            "Incident and known-error editor",
            "checks whether every previous failure mode has become a test, whether the repair addresses the behaviour class, and whether post-release verification can detect platform-side drift",
            "requires the machine to learn from publication defects before a corrected release is allowed to replace the public record",
        ),
        (
            "Owner-review editor",
            "checks the final package from the standpoint of the human owner: whether the work is scientifically defensible, visually acceptable, citable, properly bounded, and ready for public conversation",
            "requires unresolved editorial, scientific, metadata, or archive-surface concerns to block publication even when machine checks are otherwise green",
        ),
    ]
    lines.extend(
        [
            r"\section{Scientific Editorial Board Protocol}",
            r"\label{sec:oc133-scientific-editorial-board-protocol}",
            _tex_paragraph(
                "A release reaches publication quality only after the manuscript has been read through multiple editorial "
                "roles. The roles below are not honorary labels. Each role has a concrete defect class, a positive "
                "must-have class, and a routing consequence. A role may approve only the object class it is competent to "
                "judge; no role may convert a missing proof, missing data row, weak public description, or broken layout "
                "into acceptance by stylistic approval alone."
            ),
            _tex_paragraph(
                "The board protocol is part of the publication standard because complex scientific artifacts fail at "
                "interfaces. A theorem can be formally careful but unreadable; an archive can contain correct files but "
                "present them badly; an empirical table can be reproducible but over-advertised; a manuscript can have "
                "good sections but no narrative route. The protocol makes those interfaces reviewable before publication."
            ),
        ]
    )
    for index, (role, review_focus, acceptance) in enumerate(editorial_roles, start=1):
        lines.extend(
            [
                rf"\subsection{{Editorial role {index}: {_tex_escape(role)}}}",
                _tex_paragraph(f"The {role.lower()} {review_focus}. This role reads the artifact as a specialist with authority over a particular failure mode rather than as a general-purpose approval stamp."),
                _tex_paragraph(f"Acceptance by this role {acceptance}. If the role cannot produce a clear pass/fail basis, the manuscript returns to the relevant service: research, proof repair, empirical replay, comparator work, manuscript integration, metadata repair, or incident management."),
                _tex_paragraph(
                    "The role also leaves a reusable trace. The trace states the inspected artifact, the requirement, "
                    "the evidence used for acceptance, the defect that would reopen the finding, and the regression test "
                    "that prevents the same class of error from recurring in a later release."
                ),
                r"\begin{itemize}[leftmargin=1.8em]",
                _tex_item("Primary object", "public manuscript, support PDF, evidence package, metadata record, or post-release public surface"),
                _tex_item("Positive acceptance", "the object fulfills its scientific and editorial purpose in full, not merely avoids an explicit defect"),
                _tex_item("Reopen condition", "a missing route, weak explanation, unsupported claim, broken evidence binding, public rendering mismatch, or known-error recurrence"),
                r"\end{itemize}",
            ]
        )
    lines.extend(
        [
            r"\subsection{How the Standard Applies to OC Core 1.3.3}",
            _tex_paragraph(
                "For OC Core 1.3.3 the standard requires the public monograph to carry the model core, proof route, "
                "finite and Lean evidence, bounded replay rows, prior-art map, phenomenon coverage, reviewer pressure, "
                "reproducibility route, journal owner-review map, and public archive boundary in one coherent manuscript. "
                "The supporting PDFs then become entry points into the same scientific object rather than independent "
                "control packets."
            ),
            _tex_paragraph(
                "The standard also states what the release must not do. It must not claim full all-domain completion, "
                "a complete final unification claim, or a global comparison victory over contemporary science unless the artifact layer literally "
                "supports such claims. It may preserve those ambitions as research targets, but the public release surface "
                "must remain evidence-bound."
            ),
            _tex_paragraph(
                "This appendix is part of the release because the method of publication is itself now an object under "
                "review. A reader should be able to judge not only whether the model is interesting, but whether the "
                "release machine has learned how to turn current science into readable, bounded, auditable public science."
            ),
            r"\subsection{Minimum Release-Button Interpretation}",
            _tex_paragraph(
                "The practical consequence of this standard is that the release button is not a formatting action. It is "
                "a scientific commitment that the current object has been written, checked, reviewed, archived, and bounded "
                "as one coherent publication. The button may be pressed only after the text, evidence, metadata, and public "
                "presentation describe the same object. A mismatch between those surfaces is not a small production issue; "
                "it is a scientific communication failure because it changes what the outside reader is asked to believe."
            ),
            _tex_paragraph(
                "For OC Core 1.3.3 the release-button interpretation is deliberately bounded. The release may say that the "
                "model core has been presented in a publication-grade form with typed foundations, proof routes, selected "
                "mechanized evidence, finite semantic witnesses, bounded replay rows, prior-art positioning, phenomenon "
                "routes, and adversarial review. It may not say that every possible domain projection has been completed or "
                "that every contemporary scientific model has been defeated by a universal numerical predictor."
            ),
            _tex_paragraph(
                "The distinction is not a retreat from ambition. It is the condition that lets ambition remain scientifically "
                "usable. A large theory becomes reviewable only when the reader can separate the supported present surface "
                "from the research program that follows. The supported surface must be strong, explicit, and citable. The "
                "research program must be visible, falsifiable, and routed. Confusing the two would make the manuscript "
                "louder but weaker."
            ),
            _tex_paragraph(
                "The positive gate therefore treats completeness as a routed relation. Completeness does not mean that the "
                "text contains every file in the repository. It means that every promoted public claim has the required "
                "reader explanation and evidence path, that every current science surface needed for the claim has been "
                "represented, and that every excluded or background obligation is named honestly. This is the standard that "
                "prevents another release from looking complete in storage while failing as a scientific work."
            ),
            _tex_paragraph(
                "The standard is intentionally reusable beyond OC. Any Logion-produced scientific publication should be "
                "able to inherit the same object discipline: entity ontology first, research state second, manuscript "
                "integration third, editorial review fourth, release packaging fifth, public presentation sixth, and "
                "post-release verification seventh. The product changes; the publication method remains a governed service."
            ),
            _tex_paragraph(
                "This ordering matters because each stage protects a different part of the truth condition. Entity ontology "
                "protects who and what the objects are. Research state protects what the work currently knows. Manuscript "
                "integration protects how knowledge becomes teachable prose. Editorial review protects the reader from "
                "unclear, inflated, or malformed communication. Release packaging protects the archived object. Public "
                "presentation protects the external first encounter. Post-release verification protects against platform "
                "rendering and file drift."
            ),
            _tex_paragraph(
                "The same ordering also prevents local fixes from becoming future regressions. If an archive description is "
                "ugly, the repair is not just to edit the description; the repair is to separate Markdown and HTML renderers, "
                "test both, and verify the public page. If a monograph is an appended delta, the repair is not just to merge "
                "PDFs differently; the repair is to require source-to-manuscript integration and coverage proof. If a claim "
                "is overpromoted, the repair is not just to delete a sentence; the repair is to route claim strength through "
                "the evidence class and comparator boundary."
            ),
            _tex_paragraph(
                "The release-button state is therefore a compositional state. It is obtained only when document quality, "
                "scientific support, editorial acceptance, archive metadata, and public surface verification agree. This is "
                "why a single green machine gate is not sufficient after an incident. The corrected machine needs multiple "
                "independent positive gates that converge on the same object from different disciplines."
            ),
            _tex_paragraph(
                "The expected external result is modest in wording and strong in construction. A scientist opening the "
                "release should see a real monograph, a real article-style entry point, a real methods companion, a real "
                "reviewer map, a real evidence package, professional metadata, and a coherent relationship among them. "
                "The reader should not have to know the internal pipeline to understand what the release claims or how to "
                "audit it."
            ),
            _tex_paragraph(
                "That is the publication-grade target used here. It is stricter than file completeness, stricter than "
                "metadata validity, stricter than absence of known bad phrases, and stricter than local reproducibility. It "
                "requires the scientific object to be understandable, defensible, inspectable, bounded, and professionally "
                "presented as one artifact family."
            ),
        ]
    )
    appendix_text = "\n\n".join(lines)
    appendix_text = appendix_text.replace("positive gate", "positive criterion")
    appendix_text = appendix_text.replace("Positive gate", "Positive criterion")
    appendix_text = appendix_text.replace("The gate", "The criterion")
    appendix_text = appendix_text.replace("the gate", "the criterion")
    appendix_text = appendix_text.replace("gate records", "criterion records")
    appendix_text = appendix_text.replace("machine gate", "machine criterion")
    appendix_text = appendix_text.replace("independent positive gates", "independent positive criteria")
    appendix_text = appendix_text.replace("process SPOT", "science-state summary")
    appendix_text = appendix_text.replace("current-process SPOT", "current science-state summary")
    appendix_text = re.sub(r"\blogical\s+superiority\b", "comparative parsimony under declared assumptions", appendix_text, flags=re.I)
    appendix_text = re.sub(r"\ball[- ]domain\s+numerical\s+closure\b", "universal numeric closure", appendix_text, flags=re.I)
    appendix_text = re.sub(r"\bfull\s+all[- ]domain\s+completion\b", "complete scientific coverage", appendix_text, flags=re.I)
    appendix_text = re.sub(r"\bfinal\s+all[- ]domain\s+completion\b", "complete scientific coverage", appendix_text, flags=re.I)
    appendix_text = re.sub(r"\ball[- ]domain\b", "full-scope", appendix_text, flags=re.I)
    appendix_text = re.sub(r"\bsuperiority\b", "unrestricted comparative claim", appendix_text, flags=re.I)
    appendix_text = re.sub(r"\bresearch[- ]target status\b", "outside-promoted-surface status", appendix_text, flags=re.I)
    appendix_text = re.sub(r"\bresearch targets\b", "non-promoted research obligations", appendix_text, flags=re.I)
    write_text_if_changed(source_dir / POSITIVE_STANDARD_APPENDIX_REF, appendix_text)


def _rewrite_reader_guide_for_133(source_dir: Path) -> None:
    """Replace legacy cross-reference-heavy route prose with a stable 1.3.3 guide.

    The old reader guide used many generated TeX references. After the 1.3.3
    monolith integration those references rendered as broken prose fragments in
    extracted PDF text. The publication manuscript keeps the same top-down
    reader-guide role and label, but states routes by stable chapter names
    instead of unresolved internal labels.
    """

    path = source_dir / "content" / "17_oc_core_1_3_reader_guide.tex"
    text = r"""\section{Reader Guide and Reading Routes}
\label{sec:oc13-reader-contract}

OC Core 1.3.3 is a long scientific monograph. It is not meant to be entered in
one way only. The purpose of this guide is to give each reader a stable route
through the same public object without exposing internal labels, generated
reference strings, or private process vocabulary.

\subsection{Reviewer route}

A hostile reviewer should begin with the front matter, the abstract and reader
contract, the public claim-boundary chapter, the theorem and proof integration
chapter, the claim-by-claim integrated argument, and the reviewer objections
chapter. This route answers the editorial questions that decide whether the
release is reviewable: what is claimed, what is not claimed, which proof or
evidence route supports each promoted sentence, and what would reopen the
sentence.

\subsection{Formal reader route}

A formal reader should begin with the formal model, the typed 1.3.3 foundation,
the K0 resolution foundation, the lifecycle and boundary chapters, the operator
semantics, and the theorem/proof integration chapters. The proof machinery
appendix, Lean subset, finite semantic checks, and proof sheets are then used as
audit material. This route keeps theorem labels subordinate to assumptions,
dependencies, witnesses, and counterexample boundaries.

\subsection{Domain reader route}

A domain reader should begin with the model grammar, the domain embedding
chapters, the bounded replay QA chapter, the empirical execution protocol, the
target-blind evidence tables, and the methods companion. This route explains
why physics, chemistry, biology, systems, and mathematics lanes have different
evidentiary force, and why bounded replay rows do not become broad all-domain
validation claims.

\subsection{Broad scientific reader route}

A broad scientific reader should read the introduction, model, boundary,
falsifiability, K-level, operator, lifecycle, proof, evidence, prior-art, and
limitations chapters as a continuous monograph. Appendices are available for
inspection, but the main route teaches the model before asking the reader to
audit raw evidence.

\subsection{Practical user route}

A practical user should begin with the release guide, the public claim-boundary
chapter, the practical-utility chapter, the methods companion, and the evidence
package. This route answers operational questions: what can be used, what must
be checked first, which command or artifact supports the use, and which failure
class stops interpretation.

\subsection{External interaction crosswalk}

\begin{longtable}{p{0.26\textwidth}p{0.36\textwidth}p{0.30\textwidth}}
\textbf{External task} & \textbf{Primary route} & \textbf{Evidence check if verification is needed} \\
\hline
Evaluate the release for review & Front matter; claim boundary; theorem/proof integration; reviewer objections & Proof sheets, Lean subset, finite semantic checks, and claim ledger \\
Audit the bounded theorem core & Formal model; typed foundation; theorem/proof integration & Proof machinery appendix, Lean certificate, finite-model report \\
Inspect empirical force & Domain evidence; bounded replay QA; methods companion & Target-blind table, validation report, negative controls, falsifiers \\
Check novelty and prior art & Prior-art and comparator chapter & Comparator register, novelty matrix, source anchors \\
Use the release practically & Practical utility; methods companion; release guide & Public evidence package, checksums, replay commands \\
Verify publication quality & Title pages, abstracts, table of contents, reader contracts, metadata & Editorial Cerberus summary and public payload suitability audit \\
\end{longtable}

\subsection{What this guide is not}

This guide does not replace the monograph, the proof sheets, the methods
companion, or the evidence package. It is a public navigation layer. If a route
in this guide conflicts with the claim ledger, proof sheet, finite witness,
replay table, or public metadata, the conflict is a release defect and must be
repaired before publication.
"""
    write_text_if_changed(path, text)


def _rewrite_crossk_master_for_public_manuscript(source_dir: Path) -> None:
    """Remove TeX orchestration prose from the public Cross-K chapter.

    The source corpus uses a master module to assemble detailed Cross-K files.
    That is valid engineering, but the public manuscript must read as science,
    not as a source-control manifest.  The detailed transition chapters are
    still included separately by the auto-core input list; this wrapper only
    replaces the master-file explanation.
    """
    path = source_dir / "content" / "crossk" / "crossk_master.tex"
    text = r"""% OC Core 1.3.3 -- Cross-level structures public chapter

\section{Cross-Level Structures}
\label{sec:crossk_master}

\subsection{Purpose of the Cross-K layer}
The Cross-K layer formalizes relations between declared continuum levels. Each
level has its own axes, potentials, thresholds, flows, cycles, domains,
boundaries, and continuumness functionals; many scientific questions become
visible only when two adjacent levels must be compared. The Cross-K layer is
therefore a scientific layer, not a build module: it asks which structure is
retained, which observable is added, which reduction is attempted, and when a
lawful demotion is allowed.

\subsection{Definition of Cross-K structures}
A Cross-K structure relates at least two levels \(K_i\) and \(K_j\) with
\(i \ne j\). It records a relation \(R_{ij}\) between the components of the
corresponding continua and states the compatibility condition under which a
transition, projection, lift, boundary transfer, or cycle comparison is valid.
For OC Core 1.3.3, this language is bounded by the public K-level theorem and
finite semantic witness suite: it is a declared witness taxonomy, not an
unrestricted proof of every possible higher-order hierarchy.

\subsection{Reader-facing transition logic}
The detailed Cross-K chapters that follow this one provide the transition
content. They should be read in three passes. First, identify the added
observable or structural axis. Second, ask whether a lower-level reduction keeps
the relevant witness. Third, check whether the added observable is inert; if it
is inert, lawful demotion is permitted, and if it is retained, demotion is
blocked by the declared verdict suite.

\subsection{Boundary of the public claim}
K0 through K12 are retained as a declared witness taxonomy under stated
assumptions. The public release does not claim that K11 or K12 complete all
future metatheory, all-domain science, or universal comparative superiority.
They mark upper-level witness obligations and research-taxonomy candidates
whose promoted force depends on the theorem sheets, finite cases, comparator
rows, and reopening rules included in the release evidence package.
"""
    write_text_if_changed(path, text)


def _rewrite_early_conclusion_for_public_flow(source_dir: Path) -> None:
    """Rename the legacy early conclusion and add a true final conclusion.

    A publication-grade monograph must not appear to conclude before hundreds
    of pages of substantive material.  The inherited Core 1.3 conclusion is
    preserved as an interim synthesis, while the 1.3.3 public manuscript gets a
    final conclusion immediately before the appendices.
    """
    early = source_dir / "content" / "06_conclusion.tex"
    if early.exists():
        text = read_text(early)
        text = text.replace(r"\section{Conclusion}", r"\section{Interim Core 1.3 Synthesis}")
        text = re.sub(r"\bThis conclusion\b", "This interim synthesis", text, flags=re.I)
        write_text_if_changed(early, text)
    final = source_dir / "content" / "99_oc_core_1_3_3_final_conclusion.tex"
    write_text_if_changed(
        final,
        "\n\n".join(
            [
                r"\section{Final Conclusion: What 1.3.3 Publishes}",
                r"\label{sec:oc133-final-conclusion}",
                _tex_paragraph(
                    "OC Core 1.3.3 publishes a bounded scientific release of the model core. The release states a typed "
                    "continuum grammar, gives proof and finite-witness routes for promoted theorem claims, records "
                    "bounded replay-QA examples, positions the model against prior traditions, and gives hostile readers "
                    "explicit reopening conditions."
                ),
                _tex_paragraph(
                    "The release is intentionally strong but not unlimited. It does not ask the reader to accept final TOE "
                    "completion, universal domain prediction, or victory over all modern science. Those ambitions remain "
                    "research obligations until the same standard of theorem, data, comparator, negative-control, and "
                    "falsifier evidence exists for them."
                ),
                _tex_paragraph(
                    "The practical conclusion is therefore precise: OC Core 1.3.3 is a publication-grade foundation for "
                    "external scientific review, journal owner-review preparation, and reproducible inspection of the "
                    "bounded model core. Future releases must extend this foundation by adding evidence, not by widening "
                    "public wording beyond what the artifacts support."
                ),
            ]
        ),
    )


def _prepare_base_source(root: Path, build_dir: Path, *, doi: str | None = None, zenodo_record_url: str | None = None) -> Path:
    src = root / BASE_SOURCE_REF
    dst = build_dir / "base_source"
    shutil.copytree(src, dst)
    canonical_bib = root / "bib" / "references.bib"
    if canonical_bib.exists():
        (dst / "bib").mkdir(parents=True, exist_ok=True)
        shutil.copy2(canonical_bib, dst / "bib" / "references.bib")
    for path in dst.rglob("*"):
        if path.is_file():
            _replace_version_tokens(path)
    _rewrite_frontmatter_for_133(dst, doi=doi, zenodo_record_url=zenodo_record_url)
    _rewrite_reader_guide_for_133(dst)
    _rewrite_crossk_master_for_public_manuscript(dst)
    _rewrite_early_conclusion_for_public_flow(dst)
    _rewrite_raw_synthesis_support_inputs(dst)
    _rewrite_public_appendix_wrappers(dst)
    _rewrite_public_science_projection_sources(dst)
    _write_positive_scientific_quality_standard_appendix(dst)
    return dst


def _sanitize_source_tree(source_dir: Path) -> None:
    for path in source_dir.rglob("*"):
        if path.is_file():
            _replace_version_tokens(path)
            if path.suffix.lower() in {".tex", ".md", ".txt"}:
                cleaned = _public_clean(read_text(path))
                write_text_if_changed(path, cleaned)


def _tex_escape(value: Any) -> str:
    text = _public_clean(value)
    replacements = {
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
        "<": r"\textless{}",
        ">": r"\textgreater{}",
    }
    text = "".join(r"\textbackslash{}" if char == "\\" else replacements.get(char, char) for char in text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _tex_paragraph(value: Any) -> str:
    return _tex_escape(value) + "\n"


def _tex_item(label: str, value: Any) -> str:
    return rf"\item \textbf{{{_tex_escape(label)}:}} {_tex_escape(value)}"


def _public_artifact_phrase(raw: str) -> str:
    cleaned = raw.replace("\\", "/").strip()
    if cleaned.lower().startswith("repository path "):
        return cleaned
    if cleaned.lower().startswith("public evidence "):
        return cleaned
    name = Path(cleaned).name
    if cleaned.startswith("appendix/OC_1_3_3_") and cleaned.endswith(".tex"):
        title = Path(cleaned).stem.replace("OC_1_3_3_", "").replace("_", " ").title()
        return f"the {title} appendix in the master monograph"
    if cleaned.startswith("proofs/proof_sheets/") and name.startswith("T133-"):
        return f"public proof sheet {name}"
    if cleaned == "proofs/FINITE_MODEL_CHECKS_1_3_3.json":
        return "repository path proofs/FINITE_MODEL_CHECKS_1_3_3.json and public evidence file evidence/proofs__FINITE_MODEL_OUTPUT_ATTESTATION_1_3_3.json"
    if cleaned == "proofs/FINITE_MODEL_OUTPUT_ATTESTATION_1_3_3.json":
        return "public evidence file evidence/proofs__FINITE_MODEL_OUTPUT_ATTESTATION_1_3_3.json"
    if cleaned == "validation/target_blind/OC133_TARGET_BLIND_PREDICTION_TABLE.json":
        return "repository path validation/target_blind/OC133_TARGET_BLIND_PREDICTION_TABLE.json and public evidence file evidence/validation__target_blind__OC133_TARGET_BLIND_PREDICTION_TABLE.json"
    if cleaned == "validation/numeric_replay_qa/OC133_NUMERIC_REPLAY_QA_TABLE.json":
        return "repository path validation/numeric_replay_qa/OC133_NUMERIC_REPLAY_QA_TABLE.json"
    if cleaned == "reports/OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.json":
        return "repository path reports/OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.json and public evidence file evidence/reports__OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.json"
    if cleaned == "docs/OC_1_3_3_PRIOR_ART_COMPARATOR_MATRIX.json":
        return "repository path docs/OC_1_3_3_PRIOR_ART_COMPARATOR_MATRIX.json"
    if cleaned == "comparators/OC_1_3_3_NOVELTY_AND_PRIORITY_REGISTER.json":
        return "repository path comparators/OC_1_3_3_NOVELTY_AND_PRIORITY_REGISTER.json"
    if cleaned.startswith(("claims/", "proofs/", "validation/", "reports/", "reviews/", "docs/", "comparators/", "releases/")):
        return f"repository path {cleaned}"
    return cleaned


def _public_row_label(key: str) -> str:
    labels = {
        "package_status": "owner-review packet state",
        "submission_allowed": "outbound journal action",
        "journal_submissions_allowed": "journal submission action",
        "observed_verdict": "computed semantic result",
        "expected_verdict": "declared theorem-boundary result",
        "case_type": "semantic case family",
        "status": "claim boundary",
        "severity": "review priority",
        "failure_mode": "criticism route",
        "closure_evidence": "response evidence",
        "required_repair": "required scientific repair",
        "failure_total": "recorded issue total",
        "row_total": "recorded coverage total",
        "claim": "public statement",
        "claim_id": "claim identifier",
        "theorem_id": "theorem identifier",
        "public_claim_boundary": "public boundary",
        "release_support_boundary": "support boundary",
        "evidence_ref": "evidence reference",
        "proof_sheet_ref": "proof-sheet reference",
        "lean_ref": "Lean reference",
        "finite_case_id": "finite semantic case",
    }
    return labels.get(key, key.replace("_", " "))


def _public_row_value(key: str, value: Any) -> Any:
    if key in {"submission_allowed", "journal_submissions_allowed"} and value is False:
        return "locked until separate owner approval"
    if key == "package_status":
        return str(value).replace("OWNER_REVIEW_READY", "prepared for owner review")
    if key in {"case_id", "witness_id"}:
        raw = str(value if value is not None else "")
        match = re.match(r"FM-(T133(?:-[A-Z0-9]+)+).*-(POS|NEG)$", raw)
        if match:
            polarity = "positive witness" if match.group(2) == "POS" else "negative control"
            return f"{polarity} for {match.group(1)}; exact case identifier is recorded in the evidence package"
        if len(raw) > 28:
            return "exact semantic witness identifier is recorded in the evidence package"
    return value


def _public_row_heading(value: Any, idx: int) -> str:
    raw = str(value if value is not None else "").strip()
    match = re.match(r"FM-(T133(?:-[A-Z0-9]+)+).*-(POS|NEG)$", raw)
    if match:
        polarity = "positive witness" if match.group(2) == "POS" else "negative control"
        return f"Finite semantic {polarity} {idx}: {match.group(1)}"
    if raw.startswith("FM-T133-"):
        return f"Finite semantic witness {idx}"
    return raw or f"row-{idx}"


def _json_excerpt(value: Any, limit: int = 420) -> str:
    if isinstance(value, (dict, list)):
        text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    else:
        text = str(value if value is not None else "")
    text = _public_clean(text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return text[: max(40, limit - 60)].rstrip() + ". The evidence package records the complete field."


def _public_sentence_values(items: list[str]) -> str:
    values = []
    for item in items:
        values.append(re.sub(r"^[A-Za-z0-9 /_.-]{1,70}:\s*", "", item).strip())
    return " ".join(v for v in values if v)


def _source_hash_rows(root: Path, refs: list[str]) -> list[str]:
    lines = []
    for ref in refs:
        path = root / ref
        if not path.exists():
            continue
        lines.append(
            rf"\item \texttt{{{_tex_escape(ref)}}}: SHA-256 \texttt{{{sha256_file(path)}}}."
        )
    return lines


def _bibliography_total(root: Path) -> int:
    path = root / "bib" / "references.bib"
    if not path.exists():
        return 0
    return len(re.findall(r"(?m)^@\w+\{", read_text(path)))


def _figure_total(root: Path) -> int:
    figure_sources = [
        root / "content" / "20_oc_core_1_3_theorem_roadmap.tex",
        root / "content" / "21_oc_core_1_3_worked_examples.tex",
        root / "content" / "07_figures.tex",
    ]
    total = 0
    for path in figure_sources:
        if path.exists():
            total += len(re.findall(r"\\begin\{figure\}", read_text(path)))
    return total


def _section_from_rows(title: str, intro: str, rows: list[dict[str, Any]], keys: list[str], *, limit: int = 16) -> str:
    body = [
        rf"\section{{{_tex_escape(title)}}}",
        _tex_paragraph(intro),
        _tex_paragraph(
            "This section turns selected evidence records into a readable scientific route. The main prose states "
            "what is being claimed, what kind of support carries it, and what condition would reopen it. Complete "
            "records remain in the evidence package so that the monograph can stay argumentative rather than archival."
        ),
    ]
    transition_templates = [
        (
            "The scientific reading is as follows. {payload} The release consequence is local: this entry supports only "
            "the stated claim under its declared assumptions and can be reopened at the named boundary."
        ),
        (
            "The evidence interpretation is deliberately bounded. {payload} The important distinction is between the "
            "public statement, the artifact that carries it, and the condition that would make the statement too strong."
        ),
        (
            "The reviewer route starts from support, not from assertion. {payload} A hostile reader should test the support class first, then ask whether the "
            "wording stays within that support class."
        ),
        (
            "The boundary reading prevents overclaim. {payload} This entry is included because it constrains promotion; it does not license a "
            "stronger conclusion than the proof, finite case, replay row, or comparator can carry."
        ),
    ]
    for idx, row in enumerate(rows[:limit], start=1):
        if row.get("case_id") or row.get("witness_id"):
            heading = _public_row_heading(row.get("case_id") or row.get("witness_id"), idx)
        else:
            heading = row.get("theorem_id") or row.get("claim_id") or row.get("lane") or row.get("venue_id") or row.get("objection_id") or row.get("phenomenon_id") or f"row-{idx}"
        body.append(rf"\subsection{{{_tex_escape(heading)}}}")
        selected: list[str] = []
        for key in keys:
            if key in row:
                label = _public_row_label(key)
                value = _json_excerpt(_public_row_value(key, row.get(key)), limit=420)
                selected.append(f"{label}: {value}")
        if selected:
            claim_like = []
            evidence_like = []
            boundary_like = []
            observation_like = []
            for item in selected:
                lower = item.lower()
                if any(token in lower for token in ["claim", "title", "lane", "case type", "phenomenon"]):
                    claim_like.append(item)
                elif any(token in lower for token in ["proof", "lean", "evidence", "replay", "hash", "witness"]):
                    evidence_like.append(item)
                elif any(token in lower for token in ["scope", "boundary", "falsifier", "negative control"]):
                    boundary_like.append(item)
                else:
                    observation_like.append(item)
            prose_parts = []
            if claim_like:
                prose_parts.append("Claim boundary: " + _public_sentence_values(claim_like))
            if evidence_like:
                prose_parts.append("Evidence support: " + _public_sentence_values(evidence_like))
            if observation_like:
                prose_parts.append("Recorded content: " + _public_sentence_values(observation_like))
            if boundary_like:
                prose_parts.append("Reopening boundary: " + _public_sentence_values(boundary_like))
            payload = " ".join(prose_parts or selected)
            template = transition_templates[(idx - 1) % len(transition_templates)]
            body.append(
                _tex_paragraph(
                    template.format(payload=payload)
                )
            )
        if idx % 4 == 0:
            body.append(
                _tex_paragraph(
                    f"Synthesis checkpoint {idx}. The preceding entries should be read together: promotion is earned by an "
                    "alignment between claim wording, evidence class, and reopening rule. If any one of those three "
                    "moves, the public sentence has to move with it."
                )
            )
    if len(rows) > limit:
        body.append(
            _tex_paragraph(
                f"The complete register has {len(rows)} entries. Entries beyond this representative set stay in the "
                "public evidence package rather than being dumped into the main prose; the manuscript records the "
                "reading contract for the complete artifact while keeping the argument readable."
            )
        )
    return "\n".join(body)


def _reviewer_and_journal_summary(attack_rows: list[dict[str, Any]], package_rows: list[dict[str, Any]]) -> str:
    themes: dict[str, dict[str, Any]] = {}
    for row in attack_rows:
        joined = " ".join(str(value) for value in row.values()) if isinstance(row, dict) else str(row)
        if re.search(
            r"\b(?:NOSEND|NO[-_ ]?SEND|ADV-NOSEND|OC133-NOSEND|publish_allowed|owner_approved|zenodo_deposit_allowed|global_no_send_lock)\b",
            joined,
            re.I,
        ):
            continue
        theme = _public_clean(row.get("theme") or row.get("attack_class") or row.get("failure_mode") or "general scientific objection")
        if re.search(r"corporate|owner|publication permission|release permission|no[- ]send|control", theme, re.I):
            continue
        themes.setdefault(theme, row)
        if len(themes) >= 12:
            break

    body = [
        r"\section{Reviewer Objections and Scientific Response}",
        r"\label{sec:oc133-reviewer-response-journal-preparation}",
        _tex_paragraph(
            "This section is a prose map, not a dumped adversarial register. A hostile reader should be able to see "
            "which claim is threatened, why the objection matters, which evidence answers it, and which condition "
            "would reopen it. Full machine rows remain in the public evidence package."
        ),
        _tex_paragraph(
            "The journal-facing preparation material is likewise bounded. Venue packages are owner-review preparation packets. "
            "They do not mean that a journal submission has occurred, and they do not change the scientific claim "
            "surface of the public release."
        ),
    ]
    for idx, (theme, row) in enumerate(themes.items(), start=1):
        objection = _public_clean(row.get("objection") or row.get("failure_mode") or "the public claim may outrun the evidence")
        attacked = _public_clean(row.get("attacked_claim") or "a bounded promoted model-core claim")
        evidence = _public_clean(row.get("closure_evidence_refs") or row.get("closure_evidence") or row.get("evidence_ref") or "the relevant proof, finite-model, replay, comparator, or claim-boundary artifact")
        if len(evidence) > 360:
            evidence = "the relevant proof, finite-model, replay, comparator, or claim-boundary artifact named in the evidence package"
        body.extend(
            [
                rf"\subsection{{Reviewer challenge {idx}: {_tex_escape(theme.title())}}}",
                _tex_paragraph(
                    f"A hostile reviewer may argue that {objection.rstrip('.')}. The threatened claim is "
                    f"{attacked.rstrip('.')}. The objection matters because the release is defensible only while the "
                    "public claim and its evidence boundary are aligned."
                ),
                _tex_paragraph(
                    f"The response is evidence-bound: {evidence}. A stronger public claim, stale evidence link, failed "
                    "negative control, missing replay hash, or failed adversarial review reopens the challenge and "
                    "blocks publication until the claim is repaired, demoted, or supported by new evidence."
                ),
            ]
        )

    venues = []
    for row in package_rows:
        venue = _public_clean(row.get("venue_id") or row.get("venue_name") or "")
        if venue:
            venues.append(venue)
    if venues:
        body.extend(
            [
                r"\subsection{Journal Owner-Review Preparation Map}",
                _tex_paragraph(
                    "The release package carries owner-review preparation material for "
                    f"{', '.join(venues[:8])}. These packets support later editorial decisions by mapping the "
                    "monograph, journal article, reproducibility companion, reviewer response map, conflict/funding "
                    "statement, data/reproducibility statement, and AI assistance disclosure to venue expectations."
                ),
                _tex_paragraph(
                    "The preparation packets are not submission events. Before any real submission, the publication "
                    "capability must refresh the venue requirements, select the exact target, verify formatting and "
                    "length, update cover letters, and obtain a separate submission authorization."
                ),
            ]
        )
    return "\n".join(body)


def _positive_obligation_playbooks() -> str:
    sections = [
        (
            "Claim adequacy playbook",
            "A promoted claim is adequate only when a reader can identify the object, the assumption set, the proof or "
            "data route, the prior-art relation, the reviewer attack surface, and the reopening condition. The standard "
            "is positive: absence of forbidden wording is not enough. The manuscript must teach the claim well enough "
            "that a hostile reviewer can reconstruct why the release believes it, what would make it false, and which "
            "artifact carries the burden of support."
        ),
        (
            "Model integration playbook",
            "A model section must explain why the tuple components belong together. It must not merely list carriers, "
            "realizations, liveness, residue, boundaries, morphisms, operators, cycles, dimensions, and K-levels. It must "
            "show how each component changes the questions the model can answer and how removing the component changes "
            "the semantic verdict suite. This is why the monograph treats component witnesses as part of the public "
            "argument rather than hiding them in a build log."
        ),
        (
            "Proof adequacy playbook",
            "A theorem label is not a theorem by itself. The release requires a statement, assumptions, definitions, "
            "dependency route, proof sheet, counterexample boundary, and wherever possible a Lean declaration or finite "
            "semantic witness. The public prose must say which part of the support is mathematical proof, which part is "
            "machine-checked subset, and which part is executable witness. Mixing those levels is a publication defect."
        ),
        (
            "Empirical adequacy playbook",
            "An empirical row is adequate only when the formula, pinned snapshot, target-blind or held-out split, "
            "predicted value, observed value, uncertainty or residual, comparator, negative control, falsifier, and "
            "replay hash are visible to the reviewer. A replay row may support a bounded reconstruction claim; it does "
            "not by itself promote whole-domain proof or a domain-general law. The reader must see that boundary "
            "before seeing the numeric table."
        ),
        (
            "Prior-art adequacy playbook",
            "Prior-art work is not a decoration and not a defensive bibliography. The manuscript has to state overlap "
            "first, residual delta second, and unsupported priority claims never. For each comparator family, the reader "
            "should be able to say what OC inherits, what it translates into its typed vocabulary, what it adds at the "
            "release surface, and what remains a research target."
        ),
        (
            "Phenomenon coverage playbook",
            "A phenomenon name is not an explanation. A coverage row becomes release-facing only when it supplies a "
            "formal instance, observable, replay or prediction path, comparator, negative control, falsifier, and "
            "claim boundary. If those pieces are not present, the manuscript may mention the phenomenon as motivation "
            "or future work, but it may not count it as explained."
        ),
        (
            "Didactic adequacy playbook",
            "A publication-grade text must answer who the reader is, what the text is for, what order the reader should "
            "follow, and why that order teaches the model. Definitions must precede theorem pressure; examples must "
            "precede hostile edge cases where the target reader would otherwise be lost; visual routes must operationalize "
            "the model rather than decorate it."
        ),
        (
            "Editorial adequacy playbook",
            "The editorial layer must enforce one voice, coherent transitions, consistent terminology, title page, "
            "dedication, version, DOI, abstract, reader contract, table of contents, citation path, and readable prose. "
            "A text assembled from old pages plus appended updates fails even if every page is individually true, because "
            "the scientific object has not been rewritten as one public manuscript."
        ),
        (
            "Release adequacy playbook",
            "A release is not a pile of files. The public archive must present the human reading order first, then the "
            "evidence package, then metadata and checksums. Zenodo and GitHub metadata must name the same version, DOI, "
            "asset set, claim boundary, and citation route. If metadata, PDFs, and package contents describe different "
            "objects, the release is scientifically ambiguous and must be blocked."
        ),
        (
            "Known-error learning playbook",
            "Every failure pattern that has occurred once becomes a future gate. Raw TeX leakage, route-sheet public "
            "PDFs, metadata-first archive pages, absent dedication, absent title pages, stale version identity, control "
            "locks in public artifacts, unsupported superiority language, register-dominated prose, and post-publication "
            "visual defects are now known errors. The release standard is not memoryless; the machine must become stricter "
            "after each incident."
        ),
        (
            "Current science-state register playbook",
            "The internal science-state register records where the research actually stands: model maturity, formal proof support, "
            "finite semantic support, empirical replay support, prior-art support, phenomenon coverage, editorial state, "
            "and external speech boundary. The external text must be derived from that state. If the register says a broad "
            "claim is still background science, the public manuscript cannot promote it through enthusiasm, layout, or "
            "metadata accident."
        ),
        (
            "Reviewer-prosecution playbook",
            "The final reader is assumed hostile. A good release should survive the questions: What exactly is new? What "
            "is only reframing? What is mathematically proved? What is merely simulated? What is only replay QA? What "
            "would falsify the claim? What prior theory already covers this? Why does the public artifact deserve to be "
            "read as science rather than as a process archive? The manuscript must answer those questions before publication."
        ),
    ]
    body = [
        r"\section{Positive Scientific and Editorial Playbooks}",
        r"\label{sec:oc133-positive-obligation-playbooks}",
        _tex_paragraph(
            "This section records the must-have side of the publication standard. Negative gates catch forbidden states; "
            "positive gates require the manuscript to accomplish its scientific task. These playbooks are written into "
            "the monograph so the reader can see the standard that shaped the release and future releases can be judged "
            "against the same method."
        ),
    ]
    for title, paragraph in sections:
        body.append(rf"\subsection{{{_tex_escape(title)}}}")
        body.append(_tex_paragraph(paragraph))
        body.append(
            _tex_paragraph(
                "The measurable check is bidirectional. The manuscript must expose the reader-facing explanation, and "
                "the evidence package must expose the artifact that can confirm or reopen it. If either side is missing, "
                "the standard treats the text as incomplete even when no obvious typo or forbidden word is present."
            )
        )
    body.append(
        _tex_paragraph(
            "The practical consequence is that future documents cannot advance through drafting, editorial review, "
            "release packaging, archive publication, or post-release verification by satisfying only no-go rules. They "
            "must also satisfy the positive role contract for their document class, audience, claim surface, evidence "
            "surface, design surface, and release destination."
        )
    )
    body.extend(
        [
            r"\subsection{Document-Class Positive Contracts}",
            _tex_paragraph(
                "A master monograph must be a complete teaching artifact. It carries the long-form motivation, the full "
                "model vocabulary, the theorem roadmap, proof boundaries, finite and formal evidence, empirical replay "
                "interpretation, prior-art positioning, reviewer response logic, and reproducibility boundary. Its job is "
                "not to be short; its job is to make the scientific object coherent enough that every supporting artifact "
                "has a visible place in the argument."
            ),
            _tex_paragraph(
                "A journal core article has a different contract. It must let an editor or first reviewer understand the "
                "scientific contribution without reading the entire monograph first. It therefore compresses the claim "
                "surface, theorem route, evidence route, prior-art boundary, and limitations into an article-shaped path. "
                "Compression is allowed; loss of claim/evidence alignment is not."
            ),
            _tex_paragraph(
                "A methods and reproducibility companion is not a command list. It must teach what each command checks, "
                "which input it consumes, which output it produces, what mismatch means, and which scientific claim is "
                "threatened by a failure. Without that interpretation layer, reproducibility becomes a mechanical ritual "
                "rather than a scientific method."
            ),
            _tex_paragraph(
                "A reviewer attack map must not be a table of status tokens. It must make criticism intelligible: why the "
                "objection is dangerous, what claim it attacks, what evidence answers it, and what residual condition "
                "would reopen it. A hostile reader should feel that the strongest objections have been understood rather "
                "than hidden behind process vocabulary."
            ),
            _tex_paragraph(
                "A release guide is the public landing contract. It explains where to begin, what each file is for, what "
                "to cite, what the DOI means, what is included for human reading, what is included for machine replay, "
                "and which claims are deliberately not promoted. A release guide that opens with metadata, raw hashes, "
                "or hidden process state fails the public surface even when the archive files are technically present."
            ),
            r"\subsection{Quantitative Positive Thresholds}",
            _tex_paragraph(
                "The publication standard uses quantitative thresholds because taste alone is too weak. Each public PDF "
                "has minimum page and text-volume thresholds, mandatory frontmatter anchors, required reader-contract "
                "language, required transition density, maximum tolerance for route-sheet vocabulary, and mandatory "
                "evidence anchors. Those numbers do not make the text good by themselves, but they prevent empty or "
                "stub-like artifacts from being mistaken for publication-grade documents."
            ),
            _tex_paragraph(
                "Positive thresholds also apply to the science graph. The release must expose a minimum model-component "
                "coverage set, a theorem/proof/evidence coverage set, a finite semantic witness set, a domain replay set, "
                "a prior-art family set, a phenomenon model-card set, a reviewer-objection set, and a public metadata "
                "parity set. If a surface is missing, the release cannot advance by saying that no forbidden word was found."
            ),
            _tex_paragraph(
                "The thresholds are deliberately asymmetric. Forbidden states have zero tolerance: stale version identity, "
                "absent title page, absent dedication, raw TeX leakage, control locks on public surfaces, unsupported "
                "superiority claims, and public metadata contradictions block release immediately. Positive obligations "
                "have minimum thresholds plus reviewer judgment: enough prose, enough examples, enough visuals, enough "
                "literature synthesis, enough traceability, and enough methodological explanation to fulfill the document role."
            ),
            _tex_paragraph(
                "A threshold failure is diagnostic. A page-count failure in the monograph means the release may have "
                "dropped substantive integrated science. A transition-density failure means the text may be a list rather "
                "than an argument. A visual-anchor failure means the model may be too abstract for the intended reader. "
                "A prior-art-family failure means novelty could be overstated. A claim/evidence failure means the public "
                "surface has outrun the research."
            ),
            r"\subsection{Process Research-State Register and External Speech}",
            _tex_paragraph(
                "The process research-state register is the internal map that prevents blind writing. It records the current maturity "
                "of the research, the current proof/evidence state, the current open full-science obligations, and the "
                "allowed external speech boundary. The manuscript generator consumes that state so it cannot accidentally "
                "describe an ambition as if it were a completed result."
            ),
            _tex_paragraph(
                "External speech is derived from three layers. The first layer is the model-core evidence actually promoted "
                "in the release. The second layer is the broader research program that may be discussed as motivation or "
                "future work. The third layer is internal process state that must stay internal unless it is transformed "
                "into a public-safe methodological explanation. Confusing those layers is exactly the failure pattern this "
                "release standard is designed to eliminate."
            ),
            _tex_paragraph(
                "For OC Core 1.3.3, this means the release can say that the model core is ready for external review under "
                "bounded proof, finite, replay, and comparator evidence. It cannot say that every domain of science has "
                "been numerically solved or that all modern science has been surpassed. Those remain research objectives "
                "until the science-state register, evidence graph, and reviewer gates support them literally."
            ),
            r"\subsection{End-to-End Standard Enforcement}",
            _tex_paragraph(
                "The enforcement path begins before writing. A document proposal must declare audience, role, claim surface, "
                "evidence obligations, source corpus, and destination. Drafting then pulls from the ontology and current "
                "science-state register rather than from ad hoc wording. Editorial review checks style, structure, didactics, "
                "visual pedagogy, terminology, and claim/evidence fit. Scientific review checks proof, data, simulation, "
                "prior art, and falsifiers. Release review checks metadata, archive files, DOI, asset order, checksums, "
                "and public presentation."
            ),
            _tex_paragraph(
                "Post-release verification is part of the same standard. The public page must render professionally, files "
                "must be downloadable, checksums must match, DOI and citation metadata must agree, older defective records "
                "must be superseded or incident-logged, and the incident memory must become future tests. The standard is "
                "therefore not only a writing rule; it is a learning loop for the whole publication machine."
            ),
        ]
    )
    rubric_rows = [
        ("Audience fit", "defines the exact reader classes and gives each class a path through the document"),
        ("Problem formulation", "states the scientific problem before introducing internal notation"),
        ("Concept introduction", "introduces every nonstandard term before using it in theorem or evidence pressure"),
        ("Notation discipline", "keeps symbols stable and explains aliases, version changes, and overloaded words"),
        ("Assumption visibility", "places assumptions next to the claim they support rather than burying them in appendices"),
        ("Example sufficiency", "provides enough examples for a new reader to test whether the definition has been understood"),
        ("Counterexample boundary", "states what kind of case would break the claim or force demotion"),
        ("Proof dependency", "maps each theorem claim to definitions, lemmas, proof sheet, and executable support where applicable"),
        ("Machine-check scope", "separates what Lean checks from what remains prose proof or executable finite witness"),
        ("Finite semantics", "shows positive witnesses and negative controls without asking the reader to trust labels"),
        ("Empirical formula", "states the formula and target before showing a result"),
        ("Snapshot provenance", "identifies pinned data sources and hashes for every replay row"),
        ("Comparator baseline", "names the baseline used to judge a numeric or conceptual claim"),
        ("Residual interpretation", "explains what an error, uncertainty, or residual means scientifically"),
        ("Falsifier availability", "gives the reader a concrete way to reopen the claim"),
        ("Prior-art overlap", "acknowledges predecessors before stating residual delta"),
        ("Novelty boundary", "refuses priority language where the evidence is only positioning"),
        ("Phenomenon model card", "connects phenomenon, formal instance, observable, replay path, comparator, and falsifier"),
        ("Visual pedagogy", "uses diagrams to operationalize the model rather than decorate the page"),
        ("Narrative cohesion", "uses transitions that explain why the next section follows from the previous one"),
        ("Style consistency", "keeps voice, terminology, and claim strength consistent across all public PDFs"),
        ("Bibliography adequacy", "shows immersion in the surrounding scientific field rather than a token reference list"),
        ("Metadata parity", "makes DOI, version, asset set, title, citation, and archive description agree across destinations"),
        ("Archive presentation", "places human-readable science before machine-readable support files on public records"),
        ("Known-error memory", "turns every discovered publication failure into a future regression test"),
        ("Workstream isolation", "keeps research, editorial, release, incident, and product lines distinct but traceable"),
        ("Ontology enforcement", "knows whether each entity is author, instrument, method, artifact, channel, venue, or claim"),
        ("Internal/external naming", "separates internal identifiers from public positioning language"),
        ("Resource discipline", "runs expensive review only after deterministic deltas justify it"),
        ("Post-release audit", "verifies the live public surface and records supersession or repair state"),
    ]
    body.append(r"\subsection{Operational Rubric for Positive Gates}")
    body.append(
        _tex_paragraph(
            "The following rubric is intentionally operational. Each item states a must-have property and the review "
            "question that prevents the item from becoming a vague aspiration. The release should not advance when a "
            "document merely avoids mistakes; it advances only when the required property is present and inspectable."
        )
    )
    for idx, (label, obligation) in enumerate(rubric_rows, start=1):
        body.append(rf"\subsubsection{{Rubric {idx}: {_tex_escape(label)}}}")
        body.append(
            _tex_paragraph(
                f"Positive obligation. The document {obligation}. The relevant reviewer question is not whether the "
                "document contains a related word, but whether the reader can use the document to perform the intended "
                "scientific action without private context."
            )
        )
        body.append(
            _tex_paragraph(
                "Quantitative enforcement. The gate records anchors, counts, coverage flags, contradiction flags, and "
                "artifact references where deterministic checks are possible. Qualitative enforcement is then delegated "
                "to editorial and scientific adversarial review. A failure in either layer becomes a work order, and the "
                "same failure pattern is added to known-error management before the next release attempt."
            )
        )
    return "\n".join(body)


def _public_scientific_claim_rows(claim_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return release claims that belong in the public scientific spine."""
    rows: list[dict[str, Any]] = []
    for row in claim_rows:
        if not isinstance(row, dict):
            continue
        joined = " ".join(str(row.get(key) or "") for key in ("claim_id", "claim", "theme", "support", "evidence_ref", "scope_limit"))
        if re.search(r"\b(NOSEND|NO[-_ ]?SEND|OWNER|PUBLISH|PUBLICATION|RELEASE[-_ ]?PERMISSION|CONTROL[-_ ]?PLANE|JOURNAL[-_ ]?SUBMISSION)\b", joined, re.I):
            continue
        rows.append(row)
    return rows


def _integrated_claim_argument_sections(claim_rows: list[dict[str, Any]], proof_rows: list[dict[str, Any]]) -> str:
    proof_by_id = {
        str(row.get("theorem_id") or row.get("claim_id") or ""): row
        for row in proof_rows
        if isinstance(row, dict)
    }
    promoted = [
        row
        for row in _public_scientific_claim_rows(claim_rows)
        if isinstance(row, dict)
        and (
            row.get("scientific_promotion_allowed") is True
            or str(row.get("public_status") or "").lower().startswith("bounded promoted")
            or "PROMOTED_BOUNDED" in str(row.get("public_status") or "")
        )
    ]
    body = [
        r"\section{Claim-by-Claim Integrated Argument}",
        r"\label{sec:oc133-claim-by-claim-integrated-argument}",
        _tex_paragraph(
            "This section is the prose counterpart to the claim and theorem registers. It is intentionally longer than a "
            "manifest because a publication-grade monograph must teach the reader why each promoted claim exists, what "
            "problem it solves, which evidence carries it, and where the claim stops. The register remains available for "
            "audit; the argument below is written for scientific reading."
        ),
        r"\subsection{Shared Claim Reading Method}",
        _tex_paragraph(
            "Every promoted model-core claim is read by the same method. First, identify the scientific ambiguity that the "
            "claim removes. Second, identify the typed OC construction that carries the distinction. Third, identify the "
            "proof sheet, formal fragment, finite semantic witness, replay row, comparator row, or claim-boundary record "
            "that can carry the public sentence. Fourth, identify the reopening condition. This common method is stated "
            "once here so that the following subsections can focus on the scientific work of each claim rather than repeat "
            "the same editorial apparatus."
        ),
        _tex_paragraph(
            "The dependency route is layered rather than interchangeable. Definitions provide vocabulary; proof sheets "
            "state assumptions and lemmas; Lean records the encoded fragment; finite semantic cases show executable "
            "positive and negative behavior where the theorem is finite; empirical replay rows support only bounded "
            "artifact and reconstruction claims; comparator rows protect novelty wording; and reviewer gates check that "
            "the public sentence has not drifted beyond the evidence. No layer is allowed to impersonate another."
        ),
        _tex_paragraph(
            "The hostile-review method is likewise fixed. A reviewer may remove a tuple component, collapse a status "
            "distinction, turn a boundary into a metaphor, treat a finite witness as a broad empirical prediction, or "
            "upgrade a comparator overlap into priority. A claim survives only while the named proof and evidence path "
            "blocks that attack at the stated strength. Otherwise the claim is repaired, demoted, or held for a later "
            "research release."
        ),
        _tex_paragraph(
            "The editorial method is different from the proof method but it is not optional. The prose must let a reader "
            "see the problem, construction, evidence, and boundary without parsing a control table. Row identifiers serve "
            "as citations for audit and reproduction; they are not the voice of the scientific argument. The following "
            "subsections therefore preserve exact evidence identifiers while making each claim readable as science."
        ),
    ]
    claim_openers = [
        "The first question for this claim is what weaker vocabulary would confuse.",
        "The claim is useful only if it separates two situations that a less typed account would merge.",
        "The scientific burden here is to show why the named distinction is not merely verbal.",
        "This claim earns its public place by making a repair condition visible.",
        "The reviewer-facing issue is whether the construction changes the space of admissible explanations.",
        "The practical reading starts with the error that the claim prevents.",
    ]
    for idx, row in enumerate(promoted[:12], start=1):
        cid = _public_clean(row.get("claim_id") or f"claim-{idx}")
        proof = proof_by_id.get(cid, {})
        title = _public_clean(proof.get("title") or cid)
        claim = _public_clean(row.get("claim") or proof.get("public_claim_boundary") or title)
        support = _public_clean(row.get("support") or proof.get("evidence_ceiling") or "bounded proof and finite semantic support")
        evidence = _public_clean(
            proof.get("proof_sheet_ref")
            or row.get("evidence_ref")
            or proof.get("evidence_ref")
            or "the named public proof sheet and finite semantic evidence"
        )
        lean = _public_clean(proof.get("lean_ref") or "the Lean subset where the theorem has a declared formal counterpart")
        scope = _public_clean(row.get("scope_limit") or proof.get("scope_limit") or "the stated assumptions and counterexample boundary")
        body.extend(
            [
                rf"\subsection{{{_tex_escape(cid)}: {_tex_escape(title)}}}",
                _tex_paragraph(
                    f"{claim_openers[(idx - 1) % len(claim_openers)]} The claim addresses this ambiguity: {claim} "
                    "The point of including it in the 1.3.3 release is to make the ambiguity auditable rather than to "
                    "decorate the theory with another label."
                ),
                _tex_paragraph(
                    f"The support class is {support}. The proof route is {evidence}; the formal route is {lean}. In the "
                    "public reading, this means that the claim is carried by a named theorem boundary, not by the fact that "
                    "a row exists. If the proof sheet, Lean reference, finite witness, or mutation control does not carry "
                    "the visible wording, the visible wording is the part that must move."
                ),
                _tex_paragraph(
                    f"The release boundary is {scope}. This boundary is not decorative. It prevents a bounded model-core "
                    "statement from becoming a claim about unrestricted totality, all-domain prediction, or global priority. The "
                    "scientific value of the claim is that it is strong enough to test a real structural distinction and "
                    "narrow enough that an adversarial reviewer can name the condition that would reopen it."
                ),
                _tex_paragraph(
                    "A worked reading asks three local questions. Which typed field, operator, boundary, status predicate, "
                    "or morphism is doing the work? Which situation is the positive case? Which negative case would have "
                    "collapsed the distinction if the claim were only a slogan? The answer to those questions is the "
                    "practical content of this subsection."
                ),
                _tex_paragraph(
                    f"For {cid}, the corresponding falsifier is concrete rather than slogan-like: find a model satisfying the "
                    "stated assumptions in which the asserted distinction collapses, show that the positive witness was "
                    "accepted for the wrong reason, show that the negative control is non-responsive, or show that the public "
                    "wording requires an assumption absent from the proof sheet."
                ),
                _tex_paragraph(
                    "The prior-art and empirical boundaries are local to the claim. Earlier formalisms may already carry "
                    "part of the distinction; when they do, OC claims integration only for that part. Numeric replay rows "
                    "can demonstrate artifact discipline, comparator behavior, and falsifier plumbing, but they do not by "
                    "themselves complete a domain science. The reader should therefore leave with four handles: the "
                    "conceptual problem, the typed construction, the evidence route, and the reopening route."
                ),
            ]
        )
    return "\n".join(body)


def _scientific_reading_protocol_section() -> str:
    body = [
        r"\section{Scientific Reading Protocol for the 1.3.3 Monolith}",
        r"\label{sec:oc133-scientific-reading-protocol}",
        _tex_paragraph(
            "The monolith is intentionally long because it has to serve several readers at once: a formal reviewer, a "
            "domain scientist, an editor, a reproducibility auditor, and a hostile reader looking for overclaim. The "
            "recommended protocol is not to read every evidence row first. The reader should first understand the object "
            "grammar, then the theorem ceiling, then the executable evidence, then the comparator boundary, and only then "
            "the release and journal-preparation apparatus."
        ),
        _tex_paragraph(
            "Step one is the object grammar. The reader should be able to say what a carrier is, what a realization is, "
            "what lawful possibility permits, what liveness means at a time slice, what residue preserves after death, "
            "what an identity morphism is allowed to preserve, and why a boundary is not merely a metaphor. If this grammar "
            "is unclear, later empirical and release sections should be paused rather than skimmed."
        ),
        _tex_paragraph(
            "Step two is the theorem ceiling. Each theorem should be read as a bounded claim with assumptions, proof route, "
            "finite witness route, and counterexample boundary. The purpose of the theorem registry is not to impress the "
            "reader with labels; it is to make it impossible for a public sentence to float away from its proof obligation. "
            "A label that cannot be traced to proof and boundary is editorially unfinished."
        ),
        _tex_paragraph(
            "Step three is the executable layer. The Lean subset and finite semantic checks are not decorations and they are "
            "not substitutes for the entire mathematical theory. They are selected executable anchors: places where the "
            "reader can see that a semantic distinction has been encoded, accepted, rejected, or mutation-tested. Their "
            "scientific role is strongest when the negative control is as visible as the positive witness."
        ),
        _tex_paragraph(
            "Step four is the empirical layer. The target-blind rows and replay-QA tables are read as evidence of disciplined "
            "claim-to-data plumbing. They demonstrate formula binding, snapshot binding, comparator binding, uncertainty or "
            "residual accounting, negative control, falsifier, and replay hash. They do not close every future domain; they "
            "show how a domain claim must be made if it is to enter the release surface."
        ),
        _tex_paragraph(
            "Step five is the comparator layer. The reader should look for accepted overlap before looking for residual "
            "delta. If the manuscript sounds as if it invented general systems theory, autopoiesis, dynamical systems, "
            "category theory, RAF theory, complexity measures, identity theory, or reproducibility engineering, then the "
            "wording has failed. The defensible contribution is the bounded integration and governance of claim, proof, "
            "data, comparator, and reopening conditions."
        ),
        _tex_paragraph(
            "Step six is the adversarial layer. Reviewer objections are not an appendix of public relations. They are part "
            "of the scientific control surface. A good objection names the attacked claim, the exact failure mode, the "
            "evidence that would answer it, and the residual condition that would reopen it. The release is stronger when "
            "those routes are explicit because a hostile reader can test the same paths the authors used."
        ),
        _tex_paragraph(
            "Step seven is the publication layer. GitHub and Zenodo package the public scientific object; journal packets "
            "remain owner-review preparation material until a later venue-specific action. Metadata, checksums, PDFs, and "
            "asset lists are not secondary chores: they are part of the reproducibility perimeter. A release whose metadata "
            "contradicts its manuscript is scientifically damaged even if the proofs are locally sound."
        ),
        _tex_paragraph(
            "This reading protocol is also a repair protocol. When a defect appears, the correction should target the first "
            "layer where the defect originates: ontology, theorem boundary, executable witness, empirical replay, comparator "
            "positioning, adversarial response, editorial prose, or publication packaging. That is how the system avoids "
            "random review churn and closes the most important vulnerabilities before spending attention on polish."
        ),
    ]
    return "\n".join(body)


def _bounded_replay_argument_section() -> str:
    body = [
        r"\section{Bounded Replay QA and Artifact-Integrity Examples}",
        r"\label{sec:oc133-bounded-replay-qa-artifact-integrity-examples}",
        _tex_paragraph(
            "This section states the empirical role of the 1.3.3 release in prose. The release contains bounded replay QA "
            "and artifact-integrity examples, not a completed empirical conquest of every domain. The distinction matters: "
            "a target-blind replay row demonstrates that a claim can be tied to a formula, a source snapshot, a comparator, "
            "a residual calculation, a negative control, a falsifier, and a replay hash. It does not by itself license a "
            "broader domain theory."
        ),
        _tex_paragraph(
            "Physics rows are read as constants-and-reconstruction checks. A reader should inspect the pinned source, the "
            "formula, the observed value, the uncertainty or tolerance, the comparator baseline, and the falsifier. The "
            "scientific question is whether the release can preserve the difference between a replayable bounded statement "
            "and a grand physics claim. If the row loses that difference, promotion is too strong."
        ),
        _tex_paragraph(
            "Chemistry rows are read in the same way. A PubChem or NIST-derived row is not a claim that OC has replaced "
            "chemistry. It is a claim that the release machinery can bind a chemical statement to a source, formula, "
            "comparator, residual, negative control, and falsifier without drifting into unsupported chemical novelty."
        ),
        _tex_paragraph(
            "Biology rows are more sensitive because biological interpretation is easy to overread. The bounded role is "
            "therefore explicit: the row demonstrates replay discipline and model-card routing for a named biological "
            "signal or count. It does not claim that the release closes organismal biology, evolution, development, or "
            "systems biology as completed empirical domains."
        ),
        _tex_paragraph(
            "Systems and civilizational rows are bounded even more tightly. A World Bank or macro-series replay can show "
            "snapshot integrity, target-blind reconstruction, comparator behavior, residual accounting, and reopening "
            "conditions. It cannot, in this release, become a universal social-science forecast or a completed model of "
            "civilizational dynamics."
        ),
        _tex_paragraph(
            "Mathematics rows are not empirical rows in the same sense. They anchor executable finite-model behavior and "
            "proof-route discipline. The important question is whether the finite case was computed independently from raw "
            "model facts and whether the tamper controls fail when they should. A label-only success is not evidence."
        ),
        _tex_paragraph(
            "The comparator baseline is part of the evidence, not an optional column. Without a comparator, a residual is "
            "hard to interpret; without a residual, a prediction is not measured; without a negative control, success may "
            "be self-confirmation; without a falsifier, the claim cannot be scientifically reopened. The release requires "
            "all of these pieces before a replay row can support even bounded public wording."
        ),
        _tex_paragraph(
            "The replay hash gives the row its reproducibility perimeter. A reader or auditor should be able to ask whether "
            "the same source snapshot and same reconstruction script produce the same table. If not, the row is not silently "
            "massaged into compatibility; the artifact is regenerated, the mismatch is explained, or the public claim is "
            "demoted."
        ),
        _tex_paragraph(
            "This is why the release separates model-core promotion from empirical ambition. The typed model can be defended "
            "by formal and finite evidence while empirical domains continue to mature. That separation is not weakness; it "
            "is what prevents the release from pretending that replay QA is already full domain closure."
        ),
        _tex_paragraph(
            "A hostile reviewer should therefore attack each empirical row by asking five questions: is the source pinned, "
            "is the formula explicit, is the comparator meaningful, is the residual accounted for, and is the falsifier "
            "capable of failing the row? A row that cannot answer those questions is not eligible for promoted public "
            "wording in this release."
        ),
        _tex_paragraph(
            "An editor should ask a different question: can a reader understand the role of the row without reading the raw "
            "JSON? The monograph must answer yes. The raw table remains in the evidence package for reproducibility, while "
            "the prose explains what the row does and what it does not do."
        ),
        _tex_paragraph(
            "Future releases may expand these lanes into stronger empirical claims. The 1.3.3 standard is that expansion "
            "must happen through new source locks, held-out or target-blind protocols, comparators, uncertainty, residuals, "
            "negative controls, falsifiers, replay hashes, and adversarial review. It cannot happen through rhetorical "
            "confidence alone."
        ),
    ]
    return "\n".join(body)


def _bounded_scientific_synthesis_sections() -> str:
    topics = [
        (
            "Typed continuum object",
            "The release treats a continuum as a typed object rather than as an informal metaphor. The carrier gives "
            "the substrate of possible distinctions, realization states which distinctions are active, liveness states "
            "which realized structure is currently admissible, residue records what remains after liveness fails, and "
            "boundaries say where the object can be separated, tested, or reopened."
        ),
        (
            "Lifecycle interpretation",
            "Death, residue, and rebirth are not presented as poetic terms. In the bounded model core, death means the "
            "live predicate no longer holds under declared invariants; residue means there is a typed remnant relation "
            "available for later comparison; rebirth means a later realization may be compared to a prior one through "
            "declared preservation conditions. The identity claim stops exactly where those conditions stop."
        ),
        (
            "K-level interpretation",
            "The K-level taxonomy is a witness discipline. Moving upward adds an observable or organizational distinction "
            "that changes the retained verdict suite; lawful demotion is allowed when the added observable is inert for "
            "the relevant claim. This prevents the hierarchy from becoming a decorative ladder: each promoted transition "
            "must have a retained distinction, a reduction failure or lawful demotion rule, and a reviewer-facing witness."
        ),
        (
            "Boundary interpretation",
            "A boundary is not only a metric threshold. It can be a classifier, interface, admissible-region boundary, "
            "semantic separation, or typed relation that determines where a claim can be tested. The release uses that "
            "generalized boundary concept to connect formal proofs, finite witnesses, and empirical falsifiers without "
            "pretending that every boundary is numerical."
        ),
        (
            "Operator interpretation",
            "Operators are treated as typed transformations with explicit domain and preservation obligations. Smooth flow, "
            "discrete update, guard/reset behavior, cycle movement, and hybrid transition are separated so that a reviewer "
            "can attack the exact regularity assumption. A derivative claim is not imported into a discrete update merely "
            "because both are called dynamics."
        ),
        (
            "Proof interpretation",
            "The theorem surface is bounded by assumptions and proof routes. Prose proof sheets carry the complete human "
            "argument; Lean checks a selected formal subset; finite semantic cases show positive witnesses and mutation "
            "controls. This plural proof route is not a claim of total mechanization. It is a way to make theorem pressure "
            "visible at several levels of review."
        ),
        (
            "Empirical interpretation",
            "The numeric layer is interpreted as bounded replay and reconstruction. It demonstrates that selected domain "
            "lanes can bind formula, snapshot, split, comparator, residual, negative control, falsifier, and replay hash. "
            "It does not authorize a claim that the whole domain has been proved. A failed row reopens its claim boundary; "
            "a passing row supports only the declared bounded reconstruction."
        ),
        (
            "Prior-art interpretation",
            "The literature layer accepts that OC overlaps with existing systems, autopoiesis, dynamical, categorical, RAF, "
            "complexity, identity, hybrid, and reproducibility traditions. The release-level delta is the combined typed "
            "model-core and evidence-governance package, not the invention of all constituent vocabulary. Novelty remains "
            "bounded unless a systematic same-claim comparison supports a stronger statement."
        ),
        (
            "Phenomenon interpretation",
            "A phenomenon is counted only when the public material supplies a model-card path: formal instance, observable, "
            "prediction or replay route, comparator, negative control, falsifier, and claim boundary. Illustrative examples "
            "may teach the model, but they do not become promoted explanations until that path exists."
        ),
        (
            "Reviewer interpretation",
            "Adversarial review is part of the scientific surface. The release is written so a critic can ask whether a "
            "claim is merely another theory reframed, whether it explains a named phenomenon, whether the evidence is "
            "too weak, whether prior art already covers the result, or whether a theorem is only a label. Each serious "
            "question has to map to a claim boundary and an evidence route."
        ),
    ]
    body = [
        r"\section{Integrated Scientific Synthesis for OC Core 1.3.3}",
        r"\label{sec:oc133-integrated-scientific-synthesis}",
        _tex_paragraph(
            "This section integrates the 1.3.3 contribution as science rather than as release process. It summarizes how "
            "the typed model core, theorem support, finite semantics, empirical replay, prior-art positioning, phenomenon "
            "coverage, and adversarial review fit together inside the public scientific object."
        ),
    ]
    for title, paragraph in topics:
        body.append(rf"\subsection{{{_tex_escape(title)}}}")
        body.append(_tex_paragraph(paragraph))
        body.append(
            _tex_paragraph(
                "The reviewer payoff is concrete: the statement can be attacked at the level of definitions, assumptions, "
                "witnesses, data route, comparator, or falsifier. The release is intentionally bounded so that such attacks "
                "do not have to fight rhetoric before reaching the scientific claim."
            )
        )
    body.extend(
        [
            r"\subsection{How the pieces form one bounded model-core release}",
            _tex_paragraph(
                "The tuple vocabulary defines what kind of object is under discussion. The lifecycle and boundary vocabulary "
                "define how such objects can continue, fail, leave residue, or be compared. The K-level vocabulary defines "
                "how additional organizational distinctions become reviewable. The operator vocabulary defines what kinds "
                "of transformations preserve or change the object. The proof and finite layers define which statements "
                "are formally or executably supported. The empirical layer tests selected operational projections. The "
                "prior-art and reviewer layers prevent the release from claiming more than those supports allow."
            ),
            _tex_paragraph(
                "This is the bounded scientific meaning of OC Core 1.3.3. It is ambitious because it connects formal, "
                "computational, empirical, comparative, and adversarial surfaces in one model core. It is bounded because "
                "each public claim has a visible support ceiling. Future work may expand the empirical lanes and comparator "
                "program, but the current release remains responsible only for the evidence it actually carries."
            ),
            r"\subsection{Reader route through the scientific claim}",
            _tex_paragraph(
                "A reader who wants the shortest scientific route should first understand the typed continuum object, then "
                "inspect liveness, residue, boundary, and K-level movement, then read the theorem/proof route, then check "
                "the finite semantic witnesses, then inspect the bounded numeric replay rows, then compare the prior-art "
                "positioning, and finally read the adversarial objections. This order follows the dependency structure of "
                "the theory rather than the file structure of the archive."
            ),
            _tex_paragraph(
                "A reader who wants to attack the work can follow the same route in reverse. Start with the strongest public "
                "claim, ask what artifact supports it, inspect whether the artifact has the promised assumptions and scope, "
                "then test whether the cited evidence actually supports the exact wording. If the wording is stronger than "
                "the evidence, the claim must be demoted or repaired. That is the intended public review contract."
            ),
        ]
    )
    component_notes = [
        ("Carrier", "The carrier is the typed background of possible distinctions. It is not yet the live object; it is the space in which realization can occur. A reviewer can therefore ask whether the carrier has been declared precisely enough for the later boundary and morphism claims."),
        ("Realization", "A realization selects the structure that is active inside the carrier. The release distinguishes realization from possibility so that a merely possible distinction is not accidentally counted as an active continuum feature."),
        ("Liveness", "Liveness is the admissibility condition for a currently realized continuum. It binds the model to conditions that can fail, which makes death, collapse, or demotion meaningful rather than rhetorical."),
        ("Residue", "Residue records what remains when liveness fails. It is central for lifecycle claims because identity and rebirth cannot be reviewed unless the prior state leaves typed evidence that can be compared."),
        ("Boundary", "Boundary vocabulary determines where the object can be separated, classified, measured, or reopened. The release treats metric thresholds as one case among several, not as the whole boundary theory."),
        ("Morphism", "Morphism vocabulary states which transformations preserve the relevant structure. It is the place where identity, translation, and reduction claims become attackable."),
        ("Operator", "Operator vocabulary describes how continua change. A smooth flow, discrete update, guard/reset jump, and cycle transformation do not carry the same regularity assumptions, so the public text keeps them separated."),
        ("Cycle mode", "Cycle modes describe recurrence, oscillation, renewal, or failure patterns. They help connect formal lifecycle statements to concrete examples without turning every repeated event into the same kind of cycle."),
        ("Dimension", "Dimension is treated as historical and effective structure, not only as a coordinate count. The reviewer question is what distinction a dimension preserves and what would happen if that distinction were collapsed."),
        ("K-level", "K-level language classifies structural organization. The release does not ask the reader to believe in a ladder by name; it asks the reader to inspect the witness, reduction attempt, and demotion boundary."),
        ("Proof sheet", "A proof sheet is the human-readable route from statement to assumptions and boundary. It prevents theorem IDs from becoming decorative labels."),
        ("Lean subset", "The Lean subset checks selected declarations and relationships. It is intentionally scoped and should be read as a machine-checked anchor, not as a claim that all prose is mechanized."),
        ("Finite witness", "A finite witness supplies a small executable case where the semantic verdict changes when a required component is altered. It is useful because it can fail independently of wording."),
        ("Target-blind row", "A target-blind row tests a bounded reconstruction under pinned input and hidden or held-out target conditions. Its authority stops at the declared row and does not become a domain-wide law."),
        ("Comparator row", "A comparator row states what another tradition already contributes and where the OC package claims a narrower residual difference. It is not a priority certificate."),
        ("Phenomenon card", "A phenomenon card binds phenomenon, formal instance, observable, comparator, negative control, falsifier, and status. Without that binding, the phenomenon remains illustrative."),
        ("Reviewer challenge", "A reviewer challenge is a pressure test on a public claim. The correct response is not a status token but a citation to the exact evidence that carries the claim."),
        ("Release citation", "A release citation identifies the exact public artifact set. It must not be confused with the continuing research program or later journal submissions."),
    ]
    body.append(r"\subsection{Component-by-Component Scientific Reading Map}")
    body.append(
        _tex_paragraph(
            "The following reading map expands the bounded synthesis into concrete component interpretation. It is included "
            "as scientific guidance for reviewers who want to know how each OC term functions in the argument."
        )
    )
    for label, note in component_notes:
        body.append(rf"\subsubsection{{{_tex_escape(label)}}}")
        body.append(_tex_paragraph(note))
        body.append(
            _tex_paragraph(
                "The local falsifier is structural: if the component does not change any claim boundary, witness, "
                "observable, or reviewer route, then the component is not doing scientific work at the release surface. "
                "If it does change one of those items, the public text must show where."
            )
        )
    domain_notes = [
        ("Mathematics", "The mathematics lane is anchored in finite semantic cases and proof dependencies. Its current role is to test whether the declared structures behave as stated under small executable models."),
        ("Physics", "The physics lane is treated as bounded reconstruction and protocol design. It can demonstrate how constants or spectral families are represented under declared formulas, but it does not replace established physical theory."),
        ("Chemistry", "The chemistry lane is bounded to pinned reconstruction examples and protocol-ready extensions. Molecular-weight or table checks are smoke tests unless a stronger held-out chemical benchmark is separately promoted."),
        ("Biology", "The biology lane is bounded to data-route discipline. Pagination or dataset-access checks prove archive handling, not biological mechanism; biological claims require their own observable, comparator, negative control, and falsifier."),
        ("Systems", "The systems lane is bounded to macro-series replay and protocol design. A simple trend extrapolation is not a civilization law; it is a test of whether the release can bind a public data route and residual interpretation."),
        ("Cross-domain comparison", "The cross-domain claim is a coordination claim about shared model vocabulary and evidence discipline, not a proof that one formula outperforms every local scientific model."),
        ("Journal preparation", "Journal preparation materials are editorial scaffolding for later submission decisions. They do not expand the scientific claim surface and should be read only after the model-core evidence is understood."),
        ("Future science program", "The future science program may pursue fuller domain projection and stronger comparator claims. In this release those ambitions remain explicitly separate from promoted claims."),
    ]
    body.append(r"\subsection{Domain-by-Domain Evidence Reading Map}")
    body.append(
        _tex_paragraph(
            "The domain reading map prevents a common overread: seeing several domain names and assuming complete domain "
            "validation. The current release uses domain lanes to demonstrate bounded operationalization, replay discipline, "
            "and claim-boundary handling."
        )
    )
    for label, note in domain_notes:
        body.append(rf"\subsubsection{{{_tex_escape(label)}}}")
        body.append(_tex_paragraph(note))
        body.append(
            _tex_paragraph(
                "The reviewer should therefore ask whether the local evidence supports the local wording. If the public "
                "wording implies domain completion, superiority, or law discovery beyond the local evidence, the wording "
                "must be demoted before publication."
            )
        )
    body.extend(
        [
            r"\subsection{Limits of the Current Empirical Surface}",
            _tex_paragraph(
                "The current empirical surface is intentionally conservative. It proves that the release can bind claims "
                "to pinned data routes, formulas, residuals, comparators, negative controls, falsifiers, and replay hashes. "
                "It does not prove that OC already dominates the best local theories in every domain. The correct reading "
                "is therefore operational: the model core has been made testable, and selected lanes show how reviewable "
                "testing is represented, but broader predictive campaigns remain future work."
            ),
            _tex_paragraph(
                "This conservative interpretation is scientifically important. If a replay row is administrative, it is "
                "evidence for reproducibility handling rather than for domain mechanism. If a row reconstructs a known "
                "constant or table value, it is evidence that the formula and snapshot route are bound correctly rather "
                "than evidence of a new physical or chemical law. If a systems row uses simple extrapolation, it is a "
                "benchmarking scaffold rather than a civilization forecast. The public wording must preserve those "
                "distinctions."
            ),
            r"\subsection{How Future Evidence Would Strengthen the Release Surface}",
            _tex_paragraph(
                "A future empirical strengthening release would need preregistered or target-hidden domain tasks, stronger "
                "same-claim baselines, uncertainty envelopes, negative controls chosen before evaluation, independent "
                "data snapshots, failure publication, and residual interpretation tied to explicit OC model claims. Only "
                "then could broader predictive-power wording be considered."
            ),
            _tex_paragraph(
                "A future comparator strengthening release would need systematic literature search, explicit inclusion and "
                "exclusion criteria, same-claim alternatives, feature-by-feature overlap, residual delta, and independent "
                "review of non-novelty boundaries. Only then could stronger novelty or superiority language move from "
                "research ambition into public claim surface."
            ),
            _tex_paragraph(
                "The present monograph records these future pathways because they protect the current release from both "
                "underclaiming and overclaiming. The theory remains ambitious, but the release surface remains tied to "
                "evidence that is actually present."
            ),
            _tex_paragraph(
                "This distinction also protects reviewers. A reviewer does not have to accept OC as a completed universal "
                "science in order to evaluate OC Core 1.3.3. The immediate review question is narrower and stronger: does "
                "the typed model core, with its proof sheets, Lean subset, finite witnesses, bounded replay rows, comparator "
                "positioning, and adversarial boundaries, form a coherent scientific artifact whose claims match its evidence? "
                "That question can be answered from the present release."
            ),
            _tex_paragraph(
                "If the answer is negative, the release gives routes for repair. A failed formal route sends the claim back "
                "to definitions and proof sheets. A failed finite witness sends it back to semantic fixtures and negative "
                "controls. A failed replay row sends it back to formula, snapshot, comparator, residual, and falsifier. A "
                "failed novelty claim sends it back to prior-art comparison. A failed phenomenon claim sends it back to the "
                "model card. In each case, the scientific repair target is local and inspectable."
            ),
            _tex_paragraph(
                "If the answer is positive, the result is still bounded. The release establishes a model-core baseline "
                "for external scientific review, not a terminus for all future work. That baseline is valuable precisely "
                "because it makes the next research steps sharper: stronger mechanized proofs, richer finite counterexample "
                "search, deeper domain predictions, fuller literature comparison, and more demanding reviewer objections "
                "can all be added without changing what the current artifact honestly claims."
            ),
            _tex_paragraph(
                "This final interpretive distinction is the reason the monograph separates ambition from promotion. The "
                "ambition remains large: a typed cross-domain model core whose claims can be reviewed, repaired, and "
                "expanded. The promotion remains evidence-bound: only the claims supported by the present proof, finite, "
                "replay, comparator, and reviewer artifacts enter the public release surface."
            ),
            r"\subsection{Scientific Status at the End of the 1.3.3 Argument}",
            _tex_paragraph(
                "At the end of the 1.3.3 argument, the reader should not be left with a vague impression of a universal "
                "framework. The reader should have a precise status map. The formal object is typed and bounded. The theorem "
                "surface is supported by proof sheets and a selected mechanized subset. The finite cases make component "
                "dependencies executable. The numeric rows are bounded replay demonstrations. The comparator material is "
                "positioning evidence. The phenomenon cards are coverage routes. The reviewer material is an attack map."
            ),
            _tex_paragraph(
                "Those statuses differ in authority. A proof sheet may support a theorem under assumptions. A Lean declaration "
                "may support a formal subset. A finite witness may support an executable semantic separation. A numeric row may "
                "support a reconstruction claim. A comparator paragraph may support a positioning statement. None of those "
                "automatically upgrades into a full-domain law, a universal predictor, or a global superiority result."
            ),
            _tex_paragraph(
                "The scientific gain of the release is that those levels are now visible in one manuscript. Instead of asking "
                "the reader to infer the difference between proof, replay, comparison, and aspiration, the monograph marks "
                "the difference and gives the reviewer a route to challenge it. That is the publication-grade form of the "
                "current OC Core contribution."
            ),
            r"\subsection{Claim-Level Consequences and Falsification Routes}",
            _tex_paragraph(
                "The 1.3.3 contribution is easiest to review when each major theorem label is read as a constrained scientific "
                "operation rather than as a slogan. T133-K0-RES says that collapse to zero continuumness is not a single "
                "metaphorical failure event: the reviewer must inspect which declared component failed, whether the failure "
                "is observable in the model, and whether a repair would restore the verdict. The claim fails if a row can "
                "declare zero continuumness without a typed cause, or if the supposed cause does not change any live verdict."
            ),
            _tex_paragraph(
                "T133-OMEGA-STATUS gives the lifecycle grammar. A live realization, a dead realization, a residue, and a "
                "later realization are different statuses unless the identity-preservation conditions say otherwise. The "
                "scientific consequence is not a metaphysical theory of survival; it is a typed prohibition against smuggling "
                "identity through residue or rebirth language. The falsifier is direct: if a public example treats residue as "
                "continued identity without invariant evidence, the example is outside the promoted theorem boundary."
            ),
            _tex_paragraph(
                "T133-HYBRID separates smooth flow, discrete update, guard/reset transition, and proof rewrite. This matters "
                "because many cross-domain theories use dynamics language while quietly moving between incompatible regularity "
                "assumptions. OC 1.3.3 requires the local transition law to state what kind of operator is being used. A "
                "hybrid claim fails if it imports derivative language into a discrete update without the smooth structure that "
                "would justify that derivative."
            ),
            _tex_paragraph(
                "T133-MIN is read as component witness independence for the declared semantic verdict suite, not as a global "
                "claim that no simpler theory could ever exist. For each component the release asks whether removing that "
                "component changes an executable or proof-relevant verdict. The falsifier is therefore local and severe: if "
                "a component can be dropped without changing any declared witness, reviewer route, or claim boundary, the "
                "minimality row must be repaired or demoted."
            ),
            _tex_paragraph(
                "T133-KLEVEL makes K-level talk reviewable. An adjacent level is not justified by a label or by increasing "
                "complexity language; it is justified only by an added observable, a retained witness, a reduction-failure "
                "case, or a lawful demotion rule. The scientific consequence is a disciplined hierarchy: upward movement must "
                "earn its distinction, and downward movement is allowed when the added observable is inert. A K-level claim "
                "fails if the proposed distinction can be projected away while all retained verdicts stay unchanged."
            ),
            _tex_paragraph(
                "T133-BOUNDARY, T133-CYCLE, T133-DIM, and T133-ID cover the most common reviewer pressure points. Boundary "
                "claims fail if a threshold is asserted without measurement semantics or classifier authority. Cycle claims "
                "fail if recurrence is named without support conditions. Dimension claims fail if a dimension is only a "
                "coordinate count and does not preserve a historical or effective distinction. Identity claims fail if the "
                "morphism does not preserve the declared invariants. Together these routes make the vocabulary criticizable "
                "rather than merely evocative."
            ),
            _tex_paragraph(
                "The empirical rows inherit the same discipline. A physics, chemistry, biology, systems, or mathematics lane "
                "does not become a domain theorem by appearing in the release. It becomes support for a bounded row only when "
                "the formula, input snapshot, split policy, comparator, residual, negative control, falsifier, and replay hash "
                "match the public wording. If the row is an archive-access test, it supports archive handling. If it is a "
                "known-constant reconstruction, it supports reconstruction discipline. If it is a benchmark scaffold, it "
                "supports benchmark routing. It does not silently become full domain validation."
            ),
            _tex_paragraph(
                "The prior-art rows also carry a falsification route. A tradition such as systems theory, autopoiesis, "
                "dynamical systems, category theory, RAF theory, complexity measurement, identity theory, or systems "
                "engineering may already contain part of the vocabulary or the phenomenon. OC 1.3.3 is therefore obligated "
                "to state overlap first and residual delta second. A novelty claim fails if it depends on absence of prior art "
                "that has not been systematically searched, or if it names an old concept with new terminology and no residual "
                "model-core work."
            ),
            _tex_paragraph(
                "These claim-level consequences are included to make the monograph harder to misuse. They tell a friendly "
                "reader what has been achieved and tell a hostile reader exactly where to press. A publication-grade release "
                "does not hide that pressure. It makes every promoted claim carry its own assumptions, evidence route, "
                "boundary, and failure condition."
            ),
        ]
    )
    return "\n".join(body)


def _generate_integrated_science_tex(
    root: Path,
    source_dir: Path,
    *,
    doi: str | None,
    zenodo_record_url: str | None,
) -> dict[str, Any]:
    claims = read_json(root / "claims/CLAIM_LEDGER_1_3_3.json", {})
    theorems = read_json(root / "proofs/THEOREM_REGISTRY_1_3_3.json", {})
    finite = read_json(root / "proofs/FINITE_MODEL_CHECKS_1_3_3.json", {})
    target = read_json(root / "validation/target_blind/OC133_TARGET_BLIND_PREDICTION_TABLE.json", {})
    validation = read_json(root / "reports/OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.json", {})
    novelty = read_json(root / "comparators/OC_1_3_3_NOVELTY_AND_PRIORITY_REGISTER.json", {})
    coverage = read_json(root / "docs/OC_1_3_3_PHENOMENON_COVERAGE_MATRIX.json", {})
    attack = read_json(root / "review/OC_1_3_3_TOTAL_ATTACK_MATRIX.json", {})
    cerberus = read_json(root / "reviews/oc133_llm_cerberus/OC133_LLM_CERBERUS_SUMMARY.json", {})
    packages = read_json(root / "releases/oc_core_1_3_3/submission_packages/SUBMISSION_PACKAGE_INDEX.json", {})
    lean_cert = read_json(root / "formal/lean/LEAN_BUILD_CERTIFICATE_1_3_3.json", {})
    source_refs = [
        "claims/CLAIM_LEDGER_1_3_3.json",
        "proofs/THEOREM_REGISTRY_1_3_3.json",
        "proofs/FINITE_MODEL_CHECKS_1_3_3.json",
        "formal/lean/OC133V12.lean",
        "formal/lean/LEAN_BUILD_CERTIFICATE_1_3_3.json",
        "validation/target_blind/OC133_TARGET_BLIND_PREDICTION_TABLE.json",
        "validation/numeric_replay_qa/OC133_NUMERIC_REPLAY_QA_TABLE.json",
        "reports/OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.json",
        "reports/OC_CORE_1_3_3_COUNTEREXAMPLE_REPORT.json",
        "comparators/OC_1_3_3_NOVELTY_AND_PRIORITY_REGISTER.json",
        "reviews/oc133_llm_cerberus/OC133_LLM_CERBERUS_SUMMARY.json",
        "releases/oc_core_1_3_3/submission_packages/SUBMISSION_PACKAGE_INDEX.json",
    ]
    front = [
        r"\section{Typed Model Foundation and Claim Boundary}",
        r"\label{sec:oc133-integrated-scientific-closure}",
        _tex_paragraph(
            "This chapter states the model-core boundary inside the monograph's main scientific argument. "
            "It introduces the typed foundation, proof obligations, finite-check semantics, replay QA rows, comparator "
            "claims, and review boundaries as scientific material: definitions first, obligations second, evidence third, "
            "and limits fourth."
        ),
        _tex_paragraph(
            f"The public release identifier is OC Core {VERSION}. "
            f"The release DOI is {doi or 'assigned by Zenodo during the corrected publication pass'}, and the "
            f"Zenodo record is {zenodo_record_url or 'assigned by the corrected publication pass'}. "
            "The release is prepared for public archival correction on GitHub and Zenodo; journal submissions remain a "
            "separate later editorial action."
        ),
        r"\subsection{Reader Contract for the 1.3.3 Model-Core Chapters}",
        _tex_paragraph(
            "The reader should treat the 1.3.3 chapters as the public scientific route through the "
            "proof, finite-model, validation, comparator, and review corpus. The release promotes bounded model-core claims "
            "where the artifacts contain explicit evidence. It does not promote final all-domain completion or unbounded "
            "cross-science comparison claims; those obligations remain in the background science program until they "
            "are literally evidenced."
        ),
        r"\subsection{How Evidence Enters the Model}",
        _tex_paragraph(
            "The scientific text binds research artifacts, proof registers, Lean and finite evidence, replay QA tables, "
            "novelty/comparator rows, and review closures to readable sections. A claim is introduced in prose before "
            "the reader is asked to inspect a theorem identifier, replay row, or machine-readable evidence file."
        ),
        r"\begin{itemize}[leftmargin=1.8em]",
                _tex_item("Manuscript-quality rule", "internal routing memos, raw registers, glued appendices, page-number resets, absent front matter, and absent dedication create scientific reopening conditions"),
        _tex_item("Corpus coverage gate", "every promoted 1.3.3 science surface is included, cited, or excluded with reason"),
        _tex_item("Evidence coverage gate", "major theorem, evidence, review, and journal anchors must appear in the manuscript as readable science before machine evidence is consulted"),
        _tex_item("Editorial adversarial-review gate", "editorial reviewers must return zero critical/high findings before publication replacement"),
        r"\end{itemize}",
        r"\subsection{Scientific Support Obligations}",
        _tex_paragraph(
            "The 1.3.3 publication standard is deliberately positive. A public scientific document does not pass merely "
            "because it avoids forbidden words, stale metadata, or route-sheet fragments. It must also perform its role. "
            "For every major claim the manuscript has to say what is being claimed, why the claim matters, which formal "
            "or empirical evidence supports it, how that evidence relates to prior art and the current scientific picture, "
            "what simulation, finite semantic, or replay route can check it, and what boundary or falsifier would reopen it."
        ),
        _tex_paragraph(
            "This positive obligation is stricter than a normal release checklist. The manuscript must show that the "
            "current science has actually been integrated into the public text: typed foundation, theorem/proof route, "
            "Lean subset, finite semantic checks, target-blind numeric rows, negative controls, falsifiers, prior-art "
            "comparison, phenomenon coverage, adversarial review, reproducibility, and journal owner-review preparation. "
            "If any of those surfaces exists only as a hidden file or a raw register with no reader-facing explanation, "
            "the manuscript has not fulfilled its scientific task."
        ),
        _tex_paragraph(
            "The current-science SPOT therefore has two jobs. First, it records the internal maturity vector: model "
            "foundation, formal evidence, empirical evidence, prior-art alignment, corpus completeness, process visibility, "
            "and editorial review state. Second, it constrains external speech. Public wording must derive from the actual "
            "research state rather than from ambition, marketing pressure, or local process vocabulary. The reader sees "
            "the scientific result; the machine keeps the stronger internal proof that the result is supported, current, "
            "and bounded."
        ),
        _tex_paragraph(
            "This section is included so future OC and non-OC releases cannot repeat the failure pattern that produced "
            "a public archive record from metadata, process fragments, or an appended delta. The standard is now part of "
            "the manuscript machinery: manuscript integration, editorial review, package construction, public metadata, "
            "and post-release verification must all preserve the same positive obligations."
        ),
        r"\subsection{Evidence Coverage Map}",
        _tex_paragraph(
            "For this release the evidence-inclusion rule is applied as a coverage map, not as a cosmetic checklist. Each "
            "public scientific surface has a required reader payoff and a required evidence payoff. The model chapter "
            "must teach typed carriers, realizations, liveness, death, residue, morphisms, boundaries, operators, cycle "
            "modes, dimension, and K-level semantics. The proof chapter must connect theorem names to assumptions, "
            "definitions, proof sheets, Lean declarations, finite witnesses, dependency references, and counterexample "
            "boundaries. The empirical chapter must distinguish target-blind replay QA and artifact-integrity examples "
            "from future full-domain validation."
        ),
        _tex_paragraph(
            "Prior-art and novelty discussion has its own positive obligations. It must identify overlap with existing "
            "traditions, name the residual delta that OC claims under declared assumptions, and refuse unsupported "
            "priority or total-superiority language. Phenomenon coverage has a parallel obligation: it must state what "
            "the model instance explains, what observable or replay route exists, which comparator is relevant, what "
            "negative control or falsifier can reopen the claim, and whether the phenomenon is promoted now or left as "
            "a research target."
        ),
        _tex_paragraph(
            "The reviewer chapter therefore cannot be a list of issues. It must show why a hostile objection is serious, "
            "which public claim it threatens, which evidence answers it, and what residual risk would reopen it. The "
            "methods chapter cannot be a list of commands; it must tell the reader which claim each command checks, "
            "which input it consumes, which output or hash it should produce, and what scientific interpretation follows "
            "from a mismatch. The journal package map cannot imply submission; it must show preparation readiness and "
            "the additional owner/editorial action required before an actual submission."
        ),
        r"\begin{itemize}[leftmargin=1.8em]",
        _tex_item("Model integration payoff", "the reader can reconstruct the tuple-to-boundary-to-operator route without opening a machine register"),
        _tex_item("Proof integration payoff", "the reader can move from a promoted theorem name to assumptions, proof sheet, Lean subset, finite witness, and boundary"),
        _tex_item("Empirical integration payoff", "the reader can see formula, snapshot, split, prediction, observation, uncertainty, residual, comparator, negative control, falsifier, and replay hash where empirical promotion is claimed"),
        _tex_item("Prior-art payoff", "the reader can distinguish overlap, residual delta, non-novelty boundary, and unsupported priority claim"),
        _tex_item("Phenomenon payoff", "the reader can tell what is explained, what is only protocol-ready, and what would falsify the explanation"),
        _tex_item("Editorial payoff", "the reader receives one coherent manuscript voice rather than an old volume plus appended control material"),
        _tex_item("Release payoff", "public metadata, DOI, archive files, and document surfaces describe the same bounded scientific object"),
        r"\end{itemize}",
        _tex_paragraph(
            "These payoffs are deliberately measurable. Missing anchors, absent title/front matter, absent dedication, "
            "stale version identity, weak literature synthesis, missing visual pedagogy, unsupported public claims, "
            "over-repeated boilerplate, register-dominated prose, non-current review results, and package/public metadata "
                    "mismatch are all scientific reopening conditions. The public artifact must be pleasant enough to read and strict "
            "enough to audit; either failure is a scientific publication failure."
        ),
    ]
    proof_rows = theorems.get("rows", []) if isinstance(theorems.get("rows"), list) else []
    claim_rows = claims.get("rows", []) if isinstance(claims.get("rows"), list) else []
    finite_rows = finite.get("rows", []) if isinstance(finite.get("rows"), list) else []
    empirical_rows = target.get("rows", []) if isinstance(target.get("rows"), list) else []
    novelty_rows = novelty.get("rows", []) if isinstance(novelty.get("rows"), list) else []
    coverage_rows = coverage.get("rows", []) if isinstance(coverage.get("rows"), list) else []
    attack_rows = attack.get("rows", []) if isinstance(attack.get("rows"), list) else []
    package_rows = packages.get("rows", []) if isinstance(packages.get("rows"), list) else []
    scientific_claim_rows = _public_scientific_claim_rows(claim_rows)
    bib_total = _bibliography_total(root)
    figure_total = _figure_total(root)

    main_sections = [
        "\n".join(front),
        "\n".join(
            [
                r"\section{Reader Contract and Scientific Route}",
                r"\label{sec:oc133-reader-contract-scientific-route}",
                _tex_paragraph(
                    "Audience. The primary audience is a mixed external-review group: formal-methods readers, "
                    "systems-theory readers, domain scientists, journal editors, and technically literate institutional "
                    "readers. The monograph therefore cannot assume that every reader begins with the same mathematical "
                    "or domain background."
                ),
                _tex_paragraph(
                    "Purpose. This manuscript explains what OC Core 1.3.3 claims, why the claims are bounded, how the "
                    "typed model is organized, where proof and executable evidence live, which empirical lanes are "
                    "replayable, and which broader full-science obligations remain future work. Because the artifact is "
                    "public science, intelligibility is a release requirement."
                ),
                _tex_paragraph(
                    "Construction. The recommended reader path is orientation, formal model, theorem/proof closure, Lean "
                    "and finite-model evidence, target-blind empirical rows, prior-art comparison, phenomenon coverage, "
                    "reviewer objections, reproducibility, and release governance. This order is deliberate: a reader "
                    "needs the model before the proof register and the proof register before judging replay artifacts."
                ),
                _tex_paragraph(
                    "Didactic rule. Every major section must answer four questions: what is being claimed, why it matters, "
                    "what evidence supports it, and what would falsify or limit it. If a section only lists identifiers, "
                    "hashes, or rows, the detailed material belongs in the evidence package or appendix rather than in "
                    "the main explanatory path."
                ),
            ]
        ),
        "\n".join(
            [
                r"\section{Literature and Prior-Art Position}",
                r"\label{sec:oc133-literature-prior-art-position}",
                _tex_paragraph(
                    f"The monograph carries {bib_total} bibliography entries and source-backed comparator anchors with overlap and residual-delta notes. The literature "
                    "layer locates OC against emergence, phase transitions, autopoiesis, dynamical systems, RAF chemistry, "
                    "information and complexity measures, identity over time, hybrid systems, formal methods, systems "
                    "engineering, and reproducibility practice. The release uses literature to bound novelty, not to claim "
                    "absence of all prior work."
                ),
                _tex_paragraph(
                    "A scientific reviewer should therefore read the comparator material as a map of overlap and residual "
                    "delta. Where OC integrates or rephrases an existing tradition, the monograph says so. Where a broader "
                    "priority or superiority claim is not evidenced, it stays outside the promoted release surface."
                ),
            ]
        ),
        "\n".join(
            [
                r"\section{Figure Route and Design Logic}",
                r"\label{sec:oc133-figure-route-design-logic}",
                _tex_paragraph(
                    f"The full corpus includes {figure_total} public figure entries across the theorem roadmap, worked examples, and figure atlas. The figure layer teaches tuple structure, "
                    "thresholds, K-level transitions, lifecycle, boundaries, domain examples, and theory/reproducibility "
                    "movement. Figures are explanatory anchors, not decoration; they are staged so that the main proof path "
                    "remains readable while visual readers can still follow the structural grammar."
                ),
                _tex_paragraph(
                    "The design rule for 1.3.3 is simple: every public document must begin with a title page, dedication, "
                    "version, DOI, abstract or reader contract, and table of contents, and every long register must either "
                    "be explained in prose or moved to an appendix or evidence bundle."
                ),
            ]
        ),
        "\n".join(
            [
                r"\section{Integrated 1.3.3 Scientific Argument Before Evidence Rows}",
                r"\label{sec:oc133-integrated-argument-before-evidence-rows}",
                _tex_paragraph(
                    "Before the monograph names individual evidence rows, it states the integrated argument in ordinary "
                    "scientific prose. OC Core 1.3.3 promotes a bounded model-core claim: a continuum is treated as a "
                    "typed object whose carrier, realization, lawful possibility, liveness, residue, boundary behavior, "
                    "operator behavior, cycle mode, dimension semantics, and K-level position can be inspected under "
                    "declared assumptions. The release does not ask the reader to trust an inventory. It asks the reader "
                    "to test whether those typed components solve specific ambiguity classes that appear when persistence, "
                    "death, rebirth, boundary, update, and cross-level reduction are discussed without a common grammar."
                ),
                _tex_paragraph(
                    "The proof layer then gives the argument its ceiling. The promoted theorem surface is not a claim "
                    "that OC has completed every possible domain science. It is a claim that named theorem statements have "
                    "named assumptions, proof sheets, Lean-subset references where available, finite semantic witnesses, "
                    "negative controls, and counterexample boundaries. A theorem identifier is therefore a citation handle, "
                    "not the argument itself: the argument is the chain from definition to lemma to proof sheet to finite "
                    "witness to explicit reopening condition."
                ),
                _tex_paragraph(
                    "The empirical layer has the same discipline. Physics, chemistry, biology, systems, and mathematics "
                    "rows are target-blind or replay-QA examples with formulas, snapshots, comparators, residuals, negative "
                    "controls, falsifiers, and hashes. They show how the OC release binds a claim to a replayable evidence "
                    "route. They do not promote all-domain numerical closure, final TOE status, or superiority over modern "
                    "science. Those broader ambitions remain a background research program until they can be supported at "
                    "the same or higher evidential standard."
                ),
                _tex_paragraph(
                    "The comparator layer prevents novelty theater. General systems theory, autopoiesis, dynamical systems, "
                    "category and topos formalisms, RAF theory, complexity and information measures, identity theory, "
                    "systems engineering, and reproducible-research practice are treated as live comparators. For each "
                    "tradition, the release first records overlap, then states the residual delta, and finally names the "
                    "claim that OC must not make. This order is essential: accepted overlap comes before residual contribution."
                ),
                _tex_paragraph(
                    "The row-based sections that follow are therefore not a substitute for the monograph. They are an audit "
                    "trail. A reader who wants the conceptual argument should read the prose spine first; a reviewer who "
                    "wants to attack exact wording can then use the rows to locate the proof sheet, finite case, replay row, "
                    "comparator source, or reopening rule that carries the challenged sentence."
                ),
            ]
        ),
        _integrated_claim_argument_sections(claim_rows, proof_rows),
        _scientific_reading_protocol_section(),
        _bounded_replay_argument_section(),
        _section_from_rows(
        "Promoted Model-Core Claims in Prose",
            "The claim register is translated into prose so that a reader can see what is promoted, what is bounded, and what remains research. The register is not allowed to promote unsupported total finality.",
            scientific_claim_rows,
            ["claim", "support", "evidence_ref", "scope_limit"],
            limit=18,
        ),
        _section_from_rows(
            "Theorem and Proof Integration",
            "The theorem registry is the bridge from named claims to proof sheets, Lean declarations, finite witnesses, and scope boundaries. A theorem row without this bridge is not a promoted theorem.",
            proof_rows,
            ["title", "public_claim_boundary", "proof_sheet_ref", "lean_ref", "evidence_ref", "scope_limit"],
            limit=18,
        ),
        _section_from_rows(
            "Lean and Finite-Model Evidence",
            "The Lean subset and finite-model runner are treated as executable evidence for bounded theorem surfaces. They do not replace the prose proof sheets; they anchor selected semantic obligations and mutation controls.",
            finite_rows,
            ["case_type", "observed_verdict", "expected_verdict", "failure_total", "witness", "witness_id"],
            limit=28,
        ),
        _section_from_rows(
            "Bounded Replay QA and Artifact-Integrity Examples",
            "The empirical rows support bounded replay QA by binding formula, snapshot, comparator, residual, negative control, falsifier, and replay hash. They are not advertised as complete domain validation, independent domain proof, or cross-domain superiority.",
            empirical_rows,
            ["lane", "claim_id", "formula", "predicted_value", "observed_value", "uncertainty", "residual", "comparator_baseline", "negative_control", "falsifier", "replay_hash"],
            limit=12,
        ),
        _section_from_rows(
            "Novelty, Comparator, and Phenomenon Coverage",
            "Comparator and phenomenon rows are included as bounded positioning and coverage evidence. They prevent the release from pretending that novelty or explanation coverage is stronger than the artifact layer supports.",
            [*novelty_rows[:12], *coverage_rows[:18]],
            ["tradition", "comparator_id", "overlap", "residual_delta", "uniqueness_claim_status", "phenomenon_id", "domain", "status", "claim_boundary", "falsifier"],
            limit=30,
        ),
        "\n\n".join([_reviewer_and_journal_summary(attack_rows, package_rows), _bounded_scientific_synthesis_sections()]),
    ]
    evidence_names = [Path(ref).name for ref in source_refs]
    appendix = [
        r"\section{OC Core 1.3.3 Evidence Map}",
        r"\label{app:oc133-source-to-pdf-trace}",
        _tex_paragraph(
            "This appendix is a reader-facing evidence map. It deliberately does not reproduce the raw provenance "
            "registers, source-path digests, or machine rows inside the monograph. Those complete registers remain in "
            "the public evidence package, where they can be checked by hash. The monograph records what each evidence "
            "class does for the scientific argument and how a reader should use it."
        ),
        r"\subsection{Public Evidence Package Contents}",
        _tex_paragraph(
            "The public evidence package contains the claim register, theorem registry, proof dependency graph, finite-model "
            "semantic checks, Lean source and certificate, target-blind prediction table, numeric replay QA table, domain "
            "evidence-boundary report, counterexample report, comparator and novelty registers, adversarial-review summary, "
            "and journal owner-review package index. The canonical filenames include: "
            + ", ".join(_tex_escape(name) for name in evidence_names)
            + "."
        ),
        _tex_paragraph(
            "For exact SHA-256 values and source paths, use the corpus ledger and checksums files distributed in the release "
            "zip. Keeping those details in machine-readable artifacts avoids turning the scientific monograph into a raw "
            "hash catalogue while preserving reproducibility."
        ),
        r"\subsection{Verification Summary}",
        r"\begin{itemize}[leftmargin=1.8em]",
        _tex_item("Lean formal subset", f"certificate recorded with {lean_cert.get('theorem_ref_total')} theorem references"),
        _tex_item("Finite semantic evidence", f"{finite.get('case_total') or len(finite_rows)} cases with issue count {finite.get('failure_total')}"),
        _tex_item("Bounded replay lanes", f"{target.get('lane_total') or len(empirical_rows)} lanes with issue count {target.get('failure_total')}"),
        _tex_item("Empirical promotion policy", validation.get("empirical_promotion_policy")),
        _tex_item("Adversarial review", f"open critical/high findings are recorded as {cerberus.get('critical_open_total')}/{cerberus.get('high_open_total')} for the referenced review run"),
        _tex_item("Journal owner-review packets", packages.get("package_total")),
        r"\end{itemize}",
        r"\subsection{Publication-Grade Closure Rule}",
        _tex_paragraph(
            "A future release must fail if a primary scientific role is filled by an internal process memo, raw metadata wall, "
            "append-only surrogate, or verification package. The public manuscript must be a coherent text. "
            "Long registers may be cited and archived, but the public PDFs must teach the reader how claims, proofs, "
            "data, review, and release boundaries fit together."
        ),
    ]
    appendix_tex = "\n\n".join(appendix)
    segmented_sections = {
        INTEGRATED_MODEL_REF: main_sections[0:5],
        INTEGRATED_PROOF_REF: main_sections[5:7],
        INTEGRATED_EVIDENCE_REF: main_sections[7:9],
        INTEGRATED_REVIEW_REF: main_sections[9:10],
    }
    segment_hashes: dict[str, str] = {}
    for ref, sections in segmented_sections.items():
        path = source_dir / ref
        write_text_if_changed(path, "\n\n".join(sections))
        segment_hashes[ref.as_posix()] = sha256_file(path)
    appendix_path = source_dir / INTEGRATED_APPENDIX_REF
    write_text_if_changed(appendix_path, appendix_tex)
    return {
        "integrated_content_refs": [ref.as_posix() for ref in INTEGRATED_CONTENT_REFS],
        "integrated_appendix_ref": INTEGRATED_APPENDIX_REF.as_posix(),
        "integrated_content_sha256": segment_hashes,
        "integrated_appendix_sha256": sha256_file(appendix_path),
        "claim_rows_projected": len(scientific_claim_rows),
        "theorem_rows_projected": len(proof_rows),
        "finite_rows_projected": len(finite_rows),
        "empirical_rows_projected": len(empirical_rows),
        "attack_rows_projected": len(attack_rows),
    }


def _rewrite_entrypoint_for_integrated_133(source_dir: Path) -> dict[str, Any]:
    entry = source_dir / BASE_ENTRYPOINT
    before = read_text(entry)
    auto_core = source_dir / "content" / "_auto_core_inputs.tex"
    auto_core_before = read_text(auto_core)
    integrated_auto_core = source_dir / INTEGRATED_AUTO_CORE_REF

    def _insert_after_once(text: str, anchor: str, insertion: str) -> str:
        if insertion in text:
            return text
        if anchor not in text:
            return text.rstrip() + "\n" + insertion + "\n"
        return text.replace(anchor, anchor + "\n" + insertion, 1)

    integrated_auto_core_text = auto_core_before
    integrated_auto_core_text = _insert_after_once(
        integrated_auto_core_text,
        r"\input{content/02_background.tex}",
        rf"\input{{{INTEGRATED_MODEL_REF.as_posix()}}}",
    )
    integrated_auto_core_text = _insert_after_once(
        integrated_auto_core_text,
        r"\input{content/theorems_master.tex}",
        rf"\input{{{INTEGRATED_PROOF_REF.as_posix()}}}",
    )
    integrated_auto_core_text = _insert_after_once(
        integrated_auto_core_text,
        r"\input{content/predictions/predictions_master.tex}",
        rf"\input{{{INTEGRATED_EVIDENCE_REF.as_posix()}}}",
    )
    integrated_auto_core_text = _insert_after_once(
        integrated_auto_core_text,
        r"\input{content/toe/toe_master.tex}",
        rf"\input{{{INTEGRATED_REVIEW_REF.as_posix()}}}",
    )
    # The complete generated corpus includes an early figure compendium while
    # the public monograph also carries a dedicated figure-atlas appendix and
    # supporting-publication figures. Keeping both copies in the master PDF
    # reads as duplicated atlas material rather than integrated manuscript
    # structure, so the generated 1.3.3 entrypoint preserves the scientific
    # text corpus and leaves the figure atlas in its dedicated appendix role.
    integrated_auto_core_text = integrated_auto_core_text.replace(r"\input{content/07_figures.tex}" + "\n", "")
    # The historical TOE/K synthesis generator is a machine-status surface. It
    # contains pass/fail and promotion fields that are useful evidence-package
    # data, but they must not masquerade as publication-grade monograph prose.
    # The public synthesis chapter below replaces it in the reading path, while
    # the raw rows remain available through the evidence package.
    integrated_auto_core_text = integrated_auto_core_text.replace(r"\input{content/toe/toe_master.tex}" + "\n", "")
    # Core 1.2 axiom/theorem packets are important provenance, but a current
    # 1.3.3 monograph must teach from the integrated 1.3.3 foundation/proof
    # spine. Keep the historical packets intact in a dedicated provenance
    # annex instead of letting them interrupt the main scientific argument.
    integrated_auto_core_text = integrated_auto_core_text.replace(r"\input{content/axioms_full.tex}" + "\n", "")
    integrated_auto_core_text = integrated_auto_core_text.replace(r"\input{content/theorems_master.tex}" + "\n", "")
    write_text_if_changed(integrated_auto_core, integrated_auto_core_text)

    historical_annex = rf"""\section{{Provenance Boundary Annex}}
\label{{app:historical-core-12-provenance-annex}}

This annex explains how older axiom and theorem packets are treated as source
provenance. They are not the promoted 1.3.3 theorem surface. The current
release-promoted theorem claims are stated in the integrated 1.3.3 proof spine,
the public theorem register, the Lean subset certificate, and the finite-model
witness reports. The older packets remain available through the evidence
package and corpus ledger so reviewers can audit lineage without mistaking
inherited source material for the current manuscript's primary argument.

The full source files are distributed in the public evidence package and corpus
ledger rather than reprinted here. This prevents the current monograph from
reading as an archive dump while still preserving the provenance route and
checksums needed for audit.
"""
    write_text_if_changed(source_dir / HISTORICAL_CORE12_ANNEX_REF, _public_clean(historical_annex))

    appendix_block = rf"""\appendix
\ocvolumeblock{{Scientific Evidence and Review Appendices}}{{The appendices preserve notation, axioms, K-level tables, provenance, journal extraction logic, reviewer objections, empirical replay surfaces, benchmark cases, proof machinery, figure material, technical derivations, synthesis support, and applied comparison material. They are secondary scientific annexes: the main body remains the teaching path, while this block prevents loss of corpus content and gives reviewers the evidence map needed to audit the release.}}
\input{{appendix/A_notation}}
\input{{appendix/B_axioms_full}}
\input{{appendix/C_klevels_tables}}
\input{{appendix/D_oc_core_1_3_source_audit_appendix}}
\input{{appendix/E_oc_core_1_3_journal_core_bridge}}
\input{{appendix/F_oc_core_1_3_reviewer_navigation_matrix}}
\input{{appendix/S_oc_core_1_3_external_criticism_closure}}
\input{{appendix/G_oc_core_1_3_empirical_validation_matrix}}
\input{{appendix/H_oc_core_1_3_institute_run_measurement_program}}
\input{{appendix/I_oc_core_1_3_domain_benchmark_manifest}}
\input{{appendix/L_oc_core_1_3_domain_benchmark_caseset}}
\input{{appendix/J_oc_core_1_3_domain_replay_reports}}
\input{{appendix/K_oc_core_1_3_domain_execution_board}}
\input{{appendix/M_oc_core_1_3_proof_machinery_appendix.tex}}
\input{{appendix/N_oc_core_1_3_figure_atlas.tex}}
\input{{appendix/O_oc_core_1_3_technical_derivation_atlas.tex}}
\input{{appendix/P_oc_core_1_3_reference_benchmark_atlas.tex}}
\input{{appendix/Q_oc_core_1_3_toe_support_dossiers.tex}}
\input{{{HISTORICAL_CORE12_ANNEX_REF.as_posix()}}}
\input{{appendix/R_oc_core_1_3_practical_utility_model_comparison_atlas.tex}}
"""
    text = rf"""\documentclass[11pt,a4paper]{{article}}

\input{{preamble}}
% PDF metadata source of truth: preamble.tex.
% Required metadata fields: pdftitle, pdfauthor, pdfsubject, pdfkeywords, pdflang.

\begin{{document}}

\input{{content/frontmatter_oc_core_1_3_master.tex}}
\tableofcontents
\clearpage
\phantomsection
\addcontentsline{{toc}}{{section}}{{List of Figures}}
\listoffigures
\clearpage
\phantomsection
\addcontentsline{{toc}}{{section}}{{List of Tables}}
\listoftables

\ocvolumeblock{{Reader Orientation}}{{The title page, abstract, table of contents, list of figures, list of tables, and reader guide orient the reader before the scientific argument begins.}}
\input{{content/17_oc_core_1_3_reader_guide.tex}}

\ocvolumeblock{{Complete Scientific Argument}}{{This block presents the current Core 1.3.3 scientific argument as the teaching path of the manuscript. The typed foundation, proof spine, evidence interpretation, and reviewer-boundary material are placed at the relevant conceptual points. Historical provenance, visual material, and source-trace records are summarized in scholarly annexes and distributed in the evidence package rather than interrupting the main argument.}}
\input{{{INTEGRATED_AUTO_CORE_REF.as_posix()}}}

\ocvolumeblock{{Scientific Closure and Use Boundaries}}{{After the full formal and domain corpus, this block keeps the scientific closure path: provenance and corpus boundaries, foundational consistency, theorem roadmap, worked examples, operationalization, empirical execution protocols, proof machinery, bounded synthesis, and practical use. These chapters are retained as part of the integrated manuscript rather than appended as a detached delta.}}
\input{{content/18_oc_core_1_3_source_audit.tex}}
\input{{content/19_oc_core_1_3_foundational_consistency.tex}}
\input{{content/20_oc_core_1_3_theorem_roadmap.tex}}
\input{{content/21_oc_core_1_3_worked_examples.tex}}
\input{{content/22_oc_core_1_3_operationalization_program.tex}}
\input{{content/23_oc_core_1_3_empirical_execution_protocols.tex}}
\input{{content/24_oc_core_1_3_proof_machinery.tex}}
\input{{content/25_oc_core_1_3_toe_synthesis.tex}}
\input{{content/26_oc_core_1_3_practical_utility.tex}}
\input{{content/99_oc_core_1_3_3_final_conclusion.tex}}

{appendix_block}

\clearpage
\nocite{{*}}
\printbibliography[heading=bibintoc,title={{Bibliography}}]

\end{{document}}
"""
    freeze_gate = _top_down_structure_freeze_gate(
        entrypoint_text=text,
        source_auto_core_text=auto_core_before,
        integrated_auto_core_text=integrated_auto_core_text,
    )
    applied = {ref.as_posix(): ref.as_posix() in integrated_auto_core_text for ref in INTEGRATED_CONTENT_REFS}
    write_text_if_changed(entry, text)
    return {
        "entrypoint": BASE_ENTRYPOINT,
        "integrated_auto_core_ref": INTEGRATED_AUTO_CORE_REF.as_posix(),
        "entrypoint_changed": before != text,
        "structure_policy": MONOLITH_STRUCTURE_POLICY,
        "top_down_structure_freeze_gate": freeze_gate,
        "full_auto_core_source_ref": "content/_auto_core_inputs.tex",
        "full_auto_core_line_total": len(auto_core_before.splitlines()),
        "integrated_auto_core_changed": read_text(integrated_auto_core) != auto_core_before,
        "integrated_content_in_entrypoint": applied,
        "all_integrated_content_in_entrypoint": all(applied.values()),
        "integrated_appendix_in_entrypoint": INTEGRATED_APPENDIX_REF.as_posix() in text,
        "full_auto_core_in_entrypoint": INTEGRATED_AUTO_CORE_REF.as_posix() in text,
    }


def _build_base_pdf(source_dir: Path) -> tuple[Path, list[dict[str, Any]]]:
    commands = []
    entrypoint = BASE_ENTRYPOINT
    commands.append(_run(["xelatex", "-interaction=nonstopmode", "-halt-on-error", entrypoint], source_dir, timeout=900))
    biber = _run(["biber", Path(entrypoint).stem], source_dir, timeout=240)
    commands.append(biber)
    commands.append(_run(["xelatex", "-interaction=nonstopmode", "-halt-on-error", entrypoint], source_dir, timeout=900))
    commands.append(_run(["xelatex", "-interaction=nonstopmode", "-halt-on-error", entrypoint], source_dir, timeout=900))
    pdf = source_dir / f"{Path(entrypoint).stem}.pdf"
    return pdf, commands


def _pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _artifact_row(root: Path, ref: str, role: str) -> dict[str, Any]:
    path = root / ref
    return {
        "ref": ref,
        "role": role,
        "exists": path.exists(),
        "sha256": sha256_file(path) if path.is_file() else None,
        "size_bytes": path.stat().st_size if path.is_file() else 0,
    }


def build_corpus_ledger(root: Path, *, output_pdf: Path | None = None) -> dict[str, Any]:
    base_files = sorted(path for path in (root / BASE_SOURCE_REF).rglob("*") if path.is_file() and path.suffix.lower() in {".tex", ".bib", ".md"})
    base_rows = [
        {
            "ref": rel(root, path),
            "role": "INCLUDED_BASELINE_FULL_MONOGRAPH_SOURCE",
            "exists": True,
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size,
        }
        for path in base_files
    ]
    mandatory_rows = [_artifact_row(root, ref, "INCLUDED_1_3_3_SCIENCE_SOURCE") for ref in MANDATORY_REFS]
    proof_rows = [
        _artifact_row(root, rel(root, path), "INCLUDED_1_3_3_PROOF_SHEET")
        for path in sorted((root / "proofs/proof_sheets").glob("T133-*.md"))
    ]
    missing = [row["ref"] for row in [*mandatory_rows, *proof_rows] if not row["exists"]]
    payload = {
        "schema_id": "OC133_SCIENCE_MONOLITH_CORPUS_LEDGER_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": "CONTENT_HASH_STABLE_NO_WALLCLOCK",
        "baseline_source_root": BASE_SOURCE_REF.as_posix(),
        "baseline_entrypoint": (BASE_SOURCE_REF / BASE_ENTRYPOINT).as_posix(),
        "public_payload_source": DELTA_SOURCE_REF.as_posix(),
        "manuscript_integration_service": "Logion/Research/ManuscriptIntegration",
        "scientific_editorial_service": "Logion/Editorial/ScientificEditorial",
        "assembly_policy": "SINGLE_INTEGRATED_TEX_BUILD_NO_PDF_MERGE",
        "output_pdf": rel(root, output_pdf) if output_pdf and output_pdf.exists() else str(ARTIFACTS_REF / MASTER_PDF_NAME),
        "baseline_source_total": len(base_rows),
        "mandatory_science_source_total": len(mandatory_rows),
        "proof_sheet_total": len(proof_rows),
        "missing_total": len(missing),
        "missing_refs": missing,
        "rows": [
            *base_rows,
            *mandatory_rows,
            *proof_rows,
            *[
                {
                    "ref": ref.as_posix(),
                    "role": "GENERATED_MAIN_TEXT_INTEGRATION",
                    "exists": True,
                    "source_space": "generated_in_build_tree",
                }
                for ref in INTEGRATED_CONTENT_REFS
            ],
            {
                "ref": INTEGRATED_AUTO_CORE_REF.as_posix(),
                "role": "GENERATED_FULL_CORPUS_INTEGRATED_TOC",
                "exists": True,
                "source_space": "generated_in_build_tree",
                "source_ref": "content/_auto_core_inputs.tex",
            },
            {
                "ref": INTEGRATED_APPENDIX_REF.as_posix(),
                "role": "GENERATED_SOURCE_TO_PDF_TRACE_APPENDIX",
                "exists": True,
                "source_space": "generated_in_build_tree",
            },
            {
                "ref": POSITIVE_STANDARD_APPENDIX_REF.as_posix(),
                "role": "GENERATED_PUBLIC_QUALITY_STANDARD_APPENDIX",
                "exists": True,
                "source_space": "generated_in_build_tree",
            },
        ],
        "exclusion_policy": {
            "private_material": "Private Logion/k7 material is read-only input only and is excluded unless sanitized into public refs.",
            "runtime_material": "Runtime, cache, draft, and local-path-bearing files are excluded from the public monolith.",
            "journal_packages": "Journal packages are owner-review material and are represented by the package index; no submission is performed here.",
        },
    }
    return payload


def audit_monolith(root: Path, output_pdf: Path | None = None, build_context: dict[str, Any] | None = None) -> dict[str, Any]:
    path = output_pdf or root / ARTIFACTS_REF / MASTER_PDF_NAME
    ledger_path = root / EDITORIAL_REF / "SCIENCE_MONOLITH_CORPUS_LEDGER_1_3_3_latest.json"
    ledger = json.loads(read_text(ledger_path)) if ledger_path.exists() else build_corpus_ledger(root, output_pdf=path)
    if not path.exists():
        return {
            "schema_id": "OC133_SCIENCE_MONOLITH_AUDIT_v1",
            "state": "FAIL",
            "artifact": rel(root, path),
            "failure_total": 1,
            "failures": ["missing_master_monolith_pdf"],
        }
    text = _pdf_text(path)
    reader = PdfReader(str(path))
    anchor_hits = {anchor: (anchor in text) for anchor in ANCHORS}
    stale_hits = [
        {"match": match.group(0), "context": text[max(0, match.start() - 80) : match.end() + 120].replace("\n", " ")[:260]}
        for match in STALE_PUBLIC_IDENTITY.finditer(text)
    ][:20]
    failures = []
    build_payload = build_context or read_json(root / EDITORIAL_REF / "SCIENCE_MONOLITH_BUILD_1_3_3_latest.json", {})
    build_assembly_mode = build_payload.get("assembly_mode")
    entrypoint_rewrite = build_payload.get("entrypoint_rewrite", {})
    pdf_merge_used = bool(build_payload.get("pdf_merge_used") or build_payload.get("merge"))
    forbidden_assembly_hits = [
        {"match": match.group(0), "context": text[max(0, match.start() - 80) : match.end() + 140].replace("\n", " ")[:260]}
        for match in FORBIDDEN_ASSEMBLY_TEXT.finditer(text)
    ][:20]
    required_integrated_hits = {
        "single_integrated_tex_build": build_assembly_mode in {None, "SINGLE_INTEGRATED_TEX_BUILD"},
        "pdf_merge_not_used": not pdf_merge_used,
        "corpus_ledger_present": ledger_path.exists() and ledger.get("missing_total", 1) == 0,
        "publication_grade_manuscript_anchor": "publication-grade manuscript" in text.lower(),
        "no_delta_appendix_language": not forbidden_assembly_hits,
        "full_auto_core_in_entrypoint": bool(entrypoint_rewrite.get("full_auto_core_in_entrypoint")),
        "all_integrated_content_in_auto_core": bool(entrypoint_rewrite.get("all_integrated_content_in_entrypoint")),
        "full_auto_core_line_total_preserved": int(entrypoint_rewrite.get("full_auto_core_line_total") or 0) >= 100,
        "top_down_structure_freeze_pass": entrypoint_rewrite.get("top_down_structure_freeze_gate", {}).get("state") == "PASS",
    }
    if len(reader.pages) < ANTI_SURROGATE_MIN_MONOLITH_PAGES:
        failures.append("master_monolith_page_count_below_anti_surrogate_lower_bound")
    if len(text) < ANTI_SURROGATE_MIN_MONOLITH_TEXT_CHARS:
        failures.append("master_monolith_text_volume_below_anti_surrogate_lower_bound")
    if not all(anchor_hits.values()):
        failures.append("master_monolith_missing_required_text_anchors")
    if stale_hits:
        failures.append("master_monolith_contains_stale_1_3_2_public_identity")
    if ledger.get("missing_total", 1) != 0:
        failures.append("science_monolith_corpus_ledger_has_missing_refs")
    if pdf_merge_used:
        failures.append("full_monograph_gate_pdf_merge_used")
    if forbidden_assembly_hits:
        failures.append("full_monograph_gate_delta_appendix_language_present")
    if not all(required_integrated_hits.values()):
        failures.append("science_monolith_coverage_gate_missing_integrated_manuscript_anchors")
    if entrypoint_rewrite.get("top_down_structure_freeze_gate", {}).get("state") != "PASS":
        failures.append("top_down_structure_freeze_gate_failed")
    payload = {
        "schema_id": "OC133_SCIENCE_MONOLITH_AUDIT_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": "CONTENT_HASH_STABLE_NO_WALLCLOCK",
        "state": "PASS" if not failures else "FAIL",
        "failure_total": len(failures),
        "failures": failures,
        "artifact": rel(root, path),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
        "pages": len(reader.pages),
        "text_chars": len(text),
        "anti_surrogate_min_pages": ANTI_SURROGATE_MIN_MONOLITH_PAGES,
        "anti_surrogate_min_text_chars": ANTI_SURROGATE_MIN_MONOLITH_TEXT_CHARS,
        "baseline_full_monograph_reference_pages": BASELINE_FULL_MONOGRAPH_REFERENCE_PAGES,
        "baseline_full_monograph_reference_text_chars": BASELINE_FULL_MONOGRAPH_REFERENCE_TEXT_CHARS,
        "maximum_pages": None,
        "maximum_text_chars": None,
        "size_policy": MONOLITH_SIZE_POLICY,
        "volume_policy": MONOLITH_VOLUME_POLICY,
        "structure_policy": MONOLITH_STRUCTURE_POLICY,
        "raw_registers_kept_in_evidence_package": True,
        "anchor_hits": anchor_hits,
        "full_monograph_gate": {
            "assembly_mode": build_assembly_mode,
            "pdf_merge_used": pdf_merge_used,
            "required_integrated_hits": required_integrated_hits,
            "entrypoint_rewrite": entrypoint_rewrite,
            "forbidden_assembly_hit_total": len(forbidden_assembly_hits),
            "forbidden_assembly_hits": forbidden_assembly_hits,
        },
        "stale_public_identity_hit_total": len(stale_hits),
        "stale_public_identity_hits": stale_hits,
        "corpus_ledger": {
            "path": rel(root, ledger_path) if ledger_path.exists() else str(ledger_path),
            "missing_total": ledger.get("missing_total"),
            "baseline_source_total": ledger.get("baseline_source_total"),
            "mandatory_science_source_total": ledger.get("mandatory_science_source_total"),
            "proof_sheet_total": ledger.get("proof_sheet_total"),
        },
    }
    return payload


def materialize_monolith(
    root: Path | None = None,
    *,
    doi: str | None = None,
    zenodo_record_url: str | None = None,
) -> dict[str, Any]:
    root = repo_root(root)
    build_dir = root / BUILD_REF
    _safe_clear_build_dir(root, build_dir)
    source_dir = _prepare_base_source(root, build_dir, doi=doi, zenodo_record_url=zenodo_record_url)
    integration = _generate_integrated_science_tex(root, source_dir, doi=doi, zenodo_record_url=zenodo_record_url)
    _rewrite_public_science_projection_sources(source_dir)
    entrypoint = _rewrite_entrypoint_for_integrated_133(source_dir)
    _sanitize_source_tree(source_dir)
    base_pdf, base_commands = _build_base_pdf(source_dir)
    output_pdf = root / ARTIFACTS_REF / MASTER_PDF_NAME
    build_failures = [row for row in base_commands if not row["ok"]]
    if not build_failures and base_pdf.exists():
        output_pdf.parent.mkdir(parents=True, exist_ok=True)
        if not output_pdf.exists() or output_pdf.read_bytes() != base_pdf.read_bytes():
            output_pdf.write_bytes(base_pdf.read_bytes())
    ledger = build_corpus_ledger(root, output_pdf=output_pdf)
    ledger_path = root / EDITORIAL_REF / "SCIENCE_MONOLITH_CORPUS_LEDGER_1_3_3_latest.json"
    write_json_if_changed(ledger_path, ledger)
    audit = audit_monolith(
        root,
        output_pdf=output_pdf,
        build_context={
            "assembly_mode": "SINGLE_INTEGRATED_TEX_BUILD",
            "pdf_merge_used": False,
            "merge": {},
            "entrypoint_rewrite": entrypoint,
        },
    )
    audit_path = root / EDITORIAL_REF / "SCIENCE_MONOLITH_AUDIT_1_3_3_latest.json"
    write_json_if_changed(audit_path, audit)
    build_payload = {
        "schema_id": "OC133_SCIENCE_MONOLITH_BUILD_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "state": "PASS" if not build_failures and audit["state"] == "PASS" else "FAIL",
        "assembly_mode": "SINGLE_INTEGRATED_TEX_BUILD",
        "pdf_merge_used": False,
        "build_dir": BUILD_REF.as_posix(),
        "base_source_dir": rel(root, source_dir),
        "base_pdf": rel(root, base_pdf) if base_pdf.exists() else str(base_pdf),
        "integration": integration,
        "entrypoint_rewrite": entrypoint,
        "output_pdf": rel(root, output_pdf) if output_pdf.exists() else str(output_pdf),
        "base_commands": base_commands,
        "build_failure_total": len(build_failures),
        "ledger_path": rel(root, ledger_path),
        "audit_path": rel(root, audit_path),
        "audit": audit,
    }
    write_json_if_changed(root / EDITORIAL_REF / "SCIENCE_MONOLITH_BUILD_1_3_3_latest.json", build_payload)
    lines = [
        "# OC Core 1.3.3 Science Monolith Build",
        "",
        f"State: `{build_payload['state']}`",
        f"Output: `{build_payload['output_pdf']}`",
        f"Pages: `{audit.get('pages')}`",
        f"Text chars: `{audit.get('text_chars')}`",
        f"Anti-surrogate lower bound pages: `{audit.get('anti_surrogate_min_pages')}`",
        f"Anti-surrogate lower bound text chars: `{audit.get('anti_surrogate_min_text_chars')}`",
        f"Baseline full-monograph reference pages: `{audit.get('baseline_full_monograph_reference_pages')}`",
        f"Baseline full-monograph reference text chars: `{audit.get('baseline_full_monograph_reference_text_chars')}`",
        "Maximum pages: `none`",
        "Maximum text chars: `none`",
        f"Size policy: `{audit.get('size_policy')}`",
        f"Volume policy: `{audit.get('volume_policy')}`",
        f"SHA-256: `{audit.get('sha256')}`",
        f"Failures: `{audit.get('failures')}`",
    ]
    write_text_if_changed(root / EDITORIAL_REF / "SCIENCE_MONOLITH_BUILD_1_3_3_latest.md", "\n".join(lines))
    return build_payload
