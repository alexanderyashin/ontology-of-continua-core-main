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
        "prospective_lock_metadata": dict(runner.DEFAULT_PROSPECTIVE_LOCK_METADATA),
    }


def acquisition_row_without_lock_metadata(url: str) -> dict:
    row = acquisition_row(url)
    row.pop("prospective_lock_metadata")
    return row


class FakeResponse:
    def __init__(self, body: bytes, status: int = 200, headers: dict[str, str] | None = None) -> None:
        self.body = body
        self.status = status
        self.headers = headers or {"Content-Type": "application/json"}

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
            order_record = root / record["order_record_ref"]
            self.assertEqual(snapshot.read_bytes(), body)
            self.assertTrue(metadata.is_file())
            self.assertTrue(order_record.is_file())
            order_payload = json.loads(order_record.read_text(encoding="utf-8"))
            self.assertEqual(order_payload["source_bytes_sha256"], expected_sha)
            self.assertTrue(order_payload["sequence_proof"]["source_snapshot_pre_target_lock"])
            self.assertTrue(order_payload["sequence_proof"]["target_hidden_until_scoring"])
            self.assertTrue(order_payload["sequence_proof"]["prediction_materialization_required_before_scoring"])
            self.assertFalse(order_payload["sequence_proof"]["target_projection_unsealed_for_scoring"])
            self.assertFalse(order_payload["sequence_proof"]["scoring_started"])
            lock_payload = json.loads(lock.read_text(encoding="utf-8"))
            self.assertEqual(lock_payload["snapshot_sha256"], expected_sha)
            self.assertEqual(lock_payload["source_bytes_sha256"], expected_sha)
            self.assertEqual(lock_payload["order_record_sha256"], order_payload["order_record_sha256"])
            self.assertEqual(lock_payload["byte_count"], len(body))
            self.assertTrue(lock_payload["locks"]["no_send"])
            self.assertFalse(lock_payload["locks"]["publish_allowed"])
            self.assertFalse(lock_payload["locks"]["push_allowed"])
            self.assertFalse(lock_payload["locks"]["journal_submissions_allowed"])
            self.assertFalse(lock_payload["locks"]["doi_registration_allowed"])
            self.assertFalse(lock_payload["locks"]["zenodo_upload_allowed"])
            self.assertFalse(lock_payload["locks"]["registry_write_allowed"])
            self.assertFalse(lock_payload["locks"]["release_promotion_allowed"])
            self.assertFalse(lock_payload["scientific_pass"])

    def test_execute_network_reuses_valid_acquired_lock_without_refetch(self) -> None:
        body = b'{"already": "acquired"}\n'
        expected_sha = hashlib.sha256(body).hexdigest()
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

            with mock.patch.object(runner.urllib.request, "urlopen", return_value=FakeResponse(body)):
                first_report = runner.build_report(root, [packet], execute_network=True)

            with mock.patch.object(runner.urllib.request, "urlopen", side_effect=AssertionError("network")):
                resumed_report = runner.build_report(root, [packet], execute_network=True)

            first_record = first_report["records"][0]
            resumed_record = resumed_report["records"][0]
            self.assertEqual(first_record["status"], "ACQUIRED_READONLY")
            self.assertEqual(resumed_record["status"], "ACQUIRED_READONLY")
            self.assertFalse(resumed_record["network_executed"])
            self.assertTrue(resumed_record["resume_reused_existing_acquisition"])
            self.assertEqual(resumed_record["network_skipped_reason"], "VALID_EXISTING_ACQUIRED_READONLY_LOCK")
            self.assertEqual(resumed_record["sha256"], expected_sha)
            self.assertEqual(resumed_report["resumed_acquired_readonly_total"], 1)
            self.assertEqual(resumed_report["network_failure_total"], 0)
            self.assertFalse(resumed_report["scientific_pass"])

    def test_execute_network_retries_429_with_injected_backoff_without_sleeping(self) -> None:
        body = b'{"ok": "after retry"}\n'
        sleeper = mock.Mock()
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

            with mock.patch.object(
                runner.urllib.request,
                "urlopen",
                side_effect=[
                    FakeResponse(b"rate limited", status=429, headers={"Retry-After": "0"}),
                    FakeResponse(body),
                ],
            ) as urlopen:
                report = runner.build_report(
                    root,
                    [packet],
                    execute_network=True,
                    retry_delays=(0.0,),
                    max_attempts=2,
                    sleeper=sleeper,
                )

            self.assertEqual(urlopen.call_count, 2)
            sleeper.assert_called_once_with(0.0)
            record = report["records"][0]
            self.assertEqual(record["status"], "ACQUIRED_READONLY")
            self.assertEqual(record["network_attempt_total"], 2)
            self.assertEqual(record["retry_attempts"][0]["http_status"], 429)
            self.assertTrue(record["retry_attempts"][0]["transient"])
            self.assertEqual(record["retry_attempts"][0]["applied_retry_delay_seconds"], 0.0)
            self.assertEqual(report["retry_report"]["success_after_retry_total"], 1)
            self.assertEqual(report["retry_queue_total"], 0)
            self.assertFalse(report["retry_report"]["scientific_pass"])

    def test_transient_exhaustion_produces_retry_queue_without_snapshot_lock(self) -> None:
        sleeper = mock.Mock()
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

            with mock.patch.object(
                runner.urllib.request,
                "urlopen",
                side_effect=[
                    FakeResponse(b"rate limited", status=429, headers={"Retry-After": "0"}),
                    FakeResponse(b"still rate limited", status=429, headers={"Retry-After": "0"}),
                ],
            ):
                report = runner.build_report(
                    root,
                    [packet],
                    execute_network=True,
                    retry_delays=(0.0,),
                    max_attempts=2,
                    sleeper=sleeper,
                )

            record = report["records"][0]
            self.assertEqual(record["status"], "HTTP_STATUS_NOT_SUCCESS")
            self.assertTrue(record["retry_queue_eligible"])
            self.assertEqual(report["retry_queue_total"], 1)
            self.assertEqual(report["retry_queue"][0]["http_status"], 429)
            self.assertEqual(report["network_failure_total"], 1)
            self.assertFalse((root / record["snapshot_ref"]).exists())
            self.assertFalse((root / record["lock_ref"]).exists())
            self.assertFalse(report["scientific_pass"])

    def test_weakened_existing_lock_is_not_reused_and_no_send_lock_is_restored(self) -> None:
        first_body = b'{"lock": "strict"}\n'
        second_body = b'{"lock": "restored"}\n'
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

            with mock.patch.object(runner.urllib.request, "urlopen", return_value=FakeResponse(first_body)):
                first_report = runner.build_report(root, [packet], execute_network=True)

            lock_path = root / first_report["records"][0]["lock_ref"]
            weakened_lock = json.loads(lock_path.read_text(encoding="utf-8"))
            weakened_lock["locks"]["publish_allowed"] = True
            write_json(lock_path, weakened_lock)

            with mock.patch.object(runner.urllib.request, "urlopen", return_value=FakeResponse(second_body)) as urlopen:
                report = runner.build_report(root, [packet], execute_network=True)

            urlopen.assert_called_once()
            record = report["records"][0]
            self.assertTrue(record["network_executed"])
            self.assertFalse(record["resume_reused_existing_acquisition"])
            restored_lock = json.loads(lock_path.read_text(encoding="utf-8"))
            self.assertEqual(restored_lock["locks"], runner.NO_SEND_LOCKS)
            self.assertFalse(restored_lock["scientific_pass"])
            self.assertEqual(report["locks"], runner.NO_SEND_LOCKS)
            self.assertFalse(report["publish_allowed"])
            self.assertFalse(report["scientific_pass"])

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
        nist_asd_url = (
            "https://physics.nist.gov/cgi-bin/ASD/lines1.pl?spectra=H&limits_type=0&low_w=&upp_w="
            "&unit=1&de=0&format=3&line_out=0&remove_js=on&en_unit=1&output=0&page_size=50"
            "&show_obs_wl=1&show_calc_wl=1&show_wn=1"
        )
        allowed_urls = {
            "NCBI EUtils": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=gds",
            "PubChem PUG REST": "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/962/JSON",
            "World Bank API": "https://api.worldbank.org/v2/country/USA/indicator/NY.GDP.MKTP.CD?format=json",
            "NIST physics constants": "https://physics.nist.gov/cuu/Constants/Table/allascii.txt",
            "NIST ASD hydrogen Balmer lines TSV": nist_asd_url,
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

        blocked, matched_rule, blockers = runner.allowlist_match(nist_asd_url.replace("format=3", "format=0"))
        self.assertFalse(blocked)
        self.assertEqual(matched_rule, "NIST ASD hydrogen Balmer lines TSV")
        self.assertIn("QUERY_PARAM_VALUE_NOT_ALLOWED::format", blockers)

        blocked, _, blockers = runner.allowlist_match(
            nist_asd_url.replace("/cgi-bin/ASD/lines1.pl", "/cgi-bin/ASD/energy1.pl")
        )
        self.assertFalse(blocked)
        self.assertTrue(any(blocker.startswith("URL_NOT_IN_OFFICIAL_ALLOWLIST::") for blocker in blockers))

    def test_nist_asd_physics_request_passes_dry_run_without_network(self) -> None:
        nist_asd_url = (
            "https://physics.nist.gov/cgi-bin/ASD/lines1.pl?spectra=H&limits_type=0&low_w=&upp_w="
            "&unit=1&de=0&format=3&line_out=0&remove_js=on&en_unit=1&output=0&page_size=50"
            "&show_obs_wl=1&show_calc_wl=1&show_wn=1"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet = root / "validation/heldout/grand_science/physics/PACKET_ACQUISITION_PACKET.json"
            write_json(
                packet,
                packet_payload(
                    acquisition_row(nist_asd_url, "validation/_raw/physics_nist_asd_hydrogen_balmer_lines_v1.tsv")
                ),
            )

            with mock.patch.object(runner.urllib.request, "urlopen", side_effect=AssertionError("network")):
                report = runner.build_report(root, [packet], execute_network=False)

            self.assertEqual(report["validated_for_network_total"], 1)
            self.assertEqual(report["validation_blocked_total"], 0)
            self.assertEqual(report["records"][0]["allowlist_rule"], "NIST ASD hydrogen Balmer lines TSV")
            self.assertEqual(report["records"][0]["status"], "DRY_RUN_NETWORK_NOT_EXECUTED")

    def test_execute_network_blocks_missing_or_post_scoring_lock_metadata_before_network(self) -> None:
        url = "https://physics.nist.gov/cuu/Constants/Table/allascii.txt"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet = root / "validation/heldout/grand_science/physics/PACKET_ACQUISITION_PACKET.json"
            post_scoring = acquisition_row(url, "validation/_raw/post_scoring.txt")
            post_scoring["acquisition_id"] = "TEST-POST-SCORING"
            post_scoring["prospective_lock_metadata"]["scoring_started"] = True
            post_scoring["prospective_lock_metadata"]["scoring_started_at"] = "2026-05-01T00:00:00Z"
            write_json(
                packet,
                packet_payload(
                    acquisition_row_without_lock_metadata(url),
                    post_scoring,
                ),
            )

            with mock.patch.object(runner.urllib.request, "urlopen") as urlopen:
                report = runner.build_report(root, [packet], execute_network=True)

            urlopen.assert_not_called()
            by_id = {row["acquisition_id"]: row for row in report["records"]}
            self.assertEqual(by_id["TEST-OFFICIAL-SNAPSHOT-0001"]["status"], "VALIDATION_BLOCKED")
            self.assertIn(
                "PROSPECTIVE_LOCK_METADATA_MISSING",
                by_id["TEST-OFFICIAL-SNAPSHOT-0001"]["validation_blockers"],
            )
            self.assertEqual(by_id["TEST-POST-SCORING"]["status"], "VALIDATION_BLOCKED")
            self.assertIn("POST_SCORING_ACQUISITION_NOT_ALLOWED", by_id["TEST-POST-SCORING"]["validation_blockers"])
            self.assertIn("PROSPECTIVE_LOCK_METADATA_INVALID::scoring_started", report["blockers"])
            self.assertEqual(report["execution_blocker_packet"]["status"], "BLOCKED")

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
