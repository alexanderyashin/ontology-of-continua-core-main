# OC Core 1.3.3 Harvester Run

Verdict: `HARVESTERS_RAN`
Harvesters: `2`
Command failures: `0`
Candidate packs: `1`
Valid packs reported: `0`
Blocked obligations: `44`

Harvesters may create candidate evidence packs, but grand empirical closure is decided only by validation/grand_science/evidence_pack_factory.py after registry/source-separation/schema checks.

| Harvester | Return code | Parsed JSON | Candidate packs | Valid packs | Verdict |
| --- | ---: | --- | ---: | ---: | --- |
| `validation/heldout/harvesters/physics_chemistry_harvester.py` | `0` | `true` | `0` | `0` | `BLOCKED_PENDING_GENUINE_PHYSICS_CHEMISTRY_EVIDENCE` |
| `validation/heldout/harvesters/systems_harvester.py` | `0` | `true` | `1` | `0` | `BLOCKED_PENDING_GENUINE_EVIDENCE` |
