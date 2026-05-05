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
TOOLS_DIR = ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

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
ROOT_CAUSE_LEDGER_NAME = "OC133_TOE_ROOT_CAUSE_LEDGER.json"
CAPABILITY_BACKLOG_NAME = "OC133_TOE_CAPABILITY_BACKLOG.json"
SUBWORK_ORDERS_NAME = "OC133_TOE_LANE_SUBWORK_ORDERS.json"
VALIDATOR_DELTA_TRACE_NAME = "OC133_TOE_VALIDATOR_DELTA_TRACE.json"

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


def root_cause_for_error(error: str) -> dict[str, Any]:
    finding_class, severity, route, closure, effect = classify_validator_error(error)
    lowered = error.lower()
    if finding_class == "AI_DOMAIN_TOE_PROJECTION_LANE":
        return {
            "root_cause_class": "MISSING_EXECUTABLE_AI_TOE_PROJECTION_SUPPORT",
            "root_cause_evidence": [
                "releases/oc_core_1_3/editorial/science_sources/toe_projection_lanes/ai.json::closure_verdict=FAIL_CLOSED",
                "tools/oc133_toe_closure_factory.py::AI lane previously had no dedicated source-grounded capability",
            ],
            "why_it_failed": "The AI lane is present, but it contains bounded future-research rows rather than dedicated PASS-grade claim, formal-boundary, evidence/simulation, comparator, and falsifier bindings.",
            "repair_strategy": "Execute the AI projection capability lane: inventory AI claims from the canonical corpus, bind formal boundaries and finite witnesses, add benchmark/simulation evidence, comparator baselines, and falsifier rows, then rewrite ai.json only when all required refs exist.",
            "required_capability": "Research/AIProjection",
        }
    if finding_class == "ENTERPRISE_ARCHITECTURE_DOMAIN_TOE_PROJECTION_LANE":
        return {
            "root_cause_class": "MISSING_EXECUTABLE_EA_TOE_PROJECTION_SUPPORT",
            "root_cause_evidence": [
                "releases/oc_core_1_3/editorial/science_sources/toe_projection_lanes/enterprise_architecture.json::closure_verdict=FAIL_CLOSED",
                "tools/oc133_toe_closure_factory.py::EA lane previously had no dedicated source-grounded capability",
            ],
            "why_it_failed": "The EA lane is present, but it contains bounded future-research rows rather than dedicated PASS-grade architecture cases, operational metrics, comparator alternatives, and falsifier bindings.",
            "repair_strategy": "Execute the EA projection capability lane: inventory EA claims from the canonical corpus, bind architecture cases and operational metrics, add comparator alternatives and falsifiers, then rewrite enterprise_architecture.json only when all required refs exist.",
            "required_capability": "Research/EnterpriseArchitectureProjection",
        }
    if finding_class == "GRAND_TOE_CLAIM_LEDGER_EVIDENCE":
        return {
            "root_cause_class": "GRAND_PROMOTION_CONTRACT_DEPENDENCY_FAILURE",
            "root_cause_evidence": [
                str(GRAND_SCORECARD),
                str(GRAND_PROMOTION_REPORT),
                str(FINITE_CHECK_REPORT),
            ],
            "why_it_failed": "The grand TOE promotion contract is blocked by missing dedicated promoted-claim evidence, comparator superiority, empirical superiority, and finite model failures.",
            "repair_strategy": "Split grand closure into sublanes for promoted claim row, theorem/proof refs, Lean refs, finite positive/negative controls, finite failure repair, empirical pack, comparator pack, and promotion contract refresh.",
            "required_capability": "Research/FormalScience",
        }
    if finding_class == "MODERN_SCIENCE_COMPARATOR_SUPERIORITY":
        return {
            "root_cause_class": "BROAD_COMPARATOR_COVERAGE_GAP",
            "root_cause_evidence": [
                str(COMPARATOR_REGISTER),
                "comparators/OC_1_3_3_MODERN_SCIENCE_SUPERIORITY_REGISTER.json::coverage_extends_to_all_of_modern_science=false",
            ],
            "why_it_failed": "The current comparator evidence certifies only benchmark-scoped superiority; broad modern-science superiority is blocked by uncovered domains and missing source-backed comparator predicates.",
            "repair_strategy": "Expand comparator work into per-gap source-backed benchmark/comparator rows and keep broad superiority blocked until all broad coverage predicates pass.",
            "required_capability": "Research/PriorArt",
        }
    if finding_class == "ALL_DOMAIN_READINESS_SCORECARD":
        return {
            "root_cause_class": "DOWNSTREAM_SCORECARD_BLOCKED_BY_OPEN_LANES",
            "root_cause_evidence": [str(GRAND_SCORECARD)],
            "why_it_failed": "The all-domain readiness flag is downstream of AI, EA, grand promotion, comparator, and Cerberus gates; it cannot turn green while any parent lane remains red.",
            "repair_strategy": "Close parent lanes first, rebuild the SPOT and scorecard, then rerun the final TOE validator.",
            "required_capability": "Research/ScorecardSync",
        }
    if finding_class == "CERBERUS_RELEASE_REVIEW_GATE":
        return {
            "root_cause_class": "STALE_OR_UNCLEAN_CERBERUS_SURFACE",
            "root_cause_evidence": [
                str(CERBERUS_ACCEPTANCE),
                str(CERBERUS_FINDINGS),
            ],
            "why_it_failed": "Cerberus targets/run/acceptance fingerprints or open findings do not bind cleanly to the current repository state.",
            "repair_strategy": "Skip expensive Cerberus while deterministic science gates are red; after science PASS, refresh Cerberus targets/run/acceptance and clear open findings.",
            "required_capability": "Review/Cerberus",
        }
    return {
        "root_cause_class": "UNCLASSIFIED_TOE_VALIDATOR_BLOCKER",
        "root_cause_evidence": ["tools/validate_oc_core_1_3_science_spot.py"],
        "why_it_failed": "The strict validator emitted an unclassified blocker; the factory must classify it before promotion.",
        "repair_strategy": "Add a classifier, evidence refs, and executable lane or sublane for this validator message, then rerun the final validator.",
        "required_capability": "Research/ValidatorClassifier",
    }


def execution_command_for_finding(finding_class: str) -> list[str]:
    lane_by_finding = {row["finding_class"]: row["lane_id"] for row in lane_registry_rows()}
    lane_id = lane_by_finding.get(finding_class)
    if lane_id:
        return [sys.executable, "tools/oc133_toe_closure_factory.py", "--execute-capability-lane", lane_id, "--write"]
    return [sys.executable, "tools/oc133_toe_closure_factory.py", "--execute", "--write"]


def root_cause_row_for_error(index: int, error: str) -> dict[str, Any]:
    finding_class, severity, route, closure, effect = classify_validator_error(error)
    root_cause = root_cause_for_error(error)
    return {
        "problem_id": f"R017-ROOT-CAUSE-{index:03d}",
        "source_validator_message": error,
        "symptom": error,
        "severity": severity,
        "finding_class": finding_class,
        "root_cause_class": root_cause["root_cause_class"],
        "root_cause_evidence": root_cause["root_cause_evidence"],
        "why_it_failed": root_cause["why_it_failed"],
        "repair_strategy": root_cause["repair_strategy"],
        "research_route": route,
        "required_capability": root_cause["required_capability"],
        "execution_command": execution_command_for_finding(finding_class),
        "pass_predicate": closure,
        "expected_validator_delta": 1,
        "actual_validator_delta": 0,
        "next_escalation": "Create or execute the required capability lane; if source support is absent, produce a source-gap work order rather than passing.",
        "claim_effect": effect,
        "status": "OPEN",
        "blocks_r017": True,
        "fake_closure_rejected": True,
    }


def work_order_for_error(index: int, error: str) -> dict[str, Any]:
    finding_class, severity, route, closure, effect = classify_validator_error(error)
    root_cause = root_cause_for_error(error)
    return {
        "work_order_id": f"R017-TOE-CLOSURE-{index:03d}",
        "source_validator_message": error,
        "finding_class": finding_class,
        "root_cause_class": root_cause["root_cause_class"],
        "root_cause_evidence": root_cause["root_cause_evidence"],
        "why_it_failed": root_cause["why_it_failed"],
        "repair_strategy": root_cause["repair_strategy"],
        "required_capability": root_cause["required_capability"],
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
        root_cause = root_cause_for_error(f"{lane_id} lane closure_verdict is not PASS")
        output.append(
            {
                "work_order_id": f"R017-TOE-LANE-{lane_id}-{start_index + offset:03d}",
                "source_validator_message": f"{lane_id} lane active closure obligation",
                "finding_class": finding_class,
                "root_cause_class": root_cause["root_cause_class"],
                "root_cause_evidence": root_cause["root_cause_evidence"],
                "why_it_failed": root_cause["why_it_failed"],
                "repair_strategy": root_cause["repair_strategy"],
                "required_capability": root_cause["required_capability"],
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


def failed_finite_rows(root: Path) -> list[dict[str, Any]]:
    finite = read_json(root / FINITE_CHECK_REPORT)
    rows = finite.get("rows", [])
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict) and row.get("passed") is not True]


def comparator_gap_total(root: Path) -> int:
    register = read_json(root / COMPARATOR_REGISTER)
    try:
        return int(register.get("coverage_gap_total") or 0)
    except Exception:
        return 0


def comparator_gap_rows(root: Path) -> list[dict[str, Any]]:
    register = read_json(root / COMPARATOR_REGISTER)
    gap_total = comparator_gap_total(root)
    blockers = register.get("broad_claim_blockers")
    if not isinstance(blockers, list) or not blockers:
        blockers = ["coverage_extends_to_all_of_modern_science"]
    matrix_summary = register.get("domain_evidence_matrix_summary", {})
    domains = matrix_summary.get("domains") if isinstance(matrix_summary, dict) else None
    if not isinstance(domains, list) or not domains:
        domains = ["physics", "chemistry", "biology", "systems"]
    rows: list[dict[str, Any]] = []
    for index in range(1, max(gap_total, 1) + 1):
        domain = str(domains[(index - 1) % len(domains)])
        rows.append(
            {
                "subwork_order_id": f"R017-COMPARATOR-COVERAGE-GAP-{index:03d}",
                "lane_id": "MODERN_SCIENCE_COMPARATOR_SUPERIORITY",
                "status": "OPEN",
                "domain": domain,
                "root_cause_class": "BROAD_COMPARATOR_COVERAGE_GAP",
                "why_it_failed": "Broad superiority is blocked because current evidence is benchmark-scoped and does not cover all of modern science.",
                "repair_strategy": "Bind a source-backed comparator row, evidence pack, baseline, uncertainty/fairness statement, and falsifier for this coverage gap.",
                "closure_condition": "coverage_extends_to_all_of_modern_science can only turn true after every required coverage gap has source-backed comparator support.",
                "source_refs": [str(COMPARATOR_REGISTER)],
                "blockers": blockers,
            }
        )
    return rows


def projection_lane_subwork(lane_id: str) -> list[dict[str, Any]]:
    if lane_id == "AI":
        capability = "Research/AIProjection"
        work = [
            ("CLAIM_GRAPH", "Extract source-grounded AI/agentic-system claims from canonical SPOT and claim ledgers."),
            ("FORMAL_BOUNDARY", "Bind each AI claim to a theorem, proof sheet, Lean ref, finite case, or explicit formal boundary."),
            ("BENCHMARK_SIMULATION", "Bind benchmark or simulation evidence with replayable source refs."),
            ("COMPARATOR_BASELINE", "Bind comparator baselines against relevant AI/system-design alternatives."),
            ("FALSIFIER", "Bind falsifier rows and scope limits for each promoted AI claim."),
            ("PROJECTION_PASS_WRITER", "Rewrite ai.json only if every required field and ref passes static validation."),
        ]
    else:
        capability = "Research/EnterpriseArchitectureProjection"
        work = [
            ("CLAIM_GRAPH", "Extract source-grounded enterprise-architecture claims from canonical SPOT and public payload sources."),
            ("ARCHITECTURE_CASES", "Bind architecture cases, operational metrics, and decision records."),
            ("FORMAL_BOUNDARY", "Bind each EA claim to a formal boundary, theorem/proof packet, finite witness, or explicit non-promotion boundary."),
            ("COMPARATOR_ALTERNATIVES", "Bind comparator alternatives such as TOGAF, Zachman, DDD, capability maps, and systems-engineering baselines."),
            ("FALSIFIER", "Bind falsifier rows and scope limits for each promoted EA claim."),
            ("PROJECTION_PASS_WRITER", "Rewrite enterprise_architecture.json only if every required field and ref passes static validation."),
        ]
    finding_class = "AI_DOMAIN_TOE_PROJECTION_LANE" if lane_id == "AI" else "ENTERPRISE_ARCHITECTURE_DOMAIN_TOE_PROJECTION_LANE"
    rows = []
    for index, (step_id, description) in enumerate(work, start=1):
        rows.append(
            {
                "subwork_order_id": f"R017-{lane_id}-{step_id}-{index:03d}",
                "lane_id": lane_id,
                "status": "OPEN",
                "finding_class": finding_class,
                "required_capability": capability,
                "why_it_failed": "The current projection lane is bounded future research and lacks PASS-grade source-bound projection rows.",
                "repair_strategy": description,
                "closure_condition": "The lane may PASS only when claim id, public scope, formal/evidence/comparator/falsifier refs, row PASS, lane PASS, and final TOE support are all true.",
                "source_refs": [str(FINAL_TOE_PROJECTION_LANE_TARGETS[lane_id].relative_to(REPO_ROOT))],
                "fake_closure_rejected": True,
            }
        )
    return rows


def grand_claim_subwork(root: Path) -> list[dict[str, Any]]:
    rows = [
        ("PROMOTED_CLAIM_ROW", "Create a dedicated promoted grand TOE claim row only if all formal, finite, empirical, comparator, and falsifier dependencies pass."),
        ("THEOREM_PROOF_REFS", "Bind theorem and proof-sheet refs to the promoted claim route."),
        ("LEAN_REFS", "Bind Lean refs and certificate hashes to the promotion route."),
        ("FINITE_CONTROL_SET", "Bind finite positive and negative controls to the promotion route."),
        ("EMPIRICAL_PACK", "Bind the all-domain empirical pack and replay evidence."),
        ("COMPARATOR_PACK", "Bind modern-science comparator PASS evidence."),
        ("PROMOTION_CONTRACT_REFRESH", "Refresh the grand promotion contract after all dependencies pass."),
    ]
    output: list[dict[str, Any]] = []
    for index, (step_id, strategy) in enumerate(rows, start=1):
        output.append(
            {
                "subwork_order_id": f"R017-GRAND-{step_id}-{index:03d}",
                "lane_id": "GRAND_TOE_CLAIM_LEDGER_EVIDENCE",
                "status": "OPEN",
                "finding_class": "GRAND_TOE_CLAIM_LEDGER_EVIDENCE",
                "required_capability": "Research/FormalScience",
                "why_it_failed": "The grand promotion contract is blocked by missing or failing promotion dependencies.",
                "repair_strategy": strategy,
                "closure_condition": "Grand promotion contract verdict is PASS and grand_toe_claim_ledger_evidence is not in blocker_ids.",
                "source_refs": [str(GRAND_SCORECARD), str(GRAND_PROMOTION_REPORT), str(FINITE_CHECK_REPORT)],
                "fake_closure_rejected": True,
            }
        )
    for failed in failed_finite_rows(root):
        case_id = str(failed.get("case_id") or "UNKNOWN")
        output.append(
            {
                "subwork_order_id": f"R017-FINITE-FAILURE-{case_id}",
                "lane_id": "GRAND_TOE_CLAIM_LEDGER_EVIDENCE",
                "status": "OPEN",
                "finding_class": "GRAND_TOE_CLAIM_LEDGER_EVIDENCE",
                "required_capability": "Research/FiniteModelChecks",
                "why_it_failed": f"Finite model case {case_id} did not pass: expected {failed.get('effective_expected_verdict') or failed.get('expected_verdict')} but observed {failed.get('observed_verdict')}.",
                "repair_strategy": "Diagnose whether the model, expectation, theorem binding, or promotion claim is wrong; then repair the source or keep the claim blocked.",
                "closure_condition": f"Finite model case {case_id} passes without weakening the finite-check gate.",
                "source_refs": [str(FINITE_CHECK_REPORT), str(failed.get("lean_theorem_ref") or "NO_LEAN_REF_BOUND")],
                "finite_case": failed,
                "fake_closure_rejected": True,
            }
        )
    return output


def build_lane_subwork_orders(root: Path, validator_errors: list[str], *, generated_at: str | None = None) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    classes = error_classes(validator_errors)
    if "AI_DOMAIN_TOE_PROJECTION_LANE" in classes or lane_result_by_id(root, "AI").get("status") != "PASS":
        rows.extend(projection_lane_subwork("AI"))
    if "ENTERPRISE_ARCHITECTURE_DOMAIN_TOE_PROJECTION_LANE" in classes or lane_result_by_id(root, "ENTERPRISE_ARCHITECTURE").get("status") != "PASS":
        rows.extend(projection_lane_subwork("ENTERPRISE_ARCHITECTURE"))
    if "GRAND_TOE_CLAIM_LEDGER_EVIDENCE" in classes or lane_result_by_id(root, "GRAND_TOE_CLAIM_LEDGER_EVIDENCE").get("status") != "PASS":
        rows.extend(grand_claim_subwork(root))
    if "MODERN_SCIENCE_COMPARATOR_SUPERIORITY" in classes or lane_result_by_id(root, "MODERN_SCIENCE_COMPARATOR_SUPERIORITY").get("status") != "PASS":
        rows.extend(comparator_gap_rows(root))
    if "CERBERUS_RELEASE_REVIEW_GATE" in classes or lane_result_by_id(root, "CERBERUS_RELEASE_REVIEW_GATE").get("status") != "PASS":
        rows.extend(
            [
                {
                    "subwork_order_id": "R017-CERBERUS-DETERMINISTIC-FINGERPRINT-REFRESH",
                    "lane_id": "CERBERUS_RELEASE_REVIEW_GATE",
                    "status": "BLOCKED_BY_SCIENCE_VALIDATOR" if science_errors(root) else "OPEN",
                    "finding_class": "CERBERUS_RELEASE_REVIEW_GATE",
                    "required_capability": "Review/Cerberus",
                    "why_it_failed": "Cerberus targets/run/acceptance fingerprints or open findings do not bind cleanly to current HEAD.",
                    "repair_strategy": "After deterministic science PASS, refresh Cerberus target/run/acceptance surfaces and rerun clean acceptance.",
                    "closure_condition": "Cerberus acceptance PASS, LLM gate PASS, fingerprint match, and open defect findings zero.",
                    "source_refs": [str(CERBERUS_ACCEPTANCE), str(CERBERUS_FINDINGS)],
                    "fake_closure_rejected": True,
                }
            ]
        )
    payload = {
        "schema_id": "OC133_TOE_LANE_SUBWORK_ORDERS_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": generated_at or utc_now(),
        "status": "OPEN" if rows else "PASS",
        "subwork_order_total": len(rows),
        "open_subwork_order_total": sum(1 for row in rows if row.get("status") == "OPEN"),
        "blocked_subwork_order_total": sum(1 for row in rows if str(row.get("status", "")).startswith("BLOCKED")),
        "rows": rows,
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def build_root_cause_ledger(
    root: Path,
    validator_errors: list[str],
    execution_trace: list[dict[str, Any]],
    *,
    generated_at: str | None = None,
) -> dict[str, Any]:
    rows = [root_cause_row_for_error(index + 1, error) for index, error in enumerate(validator_errors)]
    required = [
        "problem_id",
        "symptom",
        "root_cause_class",
        "root_cause_evidence",
        "why_it_failed",
        "repair_strategy",
        "required_capability",
        "execution_command",
        "pass_predicate",
        "expected_validator_delta",
        "actual_validator_delta",
        "next_escalation",
    ]
    incomplete = [
        row["problem_id"]
        for row in rows
        if any(row.get(field) is None or row.get(field) == "" or row.get(field) == [] for field in required)
    ]
    payload = {
        "schema_id": "OC133_TOE_ROOT_CAUSE_LEDGER_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": generated_at or utc_now(),
        "status": "PASS" if not rows else "OPEN",
        "root_cause_coverage_status": "PASS" if len(rows) == len(validator_errors) and not incomplete else "FAIL",
        "validator_error_total": len(validator_errors),
        "root_cause_total": len(rows),
        "incomplete_root_cause_total": len(incomplete),
        "incomplete_problem_ids": incomplete,
        "execution_trace_step_total": len(execution_trace),
        "rows": rows,
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def build_capability_backlog(
    root: Path,
    root_causes: dict[str, Any],
    subwork_orders: dict[str, Any],
    *,
    generated_at: str | None = None,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for row in root_causes.get("rows", []):
        key = (str(row.get("required_capability")), str(row.get("root_cause_class")))
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                "capability_backlog_id": f"R017-CAPABILITY-{len(rows) + 1:03d}",
                "required_capability": row.get("required_capability"),
                "root_cause_class": row.get("root_cause_class"),
                "status": "OPEN",
                "why_needed": row.get("why_it_failed"),
                "next_action": row.get("repair_strategy"),
                "execution_command": row.get("execution_command"),
                "pass_predicate": row.get("pass_predicate"),
            }
        )
    for row in subwork_orders.get("rows", []):
        key = (str(row.get("required_capability")), str(row.get("subwork_order_id")))
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                "capability_backlog_id": f"R017-CAPABILITY-{len(rows) + 1:03d}",
                "required_capability": row.get("required_capability"),
                "root_cause_class": row.get("finding_class"),
                "status": row.get("status", "OPEN"),
                "why_needed": row.get("why_it_failed"),
                "next_action": row.get("repair_strategy"),
                "execution_command": [sys.executable, "tools/oc133_toe_closure_factory.py", "--execute-capability-lane", row.get("lane_id", ""), "--write"],
                "pass_predicate": row.get("closure_condition"),
                "source_subwork_order_id": row.get("subwork_order_id"),
            }
        )
    payload = {
        "schema_id": "OC133_TOE_CAPABILITY_BACKLOG_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": generated_at or utc_now(),
        "status": "OPEN" if rows else "PASS",
        "capability_total": len(rows),
        "open_capability_total": sum(1 for row in rows if row.get("status") == "OPEN"),
        "rows": rows,
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def build_validator_delta_trace(
    execution_trace: list[dict[str, Any]],
    root_causes: dict[str, Any],
    capability_backlog: dict[str, Any],
    *,
    generated_at: str | None = None,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for index, step in enumerate(execution_trace, start=1):
        result = step.get("result", {}) if isinstance(step.get("result"), dict) else {}
        rows.append(
            {
                "delta_trace_id": f"R017-VALIDATOR-DELTA-{index:03d}",
                "purpose": step.get("purpose"),
                "status": step.get("status"),
                "before_validator_error_total": result.get("before_validator_error_total"),
                "after_validator_error_total": result.get("after_validator_error_total"),
                "validator_error_delta": result.get("validator_error_delta"),
            }
        )
    no_progress = any((row.get("validator_error_delta") in (0, None)) and row.get("status") not in {"PASS"} for row in rows)
    payload = {
        "schema_id": "OC133_TOE_VALIDATOR_DELTA_TRACE_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": generated_at or utc_now(),
        "status": "PASS" if root_causes.get("validator_error_total") == 0 else "CAPABILITY_BACKLOG_OPEN" if no_progress else "PROGRESS_REMAINS_BLOCKED",
        "trace_row_total": len(rows),
        "root_cause_total": root_causes.get("root_cause_total"),
        "capability_backlog_total": capability_backlog.get("capability_total"),
        "no_progress_creates_backlog": True,
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
        execution_state = "EXECUTED_SOURCE_GAP_DIAGNOSTIC"
        subwork = projection_lane_subwork(lane_id)
        command_results.append(
            {
                "cmd": ["internal", "build_projection_lane_subwork", lane_id],
                "returncode": 0,
                "stdout_tail": json.dumps(
                    {
                        "lane_id": lane_id,
                        "subwork_order_total": len(subwork),
                        "subwork_order_ids": [row["subwork_order_id"] for row in subwork],
                    },
                    ensure_ascii=False,
                ),
                "stderr_tail": (
                    f"{lane_id} source-gap diagnostic executed. The lane remains fail-closed until the "
                    "claim/formal/evidence/comparator/falsifier artifacts exist and pass static validation."
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
    if execution_state in {"SKIPPED_DETERMINISTIC_SCIENCE_BLOCKERS_REMAIN"}:
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
    backlog_total = sum(1 for row in rows if row["execution_state"] == "EXECUTED_SOURCE_GAP_DIAGNOSTIC")
    return {
        "schema_id": "OC133_TOE_ACTIVE_LANE_EXECUTION_v1",
        "lane_total": len(rows),
        "pass_lane_total": pass_total,
        "capability_backlog_lane_total": backlog_total,
        "fail_closed_lane_total": len(rows) - pass_total,
        "before_validator_error_total": before_total,
        "after_validator_error_total": after_total,
        "validator_error_delta": before_total - after_total,
        "status": "PASS" if after_total == 0 else "CAPABILITY_BACKLOG_OPEN" if backlog_total else "FAIL_CLOSED",
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
                "status": "PASS" if current_total == 0 else "CAPABILITY_BACKLOG_OPEN" if delta <= 0 else "PROGRESS_REMAINS_BLOCKED",
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
            remaining = current_validator_errors(root)
            subwork = build_lane_subwork_orders(root, remaining)
            trace.append(
                {
                    "step_index": len(trace) + 1,
                    "purpose": "until_final_pass_capability_backlog",
                    "status": "CAPABILITY_BACKLOG_OPEN",
                    "result": {
                        "reason": "No validator-error reduction in the latest iteration; the factory emits executable capability backlog and keeps r017 blocked instead of stopping with a fake terminal state.",
                        "remaining_validator_errors": remaining,
                        "subwork_order_total": subwork.get("subwork_order_total"),
                        "open_subwork_order_total": subwork.get("open_subwork_order_total"),
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
    root_causes: dict[str, Any] | None = None,
    capability_backlog: dict[str, Any] | None = None,
    subwork_orders: dict[str, Any] | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    validator_errors = validator_parts["science_errors"] + validator_parts["cerberus_errors"]
    local_exhausted = any(row.get("status") in {"LOCAL_CAPABILITY_EXHAUSTED", "NO_PROGRESS_STOP"} for row in execution_trace)
    root_causes = root_causes or {}
    capability_backlog = capability_backlog or {}
    subwork_orders = subwork_orders or {}
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
        "root_cause_coverage_status": root_causes.get("root_cause_coverage_status"),
        "root_cause_total": root_causes.get("root_cause_total"),
        "capability_backlog_total": capability_backlog.get("capability_total"),
        "lane_subwork_order_total": subwork_orders.get("subwork_order_total"),
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
    root_causes: dict[str, Any] | None = None,
    capability_backlog: dict[str, Any] | None = None,
    subwork_orders: dict[str, Any] | None = None,
    delta_trace: dict[str, Any] | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    validator_parts = validator_parts or {"science_errors": validator_errors, "cerberus_errors": []}
    root_causes = root_causes or {}
    capability_backlog = capability_backlog or {}
    subwork_orders = subwork_orders or {}
    delta_trace = delta_trace or {}
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
        "root_cause_coverage_status": root_causes.get("root_cause_coverage_status", "MISSING"),
        "root_cause_total": root_causes.get("root_cause_total", 0),
        "capability_backlog_status": capability_backlog.get("status", "MISSING"),
        "capability_backlog_total": capability_backlog.get("capability_total", 0),
        "lane_subwork_order_status": subwork_orders.get("status", "MISSING"),
        "lane_subwork_order_total": subwork_orders.get("subwork_order_total", 0),
        "validator_delta_trace_status": delta_trace.get("status", "MISSING"),
        "no_progress_creates_backlog": delta_trace.get("no_progress_creates_backlog", False),
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
        f"Root-cause coverage: `{cockpit.get('root_cause_coverage_status', 'MISSING')}`",
        f"Capability backlog: `{cockpit.get('capability_backlog_total', 0)}`",
        f"Lane subwork orders: `{cockpit.get('lane_subwork_order_total', 0)}`",
        f"Delta trace: `{cockpit.get('validator_delta_trace_status', 'MISSING')}`",
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
    root_cause_generated_at = existing_generated_at(base / ROOT_CAUSE_LEDGER_NAME) if preserve_existing_generated_at else None
    backlog_generated_at = existing_generated_at(base / CAPABILITY_BACKLOG_NAME) if preserve_existing_generated_at else None
    subwork_generated_at = existing_generated_at(base / SUBWORK_ORDERS_NAME) if preserve_existing_generated_at else None
    delta_trace_generated_at = existing_generated_at(base / VALIDATOR_DELTA_TRACE_NAME) if preserve_existing_generated_at else None
    obligations = build_obligations(root, validator_errors, generated_at=obligations_generated_at)
    lanes = build_lane_results(root, generated_at=lanes_generated_at)
    registry = build_lane_capability_registry(generated_at=registry_generated_at)
    subwork_orders = build_lane_subwork_orders(root, validator_errors, generated_at=subwork_generated_at)
    root_causes = build_root_cause_ledger(root, validator_errors, execution_trace, generated_at=root_cause_generated_at)
    capability_backlog = build_capability_backlog(
        root,
        root_causes,
        subwork_orders,
        generated_at=backlog_generated_at,
    )
    delta_trace = build_validator_delta_trace(
        execution_trace,
        root_causes,
        capability_backlog,
        generated_at=delta_trace_generated_at,
    )
    state = build_closure_state(
        root,
        validator_parts,
        lanes,
        registry,
        execution_trace,
        root_causes=root_causes,
        capability_backlog=capability_backlog,
        subwork_orders=subwork_orders,
        generated_at=state_generated_at,
    )
    cockpit = build_cockpit(
        root,
        obligations,
        lanes,
        validator_errors,
        execution_trace,
        validator_parts=validator_parts,
        root_causes=root_causes,
        capability_backlog=capability_backlog,
        subwork_orders=subwork_orders,
        delta_trace=delta_trace,
        generated_at=cockpit_generated_at,
    )
    return {
        base / OBLIGATIONS_NAME: stable_json(obligations),
        base / LANES_NAME: stable_json(lanes),
        base / REGISTRY_NAME: stable_json(registry),
        base / ROOT_CAUSE_LEDGER_NAME: stable_json(root_causes),
        base / CAPABILITY_BACKLOG_NAME: stable_json(capability_backlog),
        base / SUBWORK_ORDERS_NAME: stable_json(subwork_orders),
        base / VALIDATOR_DELTA_TRACE_NAME: stable_json(delta_trace),
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
    parser.add_argument("--emit-root-cause-ledger", action="store_true", help="Emit only the current root-cause ledger.")
    parser.add_argument("--max-iterations", type=int, default=6)
    parser.add_argument("--execute-lane", choices=[row["lane_id"] for row in lane_registry_rows()])
    parser.add_argument("--execute-capability-lane", choices=[row["lane_id"] for row in lane_registry_rows()])
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args(argv)
    lane_arg = args.execute_lane or args.execute_capability_lane
    if lane_arg:
        payload = execute_lane_attempt(ROOT, lane_arg, args.timeout)
        payload["generated_at"] = utc_now()
        payload["artifact_hash"] = artifact_hash(payload)
        path = ROOT / FACTORY_DIR / f"OC133_TOE_LANE_EXECUTION_{lane_arg}.json"
        result = validation_result({path: stable_json(payload)}, write=args.write)
        print(json.dumps(result if args.write or args.check else payload, ensure_ascii=False, indent=2, sort_keys=True))
        return 1 if args.check and result["state"] != "PASS" else 0
    if args.emit_root_cause_ledger:
        parts = current_validator_error_parts(ROOT)
        errors = parts["science_errors"] + parts["cerberus_errors"]
        path = ROOT / FACTORY_DIR / ROOT_CAUSE_LEDGER_NAME
        generated_at = existing_generated_at(path) if args.check and not args.write else None
        execution_trace = existing_execution_trace(ROOT / FACTORY_DIR / COCKPIT_NAME) if args.check and not args.write else []
        payload = build_root_cause_ledger(ROOT, errors, execution_trace, generated_at=generated_at)
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
