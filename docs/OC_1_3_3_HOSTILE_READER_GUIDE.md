# OC Core 1.3.3 Hostile Reader Guide

This is the skeptical route table. While G57/G58/G70 are open, theorem rows are candidate routes, not release-promoted claims. A route becomes promoted only when the claim ledger reports `release_promotion_allowed=true`.

| Claim | Public status | Blockers | Tuple components | Lean certificate | Lean ref | Finite positive | Negative control | Falsifier boundary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `T133-K0-RES` | `BLOCKED_PENDING_ADVERSARIAL_REPAIR_V12` | `14` | `k; carrier; realization` | `formal/lean/LEAN_BUILD_CERTIFICATE_1_3_3.json` | `formal/lean/OC133V12.lean::k0_countermodel_raw_separation_not_resolution_distinction` | `FM-T133-K0-RES-POS` | `FM-T133-K0-RES-NEG` | A proof that assumes every pair of raw real states is epsilon-separated is outside v12 and fails G33. |
| `T133-OMEGA-STATUS` | `BLOCKED_PENDING_ADVERSARIAL_REPAIR_V12` | `14` | `liveness; residue; morphisms` | `formal/lean/LEAN_BUILD_CERTIFICATE_1_3_3.json` | `formal/lean/OC133V12.lean::lifecycle_residue_rebirth_morphism_boundary` | `FM-T133-OMEGA-STATUS-POS` | `FM-T133-OMEGA-STATUS-NEG` | Any claim reading residue-preserving restart as same-identity survival is rejected unless endpoint-bound identity evidence is supplied. |
| `T133-K-ZERO` | `BLOCKED_PENDING_ADVERSARIAL_REPAIR_V12` | `14` | `k; lawful_possibility; cycles` | `formal/lean/LEAN_BUILD_CERTIFICATE_1_3_3.json` | `formal/lean/OC133V12.lean::continuumness_zero_case_iff_declared_zero_cause_with_support` | `FM-T133-K-ZERO-POS` | `FM-T133-K-ZERO-NEG` | A realization with undeclared zero-cause, missing live support, or any active obstruction may not promote k=0. |
| `T133-BOUNDARY` | `BLOCKED_PENDING_ADVERSARIAL_REPAIR_V12` | `14` | `boundaries; realization` | `formal/lean/LEAN_BUILD_CERTIFICATE_1_3_3.json` | `formal/lean/OC133V12.lean::metric_boundary_specialization` | `FM-T133-BOUNDARY-POS` | `FM-T133-BOUNDARY-NEG` | A social or logical boundary represented numerically without a measurement rule is blocked by G40. |
| `T133-HYBRID` | `BLOCKED_PENDING_ADVERSARIAL_REPAIR_V12` | `14` | `operators; lawful_possibility` | `formal/lean/LEAN_BUILD_CERTIFICATE_1_3_3.json` | `formal/lean/OC133V12.lean::smooth_hybrid_operator_semantics` | `FM-T133-HYBRID-POS; FM-T133-HYBRID-PROOF-UPDATE-POS` | `FM-T133-HYBRID-NEG; FM-T133-HYBRID-PROOF-UPDATE-NEG` | Any section treating a chart token as a differentiability, manifold, vector-field, or ODE-solution theorem fails G41. |
| `T133-DIM` | `BLOCKED_PENDING_ADVERSARIAL_REPAIR_V12` | `14` | `dimension; realization` | `formal/lean/LEAN_BUILD_CERTIFICATE_1_3_3.json` | `formal/lean/OC133V12.lean::historical_axis_survives_rank_drop` | `FM-T133-DIM-POS` | `FM-T133-DIM-NEG` | A K-level is demotable only when the alleged new axis has no witness and no observable consequence. |
| `T133-CYCLE` | `BLOCKED_PENDING_ADVERSARIAL_REPAIR_V12` | `14` | `cycles; liveness` | `formal/lean/LEAN_BUILD_CERTIFICATE_1_3_3.json` | `formal/lean/OC133V12.lean::eligible_live_requires_cycle_or_maintenance` | `FM-T133-CYCLE-POS` | `FM-T133-CYCLE-NEG` | An artifact that never updates, replays, checks, or maintains itself is archive residue, not live continuum. |
| `T133-ID` | `BLOCKED_PENDING_ADVERSARIAL_REPAIR_V12` | `14` | `morphisms; residue; liveness` | `formal/lean/LEAN_BUILD_CERTIFICATE_1_3_3.json` | `formal/lean/OC133V12.lean::endpoint_bound_identity_classification` | `FM-T133-ID-POS` | `FM-T133-ID-NEG` | Any public claim reading rebirth as literal same-identity survival is blocked. |
| `T133-MIN` | `BLOCKED_PENDING_ADVERSARIAL_REPAIR_V12` | `14` | `carrier; realization; lawful_possibility; liveness; residue; morphisms; boundaries; operators; cycles; dimension; k` | `formal/lean/LEAN_BUILD_CERTIFICATE_1_3_3.json` | `formal/lean/OC133V12.lean::release_tuple_semantic_component_irredundant` | `FM-T133-MIN-POS` | `FM-T133-MIN-NEG` | If any promoted tuple component can be removed while `FM-MIN-*` still returns PASS for the declared semantic verdict suite, the minimality card fails. |
| `T133-KLEVEL` | `BLOCKED_PENDING_ADVERSARIAL_REPAIR_V12` | `14` | `k; carrier; realization; operators; boundaries` | `formal/lean/LEAN_BUILD_CERTIFICATE_1_3_3.json` | `formal/lean/OC133V12.lean::release_atlas_manifest_has_total_finite_case_coverage` | `FM-T133-KLEVEL-POS` | `FM-T133-KLEVEL-NEG` | If any adjacent K row lacks row identity, retained-witness evaluator failure, or inert-witness demotion control, the finite negative control fails; independent semantic irreducibility remains unpromoted unless separately proven. |

## Prediction Limits

All official-data numeric rows are replay QA. They are barred from empirical or prediction support until a prospective, target-blind protocol exists.

Numeric replay QA table: `validation/numeric_replay_qa/OC133_NUMERIC_REPLAY_QA_TABLE.json`.

| Claim | Mode | Dataset/evidence | Negative control | Falsifier | Prediction support | Empirical support |
| --- | --- | --- | --- | --- | --- | --- |
| `OC133-NUM-PHYS-C` | `REPLAY_QA` | `validation/_raw/physics_nist_constants.txt` | replace c by 300000000 and residual becomes nonzero | NIST snapshot parse does not yield 299792458 m s^-1 | `false` | `false` |
| `OC133-NUM-CHEM-WEBBOOK-H2O` | `REPLAY_QA` | `validation/_raw/chemistry_nist_webbook_water.txt` | use CO2 molecular-weight value against NIST WebBook water snapshot and require mismatch | NIST Chemistry WebBook snapshot parser cannot recover molecularWeight=18.0153 for water | `false` | `false` |
| `OC133-NUM-CHEM-H2O` | `REPLAY_QA` | `validation/_raw/chemistry_pubchem_water.txt` | use CO2 molecular-weight field against water snapshot and require mismatch | PubChem snapshot parser cannot recover MolecularWeight=18.015 for CID 962 | `false` | `false` |
| `OC133-NUM-BIO-GEO-COUNT` | `REPLAY_QA` | `validation/_raw/biology_ncbi_geo_platform.txt` | synthetic +1 count mutation against the pinned accession snapshot | replay parser cannot recover the pinned count | `false` | `false` |
| `OC133-NUM-SYS-WDI-GDP` | `REPLAY_QA` | `validation/_raw/systems_world_bank_gdp.txt` | remove or corrupt the latest WDI value and require replay parser failure | replay parser cannot recover the pinned latest non-null WDI value | `false` | `false` |
| `OC133-NUM-MATH-FINITE` | `REPLAY_QA` | `proofs/FINITE_MODEL_CHECKS_1_3_3.json` | remove a required tuple component and observe rejected stronger reading | any finite model case has observed verdict different from expected | `false` | `false` |

Every row above is barred from empirical/prediction promotion: `prediction_support_allowed=false` and `empirical_support_allowed=false`. The replay QA table is the controlling row-level artifact.

## Novelty Limits

The comparator matrix accepts prior-art overlap first. Uniqueness, priority, and absence claims are not promoted by the public claim ledger.

## Public-Action Limits

The no-send finite case reads the current owner approval and publish manifest. GitHub, Zenodo, Software Heritage, journal submission, and DOI minting remain locked.
