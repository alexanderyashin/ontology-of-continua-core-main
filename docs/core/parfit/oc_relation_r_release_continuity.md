# Relation R Release Continuity

Relation R is used here as a release-continuity check: an artifact should not be released as the same OC line unless it preserves causal lineage, evidence discipline, support classes, publication boundary, release contract and correction history.

Labels:

- `OC_CONTINUATION_STRONG`: sufficient continuity for no-send release review.
- `OC_CONTINUATION_WEAK`: release needs migration notes.
- `OC_FORK_REQUIRES_MIGRATION_MAP`: fork-like continuity; not same-line release without a map.
- `OC_IDENTITY_BREAK_DO_NOT_RELEASE_AS_OC`: blocker.
