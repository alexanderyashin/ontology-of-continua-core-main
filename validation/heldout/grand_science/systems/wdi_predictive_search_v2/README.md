# Systems WDI Predictive Search V2

Verdict: `BLOCKED`
Grand TOE support allowed: `false`
Snapshot: `validation/heldout/grand_science/systems/harvested/systems_world_bank_wdi_official_endpoint_snapshot.json`
Rows: `57`
Minimum N: `20`

This factory replays a pinned WDI snapshot with a locked transparent model family. Model selection uses only prior same-series rows for each heldout target, then strict comparators, uncertainty, falsifiers, negative controls, schema checks, and tamper checks decide whether the candidate remains blocked.

## Open Blockers
- `DECLARED_BEFORE_SCORING_REQUIRED`
- `PRE_TARGET_LOCK_ID_REQUIRED`
- `PRE_TARGET_LOCK_TIMESTAMP_REQUIRED`
- `SOURCE_LOCK_PREDICATE_NOT_TRUE::declared_before_scoring`
- `SOURCE_LOCK_EXTERNAL_ID_REQUIRED`
- `SOURCE_LOCK_EXTERNAL_TIMESTAMP_REQUIRED`
- `GRAND_TOE_SUPPORT_NOT_ALLOWED`
- `STRICT_SOURCE_LOCK_PREDICATE_NOT_TRUE::declared_before_scoring`
- `STRICT_SOURCE_LOCK_EXTERNAL_ID_REQUIRED`
- `STRICT_SOURCE_LOCK_EXTERNAL_TIMESTAMP_REQUIRED`

## Exact Failure Rows
- `none`

## Next Work Orders
- `OC133-SYSTEMS-WDI-PREDICTIVE-SEARCH-V2-SOURCE-SEPARATION`: Attach complete pre-target lock metadata with target-blind or prospective source separation before any support claim.
- `OC133-SYSTEMS-WDI-PREDICTIVE-SEARCH-V2-STRICT-SCHEMA`: Repair schema/hash fields and rerun the factory; do not mark grand support by hand.

## Tamper Tests
- `systems-wdi-predictive-search-v2-target-mutation-changes-payload-hashes`: `True`
- `systems-wdi-predictive-search-v2-target-mutation-changes-row-hashes`: `True`
- `systems-wdi-predictive-search-v2-selection-target-leakage-control`: `True`
- `systems-wdi-predictive-search-v2-pack-hash-changes-on-pack-mutation`: `True`
