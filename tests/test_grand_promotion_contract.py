from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
FACTORY_PATH = REPO_ROOT / "tools" / "oc133_grand_promotion_contract.py"


def load_factory():
    spec = importlib.util.spec_from_file_location("oc133_grand_promotion_contract", FACTORY_PATH)
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


def lean_contract_text(factory, extra_symbols: tuple[str, ...] = ()) -> str:
    symbols = [ref.rsplit("::", 1)[1] for ref in factory.CONTRACT_LEAN_REFS]
    symbols.extend(extra_symbols)
    lines = ["namespace OC133GrandPromotion", ""]
    lines.extend(f"theorem {symbol} : True := by trivial" for symbol in symbols)
    lines.extend(["", "end OC133GrandPromotion", ""])
    return "\n".join(lines)


def passing_root(root: Path, factory) -> None:
    domains = ["physics", "chemistry", "biology", "systems", "mathematics"]
    write_json(
        root,
        factory.FORMAL_OBLIGATION_LEDGER_REL,
        {"requested_claim_classes": list(factory.DEFAULT_REQUIRED_CLAIM_CLASSES), "blocker_remains": False},
    )
    write_text(
        root,
        "formal/lean/OC133GrandPromotion.lean",
        lean_contract_text(factory, ("future_grand_toe_theorem",)),
    )
    write_text(root, "proofs/grand_promotion/GT-THM-1.md", "# fixture proof boundary\n")
    write_json(
        root,
        factory.CLAIM_LEDGER_REL,
        {
            "release_id": factory.RELEASE_ID,
            "release_promotion_allowed": True,
            "unsupported_promoted_total": 0,
            "rows": [
                {
                    "claim_id": "OC133-GRAND-TOE-PROMOTION",
                    "claim": "Grand TOE all-domain numerical prediction that predicts better than modern science under registered evidence.",
                    "claim_classes": list(factory.DEFAULT_REQUIRED_CLAIM_CLASSES),
                    "release_promotion_allowed": True,
                    "scientific_promotion_allowed": True,
                    "public_status": "PROMOTED_GRAND_TOE_FIXTURE",
                    "promotion_theorem_ids": ["GT-THM-1"],
                    "proof_refs": ["proofs/grand_promotion/GT-THM-1.md"],
                    "lean_refs": ["formal/lean/OC133GrandPromotion.lean::future_grand_toe_theorem"],
                    "finite_case_ids": ["FM-GRAND-POS", "FM-GRAND-NEG"],
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
        factory.GRAND_EMPIRICAL_REPORT_REL,
        {
            "verdict": "GRAND_EMPIRICAL_SUPPORT_ALLOWED",
            "grand_toe_support_allowed": True,
            "domain_predictive_superiority_supported": True,
            "blocked_domain_total": 0,
            "valid_evidence_pack_total": len(domains),
            "domains": [
                {
                    "domain": domain,
                    "grand_toe_support_allowed": True,
                    "valid_n": 20,
                    "minimum_n": 20,
                    "valid_pack_total": 1,
                    "status": "EVIDENCE_SUFFICIENT_PENDING_REVIEW",
                    "blockers": [],
                }
                for domain in domains
            ],
        },
    )
    write_json(
        root,
        factory.MODERN_SCIENCE_REPORT_REL,
        {
            "verdict": "MODERN_SCIENCE_SUPERIORITY_CERTIFIED",
            "release_promotion_allowed": True,
            "row_total": len(domains),
            "superiority_certified_total": len(domains),
            "blocked_superiority_total": 0,
            "blocking_summary": [],
            "domain_evidence_matrix": [
                {
                    "domain": domain,
                    "superiority_decision": {"certified": True},
                    "blocker_reason": {"blocked_by": []},
                }
                for domain in domains
            ],
        },
    )


class GrandPromotionContractTests(unittest.TestCase):
    def test_current_repo_blocks_grand_promotion_on_three_release_blockers(self) -> None:
        factory = load_factory()

        report = factory.build_grand_promotion_contract(REPO_ROOT)

        self.assertEqual(report["verdict"], "BLOCKED")
        self.assertFalse(report["promotion_allowed"])
        self.assertEqual(
            report["open_blockers"],
            [
                "grand_toe_claim_ledger_evidence",
                "grand_toe_empirical_superiority",
                "modern_science_comparator_superiority",
            ],
        )
        self.assertIn("all_domain_empirical_pack_valid", report["failed_gate_predicates"])
        self.assertIn("modern_science_superiority_certified", report["failed_gate_predicates"])

    def test_contract_accepts_only_when_claim_empirical_comparator_and_finite_refs_all_bind(self) -> None:
        factory = load_factory()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            passing_root(root, factory)

            report = factory.build_grand_promotion_contract(root)

            self.assertEqual(report["verdict"], "PASS")
            self.assertTrue(report["promotion_allowed"])
            self.assertEqual(report["open_blockers"], [])
            self.assertTrue(all(report["promotion_gate_vector"].values()))

    def test_global_finite_pass_does_not_substitute_for_dedicated_grand_finite_refs(self) -> None:
        factory = load_factory()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            passing_root(root, factory)
            claim_ledger = json.loads((root / factory.CLAIM_LEDGER_REL).read_text(encoding="utf-8"))
            claim_ledger["rows"][0]["finite_case_ids"] = []
            write_json(root, factory.CLAIM_LEDGER_REL, claim_ledger)

            report = factory.build_grand_promotion_contract(root)

            self.assertEqual(report["verdict"], "BLOCKED")
            self.assertTrue(report["promotion_gate_vector"]["finite_checks_passed"])
            self.assertFalse(report["promotion_gate_vector"]["finite_refs_bound"])
            self.assertFalse(report["promotion_gate_vector"]["finite_positive_negative_controls_bound"])
            self.assertEqual(report["open_blockers"], ["grand_toe_claim_ledger_evidence"])

    def test_stored_contract_report_is_synchronized(self) -> None:
        factory = load_factory()
        self.assertEqual(factory.check_stored(REPO_ROOT), [])


if __name__ == "__main__":
    unittest.main()
