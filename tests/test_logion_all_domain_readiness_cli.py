from __future__ import annotations

import sys
import unittest
from unittest import mock

from tools import oc133_logion_all_domain_readiness as readiness


class LogionAllDomainReadinessCliTests(unittest.TestCase):
    def test_allow_blocked_exit_zero_keeps_scientific_blocker_nonfatal(self) -> None:
        blocked_audit = {
            "state": "OC_CORE_1_3_3_ALL_DOMAIN_SCIENTIFIC_READINESS_RUNNING",
            "final_readiness_state": "SCIENTIFIC_BLOCKERS_REMAIN",
            "blocker_total": 1,
            "blocker_ids": ["grand_toe_empirical_superiority"],
            "next_automatic_action": "OC133-PLATINUM-WO-002",
            "all_domain_ready_no_send": False,
        }
        execute_result = {
            "execution_state": "SCIENTIFIC_BLOCKERS_REMAIN",
            "after_final_readiness_state": "SCIENTIFIC_BLOCKERS_REMAIN",
        }
        with (
            mock.patch.object(
                sys,
                "argv",
                [
                    "oc133_logion_all_domain_readiness.py",
                    "--write",
                    "--execute-next",
                    "--allow-blocked-exit-zero",
                ],
            ),
            mock.patch.object(readiness, "execute_next", return_value=execute_result),
            mock.patch.object(readiness.oc133_platinum, "content_closure_audit", return_value={}),
            mock.patch.object(readiness.oc133_platinum, "all_domain_readiness_audit", return_value=blocked_audit),
            mock.patch.object(readiness, "write_all_domain_outputs", return_value={"scorecard": "x"}),
            mock.patch("builtins.print"),
        ):
            self.assertEqual(readiness.main(), 0)

    def test_blocked_exit_remains_nonzero_without_explicit_loop_flag(self) -> None:
        blocked_audit = {
            "state": "OC_CORE_1_3_3_ALL_DOMAIN_SCIENTIFIC_READINESS_RUNNING",
            "final_readiness_state": "SCIENTIFIC_BLOCKERS_REMAIN",
            "blocker_total": 1,
            "blocker_ids": ["grand_toe_empirical_superiority"],
            "next_automatic_action": "OC133-PLATINUM-WO-002",
            "all_domain_ready_no_send": False,
        }
        with (
            mock.patch.object(sys, "argv", ["oc133_logion_all_domain_readiness.py", "--write"]),
            mock.patch.object(readiness.oc133_platinum, "content_closure_audit", return_value={}),
            mock.patch.object(readiness.oc133_platinum, "all_domain_readiness_audit", return_value=blocked_audit),
            mock.patch.object(readiness, "write_all_domain_outputs", return_value={"scorecard": "x"}),
            mock.patch("builtins.print"),
        ):
            self.assertEqual(readiness.main(), 2)


if __name__ == "__main__":
    raise SystemExit(unittest.main())
