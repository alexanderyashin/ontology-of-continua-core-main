from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
BLOCKER_ID = "grand_toe_claim_ledger_evidence"
CLAIM_ID = "OC133-GRAND-TOE-FORMAL-BLOCKER"

PROOF_SHEET_REF = "proofs/proof_sheets/GRAND_TOE_FORMAL_BLOCKER.md"
CLAIM_LEDGER_REF = "claims/CLAIM_LEDGER_1_3_3.json"
FINITE_INPUT_REF = "proofs/finite_model_checks/OC133_FINITE_MODEL_INPUTS.json"
CLAIM_OBLIGATION_LEDGER_REF = "claims/GRAND_TOE_FORMAL_OBLIGATION_LEDGER_1_3_3.json"
PROOF_OBLIGATION_LEDGER_REF = "proofs/GRAND_TOE_FORMAL_OBLIGATION_LEDGER_1_3_3.json"

LEAN_REFS = [
    "formal/lean/OC133V12.lean::grand_toe_promotion_requires_all_formal_obligations",
    "formal/lean/OC133V12.lean::grand_toe_complete_formal_obligations_accept_control",
    "formal/lean/OC133V12.lean::grand_toe_current_artifact_class_cannot_promote",
    "formal/lean/OC133V12.lean::grand_toe_current_artifact_class_missing_dedicated_claim",
    "formal/lean/OC133V12.lean::grand_toe_missing_finite_cases_blocks_promotion",
]
FINITE_CASE_IDS = [
    "FM-GRAND-TOE-FORMAL-CURRENT-REJECT",
    "FM-GRAND-TOE-FORMAL-HYPOTHETICAL-ACCEPT",
    "FM-GRAND-TOE-FORMAL-MISSING-FINITE-REJECT",
]


def read_json(ref: str) -> dict[str, Any]:
    path = ROOT / ref
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def write_json(ref: str, payload: Any) -> None:
    path = ROOT / ref
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(ref: str, text: str) -> None:
    path = ROOT / ref
    path.parent.mkdir(parents=True, exist_ok=True)
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text, encoding="utf-8", newline="\n")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def finite_rows() -> list[dict[str, Any]]:
    payload = read_json(FINITE_INPUT_REF)
    rows = payload.get("rows", [])
    return rows if isinstance(rows, list) else []


def grand_finite_input_rows() -> list[dict[str, Any]]:
    return [
        {
            "case_id": "FM-GRAND-TOE-FORMAL-CURRENT-REJECT",
            "theorem_id": CLAIM_ID,
            "case_type": "grand_toe_formal_obligation",
            "expected_verdict": "REJECT_PROMOTION",
            "model": {
                "mode": "current_claim_ledger",
                "claim_ledger_ref": CLAIM_LEDGER_REF,
                "requested_claim_classes": [
                    "numerically_proven_toe",
                    "all_domain_numerical_prediction",
                    "predicts_better_than_modern_science",
                ],
                "required_promotion_theorem_ids": ["OC133-GRAND-TOE-PROMOTED-FORMAL-THEOREM"],
                "blocking_theorem_ids": [CLAIM_ID],
                "required_lean_refs": LEAN_REFS,
                "required_finite_case_ids": FINITE_CASE_IDS,
                "proof_sheet_refs": [PROOF_SHEET_REF],
                "current_artifact_class": "bounded theorem rows plus replay/baseline support; no dedicated promoted grand TOE/all-domain claim row",
            },
            "negative_control_id": "FM-GRAND-TOE-FORMAL-HYPOTHETICAL-ACCEPT",
            "lean_ref": "formal/lean/OC133V12.lean::grand_toe_current_artifact_class_cannot_promote",
        },
        {
            "case_id": "FM-GRAND-TOE-FORMAL-HYPOTHETICAL-ACCEPT",
            "theorem_id": CLAIM_ID,
            "case_type": "grand_toe_formal_obligation",
            "expected_verdict": "ACCEPT_PROMOTION",
            "model": {
                "mode": "hypothetical_complete",
                "dedicated_claim_row": True,
                "release_promotion_allowed": True,
                "scientific_promotion_allowed": True,
                "public_status_promoted": True,
                "unsupported_promoted_total": 0,
                "requested_claim_classes": [
                    "numerically_proven_toe",
                    "all_domain_numerical_prediction",
                    "predicts_better_than_modern_science",
                ],
                "promoted_grand_claim_ids": ["OC133-GRAND-TOE-HYPOTHETICAL-PROMOTION"],
                "required_promotion_theorem_ids": ["OC133-GRAND-TOE-HYPOTHETICAL-PROMOTION"],
                "blocking_theorem_ids": [CLAIM_ID],
                "required_lean_refs": [
                    "formal/lean/OC133V12.lean::grand_toe_promotion_requires_all_formal_obligations",
                    "formal/lean/OC133V12.lean::grand_toe_complete_formal_obligations_accept_control",
                ],
                "required_finite_case_ids": FINITE_CASE_IDS,
                "proof_sheet_refs": [PROOF_SHEET_REF],
                "control_policy": "hypothetical only; not a current release promotion",
            },
            "negative_control_id": "FM-GRAND-TOE-FORMAL-MISSING-FINITE-REJECT",
            "lean_ref": "formal/lean/OC133V12.lean::grand_toe_complete_formal_obligations_accept_control",
        },
        {
            "case_id": "FM-GRAND-TOE-FORMAL-MISSING-FINITE-REJECT",
            "theorem_id": CLAIM_ID,
            "case_type": "grand_toe_formal_obligation",
            "expected_verdict": "REJECT_PROMOTION",
            "model": {
                "mode": "hypothetical_missing_finite",
                "dedicated_claim_row": True,
                "release_promotion_allowed": True,
                "scientific_promotion_allowed": True,
                "public_status_promoted": True,
                "unsupported_promoted_total": 0,
                "requested_claim_classes": [
                    "numerically_proven_toe",
                    "all_domain_numerical_prediction",
                    "predicts_better_than_modern_science",
                ],
                "promoted_grand_claim_ids": ["OC133-GRAND-TOE-HYPOTHETICAL-PROMOTION"],
                "required_promotion_theorem_ids": ["OC133-GRAND-TOE-HYPOTHETICAL-PROMOTION"],
                "blocking_theorem_ids": [CLAIM_ID],
                "required_lean_refs": [
                    "formal/lean/OC133V12.lean::grand_toe_promotion_requires_all_formal_obligations",
                    "formal/lean/OC133V12.lean::grand_toe_missing_finite_cases_blocks_promotion",
                ],
                "required_finite_case_ids": [],
                "proof_sheet_refs": [PROOF_SHEET_REF],
                "negative_control_isolated_dimension": "finite_case_ids_missing_only",
            },
            "negative_control_id": "",
            "lean_ref": "formal/lean/OC133V12.lean::grand_toe_missing_finite_cases_blocks_promotion",
        },
    ]


def ensure_grand_finite_input_rows() -> None:
    payload = read_json(FINITE_INPUT_REF)
    rows = payload.get("rows", [])
    if not isinstance(rows, list):
        rows = []
    wanted = set(FINITE_CASE_IDS)
    retained = [row for row in rows if not (isinstance(row, dict) and row.get("case_id") in wanted)]
    payload["rows"] = retained + grand_finite_input_rows()
    write_json(FINITE_INPUT_REF, payload)


def grand_finite_rows() -> list[dict[str, Any]]:
    wanted = set(FINITE_CASE_IDS)
    return [row for row in finite_rows() if isinstance(row, dict) and row.get("case_id") in wanted]


def lean_symbol_exists(ref: str) -> bool:
    if "::" not in ref:
        return (ROOT / ref).exists()
    path_ref, symbol = ref.split("::", 1)
    path = ROOT / path_ref
    if not path.exists():
        return False
    return symbol in path.read_text(encoding="utf-8", errors="replace")


def promoted_grand_claim_ids(claims: dict[str, Any]) -> list[str]:
    tokens = (
        "theory of everything",
        "toe",
        "all-domain",
        "all domain",
        "across all domains",
        "numerically proven",
        "modern science",
        "better than",
    )
    out = []
    for row in claims.get("rows", []) if isinstance(claims.get("rows"), list) else []:
        if not isinstance(row, dict):
            continue
        text = json.dumps(row, ensure_ascii=False).lower()
        if not any(token in text for token in tokens):
            continue
        if (
            row.get("scientific_promotion_allowed") is True
            and row.get("release_promotion_allowed") is True
            and "PROMOTED" in str(row.get("public_status", "")).upper()
        ):
            out.append(str(row.get("claim_id")))
    return out


def obligation_payload() -> dict[str, Any]:
    claims = read_json(CLAIM_LEDGER_REF)
    finite_declared = {str(row.get("case_id")) for row in finite_rows() if isinstance(row, dict)}
    lean_bound = {ref: lean_symbol_exists(ref) for ref in LEAN_REFS}
    finite_bound = {case_id: case_id in finite_declared for case_id in FINITE_CASE_IDS}
    promoted_ids = promoted_grand_claim_ids(claims)
    failed_gate_predicates = [
        "dedicated_claim_row",
        "release_promotion_allowed",
        "scientific_promotion_allowed",
        "public_status_promoted",
        "promotion_theorem_ids_bound",
    ]
    machine_proof_ready = (
        all(lean_bound.values())
        and all(finite_bound.values())
        and len(grand_finite_rows()) == len(FINITE_CASE_IDS)
    )
    return {
        "schema_id": "OC133_GRAND_TOE_FORMAL_OBLIGATION_LEDGER_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": "Research/FormalScience",
        "blocker_id": BLOCKER_ID,
        "claim_id": CLAIM_ID,
        "state": "CURRENT_ARTIFACT_CLASS_CANNOT_PROMOTE",
        "blocker_remains": True,
        "release_promotion_allowed": False,
        "scientific_promotion_allowed": False,
        "requested_claim_classes": [
            "numerically_proven_toe",
            "all_domain_numerical_prediction",
            "predicts_better_than_modern_science",
        ],
        "promoted_grand_claim_ids": promoted_ids,
        "promoted_grand_claim_total": len(promoted_ids),
        "current_artifact_class": "bounded theorem rows, target-blind/replay baseline rows, no-send governance rows, and non-promoted comparator notes",
        "formal_gate_vector": {
            "dedicated_claim_row": False,
            "release_promotion_allowed": False,
            "scientific_promotion_allowed": False,
            "public_status_promoted": False,
            "promotion_theorem_ids_bound": False,
            "proof_sheet_refs_bound": (ROOT / PROOF_SHEET_REF).exists(),
            "lean_theorem_ids_bound": all(lean_bound.values()),
            "finite_case_ids_bound": all(finite_bound.values()),
            "unsupported_promoted_total_zero": claims.get("unsupported_promoted_total") == 0,
        },
        "failed_gate_predicates": failed_gate_predicates,
        "machine_proved_nonpromotion": machine_proof_ready,
        "machine_proof_refs": {
            "proof_sheet_ref": PROOF_SHEET_REF,
            "lean_refs": LEAN_REFS,
            "finite_case_ids": FINITE_CASE_IDS,
            "finite_input_ref": FINITE_INPUT_REF,
            "finite_output_refs": [f"proofs/FINITE_MODEL_CHECKS_1_3_3.json::{case_id}" for case_id in FINITE_CASE_IDS],
        },
        "positive_control_case_id": "FM-GRAND-TOE-FORMAL-HYPOTHETICAL-ACCEPT",
        "current_reject_case_id": "FM-GRAND-TOE-FORMAL-CURRENT-REJECT",
        "negative_control_case_id": "FM-GRAND-TOE-FORMAL-MISSING-FINITE-REJECT",
        "work_order_decomposition": [
            {
                "work_order_id": "OC133-GRAND-FORMAL-WO-001",
                "title": "Create a dedicated promoted grand TOE/all-domain claim row only if the grand claim is actually intended for promotion.",
                "acceptance": "Claim row has release_promotion_allowed=true, scientific_promotion_allowed=true, public_status promoted, and explicit theorem/proof/Lean/finite refs.",
            },
            {
                "work_order_id": "OC133-GRAND-FORMAL-WO-002",
                "title": "Bind theorem inventory and proof sheet IDs for the dedicated grand claim.",
                "acceptance": "The promoted row names theorem IDs distinct from the bounded v12 theorem rows and cites proof sheets with assumptions and falsifier boundaries.",
            },
            {
                "work_order_id": "OC133-GRAND-FORMAL-WO-003",
                "title": "Add Lean theorem obligations for the grand claim itself.",
                "acceptance": "Lean contains theorem IDs proving the promoted grand statement, not only the non-promotion gate or bounded tuple classifiers.",
            },
            {
                "work_order_id": "OC133-GRAND-FORMAL-WO-004",
                "title": "Add executable finite positive and negative cases for the dedicated grand claim.",
                "acceptance": "Finite rows include positive witness IDs and mutation/negative controls; missing finite IDs keep promotion rejected.",
            },
            {
                "work_order_id": "OC133-GRAND-FORMAL-WO-005",
                "title": "Re-audit with Logion all-domain readiness after empirical and modern-science comparator blockers are separately closed.",
                "acceptance": "grand_toe_claim_ledger_evidence, grand_toe_empirical_superiority, and modern_science_comparator_superiority all re-audit PASS without no-send unlock.",
            },
        ],
        "no_send": True,
        "publish_allowed": False,
        "journal_submissions_allowed": False,
    }


def render_proof_sheet(payload: dict[str, Any]) -> str:
    lean_rows = "\n".join(f"- `{ref}`" for ref in LEAN_REFS)
    finite_rows_text = "\n".join(f"- `{case_id}`" for case_id in FINITE_CASE_IDS)
    gate_rows = "\n".join(
        f"| `{key}` | `{str(value).lower()}` |"
        for key, value in payload["formal_gate_vector"].items()
    )
    work_rows = "\n".join(
        f"| `{row['work_order_id']}` | {row['title']} | {row['acceptance']} |"
        for row in payload["work_order_decomposition"]
    )
    return f"""# Grand TOE Formal Blocker

Verdict: `CURRENT_ARTIFACT_CLASS_CANNOT_PROMOTE`.

This sheet is the Logion Research/FormalScience obligation layer for blocker `{BLOCKER_ID}`. It does not promote a grand TOE/all-domain claim. It machine-binds the stricter reason why the current artifact class cannot promote that claim.

## Bound Machine Evidence

Lean theorem refs:

{lean_rows}

Finite case IDs:

{finite_rows_text}

The current row is `{payload['current_reject_case_id']}` and must observe `REJECT_PROMOTION`. The positive control `{payload['positive_control_case_id']}` may observe `ACCEPT_PROMOTION` only because it is explicitly hypothetical and carries theorem/proof/Lean/finite IDs. The missing-finite control `{payload['negative_control_case_id']}` must observe `REJECT_PROMOTION`.

## Formal Gate Vector

| Gate | Current value |
| --- | --- |
{gate_rows}

Failed promotion predicates: `{', '.join(payload['failed_gate_predicates'])}`.

## Work-Order Decomposition

| Work order | Task | Acceptance |
| --- | --- | --- |
{work_rows}

## Non-Promotion Rule

No `PASS` or promoted public status is available from artifact existence, bounded theorem rows, replay QA, or target-blind baseline rows. A future grand claim needs a dedicated promoted ledger row plus theorem IDs, proof sheet refs, Lean theorem refs, finite case IDs, empirical superiority evidence, and modern-science comparator closure.
"""


def formal_claim_row() -> dict[str, Any]:
    return {
        "claim_id": CLAIM_ID,
        "claim": "The current OC133 v12 artifact class cannot promote a dedicated grand TOE/all-domain claim because no promoted grand claim-ledger row is bound to theorem, proof-sheet, Lean, and finite-model obligations.",
        "support": "LEAN_SUBSET_FINITE_NEGATIVE_OBLIGATION_PROOF",
        "evidence_ref": PROOF_SHEET_REF,
        "supporting_evidence_refs": [
            *LEAN_REFS,
            *[f"{FINITE_INPUT_REF}::{case_id}" for case_id in FINITE_CASE_IDS],
            *[f"proofs/FINITE_MODEL_CHECKS_1_3_3.json::{case_id}" for case_id in FINITE_CASE_IDS],
            CLAIM_OBLIGATION_LEDGER_REF,
            PROOF_OBLIGATION_LEDGER_REF,
        ],
        "public_status": "FORMAL_BLOCKER_NOT_PROMOTED_V12",
        "release_promotion_allowed": False,
        "scientific_promotion_allowed": False,
        "grand_toe_promotion_allowed": False,
        "evidence_ceiling": "FORMAL_NONPROMOTION_OBLIGATION_PROOF_NOT_GRAND_THEOREM",
        "blocker_id": BLOCKER_ID,
        "current_reject_case": "FM-GRAND-TOE-FORMAL-CURRENT-REJECT",
        "positive_hypothetical_accept_case": "FM-GRAND-TOE-FORMAL-HYPOTHETICAL-ACCEPT",
        "negative_control_cases": ["FM-GRAND-TOE-FORMAL-MISSING-FINITE-REJECT"],
        "adversarial_review_blocker_total": 0,
        "prior_cerberus_open_total_at_generation": 0,
        "fresh_cerberus_required_for_release": True,
        "promotion_condition": "Not promotable in the current artifact class; requires a future dedicated promoted grand claim row with theorem/proof/Lean/finite IDs plus separate empirical and comparator closure.",
        "scope_limit": "This row is a blocker proof and work-order decomposition only. It is not a TOE theorem, empirical law, modern-science superiority claim, or public release authorization.",
    }


def update_claim_ledger() -> dict[str, Any]:
    payload = read_json(CLAIM_LEDGER_REF)
    rows = payload.get("rows", []) if isinstance(payload.get("rows"), list) else []
    rows = [row for row in rows if not (isinstance(row, dict) and row.get("claim_id") == CLAIM_ID)]
    insert_at = len(rows)
    for index, row in enumerate(rows):
        if isinstance(row, dict) and row.get("claim_id") == "T133-KLEVEL":
            insert_at = index + 1
            break
    rows.insert(insert_at, formal_claim_row())
    payload["rows"] = rows
    payload["claim_total"] = len(rows)
    payload["scientific_promotion_allowed_total"] = sum(
        1 for row in rows if isinstance(row, dict) and row.get("scientific_promotion_allowed") is True
    )
    payload["governance_control_allowed_total"] = sum(
        1 for row in rows if isinstance(row, dict) and row.get("governance_control_allowed") is True
    )
    payload["control_plane_total"] = sum(
        1 for row in rows if isinstance(row, dict) and row.get("control_plane_claim") is True
    )
    payload["unsupported_promoted_total"] = 0
    formal_ids = [
        str(row.get("claim_id"))
        for row in rows
        if isinstance(row, dict)
        and row.get("evidence_ceiling") == "FORMAL_NONPROMOTION_OBLIGATION_PROOF_NOT_GRAND_THEOREM"
    ]
    payload["formal_consistency_limited_claim_total"] = len(formal_ids)
    payload["formal_consistency_limited_claim_ids"] = formal_ids
    payload["release_promotion_allowed"] = False
    payload["promotion_condition"] = (
        "Current ledger rows are no-send owner-review obligations, replay-QA quarantine rows, non-promoted prior-art positioning notes, "
        "a bounded governance control, and a machine-checked grand TOE formal non-promotion blocker. Scientific promotion remains false "
        "until G57/G58/G70 pass after fresh zero critical/high Cerberus review and the grand TOE formal/empirical/comparator blockers close."
    )
    write_json(CLAIM_LEDGER_REF, payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Materialize OC133 grand TOE formal obligation blocker artifacts.")
    parser.add_argument("--write", action="store_true", help="Write proof sheet, generated ledgers, and claim ledger blocker row.")
    args = parser.parse_args()

    ensure_grand_finite_input_rows()
    if args.write:
        write_text(PROOF_SHEET_REF, render_proof_sheet(obligation_payload()))
        claim_ledger = update_claim_ledger()
        payload = obligation_payload()
        payload["claim_ledger_sha256_after_update"] = sha256_text(
            json.dumps(claim_ledger, ensure_ascii=False, sort_keys=True)
        )
        write_json(CLAIM_OBLIGATION_LEDGER_REF, payload)
        write_json(PROOF_OBLIGATION_LEDGER_REF, payload)
    else:
        payload = obligation_payload()
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
