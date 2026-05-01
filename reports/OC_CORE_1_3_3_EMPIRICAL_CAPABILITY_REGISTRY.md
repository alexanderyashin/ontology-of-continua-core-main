# OC Core 1.3.3 Empirical Capability Registry

Verdict: `CAPABILITY_REBALANCE_BLOCKED`
Total components discovered: `10`
Blocked components: `9`
Factory rows: `3`
Harvester rows: `2`
Executor rows: `3`
Planner rows: `2`
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
| `OC133-ECQ-001` | `harvester` | `validation/heldout/harvesters/systems_harvester.py` | `41` | `4101` | `Run harvester offline and reconcile blocker causes.` |
| `OC133-ECQ-002` | `planner` | `tools/oc133_physics_chemistry_acquisition_planner.py` | `15` | `1500` | `Run acquisition planner, then schedule bounded protocol updates.` |
| `OC133-ECQ-003` | `factory` | `tools/oc133_biology_ncbi_benchmark_factory.py` | `11` | `1376` | `Refresh empirical factory outputs after removing blockers.` |
| `OC133-ECQ-004` | `factory` | `tools/oc133_systems_wdi_benchmark_factory.py` | `9` | `1125` | `Refresh empirical factory outputs after removing blockers.` |
| `OC133-ECQ-005` | `factory` | `tools/oc133_grand_empirical_evidence_factory.py` | `5` | `500` | `Refresh empirical factory outputs after removing blockers.` |
| `OC133-ECQ-006` | `harvester` | `validation/heldout/harvesters/physics_chemistry_harvester.py` | `3` | `300` | `Run harvester offline and reconcile blocker causes.` |
| `OC133-ECQ-007` | `executor` | `validation/heldout/domain_evidence/biology_systems_evidence_executor.py` | `2` | `252` | `Run evidence executor to regenerate candidate packs and gate status.` |
| `OC133-ECQ-008` | `planner` | `tools/oc133_biology_systems_acquisition_planner.py` | `2` | `200` | `Run acquisition planner, then schedule bounded protocol updates.` |
| `OC133-ECQ-009` | `executor` | `validation/heldout/domain_evidence/mathematics_evidence_executor.py` | `1` | `126` | `Run evidence executor to regenerate candidate packs and gate status.` |
| `OC133-ECQ-010` | `executor` | `validation/heldout/domain_evidence/physics_chemistry_evidence_executor.py` | `0` | `52` | `Monitor for upstream input readiness; rerun to re-evaluate blockade.` |

## Next-Action Queue

| Action ID | Position | Component | Command |
| --- | ---: | --- | --- |
| `OC133-ECQ-001` | `1` | `validation/heldout/harvesters/systems_harvester.py` | `python validation/heldout/harvesters/systems_harvester.py --write --offline --allow-blocked-exit-zero` |
| `OC133-ECQ-002` | `2` | `tools/oc133_physics_chemistry_acquisition_planner.py` | `python tools/oc133_physics_chemistry_acquisition_planner.py --write --allow-blocked-exit-zero` |
| `OC133-ECQ-003` | `3` | `tools/oc133_biology_ncbi_benchmark_factory.py` | `python tools/oc133_biology_ncbi_benchmark_factory.py --write` |
| `OC133-ECQ-004` | `4` | `tools/oc133_systems_wdi_benchmark_factory.py` | `python tools/oc133_systems_wdi_benchmark_factory.py --write` |
| `OC133-ECQ-005` | `5` | `tools/oc133_grand_empirical_evidence_factory.py` | `python tools/oc133_grand_empirical_evidence_factory.py --write` |
| `OC133-ECQ-006` | `6` | `validation/heldout/harvesters/physics_chemistry_harvester.py` | `python validation/heldout/harvesters/physics_chemistry_harvester.py --write --offline --allow-blocked-exit-zero` |
| `OC133-ECQ-007` | `7` | `validation/heldout/domain_evidence/biology_systems_evidence_executor.py` | `python validation/heldout/domain_evidence/biology_systems_evidence_executor.py --write --allow-blocked-exit-zero` |
| `OC133-ECQ-008` | `8` | `tools/oc133_biology_systems_acquisition_planner.py` | `python tools/oc133_biology_systems_acquisition_planner.py --write --allow-blocked-exit-zero` |
| `OC133-ECQ-009` | `9` | `validation/heldout/domain_evidence/mathematics_evidence_executor.py` | `python validation/heldout/domain_evidence/mathematics_evidence_executor.py --write --allow-blocked-exit-zero` |
| `OC133-ECQ-010` | `10` | `validation/heldout/domain_evidence/physics_chemistry_evidence_executor.py` | `python validation/heldout/domain_evidence/physics_chemistry_evidence_executor.py --write --allow-blocked-exit-zero` |
