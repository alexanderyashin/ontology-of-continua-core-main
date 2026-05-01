from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import logion_project_controller as controller


def write_json(root: Path, rel_path: str, payload: dict[str, object]) -> None:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")


class LogionProjectControllerTests(unittest.TestCase):
    def test_controller_splits_release_and_background_science_budget(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(
                root,
                controller.ALL_DOMAIN_SCORECARD_REL,
                {
                    "final_readiness_state": controller.RELEASE_STATE,
                    "external_review_ready_no_send": True,
                    "all_domain_ready_no_send": False,
                    "full_science_program_state": controller.FULL_SCIENCE_STATE,
                    "blocker_total": 2,
                    "blocker_ids": ["grand_toe_claim_ledger_evidence", "modern_science_comparator_superiority"],
                },
            )
            write_json(
                root,
                controller.JOURNAL_INDEX_REL,
                {
                    "package_total": 8,
                    "recommended_package_total": 2,
                    "submission_allowed": False,
                    "journal_submissions_allowed": False,
                    "owner_approval_required": True,
                    "package_status_counts": {"OWNER_REVIEW_READY_NO_SEND": 8},
                },
            )
            write_json(root, controller.CERBERUS_SUMMARY_REL, {"critical_open_total": 0, "high_open_total": 0})

            cockpit = controller.build_cockpit(root)

            self.assertEqual(cockpit["portfolio"]["release_state"], controller.RELEASE_STATE)
            self.assertTrue(cockpit["portfolio"]["external_review_ready_no_send"])
            self.assertFalse(cockpit["portfolio"]["all_domain_ready_no_send"])
            self.assertEqual(cockpit["portfolio"]["full_science_program_state"], controller.FULL_SCIENCE_STATE)
            self.assertEqual(cockpit["budget_ledger"]["daily_external_llm_budget_tokens"], 2_000_000)
            self.assertTrue(cockpit["budget_ledger"]["host_compute_allowed"])
            self.assertEqual(cockpit["resource_policy"]["budget_override_action"], "REQUEST_EXTRA_LLM_BUDGET")
            release_stream = next(
                row for row in cockpit["portfolio"]["workstreams"] if row["workstream_id"] == "OC133_RELEASE_FOREGROUND"
            )
            science_stream = next(
                row for row in cockpit["portfolio"]["workstreams"] if row["workstream_id"] == "OC_FULL_SCIENCE_BACKGROUND"
            )
            self.assertTrue(release_stream["release_artifact_write_owner"])
            self.assertFalse(science_stream["release_artifact_write_owner"])

    def test_controller_requires_current_governed_dirty_ledger_for_git_roots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".git").mkdir()
            write_json(
                root,
                controller.DIRTY_LEDGER_REL,
                {
                    "governance_state": "GOVERNED_DIRTY_TREE",
                    "dirty_tree_fingerprint": "fixture-fingerprint",
                    "public_unclassified_total": 0,
                    "private_unknown_total": 0,
                    "public_dirty_total": 3,
                    "private_dirty_total": 1,
                    "public_class_counts": {"oc133_release_package": 1, "background_science": 2},
                    "private_class_counts": {"private_release_anchor_governance": 1},
                },
            )

            with patch.object(controller.dirty_governance, "current_fingerprint", return_value="fixture-fingerprint"):
                cockpit = controller.build_cockpit(root)
                self.assertTrue(cockpit["portfolio"]["dirty_tree_governed"])
                self.assertTrue(cockpit["portfolio"]["dirty_tree_ledger_current"])
                self.assertEqual(controller.check_outputs(root, cockpit), [
                    controller.PORTFOLIO_REL,
                    controller.RESOURCE_POLICY_REL,
                    controller.BUDGET_LEDGER_REL,
                    controller.WORKSTREAM_LOCKS_REL,
                    controller.MILESTONE_PLAN_REL,
                    controller.COCKPIT_JSON_REL,
                    controller.COCKPIT_MD_REL,
                ])

            with patch.object(controller.dirty_governance, "current_fingerprint", return_value="new-fingerprint"):
                cockpit = controller.build_cockpit(root)
                self.assertFalse(cockpit["portfolio"]["dirty_tree_governed"])
                self.assertFalse(cockpit["portfolio"]["dirty_tree_ledger_current"])
                self.assertIn(controller.DIRTY_LEDGER_REL, controller.check_outputs(root, cockpit))

    def test_write_then_check_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(
                root,
                controller.ALL_DOMAIN_SCORECARD_REL,
                {
                    "final_readiness_state": "SCIENTIFIC_BLOCKERS_REMAIN",
                    "external_review_ready_no_send": False,
                    "all_domain_ready_no_send": False,
                    "blocker_total": 1,
                    "blocker_ids": ["modern_science_comparator_superiority"],
                },
            )
            self.assertEqual(controller.main(["--root", str(root), "--write"]), 0)
            self.assertEqual(controller.main(["--root", str(root), "--check"]), 0)


if __name__ == "__main__":
    unittest.main()
