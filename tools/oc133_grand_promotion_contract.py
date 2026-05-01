from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


SCHEMA_ID = "OC133_GRAND_PROMOTION_CONTRACT_v1"
RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
CAPABILITY_OWNER = "Logion Research/FormalScience + Review/ClaimBoundary"

CLAIM_LEDGER_REL = "claims/CLAIM_LEDGER_1_3_3.json"
FORMAL_OBLIGATION_LEDGER_REL = "claims/GRAND_TOE_FORMAL_OBLIGATION_LEDGER_1_3_3.json"
GRAND_EMPIRICAL_REPORT_REL = "reports/OC_CORE_1_3_3_GRAND_EMPIRICAL_REPORT.json"
MODERN_SCIENCE_REPORT_REL = "reports/OC_CORE_1_3_3_MODERN_SCIENCE_SUPERIORITY_REPORT.json"
MODERN_SCIENCE_REGISTER_REL = "comparators/OC_1_3_3_MODERN_SCIENCE_SUPERIORITY_REGISTER.json"
FINITE_CHECKS_REL = "proofs/FINITE_MODEL_CHECKS_1_3_3.json"

CONTRACT_JSON_REL = "proofs/grand_promotion/OC133_GRAND_PROMOTION_CONTRACT_REPORT.json"
CONTRACT_MD_REL = "proofs/grand_promotion/OC133_GRAND_PROMOTION_CONTRACT_REPORT.md"
FACTORY_REF = "tools/oc133_grand_promotion_contract.py"

DEFAULT_REQUIRED_CLAIM_CLASSES = (
    "numerically_proven_toe",
    "all_domain_numerical_prediction",
    "predicts_better_than_modern_science",
)

CONTRACT_LEAN_REFS = (
    "formal/lean/OC133GrandPromotion.lean::grand_promotion_pass_requires_all_obligations",
    "formal/lean/OC133GrandPromotion.lean::grand_promotion_complete_control_accepts",
    "formal/lean/OC133GrandPromotion.lean::grand_promotion_current_artifact_class_cannot_promote",
    "formal/lean/OC133GrandPromotion.lean::grand_promotion_current_artifact_class_missing_claim_ledger_evidence",
    "formal/lean/OC133GrandPromotion.lean::grand_promotion_missing_empirical_pack_blocks_promotion",
    "formal/lean/OC133GrandPromotion.lean::grand_promotion_missing_modern_science_superiority_blocks_promotion",
    "formal/lean/OC133GrandPromotion.lean::grand_promotion_missing_finite_refs_blocks_promotion",
)

FORMAL_GATE_PREDICATES = (
    "dedicated_claim_row",
    "release_promotion_allowed",
    "scientific_promotion_allowed",
    "public_status_promoted",
    "promotion_theorem_ids_bound",
    "proof_refs_bound",
    "claim_lean_refs_bound",
    "finite_refs_bound",
    "finite_positive_negative_controls_bound",
    "unsupported_promoted_total_zero",
)

SYMBOL_DECL_RE = re.compile(
    r"^\s*(?:theorem|def|inductive|structure|abbrev)\s+([A-Za-z0-9_']+)\b",
    re.MULTILINE,
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def ordered_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if isinstance(value, (list, tuple)):
        result: list[str] = []
        for item in value:
            result.extend(string_list(item))
        return result
    return []


def gather_strings(row: dict[str, Any], keys: tuple[str, ...]) -> list[str]:
    values: list[str] = []
    for key in keys:
        values.extend(string_list(row.get(key)))
    return ordered_unique(values)


def ref_path(ref: str) -> str:
    return ref.split("::", 1)[0]


def ref_symbol(ref: str) -> str:
    return ref.split("::", 1)[1] if "::" in ref else ""


def declared_symbols(path: Path) -> set[str]:
    if not path.exists() or not path.is_file():
        return set()
    return set(SYMBOL_DECL_RE.findall(path.read_text(encoding="utf-8", errors="replace")))


def ref_bound(root: Path, ref: str, require_symbol: bool = False) -> bool:
    path = root / ref_path(ref)
    if not path.exists() or not path.is_file():
        return False
    symbol = ref_symbol(ref)
    if symbol or require_symbol:
        return bool(symbol) and symbol in declared_symbols(path)
    return True


def proof_ref_bound(root: Path, ref: str) -> bool:
    path_ref = ref_path(ref)
    if not path_ref.startswith("proofs/"):
        return False
    return (root / path_ref).is_file()


def is_proof_ref(ref: str) -> bool:
    path_ref = ref_path(ref)
    return path_ref.startswith("proofs/") and path_ref.lower().endswith((".md", ".tex", ".lean"))


def is_lean_ref(ref: str) -> bool:
    return ref_path(ref).startswith("formal/lean/") and bool(ref_symbol(ref))


def finite_case_id(ref: str) -> str:
    if "::" in ref:
        return ref.rsplit("::", 1)[1].strip()
    if "/" in ref or "\\" in ref or ref.endswith(".json"):
        return ""
    return ref.strip()


def finite_rows_by_case_id(finite_report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = finite_report.get("rows", [])
    if not isinstance(rows, list):
        return {}
    return {
        str(row.get("case_id")): row
        for row in rows
        if isinstance(row, dict) and row.get("case_id")
    }


def row_expected_positive(row: dict[str, Any]) -> bool:
    expected = str(row.get("expected_verdict", "")).upper()
    return "ACCEPT" in expected or expected == "PASS"


def row_expected_negative(row: dict[str, Any]) -> bool:
    case_id = str(row.get("case_id", "")).upper()
    expected = str(row.get("expected_verdict", "")).upper()
    case_type = str(row.get("case_type", "")).upper()
    return "REJECT" in expected or "NEG" in case_id or "CONTROL" in case_type


def claim_text(row: dict[str, Any]) -> str:
    return json.dumps(row, ensure_ascii=False, sort_keys=True).lower().replace("_", "-")


def row_claim_classes(row: dict[str, Any]) -> set[str]:
    classes: list[str] = []
    for key in ("claim_classes", "requested_claim_classes", "claim_class", "claim_type", "tags"):
        classes.extend(string_list(row.get(key)))
    return {item.lower() for item in classes}


def is_grand_claim_candidate(row: dict[str, Any], required_classes: tuple[str, ...]) -> bool:
    classes = row_claim_classes(row)
    if set(required_classes).issubset(classes):
        return True

    claim_id = str(row.get("claim_id", "")).lower()
    if claim_id.startswith("oc133-grand"):
        return True

    text = claim_text(row)
    has_grand_toe = (
        "grand-toe" in text
        or "grand toe" in text
        or "theory of everything" in text
        or "all-domain" in text
    )
    has_superiority_scope = (
        "predicts-better-than-modern-science" in text
        or "modern science" in text
        or "all-domain-numerical-prediction" in text
    )
    return has_grand_toe and has_superiority_scope


def is_promoted_claim_row(row: dict[str, Any]) -> bool:
    status = str(row.get("public_status", "")).upper()
    return (
        row.get("release_promotion_allowed") is True
        and row.get("scientific_promotion_allowed") is True
        and "PROMOTED" in status
    )


def row_proof_refs(row: dict[str, Any]) -> list[str]:
    refs = gather_strings(
        row,
        (
            "proof_refs",
            "proof_sheet_refs",
            "proof_sheet_ref",
            "evidence_ref",
            "supporting_evidence_refs",
        ),
    )
    return [ref for ref in refs if is_proof_ref(ref)]


def row_lean_refs(row: dict[str, Any]) -> list[str]:
    refs = gather_strings(
        row,
        (
            "lean_refs",
            "lean_theorem_refs",
            "lean_ref",
            "machine_proof_refs",
            "supporting_evidence_refs",
        ),
    )
    return [ref for ref in refs if is_lean_ref(ref)]


def row_theorem_ids(row: dict[str, Any]) -> list[str]:
    return gather_strings(
        row,
        (
            "promotion_theorem_ids",
            "theorem_ids",
            "theorem_id",
            "required_promotion_theorem_ids",
        ),
    )


def row_finite_case_ids(row: dict[str, Any]) -> list[str]:
    refs = gather_strings(
        row,
        (
            "finite_case_ids",
            "finite_refs",
            "finite_output_refs",
        ),
    )
    refs.extend(
        ref
        for ref in gather_strings(row, ("supporting_evidence_refs",))
        if ref_path(ref) == FINITE_CHECKS_REL
    )
    return ordered_unique([case_id for case_id in (finite_case_id(ref) for ref in refs) if case_id])


def required_claim_classes(formal_ledger: dict[str, Any]) -> tuple[str, ...]:
    configured = string_list(formal_ledger.get("requested_claim_classes"))
    if not configured:
        configured = list(DEFAULT_REQUIRED_CLAIM_CLASSES)
    return tuple(configured)


def assess_claim_ledger(
    root: Path,
    claim_ledger: dict[str, Any],
    formal_ledger: dict[str, Any],
    finite_report: dict[str, Any],
) -> dict[str, Any]:
    rows = claim_ledger.get("rows", [])
    claim_rows = [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []
    required_classes = required_claim_classes(formal_ledger)
    candidates = [row for row in claim_rows if is_grand_claim_candidate(row, required_classes)]
    promoted_candidates = [row for row in candidates if is_promoted_claim_row(row)]
    selected = promoted_candidates[0] if promoted_candidates else (candidates[0] if candidates else {})

    proof_refs = row_proof_refs(selected)
    lean_refs = row_lean_refs(selected)
    theorem_ids = row_theorem_ids(selected)
    finite_ids = row_finite_case_ids(selected)
    finite_rows = finite_rows_by_case_id(finite_report)
    finite_bound_rows = [finite_rows[case_id] for case_id in finite_ids if case_id in finite_rows]

    finite_refs_declared = bool(finite_ids)
    finite_refs_bound = (
        finite_refs_declared
        and len(finite_bound_rows) == len(finite_ids)
        and all(row.get("passed") is True for row in finite_bound_rows)
    )
    finite_positive_negative_controls_bound = (
        finite_refs_bound
        and any(row_expected_positive(row) for row in finite_bound_rows)
        and any(row_expected_negative(row) for row in finite_bound_rows)
    )

    top_release_allowed = claim_ledger.get("release_promotion_allowed") is True
    selected_is_promoted = bool(selected) and is_promoted_claim_row(selected)
    formal_gate_vector = {
        "dedicated_claim_row": bool(promoted_candidates),
        "release_promotion_allowed": selected_is_promoted and top_release_allowed,
        "scientific_promotion_allowed": bool(selected) and selected.get("scientific_promotion_allowed") is True,
        "public_status_promoted": selected_is_promoted and "PROMOTED" in str(selected.get("public_status", "")).upper(),
        "promotion_theorem_ids_bound": bool(theorem_ids),
        "proof_refs_bound": bool(proof_refs) and all(proof_ref_bound(root, ref) for ref in proof_refs),
        "claim_lean_refs_bound": bool(lean_refs) and all(ref_bound(root, ref, require_symbol=True) for ref in lean_refs),
        "finite_refs_bound": finite_refs_bound,
        "finite_positive_negative_controls_bound": finite_positive_negative_controls_bound,
        "unsupported_promoted_total_zero": int(claim_ledger.get("unsupported_promoted_total", 1) or 0) == 0,
    }
    return {
        "claim_ledger_ref": CLAIM_LEDGER_REL,
        "formal_obligation_ledger_ref": FORMAL_OBLIGATION_LEDGER_REL,
        "required_claim_classes": list(required_classes),
        "formal_obligation_ledger_blocker_remains": formal_ledger.get("blocker_remains") is True,
        "candidate_grand_claim_total": len(candidates),
        "candidate_grand_claim_ids": [str(row.get("claim_id")) for row in candidates],
        "promoted_grand_claim_total": len(promoted_candidates),
        "promoted_grand_claim_ids": [str(row.get("claim_id")) for row in promoted_candidates],
        "selected_claim_id": str(selected.get("claim_id", "")) if selected else "",
        "proof_refs": proof_refs,
        "promotion_theorem_ids": theorem_ids,
        "claim_lean_refs": lean_refs,
        "finite_case_ids": finite_ids,
        "finite_refs_declared": finite_refs_declared,
        "finite_positive_case_ids": [str(row.get("case_id")) for row in finite_bound_rows if row_expected_positive(row)],
        "finite_negative_case_ids": [str(row.get("case_id")) for row in finite_bound_rows if row_expected_negative(row)],
        "missing_finite_case_ids": [case_id for case_id in finite_ids if case_id not in finite_rows],
        "formal_gate_vector": formal_gate_vector,
        "failed_formal_gate_predicates": [key for key, value in formal_gate_vector.items() if value is not True],
    }


def assess_finite_checks(finite_report: dict[str, Any]) -> dict[str, Any]:
    rows = finite_report.get("rows", [])
    finite_rows = [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []
    passed_total = sum(1 for row in finite_rows if row.get("passed") is True)
    failed_rows = [
        str(row.get("case_id"))
        for row in finite_rows
        if row.get("passed") is not True
    ]
    finite_checks_passed = (
        finite_report.get("failure_total", 1) == 0
        and bool(finite_rows)
        and passed_total == len(finite_rows)
    )
    return {
        "finite_checks_ref": FINITE_CHECKS_REL,
        "finite_checks_passed": finite_checks_passed,
        "case_total": len(finite_rows),
        "passed_total": passed_total,
        "failure_total": finite_report.get("failure_total"),
        "failed_case_ids": failed_rows[:20],
    }


def assess_contract_lean_refs(root: Path) -> dict[str, Any]:
    rows = [
        {
            "lean_ref": ref,
            "bound": ref_bound(root, ref, require_symbol=True),
        }
        for ref in CONTRACT_LEAN_REFS
    ]
    return {
        "contract_lean_refs": list(CONTRACT_LEAN_REFS),
        "contract_lean_refs_bound": all(row["bound"] for row in rows),
        "rows": rows,
    }


def assess_grand_empirical(report: dict[str, Any]) -> dict[str, Any]:
    domains = report.get("domains", [])
    domain_rows = [row for row in domains if isinstance(row, dict)] if isinstance(domains, list) else []
    domain_failures: list[str] = []
    per_domain: list[dict[str, Any]] = []
    for row in domain_rows:
        blockers = string_list(row.get("blockers"))
        valid_n = int(row.get("valid_n", 0) or 0)
        minimum_n = int(row.get("minimum_n", 0) or 0)
        allowed = (
            row.get("grand_toe_support_allowed") is True
            and valid_n >= minimum_n
            and int(row.get("valid_pack_total", 0) or 0) > 0
            and not blockers
        )
        if not allowed:
            domain_failures.extend([f"{row.get('domain')}::{blocker}" for blocker in blockers])
        per_domain.append(
            {
                "domain": row.get("domain"),
                "grand_toe_support_allowed": row.get("grand_toe_support_allowed"),
                "valid_n": valid_n,
                "minimum_n": minimum_n,
                "valid_pack_total": row.get("valid_pack_total"),
                "status": row.get("status"),
                "blockers": blockers,
            }
        )

    all_domain_empirical_pack_valid = (
        report.get("grand_toe_support_allowed") is True
        and report.get("domain_predictive_superiority_supported") is True
        and int(report.get("blocked_domain_total", 1) or 0) == 0
        and bool(domain_rows)
        and all(row["grand_toe_support_allowed"] is True for row in per_domain)
        and all(int(row["valid_n"] or 0) >= int(row["minimum_n"] or 0) for row in per_domain)
        and all(int(row["valid_pack_total"] or 0) > 0 for row in per_domain)
    )
    return {
        "grand_empirical_report_ref": GRAND_EMPIRICAL_REPORT_REL,
        "all_domain_empirical_pack_valid": all_domain_empirical_pack_valid,
        "verdict": report.get("verdict"),
        "grand_toe_support_allowed": report.get("grand_toe_support_allowed"),
        "domain_predictive_superiority_supported": report.get("domain_predictive_superiority_supported"),
        "blocked_domain_total": report.get("blocked_domain_total"),
        "valid_evidence_pack_total": report.get("valid_evidence_pack_total"),
        "domain_rows": per_domain,
        "failed_predicates": ordered_unique(domain_failures),
    }


def assess_modern_science(report: dict[str, Any], register: dict[str, Any]) -> dict[str, Any]:
    matrix = report.get("domain_evidence_matrix")
    if not isinstance(matrix, list) or not matrix:
        matrix = register.get("domain_evidence_matrix", [])
    matrix_rows = [row for row in matrix if isinstance(row, dict)] if isinstance(matrix, list) else []

    row_total = int(report.get("row_total", len(matrix_rows)) or 0)
    certified_total = int(report.get("superiority_certified_total", 0) or 0)
    blocked_total = int(report.get("blocked_superiority_total", row_total) or 0)
    matrix_certified = bool(matrix_rows) and all(
        row.get("superiority_decision", {}).get("certified") is True
        for row in matrix_rows
    )
    report_certified = (
        report.get("release_promotion_allowed") is True
        and row_total > 0
        and certified_total == row_total
        and blocked_total == 0
        and "BLOCKED" not in str(report.get("verdict", "")).upper()
    )

    failed_predicates: list[str] = []
    failed_predicates.extend(string_list(report.get("blocking_summary")))
    for row in matrix_rows:
        domain = str(row.get("domain", "unknown"))
        blocker = row.get("blocker_reason", {})
        for predicate in string_list(blocker.get("blocked_by")):
            failed_predicates.append(f"{domain}::{predicate}")

    return {
        "modern_science_report_ref": MODERN_SCIENCE_REPORT_REL,
        "modern_science_register_ref": MODERN_SCIENCE_REGISTER_REL,
        "modern_science_superiority_certified": report_certified and matrix_certified,
        "verdict": report.get("verdict"),
        "release_promotion_allowed": report.get("release_promotion_allowed"),
        "row_total": row_total,
        "superiority_certified_total": certified_total,
        "blocked_superiority_total": blocked_total,
        "matrix_row_total": len(matrix_rows),
        "matrix_certified": matrix_certified,
        "failed_predicates": ordered_unique(failed_predicates),
    }


def gate_vector(
    claim_assessment: dict[str, Any],
    finite_assessment: dict[str, Any],
    lean_assessment: dict[str, Any],
    empirical_assessment: dict[str, Any],
    modern_assessment: dict[str, Any],
) -> dict[str, bool]:
    formal = claim_assessment["formal_gate_vector"]
    return {
        **{key: bool(formal.get(key)) for key in FORMAL_GATE_PREDICATES},
        "finite_checks_passed": bool(finite_assessment.get("finite_checks_passed")),
        "contract_lean_refs_bound": bool(lean_assessment.get("contract_lean_refs_bound")),
        "all_domain_empirical_pack_valid": bool(empirical_assessment.get("all_domain_empirical_pack_valid")),
        "modern_science_superiority_certified": bool(modern_assessment.get("modern_science_superiority_certified")),
    }


def open_blockers(vector: dict[str, bool]) -> list[str]:
    blockers: list[str] = []
    formal_keys = set(FORMAL_GATE_PREDICATES)
    if any(vector.get(key) is not True for key in formal_keys):
        blockers.append("grand_toe_claim_ledger_evidence")
    if vector.get("all_domain_empirical_pack_valid") is not True:
        blockers.append("grand_toe_empirical_superiority")
    if vector.get("modern_science_superiority_certified") is not True:
        blockers.append("modern_science_comparator_superiority")
    if vector.get("contract_lean_refs_bound") is not True:
        blockers.append("grand_promotion_contract_lean_refs_missing")
    if vector.get("finite_checks_passed") is not True:
        blockers.append("grand_promotion_finite_checks_not_passing")
    return blockers


def build_grand_promotion_contract(root: Path | None = None) -> dict[str, Any]:
    root = root or repo_root()
    claim_ledger = read_json(root / CLAIM_LEDGER_REL)
    formal_ledger = read_json(root / FORMAL_OBLIGATION_LEDGER_REL)
    finite_report = read_json(root / FINITE_CHECKS_REL)
    grand_empirical_report = read_json(root / GRAND_EMPIRICAL_REPORT_REL)
    modern_report = read_json(root / MODERN_SCIENCE_REPORT_REL)
    modern_register = read_json(root / MODERN_SCIENCE_REGISTER_REL)

    finite_assessment = assess_finite_checks(finite_report)
    lean_assessment = assess_contract_lean_refs(root)
    claim_assessment = assess_claim_ledger(root, claim_ledger, formal_ledger, finite_report)
    empirical_assessment = assess_grand_empirical(grand_empirical_report)
    modern_assessment = assess_modern_science(modern_report, modern_register)
    vector = gate_vector(claim_assessment, finite_assessment, lean_assessment, empirical_assessment, modern_assessment)
    failed = [key for key, value in vector.items() if value is not True]
    blockers = open_blockers(vector)

    return {
        "schema_id": SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "generated_by": FACTORY_REF,
        "lean_contract_module": "formal/lean/OC133GrandPromotion.lean",
        "contract_scope": "Reusable fail-closed promotion contract for future grand TOE/all-domain claims; it does not prove or promote the current artifacts.",
        "promotion_allowed": not failed,
        "verdict": "PASS" if not failed else "BLOCKED",
        "open_blockers": blockers,
        "failed_gate_predicates": failed,
        "promotion_gate_vector": vector,
        "claim_ledger_assessment": claim_assessment,
        "finite_checks_assessment": finite_assessment,
        "contract_lean_assessment": lean_assessment,
        "grand_empirical_assessment": empirical_assessment,
        "modern_science_assessment": modern_assessment,
        "pass_condition": (
            "PASS requires a dedicated promoted grand claim row with theorem IDs, proof refs, Lean refs, "
            "finite positive and negative refs, zero unsupported promoted claims, a passing finite report, "
            "valid all-domain empirical evidence packs, and certified modern-science superiority."
        ),
        "no_fabricated_pass_policy": (
            "Bounded theorem rows, replay QA, target-blind baseline rows, sample packs, and source-backed "
            "comparator notes are insufficient for this grand promotion contract."
        ),
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OC Core 1.3.3 Grand Promotion Contract",
        "",
        f"Verdict: `{report['verdict']}`",
        f"Promotion allowed: `{str(report['promotion_allowed']).lower()}`",
        "",
        report["contract_scope"],
        "",
        "Open blockers:",
        "",
    ]
    if report["open_blockers"]:
        for blocker in report["open_blockers"]:
            lines.append(f"- `{blocker}`")
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "Failed gate predicates:",
            "",
        ]
    )
    if report["failed_gate_predicates"]:
        for predicate in report["failed_gate_predicates"]:
            lines.append(f"- `{predicate}`")
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "Gate vector:",
            "",
            "| Predicate | Value |",
            "| --- | --- |",
        ]
    )
    for key, value in report["promotion_gate_vector"].items():
        lines.append(f"| `{key}` | `{str(value).lower()}` |")
    lines.extend(
        [
            "",
            "Pass condition:",
            "",
            report["pass_condition"],
            "",
            "No fabricated pass policy:",
            "",
            report["no_fabricated_pass_policy"],
            "",
        ]
    )
    return "\n".join(lines)


def build_all(root: Path | None = None) -> dict[str, dict[str, Any]]:
    root = root or repo_root()
    report = build_grand_promotion_contract(root)
    return {
        CONTRACT_JSON_REL: report,
        CONTRACT_MD_REL: {"text": render_markdown(report)},
    }


def write_outputs(root: Path | None = None) -> None:
    root = root or repo_root()
    payloads = build_all(root)
    for rel, payload in payloads.items():
        path = root / rel
        if rel.endswith(".md"):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(payload["text"] + "\n", encoding="utf-8", newline="\n")
        else:
            write_json(path, payload)


def check_stored(root: Path | None = None) -> list[str]:
    root = root or repo_root()
    expected = build_all(root)
    errors: list[str] = []
    for rel, payload in expected.items():
        path = root / rel
        if rel.endswith(".md"):
            actual_text = path.read_text(encoding="utf-8") if path.exists() else ""
            if actual_text != payload["text"] + "\n":
                errors.append(f"{rel} is not synchronized with {FACTORY_REF}")
        else:
            actual = read_json(path)
            if actual != payload:
                errors.append(f"{rel} is not synchronized with {FACTORY_REF}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Check the OC133 grand TOE/all-domain promotion contract.")
    parser.add_argument("--write", action="store_true", help="Write the contract report under proofs/grand_promotion.")
    parser.add_argument("--check", action="store_true", help="Check stored contract reports against the deterministic builder.")
    parser.add_argument("--allow-blocked-exit-zero", action="store_true", help="Return zero even when the current contract is blocked.")
    args = parser.parse_args()

    root = repo_root()
    if args.write:
        write_outputs(root)
        report = build_grand_promotion_contract(root)
        print(f"grand promotion contract materialized; verdict={report['verdict']}")
        return 0

    if args.check:
        errors = check_stored(root)
        if errors:
            for error in errors:
                print(f"ERROR: {error}")
            return 1
        print("grand promotion contract check passed; current grand promotion remains blocked")
        return 0

    report = build_grand_promotion_contract(root)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["promotion_allowed"] or args.allow_blocked_exit_zero:
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
