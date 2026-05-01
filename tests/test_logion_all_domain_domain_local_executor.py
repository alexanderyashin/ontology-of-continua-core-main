from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools import oc133_logion_all_domain_readiness as readiness


def write_json(root: Path, rel_path: str, payload: dict[str, object]) -> None:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(root: Path, rel_path: str, text: str) -> None:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def coverage_lane(work_order_id: str = "MS-COV-WO-501") -> dict[str, object]:
    return {
        "queue_rank": 1,
        "dispatch_id": "MS-COV-DISPATCH-501",
        "stable_id": f"{work_order_id}::test_domain::domain_local_replay_lane",
        "work_order_id": work_order_id,
        "coverage_gap_id": "MS-COV-GAP-TEST_DOMAIN-DOMAIN_LOCAL_REPLAY_LANE",
        "priority": "P0",
        "domain_class_id": "test_domain",
        "phenomenon_class_id": "domain_local_replay_lane",
        "phenomenon_label": "domain local replay lane",
        "lane_route": "EMPIRICAL_SOURCE_BACKED_BENCHMARK",
        "owner_capability": "Logion Test Evidence Capability",
        "resource_estimate": {"planning_points": 3, "expected_worker_roles": ["test owner"]},
        "dependencies": [{"dependency_id": "source_capsule_lock", "state": "OPEN"}],
        "expected_acceptance_predicates": ["STRICT_PACK_SCHEMA_PASS"],
        "coverage_closure": {"current_status": "OPEN", "mark_closed_allowed": False},
    }


class LogionAllDomainDomainLocalExecutorTests(unittest.TestCase):
    def test_domain_local_summary_exposes_safe_replay_command_and_refs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            replay_script = (
                "validation/heldout/grand_science/test_domain/coverage_work_orders/"
                "oc133_test_domain_replay.py"
            )
            source_ref = "validation/heldout/grand_science/test_domain/coverage_work_orders/raw/source.json"
            pack_ref = "validation/heldout/grand_science/test_domain/coverage_work_orders/STRICT_PACK.json"
            write_text(root, replay_script, "raise SystemExit(0)\n")
            write_json(root, source_ref, {"schema_id": "TEST_SOURCE_v1"})
            write_json(root, pack_ref, {"schema_id": "TEST_STRICT_PACK_v1"})

            summary = readiness.domain_local_lane_summary(
                row={
                    "work_order_id": "MS-COV-WO-501",
                    "coverage_gap_id": "MS-COV-GAP-TEST_DOMAIN-DOMAIN_LOCAL_REPLAY_LANE",
                    "domain_class_id": "test_domain",
                    "phenomenon_class_id": "domain_local_replay_lane",
                    "lane_status": "SCORER_READY_FAIL_CLOSED_STRICT_EVIDENCE_NOT_MET",
                    "current_evidence_status": {
                        "source_snapshot_hash_bound": True,
                        "target_hidden_scorer_present": True,
                        "implemented_snapshot_ref": source_ref,
                    },
                    "executable_spec": {
                        "fail_closed_current_evidence": {
                            "strict_evidence_pack_ref": pack_ref,
                            "strict_evidence_pack_sha256": "abc123",
                            "comparator_residual_metric_bound": True,
                            "negative_control_rejected": True,
                        },
                        "replay_command": {
                            "commands": [
                                f"python {replay_script} --score --write",
                                "python benchmarks/modern_science/coverage_lane_dispatcher.py --check",
                            ]
                        },
                    },
                },
                artifact_ref="validation/heldout/grand_science/test_domain/coverage_work_orders/WORK_ORDERS.json",
                ancillary_payloads=[],
                root=root,
            )

            self.assertTrue(summary["domain_local_replay_ready"])
            self.assertEqual(summary["replay_command"]["argv"], ["python", replay_script, "--score", "--write"])
            self.assertEqual(summary["replay_command"]["script_ref"], replay_script)
            self.assertIn(source_ref, summary["replay_evidence_refs"])
            self.assertIn(pack_ref, summary["replay_evidence_refs"])

    def test_coverage_lane_work_order_uses_domain_local_replay_executor_without_closure(self) -> None:
        replay_script = (
            "validation/heldout/grand_science/test_domain/coverage_work_orders/"
            "oc133_test_domain_replay.py"
        )
        lane = readiness.build_coverage_lane_work_order(
            coverage_lane(),
            {
                "missing_predicate_count": 1,
                "domain_local_evidence_priority_rank": 0,
                "source_acquired": True,
                "scorer_ready": True,
                "domain_local_replay_ready": True,
                "replay_command": {
                    "command": f"python {replay_script} --score --write",
                    "argv": ["python", replay_script, "--score", "--write"],
                    "script_ref": replay_script,
                },
                "replay_evidence_refs": [
                    "validation/heldout/grand_science/test_domain/coverage_work_orders/STRICT_PACK.json"
                ],
            },
        )

        self.assertEqual(lane["executor"]["mode"], "domain_local_replay")
        self.assertEqual(lane["executor"]["argv"], ["python", replay_script, "--score", "--write"])
        self.assertTrue(lane["no_send"])
        self.assertFalse(lane["closure_control"]["mark_closed_allowed_in_this_dispatch"])
        self.assertTrue(lane["closure_control"]["domain_local_replay_exists_is_not_closure"])

    def test_execute_next_replay_success_still_marks_scientific_blockers_when_predicates_remain(self) -> None:
        work_order = readiness.build_coverage_lane_work_order(
            coverage_lane(),
            {
                "missing_predicate_count": 1,
                "domain_local_evidence_priority_rank": 0,
                "source_acquired": True,
                "scorer_ready": True,
                "domain_local_replay_ready": True,
                "replay_command": {
                    "command": "python validation/heldout/grand_science/test_domain/coverage_work_orders/replay.py --check",
                    "argv": [
                        "python",
                        "validation/heldout/grand_science/test_domain/coverage_work_orders/replay.py",
                        "--check",
                    ],
                    "script_ref": "validation/heldout/grand_science/test_domain/coverage_work_orders/replay.py",
                },
                "replay_evidence_refs": [
                    "validation/heldout/grand_science/test_domain/coverage_work_orders/STRICT_PACK.json"
                ],
            },
        )
        before = {
            "state": "OC_CORE_1_3_3_ALL_DOMAIN_SCIENTIFIC_READINESS_RUNNING",
            "final_readiness_state": "SCIENTIFIC_BLOCKERS_REMAIN",
            "work_orders": [work_order],
        }
        after = {
            "state": "OC_CORE_1_3_3_ALL_DOMAIN_SCIENTIFIC_READINESS_RUNNING",
            "final_readiness_state": "SCIENTIFIC_BLOCKERS_REMAIN",
            "blocker_ids": ["modern_science_comparator_superiority"],
            "work_orders": [work_order],
        }

        with (
            mock.patch.object(readiness.oc133_platinum, "content_closure_audit", return_value={}),
            mock.patch.object(readiness.oc133_platinum, "all_domain_readiness_audit", return_value={}),
            mock.patch.object(readiness, "enrich_readiness_dispatch", side_effect=[before, after]),
            mock.patch.object(readiness, "command", return_value={"returncode": 0, "cmd": work_order["executor"]["argv"]}) as command,
            mock.patch.object(readiness, "write_all_domain_outputs", return_value={"dispatch": "x"}),
            mock.patch.object(readiness, "append_ledger", side_effect=lambda row: {"latest_execution_state": row["execution_state"]}),
        ):
            result = readiness.execute_next()

        command.assert_called_once()
        self.assertEqual(command.call_args.args[0][1], "validation/heldout/grand_science/test_domain/coverage_work_orders/replay.py")
        self.assertEqual(result["executor"]["mode"], "domain_local_replay")
        self.assertEqual(result["execution_state"], "SCIENTIFIC_BLOCKERS_REMAIN")
        self.assertTrue(result["no_send"])


if __name__ == "__main__":
    raise SystemExit(unittest.main())
