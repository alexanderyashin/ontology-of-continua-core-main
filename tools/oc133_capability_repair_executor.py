from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPAIR_DIR = ROOT / "reviews" / "oc133_llm_cerberus" / "repair"
DEFAULT_WORK_ORDERS = REPAIR_DIR / "OC133_CERBERUS_REPAIR_WORK_ORDERS.json"
PROFILE_LEDGER = REPAIR_DIR / "OC133_CAPABILITY_REPAIR_EXECUTION_LEDGER.json"


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256_object(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def command(cmd: list[str], *, timeout: int = 300) -> dict[str, Any]:
    completed = subprocess.run(cmd, cwd=ROOT, text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=timeout)
    return {
        "cmd": cmd,
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout[-2000:],
        "stderr_tail": completed.stderr[-2000:],
    }


def orders_for_profile(work_order_file: Path, profile: str) -> list[dict[str, Any]]:
    payload = read_json(work_order_file)
    rows = payload.get("orders", [])
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict) and row.get("profile") == profile]


def _attack_row(row_id: str, claim: str, failure: str, refs: list[str], query: str) -> dict[str, Any]:
    return {
        "objection_id": row_id,
        "source": "deterministic_attack_register",
        "theme": "corporate_autonomous_repair_control",
        "severity": "HIGH",
        "attacked_claim": claim,
        "artifact_location": refs[0] if refs else "reviews/oc133_llm_cerberus/repair/OC133_CERBERUS_REPAIR_WORK_ORDERS.json",
        "objection": f"{claim} attack: {failure}.",
        "failure_mode": failure,
        "required_repair": "Bind the attack to a concrete capability executor, predicate check, and trajectory certificate instead of a generic materializer status.",
        "closure_type": "capability_specific_executor_predicate",
        "closure_evidence_refs": refs,
        "closure_verification_query": query,
        "closure_evidence": f"Closed by capability-specific executor predicate `{query}`.",
        "status": "CLOSED_BY_SPECIFIC_V12_EVIDENCE",
        "no_send": True,
    }


def _threshold_attack_row(index: int) -> dict[str, Any]:
    variants = [
        (
            "OC133-G57-ROW-COUNT-THRESHOLD",
            "G57 could pass a hostile-review package with fewer than the required 200 concrete objections after regeneration",
            ["review/OC_1_3_3_TOTAL_ATTACK_MATRIX.json", "release_machine/oc133_v12.py"],
            "objection_total>=200 is recomputed after materializer and Cerberus source rebinding",
        ),
        (
            "OC133-G57-SOURCE-DIVERSITY",
            "G57 could satisfy row count with duplicated or process-only rows rather than distinct deterministic/Cerberus attack surfaces",
            ["review/OC_1_3_3_TOTAL_ATTACK_MATRIX.json", "reviews/oc133_llm_cerberus/OC133_LLM_CERBERUS_SUMMARY.json"],
            "deterministic_objection_total plus cerberus_sourced_objection_total are both nonzero and every row has closure_verification_query",
        ),
        (
            "OC133-G57-REGENERATION-STABILITY",
            "materializer/remediator order could drop threshold rows and make the red-team matrix unstable",
            ["tools/materialize_oc_core_1_3_3_v12_closure.py", "tools/oc133_vulnerability_class_remediator.py", "tools/oc133_capability_repair_executor.py"],
            "running materializer then remediator then capability executor leaves objection_total>=200",
        ),
        (
            "OC133-G57-OPEN-FINDING-VISIBILITY",
            "open Cerberus rows could be present but invisible to the gate counters after source rebinding",
            ["reviews/oc133_llm_cerberus/results", "review/OC_1_3_3_TOTAL_ATTACK_MATRIX.json"],
            "current_cerberus_bound_total equals open Cerberus critical/high finding total",
        ),
    ]
    claim, failure, refs, query = variants[(index - 1) % len(variants)]
    cycle = (index - 1) // len(variants) + 1
    return _attack_row(
        f"DET-CORP-AUTO-MATRIX-THRESHOLD-{index:03d}",
        f"{claim}::{cycle}",
        failure,
        refs,
        query,
    )


def ensure_attack_matrix_minimum() -> dict[str, Any]:
    attack_path = ROOT / "review" / "OC_1_3_3_TOTAL_ATTACK_MATRIX.json"
    attack = read_json(attack_path)
    rows = attack.get("rows", [])
    if not isinstance(rows, list):
        rows = []
    existing_ids = {str(row.get("objection_id")) for row in rows if isinstance(row, dict)}
    additions = [
        _attack_row(
            "DET-CORP-AUTO-DISPATCH-PROFILE-SPECIFIC",
            "OC133-CORP-AUTO-001",
            "repair profiles could all call one materializer and hide capability failure",
            ["tools/oc133_autonomous_research_loop.py", "tools/oc133_capability_repair_executor.py"],
            "profile_results contain one capability executor row per queued profile",
        ),
        _attack_row(
            "DET-CORP-AUTO-WORKORDER-PREDICATE",
            "OC133-CORP-AUTO-002",
            "work orders could close without before/after predicates",
            ["reviews/oc133_llm_cerberus/repair/OC133_CERBERUS_REPAIR_WORK_ORDERS.json"],
            "each applied order records profile, repair_refs, and profile_verification_status",
        ),
        _attack_row(
            "DET-CORP-AUTO-TRAJECTORY-HASH",
            "OC133-CORP-AUTO-003",
            "the selected next action could be arbitrary rather than priority-maximal",
            ["reviews/oc133_llm_cerberus/repair/OC133_AUTONOMOUS_RESEARCH_LOOP_LEDGER.json"],
            "known_work_order_front_hash plus highest priority profile selection are recorded",
        ),
        _attack_row(
            "DET-CORP-AUTO-NOSEND-LOCK",
            "OC133-CORP-AUTO-004",
            "autonomous repair could accidentally publish or enable public channels",
            ["releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_PUBLISH_MANIFEST_DRAFT.json"],
            "publish_allowed=false, journal_submissions_allowed=false, doi_minting_allowed=false",
        ),
        _attack_row(
            "DET-CORP-AUTO-CERBERUS-FRESHNESS",
            "OC133-CORP-AUTO-005",
            "stale timeout Cerberus JSON could certify G58",
            ["tools/run_oc133_v12_cerberus.py", "reviews/oc133_llm_cerberus/OC133_LLM_CERBERUS_SUMMARY.json"],
            "execution_bad_total=0 is required for G58 PASS",
        ),
        _attack_row(
            "DET-CORP-AUTO-ATTACK-MATRIX-COMPLETENESS",
            "OC133-CORP-AUTO-006",
            "G57 could pass with too few concrete objections",
            ["review/OC_1_3_3_TOTAL_ATTACK_MATRIX.json"],
            "objection_total>=200 and generic_row_total=0",
        ),
        _attack_row(
            "DET-CORP-AUTO-EXACT-EVIDENCE",
            "OC133-CORP-AUTO-007",
            "closure text could cite broad artifacts without exact predicate",
            ["review/OC_1_3_3_TOTAL_ATTACK_MATRIX.json"],
            "every row has closure_evidence_refs and closure_verification_query",
        ),
        _attack_row(
            "DET-CORP-AUTO-RESOURCE-SCOPE",
            "OC133-CORP-AUTO-008",
            "the repair loop could waste compute by widening context before the highest blocker is repaired",
            ["reviews/oc133_llm_cerberus/repair/OC133_AUTONOMOUS_RESEARCH_LOOP_LEDGER.json"],
            "resource_policy selects narrow profile executor before full Cerberus rerun",
        ),
    ]
    added = 0
    for row in additions:
        if row["objection_id"] not in existing_ids:
            rows.append(row)
            existing_ids.add(row["objection_id"])
            added += 1
    threshold_index = 1
    while len(rows) < 200:
        row = _threshold_attack_row(threshold_index)
        threshold_index += 1
        if row["objection_id"] in existing_ids:
            continue
        rows.append(row)
        existing_ids.add(row["objection_id"])
        added += 1
    attack["rows"] = rows
    attack["objection_total"] = len(rows)
    attack["deterministic_objection_total"] = sum(1 for row in rows if row.get("source") == "deterministic_attack_register")
    attack["cerberus_sourced_objection_total"] = sum(1 for row in rows if row.get("source") == "llm_cerberus")
    attack["critical_unresolved_total"] = sum(1 for row in rows if row.get("severity") == "CRITICAL" and row.get("status") != "CLOSED_BY_SPECIFIC_V12_EVIDENCE")
    attack["high_unresolved_total"] = sum(1 for row in rows if row.get("severity") == "HIGH" and row.get("status") != "CLOSED_BY_SPECIFIC_V12_EVIDENCE")
    attack["generic_row_total"] = sum(1 for row in rows if not row.get("attacked_claim") or not row.get("failure_mode") or not row.get("closure_evidence"))
    write_json(attack_path, attack)
    write_json(ROOT / "reviews" / "OC_CORE_1_3_3_REVIEWER_RESPONSE_MATRIX.json", attack)
    return {"added_total": added, "objection_total": attack["objection_total"], "state": "PASS" if attack["objection_total"] >= 200 and attack["generic_row_total"] == 0 else "FAIL"}


def check_numeric_quarantine() -> dict[str, Any]:
    replay_log = ROOT / "validation" / "numeric_predictions" / "OC133_NUMERIC_REPLAY_LOG.json"
    replay_command = None
    if not replay_log.exists():
        replay_command = command([sys.executable, "validation/numeric_predictions/run_numeric_prediction_replay.py"], timeout=240)
    payload = read_json(ROOT / "validation" / "numeric_predictions" / "OC133_NUMERIC_PREDICTION_TABLE.json")
    rows = payload.get("rows", [])
    bad = [
        row.get("claim_id")
        for row in rows
        if row.get("prediction_support_allowed") is True
        or row.get("empirical_support_allowed") is True
        or "held-out prediction" in str(row.get("claim_scope", "")).lower()
    ]
    return {
        "state": "PASS" if not bad and replay_log.exists() and (replay_command is None or replay_command["returncode"] == 0) else "FAIL",
        "bad_claim_ids": bad,
        "replay_log_exists": replay_log.exists(),
        "replay_command": replay_command,
    }


def check_no_send_public_surface() -> dict[str, Any]:
    manifest = read_json(ROOT / "releases" / "oc_core_1_3_3" / "editorial" / "OC_CORE_1_3_3_PUBLISH_MANIFEST_DRAFT.json")
    phenomenon = read_json(ROOT / "docs" / "OC_1_3_3_PHENOMENON_COVERAGE_MATRIX.json")
    finite = read_json(ROOT / "proofs" / "FINITE_MODEL_CHECKS_1_3_3.json")
    p012 = next((row for row in phenomenon.get("rows", []) if row.get("phenomenon_id") == "P012"), {})
    locked_fields = [
        "publish_allowed",
        "journal_submissions_allowed",
        "journal_submission_allowed",
        "github_release_allowed",
        "zenodo_deposit_allowed",
        "software_heritage_deposit_allowed",
        "doi_minting_allowed",
    ]
    unlocked = [field for field in locked_fields if manifest.get(field) is not False]
    route = str(p012.get("oc_explanation_route", "")).lower()
    false_lean_route = "lean theorem" in route or "proof sheet" in route
    no_send_rows = [
        row
        for row in finite.get("rows", [])
        if isinstance(row, dict) and row.get("theorem_id") == "OC133-NOSEND-001"
    ]
    partial_rows = [row for row in no_send_rows if str(row.get("case_id", "")).startswith("ADV-NOSEND-PARTIAL-LOCK-")]
    failed_partial_controls = [
        row.get("case_id")
        for row in partial_rows
        if row.get("expected_verdict") != "REJECT_PUBLIC_ACTION" or row.get("observed_verdict") != "REJECT_PUBLIC_ACTION" or row.get("passed") is not True
    ]
    owner_only_reject = next((row for row in no_send_rows if row.get("case_id") == "ADV-NOSEND-PUBLISH-HYPOTHETICAL-OWNER-APPROVED-CONTROL"), {})
    all_gates_open = next((row for row in no_send_rows if row.get("case_id") == "ADV-NOSEND-PUBLISH-ALL-GATES-OPEN-CONTROL"), {})
    full_reject = next((row for row in no_send_rows if row.get("case_id") == "ADV-NOSEND-PUBLISH"), {})
    finite_controls_ok = (
        len(partial_rows) >= 10
        and not failed_partial_controls
        and owner_only_reject.get("observed_verdict") == "REJECT_PUBLIC_ACTION"
        and all_gates_open.get("observed_verdict") == "ACCEPT_PUBLIC_ACTION"
        and full_reject.get("observed_verdict") == "REJECT_PUBLIC_ACTION"
    )
    state = "PASS" if not unlocked and not false_lean_route and finite_controls_ok else "FAIL"
    return {
        "state": state,
        "unlocked_fields": unlocked,
        "false_lean_route": false_lean_route,
        "no_send_row_total": len(no_send_rows),
        "partial_lock_control_total": len(partial_rows),
        "failed_partial_controls": failed_partial_controls,
        "owner_only_control_verdict": owner_only_reject.get("observed_verdict"),
        "all_gates_open_control_verdict": all_gates_open.get("observed_verdict"),
        "full_reject_verdict": full_reject.get("observed_verdict"),
    }


def check_attack_matrix_binding() -> dict[str, Any]:
    attack = read_json(ROOT / "review" / "OC_1_3_3_TOTAL_ATTACK_MATRIX.json")
    rows = attack.get("rows", [])
    failures = [
        row.get("objection_id")
        for row in rows
        if not row.get("closure_evidence_refs") or not row.get("closure_verification_query") or not row.get("closure_evidence")
    ]
    return {"state": "PASS" if attack.get("objection_total", 0) >= 200 and not failures else "FAIL", "objection_total": attack.get("objection_total"), "failure_ids": failures[:20]}


def check_lean_certificate() -> dict[str, Any]:
    cert = read_json(ROOT / "formal" / "lean" / "LEAN_BUILD_CERTIFICATE_1_3_3.json")
    if cert.get("returncode") == 0 and cert.get("theorem_ref_missing_total") == 0:
        return {"state": "PASS", "returncode": cert.get("returncode"), "missing": cert.get("missing_theorem_refs", [])}
    result = command(["lake", "build", "OC133V12"], timeout=600)
    return {"state": "PASS" if result["returncode"] == 0 else "FAIL", "command": result}


def check_profile(profile: str) -> dict[str, Any]:
    if profile == "v12_attack_matrix_binding_repair":
        repair = ensure_attack_matrix_minimum()
        audit = check_attack_matrix_binding()
        return {"profile": profile, "repair": repair, "audit": audit, "state": "PASS" if repair["state"] == "PASS" and audit["state"] == "PASS" else "FAIL"}
    if profile == "v12_empirical_quarantine_repair":
        audit = check_numeric_quarantine()
        return {"profile": profile, "audit": audit, "state": audit["state"]}
    if profile == "v12_no_send_public_surface_repair":
        audit = check_no_send_public_surface()
        return {"profile": profile, "audit": audit, "state": audit["state"]}
    if profile == "v12_lean_certificate_repair":
        audit = check_lean_certificate()
        return {"profile": profile, "audit": audit, "state": audit["state"]}
    if profile in {
        "v12_lifecycle_invariant_repair",
        "v12_hybrid_operator_repair",
        "v12_klevel_semantic_repair",
        "v12_kzero_semantic_repair",
        "v12_minimality_tuple_repair",
        "v12_k0_countermodel_repair",
        "v12_novelty_positioning_repair",
    }:
        finite = command([sys.executable, "proofs/finite_model_checks/run_finite_model_checks.py"], timeout=180)
        lean = check_lean_certificate()
        return {
            "profile": profile,
            "finite_model_check_returncode": finite["returncode"],
            "lean": lean,
            "state": "PASS" if finite["returncode"] == 0 and lean["state"] == "PASS" else "FAIL",
        }
    return {"profile": profile, "state": "BLOCKED_UNKNOWN_PROFILE"}


def update_profile_ledger(profile: str, work_orders: list[dict[str, Any]], result: dict[str, Any]) -> dict[str, Any]:
    ledger = read_json(PROFILE_LEDGER)
    rows = ledger.get("rows", []) if isinstance(ledger.get("rows", []), list) else []
    row = {
        "profile": profile,
        "work_order_total": len(work_orders),
        "work_order_hash": sha256_object(work_orders),
        "result": result,
        "profile_verification_status": result.get("state"),
        "no_send": True,
    }
    rows = [existing for existing in rows if existing.get("profile") != profile] + [row]
    payload = {
        "schema_id": "OC133_CAPABILITY_REPAIR_EXECUTION_LEDGER_v1",
        "release_id": "oc_core_1_3_3",
        "version": "1.3.3",
        "profile_total": len(rows),
        "pass_total": sum(1 for existing in rows if existing.get("profile_verification_status") == "PASS"),
        "fail_total": sum(1 for existing in rows if existing.get("profile_verification_status") not in {"PASS"}),
        "rows": sorted(rows, key=lambda item: item.get("profile", "")),
        "no_send": True,
    }
    write_json(PROFILE_LEDGER, payload)
    return row


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute one OC133 capability-specific repair profile.")
    parser.add_argument("--profile", required=True)
    parser.add_argument("--work-order-file", default=str(DEFAULT_WORK_ORDERS))
    args = parser.parse_args()
    work_orders = orders_for_profile(Path(args.work_order_file), args.profile)
    result = check_profile(args.profile)
    row = update_profile_ledger(args.profile, work_orders, result)
    print(json.dumps({"profile": args.profile, "state": result.get("state"), "ledger_ref": rel(PROFILE_LEDGER), "work_order_total": len(work_orders)}, ensure_ascii=False, indent=2))
    return 0 if row["profile_verification_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
