from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ASSEMBLY = ROOT / "operations" / "release_assembly" / "oc_core"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class ReleaseAssemblyMachineTests(unittest.TestCase):
    def test_common_aggregator_is_not_versioned_release_toc(self) -> None:
        path = ASSEMBLY / "current_release_aggregator" / "OC_CORE_CURRENT_RELEASE_AGGREGATOR.json"
        payload = read_json(path)
        text = json.dumps(payload, ensure_ascii=False)
        self.assertEqual(payload["artifact_kind"], "OC_CORE_CURRENT_RELEASE_AGGREGATOR")
        self.assertNotRegex(text, re.compile(r"\b1\.3\.3\b"))
        self.assertNotIn("github", text.lower())
        self.assertNotIn("zenodo", text.lower())
        self.assertNotIn(".pdf", text.lower())
        self.assertNotIn(".zip", text.lower())
        self.assertGreater(payload["node_total"], 5000)

    def test_package_cascade_has_standard_artifact_set(self) -> None:
        path = ASSEMBLY / "package_structure" / "OC_CORE_RELEASE_PACKAGE_CASCADE.json"
        payload = read_json(path)
        self.assertEqual(payload["artifact_type_total"], 9)
        for artifact in payload["artifact_types"]:
            self.assertTrue(artifact["standard_package_member"])
            self.assertGreaterEqual(len(artifact["mini_cascade"]), 3)
            self.assertTrue(artifact["purpose"])
            self.assertTrue(artifact["known_error_classes_prevented"])

    def test_text_fill_rules_are_positive_and_negative(self) -> None:
        path = ASSEMBLY / "text_fill_rules" / "OC_CORE_TEXT_FILL_RULES.json"
        payload = read_json(path)
        text = json.dumps(payload, ensure_ascii=False)
        for phrase in ["reader payoff", "claim", "source trace", "raw ledgers", "control-plane", "unsupported overclaims"]:
            self.assertIn(phrase, text)
        self.assertEqual(len(payload["standard_sources"]), 3)

    def test_versioned_instance_assigns_release_number_downstream(self) -> None:
        instance_path = ROOT / "releases" / "oc_core_1_3_3" / "editorial" / "release_assembly" / "OC_CORE_RELEASE_INSTANCE_1.3.3.json"
        payload = read_json(instance_path)
        self.assertEqual(payload["release_identity"]["version"], "1.3.3")
        self.assertTrue(payload["release_identity"]["version_assigned_at_instance_layer"])
        self.assertEqual(
            payload["source_hashes"]["current_release_aggregator_hash"],
            read_json(ASSEMBLY / "current_release_aggregator" / "OC_CORE_CURRENT_RELEASE_AGGREGATOR.json")["artifact_hash"],
        )

    def test_old_versioned_toc_is_not_canonical(self) -> None:
        old_dir = ROOT / "releases" / "oc_core_1_3_3" / "editorial" / "oc_core_1_3_3_release_table_of_content"
        self.assertFalse(old_dir.exists())


if __name__ == "__main__":
    unittest.main()
