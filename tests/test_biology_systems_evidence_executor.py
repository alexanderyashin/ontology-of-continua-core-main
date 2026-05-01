from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from validation.heldout.domain_evidence import biology_systems_evidence_executor as executor


REPO_ROOT = Path(__file__).resolve().parents[1]


def write_json(root: Path, rel_path: str, payload: dict | list) -> None:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def official_bundle(domain: str, row_total: int = 20, break_negative_control: bool = False) -> dict:
    observations = []
    for idx in range(row_total):
        observed = float(1000 + idx)
        predicted = observed
        comparator = observed + 10.0
        if break_negative_control and idx == 0:
            comparator = observed
        observations.append(
            {
                "observation_id": f"{domain.upper()}-OBS-{idx + 1:04d}",
                "training_source": f"official-{domain}-training-{idx + 1:04d}",
                "target_source": f"official-{domain}-target-{idx + 1:04d}",
                "formula": "pre_registered_oc_model_v1(features)",
                "predicted_value": predicted,
                "observed_value": observed,
                "comparator_prediction": comparator,
                "uncertainty": 0.0,
                "negative_control_id": f"{domain}-control-{idx + 1:04d}",
                "negative_control_description": "comparator residual must exceed model residual",
                "falsifier": "model residual exceeds uncertainty or comparator is not worse",
            }
        )
    return {
        "schema_id": executor.OFFICIAL_SNAPSHOT_BUNDLE_SCHEMA_ID,
        "domain": domain,
        "snapshot_kind": "official_snapshot_bundle",
        "source_separation": {
            "mode": "target_blind",
            "pre_target_lock": True,
            "target_hidden_until_scoring": True,
        },
        "model_under_test": "pre_registered_oc_model_v1(features)",
        "comparator_baseline": {
            "name": f"{domain} preregistered comparator",
            "prediction_rule": "fixed baseline comparator replayed on the same targets",
            "pre_registered": True,
        },
        "uncertainty_metric": "mean absolute residual",
        "uncertainty_method": "exact deterministic interval",
        "observations": observations,
    }


class BiologySystemsEvidenceExecutorTests(unittest.TestCase):
    def test_current_repo_snapshots_emit_blocked_candidates(self) -> None:
        report, candidates, protocol = executor.build_execution_payload(REPO_ROOT)

        self.assertEqual(report["candidate_pack_total"], 2)
        self.assertEqual(report["valid_under_current_grand_schema_total"], 0)
        self.assertEqual(report["valid_under_grand_gate_total"], 0)
        self.assertEqual(report["verdict"], "BLOCKED_PENDING_GENUINE_BIOLOGY_SYSTEMS_EVIDENCE")
        self.assertEqual(protocol["blocked_domain_total"], 2)

        by_domain = {candidate.domain: candidate for candidate in candidates}
        for domain in ("biology", "systems"):
            row = by_domain[domain].report_row
            self.assertEqual(row["candidate_n"], 1)
            self.assertFalse(row["valid_under_current_grand_schema"])
            self.assertFalse(row["valid_under_grand_gate"])
            self.assertFalse(by_domain[domain].pack["grand_toe_support_allowed"])
            self.assertIn("N_BELOW_MINIMUM::1/20", row["observation_validation_failures"])
            self.assertIn("SOURCE_SEPARATION_NOT_VERIFIABLE_FROM_CURRENT_SINGLE_RAW_SNAPSHOT", row["blockers"])
            self.assertTrue(all(test["passed"] for test in row["tamper_tests"]))

    def test_valid_official_snapshot_bundle_generates_schema_valid_pack(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(root, "validation/_raw/biology_bundle.json", official_bundle("biology"))

            candidate = executor.build_domain_candidate(root, "biology", "validation/_raw/biology_bundle.json")

            self.assertTrue(candidate.report_row["valid_under_executor"])
            self.assertTrue(candidate.report_row["valid_under_current_grand_schema"])
            self.assertTrue(candidate.report_row["valid_under_grand_gate"])
            self.assertEqual(candidate.pack["n"], 20)
            self.assertTrue(candidate.pack["grand_toe_support_allowed"])
            self.assertEqual(candidate.report_row["blockers"], [])
            self.assertTrue(all(test["passed"] for test in candidate.report_row["tamper_tests"]))

    def test_negative_control_failure_blocks_otherwise_large_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(
                root,
                "validation/_raw/systems_bundle.json",
                official_bundle("systems", break_negative_control=True),
            )

            candidate = executor.build_domain_candidate(root, "systems", "validation/_raw/systems_bundle.json")

            self.assertFalse(candidate.report_row["valid_under_executor"])
            self.assertFalse(candidate.report_row["valid_under_current_grand_schema"])
            self.assertFalse(candidate.report_row["valid_under_grand_gate"])
            self.assertFalse(candidate.pack["negative_controls"][0]["rejected"])
            self.assertFalse(candidate.pack["grand_toe_support_allowed"])
            self.assertIn(
                "OBSERVATION::0::SYSTEMS-OBS-0001::NEGATIVE_CONTROL_NOT_REJECTED",
                candidate.report_row["observation_validation_failures"],
            )

    def test_writer_materializes_only_scoped_output_refs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(root, "validation/_raw/biology_bundle.json", official_bundle("biology"))
            write_json(root, "validation/_raw/systems_bundle.json", official_bundle("systems"))

            report = executor.write_outputs(
                root,
                biology_snapshot_ref="validation/_raw/biology_bundle.json",
                systems_snapshot_ref="validation/_raw/systems_bundle.json",
            )

            self.assertEqual(report["valid_under_grand_gate_total"], 2)
            for ref in report["candidate_pack_refs"]:
                self.assertTrue((root / ref).is_file())
                self.assertTrue(ref.startswith(executor.OUTPUT_ROOT_REL))
            self.assertTrue((root / executor.OUTPUT_ROOT_REL / "OC133_BIOLOGY_SYSTEMS_EVIDENCE_PROTOCOL.json").is_file())
            self.assertTrue((root / executor.OUTPUT_ROOT_REL / "OC133_BIOLOGY_SYSTEMS_EVIDENCE_EXECUTION_REPORT.json").is_file())


if __name__ == "__main__":
    unittest.main()
