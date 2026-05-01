from __future__ import annotations

import json
import hashlib
import tempfile
import unittest
from pathlib import Path

from tools import oc133_biology_ncbi_batch_factory as factory


REPO_ROOT = Path(__file__).resolve().parents[1]


def write_json(root: Path, rel_path: str, payload: dict) -> None:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_bytes(root: Path, rel_path: str, payload: bytes) -> None:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


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


def acquisition_request(idx: int, retstart: int, retmax: int = 20) -> dict:
    return {
        "acquisition_id": f"OC133-NCBI-GEO-OFFICIAL-SNAPSHOT-{idx:04d}",
        "official_source": "NCBI E-utilities ESearch",
        "official_endpoint_url": factory.official_esearch_url("GPL96[Accession]", retstart, retmax),
        "expected_local_snapshot_ref": (
            f"validation/_raw/biology_ncbi_geo_gpl96_accession_retstart_{retstart:06d}_retmax_{retmax}.json"
        ),
        "query_params": {"db": "gds", "term": "GPL96[Accession]", "retmode": "json", "retstart": retstart, "retmax": retmax},
        "required_fields": [
            "header.type",
            "esearchresult.count",
            "esearchresult.retmax",
            "esearchresult.retstart",
            "esearchresult.idlist",
            "esearchresult.querytranslation",
        ],
        "no_send_lock": True,
    }


def write_official_lock_fixture(root: Path, idx: int, retstart: int, retmax: int = 20) -> None:
    acquisition_id = f"OC133-NCBI-GEO-OFFICIAL-SNAPSHOT-{idx:04d}"
    snapshot_ref = f"{factory.OFFICIAL_ACQUISITION_SNAPSHOTS_REL}/{acquisition_id}.json"
    lock_ref = f"{factory.OFFICIAL_ACQUISITION_LOCKS_REL}/{acquisition_id}.lock.json"
    body = json.dumps(esearch_record(idx, retmax)["esearchresult"], ensure_ascii=True, separators=(",", ":"))
    payload = (
        '{"header":{"type":"esearch","version":"0.3"},"esearchresult":'
        + body
        + "}\n"
    ).encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    expected_ref = f"validation/_raw/biology_ncbi_geo_gpl96_accession_retstart_{retstart:06d}_retmax_{retmax}.json"
    write_bytes(root, snapshot_ref, payload)
    write_json(
        root,
        lock_ref,
        {
            "schema_id": "OC133_OFFICIAL_READONLY_ACQUISITION_NO_SEND_LOCK_v1",
            "release_id": "oc_core_1_3_3",
            "acquisition_id": acquisition_id,
            "official_endpoint_url": factory.official_esearch_url("GPL96[Accession]", retstart, retmax),
            "expected_local_snapshot_ref": expected_ref,
            "snapshot_ref": snapshot_ref,
            "snapshot_sha256": digest,
            "byte_count": len(payload),
            "http_status": 200,
            "hash_policy": factory.OFFICIAL_ACQUISITION_HASH_POLICY,
            "locks": {"no_send": True, "publish_allowed": False, "registry_write_allowed": False},
            "scientific_pass": False,
        },
    )


class BiologyNcbiBatchFactoryTests(unittest.TestCase):
    def test_current_official_geo_locks_are_scored_and_remaining_packet_deltas_emitted(self) -> None:
        payload = factory.build_payload(REPO_ROOT)
        report = payload["report"]
        tasks = payload["tasks"]
        pack = payload["candidate_pack"]
        acquisition = payload["acquisition_packet"]

        self.assertFalse(report["grand_toe_support_allowed"])
        self.assertEqual(report["verdict"], "BLOCKED_ACQUISITION_READY_NCBI_GEO_BATCH")
        self.assertEqual(report["candidate_n"], 20)
        self.assertEqual(report["missing_n"], 0)
        self.assertEqual(acquisition["missing_official_snapshot_total"], 0)
        self.assertTrue(acquisition["no_send"])
        self.assertFalse(acquisition["publish_allowed"])
        self.assertFalse(acquisition["registry_write_allowed"])
        self.assertFalse(pack["grand_toe_support_allowed"])
        official_row = tasks["rows"][1]
        self.assertTrue(official_row["row_hash"])
        self.assertEqual(official_row["formula"], "len(esearchresult.idlist)")
        self.assertTrue(official_row["declared_before_scoring_lock"])
        self.assertTrue(official_row["lock_ref"].endswith(".lock.json"))
        self.assertTrue(official_row["source_snapshot_hash"])
        self.assertEqual(official_row["negative_control_status"], "REJECTED")
        self.assertIn("formula_inputs", official_row)
        self.assertIn("prediction_inputs", official_row)

        blocker_text = " ".join(report["blockers"])
        self.assertIn("SOURCE_SEPARATION_MODE_NOT_ALLOWED::official_readonly_snapshot_replay", blocker_text)
        self.assertIn("TARGET_HIDDEN_UNTIL_SCORING_REQUIRED", blocker_text)
        self.assertIn("DECLARED_BEFORE_SCORING_LOCK_REQUIRED", blocker_text)
        self.assertIn("COMPARATOR_BASELINE_NOT_PREREGISTERED", blocker_text)
        self.assertNotIn("N_BELOW_MINIMUM", blocker_text)
        self.assertIn("GRAND_TOE_SUPPORT_NOT_ALLOWED", blocker_text)
        self.assertEqual(acquisition["missing_official_snapshots"], [])

    def test_fixture_acquisition_locks_are_mapped_back_to_packet_requests(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(root, factory.REQUIREMENTS_REL, requirements())
            write_json(
                root,
                factory.ACQUISITION_REL,
                {
                    "schema_id": factory.ACQUISITION_SCHEMA_ID,
                    "missing_official_snapshots": [
                        acquisition_request(1, 20),
                        acquisition_request(2, 40),
                        acquisition_request(3, 60),
                    ],
                    "no_send": True,
                },
            )
            write_official_lock_fixture(root, 1, 20)
            write_official_lock_fixture(root, 2, 40)

            payload = factory.write_outputs(root)
            report = payload["report"]
            acquisition = payload["acquisition_packet"]

            self.assertEqual(factory.check_stored(root), [])
            self.assertFalse(report["grand_toe_support_allowed"])
            self.assertEqual(report["candidate_n"], 2)
            self.assertEqual(acquisition["missing_official_snapshot_total"], 18)
            self.assertEqual(acquisition["missing_official_snapshots"][0]["acquisition_id"], "OC133-NCBI-GEO-OFFICIAL-SNAPSHOT-0003")
            self.assertTrue(all(row["declared_before_scoring_lock"] for row in payload["tasks"]["rows"]))
            self.assertTrue(all(row["expected_local_snapshot_ref"] for row in payload["tasks"]["rows"]))
            self.assertIn("TARGET_HIDDEN_UNTIL_SCORING_REQUIRED", report["blockers"])
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
