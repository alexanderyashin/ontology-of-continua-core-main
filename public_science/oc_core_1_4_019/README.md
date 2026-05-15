# OC Core 1.4 019 Proof-Only Public Projection

This directory is a public-safe local projection of the OC Core 1.4 019 proof-only burn-down state.

It is not a public release package and not owner approval for publication. The 019 release remains fail-closed because the frozen scope still contains non-terminal proof rows.

Current public-safe summary:
- problem_total: `254`
- terminal_total: `7`
- non_terminal_total: `247`
- status_counts: `{"BLOCKED_WITH_PROOF": 233, "CALIBRATION_REPLAYED": 1, "DISPROVED_OR_REFUTED": 2, "PARTIAL": 14, "PROVED": 4}`

Files:
- `PROOF_ONLY_PUBLIC_PROJECTION_019.json` - public-safe scope and per-problem proof-only state.
- `PUBLIC_TERMINALIZATION_LEDGER_019.json` - terminalization outcomes without private paths or raw machinery.
- `PUBLIC_STRICT_RESULT_BRIDGE_AUDIT_019.json` - strict-result bridge summary and policy.
- `PUBLIC_PROJECTION_MANIFEST_019.json` - checksums for this projection.

Boundary: Clay/Millennium rows are not claimed solved. Counted strict closures are bounded results under their recorded scope, not prize claims.

