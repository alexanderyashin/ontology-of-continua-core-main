# OC Core 1.3.3 Empirical Capability Registry

Verdict: `CAPABILITY_REBALANCE_BLOCKED`
Total components discovered: `18`
Blocked components: `15`
Factory rows: `10`
Harvester rows: `2`
Executor rows: `3`
Planner rows: `3`
No-send lock: `True`
External network allowed: `False`
Automatic dispatch allowed: `False`

This registry does not execute external network calls; it only reads local artifacts and emits a deterministic no-send queue.

## Cockpit Locks

| Lock | Value |
| --- | ---: |
| `no_send` | `True` |
| `publish_allowed` | `False` |
| `journal_submissions_allowed` | `False` |
| `external_network_allowed` | `False` |
| `automatic_dispatch_allowed` | `False` |
| `owner_approval_required` | `True` |

## Compute-Degradation Notes

- Capability registry ran in local-read dispatcher mode and did not call component commands.
- No-send and automatic-dispatch locks keep all next actions as queue entries, not executions.
- Rows with blockers are ranked for blocker reconciliation before compute-heavy reruns.
- Rows without local payloads or open blockers degrade to monitoring until upstream inputs change.

## Ranked Components

| Position | Resource Class | Component | Blockers | Unblock Value | Next Action |
| --- | --- | --- | ---: | ---: | --- |
| `OC133-ECQ-001` | `factory` | `tools/oc133_systems_wdi_model_search_factory.py` | `41` | `4126` | `Refresh empirical factory outputs after removing blockers.` |
| `OC133-ECQ-002` | `harvester` | `validation/heldout/harvesters/systems_harvester.py` | `41` | `4101` | `Run harvester offline and reconcile blocker causes.` |
| `OC133-ECQ-003` | `factory` | `tools/oc133_grand_evidence_registry_sync_factory.py` | `18` | `2216` | `Refresh empirical factory outputs after removing blockers.` |
| `OC133-ECQ-004` | `planner` | `tools/oc133_physics_chemistry_acquisition_planner.py` | `15` | `1500` | `Run acquisition planner, then schedule bounded protocol updates.` |
| `OC133-ECQ-005` | `factory` | `tools/oc133_biology_ncbi_benchmark_factory.py` | `11` | `1376` | `Refresh empirical factory outputs after removing blockers.` |
| `OC133-ECQ-006` | `factory` | `tools/oc133_biology_ncbi_batch_factory.py` | `11` | `1375` | `Refresh empirical factory outputs after removing blockers.` |
| `OC133-ECQ-007` | `factory` | `tools/oc133_systems_wdi_benchmark_factory.py` | `9` | `1125` | `Refresh empirical factory outputs after removing blockers.` |
| `OC133-ECQ-008` | `factory` | `tools/oc133_systems_wdi_predictive_search_v2_factory.py` | `10` | `1026` | `Refresh empirical factory outputs after removing blockers.` |
| `OC133-ECQ-009` | `factory` | `tools/oc133_physics_chemistry_official_batch_factory.py` | `9` | `952` | `Refresh empirical factory outputs after removing blockers.` |
| `OC133-ECQ-010` | `factory` | `tools/oc133_chemistry_pubchem_formula_batch_factory.py` | `9` | `926` | `Refresh empirical factory outputs after removing blockers.` |
| `OC133-ECQ-011` | `factory` | `tools/oc133_grand_empirical_evidence_factory.py` | `5` | `500` | `Refresh empirical factory outputs after removing blockers.` |
| `OC133-ECQ-012` | `harvester` | `validation/heldout/harvesters/physics_chemistry_harvester.py` | `3` | `300` | `Run harvester offline and reconcile blocker causes.` |
| `OC133-ECQ-013` | `executor` | `validation/heldout/domain_evidence/biology_systems_evidence_executor.py` | `2` | `252` | `Run evidence executor to regenerate candidate packs and gate status.` |
| `OC133-ECQ-014` | `planner` | `tools/oc133_biology_systems_acquisition_planner.py` | `2` | `200` | `Run acquisition planner, then schedule bounded protocol updates.` |
| `OC133-ECQ-015` | `executor` | `validation/heldout/domain_evidence/mathematics_evidence_executor.py` | `1` | `126` | `Run evidence executor to regenerate candidate packs and gate status.` |
| `OC133-ECQ-016` | `executor` | `validation/heldout/domain_evidence/physics_chemistry_evidence_executor.py` | `0` | `52` | `Monitor for upstream input readiness; rerun to re-evaluate blockade.` |
| `OC133-ECQ-017` | `factory` | `tools/oc133_target_projection_lock_factory.py` | `0` | `0` | `Monitor for upstream input readiness; rerun to re-evaluate blockade.` |
| `OC133-ECQ-018` | `planner` | `tools/oc133_official_readonly_acquisition_runner.py` | `0` | `0` | `Monitor for upstream input readiness; rerun to re-evaluate blockade.` |

## Next-Action Queue

| Action ID | Position | Component | Command |
| --- | ---: | --- | --- |
| `OC133-ECQ-001` | `1` | `tools/oc133_systems_wdi_model_search_factory.py` | `python tools/oc133_systems_wdi_model_search_factory.py --write` |
| `OC133-ECQ-002` | `2` | `validation/heldout/harvesters/systems_harvester.py` | `python validation/heldout/harvesters/systems_harvester.py --write --offline --allow-blocked-exit-zero` |
| `OC133-ECQ-003` | `3` | `tools/oc133_grand_evidence_registry_sync_factory.py` | `python tools/oc133_grand_evidence_registry_sync_factory.py --write` |
| `OC133-ECQ-004` | `4` | `tools/oc133_physics_chemistry_acquisition_planner.py` | `python tools/oc133_physics_chemistry_acquisition_planner.py --write --allow-blocked-exit-zero` |
| `OC133-ECQ-005` | `5` | `tools/oc133_biology_ncbi_benchmark_factory.py` | `python tools/oc133_biology_ncbi_benchmark_factory.py --write` |
| `OC133-ECQ-006` | `6` | `tools/oc133_biology_ncbi_batch_factory.py` | `python tools/oc133_biology_ncbi_batch_factory.py --write` |
| `OC133-ECQ-007` | `7` | `tools/oc133_systems_wdi_benchmark_factory.py` | `python tools/oc133_systems_wdi_benchmark_factory.py --write` |
| `OC133-ECQ-008` | `8` | `tools/oc133_systems_wdi_predictive_search_v2_factory.py` | `python tools/oc133_systems_wdi_predictive_search_v2_factory.py --write` |
| `OC133-ECQ-009` | `9` | `tools/oc133_physics_chemistry_official_batch_factory.py` | `python tools/oc133_physics_chemistry_official_batch_factory.py --write` |
| `OC133-ECQ-010` | `10` | `tools/oc133_chemistry_pubchem_formula_batch_factory.py` | `python tools/oc133_chemistry_pubchem_formula_batch_factory.py --write` |
| `OC133-ECQ-011` | `11` | `tools/oc133_grand_empirical_evidence_factory.py` | `python tools/oc133_grand_empirical_evidence_factory.py --write` |
| `OC133-ECQ-012` | `12` | `validation/heldout/harvesters/physics_chemistry_harvester.py` | `python validation/heldout/harvesters/physics_chemistry_harvester.py --write --offline --allow-blocked-exit-zero` |
| `OC133-ECQ-013` | `13` | `validation/heldout/domain_evidence/biology_systems_evidence_executor.py` | `python validation/heldout/domain_evidence/biology_systems_evidence_executor.py --write --allow-blocked-exit-zero` |
| `OC133-ECQ-014` | `14` | `tools/oc133_biology_systems_acquisition_planner.py` | `python tools/oc133_biology_systems_acquisition_planner.py --write --allow-blocked-exit-zero` |
| `OC133-ECQ-015` | `15` | `validation/heldout/domain_evidence/mathematics_evidence_executor.py` | `python validation/heldout/domain_evidence/mathematics_evidence_executor.py --write --allow-blocked-exit-zero` |
| `OC133-ECQ-016` | `16` | `validation/heldout/domain_evidence/physics_chemistry_evidence_executor.py` | `python validation/heldout/domain_evidence/physics_chemistry_evidence_executor.py --write --allow-blocked-exit-zero` |
| `OC133-ECQ-017` | `17` | `tools/oc133_target_projection_lock_factory.py` | `python tools/oc133_target_projection_lock_factory.py --write` |
| `OC133-ECQ-018` | `18` | `tools/oc133_official_readonly_acquisition_runner.py` | `python tools/oc133_official_readonly_acquisition_runner.py --write --allow-blocked-exit-zero` |
