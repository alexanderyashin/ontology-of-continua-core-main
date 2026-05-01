# OC Core 1.3.3 Modern Science Superiority Report

Verdict: `BLOCKED_NO_MODERN_SCIENCE_SUPERIORITY_CERTIFIED`

Release promotion allowed: `false`

This report records source-backed comparator lanes only. It does not certify OC Core 1.3.3 superiority over modern science.

| Domain | Incumbent source | OC result | Comparator result | Benchmark predicate | Uncertainty/fairness | Blocker reason |
| --- | --- | --- | --- | --- | --- | --- |
| `physics` | NIST CODATA recommended values of the fundamental physical constants, 2022 adjustment | `BOUNDED_TARGET_BLIND_RECONSTRUCTION_NOT_SUPERIORITY` residual `1.4892870576445277e-35` | `unit-incompatible Planck-constant-only negative control` residual `1.9864458503739297e-25` | `MS-PRED-PHYS-001` `BLOCKED_NO_SUPERIORITY_CERTIFIED` | uncertainty `1e-33`, `BOUNDED_FAIRNESS_INSUFFICIENT_FOR_SUPERIORITY` | `independent_replay_passes_from_clean_checkout, result_is_not_merely_exact_standard_replay, domain_relevance_exceeds_exact_standard_replay` |
| `chemistry` | NIST Chemistry WebBook, SRD 69, Water, PubChem compound record, Water, CID 962 | `BOUNDED_TARGET_BLIND_RECONSTRUCTION_NOT_SUPERIORITY` residual `0.000280000000000058` | `CO2 molecular-weight negative control against water target` residual `25.994500000000002` | `MS-PRED-CHEM-001` `BLOCKED_NO_SUPERIORITY_CERTIFIED` | uncertainty `0.02`, `BOUNDED_FAIRNESS_INSUFFICIENT_FOR_SUPERIORITY` | `independent_replay_passes_from_clean_checkout, not_a_curated_field_copy, domain_relevance_exceeds_curated_field_reconstruction` |
| `biology` | NCBI Gene Expression Omnibus overview and dataset documentation | `BOUNDED_TARGET_BLIND_RECONSTRUCTION_NOT_SUPERIORITY` residual `0.0` | `use total hit count as pagination-size negative control` residual `43988.0` | `MS-PRED-BIO-001` `BLOCKED_NO_SUPERIORITY_CERTIFIED` | uncertainty `0.0`, `BOUNDED_FAIRNESS_INSUFFICIENT_FOR_SUPERIORITY` | `independent_replay_passes_from_clean_checkout, biological_mechanism_test_present` |
| `systems` | World Bank WDI metadata for NY.GDP.MKTP.CD | `BOUNDED_TARGET_BLIND_RECONSTRUCTION_NOT_SUPERIORITY` residual `59572919095.09375` | `last-observation carry-forward GDP_2023` residual `4241013358949.0` | `MS-PRED-SYS-001` `BLOCKED_NO_SUPERIORITY_CERTIFIED` | uncertainty `1109826611800.1301`, `BOUNDED_FAIRNESS_INSUFFICIENT_FOR_SUPERIORITY` | `independent_replay_passes_from_clean_checkout, prospective_or_time-locked_protocol_present` |
| `mathematics` | Lean 4 official site | `BOUNDED_TARGET_BLIND_RECONSTRUCTION_NOT_SUPERIORITY` residual `0.0` | `positive_case_total negative control, which counts non-theorem support rows too` residual `11.0` | `MS-PRED-MATH-001` `BLOCKED_NO_SUPERIORITY_CERTIFIED` | uncertainty `0.0`, `BOUNDED_FAIRNESS_INSUFFICIENT_FOR_SUPERIORITY` | `independent_replay_passes_from_clean_checkout, machine_checked_theorem_scope_matches_public_claim` |

Blocking summary:

- No lane has clean-checkout independent replay recorded in this register.
- Physics and chemistry lanes remain exact-standard or curated-field reconstruction, not superiority evidence.
- Biology lacks a biological mechanism benchmark beyond API/query accounting.
- Systems lacks a prospective or time-locked protocol beyond retrospective pinned WDI rows.
- Mathematics lacks public claim scope matching strong enough to certify superiority over Lean/formal mathematics.

Executable validation:

- `python tools/oc133_modern_science_comparator_factory.py --check`
- `python benchmarks/modern_science/validate_modern_science_register.py`

Work-order decomposition:

- `physics` `independent_replay_passes_from_clean_checkout`: Run an independent clean-checkout replay with command, output tail, artifact hashes, and environment note recorded.
- `physics` `result_is_not_merely_exact_standard_replay`: Replace exact reference-standard replay with a domain-relevant held-out or prospective physics benchmark before scoring.
- `physics` `domain_relevance_exceeds_exact_standard_replay`: Replace exact reference-standard replay with a domain-relevant held-out or prospective physics benchmark before scoring.
- `physics` `GENUINE_EVIDENCE_N_BELOW_MINIMUM::0/20`: Provide a valid per-domain evidence pack at the required N with target-blind or prospective source separation.
- `physics` `NO_VALID_PROSPECTIVE_OR_TARGET_BLIND_EVIDENCE_PACK`: Provide a valid per-domain evidence pack at the required N with target-blind or prospective source separation.
- `physics` `CANDIDATE_EVIDENCE_PACKS_INVALID::1`: Provide a valid per-domain evidence pack at the required N with target-blind or prospective source separation.
- `chemistry` `independent_replay_passes_from_clean_checkout`: Run an independent clean-checkout replay with command, output tail, artifact hashes, and environment note recorded.
- `chemistry` `not_a_curated_field_copy`: Separate curated-field parser replay from a chemistry benchmark whose targets, baselines, uncertainty, and negative controls are declared before scoring.
- `chemistry` `domain_relevance_exceeds_curated_field_reconstruction`: Separate curated-field parser replay from a chemistry benchmark whose targets, baselines, uncertainty, and negative controls are declared before scoring.
- `chemistry` `GENUINE_EVIDENCE_N_BELOW_MINIMUM::0/20`: Provide a valid per-domain evidence pack at the required N with target-blind or prospective source separation.
- `chemistry` `NO_VALID_PROSPECTIVE_OR_TARGET_BLIND_EVIDENCE_PACK`: Provide a valid per-domain evidence pack at the required N with target-blind or prospective source separation.
- `chemistry` `CANDIDATE_EVIDENCE_PACKS_INVALID::1`: Provide a valid per-domain evidence pack at the required N with target-blind or prospective source separation.
- `biology` `independent_replay_passes_from_clean_checkout`: Run an independent clean-checkout replay with command, output tail, artifact hashes, and environment note recorded.
- `biology` `biological_mechanism_test_present`: Add a source-backed biological mechanism benchmark instead of repository pagination/count reconstruction.
- `biology` `GENUINE_EVIDENCE_N_BELOW_MINIMUM::0/20`: Provide a valid per-domain evidence pack at the required N with target-blind or prospective source separation.
- `biology` `NO_VALID_PROSPECTIVE_OR_TARGET_BLIND_EVIDENCE_PACK`: Provide a valid per-domain evidence pack at the required N with target-blind or prospective source separation.
- `biology` `CANDIDATE_EVIDENCE_PACKS_INVALID::1`: Provide a valid per-domain evidence pack at the required N with target-blind or prospective source separation.
- `systems` `independent_replay_passes_from_clean_checkout`: Run an independent clean-checkout replay with command, output tail, artifact hashes, and environment note recorded.
- `systems` `prospective_or_time-locked_protocol_present`: Add a prospective or time-locked WDI/systems protocol with comparator and scoring locked before the target is read.
- `systems` `GENUINE_EVIDENCE_N_BELOW_MINIMUM::0/20`: Provide a valid per-domain evidence pack at the required N with target-blind or prospective source separation.
- `systems` `NO_VALID_PROSPECTIVE_OR_TARGET_BLIND_EVIDENCE_PACK`: Provide a valid per-domain evidence pack at the required N with target-blind or prospective source separation.
- `systems` `CANDIDATE_EVIDENCE_PACKS_INVALID::1`: Provide a valid per-domain evidence pack at the required N with target-blind or prospective source separation.
- `mathematics` `independent_replay_passes_from_clean_checkout`: Run an independent clean-checkout replay with command, output tail, artifact hashes, and environment note recorded.
- `mathematics` `machine_checked_theorem_scope_matches_public_claim`: Bind public mathematical claim scope to machine-checked Lean/formal artifacts and an independently replayed proof surface.
- `mathematics` `GENUINE_EVIDENCE_N_BELOW_MINIMUM::0/20`: Provide a valid per-domain evidence pack at the required N with target-blind or prospective source separation.
- `mathematics` `NO_VALID_PROSPECTIVE_OR_TARGET_BLIND_EVIDENCE_PACK`: Provide a valid per-domain evidence pack at the required N with target-blind or prospective source separation.
- `mathematics` `NO_CANDIDATE_EVIDENCE_PACK_DISCOVERED`: Provide a valid per-domain evidence pack at the required N with target-blind or prospective source separation.
- `mathematics` `CURRENT_FORMAL_CORPUS_BASELINE_IS_NOT_EMPIRICAL_GRAND_SCIENCE_EVIDENCE`: Provide a valid per-domain evidence pack at the required N with target-blind or prospective source separation.

Allowed current claim: OC Core 1.3.3 has source-backed comparator lanes and bounded reconstruction/QA predicates; it does not certify superiority to modern science.
