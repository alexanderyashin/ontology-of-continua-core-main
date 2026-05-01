from __future__ import annotations

import unittest

from tools import logion_dirty_tree_governance as governance


class LogionDirtyTreeGovernanceTests(unittest.TestCase):
    def test_public_path_classification_covers_release_background_and_legacy(self) -> None:
        self.assertEqual(
            governance.classify_public_path("releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_RELEASE_SCORECARD_latest.json"),
            "oc133_release_package",
        )
        self.assertEqual(
            governance.classify_public_path("validation/heldout/grand_science/biology/ncbi_batch/report.json"),
            "background_science",
        )
        self.assertEqual(
            governance.classify_public_path("releases/oc_core_1_3_2/editorial/OC_CORE_1_3_2_SHA256SUMS"),
            "legacy_1_3_2",
        )

    def test_private_anchor_metadata_is_classified(self) -> None:
        self.assertEqual(
            governance.classify_private_path("logion/k0/governance/status/OC_CORE_1_3_RELEASE_ANCHOR_latest.json"),
            "private_release_anchor_governance",
        )


if __name__ == "__main__":
    unittest.main()
