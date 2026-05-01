from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests.test_grand_empirical_factory import base_requirements, biology_target_pack, valid_pack, write_json
from validation.grand_science import evidence_pack_factory as factory


class GrandEmpiricalEvidenceSupersessionTests(unittest.TestCase):
    def _minimal_root(self, root: Path) -> None:
        write_json(root, factory.REQUIREMENTS_REL, base_requirements(["physics"]))
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

    def test_valid_successor_suppresses_stale_invalid_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._minimal_root(root)

            stale_ref = "validation/heldout/stale_physics_pack.json"
            stale = valid_pack("physics")
            stale["evidence_pack_id"] = "PACK-PHYSICS-STALE"
            stale["evidence_family"] = "physics-heldout-route"
            stale["pack_version"] = "1.0"
            stale["n"] = 3
            stale["grand_toe_support_allowed"] = False
            write_json(root, stale_ref, stale)

            successor_ref = "validation/heldout/current_physics_pack.json"
            successor = valid_pack("physics")
            successor["evidence_pack_id"] = "PACK-PHYSICS-CURRENT"
            successor["evidence_family"] = "physics-heldout-route"
            successor["pack_version"] = "2.0"
            successor["supersedes"] = ["PACK-PHYSICS-STALE", stale_ref]
            write_json(root, successor_ref, successor)

            payload = factory.build_grand_empirical_payload(root)
            domain = payload["domains"][0]

            self.assertEqual(payload["blocked_domain_total"], 0)
            self.assertTrue(payload["empirical_domain_support_allowed"])
            self.assertFalse(payload["grand_toe_support_allowed"])
            self.assertEqual(payload["valid_evidence_pack_total"], 1)
            self.assertEqual(payload["current_evidence_pack_failure_total"], 0)
            self.assertEqual(domain["candidate_pack_total"], 2)
            self.assertEqual(domain["current_candidate_pack_total"], 1)
            self.assertEqual(domain["superseded_candidate_pack_total"], 1)
            self.assertEqual(domain["valid_pack_refs"], [successor_ref])
            self.assertEqual(domain["blockers"], [])
            self.assertEqual(payload["candidate_rows"][0]["source_ref"], successor_ref)
            self.assertEqual(payload["candidate_rows"][1]["supersession_status"], "superseded")

    def test_valid_source_contract_successor_suppresses_stale_invalid_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._minimal_root(root)

            stale_ref = "validation/heldout/legacy_pubchem_physics_pack.json"
            stale = valid_pack("physics")
            stale["evidence_pack_id"] = "PACK-PHYSICS-PUBCHEM-STALE"
            stale["source_separation"]["training_sources"] = [
                "validation/_raw/physics_pubchem_legacy.txt::visible-fields"
            ]
            stale["source_separation"]["target_sources"] = [
                "validation/_raw/physics_pubchem_legacy.txt::target-field"
            ]
            stale["n"] = 3
            stale["grand_toe_support_allowed"] = False
            write_json(root, stale_ref, stale)

            successor_ref = "validation/heldout/current_pubchem_physics_pack.json"
            successor = valid_pack("physics")
            successor["evidence_pack_id"] = "PACK-PHYSICS-PUBCHEM-CURRENT"
            successor["source_separation"]["training_sources"] = [
                "validation/heldout/grand_science/physics/pubchem_batch/acquisition.json::visible-fields"
            ]
            successor["source_separation"]["target_sources"] = [
                "validation/heldout/grand_science/physics/pubchem_batch/acquisition.json::target-field"
            ]
            write_json(root, successor_ref, successor)

            payload = factory.build_grand_empirical_payload(root)
            stale_row = next(row for row in payload["candidate_rows"] if row["source_ref"] == stale_ref)

            self.assertEqual(payload["blocked_domain_total"], 0)
            self.assertTrue(payload["empirical_domain_support_allowed"])
            self.assertFalse(payload["grand_toe_support_allowed"])
            self.assertEqual(payload["current_evidence_pack_failure_total"], 0)
            self.assertEqual(stale_row["supersession_status"], "superseded")
            self.assertIn("pubchem", stale_row["source_contracts"])
            self.assertTrue(
                any(reason.startswith("SOURCE_CONTRACT_VALID_SUCCESSOR_SUPERSESSION::") for reason in stale_row["supersession_reasons"])
            )

    def test_invalid_successor_fails_closed_and_does_not_hide_stale_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._minimal_root(root)

            stale = valid_pack("physics")
            stale["evidence_pack_id"] = "PACK-PHYSICS-STALE"
            stale["evidence_family"] = "physics-heldout-route"
            stale["pack_version"] = "1.0"
            stale["n"] = 3
            stale["grand_toe_support_allowed"] = False
            write_json(root, "validation/heldout/stale_physics_pack.json", stale)

            successor = valid_pack("physics")
            successor["evidence_pack_id"] = "PACK-PHYSICS-CURRENT"
            successor["evidence_family"] = "physics-heldout-route"
            successor["pack_version"] = "2.0"
            successor["supersedes"] = ["PACK-PHYSICS-STALE"]
            successor["n"] = 19
            write_json(root, "validation/heldout/current_physics_pack.json", successor)

            payload = factory.build_grand_empirical_payload(root)
            domain = payload["domains"][0]

            self.assertEqual(payload["blocked_domain_total"], 1)
            self.assertFalse(payload["empirical_domain_support_allowed"])
            self.assertFalse(payload["grand_toe_support_allowed"])
            self.assertEqual(payload["valid_evidence_pack_total"], 0)
            self.assertEqual(payload["superseded_evidence_pack_total"], 0)
            self.assertEqual(payload["current_evidence_pack_failure_total"], 2)
            self.assertIn("CANDIDATE_EVIDENCE_PACKS_INVALID::2", domain["blockers"])

    def test_unrelated_invalid_candidate_remains_active_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._minimal_root(root)

            current_ref = "validation/heldout/current_pubchem_physics_pack.json"
            current = valid_pack("physics")
            current["evidence_pack_id"] = "PACK-PHYSICS-PUBCHEM-CURRENT"
            current["source_separation"]["training_sources"] = [
                "validation/heldout/grand_science/physics/pubchem_batch/acquisition.json::visible-fields"
            ]
            current["source_separation"]["target_sources"] = [
                "validation/heldout/grand_science/physics/pubchem_batch/acquisition.json::target-field"
            ]
            write_json(root, current_ref, current)

            unrelated_ref = "validation/heldout/unrelated_nist_physics_pack.json"
            unrelated = valid_pack("physics")
            unrelated["evidence_pack_id"] = "PACK-PHYSICS-NIST-INDEPENDENT"
            unrelated["source_separation"]["training_sources"] = [
                "validation/_raw/physics_nist_constants.txt::visible-fields"
            ]
            unrelated["source_separation"]["target_sources"] = [
                "validation/_raw/physics_nist_constants.txt::target-field"
            ]
            unrelated["n"] = 3
            unrelated["grand_toe_support_allowed"] = False
            write_json(root, unrelated_ref, unrelated)

            payload = factory.build_grand_empirical_payload(root)
            domain = payload["domains"][0]
            unrelated_row = next(row for row in payload["candidate_rows"] if row["source_ref"] == unrelated_ref)

            self.assertEqual(payload["blocked_domain_total"], 1)
            self.assertEqual(unrelated_row["supersession_status"], "current")
            self.assertIn("CANDIDATE_EVIDENCE_PACKS_INVALID::1", domain["blockers"])

    def _minimal_biology_root(self, root: Path) -> None:
        write_json(root, factory.REQUIREMENTS_REL, base_requirements(["biology"]))
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

    def _biology_pagination_candidate(self, pack_id: str) -> dict:
        pack = valid_pack("biology")
        pack["evidence_pack_id"] = pack_id
        pack["source_separation"]["pre_target_lock"] = False
        pack["source_separation"]["target_hidden_until_scoring"] = False
        pack["source_separation"]["training_sources"] = [
            "validation/_raw/biology_ncbi_geo_platform.txt::visible_fields(retstart,idlist)"
        ]
        pack["source_separation"]["target_sources"] = [
            "validation/_raw/biology_ncbi_geo_platform.txt::withheld_field(retmax)"
        ]
        pack["n"] = 1
        pack["model_under_test"] = "NCBI/GEO ESearch page-size reconstruction from retstart and idlist"
        pack["comparator_baseline"] = {
            "name": "GEO total-hit-count pagination negative control",
            "prediction_rule": "use esearchresult.count as the retmax prediction",
            "pre_registered": False,
        }
        pack["grand_toe_support_allowed"] = False
        return pack

    def test_valid_biology_target_successor_supersedes_pagination_and_template_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._minimal_biology_root(root)

            successor_ref = "validation/heldout/grand_science/biology/target_evidence/biology_targets.json"
            successor = biology_target_pack()
            successor["source_contract"] = "official_biology_target_bundle"
            write_json(root, successor_ref, successor)

            pagination_ref = "validation/heldout/grand_science/biology/ncbi_benchmark/benchmark.json"
            write_json(root, pagination_ref, self._biology_pagination_candidate("PACK-BIOLOGY-NCBI-PAGINATION"))

            template_ref = "validation/heldout/acquisition_plans/biology_systems/biology_candidate_pack_template.json"
            template = self._biology_pagination_candidate("PACK-BIOLOGY-SOURCE-TEMPLATE")
            template["evidence_family"] = "biology-bounded-source-template"
            write_json(root, template_ref, template)

            payload = factory.build_grand_empirical_payload(root)
            domain = payload["domains"][0]
            stale_rows = [
                row for row in payload["candidate_rows"]
                if row["source_ref"] in {pagination_ref, template_ref}
            ]

            self.assertEqual(payload["blocked_domain_total"], 0)
            self.assertTrue(payload["empirical_domain_support_allowed"])
            self.assertFalse(payload["grand_toe_support_allowed"])
            self.assertEqual(payload["current_evidence_pack_failure_total"], 0)
            self.assertEqual(domain["valid_pack_refs"], [successor_ref])
            self.assertEqual(domain["superseded_candidate_pack_total"], 2)
            self.assertTrue(all(row["supersession_status"] == "superseded" for row in stale_rows))
            self.assertTrue(
                all(
                    any(
                        reason.startswith("BIOLOGY_TARGET_VALID_SUCCESSOR_SUPERSESSION::PACK-BIOLOGY-TARGETS-001::")
                        and "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" in reason
                        for reason in row["supersession_reasons"]
                    )
                    for row in stale_rows
                )
            )

    def test_invalid_biology_target_successor_does_not_supersede_pagination_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._minimal_biology_root(root)

            successor = biology_target_pack()
            successor["source_contract"] = "official_biology_target_bundle"
            successor["n"] = 19
            write_json(root, "validation/heldout/grand_science/biology/target_evidence/biology_targets.json", successor)

            pagination_ref = "validation/heldout/grand_science/biology/ncbi_benchmark/benchmark.json"
            write_json(root, pagination_ref, self._biology_pagination_candidate("PACK-BIOLOGY-NCBI-PAGINATION"))

            payload = factory.build_grand_empirical_payload(root)
            stale_row = next(row for row in payload["candidate_rows"] if row["source_ref"] == pagination_ref)

            self.assertEqual(payload["blocked_domain_total"], 1)
            self.assertEqual(payload["superseded_evidence_pack_total"], 0)
            self.assertEqual(stale_row["supersession_status"], "current")
            self.assertIn("CANDIDATE_EVIDENCE_PACKS_INVALID::2", payload["domains"][0]["blockers"])

    def test_unrelated_invalid_biology_target_candidate_remains_active_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._minimal_biology_root(root)

            successor_ref = "validation/heldout/grand_science/biology/target_evidence/current_biology_targets.json"
            successor = biology_target_pack()
            successor["source_contract"] = "official_biology_target_bundle"
            write_json(root, successor_ref, successor)

            unrelated_ref = "validation/heldout/grand_science/biology/target_evidence/unrelated_invalid_targets.json"
            unrelated = biology_target_pack()
            unrelated["evidence_pack_id"] = "PACK-BIOLOGY-TARGETS-INDEPENDENT-INVALID"
            unrelated["source_contract"] = "official_biology_target_bundle"
            unrelated["n"] = 19
            write_json(root, unrelated_ref, unrelated)

            payload = factory.build_grand_empirical_payload(root)
            unrelated_row = next(row for row in payload["candidate_rows"] if row["source_ref"] == unrelated_ref)

            self.assertEqual(payload["blocked_domain_total"], 1)
            self.assertEqual(unrelated_row["supersession_status"], "current")
            self.assertEqual(unrelated_row["superseded_by"], [])
            self.assertIn("CANDIDATE_EVIDENCE_PACKS_INVALID::1", payload["domains"][0]["blockers"])


if __name__ == "__main__":
    unittest.main()
