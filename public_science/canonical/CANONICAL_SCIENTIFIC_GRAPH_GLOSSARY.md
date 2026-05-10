# Canonical Scientific Graph Glossary

This glossary is the public reviewer navigation copy for the canonical scientific graph.

## First Checks

- Manifest: `public_science/canonical/CANONICAL_SCIENTIFIC_GRAPH_MANIFEST.json`
- Verification command: `python tools/build_canonical_scientific_graph.py --verify-only`
- Theorem graph: `public_science/canonical/THEOREM_GRAPH.json`
- Proof graph: `public_science/canonical/PROOF_GRAPH.json`
- Evidence graph: `public_science/canonical/EVIDENCE_GRAPH.json`

## Core Terms

| Term | Kind | Public ref | Reviewer use |
| --- | --- | --- | --- |
| Canonical scientific graph | graph-system | `public_science/canonical/CANONICAL_SCIENTIFIC_GRAPH_MANIFEST.json` | Start here to check status, source hashes, verification command, and graph references. |
| Theorem graph | graph | `public_science/canonical/THEOREM_GRAPH.json` | Lists promoted theorem nodes and their claim, proof sheet, Lean, and finite-check edges. |
| Proof graph | graph | `public_science/canonical/PROOF_GRAPH.json` | Carries proof dependency rows, Lean certificate refs, finite checks, and grand formal obligation status. |
| Evidence graph | graph | `public_science/canonical/EVIDENCE_GRAPH.json` | Carries selected empirical evidence packs and support edges into the grand scientific closure claim. |
| Lean build certificate | formal-certificate | `formal/lean/LEAN_BUILD_CERTIFICATE_1_3_3.json` | Checks compiled Lean source refs and theorem declaration coverage. |
| Finite model checks | finite-check-ledger | `proofs/FINITE_MODEL_CHECKS_1_3_3.json` | Checks finite accept/reject witness cases bound to theorem rows. |
| Grand formal obligation ledger | promotion-ledger | `proofs/GRAND_TOE_FORMAL_OBLIGATION_LEDGER_1_3_3.json` | Checks the formal promotion gate for the declared scientific closure. |
| Science SPOT gate | review-gate | `releases/oc_core_1_3/editorial/OC_CORE_1_3_SCIENCE_SPOT_latest.json` | Checks hostile-review closure for the science surface used by this graph. |

## Theorem Navigation

| Theorem id | Title | Proof sheet | Lean ref | Finite cases |
| --- | --- | --- | --- | --- |
| T133-K0-RES | K0 resolution-relative distinguishability theorem | `proofs/proof_sheets/T133-K0-RES.md` | `formal/lean/OC133V12.lean::k0_countermodel_raw_separation_not_resolution_distinction` | 2 |
| T133-OMEGA-STATUS | Typed liveness, death, residue, and rebirth evidence-consistency theorem | `proofs/proof_sheets/T133-OMEGA-STATUS.md` | `formal/lean/OC133V12.lean::lifecycle_residue_rebirth_morphism_boundary` | 3 |
| T133-K-ZERO | Continuumness zero obstruction theorem | `proofs/proof_sheets/T133-K-ZERO.md` | `formal/lean/OC133V12.lean::continuumness_zero_case_iff_declared_zero_cause_with_support` | 4 |
| T133-BOUNDARY | Metric-threshold boundary specialization theorem | `proofs/proof_sheets/T133-BOUNDARY.md` | `formal/lean/OC133V12.lean::metric_boundary_specialization` | 3 |
| T133-HYBRID | Typed update and chart-labelled operator semantics theorem | `proofs/proof_sheets/T133-HYBRID.md` | `formal/lean/OC133V12.lean::integrated_operator_semantics` | 15 |
| T133-DIM | Historical axis and effective-rank compatibility theorem | `proofs/proof_sheets/T133-DIM.md` | `formal/lean/OC133V12.lean::historical_axis_survives_rank_drop` | 2 |
| T133-CYCLE | Live-status cycle-mode requirement theorem | `proofs/proof_sheets/T133-CYCLE.md` | `formal/lean/OC133V12.lean::eligible_live_requires_cycle_or_maintenance` | 2 |
| T133-ID | Identity, residue, and rebirth evidence-classification theorem | `proofs/proof_sheets/T133-ID.md` | `formal/lean/OC133V12.lean::endpoint_bound_identity_classification` | 53 |
| T133-MIN | Declared semantic-verdict component independence theorem | `proofs/proof_sheets/T133-MIN.md` | `formal/lean/OC133V12.lean::release_tuple_semantic_component_irredundant` | 14 |
| T133-KLEVEL | Declared adjacent K-level atlas/evaluator consistency theorem | `proofs/proof_sheets/T133-KLEVEL.md` | `formal/lean/OC133V12.lean::release_atlas_manifest_has_total_finite_case_coverage` | 30 |
| OC133-GRAND-TOE-DECLARED-TAXONOMY-PROMOTION | Declared-taxonomy grand TOE promotion contract theorem | `proofs/proof_sheets/OC133-GRAND-TOE-DECLARED-TAXONOMY-PROMOTION.md` | `formal/lean/OC133GrandPromotion.lean::grand_promotion_declared_taxonomy_support_closes_when_all_obligations_pass` | 2 |

## Evidence Navigation

| Domain | Evidence pack | Source ref | Supports |
| --- | --- | --- | --- |
| biology | OC133-BIOLOGY-TARGET-EVIDENCE-CANDIDATE | `validation/heldout/grand_science/biology/target_evidence/biology_target_evidence_candidate_pack.json` | `grand_claim:DECLARED_TOE_SCIENTIFIC_CLOSURE` |
| chemistry | OC133-GRAND-CHEMISTRY-PUBCHEM-HBOND-DONOR | `validation/heldout/grand_science/chemistry/pubchem_hbond_donor/OC133_CHEMISTRY_PUBCHEM_HBOND_DONOR_CANDIDATE_PACK.json` | `grand_claim:DECLARED_TOE_SCIENTIFIC_CLOSURE` |
| physics | OC133-PHYSICS-OFFICIAL-SNAPSHOT-BATCH-CANDIDATE | `validation/heldout/grand_science/physics_chemistry/official_batch/physics_official_batch_candidate_evidence_pack.json` | `grand_claim:DECLARED_TOE_SCIENTIFIC_CLOSURE` |
| systems | OC133-SYSTEMS-WDI-POPULATION-MATERIALITY-CANDIDATE | `validation/heldout/grand_science/systems/wdi_population_materiality/OC133_SYSTEMS_WDI_POPULATION_MATERIALITY_CANDIDATE_PACK.json` | `grand_claim:DECLARED_TOE_SCIENTIFIC_CLOSURE` |
