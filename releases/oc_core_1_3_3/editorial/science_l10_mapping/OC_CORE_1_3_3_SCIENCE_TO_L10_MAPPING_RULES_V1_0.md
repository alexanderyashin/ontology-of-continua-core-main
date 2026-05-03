# OC Core 1.3.3 Science to L10 Mapping Rules v1.0

Status: ACTIVE_MAPPING_RULES_V1_0
Artifact hash: `49bfacb2c26a70c641ae7a6eeb208eabcc333db553db8a4a8a8cd5a069a6df0c`

This is a mapping-rule artifact. It is separate from the L10 template and does not assess fill.

## Source Families

- formal_model_and_foundation: typed foundation, model definitions, k-level semantics, identity, boundary, and operator material (formal/**; proofs/**; releases/oc_core_1_3_3/**/theorem*; releases/oc_core_1_3_3/**/proof*)
- machine_checked_and_finite_semantics: Lean/Lake subset, finite-model semantics, witness cases, and tamper controls (formal/lean/**; proofs/finite_model_checks/**; releases/oc_core_1_3_3/**/finite*; releases/oc_core_1_3_3/**/lean*)
- empirical_computational_evidence: validation, target-blind/held-out evidence, simulation, adversarial simulation, and counterexample search material (validation/**; simulations/**; falsification/**; releases/oc_core_1_3_3/**/evidence*; releases/oc_core_1_3_3/**/validation*)
- prior_art_novelty_and_comparator: prior art, comparator, novelty, residual-delta, and positioning material (releases/oc_core_1_3_3/**/novelty*; releases/oc_core_1_3_3/**/comparator*; releases/oc_core_1_3_3/**/prior*)
- review_attack_response_and_limits: Cerberus, hostile review, claim-boundary, attack matrix, limitation, and failure-mode material (releases/oc_core_1_3_3/**/cerberus*; releases/oc_core_1_3_3/**/attack*; releases/oc_core_1_3_3/**/review*; releases/oc_core_1_3_3/**/limits*)
- reproducibility_governance_and_artifacts: artifact inventory, checksums, replay protocol, metadata, release governance, and traceability material (releases/oc_core_1_3_3/**/manifest*; releases/oc_core_1_3_3/**/checksum*; releases/oc_core_1_3_3/**/reproduc*; tools/oc133_*; tools/verify_oc133_*; tools/logion_project_controller.py; tools/logion_delta_queue.py; tools/logion_process_coherence_guard.py)
- didactic_synthesis_and_reader_guidance: worked examples, figures/tables, reader tracks, synthesis, and external-use guidance (releases/oc_core_1_3_3/**/didactic*; releases/oc_core_1_3_3/**/figure*; releases/oc_core_1_3_3/**/guide*; releases/oc_core_1_3_3/**/synthesis*)

## Role To Source Families

- definition_model: formal_model_and_foundation, prior_art_novelty_and_comparator, didactic_synthesis_and_reader_guidance
- proof_evidence: formal_model_and_foundation, machine_checked_and_finite_semantics, empirical_computational_evidence, reproducibility_governance_and_artifacts
- limits_falsifier: review_attack_response_and_limits, empirical_computational_evidence, prior_art_novelty_and_comparator
- synthesis_transition: didactic_synthesis_and_reader_guidance, reproducibility_governance_and_artifacts, review_attack_response_and_limits
