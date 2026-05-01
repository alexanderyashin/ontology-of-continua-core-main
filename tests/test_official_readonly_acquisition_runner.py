from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools import oc133_official_readonly_acquisition_runner as runner


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")


def packet_payload(*rows: dict) -> dict:
    return {
        "schema_id": "TEST_ACQUISITION_PACKET_v1",
        "release_id": "oc_core_1_3_3",
        "no_send": True,
        "publish_allowed": False,
        "push_allowed": False,
        "missing_official_snapshots": list(rows),
    }


def acquisition_row(url: str, expected_ref: str = "validation/_raw/test_snapshot.json") -> dict:
    return {
        "acquisition_id": "TEST-OFFICIAL-SNAPSHOT-0001",
        "official_source": "test official source",
        "official_endpoint_url": url,
        "expected_local_snapshot_ref": expected_ref,
        "no_send_lock": True,
    }


class FakeResponse:
    status = 200
    headers = {"Content-Type": "application/json"}

    def __init__(self, body: bytes) -> None:
        self.body = body

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def read(self, size: int = -1) -> bytes:
        return self.body

    def getcode(self) -> int:
        return self.status


class OfficialReadonlyAcquisitionRunnerTests(unittest.TestCase):
    def test_dry_run_validates_without_calling_network(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet = root / "validation/heldout/grand_science/biology/ncbi_batch/PACKET_ACQUISITION_PACKET.json"
            write_json(
                packet,
                packet_payload(
                    acquisition_row(
                        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=gds&retmode=json"
                    )
                ),
            )

            with mock.patch.object(runner.urllib.request, "urlopen", side_effect=AssertionError("network")):
                report = runner.build_report(root, [packet], execute_network=False)

            self.assertEqual(report["mode"], "dry_run_check")
            self.assertEqual(report["request_total"], 1)
            self.assertEqual(report["validated_for_network_total"], 1)
            self.assertEqual(report["records"][0]["status"], "DRY_RUN_NETWORK_NOT_EXECUTED")
            self.assertFalse(report["records"][0]["network_executed"])
            self.assertEqual(report["records"][0]["byte_count"], 0)
            self.assertEqual(report["records"][0]["sha256"], "")
            self.assertEqual(report["records"][0]["allowlist_rule"], "NCBI EUtils")
            self.assertFalse(report["scientific_pass"])

    def test_execute_network_writes_pinned_snapshot_metadata_and_lock(self) -> None:
        body = b'{"ok": true}\n'
        expected_sha = hashlib.sha256(body).hexdigest()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet = root / "validation/heldout/grand_science/chemistry/pubchem/PACKET_ACQUISITION_PACKET.json"
            write_json(
                packet,
                packet_payload(
                    acquisition_row(
                        "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/962/property/MolecularFormula/JSON"
                    )
                ),
            )

            with mock.patch.object(runner.urllib.request, "urlopen", return_value=FakeResponse(body)) as urlopen:
                report = runner.build_report(root, [packet], execute_network=True)

            urlopen.assert_called_once()
            request = urlopen.call_args.args[0]
            self.assertEqual(request.full_url, report["records"][0]["official_endpoint_url"])
            self.assertNotIn("Authorization", request.headers)

            record = report["records"][0]
            self.assertEqual(record["status"], "ACQUIRED_READONLY")
            self.assertEqual(record["http_status"], 200)
            self.assertEqual(record["byte_count"], len(body))
            self.assertEqual(record["sha256"], expected_sha)
            self.assertFalse(report["scientific_pass"])
            self.assertFalse(report["grand_toe_support_allowed"])

            snapshot = root / record["snapshot_ref"]
            metadata = root / record["snapshot_metadata_ref"]
            lock = root / record["lock_ref"]
            self.assertEqual(snapshot.read_bytes(), body)
            self.assertTrue(metadata.is_file())
            lock_payload = json.loads(lock.read_text(encoding="utf-8"))
            self.assertEqual(lock_payload["snapshot_sha256"], expected_sha)
            self.assertEqual(lock_payload["byte_count"], len(body))
            self.assertTrue(lock_payload["locks"]["no_send"])
            self.assertFalse(lock_payload["locks"]["publish_allowed"])
            self.assertFalse(lock_payload["locks"]["push_allowed"])
            self.assertFalse(lock_payload["scientific_pass"])

    def test_rejects_non_allowlisted_url_and_redacts_token_without_network(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet = root / "validation/heldout/grand_science/systems/PACKET_ACQUISITION_PACKET.json"
            write_json(
                packet,
                packet_payload(
                    acquisition_row("https://example.com/data?access_token=SECRET_VALUE&format=json")
                ),
            )

            with mock.patch.object(runner.urllib.request, "urlopen") as urlopen:
                report = runner.build_report(root, [packet], execute_network=True)

            urlopen.assert_not_called()
            record = report["records"][0]
            self.assertEqual(record["status"], "VALIDATION_BLOCKED")
            self.assertFalse(record["network_executed"])
            self.assertIn("SENSITIVE_QUERY_TOKEN_NOT_ALLOWED::access_token", record["validation_blockers"])
            self.assertTrue(
                any(blocker.startswith("URL_NOT_IN_OFFICIAL_ALLOWLIST::") for blocker in record["validation_blockers"])
            )
            serialized = json.dumps(report)
            self.assertNotIn("SECRET_VALUE", serialized)
            self.assertIn("access_token=REDACTED", record["official_endpoint_url"])

    def test_allowlist_accepts_only_named_official_endpoint_families(self) -> None:
        allowed_urls = {
            "NCBI EUtils": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=gds",
            "PubChem PUG REST": "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/962/JSON",
            "World Bank API": "https://api.worldbank.org/v2/country/USA/indicator/NY.GDP.MKTP.CD?format=json",
            "NIST physics constants": "https://physics.nist.gov/cuu/Constants/Table/allascii.txt",
            "NIST Chemistry WebBook": "https://webbook.nist.gov/cgi/cbook.cgi?ID=C7732185&Units=SI",
        }
        for rule_name, url in allowed_urls.items():
            with self.subTest(rule_name=rule_name):
                allowed, matched_rule, blockers = runner.allowlist_match(url)
                self.assertTrue(allowed)
                self.assertEqual(matched_rule, rule_name)
                self.assertEqual(blockers, [])

        blocked, _, blockers = runner.allowlist_match("https://pubchem.ncbi.nlm.nih.gov/not-pug/data")
        self.assertFalse(blocked)
        self.assertTrue(any(blocker.startswith("URL_NOT_IN_OFFICIAL_ALLOWLIST::") for blocker in blockers))

    def test_unsafe_expected_snapshot_ref_blocks_execution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet = root / "validation/heldout/grand_science/physics/PACKET_ACQUISITION_PACKET.json"
            write_json(
                packet,
                packet_payload(
                    acquisition_row(
                        "https://physics.nist.gov/cuu/Constants/Table/allascii.txt",
                        "../outside.json",
                    )
                ),
            )

            with mock.patch.object(runner.urllib.request, "urlopen") as urlopen:
                report = runner.build_report(root, [packet], execute_network=True)

            urlopen.assert_not_called()
            self.assertEqual(report["records"][0]["status"], "VALIDATION_BLOCKED")
            self.assertIn("EXPECTED_LOCAL_SNAPSHOT_REF_UNSAFE", report["records"][0]["validation_blockers"])

    def test_write_reports_materializes_run_and_public_report_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet = root / "validation/heldout/grand_science/biology/PACKET_ACQUISITION_PACKET.json"
            write_json(
                packet,
                packet_payload(
                    acquisition_row(
                        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=gds&retmode=json"
                    )
                ),
            )

            with mock.patch.object(runner.urllib.request, "urlopen", side_effect=AssertionError("network")):
                report = runner.build_report(root, [packet], execute_network=False)
                runner.write_reports(root, report)

            self.assertTrue((root / runner.RUN_REPORT_REL).is_file())
            self.assertTrue((root / runner.PUBLIC_REPORT_REL).is_file())
            self.assertEqual(runner.check_stored(root, [packet]), [])

    def test_standard_logion_write_alias_materializes_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet = root / "validation/heldout/grand_science/biology/PACKET_ACQUISITION_PACKET.json"
            write_json(
                packet,
                packet_payload(
                    acquisition_row(
                        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=gds&retmode=json"
                    )
                ),
            )

            with mock.patch.object(runner.urllib.request, "urlopen", side_effect=AssertionError("network")):
                exit_code = runner.main(["--root", str(root), "--packet", packet.relative_to(root).as_posix(), "--write"])

            self.assertEqual(exit_code, 0)
            self.assertTrue((root / runner.RUN_REPORT_REL).is_file())
            self.assertTrue((root / runner.REPORT_JSON_REL).is_file())


if __name__ == "__main__":
    unittest.main()
