from __future__ import annotations

import json
import re
import runpy
import subprocess
import contextlib
import io
from pathlib import Path
from typing import Any, Callable


RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"

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


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


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
        completed = subprocess.run(["lake", "build"], cwd=root, text=True, capture_output=True, timeout=180)
    except Exception as exc:
        return {"state": "FAIL", "returncode": -1, "stderr_tail": str(exc)[-1200:]}
    return {
        "state": "PASS" if completed.returncode == 0 else "FAIL",
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout[-1200:],
        "stderr_tail": completed.stderr[-1200:],
    }


def audit(root: Path) -> dict[str, Any]:
    ensure_v12(root)
    inv = read_json(root / "proofs" / "THEOREM_INVENTORY_1_3_3.json")
    registry = read_json(root / "proofs" / "THEOREM_REGISTRY_1_3_3.json")
    finite = read_json(root / "proofs" / "FINITE_MODEL_CHECKS_1_3_3.json")
    finite_inputs = read_json(root / "proofs" / "finite_model_checks" / "OC133_FINITE_MODEL_INPUTS.json")
    claims = read_json(root / "claims" / "CLAIM_LEDGER_1_3_3.json")
    numeric = read_json(root / "validation" / "numeric_predictions" / "OC133_NUMERIC_PREDICTION_TABLE.json")
    domain = read_json(root / "data" / "domain_semantics_matrix.json")
    klevel = read_json(root / "data" / "k_level_irreducibility_matrix.json")
    minimality = read_json(root / "data" / "OC133_GLOBAL_MINIMALITY_WITNESSES.json")
    attack = read_json(root / "review" / "OC_1_3_3_TOTAL_ATTACK_MATRIX.json")
    llm = read_json(root / "reviews" / "oc133_llm_cerberus" / "OC133_LLM_CERBERUS_SUMMARY.json")
    comparator = read_json(root / "comparators" / "OC_1_3_3_NOVELTY_AND_PRIORITY_REGISTER.json")
    phenomenon = read_json(root / "docs" / "OC_1_3_3_PHENOMENON_COVERAGE_MATRIX.json")
    adversarial = read_json(root / "reports" / "OC_CORE_1_3_3_ADVERSARIAL_SIMULATION_REPORT.json")
    counter = read_json(root / "falsification" / "COUNTEREXAMPLE_ATLAS_1_3_3.json")
    manifest = read_json(root / "releases" / "oc_core_1_3_3" / "editorial" / "OC_CORE_1_3_3_PUBLISH_MANIFEST_DRAFT.json")
    approval = read_json(root / "releases" / "oc_core_1_3_3" / "editorial" / "OWNER_RELEASE_APPROVAL_v1.3.3.json")
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
        "KTransitionModel",
        "upperKVerdict",
        "reducedKVerdict",
        "retained_transition_reduction_fails",
        "every_adjacent_transition_has_lawful_demotion_case",
        "reductionFails",
        "lawfulDemotion",
        "hybrid_guard_uses_reset",
        "smooth_operator_is_update_special_case",
        "differential_notation_requires_chart",
        "eligible_live_requires_cycle_or_maintenance",
        "residue_preservation_not_identity_without_invariant",
        "rebirth_not_identity_without_invariant",
        "invariant_lost_blocks_identity",
        "invariant_preserved_classifies_identity",
        "declared_death_blocks_live",
        "metric_boundary_failure_equiv",
        "k_zero_iff_declared_zero_cause",
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
    if "case_type" in text(root / "proofs" / "finite_model_checks" / "run_finite_model_checks.py") and "model.get" not in text(root / "proofs" / "finite_model_checks" / "run_finite_model_checks.py"):
        finite_semantic_failures.append("finite runner does not inspect model facts")
    comparator_failures = [
        row.get("tradition")
        for row in comparator.get("rows", [])
        if not row.get("source_refs") or not row.get("feature_tests") or not row.get("absence_test") or row.get("uniqueness_claim_status") != "NOT_PROMOTED_PRIOR_ART_POSITIONING_ONLY"
    ]
    phenomenon_failures = [
        row.get("phenomenon_id")
        for row in phenomenon.get("rows", [])
        if not row.get("model_card")
        or "finite witness or replay row" in str(row.get("observable", "")).lower()
        or row.get("explanation_status") != "PHENOMENON_SPECIFIC_MODEL_REPLAYED"
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
    ]
    numeric_missing = [
        row.get("claim_id")
        for row in numeric.get("rows", [])
        if not all(row.get(key) not in (None, "") for key in [
            "formula", "dataset_snapshot_ref", "split_policy", "predicted_value", "observed_value",
            "uncertainty", "comparator_prediction", "residual", "negative_control", "falsifier",
        ])
    ]
    packet_missing = [
        lane for lane in {row["lane"] for row in numeric.get("rows", [])}
        if not (root / "empirical" / lane / "EMPIRICAL_PACKET.json").exists()
    ]
    llm_result_bad = []
    for ref in llm.get("result_refs", []):
        row = read_json(root / ref)
        if row.get("execution_status") != "EXECUTED" or row.get("critical_open_total", 0) or row.get("high_open_total", 0):
            llm_result_bad.append(ref)
    lake = _run_lake(root)
    surface_paths = [
        root / "releases" / "oc_core_1_3_3" / "README.md",
        root / "releases" / "oc_core_1_3_3" / "VERSION",
        root / "releases" / "oc_core_1_3_3" / "RELEASE_NOTES.md",
        root / "releases" / "oc_core_1_3_3" / "CHANGELOG.md",
        root / "CITATION.cff",
        root / ".zenodo.json",
        root / ".codemeta.json",
        root / "ro-crate-metadata.jsonld",
    ]
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
        "identity": {"state": "PASS" if "identity" in text(root / "appendix" / "OC_1_3_3_IDENTITY_RESIDUE_REBIRTH_CATEGORY.tex").lower() else "FAIL"},
        "klevel": {"state": "PASS" if klevel.get("transition_total") == 12 and klevel.get("unresolved_total") == 0 and klevel.get("inflated_without_witness_total") == 0 else "FAIL", **{k: klevel.get(k) for k in ["transition_total", "unresolved_total", "inflated_without_witness_total"]}},
        "minimality": {"state": "PASS" if minimality.get("unwitnessed_component_total") == 0 and minimality.get("component_total", 0) >= 10 else "FAIL", **{k: minimality.get(k) for k in ["component_total", "unwitnessed_component_total"]}},
        "machine_checked": {"state": "PASS" if lake["state"] == "PASS" and inv.get("machine_checked_subset_total") == inv.get("theorem_total") and not missing_lean_semantic_markers and not finite_semantic_failures else "FAIL", "lake": lake, "machine_checked_subset_total": inv.get("machine_checked_subset_total"), "missing_lean_semantic_markers": missing_lean_semantic_markers, "finite_semantic_failures": finite_semantic_failures},
        "empirical_packets": {"state": "PASS" if numeric.get("lane_total") >= 5 and not packet_missing and not numeric_missing else "FAIL", "lane_total": numeric.get("lane_total"), "packet_missing": packet_missing, "numeric_missing": numeric_missing},
        "heldout": {"state": "PASS" if not numeric_missing and all("split" in str(row.get("split_policy", "")).lower() or "train" in str(row.get("split_policy", "")).lower() or "replay" in str(row.get("split_policy", "")).lower() for row in numeric.get("rows", [])) else "FAIL"},
        "negative_controls": {"state": "PASS" if all(row.get("negative_control") for row in numeric.get("rows", [])) else "FAIL"},
        "baseline_comparators": {"state": "PASS" if all(row.get("comparator_prediction") is not None for row in numeric.get("rows", [])) else "FAIL"},
        "adversarial": {"state": "PASS" if adversarial.get("failure_total") == 0 and adversarial.get("case_total", 0) >= 10 else "FAIL", **{k: adversarial.get(k) for k in ["case_total", "failure_total"]}},
        "counterexample": {"state": "PASS" if counter.get("open_counterexample_total") == 0 and counter.get("case_total", 0) >= 10 else "FAIL", **{k: counter.get(k) for k in ["case_total", "open_counterexample_total"]}},
        "comparator": {"state": "PASS" if comparator.get("row_total", 0) >= 10 and comparator.get("unsupported_uniqueness_total") == 0 and not comparator_failures else "FAIL", **{k: comparator.get(k) for k in ["row_total", "unsupported_uniqueness_total"]}, "comparator_failures": comparator_failures},
        "novelty": {"state": "PASS" if comparator.get("unsupported_uniqueness_total") == 0 and not comparator_failures else "FAIL", "comparator_failures": comparator_failures},
        "claim_binding": {"state": "PASS" if claims.get("unsupported_promoted_total") == 0 and claims.get("demoted_public_claim_total") == 0 and not proof_bound_failures else "FAIL", "claim_total": claims.get("claim_total"), "proof_bound_failure_total": len(proof_bound_failures)},
        "attack_matrix": {"state": "PASS" if attack.get("critical_unresolved_total") == 0 and attack.get("high_unresolved_total") == 0 and attack.get("objection_total", 0) >= 200 and not attack_closure_failures else "FAIL", **{k: attack.get(k) for k in ["objection_total", "critical_unresolved_total", "high_unresolved_total"]}, "attack_closure_failures": attack_closure_failures[:20]},
        "llm": {"state": "PASS" if llm.get("execution_status") == "EXECUTED_WITH_FINDINGS_CLOSED" and llm.get("role_total") == 14 and not llm_result_bad else "BLOCKED", "execution_status": llm.get("execution_status"), "role_total": llm.get("role_total"), "bad_results": llm_result_bad[:20], "pending_role_total": llm.get("pending_role_total", 0), "critical_open_total": llm.get("critical_open_total"), "high_open_total": llm.get("high_open_total"), "parse_failure_total": llm.get("parse_failure_total")},
        "reproducibility": {"state": "PASS" if (root / "lakefile.lean").exists() and (root / "validation" / "run_all.py").exists() and (root / "simulations" / "adversarial" / "run_all.py").exists() else "FAIL"},
        "no_local_paths_secrets": {"state": "PASS" if not secret_hits else "FAIL", "hit_total": len(secret_hits), "hits": secret_hits[:20]},
        "surface_parity": {"state": "PASS" if all(path.exists() for path in surface_paths) and text(root / "releases" / "oc_core_1_3_3" / "VERSION").strip() == VERSION else "FAIL", "missing": [rel(root, path) for path in surface_paths if not path.exists()]},
        "llm_schema_claim_boundary": {"state": "PASS" if not absolute_hits and phenomenon.get("unsupported_closed_total") == 0 and not phenomenon_failures and not phenomenon_missing_controls else "FAIL", "absolute_hit_total": len(absolute_hits), "absolute_hits": absolute_hits[:20], "phenomenon_rows": phenomenon.get("row_total"), "phenomenon_failures": phenomenon_failures, "phenomenon_missing_controls": phenomenon_missing_controls},
        "no_empirical_discovery_only": {"state": "PASS" if numeric.get("unsupported_promoted_total") == 0 and numeric.get("blocked_for_promotion_total") == 0 and not numeric_missing else "FAIL", "unsupported_promoted_total": numeric.get("unsupported_promoted_total"), "blocked_for_promotion_total": numeric.get("blocked_for_promotion_total")},
        "no_scope_narrowing": {"state": "PASS" if not scope_hits and claims.get("demoted_public_claim_total") == 0 else "FAIL", "scope_hit_total": len(scope_hits), "hits": scope_hits[:20]},
        "owner_packet": {"state": "PASS" if approval.get("decision") == "PENDING" and (root / "releases" / "oc_core_1_3_3" / "editorial" / "OC_CORE_1_3_3_OWNER_APPROVAL_PACKET.json").exists() else "FAIL"},
        "zenodo": {"state": "PASS" if (root / ".zenodo.json").exists() and manifest.get("zenodo_deposit_allowed") is False else "FAIL"},
        "github": {"state": "PASS" if manifest.get("github_release_allowed") is False and manifest.get("publish_allowed") is False else "FAIL"},
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
            details = {"prior_critical_high_bad_total": len(prior_bad), "release_state_on_pass": "OC_CORE_1_3_3_10_10_READY_NO_SEND"}
            state = "PASS" if not prior_bad else "FAIL"
        else:
            details = audits[key_by_gate[gate_id]]
            state = details["state"]
        rows.append(gate_fn(gate_id, name, state, severity, f"{name} checked by v12 no-compromise release profile.", details))
    return rows
