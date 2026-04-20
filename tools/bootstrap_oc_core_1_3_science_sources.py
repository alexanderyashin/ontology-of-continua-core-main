from __future__ import annotations

import argparse
from typing import Any

from oc_core_1_3_science_spot_lib import (
    CORE_DOMAIN_IDS,
    EDITORIAL_DIR,
    SCIENCE_SOURCE_CLOSURE_BUNDLE_DIR,
    SCIENCE_SOURCE_HOSTILE_REVIEW_DIR,
    SCIENCE_SOURCE_K_LEVEL_DIR,
    closure_bundle_source_file,
    dump_json,
    hostile_review_source_file,
    k_level_source_file,
    load_json,
    repo_rel,
    unique_strings,
)


DOMAIN_CLAIM_IDS = CORE_DOMAIN_IDS + ["METAONTOLOGY"]
GLOBAL_CLAIM_IDS = ["LOAD_BEARING_SPINE", "K11_K12_IRREDUCIBILITY"]

DOMAIN_PARAMETER_SYMBOLS = {
    "MATHEMATICS": ["epsilon_star", "minimal_denominator", "strict_terminalized_total"],
    "PHYSICS": ["alpha_res", "lambda_Balmer", "tau_transport"],
    "CHEMISTRY": ["DeltaH_res", "nu_spec", "k_or_K_eq"],
    "BIOLOGY": ["A_expr", "pi_state", "t_onset"],
    "SYSTEMS_CIVILIZATIONAL_PROJECTION": ["R_pop", "E_tp", "S_regime"],
    "METAONTOLOGY": ["C_frame", "R_frame", "B_frame"],
}

DOMAIN_PARAMETER_UNITS = {
    "MATHEMATICS": {
        "epsilon_star": "dimensionless",
        "minimal_denominator": "integer",
        "strict_terminalized_total": "count",
    },
    "PHYSICS": {
        "alpha_res": "dimensionless residual",
        "lambda_Balmer": "nm",
        "tau_transport": "dimensionless sigma",
    },
    "CHEMISTRY": {
        "DeltaH_res": "kJ/mol residual",
        "nu_spec": "cm^-1 residual",
        "k_or_K_eq": "dimensionless residual",
    },
    "BIOLOGY": {
        "A_expr": "normalized expression amplitude",
        "pi_state": "ordering score",
        "t_onset": "hours residual",
    },
    "SYSTEMS_CIVILIZATIONAL_PROJECTION": {
        "R_pop": "trajectory residual",
        "E_tp": "turning-point error",
        "S_regime": "regime score",
    },
    "METAONTOLOGY": {
        "C_frame": "dimensionless",
        "R_frame": "dimensionless",
        "B_frame": "dimensionless",
    },
}

DOMAIN_COMPARATOR_FAMILIES = {
    "MATHEMATICS": ["exact enumerative baseline", "direct constructive proof baseline"],
    "PHYSICS": ["bounded residual fit without theorem trace", "family-wise least-squares baseline"],
    "CHEMISTRY": ["reference-table envelope baseline", "reaction-class residual fit baseline"],
    "BIOLOGY": ["dataset-family signature fit baseline", "state-transition score baseline"],
    "SYSTEMS_CIVILIZATIONAL_PROJECTION": ["macro-trend residual baseline", "turning-point heuristic baseline"],
    "METAONTOLOGY": ["frame-only descriptive baseline"],
}

HOSTILE_REVIEW_SOURCE_SECTIONS = {
    "HOSTILE::LAWFUL_COLLAPSE": {
        "exact_theorem_route_under_attack": ["Axiom 3.3", "Definition 12.6", "Source Corollary 3.2", "Lemma 3"],
        "premises": ["Axiom 3.3", "Definition 12.6", "OBLIGATION::SOURCE_COROLLARY_3_2", "OBLIGATION::LEMMA_3"],
        "forbidden_shortcuts": [
            "No metaphor may substitute for admissible-state loss.",
            "No residue label may be promoted into persistence without theorem support.",
        ],
        "formal_argument_body": [
            "Collapse is lawful only when admissible realization is lost under the Axiom 3.3 route, not when the text merely changes narrative tone.",
            "Source Corollary 3.2 and Lemma 3 jointly bind collapse to irreversible failure of the admissible realization and restrict post-collapse descriptions to residue or rebirth classifications.",
            "Any positive claim that preserves the same realized identity after lawful collapse reopens the core route and forces fail-closed rebuild.",
        ],
        "falsifier_conditions": [
            "Produce a surviving case where collapse is declared without admissible-state loss.",
            "Show that the same identity persists numerically after declared collapse without violating Axiom 3.3.",
        ],
    },
    "HOSTILE::IRREVERSIBILITY": {
        "exact_theorem_route_under_attack": ["Axiom 3.3", "Definition 12.6", "Source Corollary 3.2"],
        "premises": ["Axiom 3.3", "Definition 12.6", "OBLIGATION::SOURCE_COROLLARY_3_2"],
        "forbidden_shortcuts": [
            "No residue-to-identity leap is allowed.",
            "No numerically identical restoration after lawful death is allowed without an explicit theorem.",
        ],
        "formal_argument_body": [
            "The irreversibility claim stands or falls on the corollary route from Axiom 3.3 rather than on rhetoric about finality.",
            "If lawful death has occurred, any later state that is merely structurally similar must be classified separately; it may not be counted as the same realized identity without contradicting the corollary.",
            "This dossier therefore treats numerical identity restoration as a falsifier rather than as an interpretive option.",
        ],
        "falsifier_conditions": [
            "Construct a lawful death event followed by numerically identical restoration of the same continuum.",
            "Show that the current corollary route requires hidden premises to exclude restoration.",
        ],
    },
    "HOSTILE::RESIDUE_REBIRTH_BOUNDARY": {
        "exact_theorem_route_under_attack": ["Source Corollary 3.2", "Lemma 3", "collapse/rebirth classification boundary"],
        "premises": ["Source Corollary 3.2", "OBLIGATION::LEMMA_3"],
        "forbidden_shortcuts": [
            "Residue may not be counted as persistence.",
            "Rebirth may not inherit identity unless a new theorem route exists.",
        ],
        "formal_argument_body": [
            "The residue/rebirth boundary is a classification theorem burden, not a narrative convenience.",
            "Lemma 3 already requires that residue be treated as structural aftermath only, while rebirth must be explicitly new and not silently identified with persistence.",
            "The science remains fail-closed until those boundary conditions are carried as formal dossier clauses with explicit falsifiers.",
        ],
        "falsifier_conditions": [
            "Show a residue case that preserves full live identity.",
            "Show a rebirth case that inherits identity without a new theorem route.",
        ],
    },
    "HOSTILE::EXCLUDED_LIFT_FIREWALL": {
        "exact_theorem_route_under_attack": ["Axiom 3.2 route to Source Theorem 3", "Lemma 1", "Lemma 2", "Theorem A"],
        "premises": ["OBLIGATION::SOURCE_THEOREM_3", "OBLIGATION::LEMMA_1", "OBLIGATION::LEMMA_2", "OBLIGATION::THEOREM_A"],
        "forbidden_shortcuts": [
            "No excluded lift-heavy family may enter the positive bounded argument.",
            "No extension branch or bridge-only packet may masquerade as theorem support.",
        ],
        "formal_argument_body": [
            "The firewall exists to keep the closed core route from silently importing excluded theorem families, extension branches, or bridge-only evidence as proof support.",
            "The obligation chain from Source Theorem 3 through Theorem A explicitly names excluded dependencies; the firewall dossier must therefore be an auditable exclusion ledger rather than a prose assurance.",
            "Any leak from excluded lift-heavy material back into the core route invalidates the current promotion surface immediately.",
        ],
        "falsifier_conditions": [
            "Identify an excluded branch identifier inside any core proof path.",
            "Show that Lemma 2 or Theorem A requires extension or bridge-only support.",
        ],
    },
    "HOSTILE::JOURNAL_CORE_ASYMMETRY": {
        "exact_theorem_route_under_attack": ["Lemma 2", "Theorem A", "journal-core extraction"],
        "premises": ["OBLIGATION::LEMMA_2", "OBLIGATION::THEOREM_A"],
        "forbidden_shortcuts": [
            "No journal-core claim may outrun the master monograph.",
            "No compression-only statement may reintroduce excluded theorem material.",
        ],
        "formal_argument_body": [
            "The journal core is lawful only as an extraction from the master route; it is not an independent theorem authority.",
            "Theorem A and its supporting obligations already constrain the extraction to the master scope. The dossier must therefore prove traceability from every public journal-core claim back to the closed master route.",
            "If a compressed public surface says more than the master has proved, the closure machine must demote the public surface rather than stretch the master by implication.",
        ],
        "falsifier_conditions": [
            "Find a journal-core theorem claim that lacks a master-route support chain.",
            "Show a compressed claim stronger than Theorem A or its lawful support.",
        ],
    },
    "HOSTILE::K11_K12_IRREDUCIBILITY": {
        "exact_theorem_route_under_attack": ["K10", "K11", "K12", "upper-level irreducibility fork"],
        "premises": ["K10 closed formal-system lane", "K11 theorem target", "K12 semantic-coherence target"],
        "forbidden_shortcuts": [
            "No decorative level inflation is allowed.",
            "No appeal to narrative scope may replace an irreducibility proof.",
        ],
        "formal_argument_body": [
            "K11 and K12 survive only if they do irreducible scientific work beyond K10 and survive direct reduction attempts.",
            "The closure machine treats this as a fork with only two lawful exits: prove necessity beyond K10 or demote the levels and rebuild dependent routes.",
            "This dossier therefore keeps the upper levels explicitly provisional rather than silently canonical.",
        ],
        "falsifier_conditions": [
            "Exhibit a lossless reduction of K11 to K10.",
            "Exhibit a lossless reduction of K12 to K10 or K11 without weakening the current theorem stack.",
        ],
    },
}


def ensure_dir(path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def science_source_ref(path) -> str:
    return repo_rel(path)


def read_surfaces() -> dict[str, Any]:
    root = EDITORIAL_DIR
    return {
        "spot": load_json(root / "OC_CORE_1_3_SCIENCE_SPOT_latest.json"),
        "closure_bundles": load_json(root / "OC_CORE_1_3_DOMAIN_CLOSURE_BUNDLE_REGISTRY_latest.json"),
        "hostile_review": load_json(root / "OC_CORE_1_3_HOSTILE_REVIEW_BACKLOG_latest.json"),
        "toe": load_json(root / "OC_CORE_1_3_TOE_SYNTHESIS_latest.json"),
        "proofs": load_json(root / "OC_CORE_1_3_PROOF_OBLIGATION_REGISTRY_latest.json"),
    }


def units_by_observable(domain_id: str, observable_ids: list[str]) -> dict[str, str]:
    default_unit = {
        "MATHEMATICS": "exact quantity",
        "PHYSICS": "bounded residual or SI family unit",
        "CHEMISTRY": "bounded residual or chemistry family unit",
        "BIOLOGY": "normalized assay or timing unit",
        "SYSTEMS_CIVILIZATIONAL_PROJECTION": "trajectory or regime-score unit",
        "METAONTOLOGY": "frame-only unit",
    }.get(domain_id, "domain unit")
    return {observable_id: default_unit for observable_id in observable_ids}


def dataset_field_bindings(domain_row: dict[str, Any]) -> list[dict[str, Any]]:
    bindings = []
    for item in domain_row.get("benchmark_dataset_manifest", []):
        bindings.append(
            {
                "benchmark_id": item.get("benchmark_id", ""),
                "observable_name": item.get("observable_name", ""),
                "dataset_url": item.get("dataset_url", ""),
                "held_out_policy": item.get("held_out_policy", ""),
            }
        )
    return bindings


def falsifier_classes_for_domain(domain_id: str) -> list[str]:
    return {
        "MATHEMATICS": ["replay_divergence", "surviving_counterexample"],
        "PHYSICS": ["held_out_residual_breach", "sign_or_order_break"],
        "CHEMISTRY": ["held_out_family_breach", "reaction_class_drift"],
        "BIOLOGY": ["held_out_signature_failure", "single_dataset_dependence"],
        "SYSTEMS_CIVILIZATIONAL_PROJECTION": ["turning_point_failure", "out_of_band_trajectory"],
        "METAONTOLOGY": ["frame_leakage", "standalone_empirical_overclaim"],
    }.get(domain_id, ["domain_specific_falsifier"])


def artifact_payloads_for_domain(domain_row: dict[str, Any], bundle_row: dict[str, Any]) -> dict[str, Any]:
    domain_id = domain_row["domain_id"]
    observable_ids = domain_row.get("observable_ids", [])
    dataset_ids = domain_row.get("dataset_ids", [])
    official_routes = domain_row.get("official_route_refs", [])
    bundle_refs = unique_strings([*bundle_row.get("refs", []), *domain_row.get("source_refs", [])])
    held_out_case_ids = domain_row.get("held_out_case_ids", [])
    calibration_case_ids = [case_id for case_id in domain_row.get("declared_case_ids", []) if case_id not in held_out_case_ids]
    return {
        "theorem_packet": {
            "status": bundle_row["artifact_statuses"]["theorem_packet"],
            "exact_formal_statement": bundle_row["minimum_theorem_native_claim"],
            "premises": unique_strings([*domain_row.get("primary_k_levels", []), *domain_row.get("root_operator_refs", [])]),
            "derivation_steps": unique_strings(
                [
                    "Fix the bounded theorem-native claim without widening domain scope.",
                    *domain_row.get("theorem_to_observable_map", []),
                    "Demonstrate that every promoted theorem step traces back to the declared root operators and K-level route.",
                ]
            ),
            "excluded_dependencies": domain_row.get("core_proof_path_branch_ids", []) or ["EXTENSION branches", "REFUTED branches"],
            "scope_boundary": domain_row.get("nonclaim_boundary") or domain_row.get("classification_rationale", ""),
            "refs": unique_strings([*domain_row.get("theorem_refs", []), *bundle_refs]),
        },
        "parameter_law_packet": {
            "status": bundle_row["artifact_statuses"]["parameter_law_packet"],
            "symbols": DOMAIN_PARAMETER_SYMBOLS.get(domain_id, []),
            "units": DOMAIN_PARAMETER_UNITS.get(domain_id, {}),
            "regime": domain_row.get("measurement_schema", ""),
            "asymptotics": bundle_row["parameter_law_target"],
            "sign_order_constraints": [domain_row.get("acceptance_criterion", ""), domain_row.get("falsifier_specification", "")],
            "collapse_boundary": domain_row.get("falsifier_specification", ""),
            "forbidden_rubberization": [
                "No hidden fit parameter may be introduced after the theorem target locks.",
                "No post-hoc scope widening is allowed.",
            ],
            "refs": unique_strings([*domain_row.get("theorem_refs", []), *bundle_refs]),
        },
        "observable_binding_spec": {
            "status": bundle_row["artifact_statuses"]["observable_binding_spec"],
            "theorem_to_observable_map": domain_row.get("theorem_to_observable_map", []),
            "observable_ids": observable_ids,
            "units_by_observable": units_by_observable(domain_id, observable_ids),
            "dataset_field_bindings": dataset_field_bindings(domain_row),
            "refs": unique_strings([*domain_row.get("theorem_refs", []), *bundle_refs]),
        },
        "dataset_data_route_manifest": {
            "status": bundle_row["artifact_statuses"]["dataset_data_route_manifest"],
            "official_route_ids": [route.get("route_id", "") for route in official_routes],
            "pinned_dataset_ids": dataset_ids,
            "pinned_dataset_versions": ["PINNED_RELEASE_SNAPSHOT" for _ in dataset_ids],
            "split_lock": domain_row.get("benchmark_design", {}).get("held_out_policy", "NOT_DECLARED"),
            "refs": unique_strings([*(route.get("official_url", "") for route in official_routes), *bundle_refs]),
        },
        "held_out_replay_spec": {
            "status": bundle_row["artifact_statuses"]["held_out_replay_spec"],
            "calibration_case_ids": calibration_case_ids,
            "held_out_case_ids": held_out_case_ids,
            "acceptance_metrics": domain_row.get("quantitative_acceptance_thresholds", {}),
            "no_post_hoc_split_rule": "HELD_OUT_SPLIT_IS_LOCKED_EX_ANTE_AND_MAY_NOT_BE_CHANGED_AFTER_REPLAY",
            "acceptance_criterion": domain_row.get("acceptance_criterion", ""),
            "refs": unique_strings([domain_row.get("replay_harness", {}).get("command_ref", ""), *bundle_refs]),
        },
        "falsifier_ledger": {
            "status": bundle_row["artifact_statuses"]["falsifier_ledger"],
            "falsifier_classes": falsifier_classes_for_domain(domain_id),
            "kill_conditions": [domain_row.get("falsifier_specification", "")],
            "boundary_statement": domain_row.get("nonclaim_boundary", "") or domain_row.get("classification_rationale", ""),
            "refs": unique_strings([*domain_row.get("falsifier_refs", []), *bundle_refs]),
        },
        "counterexample_ledger": {
            "status": bundle_row["artifact_statuses"]["counterexample_ledger"],
            "attempted_counterexamples": [],
            "current_survivors": domain_row.get("gap_types", []),
            "resolution_state": "OPEN" if domain_row.get("closure_verdict") != "PASS" else "NO_SURVIVOR",
            "refs": bundle_refs,
        },
        "same_claim_class_comparator_ledger": {
            "status": bundle_row["artifact_statuses"]["same_claim_class_comparator_ledger"],
            "comparator_families": DOMAIN_COMPARATOR_FAMILIES.get(domain_id, []),
            "complexity_budget": "NO_COMPARATOR_MAY_WIN_ON_SAME_CLAIM_CLASS_AFTER_COST_NORMALIZATION",
            "verdict": bundle_row["artifact_statuses"]["same_claim_class_comparator_ledger"],
            "refs": bundle_refs,
        },
    }


def artifact_payloads_for_global_claim(claim_id: str, bundle_row: dict[str, Any], proofs: dict[str, Any]) -> dict[str, Any]:
    proof_rows = proofs["proof_obligation_sheets"]
    theorem_steps = [row["statement"] for row in proof_rows]
    theorem_premises = unique_strings([premise for row in proof_rows for premise in row["premises"]])
    excluded = unique_strings([item for row in proof_rows for item in row["excluded_dependencies"]])
    falsifier_rows = [row["falsifier_condition"] for row in proof_rows]
    if claim_id == "LOAD_BEARING_SPINE":
        falsifier_classes = ["hidden_dependency", "broken_implication", "journal_core_overreach"]
        counterexample_survivors = []
        theorem_statement = bundle_row["minimum_theorem_native_claim"]
        scope_boundary = "Load-bearing core only; no empirical bridge may substitute for theorem support."
        comparator_families = ["journal_core_only_compression", "excluded_lift_heavy_variant"]
        complexity_budget = "Comparator may not outrun the master theorem route."
    else:
        falsifier_classes = ["lossless_reduction_to_K10"]
        counterexample_survivors = ["K11_reduction_open", "K12_reduction_open"]
        theorem_statement = bundle_row["minimum_theorem_native_claim"]
        scope_boundary = "Upper-level irreducibility only."
        comparator_families = ["K10_only_reduction"]
        complexity_budget = "An upper level survives only if reduction loses declared scientific work."
    return {
        "theorem_packet": {
            "status": bundle_row["artifact_statuses"]["theorem_packet"],
            "exact_formal_statement": theorem_statement,
            "premises": theorem_premises if claim_id == "LOAD_BEARING_SPINE" else ["K10 closed formal-system lane", "K11 theorem target", "K12 theorem target"],
            "derivation_steps": theorem_steps if claim_id == "LOAD_BEARING_SPINE" else [
                "Attempt a lawful reduction of K11 to K10.",
                "Attempt a lawful reduction of K12 to K10 or K11.",
                "If reduction succeeds without loss, demote the upper level and rebuild dependencies.",
            ],
            "excluded_dependencies": excluded if claim_id == "LOAD_BEARING_SPINE" else ["decorative level inflation", "narrative-only semantic escalation"],
            "scope_boundary": scope_boundary,
            "refs": bundle_row["refs"],
        },
        "parameter_law_packet": {
            "status": bundle_row["artifact_statuses"]["parameter_law_packet"],
            "symbols": ["not_required_nonempirical"],
            "units": {"not_required_nonempirical": "none"},
            "regime": "nonempirical closed-core route" if claim_id == "LOAD_BEARING_SPINE" else "upper-level irreducibility audit",
            "asymptotics": "not required",
            "sign_order_constraints": [],
            "collapse_boundary": bundle_row["falsifier_specification"],
            "forbidden_rubberization": ["No narrative compression or rhetorical necessity claim may widen the route."],
            "refs": bundle_row["refs"],
        },
        "observable_binding_spec": {
            "status": bundle_row["artifact_statuses"]["observable_binding_spec"],
            "theorem_to_observable_map": [],
            "observable_ids": [],
            "units_by_observable": {},
            "dataset_field_bindings": [],
            "refs": bundle_row["refs"],
        },
        "dataset_data_route_manifest": {
            "status": bundle_row["artifact_statuses"]["dataset_data_route_manifest"],
            "official_route_ids": [],
            "pinned_dataset_ids": [],
            "pinned_dataset_versions": [],
            "split_lock": "NOT_REQUIRED_NONEMPIRICAL",
            "refs": bundle_row["refs"],
        },
        "held_out_replay_spec": {
            "status": bundle_row["artifact_statuses"]["held_out_replay_spec"],
            "calibration_case_ids": [],
            "held_out_case_ids": [],
            "acceptance_metrics": {},
            "no_post_hoc_split_rule": "NOT_REQUIRED_NONEMPIRICAL",
            "acceptance_criterion": "Core proof route remains exact and self-contained." if claim_id == "LOAD_BEARING_SPINE" else "Promotion requires proof of irreducible scientific work beyond K10.",
            "refs": bundle_row["refs"],
        },
        "falsifier_ledger": {
            "status": bundle_row["artifact_statuses"]["falsifier_ledger"],
            "falsifier_classes": falsifier_classes,
            "kill_conditions": falsifier_rows if claim_id == "LOAD_BEARING_SPINE" else [bundle_row["falsifier_specification"]],
            "boundary_statement": "Any broken implication or excluded dependency voids the route." if claim_id == "LOAD_BEARING_SPINE" else "A successful reduction forces demotion and graph rebuild.",
            "refs": bundle_row["refs"],
        },
        "counterexample_ledger": {
            "status": bundle_row["artifact_statuses"]["counterexample_ledger"],
            "attempted_counterexamples": [],
            "current_survivors": counterexample_survivors,
            "resolution_state": "CONTINUOUS_SEARCH" if claim_id == "LOAD_BEARING_SPINE" else "OPEN",
            "refs": bundle_row["refs"],
        },
        "same_claim_class_comparator_ledger": {
            "status": bundle_row["artifact_statuses"]["same_claim_class_comparator_ledger"],
            "comparator_families": comparator_families,
            "complexity_budget": complexity_budget,
            "verdict": bundle_row["artifact_statuses"]["same_claim_class_comparator_ledger"],
            "refs": bundle_row["refs"],
        },
    }


def build_closure_bundle_source(bundle_row: dict[str, Any], domain_row: dict[str, Any] | None, proofs: dict[str, Any]) -> dict[str, Any]:
    claim_id = bundle_row["claim_id"]
    payload = {
        "claim_id": claim_id,
        "domain_id": bundle_row["domain_id"],
        "domain_title": domain_row.get("domain_title", claim_id) if domain_row else claim_id,
        "scope_role": domain_row.get("scope_role", "global_bundle") if domain_row else "global_bundle",
        "scientific_class": bundle_row["scientific_class"],
        "trace_status": bundle_row["trace_status"],
        "evidence_status": bundle_row["evidence_status"],
        "closure_verdict": bundle_row["closure_verdict"],
        "gap_types": domain_row.get("gap_types", []) if domain_row else [],
        "claim_level": domain_row.get("claim_level", "PHASE1_GLOBAL_CLAIM") if domain_row else "PHASE1_GLOBAL_CLAIM",
        "scientific_state": domain_row.get("scientific_state", bundle_row["closure_verdict"]) if domain_row else bundle_row["closure_verdict"],
        "next_required_action": domain_row.get("next_required_action", bundle_row["current_transition_gate"]) if domain_row else bundle_row["current_transition_gate"],
        "inclusion_verdict": domain_row.get("inclusion_verdict", "PHASE1_GLOBAL_BUNDLE") if domain_row else "PHASE1_GLOBAL_BUNDLE",
        "promotion_scope_status": domain_row.get("promotion_scope_status", bundle_row["current_transition_gate"]) if domain_row else bundle_row["current_transition_gate"],
        "non_inclusion_reason": domain_row.get("non_inclusion_reason", "") if domain_row else "",
        "primary_k_levels": domain_row.get("primary_k_levels", []) if domain_row else [],
        "theorem_refs": domain_row.get("theorem_refs", []) if domain_row else [],
        "root_operator_refs": domain_row.get("root_operator_refs", []) if domain_row else [],
        "observable_ids": domain_row.get("observable_ids", []) if domain_row else [],
        "dataset_ids": domain_row.get("dataset_ids", []) if domain_row else [],
        "held_out_case_ids": domain_row.get("held_out_case_ids", []) if domain_row else [],
        "declared_case_ids": domain_row.get("declared_case_ids", []) if domain_row else [],
        "falsifier_refs": domain_row.get("falsifier_refs", []) if domain_row else [],
        "benchmark": domain_row.get("benchmark", "") if domain_row else "",
        "benchmark_families": domain_row.get("benchmark_families", []) if domain_row else [],
        "benchmark_dataset_manifest": domain_row.get("benchmark_dataset_manifest", []) if domain_row else [],
        "measurable_outputs": domain_row.get("measurable_outputs", []) if domain_row else [],
        "measurement_schema": domain_row.get("measurement_schema", "") if domain_row else "",
        "acceptance_criterion": domain_row.get("acceptance_criterion", "") if domain_row else "",
        "falsifier_specification": domain_row.get("falsifier_specification", bundle_row.get("falsifier_specification", "")) if domain_row else bundle_row.get("falsifier_specification", ""),
        "measurement_escalation_rule": domain_row.get("measurement_escalation_rule", "") if domain_row else "",
        "theorem_to_observable_map": domain_row.get("theorem_to_observable_map", bundle_row.get("theorem_to_observable_map", [])) if domain_row else bundle_row.get("theorem_to_observable_map", []),
        "official_route_refs": domain_row.get("official_route_refs", []) if domain_row else [],
        "selected_route_institutions": bundle_row.get("selected_route_institutions", []),
        "official_source_status": domain_row.get("official_source_status", "") if domain_row else "",
        "numerical_packet_status": domain_row.get("numerical_packet_status", "") if domain_row else "",
        "quantitative_packet_status": domain_row.get("quantitative_packet_status", "") if domain_row else "",
        "prediction_contract_status": domain_row.get("prediction_contract_status", "") if domain_row else "",
        "validation_evidence": domain_row.get("validation_evidence", {}) if domain_row else {},
        "quantitative_acceptance_result": domain_row.get("quantitative_acceptance_result", "") if domain_row else "",
        "benchmark_wave_id": domain_row.get("benchmark_wave_id", "") if domain_row else "",
        "benchmark_design": domain_row.get("benchmark_design", {}) if domain_row else {},
        "evidence_bar": domain_row.get("evidence_bar", "") if domain_row else "",
        "protocol_id": domain_row.get("protocol_id", "") if domain_row else "",
        "execution_basis_class": domain_row.get("execution_basis_class", "") if domain_row else "",
        "execution_scope": domain_row.get("execution_scope", "") if domain_row else "",
        "replay_harness": domain_row.get("replay_harness", {}) if domain_row else {},
        "replay_status": domain_row.get("replay_status", "") if domain_row else "",
        "quantitative_acceptance_thresholds": domain_row.get("quantitative_acceptance_thresholds", {}) if domain_row else {},
        "official_coverage_summary": domain_row.get("official_coverage_summary", {}) if domain_row else {},
        "official_metrics_summary": domain_row.get("official_metrics_summary", {}) if domain_row else {},
        "institute_run_escalation": domain_row.get("institute_run_escalation", {}) if domain_row else {},
        "matrix_snapshot": domain_row.get("matrix_snapshot", {}) if domain_row else {},
        "nonclaim_refs": domain_row.get("nonclaim_refs", []) if domain_row else [],
        "core_proof_path_branch_ids": domain_row.get("core_proof_path_branch_ids", []) if domain_row else [],
        "phase_id": bundle_row["phase_id"],
        "launch_rule": bundle_row["launch_rule"],
        "formal_derivation_order": bundle_row["formal_derivation_order"],
        "empirical_cost_order": bundle_row["empirical_cost_order"],
        "execution_order_authority": bundle_row["execution_order_authority"],
        "current_transition_gate": bundle_row["current_transition_gate"],
        "pass_transition": bundle_row["pass_transition"],
        "fail_transition": bundle_row["fail_transition"],
        "blocking_ids": bundle_row["blocking_ids"],
        "minimum_theorem_native_claim": bundle_row["minimum_theorem_native_claim"],
        "parameter_law_target": bundle_row["parameter_law_target"],
        "metric_summary": bundle_row["metric_summary"],
        "artifact_statuses": bundle_row["artifact_statuses"],
        "refs": unique_strings([*bundle_row.get("refs", []), *(domain_row.get("source_refs", []) if domain_row else [])]),
    }
    payload["artifacts"] = (
        artifact_payloads_for_domain(domain_row, bundle_row)
        if domain_row is not None
        else artifact_payloads_for_global_claim(claim_id, bundle_row, proofs)
    )
    return payload


def build_hostile_review_source(row: dict[str, Any]) -> dict[str, Any]:
    extra = HOSTILE_REVIEW_SOURCE_SECTIONS[row["review_id"]]
    return {
        "review_id": row["review_id"],
        "scientific_class": row.get("scientific_class", "THEOREM_NATIVE"),
        "trace_status": row.get("trace_status", "TRACE_COMPLETE_REQUIRES_DOSSIER_LOCK"),
        "evidence_status": row.get("evidence_status", "EVIDENCE_PENDING_HOSTILE_REVIEW_DOSSIER"),
        "current_status": row["current_status"],
        "current_resolution_state": row["current_resolution_state"],
        "blocks_global_pass": row["blocks_global_pass"],
        "challenge_statement": row["challenge"],
        "exact_theorem_route_under_attack": extra["exact_theorem_route_under_attack"],
        "premises": extra["premises"],
        "forbidden_shortcuts": extra["forbidden_shortcuts"],
        "formal_argument_body": extra["formal_argument_body"],
        "falsifier_conditions": extra["falsifier_conditions"],
        "exit_criterion": row["exit_criterion"],
        "resolution_outcome": "PASS" if row["current_status"] == "PASS" else "FAIL_CLOSED_REBUILD_REQUIRED",
        "refs": row["refs"],
    }


def build_k_level_source(level_row: dict[str, Any], toe_row: dict[str, Any]) -> dict[str, Any]:
    return {
        "level_id": level_row["level_id"],
        "scientific_class": level_row["scientific_class"],
        "trace_status": level_row["trace_status"],
        "evidence_status": level_row["evidence_status"],
        "closure_verdict": level_row["closure_verdict"],
        "theorem_schema": level_row["theorem_schema"],
        "benchmark": level_row["benchmark"],
        "prediction_interface_status": level_row["prediction_interface_status"],
        "projected_domain_ids": level_row["projected_domain_ids"],
        "falsifier": level_row["falsifier"],
        "title": toe_row["level_title"],
        "toe_file_ref": next(ref for ref in toe_row["manuscript_anchor_refs"] if ref.startswith("content/toe/")),
        "appendix_table_label": toe_row["appendix_table_label"],
        "theorem_native_claim": toe_row["theorem_native_claim"],
        "operator_binding_summary": toe_row["operator_binding_summary"],
        "parameter_law_display": toe_row["parameter_law_display"],
        "observable_map_summary": toe_row["observable_map_summary"],
        "synthetic_observable_ids": [observable_id for observable_id in toe_row["observable_ids"] if observable_id.startswith(f"{level_row['level_id']}::")],
        "numerical_rows": toe_row["numerical_rows"],
        "collapse_boundary": toe_row["collapse_boundary"],
        "refs": unique_strings([*level_row["refs"], *toe_row["theorem_refs"], *toe_row["falsifier_refs"]]),
    }


def bootstrap_science_sources(force: bool = False) -> None:
    surfaces = read_surfaces()
    spot = surfaces["spot"]
    bundle_rows = {row["claim_id"]: row for row in surfaces["closure_bundles"]["rows"]}
    domain_rows = {row["domain_id"]: row for row in spot["domain_registry"]}
    hostile_rows = surfaces["hostile_review"]["rows"]
    proof_rows = surfaces["proofs"]
    k_level_rows = {row["level_id"]: row for row in spot["k_levels"]}
    toe_rows = {row["level_id"]: row for row in surfaces["toe"]["k_level_rows"]}

    ensure_dir(SCIENCE_SOURCE_CLOSURE_BUNDLE_DIR)
    ensure_dir(SCIENCE_SOURCE_HOSTILE_REVIEW_DIR)
    ensure_dir(SCIENCE_SOURCE_K_LEVEL_DIR)

    for claim_id in DOMAIN_CLAIM_IDS:
        path = closure_bundle_source_file(claim_id)
        if path.exists() and not force:
            continue
        dump_json(path, build_closure_bundle_source(bundle_rows[claim_id], domain_rows[claim_id], proof_rows))

    for claim_id in GLOBAL_CLAIM_IDS:
        path = closure_bundle_source_file(claim_id)
        if path.exists() and not force:
            continue
        dump_json(path, build_closure_bundle_source(bundle_rows[claim_id], None, proof_rows))

    for row in hostile_rows:
        path = hostile_review_source_file(row["review_id"])
        if path.exists() and not force:
            continue
        dump_json(path, build_hostile_review_source(row))

    for level_id in sorted(k_level_rows.keys()):
        path = k_level_source_file(level_id)
        if path.exists() and not force:
            continue
        dump_json(path, build_k_level_source(k_level_rows[level_id], toe_rows[level_id]))


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap source-owned OC Core 1.3 science corpus files from current projected surfaces.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing science source files.")
    args = parser.parse_args()
    bootstrap_science_sources(force=args.force)
    print(f"Bootstrapped science sources under {science_source_ref(EDITORIAL_DIR / 'science_sources')}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
