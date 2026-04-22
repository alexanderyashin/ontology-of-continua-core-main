from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from oc_core_1_3_science_spot_lib import (
    EDITORIAL_DIR,
    MONOGRAPH_SOURCE_DIR,
    REPO_ROOT,
    SCIENCE_SURFACE_TARGETS,
    dump_json,
    load_json,
    repo_rel,
    validate_existing_bundle,
)


CERBERUS_RUNS_DIR = EDITORIAL_DIR / "cerberus_runs"
CERBERUS_BUILD_DIR = REPO_ROOT / "build_oc_core_1_3_cerberus_review"
CERBERUS_SURFACE_TARGETS = {
    "targets": EDITORIAL_DIR / "OC_CORE_1_3_RELEASE_REVIEW_TARGETS_latest.json",
    "findings": EDITORIAL_DIR / "OC_CORE_1_3_CERBERUS_REVIEW_FINDINGS_latest.json",
    "run": EDITORIAL_DIR / "OC_CORE_1_3_CERBERUS_RUN_latest.json",
    "acceptance": EDITORIAL_DIR / "OC_CORE_1_3_CERBERUS_ACCEPTANCE_CERT_latest.json",
}

MASTER_MONOGRAPH_TEX = REPO_ROOT / "oc_core_1_3_master_monograph.tex"
RELEASE_README = REPO_ROOT / "releases" / "oc_core_1_3" / "README.md"
ZENODO_METADATA = REPO_ROOT / ".zenodo.json"
EN_RELEASE_MONOGRAPH_PDF = REPO_ROOT / "releases" / "oc_core_1_3" / "monograph" / "OC_CORE_1_3_MASTER_MONOGRAPH_EN.pdf"
EN_RELEASE_MANUSCRIPT_PDF = REPO_ROOT / "releases" / "oc_core_1_3" / "manuscripts" / "OC_CORE_1_3_FLAGSHIP_MANUSCRIPT_EN.pdf"
EN_JOURNAL_CORE_MD = REPO_ROOT / "releases" / "oc_core_1_3" / "journal_core" / "OC_CORE_1_3_JOURNAL_CORE_EN.md"
EN_JOURNAL_CORE_PDF = REPO_ROOT / "releases" / "oc_core_1_3" / "journal_core" / "OC_CORE_1_3_JOURNAL_CORE_EN.pdf"
RELEASE_ARTIFACT_CONTRACT = EDITORIAL_DIR / "OC_CORE_1_3_SCIENCE_ARTIFACT_CONTRACT.json"
MASTER_AUXILIARY_SUFFIXES = [
    ".aux",
    ".bcf",
    ".bbl",
    ".blg",
    ".lof",
    ".lot",
    ".log",
    ".out",
    ".run.xml",
    ".toc",
]

SEVERITY_VALUES = ["BLOCKER", "MAJOR", "MINOR", "NON_DEFECT_OBSERVATION"]
CATEGORY_VALUES = [
    "build",
    "latex_typography",
    "structure",
    "duplication",
    "claim_scope",
    "theorem_precision",
    "notation",
    "numeric_sync",
    "citation",
    "comparison_honesty",
    "practical_use_honesty",
    "language_style",
    "release_consistency",
    "metadata",
]
SEVERITY_RANK = {value: index for index, value in enumerate(SEVERITY_VALUES)}

OPEN_STATUS = "OPEN"
NOT_ACTIONABLE_STATUS = "NOT_ACTIONABLE"
DETERMINISTIC_CLASS = "DETERMINISTIC_SCRIPT"
LLM_CLASS = "LLM_CODEX_CLI"

LLM_TASTE_ONLY_MARKERS = [
    "awkward",
    "clunky",
    "glossary-heavy",
    "harder to scan",
    "slower to scan",
    "less naturally",
    "less natural",
    "not parallel",
    "nonparallel",
    "cadence",
    "wordy",
    "tone",
    "reads less",
]
LLM_ACTIONABLE_STYLE_MARKERS = [
    "claim",
    "scope",
    "overclaim",
    "unsupported",
    "undefined",
    "inconsistent",
    "mismatch",
    "numeric",
    "formula",
    "theorem",
    "citation",
    "cite",
    "reference",
    "cross-reference",
    "grammar",
    "punctuation",
    "comma",
    "spelling",
    "typo",
    "missing",
    "wrong",
    "incorrect",
    "ambiguous",
]

PRIMARY_BLOCK_ORDER = [
    "Front Matter and Reader Contract",
    "Orientation and Scientific Promise",
    "Formal Core and Structural Doctrine",
    "Core 1.3 Closure, Synthesis, and Practical Use",
    "Audit and Atlas Archive",
]
EXPECTED_MAIN_INPUT_ORDER = [
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
EXPECTED_APPENDIX_ORDER = [
    "appendix/A_notation.tex",
    "appendix/B_axioms_full.tex",
    "appendix/C_klevels_tables.tex",
    "appendix/D_oc_core_1_3_source_audit_appendix.tex",
    "appendix/E_oc_core_1_3_journal_core_bridge.tex",
    "appendix/F_oc_core_1_3_reviewer_navigation_matrix.tex",
    "appendix/G_oc_core_1_3_empirical_validation_matrix.tex",
    "appendix/H_oc_core_1_3_institute_run_measurement_program.tex",
    "appendix/I_oc_core_1_3_domain_benchmark_manifest.tex",
    "appendix/L_oc_core_1_3_domain_benchmark_caseset.tex",
    "appendix/J_oc_core_1_3_domain_replay_reports.tex",
    "appendix/K_oc_core_1_3_domain_execution_board.tex",
    "appendix/M_oc_core_1_3_proof_machinery_appendix.tex",
    "appendix/N_oc_core_1_3_figure_atlas.tex",
    "appendix/O_oc_core_1_3_technical_derivation_atlas.tex",
    "appendix/P_oc_core_1_3_reference_benchmark_atlas.tex",
    "appendix/Q_oc_core_1_3_toe_support_dossiers.tex",
    "appendix/R_oc_core_1_3_practical_utility_model_comparison_atlas.tex",
]
PRIMARY_CITATION_TARGETS = [
    "content/14_disciplines_extended.tex",
    "content/26_oc_core_1_3_practical_utility.tex",
    "releases/oc_core_1_3/journal_core/OC_CORE_1_3_JOURNAL_CORE_EN.md",
]
PLACEHOLDER_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"\[\s*PLACEHOLDER\s*\]",
        r"\bPLACEHOLDER\s*:",
        r"\[\s*TODO\s*\]",
        r"\bTODO\s*:",
        r"\bTO BE FILLED\b",
        r"\bTBD\b",
        r"\bFIXME\b",
        r"\bXXX\b",
        r"\bLOREM IPSUM\b",
    ]
]
LEGACY_PATTERNS = [re.compile(r"\bCore 1\.1\b", re.IGNORECASE)]
SWEEPING_CLAIM_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"\bsupersed(?:e|es|ing)\s+(?:all|every|the whole of)\b",
        r"\ball prior science\b",
        r"\bevery model\b",
        r"\ball models\b",
        r"\bexplains everything\b",
        r"\buniversal(?:ly)? explains\b",
        r"\breplaces? all prior science\b",
    ]
]
MACHINE_TONE_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"\bNOT_DISPATCHED\b",
        r"\bPENDING_FORMAL_REVIEW\b",
        r"\bDERIVE_FROM_SPOT_ONLY\b",
        r"\bmanifest\.json\b",
        r"\btask_board\b",
        r"\bpackage_class\b",
        r"\bcurrent_status\b",
        r"\bresolution_if_pass\b",
    ]
]
THEOREM_VAGUE_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"\bobvious(?:ly)?\b",
        r"\btrivial(?:ly)?\b",
        r"\broutine\b",
        r"\bstraightforward\b",
        r"\beasy to see\b",
        r"\bone can show\b",
    ]
]
READER_FACING_ROLES = {
    "MANUSCRIPT_SPINE",
    "PRIMARY_READER_FACING",
    "READER_AUDIT_APPENDIX",
    "PUBLIC_RELEASE_DOC",
    "PUBLIC_METADATA",
}
LLM_ENABLED_ROLES = {
    "MANUSCRIPT_SPINE",
    "PRIMARY_READER_FACING",
    "READER_AUDIT_APPENDIX",
    "PUBLIC_RELEASE_DOC",
    "PUBLIC_METADATA",
    "TOE_SUPPORT_APPENDIX",
    "PRACTICAL_COMPARISON_APPENDIX",
}
LLM_REVIEWERS = [
    {
        "reviewer_id": "CERBERUS_LLM__HOSTILE_GENERALIST_SCIENTIST",
        "label": "hostile generalist scientific reviewer",
        "focus": "scientific honesty, boundedness, structure, and external defensibility",
        "categories": ["claim_scope", "comparison_honesty", "practical_use_honesty", "structure", "citation"],
    },
    {
        "reviewer_id": "CERBERUS_LLM__HOSTILE_MATHEMATICIAN",
        "label": "hostile mathematician",
        "focus": "theorem precision, notation, hidden assumptions, and scope leakage",
        "categories": ["theorem_precision", "notation", "claim_scope", "numeric_sync"],
    },
    {
        "reviewer_id": "CERBERUS_LLM__ELITE_COPY_CHIEF",
        "label": "elite journal copy chief",
        "focus": "language quality, typography-facing prose choices, metadata, and reader friction",
        "categories": ["language_style", "metadata", "structure", "latex_typography"],
    },
    {
        "reviewer_id": "CERBERUS_LLM__PRACTICAL_RED_TEAM",
        "label": "practical-use and comparison red team",
        "focus": "use claims, comparison honesty, and operational boundedness",
        "categories": ["practical_use_honesty", "comparison_honesty", "citation", "claim_scope"],
    },
]

INPUT_PATTERN = re.compile(r"\\input\{([^}]+)\}")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def compute_fingerprint(refs: list[str]) -> str:
    parts: list[str] = []
    for ref in refs:
        path = REPO_ROOT / ref
        if path.exists():
            parts.append(f"{ref}:{sha256_file(path)}")
        else:
            parts.append(f"{ref}:MISSING")
    return sha256_text("\n".join(parts))


def deepcopy_jsonable(payload: Any) -> Any:
    return json.loads(json.dumps(payload))


def git_head_sha(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    return result.stdout.strip()


def git_optional_ref_sha(repo_root: Path, ref: str) -> str:
    result = subprocess.run(
        ["git", "rev-parse", ref],
        cwd=repo_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def normalize_tex_ref(ref: str) -> str:
    normalized = ref.strip().replace("\\", "/")
    if normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def resolve_input_ref(ref: str) -> Path | None:
    normalized = normalize_tex_ref(ref)
    candidate = REPO_ROOT / normalized
    if candidate.exists():
        return candidate
    if candidate.suffix:
        return None
    tex_candidate = candidate.with_suffix(".tex")
    if tex_candidate.exists():
        return tex_candidate
    return None


def resolve_to_rel(ref: str) -> str:
    resolved = resolve_input_ref(ref)
    return repo_rel(resolved) if resolved is not None else normalize_tex_ref(ref)


def extract_input_refs(tex_path: Path) -> list[str]:
    text = tex_path.read_text(encoding="utf-8")
    return [normalize_tex_ref(match.group(1)) for match in INPUT_PATTERN.finditer(text)]


def collect_recursive_inputs(root_path: Path) -> list[Path]:
    ordered: list[Path] = []
    visited: set[Path] = set()

    def visit(path: Path) -> None:
        resolved = path.resolve()
        if resolved in visited or not path.exists():
            return
        visited.add(resolved)
        ordered.append(path)
        for input_ref in extract_input_refs(path):
            child = resolve_input_ref(input_ref)
            if child is not None:
                visit(child)

    visit(root_path)
    return ordered


def classify_review_unit(rel_path: str) -> str:
    if rel_path == "oc_core_1_3_master_monograph.tex":
        return "MANUSCRIPT_SPINE"
    if rel_path in {"preamble.tex", "content/frontmatter_oc_core_1_3_master.tex", "content/17_oc_core_1_3_reader_guide.tex"}:
        return "PRIMARY_READER_FACING"
    if rel_path.startswith("releases/oc_core_1_3/journal_core/"):
        return "PUBLIC_RELEASE_DOC"
    if rel_path == ".zenodo.json":
        return "PUBLIC_METADATA"
    if rel_path == "releases/oc_core_1_3/README.md":
        return "PUBLIC_RELEASE_DOC"
    if re.match(r"content/(0[1-9]|1[0-9]|2[0-6])_.*\.tex$", rel_path):
        return "PRIMARY_READER_FACING"
    if re.match(r"appendix/[A-M]_.*\.tex$", rel_path):
        return "READER_AUDIT_APPENDIX"
    if re.match(r"appendix/[N-P]_.*\.tex$", rel_path):
        return "ATLAS_SUPPORT_APPENDIX"
    if re.match(r"appendix/Q_.*\.tex$", rel_path):
        return "TOE_SUPPORT_APPENDIX"
    if re.match(r"appendix/R_.*\.tex$", rel_path):
        return "PRACTICAL_COMPARISON_APPENDIX"
    if rel_path.startswith("content/generated/"):
        return "GENERATED_READER_FACING"
    if rel_path.startswith("appendix/generated/"):
        return "GENERATED_APPENDIX_SUPPORT"
    if rel_path.startswith("content/toe/"):
        return "TOE_SUPPORT_DOSSIER"
    if rel_path.startswith(("content/crossk/", "content/cycles/", "content/experiments/", "content/falsifiability/", "content/jets/", "content/k_levels/", "content/m_spaces/", "content/predictions/", "content/processes/")):
        return "TECHNICAL_ATLAS_LEAF"
    return "SUPPORT_SOURCE"


def llm_required_for_role(role: str) -> bool:
    return role in LLM_ENABLED_ROLES


def build_review_units() -> list[dict[str, Any]]:
    units: list[dict[str, Any]] = []
    input_paths = collect_recursive_inputs(MASTER_MONOGRAPH_TEX)
    extra_public_docs = [RELEASE_README, EN_JOURNAL_CORE_MD, ZENODO_METADATA]
    for path in [*input_paths, *extra_public_docs]:
        rel = repo_rel(path)
        role = classify_review_unit(rel)
        units.append(
            {
                "artifact_id": f"CERBERUS_UNIT::{rel.replace('/', '__')}",
                "artifact_ref": rel,
                "unit_role": role,
                "llm_required": llm_required_for_role(role),
            }
        )
    return units


def build_sync_pairs(review_units: list[dict[str, Any]]) -> list[dict[str, str]]:
    pairs: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for unit in review_units:
        rel = unit["artifact_ref"]
        if rel.startswith("releases/"):
            continue
        if not (
            rel == "oc_core_1_3_master_monograph.tex"
            or rel == "preamble.tex"
            or rel.startswith(("content/", "appendix/", "figures/"))
        ):
            continue
        source_path = MONOGRAPH_SOURCE_DIR / rel
        pair = (rel, repo_rel(source_path))
        if pair in seen:
            continue
        seen.add(pair)
        pairs.append({"root_ref": rel, "source_ref": repo_rel(source_path)})
    return pairs


def build_artifact_targets(review_units: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    targets: list[dict[str, Any]] = []
    for unit in review_units:
        ref = unit["artifact_ref"]
        if ref in seen:
            continue
        seen.add(ref)
        targets.append(
            {
                "artifact_id": unit["artifact_id"],
                "artifact_ref": ref,
                "artifact_kind": "SOURCE_UNIT" if ref.endswith((".tex", ".md", ".json")) else "ARTIFACT",
                "outward_facing": unit["unit_role"] in READER_FACING_ROLES,
            }
        )
    for ref in [
        repo_rel(EN_RELEASE_MONOGRAPH_PDF),
        repo_rel(EN_RELEASE_MANUSCRIPT_PDF),
        repo_rel(EN_JOURNAL_CORE_PDF),
        repo_rel(RELEASE_ARTIFACT_CONTRACT),
        repo_rel(SCIENCE_SURFACE_TARGETS["spot"]),
        repo_rel(SCIENCE_SURFACE_TARGETS["foundational"]),
        repo_rel(SCIENCE_SURFACE_TARGETS["toe_synthesis"]),
        repo_rel(SCIENCE_SURFACE_TARGETS["practical_utility"]),
        repo_rel(SCIENCE_SURFACE_TARGETS["phase1_dossier"]),
    ]:
        if ref in seen:
            continue
        seen.add(ref)
        targets.append(
            {
                "artifact_id": f"CERBERUS_TARGET::{ref.replace('/', '__')}",
                "artifact_ref": ref,
                "artifact_kind": "RELEASE_ARTIFACT",
                "outward_facing": True,
            }
        )
    return targets


def build_hash_groups() -> list[dict[str, Any]]:
    return [
        {
            "group_id": "EN_FLAGSHIP_RELEASE_PDF_HASH_GROUP",
            "expected_hash_identity": True,
            "refs": [
                repo_rel(EN_RELEASE_MONOGRAPH_PDF),
                repo_rel(EN_RELEASE_MANUSCRIPT_PDF),
            ],
        }
    ]


def build_release_review_targets(repo_root: Path | None = None) -> dict[str, Any]:
    repo_root = repo_root or REPO_ROOT
    review_units = build_review_units()
    artifact_targets = build_artifact_targets(review_units)
    sync_pairs = build_sync_pairs(review_units)
    baseline_tag = "oc-core-1.3-pre-cerberus-baseline"
    fingerprint_refs = sorted(
        {
            *[unit["artifact_ref"] for unit in review_units],
            *[target["artifact_ref"] for target in artifact_targets],
        }
    )
    return {
        "metadata": {
            "repo_sha": git_head_sha(repo_root),
            "cerberus_baseline_tag": baseline_tag,
            "cerberus_baseline_sha": git_optional_ref_sha(repo_root, baseline_tag),
            "generated_at_utc": utc_now(),
            "script": "oc_core_1_3_cerberus_review.py",
            "surface": "logion/k0/governance/status/OC_CORE_1_3_RELEASE_REVIEW_TARGETS_latest.json",
        },
        "scope_id": "OC_CORE_1_3_ENGLISH_FLAGSHIP_RELEASE_PACKAGE",
        "stop_rule": "ZERO_OPEN_FINDINGS",
        "capability_scope": "RELEASE_WIDE_BUT_EN_FIRST",
        "active_language_codes": ["EN"],
        "deferred_language_codes": ["RU", "DE"],
        "deferred_reason": "Translations stay secondary until the English flagship Cerberus authority reaches zero open findings.",
        "review_units": review_units,
        "artifact_targets": artifact_targets,
        "hash_identity_groups": build_hash_groups(),
        "mirror_sync_pairs": sync_pairs,
        "fingerprint_refs": fingerprint_refs,
        "llm_reviewer_roster": deepcopy_jsonable(LLM_REVIEWERS),
    }


def finding_signature(finding: dict[str, Any]) -> str:
    section_ref = finding.get("section_ref") or ""
    return sha256_text(
        "||".join(
            [
                finding["artifact_ref"],
                section_ref,
                finding["category"],
                re.sub(r"\s+", " ", finding["claim"]).strip().lower(),
            ]
        )
    )


def make_finding(
    *,
    run_id: str,
    reviewer_id: str,
    artifact_ref: str,
    severity: str,
    category: str,
    determinism_class: str,
    claim: str,
    evidence: str,
    required_action: str,
    artifact_id: str | None = None,
    section_ref: str = "",
    status: str = OPEN_STATUS,
) -> dict[str, Any]:
    finding = {
        "finding_id": "",
        "run_id": run_id,
        "reviewer_id": reviewer_id,
        "artifact_id": artifact_id or f"CERBERUS::{artifact_ref.replace('/', '__')}",
        "artifact_ref": artifact_ref,
        "section_ref": section_ref or artifact_ref,
        "severity": severity,
        "category": category,
        "determinism_class": determinism_class,
        "claim": claim.strip(),
        "evidence": evidence.strip(),
        "required_action": required_action.strip(),
        "status": status,
    }
    finding["finding_id"] = f"CERBERUS_FINDING::{finding_signature(finding)[:20]}"
    return finding


def normalize_llm_finding_row(row: dict[str, Any]) -> dict[str, Any]:
    """Keep the LLM gate strict on defects while preventing taste-only churn.

    Copy-edit suggestions are welcome as observations, but they should not
    block the release unless the LLM identifies a concrete defect in meaning,
    grammar, punctuation, citation, theorem precision, numeric sync, metadata,
    or layout. Deterministic reviewers and non-language LLM categories are not
    downgraded here.
    """
    normalized = dict(row)
    if normalized.get("severity") != "MINOR" or normalized.get("category") != "language_style":
        return normalized
    combined = " ".join(
        str(normalized.get(key, ""))
        for key in ["section_ref", "claim", "evidence", "required_action"]
    ).lower()
    is_taste_only = any(marker in combined for marker in LLM_TASTE_ONLY_MARKERS)
    has_actionable_marker = any(marker in combined for marker in LLM_ACTIONABLE_STYLE_MARKERS)
    if is_taste_only and not has_actionable_marker:
        normalized["severity"] = "NON_DEFECT_OBSERVATION"
        normalized["status"] = NOT_ACTIONABLE_STATUS
        normalized["required_action"] = (
            "Optional editorial observation only; no release-blocking action is required unless "
            "a future reviewer ties it to meaning, grammar, punctuation, citation, theorem "
            "precision, numeric sync, metadata, or visible layout."
        )
    return normalized


def merge_findings(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for finding in findings:
        signature = finding_signature(finding)
        if signature not in merged:
            finding["corroborating_reviewer_ids"] = []
            merged[signature] = finding
            continue
        current = merged[signature]
        current["corroborating_reviewer_ids"] = sorted(
            {
                *current.get("corroborating_reviewer_ids", []),
                current["reviewer_id"],
                finding["reviewer_id"],
            }
        )
        if SEVERITY_RANK[finding["severity"]] < SEVERITY_RANK[current["severity"]]:
            current["severity"] = finding["severity"]
        if finding["status"] == OPEN_STATUS:
            current["status"] = OPEN_STATUS
        if len(finding["evidence"]) > len(current["evidence"]):
            current["evidence"] = finding["evidence"]
        if len(finding["required_action"]) > len(current["required_action"]):
            current["required_action"] = finding["required_action"]
    return sorted(merged.values(), key=lambda row: (SEVERITY_RANK[row["severity"]], row["artifact_ref"], row["category"], row["finding_id"]))


def count_open_defects(findings: list[dict[str, Any]]) -> int:
    return sum(1 for row in findings if row["status"] == OPEN_STATUS and row["severity"] != "NON_DEFECT_OBSERVATION")


def deterministic_release_integrity_review(manifest: dict[str, Any], run_id: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for target in manifest["artifact_targets"]:
        ref = target["artifact_ref"]
        path = REPO_ROOT / ref
        if not path.exists():
            findings.append(
                make_finding(
                    run_id=run_id,
                    reviewer_id="CERBERUS_DETERMINISTIC__RELEASE_INTEGRITY",
                    artifact_ref=ref,
                    severity="BLOCKER",
                    category="release_consistency",
                    determinism_class=DETERMINISTIC_CLASS,
                    claim="A release target declared by the Cerberus manifest is missing from disk.",
                    evidence=f"Missing target: {ref}",
                    required_action="Restore the outward-facing artifact or remove it from the release-target manifest generation logic.",
                )
            )
    for pair in manifest["mirror_sync_pairs"]:
        root_path = REPO_ROOT / pair["root_ref"]
        source_path = REPO_ROOT / pair["source_ref"]
        if not source_path.exists():
            findings.append(
                make_finding(
                    run_id=run_id,
                    reviewer_id="CERBERUS_DETERMINISTIC__RELEASE_INTEGRITY",
                    artifact_ref=pair["source_ref"],
                    severity="MAJOR",
                    category="release_consistency",
                    determinism_class=DETERMINISTIC_CLASS,
                    claim="The release source mirror is missing a flagship manuscript file that exists in the root source tree.",
                    evidence=f"Missing release mirror for {pair['root_ref']}",
                    required_action="Materialize the missing file under releases/oc_core_1_3/monograph/source or stop treating the root file as part of the flagship release path.",
                )
            )
            continue
        if sha256_file(root_path) != sha256_file(source_path):
            findings.append(
                make_finding(
                    run_id=run_id,
                    reviewer_id="CERBERUS_DETERMINISTIC__RELEASE_INTEGRITY",
                    artifact_ref=pair["root_ref"],
                    severity="MAJOR",
                    category="release_consistency",
                    determinism_class=DETERMINISTIC_CLASS,
                    claim="The root flagship source and the release-source mirror have drifted out of byte-identical sync.",
                    evidence=f"Sync pair drift: {pair['root_ref']} != {pair['source_ref']}",
                    required_action="Resynchronize the release source mirror from the canonical root flagship source before release review continues.",
                )
            )
    for group in manifest["hash_identity_groups"]:
        hashes: dict[str, str] = {}
        missing_refs: list[str] = []
        for ref in group["refs"]:
            path = REPO_ROOT / ref
            if not path.exists():
                missing_refs.append(ref)
                continue
            hashes[ref] = sha256_file(path)
        if missing_refs:
            findings.append(
                make_finding(
                    run_id=run_id,
                    reviewer_id="CERBERUS_DETERMINISTIC__RELEASE_INTEGRITY",
                    artifact_ref=group["refs"][0],
                    severity="BLOCKER",
                    category="release_consistency",
                    determinism_class=DETERMINISTIC_CLASS,
                    claim="A release PDF required to remain hash-identical is missing.",
                    evidence=f"Hash-identity group {group['group_id']} is missing {missing_refs}",
                    required_action="Rebuild and restore every PDF in the hash-identity group before release review.",
                )
            )
            continue
        if len(set(hashes.values())) != 1:
            findings.append(
                make_finding(
                    run_id=run_id,
                    reviewer_id="CERBERUS_DETERMINISTIC__RELEASE_INTEGRITY",
                    artifact_ref=group["refs"][0],
                    severity="BLOCKER",
                    category="release_consistency",
                    determinism_class=DETERMINISTIC_CLASS,
                    claim="Release PDFs that must remain hash-identical have diverged.",
                    evidence=f"Hash mismatch in {group['group_id']}: {hashes}",
                    required_action="Regenerate the release PDFs from one canonical flagship build and refresh every outward-facing copy.",
                )
            )
    return findings


def run_subprocess(command: list[str], *, cwd: Path, timeout_ms: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout_ms / 1000,
    )


def parse_build_log(log_text: str) -> dict[str, Any]:
    return {
        "overfull_total": len(re.findall(r"Overfull \\\\hbox", log_text)),
        "underfull_total": len(re.findall(r"Underfull \\\\hbox", log_text)),
        "undefined_reference_total": len(re.findall(r"There were undefined references", log_text)),
        "rerun_warning_total": len(re.findall(r"Rerun to get cross-references right|Label\\(s\\) may have changed|Please \\(re\\)run Biber", log_text)),
        "empty_bibliography_total": len(re.findall(r"Empty bibliography", log_text)),
        "pdf_string_warning_total": len(re.findall(r"Token not allowed in a PDF string", log_text)),
        "missing_character_total": len(re.findall(r"Missing character:", log_text)),
    }


def deterministic_build_review(
    manifest: dict[str, Any],
    run_id: str,
    run_dir: Path,
    *,
    build_mode: str = "full",
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    build_dir = CERBERUS_BUILD_DIR
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir(parents=True, exist_ok=True)

    science_errors = validate_existing_bundle(REPO_ROOT, require_final_toe_pass=True)
    if science_errors:
        findings.append(
            make_finding(
                run_id=run_id,
                reviewer_id="CERBERUS_DETERMINISTIC__BUILD_AND_SCIENCE_GATE",
                artifact_ref=repo_rel(SCIENCE_SURFACE_TARGETS["spot"]),
                severity="BLOCKER",
                category="release_consistency",
                determinism_class=DETERMINISTIC_CLASS,
                claim="The strict science bundle gate is not clean before manuscript release review.",
                evidence=" | ".join(science_errors[:8]),
                required_action="Resolve the strict science validation errors before trusting any manuscript acceptance verdict.",
            )
        )

    if build_mode == "skip":
        return findings, {
            "build_dir": repo_rel(build_dir),
            "pdf_ref": "",
            "log_ref": "",
            "build_failed": False,
            "build_skipped": True,
            "command_results": [],
            "log_stats": parse_build_log(""),
            "pdf_hash": "",
        }

    commands = [
        [
            "xelatex",
            "-interaction=nonstopmode",
            "-halt-on-error",
            f"-aux-directory={build_dir}",
            f"-output-directory={build_dir}",
            MASTER_MONOGRAPH_TEX.name,
        ],
        ["biber", "--input-directory", str(build_dir), "--output-directory", str(build_dir), MASTER_MONOGRAPH_TEX.stem],
        [
            "xelatex",
            "-interaction=nonstopmode",
            "-halt-on-error",
            f"-aux-directory={build_dir}",
            f"-output-directory={build_dir}",
            MASTER_MONOGRAPH_TEX.name,
        ],
        [
            "xelatex",
            "-interaction=nonstopmode",
            "-halt-on-error",
            f"-aux-directory={build_dir}",
            f"-output-directory={build_dir}",
            MASTER_MONOGRAPH_TEX.name,
        ],
    ]
    command_results: list[dict[str, Any]] = []
    build_failed = False
    root_aux_paths = [REPO_ROOT / f"{MASTER_MONOGRAPH_TEX.stem}{suffix}" for suffix in MASTER_AUXILIARY_SUFFIXES]
    root_aux_backup_dir = build_dir / "_root_aux_backup"
    root_aux_backup_dir.mkdir(parents=True, exist_ok=True)
    try:
        for path in root_aux_paths:
            if path.exists():
                shutil.move(str(path), str(root_aux_backup_dir / path.name))

        for command in commands:
            result = run_subprocess(command, cwd=REPO_ROOT, timeout_ms=240000)
            command_results.append(
                {
                    "command": command,
                    "returncode": result.returncode,
                    "stdout_tail": "\n".join(result.stdout.splitlines()[-20:]),
                    "stderr_tail": "\n".join(result.stderr.splitlines()[-20:]),
                }
            )
            if result.returncode != 0:
                build_failed = True
                findings.append(
                    make_finding(
                        run_id=run_id,
                        reviewer_id="CERBERUS_DETERMINISTIC__BUILD_AND_SCIENCE_GATE",
                        artifact_ref=repo_rel(MASTER_MONOGRAPH_TEX),
                        severity="BLOCKER",
                        category="build",
                        determinism_class=DETERMINISTIC_CLASS,
                        claim="The flagship English monograph does not complete the required XeLaTeX/Biber build chain.",
                        evidence=f"Command failed: {' '.join(command)} | stderr tail: {' '.join(result.stderr.splitlines()[-8:])}",
                        required_action="Repair the manuscript build until XeLaTeX -> Biber -> XeLaTeX -> XeLaTeX completes without command failure.",
                    )
                )
                break
    finally:
        for path in root_aux_paths:
            if path.exists():
                path.unlink()
            backup_path = root_aux_backup_dir / path.name
            if backup_path.exists():
                shutil.move(str(backup_path), str(path))

    log_path = build_dir / f"{MASTER_MONOGRAPH_TEX.stem}.log"
    pdf_path = build_dir / f"{MASTER_MONOGRAPH_TEX.stem}.pdf"
    log_text = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
    if log_path.exists():
        target_log_path = run_dir / "build" / log_path.name
        target_log_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(log_path, target_log_path)
    if pdf_path.exists():
        target_pdf_path = run_dir / "build" / pdf_path.name
        target_pdf_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(pdf_path, target_pdf_path)

    log_stats = parse_build_log(log_text)
    if log_stats["undefined_reference_total"] > 0:
        findings.append(
            make_finding(
                run_id=run_id,
                reviewer_id="CERBERUS_DETERMINISTIC__BUILD_AND_SCIENCE_GATE",
                artifact_ref=repo_rel(MASTER_MONOGRAPH_TEX),
                severity="BLOCKER",
                category="build",
                determinism_class=DETERMINISTIC_CLASS,
                claim="The build log reports undefined references.",
                evidence=f"Undefined-reference count: {log_stats['undefined_reference_total']}",
                required_action="Resolve every undefined reference before release review can pass.",
            )
        )
    if log_stats["rerun_warning_total"] > 0:
        findings.append(
            make_finding(
                run_id=run_id,
                reviewer_id="CERBERUS_DETERMINISTIC__BUILD_AND_SCIENCE_GATE",
                artifact_ref=repo_rel(MASTER_MONOGRAPH_TEX),
                severity="BLOCKER",
                category="build",
                determinism_class=DETERMINISTIC_CLASS,
                claim="The build log still asks for an additional rerun.",
                evidence=f"Rerun-warning count: {log_stats['rerun_warning_total']}",
                required_action="Stabilize the manuscript so the required build chain ends without rerun-needed warnings.",
            )
        )
    if log_stats["empty_bibliography_total"] > 0:
        findings.append(
            make_finding(
                run_id=run_id,
                reviewer_id="CERBERUS_DETERMINISTIC__BUILD_AND_SCIENCE_GATE",
                artifact_ref=repo_rel(MASTER_MONOGRAPH_TEX),
                severity="BLOCKER",
                category="build",
                determinism_class=DETERMINISTIC_CLASS,
                claim="The bibliography is empty at build time.",
                evidence=f"Empty-bibliography count: {log_stats['empty_bibliography_total']}",
                required_action="Restore bibliography resolution before release review can continue.",
            )
        )
    if log_stats["overfull_total"] > 0:
        findings.append(
            make_finding(
                run_id=run_id,
                reviewer_id="CERBERUS_DETERMINISTIC__TYPOGRAPHY",
                artifact_ref=repo_rel(MASTER_MONOGRAPH_TEX),
                severity="MAJOR",
                category="latex_typography",
                determinism_class=DETERMINISTIC_CLASS,
                claim="The build log still contains overfull boxes.",
                evidence=f"Overfull total: {log_stats['overfull_total']}",
                required_action="Reflow the affected content until the flagship build reaches zero overfull boxes.",
            )
        )
    if log_stats["underfull_total"] > 0:
        findings.append(
            make_finding(
                run_id=run_id,
                reviewer_id="CERBERUS_DETERMINISTIC__TYPOGRAPHY",
                artifact_ref=repo_rel(MASTER_MONOGRAPH_TEX),
                severity="MINOR",
                category="latex_typography",
                determinism_class=DETERMINISTIC_CLASS,
                claim="The build log still contains underfull boxes.",
                evidence=f"Underfull total: {log_stats['underfull_total']}",
                required_action="Reduce residual underfull spacing debt until the flagship build is typographically clean.",
            )
        )
    if log_stats["pdf_string_warning_total"] > 0:
        findings.append(
            make_finding(
                run_id=run_id,
                reviewer_id="CERBERUS_DETERMINISTIC__TYPOGRAPHY",
                artifact_ref=repo_rel(MASTER_MONOGRAPH_TEX),
                severity="MAJOR",
                category="metadata",
                determinism_class=DETERMINISTIC_CLASS,
                claim="The build log still contains PDF-string or bookmark warnings.",
                evidence=f"PDF-string warning total: {log_stats['pdf_string_warning_total']}",
                required_action="Normalize headings and bookmarks until PDF-string warnings disappear.",
            )
        )
    if log_stats["missing_character_total"] > 0:
        findings.append(
            make_finding(
                run_id=run_id,
                reviewer_id="CERBERUS_DETERMINISTIC__TYPOGRAPHY",
                artifact_ref=repo_rel(MASTER_MONOGRAPH_TEX),
                severity="BLOCKER",
                category="latex_typography",
                determinism_class=DETERMINISTIC_CLASS,
                claim="The build log still contains missing-character defects.",
                evidence=f"Missing-character total: {log_stats['missing_character_total']}",
                required_action="Repair the offending glyph or macro usage until the build log is free of missing-character defects.",
            )
        )
    if not pdf_path.exists():
        findings.append(
            make_finding(
                run_id=run_id,
                reviewer_id="CERBERUS_DETERMINISTIC__BUILD_AND_SCIENCE_GATE",
                artifact_ref=repo_rel(MASTER_MONOGRAPH_TEX),
                severity="BLOCKER",
                category="build",
                determinism_class=DETERMINISTIC_CLASS,
                claim="The Cerberus build did not emit the flagship PDF.",
                evidence=f"Missing build output: {repo_rel(pdf_path)}",
                required_action="Repair the build chain until the flagship PDF is emitted in the Cerberus build directory.",
            )
        )

    return findings, {
        "build_dir": repo_rel(build_dir),
        "pdf_ref": repo_rel(pdf_path),
        "log_ref": repo_rel(log_path),
        "build_failed": build_failed,
        "build_skipped": False,
        "command_results": command_results,
        "log_stats": log_stats,
        "pdf_hash": sha256_file(pdf_path) if pdf_path.exists() else "",
    }


def deterministic_structure_review(manifest: dict[str, Any], run_id: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    master_text = MASTER_MONOGRAPH_TEX.read_text(encoding="utf-8")
    blocks = [block.replace("~", " ") for block in re.findall(r"\\ocvolumeblock\{([^}]*)\}", master_text)]
    if blocks != PRIMARY_BLOCK_ORDER:
        findings.append(
            make_finding(
                run_id=run_id,
                reviewer_id="CERBERUS_DETERMINISTIC__STRUCTURE",
                artifact_ref=repo_rel(MASTER_MONOGRAPH_TEX),
                severity="MAJOR",
                category="structure",
                determinism_class=DETERMINISTIC_CLASS,
                claim="The flagship volume-block sequence does not match the canonical five-block reading architecture.",
                evidence=f"Observed blocks: {blocks}",
                required_action="Restore the canonical block order for front matter, orientation, doctrine, closure/synthesis/use, and archive.",
            )
        )
    top_level_inputs = [normalize_tex_ref(match.group(1)) for match in INPUT_PATTERN.finditer(master_text)]
    actual_main_inputs = [
        resolve_to_rel(ref)
        for ref in top_level_inputs
        if resolve_to_rel(ref).startswith("content/") and resolve_to_rel(ref) != "content/frontmatter_oc_core_1_3_master.tex"
    ]
    actual_appendix_inputs = [resolve_to_rel(ref) for ref in top_level_inputs if resolve_to_rel(ref).startswith("appendix/")]
    if actual_main_inputs != EXPECTED_MAIN_INPUT_ORDER:
        findings.append(
            make_finding(
                run_id=run_id,
                reviewer_id="CERBERUS_DETERMINISTIC__STRUCTURE",
                artifact_ref=repo_rel(MASTER_MONOGRAPH_TEX),
                severity="MAJOR",
                category="structure",
                determinism_class=DETERMINISTIC_CLASS,
                claim="The main-body chapter order no longer matches the balanced flagship contract.",
                evidence=f"Observed main-body order: {actual_main_inputs}",
                required_action="Restore the lawful chapter order from the reader guide through chapter 26.",
            )
        )
    if actual_appendix_inputs != EXPECTED_APPENDIX_ORDER:
        findings.append(
            make_finding(
                run_id=run_id,
                reviewer_id="CERBERUS_DETERMINISTIC__STRUCTURE",
                artifact_ref=repo_rel(MASTER_MONOGRAPH_TEX),
                severity="MAJOR",
                category="structure",
                determinism_class=DETERMINISTIC_CLASS,
                claim="The appendix order no longer matches the canonical inspection spine.",
                evidence=f"Observed appendix order: {actual_appendix_inputs}",
                required_action="Restore the monotone appendix order ending with Q as synthesis support and R as practical comparison atlas.",
            )
        )
    for forbidden_ref in ["content/toe/toe_master.tex", "appendix/toe_data.tex"]:
        if forbidden_ref in top_level_inputs or forbidden_ref.replace(".tex", "") in top_level_inputs:
            findings.append(
                make_finding(
                    run_id=run_id,
                    reviewer_id="CERBERUS_DETERMINISTIC__STRUCTURE",
                    artifact_ref=repo_rel(MASTER_MONOGRAPH_TEX),
                    severity="MAJOR",
                    category="duplication",
                    determinism_class=DETERMINISTIC_CLASS,
                    claim="The master manuscript directly includes a support block that must remain subordinate to the canonical flagship spine.",
                    evidence=f"Forbidden top-level include: {forbidden_ref}",
                    required_action="Keep toe support and toe data subordinate through their designated appendix wrappers only.",
                )
            )
    for required_ref in ["content/25_oc_core_1_3_toe_synthesis.tex", "content/26_oc_core_1_3_practical_utility.tex"]:
        if actual_main_inputs.count(required_ref) != 1:
            findings.append(
                make_finding(
                    run_id=run_id,
                    reviewer_id="CERBERUS_DETERMINISTIC__STRUCTURE",
                    artifact_ref=repo_rel(MASTER_MONOGRAPH_TEX),
                    severity="BLOCKER",
                    category="structure",
                    determinism_class=DETERMINISTIC_CLASS,
                    claim="A canonical main-body chapter is missing or duplicated in the flagship spine.",
                    evidence=f"Input count for {required_ref}: {actual_main_inputs.count(required_ref)}",
                    required_action="Ensure chapters 25 and 26 each appear exactly once in the top-level English master manuscript.",
                )
            )
    return findings


def deterministic_theorem_notation_review(manifest: dict[str, Any], run_id: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    notation_path = REPO_ROOT / "appendix" / "A_notation.tex"
    notation_text = notation_path.read_text(encoding="utf-8", errors="replace")
    for level in range(13):
        token_pattern = re.compile(rf"K(?:_\{{{level}\}}|_{level}|\s*{level}\b)")
        if not token_pattern.search(notation_text):
            findings.append(
                make_finding(
                    run_id=run_id,
                    reviewer_id="CERBERUS_DETERMINISTIC__THEOREM_AND_NOTATION",
                    artifact_ref=repo_rel(notation_path),
                    severity="MAJOR",
                    category="notation",
                    determinism_class=DETERMINISTIC_CLASS,
                    claim="The notation appendix no longer enumerates the full K0-K12 ladder required by the flagship theorem spine.",
                    evidence=f"Missing K-level token in notation appendix: K{level}",
                    required_action="Restore an explicit notation entry or clear reference for every K-level from K0 through K12.",
                )
            )
    theorem_paths = [
        REPO_ROOT / "content" / "19_oc_core_1_3_foundational_consistency.tex",
        REPO_ROOT / "content" / "20_oc_core_1_3_theorem_roadmap.tex",
        REPO_ROOT / "content" / "21_oc_core_1_3_worked_examples.tex",
        REPO_ROOT / "content" / "24_oc_core_1_3_proof_machinery.tex",
        REPO_ROOT / "content" / "25_oc_core_1_3_toe_synthesis.tex",
        REPO_ROOT / "appendix" / "M_oc_core_1_3_proof_machinery_appendix.tex",
    ]
    for path in theorem_paths:
        rel = repo_rel(path)
        if not path.exists():
            findings.append(
                make_finding(
                    run_id=run_id,
                    reviewer_id="CERBERUS_DETERMINISTIC__THEOREM_AND_NOTATION",
                    artifact_ref=rel,
                    severity="BLOCKER",
                    category="theorem_precision",
                    determinism_class=DETERMINISTIC_CLASS,
                    claim="A theorem-bearing flagship source file is missing from disk.",
                    evidence=f"Missing theorem-bearing file: {rel}",
                    required_action="Restore the theorem-bearing source file before manuscript review continues.",
                )
            )
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern in THEOREM_VAGUE_PATTERNS:
            for match in pattern.finditer(text):
                findings.append(
                    make_finding(
                        run_id=run_id,
                        reviewer_id="CERBERUS_DETERMINISTIC__THEOREM_AND_NOTATION",
                        artifact_ref=rel,
                        severity="MINOR",
                        category="theorem_precision",
                        determinism_class=DETERMINISTIC_CLASS,
                        claim="Theorem-facing prose uses a vague proof shortcut phrase that weakens hostile-review defensibility.",
                        evidence=f"Matched theorem-vagueness phrase `{match.group(0)}` in {rel}",
                        required_action="Replace the shortcut phrase with explicit proof routing, bounded statement language, or a precise reference to the supporting theorem path.",
                    )
                )
        if rel.endswith("20_oc_core_1_3_theorem_roadmap.tex") and "Theorem" not in text:
            findings.append(
                make_finding(
                    run_id=run_id,
                    reviewer_id="CERBERUS_DETERMINISTIC__THEOREM_AND_NOTATION",
                    artifact_ref=rel,
                    severity="MAJOR",
                    category="theorem_precision",
                    determinism_class=DETERMINISTIC_CLASS,
                    claim="The theorem roadmap no longer explicitly names theorem-level objects.",
                    evidence="Theorem roadmap chapter does not contain the token `Theorem`.",
                    required_action="Restore explicit theorem-level routing language in the theorem roadmap chapter.",
                )
            )
    return findings


def deterministic_numeric_surface_review(manifest: dict[str, Any], run_id: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    atlas = load_json(SCIENCE_SURFACE_TARGETS["practical_utility"])
    use_rows = atlas.get("use_case_rows", [])
    playbooks = atlas.get("operational_playbooks", [])
    expected_domains = {"PHYSICS", "CHEMISTRY", "BIOLOGY", "SYSTEMS_CIVILIZATIONAL_PROJECTION"}
    observed_use_domains = {row.get("domain_id") for row in use_rows if row.get("domain_id") in expected_domains}
    observed_playbook_domains = {row.get("domain_id") for row in playbooks if row.get("domain_id") in expected_domains}
    missing_use_domains = sorted(expected_domains - observed_use_domains)
    missing_playbook_domains = sorted(expected_domains - observed_playbook_domains)
    if missing_use_domains:
        findings.append(
            make_finding(
                run_id=run_id,
                reviewer_id="CERBERUS_DETERMINISTIC__NUMERIC_AND_SURFACE",
                artifact_ref=repo_rel(SCIENCE_SURFACE_TARGETS["practical_utility"]),
                severity="MAJOR",
                category="practical_use_honesty",
                determinism_class=DETERMINISTIC_CLASS,
                claim="The practical-utility atlas is missing at least one core-domain use-case row.",
                evidence=f"Missing use-case domains: {missing_use_domains}",
                required_action="Provide at least one practical-use row for every core empirical domain.",
            )
        )
    if missing_playbook_domains:
        findings.append(
            make_finding(
                run_id=run_id,
                reviewer_id="CERBERUS_DETERMINISTIC__NUMERIC_AND_SURFACE",
                artifact_ref=repo_rel(SCIENCE_SURFACE_TARGETS["practical_utility"]),
                severity="MAJOR",
                category="practical_use_honesty",
                determinism_class=DETERMINISTIC_CLASS,
                claim="The practical-utility atlas is missing at least one operational playbook for a core domain.",
                evidence=f"Missing playbook domains: {missing_playbook_domains}",
                required_action="Provide at least one operational playbook for every core empirical domain.",
            )
        )
    for row in use_rows:
        if row.get("usable_now") and not row.get("trace_refs"):
            findings.append(
                make_finding(
                    run_id=run_id,
                    reviewer_id="CERBERUS_DETERMINISTIC__NUMERIC_AND_SURFACE",
                    artifact_ref=repo_rel(SCIENCE_SURFACE_TARGETS["practical_utility"]),
                    severity="BLOCKER",
                    category="numeric_sync",
                    determinism_class=DETERMINISTIC_CLASS,
                    claim="A practical-use row is marked as usable now but lacks traceable canonical references.",
                    evidence=f"Use-case row without trace refs: {row.get('use_case_id', 'UNKNOWN')}",
                    required_action="Add trace references for every row presented as usable now.",
                )
            )
    toe_surface = load_json(SCIENCE_SURFACE_TARGETS["toe_synthesis"])
    toe_rows = toe_surface.get("k_level_rows", [])
    if len(toe_rows) != 13:
        findings.append(
            make_finding(
                run_id=run_id,
                reviewer_id="CERBERUS_DETERMINISTIC__NUMERIC_AND_SURFACE",
                artifact_ref=repo_rel(SCIENCE_SURFACE_TARGETS["toe_synthesis"]),
                severity="BLOCKER",
                category="numeric_sync",
                determinism_class=DETERMINISTIC_CLASS,
                claim="The unified synthesis surface no longer covers every K-level row.",
                evidence=f"Observed synthesis row total: {len(toe_rows)}",
                required_action="Restore explicit K0-K12 coverage in the unified synthesis surface.",
            )
        )
    return findings


def pattern_scan_text(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix == ".tex":
        return re.sub(r"(?m)^\s*%.*$", "", text)
    return text


def has_explicit_citation(path: Path) -> bool:
    if path.suffix == ".tex":
        for tex_path in collect_recursive_inputs(path):
            text = pattern_scan_text(tex_path)
            if re.search(r"\\[A-Za-z]*cite[A-Za-z]*\{", text):
                return True
        return False
    text = pattern_scan_text(path)
    if re.search(r"(?mi)^##\s+References\b", text):
        return True
    if re.search(r"(?m)^\[\d+\]\s", text):
        return True
    return False


def deterministic_citation_review(manifest: dict[str, Any], run_id: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for rel in PRIMARY_CITATION_TARGETS:
        path = REPO_ROOT / rel
        if not path.exists():
            continue
        if not has_explicit_citation(path):
            findings.append(
                make_finding(
                    run_id=run_id,
                    reviewer_id="CERBERUS_DETERMINISTIC__CITATION_AND_COMPARISON",
                    artifact_ref=rel,
                    severity="MAJOR",
                    category="citation",
                    determinism_class=DETERMINISTIC_CLASS,
                    claim="A comparison-heavy or externally referential English release chapter lacks explicit citations.",
                    evidence=f"No citation marker found in {rel}",
                    required_action="Add selective primary or canonical citations where the chapter compares OC to established sciences or model families.",
                )
            )
    for unit in manifest["review_units"]:
        if unit["unit_role"] not in READER_FACING_ROLES and unit["unit_role"] != "PRIMARY_READER_FACING":
            continue
        path = REPO_ROOT / unit["artifact_ref"]
        if not path.exists():
            continue
        text = pattern_scan_text(path)
        for pattern in SWEEPING_CLAIM_PATTERNS:
            for match in pattern.finditer(text):
                findings.append(
                    make_finding(
                        run_id=run_id,
                        reviewer_id="CERBERUS_DETERMINISTIC__CITATION_AND_COMPARISON",
                        artifact_ref=unit["artifact_ref"],
                        severity="MAJOR",
                        category="comparison_honesty",
                        determinism_class=DETERMINISTIC_CLASS,
                        claim="Reader-facing release prose uses sweeping comparison language that outruns the bounded comparison doctrine.",
                        evidence=f"Matched phrase `{match.group(0)}` in {unit['artifact_ref']}",
                        required_action="Narrow the comparison claim to a bounded lane or support it explicitly without global supersession rhetoric.",
                    )
                )
    return findings


def deterministic_language_review(manifest: dict[str, Any], run_id: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for unit in manifest["review_units"]:
        path = REPO_ROOT / unit["artifact_ref"]
        if not path.exists():
            continue
        text = pattern_scan_text(path)
        for pattern in PLACEHOLDER_PATTERNS:
            if pattern.search(text):
                findings.append(
                    make_finding(
                        run_id=run_id,
                        reviewer_id="CERBERUS_DETERMINISTIC__LANGUAGE_AND_EDITORIAL",
                        artifact_ref=unit["artifact_ref"],
                        severity="BLOCKER",
                        category="language_style",
                        determinism_class=DETERMINISTIC_CLASS,
                        claim="A reviewer-visible placeholder or unfinished marker remains inside the active release corpus.",
                        evidence=f"Matched placeholder pattern `{pattern.pattern}` in {unit['artifact_ref']}",
                        required_action="Remove the placeholder residue or finish the section before release review continues.",
                    )
                )
        if unit["unit_role"] in READER_FACING_ROLES | {"PRIMARY_READER_FACING", "READER_AUDIT_APPENDIX"}:
            for pattern in LEGACY_PATTERNS:
                if pattern.search(text):
                    findings.append(
                        make_finding(
                            run_id=run_id,
                            reviewer_id="CERBERUS_DETERMINISTIC__LANGUAGE_AND_EDITORIAL",
                            artifact_ref=unit["artifact_ref"],
                            severity="MAJOR",
                            category="language_style",
                            determinism_class=DETERMINISTIC_CLASS,
                            claim="Legacy release-language residue remains in a reader-facing English flagship unit.",
                            evidence=f"Matched legacy pattern `{pattern.pattern}` in {unit['artifact_ref']}",
                            required_action="Remove or demote the legacy residue so the flagship speaks consistently as Core 1.3.",
                        )
                    )
            for pattern in MACHINE_TONE_PATTERNS:
                if pattern.search(text):
                    findings.append(
                        make_finding(
                            run_id=run_id,
                            reviewer_id="CERBERUS_DETERMINISTIC__LANGUAGE_AND_EDITORIAL",
                            artifact_ref=unit["artifact_ref"],
                            severity="MINOR",
                            category="language_style",
                            determinism_class=DETERMINISTIC_CLASS,
                            claim="Reader-facing prose still leaks internal governance or machine-diction markers.",
                            evidence=f"Matched machine-tone pattern `{pattern.pattern}` in {unit['artifact_ref']}",
                            required_action="Rewrite the passage into publication-grade prose and keep machine governance language inside review ledgers only.",
                        )
                    )
    return findings


def deterministic_metadata_review(run_id: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    metadata = load_json(ZENODO_METADATA)
    for required_key in ["title", "description", "creators", "keywords", "version", "upload_type", "publication_type", "license", "language"]:
        if not metadata.get(required_key):
            findings.append(
                make_finding(
                    run_id=run_id,
                    reviewer_id="CERBERUS_DETERMINISTIC__METADATA",
                    artifact_ref=repo_rel(ZENODO_METADATA),
                    severity="MAJOR",
                    category="metadata",
                    determinism_class=DETERMINISTIC_CLASS,
                    claim="The outward metadata payload is missing a required publication field.",
                    evidence=f"Missing key: {required_key}",
                    required_action="Restore every required Zenodo metadata field before release review continues.",
                )
            )
    master_text = MASTER_MONOGRAPH_TEX.read_text(encoding="utf-8")
    for required_token in ["pdftitle", "pdfauthor", "pdfsubject", "pdfkeywords", "pdflang"]:
        if required_token not in master_text:
            findings.append(
                make_finding(
                    run_id=run_id,
                    reviewer_id="CERBERUS_DETERMINISTIC__METADATA",
                    artifact_ref=repo_rel(MASTER_MONOGRAPH_TEX),
                    severity="MAJOR",
                    category="metadata",
                    determinism_class=DETERMINISTIC_CLASS,
                    claim="The flagship manuscript metadata shell is incomplete.",
                    evidence=f"Missing token `{required_token}` in oc_core_1_3_master_monograph.tex",
                    required_action="Restore the full PDF metadata shell in the flagship manuscript preamble.",
                )
            )
    return findings


def unit_excerpt(text: str, max_chars: int = 12000) -> str:
    compact = text.strip()
    if len(compact) <= max_chars:
        return compact
    half = max_chars // 2
    return compact[:half] + "\n\n[... omitted middle content for Cerberus prompt compression ...]\n\n" + compact[-half:]


def should_review_with_llm(unit: dict[str, Any], reviewer: dict[str, Any]) -> bool:
    role = unit["unit_role"]
    if role not in LLM_ENABLED_ROLES:
        return False
    ref = unit["artifact_ref"]
    generalist_refs = {
        "content/frontmatter_oc_core_1_3_master.tex",
        "content/17_oc_core_1_3_reader_guide.tex",
        "content/18_oc_core_1_3_source_audit.tex",
        "content/20_oc_core_1_3_theorem_roadmap.tex",
        "content/22_oc_core_1_3_operationalization_program.tex",
        "content/23_oc_core_1_3_empirical_execution_protocols.tex",
        "content/25_oc_core_1_3_toe_synthesis.tex",
        "content/26_oc_core_1_3_practical_utility.tex",
        "releases/oc_core_1_3/README.md",
        "releases/oc_core_1_3/journal_core/OC_CORE_1_3_JOURNAL_CORE_EN.md",
    }
    mathematician_refs = {
        "content/19_oc_core_1_3_foundational_consistency.tex",
        "content/20_oc_core_1_3_theorem_roadmap.tex",
        "content/21_oc_core_1_3_worked_examples.tex",
        "content/24_oc_core_1_3_proof_machinery.tex",
        "content/25_oc_core_1_3_toe_synthesis.tex",
        "appendix/A_notation.tex",
        "appendix/M_oc_core_1_3_proof_machinery_appendix.tex",
        "appendix/Q_oc_core_1_3_toe_support_dossiers.tex",
    }
    copychief_refs = {
        "oc_core_1_3_master_monograph.tex",
        "preamble.tex",
        "content/frontmatter_oc_core_1_3_master.tex",
        "content/17_oc_core_1_3_reader_guide.tex",
        "content/01_intro.tex",
        "content/03_model.tex",
        "content/05_discussion.tex",
        "content/14_disciplines_extended.tex",
        "content/25_oc_core_1_3_toe_synthesis.tex",
        "content/26_oc_core_1_3_practical_utility.tex",
        "appendix/F_oc_core_1_3_reviewer_navigation_matrix.tex",
        "appendix/R_oc_core_1_3_practical_utility_model_comparison_atlas.tex",
        "releases/oc_core_1_3/README.md",
        "releases/oc_core_1_3/journal_core/OC_CORE_1_3_JOURNAL_CORE_EN.md",
        ".zenodo.json",
    }
    if reviewer["reviewer_id"].endswith("HOSTILE_GENERALIST_SCIENTIST"):
        return ref in generalist_refs
    if reviewer["reviewer_id"].endswith("PRACTICAL_RED_TEAM"):
        return any(
            token in ref
            for token in [
                "content/26_oc_core_1_3_practical_utility.tex",
                "content/generated/oc_core_1_3_practical_utility_generated.tex",
                "appendix/R_oc_core_1_3_practical_utility_model_comparison_atlas.tex",
                "appendix/generated/oc_core_1_3_practical_utility_model_comparison_atlas_generated.tex",
                "content/14_disciplines_extended.tex",
                "releases/oc_core_1_3/journal_core/OC_CORE_1_3_JOURNAL_CORE_EN.md",
            ]
        )
    if reviewer["reviewer_id"].endswith("HOSTILE_MATHEMATICIAN"):
        return ref in mathematician_refs
    if reviewer["reviewer_id"].endswith("ELITE_COPY_CHIEF"):
        return ref in copychief_refs
    return True


def llm_output_schema(categories: list[str], artifact_refs: list[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "findings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "artifact_ref": {"type": "string", "enum": artifact_refs},
                        "severity": {"type": "string", "enum": SEVERITY_VALUES},
                        "category": {"type": "string", "enum": categories},
                        "section_ref": {"type": "string"},
                        "claim": {"type": "string"},
                        "evidence": {"type": "string"},
                        "required_action": {"type": "string"},
                        "status": {"type": "string", "enum": [OPEN_STATUS, NOT_ACTIONABLE_STATUS]},
                    },
                    "required": ["artifact_ref", "severity", "category", "section_ref", "claim", "evidence", "required_action", "status"],
                },
            }
        },
        "required": ["findings"],
    }


def build_llm_batches(units: list[dict[str, Any]], *, max_chars: int = 12000) -> list[list[dict[str, Any]]]:
    batches: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    current_chars = 0
    for unit in units:
        estimated = min(len(pattern_scan_text(REPO_ROOT / unit["artifact_ref"])), 2200) + 400
        if current and current_chars + estimated > max_chars:
            batches.append(current)
            current = []
            current_chars = 0
        current.append(unit)
        current_chars += estimated
    if current:
        batches.append(current)
    return batches


def render_llm_prompt(units: list[dict[str, Any]], reviewer: dict[str, Any]) -> str:
    joined_refs = " ".join(unit["artifact_ref"] for unit in units)
    extra_context: list[str] = []
    if any(token in joined_refs for token in ["26_oc_core_1_3_practical_utility", "practical_utility_model_comparison_atlas", "14_disciplines_extended", "JOURNAL_CORE_EN"]):
        extra_context.append(
            "Canonical practical-utility surface excerpt:\n"
            + unit_excerpt(json.dumps(load_json(SCIENCE_SURFACE_TARGETS["practical_utility"]), indent=2, ensure_ascii=True), max_chars=2500)
        )
    elif any(token in joined_refs for token in ["25_oc_core_1_3_toe_synthesis", "toe_support", "content/toe/"]):
        extra_context.append(
            "Canonical unified synthesis surface excerpt:\n"
            + unit_excerpt(json.dumps(load_json(SCIENCE_SURFACE_TARGETS["toe_synthesis"]), indent=2, ensure_ascii=True), max_chars=2500)
        )
    else:
        extra_context.append(
            "Canonical science spot summary excerpt:\n"
            + unit_excerpt(json.dumps(load_json(SCIENCE_SURFACE_TARGETS["spot"]), indent=2, ensure_ascii=True), max_chars=2000)
        )
    artifact_blocks: list[str] = []
    for unit in units:
        ref = unit["artifact_ref"]
        path = REPO_ROOT / ref
        text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
        artifact_blocks.append(
            "\n".join(
                [
                    "=== ARTIFACT START ===",
                    f"artifact_ref: {ref}",
                    f"artifact_role: {unit['unit_role']}",
                    "excerpt:",
                    unit_excerpt(text, max_chars=2200),
                    "=== ARTIFACT END ===",
                ]
            )
        )
    return "\n".join(
        [
            f"You are the Cerberus reviewer `{reviewer['label']}`.",
            f"Primary focus: {reviewer['focus']}.",
            "Return only strict JSON matching the supplied schema.",
            "If you see no real issue, return {\"findings\": []}.",
            "Use severity BLOCKER, MAJOR, MINOR, or NON_DEFECT_OBSERVATION only.",
            "Use only the allowed categories from the schema.",
            "Do not invent facts outside the provided artifact and canonical context.",
            "Flag only concrete, reviewer-actionable issues or explicit non-defect observations.",
            "Taste-only copy-edit preferences must be NON_DEFECT_OBSERVATION, not MINOR. "
            "Use MINOR language_style only for concrete grammar, punctuation, terminology, "
            "or meaning-risk defects that would reasonably matter to publication review.",
            "For every finding, set `artifact_ref` to the exact artifact from this batch.",
            "",
            *artifact_blocks,
            "",
            *extra_context,
        ]
    )


def call_codex_llm(
    *,
    run_dir: Path,
    units: list[dict[str, Any]],
    reviewer: dict[str, Any],
    codex_binary: str,
    codex_model: str,
    batch_index: int,
    timeout_seconds: int,
) -> dict[str, Any]:
    started_at = time.perf_counter()
    llm_dir = run_dir / "llm"
    llm_dir.mkdir(parents=True, exist_ok=True)
    artifact_refs = [unit["artifact_ref"] for unit in units]
    slug = sha256_text(f"{reviewer['reviewer_id']}::{batch_index}::{'|'.join(artifact_refs)}")[:16]
    schema_path = llm_dir / f"{slug}_schema.json"
    output_path = llm_dir / f"{slug}_output.json"
    prompt_path = llm_dir / f"{slug}_prompt.txt"
    dump_json(schema_path, llm_output_schema(reviewer["categories"], artifact_refs))
    prompt = render_llm_prompt(units, reviewer)
    prompt_path.write_text(prompt, encoding="utf-8")
    model_candidates = [codex_model]
    for fallback_model in ["gpt-5.3-codex-spark", "gpt-5.3-codex"]:
        if fallback_model not in model_candidates:
            model_candidates.append(fallback_model)
    retry_delays = [5, 15, 30]
    last_result: subprocess.CompletedProcess[str] | None = None
    last_command: list[str] | None = None
    payload: dict[str, Any] = {"findings": []}
    timeout_seconds = max(60, int(timeout_seconds))
    for model_index, active_model in enumerate(model_candidates):
        command = [
            codex_binary,
            "exec",
            "-C",
            str(REPO_ROOT),
            "-m",
            active_model,
            "--dangerously-bypass-approvals-and-sandbox",
            "--color",
            "never",
            "--output-schema",
            str(schema_path),
            "-o",
            str(output_path),
            "-",
        ]
        model_timed_out = False
        for attempt_index in range(len(retry_delays) + 1):
            if output_path.exists():
                output_path.unlink()
            try:
                result = subprocess.run(
                    command,
                    cwd=REPO_ROOT,
                    input=prompt,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=timeout_seconds,
                )
            except subprocess.TimeoutExpired as exc:
                stdout = exc.stdout if isinstance(exc.stdout, str) else ""
                stderr = exc.stderr if isinstance(exc.stderr, str) else ""
                timeout_note = (
                    f"TIMEOUT after {timeout_seconds}s for {reviewer['reviewer_id']} "
                    f"on batch {batch_index} with model {active_model}"
                )
                result = subprocess.CompletedProcess(
                    command,
                    124,
                    stdout=stdout,
                    stderr="\n".join(part for part in [stderr, timeout_note] if part),
                )
                model_timed_out = True
            last_result = result
            last_command = command
            if result.returncode == 0 and output_path.exists():
                payload = json.loads(output_path.read_text(encoding="utf-8"))
                break
            if model_timed_out:
                break
            if attempt_index < len(retry_delays):
                time.sleep(retry_delays[attempt_index])
        if last_result is not None and last_result.returncode == 0 and output_path.exists():
            break
        if model_index < len(model_candidates) - 1:
            time.sleep(10)
    if last_result is None or not (last_result.returncode == 0 and output_path.exists()):
        stderr_tail = ""
        if last_result is not None:
            stderr_tail = " ".join(last_result.stderr.splitlines()[-10:])
        raise RuntimeError(
            f"codex exec failed for {reviewer['reviewer_id']} on batch {batch_index}: "
            f"returncode={getattr(last_result, 'returncode', 'NONE')} stderr_tail={stderr_tail}"
        )
    return {
        "command": last_command,
        "returncode": last_result.returncode,
        "stdout_tail": "\n".join(last_result.stdout.splitlines()[-20:]),
        "stderr_tail": "\n".join(last_result.stderr.splitlines()[-20:]),
        "model_used": last_command[5] if last_command else codex_model,
        "prompt_ref": repo_rel(prompt_path),
        "schema_ref": repo_rel(schema_path),
        "output_ref": repo_rel(output_path),
        "artifact_refs": artifact_refs,
        "payload": payload,
        "duration_seconds": round(time.perf_counter() - started_at, 3),
    }


def llm_review(
    manifest: dict[str, Any],
    run_id: str,
    run_dir: Path,
    *,
    codex_binary: str = "codex",
    codex_model: str = "gpt-5.4-mini",
    artifact_ref_filter: set[str] | None = None,
    max_workers: int = 1,
    batch_max_chars: int = 12000,
    llm_timeout_seconds: int = 900,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    llm_runs: list[dict[str, Any]] = []
    unit_by_ref = {unit["artifact_ref"]: unit for unit in manifest["review_units"]}
    tasks: list[dict[str, Any]] = []
    for reviewer in manifest["llm_reviewer_roster"]:
        selected_units = [unit for unit in manifest["review_units"] if should_review_with_llm(unit, reviewer)]
        if artifact_ref_filter is not None:
            selected_units = [unit for unit in selected_units if unit["artifact_ref"] in artifact_ref_filter]
        for batch_index, batch_units in enumerate(build_llm_batches(selected_units, max_chars=batch_max_chars), start=1):
            tasks.append(
                {
                    "task_index": len(tasks),
                    "reviewer": reviewer,
                    "batch_index": batch_index,
                    "batch_units": batch_units,
                }
            )

    max_workers = max(1, min(max_workers, max(1, len(tasks))))
    run_payloads: dict[int, dict[str, Any]] = {}
    if tasks:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_map = {
                executor.submit(
                    call_codex_llm,
                    run_dir=run_dir,
                    units=task["batch_units"],
                    reviewer=task["reviewer"],
                    codex_binary=codex_binary,
                    codex_model=codex_model,
                    batch_index=task["batch_index"],
                    timeout_seconds=llm_timeout_seconds,
                ): task
                for task in tasks
            }
            for future in as_completed(future_map):
                task = future_map[future]
                run_payloads[task["task_index"]] = future.result()

    for task in tasks:
        reviewer = task["reviewer"]
        run_payload = run_payloads[task["task_index"]]
        llm_runs.append(
            {
                "reviewer_id": reviewer["reviewer_id"],
                "batch_index": task["batch_index"],
                "model_used": run_payload["model_used"],
                "artifact_refs": run_payload["artifact_refs"],
                "command": run_payload["command"],
                "returncode": run_payload["returncode"],
                "stdout_tail": run_payload["stdout_tail"],
                "stderr_tail": run_payload["stderr_tail"],
                "prompt_ref": run_payload["prompt_ref"],
                "schema_ref": run_payload["schema_ref"],
                "output_ref": run_payload["output_ref"],
                "duration_seconds": run_payload["duration_seconds"],
            }
        )
        for row in run_payload["payload"].get("findings", []):
            row = normalize_llm_finding_row(row)
            artifact_ref = row["artifact_ref"]
            unit = unit_by_ref.get(artifact_ref)
            if unit is None:
                continue
            findings.append(
                make_finding(
                    run_id=run_id,
                    reviewer_id=reviewer["reviewer_id"],
                    artifact_ref=artifact_ref,
                    artifact_id=unit["artifact_id"],
                    severity=row["severity"],
                    category=row["category"],
                    determinism_class=LLM_CLASS,
                    claim=row["claim"],
                    evidence=row["evidence"],
                    required_action=row["required_action"],
                    section_ref=row.get("section_ref") or unit["artifact_ref"],
                    status=row.get("status", OPEN_STATUS),
                )
            )
    return findings, {
        "review_count": len(llm_runs),
        "runs": llm_runs,
        "codex_model": codex_model,
        "codex_binary": codex_binary,
        "max_workers": max_workers,
        "batch_max_chars": batch_max_chars,
        "timeout_seconds": max(60, int(llm_timeout_seconds)),
        "artifact_ref_filter": sorted(artifact_ref_filter) if artifact_ref_filter is not None else None,
    }


def latest_open_finding_artifact_refs() -> set[str]:
    """Return artifact refs that still had actionable defects in the latest Cerberus ledger."""
    if not CERBERUS_SURFACE_TARGETS["findings"].exists():
        return set()
    try:
        payload = load_json(CERBERUS_SURFACE_TARGETS["findings"])
    except Exception:
        return set()
    refs: set[str] = set()
    for row in payload.get("findings", []):
        if row.get("status") != OPEN_STATUS:
            continue
        if row.get("severity") == "NON_DEFECT_OBSERVATION":
            continue
        artifact_ref = row.get("artifact_ref")
        if artifact_ref:
            refs.add(str(artifact_ref))
    return refs


def build_acceptance_cert(
    *,
    run_id: str,
    manifest: dict[str, Any],
    findings: list[dict[str, Any]],
    llm_gate_status: str,
    build_info: dict[str, Any],
) -> dict[str, Any]:
    open_by_severity = Counter(
        row["severity"] for row in findings if row["status"] == OPEN_STATUS and row["severity"] != "NON_DEFECT_OBSERVATION"
    )
    open_total = count_open_defects(findings)
    manifest_fingerprint = compute_fingerprint(manifest["fingerprint_refs"])
    status = (
        "PASS"
        if open_total == 0
        and llm_gate_status == "PASS"
        and not build_info.get("build_failed", False)
        and not build_info.get("build_skipped", False)
        else "FAIL_CLOSED"
    )
    return {
        "metadata": {
            "repo_sha": manifest["metadata"]["repo_sha"],
            "generated_at_utc": utc_now(),
            "surface": "logion/k0/governance/status/OC_CORE_1_3_CERBERUS_ACCEPTANCE_CERT_latest.json",
            "script": "oc_core_1_3_cerberus_review.py",
        },
        "run_id": run_id,
        "scope_id": manifest["scope_id"],
        "manifest_fingerprint": manifest_fingerprint,
        "status": status,
        "llm_gate_status": llm_gate_status,
        "open_findings_total": open_total,
        "open_findings_by_severity": {severity: open_by_severity.get(severity, 0) for severity in SEVERITY_VALUES if severity != "NON_DEFECT_OBSERVATION"},
        "reviewer_roster": {
            "deterministic_reviewers": [
                "CERBERUS_DETERMINISTIC__RELEASE_INTEGRITY",
                "CERBERUS_DETERMINISTIC__BUILD_AND_SCIENCE_GATE",
                "CERBERUS_DETERMINISTIC__STRUCTURE",
                "CERBERUS_DETERMINISTIC__THEOREM_AND_NOTATION",
                "CERBERUS_DETERMINISTIC__NUMERIC_AND_SURFACE",
                "CERBERUS_DETERMINISTIC__CITATION_AND_COMPARISON",
                "CERBERUS_DETERMINISTIC__LANGUAGE_AND_EDITORIAL",
                "CERBERUS_DETERMINISTIC__METADATA",
                "CERBERUS_DETERMINISTIC__TYPOGRAPHY",
            ],
            "llm_reviewers": [row["reviewer_id"] for row in manifest["llm_reviewer_roster"]],
        },
        "build_output": {
            "pdf_ref": build_info.get("pdf_ref", ""),
            "log_ref": build_info.get("log_ref", ""),
            "pdf_hash": build_info.get("pdf_hash", ""),
        },
        "input_fingerprint_refs": manifest["fingerprint_refs"],
        "hash_identity_groups": manifest["hash_identity_groups"],
        "acceptance_rule": "PASS requires zero open defect findings, a successful build, and a completed LLM gate.",
    }


def run_cerberus_review(
    repo_root: Path | None = None,
    *,
    skip_llm: bool = False,
    codex_binary: str = "codex",
    codex_model: str = "gpt-5.4-mini",
    llm_scope: str = "full",
    llm_artifact_refs: set[str] | None = None,
    llm_workers: int = 1,
    llm_batch_max_chars: int = 12000,
    llm_timeout_seconds: int = 900,
    build_mode: str = "full",
) -> dict[str, Any]:
    started_at = time.perf_counter()
    repo_root = repo_root or REPO_ROOT
    build_mode = build_mode.lower().strip()
    if build_mode not in {"full", "skip"}:
        raise ValueError("build_mode must be one of: full, skip")
    manifest = build_release_review_targets(repo_root)
    run_id = f"CERBERUS_RUN__{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}__{manifest['metadata']['repo_sha'][:8]}"
    run_dir = CERBERUS_RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    deterministic_findings: list[dict[str, Any]] = []
    deterministic_findings.extend(deterministic_release_integrity_review(manifest, run_id))
    build_findings, build_info = deterministic_build_review(manifest, run_id, run_dir, build_mode=build_mode)
    deterministic_findings.extend(build_findings)
    deterministic_findings.extend(deterministic_structure_review(manifest, run_id))
    deterministic_findings.extend(deterministic_theorem_notation_review(manifest, run_id))
    deterministic_findings.extend(deterministic_numeric_surface_review(manifest, run_id))
    deterministic_findings.extend(deterministic_citation_review(manifest, run_id))
    deterministic_findings.extend(deterministic_language_review(manifest, run_id))
    deterministic_findings.extend(deterministic_metadata_review(run_id))

    merged_deterministic = merge_findings(deterministic_findings)
    llm_findings: list[dict[str, Any]] = []
    llm_scope = llm_scope.lower().strip()
    if llm_scope not in {"full", "latest-findings", "refs"}:
        raise ValueError("llm_scope must be one of: full, latest-findings, refs")
    llm_artifact_refs = set(llm_artifact_refs or set())
    llm_ref_filter: set[str] | None = None
    if llm_scope == "latest-findings":
        llm_ref_filter = latest_open_finding_artifact_refs()
    elif llm_scope == "refs":
        llm_ref_filter = llm_artifact_refs

    llm_info: dict[str, Any] = {
        "review_count": 0,
        "runs": [],
        "codex_model": codex_model,
        "codex_binary": codex_binary,
        "llm_scope": llm_scope,
        "artifact_ref_filter": sorted(llm_ref_filter) if llm_ref_filter is not None else None,
        "max_workers": max(1, llm_workers),
        "batch_max_chars": max(1200, llm_batch_max_chars),
        "timeout_seconds": max(60, int(llm_timeout_seconds)),
    }
    llm_gate_status = "SKIPPED_DETERMINISTIC_OPEN_DEFECTS"
    if skip_llm:
        llm_gate_status = "SKIPPED_BY_FLAG"
    elif count_open_defects(merged_deterministic) == 0:
        try:
            llm_findings, llm_info = llm_review(
                manifest,
                run_id,
                run_dir,
                codex_binary=codex_binary,
                codex_model=codex_model,
                artifact_ref_filter=llm_ref_filter,
                max_workers=max(1, llm_workers),
                batch_max_chars=max(1200, llm_batch_max_chars),
                llm_timeout_seconds=max(60, int(llm_timeout_seconds)),
            )
            llm_info["llm_scope"] = llm_scope
            llm_info["artifact_ref_filter"] = sorted(llm_ref_filter) if llm_ref_filter is not None else None
            llm_gate_status = "PASS" if llm_scope == "full" else "TARGETED_PASS_NOT_RELEASE_GATE"
        except Exception as exc:
            llm_gate_status = "FAILED_TO_RUN"
            llm_findings.append(
                make_finding(
                    run_id=run_id,
                    reviewer_id="CERBERUS_LLM__ORCHESTRATOR",
                    artifact_ref=repo_rel(MASTER_MONOGRAPH_TEX),
                    severity="BLOCKER",
                    category="release_consistency",
                    determinism_class=LLM_CLASS,
                    claim="The mandatory Cerberus LLM review panel did not complete successfully.",
                    evidence=str(exc),
                    required_action="Repair the Codex CLI review path and rerun the full Cerberus panel.",
                )
            )

    merged_all = merge_findings([*merged_deterministic, *llm_findings])
    duration_seconds = round(time.perf_counter() - started_at, 3)
    acceptance = build_acceptance_cert(
        run_id=run_id,
        manifest=manifest,
        findings=merged_all,
        llm_gate_status=llm_gate_status if count_open_defects(merged_deterministic) == 0 or skip_llm else "SKIPPED_DETERMINISTIC_OPEN_DEFECTS",
        build_info=build_info,
    )
    run_summary = {
        "metadata": {
            "repo_sha": manifest["metadata"]["repo_sha"],
            "generated_at_utc": utc_now(),
            "surface": "logion/k0/governance/status/OC_CORE_1_3_CERBERUS_RUN_latest.json",
            "script": "oc_core_1_3_cerberus_review.py",
        },
        "run_id": run_id,
        "scope_id": manifest["scope_id"],
        "manifest_fingerprint": compute_fingerprint(manifest["fingerprint_refs"]),
        "build": build_info,
        "summary": {
            "deterministic_findings_total": len(merged_deterministic),
            "llm_findings_total": len(llm_findings),
            "open_findings_total": count_open_defects(merged_all),
            "llm_gate_status": acceptance["llm_gate_status"],
            "status": acceptance["status"],
            "duration_seconds": duration_seconds,
        },
        "llm": llm_info,
    }
    findings_payload = {
        "metadata": {
            "repo_sha": manifest["metadata"]["repo_sha"],
            "generated_at_utc": utc_now(),
            "surface": "logion/k0/governance/status/OC_CORE_1_3_CERBERUS_REVIEW_FINDINGS_latest.json",
            "script": "oc_core_1_3_cerberus_review.py",
        },
        "run_id": run_id,
        "scope_id": manifest["scope_id"],
        "findings": merged_all,
    }

    per_run_targets = run_dir / "OC_CORE_1_3_RELEASE_REVIEW_TARGETS.json"
    per_run_findings = run_dir / "OC_CORE_1_3_CERBERUS_REVIEW_FINDINGS.json"
    per_run_run = run_dir / "OC_CORE_1_3_CERBERUS_RUN.json"
    per_run_acceptance = run_dir / "OC_CORE_1_3_CERBERUS_ACCEPTANCE_CERT.json"
    dump_json(per_run_targets, manifest)
    dump_json(per_run_findings, findings_payload)
    dump_json(per_run_run, run_summary)
    dump_json(per_run_acceptance, acceptance)
    dump_json(CERBERUS_SURFACE_TARGETS["targets"], manifest)
    dump_json(CERBERUS_SURFACE_TARGETS["findings"], findings_payload)
    dump_json(CERBERUS_SURFACE_TARGETS["run"], run_summary)
    dump_json(CERBERUS_SURFACE_TARGETS["acceptance"], acceptance)

    return {
        "run_id": run_id,
        "run_dir": repo_rel(run_dir),
        "targets": manifest,
        "findings": findings_payload,
        "run": run_summary,
        "acceptance": acceptance,
    }


def validate_existing_cerberus_bundle(repo_root: Path | None = None, *, require_clean: bool = False) -> list[str]:
    repo_root = repo_root or REPO_ROOT
    errors: list[str] = []
    for surface_id, path in CERBERUS_SURFACE_TARGETS.items():
        if not path.exists():
            errors.append(f"Cerberus surface `{surface_id}` is missing: {repo_rel(path)}")
    if errors:
        return errors

    targets = load_json(CERBERUS_SURFACE_TARGETS["targets"])
    findings_payload = load_json(CERBERUS_SURFACE_TARGETS["findings"])
    run_payload = load_json(CERBERUS_SURFACE_TARGETS["run"])
    acceptance = load_json(CERBERUS_SURFACE_TARGETS["acceptance"])
    current_sha = git_head_sha(repo_root)
    manifest_fingerprint = compute_fingerprint(targets.get("fingerprint_refs", []))

    if targets.get("metadata", {}).get("repo_sha") != current_sha:
        errors.append("Cerberus targets surface does not match the current repository HEAD.")
    if run_payload.get("metadata", {}).get("repo_sha") != current_sha:
        errors.append("Cerberus run surface does not match the current repository HEAD.")
    if acceptance.get("metadata", {}).get("repo_sha") != current_sha:
        errors.append("Cerberus acceptance surface does not match the current repository HEAD.")
    if run_payload.get("run_id") != findings_payload.get("run_id") or run_payload.get("run_id") != acceptance.get("run_id"):
        errors.append("Cerberus latest surfaces disagree on the active run_id.")
    if run_payload.get("scope_id") != targets.get("scope_id") or acceptance.get("scope_id") != targets.get("scope_id"):
        errors.append("Cerberus latest surfaces disagree on the active scope_id.")
    if run_payload.get("manifest_fingerprint") != manifest_fingerprint:
        errors.append("Cerberus run fingerprint does not match the current manifest inputs.")
    if acceptance.get("manifest_fingerprint") != manifest_fingerprint:
        errors.append("Cerberus acceptance fingerprint does not match the current manifest inputs.")

    findings = findings_payload.get("findings", [])
    for row in findings:
        if row.get("run_id") != run_payload.get("run_id"):
            errors.append(f"Cerberus finding `{row.get('finding_id', 'UNKNOWN')}` is attached to the wrong run_id.")
        if row.get("severity") not in SEVERITY_VALUES:
            errors.append(f"Cerberus finding `{row.get('finding_id', 'UNKNOWN')}` uses an invalid severity.")
        if row.get("category") not in CATEGORY_VALUES:
            errors.append(f"Cerberus finding `{row.get('finding_id', 'UNKNOWN')}` uses an invalid category.")

    open_total = count_open_defects(findings)
    if run_payload.get("summary", {}).get("open_findings_total") != open_total:
        errors.append("Cerberus run summary open-findings total does not match the findings ledger.")
    if acceptance.get("open_findings_total") != open_total:
        errors.append("Cerberus acceptance certificate open-findings total does not match the findings ledger.")

    if require_clean:
        if acceptance.get("status") != "PASS":
            errors.append("Cerberus acceptance certificate is not PASS.")
        if acceptance.get("llm_gate_status") != "PASS":
            errors.append("Cerberus LLM gate is not PASS.")
        if open_total != 0:
            errors.append("Cerberus still has open defect findings.")

    return errors
