# OC Core 1.3.3 Empirical Capability Dispatcher

Verdict: `DISPATCH_RAN_WITH_SCIENTIFIC_BLOCKERS`
Execute requested: `True`
Selected actions: `10`
Executed actions: `10`
Rejected actions: `0`
Executor successes: `10`
Command failures: `0`
Scientific blockers: `10`
PASS actions: `0`

No network by default: only allowlisted local Python commands run; harvester commands require --offline; proxy variables are stripped from command environments.

Dispatcher PASS means command execution succeeded and the returned scientific payload is not blocked. A zero return code with blockers is recorded as executor_success plus SCIENTIFIC_BLOCKED, not PASS.

## Cockpit Locks

| Lock | Value |
| --- | ---: |
| `automatic_dispatch_allowed` | `False` |
| `external_network_allowed` | `False` |
| `journal_submissions_allowed` | `False` |
| `no_send` | `True` |
| `owner_approval_required` | `True` |
| `publish_allowed` | `False` |

## Dispatch Results

| Action | Component | Allowed | Executed | Return code | Outcome | Science verdict | Hash changed |
| --- | --- | --- | --- | ---: | --- | --- | --- |
| `OC133-ECQ-001` | `validation/heldout/harvesters/systems_harvester.py` | `True` | `True` | `0` | `SCIENTIFIC_BLOCKED` | `BLOCKED_PENDING_GENUINE_EVIDENCE` | `False` |
| `OC133-ECQ-002` | `tools/oc133_physics_chemistry_acquisition_planner.py` | `True` | `True` | `0` | `SCIENTIFIC_BLOCKED` | `BLOCKED_PENDING_GENUINE_ACQUISITION` | `True` |
| `OC133-ECQ-003` | `tools/oc133_biology_ncbi_benchmark_factory.py` | `True` | `True` | `2` | `SCIENTIFIC_BLOCKED_LEGACY_NONZERO` | `BLOCKED_PENDING_GENUINE_BIOLOGY_REPLAY_EVIDENCE` | `False` |
| `OC133-ECQ-004` | `tools/oc133_systems_wdi_benchmark_factory.py` | `True` | `True` | `2` | `SCIENTIFIC_BLOCKED_LEGACY_NONZERO` | `BLOCKED_PENDING_GENUINE_WDI_BENCHMARK` | `False` |
| `OC133-ECQ-005` | `tools/oc133_grand_empirical_evidence_factory.py` | `True` | `True` | `2` | `SCIENTIFIC_BLOCKED_LEGACY_NONZERO` | `BLOCKED_PENDING_GENUINE_PER_DOMAIN_EVIDENCE` | `False` |
| `OC133-ECQ-006` | `validation/heldout/harvesters/physics_chemistry_harvester.py` | `True` | `True` | `0` | `SCIENTIFIC_BLOCKED` | `BLOCKED_PENDING_GENUINE_PHYSICS_CHEMISTRY_EVIDENCE` | `False` |
| `OC133-ECQ-007` | `validation/heldout/domain_evidence/biology_systems_evidence_executor.py` | `True` | `True` | `0` | `SCIENTIFIC_BLOCKED` | `BLOCKED_PENDING_GENUINE_BIOLOGY_SYSTEMS_EVIDENCE` | `False` |
| `OC133-ECQ-008` | `tools/oc133_biology_systems_acquisition_planner.py` | `True` | `True` | `0` | `SCIENTIFIC_BLOCKED` | `BLOCKED_PENDING_GENUINE_BIOLOGY_SYSTEMS_EVIDENCE` | `False` |
| `OC133-ECQ-009` | `validation/heldout/domain_evidence/mathematics_evidence_executor.py` | `True` | `True` | `0` | `SCIENTIFIC_BLOCKED` | `BLOCKED_PENDING_GENUINE_MATHEMATICS_EVIDENCE` | `False` |
| `OC133-ECQ-010` | `validation/heldout/domain_evidence/physics_chemistry_evidence_executor.py` | `True` | `True` | `0` | `SCIENTIFIC_BLOCKED` | `UNKNOWN` | `False` |

## Rejections

- `none`
