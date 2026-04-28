# OC Core 1.3.3 Hostile Hardening Report

Pass: `7`
Fail: `0`
Blocked: `0`
Red-team concreteness: `PASS`

| Audit | State | Key evidence |
| --- | --- | --- |
| `llm_adversarial_review` | `PASS` | role_total=9, critical_open_total=0, high_open_total=0, parse_failure_total=0 |
| `proof_depth` | `PASS` | theorem_total=8, proof_sheet_total=8, failure_total=0, finite_model_case_total=9, finite_model_failure_total=0 |
| `empirical_numeric_prediction` | `PASS` | lane_total=5, row_total=5, incomplete_total=0, promoted_without_numeric_total=0, fake_pass_total=0, unsupported_promoted_total=0, blocked_for_promotion_total=1 |
| `novelty_competitor` | `PASS` | row_total=10, complete_row_total=10, unsupported_uniqueness_total=0 |
| `phenomenon_coverage` | `PASS` | row_total=14, complete_row_total=14, unsupported_closed_total=0 |
| `hostile_reader_didactics` | `PASS` |  |
| `absolute_toe_overclaim` | `PASS` | hit_total=0, scanned_file_total=18 |
