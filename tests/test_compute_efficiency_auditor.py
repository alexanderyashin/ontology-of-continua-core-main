from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools import oc133_compute_efficiency_auditor as auditor


def write_json(root: Path, rel_path: str, payload: dict[str, object]) -> None:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")


def planning_row(work_order_id: str) -> dict[str, object]:
    return {
        "work_order_id": work_order_id,
        "owner_capability": "Research/Planning",
        "executor": {
            "mode": "planning_queue_validation",
            "command": "python benchmarks/modern_science/coverage_lane_dispatcher.py --check",
            "closure_policy": "Planning/check execution is not scientific closure.",
        },
    }


def capability_row(work_order_id: str) -> dict[str, object]:
    return {
        "work_order_id": work_order_id,
        "owner_capability": "Research/FormalScience",
        "executor": {
            "mode": "capability_profile",
            "command": "python tools/oc133_capability_repair_executor.py --profile v12_grand_formal_science_research_program",
        },
    }


class ComputeEfficiencyAuditorTests(unittest.TestCase):
    def test_planning_only_front_of_queue_routes_real_executor_before_spending(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(
                root,
                auditor.WORK_ORDERS_REL,
                {"rows": [planning_row("WO-PLAN-001"), capability_row("WO-CAP-001")]},
            )
            write_json(
                root,
                auditor.SCORECARD_REL,
                {
                    "final_readiness_state": "SCIENTIFIC_BLOCKERS_REMAIN",
                    "blocker_total": 2,
                    "blocker_ids": ["grand_toe_claim_ledger_evidence", "modern_science_comparator_superiority"],
                },
            )
            write_json(
                root,
                auditor.EXECUTION_LEDGER_REL,
                {
                    "rows": [
                        {"work_order_id": "WO-OLD", "execution_state": "FAIL"},
                        {"work_order_id": "WO-OLD", "execution_state": "FAIL"},
                        {"work_order_id": "WO-OLD", "execution_state": "FAIL"},
                    ]
                },
            )
            write_json(root, auditor.COVERAGE_QUEUE_REL, {"queue_size": 3, "executable_lane_total": 1})

            audit = auditor.build_audit(root)

            self.assertEqual(audit["findings"]["known_blocker_total"], 2)
            self.assertEqual(audit["findings"]["planning_only_top_work_order_total"], 1)
            self.assertEqual(audit["findings"]["capability_profile_top_work_order_total"], 1)
            self.assertEqual(audit["next_efficient_action"]["action_id"], "ROUTE_REAL_EXECUTOR_FOR_WO-PLAN-001")
            self.assertIn("FULL_CERBERUS_SUITE_BEFORE_BLOCKER_DELTA", audit["next_efficient_action"]["blocked_actions"])
            self.assertEqual(audit["findings"]["execution_repetition"]["repeated_work_order_total"], 1)

    def test_write_then_check_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(root, auditor.WORK_ORDERS_REL, {"rows": [capability_row("WO-CAP-001")]})
            write_json(root, auditor.SCORECARD_REL, {"final_readiness_state": "SCIENTIFIC_BLOCKERS_REMAIN"})
            write_json(root, auditor.EXECUTION_LEDGER_REL, {"rows": []})
            write_json(root, auditor.COVERAGE_QUEUE_REL, {"queue_size": 1})

            self.assertEqual(auditor.main(["--root", str(root), "--write"]), 0)
            self.assertEqual(auditor.main(["--root", str(root), "--check"]), 0)


if __name__ == "__main__":
    unittest.main()
