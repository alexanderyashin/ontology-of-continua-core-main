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


def theorem_case(case_id: str, idx: int, expected: str) -> dict:
    return {
        "case_id": case_id,
        "theorem_id": f"T-MATH-{idx // 2}",
        "case_type": "theorem_case",
        "expected_verdict": expected,
        "lean_ref": f"formal/lean/OC133V12.lean::test_theorem_{idx // 2}",
        "model": {
            "finite_case_index": idx,
            "predicate_value": expected == "ACCEPT",
            "dimension": idx % 5,
        },
        "negative_control_id": f"MATH-CASE-{idx + 1:03d}" if expected == "ACCEPT" else "",
    }


def corpus_rows(n: int) -> list[dict]:
    return [theorem_case(f"MATH-CASE-{idx:03d}", idx, "ACCEPT" if idx % 2 == 0 else "REJECT") for idx in range(n)]


def materialize_corpus(
    root: Path,
    n: int = 20,
    *,
    target_leak: bool = False,
    tamper: str | None = None,
    missing_registry: bool = False,
    missing_proof_sheet: bool = False,
    missing_lean_ref: bool = False,
) -> None:
    input_rows = corpus_rows(n)
    if target_leak:
        input_rows[0]["observed_verdict"] = input_rows[0]["expected_verdict"]
    input_payload = {
        "schema_id": "OC133_TEST_FINITE_MODEL_INPUTS",
        "release_id": "oc_core_1_3_3",
        "version": "1.3.3",
        "observed_field_total": 1 if target_leak else 0,
        "flag_oracle_key_total": 0,
        "rows": input_rows,
    }
    write_json(root, "proofs/finite_model_checks/OC133_FINITE_MODEL_INPUTS.json", input_payload)
    input_sha = executor.sha256_file(root / "proofs/finite_model_checks/OC133_FINITE_MODEL_INPUTS.json")

    output_rows = []
    for row in input_rows:
        output = {
            "case_id": row["case_id"],
            "theorem_id": row["theorem_id"],
            "case_type": row["case_type"],
            "expected_verdict": row["expected_verdict"],
            "model": dict(row["model"]),
            "negative_control_id": row["negative_control_id"],
            "lean_theorem_ref": row["lean_ref"],
            "observed_verdict": row["expected_verdict"],
            "passed": True,
        }
        output_rows.append(output)
    if tamper == "observed_verdict":
        output_rows[0]["observed_verdict"] = "REJECT" if output_rows[0]["observed_verdict"] == "ACCEPT" else "ACCEPT"
    if tamper == "model":
        output_rows[0]["model"]["finite_case_index"] = 999

    snapshot = {
        "schema_id": "OC133_TEST_FINITE_MODEL_CHECKS",
        "release_id": "oc_core_1_3_3",
        "version": "1.3.3",
        "input_ref": "proofs/finite_model_checks/OC133_FINITE_MODEL_INPUTS.json",
        "input_sha256": input_sha,
        "lean_build_returncode": 0,
        "live_lean_build_returncode": 0,
        "cert_lean_sha256_matches_current_source": True,
        "failure_total": 0,
        "lean_theorem_ref_total": n,
        "lean_theorem_refs": sorted({row["lean_theorem_ref"] for row in output_rows}),
        "lean_source_ref": "formal/lean/OC133V12.lean",
        "current_lean_source_sha256": "abc123",
        "certificate_lean_source_sha256": "abc123",
        "case_total": n,
        "positive_case_total": sum(1 for row in output_rows if row["expected_verdict"] == "ACCEPT"),
        "machine_checked_subset_total": n,
        "rows": output_rows,
    }
    write_json(root, executor.DEFAULT_SNAPSHOT_REF, snapshot)
    write_json(root, executor.REQUIREMENTS_REL, requirements())
    if not missing_registry:
        theorem_rows = []
        for theorem_id in sorted({row["theorem_id"] for row in input_rows}):
            proof_sheet_ref = f"proofs/proof_sheets/{theorem_id}.md"
            theorem_idx = theorem_id.rsplit("-", 1)[-1]
            lean_ref = "" if missing_lean_ref else f"formal/lean/OC133V12.lean::test_theorem_{theorem_idx}"
            theorem_rows.append(
                {
                    "theorem_id": theorem_id,
                    "proof_sheet_ref": proof_sheet_ref,
                    "lean_ref": lean_ref,
                    "public_claim_boundary": f"{theorem_id} supports only the fixture formal claim boundary.",
                }
            )
            if not missing_proof_sheet:
                (root / proof_sheet_ref).parent.mkdir(parents=True, exist_ok=True)
                (root / proof_sheet_ref).write_text(f"# {theorem_id}\n\nFixture proof sheet.\n", encoding="utf-8", newline="\n")
        write_json(
            root,
            executor.THEOREM_REGISTRY_REL,
            {
                "schema_id": "OC133_TEST_THEOREM_REGISTRY",
                "release_id": "oc_core_1_3_3",
                "rows": theorem_rows,
            },
        )


class MathematicsEvidenceExecutorTests(unittest.TestCase):
    def test_current_repo_mathematics_output_is_row_level_evidence_pack(self) -> None:
        self.assertEqual(executor.check_stored(REPO_ROOT), [])

        report, candidate, protocol = executor.build_execution_payload(REPO_ROOT)
        row = candidate.report_row

        self.assertEqual(report["verdict"], "MATHEMATICS_FORMAL_SUPPORT_ROUTE_READY")
        self.assertEqual(report["valid_pack_total"], 1)
        self.assertEqual(protocol["blocked_domain_total"], 0)
        self.assertEqual(candidate.pack["schema_id"], executor.FORMAL_EVIDENCE_SCHEMA_ID)
        self.assertEqual(candidate.pack["support_route"], "formal")
        self.assertGreaterEqual(candidate.pack["n"], 20)
        self.assertEqual(candidate.pack["n"], row["valid_case_total"])
        self.assertEqual(row["source_assessment"]["source_kind"], "executable_finite_model_proof_corpus")
        self.assertFalse(row["source_assessment"]["grand_empirical_source"])
        self.assertFalse(candidate.pack["empirical_support_allowed"])
        self.assertTrue(candidate.pack["formal_support_allowed"])
        self.assertEqual(candidate.pack["formal_support_verdict"], "FORMAL_SUPPORT_ACCEPTED")
        self.assertTrue(candidate.pack["source_separation"]["pre_target_lock"])
        self.assertTrue(candidate.pack["source_separation"]["target_hidden_until_scoring"])
        self.assertFalse(candidate.pack["grand_toe_support_allowed"])
        self.assertGreaterEqual(len(candidate.pack["theorem_ids"]), 10)
        self.assertTrue(candidate.pack["proof_sheet_refs"])
        self.assertTrue(candidate.pack["lean_refs"])
        self.assertTrue(candidate.pack["finite_case_ids"])
        self.assertTrue(all(obligation["formal_obligation_passed"] for obligation in candidate.pack["formal_obligations"]))
        self.assertTrue(all(test["passed"] for test in row["tamper_tests"]))
        self.assertEqual(row["blockers"], [])

        failures = grand_factory.pack_failure_reasons(
            candidate.pack,
            executor.read_json(REPO_ROOT / executor.REQUIREMENTS_REL),
        )
        self.assertIn("FORMAL_SUPPORT_ROUTE_NOT_EMPIRICAL_GRAND_EVIDENCE", failures)
        self.assertFalse(row["valid_under_grand_gate"])
        self.assertTrue(row["empirical_gate_rejects_formal_pack"])

    def test_tampered_executed_verdict_and_model_rows_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            materialize_corpus(root, n=20, tamper="observed_verdict")
            candidate = executor.build_domain_candidate(root)
            blockers = " ".join(candidate.report_row["blockers"])
            self.assertIn("PASSED_FLAG_NOT_DERIVED_FROM_EXPECTED_OBSERVED", blockers)
            self.assertFalse(candidate.report_row["valid_under_executor"])
            self.assertFalse(candidate.pack["formal_support_allowed"])

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            materialize_corpus(root, n=20, tamper="model")
            candidate = executor.build_domain_candidate(root)
            blockers = " ".join(candidate.report_row["blockers"])
            self.assertIn("INPUT_OUTPUT_MODEL_HASH_MISMATCH", blockers)
            self.assertFalse(candidate.report_row["valid_under_executor"])
            self.assertFalse(candidate.pack["formal_support_allowed"])

    def test_target_leakage_in_input_blocks_pack(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            materialize_corpus(root, n=20, target_leak=True)

            candidate = executor.build_domain_candidate(root)
            blockers = " ".join(candidate.report_row["blockers"])

            self.assertFalse(candidate.pack["source_separation"]["target_hidden_until_scoring"])
            self.assertIn("TARGET_LEAKAGE_IN_INPUT_ROW::MATH-CASE-000", blockers)
            self.assertIn("TARGET_LEAKAGE_FAILED", blockers)
            self.assertFalse(candidate.report_row["valid_under_executor"])
            self.assertFalse(candidate.pack["formal_support_allowed"])

    def test_n_below_twenty_blocks_pack_and_grand_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            materialize_corpus(root, n=19)

            report, candidate, _protocol = executor.build_execution_payload(root)
            failures = grand_factory.pack_failure_reasons(candidate.pack, requirements())

            self.assertEqual(candidate.pack["n"], 19)
            self.assertFalse(candidate.pack["formal_support_allowed"])
            self.assertIn("FORMAL_FINITE_CASE_N_BELOW_MINIMUM::19/20", candidate.report_row["blockers"])
            self.assertIn("N_BELOW_MINIMUM::20", failures)
            self.assertIn("FORMAL_SUPPORT_ROUTE_NOT_EMPIRICAL_GRAND_EVIDENCE", failures)
            self.assertEqual(report["valid_pack_total"], 0)
            self.assertEqual(report["blocked_domain_total"], 1)

    def test_formal_route_requires_exact_theorem_proof_lean_and_finite_refs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            materialize_corpus(root, n=20)
            candidate = executor.build_domain_candidate(root)

            self.assertTrue(candidate.pack["formal_support_allowed"])
            self.assertTrue(all(row["proof_sheet_ref_exists"] for row in candidate.pack["formal_obligations"]))
            self.assertTrue(all(row["finite_positive_case_ids"] for row in candidate.pack["formal_obligations"]))
            self.assertTrue(all(row["finite_negative_case_ids"] for row in candidate.pack["formal_obligations"]))

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            materialize_corpus(root, n=20, missing_proof_sheet=True)
            candidate = executor.build_domain_candidate(root)

            self.assertFalse(candidate.pack["formal_support_allowed"])
            self.assertTrue(any("FORMAL_PROOF_SHEET_REF_NOT_FOUND" in blocker for blocker in candidate.report_row["blockers"]))

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            materialize_corpus(root, n=20, missing_lean_ref=True)
            candidate = executor.build_domain_candidate(root)

            self.assertFalse(candidate.pack["formal_support_allowed"])
            self.assertTrue(any("FORMAL_PRIMARY_LEAN_REF_MISSING" in blocker for blocker in candidate.report_row["blockers"]))

    def test_write_outputs_materializes_only_mathematics_refs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            materialize_corpus(root, n=20)

            report = executor.write_outputs(root)

            self.assertEqual(report["verdict"], "MATHEMATICS_FORMAL_SUPPORT_ROUTE_READY")
            for ref in report["candidate_pack_refs"]:
                self.assertTrue(ref.startswith(executor.OUTPUT_ROOT_REL))
                self.assertTrue((root / ref).is_file())
            self.assertTrue((root / executor.OUTPUT_ROOT_REL / "OC133_MATHEMATICS_EVIDENCE_PROTOCOL.json").is_file())
            self.assertTrue((root / executor.OUTPUT_ROOT_REL / "OC133_MATHEMATICS_EVIDENCE_EXECUTION_REPORT.json").is_file())
            self.assertTrue((root / executor.OUTPUT_ROOT_REL / "README.md").is_file())


if __name__ == "__main__":
    unittest.main()
