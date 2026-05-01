from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
FACTORY_PATH = REPO_ROOT / "tools" / "oc133_strict_claim_evidence_synchronizer.py"


def load_factory():
    spec = importlib.util.spec_from_file_location("oc133_strict_claim_evidence_synchronizer", FACTORY_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_json(root: Path, rel_path: str, payload: dict) -> None:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_text(root: Path, rel_path: str, payload: str) -> None:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def promoted_grand_claim(**overrides):
    row = {
        "claim_id": "OC133-GRAND-TOE-PROMOTION",
        "claim": "Grand TOE all-domain numerical prediction that is irrefutable and predicts better than modern science.",
        "claim_classes": [
            "numerically_proven_toe",
            "all_domain_numerical_prediction",
            "predicts_better_than_modern_science",
        ],
        "release_promotion_allowed": True,
        "scientific_promotion_allowed": True,
        "public_status": "PROMOTED_GRAND_TOE_FIXTURE",
    }
    row.update(overrides)
    return row


def write_common_gates(root: Path, factory, *, pass_gates: bool) -> None:
    write_json(
        root,
        factory.GRAND_PROMOTION_CONTRACT_REL,
        {
            "promotion_allowed": pass_gates,
            "verdict": "PASS" if pass_gates else "BLOCKED",
        },
    )
    write_json(
        root,
        factory.GRAND_EMPIRICAL_REPORT_REL,
        {
            "verdict": "PASS" if pass_gates else "BLOCKED_PENDING_GENUINE_PER_DOMAIN_EVIDENCE",
            "grand_toe_support_allowed": pass_gates,
            "blocked_domain_total": 0 if pass_gates else 5,
        },
    )


class StrictClaimEvidenceSynchronizerTests(unittest.TestCase):
    def test_overclaim_emits_capability_work_orders_without_narrowing_claim(self) -> None:
        factory = load_factory()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            claim = promoted_grand_claim()
            write_json(
                root,
                factory.CLAIM_LEDGER_REL,
                {
                    "release_id": factory.RELEASE_ID,
                    "rows": [claim],
                },
            )
            write_json(root, factory.THEOREM_INVENTORY_REL, {"rows": []})
            write_json(root, factory.FINITE_CHECKS_REL, {"failure_total": 0, "rows": []})
            write_common_gates(root, factory, pass_gates=False)

            report = factory.build_claim_evidence_sync_report(root)

            self.assertEqual(report["verdict"], "BLOCKED")
            self.assertEqual(report["target_claim_ids"], ["OC133-GRAND-TOE-PROMOTION"])
            self.assertEqual(report["blocked_claim_total"], 1)
            issues = {row["missing_issue"] for row in report["work_orders"]}
            self.assertIn("promotion_theorem_ids_missing", issues)
            self.assertIn("finite_case_ref_missing", issues)
            self.assertIn("grand_promotion_contract_not_pass", issues)
            self.assertIn("grand_empirical_support_not_ready", issues)
            self.assertEqual(report["claim_assessments"][0]["claim"], claim["claim"])
            self.assertIn("never silently narrowed", report["work_order_policy"])

    def test_supported_promoted_grand_claim_passes_when_all_evidence_surfaces_bind(self) -> None:
        factory = load_factory()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_text(root, "proofs/grand_promotion/GT-THM-1.md", "# Fixture proof\n")
            write_text(
                root,
                "formal/lean/OC133GrandPromotion.lean",
                "namespace OC133GrandPromotion\n\ntheorem future_grand_toe_theorem : True := by trivial\n\nend OC133GrandPromotion\n",
            )
            write_json(
                root,
                factory.THEOREM_INVENTORY_REL,
                {
                    "rows": [
                        {
                            "theorem_id": "GT-THM-1",
                            "proof_sheet_ref": "proofs/grand_promotion/GT-THM-1.md",
                            "lean_ref": "formal/lean/OC133GrandPromotion.lean::future_grand_toe_theorem",
                        }
                    ],
                },
            )
            write_json(
                root,
                factory.FINITE_CHECKS_REL,
                {
                    "failure_total": 0,
                    "rows": [
                        {
                            "case_id": "FM-GRAND-POS",
                            "expected_verdict": "ACCEPT_PROMOTION",
                            "observed_verdict": "ACCEPT_PROMOTION",
                            "passed": True,
                        },
                        {
                            "case_id": "FM-GRAND-NEG",
                            "expected_verdict": "REJECT_PROMOTION",
                            "observed_verdict": "REJECT_PROMOTION",
                            "passed": True,
                        },
                    ],
                },
            )
            write_json(
                root,
                factory.CLAIM_LEDGER_REL,
                {
                    "release_id": factory.RELEASE_ID,
                    "rows": [
                        promoted_grand_claim(
                            promotion_theorem_ids=["GT-THM-1"],
                            proof_refs=["proofs/grand_promotion/GT-THM-1.md"],
                            lean_refs=["formal/lean/OC133GrandPromotion.lean::future_grand_toe_theorem"],
                            finite_case_ids=["FM-GRAND-POS", "FM-GRAND-NEG"],
                        )
                    ],
                },
            )
            write_common_gates(root, factory, pass_gates=True)

            report = factory.build_claim_evidence_sync_report(root)

            self.assertEqual(report["verdict"], "PASS")
            self.assertEqual(report["supported_claim_total"], 1)
            self.assertEqual(report["blocked_claim_total"], 0)
            self.assertEqual(report["work_order_total"], 0)

    def test_absent_grand_claim_surface_blocks_final_mission_readiness(self) -> None:
        factory = load_factory()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(root, factory.CLAIM_LEDGER_REL, {"release_id": factory.RELEASE_ID, "rows": []})
            write_json(root, factory.THEOREM_INVENTORY_REL, {"rows": []})
            write_json(root, factory.FINITE_CHECKS_REL, {"failure_total": 0, "rows": []})
            write_common_gates(root, factory, pass_gates=False)

            report = factory.build_claim_evidence_sync_report(root)

            self.assertEqual(report["target_claim_total"], 0)
            self.assertEqual(report["verdict"], "BLOCKED")
            self.assertFalse(report["gate_summary"]["contract_gate"]["target_claim_surface_present"])
            issues = {row["missing_issue"] for row in report["work_orders"]}
            self.assertIn("grand_claim_promotion_surface_missing", issues)

    def test_current_stored_sync_reports_are_synchronized(self) -> None:
        factory = load_factory()
        self.assertEqual(factory.check_stored(REPO_ROOT), [])


if __name__ == "__main__":
    unittest.main()
