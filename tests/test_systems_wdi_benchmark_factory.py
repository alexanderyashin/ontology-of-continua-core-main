from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tools import oc133_systems_wdi_benchmark_factory as factory
from validation.grand_science import evidence_pack_factory as grand_factory


REPO_ROOT = Path(__file__).resolve().parents[1]


def copy_requirements(root: Path) -> None:
    source = REPO_ROOT / "benchmarks/grand_science/domain_requirements.json"
    target = root / "benchmarks/grand_science/domain_requirements.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def wdi_payload(
    *,
    series_total: int = 20,
    target_plateau: bool = False,
    include_source_separation: bool = True,
) -> list[object]:
    metadata: dict[str, object] = {
        "page": 1,
        "pages": 1,
        "per_page": 1000,
        "total": series_total * 6,
        "sourceid": "2",
        "lastupdated": "2026-04-08",
    }
    if include_source_separation:
        metadata["oc133_source_separation"] = {
            "mode": "target_blind",
            "pre_target_lock": True,
            "target_hidden_until_scoring": True,
            "declared_before_scoring": True,
            "split_policy": "last_year_heldout_per_series",
        }

    rows: list[dict[str, object]] = []
    for idx in range(series_total):
        country_code = f"C{idx:02d}"
        country_name = f"Country {idx:02d}"
        for offset, year in enumerate(range(2000, 2006)):
            value = 100.0 + idx * 10.0 + offset * 5.0
            if target_plateau and year == 2005:
                value = 100.0 + idx * 10.0 + 4 * 5.0
            rows.append(
                {
                    "indicator": {"id": "NY.GDP.MKTP.CD", "value": "GDP (current US$)"},
                    "country": {"id": country_code, "value": country_name},
                    "countryiso3code": country_code,
                    "date": str(year),
                    "value": value,
                    "unit": "",
                    "obs_status": "",
                    "decimal": 0,
                }
            )
    return [metadata, rows]


def write_snapshot(root: Path, payload: object, rel: str = "validation/_raw/mock_wdi.json") -> str:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return rel


class SystemsWdiBenchmarkFactoryTests(unittest.TestCase):
    def test_mocked_target_blind_payload_can_support_when_all_gates_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_requirements(root)
            snapshot_ref = write_snapshot(root, wdi_payload())

            payload = factory.build_payload(root, snapshot_ref=snapshot_ref)
            report = payload["report"]
            pack = payload["candidate_pack"]

            self.assertTrue(report["grand_toe_support_allowed"])
            self.assertEqual(report["candidate_n"], 20)
            self.assertEqual(report["selected_formula"]["id"], "linear_two_lag")
            self.assertEqual(report["formula_selection"]["target_rows_used_for_selection"], False)
            self.assertEqual(report["blockers"], [])
            self.assertEqual(grand_factory.pack_failure_reasons(pack, factory.load_requirements(root)[0]), [])
            self.assertTrue(all(test["passed"] for test in report["tamper_tests"]))
            self.assertTrue(all(row["negative_control_passed"] for row in payload["tasks"]["rows"]))

    def test_support_blocks_without_explicit_target_separation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_requirements(root)
            snapshot_ref = write_snapshot(root, wdi_payload(include_source_separation=False))

            payload = factory.build_payload(root, snapshot_ref=snapshot_ref)
            report = payload["report"]

            self.assertFalse(report["grand_toe_support_allowed"])
            self.assertEqual(report["candidate_n"], 20)
            self.assertIn("TARGET_SEPARATION_NOT_EXPLICIT_OR_NOT_LOCKED", report["blockers"])
            self.assertIn("SOURCE_SEPARATION_MODE_NOT_ALLOWED::snapshot_replay", report["blockers"])
            self.assertEqual(report["formula_selection"]["target_rows_used_for_selection"], False)

    def test_support_blocks_when_carry_forward_negative_control_wins(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_requirements(root)
            snapshot_ref = write_snapshot(root, wdi_payload(target_plateau=True))

            payload = factory.build_payload(root, snapshot_ref=snapshot_ref)
            report = payload["report"]

            self.assertFalse(report["grand_toe_support_allowed"])
            self.assertEqual(report["candidate_n"], 20)
            self.assertIn("HELDOUT_RESIDUAL_SUPERIORITY_NOT_MET", report["blockers"])
            self.assertTrue(any(item.startswith("NEGATIVE_CONTROL_NOT_REJECTED::") for item in report["blockers"]))
            self.assertTrue(
                any(
                    test["test_id"] == "systems-wdi-carry-forward-negative-controls" and test["passed"] is False
                    for test in report["tamper_tests"]
                )
            )

    def test_write_outputs_materializes_only_wdi_benchmark_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_requirements(root)
            snapshot_ref = write_snapshot(root, wdi_payload(series_total=3))

            payload = factory.write_outputs(root, snapshot_ref=snapshot_ref)

            self.assertFalse(payload["report"]["grand_toe_support_allowed"])
            self.assertTrue((root / factory.PACK_REL).is_file())
            self.assertTrue((root / factory.REPORT_REL).is_file())
            self.assertTrue((root / factory.PROTOCOL_REL).is_file())
            self.assertTrue((root / factory.TASKS_REL).is_file())
            self.assertTrue((root / factory.README_REL).is_file())
            self.assertEqual(factory.check_stored(root, snapshot_ref=snapshot_ref), [])


if __name__ == "__main__":
    unittest.main()
