from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools import oc133_acquisition_planner_runner as runner


class AcquisitionPlannerRunnerTests(unittest.TestCase):
    def test_empty_planner_set_is_valid_runner_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "tools").mkdir()
            payload = runner.build_payload(root, write=True)
            self.assertEqual(payload["planner_total"], 0)
            self.assertEqual(payload["command_failure_total"], 0)
            self.assertEqual(payload["verdict"], "ACQUISITION_PLANNERS_RAN")
            self.assertTrue((root / runner.REPORT_JSON_REL).exists())

    def test_planner_payload_is_counted_without_evidence_closure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tools = root / "tools"
            tools.mkdir()
            planner = tools / "oc133_sample_acquisition_planner.py"
            planner.write_text(
                "\n".join(
                    [
                        "from __future__ import annotations",
                        "import argparse, json",
                        "parser = argparse.ArgumentParser()",
                        "parser.add_argument('--write', action='store_true')",
                        "parser.add_argument('--allow-blocked-exit-zero', action='store_true')",
                        "parser.parse_args()",
                        "print(json.dumps({'verdict': 'PROTOCOL_READY_BLOCKED', 'blocker_total': 3}))",
                    ]
                )
                + "\n",
                encoding="utf-8",
                newline="\n",
            )
            payload = runner.build_payload(root, write=True)
            self.assertEqual(payload["planner_total"], 1)
            self.assertEqual(payload["command_failure_total"], 0)
            self.assertEqual(payload["blocked_obligation_total"], 3)


if __name__ == "__main__":
    raise SystemExit(unittest.main())
