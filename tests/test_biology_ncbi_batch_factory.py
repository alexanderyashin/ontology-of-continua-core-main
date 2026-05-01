from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools import oc133_biology_ncbi_batch_factory as factory


REPO_ROOT = Path(__file__).resolve().parents[1]


def write_json(root: Path, rel_path: str, payload: dict) -> None:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8", newline="\n")


def requirements(minimum_n: int = 20) -> dict:
    return {
        "schema_id": "OC133_GRAND_EMPIRICAL_DOMAIN_REQUIREMENTS_v1",
        "release_id": "oc_core_1_3_3",
        "capability_owner": "Research/EmpiricalScience",
        "minimum_per_domain_n": minimum_n,
        "required_domains": ["biology", "chemistry", "mathematics", "physics", "systems"],
        "required_source_separation_modes": ["prospective", "target_blind"],
    }


def batch_source_separation() -> dict:
    return {
        "mode": "target_blind",
        "kind": "target_blind_holdout_batch",
        "pre_target_lock": True,
        "target_hidden_until_scoring": True,
        "declared_before_scoring": True,
        "training_sources": ["mock-ncbi://geo/training-manifest-v1"],
        "target_sources": ["mock-ncbi://geo/target-manifest-v1"],
    }


def official_provenance(retstart: int = 0, retmax: int = 10) -> dict:
    return {
        "official_source": "NCBI E-utilities ESearch",
        "official_url": factory.official_esearch_url("GPL96[Accession]", retstart, retmax),
    }


def esearch_record(idx: int, retmax: int = 10) -> dict:
    retstart = idx * retmax
    return {
        "snapshot_provenance": official_provenance(retstart=retstart, retmax=retmax),
        "esearchresult": {
            "count": "1000",
            "retmax": str(retmax),
            "retstart": str(retstart),
            "idlist": [str(200000000 + retstart + item) for item in range(retmax)],
            "querytranslation": "GPL96[Accession]",
        },
    }


def ncbi_batch_snapshot(row_count: int, comparator_pre_registered: bool = True) -> dict:
    return {
        "source_separation": batch_source_separation(),
        "comparator_baseline": {
            "name": "GEO total-hit-count page-size negative control",
            "prediction_rule": "use esearchresult.count as the retmax prediction",
            "pre_registered": comparator_pre_registered,
        },
        "snapshots": [esearch_record(idx) for idx in range(row_count)],
    }


class BiologyNcbiBatchFactoryTests(unittest.TestCase):
    def test_current_single_geo_snapshot_blocks_and_emits_acquisition_packet(self) -> None:
        payload = factory.build_payload(REPO_ROOT, snapshot_refs=[factory.DEFAULT_SNAPSHOT_REF])
        report = payload["report"]
        tasks = payload["tasks"]
        pack = payload["candidate_pack"]
        acquisition = payload["acquisition_packet"]

        self.assertFalse(report["grand_toe_support_allowed"])
        self.assertEqual(report["verdict"], "BLOCKED_ACQUISITION_READY_NCBI_GEO_BATCH")
        self.assertEqual(report["candidate_n"], 1)
        self.assertEqual(report["missing_n"], 19)
        self.assertEqual(acquisition["missing_official_snapshot_total"], 19)
        self.assertTrue(acquisition["no_send"])
        self.assertFalse(acquisition["publish_allowed"])
        self.assertFalse(acquisition["registry_write_allowed"])
        self.assertFalse(pack["grand_toe_support_allowed"])
        self.assertTrue(tasks["rows"][0]["row_hash"])
        self.assertEqual(tasks["rows"][0]["formula"], "len(esearchresult.idlist)")
        self.assertIn("comparator_prediction", tasks["rows"][0])
        self.assertIn("negative_control_description", tasks["rows"][0])
        self.assertIn("falsifier", tasks["rows"][0])

        blocker_text = " ".join(report["blockers"])
        self.assertIn("SOURCE_SEPARATION_MODE_NOT_ALLOWED::snapshot_replay", blocker_text)
        self.assertIn("TARGET_HIDDEN_UNTIL_SCORING_REQUIRED", blocker_text)
        self.assertIn("COMPARATOR_BASELINE_NOT_PREREGISTERED", blocker_text)
        self.assertIn("OFFICIAL_NCBI_GEO_PROVENANCE_REQUIRED", blocker_text)
        self.assertIn("N_BELOW_MINIMUM::1/20", blocker_text)
        self.assertIn("GRAND_TOE_SUPPORT_NOT_ALLOWED", blocker_text)

        first_missing = acquisition["missing_official_snapshots"][0]
        self.assertEqual(first_missing["query_params"]["retstart"], 20)
        self.assertIn("eutils.ncbi.nlm.nih.gov", first_missing["official_endpoint_url"])
        self.assertTrue(first_missing["no_send_lock"])

    def test_target_hidden_official_batch_can_emit_support_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot_ref = "validation/_raw/ncbi_geo_batch_valid.json"
            write_json(root, factory.REQUIREMENTS_REL, requirements())
            write_json(root, snapshot_ref, ncbi_batch_snapshot(row_count=20))

            payload = factory.write_outputs(root, snapshot_refs=[snapshot_ref])
            report = payload["report"]
            pack = payload["candidate_pack"]
            acquisition = payload["acquisition_packet"]

            self.assertEqual(factory.check_stored(root, snapshot_refs=[snapshot_ref]), [])
            self.assertTrue(report["grand_toe_support_allowed"])
            self.assertEqual(report["verdict"], "READY_FOR_PARENT_REGISTRY_REVIEW")
            self.assertEqual(report["candidate_n"], 20)
            self.assertEqual(report["open_blocker_total"], 0)
            self.assertEqual(pack["n"], 20)
            self.assertTrue(pack["grand_toe_support_allowed"])
            self.assertEqual(pack["source_separation"]["mode"], "target_blind")
            self.assertTrue(pack["comparator_baseline"]["pre_registered"])
            self.assertGreater(pack["residuals"]["superiority_margin"], 0)
            self.assertEqual(len(pack["negative_controls"]), 20)
            self.assertTrue(all(control["rejected"] for control in pack["negative_controls"]))
            self.assertTrue(pack["falsifiers"])
            self.assertEqual(acquisition["missing_official_snapshot_total"], 0)
            self.assertTrue(all(test["passed"] for test in report["tamper_tests"]))
            self.assertTrue((root / factory.TASKS_REL).is_file())
            self.assertTrue((root / factory.PROTOCOL_REL).is_file())
            self.assertTrue((root / factory.CANDIDATE_PACK_REL).is_file())
            self.assertTrue((root / factory.REPORT_REL).is_file())
            self.assertTrue((root / factory.ACQUISITION_REL).is_file())
            self.assertTrue((root / factory.HASHES_REL).is_file())
            self.assertTrue((root / factory.README_REL).is_file())

    def test_nineteen_official_rows_remain_blocked_without_fake_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot_ref = "validation/_raw/ncbi_geo_batch_19.json"
            write_json(root, factory.REQUIREMENTS_REL, requirements())
            write_json(root, snapshot_ref, ncbi_batch_snapshot(row_count=19))

            payload = factory.build_payload(root, snapshot_refs=[snapshot_ref])
            report = payload["report"]

            self.assertFalse(report["grand_toe_support_allowed"])
            self.assertIn("N_BELOW_MINIMUM::19/20", report["blockers"])
            self.assertIn("GRAND_TOE_SUPPORT_NOT_ALLOWED", report["blockers"])
            self.assertEqual(payload["acquisition_packet"]["missing_official_snapshot_total"], 1)

    def test_unregistered_comparator_blocks_otherwise_valid_batch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot_ref = "validation/_raw/ncbi_geo_batch_unregistered_comparator.json"
            write_json(root, factory.REQUIREMENTS_REL, requirements())
            write_json(root, snapshot_ref, ncbi_batch_snapshot(row_count=20, comparator_pre_registered=False))

            report = factory.build_payload(root, snapshot_refs=[snapshot_ref])["report"]

            self.assertFalse(report["grand_toe_support_allowed"])
            self.assertIn("COMPARATOR_BASELINE_NOT_PREREGISTERED", report["blockers"])
            self.assertIn("GRAND_TOE_SUPPORT_NOT_ALLOWED", report["blockers"])


if __name__ == "__main__":
    raise SystemExit(unittest.main())
