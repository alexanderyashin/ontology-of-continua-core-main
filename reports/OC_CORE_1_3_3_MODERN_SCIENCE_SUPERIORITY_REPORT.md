# OC Core 1.3.3 Modern Science Superiority Report

Verdict: `BROAD_MODERN_SCIENCE_SUPERIORITY_BLOCKED_BENCHMARK_SCOPED_BASELINES_CERTIFIED`

Release promotion allowed: `false`

The current strict packs certify only benchmark-scoped superiority over declared preregistered baselines. They do not support the broad claim that OC predicts better than modern science.

| Domain | Pack | Pack SHA-256 | OC residual | Comparator residual | Benchmark verdict | Broad verdict |
| --- | --- | --- | --- | --- | --- | --- |
| `biology` | `validation/heldout/grand_science/biology/target_evidence/biology_target_evidence_candidate_pack.json` | `384783b167c7b1b7e6082c753dcb5b2b51a6c6a2ce22513205f7daad5ed9a9c9` | `7.066666666666666` | `753.34` | `CERTIFIED_AGAINST_DECLARED_INCUMBENT_BENCHMARK_BASELINES` | `BLOCKED_UNSUPPORTED_BROAD_WORDING` |
| `chemistry` | `validation/heldout/grand_science/chemistry/pubchem_hbond_donor/OC133_CHEMISTRY_PUBCHEM_HBOND_DONOR_CANDIDATE_PACK.json` | `69474ea613e339e51969e48a9d5043efc99785f53ee42933299cbb4bfd2f1ca3` | `0.0` | `0.65` | `CERTIFIED_AGAINST_DECLARED_INCUMBENT_BENCHMARK_BASELINES` | `BLOCKED_UNSUPPORTED_BROAD_WORDING` |
| `physics` | `validation/heldout/grand_science/physics_chemistry/official_batch/physics_official_batch_candidate_evidence_pack.json` | `8ee7d8282e04c6e15ee780e97d4a2766ed92e6300df4de548a739ec36209c6c4` | `0.010729530673706203` | `3.4320356941968604e+43` | `CERTIFIED_AGAINST_DECLARED_INCUMBENT_BENCHMARK_BASELINES` | `BLOCKED_UNSUPPORTED_BROAD_WORDING` |
| `systems` | `validation/heldout/grand_science/systems/wdi_population_materiality/OC133_SYSTEMS_WDI_POPULATION_MATERIALITY_CANDIDATE_PACK.json` | `ddd022b3b95168ed28efe642cab738529bd57d12d1807689802987397cea1fbd` | `6272.05` | `461289.35` | `CERTIFIED_AGAINST_DECLARED_INCUMBENT_BENCHMARK_BASELINES` | `BLOCKED_UNSUPPORTED_BROAD_WORDING` |

Blocking summary:

- Current strict evidence packs support only benchmark-scoped superiority over declared preregistered comparator baselines.
- No artifact in this register surveys or defeats all modern-science incumbents across a domain, much less all of modern science.
- The broad wording 'predicts better than modern science' remains blocked.
- Independent clean temp-tree replay is bound to the register for the current strict packs; broad coverage remains blocked.

Executable validation:

- `python benchmarks/modern_science/clean_checkout_replay.py --write`
- `python tools/oc133_modern_science_comparator_factory.py --check`
- `python benchmarks/modern_science/validate_modern_science_register.py`
