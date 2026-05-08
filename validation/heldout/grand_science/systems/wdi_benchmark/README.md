# Systems WDI Benchmark Factory

Verdict: `BLOCKED_PENDING_GENUINE_WDI_BENCHMARK`
Grand TOE support allowed: `False`
Rows: `1`
Minimum N: `20`
Selected formula: `linear_two_lag`

This artifact is a deterministic WDI benchmark candidate. It blocks support unless the payload declares an explicit heldout split, formula selection uses training years only, heldout residuals beat carry-forward controls, N is sufficient, and tamper controls pass.

## Open blockers
- `N_BELOW_MINIMUM::1/20`
- `SOURCE_SEPARATION_MODE_NOT_ALLOWED::snapshot_replay`
- `TARGET_SEPARATION_NOT_EXPLICIT_OR_NOT_LOCKED`
- `SPLIT_POLICY_NOT_EXPLICIT_LAST_YEAR_HELDOUT`
- `PRE_TARGET_LOCK_REQUIRED`
- `TARGET_HIDDEN_UNTIL_SCORING_REQUIRED`
- `SOURCE_SEPARATION_MODE_NOT_ALLOWED`
- `N_BELOW_MINIMUM::20`
- `GRAND_TOE_SUPPORT_NOT_ALLOWED`

## Tamper tests
- `systems-wdi-payload-hash-changes-on-heldout-mutation`: `True`
- `systems-wdi-row-hashes-change-on-heldout-mutation`: `True`
- `systems-wdi-formula-selection-target-leakage-control`: `True`
- `systems-wdi-carry-forward-negative-controls`: `True`
