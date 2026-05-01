from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tools import oc133_official_readonly_acquisition_runner as runner
from tools import oc133_physics_chemistry_official_batch_factory as factory
from validation.grand_science import evidence_pack_factory as grand_factory


REPO_ROOT = Path(__file__).resolve().parents[1]


def copy_fixture(root: Path, rel_path: str) -> None:
    source = REPO_ROOT / rel_path
    target = root / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def copy_required_inputs(root: Path) -> None:
    for rel_path in (
        factory.REQUIREMENTS_REL,
        factory.MANIFEST_REL,
        factory.PHYSICS_NIST_CONSTANTS_REF,
        factory.CHEMISTRY_PUBCHEM_WATER_REF,
        factory.CHEMISTRY_NIST_WEBBOOK_WATER_REF,
    ):
        copy_fixture(root, rel_path)


def target_blind_source(rows: list[dict]) -> dict:
    return {
        "mode": "target_blind",
        "pre_target_lock": True,
        "target_hidden_until_scoring": True,
        "declared_before_scoring": True,
        "visible_target_projection_declared": True,
        "visible_projection_ids": [
            str(row["visible_projection"]["projection_id"])
            for row in rows
            if isinstance(row.get("visible_projection"), dict)
        ],
        "target_projection_ids": [
            str(row["target_projection"]["projection_id"])
            for row in rows
            if isinstance(row.get("target_projection"), dict)
        ],
        "strict_source_separation_attested": False,
        "attestation_ref": "",
        "training_sources": [str(row["training_source"]) for row in rows],
        "target_sources": [str(row["target_source"]) for row in rows],
    }


def machine_verified_target_blind_source(rows: list[dict]) -> dict:
    source = target_blind_source(rows)
    source.update(
        {
            "strict_source_separation_attested": True,
            "attestation_ref": "machine_checkable_source_lock",
            "machine_checkable_source_lock": factory.build_physics_machine_source_lock(rows),
            "source_separation_class": "machine_verified_target_blind_source_lock",
        }
    )
    return source


def repo_has_physics_prospective_acquisition() -> bool:
    acquisition, failures = factory.successful_physics_codata_acquisition(REPO_ROOT)
    return acquisition is not None and not failures


def evaluate_physics_rows_with_current_requirements(rows: list[dict], source: dict) -> dict:
    requirements, requirement_blockers = factory.load_requirements(REPO_ROOT)
    return factory.evaluate_domain(
        "physics",
        rows,
        source,
        requirement_blockers,
        requirements,
        factory.PHYSICS_PACK_REL,
    )


class PhysicsChemistryOfficialBatchFactoryTests(unittest.TestCase):
    def test_current_repo_builds_blocked_acquisition_ready_packet(self) -> None:
        payload = factory.build_payload(REPO_ROOT)
        report = payload["report"]
        tasks = payload["tasks"]
        has_physics_acquisition = repo_has_physics_prospective_acquisition()

        self.assertEqual(report["verdict"], "BLOCKED_ACQUISITION_READY_NO_SEND")
        self.assertFalse(report["grand_toe_support_allowed"])
        self.assertTrue(report["no_send"])
        self.assertFalse(report["publish_allowed"])
        self.assertFalse(report["registry_integration_allowed"])

        by_domain = {row["domain"]: row for row in report["domains"]}
        self.assertEqual(set(by_domain), {"physics", "chemistry"})
        self.assertGreaterEqual(by_domain["physics"]["candidate_n"], 20)
        self.assertEqual(
            by_domain["physics"]["grand_eligible_n"],
            by_domain["physics"]["candidate_n"] if has_physics_acquisition else 0,
        )
        self.assertEqual(by_domain["physics"]["missing_n"], 0)
        self.assertEqual(by_domain["chemistry"]["candidate_n"], 12)
        self.assertEqual(by_domain["chemistry"]["missing_n"], 8)
        self.assertEqual(by_domain["chemistry"]["grand_eligible_n"], 0)

        blocker_text = " ".join(report["blockers"])
        if not has_physics_acquisition:
            self.assertIn("SOURCE_SEPARATION_MODE_NOT_ALLOWED::official_snapshot_replay", blocker_text)
            self.assertIn("PRE_TARGET_LOCK_REQUIRED", blocker_text)
            self.assertIn("TARGET_HIDDEN_UNTIL_SCORING_REQUIRED", blocker_text)
            self.assertIn("SOURCE_SEPARATION_ATTESTATION_REQUIRED", blocker_text)
        self.assertIn("N_BELOW_MINIMUM::chemistry::12/20", blocker_text)

        self.assertTrue(all(row["sha256_match"] for row in report["snapshot_records"]))
        physics_rows = tasks["domains"][0]["rows"]
        chemistry_rows = tasks["domains"][1]["rows"]
        self.assertTrue(all(row["row_hash"] for row in physics_rows[:5]))
        self.assertTrue(all(row["negative_control_rejected"] for row in physics_rows))
        self.assertTrue(all(row["negative_control_rejected"] for row in chemistry_rows))

        missing_ids = {
            item["source_id"]
            for row in report["domains"]
            for item in row["missing_official_snapshots"]
        }
        if not has_physics_acquisition:
            self.assertIn("physics_nist_constants_pre_target_lock_manifest_v1", missing_ids)
        self.assertIn("physics_nist_asd_hydrogen_balmer_lines_v1", missing_ids)
        self.assertIn("chemistry_pubchem_20_compound_properties_v1", missing_ids)
        self.assertIn("chemistry_nist_webbook_water_gas_thermo_v1", missing_ids)

    def test_candidate_packs_remain_invalid_under_grand_gate(self) -> None:
        payload = factory.build_payload(REPO_ROOT)
        requirements, _ = factory.load_requirements(REPO_ROOT)

        physics_pack = payload[factory.PHYSICS_PACK_REL]
        chemistry_pack = payload[factory.CHEMISTRY_PACK_REL]

        has_physics_acquisition = repo_has_physics_prospective_acquisition()
        self.assertEqual(physics_pack["grand_toe_support_allowed"], has_physics_acquisition)
        self.assertFalse(chemistry_pack["grand_toe_support_allowed"])
        physics_failures = grand_factory.pack_failure_reasons(physics_pack, requirements)
        chemistry_failures = grand_factory.pack_failure_reasons(chemistry_pack, requirements)

        if has_physics_acquisition:
            self.assertEqual(physics_failures, [])
        else:
            self.assertIn("SOURCE_SEPARATION_MODE_NOT_ALLOWED", physics_failures)
            self.assertIn("PRE_TARGET_LOCK_REQUIRED", physics_failures)
            self.assertIn("TARGET_HIDDEN_UNTIL_SCORING_REQUIRED", physics_failures)
            self.assertIn("GRAND_TOE_SUPPORT_NOT_ALLOWED", physics_failures)
        self.assertIn("N_BELOW_MINIMUM::20", chemistry_failures)
        self.assertIn("GRAND_TOE_SUPPORT_NOT_ALLOWED", chemistry_failures)

    def test_missing_physics_prospective_lock_blocks_rows_and_support(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_required_inputs(root)

            payload = factory.build_payload(root)
            physics_domain = {
                row["domain"]: row for row in payload["report"]["domains"]
            }["physics"]

            self.assertFalse(physics_domain["grand_toe_support_allowed"])
            self.assertFalse(payload[factory.PHYSICS_PACK_REL]["grand_toe_support_allowed"])
            self.assertEqual(physics_domain["grand_eligible_n"], 0)
            self.assertIn("PRE_TARGET_LOCK_REQUIRED", physics_domain["blockers"])
            self.assertIn(
                "PHYSICS_ROW_SOURCE_SNAPSHOT_PRE_TARGET_LOCK_MISSING::PHYS-CODATA-001",
                physics_domain["blockers"],
            )

    def test_valid_physics_lock_and_same_target_comparator_passes_physics_gate(self) -> None:
        payload = factory.build_payload(REPO_ROOT)
        physics_domain = {
            row["domain"]: row for row in payload["report"]["domains"]
        }["physics"]
        physics_pack = payload[factory.PHYSICS_PACK_REL]

        self.assertTrue(repo_has_physics_prospective_acquisition())
        self.assertTrue(physics_domain["grand_toe_support_allowed"])
        self.assertEqual(physics_domain["blockers"], [])
        self.assertTrue(physics_pack["grand_toe_support_allowed"])
        self.assertEqual(physics_pack["comparator_baseline"]["kind"], "same_target_formula_ablation")
        self.assertNotIn("null", json.dumps(physics_pack).lower())
        self.assertNotIn("wrong-field", json.dumps(physics_pack).lower())

    def test_stale_physics_policy_contradiction_blocks_support(self) -> None:
        payload = factory.build_payload(REPO_ROOT)
        rows = json.loads(json.dumps(payload["tasks"]["domains"][0]["rows"]))
        rows[0]["grand_scope"] = (
            "official snapshot consistency task; not independently pre-target locked in the current repo"
        )
        rows[0]["row_hash"] = factory.row_hash(rows[0])
        acquisition, failures = factory.successful_physics_codata_acquisition(REPO_ROOT)
        self.assertEqual(failures, [])
        source = factory.prospective_physics_source_separation(rows, acquisition)

        physics_eval = evaluate_physics_rows_with_current_requirements(rows, source)

        self.assertFalse(physics_eval["grand_toe_support_allowed"])
        self.assertIn(
            "PHYSICS_STALE_SOURCE_SEPARATION_POLICY_TEXT::PHYS-CODATA-001",
            physics_eval["blockers"],
        )

    def test_null_physics_comparator_blocks_support(self) -> None:
        payload = factory.build_payload(REPO_ROOT)
        rows = json.loads(json.dumps(payload["tasks"]["domains"][0]["rows"]))
        rows[0]["comparator"]["kind"] = "null_baseline"
        rows[0]["comparator"]["name"] = "zero-value null baseline"
        rows[0]["comparator"]["prediction_rule"] = "predict numeric zero for the target"
        rows[0]["comparator"]["prediction_value"] = 0.0
        rows[0]["preregistration"]["comparator"] = rows[0]["comparator"]
        rows[0]["comparator_baseline"] = rows[0]["comparator"]["name"]
        rows[0]["comparator_prediction"] = 0.0
        rows[0]["comparator_residual"] = abs(rows[0]["observed_value"])
        rows[0]["comparator_residual_score"] = factory.residual_score(
            rows[0]["comparator_residual"],
            rows[0]["uncertainty"],
        )
        rows[0]["negative_control_description"] = (
            "replace the derived CODATA relation with a zero-value null baseline and require a larger residual"
        )
        rows[0]["row_hash"] = factory.row_hash(rows[0])
        acquisition, failures = factory.successful_physics_codata_acquisition(REPO_ROOT)
        self.assertEqual(failures, [])
        source = factory.prospective_physics_source_separation(rows, acquisition)

        physics_eval = evaluate_physics_rows_with_current_requirements(rows, source)

        self.assertFalse(physics_eval["grand_toe_support_allowed"])
        self.assertIn(
            "PHYSICS_COMPARATOR_NULL_OR_ZERO_BASELINE::PHYS-CODATA-001",
            physics_eval["blockers"],
        )
        self.assertIn(
            "PHYSICS_COMPARATOR_NULL_OR_WRONG_FIELD_TEXT::PHYS-CODATA-001",
            physics_eval["blockers"],
        )

    def test_target_blind_shape_alone_does_not_fake_physics_promotion(self) -> None:
        base_payload = factory.build_payload(REPO_ROOT)
        physics_rows = base_payload["tasks"]["domains"][0]["rows"]
        chemistry_rows = base_payload["tasks"]["domains"][1]["rows"]
        payload = factory.build_payload(
            REPO_ROOT,
            source_separation_overrides={
                "physics": target_blind_source(physics_rows),
                "chemistry": target_blind_source(chemistry_rows),
            },
        )
        by_domain = {row["domain"]: row for row in payload["report"]["domains"]}

        self.assertFalse(by_domain["physics"]["grand_toe_support_allowed"])
        self.assertFalse(payload[factory.PHYSICS_PACK_REL]["grand_toe_support_allowed"])
        self.assertIn("SOURCE_SEPARATION_ATTESTATION_REQUIRED", by_domain["physics"]["blockers"])
        self.assertIn("PHYSICS_SOURCE_LOCK_ATTESTATION_MISSING", by_domain["physics"]["blockers"])
        self.assertIn("PHYSICS_SOURCE_LOCK_NOT_MACHINE_VERIFIED", by_domain["physics"]["blockers"])
        self.assertFalse(by_domain["chemistry"]["grand_toe_support_allowed"])
        self.assertFalse(payload["report"]["grand_toe_support_allowed"])
        self.assertIn("N_BELOW_MINIMUM::chemistry::12/20", by_domain["chemistry"]["blockers"])

    def test_physics_rows_declare_no_leakage_projection_and_preregistered_comparators(self) -> None:
        payload = factory.build_payload(REPO_ROOT)
        physics_rows = payload["tasks"]["domains"][0]["rows"]

        self.assertGreaterEqual(len(physics_rows), 20)
        self.assertTrue(all(test["passed"] for test in payload["tasks"]["tamper_tests"]))
        for row in physics_rows:
            with self.subTest(task_id=row["task_id"]):
                self.assertFalse(factory.visible_projection_has_target_leakage(row))
                visible_quantities = {
                    field["quantity"]
                    for field in row["visible_projection"]["visible_fields"]
                }
                self.assertNotIn(row["target_quantity"], visible_quantities)
                self.assertEqual(row["preregistration"]["residual_metric"]["metric_id"], factory.RESIDUAL_METRIC_ID)
                self.assertTrue(row["preregistration"]["comparator"]["pre_registered"])
                self.assertGreater(row["comparator_residual_score"], row["model_residual_score"])

        physics_pack = payload[factory.PHYSICS_PACK_REL]
        self.assertTrue(physics_pack["comparator_baseline"]["pre_registered"])
        self.assertEqual(physics_pack["uncertainty"]["metric"], factory.RESIDUAL_METRIC_ID)

    def test_physics_target_hidden_projection_lock_is_machine_checkable(self) -> None:
        payload = factory.build_payload(REPO_ROOT)
        physics_rows = payload["tasks"]["domains"][0]["rows"]
        has_physics_acquisition = repo_has_physics_prospective_acquisition()

        self.assertTrue(physics_rows)
        for row in physics_rows:
            with self.subTest(task_id=row["task_id"]):
                self.assertEqual(factory.physics_target_projection_lock_failures(row), [])
                self.assertTrue(row["target_projection_lock"]["target_projection_hidden_until_scoring"])
                self.assertTrue(row["target_projection_lock"]["prediction_materialized_before_target_projection"])
                self.assertTrue(row["projection_declaration"]["target_hidden_until_scoring"])
                self.assertEqual(
                    row["projection_declaration"]["source_snapshot_pre_target_lock"],
                    has_physics_acquisition,
                )
                self.assertEqual(
                    row["target_projection_lock"]["prediction_materialization_hash"],
                    row["prediction_materialization"]["prediction_hash"],
                )
                self.assertEqual(
                    row["target_projection_lock"]["target_projection_hash"],
                    row["target_projection"]["target_hash"],
                )
                self.assertFalse(
                    factory.payload_has_forbidden_key(
                        row["prediction_materialization"],
                        set(factory.PHYSICS_PREDICTION_FORBIDDEN_FIELDS),
                    )
                )

    def test_physics_projection_lock_tamper_controls_reject_changes(self) -> None:
        payload = factory.build_payload(REPO_ROOT)
        row = payload["tasks"]["domains"][0]["rows"][0]

        prediction_tamper = json.loads(json.dumps(row))
        prediction_tamper["prediction_materialization"]["predicted_value"] += 1.0
        self.assertIn(
            "PREDICTION_MATERIALIZATION_HASH_INVALID",
            factory.physics_target_projection_lock_failures(prediction_tamper),
        )

        target_tamper = json.loads(json.dumps(row))
        target_tamper["target_projection"]["target_fields"]["observed_value_text"] = "tampered"
        self.assertIn(
            "TARGET_PROJECTION_HASH_INVALID",
            factory.physics_target_projection_lock_failures(target_tamper),
        )

        visible_tamper = json.loads(json.dumps(row))
        visible_tamper["visible_projection"]["visible_fields"].append(
            {
                "quantity": row["target_quantity"],
                "observed_value": row["observed_value"],
            }
        )
        self.assertIn(
            "VISIBLE_PROJECTION_TARGET_LEAKAGE",
            factory.physics_target_projection_lock_failures(visible_tamper),
        )

        hidden_lock_tamper = json.loads(json.dumps(row))
        hidden_lock_tamper["target_projection_lock"]["target_projection_hidden_until_scoring"] = False
        self.assertIn(
            "TARGET_PROJECTION_NOT_HIDDEN_UNTIL_SCORING",
            factory.physics_target_projection_lock_failures(hidden_lock_tamper),
        )

    def test_physics_target_tampering_is_rejected_by_row_hash_and_check(self) -> None:
        payload = factory.build_payload(REPO_ROOT)
        physics_row = dict(payload["tasks"]["domains"][0]["rows"][0])
        physics_row["observed_value"] = physics_row["observed_value"] * 1.01
        self.assertFalse(factory.row_hash_valid(physics_row))

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_required_inputs(root)
            factory.write_outputs(root)

            tasks_path = root / factory.TASKS_REL
            tasks_payload = factory.read_json(tasks_path)
            tasks_payload["domains"][0]["rows"][0]["observed_value"] *= 1.01
            factory.write_json(tasks_path, tasks_payload)

            failures = factory.check_stored(root)
            self.assertIn(f"mismatch::{factory.TASKS_REL}", failures)

    def test_artifact_exists_attestation_does_not_close_physics_source_lock(self) -> None:
        base_payload = factory.build_payload(REPO_ROOT)
        physics_rows = base_payload["tasks"]["domains"][0]["rows"]
        source = target_blind_source(physics_rows)
        source.update(
            {
                "strict_source_separation_attested": True,
                "attestation_ref": factory.TASKS_REL,
                "source_lock_artifact_exists": True,
                "machine_checkable_source_lock": {
                    "verification_status": "passed",
                    "verification_method": "artifact_exists",
                    "artifact_exists_closes_lock": True,
                },
            }
        )

        payload = factory.build_payload(
            REPO_ROOT,
            source_separation_overrides={"physics": source},
        )
        physics_domain = {
            row["domain"]: row for row in payload["report"]["domains"]
        }["physics"]

        self.assertFalse(physics_domain["grand_toe_support_allowed"])
        self.assertFalse(payload[factory.PHYSICS_PACK_REL]["grand_toe_support_allowed"])
        self.assertIn("PHYSICS_SOURCE_LOCK_NOT_MACHINE_VERIFIED", physics_domain["blockers"])
        self.assertIn("PHYSICS_NO_ARTIFACT_EXISTS_CLOSURE", physics_domain["blockers"])
        self.assertIn("PHYSICS_SOURCE_LOCK_STATUS_TOKEN_NOT_ACCEPTED", physics_domain["blockers"])

    def test_physics_source_lock_accepts_machine_verifiable_hash_order_attestation(self) -> None:
        payload = factory.build_payload(REPO_ROOT)
        physics_rows = payload["tasks"]["domains"][0]["rows"]
        source = machine_verified_target_blind_source(physics_rows)

        self.assertEqual(factory.physics_source_lock_failures(source, physics_rows), [])

        physics_payload = factory.build_payload(
            REPO_ROOT,
            source_separation_overrides={"physics": source},
        )
        physics_domain = {
            row["domain"]: row for row in physics_payload["report"]["domains"]
        }["physics"]
        self.assertNotIn("PHYSICS_SOURCE_LOCK_NOT_MACHINE_VERIFIED", physics_domain["blockers"])
        self.assertNotIn("PHYSICS_SOURCE_LOCK_ATTESTATION_MISSING", physics_domain["blockers"])
        self.assertFalse(physics_payload["report"]["grand_toe_support_allowed"])

    def test_physics_source_lock_stale_and_provenance_mismatch_fail_closed(self) -> None:
        payload = factory.build_payload(REPO_ROOT)
        physics_rows = payload["tasks"]["domains"][0]["rows"]
        source = machine_verified_target_blind_source(physics_rows)
        lock = source["machine_checkable_source_lock"]
        lock["source_snapshot"]["sha256"] = "0" * 64
        lock["order_records"][0]["timestamp"] = "2026-04-28T00:06:00Z"
        lock["source_lock_hash"] = factory.sha256_object(
            {key: value for key, value in lock.items() if key != "source_lock_hash"}
        )

        failures = factory.physics_source_lock_failures(source, physics_rows)

        self.assertIn("PHYSICS_SOURCE_LOCK_SOURCE_SHA256_MISMATCH", failures)
        self.assertIn(
            "PHYSICS_SOURCE_LOCK_ORDER_NOT_PRECEDENT::source_snapshot_locked->source_separation_declared",
            failures,
        )
        self.assertIn("PHYSICS_SOURCE_LOCK_NOT_PRE_TARGET", failures)
        self.assertIn("PHYSICS_SOURCE_LOCK_NOT_MACHINE_VERIFIED", failures)

    def test_physics_source_lock_target_leak_fails_closed(self) -> None:
        payload = factory.build_payload(REPO_ROOT)
        physics_rows = json.loads(json.dumps(payload["tasks"]["domains"][0]["rows"]))
        source = machine_verified_target_blind_source(physics_rows)
        physics_rows[0]["visible_projection"]["visible_fields"].append(
            {
                "quantity": physics_rows[0]["target_quantity"],
                "observed_value": physics_rows[0]["observed_value"],
            }
        )

        failures = factory.physics_source_lock_failures(source, physics_rows)

        self.assertIn("PHYSICS_SOURCE_LOCK_TARGET_LEAKAGE", failures)
        self.assertIn("PHYSICS_SOURCE_LOCK_NOT_MACHINE_VERIFIED", failures)

    def test_physics_source_lock_post_scoring_order_fails_closed(self) -> None:
        payload = factory.build_payload(REPO_ROOT)
        physics_rows = payload["tasks"]["domains"][0]["rows"]
        source = target_blind_source(physics_rows)
        source.update(
            {
                "strict_source_separation_attested": True,
                "attestation_ref": "machine_checkable_source_lock",
                "machine_checkable_source_lock": factory.build_physics_machine_source_lock(
                    physics_rows,
                    target_projection_unsealed_at="2026-04-28T00:06:00Z",
                    scoring_started_at="2026-04-28T00:05:00Z",
                ),
            }
        )

        failures = factory.physics_source_lock_failures(source, physics_rows)

        self.assertIn(
            "PHYSICS_SOURCE_LOCK_ORDER_NOT_PRECEDENT::target_projection_unsealed_for_scoring->scoring_started",
            failures,
        )
        self.assertIn("PHYSICS_SOURCE_LOCK_TARGET_UNSEALED_AFTER_SCORING", failures)
        self.assertIn("PHYSICS_SOURCE_LOCK_NOT_MACHINE_VERIFIED", failures)

    def test_physics_acquisition_packet_is_runner_readable_no_send_request(self) -> None:
        payload = factory.build_payload(REPO_ROOT)
        packet = payload[factory.PHYSICS_ACQUISITION_PACKET_REL]
        has_physics_acquisition = repo_has_physics_prospective_acquisition()

        self.assertFalse(packet["grand_toe_support_allowed"])
        self.assertTrue(packet["no_send"])
        self.assertGreaterEqual(packet["candidate_n"], 20)
        self.assertEqual(packet["request_total"], len(packet["exact_acquisition_requests"]))
        self.assertEqual(packet["missing_official_snapshot_total"], len(packet["missing_official_snapshots"]))
        self.assertEqual(packet["codata_prospective_lock_satisfied"], has_physics_acquisition)
        if has_physics_acquisition:
            self.assertEqual(packet["status"], "PARTIAL_ACQUISITION_REQUIRED")
            self.assertIn("snapshot_sha256", packet["codata_prospective_lock_evidence"])
            self.assertIn("lock_sha256", packet["codata_prospective_lock_evidence"])
            self.assertIn("order_record_sha256", packet["codata_prospective_lock_evidence"])
        else:
            self.assertEqual(packet["status"], "ACQUISITION_REQUIRED")
        self.assertEqual(runner.packet_acquisition_rows(packet), packet["missing_official_snapshots"])
        self.assertEqual(runner.packet_acquisition_rows(packet), packet["exact_acquisition_requests"])
        self.assertIn("automated_prospective_protocol", packet)
        self.assertIn(
            "grand_toe_support_allowed remains false unless the strict grand gate has no failures",
            packet["automated_prospective_protocol"]["acceptance_gates"],
        )
        for row in packet["missing_official_snapshots"]:
            self.assertIn("acquisition_id", row)
            self.assertIn("official_endpoint_url", row)
            self.assertIn("expected_local_snapshot_ref", row)
            self.assertTrue(row["no_send_lock"])
            self.assertIn("prospective_lock_metadata", row)
            self.assertEqual(factory.physics_prospective_lock_metadata_failures(row), [])
            self.assertEqual(
                runner.prospective_lock_metadata_blockers(row, require_execution_metadata=True),
                [],
            )
        acquisition_ids = {row["acquisition_id"] for row in packet["missing_official_snapshots"]}
        if has_physics_acquisition:
            self.assertNotIn("OC133-PHYSICS-CODATA-PROSPECTIVE-ALLASCII-001", acquisition_ids)
        else:
            self.assertIn("OC133-PHYSICS-CODATA-PROSPECTIVE-ALLASCII-001", acquisition_ids)
        self.assertIn("OC133-PHYSICS-NIST-ASD-HYDROGEN-BALMER-001", acquisition_ids)

    def test_physics_acquisition_metadata_is_deterministic_target_hidden_and_order_hashed(self) -> None:
        payload = factory.build_payload(REPO_ROOT)
        packet = payload[factory.PHYSICS_ACQUISITION_PACKET_REL]

        for row in packet["missing_official_snapshots"]:
            with self.subTest(acquisition_id=row["acquisition_id"]):
                metadata = row["prospective_lock_metadata"]
                expected = factory.build_physics_prospective_lock_metadata(row)
                self.assertEqual(metadata, expected)
                self.assertEqual(metadata["schema_id"], factory.PROSPECTIVE_LOCK_METADATA_SCHEMA_ID)
                self.assertEqual(
                    metadata["request_visible_fields_hash"],
                    factory.sha256_object(factory.prospective_metadata_visible_request_fields(row)),
                )
                self.assertEqual(metadata["order_hash"], metadata["prospective_order_hash"])
                self.assertEqual(
                    metadata["prospective_order_hash"],
                    metadata["prospective_order_proof"]["order_hash"],
                )
                self.assertFalse(factory.payload_has_prospective_metadata_target_value(metadata))
                self.assertFalse(metadata["target_value_leak_check"]["target_values_present"])
                self.assertTrue(metadata["no_send_locks"]["no_send"])
                self.assertFalse(metadata["no_send_locks"]["publish_allowed"])

    def test_physics_acquisition_metadata_missing_stale_post_scoring_and_target_leaking_fail(self) -> None:
        payload = factory.build_payload(REPO_ROOT)
        row = json.loads(json.dumps(payload[factory.PHYSICS_ACQUISITION_PACKET_REL]["missing_official_snapshots"][0]))

        missing = json.loads(json.dumps(row))
        missing.pop("prospective_lock_metadata")
        self.assertIn("PROSPECTIVE_LOCK_METADATA_MISSING", factory.physics_prospective_lock_metadata_failures(missing))
        self.assertIn(
            "PROSPECTIVE_LOCK_METADATA_MISSING",
            runner.prospective_lock_metadata_blockers(missing, require_execution_metadata=True),
        )

        stale = json.loads(json.dumps(row))
        stale["current_official_batch_rows"] += 1
        self.assertIn("PROSPECTIVE_LOCK_METADATA_STALE", factory.physics_prospective_lock_metadata_failures(stale))

        stale_order = json.loads(json.dumps(row))
        stale_order["prospective_lock_metadata"]["prospective_order_proof"]["event_order"][0]["event"] = "scoring_started"
        self.assertIn(
            "PROSPECTIVE_LOCK_METADATA_ORDER_HASH_STALE",
            factory.physics_prospective_lock_metadata_failures(stale_order),
        )

        post_scoring = json.loads(json.dumps(row))
        post_scoring["prospective_lock_metadata"]["scoring_started"] = True
        post_scoring["prospective_lock_metadata"]["scoring_started_at"] = "2026-05-01T00:00:00Z"
        self.assertIn(
            "POST_SCORING_ACQUISITION_NOT_ALLOWED",
            factory.physics_prospective_lock_metadata_failures(post_scoring),
        )
        self.assertIn(
            "POST_SCORING_ACQUISITION_NOT_ALLOWED",
            runner.prospective_lock_metadata_blockers(post_scoring, require_execution_metadata=True),
        )

        target_leak = json.loads(json.dumps(row))
        target_leak["prospective_lock_metadata"]["request_visible_fields"]["observed_value"] = 656.281
        self.assertIn(
            "PROSPECTIVE_LOCK_METADATA_TARGET_VALUE_LEAKAGE",
            factory.physics_prospective_lock_metadata_failures(target_leak),
        )

    def test_physics_acquisition_packet_dry_run_allows_exact_nist_asd_request(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_required_inputs(root)
            factory.write_outputs(root)
            packet_path = root / factory.PHYSICS_ACQUISITION_PACKET_REL

            report = runner.build_report(root, [packet_path], execute_network=False)

            self.assertFalse(report["grand_toe_support_allowed"])
            self.assertEqual(report["request_total"], 2)
            self.assertEqual(report["validated_for_network_total"], 2)
            self.assertEqual(report["validation_blocked_total"], 0)
            self.assertEqual(report["execution_blocker_packet"]["status"], "CLEAR")
            self.assertNotIn("URL_NOT_IN_OFFICIAL_ALLOWLIST::physics.nist.gov/cgi-bin/ASD/lines1.pl", report["blockers"])
            self.assertNotIn("PROSPECTIVE_LOCK_METADATA_MISSING", report["execution_blocker_packet"]["remaining_execution_blockers"])
            by_id = {row["acquisition_id"]: row for row in report["records"]}
            self.assertTrue(by_id["OC133-PHYSICS-CODATA-PROSPECTIVE-ALLASCII-001"]["validated_for_network"])
            self.assertTrue(by_id["OC133-PHYSICS-NIST-ASD-HYDROGEN-BALMER-001"]["validated_for_network"])
            self.assertEqual(
                by_id["OC133-PHYSICS-NIST-ASD-HYDROGEN-BALMER-001"]["allowlist_rule"],
                "NIST ASD hydrogen Balmer lines TSV",
            )

    def test_physics_acquisition_packet_omits_codata_request_when_lock_is_satisfied(self) -> None:
        payload = factory.build_payload(REPO_ROOT)
        packet = payload[factory.PHYSICS_ACQUISITION_PACKET_REL]

        self.assertTrue(packet["codata_prospective_lock_satisfied"])
        self.assertEqual(packet["request_total"], 1)
        self.assertEqual(
            [row["acquisition_id"] for row in packet["missing_official_snapshots"]],
            ["OC133-PHYSICS-NIST-ASD-HYDROGEN-BALMER-001"],
        )

    def test_write_outputs_materializes_only_official_batch_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_required_inputs(root)

            report = factory.write_outputs(root)

            self.assertFalse(report["grand_toe_support_allowed"])
            for rel_path in (
                factory.PHYSICS_PACK_REL,
                factory.CHEMISTRY_PACK_REL,
                factory.PHYSICS_ACQUISITION_PACKET_REL,
                factory.TASKS_REL,
                factory.PROTOCOL_REL,
                factory.REPORT_REL,
                factory.README_REL,
            ):
                self.assertTrue((root / rel_path).is_file(), rel_path)
                self.assertTrue(rel_path.startswith(factory.OUTPUT_ROOT_REL) or rel_path.startswith("validation/heldout/grand_science/physics_chemistry/official_batch"))
            self.assertEqual(factory.check_stored(root), [])


if __name__ == "__main__":
    unittest.main()
