from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tools import oc133_biology_systems_acquisition_planner as planner
from validation.grand_science import evidence_pack_factory as grand_factory


REPO_ROOT = Path(__file__).resolve().parents[1]


def copy_required_fixtures(root: Path) -> None:
    fixtures = [
        "benchmarks/grand_science/domain_requirements.json",
        "validation/grand_science/grand_empirical_evidence.schema.json",
        "validation/grand_science/grand_empirical_protocol.schema.json",
        "validation/_raw/biology_ncbi_geo_platform.txt",
        "validation/_raw/systems_world_bank_gdp.txt",
    ]
    for rel in fixtures:
        source = REPO_ROOT / rel
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


class BiologySystemsAcquisitionPlannerTests(unittest.TestCase):
    def test_default_plan_is_blocked_with_genuity_requirements(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_required_fixtures(root)
            payload = planner.build_payload(root)
            plan = payload["plan"]
            report = payload["report"]

            self.assertEqual(plan["verdict"], "BLOCKED_PENDING_GENUINE_BIOLOGY_SYSTEMS_ACQUISITION")
            self.assertFalse(plan["grand_toe_support_allowed"])
            self.assertEqual(report["verdict"], "BLOCKED_PENDING_GENUINE_BIOLOGY_SYSTEMS_EVIDENCE")
            self.assertEqual(report["open_blocker_total"], 2)
            self.assertEqual(report["blocked_domain_total"], 2)

            rows = {row["domain"]: row for row in plan["rows"]}
            for domain in ("biology", "systems"):
                row = rows[domain]
                self.assertFalse(row["grand_toe_support_allowed"])
                self.assertEqual(row["required_n"], 20)
                self.assertEqual(row["snapshot_ref"], f"validation/_raw/{'biology_ncbi_geo_platform.txt' if domain=='biology' else 'systems_world_bank_gdp.txt'}")
                self.assertEqual(row["status"], "BLOCKED_PENDING_GENUINE_EVIDENCE_PLAN")
                self.assertIn("N_BELOW_MINIMUM::1/20", row["blockers"])

    def test_bounded_templates_cannot_pass_grand_factory_checks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_required_fixtures(root)
            requirements = planner.load_requirements(root)
            payload = planner.build_payload(root)

            for row in payload["plan"]["rows"]:
                template = row["candidate_pack_template"]
                failures = grand_factory.pack_failure_reasons(template, requirements)
                self.assertIn("GRAND_TOE_SUPPORT_NOT_ALLOWED", failures)
                self.assertFalse(template["grand_toe_support_allowed"])
                self.assertIn("N_BELOW_MINIMUM::20", ", ".join(failures))
                self.assertTrue(len(row["blockers"]) >= 1)

    def test_plan_and_report_are_written_deterministically(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_required_fixtures(root)

            first_report = planner.write_outputs(root, run_endpoint_checks=False)
            first_plan_text = (root / planner.PLAN_REL).read_text(encoding="utf-8")
            first_report_text = (root / planner.REPORT_REL).read_text(encoding="utf-8")
            first_bio_template = (root / planner.BIOLOGY_TEMPLATE_REL).read_text(encoding="utf-8")
            first_systems_template = (root / planner.SYSTEMS_TEMPLATE_REL).read_text(encoding="utf-8")

            second_report = planner.write_outputs(root, run_endpoint_checks=False)
            second_plan_text = (root / planner.PLAN_REL).read_text(encoding="utf-8")
            second_report_text = (root / planner.REPORT_REL).read_text(encoding="utf-8")
            second_bio_template = (root / planner.BIOLOGY_TEMPLATE_REL).read_text(encoding="utf-8")
            second_systems_template = (root / planner.SYSTEMS_TEMPLATE_REL).read_text(encoding="utf-8")

            self.assertEqual(first_report["open_blocker_total"], 2)
            self.assertEqual(second_report["open_blocker_total"], 2)
            self.assertEqual(first_plan_text, second_plan_text)
            self.assertEqual(first_report_text, second_report_text)
            self.assertEqual(first_bio_template, second_bio_template)
            self.assertEqual(first_systems_template, second_systems_template)


if __name__ == "__main__":
    unittest.main()
