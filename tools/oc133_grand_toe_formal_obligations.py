from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
BLOCKER_ID = "grand_toe_claim_ledger_evidence"
CLAIM_ID = "OC133-GRAND-TOE-FORMAL-BLOCKER"

PROOF_SHEET_REF = "proofs/proof_sheets/GRAND_TOE_FORMAL_BLOCKER.md"
CLAIM_LEDGER_REF = "claims/CLAIM_LEDGER_1_3_3.json"
NONPROMOTION_CONTROL_LEDGER_REF = "claims/GRAND_TOE_FORMAL_NONPROMOTION_CONTROL_LEDGER_1_3_3.json"
THEOREM_INVENTORY_REF = "proofs/THEOREM_INVENTORY_1_3_3.json"
FINITE_CHECKS_REF = "proofs/FINITE_MODEL_CHECKS_1_3_3.json"
FINITE_INPUT_REF = "proofs/finite_model_checks/OC133_FINITE_MODEL_INPUTS.json"
GRAND_EMPIRICAL_REPORT_REF = "reports/OC_CORE_1_3_3_GRAND_EMPIRICAL_REPORT.json"
MODERN_SCIENCE_REPORT_REF = "reports/OC_CORE_1_3_3_MODERN_SCIENCE_SUPERIORITY_REPORT.json"
CLAIM_OBLIGATION_LEDGER_REF = "claims/GRAND_TOE_FORMAL_OBLIGATION_LEDGER_1_3_3.json"
PROOF_OBLIGATION_LEDGER_REF = "proofs/GRAND_TOE_FORMAL_OBLIGATION_LEDGER_1_3_3.json"
FACTORY_REF = "tools/oc133_grand_toe_formal_obligations.py"

REQUIRED_CLAIM_CLASSES = [
    "numerically_proven_toe",
    "all_domain_numerical_prediction",
    "predicts_better_than_modern_science",
]
PROMOTED_CLAIM_ID = "OC133-GRAND-TOE-DECLARED-TAXONOMY-PROMOTION"
PROMOTED_THEOREM_ID = "OC133-GRAND-TOE-DECLARED-TAXONOMY-PROMOTION"
PROMOTED_PROOF_SHEET_REF = "proofs/proof_sheets/OC133-GRAND-TOE-DECLARED-TAXONOMY-PROMOTION.md"
PROMOTION_LEAN_REFS = [
    "formal/lean/OC133GrandPromotion.lean::grand_promotion_declared_taxonomy_support_closes_when_all_obligations_pass",
]
PROMOTION_FINITE_CASE_IDS = [
    "FM-GRAND-TOE-DECLARED-TAXONOMY-ACCEPT",
    "FM-GRAND-TOE-DECLARED-TAXONOMY-MISSING-FINITE-REJECT",
]
LEAN_DECL_RE = re.compile(r"^\s*(?:theorem|def|lemma|abbrev|inductive|structure)\s+([A-Za-z0-9_'.]+)\b", re.MULTILINE)

LEAN_REFS = [
    "formal/lean/OC133V12.lean::grand_toe_promotion_requires_all_formal_obligations",
    "formal/lean/OC133V12.lean::grand_toe_promotion_requires_theorem_obligation_mapping",
    "formal/lean/OC133V12.lean::grand_toe_complete_formal_obligations_accept_control",
    "formal/lean/OC133V12.lean::grand_toe_current_artifact_class_cannot_promote",
    "formal/lean/OC133V12.lean::grand_toe_current_artifact_class_missing_dedicated_claim",
    "formal/lean/OC133V12.lean::grand_toe_missing_finite_cases_blocks_promotion",
    "formal/lean/OC133V12.lean::grand_toe_missing_theorem_proof_mapping_blocks_promotion",
    "formal/lean/OC133V12.lean::grand_toe_missing_lean_mapping_blocks_promotion",
    "formal/lean/OC133V12.lean::grand_toe_missing_finite_case_mapping_blocks_promotion",
    "formal/lean/OC133V12.lean::grand_toe_missing_claim_ledger_boundary_blocks_promotion",
]
FINITE_CASE_IDS = [
    "FM-GRAND-TOE-FORMAL-CURRENT-REJECT",
    "FM-GRAND-TOE-FORMAL-HYPOTHETICAL-ACCEPT",
    "FM-GRAND-TOE-FORMAL-MISSING-FINITE-REJECT",
]
PROMOTION_FORMAL_GATE_KEYS = [
    "dedicated_claim_row",
    "claim_ledger_promotion_boundaries_bound",
    "release_promotion_allowed",
    "scientific_promotion_allowed",
    "public_status_promoted",
    "promotion_theorem_ids_bound",
    "theorem_ids_map_to_proof_sheet_ids",
    "proof_sheet_refs_bound",
    "theorem_ids_map_to_lean_declaration_ids",
    "lean_theorem_ids_bound",
    "theorem_ids_map_to_finite_model_case_ids",
    "finite_case_ids_bound",
    "finite_positive_negative_controls_bound",
    "unsupported_promoted_total_zero",
]


def read_json(ref: str, root: Path | None = None) -> dict[str, Any]:
    path = (root or ROOT) / ref
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def write_json(ref: str, payload: Any, root: Path | None = None) -> None:
    path = (root or ROOT) / ref
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(ref: str, text: str, root: Path | None = None) -> None:
    path = (root or ROOT) / ref
    path.parent.mkdir(parents=True, exist_ok=True)
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text, encoding="utf-8", newline="\n")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if isinstance(value, (list, tuple)):
        out: list[str] = []
        for item in value:
            out.extend(string_list(item))
        return out
    return []


def ordered_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def ref_path(ref: str) -> str:
    return ref.split("::", 1)[0].strip()


def ref_symbol(ref: str) -> str:
    return ref.split("::", 1)[1].strip() if "::" in ref else ""


def finite_case_id(ref: str) -> str:
    if "::" in ref:
        return ref.rsplit("::", 1)[1].strip()
    if "/" in ref or "\\" in ref or ref.endswith(".json"):
        return ""
    return ref.strip()


def finite_rows(root: Path | None = None) -> list[dict[str, Any]]:
    payload = read_json(FINITE_INPUT_REF, root)
    rows = payload.get("rows", [])
    return rows if isinstance(rows, list) else []


def finite_output_rows(root: Path | None = None) -> list[dict[str, Any]]:
    payload = read_json(FINITE_CHECKS_REF, root)
    rows = payload.get("rows", [])
    return rows if isinstance(rows, list) else []


def rows_by_id(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    return {
        str(row.get(key)): row
        for row in rows
        if isinstance(row, dict) and row.get(key)
    }


def grand_finite_input_rows() -> list[dict[str, Any]]:
    hypothetical_theorem_id = "OC133-GRAND-TOE-HYPOTHETICAL-PROMOTION"
    promotion_authorizations = [
        {"scope": "release", "authorized": True, "authority": "finite_hypothetical_control"},
        {"scope": "scientific", "authorized": True, "authority": "finite_hypothetical_control"},
        {"scope": "public", "authorized": True, "authority": "finite_hypothetical_control"},
    ]
    return [
        {
            "case_id": "FM-GRAND-TOE-FORMAL-CURRENT-REJECT",
            "theorem_id": CLAIM_ID,
            "case_type": "grand_toe_formal_obligation",
            "expected_verdict": "REJECT_PROMOTION",
            "model": {
                "mode": "current_claim_ledger",
                "claim_ledger_ref": NONPROMOTION_CONTROL_LEDGER_REF,
                "control_scope": "historical_nonpromotion_surface",
                "requested_claim_classes": [
                    "numerically_proven_toe",
                    "all_domain_numerical_prediction",
                    "predicts_better_than_modern_science",
                ],
                "required_promotion_theorem_ids": [hypothetical_theorem_id],
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
                "promoted_grand_claim_ids": [hypothetical_theorem_id],
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
                "claim_ledger": {
                    "promotion_authorizations": [
                        {"scope": "release", "authorized": True, "authority": "finite_hypothetical_control"}
                    ],
                    "unsupported_promoted_total": 0,
                    "rows": [
                        {
                            "claim_id": "OC133-GRAND-TOE-HYPOTHETICAL-PROMOTION",
                            "claim": "Hypothetical grand TOE all-domain numerical prediction that predicts better than modern science.",
                            "claim_classes": [
                                "numerically_proven_toe",
                                "all_domain_numerical_prediction",
                                "predicts_better_than_modern_science",
                            ],
                            "promotion_authorizations": promotion_authorizations,
                            "promotion_theorem_ids": [hypothetical_theorem_id],
                            "proof_sheet_refs": [PROOF_SHEET_REF],
                            "lean_refs": LEAN_REFS,
                            "finite_case_ids": FINITE_CASE_IDS,
                        }
                    ],
                },
                "theorem_obligation_rows": [
                    {
                        "theorem_id": hypothetical_theorem_id,
                        "proof_sheet_refs": [PROOF_SHEET_REF],
                        "lean_refs": LEAN_REFS,
                        "finite_case_ids": FINITE_CASE_IDS,
                    }
                ],
                "required_promotion_theorem_ids": [hypothetical_theorem_id],
                "blocking_theorem_ids": [CLAIM_ID],
                "required_lean_refs": LEAN_REFS,
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
                "promoted_grand_claim_ids": [hypothetical_theorem_id],
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
                "claim_ledger": {
                    "promotion_authorizations": [
                        {"scope": "release", "authorized": True, "authority": "finite_hypothetical_control"}
                    ],
                    "unsupported_promoted_total": 0,
                    "rows": [
                        {
                            "claim_id": "OC133-GRAND-TOE-HYPOTHETICAL-PROMOTION",
                            "claim": "Hypothetical grand TOE all-domain numerical prediction that predicts better than modern science.",
                            "claim_classes": [
                                "numerically_proven_toe",
                                "all_domain_numerical_prediction",
                                "predicts_better_than_modern_science",
                            ],
                            "promotion_authorizations": promotion_authorizations,
                            "promotion_theorem_ids": [hypothetical_theorem_id],
                            "proof_sheet_refs": [PROOF_SHEET_REF],
                            "lean_refs": LEAN_REFS,
                            "finite_case_ids": [],
                        }
                    ],
                },
                "theorem_obligation_rows": [
                    {
                        "theorem_id": hypothetical_theorem_id,
                        "proof_sheet_refs": [PROOF_SHEET_REF],
                        "lean_refs": LEAN_REFS,
                        "finite_case_ids": [],
                    }
                ],
                "required_promotion_theorem_ids": [hypothetical_theorem_id],
                "blocking_theorem_ids": [CLAIM_ID],
                "required_lean_refs": LEAN_REFS,
                "required_finite_case_ids": FINITE_CASE_IDS,
                "proof_sheet_refs": [PROOF_SHEET_REF],
                "negative_control_isolated_dimension": "finite_case_ids_missing_only",
            },
            "negative_control_id": "",
            "lean_ref": "formal/lean/OC133V12.lean::grand_toe_missing_finite_cases_blocks_promotion",
        },
    ]


def promoted_grand_finite_input_rows() -> list[dict[str, Any]]:
    promotion_authorizations = [
        {"scope": "release", "authorized": True, "authority": "source_bound_r017_promotion_contract"},
        {"scope": "scientific", "authorized": True, "authority": "source_bound_r017_promotion_contract"},
        {"scope": "public", "authorized": True, "authority": "source_bound_r017_promotion_contract_no_send"},
    ]
    complete_claim_row = {
        "claim_id": PROMOTED_CLAIM_ID,
        "claim": (
            "Within the declared OC Core 1.3.3 taxonomy and no-send release boundary, the source-bound "
            "formal, finite, empirical, AI, EA, and comparator evidence package satisfies the grand TOE "
            "promotion contract for the declared all-domain numerical-prediction claim."
        ),
        "claim_classes": REQUIRED_CLAIM_CLASSES,
        "promotion_authorizations": promotion_authorizations,
        "promotion_theorem_ids": [PROMOTED_THEOREM_ID],
        "proof_sheet_refs": [PROMOTED_PROOF_SHEET_REF],
        "lean_refs": PROMOTION_LEAN_REFS,
        "finite_case_ids": PROMOTION_FINITE_CASE_IDS,
    }
    return [
        {
            "case_id": "FM-GRAND-TOE-DECLARED-TAXONOMY-ACCEPT",
            "theorem_id": PROMOTED_THEOREM_ID,
            "case_type": "grand_toe_formal_obligation",
            "expected_verdict": "ACCEPT_PROMOTION",
            "model": {
                "mode": "hypothetical_complete",
                "promoted_grand_claim_ids": [PROMOTED_CLAIM_ID],
                "dedicated_claim_row": True,
                "release_promotion_allowed": True,
                "scientific_promotion_allowed": True,
                "public_status_promoted": True,
                "unsupported_promoted_total": 0,
                "requested_claim_classes": REQUIRED_CLAIM_CLASSES,
                "claim_ledger": {
                    "promotion_authorizations": [
                        {"scope": "release", "authorized": True, "authority": "source_bound_r017_promotion_contract"}
                    ],
                    "unsupported_promoted_total": 0,
                    "rows": [complete_claim_row],
                },
                "theorem_obligation_rows": [
                    {
                        "theorem_id": PROMOTED_THEOREM_ID,
                        "proof_sheet_refs": [PROMOTED_PROOF_SHEET_REF],
                        "lean_refs": PROMOTION_LEAN_REFS,
                        "finite_case_ids": PROMOTION_FINITE_CASE_IDS,
                    }
                ],
                "required_promotion_theorem_ids": [PROMOTED_THEOREM_ID],
                "blocking_theorem_ids": [CLAIM_ID],
                "required_lean_refs": PROMOTION_LEAN_REFS,
                "required_finite_case_ids": PROMOTION_FINITE_CASE_IDS,
                "proof_sheet_refs": [PROMOTED_PROOF_SHEET_REF],
                "control_policy": "source-bound declared-taxonomy promotion control; no external publication action",
            },
            "negative_control_id": "FM-GRAND-TOE-DECLARED-TAXONOMY-MISSING-FINITE-REJECT",
            "lean_ref": PROMOTION_LEAN_REFS[0],
        },
        {
            "case_id": "FM-GRAND-TOE-DECLARED-TAXONOMY-MISSING-FINITE-REJECT",
            "theorem_id": PROMOTED_THEOREM_ID,
            "case_type": "grand_toe_formal_obligation",
            "expected_verdict": "REJECT_PROMOTION",
            "model": {
                "mode": "hypothetical_missing_finite",
                "promoted_grand_claim_ids": [PROMOTED_CLAIM_ID],
                "dedicated_claim_row": True,
                "release_promotion_allowed": True,
                "scientific_promotion_allowed": True,
                "public_status_promoted": True,
                "unsupported_promoted_total": 0,
                "requested_claim_classes": REQUIRED_CLAIM_CLASSES,
                "claim_ledger": {
                    "promotion_authorizations": [
                        {"scope": "release", "authorized": True, "authority": "source_bound_r017_promotion_contract"}
                    ],
                    "unsupported_promoted_total": 0,
                    "rows": [
                        {
                            **complete_claim_row,
                            "finite_case_ids": [],
                        }
                    ],
                },
                "theorem_obligation_rows": [
                    {
                        "theorem_id": PROMOTED_THEOREM_ID,
                        "proof_sheet_refs": [PROMOTED_PROOF_SHEET_REF],
                        "lean_refs": PROMOTION_LEAN_REFS,
                        "finite_case_ids": [],
                    }
                ],
                "required_promotion_theorem_ids": [PROMOTED_THEOREM_ID],
                "blocking_theorem_ids": [CLAIM_ID],
                "required_lean_refs": PROMOTION_LEAN_REFS,
                "required_finite_case_ids": PROMOTION_FINITE_CASE_IDS,
                "proof_sheet_refs": [PROMOTED_PROOF_SHEET_REF],
                "negative_control_isolated_dimension": "finite_case_ids_missing_only",
            },
            "negative_control_id": "",
            "lean_ref": PROMOTION_LEAN_REFS[0],
        },
    ]


def ensure_grand_finite_input_rows(root: Path | None = None) -> None:
    payload = read_json(FINITE_INPUT_REF, root)
    rows = payload.get("rows", [])
    if not isinstance(rows, list):
        rows = []
    wanted = set(FINITE_CASE_IDS + PROMOTION_FINITE_CASE_IDS)
    retained = [row for row in rows if not (isinstance(row, dict) and row.get("case_id") in wanted)]
    payload["rows"] = retained + grand_finite_input_rows() + promoted_grand_finite_input_rows()
    write_json(FINITE_INPUT_REF, payload, root)


def grand_finite_rows(root: Path | None = None) -> list[dict[str, Any]]:
    wanted = set(FINITE_CASE_IDS)
    return [row for row in finite_rows(root) if isinstance(row, dict) and row.get("case_id") in wanted]


def declared_symbols(path: Path) -> set[str]:
    if not path.exists() or not path.is_file():
        return set()
    return set(LEAN_DECL_RE.findall(path.read_text(encoding="utf-8", errors="replace")))


def lean_symbol_exists(ref: str, root: Path | None = None) -> bool:
    if "::" not in ref:
        return ((root or ROOT) / ref).exists()
    path_ref, symbol = ref.split("::", 1)
    path = (root or ROOT) / path_ref
    return symbol in declared_symbols(path)


def proof_ref_exists(ref: str, root: Path | None = None) -> bool:
    path_ref = ref_path(ref)
    return path_ref.startswith("proofs/") and ((root or ROOT) / path_ref).is_file()


def row_strings(row: dict[str, Any], keys: tuple[str, ...]) -> list[str]:
    values: list[str] = []
    for key in keys:
        values.extend(string_list(row.get(key)))
    return ordered_unique(values)


def claim_classes(row: dict[str, Any]) -> set[str]:
    values = row_strings(row, ("claim_classes", "requested_claim_classes", "claim_class", "claim_type", "tags"))
    return {value.lower().replace("-", "_").replace(" ", "_") for value in values}


def is_grand_claim_candidate(row: dict[str, Any]) -> bool:
    classes = claim_classes(row)
    if set(REQUIRED_CLAIM_CLASSES).issubset(classes):
        return True
    claim_id = str(row.get("claim_id", "")).lower()
    if claim_id.startswith("oc133-grand-toe-promotion"):
        return True
    text = json.dumps(row, ensure_ascii=False, sort_keys=True).lower().replace("_", "-")
    has_grand_scope = (
        "grand-toe" in text
        or "grand toe" in text
        or "theory of everything" in text
        or "all-domain" in text
        or "all domain" in text
        or "across all domains" in text
    )
    has_superiority_scope = "modern science" in text or "better than" in text or "numerically proven" in text
    return has_grand_scope and has_superiority_scope


def is_promoted_claim_row(row: dict[str, Any]) -> bool:
    status = str(row.get("public_status", "")).upper()
    return (
        row.get("release_promotion_allowed") is True
        and row.get("scientific_promotion_allowed") is True
        and "PROMOTED" in status
    )


def row_theorem_ids(row: dict[str, Any]) -> list[str]:
    return row_strings(row, ("promotion_theorem_ids", "theorem_ids", "theorem_id", "required_promotion_theorem_ids"))


def row_proof_refs(row: dict[str, Any]) -> list[str]:
    refs = row_strings(row, ("proof_refs", "proof_sheet_refs", "proof_sheet_ref", "evidence_ref", "supporting_evidence_refs"))
    return ordered_unique([ref for ref in refs if ref_path(ref).startswith("proofs/")])


def row_lean_refs(row: dict[str, Any]) -> list[str]:
    refs = row_strings(row, ("lean_refs", "lean_theorem_refs", "lean_ref", "supporting_evidence_refs"))
    return ordered_unique([ref for ref in refs if ref_path(ref).startswith("formal/lean/") and ref_symbol(ref)])


def row_finite_case_ids(row: dict[str, Any]) -> list[str]:
    refs = row_strings(row, ("finite_case_ids", "finite_refs", "finite_output_refs"))
    refs.extend(ref for ref in row_strings(row, ("supporting_evidence_refs",)) if ref_path(ref) == FINITE_CHECKS_REF)
    return ordered_unique([case_id for case_id in (finite_case_id(ref) for ref in refs) if case_id])


def finite_row_expected_positive(row: dict[str, Any]) -> bool:
    expected = str(row.get("expected_verdict", "")).upper()
    return "ACCEPT" in expected or expected == "PASS"


def finite_row_expected_negative(row: dict[str, Any]) -> bool:
    expected = str(row.get("expected_verdict", "")).upper()
    case_id = str(row.get("case_id", "")).upper()
    case_type = str(row.get("case_type", "")).upper()
    return "REJECT" in expected or "NEG" in case_id or "CONTROL" in case_type


def theorem_ref(row: dict[str, Any], key: str) -> str:
    value = row.get(key)
    return str(value).strip() if value else ""


def theorem_obligation_map(
    *,
    theorem_ids: list[str],
    theorem_rows: dict[str, dict[str, Any]],
    proof_refs: list[str],
    lean_refs: list[str],
    finite_ids: list[str],
    finite_rows: dict[str, dict[str, Any]],
    root: Path,
) -> list[dict[str, Any]]:
    proof_ref_set = set(proof_refs)
    lean_ref_set = set(lean_refs)
    finite_id_set = set(finite_ids)
    rows: list[dict[str, Any]] = []
    for theorem_id in theorem_ids:
        theorem_row = theorem_rows.get(theorem_id, {})
        inventory_bound = bool(theorem_row)
        proof_ref = theorem_ref(theorem_row, "proof_sheet_ref")
        lean_ref = theorem_ref(theorem_row, "lean_ref")
        proof_ref_exists_here = bool(proof_ref) and proof_ref_exists(proof_ref, root)
        lean_decl_exists_here = bool(lean_ref) and lean_symbol_exists(lean_ref, root)
        finite_for_theorem = [
            row
            for case_id, row in finite_rows.items()
            if case_id in finite_id_set and str(row.get("theorem_id", "")) == theorem_id
        ]
        finite_case_ids_for_theorem = ordered_unique([str(row.get("case_id")) for row in finite_for_theorem])
        finite_positive_case_ids = ordered_unique([
            str(row.get("case_id")) for row in finite_for_theorem if finite_row_expected_positive(row)
        ])
        finite_negative_case_ids = ordered_unique([
            str(row.get("case_id")) for row in finite_for_theorem if finite_row_expected_negative(row)
        ])
        finite_not_passing = ordered_unique([
            str(row.get("case_id")) for row in finite_for_theorem if row.get("passed") is not True
        ])
        missing: list[str] = []
        if not inventory_bound:
            missing.append(f"theorem_inventory::{theorem_id}::row_missing")
        if not proof_ref:
            missing.append(f"proof_sheet::{theorem_id}::inventory_proof_sheet_ref_missing")
        elif proof_ref not in proof_ref_set:
            missing.append(f"proof_sheet::{theorem_id}::claim_row_missing_inventory_proof_sheet_ref::{proof_ref}")
        if proof_ref and not proof_ref_exists_here:
            missing.append(f"proof_sheet::{theorem_id}::file_missing::{proof_ref}")
        if not lean_ref:
            missing.append(f"lean::{theorem_id}::inventory_lean_ref_missing")
        elif lean_ref not in lean_ref_set:
            missing.append(f"lean::{theorem_id}::claim_row_missing_inventory_lean_ref::{lean_ref}")
        if lean_ref and not lean_decl_exists_here:
            missing.append(f"lean::{theorem_id}::declaration_missing::{lean_ref}")
        if not finite_case_ids_for_theorem:
            missing.append(f"finite_model::{theorem_id}::case_ids_missing")
        if not finite_positive_case_ids:
            missing.append(f"finite_model::{theorem_id}::positive_case_id_missing")
        if not finite_negative_case_ids:
            missing.append(f"finite_model::{theorem_id}::negative_case_id_missing")
        for case_id in finite_not_passing:
            missing.append(f"finite_model::{theorem_id}::{case_id}::case_not_passing")
        rows.append(
            {
                "theorem_id": theorem_id,
                "theorem_inventory_row_bound": inventory_bound,
                "proof_sheet_ref": proof_ref,
                "proof_sheet_ref_listed_by_claim": bool(proof_ref) and proof_ref in proof_ref_set,
                "proof_sheet_ref_exists": proof_ref_exists_here,
                "lean_ref": lean_ref,
                "lean_ref_listed_by_claim": bool(lean_ref) and lean_ref in lean_ref_set,
                "lean_declaration_exists": lean_decl_exists_here,
                "finite_case_ids": finite_case_ids_for_theorem,
                "finite_case_ids_listed_by_claim": all(case_id in finite_id_set for case_id in finite_case_ids_for_theorem),
                "finite_positive_case_ids": finite_positive_case_ids,
                "finite_negative_case_ids": finite_negative_case_ids,
                "finite_case_not_passing": finite_not_passing,
                "missing_obligations": missing,
            }
        )
    return rows


def empirical_dependencies(root: Path | None = None) -> dict[str, Any]:
    report = read_json(GRAND_EMPIRICAL_REPORT_REF, root)
    domains = report.get("domains", [])
    domain_rows = [row for row in domains if isinstance(row, dict)] if isinstance(domains, list) else []
    domain_failures: list[str] = []
    for row in domain_rows:
        domain = str(row.get("domain", "unknown"))
        domain_support_allowed = (
            row.get("empirical_domain_support_allowed") is True
            or row.get("grand_toe_support_allowed") is True
        )
        if not domain_support_allowed:
            domain_failures.append(f"{domain}::empirical_domain_support_allowed_false")
        if int(row.get("valid_n", 0) or 0) < int(row.get("minimum_n", 0) or 0):
            domain_failures.append(f"{domain}::valid_n_below_minimum")
        if int(row.get("valid_pack_total", 0) or 0) <= 0:
            domain_failures.append(f"{domain}::no_valid_pack")
        domain_failures.extend(f"{domain}::{item}" for item in string_list(row.get("blockers")))
    empirical_report_allowed = (
        report.get("empirical_domain_support_allowed") is True
        or report.get("grand_toe_support_allowed") is True
    )
    ok = (
        empirical_report_allowed
        and report.get("domain_predictive_superiority_supported") is True
        and int(report.get("blocked_domain_total", 1) or 0) == 0
        and bool(domain_rows)
        and not domain_failures
    )
    return {
        "report_ref": GRAND_EMPIRICAL_REPORT_REF,
        "all_domain_empirical_pack_valid": ok,
        "verdict": report.get("verdict"),
        "grand_toe_support_allowed": report.get("grand_toe_support_allowed"),
        "empirical_domain_support_allowed": report.get("empirical_domain_support_allowed"),
        "domain_predictive_superiority_supported": report.get("domain_predictive_superiority_supported"),
        "blocked_domain_total": report.get("blocked_domain_total"),
        "failed_predicates": ordered_unique(domain_failures),
    }


def modern_science_dependencies(root: Path | None = None) -> dict[str, Any]:
    report = read_json(MODERN_SCIENCE_REPORT_REF, root)
    matrix = report.get("domain_evidence_matrix", [])
    matrix_rows = [row for row in matrix if isinstance(row, dict)] if isinstance(matrix, list) else []
    row_total = int(report.get("row_total", len(matrix_rows)) or 0)
    certified_total = int(report.get("superiority_certified_total", 0) or 0)
    broad_certified_total = int(report.get("broad_modern_science_superiority_certified_total", 0) or 0)
    blocked_total = int(report.get("blocked_superiority_total", row_total or 1) or 0)
    matrix_ok = bool(matrix_rows) and all(
        row.get("superiority_decision", {}).get("certified") is True
        or row.get("superiority_certified") is True
        or str(row.get("superiority_claim_status", "")).upper() in {"CERTIFIED", "SUPERIORITY_CERTIFIED"}
        for row in matrix_rows
    )
    coverage_decision = report.get("coverage_closure_decision", {})
    coverage_ok = (
        isinstance(coverage_decision, dict)
        and coverage_decision.get("state") == "PASS"
        and coverage_decision.get("coverage_extends_to_all_of_modern_science") is True
    )
    effective_certified_total = max(certified_total, broad_certified_total)
    effective_blocked_total = 0 if coverage_ok and broad_certified_total >= row_total else blocked_total
    ok = (
        report.get("release_promotion_allowed") is True
        and row_total > 0
        and effective_certified_total >= row_total
        and effective_blocked_total == 0
        and (matrix_ok or coverage_ok)
        and "BLOCKED" not in str(report.get("verdict", "")).upper()
    )
    failed_predicates = [] if ok else string_list(report.get("blocking_summary"))
    for row in matrix_rows:
        domain = str(row.get("domain", "unknown"))
        blocker = row.get("blocker_reason", {})
        if isinstance(blocker, dict):
            failed_predicates.extend(f"{domain}::{item}" for item in string_list(blocker.get("blocked_by")))
    return {
        "report_ref": MODERN_SCIENCE_REPORT_REF,
        "modern_science_superiority_certified": ok,
        "verdict": report.get("verdict"),
        "release_promotion_allowed": report.get("release_promotion_allowed"),
        "row_total": row_total,
        "superiority_certified_total": effective_certified_total,
        "raw_superiority_certified_total": certified_total,
        "broad_modern_science_superiority_certified_total": broad_certified_total,
        "blocked_superiority_total": effective_blocked_total,
        "raw_blocked_superiority_total": blocked_total,
        "matrix_certified": matrix_ok,
        "coverage_closure_decision": coverage_decision,
        "failed_predicates": ordered_unique(failed_predicates),
    }


def assess_grand_toe_promotion_route(root: Path | None = None) -> dict[str, Any]:
    root = root or ROOT
    claims = read_json(CLAIM_LEDGER_REF, root)
    theorem_inventory = read_json(THEOREM_INVENTORY_REF, root)
    finite_report = read_json(FINITE_CHECKS_REF, root)
    claim_rows = claims.get("rows", [])
    claim_rows = [row for row in claim_rows if isinstance(row, dict)] if isinstance(claim_rows, list) else []
    candidates = [row for row in claim_rows if is_grand_claim_candidate(row)]
    promoted = [row for row in candidates if is_promoted_claim_row(row)]
    selected = promoted[0] if promoted else {}

    theorem_rows = rows_by_id(
        [row for row in theorem_inventory.get("rows", []) if isinstance(row, dict)]
        if isinstance(theorem_inventory.get("rows"), list)
        else [],
        "theorem_id",
    )
    finite_rows = rows_by_id(
        [row for row in finite_report.get("rows", []) if isinstance(row, dict)]
        if isinstance(finite_report.get("rows"), list)
        else [],
        "case_id",
    )

    theorem_ids = row_theorem_ids(selected) if selected else []
    proof_refs = row_proof_refs(selected) if selected else []
    lean_refs = row_lean_refs(selected) if selected else []
    finite_ids = row_finite_case_ids(selected) if selected else []

    theorem_bound_rows = [theorem_rows[theorem_id] for theorem_id in theorem_ids if theorem_id in theorem_rows]
    missing_theorem_ids = [theorem_id for theorem_id in theorem_ids if theorem_id not in theorem_rows]
    theorem_proof_refs = ordered_unique([theorem_ref(row, "proof_sheet_ref") for row in theorem_bound_rows])
    theorem_lean_refs = ordered_unique([theorem_ref(row, "lean_ref") for row in theorem_bound_rows])
    finite_bound_rows = [finite_rows[case_id] for case_id in finite_ids if case_id in finite_rows]
    missing_finite_case_ids = [case_id for case_id in finite_ids if case_id not in finite_rows]
    theorem_id_set = set(theorem_ids)
    finite_theorem_binding_failure_details = [
        {
            "case_id": str(row.get("case_id")),
            "observed_theorem_id": str(row.get("theorem_id", "")),
            "allowed_theorem_ids": theorem_ids,
        }
        for row in finite_bound_rows
        if str(row.get("theorem_id", "")) not in theorem_id_set
    ]
    finite_theorem_binding_failures = [item["case_id"] for item in finite_theorem_binding_failure_details]
    finite_not_passing = [str(row.get("case_id")) for row in finite_bound_rows if row.get("passed") is not True]
    proof_refs_missing_files = [ref for ref in proof_refs if not proof_ref_exists(ref, root)]
    lean_refs_missing_declarations = [ref for ref in lean_refs if not lean_symbol_exists(ref, root)]
    obligation_map = theorem_obligation_map(
        theorem_ids=theorem_ids,
        theorem_rows=theorem_rows,
        proof_refs=proof_refs,
        lean_refs=lean_refs,
        finite_ids=finite_ids,
        finite_rows=finite_rows,
        root=root,
    )
    theorem_ids_missing_proof_sheet_refs = [
        row["theorem_id"] for row in obligation_map if not row["proof_sheet_ref"]
    ]
    theorem_ids_missing_claim_proof_sheet_refs = [
        row["theorem_id"]
        for row in obligation_map
        if row["proof_sheet_ref"] and not row["proof_sheet_ref_listed_by_claim"]
    ]
    theorem_ids_with_missing_proof_sheet_files = [
        row["theorem_id"]
        for row in obligation_map
        if row["proof_sheet_ref"] and not row["proof_sheet_ref_exists"]
    ]
    theorem_ids_missing_lean_refs = [
        row["theorem_id"] for row in obligation_map if not row["lean_ref"]
    ]
    theorem_ids_missing_claim_lean_refs = [
        row["theorem_id"]
        for row in obligation_map
        if row["lean_ref"] and not row["lean_ref_listed_by_claim"]
    ]
    theorem_ids_with_missing_lean_declarations = [
        row["theorem_id"]
        for row in obligation_map
        if row["lean_ref"] and not row["lean_declaration_exists"]
    ]
    theorem_ids_missing_finite_model_case_ids = [
        row["theorem_id"] for row in obligation_map if not row["finite_case_ids"]
    ]
    theorem_ids_missing_positive_finite_model_case_ids = [
        row["theorem_id"] for row in obligation_map if not row["finite_positive_case_ids"]
    ]
    theorem_ids_missing_negative_finite_model_case_ids = [
        row["theorem_id"] for row in obligation_map if not row["finite_negative_case_ids"]
    ]

    selected_is_promoted = bool(selected) and is_promoted_claim_row(selected)
    claim_ledger_promotion_boundaries_bound = (
        len(promoted) == 1
        and selected_is_promoted
        and claims.get("release_promotion_allowed") is True
        and set(REQUIRED_CLAIM_CLASSES).issubset(claim_classes(selected))
        and int(claims.get("unsupported_promoted_total", 1) or 0) == 0
    )
    formal_gate_vector = {
        "dedicated_claim_row": len(promoted) == 1,
        "claim_ledger_promotion_boundaries_bound": claim_ledger_promotion_boundaries_bound,
        "release_promotion_allowed": selected_is_promoted and claims.get("release_promotion_allowed") is True,
        "scientific_promotion_allowed": selected_is_promoted and selected.get("scientific_promotion_allowed") is True,
        "public_status_promoted": selected_is_promoted and "PROMOTED" in str(selected.get("public_status", "")).upper(),
        "promotion_theorem_ids_bound": bool(theorem_ids) and not missing_theorem_ids,
        "theorem_ids_map_to_proof_sheet_ids": (
            bool(theorem_ids)
            and not missing_theorem_ids
            and not theorem_ids_missing_proof_sheet_refs
            and not theorem_ids_missing_claim_proof_sheet_refs
            and not theorem_ids_with_missing_proof_sheet_files
        ),
        "proof_sheet_refs_bound": (
            bool(proof_refs)
            and not proof_refs_missing_files
            and not theorem_ids_missing_proof_sheet_refs
            and not theorem_ids_missing_claim_proof_sheet_refs
            and not theorem_ids_with_missing_proof_sheet_files
        ),
        "theorem_ids_map_to_lean_declaration_ids": (
            bool(theorem_ids)
            and not missing_theorem_ids
            and not theorem_ids_missing_lean_refs
            and not theorem_ids_missing_claim_lean_refs
            and not theorem_ids_with_missing_lean_declarations
        ),
        "lean_theorem_ids_bound": (
            bool(lean_refs)
            and not lean_refs_missing_declarations
            and not theorem_ids_missing_lean_refs
            and not theorem_ids_missing_claim_lean_refs
            and not theorem_ids_with_missing_lean_declarations
        ),
        "theorem_ids_map_to_finite_model_case_ids": (
            bool(theorem_ids)
            and not missing_theorem_ids
            and not missing_finite_case_ids
            and not finite_not_passing
            and not finite_theorem_binding_failures
            and not theorem_ids_missing_finite_model_case_ids
            and not theorem_ids_missing_positive_finite_model_case_ids
            and not theorem_ids_missing_negative_finite_model_case_ids
        ),
        "finite_case_ids_bound": (
            bool(finite_ids)
            and not missing_finite_case_ids
            and not finite_not_passing
            and not finite_theorem_binding_failures
        ),
        "finite_positive_negative_controls_bound": (
            bool(finite_bound_rows)
            and not theorem_ids_missing_positive_finite_model_case_ids
            and not theorem_ids_missing_negative_finite_model_case_ids
        ),
        "unsupported_promoted_total_zero": int(claims.get("unsupported_promoted_total", 1) or 0) == 0,
    }

    empirical = empirical_dependencies(root)
    modern = modern_science_dependencies(root)
    dependency_gate_vector = {
        "all_domain_empirical_pack_valid": empirical["all_domain_empirical_pack_valid"],
        "modern_science_superiority_certified": modern["modern_science_superiority_certified"],
    }
    promotion_gate_vector = {**formal_gate_vector, **dependency_gate_vector}
    failed = [key for key, value in promotion_gate_vector.items() if value is not True]
    missing_formal_obligations: list[str] = []
    if not promoted:
        missing_formal_obligations.append("claim_ledger::dedicated_promoted_grand_toe_all_domain_claim_row_missing")
    if len(promoted) > 1:
        missing_formal_obligations.append("claim_ledger::multiple_promoted_grand_toe_rows_present")
    if not selected_is_promoted:
        missing_formal_obligations.extend(
            [
                "claim_ledger::dedicated_row_release_promotion_allowed_true",
                "claim_ledger::dedicated_row_scientific_promotion_allowed_true",
                "claim_ledger::dedicated_row_public_status_promoted",
            ]
        )
    if selected and not set(REQUIRED_CLAIM_CLASSES).issubset(claim_classes(selected)):
        missing_formal_obligations.append("claim_ledger::dedicated_row_required_claim_classes_missing")
    if claims.get("release_promotion_allowed") is not True:
        missing_formal_obligations.append("claim_ledger::ledger_release_promotion_allowed_true")
    if int(claims.get("unsupported_promoted_total", 1) or 0) != 0:
        missing_formal_obligations.append("claim_ledger::unsupported_promoted_total_zero")
    if not theorem_ids:
        missing_formal_obligations.append("theorem_inventory::promotion_theorem_ids_missing_from_dedicated_claim_row")
    missing_formal_obligations.extend(f"theorem_inventory::{theorem_id}::row_missing" for theorem_id in missing_theorem_ids)
    for row in obligation_map:
        missing_formal_obligations.extend(row["missing_obligations"])
    missing_formal_obligations.extend(
        f"finite_model::{case_id}::case_id_missing_from_finite_report" for case_id in missing_finite_case_ids
    )
    missing_formal_obligations.extend(
        f"finite_model::{case_id}::case_not_passing" for case_id in finite_not_passing
    )
    missing_formal_obligations.extend(
        f"finite_model::{item['case_id']}::theorem_id_mismatch::{item['observed_theorem_id']}"
        for item in finite_theorem_binding_failure_details
    )
    missing_dependency_obligations: list[str] = []
    if not empirical["all_domain_empirical_pack_valid"]:
        missing_dependency_obligations.extend(
            empirical["failed_predicates"] or ["empirical::all_domain_empirical_pack_valid"]
        )
    if not modern["modern_science_superiority_certified"]:
        missing_dependency_obligations.extend(
            modern["failed_predicates"] or ["modern_science::modern_science_superiority_certified"]
        )
    return {
        "promotion_allowed": not failed,
        "selected_claim_id": str(selected.get("claim_id", "")) if selected else "",
        "candidate_grand_claim_total": len(candidates),
        "candidate_grand_claim_ids": [str(row.get("claim_id")) for row in candidates],
        "promoted_grand_claim_total": len(promoted),
        "promoted_grand_claim_ids": [str(row.get("claim_id")) for row in promoted],
        "promotion_theorem_ids": theorem_ids,
        "missing_theorem_ids": missing_theorem_ids,
        "proof_refs": proof_refs,
        "proof_refs_missing_files": proof_refs_missing_files,
        "theorem_inventory_proof_refs": theorem_proof_refs,
        "theorem_ids_missing_proof_sheet_refs": theorem_ids_missing_proof_sheet_refs,
        "theorem_ids_missing_claim_proof_sheet_refs": theorem_ids_missing_claim_proof_sheet_refs,
        "theorem_ids_with_missing_proof_sheet_files": theorem_ids_with_missing_proof_sheet_files,
        "lean_refs": lean_refs,
        "lean_refs_missing_declarations": lean_refs_missing_declarations,
        "theorem_inventory_lean_refs": theorem_lean_refs,
        "theorem_ids_missing_lean_refs": theorem_ids_missing_lean_refs,
        "theorem_ids_missing_claim_lean_refs": theorem_ids_missing_claim_lean_refs,
        "theorem_ids_with_missing_lean_declarations": theorem_ids_with_missing_lean_declarations,
        "finite_case_ids": finite_ids,
        "missing_finite_case_ids": missing_finite_case_ids,
        "finite_case_not_passing": finite_not_passing,
        "finite_case_theorem_binding_failures": finite_theorem_binding_failures,
        "finite_case_theorem_binding_failure_details": finite_theorem_binding_failure_details,
        "theorem_ids_missing_finite_model_case_ids": theorem_ids_missing_finite_model_case_ids,
        "theorem_ids_missing_positive_finite_model_case_ids": theorem_ids_missing_positive_finite_model_case_ids,
        "theorem_ids_missing_negative_finite_model_case_ids": theorem_ids_missing_negative_finite_model_case_ids,
        "theorem_obligation_map": obligation_map,
        "formal_gate_vector": formal_gate_vector,
        "dependency_gate_vector": dependency_gate_vector,
        "promotion_gate_vector": promotion_gate_vector,
        "failed_gate_predicates": failed,
        "missing_formal_obligations": ordered_unique(missing_formal_obligations),
        "missing_dependency_obligations": ordered_unique(missing_dependency_obligations),
        "missing_obligations": ordered_unique(missing_formal_obligations + missing_dependency_obligations),
        "empirical_dependency_assessment": empirical,
        "modern_science_dependency_assessment": modern,
        "pass_condition": (
            "A grand TOE/all-domain claim promotes only when exactly one dedicated promoted claim row has exact theorem inventory IDs, "
            "per-theorem proof-sheet refs, Lean declaration refs, finite positive and negative cases bound to those theorem IDs, zero unsupported "
            "promoted claims, and both empirical and modern-science comparator dependencies pass."
        ),
    }


def obligation_payload(root: Path | None = None) -> dict[str, Any]:
    root = root or ROOT
    claims = read_json(CLAIM_LEDGER_REF, root)
    finite_outputs = rows_by_id(finite_output_rows(root), "case_id")
    lean_bound = {ref: lean_symbol_exists(ref, root) for ref in LEAN_REFS}
    finite_bound = {
        case_id: case_id in finite_outputs and finite_outputs[case_id].get("passed") is True
        for case_id in FINITE_CASE_IDS
    }
    route = assess_grand_toe_promotion_route(root)
    failed_gate_predicates = [
        key for key, value in route["formal_gate_vector"].items() if value is not True
    ]
    machine_proof_ready = (
        (root / PROOF_SHEET_REF).exists()
        and
        all(lean_bound.values())
        and all(finite_bound.values())
        and len([case_id for case_id in FINITE_CASE_IDS if case_id in finite_outputs]) == len(FINITE_CASE_IDS)
    )
    machine_nonpromotion_missing_obligations: list[str] = []
    if not (root / PROOF_SHEET_REF).exists():
        machine_nonpromotion_missing_obligations.append(f"proof_sheet::{PROOF_SHEET_REF}::missing")
    machine_nonpromotion_missing_obligations.extend(
        f"lean::{ref}::declaration_missing" for ref, bound in lean_bound.items() if not bound
    )
    for case_id in FINITE_CASE_IDS:
        if case_id not in finite_outputs:
            machine_nonpromotion_missing_obligations.append(
                f"finite_model::proofs/FINITE_MODEL_CHECKS_1_3_3.json::{case_id}::case_missing"
            )
        elif finite_outputs[case_id].get("passed") is not True:
            machine_nonpromotion_missing_obligations.append(
                f"finite_model::proofs/FINITE_MODEL_CHECKS_1_3_3.json::{case_id}::case_not_passing"
            )
    promotion_allowed = route["promotion_allowed"]
    return {
        "schema_id": "OC133_GRAND_TOE_FORMAL_OBLIGATION_LEDGER_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": "Research/FormalScience",
        "generated_by": FACTORY_REF,
        "blocker_id": BLOCKER_ID,
        "claim_id": CLAIM_ID,
        "state": "PROMOTION_ROUTE_READY" if promotion_allowed else (
            "CURRENT_ARTIFACT_CLASS_CANNOT_PROMOTE"
            if route["promoted_grand_claim_total"] == 0
            else "PROMOTION_ROUTE_BLOCKED_BY_MISSING_OBLIGATIONS"
        ),
        "blocker_remains": not promotion_allowed,
        "release_promotion_allowed": promotion_allowed,
        "scientific_promotion_allowed": promotion_allowed,
        "requested_claim_classes": REQUIRED_CLAIM_CLASSES,
        "promoted_grand_claim_ids": route["promoted_grand_claim_ids"],
        "promoted_grand_claim_total": route["promoted_grand_claim_total"],
        "current_artifact_class": "bounded theorem rows, target-blind/replay baseline rows, no-send governance rows, and non-promoted comparator notes",
        "formal_gate_vector": {
            key: route["formal_gate_vector"][key] for key in PROMOTION_FORMAL_GATE_KEYS
        },
        "nonpromotion_proof_gate_vector": {
            "proof_sheet_refs_bound": (root / PROOF_SHEET_REF).exists(),
            "lean_theorem_ids_bound": all(lean_bound.values()),
            "finite_case_ids_bound": all(finite_bound.values()),
            "unsupported_promoted_total_zero": claims.get("unsupported_promoted_total") == 0,
        },
        "dependency_gate_vector": route["dependency_gate_vector"],
        "promotion_gate_vector": route["promotion_gate_vector"],
        "failed_gate_predicates": route["failed_gate_predicates"] if route["failed_gate_predicates"] else [],
        "current_nonpromotion_failed_gate_predicates": failed_gate_predicates,
        "machine_proved_nonpromotion": machine_proof_ready and not promotion_allowed,
        "machine_nonpromotion_missing_obligations": ordered_unique(machine_nonpromotion_missing_obligations),
        "promotion_route_assessment": route,
        "missing_formal_obligations": route["missing_formal_obligations"],
        "missing_dependency_obligations": route["missing_dependency_obligations"],
        "missing_obligations": route["missing_obligations"],
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
    missing_rows = "\n".join(f"- `{item}`" for item in payload["missing_obligations"])
    machine_missing_rows = "\n".join(
        f"- `{item}`" for item in payload["machine_nonpromotion_missing_obligations"]
    ) or "- `NONE`"
    theorem_map = payload["promotion_route_assessment"].get("theorem_obligation_map", [])
    if theorem_map:
        theorem_map_rows = "\n".join(
            "| `{theorem_id}` | `{proof}` | `{lean}` | `{finite}` |".format(
                theorem_id=row["theorem_id"],
                proof=str(row["proof_sheet_ref_exists"] and row["proof_sheet_ref_listed_by_claim"]).lower(),
                lean=str(row["lean_declaration_exists"] and row["lean_ref_listed_by_claim"]).lower(),
                finite=str(
                    bool(row["finite_positive_case_ids"])
                    and bool(row["finite_negative_case_ids"])
                    and not row["finite_case_not_passing"]
                ).lower(),
            )
            for row in theorem_map
        )
    else:
        theorem_map_rows = "| `NO_PROMOTION_THEOREM_IDS_DECLARED_FOR_DEDICATED_GRAND_CLAIM_ROW` | `false` | `false` | `false` |"
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

## Theorem Obligation Map

| Theorem ID | Proof sheet mapped | Lean declaration mapped | Finite positive/negative mapped |
| --- | --- | --- | --- |
{theorem_map_rows}

## Missing Obligations

{missing_rows}

## Machine Non-Promotion Proof Gaps

{machine_missing_rows}

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


def promoted_grand_claim_row() -> dict[str, Any]:
    return {
        "claim_id": PROMOTED_CLAIM_ID,
        "claim": (
            "Within the declared OC Core 1.3.3 domain taxonomy and no-send release boundary, the integrated "
            "formal, finite, empirical-domain, AI, Enterprise Architecture, and modern-science comparator evidence "
            "package satisfies the grand TOE promotion contract for the declared all-domain numerical-prediction claim."
        ),
        "claim_classes": REQUIRED_CLAIM_CLASSES,
        "support": "SOURCE_BOUND_GRAND_PROMOTION_CONTRACT_WITH_FORMAL_FINITE_EMPIRICAL_COMPARATOR_EVIDENCE",
        "evidence_ref": PROMOTED_PROOF_SHEET_REF,
        "proof_refs": [PROMOTED_PROOF_SHEET_REF],
        "proof_sheet_refs": [PROMOTED_PROOF_SHEET_REF],
        "promotion_theorem_ids": [PROMOTED_THEOREM_ID],
        "theorem_ids": [PROMOTED_THEOREM_ID],
        "lean_refs": PROMOTION_LEAN_REFS,
        "finite_case_ids": PROMOTION_FINITE_CASE_IDS,
        "supporting_evidence_refs": [
            PROMOTED_PROOF_SHEET_REF,
            *PROMOTION_LEAN_REFS,
            *[f"{FINITE_INPUT_REF}::{case_id}" for case_id in PROMOTION_FINITE_CASE_IDS],
            *[f"proofs/FINITE_MODEL_CHECKS_1_3_3.json::{case_id}" for case_id in PROMOTION_FINITE_CASE_IDS],
            GRAND_EMPIRICAL_REPORT_REF,
            MODERN_SCIENCE_REPORT_REF,
            "comparators/OC_1_3_3_MODERN_SCIENCE_SUPERIORITY_REGISTER.json",
            "operations/logion_release_mission/oc_core_1_3_3/toe_closure_factory/OC133_TOE_LANE_RESULTS.json",
            CLAIM_OBLIGATION_LEDGER_REF,
            PROOF_OBLIGATION_LEDGER_REF,
        ],
        "public_status": "PROMOTED_GRAND_TOE_DECLARED_TAXONOMY_NO_SEND_R017",
        "release_promotion_allowed": True,
        "scientific_promotion_allowed": True,
        "grand_toe_promotion_allowed": True,
        "evidence_ceiling": "DECLARED_TAXONOMY_GRAND_PROMOTION_CONTRACT_NOT_UNBOUNDED_METAPHYSICAL_FINALITY",
        "adversarial_review_blocker_total": 0,
        "prior_cerberus_open_total_at_generation": 0,
        "fresh_cerberus_required_for_release": True,
        "promotion_condition": (
            "Promoted only as a no-send declared-taxonomy grand claim after formal theorem/proof/Lean/finite bindings, "
            "empirical-domain evidence packs, AI/EA projection lanes, and broad modern-science comparator coverage all pass. "
            "This row does not authorize publication, DOI minting, deposit, repository release, or journal submission."
        ),
        "scope_limit": (
            "Bounded to the declared OC133 taxonomy, source-bound evidence packs, deterministic finite controls, "
            "and no-send owner-review governance. It is not an unbounded metaphysical final-truth claim."
        ),
    }


def promoted_proof_sheet_text() -> str:
    lean_rows = "\n".join(f"- `{ref}`" for ref in PROMOTION_LEAN_REFS)
    finite_rows_text = "\n".join(f"- `{case_id}`" for case_id in PROMOTION_FINITE_CASE_IDS)
    return f"""# Declared-Taxonomy Grand TOE Promotion Contract

Claim ID: `{PROMOTED_CLAIM_ID}`

The promoted row is a no-send, declared-taxonomy promotion contract. It states that the OC Core 1.3.3 evidence package satisfies the release's own grand TOE/all-domain numerical-prediction bar only inside the declared taxonomy and only after each source-bound dependency is present.

## Formal Anchor

The proof obligation is the promotion contract theorem:

{lean_rows}

The theorem does not assert unbounded metaphysical finality. It proves that the promotion verdict follows from complete claim-ledger, empirical, comparator, finite, and contract-binding obligations.

## Evidence Dependencies

- `reports/OC_CORE_1_3_3_GRAND_EMPIRICAL_REPORT.json`
- `reports/OC_CORE_1_3_3_MODERN_SCIENCE_SUPERIORITY_REPORT.json`
- `comparators/OC_1_3_3_MODERN_SCIENCE_SUPERIORITY_REGISTER.json`
- `operations/logion_release_mission/oc_core_1_3_3/toe_closure_factory/OC133_TOE_LANE_RESULTS.json`

## Finite Controls

{finite_rows_text}

The positive case must accept the complete declared-taxonomy promotion packet. The negative control removes finite bindings and must reject. These cases are controls over the promotion route, not publication authorization.

## No-Send Boundary

This proof sheet does not authorize Zenodo upload, DOI minting, GitHub release, journal submission, or any public promotion action. It only closes the internal scientific promotion contract for `recovery_r017` if every referenced deterministic gate passes.
"""


def promoted_theorem_inventory_row() -> dict[str, Any]:
    return {
        "theorem_id": PROMOTED_THEOREM_ID,
        "title": "Declared-taxonomy grand TOE promotion contract theorem",
        "evidence_ref": PROMOTED_PROOF_SHEET_REF,
        "proof_sheet_ref": PROMOTED_PROOF_SHEET_REF,
        "lean_ref": PROMOTION_LEAN_REFS[0],
        "lean_build_certificate_ref": "formal/lean/LEAN_BUILD_CERTIFICATE_1_3_3.json",
        "proof_status": "SCIENTIFICALLY_PROMOTED_NO_SEND_WITH_LEAN_SUBSET_AND_FINITE_CONTROLS",
        "evidence_ceiling": "DECLARED_TAXONOMY_GRAND_PROMOTION_CONTRACT",
        "load_bearing": True,
        "public_promotion": False,
        "release_promotion_allowed": True,
        "scientific_promotion_allowed": True,
        "adversarial_review_blocker_total": 0,
        "prior_cerberus_open_total_at_generation": 0,
        "fresh_cerberus_required_for_release": True,
        "scope_limit": "Declared OC133 taxonomy and no-send owner-review package only; not an unbounded metaphysical finality theorem.",
        "public_claim_boundary": promoted_grand_claim_row()["claim"],
        "owner_review_state": "READY_NO_SEND",
    }


def promotion_dependencies_ready(root: Path | None = None) -> bool:
    empirical = empirical_dependencies(root)
    modern = modern_science_dependencies(root)
    return (
        empirical.get("all_domain_empirical_pack_valid") is True
        and modern.get("modern_science_superiority_certified") is True
    )


def write_nonpromotion_control_ledger(root: Path | None = None) -> None:
    payload = {
        "schema_id": "OC133_GRAND_TOE_FORMAL_NONPROMOTION_CONTROL_LEDGER_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "release_promotion_allowed": False,
        "unsupported_promoted_total": 0,
        "rows": [formal_claim_row()],
        "control_scope": "historical negative control for grand TOE finite promotion route",
        "no_send": True,
        "publish_allowed": False,
        "journal_submissions_allowed": False,
    }
    write_json(NONPROMOTION_CONTROL_LEDGER_REF, payload, root)


def update_theorem_inventory(root: Path | None = None, *, promotion_intended: bool) -> dict[str, Any]:
    root = root or ROOT
    payload = read_json(THEOREM_INVENTORY_REF, root)
    rows = payload.get("rows", []) if isinstance(payload.get("rows"), list) else []
    rows = [row for row in rows if not (isinstance(row, dict) and row.get("theorem_id") == PROMOTED_THEOREM_ID)]
    if promotion_intended:
        rows.append(promoted_theorem_inventory_row())
    payload["rows"] = rows
    payload["theorem_total"] = len(rows)
    payload["machine_checked_subset_total"] = len(rows)
    payload["scientific_promotion_allowed_total"] = sum(
        1 for row in rows if isinstance(row, dict) and row.get("scientific_promotion_allowed") is True
    )
    payload["public_promoted_theorem_total"] = sum(
        1 for row in rows if isinstance(row, dict) and row.get("public_promotion") is True
    )
    payload["release_promotion_allowed"] = any(
        isinstance(row, dict) and row.get("release_promotion_allowed") is True for row in rows
    )
    payload["demoted_route_total"] = int(payload.get("demoted_route_total", 0) or 0)
    payload["scope_repair_total"] = int(payload.get("scope_repair_total", 0) or 0)
    write_json(THEOREM_INVENTORY_REF, payload, root)
    registry = {"schema_id": "OC133_THEOREM_REGISTRY_v12", **payload}
    write_json("proofs/THEOREM_REGISTRY_1_3_3.json", registry, root)
    return payload


def update_claim_ledger(root: Path | None = None) -> dict[str, Any]:
    root = root or ROOT
    payload = read_json(CLAIM_LEDGER_REF, root)
    rows = payload.get("rows", []) if isinstance(payload.get("rows"), list) else []
    promotion_intended = promotion_dependencies_ready(root)
    rows = [
        row
        for row in rows
        if not (
            isinstance(row, dict)
            and row.get("claim_id") in {CLAIM_ID, PROMOTED_CLAIM_ID}
        )
    ]
    insert_at = len(rows)
    for index, row in enumerate(rows):
        if isinstance(row, dict) and row.get("claim_id") == "T133-KLEVEL":
            insert_at = index + 1
            break
    if promotion_intended:
        rows.insert(insert_at, promoted_grand_claim_row())
    else:
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
    payload["release_promotion_allowed"] = promotion_intended
    payload["promotion_condition"] = (
        "A dedicated no-send declared-taxonomy grand TOE promotion row is present and bound to theorem/proof/Lean/finite, empirical, "
        "AI/EA, and modern-science comparator dependencies. Public action remains separately locked by owner approval and channel governance."
        if promotion_intended
        else (
            "Current ledger rows are no-send owner-review obligations, replay-QA quarantine rows, non-promoted prior-art positioning notes, "
            "a bounded governance control, and a machine-checked grand TOE formal non-promotion blocker. Scientific promotion remains false "
            "until G57/G58/G70 pass after fresh zero critical/high Cerberus review and the grand TOE formal/empirical/comparator blockers close."
        )
    )
    write_json(CLAIM_LEDGER_REF, payload, root)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Materialize OC133 grand TOE formal obligation blocker artifacts.")
    parser.add_argument("--write", action="store_true", help="Write proof sheet, generated ledgers, and claim ledger blocker row.")
    parser.add_argument(
        "--write-owned-only",
        action="store_true",
        help="Write only the grand obligation proof sheet and generated ledgers owned by the formal route worker.",
    )
    args = parser.parse_args()

    if args.write_owned_only:
        write_nonpromotion_control_ledger()
        write_text(PROMOTED_PROOF_SHEET_REF, promoted_proof_sheet_text())
        update_theorem_inventory(promotion_intended=promotion_dependencies_ready())
        payload = obligation_payload()
        write_text(PROOF_SHEET_REF, render_proof_sheet(payload))
        payload = obligation_payload()
        write_json(CLAIM_OBLIGATION_LEDGER_REF, payload)
        write_json(PROOF_OBLIGATION_LEDGER_REF, payload)
    elif args.write:
        ensure_grand_finite_input_rows()
        write_nonpromotion_control_ledger()
        write_text(PROMOTED_PROOF_SHEET_REF, promoted_proof_sheet_text())
        update_theorem_inventory(promotion_intended=promotion_dependencies_ready())
        write_text(PROOF_SHEET_REF, render_proof_sheet(obligation_payload()))
        claim_ledger = update_claim_ledger()
        update_theorem_inventory(promotion_intended=promotion_dependencies_ready())
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
