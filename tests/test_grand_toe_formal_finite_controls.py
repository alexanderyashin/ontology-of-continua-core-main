from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = REPO_ROOT / "proofs" / "finite_model_checks" / "run_finite_model_checks.py"
INPUT_PATH = REPO_ROOT / "proofs" / "finite_model_checks" / "OC133_FINITE_MODEL_INPUTS.json"

CASE_IDS = [
    "FM-GRAND-TOE-FORMAL-CURRENT-REJECT",
    "FM-GRAND-TOE-FORMAL-HYPOTHETICAL-ACCEPT",
    "FM-GRAND-TOE-FORMAL-MISSING-FINITE-REJECT",
]


def load_runner():
    spec = importlib.util.spec_from_file_location("run_finite_model_checks", RUNNER_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def finite_rows() -> dict[str, dict[str, Any]]:
    payload = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    return {
        str(row.get("case_id")): row
        for row in payload.get("rows", [])
        if isinstance(row, dict) and row.get("case_id")
    }


def model_has_key(value: Any, forbidden: set[str]) -> bool:
    if isinstance(value, dict):
        return any(key in forbidden or model_has_key(child, forbidden) for key, child in value.items())
    if isinstance(value, list):
        return any(model_has_key(child, forbidden) for child in value)
    return False


class GrandToeFormalFiniteControlTests(unittest.TestCase):
    def test_grand_formal_controls_are_declared_and_semantic(self) -> None:
        rows = finite_rows()

        self.assertEqual(set(CASE_IDS), set(CASE_IDS).intersection(rows))
        expected_modes = {
            "FM-GRAND-TOE-FORMAL-CURRENT-REJECT": "current_claim_ledger",
            "FM-GRAND-TOE-FORMAL-HYPOTHETICAL-ACCEPT": "hypothetical_complete",
            "FM-GRAND-TOE-FORMAL-MISSING-FINITE-REJECT": "hypothetical_missing_finite",
        }
        for case_id, mode in expected_modes.items():
            model = rows[case_id].get("model", {})
            self.assertEqual(mode, model.get("mode"), case_id)
            self.assertFalse(
                model_has_key(
                    model,
                    {"observed_verdict", "observed_drop_verdict", "observed_keep_verdict"},
                ),
                case_id,
            )
            self.assertTrue(model.get("required_lean_refs"), case_id)
            self.assertTrue(model.get("required_finite_case_ids"), case_id)
            self.assertTrue(model.get("proof_sheet_refs"), case_id)

        for case_id in (
            "FM-GRAND-TOE-FORMAL-HYPOTHETICAL-ACCEPT",
            "FM-GRAND-TOE-FORMAL-MISSING-FINITE-REJECT",
        ):
            model = rows[case_id]["model"]
            self.assertEqual(["OC133-GRAND-TOE-HYPOTHETICAL-PROMOTION"], model.get("promoted_grand_claim_ids"))
            self.assertIs(model.get("dedicated_claim_row"), True)
            self.assertIs(model.get("release_promotion_allowed"), True)
            self.assertIs(model.get("scientific_promotion_allowed"), True)
            self.assertIs(model.get("public_status_promoted"), True)
            self.assertEqual(0, model.get("unsupported_promoted_total"))

    def test_grand_formal_control_verdicts_are_computed_from_route_facts(self) -> None:
        runner = load_runner()
        rows = finite_rows()

        current = runner.grand_toe_formal_obligation_audit(rows["FM-GRAND-TOE-FORMAL-CURRENT-REJECT"])
        complete = runner.grand_toe_formal_obligation_audit(rows["FM-GRAND-TOE-FORMAL-HYPOTHETICAL-ACCEPT"])
        missing_finite = runner.grand_toe_formal_obligation_audit(rows["FM-GRAND-TOE-FORMAL-MISSING-FINITE-REJECT"])

        self.assertEqual("REJECT_PROMOTION", current["verdict"])
        self.assertEqual("current_claim_ledger", current["mode"])
        self.assertTrue(current["machine_proved_nonpromotion"])
        self.assertEqual("ACCEPT_PROMOTION", complete["verdict"])
        self.assertEqual("hypothetical_complete", complete["mode"])
        self.assertEqual([], complete["failed_gate_predicates"])
        self.assertEqual("REJECT_PROMOTION", missing_finite["verdict"])
        self.assertEqual("hypothetical_missing_finite", missing_finite["mode"])
        self.assertEqual(["finite_case_ids_bound"], missing_finite["failed_gate_predicates"])


if __name__ == "__main__":
    unittest.main()
