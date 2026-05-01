from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tools import oc133_systems_wdi_model_search_factory as factory
from validation.grand_science import evidence_pack_factory as grand_factory


REPO_ROOT = Path(__file__).resolve().parents[1]


def copy_requirements(root: Path) -> None:
    source = REPO_ROOT / "benchmarks/grand_science/domain_requirements.json"
    target = root / factory.REQUIREMENTS_REL
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def source_separation() -> dict[str, object]:
    return {
        "mode": "target_blind",
        "pre_target_lock": True,
        "target_hidden_until_scoring": True,
        "declared_before_scoring": True,
    }


def linear_wdi_payload(*, include_source_separation: bool = True, years: range = range(2000, 2031)) -> list[object]:
    metadata: dict[str, object] = {
        "page": 1,
        "pages": 1,
        "per_page": 1000,
        "total": len(list(years)),
        "sourceid": "2",
        "lastupdated": "2026-04-08",
    }
    if include_source_separation:
        metadata["oc133_source_separation"] = source_separation()

    rows: list[dict[str, object]] = []
    for offset, year in enumerate(years):
        rows.append(
            {
                "indicator": {"id": "NY.GDP.MKTP.CD", "value": "GDP (current US$)"},
                "country": {"id": "TST", "value": "Testland"},
                "countryiso3code": "TST",
                "date": str(year),
                "value": 100.0 + offset * 5.0,
                "unit": "",
                "obs_status": "",
                "decimal": 0,
            }
        )
    return [metadata, rows]


def write_snapshot(root: Path, payload: object, rel_path: str = "validation/heldout/mock_wdi_snapshot.json") -> str:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return rel_path


class SystemsWdiModelSearchFactoryTests(unittest.TestCase):
    def test_mocked_target_blind_linear_payload_can_pass_grand_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_requirements(root)
            snapshot_ref = write_snapshot(root, linear_wdi_payload())

            payload = factory.build_payload(root, snapshot_ref=snapshot_ref)
            report = payload["report"]
            pack = payload["candidate_pack"]

            self.assertTrue(report["grand_toe_support_allowed"])
            self.assertEqual(report["verdict"], "READY_FOR_PARENT_REGISTRY_REVIEW")
            self.assertGreaterEqual(report["candidate_n"], 20)
            self.assertEqual(report["blockers"], [])
            self.assertEqual(report["valid_pack_total"], 1)
            self.assertEqual(grand_factory.pack_failure_reasons(pack, factory.load_requirements(root)[0]), [])
            self.assertEqual(report["formula_search"]["target_rows_used_for_selection"], False)
            self.assertEqual(report["formula_search"]["selected_formula_counts"], {"linear_two_lag": report["candidate_n"]})
            self.assertTrue(all(test["passed"] for test in report["tamper_tests"]))
            self.assertTrue(all(row["negative_control_rejected"] for row in payload["tasks"]["rows"]))

    def test_source_separation_is_required_even_when_mocked_residuals_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_requirements(root)
            snapshot_ref = write_snapshot(root, linear_wdi_payload(include_source_separation=False))

            report = factory.build_payload(root, snapshot_ref=snapshot_ref)["report"]

            self.assertFalse(report["grand_toe_support_allowed"])
            self.assertEqual(report["verdict"], "BLOCKED")
            self.assertIn("SOURCE_SEPARATION_MODE_NOT_ALLOWED::snapshot_replay", report["blockers"])
            self.assertIn("PRE_TARGET_LOCK_REQUIRED", report["blockers"])
            self.assertIn("TARGET_HIDDEN_UNTIL_SCORING_REQUIRED", report["blockers"])
            self.assertEqual(report["negative_control_rejected_total"], report["negative_control_total"])

    def test_current_official_harvested_snapshot_blocks_without_faking_pass(self) -> None:
        payload = factory.build_payload(REPO_ROOT)
        report = payload["report"]

        self.assertEqual(report["snapshot_ref"], factory.DEFAULT_SNAPSHOT_REF)
        self.assertEqual(report["verdict"], "BLOCKED")
        self.assertFalse(report["grand_toe_support_allowed"])
        self.assertGreaterEqual(report["candidate_n"], 20)
        self.assertLess(report["negative_control_rejected_total"], report["negative_control_total"])
        self.assertEqual(report["valid_pack_total"], 0)
        self.assertTrue(any(item.startswith("NEGATIVE_CONTROL_NOT_REJECTED::") for item in report["blockers"]))
        self.assertIn("GRAND_TOE_SUPPORT_NOT_ALLOWED", report["blockers"])
        self.assertTrue(all(test["passed"] for test in report["tamper_tests"]))
        self.assertTrue(report["next_work_orders"])

    def test_write_outputs_materializes_only_model_search_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_requirements(root)
            snapshot_ref = write_snapshot(root, linear_wdi_payload(years=range(2000, 2008)))

            payload = factory.write_outputs(root, snapshot_ref=snapshot_ref)

            self.assertFalse(payload["report"]["grand_toe_support_allowed"])
            self.assertEqual(factory.check_stored(root, snapshot_ref=snapshot_ref), [])
            output_root = root / factory.OUTPUT_ROOT_REL
            self.assertEqual(
                sorted(path.name for path in output_root.iterdir()),
                sorted(
                    [
                        "OC133_SYSTEMS_WDI_MODEL_SEARCH_CANDIDATE_PACK.json",
                        "OC133_SYSTEMS_WDI_MODEL_SEARCH_PROTOCOL.json",
                        "OC133_SYSTEMS_WDI_MODEL_SEARCH_REPORT.json",
                        "OC133_SYSTEMS_WDI_MODEL_SEARCH_TASKS.json",
                        "README.md",
                    ]
                ),
            )


if __name__ == "__main__":
    raise SystemExit(unittest.main())
