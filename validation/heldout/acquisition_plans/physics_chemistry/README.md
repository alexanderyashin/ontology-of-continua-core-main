# Physics + Chemistry Acquisition Plan

Verdict: `BLOCKED_PENDING_GENUINE_ACQUISITION`
Grand TOE support allowed: `false`
Open blocker total: `15`
Blocked domains: `2/2`

| Domain | Status | N | Missing | Blockers |
| --- | --- | ---: | ---: | --- |
| `physics` | `BLOCKED_PENDING_GENUINE_ACQUISITION` | `0` | `20` | 7 |
| `chemistry` | `BLOCKED_PENDING_GENUINE_ACQUISITION` | `0` | `20` | 8 |

No support is emitted by this planner. Existing bounded target-blind reconstructions and replay QA rows are treated as blockers. Only a future preregistered candidate pack can drive grand TOE support.

Open blockers:
- `SOURCE_ENDPOINT_CHECK_SKIPPED::physics::physics_nist_constants`
- `TARGET_BLIND::physics::OC133-TARGETBLIND-PHYSICS-001::CURRENT_TARGET_BLIND_RECONSTRUCTION_BOUNDARY`
- `TARGET_BLIND::physics::OC133-TARGETBLIND-PHYSICS-001::TARGET_BLIND_CURRENT_BASELINE_BLOCKER`
- `NUMERIC_REPLAY_QUARANTINED_NOT_DOMAIN_EVIDENCE::physics::1`
- `N_BELOW_MINIMUM::physics::0/20`
- `NO_NEGATIVE_CONTROLS::physics`
- `NO_FALSIFIERS::physics`
- `SOURCE_ENDPOINT_CHECK_SKIPPED::chemistry::chemistry_pubchem_water`
- `SOURCE_ENDPOINT_CHECK_SKIPPED::chemistry::chemistry_nist_webbook_water`
- `TARGET_BLIND::chemistry::OC133-TARGETBLIND-CHEMISTRY-001::CURRENT_TARGET_BLIND_RECONSTRUCTION_BOUNDARY`
- `TARGET_BLIND::chemistry::OC133-TARGETBLIND-CHEMISTRY-001::TARGET_BLIND_CURRENT_BASELINE_BLOCKER`
- `NUMERIC_REPLAY_QUARANTINED_NOT_DOMAIN_EVIDENCE::chemistry::2`
- `N_BELOW_MINIMUM::chemistry::0/20`
- `NO_NEGATIVE_CONTROLS::chemistry`
- `NO_FALSIFIERS::chemistry`
