from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from validation.grand_science import evidence_pack_factory as grand_factory
from validation.heldout.domain_evidence import physics_chemistry_evidence_executor as executor


REPO_ROOT = Path(__file__).resolve().parents[1]


def write_json(root: Path, rel_path: str, payload: dict) -> None:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(root: Path, rel_path: str, text: str) -> None:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def requirements(domains: list[str]) -> dict:
    return {
        "schema_id": "OC133_GRAND_EMPIRICAL_DOMAIN_REQUIREMENTS_v1",
        "release_id": "oc_core_1_3_3",
        "capability_owner": "Research/EmpiricalScience",
        "minimum_per_domain_n": 20,
        "required_domains": domains,
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
        "support_policy": "test policy",
    }


def valid_target_row(root: Path, domain: str, idx: int) -> dict:
    snapshot_ref = f"validation/_raw/{domain}_case_{idx:02d}.txt"
    observed = float(1000 + idx)
    predicted = observed
    comparator_prediction = observed + 1.0
    write_text(root, snapshot_ref, f"{domain} official held-out target {idx}: {observed}\n")
    return {
        "claim_id": f"OC133-TARGETBLIND-{domain.upper()}-{idx:03d}",
        "lane": domain,
        "dataset_snapshot_ref": snapshot_ref,
        "target_blind_split": "visible training fields locked before scoring; withheld target field hidden until scoring",
        "formula": f"pre_registered_{domain}_formula_{idx}",
        "predicted_value": predicted,
        "observed_value": observed,
        "uncertainty": 0.0,
        "comparator_baseline": f"{domain} plus-one negative control",
        "comparator_prediction": comparator_prediction,
        "residual": 0.0,
        "comparator_residual": 1.0,
        "negative_control": "plus-one comparator must have larger residual",
        "negative_control_rejected": True,
        "falsifier": "model residual differs from withheld target or comparator is not worse",
        "prediction_support_allowed": True,
        "empirical_support_allowed": True,
        "grand_empirical_support_allowed": True,
        "support_scope": "domain benchmark row with explicit grand empirical support",
        "snapshot_sha256": executor.sha256_lf_normalized_text(root / snapshot_ref),
        "snapshot_sha256_policy": executor.HASH_POLICY,
    }


class PhysicsChemistryEvidenceExecutorTests(unittest.TestCase):
    def test_current_generated_outputs_are_blocked_and_grand_factory_invalid(self) -> None:
        self.assertEqual(executor.check_stored(REPO_ROOT), [])

        payloads = executor.build_all(REPO_ROOT)
        protocol = payloads[f"{executor.OUTPUT_DIR_REL}/OC133_PHYSICS_CHEMISTRY_EVIDENCE_PROTOCOL.json"]
        self.assertIsInstance(protocol, dict)
        self.assertEqual(protocol["valid_candidate_pack_total"], 0)
        self.assertEqual(protocol["blocked_candidate_pack_total"], 2)

        reqs = executor.read_json(REPO_ROOT / executor.REQUIREMENTS_REL)
        for domain in executor.DOMAINS:
            pack = payloads[f"{executor.OUTPUT_DIR_REL}/{domain}_candidate_evidence_pack.json"]
            self.assertIsInstance(pack, dict)
            failures = grand_factory.pack_failure_reasons(pack, reqs)
            self.assertIn("N_BELOW_MINIMUM::20", failures)
            self.assertIn("GRAND_TOE_SUPPORT_NOT_ALLOWED", failures)

    def test_executor_can_emit_valid_grand_pack_for_genuine_n20_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(root, executor.REQUIREMENTS_REL, requirements(["physics", "chemistry"]))
            rows = [valid_target_row(root, "physics", idx) for idx in range(20)]
            write_json(
                root,
                executor.TARGET_BLIND_REL,
                {
                    "schema_id": "OC133_TARGET_BLIND_PREDICTION_TABLE_v1",
                    "release_id": "oc_core_1_3_3",
                    "rows": rows,
                },
            )

            pack, protocol = executor.domain_protocol(root, "physics", 20)

            self.assertTrue(protocol["grand_toe_support_allowed_by_executor"])
            self.assertEqual(protocol["grand_eligible_case_total"], 20)
            self.assertEqual(protocol["candidate_pack_grand_schema_failures"], [])
            self.assertTrue(protocol["candidate_pack_valid_under_current_grand_schema"])
            self.assertEqual(grand_factory.pack_failure_reasons(pack, requirements(["physics", "chemistry"])), [])

    def test_hash_tamper_and_negative_control_failures_are_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            row = valid_target_row(root, "chemistry", 0)
            row["snapshot_sha256"] = "not-the-actual-hash"
            row["comparator_prediction"] = row["predicted_value"]
            row["comparator_residual"] = row["residual"]
            row["negative_control_rejected"] = False

            case = executor.validate_target_blind_row(root, row)

            self.assertIn("SNAPSHOT_SHA256_MISMATCH", case["field_failures"])
            self.assertIn("COMPARATOR_NOT_WORSE_THAN_MODEL", case["field_failures"])
            self.assertIn("NEGATIVE_CONTROL_NOT_REJECTED", case["field_failures"])
            self.assertFalse(case["usable_for_blocked_candidate_pack"])
            expected_rejections = {test["expected_rejection"] for test in case["tamper_tests"]}
            self.assertIn("SNAPSHOT_SHA256_MISMATCH", expected_rejections)
            self.assertIn("COMPARATOR_NOT_WORSE_THAN_MODEL", expected_rejections)


if __name__ == "__main__":
    unittest.main()
