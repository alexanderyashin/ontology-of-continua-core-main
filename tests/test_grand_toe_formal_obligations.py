from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
FACTORY_PATH = REPO_ROOT / "tools" / "oc133_grand_toe_formal_obligations.py"


def load_factory():
    spec = importlib.util.spec_from_file_location("oc133_grand_toe_formal_obligations", FACTORY_PATH)
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


def lean_text(*symbols: str) -> str:
    lines = ["namespace Fixture", ""]
    lines.extend(f"theorem {symbol} : True := by trivial" for symbol in symbols)
    lines.extend(["", "end Fixture", ""])
    return "\n".join(lines)


def write_machine_nonpromotion_surface(root: Path, factory) -> None:
    write_text(root, factory.PROOF_SHEET_REF, "# Grand TOE formal blocker\n")
    write_text(
        root,
        "formal/lean/OC133V12.lean",
        lean_text(*(ref.rsplit("::", 1)[1] for ref in factory.LEAN_REFS)),
    )
    write_json(
        root,
        factory.FINITE_CHECKS_REF,
        {
            "failure_total": 0,
            "rows": [
                {
                    "case_id": "FM-GRAND-TOE-FORMAL-CURRENT-REJECT",
                    "theorem_id": factory.CLAIM_ID,
                    "expected_verdict": "REJECT_PROMOTION",
                    "observed_verdict": "REJECT_PROMOTION",
                    "passed": True,
                },
                {
                    "case_id": "FM-GRAND-TOE-FORMAL-HYPOTHETICAL-ACCEPT",
                    "theorem_id": factory.CLAIM_ID,
                    "expected_verdict": "ACCEPT_PROMOTION",
                    "observed_verdict": "ACCEPT_PROMOTION",
                    "passed": True,
                },
                {
                    "case_id": "FM-GRAND-TOE-FORMAL-MISSING-FINITE-REJECT",
                    "theorem_id": factory.CLAIM_ID,
                    "expected_verdict": "REJECT_PROMOTION",
                    "observed_verdict": "REJECT_PROMOTION",
                    "passed": True,
                },
            ],
        },
    )


def write_dependencies(root: Path, factory, *, passed: bool) -> None:
    domains = ["physics", "chemistry", "biology", "systems", "mathematics"]
    write_json(
        root,
        factory.GRAND_EMPIRICAL_REPORT_REF,
        {
            "verdict": "GRAND_EMPIRICAL_SUPPORT_ALLOWED" if passed else "BLOCKED_PENDING_GENUINE_PER_DOMAIN_EVIDENCE",
            "grand_toe_support_allowed": passed,
            "domain_predictive_superiority_supported": passed,
            "blocked_domain_total": 0 if passed else len(domains),
            "domains": [
                {
                    "domain": domain,
                    "grand_toe_support_allowed": passed,
                    "valid_n": 20 if passed else 0,
                    "minimum_n": 20,
                    "valid_pack_total": 1 if passed else 0,
                    "blockers": [] if passed else ["NO_VALID_PROSPECTIVE_OR_TARGET_BLIND_EVIDENCE_PACK"],
                }
                for domain in domains
            ],
        },
    )
    write_json(
        root,
        factory.MODERN_SCIENCE_REPORT_REF,
        {
            "verdict": "MODERN_SCIENCE_SUPERIORITY_CERTIFIED" if passed else "BLOCKED_NO_MODERN_SCIENCE_SUPERIORITY_CERTIFIED",
            "release_promotion_allowed": passed,
            "row_total": len(domains),
            "superiority_certified_total": len(domains) if passed else 0,
            "blocked_superiority_total": 0 if passed else len(domains),
            "blocking_summary": [] if passed else ["No lane has clean-checkout independent replay recorded."],
            "domain_evidence_matrix": [
                {
                    "domain": domain,
                    "superiority_decision": {"certified": passed},
                    "blocker_reason": {"blocked_by": [] if passed else ["independent_replay_passes_from_clean_checkout"]},
                }
                for domain in domains
            ],
        },
    )


def promoted_grand_claim(**overrides) -> dict:
    row = {
        "claim_id": "OC133-GRAND-TOE-PROMOTION",
        "claim": "Grand TOE all-domain numerical prediction that predicts better than modern science.",
        "claim_classes": [
            "numerically_proven_toe",
            "all_domain_numerical_prediction",
            "predicts_better_than_modern_science",
        ],
        "release_promotion_allowed": True,
        "scientific_promotion_allowed": True,
        "public_status": "PROMOTED_GRAND_TOE_FIXTURE",
        "promotion_theorem_ids": ["GT-THM-1"],
        "proof_refs": ["proofs/grand_promotion/GT-THM-1.md"],
        "lean_refs": ["formal/lean/OC133GrandPromotion.lean::future_grand_toe_theorem"],
        "finite_case_ids": ["FM-GRAND-POS", "FM-GRAND-NEG"],
    }
    row.update(overrides)
    return row


def write_promoted_claim_surface(root: Path, factory, *, claim: dict | None = None, dependencies_passed: bool = True) -> None:
    write_machine_nonpromotion_surface(root, factory)
    write_dependencies(root, factory, passed=dependencies_passed)
    write_text(root, "proofs/grand_promotion/GT-THM-1.md", "# Future fixture theorem proof\n")
    write_text(root, "formal/lean/OC133GrandPromotion.lean", lean_text("future_grand_toe_theorem"))
    write_json(
        root,
        factory.THEOREM_INVENTORY_REF,
        {
            "rows": [
                {
                    "theorem_id": "GT-THM-1",
                    "proof_sheet_ref": "proofs/grand_promotion/GT-THM-1.md",
                    "lean_ref": "formal/lean/OC133GrandPromotion.lean::future_grand_toe_theorem",
                }
            ]
        },
    )
    finite = json.loads((root / factory.FINITE_CHECKS_REF).read_text(encoding="utf-8"))
    finite["rows"].extend(
        [
            {
                "case_id": "FM-GRAND-POS",
                "theorem_id": "GT-THM-1",
                "expected_verdict": "ACCEPT_PROMOTION",
                "observed_verdict": "ACCEPT_PROMOTION",
                "passed": True,
            },
            {
                "case_id": "FM-GRAND-NEG",
                "theorem_id": "GT-THM-1",
                "expected_verdict": "REJECT_PROMOTION",
                "observed_verdict": "REJECT_PROMOTION",
                "passed": True,
            },
        ]
    )
    write_json(root, factory.FINITE_CHECKS_REF, finite)
    write_json(
        root,
        factory.CLAIM_LEDGER_REF,
        {
            "release_id": factory.RELEASE_ID,
            "release_promotion_allowed": True,
            "unsupported_promoted_total": 0,
            "rows": [claim or promoted_grand_claim()],
        },
    )


class GrandToeFormalObligationTests(unittest.TestCase):
    def test_missing_dedicated_row_blocks_promotion_but_keeps_nonpromotion_proof_active(self) -> None:
        factory = load_factory()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_machine_nonpromotion_surface(root, factory)
            write_dependencies(root, factory, passed=True)
            write_json(root, factory.CLAIM_LEDGER_REF, {"release_promotion_allowed": True, "unsupported_promoted_total": 0, "rows": []})
            write_json(root, factory.THEOREM_INVENTORY_REF, {"rows": []})

            payload = factory.obligation_payload(root)

            self.assertFalse(payload["release_promotion_allowed"])
            self.assertTrue(payload["machine_proved_nonpromotion"])
            self.assertIn("dedicated_claim_row", payload["failed_gate_predicates"])

    def test_missing_theorem_refs_blocks_promoted_row(self) -> None:
        factory = load_factory()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_promoted_claim_surface(root, factory, claim=promoted_grand_claim(promotion_theorem_ids=[]))

            report = factory.assess_grand_toe_promotion_route(root)

            self.assertFalse(report["promotion_allowed"])
            self.assertIn("promotion_theorem_ids_bound", report["failed_gate_predicates"])

    def test_missing_lean_refs_blocks_promoted_row_even_when_theorem_inventory_has_lean(self) -> None:
        factory = load_factory()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_promoted_claim_surface(root, factory, claim=promoted_grand_claim(lean_refs=[]))

            report = factory.assess_grand_toe_promotion_route(root)

            self.assertFalse(report["promotion_allowed"])
            self.assertIn("lean_theorem_ids_bound", report["failed_gate_predicates"])

    def test_declared_proof_file_without_theorem_inventory_mapping_does_not_promote(self) -> None:
        factory = load_factory()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_promoted_claim_surface(root, factory)
            write_json(
                root,
                factory.THEOREM_INVENTORY_REF,
                {
                    "rows": [
                        {
                            "theorem_id": "GT-THM-1",
                            "lean_ref": "formal/lean/OC133GrandPromotion.lean::future_grand_toe_theorem",
                        }
                    ]
                },
            )

            report = factory.assess_grand_toe_promotion_route(root)

            self.assertFalse(report["promotion_allowed"])
            self.assertIn("theorem_ids_map_to_proof_sheet_ids", report["failed_gate_predicates"])
            self.assertIn("proof_sheet_refs_bound", report["failed_gate_predicates"])
            self.assertIn(
                "proof_sheet::GT-THM-1::inventory_proof_sheet_ref_missing",
                report["missing_formal_obligations"],
            )

    def test_claim_lean_ref_must_match_inventory_declaration_for_theorem_id(self) -> None:
        factory = load_factory()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_promoted_claim_surface(
                root,
                factory,
                claim=promoted_grand_claim(
                    lean_refs=["formal/lean/OC133GrandPromotion.lean::unmapped_existing_theorem"]
                ),
            )
            write_text(
                root,
                "formal/lean/OC133GrandPromotion.lean",
                lean_text("future_grand_toe_theorem", "unmapped_existing_theorem"),
            )

            report = factory.assess_grand_toe_promotion_route(root)

            self.assertFalse(report["promotion_allowed"])
            self.assertIn("theorem_ids_map_to_lean_declaration_ids", report["failed_gate_predicates"])
            self.assertIn("lean_theorem_ids_bound", report["failed_gate_predicates"])
            self.assertIn(
                "lean::GT-THM-1::claim_row_missing_inventory_lean_ref::formal/lean/OC133GrandPromotion.lean::future_grand_toe_theorem",
                report["missing_formal_obligations"],
            )

    def test_missing_finite_cases_blocks_promoted_row(self) -> None:
        factory = load_factory()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_promoted_claim_surface(root, factory, claim=promoted_grand_claim(finite_case_ids=[]))

            report = factory.assess_grand_toe_promotion_route(root)

            self.assertFalse(report["promotion_allowed"])
            self.assertIn("finite_case_ids_bound", report["failed_gate_predicates"])
            self.assertIn("finite_positive_negative_controls_bound", report["failed_gate_predicates"])

    def test_finite_cases_must_cover_each_promotion_theorem_id(self) -> None:
        factory = load_factory()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_promoted_claim_surface(
                root,
                factory,
                claim=promoted_grand_claim(
                    promotion_theorem_ids=["GT-THM-1", "GT-THM-2"],
                    proof_refs=["proofs/grand_promotion/GT-THM-1.md", "proofs/grand_promotion/GT-THM-2.md"],
                    lean_refs=[
                        "formal/lean/OC133GrandPromotion.lean::future_grand_toe_theorem",
                        "formal/lean/OC133GrandPromotion.lean::future_grand_toe_theorem_two",
                    ],
                    finite_case_ids=["FM-GRAND-POS", "FM-GRAND-NEG"],
                ),
            )
            write_text(root, "proofs/grand_promotion/GT-THM-2.md", "# Future fixture theorem proof 2\n")
            write_text(
                root,
                "formal/lean/OC133GrandPromotion.lean",
                lean_text("future_grand_toe_theorem", "future_grand_toe_theorem_two"),
            )
            write_json(
                root,
                factory.THEOREM_INVENTORY_REF,
                {
                    "rows": [
                        {
                            "theorem_id": "GT-THM-1",
                            "proof_sheet_ref": "proofs/grand_promotion/GT-THM-1.md",
                            "lean_ref": "formal/lean/OC133GrandPromotion.lean::future_grand_toe_theorem",
                        },
                        {
                            "theorem_id": "GT-THM-2",
                            "proof_sheet_ref": "proofs/grand_promotion/GT-THM-2.md",
                            "lean_ref": "formal/lean/OC133GrandPromotion.lean::future_grand_toe_theorem_two",
                        },
                    ]
                },
            )

            report = factory.assess_grand_toe_promotion_route(root)

            self.assertFalse(report["promotion_allowed"])
            self.assertIn("theorem_ids_map_to_finite_model_case_ids", report["failed_gate_predicates"])
            self.assertIn("finite_positive_negative_controls_bound", report["failed_gate_predicates"])
            self.assertIn("GT-THM-2", report["theorem_ids_missing_finite_model_case_ids"])
            self.assertIn(
                "finite_model::GT-THM-2::positive_case_id_missing",
                report["missing_formal_obligations"],
            )

    def test_multiple_promoted_grand_rows_fail_claim_ledger_boundary(self) -> None:
        factory = load_factory()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_promoted_claim_surface(root, factory)
            ledger = json.loads((root / factory.CLAIM_LEDGER_REF).read_text(encoding="utf-8"))
            second = promoted_grand_claim(claim_id="OC133-GRAND-TOE-PROMOTION-SECOND")
            ledger["rows"].append(second)
            write_json(root, factory.CLAIM_LEDGER_REF, ledger)

            report = factory.assess_grand_toe_promotion_route(root)

            self.assertFalse(report["promotion_allowed"])
            self.assertIn("dedicated_claim_row", report["failed_gate_predicates"])
            self.assertIn("claim_ledger_promotion_boundaries_bound", report["failed_gate_predicates"])
            self.assertIn("claim_ledger::multiple_promoted_grand_toe_rows_present", report["missing_formal_obligations"])

    def test_dependency_blockers_prevent_promotion_despite_complete_formal_refs(self) -> None:
        factory = load_factory()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_promoted_claim_surface(root, factory, dependencies_passed=False)

            payload = factory.obligation_payload(root)

            self.assertFalse(payload["release_promotion_allowed"])
            self.assertIn("all_domain_empirical_pack_valid", payload["failed_gate_predicates"])
            self.assertIn("modern_science_superiority_certified", payload["failed_gate_predicates"])

    def test_complete_exact_refs_and_dependencies_allow_route(self) -> None:
        factory = load_factory()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_promoted_claim_surface(root, factory, dependencies_passed=True)

            report = factory.assess_grand_toe_promotion_route(root)

            self.assertTrue(report["promotion_allowed"])
            self.assertEqual(report["failed_gate_predicates"], [])


if __name__ == "__main__":
    unittest.main()
