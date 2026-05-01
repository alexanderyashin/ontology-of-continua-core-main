from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools import oc133_biology_target_official_bundle_builder as builder


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8", newline="\n")


def fake_record(acquisition_id: str, snapshot_ref: str, sha256: str = "a" * 64) -> dict:
    return {
        "acquisition_id": acquisition_id,
        "status": "ACQUIRED_READONLY",
        "snapshot_ref": snapshot_ref,
        "sha256": sha256,
        "order_record_ref": f"validation/heldout/acquisition_runs/oc133_official_readonly/order_records/{acquisition_id}.order.json",
    }


def geoprofile_summary(row_total: int = 20) -> dict:
    uids = [str(65630000 + idx) for idx in range(row_total)]
    result = {"uids": uids}
    for idx, uid in enumerate(uids, start=1):
        observed = float(40 + idx)
        result[uid] = {
            "uid": uid,
            "gds": "3716",
            "gpl": "96",
            "title": "Breast cancer: histologically normal breast epithelium",
            "taxon": "Homo sapiens",
            "gdstype": "Expression profiling by array",
            "valtype": "count",
            "idref": f"{90000 + idx}_at",
            "genename": f"GENE{idx}",
            "genedesc": f"official test gene {idx}",
            "vmin": f"{10 + idx}.0",
            "vmax": f"{200 + idx}.0",
            "rstd": int(observed),
            "rmean": int(observed),
        }
    return {"header": {"type": "esummary"}, "result": result}


class BiologyTargetOfficialBundleBuilderTests(unittest.TestCase):
    def test_search_packet_uses_allowlisted_ncbi_eutils_only(self) -> None:
        packet = builder.build_search_packet()
        row = packet["missing_official_snapshots"][0]

        self.assertTrue(row["official_endpoint_url"].startswith("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"))
        self.assertTrue(row["no_send_lock"])
        self.assertTrue(row["prospective_lock_metadata"]["target_hidden_until_scoring"])
        self.assertNotIn("ftp.ncbi.nlm.nih.gov", row["official_endpoint_url"])

    def test_builder_blocks_without_acquired_search_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            with mock.patch.object(
                builder,
                "run_packet",
                return_value={"records": [{"acquisition_id": builder.SEARCH_ACQUISITION_ID, "status": "VALIDATION_BLOCKED"}]},
            ):
                report = builder.build_or_execute(root, execute_network=False, max_attempts=1)

            self.assertFalse(report["ready_for_factory"])
            self.assertIn("OFFICIAL_GEOPROFILES_SEARCH_SNAPSHOT_NOT_ACQUIRED", report["blockers"])

    def test_build_official_bundle_from_acquired_summary_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary_ref = "validation/heldout/acquisition_runs/oc133_official_readonly/snapshots/summary.json"
            write_json(root / summary_ref, geoprofile_summary())
            search_record = fake_record(builder.SEARCH_ACQUISITION_ID, "validation/heldout/acquisition_runs/search.json")
            summary_record = fake_record(builder.SUMMARY_ACQUISITION_ID, summary_ref)

            bundle, blockers = builder.build_official_bundle(root, search_record, summary_record)

            self.assertEqual(blockers, [])
            self.assertEqual(bundle["schema_id"], "OC133_BIOLOGY_TARGET_OFFICIAL_BUNDLE_v1")
            self.assertEqual(len(bundle["biological_target_rows"]), 20)
            self.assertTrue(bundle["source_separation"]["pre_target_lock"])
            self.assertTrue(bundle["source_separation"]["target_hidden_until_scoring"])
            row = bundle["biological_target_rows"][0]
            self.assertEqual(row["biological_target_kind"], "gene_expression_profile_ranked_mean_target")
            self.assertEqual(row["predicted_value"], row["observed_value"])
            self.assertGreater(row["comparator_prediction"], row["observed_value"])


if __name__ == "__main__":
    unittest.main()
