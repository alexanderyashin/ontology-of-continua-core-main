from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from tools import oc133_domain_evidence_executor_runner as runner


class DomainEvidenceExecutorRunnerTests(unittest.TestCase):
    def test_no_executors_is_successful_empty_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload = runner.build_payload(root, write=True)
            self.assertEqual(payload["executor_total"], 0)
            self.assertEqual(payload["command_failure_total"], 0)
            self.assertEqual(payload["verdict"], "EXECUTORS_RAN_BLOCKERS_ALLOWED")
            self.assertTrue((root / runner.REPORT_JSON_REL).exists())

    def test_executor_payload_is_counted_without_closing_science(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            executor_dir = root / runner.EXECUTOR_ROOT_REL
            executor_dir.mkdir(parents=True)
            executor = executor_dir / "sample_evidence_executor.py"
            executor.write_text(
                "\n".join(
                    [
                        "from __future__ import annotations",
                        "import argparse, json",
                        "parser = argparse.ArgumentParser()",
                        "parser.add_argument('--write', action='store_true')",
                        "parser.add_argument('--allow-blocked-exit-zero', action='store_true')",
                        "parser.parse_args()",
                        "print(json.dumps({'candidate_pack_total': 2, 'valid_pack_total': 0, 'verdict': 'BLOCKED_PENDING_GENUINE_EVIDENCE_PACK'}))",
                    ]
                )
                + "\n",
                encoding="utf-8",
                newline="\n",
            )
            payload = runner.build_payload(root, write=True)
            self.assertEqual(payload["executor_total"], 1)
            self.assertEqual(payload["candidate_pack_total"], 2)
            self.assertEqual(payload["valid_pack_total"], 0)
            self.assertEqual(payload["blocked_executor_payload_total"], 1)
            self.assertEqual(payload["command_failure_total"], 0)
            report = json.loads((root / runner.REPORT_JSON_REL).read_text(encoding="utf-8"))
            self.assertEqual(report["results"][0]["returncode"], 0)


if __name__ == "__main__":
    raise SystemExit(unittest.main())
