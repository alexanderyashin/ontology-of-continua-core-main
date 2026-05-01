from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools import oc133_logion_all_domain_readiness as readiness


def write_json(root: Path, rel_path: str, payload: dict[str, object]) -> None:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")


def minimal_blocked_audit() -> dict[str, object]:
    return {
        "schema_id": "OC133_ALL_DOMAIN_SCIENTIFIC_READINESS_AUDIT_v1",
        "mission_id": readiness.oc133_platinum.MISSION_ID,
        "release_id": readiness.oc133_platinum.RELEASE_ID,
        "version": readiness.oc133_platinum.VERSION,
        "state": "OC_CORE_1_3_3_ALL_DOMAIN_SCIENTIFIC_READINESS_RUNNING",
        "final_readiness_state": "SCIENTIFIC_BLOCKERS_REMAIN",
        "all_domain_ready_no_send": False,
        "blocker_total": 2,
        "blocker_ids": ["grand_toe_claim_ledger_evidence", "modern_science_comparator_superiority"],
        "checks": {
            "grand_toe_claim_ledger_evidence": {
                "state": "FAIL",
                "failed_gate_predicates": [
                    "dedicated_claim_row",
                    "promotion_theorem_ids_bound",
                    "modern_science_superiority_certified",
                ],
            },
            "modern_science_comparator_superiority": {
                "state": "FAIL",
                "missing_certified_domains": ["physics"],
            },
        },
        "work_orders": [],
        "work_order_total": 0,
        "work_order_queue_sha256": "",
        "next_automatic_action": "OWNER_REVIEW_NO_SEND",
        "no_send": True,
        "publish_allowed": False,
        "journal_submissions_allowed": False,
    }


def coverage_lane(
    work_order_id: str,
    domain: str,
    phenomenon: str,
    *,
    priority: str,
    rank: int,
) -> dict[str, object]:
    return {
        "queue_rank": rank,
        "dispatch_id": f"MS-COV-DISPATCH-{rank:03d}",
        "stable_id": f"{work_order_id}::{domain}::{phenomenon}",
        "work_order_id": work_order_id,
        "coverage_gap_id": f"MS-COV-GAP-{domain.upper()}-{phenomenon.upper()}",
        "priority": priority,
        "domain_class_id": domain,
        "phenomenon_class_id": phenomenon,
        "phenomenon_label": phenomenon.replace("_", " "),
        "lane_route": "EMPIRICAL_SOURCE_BACKED_BENCHMARK",
        "owner_capability": "Logion Test Evidence Capability",
        "resource_estimate": {"planning_points": 5, "expected_worker_roles": ["test owner"]},
        "dependencies": [{"dependency_id": "source_capsule_lock", "state": "OPEN"}],
        "expected_acceptance_predicates": ["STRICT_PACK_SCHEMA_PASS"],
        "coverage_closure": {"current_status": "OPEN", "mark_closed_allowed": False},
    }


class LogionAllDomainReadinessCliTests(unittest.TestCase):
    def test_enriched_dispatch_covers_lanes_and_broad_claim_predicates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(
                root,
                readiness.COVERAGE_LANE_QUEUE_REL,
                {
                    "schema_id": "OC133_MODERN_SCIENCE_COVERAGE_LANE_QUEUE_v1",
                    "queue_size": 2,
                    "open_lane_total": 2,
                    "lanes": [
                        coverage_lane("MS-COV-WO-010", "earth_space", "climate_weather", priority="P0", rank=1),
                        coverage_lane("MS-COV-WO-011", "earth_space", "hydrology", priority="P1", rank=2),
                    ],
                },
            )

            audit = readiness.enrich_readiness_dispatch(minimal_blocked_audit(), root)
            rows = audit["work_orders"]

            self.assertEqual(audit["work_order_total"], 5)
            self.assertEqual(audit["autonomous_dispatch"]["uncovered_phenomenon_class_work_order_total"], 2)
            self.assertEqual(audit["autonomous_dispatch"]["broad_claim_evidence_gap_work_order_total"], 3)
            self.assertEqual(
                {row["dispatch_class"] for row in rows},
                {"uncovered_phenomenon_class", "broad_claim_evidence_gap"},
            )
            self.assertEqual([row["queue_rank"] for row in rows], [1, 2, 3, 4, 5])
            self.assertEqual(rows, sorted(rows, key=readiness.work_order_sort_key))
            self.assertEqual(rows[0]["dispatch_class"], "uncovered_phenomenon_class")
            self.assertEqual(rows[0]["coverage_priority"], "P0")
            self.assertEqual(rows[2]["broad_claim_evidence_gap_id"], "modern_science_superiority_certified")

    def test_domain_local_coverage_artifacts_drive_counters_and_lane_priority(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(
                root,
                readiness.COVERAGE_LANE_QUEUE_REL,
                {
                    "schema_id": "OC133_MODERN_SCIENCE_COVERAGE_LANE_QUEUE_v1",
                    "queue_size": 2,
                    "open_lane_total": 2,
                    "lanes": [
                        coverage_lane("MS-COV-WO-099", "test_domain", "no_source_lane", priority="P0", rank=1),
                        coverage_lane("MS-COV-WO-100", "test_domain", "source_ready_lane", priority="P1", rank=2),
                    ],
                },
            )
            write_json(
                root,
                "validation/heldout/grand_science/test_domain/coverage_work_orders/raw/source_ready_snapshot.json",
                {"schema_id": "TEST_SOURCE_SNAPSHOT_v1"},
            )
            write_json(
                root,
                "validation/heldout/grand_science/test_domain/coverage_work_orders/OC133_TEST_COVERAGE_WORK_ORDERS.json",
                {
                    "schema_id": "OC133_TEST_COVERAGE_WORK_ORDERS_v1",
                    "coverage_closure_allowed": False,
                    "broad_modern_science_superiority_allowed": False,
                    "work_orders": [
                        {
                            "work_order_id": "MS-COV-WO-099",
                            "coverage_gap_id": "MS-COV-GAP-TEST_DOMAIN-NO_SOURCE_LANE",
                            "domain_class_id": "test_domain",
                            "phenomenon_class_id": "no_source_lane",
                            "phenomenon_label": "no source lane",
                            "lane_status": "OPEN_FAIL_CLOSED_NO_EXECUTABLE_EVIDENCE",
                            "coverage_closure_allowed": False,
                            "support_allowed_for_broad_coverage": False,
                            "current_evidence_status": {
                                "coverage_closure_allowed": False,
                                "executable_evidence_exists": False,
                            },
                        },
                        {
                            "work_order_id": "MS-COV-WO-100",
                            "coverage_gap_id": "MS-COV-GAP-TEST_DOMAIN-SOURCE_READY_LANE",
                            "domain_class_id": "test_domain",
                            "phenomenon_class_id": "source_ready_lane",
                            "phenomenon_label": "source ready lane",
                            "lane_status": "OPEN_FAIL_CLOSED_SOURCE_HASH_BOUND_STRICT_EVIDENCE_MISSING",
                            "coverage_closure_allowed": False,
                            "support_allowed_for_broad_coverage": False,
                            "current_evidence_status": {
                                "coverage_closure_allowed": False,
                                "source_snapshot_hash_bound": True,
                                "implemented_snapshot_ref": "validation/heldout/grand_science/test_domain/coverage_work_orders/raw/source_ready_snapshot.json",
                                "executable_evidence_exists": False,
                            },
                        },
                    ],
                },
            )

            audit = readiness.enrich_readiness_dispatch(minimal_blocked_audit(), root)
            dispatch = audit["autonomous_dispatch"]
            nearest = dispatch["nearest_to_closure"]

            self.assertEqual(dispatch["domain_local_coverage_artifact_total"], 2)
            self.assertEqual(dispatch["source_acquired_lane_total"], 1)
            self.assertEqual(dispatch["scorer_ready_lane_total"], 0)
            self.assertEqual(dispatch["strict_evidence_pack_total"], 0)
            self.assertEqual(dispatch["coverage_closed_total"], 0)
            self.assertEqual(nearest[0]["work_order_id"], "MS-COV-WO-100")
            self.assertLess(nearest[0]["missing_predicate_count"], nearest[1]["missing_predicate_count"])
            self.assertEqual(audit["work_orders"][0]["source_work_order_id"], "MS-COV-WO-100")
            self.assertFalse(audit["work_orders"][0]["closure_control"]["domain_local_coverage_closed"])

    def test_domain_local_scorer_ready_pack_counts_without_closure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(
                root,
                readiness.COVERAGE_LANE_QUEUE_REL,
                {
                    "schema_id": "OC133_MODERN_SCIENCE_COVERAGE_LANE_QUEUE_v1",
                    "queue_size": 1,
                    "open_lane_total": 1,
                    "lanes": [
                        coverage_lane("MS-COV-WO-101", "test_domain", "scorer_ready_lane", priority="P0", rank=1)
                    ],
                },
            )
            write_json(
                root,
                "validation/heldout/grand_science/test_domain/coverage_work_orders/raw/scorer_ready_snapshot.json",
                {"schema_id": "TEST_SOURCE_SNAPSHOT_v1"},
            )
            write_json(
                root,
                "validation/heldout/grand_science/test_domain/coverage_work_orders/SCORER_READY_PACK.json",
                {
                    "schema_id": "TEST_SCORER_READY_PACK_v1",
                    "target_work_order_id": "MS-COV-WO-101",
                    "source_snapshot_hash_bound": True,
                    "target_hidden_scorer_present": True,
                    "comparator_scores_present": True,
                    "negative_control_rejected": True,
                    "strict_evidence_pack_present": True,
                    "replay_sha256": "abc123",
                    "coverage_closure_allowed": False,
                },
            )
            write_json(
                root,
                "validation/heldout/grand_science/test_domain/coverage_work_orders/OC133_TEST_COVERAGE_WORK_ORDERS.json",
                {
                    "schema_id": "OC133_TEST_COVERAGE_WORK_ORDERS_v1",
                    "coverage_closure_allowed": False,
                    "broad_modern_science_superiority_allowed": False,
                    "work_orders": [
                        {
                            "work_order_id": "MS-COV-WO-101",
                            "coverage_gap_id": "MS-COV-GAP-TEST_DOMAIN-SCORER_READY_LANE",
                            "domain_class_id": "test_domain",
                            "phenomenon_class_id": "scorer_ready_lane",
                            "phenomenon_label": "scorer ready lane",
                            "lane_status": "OPEN_FAIL_CLOSED_SCORER_READY_STRICT_EVIDENCE_PACK_NO_COVERAGE_CLOSURE",
                            "coverage_closure_allowed": False,
                            "support_allowed_for_broad_coverage": False,
                            "current_evidence_status": {
                                "coverage_closure_allowed": False,
                                "source_snapshot_hash_bound": True,
                                "target_hidden_scorer_present": True,
                                "executable_evidence_exists": True,
                                "implemented_snapshot_ref": "validation/heldout/grand_science/test_domain/coverage_work_orders/raw/scorer_ready_snapshot.json",
                            },
                        }
                    ],
                },
            )

            audit = readiness.enrich_readiness_dispatch(minimal_blocked_audit(), root)
            dispatch = audit["autonomous_dispatch"]
            lane = dispatch["nearest_to_closure"][0]

            self.assertEqual(dispatch["source_acquired_lane_total"], 1)
            self.assertEqual(dispatch["scorer_ready_lane_total"], 1)
            self.assertEqual(dispatch["strict_evidence_pack_total"], 1)
            self.assertEqual(dispatch["coverage_closed_total"], 0)
            self.assertFalse(lane["coverage_closed"])
            self.assertIn("COVERAGE_REVIEWED_OR_CLOSED", lane["missing_predicates"])

    def test_each_enriched_work_order_has_dispatch_contract_and_keeps_closure_locked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(
                root,
                readiness.COVERAGE_LANE_QUEUE_REL,
                {
                    "schema_id": "OC133_MODERN_SCIENCE_COVERAGE_LANE_QUEUE_v1",
                    "queue_size": 1,
                    "open_lane_total": 1,
                    "lanes": [
                        coverage_lane("MS-COV-WO-012", "medical_health", "clinical_outcomes", priority="P0", rank=1)
                    ],
                },
            )

            audit = readiness.enrich_readiness_dispatch(minimal_blocked_audit(), root)

            for row in audit["work_orders"]:
                self.assertTrue(row["owner_capability"])
                self.assertTrue(row["executor"]["command"])
                self.assertTrue(row["artifacts"])
                self.assertTrue(row["before_predicates"])
                self.assertTrue(row["after_predicates"])
                self.assertTrue(row["verification_commands"])
                self.assertTrue(row["resource_estimate"])
                self.assertTrue(row["closure_evidence_type"])
                self.assertTrue(row["closure_evidence_required"])
                self.assertFalse(row["closure_control"]["mark_closed_allowed_in_this_dispatch"])
                self.assertFalse(row["closure_control"]["blocked_item_closed"])
                self.assertTrue(row["no_send_locks"]["no_send"])
                self.assertFalse(row["no_send_locks"]["publish_allowed"])

    def test_allow_blocked_exit_zero_keeps_scientific_blocker_nonfatal(self) -> None:
        blocked_audit = {
            "state": "OC_CORE_1_3_3_ALL_DOMAIN_SCIENTIFIC_READINESS_RUNNING",
            "final_readiness_state": "SCIENTIFIC_BLOCKERS_REMAIN",
            "blocker_total": 1,
            "blocker_ids": ["grand_toe_empirical_superiority"],
            "next_automatic_action": "OC133-PLATINUM-WO-002",
            "all_domain_ready_no_send": False,
        }
        execute_result = {
            "execution_state": "SCIENTIFIC_BLOCKERS_REMAIN",
            "after_final_readiness_state": "SCIENTIFIC_BLOCKERS_REMAIN",
        }
        with (
            mock.patch.object(
                sys,
                "argv",
                [
                    "oc133_logion_all_domain_readiness.py",
                    "--write",
                    "--execute-next",
                    "--allow-blocked-exit-zero",
                ],
            ),
            mock.patch.object(readiness, "execute_next", return_value=execute_result),
            mock.patch.object(readiness.oc133_platinum, "content_closure_audit", return_value={}),
            mock.patch.object(readiness.oc133_platinum, "all_domain_readiness_audit", return_value=blocked_audit),
            mock.patch.object(readiness, "write_all_domain_outputs", return_value={"scorecard": "x"}),
            mock.patch("builtins.print"),
        ):
            self.assertEqual(readiness.main(), 0)

    def test_blocked_exit_remains_nonzero_without_explicit_loop_flag(self) -> None:
        blocked_audit = {
            "state": "OC_CORE_1_3_3_ALL_DOMAIN_SCIENTIFIC_READINESS_RUNNING",
            "final_readiness_state": "SCIENTIFIC_BLOCKERS_REMAIN",
            "blocker_total": 1,
            "blocker_ids": ["grand_toe_empirical_superiority"],
            "next_automatic_action": "OC133-PLATINUM-WO-002",
            "all_domain_ready_no_send": False,
        }
        with (
            mock.patch.object(sys, "argv", ["oc133_logion_all_domain_readiness.py", "--write"]),
            mock.patch.object(readiness.oc133_platinum, "content_closure_audit", return_value={}),
            mock.patch.object(readiness.oc133_platinum, "all_domain_readiness_audit", return_value=blocked_audit),
            mock.patch.object(readiness, "write_all_domain_outputs", return_value={"scorecard": "x"}),
            mock.patch("builtins.print"),
        ):
            self.assertEqual(readiness.main(), 2)

    def test_external_review_ready_exits_zero_without_full_all_domain_claim(self) -> None:
        ready_audit = {
            "state": "OC_CORE_1_3_3_EXTERNAL_REVIEW_READY_NO_SEND",
            "final_readiness_state": "OC_CORE_1_3_3_EXTERNAL_REVIEW_READY_NO_SEND",
            "blocker_total": 2,
            "blocker_ids": ["grand_toe_claim_ledger_evidence", "modern_science_comparator_superiority"],
            "next_automatic_action": "OC133-ALLDOMAIN-COVERAGE-MS-COV-WO-003",
            "all_domain_ready_no_send": False,
            "external_review_ready_no_send": True,
            "full_science_program_state": "OC_FULL_SCIENCE_PROGRAM_RUNNING",
        }
        with (
            mock.patch.object(sys, "argv", ["oc133_logion_all_domain_readiness.py", "--write"]),
            mock.patch.object(readiness.oc133_platinum, "content_closure_audit", return_value={}),
            mock.patch.object(readiness.oc133_platinum, "all_domain_readiness_audit", return_value=ready_audit),
            mock.patch.object(readiness, "write_all_domain_outputs", return_value={"scorecard": "x"}),
            mock.patch("builtins.print"),
        ):
            self.assertEqual(readiness.main(), 0)


if __name__ == "__main__":
    raise SystemExit(unittest.main())
