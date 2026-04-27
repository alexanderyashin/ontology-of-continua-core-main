# Parfitian Release Policy

The release machine treats Parfitian Cerberus as gate `G27/parfitian_cerberus`.

The gate runs after claim/evidence, simulation, Cerberus, LRGEF freshness, PDF binding and no-send supply-chain checks, and before the release contract is treated as sealed.

## Hard Rules

- Missing required Parfitian manifests fail closed in release-critical mode.
- Unknown support class, unknown burden owner or evidence-free release claim is High severity.
- Relation R identity break is a blocker.
- Self-effacing transparency is a blocker.
- No-send violations are blockers.
- High+ findings block `RELEASE_READY_NO_SEND`.

## Waivers

High and critical findings may be routed to owner review, but the audit itself never flips publication permissions. Blocker findings and no-send invariants are not waivable here.
