# OC Core 1.3.3 v12 Proof Ledger

Each row below is a proof-obligation ledger, not only a status table. The public claim is allowed only when the proof sheet, Lean subset, finite positive case, finite negative case, and counterexample boundary all exist.

| Theorem | Obligation | Proof sheet | Lean subset | Finite checks |
| --- | --- | --- | --- | --- |
| `T133-K0-RES` | public claim must match assumptions and counterexample boundary | `proofs/proof_sheets/T133-K0-RES.md` | `formal/lean/OC133V12.lean::k0_countermodel_raw_separation_not_resolution_distinction` | `FM-T133-K0-RES-POS`, `FM-T133-K0-RES-NEG` |
| `T133-OMEGA-STATUS` | public claim must match assumptions and counterexample boundary | `proofs/proof_sheets/T133-OMEGA-STATUS.md` | `formal/lean/OC133V12.lean::lifecycle_residue_rebirth_morphism_boundary` | `FM-T133-OMEGA-STATUS-POS`, `FM-T133-OMEGA-STATUS-NEG` |
| `T133-K-ZERO` | public claim must match assumptions and counterexample boundary | `proofs/proof_sheets/T133-K-ZERO.md` | `formal/lean/OC133V12.lean::continuumness_zero_case_iff_declared_zero_cause_with_support` | `FM-T133-K-ZERO-POS`, `FM-T133-K-ZERO-NEG` |
| `T133-BOUNDARY` | public claim must match assumptions and counterexample boundary | `proofs/proof_sheets/T133-BOUNDARY.md` | `formal/lean/OC133V12.lean::metric_boundary_specialization` | `FM-T133-BOUNDARY-POS`, `FM-T133-BOUNDARY-NEG` |
| `T133-HYBRID` | public claim must match assumptions and counterexample boundary | `proofs/proof_sheets/T133-HYBRID.md` | `formal/lean/OC133V12.lean::operator_admission_route_obligations` | `FM-T133-HYBRID-POS`, `FM-T133-HYBRID-NEG` |
| `T133-DIM` | public claim must match assumptions and counterexample boundary | `proofs/proof_sheets/T133-DIM.md` | `formal/lean/OC133V12.lean::historical_axis_survives_rank_drop` | `FM-T133-DIM-POS`, `FM-T133-DIM-NEG` |
| `T133-CYCLE` | public claim must match assumptions and counterexample boundary | `proofs/proof_sheets/T133-CYCLE.md` | `formal/lean/OC133V12.lean::eligible_live_requires_cycle_or_maintenance` | `FM-T133-CYCLE-POS`, `FM-T133-CYCLE-NEG` |
| `T133-ID` | public claim must match assumptions and counterexample boundary | `proofs/proof_sheets/T133-ID.md` | `formal/lean/OC133V12.lean::endpoint_bound_identity_classification` | `FM-T133-ID-POS`, `FM-T133-ID-NEG` |
| `T133-MIN` | public claim must match assumptions and counterexample boundary | `proofs/proof_sheets/T133-MIN.md` | `formal/lean/OC133V12.lean::release_tuple_semantic_component_irredundant` | `FM-T133-MIN-POS`, `FM-T133-MIN-NEG` |
| `T133-KLEVEL` | public claim must match assumptions and counterexample boundary | `proofs/proof_sheets/T133-KLEVEL.md` | `formal/lean/OC133V12.lean::release_atlas_manifest_has_total_finite_case_coverage` | `FM-T133-KLEVEL-POS`, `FM-T133-KLEVEL-NEG` |

## Minimality Coverage

T133-MIN is bound to `data/OC133_GLOBAL_MINIMALITY_WITNESSES.json` and to one executable keep/drop row per promoted tuple component in `proofs/FINITE_MODEL_CHECKS_1_3_3.json`.

## K-Level Coverage

T133-KLEVEL is bound to `data/k_level_irreducibility_matrix.json` and to one executable adjacent-transition row for each K0->K1 through K11->K12 transition.
