from __future__ import annotations

import argparse
import json
import re
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
PROBLEM_EXPLAINABILITY_GATE_NAME = "OC133_TOE_PROBLEM_EXPLAINABILITY_GATE.json"
RESEARCH_WAVE_NAME = "OC133_TOE_RESEARCH_WAVE_EXECUTION.json"
LANE_EXECUTION_DIR = FACTORY_DIR / "lane_execution"
EXPLAINABILITY_FIELDS = [
    "why_it_failed",
    "repair_strategy",
    "required_capability",
    "execution_command",
    "pass_predicate",
    "next_escalation",
]

GRAND_SCORECARD = MISSION_DIR / "OC133_ALL_DOMAIN_READINESS_SCORECARD.json"
GRAND_LOOP_REPORT = MISSION_DIR / "OC133_GRAND_SCIENCE_LOOP_latest.json"
GRAND_PROMOTION_REPORT = Path("proofs/grand_promotion/OC133_GRAND_PROMOTION_CONTRACT_REPORT.json")
FINITE_CHECK_REPORT = Path("proofs/FINITE_MODEL_CHECKS_1_3_3.json")
COMPARATOR_REGISTER = Path("comparators/OC_1_3_3_MODERN_SCIENCE_SUPERIORITY_REGISTER.json")
CERBERUS_FINDINGS = Path("releases/oc_core_1_3/editorial/OC_CORE_1_3_CERBERUS_REVIEW_FINDINGS_latest.json")
CERBERUS_ACCEPTANCE = Path("releases/oc_core_1_3/editorial/OC_CORE_1_3_CERBERUS_ACCEPTANCE_CERT_latest.json")
SYMBOL_DECL_RE = re.compile(
    r"^\s*(?:def|theorem|lemma|axiom|constant|inductive|structure)\s+([A-Za-z_][A-Za-z0-9_'.]*)",
    re.MULTILINE,
)


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


def split_ref_path(ref: str) -> str:
    return str(ref).split("::", 1)[0].strip()


def split_ref_symbol(ref: str) -> str:
    return str(ref).split("::", 1)[1].strip() if "::" in str(ref) else ""


def declared_symbols(path: Path) -> set[str]:
    if not path.exists() or not path.is_file():
        return set()
    return set(SYMBOL_DECL_RE.findall(path.read_text(encoding="utf-8", errors="replace")))


def lean_ref_bound(root: Path, ref: str) -> bool:
    path = root / split_ref_path(ref)
    symbol = split_ref_symbol(ref)
    return path.exists() and bool(symbol) and symbol in declared_symbols(path)


def finite_case_rows_by_id(root: Path) -> dict[str, dict[str, Any]]:
    finite = read_json(root / FINITE_CHECK_REPORT)
    rows = finite.get("rows", [])
    if not isinstance(rows, list):
        return {}
    return {
        str(row.get("case_id")): row
        for row in rows
        if isinstance(row, dict) and row.get("case_id")
    }


def finite_refs_status(root: Path, refs: list[Any]) -> dict[str, Any]:
    finite_rows = finite_case_rows_by_id(root)
    rows = []
    for ref in refs:
        case_id = str(ref)
        row = finite_rows.get(case_id)
        rows.append({"case_id": case_id, "exists": bool(row), "passed": bool(row and row.get("passed") is True)})
    return {
        "ref_total": len(rows),
        "existing_ref_total": sum(1 for row in rows if row["exists"]),
        "passing_ref_total": sum(1 for row in rows if row["passed"]),
        "missing_ref_total": sum(1 for row in rows if not row["exists"]),
        "failing_ref_total": sum(1 for row in rows if row["exists"] and not row["passed"]),
        "rows": rows,
        "status": "PASS" if rows and all(row["passed"] for row in rows) else "FAIL",
    }


def refs_status(root: Path, refs: list[Any]) -> dict[str, Any]:
    rows = []
    for ref in refs:
        ref_path = split_ref_path(str(ref))
        rows.append(
            {
                "ref": str(ref),
                "path": ref_path,
                "exists": bool(ref_path) and (root / ref_path).exists(),
            }
        )
    return {
        "ref_total": len(rows),
        "existing_ref_total": sum(1 for row in rows if row["exists"]),
        "missing_ref_total": sum(1 for row in rows if not row["exists"]),
        "rows": rows,
        "status": "PASS" if rows and all(row["exists"] for row in rows) else "FAIL",
    }


def write_json_artifact(root: Path, rel_path: Path, payload: dict[str, Any]) -> str:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stable_json(payload), encoding="utf-8")
    return rel(root, path)


def stable_generated_at(root: Path, rel_path: Path) -> str:
    existing = read_json(root / rel_path).get("generated_at")
    return existing if isinstance(existing, str) and existing else utc_now()


def normalize_problem_row(row: dict[str, Any], defaults: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(row)
    normalized.setdefault("why_it_failed", defaults.get("why_it_failed", "The row is open because its parent TOE validator condition is not satisfied."))
    normalized.setdefault("repair_strategy", defaults.get("repair_strategy", "Execute the associated capability lane and rerun the strict final TOE validator."))
    normalized.setdefault("required_capability", defaults.get("required_capability", normalized.get("owner_capability", "Research/TOEClosureFactory")))
    normalized.setdefault("execution_command", defaults.get("execution_command", [sys.executable, "tools/oc133_toe_closure_factory.py", "--execute", "--write", "--until-final-pass"]))
    normalized.setdefault("pass_predicate", defaults.get("pass_predicate", normalized.get("closure_condition", "Strict final TOE validator returns PASS.")))
    normalized.setdefault("next_escalation", defaults.get("next_escalation", "Create the next source-bound capability work order; do not promote r017 from this row."))
    return normalized


def explainability_missing_ids(payloads: list[dict[str, Any]]) -> list[str]:
    missing: list[str] = []
    for payload in payloads:
        for index, row in enumerate(payload.get("rows", []) or [], start=1):
            if not isinstance(row, dict):
                continue
            if row.get("status") == "PASS":
                continue
            absent = [
                field
                for field in EXPLAINABILITY_FIELDS
                if row.get(field) is None or row.get(field) == "" or row.get(field) == []
            ]
            if absent:
                missing.append(
                    str(
                        row.get("problem_id")
                        or row.get("capability_backlog_id")
                        or row.get("subwork_order_id")
                        or row.get("delta_trace_id")
                        or f"{payload.get('schema_id', 'payload')}::{index}"
                    )
                )
    return missing


def current_validator_errors(root: Path) -> list[str]:
    parts = current_validator_error_parts(root)
    return parts["science_errors"] + parts["cerberus_errors"]


def validator_error_total(parts: dict[str, list[str]]) -> int:
    return len(parts.get("science_errors", [])) + len(parts.get("cerberus_errors", []))


def git_head(root: Path) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=root,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=60,
    )
    return completed.stdout.strip() if completed.returncode == 0 else "UNKNOWN"


def closure_frontier_hash(root: Path, validator_parts: dict[str, list[str]] | None = None) -> str:
    return artifact_hash(
        {
            "validator_parts": validator_parts or current_validator_error_parts(root),
            "tracked_status_rows": git_status_rows(root),
        }
    )


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
            normalize_problem_row(
                {
                    "subwork_order_id": f"R017-COMPARATOR-COVERAGE-GAP-{index:03d}",
                    "lane_id": "MODERN_SCIENCE_COMPARATOR_SUPERIORITY",
                    "status": "OPEN",
                    "domain": domain,
                    "finding_class": "MODERN_SCIENCE_COMPARATOR_SUPERIORITY",
                    "root_cause_class": "BROAD_COMPARATOR_COVERAGE_GAP",
                    "required_capability": "Research/PriorArt",
                    "why_it_failed": "Broad superiority is blocked because current evidence is benchmark-scoped and does not cover all of modern science.",
                    "repair_strategy": "Bind a source-backed comparator row, evidence pack, baseline, uncertainty/fairness statement, and falsifier for this coverage gap.",
                    "closure_condition": "coverage_extends_to_all_of_modern_science can only turn true after every required coverage gap has source-backed comparator support.",
                    "source_refs": [str(COMPARATOR_REGISTER)],
                    "blockers": blockers,
                },
                {
                    "execution_command": [sys.executable, "tools/oc133_toe_closure_factory.py", "--execute-capability-lane", "MODERN_SCIENCE_COMPARATOR_SUPERIORITY", "--write"],
                    "pass_predicate": "Broad modern-science comparator coverage predicate passes without upgrading benchmark-scoped evidence by wording.",
                    "next_escalation": "Acquire or bind source-backed comparator evidence for this gap through governed open-data surfaces.",
                },
            )
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
            normalize_problem_row(
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
                },
                {
                    "execution_command": [sys.executable, "tools/oc133_toe_closure_factory.py", "--execute-capability-lane", lane_id, "--write"],
                    "pass_predicate": "Projection lane row passes static validation and strict final TOE projection validator error disappears.",
                    "next_escalation": "Materialize source-grounded lane artifacts; if support is absent, keep the projection fail-closed and add source-gap records.",
                },
            )
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
            normalize_problem_row(
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
                },
                {
                    "execution_command": [sys.executable, "tools/oc133_toe_closure_factory.py", "--execute-capability-lane", "GRAND_TOE_CLAIM_LEDGER_EVIDENCE", "--write"],
                    "pass_predicate": "Grand promotion contract verdict PASS, finite checks PASS, empirical pack PASS, comparator pack PASS.",
                    "next_escalation": "Run the grand formal-science capability and inspect finite/promotion dependency diagnostics.",
                },
            )
        )
    for failed in failed_finite_rows(root):
        case_id = str(failed.get("case_id") or "UNKNOWN")
        output.append(
            normalize_problem_row(
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
                },
                {
                    "execution_command": [sys.executable, "tools/oc133_toe_closure_factory.py", "--execute-capability-lane", "GRAND_TOE_CLAIM_LEDGER_EVIDENCE", "--write"],
                    "pass_predicate": f"Finite model case {case_id} passes and remains bound to a valid theorem/proof route.",
                    "next_escalation": "If the expectation is scientifically wrong, demote the promoted claim; if the model is wrong, repair the finite fixture and rerun checks.",
                },
            )
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
                },
            ]
        )
        rows[-1] = normalize_problem_row(
            rows[-1],
            {
                "execution_command": lane_registry_by_id()["CERBERUS_RELEASE_REVIEW_GATE"]["execution_command"],
                "pass_predicate": "Cerberus fingerprints bind to current HEAD, acceptance PASS, LLM gate PASS, and open defect findings zero.",
                "next_escalation": "Wait until science validator is green, then run canonical Cerberus full gate.",
            },
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
        "toe_problem_explainability_status": "PASS" if not explainability_missing_ids([{"schema_id": "OC133_TOE_LANE_SUBWORK_ORDERS_v1", "rows": rows}]) else "FAIL",
        "explainability_missing_ids": explainability_missing_ids([{"schema_id": "OC133_TOE_LANE_SUBWORK_ORDERS_v1", "rows": rows}]),
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
        "toe_problem_explainability_status": "PASS" if not incomplete else "FAIL",
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
            normalize_problem_row(
                {
                    "capability_backlog_id": f"R017-CAPABILITY-{len(rows) + 1:03d}",
                    "required_capability": row.get("required_capability"),
                    "root_cause_class": row.get("root_cause_class"),
                    "status": "OPEN",
                    "why_needed": row.get("why_it_failed"),
                    "next_action": row.get("repair_strategy"),
                    "why_it_failed": row.get("why_it_failed"),
                    "repair_strategy": row.get("repair_strategy"),
                    "execution_command": row.get("execution_command"),
                    "pass_predicate": row.get("pass_predicate"),
                    "source_problem_id": row.get("problem_id"),
                },
                {
                    "next_escalation": row.get("next_escalation"),
                },
            )
        )
    for row in subwork_orders.get("rows", []):
        key = (str(row.get("required_capability")), str(row.get("subwork_order_id")))
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            normalize_problem_row(
                {
                    "capability_backlog_id": f"R017-CAPABILITY-{len(rows) + 1:03d}",
                    "required_capability": row.get("required_capability"),
                    "root_cause_class": row.get("finding_class"),
                    "status": row.get("status", "OPEN"),
                    "why_needed": row.get("why_it_failed"),
                    "next_action": row.get("repair_strategy"),
                    "why_it_failed": row.get("why_it_failed"),
                    "repair_strategy": row.get("repair_strategy"),
                    "execution_command": [sys.executable, "tools/oc133_toe_closure_factory.py", "--execute-capability-lane", row.get("lane_id", ""), "--write"],
                    "pass_predicate": row.get("closure_condition"),
                    "source_subwork_order_id": row.get("subwork_order_id"),
                },
                {
                    "next_escalation": row.get("next_escalation"),
                },
            )
        )
    missing = explainability_missing_ids([{"schema_id": "OC133_TOE_CAPABILITY_BACKLOG_v1", "rows": rows}])
    payload = {
        "schema_id": "OC133_TOE_CAPABILITY_BACKLOG_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": generated_at or utc_now(),
        "status": "OPEN" if rows else "PASS",
        "capability_total": len(rows),
        "open_capability_total": sum(1 for row in rows if row.get("status") == "OPEN"),
        "toe_problem_explainability_status": "PASS" if not missing else "FAIL",
        "explainability_missing_total": len(missing),
        "explainability_missing_ids": missing,
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
            normalize_problem_row(
                {
                    "delta_trace_id": f"R017-VALIDATOR-DELTA-{index:03d}",
                    "purpose": step.get("purpose"),
                    "status": step.get("status"),
                    "before_validator_error_total": result.get("before_validator_error_total"),
                    "after_validator_error_total": result.get("after_validator_error_total"),
                    "validator_error_delta": result.get("validator_error_delta"),
                    "why_it_failed": "This supervisor step did not produce a strict final TOE PASS." if step.get("status") != "PASS" else "Step passed.",
                    "repair_strategy": "Use the validator delta and capability backlog to choose the next executable lane.",
                    "required_capability": "Research/TOEClosureFactory",
                    "execution_command": [sys.executable, "tools/oc133_toe_closure_factory.py", "--execute", "--write", "--until-final-pass"],
                    "pass_predicate": "The step reduces validator errors or the strict final TOE validator returns PASS.",
                    "next_escalation": "If validator_error_delta is zero, generate or execute capability backlog rather than stopping.",
                },
                {},
            )
        )
    no_progress = any((row.get("validator_error_delta") in (0, None)) and row.get("status") not in {"PASS"} for row in rows)
    missing = explainability_missing_ids([{"schema_id": "OC133_TOE_VALIDATOR_DELTA_TRACE_v1", "rows": rows}])
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
        "toe_problem_explainability_status": "PASS" if not missing else "FAIL",
        "explainability_missing_total": len(missing),
        "explainability_missing_ids": missing,
        "rows": rows,
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def build_problem_explainability_gate(payloads: list[dict[str, Any]], *, generated_at: str | None = None) -> dict[str, Any]:
    missing = explainability_missing_ids(payloads)
    payload = {
        "schema_id": "OC133_TOE_PROBLEM_EXPLAINABILITY_GATE_v1",
        "generated_at": generated_at or utc_now(),
        "status": "PASS" if not missing else "FAIL",
        "toe_problem_explainability_status": "PASS" if not missing else "FAIL",
        "checked_payload_total": len(payloads),
        "missing_total": len(missing),
        "missing_ids": missing,
        "required_fields": EXPLAINABILITY_FIELDS,
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def lane_execution_base(lane_id: str) -> Path:
    return LANE_EXECUTION_DIR / lane_id


def projection_lane_target_rel(lane_id: str) -> Path:
    return FINAL_TOE_PROJECTION_LANE_TARGETS[lane_id].relative_to(REPO_ROOT)


PROJECTION_SOURCE_REFS = [
    "claims/CLAIM_LEDGER_1_3_3.json",
    "claims/CLAIM_LEDGER_FULL.json",
    "proofs/THEOREM_REGISTRY_1_3_3.json",
    "proofs/THEOREM_INVENTORY_1_3_3.json",
    "reports/OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.json",
    "reports/OC_CORE_1_3_3_GRAND_EMPIRICAL_REPORT.json",
    "reports/OC_CORE_1_3_3_MODERN_SCIENCE_COVERAGE_LANE_QUEUE.json",
    "releases/oc_core_1_3/editorial/OC_CORE_1_3_PRACTICAL_UTILITY_ATLAS_latest.json",
    "releases/oc_core_1_3/editorial/OC_CORE_1_3_UNIFIED_SYNTHESIS_latest.json",
]

PROJECTION_LANE_TERMS = {
    "AI": ["ai", "artificial intelligence", "agentic", "machine learning", "llm"],
    "ENTERPRISE_ARCHITECTURE": ["enterprise architecture", "enterprise-architecture", "architecture case", "operational metric"],
}


def text_contains_lane_terms(value: Any, lane_id: str) -> bool:
    text = json.dumps(value, ensure_ascii=False).lower()
    for term in PROJECTION_LANE_TERMS[lane_id]:
        normalized = term.lower()
        if len(normalized) <= 3:
            if re.search(rf"\b{re.escape(normalized)}\b", text):
                return True
            continue
        if normalized in text:
            return True
    return False


def theorem_rows_by_id(root: Path) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for ref in ["proofs/THEOREM_REGISTRY_1_3_3.json", "proofs/THEOREM_INVENTORY_1_3_3.json"]:
        payload = read_json(root / ref)
        for row in payload.get("rows", []) or []:
            if isinstance(row, dict) and row.get("theorem_id"):
                rows[str(row["theorem_id"])] = row
    return rows


def finite_case_ids_by_theorem(root: Path) -> dict[str, list[str]]:
    payload = read_json(root / FINITE_CHECK_REPORT)
    rows: dict[str, list[str]] = {}
    for row in payload.get("rows", []) or []:
        if not isinstance(row, dict) or not row.get("theorem_id") or not row.get("case_id"):
            continue
        rows.setdefault(str(row["theorem_id"]), []).append(str(row["case_id"]))
    return {key: sorted(set(value)) for key, value in rows.items()}


def rows_from_payload(value: Any, *, path: str = "$") -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            rows.extend(rows_from_payload(child, path=f"{path}.{key}"))
        return rows
    if isinstance(value, list):
        if all(isinstance(item, dict) for item in value):
            for index, item in enumerate(value, start=1):
                row = dict(item)
                row.setdefault("_source_json_path", f"{path}[{index}]")
                rows.append(row)
        for index, child in enumerate(value, start=1):
            rows.extend(rows_from_payload(child, path=f"{path}[{index}]"))
    return rows


def projection_blocker_row(row: dict[str, Any]) -> bool:
    claim_id = str(row.get("claim_id") or "")
    public_scope = str(row.get("public_claim_scope") or row.get("claim") or "")
    public_status = str(row.get("public_status") or row.get("status") or "")
    return (
        "BLOCKER" in claim_id
        or "not final toe evidence" in public_scope.lower()
        or "future_research" in public_status.lower()
        or "fail_closed" in public_status.lower()
    )


def build_projection_row_from_claim(root: Path, lane_id: str, source_row: dict[str, Any], index: int) -> dict[str, Any]:
    theorem_rows = theorem_rows_by_id(root)
    finite_rows = finite_case_ids_by_theorem(root)
    claim_id = str(source_row.get("claim_id") or f"OC133-{lane_id}-MINED-{index:03d}")
    theorem = theorem_rows.get(claim_id, {})
    formal_refs = [
        ref
        for ref in [
            source_row.get("evidence_ref"),
            theorem.get("proof_sheet_ref"),
            theorem.get("evidence_ref"),
        ]
        if isinstance(ref, str) and ref
    ]
    lean_refs = [ref for ref in [theorem.get("lean_ref")] if isinstance(ref, str) and ref]
    finite_case_refs = finite_rows.get(claim_id, [])
    return {
        "projection_id": f"OC133-FINAL-TOE-{lane_id}-{index:03d}",
        "claim_id": claim_id,
        "public_claim_scope": str(
            source_row.get("claim")
            or source_row.get("public_claim_scope")
            or source_row.get("title")
            or source_row.get("domain_title")
            or source_row.get("phenomenon_label")
            or source_row.get("problem_class")
            or source_row.get("requirement")
            or source_row.get("formula_or_model")
            or theorem.get("public_claim_boundary")
            or ""
        ),
        "theorem_or_formal_boundary_refs": sorted(set(formal_refs)),
        "lean_refs": sorted(set(lean_refs)),
        "finite_case_refs": finite_case_refs,
        "evidence_or_simulation_refs": [
            ref
            for ref in [
                source_row.get("evidence_ref"),
                "reports/OC_CORE_1_3_3_GRAND_EMPIRICAL_REPORT.json",
                "validation/heldout/grand_science_evidence_registry.json",
            ]
            if isinstance(ref, str) and ref
        ],
        "comparator_refs": ["comparators/OC_1_3_3_MODERN_SCIENCE_SUPERIORITY_REGISTER.json"],
        "falsifier_refs": ["validation/target_blind/OC133_TARGET_BLIND_PREDICTION_TABLE.json"],
        "source_refs": ["claims/CLAIM_LEDGER_1_3_3.json", "proofs/THEOREM_REGISTRY_1_3_3.json", "proofs/FINITE_MODEL_CHECKS_1_3_3.json"],
        "source_claim_public_status": source_row.get("public_status"),
        "source_json_path": source_row.get("_source_json_path"),
        "closure_verdict": "FAIL_CLOSED",
    }


def projection_row_support_checks(root: Path, row: dict[str, Any]) -> dict[str, bool]:
    lean_refs = list(row.get("lean_refs") or [])
    return {
        "claim_id_present": bool(row.get("claim_id")),
        "public_claim_scope_present": bool(row.get("public_claim_scope")),
        "claim_not_blocker": not projection_blocker_row(row),
        "formal_refs_exist": refs_status(root, list(row.get("theorem_or_formal_boundary_refs") or []))["status"] == "PASS",
        "lean_refs_exist": bool(lean_refs) and all(lean_ref_bound(root, str(ref)) for ref in lean_refs),
        "finite_case_refs_present": finite_refs_status(root, list(row.get("finite_case_refs") or []))["status"] == "PASS",
        "evidence_refs_exist": refs_status(root, list(row.get("evidence_or_simulation_refs") or []))["status"] == "PASS",
        "comparator_refs_exist": refs_status(root, list(row.get("comparator_refs") or []))["status"] == "PASS",
        "falsifier_refs_exist": refs_status(root, list(row.get("falsifier_refs") or []))["status"] == "PASS",
    }


def projection_lane_prefix(lane_id: str) -> str:
    return "AI" if lane_id == "AI" else "EA"


def projection_source_intake_execution_rel(lane_id: str, work_order_id: str) -> Path:
    prefix = projection_lane_prefix(lane_id)
    short_id = work_order_id
    short_id = short_id.replace("R017-ENTERPRISE_ARCHITECTURE-SOURCE-INTAKE-", "R017-EA-SI-")
    short_id = short_id.replace("R017-AI-SOURCE-INTAKE-", "R017-AI-SI-")
    return lane_execution_base(lane_id) / "source_intake_executions" / f"{short_id}.json"


def lane_id_from_projection_work_order(work_order_id: str) -> str | None:
    if work_order_id.startswith("R017-AI-"):
        return "AI"
    if work_order_id.startswith("R017-ENTERPRISE_ARCHITECTURE-"):
        return "ENTERPRISE_ARCHITECTURE"
    return None


PROJECTION_SUPPORT_WORK = {
    "source_mined_candidate_available": (
        "SOURCE_DISCOVERY",
        "source_grounded_non_blocker_candidate",
        "Mine or create a canonical non-blocker source claim for this projection lane before any public PASS row may be written.",
    ),
    "claim_not_blocker": (
        "CLAIM_SCOPE",
        "non_blocker_public_claim_scope",
        "Replace blocker/future-research scope with a source-supported promoted claim scope or keep the lane fail-closed.",
    ),
    "formal_refs_exist": (
        "FORMAL_BOUNDARY",
        "theorem_or_formal_boundary_refs",
        "Bind the projection claim to an existing proof sheet, theorem record, or explicit formal boundary artifact.",
    ),
    "lean_refs_exist": (
        "LEAN_BINDING",
        "lean_refs",
        "Bind the projection to an existing Lean declaration and symbol-level reference.",
    ),
    "finite_case_refs_present": (
        "FINITE_CASE_BINDING",
        "finite_case_refs",
        "Bind the projection to existing finite model case ids that pass the finite-check report.",
    ),
    "evidence_refs_exist": (
        "EVIDENCE_OR_SIMULATION",
        "evidence_or_simulation_refs",
        "Bind replayable evidence, simulation, or benchmark artifacts for the projection claim.",
    ),
    "comparator_refs_exist": (
        "COMPARATOR_BASELINE",
        "comparator_refs",
        "Bind comparator baseline rows that are valid for the public claim scope.",
    ),
    "falsifier_refs_exist": (
        "FALSIFIER",
        "falsifier_refs",
        "Bind falsifier rows that state what would narrow or invalidate the projection claim.",
    ),
}


def projection_support_pack_payload(
    root: Path,
    lane_id: str,
    source_mining: dict[str, Any],
    *,
    generated_at: str,
    work_order_id: str | None = None,
) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    for key in ["candidate_rows", "rejected_candidate_rows"]:
        value = source_mining.get(key)
        if isinstance(value, list):
            candidates.extend(row for row in value if isinstance(row, dict))
    theorem_rows = theorem_rows_by_id(root)
    finite_rows = finite_case_ids_by_theorem(root)
    support_rows: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidates, start=1):
        claim_id = str(candidate.get("claim_id") or "")
        theorem = theorem_rows.get(claim_id, {})
        rebuilt = dict(candidate)
        if theorem:
            rebuilt["theorem_or_formal_boundary_refs"] = sorted(
                set(
                    list(rebuilt.get("theorem_or_formal_boundary_refs") or [])
                    + [
                        ref
                        for ref in [theorem.get("proof_sheet_ref"), theorem.get("evidence_ref")]
                        if isinstance(ref, str) and ref
                    ]
                )
            )
            if theorem.get("lean_ref"):
                rebuilt["lean_refs"] = sorted(set(list(rebuilt.get("lean_refs") or []) + [str(theorem["lean_ref"])]))
            rebuilt["finite_case_refs"] = sorted(set(list(rebuilt.get("finite_case_refs") or []) + finite_rows.get(claim_id, [])))
        checks = projection_row_support_checks(root, rebuilt)
        missing = [key for key, passed in checks.items() if passed is not True]
        support_rows.append(
            {
                "candidate_index": index,
                "projection_id": rebuilt.get("projection_id"),
                "claim_id": claim_id,
                "public_claim_scope": rebuilt.get("public_claim_scope"),
                "source_json_path": rebuilt.get("source_json_path"),
                "theorem_native_match": bool(theorem),
                "support_status": "PASS" if not missing else "SOURCE_GAP_OPEN",
                "missing_support_keys": missing,
                "support_checks": checks,
                "candidate_row": rebuilt,
                "why_it_failed": "Candidate lacks native theorem/Lean/finite/evidence/comparator/falsifier support." if missing else "Candidate is fully supported for guarded writer validation.",
                "repair_strategy": "Bind native theorem/proof, Lean declaration, passing finite witness, evidence, comparator, and falsifier refs before promotion.",
            }
        )
    support_pass_rows = [row for row in support_rows if row.get("support_status") == "PASS"]
    payload = {
        "schema_id": "OC133_TOE_PROJECTION_SUPPORT_PACK_v1",
        "generated_at": generated_at,
        "lane_id": lane_id,
        "work_order_id": work_order_id,
        "status": "PASS" if support_pass_rows else "SOURCE_GAP_OPEN",
        "candidate_total": len(candidates),
        "support_pass_candidate_total": len(support_pass_rows),
        "support_gap_candidate_total": len(support_rows) - len(support_pass_rows),
        "why_it_failed": "No projection candidate has native theorem/Lean/finite support sufficient for final TOE promotion." if not support_pass_rows else "At least one projection candidate is fully source-bound.",
        "repair_strategy": "Promote only support_pass rows through the guarded writer; route all source gaps back to the research corpus.",
        "required_capability": "Research/AIProjection" if lane_id == "AI" else "Research/EnterpriseArchitectureProjection",
        "execution_command": [sys.executable, "tools/oc133_toe_closure_factory.py", "--execute-source-intake-work-order", work_order_id or f"R017-{lane_id}-SOURCE-INTAKE", "--write"],
        "pass_predicate": "support_pass_candidate_total > 0 and strict final TOE projection validator errors disappear for this lane.",
        "next_escalation": "If no support-pass candidate exists, create a native theorem/proof/Lean/finite route or keep the lane blocked.",
        "rows": support_rows,
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def build_projection_source_intake_execution(root: Path, work_order_id: str) -> dict[str, Any]:
    lane_id = lane_id_from_projection_work_order(work_order_id)
    if not lane_id:
        payload = {
            "schema_id": "OC133_TOE_PROJECTION_SOURCE_INTAKE_EXECUTION_v1",
            "generated_at": utc_now(),
            "work_order_id": work_order_id,
            "status": "FAIL_CLOSED",
            "why_it_failed": "Work order id does not identify the AI or Enterprise Architecture projection lane.",
            "repair_strategy": "Use an R017-AI-* or R017-ENTERPRISE_ARCHITECTURE-* source-intake work order id.",
            "required_capability": "Research/TOEClosureFactory",
            "execution_command": [sys.executable, "tools/oc133_toe_closure_factory.py", "--execute-source-intake-work-order", work_order_id, "--write"],
            "pass_predicate": "Known projection work order id maps to a lane and produces a support pack.",
            "next_escalation": "Regenerate source-intake work orders for the projection lanes.",
            "rows": [],
        }
        payload["artifact_hash"] = artifact_hash(payload)
        return payload
    prefix = projection_lane_prefix(lane_id)
    base = lane_execution_base(lane_id)
    artifact_rel = projection_source_intake_execution_rel(lane_id, work_order_id)
    generated_at = stable_generated_at(root, artifact_rel)
    source_mining = mine_projection_lane_sources(root, lane_id, generated_at=generated_at)
    support_pack = projection_support_pack_payload(root, lane_id, source_mining, generated_at=generated_at, work_order_id=work_order_id)
    support_pack_rel = base / f"OC133_{prefix}_PROJECTION_SUPPORT_PACK.json"
    support_pack_ref = write_json_artifact(root, support_pack_rel, support_pack)
    matching_rows = []
    source_intake_path = base / f"OC133_{prefix}_SOURCE_INTAKE_WORK_ORDERS.json"
    source_intake = read_json(root / source_intake_path)
    for row in source_intake.get("rows", []) or []:
        if isinstance(row, dict) and row.get("work_order_id") == work_order_id:
            matching_rows.append(row)
    payload = {
        "schema_id": "OC133_TOE_PROJECTION_SOURCE_INTAKE_EXECUTION_v1",
        "generated_at": generated_at,
        "lane_id": lane_id,
        "work_order_id": work_order_id,
        "status": "PASS" if support_pack.get("status") == "PASS" else "SOURCE_GAP_OPEN",
        "source_intake_row_found": bool(matching_rows),
        "support_pack_ref": support_pack_ref,
        "support_pack_status": support_pack.get("status"),
        "candidate_total": support_pack.get("candidate_total"),
        "support_pass_candidate_total": support_pack.get("support_pass_candidate_total"),
        "why_it_failed": "Source-intake execution did not find a fully source-bound projection candidate." if support_pack.get("status") != "PASS" else "Source-intake execution found a fully source-bound candidate.",
        "repair_strategy": "Close the missing support keys in the support pack and rerun the guarded projection writer.",
        "required_capability": "Research/AIProjection" if lane_id == "AI" else "Research/EnterpriseArchitectureProjection",
        "execution_command": [sys.executable, "tools/oc133_toe_closure_factory.py", "--execute-source-intake-work-order", work_order_id, "--write"],
        "pass_predicate": "support_pack_status == PASS and the guarded writer validates the candidate without remaining strict validator errors.",
        "next_escalation": "Create theorem/proof/Lean/finite/evidence/comparator/falsifier artifacts for the lane; do not manually flip final_toe_support_allowed.",
        "source_intake_rows": matching_rows,
        "rows": support_pack.get("rows", []),
    }
    payload["artifact_hash"] = artifact_hash(payload)
    payload["artifact_ref"] = rel(root, root / artifact_rel)
    write_json_artifact(root, artifact_rel, payload)
    return payload


def build_projection_source_intake_work_orders(
    root: Path,
    lane_id: str,
    source_mining: dict[str, Any],
    support_checks: dict[str, bool],
    *,
    generated_at: str,
) -> dict[str, Any]:
    is_ai = lane_id == "AI"
    capability = "Research/AIProjection" if is_ai else "Research/EnterpriseArchitectureProjection"
    finding_class = "AI_DOMAIN_TOE_PROJECTION_LANE" if is_ai else "ENTERPRISE_ARCHITECTURE_DOMAIN_TOE_PROJECTION_LANE"
    candidates = []
    for key in ["candidate_rows", "rejected_candidate_rows"]:
        value = source_mining.get(key)
        if isinstance(value, list):
            candidates.extend(row for row in value if isinstance(row, dict))
    candidate = candidates[0] if candidates else {}
    candidate_id = str(candidate.get("projection_id") or f"OC133-FINAL-TOE-{lane_id}-SOURCE-GAP")
    candidate_scope = str(candidate.get("public_claim_scope") or "NO_SOURCE_CANDIDATE_BOUND")
    missing_keys = [
        key
        for key, value in support_checks.items()
        if key in PROJECTION_SUPPORT_WORK and value is not True
    ]
    rows: list[dict[str, Any]] = []
    if not candidates and "source_mined_candidate_available" not in missing_keys:
        missing_keys.insert(0, "source_mined_candidate_available")
    for index, key in enumerate(missing_keys, start=1):
        step_id, required_artifact, strategy = PROJECTION_SUPPORT_WORK[key]
        rows.append(
            normalize_problem_row(
                {
                    "work_order_id": f"R017-{lane_id}-SOURCE-INTAKE-{step_id}-{index:03d}",
                    "subwork_order_id": f"R017-{lane_id}-SOURCE-INTAKE-{step_id}-{index:03d}",
                    "lane_id": lane_id,
                    "finding_class": finding_class,
                    "status": "OPEN",
                    "candidate_projection_id": candidate_id,
                    "candidate_claim_id": candidate.get("claim_id"),
                    "candidate_public_claim_scope": candidate_scope,
                    "candidate_source_json_path": candidate.get("source_json_path"),
                    "missing_support_key": key,
                    "required_artifact": required_artifact,
                    "required_artifacts": [required_artifact],
                    "source_refs": [str(projection_lane_target_rel(lane_id)), *PROJECTION_SOURCE_REFS],
                    "root_cause_class": "MISSING_EXECUTABLE_AI_TOE_PROJECTION_SUPPORT" if is_ai else "MISSING_EXECUTABLE_EA_TOE_PROJECTION_SUPPORT",
                    "why_it_failed": f"{lane_id} projection cannot pass because `{key}` is false for the best current source candidate.",
                    "repair_strategy": strategy,
                    "required_capability": capability,
                    "closure_condition": "Projection lane may PASS only after claim scope, formal refs, Lean refs, finite refs, evidence, comparator, and falsifier refs are all bound and non-blocker.",
                    "fake_closure_rejected": True,
                },
                {
                    "execution_command": [sys.executable, "tools/oc133_toe_closure_factory.py", "--execute-capability-lane", lane_id, "--write"],
                    "pass_predicate": f"support_checks.{key} == true and the strict final TOE projection validator no longer emits this lane error.",
                    "next_escalation": "Route this source-intake item to the research corpus; do not write a PASS projection row until static validation succeeds.",
                },
            )
        )
    payload = {
        "schema_id": "OC133_TOE_PROJECTION_SOURCE_INTAKE_WORK_ORDERS_v1",
        "generated_at": generated_at,
        "lane_id": lane_id,
        "status": "PASS" if not rows else "OPEN",
        "source_candidate_total": len(candidates),
        "source_intake_work_order_total": len(rows),
        "open_work_order_total": len(rows),
        "missing_support_keys": missing_keys,
        "why_it_failed": "Projection source intake has open missing-support classes." if rows else "Projection source intake has no missing-support classes.",
        "repair_strategy": "Close every source-intake row from canonical research sources before guarded projection promotion.",
        "required_capability": capability,
        "execution_command": [sys.executable, "tools/oc133_toe_closure_factory.py", "--execute-capability-lane", lane_id, "--write"],
        "pass_predicate": "source_intake_work_order_total == 0 and guarded writer predicates all pass.",
        "next_escalation": "Create narrower source-mining, proof, finite, comparator, or falsifier work items if this lane still produces zero validator delta.",
        "rows": rows,
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def mine_projection_lane_sources(root: Path, lane_id: str, *, generated_at: str) -> dict[str, Any]:
    scanned_rows: list[dict[str, Any]] = []
    candidate_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = []
    for ref in PROJECTION_SOURCE_REFS:
        payload = read_json(root / ref)
        raw_rows = rows_from_payload(payload)
        matched = [row for row in raw_rows if isinstance(row, dict) and text_contains_lane_terms(row, lane_id)]
        scanned_rows.append({"source_ref": ref, "row_total": len(raw_rows), "matched_row_total": len(matched)})
        for row in matched:
            candidate = build_projection_row_from_claim(root, lane_id, row, len(candidate_rows) + len(rejected_rows) + 1)
            checks = projection_row_support_checks(root, candidate)
            candidate["support_checks"] = checks
            candidate["closure_verdict"] = "PASS" if all(checks.values()) else "FAIL_CLOSED"
            if all(checks.values()):
                candidate_rows.append(candidate)
            else:
                rejected_rows.append(candidate)
    payload = {
        "schema_id": "OC133_TOE_PROJECTION_SOURCE_MINING_REPORT_v1",
        "generated_at": generated_at,
        "lane_id": lane_id,
        "status": "PASS" if candidate_rows else "SOURCE_GAP_OPEN",
        "source_ref_total": len(PROJECTION_SOURCE_REFS),
        "candidate_total": len(candidate_rows),
        "rejected_candidate_total": len(rejected_rows),
        "scanned_sources": scanned_rows,
        "candidate_rows": candidate_rows,
        "rejected_candidate_rows": rejected_rows[:20],
        "why_it_failed": "No canonical non-blocker projection row has complete claim/formal/Lean/finite/evidence/comparator/falsifier support." if not candidate_rows else "At least one fully supported projection row is available.",
        "repair_strategy": "Create source-bound AI/EA claim, theorem/proof boundary, Lean/finite witness, evidence pack, comparator row, and falsifier before guarded promotion.",
        "required_capability": "Research/AIProjection" if lane_id == "AI" else "Research/EnterpriseArchitectureProjection",
        "execution_command": [sys.executable, "tools/oc133_toe_closure_factory.py", "--execute-capability-lane", lane_id, "--write"],
        "pass_predicate": "candidate_total > 0 and every candidate support predicate is true.",
        "next_escalation": "Route missing candidate support to the research corpus rather than manually editing the projection lane.",
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def build_projection_lane_capability_artifacts(root: Path, lane_id: str) -> dict[str, Any]:
    target_rel = projection_lane_target_rel(lane_id)
    source_payload = read_json(root / target_rel)
    rows = source_payload.get("rows", [])
    rows = rows if isinstance(rows, list) else []
    first_row = rows[0] if rows and isinstance(rows[0], dict) else {}
    is_ai = lane_id == "AI"
    lane_title = "Artificial intelligence and agentic-system TOE projection lane" if is_ai else "Enterprise architecture and organizational-systems TOE projection lane"
    capability = "Research/AIProjection" if is_ai else "Research/EnterpriseArchitectureProjection"
    prefix = "AI" if is_ai else "EA"
    formal_refs = list(first_row.get("theorem_or_formal_boundary_refs") or [])
    evidence_refs = list(first_row.get("evidence_or_simulation_refs") or [])
    comparator_refs = list(first_row.get("comparator_refs") or [])
    falsifier_refs = list(first_row.get("falsifier_refs") or [])
    lean_refs = list(first_row.get("lean_refs") or [])
    finite_case_refs = list(first_row.get("finite_case_refs") or [])
    claim_id = str(first_row.get("claim_id") or "")
    public_scope = str(first_row.get("public_claim_scope") or "")
    blocker_claim = projection_blocker_row(first_row)

    base = lane_execution_base(lane_id)
    generated_at = stable_generated_at(root, base / f"OC133_{prefix}_PROJECTION_CAPABILITY_REPORT.json")
    source_mining = mine_projection_lane_sources(root, lane_id, generated_at=generated_at)
    mined_rows = source_mining.get("candidate_rows", []) if isinstance(source_mining.get("candidate_rows"), list) else []
    if mined_rows:
        rows = mined_rows
        first_row = rows[0]
        formal_refs = list(first_row.get("theorem_or_formal_boundary_refs") or [])
        evidence_refs = list(first_row.get("evidence_or_simulation_refs") or [])
        comparator_refs = list(first_row.get("comparator_refs") or [])
        falsifier_refs = list(first_row.get("falsifier_refs") or [])
        lean_refs = list(first_row.get("lean_refs") or [])
        finite_case_refs = list(first_row.get("finite_case_refs") or [])
        claim_id = str(first_row.get("claim_id") or "")
        public_scope = str(first_row.get("public_claim_scope") or "")
        blocker_claim = projection_blocker_row(first_row)
    claim_ledger = {
        "schema_id": "OC133_TOE_PROJECTION_CLAIM_LEDGER_v1",
        "generated_at": generated_at,
        "lane_id": lane_id,
        "status": "SOURCE_GAP_OPEN" if blocker_claim else "CANDIDATE_READY",
        "claim_total": len(rows),
        "rows": [
            {
                "claim_id": row.get("claim_id"),
                "projection_id": row.get("projection_id"),
                "public_claim_scope": row.get("public_claim_scope"),
                "current_closure_verdict": row.get("closure_verdict"),
                "root_cause_class": "MISSING_EXECUTABLE_AI_TOE_PROJECTION_SUPPORT" if is_ai else "MISSING_EXECUTABLE_EA_TOE_PROJECTION_SUPPORT",
                "why_it_failed": "The current row is a bounded blocker/future-research row and therefore cannot support final TOE promotion." if blocker_claim else "The row still requires static source verification before promotion.",
                "repair_strategy": "Replace blocker-scope rows with source-grounded domain claims only after formal, evidence, comparator, and falsifier support exists.",
            }
            for row in rows
            if isinstance(row, dict)
        ],
    }
    formal_map = {
        "schema_id": "OC133_TOE_PROJECTION_FORMAL_BOUNDARY_MAP_v1",
        "generated_at": generated_at,
        "lane_id": lane_id,
        "status": refs_status(root, formal_refs)["status"],
        "formal_boundary_refs": formal_refs,
        "ref_status": refs_status(root, formal_refs),
        "promotion_boundary": "FORMAL_BLOCKER_ROW" if blocker_claim else "CANDIDATE_FORMAL_BOUNDARY",
    }
    evidence_pack = {
        "schema_id": "OC133_TOE_PROJECTION_EVIDENCE_PACK_v1",
        "generated_at": generated_at,
        "lane_id": lane_id,
        "status": refs_status(root, evidence_refs)["status"],
        "evidence_or_simulation_refs": evidence_refs,
        "ref_status": refs_status(root, evidence_refs),
        "domain_specific_evidence_status": "SOURCE_GAP_OPEN" if blocker_claim else "CANDIDATE_READY",
    }
    comparator_pack = {
        "schema_id": "OC133_TOE_PROJECTION_COMPARATOR_BASELINES_v1",
        "generated_at": generated_at,
        "lane_id": lane_id,
        "status": refs_status(root, comparator_refs)["status"],
        "comparator_refs": comparator_refs,
        "ref_status": refs_status(root, comparator_refs),
        "baseline_scope": "BROAD_TOE_BLOCKED_WHILE_MODERN_SCIENCE_COMPARATOR_SUPERIORITY_FAILS",
    }
    falsifier_pack = {
        "schema_id": "OC133_TOE_PROJECTION_FALSIFIERS_v1",
        "generated_at": generated_at,
        "lane_id": lane_id,
        "status": refs_status(root, falsifier_refs)["status"],
        "falsifier_refs": falsifier_refs,
        "ref_status": refs_status(root, falsifier_refs),
    }
    proof_sheet = {
        "schema_id": "OC133_TOE_PROJECTION_PROOF_SHEET_v1",
        "generated_at": generated_at,
        "lane_id": lane_id,
        "status": "PASS" if not blocker_claim and formal_map["status"] == "PASS" and bool(lean_refs) else "SOURCE_GAP_OPEN",
        "claim_id": claim_id,
        "public_claim_scope": public_scope,
        "formal_boundary_refs": formal_refs,
        "lean_refs": lean_refs,
        "finite_case_refs": finite_case_refs,
        "why_it_failed": "Projection proof sheet lacks a non-blocker claim, bound Lean refs, or finite witnesses." if blocker_claim or not lean_refs or not finite_case_refs else "Proof-sheet support is available for guarded validation.",
        "repair_strategy": "Bind this projection to explicit theorem/proof, Lean declaration, and passing finite case before promotion.",
    }
    falsifier_rows = {
        "schema_id": "OC133_TOE_PROJECTION_FALSIFIER_ROWS_v1",
        "generated_at": generated_at,
        "lane_id": lane_id,
        "status": falsifier_pack["status"],
        "rows": [
            {
                "claim_id": claim_id,
                "falsifier_ref": ref,
                "closure_condition": "Projection claim must fail or narrow if this falsifier row is violated.",
            }
            for ref in falsifier_refs
        ],
    }
    support_checks = {
        "source_mined_candidate_available": bool(mined_rows),
        "claim_not_blocker": not blocker_claim,
        "formal_refs_exist": formal_map["status"] == "PASS",
        "lean_refs_exist": bool(lean_refs) and all(lean_ref_bound(root, str(ref)) for ref in lean_refs),
        "finite_case_refs_present": finite_refs_status(root, finite_case_refs)["status"] == "PASS",
        "evidence_refs_exist": evidence_pack["status"] == "PASS",
        "comparator_refs_exist": comparator_pack["status"] == "PASS",
        "falsifier_refs_exist": falsifier_pack["status"] == "PASS",
        "source_payload_already_pass": source_payload.get("closure_verdict") == "PASS" and source_payload.get("final_toe_support_allowed") is True,
    }
    support_pass = all(value for key, value in support_checks.items() if key != "source_payload_already_pass")
    source_intake = build_projection_source_intake_work_orders(
        root,
        lane_id,
        source_mining,
        support_checks,
        generated_at=generated_at,
    )
    support_pack = projection_support_pack_payload(root, lane_id, source_mining, generated_at=generated_at)
    candidate = dict(source_payload)
    candidate["lane_id"] = lane_id
    candidate["title"] = candidate.get("title") or lane_title
    candidate["guarded_writer_status"] = "PASS" if support_pass else "FAIL_CLOSED"
    candidate["closure_verdict"] = "PASS" if support_pass else "FAIL_CLOSED"
    candidate["final_toe_support_allowed"] = bool(support_pass)
    candidate["status"] = "PASS" if support_pass else "SOURCE_GAP_OPEN"
    candidate["rows"] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        new_row = dict(row)
        new_row["closure_verdict"] = "PASS" if support_pass else "FAIL_CLOSED"
        new_row["source_gap_status"] = "CLOSED" if support_pass else "OPEN"
        candidate["rows"].append(new_row)

    artifact_refs = {
        "source_mining_report_ref": write_json_artifact(root, base / f"OC133_{prefix}_SOURCE_MINING_REPORT.json", source_mining),
        "claim_ledger_ref": write_json_artifact(root, base / f"OC133_{prefix}_CLAIM_LEDGER.json", claim_ledger),
        "formal_boundary_map_ref": write_json_artifact(root, base / f"OC133_{prefix}_FORMAL_BOUNDARY_MAP.json", formal_map),
        "proof_sheet_ref": write_json_artifact(root, base / f"OC133_{prefix}_PROOF_SHEET.json", proof_sheet),
        "evidence_pack_ref": write_json_artifact(root, base / f"OC133_{prefix}_EVIDENCE_PACK.json", evidence_pack),
        "evidence_or_simulation_pack_ref": write_json_artifact(root, base / f"OC133_{prefix}_EVIDENCE_OR_SIMULATION_PACK.json", evidence_pack),
        "comparator_baselines_ref": write_json_artifact(root, base / f"OC133_{prefix}_COMPARATOR_BASELINES.json", comparator_pack),
        "falsifier_ref": write_json_artifact(root, base / f"OC133_{prefix}_FALSIFIERS.json", falsifier_pack),
        "falsifier_rows_ref": write_json_artifact(root, base / f"OC133_{prefix}_FALSIFIER_ROWS.json", falsifier_rows),
        "candidate_projection_ref": write_json_artifact(root, base / f"OC133_{prefix}_PROJECTION_CANDIDATE.json", candidate),
        "source_intake_work_orders_ref": write_json_artifact(root, base / f"OC133_{prefix}_SOURCE_INTAKE_WORK_ORDERS.json", source_intake),
        "projection_support_pack_ref": write_json_artifact(root, base / f"OC133_{prefix}_PROJECTION_SUPPORT_PACK.json", support_pack),
    }
    if support_pass:
        write_json_artifact(root, target_rel, candidate)
    writer_report = {
        "schema_id": "OC133_TOE_PROJECTION_GUARDED_WRITER_REPORT_v1",
        "generated_at": generated_at,
        "lane_id": lane_id,
        "status": "PASS" if support_pass else "FAIL_CLOSED",
        "projection_write_performed": bool(support_pass),
        "public_projection_target_ref": target_rel.as_posix(),
        "support_checks": support_checks,
        "artifact_refs": artifact_refs,
        "why_it_failed": "The lane still contains blocker-scope or insufficient source support, so the public projection remains fail-closed." if not support_pass else "All guarded writer predicates passed.",
        "repair_strategy": "Close each source gap and rerun the guarded writer; it will write PASS projection only after static support checks pass.",
        "required_capability": capability,
        "execution_command": [sys.executable, "tools/oc133_toe_closure_factory.py", "--execute-capability-lane", lane_id, "--write"],
        "pass_predicate": "support_checks all true and final TOE projection validator errors for this lane disappear.",
        "next_escalation": "Execute the listed lane subwork orders; do not edit the public projection to PASS manually.",
    }
    artifact_refs["guarded_writer_report_ref"] = write_json_artifact(root, base / f"OC133_{prefix}_PROJECTION_GUARDED_WRITER_REPORT.json", writer_report)
    capability_report = {
        "schema_id": "OC133_TOE_PROJECTION_CAPABILITY_REPORT_v1",
        "generated_at": generated_at,
        "lane_id": lane_id,
        "status": "PASS" if support_pass else "SOURCE_GAP_OPEN",
        "projection_write_performed": bool(support_pass),
        "support_checks": support_checks,
        "source_intake_work_order_total": source_intake["source_intake_work_order_total"],
        "open_source_intake_work_order_total": source_intake["open_work_order_total"],
        "missing_support_keys": source_intake["missing_support_keys"],
        "support_pack_status": support_pack["status"],
        "support_pass_candidate_total": support_pack["support_pass_candidate_total"],
        "artifact_refs": artifact_refs,
    }
    artifact_refs["capability_report_ref"] = write_json_artifact(root, base / f"OC133_{prefix}_PROJECTION_CAPABILITY_REPORT.json", capability_report)
    return capability_report


def build_grand_promotion_execution_plan(root: Path, *, generated_at: str) -> dict[str, Any]:
    base = lane_execution_base("GRAND_TOE_CLAIM_LEDGER_EVIDENCE")
    promotion = read_json(root / GRAND_PROMOTION_REPORT)
    scorecard = read_json(root / GRAND_SCORECARD)
    finite = read_json(root / FINITE_CHECK_REPORT)
    vector = promotion.get("promotion_gate_vector", {}) if isinstance(promotion.get("promotion_gate_vector"), dict) else {}
    ai_result = evaluate_projection_lane(root, "AI", FINAL_TOE_PROJECTION_LANE_TARGETS["AI"])
    ea_result = evaluate_projection_lane(root, "ENTERPRISE_ARCHITECTURE", FINAL_TOE_PROJECTION_LANE_TARGETS["ENTERPRISE_ARCHITECTURE"])
    comparator_result = evaluate_comparator_lane(root)
    prerequisites = [
        ("AI_projection_pass", ai_result.get("status") == "PASS", "AI projection lane has full claim/formal/Lean/finite/evidence/comparator/falsifier support."),
        ("enterprise_architecture_projection_pass", ea_result.get("status") == "PASS", "EA projection lane has full architecture-case/formal/Lean/finite/evidence/comparator/falsifier support."),
        ("finite_model_checks_pass", int(finite.get("failure_total") or 0) == 0, "Finite model checks have zero failures."),
        ("dedicated_promoted_claim_row", vector.get("dedicated_claim_row") is True, "Dedicated promoted grand TOE claim row exists."),
        ("promotion_theorem_ids_bound", vector.get("promotion_theorem_ids_bound") is True, "Promotion theorem ids are bound."),
        ("proof_refs_bound", vector.get("proof_refs_bound") is True, "Proof refs are bound."),
        ("claim_lean_refs_bound", vector.get("claim_lean_refs_bound") is True, "Claim Lean refs are bound."),
        ("finite_positive_negative_controls_bound", vector.get("finite_positive_negative_controls_bound") is True, "Finite positive/negative controls are bound."),
        ("all_domain_empirical_pack_valid", vector.get("all_domain_empirical_pack_valid") is True, "All-domain empirical pack is valid."),
        ("modern_science_superiority_certified", vector.get("modern_science_superiority_certified") is True and comparator_result.get("status") == "PASS", "Modern-science broad comparator superiority is certified."),
        ("promotion_contract_pass", promotion.get("verdict") == "PASS", "Grand promotion contract verdict is PASS."),
        ("scorecard_no_grand_blockers", "grand_toe_claim_ledger_evidence" not in (scorecard.get("blocker_ids") or []), "Grand TOE claim ledger evidence is not in scorecard blockers."),
    ]
    rows = []
    for index, (predicate_id, passed, description) in enumerate(prerequisites, start=1):
        rows.append(
            normalize_problem_row(
                {
                    "subwork_order_id": f"R017-GRAND-PROMOTION-PREREQ-{index:03d}",
                    "lane_id": "GRAND_TOE_CLAIM_LEDGER_EVIDENCE",
                    "predicate_id": predicate_id,
                    "status": "PASS" if passed else "OPEN",
                    "passed": bool(passed),
                    "finding_class": "GRAND_TOE_CLAIM_LEDGER_EVIDENCE",
                    "why_it_failed": f"Grand promotion prerequisite `{predicate_id}` is not satisfied." if not passed else description,
                    "repair_strategy": description,
                    "required_capability": "Research/FormalScience",
                    "source_refs": [str(GRAND_PROMOTION_REPORT), str(GRAND_SCORECARD), str(FINITE_CHECK_REPORT)],
                },
                {
                    "execution_command": [sys.executable, "tools/oc133_toe_closure_factory.py", "--execute-capability-lane", "GRAND_TOE_CLAIM_LEDGER_EVIDENCE", "--write"],
                    "pass_predicate": f"{predicate_id} == true in the derived grand promotion vector.",
                    "next_escalation": "Close the named prerequisite from canonical research sources, then rebuild SPOT/projections and rerun the grand promotion contract.",
                },
            )
        )
    open_rows = [row for row in rows if row.get("status") != "PASS"]
    payload = {
        "schema_id": "OC133_GRAND_PROMOTION_EXECUTION_PLAN_v1",
        "generated_at": generated_at,
        "lane_id": "GRAND_TOE_CLAIM_LEDGER_EVIDENCE",
        "status": "PASS" if not open_rows else "FAIL_CLOSED",
        "prerequisite_total": len(rows),
        "open_prerequisite_total": len(open_rows),
        "finite_regression_guard_status": "PASS" if int(finite.get("failure_total") or 0) == 0 else "FAIL",
        "promotion_verdict": promotion.get("verdict"),
        "scorecard_blocker_ids": scorecard.get("blocker_ids", []),
        "why_it_failed": "Grand promotion cannot pass until every prerequisite row is PASS." if open_rows else "Grand promotion prerequisites are all PASS.",
        "repair_strategy": "Execute prerequisite-specific research lanes; never promote a grand TOE row manually.",
        "required_capability": "Research/FormalScience",
        "execution_command": [sys.executable, "tools/oc133_toe_closure_factory.py", "--execute-capability-lane", "GRAND_TOE_CLAIM_LEDGER_EVIDENCE", "--write"],
        "pass_predicate": "open_prerequisite_total == 0 and promotion_verdict == PASS.",
        "next_escalation": "Use open prerequisite rows as the next executable research backlog.",
        "rows": rows,
    }
    payload["artifact_hash"] = artifact_hash(payload)
    artifact_rel = base / "OC133_GRAND_PROMOTION_EXECUTION_PLAN.json"
    payload["artifact_ref"] = rel(root, root / artifact_rel)
    write_json_artifact(root, artifact_rel, payload)
    return payload


def build_grand_promotion_derivation_report(root: Path, *, generated_at: str) -> dict[str, Any]:
    base = lane_execution_base("GRAND_TOE_CLAIM_LEDGER_EVIDENCE")
    promotion = read_json(root / GRAND_PROMOTION_REPORT)
    scorecard = read_json(root / GRAND_SCORECARD)
    ai = evaluate_projection_lane(root, "AI", FINAL_TOE_PROJECTION_LANE_TARGETS["AI"])
    ea = evaluate_projection_lane(root, "ENTERPRISE_ARCHITECTURE", FINAL_TOE_PROJECTION_LANE_TARGETS["ENTERPRISE_ARCHITECTURE"])
    comparator = evaluate_comparator_lane(root)
    finite = read_json(root / FINITE_CHECK_REPORT)
    plan = build_grand_promotion_execution_plan(root, generated_at=generated_at)
    derived_checks = {
        "ai_projection_pass": ai.get("status") == "PASS",
        "enterprise_architecture_projection_pass": ea.get("status") == "PASS",
        "comparator_broad_pass": comparator.get("status") == "PASS",
        "finite_regression_guard_pass": int(finite.get("failure_total") or 0) == 0,
        "promotion_contract_pass": promotion.get("verdict") == "PASS",
        "scorecard_all_domain_ready": scorecard.get("all_domain_ready_no_send") is True,
        "scorecard_grand_toe_claim_pass": ((scorecard.get("checks") or {}).get("grand_toe_claim_ledger_evidence") or {}).get("state") == "PASS",
        "scorecard_modern_science_comparator_pass": ((scorecard.get("checks") or {}).get("modern_science_comparator_superiority") or {}).get("state") == "PASS",
    }
    missing = [key for key, passed in derived_checks.items() if passed is not True]
    payload = {
        "schema_id": "OC133_GRAND_PROMOTION_DERIVATION_REPORT_v1",
        "generated_at": generated_at,
        "lane_id": "GRAND_TOE_CLAIM_LEDGER_EVIDENCE",
        "status": "PASS" if not missing else "FAIL_CLOSED",
        "scorecard_write_performed": False,
        "derived_checks": derived_checks,
        "missing_derived_checks": missing,
        "promotion_execution_plan_ref": plan.get("artifact_ref"),
        "input_refs": {
            "grand_promotion_report": str(GRAND_PROMOTION_REPORT),
            "scorecard": str(GRAND_SCORECARD),
            "finite_checks": str(FINITE_CHECK_REPORT),
            "ai_projection_lane": rel(root, FINAL_TOE_PROJECTION_LANE_TARGETS["AI"]),
            "enterprise_architecture_projection_lane": rel(root, FINAL_TOE_PROJECTION_LANE_TARGETS["ENTERPRISE_ARCHITECTURE"]),
            "comparator_register": str(COMPARATOR_REGISTER),
        },
        "why_it_failed": "Grand promotion derivation still has unmet lane-derived prerequisites." if missing else "Grand promotion derivation predicates are all satisfied.",
        "repair_strategy": "Derive scorecard PASS only from PASS lane outputs; never manually override all_domain_ready_no_send or blocker_ids.",
        "required_capability": "Research/FormalScience",
        "execution_command": [sys.executable, "tools/oc133_toe_closure_factory.py", "--execute-capability-lane", "GRAND_TOE_CLAIM_LEDGER_EVIDENCE", "--write"],
        "pass_predicate": "All derived_checks true and strict grand-science validator errors disappear.",
        "next_escalation": "Close AI/EA/comparator support first, then rerun grand promotion derivation and scorecard sync.",
        "rows": plan.get("rows", []),
    }
    payload["artifact_hash"] = artifact_hash(payload)
    artifact_rel = base / "OC133_GRAND_PROMOTION_DERIVATION_REPORT.json"
    payload["artifact_ref"] = rel(root, root / artifact_rel)
    write_json_artifact(root, artifact_rel, payload)
    return payload


def build_grand_lane_diagnostics(root: Path) -> dict[str, Any]:
    base = lane_execution_base("GRAND_TOE_CLAIM_LEDGER_EVIDENCE")
    generated_at = stable_generated_at(root, base / "OC133_GRAND_PROMOTION_SUBLANE_DIAGNOSIS.json")
    finite_failures = failed_finite_rows(root)
    promotion = read_json(root / GRAND_PROMOTION_REPORT)
    scorecard = read_json(root / GRAND_SCORECARD)
    promotion_plan = build_grand_promotion_execution_plan(root, generated_at=generated_at)
    derivation = build_grand_promotion_derivation_report(root, generated_at=generated_at)
    payload = {
        "schema_id": "OC133_GRAND_PROMOTION_SUBLANE_DIAGNOSIS_v1",
        "generated_at": generated_at,
        "lane_id": "GRAND_TOE_CLAIM_LEDGER_EVIDENCE",
        "status": "PASS" if not finite_failures and promotion.get("verdict") == "PASS" else "FAIL_CLOSED",
        "finite_regression_guard_status": "PASS" if not finite_failures else "FAIL",
        "promotion_verdict": promotion.get("verdict"),
        "scorecard_blocker_ids": scorecard.get("blocker_ids", []),
        "finite_failure_total": len(finite_failures),
        "finite_failure_ids": [row.get("case_id") for row in finite_failures],
        "finite_failures": finite_failures,
        "promotion_dependency_vector": promotion.get("promotion_gate_vector", {}),
        "promotion_open_blockers": promotion.get("open_blockers", []),
        "promotion_execution_plan_ref": promotion_plan["artifact_ref"],
        "promotion_derivation_report_ref": derivation["artifact_ref"],
        "promotion_prerequisite_total": promotion_plan["prerequisite_total"],
        "promotion_open_prerequisite_total": promotion_plan["open_prerequisite_total"],
        "promotion_derivation_status": derivation["status"],
        "subwork_orders": grand_claim_subwork(root),
        "why_it_failed": "Grand TOE promotion is blocked while finite failures, comparator blockers, empirical blockers, or promotion contract blockers remain.",
        "repair_strategy": "Resolve each finite failure and promotion dependency, then rerun grand science loop and strict final validator.",
        "required_capability": "Research/FormalScience",
        "execution_command": [sys.executable, "tools/oc133_toe_closure_factory.py", "--execute-capability-lane", "GRAND_TOE_CLAIM_LEDGER_EVIDENCE", "--write"],
        "pass_predicate": "Grand promotion contract PASS, finite checks PASS, empirical pack PASS, comparator pack PASS.",
        "next_escalation": "Repair finite cases or demote the unsupported promoted claim; do not count blocked controls as closure.",
    }
    artifact_rel = base / "OC133_GRAND_PROMOTION_SUBLANE_DIAGNOSIS.json"
    payload["artifact_ref"] = rel(root, root / artifact_rel)
    write_json_artifact(root, artifact_rel, payload)
    return payload


COMPARATOR_REQUIRED_ARTIFACT_KEYS = [
    "verified_open_source_capsule",
    "benchmark_case",
    "incumbent_comparator",
    "oc_prediction_scoring_row",
    "uncertainty_row",
    "falsifier_row",
    "replay_record",
]


def comparator_coverage_work_order_index(root: Path) -> dict[str, dict[str, Any]]:
    coverage_work_orders = read_json(root / "benchmarks/modern_science/OC133_MODERN_SCIENCE_COVERAGE_WORK_ORDERS.json")
    work_orders = coverage_work_orders.get("work_orders", []) if isinstance(coverage_work_orders.get("work_orders"), list) else []
    return {
        str(row.get("domain_class_id", "")) + "::" + str(row.get("phenomenon_class_id", "")): row
        for row in work_orders
        if isinstance(row, dict)
    }


def comparator_execution_gap_rows(root: Path) -> list[dict[str, Any]]:
    coverage_register = read_json(root / "comparators/modern_science/OC133_MODERN_SCIENCE_COVERAGE_REGISTER.json")
    by_gap = comparator_coverage_work_order_index(root)
    execution_rows: list[dict[str, Any]] = []
    for gap in coverage_register.get("coverage_gap_rows", []) or []:
        if not isinstance(gap, dict):
            continue
        key = str(gap.get("domain_class_id", "")) + "::" + str(gap.get("phenomenon_class_id", ""))
        work_order = by_gap.get(key, {})
        source_capsule_refs = [
            row.get("source_capsule_ref")
            for row in work_order.get("source_refs", [])
            if isinstance(row, dict) and row.get("source_capsule_ref")
        ]
        source_capsule_existing_total = sum(1 for ref in source_capsule_refs if (root / str(ref)).exists())
        artifact_status = {
            "verified_open_source_capsule": bool(source_capsule_refs) and source_capsule_existing_total == len(source_capsule_refs),
            "benchmark_case": bool(work_order.get("benchmark_case_ref")) and (root / str(work_order.get("benchmark_case_ref"))).exists(),
            "incumbent_comparator": bool(work_order.get("incumbent_comparator_ref")) and (root / str(work_order.get("incumbent_comparator_ref"))).exists(),
            "oc_prediction_scoring_row": bool(work_order.get("oc_scoring_ref")) and (root / str(work_order.get("oc_scoring_ref"))).exists(),
            "uncertainty_row": bool(work_order.get("uncertainty_ref")) and (root / str(work_order.get("uncertainty_ref"))).exists(),
            "falsifier_row": bool(work_order.get("falsifier_ref")) and (root / str(work_order.get("falsifier_ref"))).exists(),
            "replay_record": bool(work_order.get("replay_record_ref")) and (root / str(work_order.get("replay_record_ref"))).exists(),
        }
        missing = [key for key, value in artifact_status.items() if value is not True]
        execution_rows.append(
            normalize_problem_row(
                {
                    "gap_id": gap.get("gap_id"),
                    "domain_class_id": gap.get("domain_class_id"),
                    "phenomenon_class_id": gap.get("phenomenon_class_id"),
                    "status": "PASS" if not missing else "OPEN",
                    "work_order_id": work_order.get("work_order_id"),
                    "source_capsule_refs": source_capsule_refs,
                    "source_capsule_ref_total": len(source_capsule_refs),
                    "source_capsule_existing_total": source_capsule_existing_total,
                    "artifact_status": artifact_status,
                    "missing_artifacts": missing,
                    "acceptance_predicates": work_order.get("acceptance_predicates", []),
                    "source_refs": [
                        "comparators/modern_science/OC133_MODERN_SCIENCE_COVERAGE_REGISTER.json",
                        "benchmarks/modern_science/OC133_MODERN_SCIENCE_COVERAGE_WORK_ORDERS.json",
                    ],
                    "why_it_failed": "Coverage gap has no certified source-backed benchmark lane; broad superiority remains blocked." if missing else "Coverage gap has all required broad-superiority artifacts.",
                    "repair_strategy": "Execute this work order by binding source capsule, target acquisition, incumbent comparator, OC scoring, uncertainty, falsifier, and replay evidence.",
                    "required_capability": "Research/PriorArt",
                },
                {
                    "execution_command": [sys.executable, "tools/oc133_toe_closure_factory.py", "--execute-capability-lane", "MODERN_SCIENCE_COMPARATOR_SUPERIORITY", "--write"],
                    "pass_predicate": "Every required comparator artifact exists, acceptance predicates pass, and this gap row is marked PASS by the coverage register.",
                    "next_escalation": "Split the gap into governed source acquisition, benchmark construction, comparator scoring, uncertainty, falsifier, and replay tasks.",
                },
            )
        )
    return execution_rows


def comparator_lane_queue_rows_by_gap(root: Path) -> dict[str, dict[str, Any]]:
    payload = read_json(root / "reports/OC_CORE_1_3_3_MODERN_SCIENCE_COVERAGE_LANE_QUEUE.json")
    rows = payload.get("rows") or payload.get("lanes") or []
    if not isinstance(rows, list):
        return {}
    return {
        str(row.get("coverage_gap_id")): row
        for row in rows
        if isinstance(row, dict) and row.get("coverage_gap_id")
    }


def comparator_gap_execution_rel(gap_id: str) -> Path:
    gap_hash = artifact_hash({"gap_id": gap_id})[:16]
    return lane_execution_base("MODERN_SCIENCE_COMPARATOR_SUPERIORITY") / "gap_jobs" / f"gap_{gap_hash}.json"


def comparator_gap_execution_payload(root: Path, gap_id: str, *, generated_at: str | None = None) -> dict[str, Any]:
    execution_rows = comparator_execution_gap_rows(root)
    gap_row = next((row for row in execution_rows if row.get("gap_id") == gap_id), {})
    queue_row = comparator_lane_queue_rows_by_gap(root).get(gap_id, {})
    missing = list(gap_row.get("missing_artifacts") or COMPARATOR_REQUIRED_ARTIFACT_KEYS)
    artifact_rows = []
    for index, artifact_key in enumerate(COMPARATOR_REQUIRED_ARTIFACT_KEYS, start=1):
        artifact_rows.append(
            normalize_problem_row(
                {
                    "subwork_order_id": f"R017-COMPARATOR-GAP-{gap_id}-{artifact_key}",
                    "gap_id": gap_id,
                    "lane_id": "MODERN_SCIENCE_COMPARATOR_SUPERIORITY",
                    "artifact_key": artifact_key,
                    "status": "PASS" if artifact_key not in missing else "OPEN",
                    "source_refs": [
                        "reports/OC_CORE_1_3_3_MODERN_SCIENCE_COVERAGE_LANE_QUEUE.json",
                        "benchmarks/modern_science/OC133_MODERN_SCIENCE_COVERAGE_WORK_ORDERS.json",
                        "comparators/modern_science/OC133_MODERN_SCIENCE_COVERAGE_REGISTER.json",
                    ],
                    "why_it_failed": f"Comparator gap `{gap_id}` lacks `{artifact_key}`." if artifact_key in missing else f"Comparator gap `{gap_id}` has `{artifact_key}` bound.",
                    "repair_strategy": f"Create or bind the `{artifact_key}` artifact through governed open/free source acquisition, target separation, scoring, uncertainty, falsifier, and replay policy.",
                    "required_capability": "Research/PriorArt",
                },
                {
                    "execution_command": [sys.executable, "tools/oc133_toe_closure_factory.py", "--execute-comparator-gap", gap_id, "--write"],
                    "pass_predicate": f"{artifact_key} exists, is hash-bound, and passes the declared comparator coverage acceptance predicates.",
                    "next_escalation": "If this artifact remains open, split it into source acquisition, scoring, or replay subtasks using the queue row dependencies.",
                },
            )
        )
    payload = {
        "schema_id": "OC133_MODERN_SCIENCE_COMPARATOR_GAP_EXECUTION_v1",
        "generated_at": generated_at or stable_generated_at(root, comparator_gap_execution_rel(gap_id)),
        "lane_id": "MODERN_SCIENCE_COMPARATOR_SUPERIORITY",
        "gap_id": gap_id,
        "domain_class_id": gap_row.get("domain_class_id") or queue_row.get("domain_class_id"),
        "phenomenon_class_id": gap_row.get("phenomenon_class_id") or queue_row.get("phenomenon_class_id"),
        "status": "PASS" if gap_row and not missing else "OPEN",
        "queue_row_found": bool(queue_row),
        "execution_state": queue_row.get("execution_state"),
        "dependency_key": queue_row.get("dependency_key"),
        "dependencies": queue_row.get("dependencies", []),
        "official_source_defaults": queue_row.get("official_source_defaults", []),
        "expected_acceptance_predicates": queue_row.get("expected_acceptance_predicates", []),
        "required_artifacts": COMPARATOR_REQUIRED_ARTIFACT_KEYS,
        "missing_artifacts": missing,
        "missing_artifact_total": len(missing),
        "artifact_rows": artifact_rows,
        "why_it_failed": "Comparator gap is not closed because one or more required artifacts are missing." if missing else "Comparator gap has all required artifacts.",
        "repair_strategy": "Execute source-capsule, benchmark, comparator, scoring, uncertainty, falsifier, and replay subtasks until the gap closes in the coverage register.",
        "required_capability": "Research/PriorArt",
        "execution_command": [sys.executable, "tools/oc133_toe_closure_factory.py", "--execute-comparator-gap", gap_id, "--write"],
        "pass_predicate": "missing_artifact_total == 0 and coverage register marks this gap PASS.",
        "next_escalation": "Use artifact_rows as the next per-artifact work list; do not count benchmark-scoped superiority as broad closure.",
        "rows": [gap_row] if gap_row else [],
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def build_comparator_gap_execution(root: Path, gap_id: str) -> dict[str, Any]:
    payload = comparator_gap_execution_payload(root, gap_id)
    artifact_rel = comparator_gap_execution_rel(gap_id)
    payload["artifact_ref"] = rel(root, root / artifact_rel)
    write_json_artifact(root, artifact_rel, payload)
    return payload


def comparator_domain_job_payload(root: Path, job_id: str, *, generated_at: str | None = None) -> dict[str, Any]:
    execution_rows = comparator_execution_gap_rows(root)
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in execution_rows:
        grouped.setdefault(str(row.get("domain_class_id") or "UNKNOWN"), []).append(row)
    sorted_groups = sorted(grouped.items())
    job_index: dict[str, tuple[str, list[dict[str, Any]]]] = {
        f"MS-COV-JOB-{index:03d}": (domain_class_id, rows_for_domain)
        for index, (domain_class_id, rows_for_domain) in enumerate(sorted_groups, start=1)
    }
    domain_class_id, rows_for_domain = job_index.get(job_id, ("UNKNOWN", []))
    missing_by_gap = {
        str(row.get("gap_id")): list(row.get("missing_artifacts") or [])
        for row in rows_for_domain
        if row.get("status") != "PASS"
    }
    gap_execution_refs: dict[str, str] = {}
    for row in rows_for_domain:
        gap_id = str(row.get("gap_id") or "")
        if gap_id:
            gap_execution_refs[gap_id] = build_comparator_gap_execution(root, gap_id).get("artifact_ref", "")
    open_rows = [row for row in rows_for_domain if row.get("status") != "PASS"]
    payload = {
        "schema_id": "OC133_MODERN_SCIENCE_COMPARATOR_DOMAIN_JOB_EXECUTION_v1",
        "generated_at": generated_at or stable_generated_at(root, lane_execution_base("MODERN_SCIENCE_COMPARATOR_SUPERIORITY") / "domain_jobs" / f"{job_id}.json"),
        "lane_id": "MODERN_SCIENCE_COMPARATOR_SUPERIORITY",
        "job_id": job_id,
        "domain_class_id": domain_class_id,
        "status": "PASS" if rows_for_domain and not open_rows else "OPEN",
        "gap_total": len(rows_for_domain),
        "open_gap_total": len(open_rows),
        "closed_gap_total": len(rows_for_domain) - len(open_rows),
        "required_artifacts": COMPARATOR_REQUIRED_ARTIFACT_KEYS,
        "missing_artifacts_by_gap": missing_by_gap,
        "gap_execution_refs": gap_execution_refs,
        "broad_pass_allowed": bool(rows_for_domain and not open_rows),
        "why_it_failed": "Domain job still has open broad-coverage comparator gaps." if open_rows else "Domain job has no open broad-coverage comparator gaps.",
        "repair_strategy": "Bind verified source capsules, benchmark cases, incumbent comparators, OC scoring, uncertainty, falsifiers, and replay records for every gap in this domain class.",
        "required_capability": "Research/PriorArt",
        "execution_command": [sys.executable, "tools/oc133_toe_closure_factory.py", "--execute-comparator-domain-job", job_id, "--write"],
        "pass_predicate": "open_gap_total == 0 and every required artifact is bound for every gap.",
        "next_escalation": "If domain execution does not reduce validator errors, split each open gap into artifact-specific acquisition/replay work orders.",
        "rows": rows_for_domain,
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def build_comparator_domain_job_execution(root: Path, job_id: str) -> dict[str, Any]:
    base = lane_execution_base("MODERN_SCIENCE_COMPARATOR_SUPERIORITY") / "domain_jobs"
    payload = comparator_domain_job_payload(root, job_id)
    artifact_rel = base / f"{job_id}.json"
    payload["artifact_ref"] = rel(root, root / artifact_rel)
    write_json_artifact(root, artifact_rel, payload)
    return payload


def build_comparator_lane_diagnostics(root: Path) -> dict[str, Any]:
    base = lane_execution_base("MODERN_SCIENCE_COMPARATOR_SUPERIORITY")
    generated_at = stable_generated_at(root, base / "OC133_MODERN_SCIENCE_BROAD_COVERAGE_WORK_ORDERS.json")
    register = read_json(root / COMPARATOR_REGISTER)
    gap_rows = comparator_gap_rows(root)
    execution_rows = comparator_execution_gap_rows(root)
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in execution_rows:
        grouped.setdefault(str(row.get("domain_class_id") or "UNKNOWN"), []).append(row)
    job_rows: list[dict[str, Any]] = []
    for domain_index, (domain_class_id, rows_for_domain) in enumerate(sorted(grouped.items()), start=1):
        job_rows.append(
            {
                "job_id": f"MS-COV-JOB-{domain_index:03d}",
                "domain_class_id": domain_class_id,
                "status": "OPEN",
                "gap_total": len(rows_for_domain),
                "open_gap_total": len([row for row in rows_for_domain if row.get("status") != "PASS"]),
                "required_artifacts": [
                    "verified_open_source_capsule",
                    "benchmark_case",
                    "incumbent_comparator",
                    "oc_prediction_scoring_row",
                    "uncertainty_row",
                    "falsifier_row",
                    "replay_record",
                ],
                "source_capsule_verified": False,
                "benchmark_case_bound": False,
                "incumbent_comparator_bound": False,
                "oc_scoring_bound": False,
                "uncertainty_bound": False,
                "falsifier_bound": False,
                "replay_record_bound": False,
                "gap_ids": [row.get("gap_id") for row in rows_for_domain],
                "why_it_failed": "This domain class still lacks complete source-capsule, benchmark, comparator, scoring, uncertainty, falsifier, and replay bindings for every gap.",
                "repair_strategy": "Execute governed open-source acquisition/cache and replay for each gap before broad coverage can pass.",
                "required_capability": "Research/PriorArt",
                "execution_command": [sys.executable, "tools/oc133_toe_closure_factory.py", "--execute-comparator-domain-job", f"MS-COV-JOB-{domain_index:03d}", "--write"],
                "pass_predicate": "All required artifacts are bound for every gap in this domain class and every gap row is PASS.",
                "next_escalation": "Split this domain class into per-gap acquisition/replay tasks if no domain-level progress occurs.",
            }
        )
    execution_report = {
        "schema_id": "OC133_MODERN_SCIENCE_BROAD_COVERAGE_EXECUTION_REPORT_v1",
        "generated_at": generated_at,
        "lane_id": "MODERN_SCIENCE_COMPARATOR_SUPERIORITY",
        "status": "OPEN" if execution_rows else "MISSING",
        "domain_job_total": len(job_rows),
        "open_domain_job_total": sum(1 for row in job_rows if row.get("status") != "PASS"),
        "coverage_gap_total": len(execution_rows),
        "closed_gap_total": sum(1 for row in execution_rows if row.get("status") == "PASS"),
        "open_gap_total": sum(1 for row in execution_rows if row.get("status") != "PASS"),
        "broad_pass_allowed": False,
        "job_rows": job_rows,
        "rows": execution_rows,
        "why_it_failed": "Broad modern-science coverage still has open source-backed comparator gaps.",
        "repair_strategy": "Close every gap row with governed source-backed benchmark/comparator evidence before broad superiority can pass.",
        "required_capability": "Research/PriorArt",
        "execution_command": [sys.executable, "tools/oc133_toe_closure_factory.py", "--execute-capability-lane", "MODERN_SCIENCE_COMPARATOR_SUPERIORITY", "--write"],
        "pass_predicate": "open_gap_total == 0 and coverage_extends_to_all_of_modern_science == true.",
        "next_escalation": "Run domain-specific coverage work-order executors, then rebuild the comparator register.",
    }
    execution_report["artifact_hash"] = artifact_hash(execution_report)
    payload = {
        "schema_id": "OC133_MODERN_SCIENCE_BROAD_COVERAGE_WORK_ORDERS_v1",
        "generated_at": generated_at,
        "lane_id": "MODERN_SCIENCE_COMPARATOR_SUPERIORITY",
        "status": "OPEN" if gap_rows else "PASS",
        "benchmark_scoped_superiority_status": register.get("modern_science_comparator_superiority", {}).get("benchmark_scoped_state"),
        "broad_superiority_status": register.get("modern_science_comparator_superiority", {}).get("state"),
        "coverage_gap_total": len(gap_rows),
        "broad_claim_predicates": register.get("broad_claim_predicates", {}),
        "rows": gap_rows,
        "why_it_failed": "Broad superiority is not closed because coverage_extends_to_all_of_modern_science is false.",
        "repair_strategy": "Close each source-backed comparator coverage gap; keep broad wording blocked until broad predicates pass.",
        "required_capability": "Research/PriorArt",
        "execution_command": [sys.executable, "tools/oc133_toe_closure_factory.py", "--execute-capability-lane", "MODERN_SCIENCE_COMPARATOR_SUPERIORITY", "--write"],
        "pass_predicate": "modern_science_comparator_superiority.state == PASS and coverage_extends_to_all_of_modern_science == true.",
        "next_escalation": "Acquire or bind governed open comparator sources for every broad-coverage gap.",
    }
    artifact_rel = base / "OC133_MODERN_SCIENCE_BROAD_COVERAGE_WORK_ORDERS.json"
    execution_artifact_rel = base / "OC133_MODERN_SCIENCE_BROAD_COVERAGE_EXECUTION_REPORT.json"
    payload["execution_report_ref"] = rel(root, root / execution_artifact_rel)
    payload["artifact_ref"] = rel(root, root / artifact_rel)
    write_json_artifact(root, execution_artifact_rel, execution_report)
    write_json_artifact(root, artifact_rel, payload)
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
            if not row.get(field):
                findings.append(f"row {index} missing {field}")
        if row.get("closure_verdict") != "PASS":
            findings.append(f"row {index} closure_verdict is not PASS")
        if projection_blocker_row(row):
            findings.append(f"row {index} is blocker/future-research/demoted scope")
        for ref_field in [
            "theorem_or_formal_boundary_refs",
            "lean_refs",
            "evidence_or_simulation_refs",
            "comparator_refs",
            "falsifier_refs",
        ]:
            value = row.get(ref_field, [])
            if not isinstance(value, list) or not value:
                findings.append(f"row {index} {ref_field} is empty or not a list")
                continue
            for ref in value:
                if ref_field == "lean_refs":
                    if not lean_ref_bound(root, str(ref)):
                        findings.append(f"row {index} {ref_field} unbound Lean ref {ref}")
                    continue
                if not ref_exists(root, str(ref)):
                    findings.append(f"row {index} {ref_field} missing ref {ref}")
        finite_status = finite_refs_status(root, list(row.get("finite_case_refs") or []))
        if finite_status["status"] != "PASS":
            findings.append(f"row {index} finite_case_refs are missing or not PASS")
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


def safe_run_command(root: Path, cmd: list[str], timeout: int) -> dict[str, Any]:
    try:
        return run_command(root, cmd, timeout)
    except subprocess.TimeoutExpired as exc:
        return {
            "cmd": cmd,
            "returncode": 124,
            "stdout_tail": (exc.stdout or "")[-3000:] if isinstance(exc.stdout, str) else "",
            "stderr_tail": (exc.stderr or "timeout")[-3000:] if isinstance(exc.stderr, str) else "timeout",
        }


def git_status_rows(root: Path) -> list[str]:
    completed = subprocess.run(
        ["git", "status", "--short"],
        cwd=root,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=60,
    )
    if completed.returncode != 0:
        return []
    ignored_prefixes = ("?? _codex_r009_run/", "?? _codex_r010_run/")
    return sorted(
        line.strip()
        for line in completed.stdout.splitlines()
        if line.strip() and not line.startswith(ignored_prefixes)
    )


def changed_artifacts(before_status: list[str], after_status: list[str], extra_refs: list[str] | None = None) -> list[str]:
    before = set(before_status)
    after = set(after_status)
    rows = sorted(after - before)
    for ref in extra_refs or []:
        if ref and ref not in rows:
            rows.append(ref)
    return rows


def artifact_refs_from_lane_attempt(result: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    for command_result in result.get("command_results", []) or []:
        if not isinstance(command_result, dict):
            continue
        stdout = command_result.get("stdout_tail")
        if not isinstance(stdout, str) or not stdout.strip().startswith("{"):
            continue
        try:
            payload = json.loads(stdout)
        except Exception:
            continue
        artifact_ref = payload.get("artifact_ref")
        if isinstance(artifact_ref, str):
            refs.append(artifact_ref)
        artifact_refs = payload.get("artifact_refs")
        if isinstance(artifact_refs, dict):
            refs.extend(str(value) for value in artifact_refs.values() if value)
        for key, value in payload.items():
            if key.endswith("_refs") and isinstance(value, dict):
                refs.extend(str(ref) for ref in value.values() if ref)
    return refs


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
        execution_state = "EXECUTED_PROJECTION_CAPABILITY"
        subwork = projection_lane_subwork(lane_id)
        capability_report = build_projection_lane_capability_artifacts(root, lane_id)
        source_intake = read_json(root / str(capability_report.get("artifact_refs", {}).get("source_intake_work_orders_ref") or ""))
        source_intake_executions: list[dict[str, Any]] = []
        for row in source_intake.get("rows", []) or []:
            if isinstance(row, dict) and row.get("work_order_id"):
                source_intake_executions.append(build_projection_source_intake_execution(root, str(row["work_order_id"])))
        command_results.append(
            {
                "cmd": ["internal", "build_projection_lane_capability_artifacts", lane_id],
                "returncode": 0,
                "stdout_tail": json.dumps(
                    {
                        "lane_id": lane_id,
                        "subwork_order_total": len(subwork),
                        "subwork_order_ids": [row["subwork_order_id"] for row in subwork],
                        "capability_status": capability_report["status"],
                        "artifact_refs": capability_report["artifact_refs"],
                        "source_intake_execution_total": len(source_intake_executions),
                        "open_source_intake_execution_total": sum(1 for row in source_intake_executions if row.get("status") != "PASS"),
                        "source_intake_execution_refs": {
                            f"source_intake_execution_{index:03d}_ref": row.get("artifact_ref")
                            for index, row in enumerate(source_intake_executions, start=1)
                        },
                        "projection_write_performed": capability_report["projection_write_performed"],
                    },
                    ensure_ascii=False,
                ),
                "stderr_tail": (
                    f"{lane_id} projection capability executed. Guarded writer leaves the lane fail-closed "
                    "unless claim/formal/evidence/comparator/falsifier artifacts pass static validation."
                ),
            }
        )
    elif lane_id == "GRAND_TOE_CLAIM_LEDGER_EVIDENCE":
        diagnostic = build_grand_lane_diagnostics(root)
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
        command_results.append(
            {
                "cmd": ["internal", "build_grand_lane_diagnostics"],
                "returncode": 0,
                "stdout_tail": json.dumps(
                    {
                        "lane_id": lane_id,
                        "diagnostic_status": diagnostic["status"],
                        "finite_failure_ids": diagnostic["finite_failure_ids"],
                        "promotion_open_prerequisite_total": diagnostic.get("promotion_open_prerequisite_total"),
                        "artifact_ref": diagnostic["artifact_ref"],
                        "artifact_refs": {
                            "grand_promotion_diagnosis_ref": diagnostic["artifact_ref"],
                            "grand_promotion_execution_plan_ref": diagnostic.get("promotion_execution_plan_ref"),
                            "grand_promotion_derivation_report_ref": diagnostic.get("promotion_derivation_report_ref"),
                        },
                    },
                    ensure_ascii=False,
                ),
                "stderr_tail": "Grand promotion sublane diagnostics materialized; PASS remains blocked until finite, empirical, comparator, and promotion predicates pass.",
            }
        )
    elif lane_id == "MODERN_SCIENCE_COMPARATOR_SUPERIORITY":
        diagnostic = build_comparator_lane_diagnostics(root)
        execution_report = read_json(root / str(diagnostic.get("execution_report_ref") or ""))
        job_payloads: list[dict[str, Any]] = []
        for job in execution_report.get("job_rows", []) or []:
            if isinstance(job, dict) and job.get("job_id"):
                job_payloads.append(build_comparator_domain_job_execution(root, str(job["job_id"])))
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
        command_results.append(
            {
                "cmd": ["internal", "build_comparator_lane_diagnostics"],
                "returncode": 0,
                "stdout_tail": json.dumps(
                    {
                        "lane_id": lane_id,
                        "diagnostic_status": diagnostic["status"],
                        "coverage_gap_total": diagnostic["coverage_gap_total"],
                        "domain_job_total": len(job_payloads),
                        "open_domain_job_total": sum(1 for payload in job_payloads if payload.get("status") != "PASS"),
                        "artifact_ref": diagnostic["artifact_ref"],
                        "artifact_refs": {
                            f"domain_job_{index:03d}_ref": payload.get("artifact_ref")
                            for index, payload in enumerate(job_payloads, start=1)
                        },
                    },
                    ensure_ascii=False,
                ),
                "stderr_tail": "Comparator broad-coverage work orders materialized; benchmark-scoped superiority is not upgraded to broad TOE superiority.",
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
        "why_it_failed": "; ".join(lane_result.get("findings", [])) or "Lane has not satisfied its strict pass predicate.",
        "repair_strategy": lane["closure_condition"],
        "required_capability": lane["owner_capability"],
        "execution_command": lane["execution_command"],
        "pass_predicate": lane["pass_predicate"],
        "next_escalation": "Use generated lane artifacts and subwork orders to close source gaps; rerun strict final TOE validator.",
    }


def execute_active_lanes(root: Path, timeout: int) -> dict[str, Any]:
    before_parts = current_validator_error_parts(root)
    lanes = active_lane_ids(root, before_parts["science_errors"])
    rows = [execute_lane_attempt(root, lane_id, timeout) for lane_id in lanes]
    after_parts = current_validator_error_parts(root)
    before_total = len(before_parts["science_errors"]) + len(before_parts["cerberus_errors"])
    after_total = len(after_parts["science_errors"]) + len(after_parts["cerberus_errors"])
    pass_total = sum(1 for row in rows if row["status"] == "PASS")
    backlog_total = sum(1 for row in rows if row["execution_state"] == "EXECUTED_PROJECTION_CAPABILITY")
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


def research_wave_step(
    *,
    step_index: int,
    purpose: str,
    status: str,
    before_parts: dict[str, list[str]],
    after_parts: dict[str, list[str]],
    result: dict[str, Any],
    changed: list[str],
    defaults: dict[str, Any],
    lane_id: str | None = None,
) -> dict[str, Any]:
    before_total = validator_error_total(before_parts)
    after_total = validator_error_total(after_parts)
    row = normalize_problem_row(
        {
            "research_wave_step_id": f"R017-RESEARCH-WAVE-{step_index:03d}",
            "step_index": step_index,
            "purpose": purpose,
            "lane_id": lane_id,
            "status": status,
            "before_validator_error_total": before_total,
            "before_science_error_total": len(before_parts.get("science_errors", [])),
            "before_cerberus_error_total": len(before_parts.get("cerberus_errors", [])),
            "after_validator_error_total": after_total,
            "after_science_error_total": len(after_parts.get("science_errors", [])),
            "after_cerberus_error_total": len(after_parts.get("cerberus_errors", [])),
            "validator_error_delta": before_total - after_total,
            "changed_artifact_total": len(changed),
            "changed_artifacts": changed[:80],
            "result": result,
        },
        defaults,
    )
    row["pass_fail_reason"] = (
        "Strict validator reached PASS for this step."
        if status == "PASS"
        else row.get("why_it_failed", "Step remains blocked by validator or lane predicates.")
    )
    return row


def execute_research_wave_command_step(
    root: Path,
    *,
    step_index: int,
    purpose: str,
    cmd: list[str],
    timeout: int,
    defaults: dict[str, Any],
) -> dict[str, Any]:
    before_parts = current_validator_error_parts(root)
    before_status = git_status_rows(root)
    result = safe_run_command(root, cmd, timeout)
    after_parts = current_validator_error_parts(root)
    after_status = git_status_rows(root)
    return research_wave_step(
        step_index=step_index,
        purpose=purpose,
        status="PASS" if result.get("returncode") == 0 else "FAIL_CLOSED",
        before_parts=before_parts,
        after_parts=after_parts,
        result=result,
        changed=changed_artifacts(before_status, after_status),
        defaults=defaults,
    )


def execute_research_wave_lane_step(
    root: Path,
    *,
    step_index: int,
    lane_id: str,
    timeout: int,
) -> dict[str, Any]:
    lane = lane_registry_by_id()[lane_id]
    before_parts = current_validator_error_parts(root)
    before_status = git_status_rows(root)
    result = execute_lane_attempt(root, lane_id, timeout)
    after_parts = current_validator_error_parts(root)
    after_status = git_status_rows(root)
    return research_wave_step(
        step_index=step_index,
        purpose=f"{lane_id.lower()}_research_lane",
        lane_id=lane_id,
        status=result.get("status", "FAIL_CLOSED"),
        before_parts=before_parts,
        after_parts=after_parts,
        result=result,
        changed=changed_artifacts(before_status, after_status, artifact_refs_from_lane_attempt(result)),
        defaults={
            "why_it_failed": result.get("why_it_failed") or "Lane predicates remain fail-closed after this research attempt.",
            "repair_strategy": lane["closure_condition"],
            "required_capability": lane["owner_capability"],
            "execution_command": [sys.executable, "tools/oc133_toe_closure_factory.py", "--execute-capability-lane", lane_id, "--write"],
            "pass_predicate": lane["pass_predicate"],
            "next_escalation": result.get("next_escalation") or "Use this lane's subwork orders and capability artifacts for the next source-bound research delta.",
        },
    )


def execute_research_wave_once(root: Path, timeout: int, iteration: int = 1) -> dict[str, Any]:
    generated_at = utc_now()
    before_parts = current_validator_error_parts(root)
    frontier_before = closure_frontier_hash(root, before_parts)
    rows: list[dict[str, Any]] = []
    defaults = {
        "why_it_failed": "This research-wave step did not close the strict final TOE validator.",
        "repair_strategy": "Execute the next dependency-ordered research lane, sync SPOT/projections, and rerun the validator.",
        "required_capability": "Research/TOEClosureFactory",
        "execution_command": [sys.executable, "tools/oc133_toe_closure_factory.py", "--execute-research-wave", "--write", "--until-final-pass"],
        "pass_predicate": "Strict final TOE validator returns PASS without weakening gates.",
        "next_escalation": "Create or execute the next source-bound capability work order; do not assemble r017.",
    }

    rows.append(
        execute_research_wave_command_step(
            root,
            step_index=len(rows) + 1,
            purpose="sync_spot_before_research_wave",
            cmd=[sys.executable, "tools/build_oc_core_1_3_science_spot.py"],
            timeout=timeout,
            defaults=defaults,
        )
    )
    for lane_id in [
        "AI",
        "ENTERPRISE_ARCHITECTURE",
        "MODERN_SCIENCE_COMPARATOR_SUPERIORITY",
        "GRAND_TOE_CLAIM_LEDGER_EVIDENCE",
    ]:
        rows.append(execute_research_wave_lane_step(root, step_index=len(rows) + 1, lane_id=lane_id, timeout=timeout))

    rows.append(
        execute_research_wave_command_step(
            root,
            step_index=len(rows) + 1,
            purpose="sync_spot_after_research_lanes",
            cmd=[sys.executable, "tools/build_oc_core_1_3_science_spot.py"],
            timeout=timeout,
            defaults=defaults,
        )
    )
    rows.append(
        execute_research_wave_command_step(
            root,
            step_index=len(rows) + 1,
            purpose="grand_science_scorecard_sync",
            cmd=[sys.executable, "tools/oc133_grand_science_research_loop.py", "--execute", "--allow-blocked-exit-zero"],
            timeout=timeout,
            defaults=defaults,
        )
    )
    rows.append(
        execute_research_wave_command_step(
            root,
            step_index=len(rows) + 1,
            purpose="science_validator_before_cerberus",
            cmd=[sys.executable, "tools/validate_oc_core_1_3_science_spot.py", "--require-final-toe-pass"],
            timeout=timeout,
            defaults=defaults,
        )
    )

    if rows[-1]["status"] == "PASS":
        cerberus_lane = lane_registry_by_id()["CERBERUS_RELEASE_REVIEW_GATE"]
        rows.append(
            execute_research_wave_command_step(
                root,
                step_index=len(rows) + 1,
                purpose="canonical_cerberus_after_science_clear",
                cmd=cerberus_lane["execution_command"],
                timeout=timeout,
                defaults={
                    "why_it_failed": "Cerberus did not reach clean acceptance for the current science surface.",
                    "repair_strategy": cerberus_lane["closure_condition"],
                    "required_capability": cerberus_lane["owner_capability"],
                    "execution_command": cerberus_lane["execution_command"],
                    "pass_predicate": cerberus_lane["pass_predicate"],
                    "next_escalation": "Refresh deterministic targets and rerun the clean Cerberus gate only after science stays green.",
                },
            )
        )
    else:
        before_parts_for_skip = current_validator_error_parts(root)
        rows.append(
            research_wave_step(
                step_index=len(rows) + 1,
                purpose="canonical_cerberus_after_science_clear",
                status="SKIPPED_DETERMINISTIC_SCIENCE_BLOCKERS_REMAIN",
                before_parts=before_parts_for_skip,
                after_parts=before_parts_for_skip,
                result={
                    "cmd": lane_registry_by_id()["CERBERUS_RELEASE_REVIEW_GATE"]["execution_command"],
                    "returncode": None,
                    "stdout_tail": "",
                    "stderr_tail": "Skipped because science validator remains red; expensive Cerberus/LLM gate is not run while deterministic science blockers remain.",
                },
                changed=[],
                defaults={
                    "why_it_failed": "Science validator errors remain, so the Cerberus/LLM gate is deliberately skipped to avoid wasting expensive review.",
                    "repair_strategy": "Close science lanes first, then refresh Cerberus fingerprints and run clean acceptance.",
                    "required_capability": "Review/Cerberus",
                    "execution_command": lane_registry_by_id()["CERBERUS_RELEASE_REVIEW_GATE"]["execution_command"],
                    "pass_predicate": "Science validator PASS must precede canonical Cerberus clean review.",
                    "next_escalation": "Return to AI/EA, grand-promotion, or comparator capability lanes based on current validator errors.",
                },
            )
        )

    rows.append(
        execute_research_wave_command_step(
            root,
            step_index=len(rows) + 1,
            purpose="final_validator",
            cmd=[sys.executable, "tools/validate_oc_core_1_3_science_spot.py", "--require-final-toe-pass", "--require-cerberus-clean"],
            timeout=timeout,
            defaults=defaults,
        )
    )
    if rows[-1]["status"] == "PASS":
        rows.append(
            execute_research_wave_command_step(
                root,
                step_index=len(rows) + 1,
                purpose="assemble_recovery_r017",
                cmd=[
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
                timeout=timeout,
                defaults=defaults,
            )
        )

    after_parts = current_validator_error_parts(root)
    frontier_after = closure_frontier_hash(root, after_parts)
    before_total = validator_error_total(before_parts)
    after_total = validator_error_total(after_parts)
    missing = explainability_missing_ids([{"schema_id": "OC133_TOE_RESEARCH_WAVE_EXECUTION_v1", "rows": rows}])
    payload = {
        "schema_id": "OC133_TOE_RESEARCH_WAVE_EXECUTION_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": generated_at,
        "wave_id": f"R017-WAVE-{iteration:03d}",
        "iteration": iteration,
        "frontier_hash_before": frontier_before,
        "frontier_hash_after": frontier_after,
        "next_action_ids": [],
        "executor_selected": "dependency_ordered_research_wave",
        "capability_escalation_ids": [],
        "commit_sha": git_head(root),
        "terminal_gate": "R017_READY_TO_ASSEMBLE" if after_total == 0 else "R017_BLOCKED_BY_TOE_CLOSURE_FACTORY",
        "status": "PASS" if after_total == 0 and all(row["status"] == "PASS" for row in rows) else "CAPABILITY_BACKLOG_OPEN",
        "before_validator_error_total": before_total,
        "before_science_error_total": len(before_parts["science_errors"]),
        "before_cerberus_error_total": len(before_parts["cerberus_errors"]),
        "after_validator_error_total": after_total,
        "after_science_error_total": len(after_parts["science_errors"]),
        "after_cerberus_error_total": len(after_parts["cerberus_errors"]),
        "validator_error_delta": before_total - after_total,
        "research_wave_step_total": len(rows),
        "dependency_order": [
            "sync_spot",
            "AI",
            "ENTERPRISE_ARCHITECTURE",
            "MODERN_SCIENCE_COMPARATOR_SUPERIORITY",
            "GRAND_TOE_CLAIM_LEDGER_EVIDENCE",
            "scorecard_sync",
            "Cerberus after science PASS",
            "final_validator",
        ],
        "changed_artifact_total": sum(row.get("changed_artifact_total", 0) for row in rows),
        "toe_problem_explainability_status": "PASS" if not missing else "FAIL",
        "explainability_missing_total": len(missing),
        "explainability_missing_ids": missing,
        "r017_promotion_allowed": after_total == 0 and all(row["status"] == "PASS" for row in rows),
        "no_fake_closure_policy": "Unsupported, demoted, future-research, stale, or blocker rows cannot satisfy r017.",
        "rows": rows,
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def execute_research_wave_until_final_pass(root: Path, timeout: int, max_iterations: int) -> dict[str, Any]:
    generated_at = utc_now()
    iterations: list[dict[str, Any]] = []
    initial_parts = current_validator_error_parts(root)
    frontier_before = closure_frontier_hash(root, initial_parts)
    previous_total = validator_error_total(initial_parts)
    for iteration in range(1, max_iterations + 1):
        wave = execute_research_wave_once(root, timeout, iteration=iteration)
        iterations.append(wave)
        current_total = validator_error_total(current_validator_error_parts(root))
        if current_total == 0 and wave.get("r017_promotion_allowed") is True:
            break
        if previous_total - current_total <= 0:
            break
        previous_total = current_total

    latest = iterations[-1] if iterations else execute_research_wave_once(root, timeout, iteration=1)
    final_parts = current_validator_error_parts(root)
    frontier_after = closure_frontier_hash(root, final_parts)
    rows: list[dict[str, Any]] = []
    for wave in iterations:
        rows.extend(wave.get("rows", []))
    missing = explainability_missing_ids([{"schema_id": "OC133_TOE_RESEARCH_WAVE_EXECUTION_v1", "rows": rows}])
    payload = {
        "schema_id": "OC133_TOE_RESEARCH_WAVE_EXECUTION_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": generated_at,
        "wave_id": "R017-WAVE-SUPERVISED",
        "frontier_hash_before": frontier_before,
        "frontier_hash_after": frontier_after,
        "next_action_ids": [],
        "executor_selected": "until_final_pass_research_wave_supervisor",
        "capability_escalation_ids": [],
        "commit_sha": git_head(root),
        "terminal_gate": "R017_READY_TO_ASSEMBLE" if latest.get("r017_promotion_allowed") is True else "R017_BLOCKED_BY_TOE_CLOSURE_FACTORY",
        "status": "PASS" if latest.get("r017_promotion_allowed") is True else "CAPABILITY_BACKLOG_OPEN",
        "iteration_total": len(iterations),
        "before_validator_error_total": iterations[0]["before_validator_error_total"] if iterations else latest["before_validator_error_total"],
        "after_validator_error_total": latest["after_validator_error_total"],
        "before_science_error_total": iterations[0]["before_science_error_total"] if iterations else latest["before_science_error_total"],
        "after_science_error_total": latest["after_science_error_total"],
        "before_cerberus_error_total": iterations[0]["before_cerberus_error_total"] if iterations else latest["before_cerberus_error_total"],
        "after_cerberus_error_total": latest["after_cerberus_error_total"],
        "validator_error_delta": (iterations[0]["before_validator_error_total"] if iterations else latest["before_validator_error_total"]) - latest["after_validator_error_total"],
        "research_wave_step_total": len(rows),
        "changed_artifact_total": sum(row.get("changed_artifact_total", 0) for row in rows),
        "toe_problem_explainability_status": "PASS" if not missing else "FAIL",
        "explainability_missing_total": len(missing),
        "explainability_missing_ids": missing,
        "r017_promotion_allowed": latest.get("r017_promotion_allowed") is True,
        "supervisor_state": "FINAL_PASS" if latest.get("r017_promotion_allowed") is True else "INTERNAL_RUN_STATE_CAPABILITY_BACKLOG_OPEN",
        "no_progress_policy": "No-progress does not mint r017; it leaves an explicit capability backlog and keeps the internal TOE-closure run alive.",
        "iteration_rows": [
            {
                "iteration": wave["iteration"],
                "status": wave["status"],
                "before_validator_error_total": wave["before_validator_error_total"],
                "after_validator_error_total": wave["after_validator_error_total"],
                "validator_error_delta": wave["validator_error_delta"],
                "research_wave_step_total": wave["research_wave_step_total"],
            }
            for wave in iterations
        ],
        "rows": rows,
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


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
    research_wave: dict[str, Any] | None = None,
    explainability_gate: dict[str, Any] | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    validator_errors = validator_parts["science_errors"] + validator_parts["cerberus_errors"]
    local_exhausted = any(row.get("status") in {"LOCAL_CAPABILITY_EXHAUSTED", "NO_PROGRESS_STOP"} for row in execution_trace)
    root_causes = root_causes or {}
    capability_backlog = capability_backlog or {}
    subwork_orders = subwork_orders or {}
    research_wave = research_wave or {}
    explainability_gate = explainability_gate or build_problem_explainability_gate([root_causes, capability_backlog, subwork_orders], generated_at=generated_at)
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
        "research_wave_status": research_wave.get("status", "MISSING"),
        "research_wave_step_total": research_wave.get("research_wave_step_total", 0),
        "research_wave_validator_delta": research_wave.get("validator_error_delta", 0),
        "toe_problem_explainability_status": explainability_gate.get("toe_problem_explainability_status", "MISSING"),
        "toe_problem_explainability_missing_total": explainability_gate.get("missing_total", 0),
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
    research_wave: dict[str, Any] | None = None,
    explainability_gate: dict[str, Any] | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    validator_parts = validator_parts or {"science_errors": validator_errors, "cerberus_errors": []}
    root_causes = root_causes or {}
    capability_backlog = capability_backlog or {}
    subwork_orders = subwork_orders or {}
    delta_trace = delta_trace or {}
    research_wave = research_wave or {}
    explainability_gate = explainability_gate or build_problem_explainability_gate([root_causes, capability_backlog, subwork_orders, delta_trace, research_wave], generated_at=generated_at)
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
        "research_wave_status": research_wave.get("status", "MISSING"),
        "research_wave_step_total": research_wave.get("research_wave_step_total", 0),
        "research_wave_validator_delta": research_wave.get("validator_error_delta", 0),
        "research_wave_changed_artifact_total": research_wave.get("changed_artifact_total", 0),
        "toe_problem_explainability_status": explainability_gate.get("toe_problem_explainability_status", "MISSING"),
        "toe_problem_explainability_missing_total": explainability_gate.get("missing_total", 0),
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
        f"Research wave: `{cockpit.get('research_wave_status', 'MISSING')}` / steps `{cockpit.get('research_wave_step_total', 0)}`",
        f"Problem explainability: `{cockpit.get('toe_problem_explainability_status', 'MISSING')}`",
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


def build_research_wave_not_run(root: Path, *, generated_at: str | None = None) -> dict[str, Any]:
    parts = current_validator_error_parts(root)
    total = validator_error_total(parts)
    payload = {
        "schema_id": "OC133_TOE_RESEARCH_WAVE_EXECUTION_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": generated_at or utc_now(),
        "status": "NOT_RUN",
        "iteration_total": 0,
        "before_validator_error_total": total,
        "after_validator_error_total": total,
        "before_science_error_total": len(parts["science_errors"]),
        "after_science_error_total": len(parts["science_errors"]),
        "before_cerberus_error_total": len(parts["cerberus_errors"]),
        "after_cerberus_error_total": len(parts["cerberus_errors"]),
        "validator_error_delta": 0,
        "research_wave_step_total": 0,
        "changed_artifact_total": 0,
        "toe_problem_explainability_status": "PASS",
        "explainability_missing_total": 0,
        "explainability_missing_ids": [],
        "r017_promotion_allowed": False,
        "supervisor_state": "NOT_RUN",
        "no_progress_policy": "Research wave has not run yet; r017 remains fail-closed.",
        "iteration_rows": [],
        "rows": [],
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def load_or_build_research_wave(root: Path, *, preserve_existing_generated_at: bool) -> dict[str, Any]:
    path = root / FACTORY_DIR / RESEARCH_WAVE_NAME
    if path.exists():
        payload = read_json(path)
        if payload:
            return payload
    generated_at = existing_generated_at(path) if preserve_existing_generated_at else None
    return build_research_wave_not_run(root, generated_at=generated_at)


def execution_trace_from_research_wave(research_wave: dict[str, Any]) -> list[dict[str, Any]]:
    if research_wave.get("status") == "NOT_RUN":
        return []
    return [
        {
            "step_index": 1,
            "purpose": "research_wave_until_final_pass" if research_wave.get("iteration_total") else "research_wave",
            "status": research_wave.get("status", "FAIL_CLOSED"),
            "result": {
                "before_validator_error_total": research_wave.get("before_validator_error_total"),
                "after_validator_error_total": research_wave.get("after_validator_error_total"),
                "validator_error_delta": research_wave.get("validator_error_delta"),
                "research_wave_step_total": research_wave.get("research_wave_step_total"),
                "changed_artifact_total": research_wave.get("changed_artifact_total"),
                "supervisor_state": research_wave.get("supervisor_state"),
                "wave_trace": research_wave.get("rows", []),
            },
        }
    ]


def expected_files(
    root: Path,
    *,
    execute: bool = False,
    execute_research_wave: bool = False,
    until_final_pass: bool = False,
    timeout: int = 900,
    max_iterations: int = 6,
    preserve_existing_generated_at: bool = False,
) -> dict[Path, str]:
    base = root / FACTORY_DIR
    if execute_research_wave and until_final_pass:
        research_wave = execute_research_wave_until_final_pass(root, timeout, max_iterations)
        execution_trace = execution_trace_from_research_wave(research_wave)
    elif execute_research_wave:
        research_wave = execute_research_wave_once(root, timeout, iteration=1)
        execution_trace = execution_trace_from_research_wave(research_wave)
    elif until_final_pass:
        research_wave = load_or_build_research_wave(root, preserve_existing_generated_at=preserve_existing_generated_at)
        execution_trace = execute_until_final_pass(root, timeout, max_iterations)
    elif execute:
        research_wave = load_or_build_research_wave(root, preserve_existing_generated_at=preserve_existing_generated_at)
        execution_trace = execute_closure_cycle(root, timeout)
    else:
        research_wave = load_or_build_research_wave(root, preserve_existing_generated_at=preserve_existing_generated_at)
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
    explainability_generated_at = existing_generated_at(base / PROBLEM_EXPLAINABILITY_GATE_NAME) if preserve_existing_generated_at else None
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
    explainability_gate = build_problem_explainability_gate(
        [root_causes, capability_backlog, subwork_orders, delta_trace, research_wave],
        generated_at=explainability_generated_at,
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
        research_wave=research_wave,
        explainability_gate=explainability_gate,
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
        research_wave=research_wave,
        explainability_gate=explainability_gate,
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
        base / PROBLEM_EXPLAINABILITY_GATE_NAME: stable_json(explainability_gate),
        base / RESEARCH_WAVE_NAME: stable_json(research_wave),
        base / STATE_NAME: stable_json(state),
        base / COCKPIT_NAME: stable_json(cockpit),
        base / COCKPIT_MD_NAME: render_cockpit_md(cockpit, lanes, obligations),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the OC Core 1.3.3 TOE Closure Factory.")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--execute", action="store_true", help="Run the sync/research/Cerberus/validator cycle before writing outputs.")
    parser.add_argument("--execute-research-wave", action="store_true", help="Run dependency-ordered TOE research lanes with validator delta tracing before writing outputs.")
    parser.add_argument("--until-final-pass", action="store_true", help="Iterate closure cycles until final validator PASS or honest local capability exhaustion.")
    parser.add_argument("--emit-root-cause-ledger", action="store_true", help="Emit only the current root-cause ledger.")
    parser.add_argument("--max-iterations", type=int, default=6)
    parser.add_argument("--execute-lane", choices=[row["lane_id"] for row in lane_registry_rows()])
    parser.add_argument("--execute-capability-lane", choices=[row["lane_id"] for row in lane_registry_rows()])
    parser.add_argument("--execute-source-intake-work-order", help="Execute one AI/EA source-intake work order.")
    parser.add_argument("--execute-comparator-gap", help="Execute one modern-science comparator coverage gap.")
    parser.add_argument("--execute-comparator-domain-job", help="Execute one modern-science comparator domain job such as MS-COV-JOB-001.")
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args(argv)
    if args.execute_source_intake_work_order:
        payload = build_projection_source_intake_execution(ROOT, args.execute_source_intake_work_order)
        lane_id = payload.get("lane_id") or "UNKNOWN"
        artifact_ref = payload.get("artifact_ref")
        path = ROOT / artifact_ref if isinstance(artifact_ref, str) and artifact_ref else ROOT / projection_source_intake_execution_rel(str(lane_id), args.execute_source_intake_work_order)
        result = validation_result({path: stable_json(payload)}, write=args.write)
        print(json.dumps(result if args.write or args.check else payload, ensure_ascii=False, indent=2, sort_keys=True))
        return 1 if args.check and result["state"] != "PASS" else 0
    if args.execute_comparator_gap:
        payload = build_comparator_gap_execution(ROOT, args.execute_comparator_gap)
        artifact_ref = payload.get("artifact_ref")
        path = ROOT / artifact_ref if isinstance(artifact_ref, str) and artifact_ref else ROOT / comparator_gap_execution_rel(args.execute_comparator_gap)
        result = validation_result({path: stable_json(payload)}, write=args.write)
        print(json.dumps(result if args.write or args.check else payload, ensure_ascii=False, indent=2, sort_keys=True))
        return 1 if args.check and result["state"] != "PASS" else 0
    if args.execute_comparator_domain_job:
        payload = build_comparator_domain_job_execution(ROOT, args.execute_comparator_domain_job)
        path = ROOT / FACTORY_DIR / "lane_execution" / "MODERN_SCIENCE_COMPARATOR_SUPERIORITY" / "domain_jobs" / f"{args.execute_comparator_domain_job}.json"
        result = validation_result({path: stable_json(payload)}, write=args.write)
        print(json.dumps(result if args.write or args.check else payload, ensure_ascii=False, indent=2, sort_keys=True))
        return 1 if args.check and result["state"] != "PASS" else 0
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
    preserve_existing_generated_at = args.check and not args.write and not args.execute and not args.execute_research_wave and not args.until_final_pass
    result = validation_result(
        expected_files(
            ROOT,
            execute=args.execute,
            execute_research_wave=args.execute_research_wave,
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
