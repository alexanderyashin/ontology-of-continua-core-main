from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools import oc133_systems_wdi_population_materiality_factory as factory


def write_requirements(root: Path, minimum_n: int = 4) -> None:
    path = root / factory.REQUIREMENTS_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_id": "OC133_GRAND_EMPIRICAL_DOMAIN_REQUIREMENTS_v1",
                "release_id": "oc_core_1_3_3",
                "capability_owner": "Research/EmpiricalScience",
                "minimum_per_domain_n": minimum_n,
                "required_domains": ["systems"],
                "required_source_separation_modes": ["prospective", "target_blind"],
                "criteria": {
                    "source_separation_required": True,
                    "target_hidden_until_scoring_required": True,
                    "pre_target_lock_required": True,
                    "comparator_baseline_required": True,
                    "uncertainty_interval_required": True,
                    "residual_superiority_required": True,
                    "negative_control_rejection_required": True,
                    "falsifier_required": True,
                    "grand_toe_support_allowed_must_be_explicit": True,
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )


def wdi_payload(values_by_year: dict[int, float]) -> list[object]:
    rows: list[dict[str, object]] = []
    for year, value in sorted(values_by_year.items(), reverse=True):
        rows.append(
            {
                "indicator": {"id": factory.TARGET_INDICATOR_ID, "value": factory.TARGET_INDICATOR_NAME},
                "country": {"id": "AR", "value": factory.TARGET_COUNTRY_NAME},
                "countryiso3code": factory.TARGET_COUNTRY_CODE,
                "date": str(year),
                "value": value,
                "unit": "",
                "obs_status": "",
                "decimal": 0,
            }
        )
    return [
        {
            "page": 1,
            "pages": 1,
            "per_page": 20000,
            "total": len(rows),
            "sourceid": "2",
            "lastupdated": "2026-04-08",
        },
        rows,
    ]


def write_snapshot(root: Path, values_by_year: dict[int, float]) -> str:
    rel = "validation/heldout/mock_population_snapshot.json"
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(wdi_payload(values_by_year), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return rel


def linear_values() -> dict[int, float]:
    return {year: 100.0 + 5.0 * (year - 1960) for year in range(1960, 1984)}


class SystemsWdiPopulationMaterialityFactoryTests(unittest.TestCase):
    def test_linear_fixture_passes_materiality_and_source_lock(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_requirements(root, minimum_n=4)
            snapshot_ref = write_snapshot(root, linear_values())

            payload = factory.build_payload(root, snapshot_ref=snapshot_ref, target_years=tuple(range(1980, 1984)))
            report = payload["report"]

            self.assertEqual(report["verdict"], "READY_FOR_PARENT_REGISTRY_REVIEW")
            self.assertTrue(report["grand_toe_support_allowed"])
            self.assertEqual(report["strict_schema_failures"], [])
            self.assertEqual(report["exact_failure_rows"], [])
            self.assertTrue(report["materiality_audit"]["passed"])
            self.assertEqual(report["materiality_audit"]["row_materiality_failed_total"], 0)
            self.assertEqual(report["selected_formula_counts"], {"last_slope": 4})
            self.assertEqual(payload["source_lock_declaration"]["target_rows_declared_before_scoring"][0]["target_value_excluded"], True)
            self.assertFalse(factory.declaration_contains_forbidden_fields(payload["source_lock_declaration"]))

    def test_near_tie_blocks_even_when_strict_comparator_loses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_requirements(root, minimum_n=1)
            values = linear_values()
            values[1980] = values[1979] + 2.51
            snapshot_ref = write_snapshot(root, values)

            payload = factory.build_payload(root, snapshot_ref=snapshot_ref, target_years=(1980,))
            row = payload["tasks"]["rows"][0]
            report = payload["report"]

            self.assertLess(row["model_residual"], row["best_comparator_residual"])
            self.assertTrue(row["negative_controls_passed"])
            self.assertFalse(row["materiality"]["passed"])
            self.assertEqual(report["verdict"], "BLOCKED")
            self.assertIn("HELDOUT_RESIDUAL_MATERIALITY_NOT_MET", report["blockers"])
            self.assertIn("STRICT_MATERIALITY_NOT_MET", report["blockers"])

    def test_target_leakage_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_requirements(root, minimum_n=4)
            snapshot_ref = write_snapshot(root, linear_values())
            payload = factory.build_payload(root, snapshot_ref=snapshot_ref, target_years=tuple(range(1980, 1984)))

            leaked = json.loads(json.dumps(payload, ensure_ascii=False))
            leaked["tasks"]["rows"][0]["formula_selection"]["target_rows_used_for_selection"] = True
            failures = factory.strict_schema_failures(leaked)
            self.assertIn("STRICT_FORMULA_SELECTION_TARGET_LEAKAGE::OC133-SYSTEMS-WDI-POPULATION-MATERIALITY-ARG-1980", failures)

            score_leak = json.loads(json.dumps(payload, ensure_ascii=False))
            score_leak["tasks"]["rows"][0]["formula_selection"]["scores"][0]["scoring_years"].append(1980)
            score_failures = factory.strict_schema_failures(score_leak)
            self.assertTrue(any("STRICT_FORMULA_SELECTION_SCORE_NOT_PRIOR" in failure for failure in score_failures))

    def test_comparator_triviality_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_requirements(root, minimum_n=4)
            snapshot_ref = write_snapshot(root, linear_values())
            payload = factory.build_payload(root, snapshot_ref=snapshot_ref, target_years=tuple(range(1980, 1984)))
            trivial = json.loads(json.dumps(payload, ensure_ascii=False))
            trivial["candidate_pack"]["comparator_baseline"]["baselines"] = [
                {
                    "id": "constant_zero",
                    "name": "constant zero comparator",
                    "prediction_rule": "always predict 0",
                    "pre_registered": True,
                }
            ]

            failures = factory.strict_schema_failures(trivial)

            self.assertIn("STRICT_COMPARATOR_BASELINES_TOO_FEW", failures)
            self.assertIn("STRICT_COMPARATOR_TRIVIAL::constant_zero", failures)

    def test_materiality_pass_is_required_for_support_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_requirements(root, minimum_n=1)
            values = linear_values()
            values[1980] = values[1979] + 2.51
            snapshot_ref = write_snapshot(root, values)

            payload = factory.build_payload(root, snapshot_ref=snapshot_ref, target_years=(1980,))
            pack = payload["candidate_pack"]

            self.assertFalse(pack["grand_toe_support_allowed"])
            self.assertFalse(pack["materiality_audit"]["passed"])
            self.assertIn("GRAND_TOE_SUPPORT_NOT_ALLOWED", payload["report"]["blockers"])


if __name__ == "__main__":
    raise SystemExit(unittest.main())
