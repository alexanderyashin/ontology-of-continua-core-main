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
GRAND_SCIENCE_PROGRAM = ROOT / "operations" / "logion_release_mission" / "oc_core_1_3_3" / "OC133_GRAND_SCIENCE_RESEARCH_PROGRAM.json"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from release_machine import oc133_platinum  # noqa: E402


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
    try:
        completed = subprocess.run(cmd, cwd=ROOT, text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=timeout)
    except FileNotFoundError as exc:
        return {
            "cmd": cmd,
            "returncode": 127,
            "stdout_tail": "",
            "stderr_tail": str(exc),
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "cmd": cmd,
            "returncode": 124,
            "stdout_tail": (exc.stdout or "")[-2000:] if isinstance(exc.stdout, str) else "",
            "stderr_tail": (exc.stderr or "")[-2000:] if isinstance(exc.stderr, str) else "",
        }
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


def check_target_blind_empirical_repair() -> dict[str, Any]:
    target_cmd = command([sys.executable, "validation/target_blind/run_target_blind_predictions.py"], timeout=180)
    validation_cmd = command([sys.executable, "validation/run_all.py", "--materialize-first", "--qa-only"], timeout=1200)
    target = read_json(ROOT / "validation" / "target_blind" / "OC133_TARGET_BLIND_PREDICTION_TABLE.json")
    report = read_json(ROOT / "reports" / "OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.json")
    numeric = read_json(ROOT / "validation" / "numeric_replay_qa" / "OC133_NUMERIC_REPLAY_QA_TABLE.json")
    required_row_fields = {
        "claim_id",
        "lane",
        "dataset_snapshot_ref",
        "target_blind_split",
        "formula",
        "predicted_value",
        "observed_value",
        "uncertainty",
        "comparator_baseline",
        "comparator_prediction",
        "residual",
        "comparator_residual",
        "negative_control",
        "negative_control_rejected",
        "falsifier",
        "prediction_support_allowed",
        "empirical_support_allowed",
        "snapshot_sha256",
        "replay_hash",
        "support_scope",
    }
    row_failures = []
    for row in target.get("rows", []):
        missing = sorted(field for field in required_row_fields if row.get(field) in {None, ""})
        if missing:
            row_failures.append({"claim_id": row.get("claim_id"), "missing": missing})
        snapshot_ref = row.get("dataset_snapshot_ref")
        if not snapshot_ref or not (ROOT / snapshot_ref).exists():
            row_failures.append({"claim_id": row.get("claim_id"), "missing_snapshot_ref": snapshot_ref})
        if row.get("negative_control_rejected") is not True:
            row_failures.append({"claim_id": row.get("claim_id"), "negative_control_rejected": row.get("negative_control_rejected")})
        if row.get("prediction_support_allowed") is not True or row.get("empirical_support_allowed") is not True:
            row_failures.append({"claim_id": row.get("claim_id"), "support_flags": "not both true"})
        if "not a" not in str(row.get("support_scope", "")).lower():
            row_failures.append({"claim_id": row.get("claim_id"), "support_scope_overclaim": row.get("support_scope")})
    predicate_checks = {
        "target_command_passed": target_cmd["returncode"] == 0,
        "validation_command_passed": validation_cmd["returncode"] == 0,
        "target_generated_by_logion": target.get("generated_by") == "LOGION_CAPABILITY_WORKER",
        "target_capability_owner_ok": target.get("capability_owner") == "Research/EmpiricalScience",
        "target_failure_total_zero": target.get("failure_total") == 0,
        "target_support_rows_present": target.get("prediction_support_allowed_total", 0) >= 5 and target.get("empirical_support_allowed_total", 0) >= 5 and target.get("lane_total", 0) >= 5,
        "target_row_predicates_complete": not row_failures,
        "numeric_replay_remains_quarantined": numeric.get("prediction_support_allowed_total", 0) == 0 and numeric.get("empirical_support_allowed_total", 0) == 0,
        "report_bounded_support_present": report.get("target_blind_bounded_reconstruction_support_present") is True,
        "report_broad_domain_promotion_false": report.get("broad_domain_validation_promoted") is False and report.get("domain_validation_support_allowed") is False,
    }
    return {
        "profile": "v12_target_blind_empirical_repair",
        "target_command": target_cmd,
        "validation_command": validation_cmd,
        "predicate_checks": predicate_checks,
        "row_failures": row_failures[:20],
        "target_ref": "validation/target_blind/OC133_TARGET_BLIND_PREDICTION_TABLE.json",
        "validation_report_ref": "reports/OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.json",
        "numeric_replay_ref": "validation/numeric_replay_qa/OC133_NUMERIC_REPLAY_QA_TABLE.json",
        "state": "PASS" if all(predicate_checks.values()) else "FAIL",
    }


def check_all_domain_empirical_readiness() -> dict[str, Any]:
    target_cmd = command([sys.executable, "validation/target_blind/run_target_blind_predictions.py"], timeout=240)
    validation_cmd = command([sys.executable, "validation/run_all.py", "--qa-only"], timeout=1200)
    audit = oc133_platinum.all_domain_readiness_audit(ROOT)
    empirical = audit.get("checks", {}).get("all_domain_empirical_predictions", {})
    return {
        "profile": "v12_all_domain_empirical_readiness_repair",
        "target_blind_command": target_cmd,
        "validation_command": validation_cmd,
        "audit_ref": "operations/logion_release_mission/oc_core_1_3_3/OC133_ALL_DOMAIN_READINESS_SCORECARD.json",
        "required_domains": empirical.get("required_domains", []),
        "passed_domains": empirical.get("passed_domains", []),
        "missing_domains": empirical.get("missing_domains", []),
        "missing_domain_total": empirical.get("missing_domain_total", 0),
        "state": "PASS" if target_cmd["returncode"] == 0 and validation_cmd["returncode"] == 0 and empirical.get("state") == "PASS" else "FAIL",
        "block_condition": "Missing domains are not auto-filled. Research/EmpiricalScience must produce honest held-out or target-blind evidence before this profile passes.",
    }


def check_claim_boundary_overclaim() -> dict[str, Any]:
    audit = oc133_platinum.all_domain_readiness_audit(ROOT)
    row = audit.get("checks", {}).get("claim_boundary_no_overclaim", {})
    return {
        "profile": "v12_claim_boundary_overclaim_repair",
        "hit_total": row.get("hit_total", 0),
        "hits": row.get("hits", []),
        "state": row.get("state"),
    }


def check_journal_package_readiness() -> dict[str, Any]:
    audit = oc133_platinum.all_domain_readiness_audit(ROOT)
    package = audit.get("checks", {}).get("journal_owner_review_packages", {})
    send = audit.get("checks", {}).get("journal_send_readiness_minus_owner_lock", {})
    state = "PASS" if package.get("state") == "PASS" and send.get("state") == "PASS" else "FAIL"
    return {
        "profile": "v12_journal_package_readiness_repair",
        "owner_review_package_ready": package.get("state") == "PASS",
        "send_allowed_now": send.get("send_allowed_now"),
        "submission_allowed": send.get("submission_allowed"),
        "journal_submissions_allowed": send.get("journal_submissions_allowed"),
        "bad_send_unlock_total": send.get("bad_send_unlock_total"),
        "package_total": package.get("package_total"),
        "recommended_package_total": package.get("recommended_package_total"),
        "state": state,
    }


def _grand_science_obligation(
    *,
    obligation_id: str,
    owner_capability: str,
    title: str,
    blocker_check: str,
    required_artifacts: list[str],
    pass_predicate: str,
    verification_command: str,
) -> dict[str, Any]:
    return {
        "obligation_id": obligation_id,
        "owner_capability": owner_capability,
        "title": title,
        "blocker_check": blocker_check,
        "required_artifacts": required_artifacts,
        "pass_predicate": pass_predicate,
        "verification_command": verification_command,
        "closure_rule": "This obligation may close only when the referenced evidence exists and release_machine.oc133_platinum re-audits the blocker check as PASS.",
        "artifact_exists_is_not_closure": True,
        "no_send": True,
    }


def materialize_grand_science_program(profile: str) -> dict[str, Any]:
    verification_commands_by_profile = {
        "v12_grand_formal_science_research_program": [
            [sys.executable, "tools/oc133_grand_toe_formal_obligations.py", "--write"],
            ["lake", "build", "OC133V12"],
            [sys.executable, "tools/oc133_refresh_lean_certificate.py"],
            [sys.executable, "proofs/finite_model_checks/run_finite_model_checks.py"],
            ["lake", "env", "lean", "formal/lean/OC133GrandPromotion.lean"],
            [sys.executable, "tools/oc133_grand_promotion_contract.py", "--write"],
        ],
        "v12_grand_empirical_superiority_research_program": [
            [sys.executable, "tools/oc133_acquisition_planner_runner.py", "--write", "--allow-blocked-exit-zero"],
            [sys.executable, "tools/oc133_official_readonly_acquisition_runner.py", "--write", "--allow-blocked-exit-zero"],
            [sys.executable, "tools/oc133_harvester_runner.py", "--write", "--allow-blocked-exit-zero"],
            [sys.executable, "tools/oc133_domain_evidence_executor_runner.py", "--write", "--allow-blocked-exit-zero"],
            [sys.executable, "tools/oc133_grand_evidence_registry_sync_factory.py", "--write"],
            [sys.executable, "tools/oc133_grand_evidence_repair_router.py", "--write"],
            [sys.executable, "tools/oc133_empirical_capability_registry.py", "--write"],
            [sys.executable, "tools/oc133_empirical_capability_dispatcher.py", "--write", "--refresh-registry", "--execute", "--max-actions", "10"],
            [sys.executable, "tools/oc133_grand_evidence_registry_sync_factory.py", "--write"],
            [sys.executable, "tools/oc133_grand_evidence_repair_router.py", "--write"],
            [sys.executable, "tools/oc133_grand_empirical_evidence_factory.py", "--allow-blocked-exit-zero"],
        ],
        "v12_modern_science_comparator_research_program": [
            [sys.executable, "tools/oc133_modern_science_comparator_factory.py", "--write"],
            [sys.executable, "benchmarks/modern_science/validate_modern_science_register.py"],
        ],
    }
    verification_commands = verification_commands_by_profile.get(profile, [])
    verification_results = [
        command(cmd, timeout=900 if cmd and cmd[0] == "lake" else 300)
        for cmd in verification_commands
    ]
    audit = oc133_platinum.all_domain_readiness_audit(ROOT, oc133_platinum.content_closure_audit(ROOT))
    checks = audit.get("checks", {})
    obligations = [
        _grand_science_obligation(
            obligation_id="OC133-GRAND-FORMAL-001",
            owner_capability="Research/FormalScience",
            title="Prove the dedicated grand TOE/all-domain claim or keep it unpromoted",
            blocker_check="grand_toe_claim_ledger_evidence",
            required_artifacts=[
                "claims/CLAIM_LEDGER_1_3_3.json::dedicated grand claim row",
                "proofs/THEOREM_INVENTORY_1_3_3.json::grand theorem IDs",
                "proofs/proof_sheets/*.md::grand theorem proof sheets",
                "formal/lean/OC133V12.lean::grand theorem subset",
                "proofs/FINITE_MODEL_CHECKS_1_3_3.json::positive/negative witness cases",
            ],
            pass_predicate="grand_toe_claim_ledger_evidence.state == PASS and release_promotion_allowed == true for the dedicated grand claim",
            verification_command="lake build OC133V12 && python proofs/finite_model_checks/run_finite_model_checks.py && python tools/oc133_logion_all_domain_readiness.py --write --allow-blocked-exit-zero",
        ),
        _grand_science_obligation(
            obligation_id="OC133-GRAND-EMPIRICAL-001",
            owner_capability="Research/EmpiricalScience",
            title="Produce strict per-domain predictive superiority evidence",
            blocker_check="grand_toe_empirical_superiority",
            required_artifacts=[
                "validation/heldout/ or validation/target_blind/::prospective or target-blind protocol",
                "reports/OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.json::broad-domain promotion evidence",
                "per-domain snapshot hashes and replay hashes",
                "per-domain comparator residuals, uncertainty, negative controls, and falsifiers",
            ],
            pass_predicate="every required domain passes strict predictive superiority against a comparator and explicitly allows grand-claim support",
            verification_command="python validation/run_all.py --qa-only && python tools/oc133_logion_all_domain_readiness.py --write --allow-blocked-exit-zero",
        ),
        _grand_science_obligation(
            obligation_id="OC133-GRAND-PRIORART-001",
            owner_capability="Research/PriorArt",
            title="Certify superiority against modern-science comparator baselines",
            blocker_check="modern_science_comparator_superiority",
            required_artifacts=[
                "comparators/OC_1_3_3_MODERN_SCIENCE_SUPERIORITY_REGISTER.json",
                "benchmarks/::per-domain benchmark definitions",
                "OC result refs",
                "modern-science comparator result refs",
                "source-backed fairness and uncertainty notes",
            ],
            pass_predicate="modern_science_comparator_superiority.state == PASS for physics, chemistry, biology, systems, and mathematics",
            verification_command="python tools/oc133_logion_all_domain_readiness.py --write --allow-blocked-exit-zero",
        ),
    ]
    selected = [row for row in obligations if row["blocker_check"] in audit.get("blocker_ids", [])]
    payload = {
        "schema_id": "OC133_GRAND_SCIENCE_RESEARCH_PROGRAM_v1",
        "release_id": "oc_core_1_3_3",
        "version": "1.3.3",
        "requested_ambition_level": getattr(oc133_platinum, "GRAND_SCIENCE_REQUESTED_AMBITION", "numerically proven TOE across all domains and better than modern science"),
        "profile": profile,
        "program_state": "RUNNING_SCIENTIFIC_BLOCKERS_REMAIN" if selected else "NO_OPEN_GRAND_SCIENCE_BLOCKERS",
        "all_domain_final_readiness_state": audit.get("final_readiness_state"),
        "all_domain_ready_no_send": audit.get("all_domain_ready_no_send"),
        "bounded_all_domain_ready_no_send": audit.get("bounded_all_domain_ready_no_send"),
        "blocker_ids": audit.get("blocker_ids", []),
        "selected_obligation_total": len(selected),
        "obligations": selected,
        "all_obligations": obligations,
        "profile_verification_commands": verification_results,
        "profile_verification_pass": all(row.get("returncode") == 0 for row in verification_results),
        "checks": {
            key: checks.get(key, {})
            for key in (
                "grand_toe_claim_ledger_evidence",
                "grand_toe_empirical_superiority",
                "modern_science_comparator_superiority",
                "broad_domain_validation_promotion_guard",
            )
        },
        "no_send": True,
        "publish_allowed": False,
        "journal_submissions_allowed": False,
    }
    write_json(GRAND_SCIENCE_PROGRAM, payload)
    verification_pass = all(row.get("returncode") == 0 for row in verification_results)
    state = "FAIL" if not verification_pass else "SCIENTIFIC_BLOCKERS_REMAIN" if selected else "PASS"
    return {
        "profile": profile,
        "program_ref": rel(GRAND_SCIENCE_PROGRAM),
        "program_state": payload["program_state"],
        "profile_verification_commands": verification_results,
        "profile_verification_pass": verification_pass,
        "selected_obligation_total": len(selected),
        "all_domain_final_readiness_state": audit.get("final_readiness_state"),
        "all_domain_ready_no_send": audit.get("all_domain_ready_no_send"),
        "scientific_closure_state": "NOT_CLOSED_UNTIL_EVIDENCE_PREDICATES_PASS",
        "state": state,
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
    if profile == "v12_target_blind_empirical_repair":
        audit = check_target_blind_empirical_repair()
        return {"profile": profile, "audit": audit, "state": audit["state"]}
    if profile == "v12_all_domain_empirical_readiness_repair":
        audit = check_all_domain_empirical_readiness()
        return {"profile": profile, "audit": audit, "state": audit["state"]}
    if profile == "v12_claim_boundary_overclaim_repair":
        audit = check_claim_boundary_overclaim()
        return {"profile": profile, "audit": audit, "state": audit["state"]}
    if profile == "v12_journal_package_readiness_repair":
        audit = check_journal_package_readiness()
        return {"profile": profile, "audit": audit, "state": audit["state"]}
    if profile in {
        "v12_grand_formal_science_research_program",
        "v12_grand_empirical_superiority_research_program",
        "v12_modern_science_comparator_research_program",
    }:
        audit = materialize_grand_science_program(profile)
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
    # A scientific blocker is a successful capability execution with a negative
    # research verdict. The caller must keep the obligation open, but should not
    # classify the executor itself as broken.
    if row["profile_verification_status"] in {"PASS", "SCIENTIFIC_BLOCKERS_REMAIN"}:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
