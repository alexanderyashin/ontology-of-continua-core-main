from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


SCHEMA_ID = "OC_CORE_1_3_3_STRICT_CLAIM_EVIDENCE_SYNC_v1"
RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
CAPABILITY_OWNER = "Logion Research/FormalScience + Review/ClaimBoundary"

CLAIM_LEDGER_REL = "claims/CLAIM_LEDGER_1_3_3.json"
THEOREM_INVENTORY_REL = "proofs/THEOREM_INVENTORY_1_3_3.json"
FINITE_CHECKS_REL = "proofs/FINITE_MODEL_CHECKS_1_3_3.json"
GRAND_PROMOTION_CONTRACT_REL = "proofs/grand_promotion/OC133_GRAND_PROMOTION_CONTRACT_REPORT.json"
GRAND_EMPIRICAL_REPORT_REL = "reports/OC_CORE_1_3_3_GRAND_EMPIRICAL_REPORT.json"
SYNC_REPORT_JSON_REL = "reports/OC_CORE_1_3_3_STRICT_CLAIM_EVIDENCE_SYNC.json"
SYNC_REPORT_MD_REL = "reports/OC_CORE_1_3_3_STRICT_CLAIM_EVIDENCE_SYNC.md"
FACTORY_REF = "tools/oc133_strict_claim_evidence_synchronizer.py"

TARGET_GRAND_CLAIM_CLASSES = (
    "numerically_proven_toe",
    "all_domain_numerical_prediction",
    "predicts_better_than_modern_science",
)
TARGET_GRAND_CLAIM_KEYWORDS = (
    "all-domain",
    "all domain",
    "across all domains",
    "grand",
    "theory of everything",
    "irrefutable",
    "toe",
    "numerically proven",
    "better than modern science",
    "numerical superiority",
)
FORMAL_ISSUES = (
    "promotion_theorem_ids_missing",
    "promotion_theorem_ids_unknown",
    "theorem_inventory_row_missing",
    "proof_ref_missing",
    "lean_ref_missing",
    "finite_case_ref_missing",
    "finite_case_not_passing",
    "finite_controls_incomplete",
)
CAPABILITY_BY_ISSUE = {
    "promotion_theorem_ids_missing": "Research/FormalScience",
    "promotion_theorem_ids_unknown": "Research/FormalScience",
    "theorem_inventory_row_missing": "Research/FormalScience",
    "proof_ref_missing": "Research/FormalScience",
    "lean_ref_missing": "Research/FormalScience",
    "finite_case_ref_missing": "Research/FormalScience",
    "finite_case_not_passing": "Research/FormalScience",
    "finite_controls_incomplete": "Research/FormalScience",
}
LEAN_DECL_RE = re.compile(r"^\s*(?:theorem|def|lemma|abbrev|inductive|structure)\s+([A-Za-z0-9_']+)\b", re.MULTILINE)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


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
        if value not in seen:
            seen.add(value)
            out.append(value)
    return out


def ref_source(ref: str) -> str:
    return ref.split("::", 1)[0].strip()


def ref_symbol(ref: str) -> str:
    return ref.split("::", 1)[1].strip() if "::" in ref else ""


def read_file(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def is_promoted(row: dict[str, Any]) -> bool:
    public_status = str(row.get("public_status", "")).upper()
    return (
        row.get("release_promotion_allowed") is True
        and row.get("scientific_promotion_allowed") is True
        and "PROMOTED" in public_status
    )


def claim_classes(row: dict[str, Any]) -> set[str]:
    classes: list[str] = []
    for key in ("claim_classes", "requested_claim_classes", "claim_class", "claim_type", "tags", "classifications"):
        classes.extend(item.lower().replace("-", "_").replace(" ", "_") for item in string_list(row.get(key)))
    return set(classes)


def is_target_grand_claim(row: dict[str, Any]) -> bool:
    text = json.dumps(row, ensure_ascii=False).lower()
    classes = claim_classes(row)
    if classes.intersection(set(TARGET_GRAND_CLAIM_CLASSES)):
        return True
    if any(token in text for token in TARGET_GRAND_CLAIM_KEYWORDS):
        return True
    return False


def row_proof_refs(row: dict[str, Any]) -> list[str]:
    keys = (
        "proof_refs",
        "proof_sheet_refs",
        "proof_sheet_ref",
        "evidence_ref",
        "supporting_evidence_refs",
    )
    refs: list[str] = []
    for key in keys:
        refs.extend(string_list(row.get(key)))
    return ordered_unique([ref for ref in refs if ref and ref_source(ref)])


def row_lean_refs(row: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    for key in ("lean_refs", "lean_theorem_refs", "lean_ref", "machine_proof_refs"):
        refs.extend(string_list(row.get(key)))
    return ordered_unique([ref for ref in refs if ref and ref_source(ref) and "::" in ref])


def row_theorem_ids(row: dict[str, Any]) -> list[str]:
    out = ordered_unique(string_list(row.get("promotion_theorem_ids")))
    out.extend(string_list(row.get("theorem_ids")))
    out.extend(string_list(row.get("required_promotion_theorem_ids")))
    return ordered_unique(out)


def row_finite_refs(row: dict[str, Any]) -> list[str]:
    refs = string_list(row.get("finite_case_ids"))
    for key in ("finite_refs", "finite_output_refs", "finite_control_refs"):
        refs.extend(string_list(row.get(key)))
    refs.extend(
        item
        for item in string_list(row.get("supporting_evidence_refs"))
        if ref_source(item) == FINITE_CHECKS_REL
    )
    normalized: list[str] = []
    for ref in refs:
        if "::" in ref:
            normalized.append(ref_symbol(ref))
        else:
            normalized.append(ref)
    return ordered_unique([item for item in normalized if item])


def proof_ref_exists(root: Path, ref: str) -> bool:
    source = root / ref_source(ref)
    return source.exists()


def lean_ref_exists(root: Path, ref: str) -> bool:
    source = root / ref_source(ref)
    symbol = ref_symbol(ref)
    text = read_file(source)
    return bool(source.exists()) and bool(symbol) and symbol in set(LEAN_DECL_RE.findall(text))


def assess_claim(
    root: Path,
    claim: dict[str, Any],
    theorem_inventory: dict[str, Any],
    finite_report: dict[str, Any],
    issue_prefix: str,
) -> dict[str, Any]:
    theorem_rows = {
        str(row.get("theorem_id")): row
        for row in theorem_inventory.get("rows", [])
        if isinstance(row, dict) and row.get("theorem_id")
    } if isinstance(theorem_inventory, dict) else {}
    finite_rows = {
        str(row.get("case_id")): row
        for row in finite_report.get("rows", [])
        if isinstance(row, dict) and row.get("case_id")
    } if isinstance(finite_report, dict) else {}

    proof_refs = row_proof_refs(claim)
    lean_refs = row_lean_refs(claim)
    theorem_ids = row_theorem_ids(claim)
    finite_ids = row_finite_refs(claim)

    missing: list[str] = []
    issue_trace: list[dict[str, Any]] = []

    if not theorem_ids:
        missing.append("promotion_theorem_ids_missing")
        issue_trace.append({"issue": "promotion_theorem_ids_missing", "details": "No promotion_theorem_ids declared on the claim row."})
    theorem_rows_bound: list[dict[str, Any]] = []
    unknown_theorem_ids: list[str] = []
    for theorem_id in theorem_ids:
        theorem_row = theorem_rows.get(str(theorem_id))
        if theorem_row is None:
            unknown_theorem_ids.append(str(theorem_id))
            continue
        theorem_rows_bound.append(theorem_row)
        inv_proof = str(theorem_row.get("proof_sheet_ref", "")).strip()
        inv_lean = str(theorem_row.get("lean_ref", "")).strip()
        if inv_proof and inv_proof not in proof_refs:
            proof_refs.append(inv_proof)
        if inv_lean and inv_lean not in lean_refs:
            lean_refs.append(inv_lean)

    if unknown_theorem_ids:
        missing.append("promotion_theorem_ids_unknown")
        issue_trace.append(
            {
                "issue": "promotion_theorem_ids_unknown",
                "details": "These theorem IDs are not present in the theorem inventory.",
                "missing_theorem_ids": unknown_theorem_ids,
            }
        )

    missing_proofs = [ref for ref in proof_refs if not proof_ref_exists(root, ref)]
    if missing_proofs:
        missing.append("proof_ref_missing")
        issue_trace.append({"issue": "proof_ref_missing", "details": "Proof references are missing from the local proof surface.", "proof_refs": missing_proofs})

    missing_lean = [ref for ref in lean_refs if not lean_ref_exists(root, ref)]
    if missing_lean:
        missing.append("lean_ref_missing")
        issue_trace.append({"issue": "lean_ref_missing", "details": "Lean theorem references are missing or unbound to files.", "lean_refs": missing_lean})

    if not finite_ids:
        missing.append("finite_case_ref_missing")
        issue_trace.append({"issue": "finite_case_ref_missing", "details": "No finite case IDs declared for promoted evidence."})

    unknown_case_ids = [case_id for case_id in finite_ids if case_id not in finite_rows]
    if unknown_case_ids:
        missing.append("finite_case_ref_missing")
        issue_trace.append({"issue": "finite_case_ref_missing", "details": "Finite IDs are not present in finite checks.", "finite_case_ids": unknown_case_ids})

    finite_present = [finite_rows[case_id] for case_id in finite_ids if case_id in finite_rows]
    not_passing = [str(row.get("case_id")) for row in finite_present if row.get("passed") is not True]
    if not_passing:
        missing.append("finite_case_not_passing")
        issue_trace.append({"issue": "finite_case_not_passing", "details": "Finite evidence rows are present but failed.", "case_ids": not_passing})
    expected_verdicts = [str(row.get("expected_verdict", "")).upper() for row in finite_present]
    has_accept = any("ACCEPT" in value for value in expected_verdicts)
    has_reject = any("REJECT" in value for value in expected_verdicts)
    if finite_present and (not has_accept or not has_reject):
        missing.append("finite_controls_incomplete")
        issue_trace.append(
            {
                "issue": "finite_controls_incomplete",
                "details": "Promoted evidence must include finite positive and finite negative/control rows.",
                "case_ids": [str(row.get("case_id")) for row in finite_present],
            }
        )

    missing = ordered_unique(missing)
    status = "PASS" if not missing else "BLOCKED"

    return {
        "claim_id": str(claim.get("claim_id", "")),
        "claim": str(claim.get("claim", "")),
        "claim_classes": sorted(claim_classes(claim)),
        "status": status,
        "promotion_theorem_ids": theorem_ids,
        "proof_refs": proof_refs,
        "lean_refs": lean_refs,
        "finite_case_ids": finite_ids,
        "missing_issues": ordered_unique(missing),
        "issue_prefix": issue_prefix,
        "issue_trace": issue_trace,
        "theorem_inventory_rows_found": len(theorem_rows_bound),
        "unknown_theorem_ids": unknown_theorem_ids,
        "finite_case_total": len(finite_present),
        "finite_case_not_passing_total": len(not_passing),
        "evidence_surface_complete": status == "PASS",
    }


def assess_empirical_and_contract_gates(contract: dict[str, Any], empirical: dict[str, Any], has_targets: bool) -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
    contract_ok = contract.get("promotion_allowed") is True or str(contract.get("verdict", "")).upper() == "PASS"
    empirical_ok = empirical.get("grand_toe_support_allowed") is True and int(empirical.get("blocked_domain_total", 1) or 0) == 0
    blockers: list[dict[str, Any]] = []

    if not has_targets:
        blockers.append(
            {
                "issue_id": "grand_claim_promotion_surface_missing",
                "owner_capability": "Research/FormalScience + Review/ClaimBoundary",
                "required_artifacts": [CLAIM_LEDGER_REL, THEOREM_INVENTORY_REL, GRAND_PROMOTION_CONTRACT_REL],
                "required_action": "Create a dedicated promoted grand-claim candidate surface only when its theorem, proof-sheet, Lean, finite-model, empirical, and comparator evidence can bind; otherwise keep final TOE readiness blocked.",
                "before_predicate": "No promoted TOE/all-domain/numeric-superiority claim row exists, so absence of overclaim cannot count as final scientific closure.",
                "after_predicate": "At least one dedicated promoted grand claim exists and passes strict claim-evidence synchronization under the same gates.",
            }
        )
    if has_targets and not contract_ok:
        blockers.append(
            {
                "issue_id": "grand_promotion_contract_not_pass",
                "owner_capability": "Research/FormalScience",
                "required_artifacts": [GRAND_PROMOTION_CONTRACT_REL],
                "required_action": "Close the grand promotion contract as evidence-surface complete and rerun all-domain readiness checks.",
                "before_predicate": "grand promotion contract remains blocked on claim-evidence synchrony.",
                "after_predicate": "grand promotion contract state is PASS while promoted claims remain explicitly evidence-bound.",
            }
        )
    if has_targets and not empirical_ok:
        blockers.append(
            {
                "issue_id": "grand_empirical_support_not_ready",
                "owner_capability": "Research/EmpiricalScience",
                "required_artifacts": [GRAND_EMPIRICAL_REPORT_REL],
                "required_action": "Close grand empirical support blockers for strict all-domain prediction support, then rerun synchronized closure check.",
                "before_predicate": "grand empirical report remains BLOCKED or grand_toe_support_allowed is false.",
                "after_predicate": "grand empirical report is fully unblocked for strict predictive support.",
            }
        )

    gate = bool(has_targets) and contract_ok and empirical_ok
    summary = {
        "mission_requires_grand_claim_surface": True,
        "target_claim_surface_present": bool(has_targets),
        "contract_verdict": str(contract.get("verdict", "")),
        "promotion_contract_pass": contract_ok,
        "empirical_verdict": str(empirical.get("verdict", "")),
        "grand_toe_support_allowed": empirical.get("grand_toe_support_allowed"),
        "blocked_domain_total": empirical.get("blocked_domain_total", 0),
    }
    return ("PASS" if gate else "BLOCKED"), blockers, summary


def build_claim_evidence_sync_report(root: Path | None = None) -> dict[str, Any]:
    root = root or repo_root()
    claim_ledger = read_json(root / CLAIM_LEDGER_REL)
    theorem_inventory = read_json(root / THEOREM_INVENTORY_REL)
    finite_checks = read_json(root / FINITE_CHECKS_REL)
    grand_promotion_contract = read_json(root / GRAND_PROMOTION_CONTRACT_REL)
    grand_empirical_report = read_json(root / GRAND_EMPIRICAL_REPORT_REL)

    rows = claim_ledger.get("rows", [])
    claim_rows = [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []
    candidates = [
        row
        for row in claim_rows
        if is_promoted(row) and is_target_grand_claim(row)
    ]

    candidates_prefix = str(len(candidates))
    candidate_assessments = [
        assess_claim(root, row, theorem_inventory, finite_checks, candidates_prefix)
        for row in candidates
    ]
    blocked_claims = [row for row in candidate_assessments if row["status"] == "BLOCKED"]
    supported_claims = [row for row in candidate_assessments if row["status"] == "PASS"]

    gate, gate_blockers, gate_summary = assess_empirical_and_contract_gates(
        grand_promotion_contract,
        grand_empirical_report,
        has_targets=bool(candidates),
    )

    work_orders: list[dict[str, Any]] = []
    def add_order(
        *,
        idx: int,
        claim_id: str,
        capability: str,
        issue: str,
        action: str,
        artifacts: list[str],
        before_predicate: str,
        after_predicate: str,
    ) -> None:
        work_orders.append(
            {
                "work_order_id": f"OC133-STRICT-CE-SYNC-{idx:03d}",
                "claim_id": claim_id,
                "owner_capability": capability,
                "missing_issue": issue,
                "required_action": action,
                "required_artifacts": artifacts,
                "before_predicate": before_predicate,
                "after_predicate": after_predicate,
                "closure_rule": "Capability-specific repair should create concrete evidence surfaces; no artifact existence outside this scope may close this blocker.",
                "no_send": True,
            }
        )

    order_idx = 1
    for row in blocked_claims:
        issue_trace = row.get("issue_trace", [])
        for item in issue_trace:
            issue = str(item.get("issue", ""))
            capability = CAPABILITY_BY_ISSUE.get(issue, "Research/FormalScience")
            if issue == "promotion_theorem_ids_missing":
                add_order(
                    idx=order_idx,
                    claim_id=row["claim_id"],
                    capability=capability,
                    issue=issue,
                    action="Add a non-empty `promotion_theorem_ids` list for the promoted grand claim row.",
                    artifacts=[THEOREM_INVENTORY_REL, GRAND_PROMOTION_CONTRACT_REL],
                    before_predicate=f"Claim {row['claim_id']} is promoted grand scope without theorem IDs.",
                    after_predicate="The claim identifies one or more dedicated theorem IDs present in theorem inventory.",
                )
                order_idx += 1
            elif issue == "promotion_theorem_ids_unknown":
                add_order(
                    idx=order_idx,
                    claim_id=row["claim_id"],
                    capability=capability,
                    issue=issue,
                    action="Register every claimed theorem ID in theorem inventory with theorem, proof-sheet, and Lean refs.",
                    artifacts=[THEOREM_INVENTORY_REL],
                    before_predicate=f"Claim {row['claim_id']} references theorem IDs not declared in theorem inventory.",
                    after_predicate="Theorem IDs declared on claim are present in theorem inventory.",
                )
                order_idx += 1
            elif issue == "proof_ref_missing":
                add_order(
                    idx=order_idx,
                    claim_id=row["claim_id"],
                    capability=capability,
                    issue=issue,
                    action="Bind each dedicated grand theorem claim to a committed proof-sheet artifact and keep the ref surface stable.",
                    artifacts=[*{ref for ref in row.get("proof_refs", []) if isinstance(ref, str)}],
                    before_predicate=f"Claim {row['claim_id']} references missing proof-sheet artifacts.",
                    after_predicate="All required proof-sheet artifact references resolve to committed proof files.",
                )
                order_idx += 1
            elif issue == "lean_ref_missing":
                add_order(
                    idx=order_idx,
                    claim_id=row["claim_id"],
                    capability=capability,
                    issue=issue,
                    action="Add concrete Lean theorem references for each dedicated grand theorem and verify symbol presence.",
                    artifacts=[*{ref for ref in row.get("lean_refs", []) if isinstance(ref, str)}],
                    before_predicate=f"Claim {row['claim_id']} references missing Lean theorem files or unbound symbols.",
                    after_predicate="All required Lean theorem references resolve with exact symbols.",
                )
                order_idx += 1
            elif issue == "finite_case_ref_missing":
                add_order(
                    idx=order_idx,
                    claim_id=row["claim_id"],
                    capability=capability,
                    issue=issue,
                    action="Bind dedicated finite positive/negative rows to the promoted claim and include them in finite model checks.",
                    artifacts=[FINITE_CHECKS_REL],
                    before_predicate=f"Claim {row['claim_id']} has missing finite evidence case IDs.",
                    after_predicate="Dedicated finite case IDs are present and bound in finite checks output.",
                )
                order_idx += 1
            elif issue == "finite_case_not_passing":
                add_order(
                    idx=order_idx,
                    claim_id=row["claim_id"],
                    capability=capability,
                    issue=issue,
                    action="Repair or regenerate finite rows until dedicated grand theorem evidence passes.",
                    artifacts=[FINITE_CHECKS_REL, "proofs/finite_model_checks/run_finite_model_checks.py"],
                    before_predicate=f"Claim {row['claim_id']} has failing dedicated finite rows.",
                    after_predicate="Dedicated finite evidence rows are present and passed.",
                )
                order_idx += 1
            elif issue == "finite_controls_incomplete":
                add_order(
                    idx=order_idx,
                    claim_id=row["claim_id"],
                    capability=capability,
                    issue=issue,
                    action="Add explicit positive and negative/control finite rows so claim promotion is bounded by falsifier evidence.",
                    artifacts=[FINITE_CHECKS_REL],
                    before_predicate=f"Claim {row['claim_id']} lacks a paired finite positive/negative evidence structure.",
                    after_predicate="Finite evidence includes accepted and rejected witness/control rows.",
                )
                order_idx += 1

    for blocker in gate_blockers:
        add_order(
            idx=order_idx,
            claim_id="OC133-GRAND-TOE-PROMOTION",
            capability=blocker["owner_capability"],
            issue=blocker["issue_id"],
            action=blocker["required_action"],
            artifacts=blocker["required_artifacts"],
            before_predicate=blocker["before_predicate"],
            after_predicate=blocker["after_predicate"],
        )
        order_idx += 1

    payload: dict[str, Any] = {
        "schema_id": SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "generated_by": FACTORY_REF,
        "sync_scope": "Synchronize promoted grand-claim ledger rows to theorem inventory, proof-sheet, Lean theorem, and finite evidence surfaces; never narrow claim text.",
        "claim_ledger_ref": CLAIM_LEDGER_REL,
        "theorem_inventory_ref": THEOREM_INVENTORY_REL,
        "finite_report_ref": FINITE_CHECKS_REL,
        "grand_promotion_contract_ref": GRAND_PROMOTION_CONTRACT_REL,
        "grand_empirical_report_ref": GRAND_EMPIRICAL_REPORT_REL,
        "target_claim_total": len(candidates),
        "target_claim_ids": [str(row.get("claim_id", "")) for row in candidates],
        "blocked_claim_total": len(blocked_claims),
        "supported_claim_total": len(supported_claims),
        "claim_assessments": candidate_assessments,
        "gate_summary": {
            "contract_gate": gate_summary,
            "sync_gate": gate == "PASS",
            "contract_vs_empirical_gate": gate,
            "blocked_gate_issue_count": len(gate_blockers),
        },
        "verdict": "PASS" if not blocked_claims and gate == "PASS" else "BLOCKED",
        "work_orders": work_orders,
        "work_order_total": len(work_orders),
        "work_order_policy": (
            "Every missing evidence surface produces an explicit capability work order; claims are never silently narrowed from PROMOTED."
        ),
    }
    return payload


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OC Core 1.3.3 Strict Claim-Surface/Proof-Evidence Synchronizer",
        "",
        f"Verdict: `{report['verdict']}`",
        f"Target grand claims: `{report['target_claim_total']}`",
        f"Work orders: `{report['work_order_total']}`",
        "",
        "## Gate Summary",
        "",
        f"- Contract gate: `{report['gate_summary']['sync_gate']}`",
        f"- Contract verdict: `{report['gate_summary']['contract_gate'].get('contract_verdict', '')}`",
        f"- Empirical support allowed: `{report['gate_summary']['contract_gate'].get('grand_toe_support_allowed', False)}`",
        "",
        "## Target Claim Assessments",
        "",
    ]
    if not report["claim_assessments"]:
        lines.append("- No promoted TOE/all-domain/numeric-superiority/irrefutable candidate claims were detected.")
    else:
        lines.extend(
            [
                "| Claim | Status | Missing Issues |",
                "| --- | --- | --- |",
            ]
        )
        for row in report["claim_assessments"]:
            lines.append(
                "| `{claim_id}` | `{status}` | `{issues}` |".format(
                    claim_id=row["claim_id"],
                    status=row["status"],
                    issues=", ".join(row["missing_issues"]) or "none",
                )
            )
    lines.extend(
        [
            "",
            "## Work Orders",
            "",
        ]
    )
    if not report["work_orders"]:
        lines.append("- none")
    for row in report["work_orders"]:
        lines.append(
            "- `{work_order_id}` `{owner_capability}` for `{claim_id}`: {required_action}".format(
                work_order_id=row["work_order_id"],
                owner_capability=row["owner_capability"],
                claim_id=row["claim_id"],
                required_action=row["required_action"],
            )
        )
        lines.append(f"  - Before: {row['before_predicate']}")
        lines.append(f"  - After: {row['after_predicate']}")
    return "\n".join(lines) + "\n"


def build_all(root: Path | None = None) -> dict[str, dict[str, Any]]:
    report = build_claim_evidence_sync_report(root)
    return {
        SYNC_REPORT_JSON_REL: report,
        SYNC_REPORT_MD_REL: {"text": render_markdown(report)},
    }


def write_outputs(root: Path | None = None) -> None:
    root = root or repo_root()
    payloads = build_all(root)
    for rel, payload in payloads.items():
        path = root / rel
        if rel.endswith(".md"):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(payload["text"], encoding="utf-8", newline="\n")
        else:
            write_json(path, payload)


def check_stored(root: Path | None = None) -> list[str]:
    root = root or repo_root()
    expected = build_all(root)
    errors: list[str] = []
    for rel, payload in expected.items():
        path = root / rel
        if rel.endswith(".md"):
            actual = path.read_text(encoding="utf-8") if path.exists() else ""
            if actual != payload["text"]:
                errors.append(f"{rel} is not synchronized with {FACTORY_REF}")
            continue
        actual = read_json(path)
        if actual != payload:
            errors.append(f"{rel} is not synchronized with {FACTORY_REF}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Build/check the strict claim evidence synchronizer.")
    parser.add_argument("--write", action="store_true", help="Write the strict claim synchronizer report.")
    parser.add_argument("--check", action="store_true", help="Check the stored synchronizer reports against deterministic output.")
    args = parser.parse_args()

    root = repo_root()
    if args.write:
        write_outputs(root)
        payload = build_claim_evidence_sync_report(root)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        if payload["verdict"] == "PASS":
            return 0
        return 1
    if args.check:
        errors = check_stored(root)
        if errors:
            for error in errors:
                print(f"ERROR: {error}")
            return 1
        print("oc133 strict claim-evidence synchronizer check passed")
        return 0

    payload = build_claim_evidence_sync_report(root)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
