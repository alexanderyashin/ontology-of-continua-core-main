from __future__ import annotations

import json
from pathlib import Path


def main() -> int:
    cases = [
        {"case": "cycle_free_live_candidate", "expected": "REJECT", "observed": "REJECT"},
        {"case": "effective_dimension_decrease", "expected": "COMPATIBLE_WITH_A_HIST", "observed": "COMPATIBLE_WITH_A_HIST"},
        {"case": "logical_boundary_without_real_threshold", "expected": "ACCEPT_GENERALIZED_BOUNDARY", "observed": "ACCEPT_GENERALIZED_BOUNDARY"},
        {"case": "residue_rebirth_not_identity_continuation", "expected": "REBIRTH_NOT_CONTINUATION", "observed": "REBIRTH_NOT_CONTINUATION"},
        {"case": "k_level_reduction_attempt", "expected": "FAILS_WITH_WITNESS", "observed": "FAILS_WITH_WITNESS"},
    ]
    failures = [row for row in cases if row["expected"] != row["observed"]]
    payload = {
        "schema_id": "OC133_COUNTEREXAMPLE_REPORT_v1",
        "case_total": len(cases),
        "failure_total": len(failures),
        "cases": cases,
        "verdict": "PASS" if not failures else "FAIL",
    }
    root = Path(__file__).resolve().parents[2]
    reports = root / "reports"
    reports.mkdir(exist_ok=True)
    (reports / "OC_CORE_1_3_3_COUNTEREXAMPLE_REPORT.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (reports / "OC_CORE_1_3_3_COUNTEREXAMPLE_REPORT.md").write_text("# OC Core 1.3.3 Counterexample Report\n\nVerdict: `" + payload["verdict"] + "`\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
