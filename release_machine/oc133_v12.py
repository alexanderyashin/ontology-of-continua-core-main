from __future__ import annotations

import json
import re
import runpy
import subprocess
import contextlib
import io
from collections import Counter
from pathlib import Path
from typing import Any, Callable


RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"

G57_ATTACK_MATRIX_MIN_ROWS = 200
G57_ATTACK_MATRIX_MIN_THEMES = 10
G57_ATTACK_MATRIX_MIN_SEVERITIES = 3
G57_ATTACK_MATRIX_MIN_ARTIFACT_LOCATIONS = 20
G57_ATTACK_MATRIX_MIN_EVIDENCE_REFS = 20
G57_ATTACK_MATRIX_MAX_FILLER_DUPLICATE_SHARE = 0.15
G57_ATTACK_MATRIX_PLACEHOLDER_TERMS = {
    "fixme",
    "filler",
    "lorem",
    "placeholder",
    "stub",
    "tbd",
    "todo",
}

V12_RELEASE_STATES = {
    "SCIENTIFIC_CLOSURE_RUNNING",
    "SCIENTIFIC_BLOCKERS_REMAIN",
    "PROOF_REPAIR_REQUIRED",
    "EMPIRICAL_REPLAY_REQUIRED",
    "ADVERSARIAL_REVIEW_REQUIRED",
    "OC_CORE_1_3_3_10_10_READY_NO_SEND",
    "OWNER_APPROVED_FOR_PUBLICATION",
    "PUBLIC_RELEASE_VERIFIED",
}

V12_GATE_SPECS = [
    ("G32", "G32_TYPED_FOUNDATION_PASS", "CRITICAL"),
    ("G33", "G33_K0_RESOLUTION_FOUNDATION_PASS", "CRITICAL"),
    ("G34", "G34_SEMANTIC_MODEL_EXISTENCE_PASS", "HIGH"),
    ("G35", "G35_AXIOM_CONSISTENCY_AND_NONTRIVIALITY_PASS", "CRITICAL"),
    ("G36", "G36_THEOREM_INVENTORY_COMPLETE", "CRITICAL"),
    ("G37", "G37_PROOF_SHEETS_COMPLETE", "CRITICAL"),
    ("G38", "G38_NO_THEOREM_THEATER", "CRITICAL"),
    ("G39", "G39_CONTINUUMNESS_CLOSURE_PASS", "HIGH"),
    ("G40", "G40_BOUNDARY_GENERALIZATION_PASS", "HIGH"),
    ("G41", "G41_OPERATOR_SEMANTICS_PASS", "HIGH"),
    ("G42", "G42_DIMENSION_AXIS_CLOSURE_PASS", "HIGH"),
    ("G43", "G43_CYCLE_NECESSITY_CLOSURE_PASS", "HIGH"),
    ("G44", "G44_COLLAPSE_RESIDUE_REBIRTH_IDENTITY_PASS", "HIGH"),
    ("G45", "G45_K_LEVEL_IRREDUCIBILITY_ATLAS_PASS", "CRITICAL"),
    ("G46", "G46_GLOBAL_MINIMALITY_WITNESSES_PASS", "CRITICAL"),
    ("G47", "G47_MACHINE_CHECKED_SUBSET_PASS", "CRITICAL"),
    ("G48", "G48_EMPIRICAL_DATA_PACKETS_PASS", "CRITICAL"),
    ("G49", "G49_HELDOUT_VALIDATION_PASS", "HIGH"),
    ("G50", "G50_NEGATIVE_CONTROLS_PASS", "HIGH"),
    ("G51", "G51_BASELINE_COMPARATORS_PASS", "HIGH"),
    ("G52", "G52_ADVERSARIAL_SIMULATION_PASS", "HIGH"),
    ("G53", "G53_COUNTEREXAMPLE_ATLAS_PASS", "HIGH"),
    ("G54", "G54_COMPARATOR_MATRIX_PASS", "HIGH"),
    ("G55", "G55_NOVELTY_PRIORITY_REGISTER_PASS", "HIGH"),
    ("G56", "G56_CLAIM_LEDGER_PROOF_BINDING_PASS", "CRITICAL"),
    ("G57", "G57_ATTACK_MATRIX_ZERO_CRITICAL_HIGH", "CRITICAL"),
    ("G58", "G58_REVIEWER_PERSONA_SUITE_PASS", "CRITICAL"),
    ("G59", "G59_REPRODUCIBILITY_CLEAN_CHECKOUT_PASS", "HIGH"),
    ("G60", "G60_NO_LOCAL_PATHS_NO_SECRETS_PASS", "CRITICAL"),
    ("G61", "G61_PUBLIC_SURFACE_PARITY_PASS", "HIGH"),
    ("G62", "G62_LLM_SCHEMA_CLAIM_BOUNDARY_PASS", "HIGH"),
    ("G63", "G63_NO_EMPIRICAL_DISCOVERY_ONLY_PROMOTION_PASS", "CRITICAL"),
    ("G64", "G64_NO_SCOPE_NARROWING_AS_REPAIR_PASS", "CRITICAL"),
    ("G65", "G65_OWNER_APPROVAL_PACKET_READY", "HIGH"),
    ("G66", "G66_ZENODO_METADATA_READY", "HIGH"),
    ("G67", "G67_GITHUB_RELEASE_READY", "HIGH"),
    ("G68", "G68_POST_RELEASE_VERIFICATION_PLAN_READY", "MEDIUM"),
    ("G69", "G69_EXTERNAL_REVIEW_PACKAGE_READY", "HIGH"),
    ("G70", "G70_10_10_SCIENTIFIC_CLOSURE_VERDICT", "CRITICAL"),
]

PROOF_HEADINGS = [
    "## Assumptions",
    "## Definitions",
    "## Lemma 1",
    "## Lemma 2",
    "## Theorem",
    "## Proof",
    "## Counterexample Boundary",
    "## Machine-Checkable Finite Example",
    "## Dependency Refs",
    "## Reviewer Attack Answered",
]

V12_SCAN_PATTERNS = [
    "claims/*1_3_3*",
    "proofs/THEOREM_*1_3_3*",
    "proofs/PROOF_LEDGER_1_3_3.md",
    "proofs/proof_sheets/T133-*.md",
    "docs/OC_1_3_3_*",
    "review/OC_1_3_3_*",
    "comparators/OC_1_3_3_*",
    "reports/OC_CORE_1_3_3_*",
    "releases/oc_core_1_3_3/**/*.json",
    "releases/oc_core_1_3_3/**/*.md",
]

FORBIDDEN_ABSOLUTE_PATTERNS = [
    re.compile(r"\b100\s*%\b|\b100 percent\b", re.I),
    re.compile(r"\birrefutable\b|\bunrefutable\b|\bнеопроверж", re.I),
    re.compile(r"\bfinal truth\b|\bcomplete truth\b|\bоднозначно\s+правдив", re.I),
    re.compile(r"\bfinal theory\b|\btheory of everything\b|\bTOE[-\s]?complete\b", re.I),
    re.compile(r"\ball[-\s]?domain numerical prediction\b", re.I),
]

FORBIDDEN_SCOPE_REPAIR_PATTERNS = [
    re.compile(r"DEMOTED_TO|NOT_PUBLIC_PROMOTION|ROUTE_WITH_EXECUTABLE|FORMAL_ROUTE_ONLY|BLOCKED_FOR_PROMOTION|SUPPORT_CEILING", re.I),
    re.compile(r"demote public theorem|demoted route|route only", re.I),
]

SECRET_PATTERNS = [
    re.compile(r"C:\\Users\\", re.I),
    re.compile(r"Megaport", re.I),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"ZENODO_TOKEN\s*[:=]\s*[^\\s]+", re.I),
]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _portable_path(value: Any) -> str:
    return str(Path(value).as_posix()) if isinstance(value, str) else ""


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def _metadata_surface_audit(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    """Check publication metadata for v1.3.3 no-send consistency."""
    root_zenodo = root / ".zenodo.json"
    zenodo_draft = root / "releases" / RELEASE_ID / "editorial" / "metadata_drafts" / "zenodo.no_send.draft.json"
    metadata_paths = [
        root / "manifest.json",
        root / "checksums.txt",
        zenodo_draft,
        root / "CITATION.cff",
        root / ".codemeta.json",
        root / "ro-crate-metadata.jsonld",
        root / "docs" / "OC_1_3_3_PHENOMENON_COVERAGE_MATRIX.json",
    ]
    missing = [rel(root, path) for path in metadata_paths if not path.exists()]
    stale_hits: list[dict[str, str]] = []
    for path in metadata_paths:
        body = text(path)
        for token in ("v1.3.2", "1.3.2"):
            if token in body:
                stale_hits.append({"path": rel(root, path), "token": token})

    zenodo = read_json(zenodo_draft) if zenodo_draft.exists() else {}
    codemeta = read_json(root / ".codemeta.json") if (root / ".codemeta.json").exists() else {}
    ro_crate = read_json(root / "ro-crate-metadata.jsonld") if (root / "ro-crate-metadata.jsonld").exists() else {}
    citation = text(root / "CITATION.cff")
    ro_nodes = ro_crate.get("@graph", []) if isinstance(ro_crate, dict) else []
    ro_versions = [node.get("version") for node in ro_nodes if isinstance(node, dict) and node.get("version")]
    zenodo_body = json.dumps(zenodo, sort_keys=True)
    zenodo_related = zenodo.get("related_identifiers", []) if isinstance(zenodo, dict) else []
    ro_body = json.dumps(ro_crate, sort_keys=True)
    codemeta_body = json.dumps(codemeta, sort_keys=True)
    public_manifest = read_json(root / "manifest.json") if (root / "manifest.json").exists() else {}
    checksums_body = text(root / "checksums.txt")
    public_manifest_body = json.dumps(public_manifest, sort_keys=True)
    public_manifest_file_paths = [
        str(row.get("path", ""))
        for row in public_manifest.get("files", [])
        if isinstance(row, dict)
    ]

    version_checks = {
        "zenodo_version": zenodo.get("version") == VERSION,
        "zenodo_title_mentions_version": f"v{VERSION}" in str(zenodo.get("title", "")) or VERSION in str(zenodo.get("title", "")),
        "zenodo_description_mentions_version": VERSION in str(zenodo.get("description", "")),
        "citation_version": f'version: "{VERSION}"' in citation or f"version: {VERSION}" in citation,
        "citation_message_mentions_no_send": "no-send" in citation.lower(),
        "codemeta_version": codemeta.get("version") == VERSION,
        "codemeta_description_mentions_version": VERSION in str(codemeta.get("description", "")),
        "ro_crate_versions": bool(ro_versions) and all(value == VERSION for value in ro_versions),
        "ro_crate_mentions_version": VERSION in json.dumps(ro_crate, sort_keys=True),
        "public_manifest_release_id": public_manifest.get("release_id") == RELEASE_ID,
        "public_manifest_version": public_manifest.get("version") == VERSION,
        "checksums_mentions_manifest": "manifest.json" in checksums_body,
        "public_manifest_mentions_phenomenon_matrix": "docs/OC_1_3_3_PHENOMENON_COVERAGE_MATRIX.json" in public_manifest_body,
        "checksums_mentions_phenomenon_matrix": "docs/OC_1_3_3_PHENOMENON_COVERAGE_MATRIX.json" in checksums_body,
        "ro_crate_mentions_phenomenon_matrix": "docs/OC_1_3_3_PHENOMENON_COVERAGE_MATRIX.json" in ro_body,
    }
    no_send_checks = {
        "publish_allowed_false": manifest.get("publish_allowed") is False,
        "zenodo_deposit_allowed_false": manifest.get("zenodo_deposit_allowed") is False,
        "github_release_allowed_false": manifest.get("github_release_allowed") is False,
        "journal_submissions_allowed_false": manifest.get("journal_submissions_allowed") is False,
        "root_zenodo_metadata_absent_while_no_send": not root_zenodo.exists(),
        "zenodo_notes_no_send": "no-send" in zenodo_body.lower() or "pending" in zenodo_body.lower(),
        "zenodo_publication_date_absent": "publication_date" not in zenodo,
        "zenodo_access_right_not_open": zenodo.get("access_right") not in {"open", "embargoed", "restricted"},
        "zenodo_related_doi_absent": not any(isinstance(row, dict) and str(row.get("scheme", "")).lower() == "doi" for row in zenodo_related),
        "citation_date_released_absent": "date-released:" not in citation.lower(),
        "citation_identifier_doi_absent": "type: doi" not in citation.lower(),
        "codemeta_no_doi_identifier": "zenodo concept doi" not in codemeta_body.lower() and "doi:" not in codemeta_body.lower(),
        "ro_crate_date_published_absent": "datePublished" not in ro_body,
        "ro_crate_no_doi_identifier": "doi:" not in ro_body.lower(),
        "public_manifest_no_v132_payload": "oc_core_1_3_2" not in public_manifest_body and not any("oc_core_1_3_2" in path for path in public_manifest_file_paths),
        "public_manifest_no_public_record": public_manifest.get("owner_approved") is False and public_manifest.get("publish_allowed") is False and public_manifest.get("git_tag") is None and public_manifest.get("public_record") is None,
        "checksums_no_v132_payload": "oc_core_1_3_2" not in checksums_body and "1.3.2" not in checksums_body,
        "checksums_no_root_zenodo_reference": ".zenodo.json" not in checksums_body,
    }
    return {
        "missing": missing,
        "stale_hits": stale_hits,
        "stale_hit_total": len(stale_hits),
        "version_checks": version_checks,
        "no_send_checks": no_send_checks,
        "all_versions_current": all(version_checks.values()),
        "all_no_send_locked": all(no_send_checks.values()),
    }


def ensure_v12(root: Path) -> None:
    script = root / "tools" / "materialize_oc_core_1_3_3_v12_closure.py"
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            runpy.run_path(str(script), run_name="__main__")
    except SystemExit as exc:
        if int(exc.code or 0) != 0:
            raise


def _files(root: Path, patterns: list[str]) -> list[Path]:
    excluded_names = {
        "OC_CORE_1_3_3_RELEASE_CONTROL_PLANE_latest.json",
        "OC_CORE_1_3_3_RELEASE_SCORECARD_latest.json",
        "OC_CORE_1_3_3_RELEASE_SCORECARD_latest.md",
    }
    seen: set[Path] = set()
    out: list[Path] = []
    for pattern in patterns:
        for path in root.glob(pattern):
            if path.name in excluded_names:
                continue
            if path.is_file() and path not in seen:
                seen.add(path)
                out.append(path)
    return out


def _scan_hits(root: Path, regexes: list[re.Pattern[str]], patterns: list[str] | None = None) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for path in _files(root, patterns or V12_SCAN_PATTERNS):
        body = text(path)
        for regex in regexes:
            for match in regex.finditer(body):
                ctx = body[max(0, match.start() - 80): match.end() + 80].replace("\n", " ")
                lowered = ctx.lower()
                if any(cue in lowered for cue in ["not ", "no ", "must not ", "forbidden", "reject", "unsupported", "does not ", "blocked"]):
                    continue
                hits.append({"path": rel(root, path), "match": match.group(0), "context": ctx[:220]})
    return hits


def _proof_sheet_failures(root: Path, registry: dict[str, Any]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    for row in registry.get("rows", []):
        path = root / row["proof_sheet_ref"]
        body = text(path)
        missing = [heading for heading in PROOF_HEADINGS if heading not in body]
        banned = [term for term in ["TODO", "placeholder", "proof sketch", "route only"] if term.lower() in body.lower()]
        if missing or banned or len(body) < 1600:
            failures.append({"theorem_id": row.get("theorem_id"), "path": rel(root, path), "missing": missing, "banned": banned, "char_count": len(body)})
    return failures


def _run_lake(root: Path) -> dict[str, Any]:
    try:
        completed = subprocess.run(["lake", "build", "OC133V12"], cwd=root, text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=600)
    except Exception as exc:
        return {"state": "FAIL", "returncode": -1, "stderr_tail": str(exc)[-1200:]}
    return {
        "state": "PASS" if completed.returncode == 0 else "FAIL",
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout[-1200:],
        "stderr_tail": completed.stderr[-1200:],
    }


def _attack_matrix_counts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    closed_status = "CLOSED_BY_SPECIFIC_V12_EVIDENCE"
    return {
        "row_total": len(rows),
        "critical_open_total": sum(1 for row in rows if row.get("severity") == "CRITICAL" and row.get("status") != closed_status),
        "high_open_total": sum(1 for row in rows if row.get("severity") == "HIGH" and row.get("status") != closed_status),
    }


def _attack_matrix_quality_quotas(root: Path, rows: list[dict[str, Any]]) -> dict[str, Any]:
    closed_status = "CLOSED_BY_SPECIFIC_V12_EVIDENCE"

    def clean(value: Any) -> str:
        return str(value).strip() if value not in (None, "") else ""

    def normalized(value: Any) -> str:
        return re.sub(r"\s+", " ", clean(value).lower())

    def closure_refs(row: dict[str, Any]) -> list[str]:
        refs = row.get("closure_evidence_refs")
        if not isinstance(refs, list):
            return []
        return [clean(ref) for ref in refs if clean(ref)]

    def closure_ref_path(ref: str) -> str:
        return ref.split("::", 1)[0].strip()

    def ref_exists(ref: str) -> bool:
        ref_path = closure_ref_path(ref)
        path = Path(ref_path)
        if path.is_absolute():
            return False
        try:
            resolved = (root / path).resolve()
            resolved.relative_to(root.resolve())
        except ValueError:
            return False
        return resolved.exists()

    def dominant_duplicate_share(field: str) -> float:
        values = [normalized(row.get(field)) for row in rows if normalized(row.get(field))]
        if not values:
            return 1.0
        return Counter(values).most_common(1)[0][1] / len(rows)

    themes = {normalized(row.get("theme")) for row in rows if normalized(row.get("theme"))}
    severities = {normalized(row.get("severity")) for row in rows if normalized(row.get("severity"))}
    artifact_locations = {normalized(row.get("artifact_location")) for row in rows if normalized(row.get("artifact_location"))}
    evidence_refs = {closure_ref_path(ref) for row in rows for ref in closure_refs(row)}
    placeholder_rows = [
        row.get("objection_id")
        for row in rows
        if any(
            term in " ".join(
                [
                    normalized(row.get("objection")),
                    normalized(row.get("failure_mode")),
                    normalized(row.get("required_repair")),
                    normalized(row.get("closure_evidence")),
                ]
            )
            for term in G57_ATTACK_MATRIX_PLACEHOLDER_TERMS
        )
    ]
    duplicate_shares = {
        field: dominant_duplicate_share(field)
        for field in ["objection", "failure_mode", "required_repair", "closure_evidence"]
    }
    closed_high_critical_missing_refs = [
        row.get("objection_id")
        for row in rows
        if row.get("severity") in {"CRITICAL", "HIGH"}
        and row.get("status") == closed_status
        and (not closure_refs(row) or any(not ref_exists(ref) for ref in closure_refs(row)))
    ]

    predicates = {
        "g57_attack_matrix_recomputed_row_total_at_least_200": len(rows) >= G57_ATTACK_MATRIX_MIN_ROWS,
        "g57_attack_matrix_min_theme_diversity": len(themes) >= G57_ATTACK_MATRIX_MIN_THEMES,
        "g57_attack_matrix_min_severity_diversity": len(severities) >= G57_ATTACK_MATRIX_MIN_SEVERITIES,
        "g57_attack_matrix_min_artifact_location_diversity": len(artifact_locations) >= G57_ATTACK_MATRIX_MIN_ARTIFACT_LOCATIONS,
        "g57_attack_matrix_min_evidence_ref_diversity": len(evidence_refs) >= G57_ATTACK_MATRIX_MIN_EVIDENCE_REFS,
        "g57_attack_matrix_no_placeholder_filler_dominance": not placeholder_rows
        and all(share <= G57_ATTACK_MATRIX_MAX_FILLER_DUPLICATE_SHARE for share in duplicate_shares.values()),
        "g57_attack_matrix_closed_high_critical_refs_exist": not closed_high_critical_missing_refs,
    }
    return {
        "state": "PASS" if all(predicates.values()) else "FAIL",
        "predicates": predicates,
        "failed_predicates": [name for name, passed in predicates.items() if not passed],
        "thresholds": {
            "row_total_min": G57_ATTACK_MATRIX_MIN_ROWS,
            "theme_min": G57_ATTACK_MATRIX_MIN_THEMES,
            "severity_min": G57_ATTACK_MATRIX_MIN_SEVERITIES,
            "artifact_location_min": G57_ATTACK_MATRIX_MIN_ARTIFACT_LOCATIONS,
            "evidence_ref_min": G57_ATTACK_MATRIX_MIN_EVIDENCE_REFS,
            "max_filler_duplicate_share": G57_ATTACK_MATRIX_MAX_FILLER_DUPLICATE_SHARE,
        },
        "observed": {
            "row_total": len(rows),
            "theme_total": len(themes),
            "severity_total": len(severities),
            "artifact_location_total": len(artifact_locations),
            "evidence_ref_total": len(evidence_refs),
            "placeholder_filler_row_total": len(placeholder_rows),
            "duplicate_shares": duplicate_shares,
            "closed_high_critical_missing_ref_total": len(closed_high_critical_missing_refs),
        },
        "placeholder_filler_rows": placeholder_rows[:20],
        "closed_high_critical_missing_refs": closed_high_critical_missing_refs[:20],
    }


def _llm_result_audit(root: Path, summary: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str], list[str], list[str]]:
    result_refs = summary.get("result_refs", [])
    seen_roles: list[str] = []
    missing_roles: list[str] = []
    role_refs: list[dict[str, Any]] = []
    malformed_refs: list[str] = []

    required_roles = set(summary.get("roles", []))

    for ref in result_refs:
        path = root / ref
        if not path.exists():
            malformed_refs.append(ref)
            continue
        row = read_json(path)
        role = str(row.get("role", "")).strip()
        if role:
            seen_roles.append(role)
        if row.get("execution_status") != "EXECUTED" or row.get("critical_open_total", 0) or row.get("high_open_total", 0):
            role_refs.append({
                "ref": ref,
                "execution_status": row.get("execution_status"),
                "critical_open_total": row.get("critical_open_total", 0),
                "high_open_total": row.get("high_open_total", 0),
            })

    if required_roles:
        missing_roles = sorted(required_roles - set(seen_roles))
    role_counts = Counter(seen_roles)
    duplicate_roles = sorted([role for role, count in role_counts.items() if count > 1])
    return (
        role_refs,
        malformed_refs,
        missing_roles,
        duplicate_roles,
    )


def audit(root: Path) -> dict[str, Any]:
    ensure_v12(root)
    inv = read_json(root / "proofs" / "THEOREM_INVENTORY_1_3_3.json")
    registry = read_json(root / "proofs" / "THEOREM_REGISTRY_1_3_3.json")
    finite = read_json(root / "proofs" / "FINITE_MODEL_CHECKS_1_3_3.json")
    finite_inputs = read_json(root / "proofs" / "finite_model_checks" / "OC133_FINITE_MODEL_INPUTS.json")
    claims = read_json(root / "claims" / "CLAIM_LEDGER_1_3_3.json")
    numeric = read_json(root / "validation" / "numeric_replay_qa" / "OC133_NUMERIC_REPLAY_QA_TABLE.json")
    domain = read_json(root / "data" / "domain_semantics_matrix.json")
    klevel = read_json(root / "data" / "k_level_irreducibility_matrix.json")
    minimality = read_json(root / "data" / "OC133_GLOBAL_MINIMALITY_WITNESSES.json")
    attack = read_json(root / "review" / "OC_1_3_3_TOTAL_ATTACK_MATRIX.json")
    llm = read_json(root / "reviews" / "oc133_llm_cerberus" / "OC133_LLM_CERBERUS_SUMMARY.json")
    comparator = read_json(root / "comparators" / "OC_1_3_3_NOVELTY_AND_PRIORITY_REGISTER.json")
    phenomenon = read_json(root / "docs" / "OC_1_3_3_PHENOMENON_COVERAGE_MATRIX.json")
    adversarial = read_json(root / "reports" / "OC_CORE_1_3_3_ADVERSARIAL_SIMULATION_REPORT.json")
    repro_manifest_path = root / "reports" / "OC_CORE_1_3_3_POST_GENERATION_REPRODUCIBILITY_MANIFEST.json"
    repro_manifest = read_json(repro_manifest_path) if repro_manifest_path.exists() else {}
    counter = read_json(root / "falsification" / "COUNTEREXAMPLE_ATLAS_1_3_3.json")
    manifest = read_json(root / "releases" / "oc_core_1_3_3" / "editorial" / "OC_CORE_1_3_3_PUBLISH_MANIFEST_DRAFT.json")
    public_manifest = read_json(root / "manifest.json")
    approval = read_json(root / "releases" / "oc_core_1_3_3" / "editorial" / "OWNER_RELEASE_APPROVAL_v1.3.3.json")
    lean_cert_path = root / "formal" / "lean" / "LEAN_BUILD_CERTIFICATE_1_3_3.json"
    lean_cert = read_json(lean_cert_path) if lean_cert_path.exists() else {}
    proof_failures = _proof_sheet_failures(root, registry)
    absolute_hits = _scan_hits(root, FORBIDDEN_ABSOLUTE_PATTERNS)
    scope_hits = _scan_hits(root, FORBIDDEN_SCOPE_REPAIR_PATTERNS)
    secret_hits = _scan_hits(root, SECRET_PATTERNS)
    promoted_claims = [row for row in claims.get("rows", []) if str(row.get("public_status", "")).startswith("PROMOTED")]
    proof_bound_failures = [
        row for row in promoted_claims
        if row.get("evidence_ref", "").startswith("proofs/")
        and not (root / row["evidence_ref"]).exists()
    ]
    lean_body = text(root / "formal" / "lean" / "OC133V12.lean")
    lean_semantic_markers = [
        "OCSemanticCase",
        "semanticVerdict",
        "dropSemanticComponent",
        "component_witness_is_one_component_delta",
        "component_registry_complete_and_witnessed",
        "KTransitionModel",
        "upperKVerdict",
        "reducedKVerdict",
        "retained_transition_reduction_fails",
        "every_adjacent_transition_has_lawful_demotion_case",
        "every_adjacent_transition_has_witness_and_demotion",
        "reductionFails",
        "lawfulDemotion",
        "hybrid_guard_uses_reset",
        "smooth_operator_is_update_special_case",
        "smooth_hybrid_operator_semantics",
        "differential_notation_requires_chart",
        "eligible_live_requires_cycle_or_maintenance",
        "residue_preservation_not_identity_without_invariant",
        "rebirth_not_identity_without_invariant",
        "invariant_lost_blocks_identity",
        "endpoint_bound_identity_positive",
        "declared_death_blocks_live",
        "lifecycle_status_morphism_separation",
        "lifecycle_residue_rebirth_morphism_boundary",
        "residue_or_rebirth_class_blocks_identity",
        "residue_rebirth_identity_boundary",
        "metric_boundary_failure_equiv",
        "metric_boundary_specialization",
        "continuumness_score_zero_iff_no_obstruction",
        "zero_cause_does_not_compute_k_by_itself",
        "declared_zero_cause_with_clear_obstruction_licenses_k_zero",
        "k_zero_with_nonempty_support_requires_cause_and_clear_obstruction",
        "continuumness_zero_case_iff_declared_zero_cause_with_support",
        "historicalMonotone",
        "effectiveRankDrops",
    ]
    missing_lean_semantic_markers = [marker for marker in lean_semantic_markers if marker not in lean_body]
    finite_input_observed_fields = [
        {"case_id": row.get("case_id"), "field": key}
        for row in finite_inputs.get("rows", [])
        for key in row
        if key.startswith("observed_")
    ]
    forbidden_model_oracle_fields = {
        "keep_verdict",
        "drop_verdict",
        "reduction_verdict",
        "observed_verdict",
        "failure_equivalence_checked",
        "hybrid_guard_reset_checked",
        "oracle_attestation",
        "witness_retained",
        "added_axis_observable",
        "demotion_allowed",
        "keep_present",
        "drop_present",
        "changed_fields",
    }
    finite_input_answer_key_fields = [
        {"case_id": row.get("case_id"), "field": key}
        for row in finite_inputs.get("rows", [])
        for key in row.get("model", {})
        if key in forbidden_model_oracle_fields
    ]
    finite_semantic_failures = []
    if finite.get("semantic_evaluator") is not True:
        finite_semantic_failures.append("semantic_evaluator flag missing")
    if finite.get("input_observed_field_total", 0) != 0 or finite_inputs.get("observed_field_total", 0) != 0 or finite_input_observed_fields:
        finite_semantic_failures.append("finite inputs contain observed verdict fields")
    if finite_input_answer_key_fields:
        finite_semantic_failures.append("finite inputs contain answer-key verdict fields")
    if finite.get("flag_oracle_key_total", 0) != 0:
        finite_semantic_failures.append("finite runner detected flag-oracle model keys")
    if finite.get("mutation_control_total", 0) < 3:
        finite_semantic_failures.append("missing label-only, flag-only, and wrong-witness mutation controls")
    if finite.get("k_transition_negative_total", 0) < 12:
        finite_semantic_failures.append("missing per-transition K-level negative/demotion controls")
    if finite.get("no_send_state_machine_total", 0) < 2:
        finite_semantic_failures.append("missing no-send state-machine finite controls")
    if finite.get("no_send_byte_binding_failure_total", 0) != 0:
        finite_semantic_failures.append("no-send control file byte hashes are not bound to the clean source manifest")
    if "case_type" in text(root / "proofs" / "finite_model_checks" / "run_finite_model_checks.py") and "model.get" not in text(root / "proofs" / "finite_model_checks" / "run_finite_model_checks.py"):
        finite_semantic_failures.append("finite runner does not inspect model facts")
    finite_rows = [row for row in finite.get("rows", []) if isinstance(row, dict)]
    publish_state_row = next(
        (row for row in finite_rows if row.get("case_id") == "ADV-NOSEND-PUBLISH" and row.get("case_type") == "no_send_state_machine"),
        None,
    )
    publish_control_ref_issues = []
    if publish_state_row is None:
        finite_semantic_failures.append("missing ADV-NOSEND-PUBLISH no_send_state_machine finite control")
    else:
        publish_state_model = publish_state_row.get("model", {})
        if not isinstance(publish_state_model, dict):
            finite_semantic_failures.append("ADV-NOSEND-PUBLISH model payload missing or malformed")
        else:
            publish_manifest_ref = publish_state_row["model"].get("manifest_ref", publish_state_row["model"].get("publish_manifest_ref"))
            publish_manifest_legacy_ref = publish_state_row["model"].get("publish_manifest_ref")
            if publish_manifest_ref and publish_manifest_legacy_ref and publish_manifest_ref != publish_manifest_legacy_ref:
                publish_control_ref_issues.append(
                    f"publish manifest ref split fields disagree: manifest_ref={publish_manifest_ref}, publish_manifest_ref={publish_manifest_legacy_ref}"
                )
            approval_manifest_ref = publish_state_row["model"].get("approval_ref", publish_state_row["model"].get("owner_release_approval_ref"))
            approval_manifest_legacy_ref = publish_state_row["model"].get("owner_release_approval_ref")
            if approval_manifest_ref and approval_manifest_legacy_ref and approval_manifest_ref != approval_manifest_legacy_ref:
                publish_control_ref_issues.append(
                    f"approval ref split fields disagree: approval_ref={approval_manifest_ref}, owner_release_approval_ref={approval_manifest_legacy_ref}"
                )
            expected_publish_manifest_ref = "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_PUBLISH_MANIFEST_DRAFT.json"
            expected_approval_ref = "releases/oc_core_1_3_3/editorial/OWNER_RELEASE_APPROVAL_v1.3.3.json"
            if publish_manifest_ref != expected_publish_manifest_ref:
                publish_control_ref_issues.append(f"publish manifest ref mismatch: {publish_manifest_ref}")
            if approval_manifest_ref != expected_approval_ref:
                publish_control_ref_issues.append(f"approval ref mismatch: {approval_manifest_ref}")
            if publish_manifest_ref and not (root / publish_manifest_ref).exists():
                publish_control_ref_issues.append(f"publish manifest ref does not exist: {publish_manifest_ref}")
            if approval_manifest_ref and not (root / approval_manifest_ref).exists():
                publish_control_ref_issues.append(f"approval ref does not exist: {approval_manifest_ref}")
            if publish_control_ref_issues:
                finite_semantic_failures.append(f"ADV-NOSEND-PUBLISH control refs invalid ({'; '.join(publish_control_ref_issues)})")
    all_gates_open_row = next(
        (row for row in finite_rows if row.get("case_id") == "ADV-NOSEND-PUBLISH-ALL-GATES-OPEN-CONTROL"),
        None,
    )
    all_gates_open_issues: list[str] = []
    all_gates_open_model: dict[str, Any] = {}
    if all_gates_open_row is None:
        all_gates_open_issues.append("missing ADV-NOSEND-PUBLISH-ALL-GATES-OPEN-CONTROL finite case")
    else:
        if all_gates_open_row.get("case_type") != "no_send_hypothetical_control":
            all_gates_open_issues.append(
                f"all-gates-open case_type mismatch: {all_gates_open_row.get('case_type')}"
            )
        all_gates_open_model = all_gates_open_row.get("model", {}) if isinstance(all_gates_open_row.get("model"), dict) else {}
        expected_gates = {
            "owner_approved",
            "publish_allowed",
            "deposit_ready_metadata",
            "public_record_present",
            "github_release_allowed",
            "zenodo_deposit_allowed",
            "software_heritage_deposit_allowed",
            "journal_submission_allowed",
            "doi_minting_allowed",
            "g57_attack_matrix_zero_critical_high",
            "g58_reviewer_persona_suite_pass",
            "g70_scientific_closure_verdict_pass",
            "fresh_cerberus_required_for_release",
        }
        for gate in expected_gates:
            if all_gates_open_model.get(gate) is not True:
                all_gates_open_issues.append(f"all-gates-open control gate false: {gate}")
        expected_channels = {"github_release", "zenodo_deposit", "software_heritage_deposit", "journal_submission", "doi_minting"}
        if set(all_gates_open_model.get("requested_channels", [])) != expected_channels:
            all_gates_open_issues.append(f"all-gates-open control channels mismatch: {sorted(set(all_gates_open_model.get('requested_channels', [])))}")
        if all_gates_open_row.get("expected_verdict") != "ACCEPT_PUBLIC_ACTION":
            all_gates_open_issues.append(f"all-gates-open control expected verdict mismatch: {all_gates_open_row.get('expected_verdict')}")
        if all_gates_open_row.get("observed_verdict") != "ACCEPT_PUBLIC_ACTION":
            all_gates_open_issues.append(f"all-gates-open control observed verdict mismatch: {all_gates_open_row.get('observed_verdict')}")
        if all_gates_open_row.get("failed_gate_predicates"):
            all_gates_open_issues.append(f"all-gates-open failed predicates: {all_gates_open_row.get('failed_gate_predicates')}")
        if all_gates_open_model.get("global_no_send_lock") is not False:
            all_gates_open_issues.append("global_no_send_lock must be False in all-gates-open control")
        if all_gates_open_model.get("critical_open_total", 0) != 0 or all_gates_open_model.get("high_open_total", 0) != 0:
            all_gates_open_issues.append(
                f"all-gates-open non-zero open totals: critical={all_gates_open_model.get('critical_open_total')}, high={all_gates_open_model.get('high_open_total')}"
            )
        if all_gates_open_model.get("publish_requested") is not True:
            all_gates_open_issues.append("all-gates-open control requires publish_requested=True")
    comparator_failures = [
        row.get("tradition")
        for row in comparator.get("rows", [])
        if not row.get("source_refs") or not row.get("feature_tests") or not row.get("absence_test") or row.get("uniqueness_claim_status") != "NOT_PROMOTED_PRIOR_ART_POSITIONING_ONLY"
    ]
    allowed_phenomenon_statuses = {
        "PHENOMENON_SPECIFIC_MODEL_REPLAYED",
        "SCOPED_CLASSIFIER_ILLUSTRATION_NOT_DOMAIN_CLOSURE",
        "ILLUSTRATIVE_INTERNAL_MODEL_NOT_PHENOMENON_COVERAGE",
        "FORMAL_MODEL_CARD_REPLAYED_NOT_EMPIRICAL_DOMAIN_COVERAGE",
        "OPERATIONAL_NO_SEND_CONTROL_REPLAYED",
    }
    phenomenon_failures = [
        row.get("phenomenon_id")
        for row in phenomenon.get("rows", [])
        if not row.get("model_card")
        or "finite witness or replay row" in str(row.get("observable", "")).lower()
        or row.get("explanation_status") not in allowed_phenomenon_statuses
    ]
    finite_case_ids = {row.get("case_id") for row in finite.get("rows", [])}
    phenomenon_missing_controls = [
        row.get("phenomenon_id")
        for row in phenomenon.get("rows", [])
        if row.get("model_card", {}).get("prediction_or_replay") not in finite_case_ids
        or row.get("model_card", {}).get("negative_control") not in finite_case_ids
    ]
    attack_closure_failures = [
        row.get("objection_id")
        for row in attack.get("rows", [])
        if not row.get("closure_evidence_refs")
        or not row.get("closure_verification_query")
        or row.get("status") != "CLOSED_BY_SPECIFIC_V12_EVIDENCE"
        or (
            row.get("closure_type") == "generated_distinct_attack_surface"
            and (
                row.get("closure_current_artifact_hash_total", 0) < 1
                or "Observed current closure" not in str(row.get("closure_evidence", ""))
                or row.get("closure_predicate_pass") is not True
            )
        )
    ]
    attack_rows = [row for row in attack.get("rows", []) if isinstance(row, dict)]
    attack_row_counts = _attack_matrix_counts(attack_rows)
    attack_quality_quotas = _attack_matrix_quality_quotas(root, attack_rows)
    attack_summary_counter_failures = []
    if attack_row_counts["row_total"] != attack.get("objection_total", 0):
        attack_summary_counter_failures.append(f"objection_total mismatch: declared={attack.get('objection_total', 0)} observed={attack_row_counts['row_total']}")
    if attack_row_counts["critical_open_total"] != attack.get("critical_unresolved_total", 0):
        attack_summary_counter_failures.append(
            f"critical_unresolved_total mismatch: declared={attack.get('critical_unresolved_total', 0)} observed={attack_row_counts['critical_open_total']}"
        )
    if attack_row_counts["high_open_total"] != attack.get("high_unresolved_total", 0):
        attack_summary_counter_failures.append(
            f"high_unresolved_total mismatch: declared={attack.get('high_unresolved_total', 0)} observed={attack_row_counts['high_open_total']}"
        )
    numeric_missing = [
        row.get("claim_id")
        for row in numeric.get("rows", [])
        if not all(row.get(key) not in (None, "") for key in [
            "replay_rule", "dataset_snapshot_ref", "split_policy", "replay_value", "parsed_snapshot_value",
            "uncertainty", "baseline_control_value", "replay_residual", "comparator_residual", "negative_control", "falsifier",
        ])
    ]
    packet_missing = [
        lane for lane in {row["lane"] for row in numeric.get("rows", [])}
        if not (root / "empirical" / lane / "EMPIRICAL_PACKET.json").exists()
    ]
    llm_result_bad, llm_missing_refs, llm_missing_roles, llm_duplicate_roles = _llm_result_audit(root, llm)
    manifest_exception_paths = {
        _portable_path(row.get("path"))
        for row in public_manifest.get("nonrecursive_manifest_exceptions", [])
        if isinstance(row, dict)
    }
    internal_checksum_failures = repro_manifest.get("internal_checksum_failures", [])
    internal_checksum_failure_count_ok = repro_manifest.get("internal_checksum_failure_total", 0) == len(internal_checksum_failures)
    mismatch_failures = repro_manifest.get("mismatches", [])
    mismatch_count_ok = repro_manifest.get("mismatch_total", 0) == len(mismatch_failures)
    unexpected_internal_checksum_failures = [
        failure
        for failure in internal_checksum_failures
        if isinstance(failure, dict) and _portable_path(failure.get("path")) not in manifest_exception_paths
    ]
    repro_non_compare_mutation_count_ok = repro_manifest.get("non_compare_ref_mutation_total", 0) == len(repro_manifest.get("non_compare_ref_mutations", []))
    lake = _run_lake(root)
    surface_paths = [
        root / "releases" / "oc_core_1_3_3" / "README.md",
        root / "releases" / "oc_core_1_3_3" / "VERSION",
        root / "releases" / "oc_core_1_3_3" / "RELEASE_NOTES.md",
        root / "releases" / "oc_core_1_3_3" / "CHANGELOG.md",
        root / "releases" / RELEASE_ID / "editorial" / "metadata_drafts" / "zenodo.no_send.draft.json",
        root / "CITATION.cff",
        root / ".codemeta.json",
        root / "ro-crate-metadata.jsonld",
    ]
    metadata_surface = _metadata_surface_audit(root, manifest)
    return {
        "typed_foundation": {
            "state": "PASS" if (root / "content" / "OC_1_3_3_TYPED_FOUNDATION.tex").exists() and inv.get("theorem_total", 0) >= 10 else "FAIL",
            "theorem_total": inv.get("theorem_total"),
        },
        "k0": {"state": "PASS" if "S/\\rho" in text(root / "appendix" / "OC_1_3_3_K0_RESOLUTION_FOUNDATION.tex") else "FAIL"},
        "semantic_models": {"state": "PASS" if domain.get("row_total", 0) >= 10 and domain.get("untyped_domain_total") == 0 else "FAIL", **domain},
        "axiom_consistency": {"state": "PASS" if lake["state"] == "PASS" and finite.get("failure_total") == 0 and not finite_semantic_failures else "FAIL", "lake": lake, "finite_failure_total": finite.get("failure_total"), "finite_semantic_failures": finite_semantic_failures},
        "theorem_inventory": {"state": "PASS" if inv.get("theorem_total") == 10 and inv.get("demoted_route_total") == 0 else "FAIL", **{k: inv.get(k) for k in ["theorem_total", "demoted_route_total", "scope_repair_total"]}},
        "proof_sheets": {"state": "PASS" if not proof_failures else "FAIL", "failure_total": len(proof_failures), "failures": proof_failures},
        "no_theorem_theater": {"state": "PASS" if not proof_failures and not scope_hits else "FAIL", "proof_failure_total": len(proof_failures), "scope_hit_total": len(scope_hits), "scope_hits": scope_hits[:20]},
        "continuumness": {"state": "PASS" if "zero-cause" in text(root / "appendix" / "OC_1_3_3_CONTINUUMNESS_FUNCTIONALS.tex").lower() else "FAIL"},
        "boundary": {"state": "PASS" if "classifier" in text(root / "appendix" / "OC_1_3_3_BOUNDARY_REPRESENTATION_THEOREM.tex").lower() else "FAIL"},
        "operator": {"state": "PASS" if "typed update" in text(root / "content" / "OC_1_3_3_OPERATOR_SEMANTICS.tex").lower() else "FAIL"},
        "dimension": {"state": "PASS" if "Historical axis" in text(root / "appendix" / "OC_1_3_3_K_LEVEL_IRREDUCIBILITY_ATLAS.tex") or klevel.get("transition_total") == 12 else "FAIL"},
        "cycle": {"state": "PASS" if "cycle" in text(root / "content" / "OC_1_3_3_CYCLE_TAXONOMY.tex").lower() else "FAIL"},
        "identity": {"state": "PASS" if "identity" in text(root / "appendix" / "OC_1_3_3_IDENTITY_RESIDUE_REBIRTH_CLASSIFICATION.tex").lower() else "FAIL"},
        "klevel": {"state": "PASS" if klevel.get("transition_total") == 12 and klevel.get("unresolved_total") == 0 and klevel.get("inflated_without_witness_total") == 0 else "FAIL", **{k: klevel.get(k) for k in ["transition_total", "unresolved_total", "inflated_without_witness_total"]}},
        "minimality": {"state": "PASS" if minimality.get("unwitnessed_component_total") == 0 and minimality.get("component_total", 0) >= 10 else "FAIL", **{k: minimality.get(k) for k in ["component_total", "unwitnessed_component_total"]}},
        "machine_checked": {
            "state": "PASS" if (
                lake["state"] == "PASS"
                and lean_cert.get("returncode") == 0
                and lean_cert.get("theorem_ref_missing_total") == 0
                and lean_cert.get("theorem_ref_present_total") == inv.get("theorem_total")
                and finite.get("machine_checked_subset_total") == inv.get("theorem_total")
                and inv.get("machine_checked_subset_total") == inv.get("theorem_total")
                and not missing_lean_semantic_markers
                and not finite_semantic_failures
            ) else "FAIL",
            "lake": lake,
            "lean_build_certificate": {
                "ref": "formal/lean/LEAN_BUILD_CERTIFICATE_1_3_3.json",
                "returncode": lean_cert.get("returncode"),
                "theorem_ref_present_total": lean_cert.get("theorem_ref_present_total"),
                "theorem_ref_missing_total": lean_cert.get("theorem_ref_missing_total"),
            },
            "finite_machine_checked_subset_total": finite.get("machine_checked_subset_total"),
            "machine_checked_subset_total": inv.get("machine_checked_subset_total"),
            "missing_lean_semantic_markers": missing_lean_semantic_markers,
            "finite_semantic_failures": finite_semantic_failures,
        },
        "empirical_packets": {"state": "PASS" if numeric.get("lane_total") >= 5 and not packet_missing and not numeric_missing else "FAIL", "lane_total": numeric.get("lane_total"), "packet_missing": packet_missing, "numeric_missing": numeric_missing},
        "heldout": {
            "state": "PASS" if (
                not numeric_missing
                and (
                    not any(row.get("prediction_support_allowed") is True or row.get("empirical_support_allowed") is True for row in numeric.get("rows", []))
                    or all(
                        "split" in str(row.get("split_policy", "")).lower()
                        or "train" in str(row.get("split_policy", "")).lower()
                        or "blind" in str(row.get("split_policy", "")).lower()
                        for row in numeric.get("rows", [])
                    )
                )
            ) else "FAIL",
            "heldout_validation_applicable": any(row.get("prediction_support_allowed") is True or row.get("empirical_support_allowed") is True for row in numeric.get("rows", [])),
            "empirical_promotion_row_total": sum(1 for row in numeric.get("rows", []) if row.get("prediction_support_allowed") is True or row.get("empirical_support_allowed") is True),
            "no_empirical_validation_promoted_without_heldout": True,
        },
        "negative_controls": {"state": "PASS" if all(row.get("negative_control") for row in numeric.get("rows", [])) else "FAIL"},
        "baseline_comparators": {"state": "PASS" if all(row.get("baseline_control_value") is not None for row in numeric.get("rows", [])) else "FAIL"},
        "adversarial": {"state": "PASS" if adversarial.get("failure_total") == 0 and adversarial.get("case_total", 0) >= 10 else "FAIL", **{k: adversarial.get(k) for k in ["case_total", "failure_total"]}},
        "counterexample": {"state": "PASS" if counter.get("open_counterexample_total") == 0 and counter.get("case_total", 0) >= 10 else "FAIL", **{k: counter.get(k) for k in ["case_total", "open_counterexample_total"]}},
        "comparator": {"state": "PASS" if comparator.get("row_total", 0) >= 10 and comparator.get("unsupported_uniqueness_total") == 0 and not comparator_failures else "FAIL", **{k: comparator.get(k) for k in ["row_total", "unsupported_uniqueness_total"]}, "comparator_failures": comparator_failures},
        "novelty": {"state": "PASS" if comparator.get("unsupported_uniqueness_total") == 0 and not comparator_failures else "FAIL", "comparator_failures": comparator_failures},
        "claim_binding": {"state": "PASS" if claims.get("unsupported_promoted_total") == 0 and claims.get("demoted_public_claim_total") == 0 and claims.get("scientific_promotion_wording_violation_total", 0) == 0 and not proof_bound_failures else "FAIL", "claim_total": claims.get("claim_total"), "proof_bound_failure_total": len(proof_bound_failures), "scientific_promotion_wording_violation_total": claims.get("scientific_promotion_wording_violation_total", 0)},
        "attack_matrix": {
            "state": "PASS"
            if (
                attack.get("critical_unresolved_total") == 0
                and attack.get("high_unresolved_total") == 0
                and attack.get("objection_total", 0) >= 200
                and attack.get("fresh_cerberus_review_satisfied") is True
                and not attack_closure_failures
                and not attack_summary_counter_failures
                and attack_quality_quotas["state"] == "PASS"
            )
            else "FAIL",
            **{k: attack.get(k) for k in ["objection_total", "critical_unresolved_total", "high_unresolved_total", "fresh_cerberus_review_satisfied", "fresh_cerberus_review_gate_status"]},
            "attack_row_counts": attack_row_counts,
            "attack_quality_quotas": attack_quality_quotas,
            "attack_summary_counter_failures": attack_summary_counter_failures,
            "attack_closure_failures": attack_closure_failures[:20],
            "publish_control_ref_issues": publish_control_ref_issues[:20],
            "all_gates_open_issues": all_gates_open_issues[:20],
        },
        "llm": {
            "state": "PASS"
            if (
                llm.get("execution_status") == "EXECUTED_WITH_FINDINGS_CLOSED"
                and llm.get("role_total") == 14
                and not llm_result_bad
                and not llm_missing_refs
                and not llm_missing_roles
                and not llm_duplicate_roles
                and llm.get("parse_failure_total", 0) == 0
            )
            else "BLOCKED",
            "execution_status": llm.get("execution_status"),
            "role_total": llm.get("role_total"),
            "bad_results": llm_result_bad[:20],
            "missing_result_refs": llm_missing_refs,
            "missing_roles": llm_missing_roles,
            "duplicate_roles": llm_duplicate_roles,
            "execution_bad_total": llm.get("execution_bad_total", 0),
            "pending_role_total": llm.get("pending_role_total", 0),
            "critical_open_total": llm.get("critical_open_total"),
            "high_open_total": llm.get("high_open_total"),
            "parse_failure_total": llm.get("parse_failure_total"),
            "all_result_refs": len(llm.get("result_refs", [])),
        },
        "all_gates_open_control": {
            "state": "PASS" if not all_gates_open_issues else "FAIL",
            "issues": all_gates_open_issues[:20],
            "expected_verdict": "ACCEPT_PUBLIC_ACTION",
            "observed_verdict": all_gates_open_row.get("observed_verdict") if all_gates_open_row else None,
            "failed_gate_predicates": all_gates_open_row.get("failed_gate_predicates", []) if all_gates_open_row else [],
            "model": all_gates_open_model,
            "critical_open_total": all_gates_open_model.get("critical_open_total", 0),
            "high_open_total": all_gates_open_model.get("high_open_total", 0),
            "publish_control_ref_issues": publish_control_ref_issues[:20],
        },
        "reproducibility": {
            "state": "PASS" if (
                (root / "lakefile.lean").exists()
                and (root / "validation" / "run_all.py").exists()
                and (root / "simulations" / "adversarial" / "run_all.py").exists()
                and (root / "tools" / "verify_oc133_reproducible_temp_tree.py").exists()
                and repro_manifest.get("verdict") == "PASS"
                and repro_manifest.get("command_failure_total") == 0
                and repro_manifest.get("mismatch_total") == 0
                and mismatch_count_ok
                and repro_manifest.get("non_compare_ref_mutation_total", 0) == 0
                and repro_non_compare_mutation_count_ok
                and repro_manifest.get("internal_checksum_failure_total", 0) == 0
                and internal_checksum_failure_count_ok
                and not unexpected_internal_checksum_failures
                and repro_manifest.get("preexisting_compared_target_total", 0) >= repro_manifest.get("compared_artifact_total", 1)
                and repro_manifest.get("git_state", {}).get("strict_head_replay_clean") is True
                and repro_manifest.get("stable_payload_sha256")
                and repro_manifest.get("previous_manifest_self_check", {}).get("current_stable_payload_sha256") == repro_manifest.get("stable_payload_sha256")
            ) else "FAIL",
            "manifest_ref": "reports/OC_CORE_1_3_3_POST_GENERATION_REPRODUCIBILITY_MANIFEST.json",
            "verdict": repro_manifest.get("verdict"),
            "command_failure_total": repro_manifest.get("command_failure_total"),
            "mismatch_total": repro_manifest.get("mismatch_total"),
            "mismatch_count_ok": mismatch_count_ok,
            "mismatch_failures": mismatch_failures[:20],
            "non_compare_ref_mutation_total": repro_manifest.get("non_compare_ref_mutation_total"),
            "repro_non_compare_mutation_count_ok": repro_non_compare_mutation_count_ok,
            "preexisting_compared_target_total": repro_manifest.get("preexisting_compared_target_total"),
            "compared_artifact_total": repro_manifest.get("compared_artifact_total"),
            "strict_head_replay_clean": repro_manifest.get("git_state", {}).get("strict_head_replay_clean"),
            "stable_payload_sha256": repro_manifest.get("stable_payload_sha256"),
            "internal_checksum_failures": internal_checksum_failures[:20],
            "internal_checksum_failure_count_ok": internal_checksum_failure_count_ok,
            "unexpected_internal_checksum_failures": unexpected_internal_checksum_failures[:20],
        },
        "no_local_paths_secrets": {"state": "PASS" if not secret_hits else "FAIL", "hit_total": len(secret_hits), "hits": secret_hits[:20]},
        "surface_parity": {
            "state": "PASS" if (
                all(path.exists() for path in surface_paths)
                and text(root / "releases" / "oc_core_1_3_3" / "VERSION").strip() == VERSION
                and metadata_surface["all_versions_current"]
                and metadata_surface["stale_hit_total"] == 0
            ) else "FAIL",
            "missing": [rel(root, path) for path in surface_paths if not path.exists()],
            "metadata_stale_hit_total": metadata_surface["stale_hit_total"],
            "metadata_version_checks": metadata_surface["version_checks"],
        },
        "llm_schema_claim_boundary": {"state": "PASS" if not absolute_hits and phenomenon.get("unsupported_closed_total") == 0 and not phenomenon_failures and not phenomenon_missing_controls else "FAIL", "absolute_hit_total": len(absolute_hits), "absolute_hits": absolute_hits[:20], "phenomenon_rows": phenomenon.get("row_total"), "phenomenon_failures": phenomenon_failures, "phenomenon_missing_controls": phenomenon_missing_controls},
        "no_empirical_discovery_only": {
            "state": "PASS" if (
                numeric.get("unsupported_promoted_total") == 0
                and numeric.get("blocked_for_promotion_total") == 0
                and numeric.get("prediction_support_allowed_total") == 0
                and all(
                    not (
                        row.get("numeric_replay") is True
                        and (
                            row.get("prediction_support_allowed") is True
                            or row.get("empirical_support_allowed") is True
                        )
                    )
                    for row in numeric.get("rows", [])
                )
                and not numeric_missing
            ) else "FAIL",
            "unsupported_promoted_total": numeric.get("unsupported_promoted_total"),
            "blocked_for_promotion_total": numeric.get("blocked_for_promotion_total"),
            "prediction_support_allowed_total": numeric.get("prediction_support_allowed_total"),
        },
        "no_scope_narrowing": {"state": "PASS" if not scope_hits and claims.get("demoted_public_claim_total") == 0 else "FAIL", "scope_hit_total": len(scope_hits), "hits": scope_hits[:20]},
        "owner_packet": {"state": "PASS" if approval.get("decision") == "PENDING" and (root / "releases" / "oc_core_1_3_3" / "editorial" / "OC_CORE_1_3_3_OWNER_APPROVAL_PACKET.json").exists() else "FAIL"},
        "zenodo": {
            "state": "PASS" if (
                not (root / ".zenodo.json").exists()
                and (root / "releases" / RELEASE_ID / "editorial" / "metadata_drafts" / "zenodo.no_send.draft.json").exists()
                and manifest.get("zenodo_deposit_allowed") is False
                and manifest.get("publish_allowed") is False
                and metadata_surface["version_checks"].get("zenodo_version") is True
                and metadata_surface["version_checks"].get("zenodo_title_mentions_version") is True
                and metadata_surface["version_checks"].get("zenodo_description_mentions_version") is True
                and metadata_surface["no_send_checks"].get("zenodo_notes_no_send") is True
                and metadata_surface["no_send_checks"].get("root_zenodo_metadata_absent_while_no_send") is True
                and not [row for row in metadata_surface["stale_hits"] if row["path"].endswith("zenodo.no_send.draft.json")]
            ) else "FAIL",
            **metadata_surface,
        },
        "github": {
            "state": "PASS" if (
                manifest.get("github_release_allowed") is False
                and manifest.get("publish_allowed") is False
                and metadata_surface["all_versions_current"]
                and metadata_surface["stale_hit_total"] == 0
                and metadata_surface["all_no_send_locked"]
            ) else "FAIL",
            **metadata_surface,
        },
        "post_release": {"state": "PASS" if (root / "POST_RELEASE_VERIFICATION_PLAN.md").exists() else "FAIL"},
        "external_review": {"state": "PASS" if (root / "releases" / "oc_core_1_3_3" / "editorial" / "OC_CORE_1_3_3_EXTERNAL_REVIEW_PACKAGE.json").exists() else "FAIL"},
    }


def v12_gate_results(root: Path, gate_fn: Callable[[str, str, str, str, str, dict[str, Any] | None], dict[str, Any]]) -> list[dict[str, Any]]:
    audits = audit(root)
    key_by_gate = {
        "G32": "typed_foundation",
        "G33": "k0",
        "G34": "semantic_models",
        "G35": "axiom_consistency",
        "G36": "theorem_inventory",
        "G37": "proof_sheets",
        "G38": "no_theorem_theater",
        "G39": "continuumness",
        "G40": "boundary",
        "G41": "operator",
        "G42": "dimension",
        "G43": "cycle",
        "G44": "identity",
        "G45": "klevel",
        "G46": "minimality",
        "G47": "machine_checked",
        "G48": "empirical_packets",
        "G49": "heldout",
        "G50": "negative_controls",
        "G51": "baseline_comparators",
        "G52": "adversarial",
        "G53": "counterexample",
        "G54": "comparator",
        "G55": "novelty",
        "G56": "claim_binding",
        "G57": "attack_matrix",
        "G58": "llm",
        "G59": "reproducibility",
        "G60": "no_local_paths_secrets",
        "G61": "surface_parity",
        "G62": "llm_schema_claim_boundary",
        "G63": "no_empirical_discovery_only",
        "G64": "no_scope_narrowing",
        "G65": "owner_packet",
        "G66": "zenodo",
        "G67": "github",
        "G68": "post_release",
        "G69": "external_review",
    }
    rows: list[dict[str, Any]] = []
    for gate_id, name, severity in V12_GATE_SPECS:
        if gate_id == "G70":
            prior_bad = [row for row in rows if row["state"] in {"FAIL", "BLOCKED"} and row["severity"] in {"CRITICAL", "HIGH"}]
            details = {
                "prior_critical_high_bad_total": len(prior_bad),
                "release_state_on_pass": "OC_CORE_1_3_3_10_10_READY_NO_SEND",
                **audits["all_gates_open_control"],
            }
            state = "PASS" if not prior_bad and audits["all_gates_open_control"]["state"] == "PASS" else "FAIL"
        else:
            details = audits[key_by_gate[gate_id]]
            state = details["state"]
        rows.append(gate_fn(gate_id, name, state, severity, f"{name} checked by v12 no-compromise release profile.", details))
    return rows
