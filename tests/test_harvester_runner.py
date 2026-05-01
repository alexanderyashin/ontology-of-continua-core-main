from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools import oc133_harvester_runner as runner


class HarvesterRunnerTests(unittest.TestCase):
    def test_empty_harvester_set_is_valid_runner_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / runner.HARVESTER_ROOT_REL).mkdir(parents=True)
            payload = runner.build_payload(root, write=True)
            self.assertEqual(payload["harvester_total"], 0)
            self.assertEqual(payload["command_failure_total"], 0)
            self.assertEqual(payload["verdict"], "HARVESTERS_RAN")

    def test_harvester_payload_is_counted_without_closure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            hroot = root / runner.HARVESTER_ROOT_REL
            hroot.mkdir(parents=True)
            harvester = hroot / "sample_harvester.py"
            harvester.write_text(
                "\n".join(
                    [
                        "from __future__ import annotations",
                        "import argparse, json",
                        "parser=argparse.ArgumentParser()",
                        "parser.add_argument('--write', action='store_true')",
                        "parser.add_argument('--offline', action='store_true')",
                        "parser.add_argument('--allow-blocked-exit-zero', action='store_true')",
                        "parser.parse_args()",
                        "print(json.dumps({'verdict':'BLOCKED','candidate_pack_total':2,'valid_pack_total':0,'blocker_total':4}))",
                    ]
                )
                + "\n",
                encoding="utf-8",
                newline="\n",
            )
            payload = runner.build_payload(root, write=True)
            self.assertEqual(payload["harvester_total"], 1)
            self.assertEqual(payload["candidate_pack_total"], 2)
            self.assertEqual(payload["valid_pack_total"], 0)
            self.assertEqual(payload["blocked_obligation_total"], 4)


if __name__ == "__main__":
    raise SystemExit(unittest.main())
