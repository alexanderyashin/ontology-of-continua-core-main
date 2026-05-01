from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from validation.grand_science import evidence_pack_factory as grand_factory
from validation.heldout.domain_evidence import mathematics_evidence_executor as executor


REPO_ROOT = Path(__file__).resolve().parents[1]


def write_json(root: Path, rel_path: str, payload: dict) -> None:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def requirements() -> dict:
    return {
        "schema_id": "OC133_GRAND_EMPIRICAL_DOMAIN_REQUIREMENTS_v1",
        "release_id": "oc_core_1_3_3",
        "capability_owner": "Research/EmpiricalScience",
        "minimum_per_domain_n": 20,
        "required_domains": ["mathematics"],
        "required_source_separation_modes": ["prospective", "target_blind"],
        "candidate_evidence_pack_roots": ["validation/heldout", "validation/grand_science"],
        "criteria": {
            "source_separation_required": True,
            "target_hidden_until_scoring_required": True,
            "pre_target_lock_required": True,
            "comparator_baseline_required": True,
            "uncertainty_interval_required": True,
            "residual_superiority_required": True,
            "negative_control_rejection_required": True,
            "falsifier_required": True,
            "grand_toe_support_allowed_must_be_explicit": True,
        },
    }


def small_proof_corpus() -> dict:
    return {
        "schema_id": "OC133_TEST_FINITE_MODEL_CHECKS",
        "release_id": "oc_core_1_3_3",
        "case_total": 4,
        "positive_case_total": 3,
        "machine_checked_subset_total": 2,
        "lean_theorem_ref_total": 2,
        "lean_source_ref": "formal/lean/OC133V12.lean",
        "current_lean_source_sha256": "abc123",
        "certificate_lean_source_sha256": "abc123",
        "rows": [
            {
                "case_id": "MATH-POS-1",
                "theorem_id": "T-MATH-1",
                "case_type": "theorem_case",
                "observed_verdict": "ACCEPT",
                "passed": True,
            },
            {
                "case_id": "MATH-POS-2",
                "theorem_id": "T-MATH-2",
                "case_type": "theorem_case",
                "observed_verdict": "ACCEPT",
                "passed": True,
            },
            {
                "case_id": "MATH-NEG-1",
                "theorem_id": "T-MATH-1",
                "case_type": "theorem_case",
                "observed_verdict": "REJECT",
                "passed": True,
            },
            {
                "case_id": "MATH-SUPPORT-1",
                "theorem_id": "T-MATH-SUPPORT",
                "case_type": "support_case",
                "observed_verdict": "ACCEPT",
                "passed": True,
            },
        ],
    }


class MathematicsEvidenceExecutorTests(unittest.TestCase):
    def test_current_repo_mathematics_output_is_blocked(self) -> None:
        self.assertEqual(executor.check_stored(REPO_ROOT), [])

        report, candidate, protocol = executor.build_execution_payload(REPO_ROOT)
        row = candidate.report_row

        self.assertEqual(report["verdict"], "BLOCKED_PENDING_GENUINE_MATHEMATICS_EVIDENCE")
        self.assertEqual(report["candidate_pack_total"], 1)
        self.assertEqual(report["valid_pack_total"], 0)
        self.assertEqual(protocol["blocked_domain_total"], 1)
        self.assertEqual(candidate.pack["n"], 1)
        self.assertLess(candidate.pack["n"], row["minimum_n"])
        self.assertFalse(candidate.pack["grand_toe_support_allowed"])
        self.assertFalse(row["grand_toe_support_allowed"])
        self.assertEqual(row["source_assessment"]["source_kind"], "finite_lean_proof_corpus")
        self.assertFalse(row["source_assessment"]["grand_empirical_source"])
        self.assertIn(
            "source is finite/Lean proof corpus, not empirical grand evidence",
            row["source_assessment"]["scope_statement"],
        )
        self.assertIn(
            "MATHEMATICS_CURRENT_SOURCE_IS_FINITE_LEAN_PROOF_CORPUS_NOT_EMPIRICAL_GRAND_EVIDENCE",
            row["blockers"],
        )
        self.assertIn("GENUINE_EVIDENCE_N_BELOW_MINIMUM::1/20", row["blockers"])
        self.assertTrue(all(test["passed"] for test in row["tamper_tests"]))

        failures = grand_factory.pack_failure_reasons(
            candidate.pack,
            executor.read_json(REPO_ROOT / executor.REQUIREMENTS_REL),
        )
        self.assertIn("N_BELOW_MINIMUM::20", failures)
        self.assertIn("GRAND_TOE_SUPPORT_NOT_ALLOWED", failures)

    def test_deterministic_hash_tamper_and_negative_control_checks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(root, executor.REQUIREMENTS_REL, requirements())
            write_json(root, executor.DEFAULT_SNAPSHOT_REF, small_proof_corpus())

            evidence = executor.load_mathematics_evidence(root)
            candidate = executor.build_domain_candidate(root)

            self.assertEqual(evidence.predicted_value, 2.0)
            self.assertEqual(evidence.observed_value, 2.0)
            self.assertEqual(evidence.comparator_prediction, 3.0)
            self.assertEqual(evidence.model_residual, 0.0)
            self.assertEqual(evidence.comparator_residual, 1.0)
            self.assertEqual(candidate.pack["n"], 1)
            self.assertFalse(candidate.pack["grand_toe_support_allowed"])
            self.assertIn("TARGET_BLIND_BINDING::TARGET_BLIND_MATHEMATICS_ROW_MISSING", candidate.report_row["blockers"])
            self.assertTrue(all(test["passed"] for test in candidate.report_row["tamper_tests"]))

            tampered = executor.tampered_machine_checked_payload(evidence)
            self.assertNotEqual(executor.sha256_object(tampered), evidence.snapshot_canonical_sha256)
            self.assertIn(
                "COMPARATOR_NOT_WORSE_THAN_MODEL",
                executor.validate_negative_control(
                    evidence.predicted_value,
                    evidence.observed_value,
                    evidence.predicted_value,
                ),
            )

    def test_write_outputs_materializes_only_mathematics_refs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(root, executor.REQUIREMENTS_REL, requirements())
            write_json(root, executor.DEFAULT_SNAPSHOT_REF, small_proof_corpus())

            report = executor.write_outputs(root)

            self.assertEqual(report["verdict"], "BLOCKED_PENDING_GENUINE_MATHEMATICS_EVIDENCE")
            for ref in report["candidate_pack_refs"]:
                self.assertTrue(ref.startswith(executor.OUTPUT_ROOT_REL))
                self.assertTrue((root / ref).is_file())
            self.assertTrue((root / executor.OUTPUT_ROOT_REL / "OC133_MATHEMATICS_EVIDENCE_PROTOCOL.json").is_file())
            self.assertTrue((root / executor.OUTPUT_ROOT_REL / "OC133_MATHEMATICS_EVIDENCE_EXECUTION_REPORT.json").is_file())
            self.assertTrue((root / executor.OUTPUT_ROOT_REL / "README.md").is_file())


if __name__ == "__main__":
    unittest.main()
