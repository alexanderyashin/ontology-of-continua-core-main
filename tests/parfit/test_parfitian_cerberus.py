from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import jsonschema
import yaml

from release_machine import complete
from release_machine.parfit import (
    audit_benchmark_corpus,
    audit_candidate_bundle,
    relation_r_score,
    release_gate_result,
)


ROOT = complete.repo_root()


class ParfitianCerberusTests(unittest.TestCase):
    def test_current_v132_report_validates_against_schema(self) -> None:
        result = release_gate_result(ROOT, "oc_core_1_3_2")
        self.assertEqual(result["state"], "PASS")
        report = json.loads((ROOT / "reports/parfit/oc_core_1_3_2.json").read_text(encoding="utf-8"))
        schema = json.loads((ROOT / "schemas/parfit/parfit_audit_report.schema.json").read_text(encoding="utf-8"))
        finding_schema = json.loads((ROOT / "schemas/parfit/parfit_audit_finding.schema.json").read_text(encoding="utf-8"))
        resolver = jsonschema.RefResolver.from_schema(schema, store={"parfit_audit_finding.schema.json": finding_schema})
        jsonschema.validate(report, schema, resolver=resolver)
        self.assertTrue(report["release_ready_no_send_allowed"])
        self.assertFalse(report["no_send_release_gate"]["publish_allowed"])

    def test_missing_required_manifest_fails_closed(self) -> None:
        bundle = {
            "candidate_id": "fixture_missing_manifests",
            "publish_allowed": False,
            "outbound_send_allowed": False,
            "owner_gate": {"approval_status": "pending", "publication_owner_unlock": False},
            "claims": [{"id": "C1", "support_class": "FORMALLY_PROVED", "evidence_refs": ["E1"], "burden_owner": "tester"}],
            "manifests": {},
        }
        report = audit_candidate_bundle(ROOT, bundle)
        self.assertEqual(report["status"], "FAIL_BLOCKING")
        self.assertGreaterEqual(report["summary"]["high_plus_total"], 1)
        self.assertIn("missing_required_manifest", {row["category"] for row in report["findings"]})

    def test_no_send_and_blocker_cannot_be_waived(self) -> None:
        bundle = {
            "candidate_id": "fixture_no_send_violation",
            "publish_allowed": True,
            "outbound_send_allowed": True,
            "owner_gate": {"approval_status": "pending", "publication_owner_unlock": False},
            "claims": [],
            "manifests": {},
        }
        report = audit_candidate_bundle(ROOT, bundle)
        blockers = [row for row in report["findings"] if row["severity"] == "blocker"]
        self.assertTrue(blockers)
        self.assertFalse(report["waiver_policy"]["blocker_waivable"])
        self.assertFalse(report["no_send_release_gate"]["outbound_send_allowed"])

    def test_relation_r_labels_identity_break(self) -> None:
        invariants = yaml.safe_load((ROOT / "configs/parfit/relation_r_invariants.yaml").read_text(encoding="utf-8"))
        score = relation_r_score({"relation_r_label": "OC_IDENTITY_BREAK_DO_NOT_RELEASE_AS_OC", "invariants": {}}, invariants)
        self.assertTrue(score.hard_break)
        self.assertEqual(score.label, "OC_IDENTITY_BREAK_DO_NOT_RELEASE_AS_OC")

    def test_benchmark_corpus_detects_twenty_seed_cases(self) -> None:
        corpus = yaml.safe_load((ROOT / "benchmarks/parfit/parfit_benchmark_corpus.yaml").read_text(encoding="utf-8"))
        report = audit_benchmark_corpus(corpus)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["case_total"], 20)
        self.assertEqual(report["pass_total"], 20)

    def test_cli_benchmark_returns_zero_and_missing_candidate_returns_three(self) -> None:
        bench = subprocess.run(
            [sys.executable, "scripts/oc_parfit_audit.py", "--benchmark", "benchmarks/parfit/parfit_benchmark_corpus.yaml", "--fail-on", "high"],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(bench.returncode, 0, bench.stderr)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "candidate.yaml"
            path.write_text(yaml.safe_dump({
                "candidate_id": "fixture_cli_missing",
                "publish_allowed": False,
                "outbound_send_allowed": False,
                "owner_gate": {"approval_status": "pending", "publication_owner_unlock": False},
                "claims": [{"id": "C1", "support_class": "FORMALLY_PROVED", "evidence_refs": ["E1"], "burden_owner": "tester"}],
                "manifests": {},
            }), encoding="utf-8")
            run = subprocess.run(
                [sys.executable, "scripts/oc_parfit_audit.py", "--candidate", str(path), "--fail-on", "high"],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            self.assertEqual(run.returncode, 3, run.stderr)

    def test_release_gate_blocks_forward_rc_until_bundle_complete(self) -> None:
        result = release_gate_result(ROOT, "oc_core_1_4_0_rc1")
        self.assertEqual(result["state"], "FAIL")
        self.assertGreaterEqual(result["details"]["high_plus_total"], 1)
        self.assertFalse(result["details"]["release_ready_no_send_allowed"])


if __name__ == "__main__":
    unittest.main()
