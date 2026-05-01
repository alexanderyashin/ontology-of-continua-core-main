from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools import oc133_target_projection_lock_factory as factory


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8", newline="\n")


def strict_locks() -> dict[str, object]:
    return dict(factory.NO_SEND_LOCKS)


def base_snapshot() -> list[dict[str, object]]:
    return [
        {"id": "a", "split": "holdout", "x": 1, "y": 3},
        {"id": "b", "split": "holdout", "x": 2, "y": 5},
        {"id": "c", "split": "train", "x": 99, "y": 999},
    ]


def base_declaration(snapshot_ref: str = "snapshots/official.json") -> dict[str, object]:
    return {
        "schema_id": "TEST_TARGET_PROJECTION_DECLARATION_v1",
        "lock_id": "unit-linear-lock",
        "snapshot_ref": snapshot_ref,
        "snapshot_format": "auto",
        "row_id_field": "id",
        "visible_fields": ["id", "split", "x"],
        "target_fields": ["y"],
        "row_inclusion_rule": {"field": "split", "equals": "holdout"},
        "model_declaration": {
            "kind": "linear",
            "intercept": 1,
            "terms": [{"field": "x", "coefficient": 2}],
        },
        "comparator_declaration": {"kind": "constant", "value": 0},
        "residual_metric": "mae",
        "uncertainty_policy": {"max_model_residual": 0.0, "min_model_advantage": 0.0},
        "negative_controls": [{"control_id": "declared-null-control", "kind": "locked-visible-only"}],
        "locks": strict_locks(),
    }


class TargetProjectionLockFactoryTests(unittest.TestCase):
    def test_builds_target_blind_projection_locks_and_pass_verdict(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot = root / "snapshots/official.json"
            declaration = root / "declarations/lock.json"
            write_json(snapshot, base_snapshot())
            write_json(declaration, base_declaration())

            report, records = factory.build_report_with_locks(root, [declaration])

            self.assertEqual(report["record_total"], 1)
            self.assertEqual(report["locked_pass_total"], 1)
            self.assertEqual(report["open_blocker_total"], 0)
            self.assertNotIn("grand_toe_support_allowed", json.dumps(report))

            record = records[0]
            self.assertEqual(record["verdict"], "LOCKED_PASS")
            self.assertEqual(record["residual_summary"]["model_residual"], 0.0)
            self.assertEqual(record["visible_projection_lock"]["row_count"], 2)
            self.assertEqual(record["target_projection_lock"]["row_count"], 2)
            self.assertTrue(record["tamper_controls"]["target_opened_after_prediction_materialization"])
            self.assertFalse(
                record["prediction_materialization_lock"]["algorithmic_target_separation"][
                    "target_projection_read_before_prediction_materialization"
                ]
            )
            self.assertEqual(record["prediction_materialization_lock"]["prediction_rows"][0]["model_prediction"], 3.0)
            self.assertEqual(record["target_projection_lock"]["rows"][0]["target"]["y"], 3)
            self.assertEqual(record["target_projection_lock"]["locks"], factory.NO_SEND_LOCKS)

    def test_fails_closed_when_target_field_is_visible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot = root / "snapshots/official.json"
            declaration = root / "declarations/lock.json"
            payload = base_declaration()
            payload["visible_fields"] = ["id", "split", "x", "y"]
            write_json(snapshot, base_snapshot())
            write_json(declaration, payload)

            report = factory.build_report(root, [declaration])

            self.assertEqual(report["blocked_total"], 1)
            self.assertIn("TARGET_FIELD_IN_VISIBLE_PROJECTION::y", report["blockers"])

    def test_fails_closed_when_declaration_contains_target_value(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot = root / "snapshots/official.json"
            declaration = root / "declarations/lock.json"
            payload = base_declaration()
            payload["forbidden_target_values"] = [3]
            write_json(snapshot, base_snapshot())
            write_json(declaration, payload)

            report = factory.build_report(root, [declaration])

            self.assertEqual(report["blocked_total"], 1)
            self.assertTrue(
                any(blocker.startswith("DECLARATION_CONTAINS_TARGET_VALUE::") for blocker in report["blockers"])
            )

    def test_fails_closed_when_no_send_locks_are_missing_or_weak(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot = root / "snapshots/official.json"
            declaration = root / "declarations/lock.json"
            payload = base_declaration()
            payload["locks"] = {"no_send": True, "publish_allowed": True}
            write_json(snapshot, base_snapshot())
            write_json(declaration, payload)

            report = factory.build_report(root, [declaration])

            self.assertEqual(report["blocked_total"], 1)
            self.assertIn("NO_SEND_LOCK_MISSING_OR_WEAK::publish_allowed", report["blockers"])
            self.assertIn("NO_SEND_LOCK_MISSING_OR_WEAK::push_allowed", report["blockers"])

    def test_fails_closed_on_declared_projection_hash_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot = root / "snapshots/official.json"
            declaration = root / "declarations/lock.json"
            payload = base_declaration()
            payload["expected_target_projection_sha256"] = "not-the-real-target-lock-hash"
            write_json(snapshot, base_snapshot())
            write_json(declaration, payload)

            report = factory.build_report(root, [declaration])

            self.assertEqual(report["blocked_total"], 1)
            self.assertIn("TARGET_PROJECTION_HASH_MISMATCH", report["blockers"])

    def test_ndjson_write_check_and_tamper_detection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot_ref = "snapshots/official.ndjson"
            snapshot = root / snapshot_ref
            declaration = root / "declarations/lock.json"
            write_text(snapshot, "".join(json.dumps(row, sort_keys=True) + "\n" for row in base_snapshot()))
            write_json(declaration, base_declaration(snapshot_ref))

            exit_code = factory.main(
                ["--root", str(root), "--declaration", declaration.relative_to(root).as_posix(), "--write"]
            )
            self.assertEqual(exit_code, 0)
            self.assertEqual(
                factory.main(["--root", str(root), "--declaration", declaration.relative_to(root).as_posix(), "--check"]),
                0,
            )

            visible_lock = root / factory.lock_paths("unit-linear-lock")["visible_lock_ref"]
            tampered = json.loads(visible_lock.read_text(encoding="utf-8"))
            tampered["rows"][0]["visible"]["x"] = 100
            write_json(visible_lock, tampered)

            failures = factory.check_stored(root, [declaration])
            self.assertIn(f"mismatch::{factory.lock_paths('unit-linear-lock')['visible_lock_ref']}", failures)


if __name__ == "__main__":
    unittest.main()
