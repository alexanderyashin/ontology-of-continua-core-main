# OC Core 1.3.3 Domain Evidence Executor Run

Verdict: `EXECUTORS_RAN_BLOCKERS_ALLOWED`
Executors: `3`
Command failures: `0`
Candidate packs reported: `5`
Valid packs reported: `1`
Blocked executor payloads: `2`

This runner only executes capability-owned evidence generators. Grand empirical closure is decided later by validation/grand_science/evidence_pack_factory.py; executor existence or zero return code is not scientific closure.

| Executor | Return code | Parsed JSON | Candidate packs | Valid packs | Verdict |
| --- | ---: | --- | ---: | ---: | --- |
| `validation/heldout/domain_evidence/biology_systems_evidence_executor.py` | `0` | `true` | `2` | `0` | `BLOCKED_PENDING_GENUINE_BIOLOGY_SYSTEMS_EVIDENCE` |
| `validation/heldout/domain_evidence/mathematics_evidence_executor.py` | `0` | `true` | `1` | `1` | `MATHEMATICS_FORMAL_SUPPORT_ROUTE_READY` |
| `validation/heldout/domain_evidence/physics_chemistry_evidence_executor.py` | `0` | `false` | `2` | `0` | `UNKNOWN` |
