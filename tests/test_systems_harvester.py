from __future__ import annotations
import json
import shutil
import tempfile
import urllib.parse
import unittest
from pathlib import Path
from unittest.mock import patch

from validation.heldout.harvesters import systems_harvester as harvester


REPO_ROOT = Path(__file__).resolve().parents[1]


def copy_fixture(root: Path, rel: str) -> None:
    source = REPO_ROOT / rel
    target = root / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def copy_required(root: Path) -> None:
    copy_fixture(root, "benchmarks/grand_science/domain_requirements.json")
    copy_fixture(root, "validation/heldout/acquisition_plans/biology_systems/OC133_BIOLOGY_SYSTEMS_ACQUISITION_PLAN.json")
    copy_fixture(root, "validation/_raw/systems_world_bank_gdp.txt")


def world_bank_linear_payload(start_year: int = 2000, end_year: int = 2024) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for year in range(start_year, end_year + 1):
        value = 1000.0 + float(year - start_year) * 12.0
        rows.append(
            {
                "indicator": {"id": "NY.GDP.MKTP.CD", "value": "GDP (current US$)"},
                "country": {"id": "USA", "value": "United States"},
                "countryiso3code": "USA",
                "date": str(year),
                "value": value,
                "unit": "",
                "obs_status": "",
                "decimal": 0,
            }
        )
    return [{"dummy": True}, rows]


class FakeResponse:
    def __init__(self, body: bytes):
        self._body = body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return None

    def read(self) -> bytes:
        return self._body


class SystemsHarvesterTests(unittest.TestCase):
    def test_offline_snapshot_build_is_deterministic_and_blocked_for_low_n(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_required(root)

            report, protocol, pack, rows = harvester.build_payload(root, offline=True)

            self.assertEqual(report["candidate_pack_total"], 1)
            self.assertEqual(report["valid_candidate_pack_total"], 0)
            self.assertEqual(report["blocked_domain_total"], 1)
            self.assertEqual(report["verdict"], "BLOCKED_PENDING_GENUINE_EVIDENCE")
            self.assertFalse(pack["grand_toe_support_allowed"])
            self.assertEqual(pack["domain"], "systems")
            self.assertLess(pack["n"], 20)
            self.assertGreater(len(rows), 0)
            self.assertIn("N_BELOW_MINIMUM", " ".join(report["blockers"]))
            self.assertGreaterEqual(len(protocol["rows"]), 1)
            self.assertEqual(protocol["rows"][0]["domain"], "systems")

    def test_endpoint_payload_can_support_valid_pack(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_required(root)
            plan = {
                "rows": [
                    {
                        "domain": "systems",
                        "official_source_refs": [
                            {"kind": "official_endpoint", "url": "https://api.worldbank.org/v2/country/USA/indicator/NY.GDP.MKTP.CD?format=json&per_page=1000"}
                        ],
                    }
                ]
            }
            plan_path = root / "validation/heldout/acquisition_plans/biology_systems/OC133_BIOLOGY_SYSTEMS_ACQUISITION_PLAN.json"
            plan_path.parent.mkdir(parents=True, exist_ok=True)
            plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

            payload = world_bank_linear_payload(2000, 2025)

            with patch(
                "validation.heldout.harvesters.systems_harvester.urllib.request.urlopen",
                return_value=FakeResponse(json.dumps(payload).encode("utf-8")),
            ):
                report, protocol, pack, rows = harvester.build_payload(root, offline=False, acquisition_plan_ref=str(plan_path))

            self.assertTrue(pack["grand_toe_support_allowed"])
            self.assertEqual(pack["n"], 24)
            self.assertEqual(report["valid_candidate_pack_total"], 1)
            self.assertEqual(report["blocked_domain_total"], 0)
            self.assertEqual(report["verdict"], "READY_FOR_PARENT_REGISTRY_REVIEW")
            self.assertGreater(len(protocol["rows"]), 0)
            self.assertEqual(protocol["rows"][0]["candidate_pack_total"], 1)
            self.assertEqual(rows[0].country.split(":")[0], "USA")

    def test_official_endpoint_is_expanded_and_pinned_for_offline_replay(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_required(root)
            plan = {
                "rows": [
                    {
                        "domain": "systems",
                        "official_source_refs": [
                            {"kind": "official_endpoint", "url": "https://api.worldbank.org/v2/country/USA/indicator/NY.GDP.MKTP.CD?format=json&per_page=5"}
                        ],
                    }
                ]
            }
            plan_path = root / "validation/heldout/acquisition_plans/biology_systems/OC133_BIOLOGY_SYSTEMS_ACQUISITION_PLAN.json"
            plan_path.parent.mkdir(parents=True, exist_ok=True)
            plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
            payload = world_bank_linear_payload(2000, 2025)
            seen_urls: list[str] = []

            def fake_urlopen(request, timeout):
                seen_urls.append(request.full_url)
                return FakeResponse(json.dumps(payload).encode("utf-8"))

            with patch(
                "validation.heldout.harvesters.systems_harvester.urllib.request.urlopen",
                side_effect=fake_urlopen,
            ):
                endpoint_report, _protocol, endpoint_pack = harvester.write_outputs(
                    root,
                    offline=False,
                    acquisition_plan_ref=str(plan_path),
                )

            self.assertTrue(endpoint_pack["grand_toe_support_allowed"])
            self.assertEqual(endpoint_report["source_kind"], "official_endpoint")
            self.assertEqual(endpoint_report["snapshot_ref"], harvester.PINNED_OFFICIAL_SNAPSHOT_REL)
            self.assertTrue((root / harvester.PINNED_OFFICIAL_SNAPSHOT_REL).is_file())
            parsed_query = urllib.parse.parse_qs(urllib.parse.urlparse(seen_urls[0]).query)
            self.assertEqual(parsed_query["per_page"], [str(harvester.DEFAULT_OFFICIAL_PER_PAGE)])

            offline_report, _protocol, offline_pack, _rows = harvester.build_payload(
                root,
                offline=True,
                acquisition_plan_ref=str(plan_path),
            )
            self.assertEqual(offline_report["source_kind"], "pinned_official_snapshot")
            self.assertTrue(offline_pack["grand_toe_support_allowed"])
            self.assertEqual(offline_pack["source_separation"]["mode"], "target_blind")

    def test_write_outputs_materializes_harvested_systems_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_required(root)

            report, _protocol, _pack = harvester.write_outputs(root)

            report_path = root / harvester.REPORT_REL
            protocol_path = root / harvester.PROTOCOL_REL
            pack_path = root / harvester.PACK_REL

            self.assertTrue(report_path.is_file())
            self.assertTrue(protocol_path.is_file())
            self.assertTrue(pack_path.is_file())
            self.assertFalse(json.loads(pack_path.read_text(encoding="utf-8"))["grand_toe_support_allowed"])
            self.assertEqual(json.loads(report_path.read_text(encoding="utf-8"))["candidate_pack_ref"], harvester.PACK_REL)


if __name__ == "__main__":
    unittest.main()
