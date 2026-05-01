from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from validation.grand_science import evidence_pack_factory as factory


def write_json(root: Path, rel_path: str, payload: dict) -> None:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def base_requirements(domains: list[str]) -> dict:
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
        "support_policy": "fixture policy",
    }


def valid_pack(domain: str = "physics") -> dict:
    return {
        "schema_id": "OC133_GRAND_EMPIRICAL_EVIDENCE_v1",
        "release_id": "oc_core_1_3_3",
        "capability_owner": "Research/EmpiricalScience",
        "evidence_pack_id": f"PACK-{domain.upper()}-001",
        "domain": domain,
        "source_separation": {
            "mode": "target_blind",
            "pre_target_lock": True,
            "target_hidden_until_scoring": True,
            "training_sources": ["training-snapshot-a"],
            "target_sources": ["target-snapshot-b"],
        },
        "n": 20,
        "model_under_test": "pre-registered OC scoring rule",
        "comparator_baseline": {
            "name": "pre-registered comparator",
            "prediction_rule": "comparator scoring rule",
            "pre_registered": True,
        },
        "uncertainty": {
            "metric": "absolute residual",
            "method": "pre-registered interval",
            "interval": [0.0, 0.1],
        },
        "residuals": {
            "model": 0.05,
            "comparator": 0.15,
            "superiority_margin": 0.1,
        },
        "negative_controls": [
            {
                "control_id": "permuted-targets",
                "description": "permuted target labels must fail",
                "rejected": True,
            }
        ],
        "falsifiers": ["model residual exceeds uncertainty interval"],
        "grand_toe_support_allowed": True,
    }


def biology_target_pack() -> dict:
    pack = valid_pack("biology")
    pack["evidence_pack_id"] = "PACK-BIOLOGY-TARGETS-001"
    pack["evidence_family"] = "biology-target-evidence"
    pack["pack_version"] = "1.0"
    pack["source_contract"] = "official_biology_target_bundle"
    pack["model_under_test"] = "pre-registered biological response target scoring rule"
    pack["comparator_baseline"] = {
        "name": "pre-registered treatment-stratified biological response baseline",
        "prediction_rule": "use training-fold response mean for the matched assay and treatment class",
        "pre_registered": True,
    }
    digest = "a" * 64
    pack["source_hashes"] = [
        {
            "source_ref": "validation/_raw/biology_target_bundle.json",
            "source_sha256": digest,
            "hash_policy": "sha256",
        }
    ]
    pack["biological_target_rows"] = [
        {
            "biological_target_id": f"BIO-TARGET-{idx + 1:04d}",
            "biological_target_kind": "gene_expression_response_target",
            "source_ref": f"validation/_raw/biology_target_bundle.json::target={idx + 1:04d}",
            "source_sha256": digest,
            "prediction": float(idx),
            "observed": float(idx),
            "comparator_prediction": float(idx + 1),
        }
        for idx in range(20)
    ]
    return pack


class GrandEmpiricalFactoryTests(unittest.TestCase):
    def _minimal_root(self, root: Path, domains: list[str]) -> None:
        write_json(root, factory.REQUIREMENTS_REL, base_requirements(domains))
        write_json(
            root,
            factory.REGISTRY_REL,
            {
                "schema_id": "OC133_GRAND_SCIENCE_HELDOUT_REGISTRY_v1",
                "release_id": "oc_core_1_3_3",
                "capability_owner": "Research/EmpiricalScience",
                "evidence_pack_refs": [],
            },
        )

    def test_empty_registry_builds_decomposition_queue_and_keeps_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._minimal_root(root, ["physics", "chemistry"])
            sample = valid_pack("physics")
            sample["evidence_pack_id"] = "SAMPLE_ONLY_DO_NOT_REGISTER"
            write_json(root, factory.SAMPLE_PACK_REL, sample)

            payload = factory.build_grand_empirical_payload(root)

            self.assertEqual(payload["verdict"], "BLOCKED_PENDING_GENUINE_PER_DOMAIN_EVIDENCE")
            self.assertFalse(payload["empirical_domain_support_allowed"])
            self.assertFalse(payload["grand_toe_support_allowed"])
            self.assertEqual(payload["evidence_pack_total"], 0)
            self.assertEqual(payload["blocked_domain_total"], 2)
            self.assertEqual(payload["decomposition_queue_total"], 2)
            self.assertTrue(all(row["blocker_id"] == "grand_toe_empirical_superiority" for row in payload["decomposition_queue"]))

    def test_valid_registered_pack_satisfies_single_domain_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._minimal_root(root, ["physics"])
            write_json(root, "validation/heldout/physics_pack.json", valid_pack("physics"))
            write_json(
                root,
                factory.REGISTRY_REL,
                {
                    "schema_id": "OC133_GRAND_SCIENCE_HELDOUT_REGISTRY_v1",
                    "release_id": "oc_core_1_3_3",
                    "capability_owner": "Research/EmpiricalScience",
                    "evidence_pack_refs": ["validation/heldout/physics_pack.json"],
                },
            )

            payload = factory.build_grand_empirical_payload(root)

            self.assertEqual(payload["blocked_domain_total"], 0)
            self.assertEqual(payload["verdict"], "EMPIRICAL_DOMAIN_SUPPORT_ALLOWED")
            self.assertTrue(payload["empirical_domain_support_allowed"])
            self.assertTrue(payload["domain_predictive_superiority_supported"])
            self.assertFalse(payload["grand_toe_support_allowed"])
            self.assertFalse(payload["grand_toe_claim_promotion_allowed"])
            self.assertFalse(payload["final_theory_or_toe_promotion_allowed"])
            self.assertFalse(payload["broad_modern_science_coverage_promotion_allowed"])
            self.assertFalse(payload["modern_science_superiority_promotion_allowed"])
            self.assertEqual(payload["valid_evidence_pack_total"], 1)
            self.assertEqual(payload["domains"][0]["valid_n"], 20)
            self.assertTrue(payload["domains"][0]["empirical_domain_support_allowed"])
            self.assertFalse(payload["domains"][0]["grand_toe_support_allowed"])
            self.assertEqual(payload["decomposition_queue_total"], 0)

    def test_formal_mathematics_pack_is_rejected_by_empirical_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._minimal_root(root, ["mathematics"])
            formal_pack = {
                "schema_id": "OC133_FORMAL_SUPPORT_EVIDENCE_v1",
                "release_id": "oc_core_1_3_3",
                "capability_owner": "Research/FormalScience",
                "evidence_pack_id": "FORMAL-MATH-ONLY",
                "domain": "mathematics",
                "support_route": "formal",
                "formal_support_allowed": True,
                "formal_support_verdict": "FORMAL_SUPPORT_ACCEPTED",
                "empirical_support_allowed": False,
                "grand_toe_support_allowed": False,
                "source_separation": {
                    "mode": "target_blind",
                    "pre_target_lock": True,
                    "target_hidden_until_scoring": True,
                    "training_sources": ["proofs/input.json::expected"],
                    "target_sources": ["proofs/output.json::observed"],
                },
                "n": 20,
                "theorem_ids": ["T-FORMAL"],
                "proof_sheet_refs": ["proofs/proof_sheets/T-FORMAL.md"],
                "lean_refs": ["formal/lean/OC133V12.lean::t_formal"],
                "finite_case_ids": ["FM-FORMAL-POS", "FM-FORMAL-NEG"],
            }
            ref = "validation/heldout/grand_science/mathematics/formal_math_pack.json"
            write_json(root, ref, formal_pack)
            write_json(
                root,
                factory.REGISTRY_REL,
                {
                    "schema_id": "OC133_GRAND_SCIENCE_HELDOUT_REGISTRY_v1",
                    "release_id": "oc_core_1_3_3",
                    "capability_owner": "Research/EmpiricalScience",
                    "evidence_pack_refs": [ref],
                },
            )

            payload = factory.build_grand_empirical_payload(root)
            candidate = payload["candidate_rows"][0]

            self.assertTrue(factory.is_formal_only_pack(formal_pack))
            self.assertTrue(candidate["formal_only_pack"])
            self.assertIn("FORMAL_SUPPORT_ROUTE_NOT_EMPIRICAL_GRAND_EVIDENCE", candidate["failures"])
            self.assertIn("FORMAL_REQUIRED_DOMAIN_NOT_EMPIRICAL_EVIDENCE", candidate["failures"])
            self.assertEqual(payload["valid_evidence_pack_total"], 0)
            self.assertEqual(payload["empirical_required_domains"], [])
            self.assertEqual(payload["formal_required_domains"], ["mathematics"])
            self.assertEqual(payload["domain_total"], 0)
            self.assertEqual(payload["blocked_domain_total"], 0)
            self.assertEqual(payload["formal_route_status"][0]["status"], "ROUTED_TO_FORMAL_SUPPORT")

    def test_empirical_grand_gate_passes_empirical_domains_without_math_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._minimal_root(root, ["biology", "chemistry", "mathematics", "physics", "systems"])
            write_json(root, "validation/heldout/physics_pack.json", valid_pack("physics"))
            write_json(root, "validation/heldout/chemistry_pack.json", valid_pack("chemistry"))
            write_json(root, "validation/heldout/systems_pack.json", valid_pack("systems"))
            write_json(root, "validation/heldout/biology_targets.json", biology_target_pack())
            formal_pack = {
                "schema_id": "OC133_FORMAL_SUPPORT_EVIDENCE_v1",
                "release_id": "oc_core_1_3_3",
                "capability_owner": "Research/FormalScience",
                "evidence_pack_id": "FORMAL-MATH-ONLY",
                "domain": "mathematics",
                "support_route": "formal",
                "formal_support_allowed": True,
                "empirical_support_allowed": False,
                "grand_toe_support_allowed": False,
            }
            write_json(root, "validation/heldout/math_formal_pack.json", formal_pack)

            payload = factory.build_grand_empirical_payload(root)
            math_candidate = next(row for row in payload["candidate_rows"] if row["domain"] == "mathematics")

            self.assertEqual(payload["empirical_required_domains"], ["biology", "chemistry", "physics", "systems"])
            self.assertEqual(payload["formal_required_domains"], ["mathematics"])
            self.assertEqual(payload["domain_total"], 4)
            self.assertEqual(payload["blocked_domain_total"], 0)
            self.assertTrue(payload["empirical_domain_support_allowed"])
            self.assertFalse(payload["grand_toe_support_allowed"])
            self.assertFalse(payload["grand_toe_claim_promotion_allowed"])
            self.assertFalse(payload["final_theory_or_toe_promotion_allowed"])
            self.assertFalse(payload["broad_modern_science_coverage_promotion_allowed"])
            self.assertFalse(payload["modern_science_superiority_promotion_allowed"])
            self.assertNotIn("mathematics", [row["domain"] for row in payload["domains"]])
            self.assertEqual(payload["valid_evidence_pack_total"], 4)
            self.assertFalse(math_candidate["valid_for_grand_support"])
            self.assertIn("FORMAL_REQUIRED_DOMAIN_NOT_EMPIRICAL_EVIDENCE", math_candidate["failures"])

    def test_invalid_candidate_reports_strict_failure_reasons(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._minimal_root(root, ["physics"])
            pack = valid_pack("physics")
            pack["n"] = 19
            pack["source_separation"]["target_sources"] = ["training-snapshot-a"]
            pack["residuals"] = {"model": 0.2, "comparator": 0.1, "superiority_margin": -0.1}
            pack["negative_controls"][0]["rejected"] = False
            pack["grand_toe_support_allowed"] = False
            write_json(root, "validation/heldout/bad_physics_pack.json", pack)

            payload = factory.build_grand_empirical_payload(root)
            failures = payload["candidate_rows"][0]["failures"]

            self.assertIn("N_BELOW_MINIMUM::20", failures)
            self.assertIn("TRAINING_TARGET_SOURCE_OVERLAP", failures)
            self.assertIn("COMPARATOR_NOT_WORSE_THAN_MODEL", failures)
            self.assertIn("NEGATIVE_CONTROL_NOT_REJECTED::0", failures)
            self.assertIn("GRAND_TOE_SUPPORT_NOT_ALLOWED", failures)
            self.assertEqual(payload["blocked_domain_total"], 1)
            self.assertFalse(payload["empirical_domain_support_allowed"])
            self.assertFalse(payload["grand_toe_support_allowed"])

    def test_biology_pagination_only_pack_is_rejected_even_when_overclaiming(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._minimal_root(root, ["biology"])
            pack = valid_pack("biology")
            pack["evidence_pack_id"] = "OC133-BIOLOGY-NCBI-BATCH-CANDIDATE"
            pack["model_under_test"] = "NCBI/GEO ESearch batch page-size reconstruction: len(esearchresult.idlist)"
            pack["comparator_baseline"] = {
                "name": "GEO total-hit-count page-size negative control",
                "prediction_rule": "use esearchresult.count as the retmax prediction for every batch row",
                "pre_registered": True,
            }
            write_json(root, "validation/heldout/biology_pagination_pack.json", pack)

            payload = factory.build_grand_empirical_payload(root)
            failures = payload["candidate_rows"][0]["failures"]

            self.assertIn("BIOLOGY_PAGINATION_QA_NOT_GRAND_EVIDENCE", failures)
            self.assertIn("BIOLOGY_TARGET_ROWS_REQUIRED", failures)
            self.assertIn("BIOLOGY_COMPARATOR_STRUCTURALLY_SILLY_OR_PAGINATION_ONLY", failures)
            self.assertEqual(payload["blocked_domain_total"], 1)
            self.assertFalse(payload["empirical_domain_support_allowed"])
            self.assertFalse(payload["grand_toe_support_allowed"])

    def test_biology_successor_target_pack_requires_real_target_rows_and_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._minimal_root(root, ["biology"])
            write_json(root, "validation/heldout/biology_targets.json", biology_target_pack())

            payload = factory.build_grand_empirical_payload(root)

            self.assertEqual(payload["blocked_domain_total"], 0)
            self.assertTrue(payload["empirical_domain_support_allowed"])
            self.assertFalse(payload["grand_toe_support_allowed"])
            self.assertEqual(payload["candidate_rows"][0]["failures"], [])

    def test_biology_successor_target_pack_without_source_hashes_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._minimal_root(root, ["biology"])
            pack = biology_target_pack()
            for row in pack["biological_target_rows"]:
                row.pop("source_sha256")
            write_json(root, "validation/heldout/biology_targets_missing_hashes.json", pack)

            payload = factory.build_grand_empirical_payload(root)
            failures = payload["candidate_rows"][0]["failures"]

            self.assertIn("BIOLOGY_TARGET_SOURCE_HASH_MISSING::0", failures)
            self.assertEqual(payload["blocked_domain_total"], 1)

    def test_discovery_ignores_operational_status_reports_that_are_not_packs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._minimal_root(root, ["physics"])
            write_json(
                root,
                "validation/heldout/status_report.json",
                {
                    "schema_id": "SOME_OPERATIONAL_REPORT",
                    "release_id": "oc_core_1_3_3",
                    "grand_toe_support_allowed": False,
                    "verdict": "BLOCKED",
                },
            )

            payload = factory.build_grand_empirical_payload(root)

            self.assertEqual(payload["evidence_pack_total"], 0)
            self.assertEqual(payload["evidence_pack_failure_total"], 0)

    def test_empirical_pass_markdown_does_not_emit_old_toe_true_phrase(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._minimal_root(root, ["physics"])
            write_json(root, "validation/heldout/physics_pack.json", valid_pack("physics"))

            payload = factory.build_grand_empirical_payload(root)
            factory.write_markdown(root, payload)
            markdown = (root / factory.REPORT_MD_REL).read_text(encoding="utf-8")

            self.assertTrue(payload["empirical_domain_support_allowed"])
            self.assertFalse(payload["grand_toe_support_allowed"])
            self.assertNotIn("Grand TOE support allowed: `true`", markdown)
            self.assertIn("Empirical-domain support allowed: `true`", markdown)
            self.assertIn("TOE/final/broad modern-science promotion allowed by this gate: `false`", markdown)


if __name__ == "__main__":
    unittest.main()
