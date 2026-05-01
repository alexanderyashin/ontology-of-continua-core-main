from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools import oc133_biology_math_target_definition as planner


REPO_ROOT = Path(__file__).resolve().parents[1]


def write_json(root: Path, rel_path: str, payload: dict) -> None:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8", newline="\n")


def biology_snapshot(retmax: int = 2) -> dict:
    idlist = [str(1000 + idx) for idx in range(retmax)]
    return {
        "header": {
            "type": "esearch",
            "version": "0.3",
        },
        "esearchresult": {
            "count": "8",
            "retmax": str(retmax),
            "retstart": "0",
            "idlist": idlist,
        },
    }


def finite_checks() -> dict:
    return {
        "schema_id": "OC133_TEST_FINITE_MODEL_CHECKS",
        "release_id": "oc_core_1_3_3",
        "case_total": 4,
        "positive_case_total": 3,
        "machine_checked_subset_total": 2,
        "lean_theorem_ref_total": 2,
        "lean_build_returncode": 0,
        "live_lean_build_returncode": 0,
        "lean_source_ref": "formal/lean/OC133V12.lean",
        "current_lean_source_sha256": "abc123",
        "certificate_lean_source_sha256": "abc123",
        "rows": [
            {
                "theorem_id": "T-MATH-1",
                "case_type": "theorem_case",
                "observed_verdict": "ACCEPT",
                "passed": True,
            },
            {
                "theorem_id": "T-MATH-2",
                "case_type": "theorem_case",
                "observed_verdict": "ACCEPT",
                "passed": True,
            },
            {
                "theorem_id": "T-MATH-1",
                "case_type": "theorem_case",
                "observed_verdict": "REJECT",
                "passed": True,
            },
            {
                "theorem_id": "T-SUPPORT",
                "case_type": "support_case",
                "observed_verdict": "ACCEPT",
                "passed": True,
            },
        ],
    }


def requirements(minimum_n: int = 20) -> dict:
    return {
        "schema_id": "OC133_GRAND_EMPIRICAL_DOMAIN_REQUIREMENTS_v1",
        "release_id": "oc_core_1_3_3",
        "capability_owner": "Research/EmpiricalScience",
        "minimum_per_domain_n": minimum_n,
    }


class BiologyMathTargetDefinitionTests(unittest.TestCase):
    def test_current_repo_targets_are_blocked_without_support(self) -> None:
        payload = planner.build_payload(REPO_ROOT)

        self.assertEqual(payload["verdict"], "BLOCKED_TARGET_DEFINITIONS_ONLY_NO_SUPPORT_ALLOWED")
        self.assertFalse(payload["support_allowed"])
        self.assertTrue(payload["no_send"])
        self.assertEqual(payload["target_definition_total"], 2)
        self.assertEqual(payload["minimum_n"], 20)

        targets = {row["domain"]: row for row in payload["target_definitions"]}
        biology = targets["biology"]
        math = targets["mathematics"]

        self.assertEqual(biology["target_definition"]["predicted_value"], 20.0)
        self.assertEqual(biology["target_definition"]["observed_value"], 20.0)
        self.assertEqual(biology["target_definition"]["comparator_prediction"], 44008.0)
        self.assertIn("API pagination is not grand evidence", biology["source_assessment"]["scope_statement"])
        self.assertFalse(biology["support_allowed"])

        self.assertEqual(math["finite_checks"]["machine_checked_subset_total"], 10)
        self.assertEqual(math["finite_checks"]["unique_accepted_theorem_total"], 10)
        self.assertEqual(math["target_definition"]["comparator_prediction"], 21.0)
        self.assertTrue(math["lean_certificate"]["present"])
        self.assertTrue(math["lean_certificate"]["source_sha256_matches_finite_checks"])
        self.assertIn("proof corpus is not grand evidence", math["source_assessment"]["scope_statement"])
        self.assertFalse(math["support_allowed"])

        blocker_text = " ".join(payload["open_blocker_ids"])
        self.assertIn("API pagination is not grand evidence", blocker_text)
        self.assertIn("proof corpus is not grand evidence", blocker_text)
        self.assertIn("N<20", blocker_text)
        self.assertIn("no support allowed", blocker_text)

    def test_deterministic_write_and_check_with_optional_missing_lean_certificate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(root, planner.REQUIREMENTS_REL, requirements())
            write_json(root, planner.BIOLOGY_SNAPSHOT_REL, biology_snapshot())
            write_json(root, planner.FINITE_CHECKS_REL, finite_checks())

            first = planner.write_outputs(root)
            second = planner.build_payload(root)

            self.assertEqual(first, second)
            self.assertEqual(planner.check_stored(root), [])
            self.assertTrue((root / planner.TARGETS_REL).is_file())
            self.assertTrue((root / planner.BLOCKERS_REL).is_file())
            self.assertTrue((root / planner.README_REL).is_file())

            targets = {row["domain"]: row for row in first["target_definitions"]}
            self.assertEqual(targets["biology"]["target_definition"]["predicted_value"], 2.0)
            self.assertEqual(targets["biology"]["target_definition"]["observed_value"], 2.0)
            self.assertFalse(targets["mathematics"]["lean_certificate"]["present"])
            self.assertEqual(targets["mathematics"]["finite_checks"]["unique_accepted_theorem_total"], 2)
            self.assertEqual(targets["mathematics"]["target_definition"]["observed_value"], 2.0)

            blockers = planner.read_json(root / planner.BLOCKERS_REL)
            self.assertFalse(blockers["support_allowed"])
            self.assertEqual(blockers["open_blocker_total"], 6)
            self.assertIn("NO_SUPPORT_ALLOWED::biology::no support allowed", blockers["open_blocker_ids"])
            self.assertIn("NO_SUPPORT_ALLOWED::mathematics::no support allowed", blockers["open_blocker_ids"])

    def test_lean_certificate_is_bound_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(root, planner.REQUIREMENTS_REL, requirements())
            write_json(root, planner.BIOLOGY_SNAPSHOT_REL, biology_snapshot())
            write_json(root, planner.FINITE_CHECKS_REL, finite_checks())
            write_json(
                root,
                planner.LEAN_CERTIFICATE_REL,
                {
                    "schema_id": "OC133_LEAN_BUILD_CERTIFICATE_v12",
                    "release_id": "oc_core_1_3_3",
                    "execution_status": "EXECUTED_ISOLATED_CLEAN_BUILD",
                    "returncode": 0,
                    "clean_returncode": 0,
                    "theorem_ref_present_total": 2,
                    "theorem_ref_missing_total": 0,
                    "lean_source_ref": "formal/lean/OC133V12.lean",
                    "lean_source_sha256": "abc123",
                },
            )

            payload = planner.build_payload(root)
            math = {row["domain"]: row for row in payload["target_definitions"]}["mathematics"]
            cert = math["lean_certificate"]

            self.assertTrue(cert["present"])
            self.assertEqual(cert["returncode"], 0)
            self.assertEqual(cert["theorem_ref_missing_total"], 0)
            self.assertTrue(cert["source_sha256_matches_finite_checks"])
            self.assertFalse(math["support_allowed"])


if __name__ == "__main__":
    unittest.main()
