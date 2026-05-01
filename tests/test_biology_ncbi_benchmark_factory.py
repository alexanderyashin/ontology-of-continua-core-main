from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools import oc133_biology_ncbi_benchmark_factory as factory


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


def ncbi_snapshot(
    *,
    source_separation: dict | None = None,
    metadata_count: int = 0,
    comparator_pre_registered: bool = True,
) -> dict:
    metadata_rows = [
        {
            "record_id": f"GSM-MOCK-{idx:04d}",
            "platform": "GPL96",
            "formula": "mock_prelocked_metadata_count",
            "predicted_value": float(idx),
            "observed_value": float(idx),
            "comparator_prediction": float(idx + 1),
            "uncertainty": 0.0,
            "comparator_pre_registered": comparator_pre_registered,
            "negative_control_description": "declared comparator must have larger residual than metadata formula",
            "falsifier": "metadata residual exceeds uncertainty or comparator is not worse",
        }
        for idx in range(1, metadata_count + 1)
    ]
    payload = {
        "header": {"type": "esearch", "version": "0.3"},
        "esearchresult": {
            "count": "101",
            "retmax": "1",
            "retstart": "0",
            "idlist": ["200000001"],
        },
        "count_task": {
            "formula": "retstart + len(idlist)",
            "predicted_value": 1.0,
            "observed_value": 1.0,
            "comparator_prediction": 2.0,
            "uncertainty": 0.0,
            "comparator_pre_registered": comparator_pre_registered,
        },
        "metadata_rows": metadata_rows,
    }
    if source_separation is not None:
        payload["source_separation"] = source_separation
    return payload


def target_blind_source_separation(kind: str = "target_blind_holdout") -> dict:
    return {
        "mode": "target_blind",
        "kind": kind,
        "pre_target_lock": True,
        "target_hidden_until_scoring": True,
        "training_sources": ["mock-ncbi://training/esearch-and-metadata-v1"],
        "target_sources": ["mock-ncbi://heldout/retmax-and-metadata-v1"],
    }


class BiologyNcbiBenchmarkFactoryTests(unittest.TestCase):
    def test_current_repo_snapshot_replay_is_blocked_and_hashes_rows(self) -> None:
        payload = factory.build_payload(REPO_ROOT)
        report = payload["report"]
        tasks = payload["tasks"]
        pack = payload["candidate_pack"]

        self.assertFalse(report["grand_toe_support_allowed"])
        self.assertEqual(report["verdict"], "BLOCKED_PENDING_GENUINE_BIOLOGY_REPLAY_EVIDENCE")
        self.assertEqual(report["n"], 1)
        self.assertEqual(report["minimum_n"], 20)
        self.assertTrue(report["snapshot_sha256"])
        self.assertTrue(report["candidate_pack_sha256"])
        self.assertEqual(len(report["candidate_pack_row_hashes"]), 1)
        self.assertTrue(tasks["rows"][0]["row_hash"])
        self.assertEqual(pack["grand_toe_support_allowed"], False)

        blocker_text = " ".join(report["blockers"])
        self.assertIn("TARGET_SEPARATION_NOT_REAL::snapshot_replay", blocker_text)
        self.assertIn("N_BELOW_MINIMUM::1/20", blocker_text)
        self.assertIn("COMPARATOR_BASELINE_NOT_PREREGISTERED", blocker_text)
        self.assertIn("PRE_TARGET_LOCK_REQUIRED", blocker_text)
        self.assertIn("TARGET_HIDDEN_UNTIL_SCORING_REQUIRED", blocker_text)

        row = tasks["rows"][0]
        self.assertEqual(row["formula"], "retstart + len(idlist)")
        self.assertIn("comparator_prediction", row)
        self.assertIn("uncertainty", row)
        self.assertIn("model_residual", row)
        self.assertIn("comparator_residual", row)
        self.assertIn("negative_control_description", row)
        self.assertIn("falsifier", row)

    def test_mocked_target_blind_ncbi_records_can_emit_support_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(root, factory.REQUIREMENTS_REL, requirements())
            write_json(
                root,
                factory.DEFAULT_SNAPSHOT_REF,
                ncbi_snapshot(
                    source_separation=target_blind_source_separation(),
                    metadata_count=19,
                    comparator_pre_registered=True,
                ),
            )

            report = factory.write_outputs(root)
            payload = factory.build_payload(root)
            pack = payload["candidate_pack"]

            self.assertEqual(report, payload["report"])
            self.assertEqual(factory.check_stored(root), [])
            self.assertTrue(report["grand_toe_support_allowed"])
            self.assertEqual(report["verdict"], "READY_FOR_PARENT_REGISTRY_REVIEW")
            self.assertEqual(report["n"], 20)
            self.assertEqual(report["open_blocker_total"], 0)
            self.assertEqual(pack["n"], 20)
            self.assertEqual(pack["source_separation"]["mode"], "target_blind")
            self.assertTrue(pack["comparator_baseline"]["pre_registered"])
            self.assertGreater(pack["residuals"]["superiority_margin"], 0)
            self.assertEqual(len(pack["negative_controls"]), 20)
            self.assertTrue(all(row["rejected"] for row in pack["negative_controls"]))
            self.assertTrue(pack["falsifiers"])
            self.assertTrue((root / factory.TASKS_REL).is_file())
            self.assertTrue((root / factory.CANDIDATE_PACK_REL).is_file())
            self.assertTrue((root / factory.PROTOCOL_REL).is_file())
            self.assertTrue((root / factory.REPORT_REL).is_file())
            self.assertTrue((root / factory.README_REL).is_file())

    def test_snapshot_replay_kind_blocks_even_with_target_blind_label(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(root, factory.REQUIREMENTS_REL, requirements())
            write_json(
                root,
                factory.DEFAULT_SNAPSHOT_REF,
                ncbi_snapshot(
                    source_separation=target_blind_source_separation(kind="snapshot_replay"),
                    metadata_count=19,
                    comparator_pre_registered=True,
                ),
            )

            report = factory.build_payload(root)["report"]

            self.assertFalse(report["grand_toe_support_allowed"])
            self.assertIn("TARGET_SEPARATION_NOT_REAL::snapshot_replay", report["blockers"])
            self.assertNotIn("N_BELOW_MINIMUM::20", report["blockers"])

    def test_unregistered_comparator_blocks_otherwise_valid_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(root, factory.REQUIREMENTS_REL, requirements())
            write_json(
                root,
                factory.DEFAULT_SNAPSHOT_REF,
                ncbi_snapshot(
                    source_separation=target_blind_source_separation(),
                    metadata_count=19,
                    comparator_pre_registered=False,
                ),
            )

            report = factory.build_payload(root)["report"]

            self.assertFalse(report["grand_toe_support_allowed"])
            self.assertIn("COMPARATOR_BASELINE_NOT_PREREGISTERED", report["blockers"])


if __name__ == "__main__":
    raise SystemExit(unittest.main())
