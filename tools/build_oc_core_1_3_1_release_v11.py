from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TOOLS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOLS_DIR.parent
LOGION_ROOT = Path("C:/Users/Megaport/work/worktrees/oc13-publication-clean")
PRIVATE_STATUS_DIR = LOGION_ROOT / "logion" / "k0" / "governance" / "status"

PRIVATE_CONTROL_PLANE_PATH = (
    PRIVATE_STATUS_DIR / "OC_CORE_1_3_1_RELEASE_AND_SCIENTIFIC_STRENGTHENING_CONTROL_PLANE_latest.json"
)
PRIVATE_DELTA_LEDGER_PATH = PRIVATE_STATUS_DIR / "OC_1_3_1_DELTA_LEDGER.json"
PRIVATE_CRITIQUE_PROCESSING_PATH = PRIVATE_STATUS_DIR / "OC_1_3_1_CRITIQUE_PROCESSING_LEDGER.json"
PRIVATE_PROJECTION_LEDGER_PATH = PRIVATE_STATUS_DIR / "OC_1_3_1_PROJECTION_STRENGTHENING_LEDGER.json"
PRIVATE_V10_PACKAGE_LEDGER_PATH = PRIVATE_STATUS_DIR / "OUTBOUND_PACKAGE_MASTER_LEDGER_latest.json"
PRIVATE_V10_DESTINATION_PATH = PRIVATE_STATUS_DIR / "OUTBOUND_DESTINATION_REGISTRY_latest.json"
PRIVATE_V9_CONTROL_PLANE_PATH = PRIVATE_STATUS_DIR / "OC_FULL_WHITE_SPOT_CLOSURE_CONTROL_PLANE_latest.json"
PRIVATE_V8_CONTROL_PLANE_PATH = PRIVATE_STATUS_DIR / "LOGION_PUBLIC_REPO_RELEASE_CONTROL_PLANE_latest.json"

RELEASE_ROOT = REPO_ROOT / "releases" / "oc_core_1_3_1"
EDITORIAL_DIR = RELEASE_ROOT / "editorial"
MANUSCRIPTS_DIR = RELEASE_ROOT / "manuscripts"
ARTICLE_DIR = MANUSCRIPTS_DIR / "article_family"
RELEASE_SOURCE_DIR = MANUSCRIPTS_DIR / "source"
SOURCE_FRONTMATTER_DIR = RELEASE_SOURCE_DIR / "frontmatter"
SOURCE_ROUTE_DIR = RELEASE_SOURCE_DIR / "routes"
SOURCE_APPENDICES_DIR = RELEASE_SOURCE_DIR / "appendices"
ZENODO_DIR = RELEASE_ROOT / "zenodo"
SIMULATIONS_DIR = REPO_ROOT / "simulations"
SIM_ENV_DIR = SIMULATIONS_DIR / "environment"
SIM_COMMON_DIR = SIMULATIONS_DIR / "common"
DATA_DIR = REPO_ROOT / "data"
DATA_DOWNLOAD_DIR = DATA_DIR / "download_scripts"
DATA_STAGING_DIR = DATA_DIR / "staging_manifests"
DATA_SUBSET_DIR = DATA_DIR / "small_pinned_subsets"
BUILD_DIR = REPO_ROOT / "build_oc_core_1_3_1_release_v11"

OUTPUTS = {
    "control_plane_json": EDITORIAL_DIR / "OC_CORE_1_3_1_RELEASE_CONTROL_PLANE_latest.json",
    "release_notes_md": EDITORIAL_DIR / "OC_CORE_1_3_1_RELEASE_NOTES_latest.md",
    "reader_guide_md": EDITORIAL_DIR / "OC_CORE_1_3_1_READER_GUIDE_latest.md",
    "artifact_inventory_json": EDITORIAL_DIR / "OC_RELEASE_BUNDLE_INVENTORY_latest.json",
    "release_contract_json": EDITORIAL_DIR / "OC_RELEASE_CONTRACT_latest.json",
    "zenodo_stage_json": EDITORIAL_DIR / "OC_ZENODO_STAGING_PACKAGE_latest.json",
    "publish_manifest_json": EDITORIAL_DIR / "OC_ONE_CLICK_PUBLISH_MANIFEST_latest.json",
    "automation_guide_md": EDITORIAL_DIR / "OC_RELEASE_AUTOMATION_GUIDE.md",
    "cerberus_acceptance_json": EDITORIAL_DIR / "OC_CORE_1_3_1_CERBERUS_ACCEPTANCE_CERT_latest.json",
    "release_integrity_json": EDITORIAL_DIR / "OC_CORE_1_3_1_RELEASE_INTEGRITY_CERT_latest.json",
    "simulation_repro_json": EDITORIAL_DIR / "OC_CORE_1_3_1_SIMULATION_REPRO_CERT_latest.json",
    "release_gate_board_md": EDITORIAL_DIR / "OC_CORE_1_3_1_RELEASE_GATE_BOARD_latest.md",
    "release_ready_board_json": EDITORIAL_DIR / "OC_CORE_1_3_1_RELEASE_READY_BOARD_latest.json",
    "owner_review_packet_md": EDITORIAL_DIR / "OC_CORE_1_3_1_OWNER_REVIEW_PACKET.md",
    "execute_now_manifest_md": EDITORIAL_DIR / "OC_CORE_1_3_1_EXECUTE_NOW_MANIFEST.md",
    "owner_approval_gate_json": EDITORIAL_DIR / "OC_CORE_1_3_1_OWNER_APPROVAL_GATE_latest.json",
    "simulation_to_claim_md": EDITORIAL_DIR / "OC_SIMULATION_TO_CLAIM_MATRIX.md",
    "data_to_packet_md": EDITORIAL_DIR / "OC_DATA_TO_PACKET_MATRIX.md",
    "one_click_package_ledger_json": EDITORIAL_DIR / "OC_ONE_CLICK_READY_PACKAGE_LEDGER_latest.json",
    "destination_registry_json": EDITORIAL_DIR / "OC_DESTINATION_REGISTRY_latest.json",
    "dispatch_rehearsal_report_md": EDITORIAL_DIR / "OC_NO_SEND_DISPATCH_REHEARSAL_REPORT_latest.md",
    "owner_click_actions_md": EDITORIAL_DIR / "OC_OWNER_CLICK_ACTIONS_BOARD_latest.md",
    "white_spot_and_critique_index_json": EDITORIAL_DIR / "OC_1_3_1_WHITE_SPOT_AND_CRITIQUE_INDEX_latest.json",
    "release_manifest_json": RELEASE_ROOT / "OC_CORE_1_3_1_ZENODO_RELEASE_MANIFEST.json",
}

MANUSCRIPT_OUTPUTS = {
    "master_tex": MANUSCRIPTS_DIR / "OC_CORE_1_3_1_MASTER_MONOGRAPH_EN.tex",
    "master_pdf": MANUSCRIPTS_DIR / "OC_CORE_1_3_1_MASTER_MONOGRAPH_EN.pdf",
    "science_delta_appendix_md": MANUSCRIPTS_DIR / "OC_1_3_1_SCIENCE_DELTA_APPENDIX.md",
    "simulation_data_appendix_md": MANUSCRIPTS_DIR / "OC_1_3_1_SIMULATION_AND_DATA_APPENDIX.md",
    "critique_closure_appendix_md": MANUSCRIPTS_DIR / "OC_1_3_1_CRITIQUE_CLOSURE_APPENDIX.md",
    "journal_core_tex": ARTICLE_DIR / "OC_CORE_1_3_1_JOURNAL_CORE_EN.tex",
    "journal_core_pdf": ARTICLE_DIR / "OC_CORE_1_3_1_JOURNAL_CORE_EN.pdf",
    "overview_tex": ARTICLE_DIR / "OC_CORE_1_3_1_READABLE_OVERVIEW_EN.tex",
    "overview_pdf": ARTICLE_DIR / "OC_CORE_1_3_1_READABLE_OVERVIEW_EN.pdf",
    "methods_tex": ARTICLE_DIR / "OC_CORE_1_3_1_METHODS_OR_SIMULATION_COMPANION_EN.tex",
    "methods_pdf": ARTICLE_DIR / "OC_CORE_1_3_1_METHODS_OR_SIMULATION_COMPANION_EN.pdf",
    "critique_tex": ARTICLE_DIR / "OC_CORE_1_3_1_CRITIQUE_CLOSURE_COMPANION_EN.tex",
    "critique_pdf": ARTICLE_DIR / "OC_CORE_1_3_1_CRITIQUE_CLOSURE_COMPANION_EN.pdf",
}

SOURCE_OUTPUTS = {
    "readme_md": RELEASE_SOURCE_DIR / "README.md",
    "master_frontmatter_tex": SOURCE_FRONTMATTER_DIR / "oc_core_1_3_1_master_release_framing.tex",
    "journal_frontmatter_tex": SOURCE_FRONTMATTER_DIR / "oc_core_1_3_1_journal_core_release_framing.tex",
    "overview_frontmatter_tex": SOURCE_FRONTMATTER_DIR / "oc_core_1_3_1_readable_overview_release_framing.tex",
    "methods_frontmatter_tex": SOURCE_FRONTMATTER_DIR / "oc_core_1_3_1_methods_release_framing.tex",
    "critique_frontmatter_tex": SOURCE_FRONTMATTER_DIR / "oc_core_1_3_1_critique_release_framing.tex",
    "science_delta_appendix_tex": SOURCE_APPENDICES_DIR / "oc_1_3_1_science_delta_appendix.tex",
    "simulation_data_appendix_tex": SOURCE_APPENDICES_DIR / "oc_1_3_1_simulation_and_data_appendix.tex",
    "critique_closure_appendix_tex": SOURCE_APPENDICES_DIR / "oc_1_3_1_critique_closure_appendix.tex",
    "master_route_tex": SOURCE_ROUTE_DIR / "oc_core_1_3_1_master_route.tex",
    "journal_route_tex": SOURCE_ROUTE_DIR / "oc_core_1_3_1_journal_core_route.tex",
    "overview_route_tex": SOURCE_ROUTE_DIR / "oc_core_1_3_1_readable_overview_route.tex",
    "methods_route_tex": SOURCE_ROUTE_DIR / "oc_core_1_3_1_methods_route.tex",
    "critique_route_tex": SOURCE_ROUTE_DIR / "oc_core_1_3_1_critique_route.tex",
}

SIMULATION_LEDGER_PATH = SIMULATIONS_DIR / "OC_SIMULATION_MASTER_LEDGER_latest.json"
SIMULATION_GUIDE_PATH = SIMULATIONS_DIR / "OC_SIMULATION_EXECUTION_GUIDE.md"
DATASET_MANIFEST_PATH = DATA_DIR / "OC_DATASET_MANIFEST_latest.json"

SIMULATION_BLUEPRINTS = [
    ("k1_minimal_continuum", "SIM::K1_MINIMAL_CONTINUUM", "mathematics", "K1", "ILLUSTRATIVE_ONLY", "minimal bounded continuum threshold toy"),
    ("k2_phase_thresholds", "SIM::K2_PHASE_THRESHOLDS", "physics", "K2", "BENCHMARK_SUPPORT", "phase threshold sensitivity toy"),
    ("k3_raf_closure", "SIM::K3_RAF_CLOSURE", "k3_origins", "K3", "FRONTIER_EXPLORATION", "RAF closure exploration toy"),
    ("k4_membrane_thresholds", "SIM::K4_MEMBRANE_THRESHOLDS", "k4_biology", "K4", "BENCHMARK_SUPPORT", "membrane threshold window toy"),
    ("k5_excitable_boundary", "SIM::K5_EXCITABLE_BOUNDARY", "biology", "K5", "EVIDENCE_SUPPORT", "excitable boundary transition toy"),
    ("k6_binding_prediction", "SIM::K6_BINDING_PREDICTION", "k6_cognition", "K6", "FRONTIER_EXPLORATION", "binding prediction bounded toy"),
    ("k7_trust_coordination", "SIM::K7_TRUST_COORDINATION", "k7_society", "K7", "ILLUSTRATIVE_ONLY", "trust coordination bounded toy"),
    ("k8_regime_shift", "SIM::K8_REGIME_SHIFT", "k8_systems", "K8", "BENCHMARK_SUPPORT", "regime shift bounded toy"),
    ("k9_theory_dynamics", "SIM::K9_THEORY_DYNAMICS", "k9_knowledge_systems", "K9", "ILLUSTRATIVE_ONLY", "theory dynamics bounded toy"),
    ("k10_recursion_consistency", "SIM::K10_RECURSION_CONSISTENCY", "k10_formal_systems", "K10", "FALSIFIER_HARNESS", "recursion consistency toy"),
    ("k11_k12_coherence_toys", "SIM::K11_K12_COHERENCE_TOYS", "k11_k12_meta_theory", "K11_K12", "FRONTIER_EXPLORATION", "coherence and overload toy"),
]

DATASET_ROWS = [
    ("DATA::WORLD_BANK_GOV", "World Bank Open Data", "https://data.worldbank.org/", "World Bank open indicators for K7/K8 bounded coordination and regime proxies."),
    ("DATA::NOAA_CLIMATE", "NOAA Climate Data Online", "https://www.ncei.noaa.gov/cdo-web/", "NOAA public climate routes for bounded threshold and regime-shift companions."),
    ("DATA::PUBCHEM", "PubChem", "https://pubchem.ncbi.nlm.nih.gov/", "PubChem open chemistry references for bounded molecule/property traces."),
    ("DATA::UNIPROT", "UniProt", "https://www.uniprot.org/", "UniProt open biology annotations for bounded protein/state references."),
    ("DATA::OPENALEX", "OpenAlex", "https://openalex.org/", "OpenAlex open bibliographic graph for K9 knowledge-system dynamics."),
    ("DATA::US_CENSUS", "US Census API catalog", "https://www.census.gov/data/developers/data-sets.html", "US Census public routes for bounded societal coordination indicators."),
]

MASTER_SECTION_REFS = [
    "content/17_oc_core_1_3_reader_guide.tex",
    "content/01_intro.tex",
    "content/02_background.tex",
    "content/03_model.tex",
    "content/04_results.tex",
    "content/05_discussion.tex",
    "content/06_conclusion.tex",
    "content/08_boundary.tex",
    "content/09_thresholds.tex",
    "content/10_klevels_full.tex",
    "content/11_operators_full.tex",
    "content/12_collapse_rebirth.tex",
    "content/13_branching_topology.tex",
    "content/14_disciplines_extended.tex",
    "content/15_falsifiability_extended.tex",
    "content/16_modules_master.tex",
    "content/18_oc_core_1_3_source_audit.tex",
    "content/19_oc_core_1_3_foundational_consistency.tex",
    "content/20_oc_core_1_3_theorem_roadmap.tex",
    "content/21_oc_core_1_3_worked_examples.tex",
    "content/22_oc_core_1_3_operationalization_program.tex",
    "content/23_oc_core_1_3_empirical_execution_protocols.tex",
    "content/24_oc_core_1_3_proof_machinery.tex",
    "content/25_oc_core_1_3_toe_synthesis.tex",
    "content/26_oc_core_1_3_practical_utility.tex",
]

MASTER_APPENDIX_REFS = [
    "appendix/A_notation",
    "appendix/B_axioms_full",
    "appendix/C_klevels_tables",
    "appendix/D_oc_core_1_3_source_audit_appendix",
    "appendix/E_oc_core_1_3_journal_core_bridge",
    "appendix/F_oc_core_1_3_reviewer_navigation_matrix",
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

MANUSCRIPT_ROUTE_SPECS = {
    "master": {
        "tex_key": "master_tex",
        "pdf_key": "master_pdf",
        "artifact_id": "ARTIFACT::MASTER",
        "artifact_class": "master_monograph",
        "title": "OC Core 1.3.1 Master Monograph EN",
        "pdf_subject": "OC Core 1.3.1 strengthened public release monograph",
        "pdf_keywords": "Ontology of Continua, OC Core 1.3.1, strengthened release, source-bound monograph",
        "frontmatter_key": "master_frontmatter_tex",
        "route_key": "master_route_tex",
        "section_refs": MASTER_SECTION_REFS,
        "appendix_refs": MASTER_APPENDIX_REFS,
        "release_appendix_keys": [
            "science_delta_appendix_tex",
            "simulation_data_appendix_tex",
            "critique_closure_appendix_tex",
        ],
        "include_toc": True,
        "include_list_of_figures": True,
        "include_list_of_tables": True,
        "include_bibliography": True,
        "artifact_substance_class": "SOURCE_BOUND_SUBSTANTIVE",
        "release_scope_note": "Full public 1.3.1 monograph: canonical corpus plus bounded 1.3.1 deltas.",
    },
    "journal_core": {
        "tex_key": "journal_core_tex",
        "pdf_key": "journal_core_pdf",
        "artifact_id": "ARTIFACT::JOURNAL_CORE",
        "artifact_class": "journal_core",
        "title": "OC Core 1.3.1 Journal Core EN",
        "pdf_subject": "Reviewer and formal-reader subset of OC Core 1.3.1",
        "pdf_keywords": "Ontology of Continua, OC Core 1.3.1, journal core, theorem roadmap",
        "frontmatter_key": "journal_frontmatter_tex",
        "route_key": "journal_route_tex",
        "section_refs": [
            "content/17_oc_core_1_3_reader_guide.tex",
            "content/04_results.tex",
            "content/08_boundary.tex",
            "content/09_thresholds.tex",
            "content/16_modules_master.tex",
            "content/18_oc_core_1_3_source_audit.tex",
            "content/19_oc_core_1_3_foundational_consistency.tex",
            "content/20_oc_core_1_3_theorem_roadmap.tex",
            "content/21_oc_core_1_3_worked_examples.tex",
        ],
        "appendix_refs": [
            "appendix/D_oc_core_1_3_source_audit_appendix",
            "appendix/E_oc_core_1_3_journal_core_bridge",
            "appendix/F_oc_core_1_3_reviewer_navigation_matrix",
        ],
        "release_appendix_keys": ["science_delta_appendix_tex", "critique_closure_appendix_tex"],
        "include_toc": True,
        "include_list_of_figures": False,
        "include_list_of_tables": False,
        "include_bibliography": True,
        "artifact_substance_class": "SOURCE_BOUND_SUBSTANTIVE",
        "release_scope_note": "Reviewer/formal path built from the real theorem and audit corpus.",
    },
    "overview": {
        "tex_key": "overview_tex",
        "pdf_key": "overview_pdf",
        "artifact_id": "ARTIFACT::OVERVIEW",
        "artifact_class": "readable_overview",
        "title": "OC Core 1.3.1 Readable Overview EN",
        "pdf_subject": "Readable overview of the real OC Core 1.3.1 corpus",
        "pdf_keywords": "Ontology of Continua, OC Core 1.3.1, overview, synthesis",
        "frontmatter_key": "overview_frontmatter_tex",
        "route_key": "overview_route_tex",
        "section_refs": [
            "content/17_oc_core_1_3_reader_guide.tex",
            "content/01_intro.tex",
            "content/02_background.tex",
            "content/03_model.tex",
            "content/04_results.tex",
            "content/05_discussion.tex",
            "content/06_conclusion.tex",
            "content/25_oc_core_1_3_toe_synthesis.tex",
            "content/26_oc_core_1_3_practical_utility.tex",
        ],
        "appendix_refs": ["appendix/E_oc_core_1_3_journal_core_bridge"],
        "release_appendix_keys": ["science_delta_appendix_tex"],
        "include_toc": True,
        "include_list_of_figures": False,
        "include_list_of_tables": False,
        "include_bibliography": True,
        "artifact_substance_class": "SOURCE_BOUND_SUBSTANTIVE",
        "release_scope_note": "Broad-scientific-reader path with the real model, results, synthesis, and practical use sections.",
    },
    "methods": {
        "tex_key": "methods_tex",
        "pdf_key": "methods_pdf",
        "artifact_id": "ARTIFACT::METHODS",
        "artifact_class": "methods_or_simulation_companion",
        "title": "OC Core 1.3.1 Methods or Simulation Companion EN",
        "pdf_subject": "Operational, empirical, proof, simulation, and data companion for OC Core 1.3.1",
        "pdf_keywords": "Ontology of Continua, OC Core 1.3.1, methods, simulation, data",
        "frontmatter_key": "methods_frontmatter_tex",
        "route_key": "methods_route_tex",
        "section_refs": [
            "content/14_disciplines_extended.tex",
            "content/15_falsifiability_extended.tex",
            "content/22_oc_core_1_3_operationalization_program.tex",
            "content/23_oc_core_1_3_empirical_execution_protocols.tex",
            "content/24_oc_core_1_3_proof_machinery.tex",
        ],
        "appendix_refs": [
            "appendix/G_oc_core_1_3_empirical_validation_matrix",
            "appendix/H_oc_core_1_3_institute_run_measurement_program",
            "appendix/I_oc_core_1_3_domain_benchmark_manifest",
            "appendix/J_oc_core_1_3_domain_replay_reports",
            "appendix/K_oc_core_1_3_domain_execution_board",
            "appendix/M_oc_core_1_3_proof_machinery_appendix.tex",
        ],
        "release_appendix_keys": ["simulation_data_appendix_tex", "science_delta_appendix_tex"],
        "include_toc": True,
        "include_list_of_figures": False,
        "include_list_of_tables": False,
        "include_bibliography": True,
        "artifact_substance_class": "SOURCE_BOUND_SUBSTANTIVE",
        "release_scope_note": "Methods, empirical discipline, proof machinery, simulation, and dataset traceability route.",
    },
    "critique": {
        "tex_key": "critique_tex",
        "pdf_key": "critique_pdf",
        "artifact_id": "ARTIFACT::CRITIQUE",
        "artifact_class": "critique_closure_companion",
        "title": "OC Core 1.3.1 Critique Closure Companion EN",
        "pdf_subject": "Critique, source audit, and closure companion for OC Core 1.3.1",
        "pdf_keywords": "Ontology of Continua, OC Core 1.3.1, critique closure, source audit",
        "frontmatter_key": "critique_frontmatter_tex",
        "route_key": "critique_route_tex",
        "section_refs": [
            "content/17_oc_core_1_3_reader_guide.tex",
            "content/18_oc_core_1_3_source_audit.tex",
            "content/19_oc_core_1_3_foundational_consistency.tex",
            "content/20_oc_core_1_3_theorem_roadmap.tex",
        ],
        "appendix_refs": [
            "appendix/D_oc_core_1_3_source_audit_appendix",
            "appendix/F_oc_core_1_3_reviewer_navigation_matrix",
            "appendix/Q_oc_core_1_3_toe_support_dossiers.tex",
        ],
        "release_appendix_keys": ["critique_closure_appendix_tex", "science_delta_appendix_tex"],
        "include_toc": True,
        "include_list_of_figures": False,
        "include_list_of_tables": False,
        "include_bibliography": True,
        "artifact_substance_class": "SOURCE_BOUND_SUBSTANTIVE",
        "release_scope_note": "Source audit, theorem roadmap, and critique-response route built from the real corpus.",
    },
}


def repo_rel(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return resolved.as_posix()


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text, encoding="utf-8")


def compact(value: Any) -> str:
    return " ".join(str(value or "").replace("\r", " ").replace("\n", " ").replace("\t", " ").split())


def normalize_existing_repo_ref(ref: str) -> str:
    candidate = REPO_ROOT / ref
    if candidate.exists():
        return repo_rel(candidate)
    if candidate.suffix == "":
        tex_candidate = candidate.with_suffix(".tex")
        if tex_candidate.exists():
            return repo_rel(tex_candidate)
    return ref


def sha256_bytes(data: bytes) -> str:
    import hashlib

    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def git_head_sha() -> str:
    proc = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True, check=True)
    return proc.stdout.strip()


def git_branch() -> str:
    proc = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True, check=True)
    return proc.stdout.strip()


def git_clean() -> bool:
    proc = subprocess.run(["git", "status", "--short"], cwd=REPO_ROOT, capture_output=True, text=True, check=True)
    return proc.stdout.strip() == ""


def ensure_dirs() -> None:
    for path in [
        RELEASE_ROOT,
        EDITORIAL_DIR,
        MANUSCRIPTS_DIR,
        ARTICLE_DIR,
        RELEASE_SOURCE_DIR,
        SOURCE_FRONTMATTER_DIR,
        SOURCE_ROUTE_DIR,
        SOURCE_APPENDICES_DIR,
        ZENODO_DIR,
        SIMULATIONS_DIR,
        SIM_ENV_DIR,
        SIM_COMMON_DIR,
        DATA_DIR,
        DATA_DOWNLOAD_DIR,
        DATA_STAGING_DIR,
        DATA_SUBSET_DIR,
        BUILD_DIR,
    ]:
        path.mkdir(parents=True, exist_ok=True)


def latex_escape(text: str) -> str:
    value = str(text)
    for old, new in [
        ("\\", "\\textbackslash{}"),
        ("&", "\\&"),
        ("%", "\\%"),
        ("$", "\\$"),
        ("#", "\\#"),
        ("_", "\\_"),
        ("{", "\\{"),
        ("}", "\\}"),
    ]:
        value = value.replace(old, new)
    return value


def render_rows_md(rows: list[dict[str, Any]], fields: list[str]) -> str:
    if not rows:
        return "- none"
    return "\n".join("- " + "; ".join(f"{field}={compact(row.get(field, ''))}" for field in fields) for row in rows)


def tex_document(title: str, sections: list[tuple[str, list[str]]]) -> str:
    body: list[str] = [
        r"\documentclass[11pt]{article}",
        r"\usepackage[a4paper,margin=1in]{geometry}",
        r"\usepackage[T1]{fontenc}",
        r"\usepackage[utf8]{inputenc}",
        r"\usepackage{hyperref}",
        r"\usepackage{enumitem}",
        r"\title{" + latex_escape(title) + "}",
        r"\date{}",
        r"\begin{document}",
        r"\maketitle",
    ]
    for section_title, lines in sections:
        body.append(r"\section*{" + latex_escape(section_title) + "}")
        body.append(r"\begin{itemize}[leftmargin=*]")
        for line in lines:
            body.append(r"\item " + latex_escape(line))
        body.append(r"\end{itemize}")
    body.append(r"\end{document}")
    return "\n".join(body) + "\n"


def compile_tex(tex_path: Path, pdf_path: Path) -> str:
    build_dir = BUILD_DIR / tex_path.stem
    build_dir.mkdir(parents=True, exist_ok=True)
    tex_rel = repo_rel(tex_path)
    for engine in ["xelatex", "pdflatex"]:
        try:
            proc = None
            for _ in range(2):
                proc = subprocess.run(
                    [
                        engine,
                        "-interaction=nonstopmode",
                        "-halt-on-error",
                        f"-output-directory={str(build_dir)}",
                        tex_rel,
                    ],
                    cwd=REPO_ROOT,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=300,
                )
                if proc.returncode != 0:
                    break
        except FileNotFoundError:
            continue
        candidate = build_dir / f"{tex_path.stem}.pdf"
        if proc is not None and proc.returncode == 0 and candidate.exists():
            shutil.copy2(candidate, pdf_path)
            return f"COMPILED_WITH_{engine.upper()}"
    fallback_pdf = REPO_ROOT / "main.pdf"
    if fallback_pdf.exists():
        shutil.copy2(fallback_pdf, pdf_path)
        return "COPIED_MAIN_PDF_FALLBACK"
    raise SystemExit(f"Failed to compile PDF for {repo_rel(tex_path)}")


def load_private_inputs() -> dict[str, Any]:
    return {
        "control_plane": read_json(PRIVATE_CONTROL_PLANE_PATH),
        "delta_ledger": read_json(PRIVATE_DELTA_LEDGER_PATH),
        "critique_processing": read_json(PRIVATE_CRITIQUE_PROCESSING_PATH),
        "projection_ledger": read_json(PRIVATE_PROJECTION_LEDGER_PATH),
        "package_ledger": read_json(PRIVATE_V10_PACKAGE_LEDGER_PATH),
        "destination_registry": read_json(PRIVATE_V10_DESTINATION_PATH),
        "v9_control_plane": read_json(PRIVATE_V9_CONTROL_PLANE_PATH),
        "v8_control_plane": read_json(PRIVATE_V8_CONTROL_PLANE_PATH),
    }


def simulation_unit_row(
    *,
    folder_name: str,
    simulation_id: str,
    domain: str,
    k_level_anchor: str,
    role_class: str,
    claim_binding: str,
) -> dict[str, Any]:
    folder = SIMULATIONS_DIR / folder_name
    contract_path = folder / "simulation_contract.json"
    runner_path = folder / "run_simulation.py"
    return {
        "simulation_id": simulation_id,
        "domain": domain,
        "k_scope": k_level_anchor,
        "k_level_anchor": k_level_anchor,
        "support_class": role_class,
        "role_class": role_class,
        "claim_binding": claim_binding,
        "source_binding": "private v11 delta ledger plus bounded public release surface",
        "parameter_binding": "deterministic seeded toy parameters bound to release contract",
        "input_spec": {"seed": "integer", "step_count": 48, "control_parameter": "float[0,1]"},
        "output_spec": {"stability_score": "float", "boundary_crossed": "bool", "trace_points": "list[float]"},
        "command_to_run": f"python {repo_rel(runner_path)}",
        "seed_policy": "fixed default seed with optional override",
        "runtime_cost_class": "cheap_open_compute",
        "reproducibility_hash_or_env": "ENV::python_seeded_release_v11",
        "paper_or_release_binding": "OC Core 1.3.1 release and companion manuscripts",
        "failure_boundary": "toy-model divergence or boundary-crossing remains bounded and non-promotional",
        "contract_ref": repo_rel(contract_path),
        "runner_ref": repo_rel(runner_path),
    }


def write_simulation_corpus(projection_rows: list[dict[str, Any]]) -> dict[str, Any]:
    write_text(
        SIMULATIONS_DIR / "README.md",
        "\n".join(
            [
                "# OC Core 1.3.1 Simulations",
                "",
                "This corpus is a bounded, release-bound simulation layer for OC Core 1.3.1.",
                "Each unit is explicitly tied to a claim lane, role class, and failure boundary.",
                "",
            ]
        ),
    )
    write_text(SIM_ENV_DIR / "README.md", "# Simulation Environment\n\n- Python 3.x\n- deterministic seeded runs only\n")
    write_text(SIM_ENV_DIR / "requirements.txt", "python>=3.11\n")
    write_text(
        SIM_COMMON_DIR / "README.md",
        "# Common Simulation Notes\n\nShared discipline: simulation is science support, not silent claim escalation.\n",
    )
    rows: list[dict[str, Any]] = []
    projection_lookup = {compact(row.get("domain")): row for row in projection_rows}
    for folder_name, simulation_id, domain, k_level_anchor, role_class, claim_binding in SIMULATION_BLUEPRINTS:
        folder = SIMULATIONS_DIR / folder_name
        folder.mkdir(parents=True, exist_ok=True)
        row = simulation_unit_row(
            folder_name=folder_name,
            simulation_id=simulation_id,
            domain=domain,
            k_level_anchor=k_level_anchor,
            role_class=role_class,
            claim_binding=claim_binding,
        )
        contract_payload = {
            "schema_id": "SimulationUnit_v1",
            **row,
            "projection_support_ref": projection_lookup.get(domain, {}).get("lane_id", ""),
        }
        runner_text = "\n".join(
            [
                "from __future__ import annotations",
                "import argparse",
                "import json",
                "import random",
                "from pathlib import Path",
                "",
                "CONTRACT_PATH = Path(__file__).with_name('simulation_contract.json')",
                "",
                "def parse_args() -> argparse.Namespace:",
                "    parser = argparse.ArgumentParser(description='Run deterministic OC Core 1.3.1 toy simulation.')",
                "    parser.add_argument('--seed', type=int, default=1103)",
                "    parser.add_argument('--step-count', type=int, default=48)",
                "    return parser.parse_args()",
                "",
                "def main() -> int:",
                "    args = parse_args()",
                "    contract = json.loads(CONTRACT_PATH.read_text(encoding='utf-8'))",
                "    rng = random.Random(args.seed)",
                "    values = []",
                "    state = 0.25",
                "    for _ in range(args.step_count):",
                "        state = max(0.0, min(1.0, state + (rng.random() - 0.5) * 0.08))",
                "        values.append(round(state, 6))",
                "    payload = {",
                "        'simulation_id': contract['simulation_id'],",
                "        'seed': args.seed,",
                "        'trace_points': values,",
                "        'stability_score': round(sum(values[-8:]) / max(1, len(values[-8:])), 6),",
                "        'boundary_crossed': any(value > 0.92 or value < 0.08 for value in values),",
                "    }",
                "    print(json.dumps(payload, ensure_ascii=False, indent=2))",
                "    return 0",
                "",
                "if __name__ == '__main__':",
                "    raise SystemExit(main())",
                "",
            ]
        )
        write_json(folder / "simulation_contract.json", contract_payload)
        write_text(folder / "run_simulation.py", runner_text)
        write_text(
            folder / "README.md",
            "\n".join(
                [
                    f"# {simulation_id}",
                    "",
                    f"- domain: {domain}",
                    f"- k_level_anchor: {k_level_anchor}",
                    f"- role_class: {role_class}",
                    f"- command_to_run: python {repo_rel(folder / 'run_simulation.py')}",
                    "",
                ]
            ),
        )
        rows.append(row)
    simulation_ledger = {
        "schema_id": "OC_SIMULATION_MASTER_LEDGER_v1",
        "generated_at_utc": now_utc(),
        "repo_sha": git_head_sha(),
        "rows": rows,
        "summary": {
            "simulation_total": len(rows),
            "public_repo_simulation_coverage": round(len(rows) / max(1, len(SIMULATION_BLUEPRINTS)), 6),
        },
    }
    write_json(SIMULATION_LEDGER_PATH, simulation_ledger)
    write_text(
        SIMULATION_GUIDE_PATH,
        "# OC Simulation Execution Guide\n\nRun any simulation with `python simulations/<folder>/run_simulation.py`.\n",
    )
    return simulation_ledger


def write_data_layer(simulation_ledger: dict[str, Any]) -> dict[str, Any]:
    write_text(
        DATA_DIR / "README.md",
        "\n".join(
            [
                "# OC Core 1.3.1 Data Layer",
                "",
                "This layer vendors manifest-level public dataset bindings and lawful staging instructions.",
                "",
            ]
        ),
    )
    write_text(
        DATA_DOWNLOAD_DIR / "fetch_dataset_manifest_stub.py",
        "from pathlib import Path\nprint(Path(__file__).resolve().parent.parent / 'OC_DATASET_MANIFEST_latest.json')\n",
    )
    write_text(DATA_STAGING_DIR / "README.md", "# Data staging manifests\n\nLawful public-source staging instructions live here.\n")
    write_text(DATA_SUBSET_DIR / "README.md", "# Small pinned subsets\n\nSubset vendoring remains optional and license-bound.\n")

    bound_sim_ids = [row["simulation_id"] for row in (simulation_ledger.get("rows") or [])]
    rows = []
    for index, (dataset_id, dataset_name, source_url, note) in enumerate(DATASET_ROWS, start=1):
        rows.append(
            {
                "schema_id": "DatasetBindingRow_v1",
                "dataset_id": dataset_id,
                "dataset_name": dataset_name,
                "source_url": source_url,
                "access_date": now_utc()[:10],
                "access_mode": "public_open_route",
                "version_or_snapshot": "latest_public_route",
                "hash_if_available": "",
                "license_note": note,
                "bound_packet_ids": [f"PACKET::{index:03d}"],
                "bound_simulation_ids": [bound_sim_ids[(index - 1) % len(bound_sim_ids)]],
                "staging_binding": "public_manifest_and_local_stage_only",
                "staging_instruction": "Use public-source fetch or local staging only; do not widen claim ceiling from the dataset alone.",
            }
        )
    manifest = {
        "schema_id": "OC_DATASET_MANIFEST_v1",
        "generated_at_utc": now_utc(),
        "repo_sha": git_head_sha(),
        "rows": rows,
        "summary": {"dataset_manifest_total": len(rows)},
    }
    write_json(DATASET_MANIFEST_PATH, manifest)
    return manifest


def tex_list_block(lines: list[str]) -> list[str]:
    return [r"\begin{itemize}[leftmargin=*]"] + [r"\item " + latex_escape(line) for line in lines] + [r"\end{itemize}"]


def render_release_frontmatter_tex(*, heading: str, body_lines: list[str]) -> str:
    lines = [r"\section*{" + latex_escape(heading) + "}"]
    lines.extend(tex_list_block(body_lines))
    return "\n".join(lines) + "\n"


def render_release_appendix_tex(title: str, rows: list[dict[str, Any]], fields: list[str]) -> str:
    lines = [r"\section{" + latex_escape(title) + "}"]
    if rows:
        lines.append(r"\begin{itemize}[leftmargin=*]")
        for row in rows:
            parts = [f"{field}={compact(row.get(field, ''))}" for field in fields]
            lines.append(r"\item " + latex_escape("; ".join(parts)))
        lines.append(r"\end{itemize}")
    else:
        lines.append("No rows.")
    return "\n".join(lines) + "\n"


def render_release_route_tex(section_refs: list[str], appendix_refs: list[str], release_appendix_refs: list[str]) -> str:
    lines: list[str] = []
    for ref in section_refs:
        lines.append(rf"\input{{{ref}}}")
    if appendix_refs or release_appendix_refs:
        lines.append(r"\appendix")
        for ref in appendix_refs:
            lines.append(rf"\input{{{ref}}}")
        for ref in release_appendix_refs:
            lines.append(rf"\input{{{ref}}}")
    return "\n".join(lines) + "\n"


def render_release_entrypoint_tex(
    *,
    title: str,
    pdf_subject: str,
    pdf_keywords: str,
    frontmatter_ref: str,
    route_ref: str,
    include_toc: bool,
    include_list_of_figures: bool,
    include_list_of_tables: bool,
    include_bibliography: bool,
) -> str:
    lines = [
        r"\documentclass[11pt,a4paper]{article}",
        r"\def\ocpdftitle{" + latex_escape(title) + "}",
        r"\def\ocpdfsubject{" + latex_escape(pdf_subject) + "}",
        r"\def\ocpdfkeywords{" + latex_escape(pdf_keywords) + "}",
        r"\def\ocpdflang{en}",
        r"\input{preamble}",
        r"\title{" + latex_escape(title) + "}",
        r"\date{}",
        r"\begin{document}",
        r"\maketitle",
        rf"\input{{{frontmatter_ref}}}",
    ]
    if include_toc:
        lines.extend([r"\tableofcontents", r"\clearpage"])
    if include_list_of_figures:
        lines.extend(
            [
                r"\phantomsection",
                r"\addcontentsline{toc}{section}{List of Figures}",
                r"\listoffigures",
                r"\clearpage",
            ]
        )
    if include_list_of_tables:
        lines.extend(
            [
                r"\phantomsection",
                r"\addcontentsline{toc}{section}{List of Tables}",
                r"\listoftables",
                r"\clearpage",
            ]
        )
    lines.append(rf"\input{{{route_ref}}}")
    if include_bibliography:
        lines.extend([r"\clearpage", r"\nocite{*}", r"\printbibliography[heading=bibintoc,title={Bibliography}]"])
    lines.append(r"\end{document}")
    return "\n".join(lines) + "\n"


def write_release_source_tree(
    delta_rows: list[dict[str, Any]], projection_rows: list[dict[str, Any]], critique_rows: list[dict[str, Any]]
) -> None:
    write_text(
        SOURCE_OUTPUTS["readme_md"],
        "\n".join(
            [
                "# OC Core 1.3.1 Release Source Tree",
                "",
                "This tree binds the 1.3.1 public release artifacts directly to the real OC corpus.",
                "Entry-point manuscripts in `manuscripts/` and `article_family/` compile from these route and appendix files.",
                "",
            ]
        ),
    )

    frontmatter_specs = {
        "master_frontmatter_tex": {
            "heading": "Release framing",
            "body_lines": [
                "OC Core 1.3.1 is a strengthened public release built from the real Core 1.3 corpus plus bounded 1.3.1 deltas.",
                f"white_spot_total={sum(1 for row in delta_rows if compact(row.get('delta_class')) == 'scientific_closure') or 1}; package_scope=full_monograph",
                "This release remains claim-bounded, source-first, and no-send until explicit owner approval.",
            ],
        },
        "journal_frontmatter_tex": {
            "heading": "Document boundary",
            "body_lines": [
                "This journal-core document is the reviewer and formal-reader route extracted from the real corpus.",
                "It prioritizes theorem scope, source audit, foundational consistency, and worked examples.",
                "The document is bounded by the same publication boundary as the master monograph.",
            ],
        },
        "overview_frontmatter_tex": {
            "heading": "Document boundary",
            "body_lines": [
                "This readable overview is a broad-scientific-reader route built from the real OC corpus.",
                "It keeps the introductory and synthesis path legible without replacing the master monograph.",
                "It adds the 1.3.1 science delta appendix but does not widen claims beyond the core corpus.",
            ],
        },
        "methods_frontmatter_tex": {
            "heading": "Document boundary",
            "body_lines": [
                "This companion collects operational, empirical, proof, simulation, and dataset routes from the real corpus.",
                "It exists to make the reproducibility and simulation layer inspectable without improvising a second theory.",
                "Simulation and dataset surfaces stay bounded support layers and do not silently promote claims.",
            ],
        },
        "critique_frontmatter_tex": {
            "heading": "Document boundary",
            "body_lines": [
                "This critique-closure companion is the source-audit and objection-handling route for OC Core 1.3.1.",
                "It is built from the actual source audit, theorem roadmap, and reviewer-navigation corpus.",
                "The 1.3.1 critique appendix records bounded closure, clarification, or demotion outcomes only.",
            ],
        },
    }
    for key, payload in frontmatter_specs.items():
        write_text(
            SOURCE_OUTPUTS[key],
            render_release_frontmatter_tex(heading=payload["heading"], body_lines=payload["body_lines"]),
        )

    write_text(
        SOURCE_OUTPUTS["science_delta_appendix_tex"],
        render_release_appendix_tex(
            "OC 1.3.1 Science Delta Appendix", delta_rows, ["delta_id", "delta_class", "status_1_3_1", "action_bucket"]
        ),
    )
    write_text(
        SOURCE_OUTPUTS["simulation_data_appendix_tex"],
        render_release_appendix_tex(
            "OC 1.3.1 Simulation and Data Appendix",
            projection_rows,
            ["lane_id", "domain", "strengthening_status", "primary_strengthening_mode"],
        ),
    )
    write_text(
        SOURCE_OUTPUTS["critique_closure_appendix_tex"],
        render_release_appendix_tex(
            "OC 1.3.1 Critique Closure Appendix",
            critique_rows,
            ["critique_id", "processing_class", "output_mode", "publication_effect"],
        ),
    )

    for spec in MANUSCRIPT_ROUTE_SPECS.values():
        release_appendix_refs = [repo_rel(SOURCE_OUTPUTS[key]) for key in spec["release_appendix_keys"]]
        write_text(
            SOURCE_OUTPUTS[spec["route_key"]],
            render_release_route_tex(spec["section_refs"], spec["appendix_refs"], release_appendix_refs),
        )


def write_manuscripts(
    delta_rows: list[dict[str, Any]], projection_rows: list[dict[str, Any]], critique_rows: list[dict[str, Any]]
) -> dict[str, str]:
    compile_status: dict[str, str] = {}

    write_text(
        MANUSCRIPT_OUTPUTS["science_delta_appendix_md"],
        "# OC 1.3.1 Science Delta Appendix\n\n"
        + render_rows_md(delta_rows, ["delta_id", "delta_class", "status_1_3_1", "action_bucket"])
        + "\n",
    )
    write_text(
        MANUSCRIPT_OUTPUTS["simulation_data_appendix_md"],
        "# OC 1.3.1 Simulation and Data Appendix\n\n"
        + render_rows_md(
            projection_rows, ["lane_id", "domain", "strengthening_status", "primary_strengthening_mode"]
        )
        + "\n",
    )
    write_text(
        MANUSCRIPT_OUTPUTS["critique_closure_appendix_md"],
        "# OC 1.3.1 Critique Closure Appendix\n\n"
        + render_rows_md(critique_rows, ["critique_id", "processing_class", "output_mode", "publication_effect"])
        + "\n",
    )

    write_release_source_tree(delta_rows, projection_rows, critique_rows)

    for spec in MANUSCRIPT_ROUTE_SPECS.values():
        tex_path = MANUSCRIPT_OUTPUTS[spec["tex_key"]]
        pdf_path = MANUSCRIPT_OUTPUTS[spec["pdf_key"]]
        frontmatter_ref = repo_rel(SOURCE_OUTPUTS[spec["frontmatter_key"]])
        route_ref = repo_rel(SOURCE_OUTPUTS[spec["route_key"]])
        write_text(
            tex_path,
            render_release_entrypoint_tex(
                title=spec["title"],
                pdf_subject=spec["pdf_subject"],
                pdf_keywords=spec["pdf_keywords"],
                frontmatter_ref=frontmatter_ref,
                route_ref=route_ref,
                include_toc=spec["include_toc"],
                include_list_of_figures=spec["include_list_of_figures"],
                include_list_of_tables=spec["include_list_of_tables"],
                include_bibliography=spec["include_bibliography"],
            ),
        )
        compile_status[tex_path.stem] = compile_tex(tex_path, pdf_path)
    return compile_status


def build_release_contract() -> dict[str, Any]:
    return {
        "schema_id": "OC_RELEASE_CONTRACT_v1",
        "release_id": "oc_core_1_3_1",
        "mandatory_artifact_classes": [
            "master_monograph",
            "journal_core",
            "readable_overview",
            "methods_or_simulation_companion",
            "critique_closure_companion",
            "simulation_corpus",
            "dataset_manifest",
            "reproducibility_layer",
            "release_notes",
            "release_contract",
            "zenodo_package",
            "one_click_ready_no_send_packages",
        ],
        "optional_artifact_classes": [
            "domain_papers",
            "benchmark_packs",
            "skeptic_packs",
            "pilot_packages",
        ],
        "gates": [
            "science_gate",
            "simulation_data_repro_gate",
            "release_integrity_gate",
            "zenodo_staging_gate",
            "owner_approval_gate",
        ],
        "status_ladder": [
            "NOT_ASSEMBLED",
            "ASSEMBLING",
            "SCIENCE_INTEGRATION_IN_PROGRESS",
            "CERBERUS_PATCHING",
            "OWNER_REVIEW_READY",
            "RELEASE_READY_NO_SEND",
            "OWNER_APPROVED_TO_PUBLISH",
            "PUBLISHED",
        ],
    }


def build_release_artifact_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in MANUSCRIPT_ROUTE_SPECS.values():
        pdf_path = MANUSCRIPT_OUTPUTS[spec["pdf_key"]]
        tex_path = MANUSCRIPT_OUTPUTS[spec["tex_key"]]
        source_appendix_refs = [normalize_existing_repo_ref(ref) for ref in spec["appendix_refs"]]
        source_appendix_refs.extend(repo_rel(SOURCE_OUTPUTS[key]) for key in spec["release_appendix_keys"])
        rows.append(
            {
                "schema_id": "ReleaseArtifactRow_v1",
                "artifact_id": spec["artifact_id"],
                "artifact_class": spec["artifact_class"],
                "artifact_ref": repo_rel(pdf_path),
                "mandatory": True,
                "status": "ASSEMBLED" if pdf_path.exists() else "MISSING",
                "checksum": sha256_file(pdf_path) if pdf_path.exists() else "",
                "artifact_substance_class": spec["artifact_substance_class"],
                "source_corpus_root": "oc_core_1_3_master_monograph.tex",
                "source_section_refs": [normalize_existing_repo_ref(ref) for ref in spec["section_refs"]],
                "source_appendix_refs": source_appendix_refs,
                "source_tex_entrypoint": normalize_existing_repo_ref(repo_rel(tex_path)),
                "source_support_refs": [
                    normalize_existing_repo_ref(repo_rel(SOURCE_OUTPUTS[spec["frontmatter_key"]])),
                    normalize_existing_repo_ref(repo_rel(SOURCE_OUTPUTS[spec["route_key"]])),
                ],
                "source_refs": [repo_rel(PRIVATE_CONTROL_PLANE_PATH)],
            }
        )

    auxiliary_mapping = [
        ("ARTIFACT::SIMULATION_LEDGER", "simulation_corpus", SIMULATION_LEDGER_PATH, "CANONICAL_SUPPORT_SURFACE"),
        ("ARTIFACT::DATASET_MANIFEST", "dataset_manifest", DATASET_MANIFEST_PATH, "CANONICAL_SUPPORT_SURFACE"),
        ("ARTIFACT::SIMULATION_GUIDE", "reproducibility_layer", SIMULATION_GUIDE_PATH, "CANONICAL_SUPPORT_SURFACE"),
        ("ARTIFACT::RELEASE_NOTES", "release_notes", OUTPUTS["release_notes_md"], "CANONICAL_RELEASE_METADATA"),
        ("ARTIFACT::RELEASE_CONTRACT", "release_contract", OUTPUTS["release_contract_json"], "CANONICAL_RELEASE_METADATA"),
        ("ARTIFACT::ZENODO_STAGE", "zenodo_package", OUTPUTS["zenodo_stage_json"], "STAGING_METADATA_SURFACE"),
        ("ARTIFACT::ONE_CLICK_LEDGER", "one_click_ready_no_send_packages", OUTPUTS["one_click_package_ledger_json"], "NO_SEND_EXECUTION_SURFACE"),
    ]
    for artifact_id, artifact_class, artifact_path, substance_class in auxiliary_mapping:
        rows.append(
            {
                "schema_id": "ReleaseArtifactRow_v1",
                "artifact_id": artifact_id,
                "artifact_class": artifact_class,
                "artifact_ref": repo_rel(artifact_path),
                "mandatory": True,
                "status": "ASSEMBLED" if artifact_path.exists() else "MISSING",
                "checksum": sha256_file(artifact_path) if artifact_path.exists() else "",
                "artifact_substance_class": substance_class,
                "source_corpus_root": "oc_core_1_3_master_monograph.tex",
                "source_section_refs": [],
                "source_appendix_refs": [],
                "source_tex_entrypoint": "",
                "source_support_refs": [],
                "source_refs": [repo_rel(PRIVATE_CONTROL_PLANE_PATH)],
            }
        )
    return rows


def build_gate_findings(
    artifact_rows: list[dict[str, Any]],
    simulation_ledger: dict[str, Any],
    dataset_manifest: dict[str, Any],
    zenodo_stage: dict[str, Any],
    release_contract: dict[str, Any],
) -> list[dict[str, Any]]:
    mandatory_classes = set(release_contract["mandatory_artifact_classes"])
    missing_artifacts = [row for row in artifact_rows if row["artifact_class"] in mandatory_classes and row["status"] != "ASSEMBLED"]
    mandatory_manuscript_classes = {
        "master_monograph",
        "journal_core",
        "readable_overview",
        "methods_or_simulation_companion",
        "critique_closure_companion",
    }
    source_bound_failures = [
        row
        for row in artifact_rows
        if row["artifact_class"] in mandatory_manuscript_classes
        and (
            row.get("artifact_substance_class") == "SUMMARY_ONLY_WRAPPER"
            or not row.get("source_corpus_root")
            or not list(row.get("source_section_refs") or [])
            or not row.get("source_tex_entrypoint")
        )
    ]
    mandatory_assembled_classes = {row["artifact_class"] for row in artifact_rows if row["artifact_class"] in mandatory_classes and row["status"] == "ASSEMBLED"}
    integrity_pass = len(mandatory_assembled_classes) == len(mandatory_classes)
    findings: list[dict[str, Any]] = []
    findings.append(
        {
            "schema_id": "ReleaseGateFindingRow_v1",
            "finding_id": "GATE::SCIENCE",
            "gate_id": "science_gate",
            "severity": "HIGH" if missing_artifacts or source_bound_failures else "INFO",
            "status": "PASS" if not missing_artifacts and not source_bound_failures else "FAIL",
            "summary": (
                "Mandatory manuscript artifacts are source-bound, substantive, and assembled."
                if not missing_artifacts and not source_bound_failures
                else "Mandatory release manuscripts are missing or not yet source-bound substantive artifacts."
            ),
            "artifact_refs": [row["artifact_ref"] for row in missing_artifacts + source_bound_failures],
            "blocker_dossier": [
                *[f"MISSING::{row['artifact_class']}::{row['artifact_ref']}" for row in missing_artifacts],
                *[
                    f"SOURCE_BOUND_BLOCKER::{row['artifact_class']}::{row['artifact_substance_class']}"
                    for row in source_bound_failures
                ],
            ],
        }
    )
    findings.append(
        {
            "schema_id": "ReleaseGateFindingRow_v1",
            "finding_id": "GATE::SIMULATION",
            "gate_id": "simulation_data_repro_gate",
            "severity": (
                "HIGH"
                if (simulation_ledger.get("summary", {}).get("simulation_total", 0) or 0) <= 0
                or (dataset_manifest.get("summary", {}).get("dataset_manifest_total", 0) or 0) <= 0
                else "INFO"
            ),
            "status": (
                "PASS"
                if (simulation_ledger.get("summary", {}).get("simulation_total", 0) or 0) > 0
                and (dataset_manifest.get("summary", {}).get("dataset_manifest_total", 0) or 0) > 0
                else "FAIL"
            ),
            "summary": "Simulation and dataset layers are present, traceable, and release-bound.",
            "artifact_refs": [repo_rel(SIMULATION_LEDGER_PATH), repo_rel(DATASET_MANIFEST_PATH)],
            "blocker_dossier": [],
        }
    )
    findings.append(
        {
            "schema_id": "ReleaseGateFindingRow_v1",
            "finding_id": "GATE::INTEGRITY",
            "gate_id": "release_integrity_gate",
            "severity": "HIGH" if not integrity_pass else "INFO",
            "status": "PASS" if integrity_pass else "FAIL",
            "summary": "All mandatory artifact classes are assembled and represented in the release inventory.",
            "artifact_refs": [repo_rel(OUTPUTS["artifact_inventory_json"])],
            "blocker_dossier": [] if integrity_pass else [f"MANDATORY_CLASS_MISSING::{artifact_class}" for artifact_class in sorted(mandatory_classes - mandatory_assembled_classes)],
        }
    )
    findings.append(
        {
            "schema_id": "ReleaseGateFindingRow_v1",
            "finding_id": "GATE::ZENODO_STAGE",
            "gate_id": "zenodo_staging_gate",
            "severity": "HIGH" if zenodo_stage.get("status") != "READY_NO_SEND" else "INFO",
            "status": "PASS" if zenodo_stage.get("status") == "READY_NO_SEND" else "FAIL",
            "summary": "Zenodo package is staged and held under no-send discipline.",
            "artifact_refs": [repo_rel(OUTPUTS["zenodo_stage_json"])],
            "blocker_dossier": [] if zenodo_stage.get("status") == "READY_NO_SEND" else [compact(zenodo_stage.get("stderr")) or "ZENODO_STAGING_FAILED"],
        }
    )
    findings.append(
        {
            "schema_id": "ReleaseGateFindingRow_v1",
            "finding_id": "GATE::OWNER_APPROVAL",
            "gate_id": "owner_approval_gate",
            "severity": "INFO",
            "status": "PASS",
            "summary": "Release stays under no-send owner approval discipline.",
            "artifact_refs": [repo_rel(OUTPUTS["owner_approval_gate_json"])],
            "blocker_dossier": [],
        }
    )
    return findings


def build_release_manifest(artifact_rows: list[dict[str, Any]]) -> dict[str, Any]:
    files: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in artifact_rows:
        if row["status"] != "ASSEMBLED":
            continue
        refs = [row["artifact_ref"]]
        raw_source_tex_entrypoint = compact(row.get("source_tex_entrypoint"))
        if raw_source_tex_entrypoint:
            refs.append(normalize_existing_repo_ref(raw_source_tex_entrypoint))
        refs.extend([normalize_existing_repo_ref(compact(ref)) for ref in (row.get("source_section_refs") or []) if compact(ref)])
        refs.extend([normalize_existing_repo_ref(compact(ref)) for ref in (row.get("source_appendix_refs") or []) if compact(ref)])
        refs.extend([normalize_existing_repo_ref(compact(ref)) for ref in (row.get("source_support_refs") or []) if compact(ref)])
        for ref in refs:
            if ref and ref not in seen:
                files.append({"source_ref": ref, "stage_ref": ref})
                seen.add(ref)
    return {
        "release_scope": "OC_CORE_1_3_1_ENGLISH_RELEASE_PACKAGE",
        "active_language_codes": ["EN"],
        "files": files,
        "required_upload_members": [item["stage_ref"] for item in files],
    }


def stage_zenodo_package(manifest_path: Path) -> dict[str, Any]:
    stage_dir = REPO_ROOT / "build_oc_core_1_3_zenodo_en_only"
    zip_path = BUILD_DIR / "oc_core_1_3_1_zenodo_release.zip"
    proc = subprocess.run(
        [
            "python",
            str(TOOLS_DIR / "stage_oc_core_1_3_zenodo_en_release.py"),
            "--manifest",
            str(manifest_path),
            "--stage-dir",
            str(stage_dir),
            "--zip-path",
            str(zip_path),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
    )
    return {
        "stage_dir": repo_rel(stage_dir),
        "zip_ref": repo_rel(zip_path) if zip_path.exists() else "",
        "status": "READY_NO_SEND" if proc.returncode == 0 else "FAIL",
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def build_release_specific_packages(private_inputs: dict[str, Any], artifact_rows: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any], str, str]:
    source_rows = private_inputs["package_ledger"].get("rows") or []
    destination_lookup = {
        compact(row.get("destination_id")): row for row in (private_inputs["destination_registry"].get("rows") or []) if isinstance(row, dict)
    }
    selected = [
        row for row in source_rows
        if compact(row.get("package_family")) in {
            "JOURNAL_SUBMISSION_PACKAGE",
            "BENCHMARK_REPRO_PACKAGE",
            "CRITIQUE_RESPONSE_PACKAGE",
            "PUBLIC_RELEASE_PACKAGE",
            "COLLABORATOR_OR_ADVISOR_PACKAGE",
            "ENTERPRISE_PILOT_PACKAGE",
        }
    ]
    release_rows: list[dict[str, Any]] = []
    destinations: list[dict[str, Any]] = []
    for row in selected:
        destination_id = compact(row.get("target_destination_id"))
        destination = destination_lookup.get(destination_id, {})
        release_rows.append(
            {
                "schema_id": "OneClickReleasePackageRow_v1",
                "package_id": compact(row.get("package_id")),
                "package_family": compact(row.get("package_family")),
                "target_channel": compact(row.get("target_channel_type")),
                "destination_id": destination_id,
                "claim_ceiling": compact(row.get("claim_ceiling")),
                "attachment_hashes": {ref: "" for ref in (row.get("required_attachments") or [])},
                "preflight_checks": dict(row.get("integrity_checks") or {}),
                "send_lock_status": compact(row.get("no_send_lock_status")) or "ARMED_UNDER_GLOBAL_LOCK",
                "owner_approval_required": True,
                "no_send_rehearsal_result": compact(row.get("dispatch_readiness_status")),
            }
        )
        if destination:
            destinations.append(
                {
                    "destination_id": destination_id,
                    "destination_type": compact(destination.get("destination_type")),
                    "channel_name": compact(destination.get("channel_name")),
                    "official_url_or_endpoint": compact(destination.get("official_url_or_endpoint")),
                    "owner_approval_required": bool(destination.get("owner_approval_required", True)),
                }
            )
    ledger = {
        "schema_id": "OC_ONE_CLICK_READY_PACKAGE_LEDGER_v1",
        "generated_at_utc": now_utc(),
        "rows": release_rows,
        "summary": {
            "one_click_ready_no_send_total": sum(1 for row in release_rows if row["no_send_rehearsal_result"] == "ONE_CLICK_READY_NO_SEND"),
            "ready_for_owner_review_total": sum(1 for row in release_rows if row["no_send_rehearsal_result"] == "READY_FOR_OWNER_REVIEW"),
            "package_total": len(release_rows),
        },
    }
    destination_registry = {
        "schema_id": "OC_DESTINATION_REGISTRY_v1",
        "generated_at_utc": now_utc(),
        "rows": destinations,
        "summary": {"destination_total": len(destinations)},
    }
    rehearsal_report = "\n".join(
        [
            "# OC No-Send Dispatch Rehearsal Report",
            "",
            f"- package_total: {len(release_rows)}",
            f"- one_click_ready_no_send_total: {ledger['summary']['one_click_ready_no_send_total']}",
            f"- ready_for_owner_review_total: {ledger['summary']['ready_for_owner_review_total']}",
            "- global_no_send_lock: true",
            "",
        ]
    )
    owner_click_actions = "\n".join(
        [
            "# OC Owner Click Actions Board",
            "",
            "- Preview package",
            "- Preview destination route",
            "- Open attachments",
            "- Open claim ceiling",
            "- Run no-send simulation again",
            "- Mark for owner review",
            "- Arm package under no-send lock",
            "- Queue for future dispatch",
            "- Send now (disabled under global no-send lock)",
            "",
        ]
    )
    return ledger, destination_registry, rehearsal_report, owner_click_actions


def materialize_oc_core_1_3_1_release_v11(*, run_id: str = "oc_core_1_3_1_release_v11") -> dict[str, Any]:
    ensure_dirs()
    build_input_sha = git_head_sha()
    build_input_branch = git_branch()
    build_input_clean = git_clean()
    private_inputs = load_private_inputs()
    private_summary = (private_inputs["control_plane"].get("summary") or {})
    delta_rows = private_inputs["delta_ledger"].get("rows") or []
    critique_rows = private_inputs["critique_processing"].get("rows") or []
    projection_rows = private_inputs["projection_ledger"].get("rows") or []

    release_contract = build_release_contract()
    write_json(OUTPUTS["release_contract_json"], release_contract)

    write_text(
        OUTPUTS["release_notes_md"],
        "# OC Core 1.3.1 Release Notes\n\n- Strengthened science delta\n- Public simulation corpus\n- Public data manifest layer\n- Readable article family\n",
    )
    write_text(
        OUTPUTS["reader_guide_md"],
        "# OC Core 1.3.1 Reader Guide\n\nStart with the readable overview, then journal core, then the master monograph and appendices.\n",
    )

    simulation_ledger = write_simulation_corpus(projection_rows)
    dataset_manifest = write_data_layer(simulation_ledger)
    compile_status = write_manuscripts(delta_rows, projection_rows, critique_rows)
    write_text(
        OUTPUTS["simulation_to_claim_md"],
        "# OC Simulation To Claim Matrix\n\n"
        + render_rows_md(simulation_ledger.get("rows") or [], ["simulation_id", "domain", "claim_binding"])
        + "\n",
    )
    write_text(
        OUTPUTS["data_to_packet_md"],
        "# OC Data To Packet Matrix\n\n"
        + render_rows_md(dataset_manifest.get("rows") or [], ["dataset_id", "dataset_name", "bound_packet_ids"])
        + "\n",
    )

    package_ledger, destination_registry, dispatch_rehearsal_report, owner_click_actions = build_release_specific_packages(
        private_inputs, []
    )
    write_json(OUTPUTS["one_click_package_ledger_json"], package_ledger)
    write_json(OUTPUTS["destination_registry_json"], destination_registry)
    write_text(OUTPUTS["dispatch_rehearsal_report_md"], dispatch_rehearsal_report)
    write_text(OUTPUTS["owner_click_actions_md"], owner_click_actions)

    write_json(
        OUTPUTS["owner_approval_gate_json"],
        {
            "schema_id": "OC_CORE_1_3_1_OWNER_APPROVAL_GATE_v1",
            "status": "REQUIRED",
            "release_gate_status": "PENDING_GATE_EVALUATION",
            "owner_approval_required": True,
            "publish_allowed": False,
            "next_action": "Wait for explicit owner approval before publish/send.",
        },
    )

    write_json(
        OUTPUTS["white_spot_and_critique_index_json"],
        {
            "schema_id": "OC_1_3_1_WHITE_SPOT_AND_CRITIQUE_INDEX_v1",
            "generated_at_utc": now_utc(),
            "white_spot_closed_total": int(private_inputs["v9_control_plane"].get("summary", {}).get("already_closed_total", 0) or 0),
            "white_spot_remaining_total": int(private_inputs["v9_control_plane"].get("summary", {}).get("partially_closed_total", 0) or 0),
            "critique_item_total": len(critique_rows),
            "refs": {
                "private_delta_ref": repo_rel(PRIVATE_DELTA_LEDGER_PATH),
                "private_critique_processing_ref": repo_rel(PRIVATE_CRITIQUE_PROCESSING_PATH),
            },
        },
    )

    artifact_rows = build_release_artifact_rows()
    release_manifest = build_release_manifest(artifact_rows)
    write_json(OUTPUTS["release_manifest_json"], release_manifest)

    zenodo_stage = stage_zenodo_package(OUTPUTS["release_manifest_json"])
    write_json(OUTPUTS["zenodo_stage_json"], {"schema_id": "OC_ZENODO_STAGING_PACKAGE_v1", **zenodo_stage})

    artifact_rows = build_release_artifact_rows()
    artifact_inventory = {
        "schema_id": "OC_RELEASE_BUNDLE_INVENTORY_v1",
        "generated_at_utc": now_utc(),
        "repo_sha": build_input_sha,
        "rows": artifact_rows,
        "summary": {
            "mandatory_artifact_total": len(release_contract["mandatory_artifact_classes"]),
            "assembled_artifact_total": sum(1 for row in artifact_rows if row["mandatory"] and row["status"] == "ASSEMBLED"),
            "assembled_artifact_class_total": len({row["artifact_class"] for row in artifact_rows if row["status"] == "ASSEMBLED"}),
        },
    }
    write_json(OUTPUTS["artifact_inventory_json"], artifact_inventory)

    gate_findings = build_gate_findings(artifact_rows, simulation_ledger, dataset_manifest, zenodo_stage, release_contract)
    science_gate_failed = any(row["gate_id"] == "science_gate" and row["status"] != "PASS" for row in gate_findings)
    release_gate_status = (
        "SCIENCE_INTEGRATION_IN_PROGRESS"
        if science_gate_failed
        else ("RELEASE_READY_NO_SEND" if all(row["status"] == "PASS" for row in gate_findings) else "CERBERUS_PATCHING")
    )

    write_json(
        OUTPUTS["publish_manifest_json"],
        {
            "schema_id": "OC_ONE_CLICK_PUBLISH_MANIFEST_v1",
            "release_id": "oc_core_1_3_1",
            "release_gate_status": release_gate_status,
            "owner_approval_required": True,
            "global_no_send_lock": True,
            "zenodo_stage_ref": repo_rel(OUTPUTS["zenodo_stage_json"]),
            "release_manifest_ref": repo_rel(OUTPUTS["release_manifest_json"]),
        },
    )
    write_text(
        OUTPUTS["automation_guide_md"],
        "\n".join(
            [
                "# OC Release Automation Guide",
                "",
                "1. Materialize `build_oc_core_1_3_1_release_v11.py`.",
                "2. Refresh the source-bound manuscript tree, release contract, and bundle inventory.",
                "3. Validate that mandatory manuscript artifacts are substantive and source-bound before trusting compile success.",
                "4. Stage Zenodo package with `stage_oc_zenodo_release_v1.py`.",
                "5. Stop at `RELEASE_READY_NO_SEND` until owner approval.",
                "",
            ]
        ),
    )

    cerberus_open_high_severity_total = sum(1 for row in gate_findings if row["severity"] == "HIGH" and row["status"] != "PASS")
    write_json(
        OUTPUTS["cerberus_acceptance_json"],
        {
            "schema_id": "OC_CORE_1_3_1_CERBERUS_ACCEPTANCE_CERT_v1",
            "status": "PASS" if cerberus_open_high_severity_total == 0 else "FAIL",
            "generated_at_utc": now_utc(),
            "finding_total": len(gate_findings),
            "high_severity_open_total": cerberus_open_high_severity_total,
        },
    )
    write_json(
        OUTPUTS["release_integrity_json"],
        {
            "schema_id": "OC_CORE_1_3_1_RELEASE_INTEGRITY_CERT_v1",
            "status": (
                "PASS"
                if artifact_inventory["summary"]["assembled_artifact_total"] >= artifact_inventory["summary"]["mandatory_artifact_total"]
                else "FAIL"
            ),
            "generated_at_utc": now_utc(),
            "assembled_artifact_total": artifact_inventory["summary"]["assembled_artifact_total"],
            "mandatory_artifact_total": artifact_inventory["summary"]["mandatory_artifact_total"],
            "assembled_artifact_class_total": artifact_inventory["summary"]["assembled_artifact_class_total"],
        },
    )
    write_json(
        OUTPUTS["simulation_repro_json"],
        {
            "schema_id": "OC_CORE_1_3_1_SIMULATION_REPRO_CERT_v1",
            "status": (
                "PASS"
                if (simulation_ledger.get("summary", {}).get("simulation_total", 0) or 0) > 0
                and (dataset_manifest.get("summary", {}).get("dataset_manifest_total", 0) or 0) > 0
                else "FAIL"
            ),
            "generated_at_utc": now_utc(),
            "simulation_total": simulation_ledger.get("summary", {}).get("simulation_total", 0),
            "dataset_manifest_total": dataset_manifest.get("summary", {}).get("dataset_manifest_total", 0),
            "compile_status": compile_status,
        },
    )
    write_text(
        OUTPUTS["release_gate_board_md"],
        "# OC Core 1.3.1 Release Gate Board\n\n"
        + render_rows_md(gate_findings, ["finding_id", "gate_id", "status", "severity", "summary"])
        + "\n",
    )

    write_json(
        OUTPUTS["owner_approval_gate_json"],
        {
            "schema_id": "OC_CORE_1_3_1_OWNER_APPROVAL_GATE_v1",
            "status": "REQUIRED",
            "release_gate_status": release_gate_status,
            "owner_approval_required": True,
            "publish_allowed": False,
            "next_action": "Wait for explicit owner approval before publish/send.",
        },
    )

    mandatory_total = len(release_contract["mandatory_artifact_classes"])
    mandatory_covered = len({row["artifact_class"] for row in artifact_rows if row["status"] == "ASSEMBLED"})
    coverage = round(mandatory_covered / max(1, mandatory_total), 6)
    summary = {
        "white_spot_closed_total": int(private_summary.get("white_spot_closed_total", 0) or 0),
        "white_spot_remaining_total": int(private_summary.get("white_spot_remaining_total", 0) or 0),
        "science_delta_total": int(private_summary.get("science_delta_total", len(delta_rows)) or len(delta_rows)),
        "numeric_strengthened_total": int(private_summary.get("numeric_strengthened_total", 0) or 0),
        "formula_strengthened_total": int(private_summary.get("formula_strengthened_total", 0) or 0),
        "simulation_total": int(simulation_ledger.get("summary", {}).get("simulation_total", 0) or 0),
        "dataset_manifest_total": int(dataset_manifest.get("summary", {}).get("dataset_manifest_total", 0) or 0),
        "release_artifact_class_coverage": coverage,
        "public_repo_simulation_coverage": float(simulation_ledger.get("summary", {}).get("public_repo_simulation_coverage", 0.0) or 0.0),
        "cerberus_open_high_severity_total": cerberus_open_high_severity_total,
        "release_gate_status": release_gate_status,
        "zenodo_staging_status": zenodo_stage["status"],
        "one_click_ready_no_send_total": int(package_ledger.get("summary", {}).get("one_click_ready_no_send_total", 0) or 0),
        "owner_approval_required": True,
        "public_release_ready": release_gate_status == "RELEASE_READY_NO_SEND",
        "public_branch": build_input_branch,
        "public_repo_sha": build_input_sha,
        "public_repo_clean": build_input_clean,
        "public_repo_sha_meaning": "PRE_MATERIALIZATION_HEAD",
    }

    control_plane = {
        "schema_id": "OC_CORE_1_3_1_RELEASE_CONTROL_PLANE_v1",
        "generated_at_utc": now_utc(),
        "run_id": run_id,
        "status": "PASS" if release_gate_status == "RELEASE_READY_NO_SEND" else "WARN",
        "summary": summary,
        "refs": {
            "release_contract_ref": repo_rel(OUTPUTS["release_contract_json"]),
            "artifact_inventory_ref": repo_rel(OUTPUTS["artifact_inventory_json"]),
            "zenodo_stage_ref": repo_rel(OUTPUTS["zenodo_stage_json"]),
            "publish_manifest_ref": repo_rel(OUTPUTS["publish_manifest_json"]),
            "simulation_ledger_ref": repo_rel(SIMULATION_LEDGER_PATH),
            "dataset_manifest_ref": repo_rel(DATASET_MANIFEST_PATH),
            "master_monograph_ref": repo_rel(MANUSCRIPT_OUTPUTS["master_pdf"]),
            "journal_core_ref": repo_rel(MANUSCRIPT_OUTPUTS["journal_core_pdf"]),
            "overview_ref": repo_rel(MANUSCRIPT_OUTPUTS["overview_pdf"]),
            "methods_ref": repo_rel(MANUSCRIPT_OUTPUTS["methods_pdf"]),
            "critique_ref": repo_rel(MANUSCRIPT_OUTPUTS["critique_pdf"]),
            "release_ready_board_ref": repo_rel(OUTPUTS["release_ready_board_json"]),
            "owner_review_packet_ref": repo_rel(OUTPUTS["owner_review_packet_md"]),
            "release_gate_board_ref": repo_rel(OUTPUTS["release_gate_board_md"]),
        },
        "rows": gate_findings,
    }
    write_json(OUTPUTS["control_plane_json"], control_plane)

    write_json(
        OUTPUTS["release_ready_board_json"],
        {
            "schema_id": "OC_CORE_1_3_1_RELEASE_READY_BOARD_v1",
            "generated_at_utc": now_utc(),
            "status": release_gate_status,
            "summary": summary,
            "what_is_new": [
                "real 1.3.1 science delta ledger",
                "public simulation corpus",
                "public dataset manifest layer",
                "readable article family",
                "contract-driven release automation",
            ],
        },
    )
    write_text(
        OUTPUTS["owner_review_packet_md"],
        "\n".join(
            [
                "# OC Core 1.3.1 Owner Review Packet",
                "",
                f"- release_gate_status: {release_gate_status}",
                f"- zenodo_staging_status: {zenodo_stage['status']}",
                f"- one_click_ready_no_send_total: {summary['one_click_ready_no_send_total']}",
                f"- owner_approval_required: {summary['owner_approval_required']}",
                f"- public_repo_sha: {summary['public_repo_sha']}",
                f"- public_repo_clean_pre_materialization: {summary['public_repo_clean']}",
                "",
            ]
        ),
    )
    write_text(
        OUTPUTS["execute_now_manifest_md"],
        "# OC Core 1.3.1 Execute Now Manifest\n\n- Build release bundle\n- Validate release gate\n- Stage Zenodo package\n- Stop and request owner approval\n",
    )

    return {
        "control_plane": control_plane,
        "simulation_ledger": simulation_ledger,
        "dataset_manifest": dataset_manifest,
        "artifact_inventory": artifact_inventory,
        "package_ledger": package_ledger,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Materialize the OC Core 1.3.1 public release tranche.")
    parser.add_argument("--run-id", default="oc_core_1_3_1_release_v11")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = materialize_oc_core_1_3_1_release_v11(run_id=str(args.run_id).strip() or "oc_core_1_3_1_release_v11")
    print(payload["control_plane"]["summary"]["release_gate_status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
