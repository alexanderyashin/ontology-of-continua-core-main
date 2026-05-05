from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from oc_core_1_3_cerberus_lib import validate_existing_cerberus_bundle
from oc_core_1_3_science_spot_lib import (
    FINAL_TOE_PROJECTION_LANE_TARGETS,
    FINAL_TOE_PROJECTION_REQUIRED_ROW_FIELDS,
    REPO_ROOT,
    validate_existing_bundle,
)
from oc_core_release_assembly_lib import artifact_hash, stable_json, validation_result


RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
MISSION_DIR = Path("operations/logion_release_mission/oc_core_1_3_3")
FACTORY_DIR = MISSION_DIR / "toe_closure_factory"
OBLIGATIONS_NAME = "OC133_TOE_CLOSURE_OBLIGATIONS.json"
LANES_NAME = "OC133_TOE_LANE_RESULTS.json"
COCKPIT_NAME = "OC133_TOE_CLOSURE_COCKPIT.json"
COCKPIT_MD_NAME = "OC133_TOE_CLOSURE_COCKPIT.md"
REGISTRY_NAME = "OC133_TOE_LANE_CAPABILITY_REGISTRY.json"
STATE_NAME = "OC133_TOE_CLOSURE_STATE.json"

GRAND_SCORECARD = MISSION_DIR / "OC133_ALL_DOMAIN_READINESS_SCORECARD.json"
GRAND_LOOP_REPORT = MISSION_DIR / "OC133_GRAND_SCIENCE_LOOP_latest.json"
GRAND_PROMOTION_REPORT = Path("proofs/grand_promotion/OC133_GRAND_PROMOTION_CONTRACT_REPORT.json")
FINITE_CHECK_REPORT = Path("proofs/FINITE_MODEL_CHECKS_1_3_3.json")
COMPARATOR_REGISTER = Path("comparators/OC_1_3_3_MODERN_SCIENCE_SUPERIORITY_REGISTER.json")
CERBERUS_FINDINGS = Path("releases/oc_core_1_3/editorial/OC_CORE_1_3_CERBERUS_REVIEW_FINDINGS_latest.json")
CERBERUS_ACCEPTANCE = Path("releases/oc_core_1_3/editorial/OC_CORE_1_3_CERBERUS_ACCEPTANCE_CERT_latest.json")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def repo_path(root: Path, path: Path) -> Path:
    return root / path


def rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except Exception:
        return path.as_posix()


def current_validator_errors(root: Path) -> list[str]:
    parts = current_validator_error_parts(root)
    return parts["science_errors"] + parts["cerberus_errors"]


def current_validator_error_parts(root: Path) -> dict[str, list[str]]:
    """Return science and Cerberus failures separately so compute is routed cheaply."""
    return {
        "science_errors": validate_existing_bundle(root, require_final_toe_pass=True),
        "cerberus_errors": validate_existing_cerberus_bundle(root, require_clean=True),
    }


def science_errors(root: Path) -> list[str]:
    return current_validator_error_parts(root)["science_errors"]


def cerberus_errors(root: Path) -> list[str]:
    return current_validator_error_parts(root)["cerberus_errors"]


def error_classes(errors: list[str]) -> set[str]:
    return {classify_validator_error(error)[0] for error in errors}


def lane_registry_rows() -> list[dict[str, Any]]:
    return [
        {
            "lane_id": "AI",
            "finding_class": "AI_DOMAIN_TOE_PROJECTION_LANE",
            "owner_capability": "Research/AIProjection",
            "closure_condition": "AI projection lane has claim id, public scope, formal boundary, evidence/simulation refs, comparator refs, falsifiers, row PASS, lane PASS, and final TOE support allowed.",
            "required_artifacts": [
                "releases/oc_core_1_3/editorial/science_sources/toe_projection_lanes/ai.json",
                "AI-domain claim ledger or source-bound claim row",
                "AI formal-boundary/proof mapping",
                "AI benchmark/simulation evidence pack",
                "AI comparator and falsifier rows",
            ],
            "execution_command": [sys.executable, "tools/oc133_toe_closure_factory.py", "--execute-lane", "AI", "--write"],
            "validator_binding": "validate_final_toe_projection_lanes::AI",
            "pass_predicate": "AI lane closure_verdict == PASS and final_toe_support_allowed == true",
            "claim_effect": "AI remains a bounded projection until the dedicated lane passes.",
            "no_fake_closure_policy": "Future-research or demoted AI rows cannot count as TOE closure.",
        },
        {
            "lane_id": "ENTERPRISE_ARCHITECTURE",
            "finding_class": "ENTERPRISE_ARCHITECTURE_DOMAIN_TOE_PROJECTION_LANE",
            "owner_capability": "Research/EnterpriseArchitectureProjection",
            "closure_condition": "EA projection lane has claim id, public scope, operational evidence, architecture cases, comparator alternatives, falsifiers, row PASS, lane PASS, and final TOE support allowed.",
            "required_artifacts": [
                "releases/oc_core_1_3/editorial/science_sources/toe_projection_lanes/enterprise_architecture.json",
                "EA-domain claim ledger or source-bound claim row",
                "EA architecture case and operational-metric evidence pack",
                "EA comparator and falsifier rows",
            ],
            "execution_command": [sys.executable, "tools/oc133_toe_closure_factory.py", "--execute-lane", "ENTERPRISE_ARCHITECTURE", "--write"],
            "validator_binding": "validate_final_toe_projection_lanes::ENTERPRISE_ARCHITECTURE",
            "pass_predicate": "ENTERPRISE_ARCHITECTURE lane closure_verdict == PASS and final_toe_support_allowed == true",
            "claim_effect": "EA remains a bounded projection until the dedicated lane passes.",
            "no_fake_closure_policy": "Future-research or demoted EA rows cannot count as TOE closure.",
        },
        {
            "lane_id": "GRAND_TOE_CLAIM_LEDGER_EVIDENCE",
            "finding_class": "GRAND_TOE_CLAIM_LEDGER_EVIDENCE",
            "owner_capability": "Research/FormalScience",
            "closure_condition": "Grand TOE claim promotion contract passes with dedicated promoted claim row, Lean refs, finite refs, positive/negative finite controls, empirical pack, and comparator PASS.",
            "required_artifacts": [
                "claims/CLAIM_LEDGER_1_3_3.json::dedicated promoted grand claim row",
                "proofs/grand_promotion/OC133_GRAND_PROMOTION_CONTRACT_REPORT.json",
                "formal/lean/OC133V12.lean",
                "proofs/FINITE_MODEL_CHECKS_1_3_3.json",
            ],
            "execution_command": [sys.executable, "tools/oc133_capability_repair_executor.py", "--profile", "v12_grand_formal_science_research_program"],
            "validator_binding": "validate_final_toe_grand_science_scorecard::grand_toe_claim_ledger_evidence",
            "pass_predicate": "grand_toe_claim_ledger_evidence.state == PASS and grand promotion contract verdict == PASS",
            "claim_effect": "Grand TOE promotion remains blocked until formal, finite, empirical, and comparator dependencies all pass.",
            "no_fake_closure_policy": "A blocker proof, artifact existence, or demoted grand claim cannot count as TOE closure.",
        },
        {
            "lane_id": "MODERN_SCIENCE_COMPARATOR_SUPERIORITY",
            "finding_class": "MODERN_SCIENCE_COMPARATOR_SUPERIORITY",
            "owner_capability": "Research/PriorArt",
            "closure_condition": "Modern-science superiority passes only if broad coverage predicates and source-backed comparator baselines pass, not merely benchmark-scoped baselines.",
            "required_artifacts": [
                "comparators/OC_1_3_3_MODERN_SCIENCE_SUPERIORITY_REGISTER.json",
                "benchmarks/modern_science/OC133_MODERN_SCIENCE_BENCHMARK_LANES.json",
                "comparators/modern_science/OC133_MODERN_SCIENCE_COVERAGE_REGISTER.json",
                "benchmarks/modern_science/OC133_MODERN_SCIENCE_COVERAGE_WORK_ORDERS.json",
            ],
            "execution_command": [sys.executable, "tools/oc133_capability_repair_executor.py", "--profile", "v12_modern_science_comparator_research_program"],
            "validator_binding": "validate_final_toe_grand_science_scorecard::modern_science_comparator_superiority",
            "pass_predicate": "modern_science_comparator_superiority.state == PASS and broad modern-science coverage is certified",
            "claim_effect": "Broad superiority language remains blocked while only benchmark-scoped superiority is certified.",
            "no_fake_closure_policy": "Benchmark-scoped superiority cannot be upgraded to broad modern-science superiority.",
        },
        {
            "lane_id": "CERBERUS_RELEASE_REVIEW_GATE",
            "finding_class": "CERBERUS_RELEASE_REVIEW_GATE",
            "owner_capability": "Review/Cerberus",
            "closure_condition": "Cerberus targets/run/acceptance fingerprints bind to current HEAD, acceptance PASS, LLM gate PASS, and open defect findings zero.",
            "required_artifacts": [
                "releases/oc_core_1_3/editorial/OC_CORE_1_3_CERBERUS_ACCEPTANCE_CERT_latest.json",
                "releases/oc_core_1_3/editorial/OC_CORE_1_3_CERBERUS_REVIEW_FINDINGS_latest.json",
            ],
            "execution_command": [
                sys.executable,
                "tools/run_oc_core_1_3_cerberus_review.py",
                "--codex-model",
                "gpt-5.4-mini",
                "--llm-workers",
                "1",
                "--llm-batch-max-chars",
                "6000",
                "--llm-timeout-seconds",
                "300",
                "--build-mode",
                "full",
            ],
            "validator_binding": "validate_existing_cerberus_bundle(require_clean=True)",
            "pass_predicate": "Cerberus acceptance PASS, LLM gate PASS, and open defect findings == 0",
            "claim_effect": "No external reasoning spend while deterministic science blockers remain.",
            "no_fake_closure_policy": "Stale fingerprints or skipped LLM gate cannot count as clean Cerberus.",
        },
    ]


def build_lane_capability_registry(*, generated_at: str | None = None) -> dict[str, Any]:
    rows = lane_registry_rows()
    payload = {
        "schema_id": "OC133_TOE_LANE_CAPABILITY_REGISTRY_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": generated_at or utc_now(),
        "status": "PASS",
        "lane_total": len(rows),
        "rows": rows,
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def _legacy_current_validator_errors(root: Path) -> list[str]:
    errors = validate_existing_bundle(root, require_final_toe_pass=True)
    errors.extend(validate_existing_cerberus_bundle(root, require_clean=True))
    return errors


def classify_validator_error(error: str) -> tuple[str, str, str, str, str]:
    lowered = error.lower()
    if "ai lane" in lowered or "ai row" in lowered:
        return (
            "AI_DOMAIN_TOE_PROJECTION_LANE",
            "HIGH",
            "AI domain claim graph -> formal boundary -> benchmark/simulation evidence -> comparator/falsifier row",
            "AI projection has PASS rows with theorem/proof or finite witnesses, evidence/simulation anchors, comparator baselines, falsifiers, and final TOE support allowed.",
            "AI claims remain bounded application/research claims until the lane passes.",
        )
    if "enterprise_architecture" in lowered or "enterprise architecture" in lowered:
        return (
            "ENTERPRISE_ARCHITECTURE_DOMAIN_TOE_PROJECTION_LANE",
            "HIGH",
            "EA domain claim graph -> architecture cases -> operational metrics -> comparator/falsifier row",
            "EA projection has PASS rows with operational metrics, case anchors, comparator alternatives, falsifiers, and final TOE support allowed.",
            "EA claims remain bounded application/research claims until the lane passes.",
        )
    if "grand_toe_claim_ledger_evidence" in lowered:
        return (
            "GRAND_TOE_CLAIM_LEDGER_EVIDENCE",
            "CRITICAL",
            "grand claim ledger -> proof sheet -> Lean certificate -> finite cases -> evidence/comparator/falsifier bindings",
            "A promoted grand TOE claim row exists only if theorem/proof/Lean/finite/evidence/comparator dependencies are satisfied.",
            "Grand TOE promotion stays blocked; demoted/future-research rows do not count as closure.",
        )
    if "modern_science_comparator_superiority" in lowered:
        return (
            "MODERN_SCIENCE_COMPARATOR_SUPERIORITY",
            "CRITICAL",
            "source-backed comparator matrix -> domain benchmarks -> superiority verdict -> residual-delta boundary",
            "Modern-science superiority is PASS only when each required domain has source-backed benchmark rows and honest superiority certification.",
            "Superiority language is demoted unless the comparator lane passes.",
        )
    if "all_domain_ready_no_send" in lowered:
        return (
            "ALL_DOMAIN_READINESS_SCORECARD",
            "CRITICAL",
            "scorecard blockers -> lane closures -> final scorecard refresh",
            "All-domain readiness is true only after all final TOE checks pass and blocker_ids is empty.",
            "All-domain readiness remains false until the blockers are closed.",
        )
    if "cerberus" in lowered:
        return (
            "CERBERUS_RELEASE_REVIEW_GATE",
            "CRITICAL",
            "deterministic Cerberus blockers -> full Cerberus run -> clean acceptance certificate",
            "Cerberus acceptance is PASS, LLM gate is PASS, and open defect findings are zero.",
            "External reasoning is not spent while deterministic blockers remain.",
        )
    return (
        "TOE_VALIDATOR_BLOCKER",
        "CRITICAL",
        "canonical SPOT repair -> projection refresh -> final validator",
        "The exact validator error disappears without weakening gates.",
        "r017 remains blocked while this validator error exists.",
    )


def work_order_for_error(index: int, error: str) -> dict[str, Any]:
    finding_class, severity, route, closure, effect = classify_validator_error(error)
    return {
        "work_order_id": f"R017-TOE-CLOSURE-{index:03d}",
        "source_validator_message": error,
        "finding_class": finding_class,
        "severity": severity,
        "status": "OPEN",
        "blocks_r017": True,
        "research_route": route,
        "closure_condition": closure,
        "evidence_required": [
            "claim_id",
            "public_claim_scope",
            "theorem_or_formal_boundary_refs",
            "lean_refs",
            "finite_case_refs",
            "evidence_or_simulation_refs",
            "comparator_refs",
            "falsifier_refs",
            "closure_verdict",
        ],
        "execution_command": [
            sys.executable,
            "tools/oc133_toe_closure_factory.py",
            "--execute",
            "--write",
        ],
        "validator_binding": "tools/validate_oc_core_1_3_science_spot.py --require-final-toe-pass --require-cerberus-clean",
        "claim_effect": effect,
        "fake_closure_rejected": True,
    }


def active_lane_work_orders(start_index: int) -> list[dict[str, Any]]:
    rows = [
        (
            "AI",
            "AI_DOMAIN_TOE_PROJECTION_LANE",
            "AI projection must add source-grounded AI claims, formal boundaries, benchmark/simulation evidence, comparator baselines, and falsifiers.",
        ),
        (
            "ENTERPRISE_ARCHITECTURE",
            "ENTERPRISE_ARCHITECTURE_DOMAIN_TOE_PROJECTION_LANE",
            "EA projection must add source-grounded architecture claims, operational metrics, architecture cases, comparator alternatives, and falsifiers.",
        ),
    ]
    output: list[dict[str, Any]] = []
    for offset, (lane_id, finding_class, closure) in enumerate(rows):
        output.append(
            {
                "work_order_id": f"R017-TOE-LANE-{lane_id}-{start_index + offset:03d}",
                "source_validator_message": f"{lane_id} lane active closure obligation",
                "finding_class": finding_class,
                "severity": "HIGH",
                "status": "OPEN",
                "blocks_r017": True,
                "research_route": f"{lane_id} lane packetization -> proof/evidence/comparator/falsifier closure",
                "closure_condition": closure,
                "evidence_required": FINAL_TOE_PROJECTION_REQUIRED_ROW_FIELDS,
                "execution_command": [
                    sys.executable,
                    "tools/oc133_toe_closure_factory.py",
                    "--execute",
                    "--write",
                ],
                "validator_binding": "validate_final_toe_projection_lanes",
                "claim_effect": "Lane remains bounded and cannot support final TOE until PASS.",
                "fake_closure_rejected": True,
            }
        )
    return output


def build_obligations(root: Path, validator_errors: list[str], *, generated_at: str | None = None) -> dict[str, Any]:
    rows = [work_order_for_error(index + 1, error) for index, error in enumerate(validator_errors)]
    rows.extend(active_lane_work_orders(len(rows) + 1))
    payload = {
        "schema_id": "OC133_TOE_CLOSURE_OBLIGATIONS_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": generated_at or utc_now(),
        "status": "OPEN" if rows else "PASS",
        "validator_error_total": len(validator_errors),
        "work_order_total": len(rows),
        "open_work_order_total": len([row for row in rows if row["status"] == "OPEN"]),
        "r017_promotion_allowed": False if rows else True,
        "fake_closure_policy": "A demoted, future-research, blocked, or missing-evidence row cannot count as TOE closure.",
        "rows": rows,
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def ref_exists(root: Path, ref: str) -> bool:
    return bool(ref) and (root / ref).exists()


def evaluate_projection_lane(root: Path, lane_id: str, path: Path) -> dict[str, Any]:
    payload = read_json(root / path.relative_to(REPO_ROOT))
    rows = payload.get("rows", [])
    findings: list[str] = []
    if payload.get("closure_verdict") != "PASS":
        findings.append("lane closure_verdict is not PASS")
    if payload.get("final_toe_support_allowed") is not True:
        findings.append("lane final_toe_support_allowed is not true")
    if not isinstance(rows, list) or not rows:
        findings.append("lane has no projection rows")
        rows = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            findings.append(f"row {index} is not an object")
            continue
        for field in FINAL_TOE_PROJECTION_REQUIRED_ROW_FIELDS:
            if field not in row:
                findings.append(f"row {index} missing {field}")
        if row.get("closure_verdict") != "PASS":
            findings.append(f"row {index} closure_verdict is not PASS")
        for ref_field in [
            "theorem_or_formal_boundary_refs",
            "lean_refs",
            "finite_case_refs",
            "evidence_or_simulation_refs",
            "comparator_refs",
            "falsifier_refs",
        ]:
            value = row.get(ref_field, [])
            if not isinstance(value, list) or not value:
                findings.append(f"row {index} {ref_field} is empty or not a list")
                continue
            for ref in value:
                if not ref_exists(root, str(ref)):
                    findings.append(f"row {index} {ref_field} missing ref {ref}")
    return {
        "lane_id": lane_id,
        "lane_type": "domain_projection",
        "source_ref": rel(root, root / path.relative_to(REPO_ROOT)),
        "status": "PASS" if not findings else "FAIL",
        "closure_verdict": "PASS" if not findings else "FAIL_CLOSED",
        "final_toe_support_allowed": bool(payload.get("final_toe_support_allowed") is True and not findings),
        "row_total": len(rows),
        "finding_total": len(findings),
        "findings": findings[:50],
    }


def evaluate_grand_claim_lane(root: Path) -> dict[str, Any]:
    scorecard = read_json(root / GRAND_SCORECARD)
    promotion = read_json(root / GRAND_PROMOTION_REPORT)
    finite = read_json(root / FINITE_CHECK_REPORT)
    checks = scorecard.get("checks", {}) if isinstance(scorecard.get("checks"), dict) else {}
    check = checks.get("grand_toe_claim_ledger_evidence", {})
    findings: list[str] = []
    if check.get("state") != "PASS":
        findings.append("grand_toe_claim_ledger_evidence check is not PASS")
    if "grand_toe_claim_ledger_evidence" in (scorecard.get("blocker_ids") or []):
        findings.append("grand_toe_claim_ledger_evidence remains in blocker_ids")
    if promotion.get("verdict") != "PASS":
        findings.append(f"grand promotion contract verdict is {promotion.get('verdict') or 'missing'}")
    if int(finite.get("failure_total") or 0) > 0:
        findings.append(f"finite model checks have failure_total={finite.get('failure_total')}")
    return {
        "lane_id": "GRAND_TOE_CLAIM_LEDGER_EVIDENCE",
        "lane_type": "grand_claim_promotion",
        "status": "PASS" if not findings else "FAIL",
        "closure_verdict": "PASS" if not findings else "FAIL_CLOSED",
        "final_toe_support_allowed": not findings,
        "source_refs": [str(GRAND_SCORECARD), str(GRAND_PROMOTION_REPORT), str(FINITE_CHECK_REPORT)],
        "finding_total": len(findings),
        "findings": findings,
    }


def evaluate_comparator_lane(root: Path) -> dict[str, Any]:
    scorecard = read_json(root / GRAND_SCORECARD)
    register = read_json(root / COMPARATOR_REGISTER)
    checks = scorecard.get("checks", {}) if isinstance(scorecard.get("checks"), dict) else {}
    check = checks.get("modern_science_comparator_superiority", {})
    findings: list[str] = []
    if check.get("state") != "PASS":
        findings.append("modern_science_comparator_superiority check is not PASS")
    if "modern_science_comparator_superiority" in (scorecard.get("blocker_ids") or []):
        findings.append("modern_science_comparator_superiority remains in blocker_ids")
    register_text = json.dumps(register, ensure_ascii=False).lower()
    if "superiority" not in register_text or "comparator" not in register_text:
        findings.append("comparator register lacks superiority/comparator content")
    if "pass" not in str(check.get("state", "")).lower():
        findings.append("source-backed benchmark superiority is not certified")
    return {
        "lane_id": "MODERN_SCIENCE_COMPARATOR_SUPERIORITY",
        "lane_type": "comparator_superiority",
        "status": "PASS" if not findings else "FAIL",
        "closure_verdict": "PASS" if not findings else "FAIL_CLOSED",
        "final_toe_support_allowed": not findings,
        "source_refs": [str(GRAND_SCORECARD), str(COMPARATOR_REGISTER)],
        "finding_total": len(findings),
        "findings": findings,
    }


def evaluate_cerberus_lane(root: Path) -> dict[str, Any]:
    acceptance = read_json(root / CERBERUS_ACCEPTANCE)
    findings_payload = read_json(root / CERBERUS_FINDINGS)
    findings = findings_payload.get("findings", [])
    open_findings = [
        row for row in findings
        if isinstance(row, dict) and row.get("status") == "OPEN" and row.get("severity") != "NON_DEFECT_OBSERVATION"
    ]
    defects: list[str] = []
    if acceptance.get("status") != "PASS":
        defects.append("Cerberus acceptance certificate is not PASS")
    if acceptance.get("llm_gate_status") != "PASS":
        defects.append("Cerberus LLM gate is not PASS")
    if open_findings:
        defects.append(f"Cerberus has {len(open_findings)} open defect findings")
    return {
        "lane_id": "CERBERUS_RELEASE_REVIEW_GATE",
        "lane_type": "review_gate",
        "status": "PASS" if not defects else "FAIL",
        "closure_verdict": "PASS" if not defects else "FAIL_CLOSED",
        "final_toe_support_allowed": not defects,
        "source_refs": [str(CERBERUS_ACCEPTANCE), str(CERBERUS_FINDINGS)],
        "open_defect_total": len(open_findings),
        "finding_total": len(defects),
        "findings": defects,
    }


def build_lane_results(root: Path, *, generated_at: str | None = None) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for lane_id, path in FINAL_TOE_PROJECTION_LANE_TARGETS.items():
        rows.append(evaluate_projection_lane(root, lane_id, path))
    rows.append(evaluate_grand_claim_lane(root))
    rows.append(evaluate_comparator_lane(root))
    rows.append(evaluate_cerberus_lane(root))
    payload = {
        "schema_id": "OC133_TOE_LANE_RESULTS_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": generated_at or utc_now(),
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
        "lane_total": len(rows),
        "pass_lane_total": sum(1 for row in rows if row["status"] == "PASS"),
        "fail_lane_total": sum(1 for row in rows if row["status"] != "PASS"),
        "rows": rows,
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def run_command(root: Path, cmd: list[str], timeout: int) -> dict[str, Any]:
    completed = subprocess.run(
        cmd,
        cwd=root,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=timeout,
    )
    return {
        "cmd": cmd,
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout[-3000:],
        "stderr_tail": completed.stderr[-3000:],
    }


def lane_registry_by_id() -> dict[str, dict[str, Any]]:
    return {row["lane_id"]: row for row in lane_registry_rows()}


def lane_result_by_id(root: Path, lane_id: str) -> dict[str, Any]:
    for row in build_lane_results(root).get("rows", []):
        if row.get("lane_id") == lane_id:
            return row
    return {
        "lane_id": lane_id,
        "status": "MISSING",
        "closure_verdict": "FAIL_CLOSED",
        "final_toe_support_allowed": False,
        "findings": ["lane result missing"],
    }


def active_lane_ids(root: Path, science_failures: list[str]) -> list[str]:
    classes = error_classes(science_failures)
    lanes: list[str] = []
    if "AI_DOMAIN_TOE_PROJECTION_LANE" in classes or lane_result_by_id(root, "AI").get("status") != "PASS":
        lanes.append("AI")
    if "ENTERPRISE_ARCHITECTURE_DOMAIN_TOE_PROJECTION_LANE" in classes or lane_result_by_id(root, "ENTERPRISE_ARCHITECTURE").get("status") != "PASS":
        lanes.append("ENTERPRISE_ARCHITECTURE")
    if "GRAND_TOE_CLAIM_LEDGER_EVIDENCE" in classes or lane_result_by_id(root, "GRAND_TOE_CLAIM_LEDGER_EVIDENCE").get("status") != "PASS":
        lanes.append("GRAND_TOE_CLAIM_LEDGER_EVIDENCE")
    if "MODERN_SCIENCE_COMPARATOR_SUPERIORITY" in classes or lane_result_by_id(root, "MODERN_SCIENCE_COMPARATOR_SUPERIORITY").get("status") != "PASS":
        lanes.append("MODERN_SCIENCE_COMPARATOR_SUPERIORITY")
    return lanes


def execute_lane_attempt(root: Path, lane_id: str, timeout: int) -> dict[str, Any]:
    registry = lane_registry_by_id()
    lane = registry.get(lane_id)
    if not lane:
        return {
            "lane_id": lane_id,
            "status": "FAIL_CLOSED",
            "execution_state": "LANE_NOT_REGISTERED",
            "command_results": [],
        }

    before_parts = current_validator_error_parts(root)
    before_total = len(before_parts["science_errors"]) + len(before_parts["cerberus_errors"])
    command_results: list[dict[str, Any]] = []
    execution_state = "EXECUTED"

    if lane_id in {"AI", "ENTERPRISE_ARCHITECTURE"}:
        execution_state = "CAPABILITY_MISSING_OR_EXHAUSTED"
        command_results.append(
            {
                "cmd": lane["execution_command"],
                "returncode": None,
                "stdout_tail": "",
                "stderr_tail": (
                    f"{lane_id} has a registered projection lane, but no source-grounded dedicated "
                    "research capability exists yet to create PASS-grade claim/formal/evidence/comparator/falsifier artifacts."
                ),
            }
        )
    elif lane_id == "CERBERUS_RELEASE_REVIEW_GATE" and before_parts["science_errors"]:
        execution_state = "SKIPPED_DETERMINISTIC_SCIENCE_BLOCKERS_REMAIN"
        command_results.append(
            {
                "cmd": lane["execution_command"],
                "returncode": None,
                "stdout_tail": "",
                "stderr_tail": "Cerberus/LLM gate skipped because science validator still has deterministic blockers.",
            }
        )
    else:
        try:
            command_results.append(run_command(root, lane["execution_command"], timeout))
        except subprocess.TimeoutExpired as exc:
            command_results.append(
                {
                    "cmd": lane["execution_command"],
                    "returncode": 124,
                    "stdout_tail": (exc.stdout or "")[-3000:] if isinstance(exc.stdout, str) else "",
                    "stderr_tail": (exc.stderr or "timeout")[-3000:] if isinstance(exc.stderr, str) else "timeout",
                }
            )

    after_parts = current_validator_error_parts(root)
    after_total = len(after_parts["science_errors"]) + len(after_parts["cerberus_errors"])
    lane_result = lane_result_by_id(root, lane_id)
    closure_status = "PASS" if lane_result.get("status") == "PASS" else "FAIL_CLOSED"
    if execution_state in {"CAPABILITY_MISSING_OR_EXHAUSTED", "SKIPPED_DETERMINISTIC_SCIENCE_BLOCKERS_REMAIN"}:
        closure_status = execution_state
    return {
        "lane_id": lane_id,
        "finding_class": lane["finding_class"],
        "owner_capability": lane["owner_capability"],
        "status": closure_status,
        "execution_state": execution_state,
        "closure_condition": lane["closure_condition"],
        "pass_predicate": lane["pass_predicate"],
        "validator_binding": lane["validator_binding"],
        "before_science_error_total": len(before_parts["science_errors"]),
        "before_cerberus_error_total": len(before_parts["cerberus_errors"]),
        "after_science_error_total": len(after_parts["science_errors"]),
        "after_cerberus_error_total": len(after_parts["cerberus_errors"]),
        "validator_error_delta": before_total - after_total,
        "lane_result": lane_result,
        "command_results": command_results,
        "no_fake_closure_policy": lane["no_fake_closure_policy"],
    }


def execute_active_lanes(root: Path, timeout: int) -> dict[str, Any]:
    before_parts = current_validator_error_parts(root)
    lanes = active_lane_ids(root, before_parts["science_errors"])
    rows = [execute_lane_attempt(root, lane_id, timeout) for lane_id in lanes]
    after_parts = current_validator_error_parts(root)
    before_total = len(before_parts["science_errors"]) + len(before_parts["cerberus_errors"])
    after_total = len(after_parts["science_errors"]) + len(after_parts["cerberus_errors"])
    pass_total = sum(1 for row in rows if row["status"] == "PASS")
    exhausted_total = sum(1 for row in rows if row["status"] == "CAPABILITY_MISSING_OR_EXHAUSTED")
    return {
        "schema_id": "OC133_TOE_ACTIVE_LANE_EXECUTION_v1",
        "lane_total": len(rows),
        "pass_lane_total": pass_total,
        "exhausted_lane_total": exhausted_total,
        "fail_closed_lane_total": len(rows) - pass_total,
        "before_validator_error_total": before_total,
        "after_validator_error_total": after_total,
        "validator_error_delta": before_total - after_total,
        "status": "PASS" if after_total == 0 else "LOCAL_CAPABILITY_EXHAUSTED" if exhausted_total else "FAIL_CLOSED",
        "rows": rows,
    }


def execute_closure_cycle(root: Path, timeout: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    commands = [
        ("sync_spot", [sys.executable, "tools/build_oc_core_1_3_science_spot.py"]),
    ]
    for index, (purpose, cmd) in enumerate(commands, start=1):
        try:
            result = run_command(root, cmd, timeout)
        except subprocess.TimeoutExpired as exc:
            result = {
                "cmd": cmd,
                "returncode": 124,
                "stdout_tail": (exc.stdout or "")[-3000:] if isinstance(exc.stdout, str) else "",
                "stderr_tail": (exc.stderr or "timeout")[-3000:] if isinstance(exc.stderr, str) else "timeout",
            }
        rows.append(
            {
                "step_index": index,
                "purpose": purpose,
                "status": "PASS" if result["returncode"] == 0 else "FAIL_CLOSED",
                "result": result,
            }
        )
    lane_payload = execute_active_lanes(root, timeout)
    rows.append(
        {
            "step_index": len(rows) + 1,
            "purpose": "lane_dispatcher",
            "status": lane_payload["status"],
            "result": lane_payload,
        }
    )
    post_lane_sync = run_command(root, [sys.executable, "tools/build_oc_core_1_3_science_spot.py"], timeout)
    rows.append(
        {
            "step_index": len(rows) + 1,
            "purpose": "sync_spot_after_lane_dispatch",
            "status": "PASS" if post_lane_sync["returncode"] == 0 else "FAIL_CLOSED",
            "result": post_lane_sync,
        }
    )
    research_result = run_command(
        root,
        [sys.executable, "tools/oc133_grand_science_research_loop.py", "--execute", "--allow-blocked-exit-zero"],
        timeout,
    )
    rows.append(
        {
            "step_index": len(rows) + 1,
            "purpose": "research_loop",
            "status": "PASS" if research_result["returncode"] == 0 else "FAIL_CLOSED",
            "result": research_result,
        }
    )
    science_result = run_command(
        root,
        [sys.executable, "tools/validate_oc_core_1_3_science_spot.py", "--require-final-toe-pass"],
        timeout,
    )
    rows.append(
        {
            "step_index": len(rows) + 1,
            "purpose": "science_validator_before_cerberus",
            "status": "PASS" if science_result["returncode"] == 0 else "FAIL_CLOSED",
            "result": science_result,
        }
    )
    if rows[-1]["status"] == "PASS":
        cerberus_cmd = [
            sys.executable,
            "tools/run_oc_core_1_3_cerberus_review.py",
            "--codex-model",
            "gpt-5.4-mini",
            "--llm-workers",
            "1",
            "--llm-batch-max-chars",
            "6000",
            "--llm-timeout-seconds",
            "300",
            "--build-mode",
            "full",
        ]
        try:
            result = run_command(root, cerberus_cmd, timeout)
        except subprocess.TimeoutExpired as exc:
            result = {
                "cmd": cerberus_cmd,
                "returncode": 124,
                "stdout_tail": (exc.stdout or "")[-3000:] if isinstance(exc.stdout, str) else "",
                "stderr_tail": (exc.stderr or "timeout")[-3000:] if isinstance(exc.stderr, str) else "timeout",
            }
        rows.append(
            {
                "step_index": len(rows) + 1,
                "purpose": "canonical_cerberus_after_science_clear",
                "status": "PASS" if result["returncode"] == 0 else "FAIL_CLOSED",
                "result": result,
            }
        )
    else:
        rows.append(
            {
                "step_index": len(rows) + 1,
                "purpose": "canonical_cerberus_after_science_clear",
                "status": "SKIPPED_DETERMINISTIC_SCIENCE_BLOCKERS_REMAIN",
                "result": {
                    "cmd": [
                        sys.executable,
                        "tools/run_oc_core_1_3_cerberus_review.py",
                        "--codex-model",
                        "gpt-5.4-mini",
                        "--llm-workers",
                        "1",
                    ],
                    "returncode": None,
                    "stdout_tail": "",
                    "stderr_tail": "Skipped because final science validator remains red; expensive Cerberus/LLM gate is not run until lower-level blockers are closed.",
                },
            }
        )
    final_cmd = [sys.executable, "tools/validate_oc_core_1_3_science_spot.py", "--require-final-toe-pass", "--require-cerberus-clean"]
    try:
        result = run_command(root, final_cmd, timeout)
    except subprocess.TimeoutExpired as exc:
        result = {
            "cmd": final_cmd,
            "returncode": 124,
            "stdout_tail": (exc.stdout or "")[-3000:] if isinstance(exc.stdout, str) else "",
            "stderr_tail": (exc.stderr or "timeout")[-3000:] if isinstance(exc.stderr, str) else "timeout",
        }
    rows.append(
        {
            "step_index": len(rows) + 1,
            "purpose": "final_validator",
            "status": "PASS" if result["returncode"] == 0 else "FAIL_CLOSED",
            "result": result,
        }
    )
    if rows and rows[-1]["status"] == "PASS":
        result = run_command(
            root,
            [
                sys.executable,
                "tools/assemble_oc_core_release_package.py",
                "--release",
                RELEASE_ID,
                "--structure-source",
                "recovered_l10c",
                "--assembly-revision",
                "recovery_r017",
                "--write",
            ],
            timeout,
        )
        rows.append(
            {
                "step_index": len(rows) + 1,
                "purpose": "assemble_r017",
                "status": "PASS" if result["returncode"] == 0 else "FAIL_CLOSED",
                "result": result,
            }
        )
    return rows


def execute_until_final_pass(root: Path, timeout: int, max_iterations: int) -> list[dict[str, Any]]:
    trace: list[dict[str, Any]] = []
    previous_total = len(current_validator_errors(root))
    for iteration in range(1, max_iterations + 1):
        if previous_total == 0:
            break
        cycle = execute_closure_cycle(root, timeout)
        current_total = len(current_validator_errors(root))
        delta = previous_total - current_total
        trace.append(
            {
                "step_index": len(trace) + 1,
                "purpose": f"until_final_pass_iteration_{iteration}",
                "status": "PASS" if current_total == 0 else "NO_PROGRESS_STOP" if delta <= 0 else "PROGRESS_REMAINS_BLOCKED",
                "result": {
                    "iteration": iteration,
                    "before_validator_error_total": previous_total,
                    "after_validator_error_total": current_total,
                    "validator_error_delta": delta,
                    "cycle_trace": cycle,
                },
            }
        )
        if current_total == 0:
            break
        if delta <= 0:
            trace.append(
                {
                    "step_index": len(trace) + 1,
                    "purpose": "until_final_pass_stop",
                    "status": "LOCAL_CAPABILITY_EXHAUSTED",
                    "result": {
                        "reason": "No validator-error reduction in the latest iteration; r017 remains blocked instead of faking TOE closure.",
                        "remaining_validator_errors": current_validator_errors(root),
                    },
                }
            )
            break
        previous_total = current_total
    return trace


def build_closure_state(
    root: Path,
    validator_parts: dict[str, list[str]],
    lanes: dict[str, Any],
    registry: dict[str, Any],
    execution_trace: list[dict[str, Any]],
    *,
    generated_at: str | None = None,
) -> dict[str, Any]:
    validator_errors = validator_parts["science_errors"] + validator_parts["cerberus_errors"]
    local_exhausted = any(row.get("status") in {"LOCAL_CAPABILITY_EXHAUSTED", "NO_PROGRESS_STOP"} for row in execution_trace)
    payload = {
        "schema_id": "OC133_TOE_CLOSURE_STATE_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": generated_at or utc_now(),
        "status": "PASS" if not validator_errors and lanes.get("status") == "PASS" else "LOCAL_CAPABILITY_EXHAUSTED" if local_exhausted else "OPEN",
        "r017_promotion_allowed": not validator_errors and lanes.get("status") == "PASS",
        "science_validator_error_total": len(validator_parts["science_errors"]),
        "cerberus_error_total": len(validator_parts["cerberus_errors"]),
        "validator_error_total": len(validator_errors),
        "lane_registry_status": registry.get("status"),
        "lane_total": registry.get("lane_total"),
        "pass_lane_total": lanes.get("pass_lane_total"),
        "fail_lane_total": lanes.get("fail_lane_total"),
        "local_capability_exhausted": local_exhausted,
        "no_fake_closure_policy": "r017 cannot be assembled unless the strict final validator and all lane gates pass.",
        "execution_trace": execution_trace,
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def build_cockpit(
    root: Path,
    obligations: dict[str, Any],
    lanes: dict[str, Any],
    validator_errors: list[str],
    execution_trace: list[dict[str, Any]],
    *,
    validator_parts: dict[str, list[str]] | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    validator_parts = validator_parts or {"science_errors": validator_errors, "cerberus_errors": []}
    promotion_allowed = not validator_errors and lanes.get("status") == "PASS" and obligations.get("open_work_order_total") == 0
    latest_execution_status = "NOT_RUN"
    if execution_trace:
        latest_execution_status = "PASS" if all(row["status"] == "PASS" for row in execution_trace) else "FAIL_CLOSED"
    payload = {
        "schema_id": "OC133_TOE_CLOSURE_COCKPIT_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": generated_at or utc_now(),
        "status": "PASS" if promotion_allowed else "OPEN",
        "current_promotion_gate": "R017_READY_TO_ASSEMBLE" if promotion_allowed else "R017_BLOCKED_BY_TOE_CLOSURE_FACTORY",
        "r017_promotion_allowed": promotion_allowed,
        "validator_error_total": len(validator_errors),
        "science_validator_error_total": len(validator_parts["science_errors"]),
        "cerberus_error_total": len(validator_parts["cerberus_errors"]),
        "open_obligation_total": obligations.get("open_work_order_total"),
        "lane_total": lanes.get("lane_total"),
        "pass_lane_total": lanes.get("pass_lane_total"),
        "fail_lane_total": lanes.get("fail_lane_total"),
        "lane_dispatcher_status": "PASS" if lanes.get("status") == "PASS" else "BLOCKED",
        "local_external_compute_policy": "deterministic/static first; governed local LLM for small chunks; external Cerberus only after deterministic blockers are zero",
        "ollama_usage_policy": "No direct unmanaged Ollama calls are made by this factory.",
        "proof_data_simulation_coverage_status": "PASS" if lanes.get("status") == "PASS" else "INCOMPLETE",
        "comparator_coverage_status": next((row["status"] for row in lanes.get("rows", []) if row["lane_id"] == "MODERN_SCIENCE_COMPARATOR_SUPERIORITY"), "MISSING"),
        "cerberus_state": next((row["status"] for row in lanes.get("rows", []) if row["lane_id"] == "CERBERUS_RELEASE_REVIEW_GATE"), "MISSING"),
        "latest_execution_status": latest_execution_status,
        "execution_step_total": len(execution_trace),
        "execution_trace": execution_trace,
        "validator_errors": validator_errors,
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def render_cockpit_md(cockpit: dict[str, Any], lanes: dict[str, Any], obligations: dict[str, Any]) -> str:
    lines = [
        "# OC Core 1.3.3 TOE Closure Factory Cockpit",
        "",
        f"Status: `{cockpit['status']}`",
        f"Promotion gate: `{cockpit['current_promotion_gate']}`",
        f"Validator errors: `{cockpit['validator_error_total']}`",
        f"Science errors: `{cockpit.get('science_validator_error_total', cockpit['validator_error_total'])}`",
        f"Cerberus errors: `{cockpit.get('cerberus_error_total', 0)}`",
        f"Open obligations: `{cockpit['open_obligation_total']}`",
        f"Lanes: `{cockpit['pass_lane_total']}/{cockpit['lane_total']}` PASS",
        f"Lane dispatcher: `{cockpit.get('lane_dispatcher_status', 'BLOCKED')}`",
        f"Latest execution: `{cockpit['latest_execution_status']}`",
        "",
        "## Lane Results",
        "",
    ]
    for row in lanes.get("rows", []):
        lines.append(f"- `{row['lane_id']}`: `{row['status']}` / `{row['closure_verdict']}`")
    lines.extend(["", "## Open Obligations", ""])
    for row in obligations.get("rows", [])[:40]:
        lines.append(f"- `{row['work_order_id']}` `{row['finding_class']}`: {row['closure_condition']}")
    return "\n".join(lines).rstrip() + "\n"


def existing_generated_at(path: Path) -> str | None:
    payload = read_json(path)
    value = payload.get("generated_at")
    return value if isinstance(value, str) and value else None


def existing_execution_trace(path: Path) -> list[dict[str, Any]]:
    payload = read_json(path)
    trace = payload.get("execution_trace")
    return trace if isinstance(trace, list) else []


def expected_files(
    root: Path,
    *,
    execute: bool = False,
    until_final_pass: bool = False,
    timeout: int = 900,
    max_iterations: int = 6,
    preserve_existing_generated_at: bool = False,
) -> dict[Path, str]:
    base = root / FACTORY_DIR
    if until_final_pass:
        execution_trace = execute_until_final_pass(root, timeout, max_iterations)
    elif execute:
        execution_trace = execute_closure_cycle(root, timeout)
    else:
        execution_trace = existing_execution_trace(base / COCKPIT_NAME) if preserve_existing_generated_at else []
    validator_parts = current_validator_error_parts(root)
    validator_errors = validator_parts["science_errors"] + validator_parts["cerberus_errors"]
    obligations_generated_at = existing_generated_at(base / OBLIGATIONS_NAME) if preserve_existing_generated_at else None
    lanes_generated_at = existing_generated_at(base / LANES_NAME) if preserve_existing_generated_at else None
    cockpit_generated_at = existing_generated_at(base / COCKPIT_NAME) if preserve_existing_generated_at else None
    registry_generated_at = existing_generated_at(base / REGISTRY_NAME) if preserve_existing_generated_at else None
    state_generated_at = existing_generated_at(base / STATE_NAME) if preserve_existing_generated_at else None
    obligations = build_obligations(root, validator_errors, generated_at=obligations_generated_at)
    lanes = build_lane_results(root, generated_at=lanes_generated_at)
    registry = build_lane_capability_registry(generated_at=registry_generated_at)
    state = build_closure_state(
        root,
        validator_parts,
        lanes,
        registry,
        execution_trace,
        generated_at=state_generated_at,
    )
    cockpit = build_cockpit(
        root,
        obligations,
        lanes,
        validator_errors,
        execution_trace,
        validator_parts=validator_parts,
        generated_at=cockpit_generated_at,
    )
    return {
        base / OBLIGATIONS_NAME: stable_json(obligations),
        base / LANES_NAME: stable_json(lanes),
        base / REGISTRY_NAME: stable_json(registry),
        base / STATE_NAME: stable_json(state),
        base / COCKPIT_NAME: stable_json(cockpit),
        base / COCKPIT_MD_NAME: render_cockpit_md(cockpit, lanes, obligations),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the OC Core 1.3.3 TOE Closure Factory.")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--execute", action="store_true", help="Run the sync/research/Cerberus/validator cycle before writing outputs.")
    parser.add_argument("--until-final-pass", action="store_true", help="Iterate closure cycles until final validator PASS or honest local capability exhaustion.")
    parser.add_argument("--max-iterations", type=int, default=6)
    parser.add_argument("--execute-lane", choices=[row["lane_id"] for row in lane_registry_rows()])
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args(argv)
    if args.execute_lane:
        payload = execute_lane_attempt(ROOT, args.execute_lane, args.timeout)
        payload["generated_at"] = utc_now()
        payload["artifact_hash"] = artifact_hash(payload)
        path = ROOT / FACTORY_DIR / f"OC133_TOE_LANE_EXECUTION_{args.execute_lane}.json"
        result = validation_result({path: stable_json(payload)}, write=args.write)
        print(json.dumps(result if args.write or args.check else payload, ensure_ascii=False, indent=2, sort_keys=True))
        return 1 if args.check and result["state"] != "PASS" else 0
    if not args.write and not args.check:
        args.check = True
    preserve_existing_generated_at = args.check and not args.write and not args.execute and not args.until_final_pass
    result = validation_result(
        expected_files(
            ROOT,
            execute=args.execute,
            until_final_pass=args.until_final_pass,
            timeout=args.timeout,
            max_iterations=args.max_iterations,
            preserve_existing_generated_at=preserve_existing_generated_at,
        ),
        write=args.write,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    cockpit = json.loads((ROOT / FACTORY_DIR / COCKPIT_NAME).read_text(encoding="utf-8")) if (ROOT / FACTORY_DIR / COCKPIT_NAME).exists() else None
    if args.check and result["state"] != "PASS":
        return 1
    if cockpit and cockpit.get("r017_promotion_allowed") is True:
        return 0
    return 0 if args.write or args.check else 1


if __name__ == "__main__":
    raise SystemExit(main())
