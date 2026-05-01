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


def ncbi_batch_snapshot_without_source_separation(row_count: int) -> dict:
    payload = ncbi_batch_snapshot(row_count)
    payload.pop("source_separation")
    return payload


def legacy_seed_snapshot(metadata: dict | None = None) -> dict:
    record = {"esearchresult": esearch_record(0)["esearchresult"]}
    if metadata is not None:
        record["legacy_seed_lock"] = metadata
    return record


def target_projection_visible(row: dict, fields: list[str]) -> dict:
    values = {
        "esearchresult.idlist": [str(item) for item in row["formula_inputs"]["idlist"]],
        "esearchresult.retstart": int(row["retstart"]),
        "esearchresult.querytranslation": str(row["query_term"]),
        "esearchresult.retmax": int(row["retmax"]),
    }
    return {field: values[field] for field in fields if field in values}


def write_target_projection_lock_bundle(
    root: Path,
    rows: list[dict],
    *,
    visible_fields: list[str] | None = None,
    target_fields: list[str] | None = None,
    refs: dict[str, str] | None = None,
    row_id_for: object | None = None,
    snapshot_ref: str = "",
    snapshot_rows: list[dict] | None = None,
) -> dict:
    visible_fields = visible_fields or list(factory.BIOLOGY_VISIBLE_FIELDS)
    target_fields = target_fields or list(factory.BIOLOGY_TARGET_FIELDS)
    refs = refs or factory.target_projection_refs()
    declaration = {
        "schema_id": "OC133_BIOLOGY_NCBI_BATCH_TARGET_PROJECTION_DECLARATION_v1",
        "release_id": "oc_core_1_3_3",
        "lock_id": factory.BIOLOGY_TARGET_LOCK_ID,
        "declared_before_scoring": True,
        "visible_fields": visible_fields,
        "target_fields": target_fields,
        "row_count": len(rows),
        "locks": factory.PROJECTION_NO_SEND_LOCKS,
    }
    if snapshot_ref:
        snapshot_payload = {
            "schema_id": "OC133_TARGET_PROJECTION_NORMALIZED_SNAPSHOT_v1",
            "domain": "biology_ncbi_batch",
            "rows": snapshot_rows or [],
        }
        write_json(root, snapshot_ref, snapshot_payload)
        declaration.update(
            {
                "snapshot_ref": snapshot_ref,
                "snapshot_format": "json",
                "row_id_field": "acquisition_id",
                "expected_snapshot_sha256": factory.sha256_bytes((root / snapshot_ref).read_bytes()),
            }
        )
    declaration_hash = factory.sha256_object(
        {
            key: value
            for key, value in declaration.items()
            if key not in factory.target_projection_factory.EXPECTED_HASH_KEYS
        }
    )
    visible_rows = []
    target_rows = []
    prediction_rows = []
    for index, row in enumerate(rows, start=1):
        row_id = row_id_for(index, row) if callable(row_id_for) else row["observation_id"]
        visible = target_projection_visible(row, visible_fields)
        target = target_projection_visible(row, target_fields)
        visible_row = {"row_index": index, "row_id": row_id, "visible": visible}
        target_row = {"row_index": index, "row_id": row_id, "target": target}
        visible_hash = factory.sha256_object(visible_row)
        target_hash = factory.sha256_object(target_row)
        visible_rows.append({**visible_row, "visible_row_sha256": visible_hash})
        target_rows.append({**target_row, "target_row_sha256": target_hash})
        prediction_rows.append(
            {
                "row_index": index,
                "row_id": row_id,
                "visible_row_sha256": visible_hash,
                "declaration_sha256": declaration_hash,
                "model_prediction": float(row["predicted_value"]),
                "comparator_prediction": float(row["comparator_prediction"]),
                "target_opened": False,
            }
        )

    visible_lock = {
        "schema_id": factory.target_projection_factory.VISIBLE_LOCK_SCHEMA_ID,
        "release_id": "oc_core_1_3_3",
        "lock_id": factory.BIOLOGY_TARGET_LOCK_ID,
        "declaration_ref": refs["declaration_ref"],
        "declaration_sha256": declaration_hash,
        "visible_fields": visible_fields,
        "row_count": len(visible_rows),
        "rows": visible_rows,
        "locks": factory.PROJECTION_NO_SEND_LOCKS,
    }
    if snapshot_ref:
        visible_lock["snapshot_ref"] = snapshot_ref
        visible_lock["snapshot_sha256"] = declaration["expected_snapshot_sha256"]
    visible_sha = factory.sha256_object(visible_lock)
    prediction_lock = {
        "schema_id": factory.target_projection_factory.PREDICTION_LOCK_SCHEMA_ID,
        "release_id": "oc_core_1_3_3",
        "lock_id": factory.BIOLOGY_TARGET_LOCK_ID,
        "declaration_ref": refs["declaration_ref"],
        "declaration_sha256": declaration_hash,
        "visible_projection_sha256": visible_sha,
        "prediction_rows": prediction_rows,
        "algorithmic_target_separation": {
            "prediction_inputs": "visible projection rows plus locked declarations only",
            "target_projection_read_before_prediction_materialization": False,
            "target_opened_after_prediction_materialization": True,
        },
        "locks": factory.PROJECTION_NO_SEND_LOCKS,
    }
    prediction_sha = factory.sha256_object(prediction_lock)
    target_lock = {
        "schema_id": factory.target_projection_factory.TARGET_LOCK_SCHEMA_ID,
        "release_id": "oc_core_1_3_3",
        "lock_id": factory.BIOLOGY_TARGET_LOCK_ID,
        "declaration_ref": refs["declaration_ref"],
        "declaration_sha256": declaration_hash,
        "visible_projection_sha256": visible_sha,
        "prediction_materialization_sha256": prediction_sha,
        "target_fields": target_fields,
        "row_count": len(target_rows),
        "rows": target_rows,
        "target_opened_after_prediction_materialization": True,
        "locks": factory.PROJECTION_NO_SEND_LOCKS,
    }
    if snapshot_ref:
        target_lock["snapshot_ref"] = snapshot_ref
        target_lock["snapshot_sha256"] = declaration["expected_snapshot_sha256"]
    target_sha = factory.sha256_object(target_lock)
    declaration.update(
        {
            "expected_declaration_sha256": declaration_hash,
            "expected_visible_projection_sha256": visible_sha,
            "expected_prediction_materialization_sha256": prediction_sha,
            "expected_target_projection_sha256": target_sha,
        }
    )
    write_json(root, refs["declaration_ref"], declaration)
    write_json(root, refs["visible_lock_ref"], visible_lock)
    write_json(root, refs["prediction_lock_ref"], prediction_lock)
    write_json(root, refs["target_lock_ref"], target_lock)
    return {
        "required": True,
        "verified": True,
        "valid": True,
        "source_separation_derived": True,
        "generated_by": "tools/oc133_target_projection_lock_orchestrator.py",
        "standard_factory": "tools/oc133_target_projection_lock_factory.py",
        "refs": {
            "declaration_ref": refs["declaration_ref"],
            "visible_projection_lock_ref": refs["visible_lock_ref"],
            "prediction_materialization_lock_ref": refs["prediction_lock_ref"],
            "target_projection_lock_ref": refs["target_lock_ref"],
        },
        "expected_refs": refs,
        "hashes": {
            "declaration_sha256": declaration_hash,
            "visible_projection_lock_sha256": visible_sha,
            "prediction_materialization_lock_sha256": prediction_sha,
            "target_projection_lock_sha256": target_sha,
            **({"snapshot_sha256": declaration["expected_snapshot_sha256"]} if snapshot_ref else {}),
        },
        "failures": [],
        "locks": factory.PROJECTION_NO_SEND_LOCKS,
    }


def normalized_projection_snapshot_row(row: dict, acquisition_id: str) -> dict:
    return {
        "acquisition_id": acquisition_id,
        "source_snapshot_ref": row["snapshot_ref"],
        "source_snapshot_sha256": row["snapshot_sha256"],
        "esearchresult": {
            "retmax": int(row["retmax"]),
            "retstart": int(row["retstart"]),
            "idlist": [str(item) for item in row["formula_inputs"]["idlist"]],
            "querytranslation": str(row["query_term"]),
        },
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
        self.assertTrue(report["target_projection_lock"]["valid"])
        self.assertEqual(report["target_projection_lock"]["legacy_seed_row_total"], 1)
        self.assertEqual(tasks["source_separation"]["mode"], "target_blind")
        self.assertEqual(tasks["source_separation"]["kind"], "target_projection_lock_with_legacy_seed_upgrade")
        seed_row = tasks["rows"][0]
        self.assertTrue(seed_row["legacy_seed_upgrade"])
        self.assertTrue(seed_row["target_projection_lock_verified"])
        self.assertTrue(seed_row["lock_ref"].startswith(factory.LEGACY_SEED_LOCK_ROOT_REL))
        self.assertTrue(seed_row["official_source_confirmed"])
        self.assertTrue(seed_row["declared_before_scoring_lock"])
        self.assertTrue(seed_row["comparator_pre_registered"])
        official_row = tasks["rows"][1]
        self.assertTrue(official_row["row_hash"])
        self.assertEqual(official_row["formula"], "len(esearchresult.idlist)")
        self.assertTrue(official_row["declared_before_scoring_lock"])
        self.assertTrue(official_row["lock_ref"].endswith(".target_projection_lock.json"))
        self.assertTrue(official_row["source_snapshot_hash"])
        self.assertEqual(official_row["negative_control_status"], "REJECTED")
        self.assertIn("formula_inputs", official_row)
        self.assertIn("prediction_inputs", official_row)

        blocker_text = " ".join(report["blockers"])
        self.assertNotIn("SOURCE_SEPARATION_MODE_NOT_ALLOWED::official_readonly_snapshot_replay", blocker_text)
        self.assertNotIn("TARGET_HIDDEN_UNTIL_SCORING_REQUIRED", blocker_text)
        self.assertNotIn("DECLARED_BEFORE_SCORING_LOCK_REQUIRED", blocker_text)
        self.assertNotIn("COMPARATOR_BASELINE_NOT_PREREGISTERED", blocker_text)
        self.assertNotIn("TARGET_PROJECTION_LOCK_REQUIRED", blocker_text)
        self.assertNotIn("N_BELOW_MINIMUM", blocker_text)
        self.assertIn(factory.PAGINATION_QA_BLOCKER, blocker_text)
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
            self.assertIn("TARGET_PROJECTION_LOCK_REQUIRED", report["blockers"])
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

    def test_target_projection_lock_derives_source_separation_and_hidden_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot_ref = "validation/_raw/ncbi_geo_batch_projection_locked.json"
            write_json(root, factory.REQUIREMENTS_REL, requirements())
            write_json(root, snapshot_ref, ncbi_batch_snapshot_without_source_separation(row_count=20))

            unlocked = factory.build_payload(root, snapshot_refs=[snapshot_ref])
            self.assertFalse(unlocked["report"]["grand_toe_support_allowed"])
            self.assertIn("TARGET_PROJECTION_LOCK_REQUIRED", unlocked["report"]["blockers"])

            write_target_projection_lock_bundle(root, unlocked["tasks"]["rows"])
            payload = factory.build_payload(root, snapshot_refs=[snapshot_ref])
            report = payload["report"]
            pack = payload["candidate_pack"]

            self.assertTrue(report["target_projection_lock"]["source_separation_derived"])
            self.assertTrue(report["target_projection_lock"]["valid"])
            self.assertTrue(pack["source_separation"]["target_hidden_until_scoring"])
            self.assertEqual(pack["source_separation"]["mode"], "target_blind")
            refs = factory.target_projection_refs()
            self.assertEqual(pack["source_separation"]["training_sources"], [refs["visible_lock_ref"]])
            self.assertEqual(pack["source_separation"]["target_sources"], [refs["target_lock_ref"]])
            self.assertTrue(all(row["declared_before_scoring_lock"] for row in payload["tasks"]["rows"]))
            self.assertNotIn("TARGET_HIDDEN_UNTIL_SCORING_REQUIRED", report["blockers"])
            self.assertNotIn("TARGET_PROJECTION_LOCK_REQUIRED", report["blockers"])
            self.assertFalse(report["grand_toe_support_allowed"])
            self.assertIn(factory.PAGINATION_QA_BLOCKER, report["blockers"])

    def test_packet_attached_target_projection_lock_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot_ref = "validation/_raw/ncbi_geo_batch_packet_projection_locked.json"
            packet_refs = {
                "declaration_ref": "validation/heldout/target_projection_locks/declarations/biology_ncbi_batch/test.json",
                "visible_lock_ref": "validation/heldout/target_projection_locks/locks/test.visible_projection_lock.json",
                "prediction_lock_ref": "validation/heldout/target_projection_locks/locks/test.prediction_materialization_lock.json",
                "target_lock_ref": "validation/heldout/target_projection_locks/locks/test.target_projection_lock.json",
            }
            write_json(root, factory.REQUIREMENTS_REL, requirements())
            write_json(root, snapshot_ref, ncbi_batch_snapshot_without_source_separation(row_count=20))

            unlocked = factory.build_payload(root, snapshot_refs=[snapshot_ref])
            self.assertIn("TARGET_PROJECTION_LOCK_REQUIRED", unlocked["report"]["blockers"])

            status = write_target_projection_lock_bundle(root, unlocked["tasks"]["rows"], refs=packet_refs)
            status["verified"] = False
            status["valid"] = False
            write_json(
                root,
                factory.ACQUISITION_REL,
                {
                    "schema_id": factory.ACQUISITION_SCHEMA_ID,
                    "source_acquisition_requests": [],
                    "target_projection_lock": status,
                    "no_send": True,
                },
            )

            payload = factory.build_payload(root, snapshot_refs=[snapshot_ref])
            blocker_text = " ".join(payload["report"]["blockers"])

            self.assertTrue(payload["report"]["target_projection_lock"]["valid"])
            self.assertEqual(payload["report"]["target_projection_lock"]["source_kind"], "packet_attachment")
            self.assertNotIn("TARGET_PROJECTION_LOCK_ARTIFACT_MISSING", blocker_text)
            self.assertNotIn("TARGET_PROJECTION_LOCK_REQUIRED", payload["report"]["blockers"])
            self.assertFalse(payload["report"]["grand_toe_support_allowed"])
            self.assertIn(factory.PAGINATION_QA_BLOCKER, payload["report"]["blockers"])

    def test_packet_acquisition_keyed_target_projection_lock_binds_to_observation_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot_ref = "validation/_raw/ncbi_geo_batch_packet_projection_acquisition_keyed.json"
            packet_refs = {
                "declaration_ref": "validation/heldout/target_projection_locks/declarations/biology_ncbi_batch/acquisition-keyed.json",
                "visible_lock_ref": "validation/heldout/target_projection_locks/locks/acquisition-keyed.visible_projection_lock.json",
                "prediction_lock_ref": "validation/heldout/target_projection_locks/locks/acquisition-keyed.prediction_materialization_lock.json",
                "target_lock_ref": "validation/heldout/target_projection_locks/locks/acquisition-keyed.target_projection_lock.json",
            }
            lock_snapshot_ref = "validation/heldout/target_projection_locks/snapshots/biology_ncbi_batch/acquisition-keyed.json"
            write_json(root, factory.REQUIREMENTS_REL, requirements())
            write_json(root, snapshot_ref, ncbi_batch_snapshot_without_source_separation(row_count=20))

            unlocked = factory.build_payload(root, snapshot_refs=[snapshot_ref])
            rows = unlocked["tasks"]["rows"]
            acquisition_ids = {
                row["observation_id"]: f"OC133-NCBI-GEO-OFFICIAL-SNAPSHOT-{index:04d}"
                for index, row in enumerate(rows, start=1)
            }
            status = write_target_projection_lock_bundle(
                root,
                rows,
                refs=packet_refs,
                row_id_for=lambda _index, row: acquisition_ids[row["observation_id"]],
                snapshot_ref=lock_snapshot_ref,
                snapshot_rows=[
                    normalized_projection_snapshot_row(row, acquisition_ids[row["observation_id"]])
                    for row in rows
                ],
            )
            write_json(
                root,
                factory.ACQUISITION_REL,
                {
                    "schema_id": factory.ACQUISITION_SCHEMA_ID,
                    "source_acquisition_requests": [],
                    "target_projection_lock": status,
                    "no_send": True,
                },
            )

            report = factory.build_payload(root, snapshot_refs=[snapshot_ref])["report"]

            blocker_text = " ".join(report["blockers"])
            self.assertTrue(report["target_projection_lock"]["valid"])
            self.assertNotIn("VISIBLE_PROJECTION_ROW_MISSING", blocker_text)
            self.assertNotIn("TARGET_PROJECTION_ROW_MISSING", blocker_text)
            self.assertNotIn("TARGET_PROJECTION_LOCK_REQUIRED", report["blockers"])

    def test_invalid_packet_attached_target_projection_lock_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot_ref = "validation/_raw/ncbi_geo_batch_packet_projection_tampered.json"
            packet_refs = {
                "declaration_ref": "validation/heldout/target_projection_locks/declarations/biology_ncbi_batch/tampered.json",
                "visible_lock_ref": "validation/heldout/target_projection_locks/locks/tampered.visible_projection_lock.json",
                "prediction_lock_ref": "validation/heldout/target_projection_locks/locks/tampered.prediction_materialization_lock.json",
                "target_lock_ref": "validation/heldout/target_projection_locks/locks/tampered.target_projection_lock.json",
            }
            write_json(root, factory.REQUIREMENTS_REL, requirements())
            write_json(root, snapshot_ref, ncbi_batch_snapshot_without_source_separation(row_count=20))
            unlocked = factory.build_payload(root, snapshot_refs=[snapshot_ref])
            status = write_target_projection_lock_bundle(root, unlocked["tasks"]["rows"], refs=packet_refs)
            status["hashes"]["target_projection_lock_sha256"] = "0" * 64
            write_json(
                root,
                factory.ACQUISITION_REL,
                {
                    "schema_id": factory.ACQUISITION_SCHEMA_ID,
                    "source_acquisition_requests": [],
                    "target_projection_lock": status,
                    "no_send": True,
                },
            )

            report = factory.build_payload(root, snapshot_refs=[snapshot_ref])["report"]

            self.assertFalse(report["grand_toe_support_allowed"])
            self.assertFalse(report["target_projection_lock"]["valid"])
            self.assertIn("TARGET_PROJECTION_LOCK_PACKET_HASH_MISMATCH::target_projection_lock_sha256", report["blockers"])
            self.assertIn("TARGET_PROJECTION_LOCK_REQUIRED", report["blockers"])

    def test_packet_attached_target_projection_lock_with_weak_no_send_locks_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot_ref = "validation/_raw/ncbi_geo_batch_packet_projection_weak_locks.json"
            packet_refs = {
                "declaration_ref": "validation/heldout/target_projection_locks/declarations/biology_ncbi_batch/weak-locks.json",
                "visible_lock_ref": "validation/heldout/target_projection_locks/locks/weak-locks.visible_projection_lock.json",
                "prediction_lock_ref": "validation/heldout/target_projection_locks/locks/weak-locks.prediction_materialization_lock.json",
                "target_lock_ref": "validation/heldout/target_projection_locks/locks/weak-locks.target_projection_lock.json",
            }
            write_json(root, factory.REQUIREMENTS_REL, requirements())
            write_json(root, snapshot_ref, ncbi_batch_snapshot_without_source_separation(row_count=20))
            unlocked = factory.build_payload(root, snapshot_refs=[snapshot_ref])
            status = write_target_projection_lock_bundle(root, unlocked["tasks"]["rows"], refs=packet_refs)
            status["locks"] = {**factory.PROJECTION_NO_SEND_LOCKS, "publish_allowed": True}
            write_json(
                root,
                factory.ACQUISITION_REL,
                {
                    "schema_id": factory.ACQUISITION_SCHEMA_ID,
                    "source_acquisition_requests": [],
                    "target_projection_lock": status,
                    "no_send": True,
                },
            )

            report = factory.build_payload(root, snapshot_refs=[snapshot_ref])["report"]

            self.assertFalse(report["target_projection_lock"]["valid"])
            self.assertIn("TARGET_PROJECTION_LOCK_PACKET_NO_SEND_LOCKS_MISSING_OR_WEAK", report["blockers"])
            self.assertIn("TARGET_PROJECTION_LOCK_REQUIRED", report["blockers"])

    def test_target_projection_lock_wrong_field_tamper_keeps_pack_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot_ref = "validation/_raw/ncbi_geo_batch_wrong_projection_lock.json"
            write_json(root, factory.REQUIREMENTS_REL, requirements())
            write_json(root, snapshot_ref, ncbi_batch_snapshot_without_source_separation(row_count=20))

            unlocked = factory.build_payload(root, snapshot_refs=[snapshot_ref])
            write_target_projection_lock_bundle(
                root,
                unlocked["tasks"]["rows"],
                visible_fields=[*factory.BIOLOGY_VISIBLE_FIELDS, "esearchresult.retmax"],
            )
            report = factory.build_payload(root, snapshot_refs=[snapshot_ref])["report"]

            self.assertFalse(report["grand_toe_support_allowed"])
            self.assertFalse(report["target_projection_lock"]["valid"])
            self.assertIn("TARGET_PROJECTION_LOCK_VISIBLE_FIELDS_UNEXPECTED", report["blockers"])
            self.assertIn("TARGET_FIELD_IN_VISIBLE_PROJECTION::esearchresult.retmax", report["blockers"])
            self.assertIn("TARGET_PROJECTION_LOCK_REQUIRED", report["blockers"])

    def test_target_projection_artifact_existence_alone_does_not_close_lock(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot_ref = "validation/_raw/ncbi_geo_batch_empty_projection_lock.json"
            write_json(root, factory.REQUIREMENTS_REL, requirements())
            write_json(root, snapshot_ref, ncbi_batch_snapshot_without_source_separation(row_count=20))
            refs = factory.target_projection_refs()
            for rel_path in (
                refs["declaration_ref"],
                refs["visible_lock_ref"],
                refs["prediction_lock_ref"],
                refs["target_lock_ref"],
            ):
                write_json(root, rel_path, {})

            report = factory.build_payload(root, snapshot_refs=[snapshot_ref])["report"]

            self.assertFalse(report["grand_toe_support_allowed"])
            self.assertFalse(report["target_projection_lock"]["valid"])
            self.assertFalse(report["target_projection_lock"]["source_separation_derived"])
            self.assertIn("TARGET_PROJECTION_LOCK_ID_MISMATCH", report["blockers"])
            self.assertIn("TARGET_PROJECTION_LOCK_REQUIRED", report["blockers"])

    def test_missing_seed_lock_metadata_auto_upgrades_default_seed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(root, factory.REQUIREMENTS_REL, requirements(minimum_n=1))
            write_json(root, factory.DEFAULT_SNAPSHOT_REF, legacy_seed_snapshot())

            payload = factory.write_outputs(root, snapshot_refs=[factory.DEFAULT_SNAPSHOT_REF])
            report = payload["report"]
            row = payload["tasks"]["rows"][0]

            self.assertEqual(factory.check_stored(root, snapshot_refs=[factory.DEFAULT_SNAPSHOT_REF]), [])
            self.assertFalse(report["grand_toe_support_allowed"])
            self.assertIn(factory.PAGINATION_QA_BLOCKER, report["blockers"])
            self.assertEqual(report["target_projection_lock"]["source_kind"], "legacy_seed_auto_projection")
            self.assertTrue(row["legacy_seed_upgrade"])
            self.assertTrue(row["target_projection_lock_verified"])
            self.assertTrue(row["lock_ref"].startswith(factory.LEGACY_SEED_LOCK_ROOT_REL))
            self.assertTrue((root / row["lock_ref"]).is_file())
            self.assertTrue(row["official_source_confirmed"])
            self.assertTrue(row["comparator_pre_registered"])

    def test_tampered_seed_lock_hash_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(root, factory.REQUIREMENTS_REL, requirements(minimum_n=1))
            write_json(root, factory.DEFAULT_SNAPSHOT_REF, legacy_seed_snapshot({"lock_sha256": "0" * 64}))

            payload = factory.build_payload(root, snapshot_refs=[factory.DEFAULT_SNAPSHOT_REF])
            report = payload["report"]
            row = payload["tasks"]["rows"][0]

            self.assertFalse(report["grand_toe_support_allowed"])
            self.assertFalse(row["target_projection_lock_verified"])
            self.assertIn("LEGACY_SEED_LOCK_HASH_MISMATCH", " ".join(report["blockers"]))
            self.assertIn("TARGET_PROJECTION_LOCK_REQUIRED", report["blockers"])

    def test_stale_legacy_seed_comparator_baseline_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(root, factory.REQUIREMENTS_REL, requirements(minimum_n=1))
            write_json(
                root,
                factory.DEFAULT_SNAPSHOT_REF,
                legacy_seed_snapshot({"comparator_baseline_sha256": "0" * 64}),
            )

            payload = factory.build_payload(root, snapshot_refs=[factory.DEFAULT_SNAPSHOT_REF])
            report = payload["report"]
            row = payload["tasks"]["rows"][0]

            self.assertFalse(report["grand_toe_support_allowed"])
            self.assertFalse(row["target_projection_lock_verified"])
            self.assertIn("LEGACY_SEED_COMPARATOR_BASELINE_STALE", " ".join(report["blockers"]))
            self.assertIn("COMPARATOR_BASELINE_NOT_PREREGISTERED", " ".join(report["blockers"]))

    def test_legacy_seed_visible_projection_target_leak_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(root, factory.REQUIREMENTS_REL, requirements(minimum_n=1))
            write_json(
                root,
                factory.DEFAULT_SNAPSHOT_REF,
                legacy_seed_snapshot({"visible_fields": [*factory.BIOLOGY_VISIBLE_FIELDS, "esearchresult.retmax"]}),
            )

            report = factory.build_payload(root, snapshot_refs=[factory.DEFAULT_SNAPSHOT_REF])["report"]

            blocker_text = " ".join(report["blockers"])
            self.assertFalse(report["grand_toe_support_allowed"])
            self.assertIn("LEGACY_SEED_VISIBLE_FIELDS_UNEXPECTED", blocker_text)
            self.assertIn("LEGACY_SEED_TARGET_FIELD_IN_VISIBLE_PROJECTION", blocker_text)
            self.assertIn("TARGET_PROJECTION_LOCK_REQUIRED", report["blockers"])


if __name__ == "__main__":
    raise SystemExit(unittest.main())
