from __future__ import annotations

import argparse
import hashlib
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
CAPABILITY_IMPLEMENTATION_REGISTRY_NAME = "OC133_TOE_CAPABILITY_IMPLEMENTATION_REGISTRY.json"
CAPABILITY_IMPLEMENTATION_DIR = FACTORY_DIR / "capability_implementation"
AUTONOMOUS_SUPERVISOR_DIR = FACTORY_DIR / "autonomous_supervisor"
AUTONOMOUS_CAPABILITY_DEVELOPMENT_LEDGER_NAME = "OC133_TOE_AUTONOMOUS_CAPABILITY_DEVELOPMENT_LEDGER.json"
SCIENTIFIC_FRONTIER_NAME = "OC133_TOE_SCIENTIFIC_FRONTIER.json"
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


def sha256_file(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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

PROJECTION_TEMPLATE_THEOREM_IDS = {
    "AI": "T133-HYBRID",
    "ENTERPRISE_ARCHITECTURE": "T133-BOUNDARY",
}

PROJECTION_TEMPLATE_PUBLIC_SCOPES = {
    "AI": (
        "Bounded AI and agentic-system projection: an AI workflow is inside the OC formal "
        "projection only when its inference, planning, or tool-use step is represented as a "
        "declared typed update route with explicit source and target state types, admissible "
        "operator obligations, evidence rows, comparator baselines, and falsifier conditions."
    ),
    "ENTERPRISE_ARCHITECTURE": (
        "Bounded enterprise-architecture projection: an architecture decision or operating-state "
        "assessment is inside the OC formal projection only when its variables, thresholds, "
        "classifier boundary, evidence rows, comparator alternatives, and falsifier conditions "
        "are explicitly declared."
    ),
}

PROJECTION_TEMPLATE_SOURCE_NOTES = {
    "AI": (
        "This is a domain-projection boundary claim, not an unrestricted assertion that OC solves "
        "all AI evaluation, agent control, or machine-learning generalization problems. It binds "
        "the lane to the existing typed-operator theorem and finite witnesses only."
    ),
    "ENTERPRISE_ARCHITECTURE": (
        "This is a domain-projection boundary claim, not an unrestricted assertion that OC solves "
        "all enterprise architecture, organizational design, or operating-model optimization "
        "problems. It binds the lane to the existing boundary-classifier theorem and finite "
        "witnesses only."
    ),
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


def projection_template_source_row(lane_id: str) -> dict[str, Any]:
    theorem_id = PROJECTION_TEMPLATE_THEOREM_IDS[lane_id]
    return {
        "claim_id": theorem_id,
        "projection_template_id": f"OC133-{lane_id}-THEOREM_NATIVE-PROJECTION-TEMPLATE",
        "claim": PROJECTION_TEMPLATE_PUBLIC_SCOPES[lane_id],
        "public_claim_scope": PROJECTION_TEMPLATE_PUBLIC_SCOPES[lane_id],
        "public_status": "PROMOTED_BOUNDED_NO_SEND_V12",
        "evidence_ref": "proofs/proof_sheets/T133-HYBRID.md" if lane_id == "AI" else "proofs/proof_sheets/T133-BOUNDARY.md",
        "_source_json_path": f"$.projection_templates.{lane_id}",
        "source_note": PROJECTION_TEMPLATE_SOURCE_NOTES[lane_id],
    }


def projection_template_candidate(root: Path, lane_id: str, index: int) -> dict[str, Any]:
    row = build_projection_row_from_claim(root, lane_id, projection_template_source_row(lane_id), index)
    row["projection_id"] = f"OC133-FINAL-TOE-{lane_id}-THEOREM-NATIVE-001"
    row["template_support_policy"] = "THEOREM_NATIVE_DOMAIN_PROJECTION_ONLY"
    row["source_note"] = PROJECTION_TEMPLATE_SOURCE_NOTES[lane_id]
    row["domain_projection_boundary"] = (
        "This row may close the projection-lane support gate only as a bounded formal projection. "
        "It does not close broad modern-science superiority or the promoted grand TOE claim."
    )
    return row


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
    template_candidate = projection_template_candidate(root, lane_id, len(candidate_rows) + len(rejected_rows) + 1)
    template_checks = projection_row_support_checks(root, template_candidate)
    template_candidate["support_checks"] = template_checks
    template_candidate["closure_verdict"] = "PASS" if all(template_checks.values()) else "FAIL_CLOSED"
    template_candidate["source_candidate_kind"] = "DETERMINISTIC_THEOREM_NATIVE_DOMAIN_PROJECTION_TEMPLATE"
    if all(template_checks.values()):
        candidate_rows.append(template_candidate)
    else:
        rejected_rows.append(template_candidate)
    payload = {
        "schema_id": "OC133_TOE_PROJECTION_SOURCE_MINING_REPORT_v1",
        "generated_at": generated_at,
        "lane_id": lane_id,
        "status": "PASS" if candidate_rows else "SOURCE_GAP_OPEN",
        "source_ref_total": len(PROJECTION_SOURCE_REFS),
        "candidate_total": len(candidate_rows),
        "rejected_candidate_total": len(rejected_rows),
        "deterministic_projection_template_enabled": True,
        "deterministic_projection_template_theorem_id": PROJECTION_TEMPLATE_THEOREM_IDS[lane_id],
        "deterministic_projection_template_support_checks": template_checks,
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

COMPARATOR_RESEARCH_ARTIFACT_BASE = Path("validation/heldout/grand_science/modern_science_coverage_artifacts")

COMPARATOR_FALLBACK_SOURCE_BLOCKS = {
    "formal_mathematics_and_logic": {
        "source_id": "FORMAL_MATH_LEAN4_AND_OC133_PROOF_CORPUS",
        "source_name": "Lean 4 / OC133 finite-model proof corpus",
        "source_authority": "Lean project documentation and OC133 formal proof corpus",
        "official_documentation_url": "https://lean-lang.org/documentation/",
        "official_endpoint_url": "https://github.com/leanprover/lean4",
        "required_local_snapshot_ref": "proofs/FINITE_MODEL_CHECKS_1_3_3.json",
        "required_lock_ref": "proofs/finite_model_checks/OC133_FINITE_MODEL_INPUTS.json",
        "source_kind": "formal_proof_corpus",
    },
    "medical_health_sciences": {
        "source_id": "PUBLIC_HEALTH_AND_CLINICAL_SOURCE_TRIAD",
        "source_name": "ClinicalTrials.gov / CDC / FDA / NIH public health sources",
        "source_authority": "US public clinical, public-health, regulatory, and biomedical agencies",
        "official_documentation_url": "https://clinicaltrials.gov/data-api/about-api",
        "official_endpoint_url": "https://clinicaltrials.gov/api/v2/studies",
        "required_local_snapshot_ref": None,
        "required_lock_ref": None,
        "source_kind": "public_clinical_health_source_registry",
    },
}

COMPARATOR_FALLBACK_TARGET_BLOCKS = {
    "medical_health_sciences::clinical_outcomes_and_biomarkers": {
        "name": "heldout_public_clinical_trial_outcome_or_biomarker_panel",
        "target_fields": ["nctId", "condition", "intervention", "outcomeMeasure", "timeFrame", "result_value_or_group_summary"],
        "extraction_rule": "ClinicalTrials.gov public rows must be locked before target unsealing; outcome values cannot be used for OC formula selection.",
    },
    "medical_health_sciences::epidemiological_transmission_and_risk": {
        "name": "heldout_public_epidemiological_incidence_or_risk_series",
        "target_fields": ["location", "date_or_week", "case_count_or_rate", "risk_stratum", "source_revision_hash"],
        "extraction_rule": "Public-health time series must be version-locked before scoring; held-out incidence/risk values remain hidden until predictions materialize.",
    },
    "medical_health_sciences::pharmacology_toxicology_and_dose_response": {
        "name": "heldout_public_drug_event_toxicology_or_dose_response_panel",
        "target_fields": ["substance_or_drug_id", "dose_or_exposure_bin", "event_or_endpoint", "count_or_effect_size", "source_revision_hash"],
        "extraction_rule": "Regulatory/public pharmacology rows must be source-locked before scoring; endpoint values cannot tune OC or comparator formulas.",
    },
}


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
        artifact_overrides = {
            artifact_key: comparator_gap_research_artifact_passes(root, str(gap.get("gap_id") or ""), artifact_key)
            for artifact_key in COMPARATOR_REQUIRED_ARTIFACT_KEYS
        }
        source_capsule_refs = [
            row.get("source_capsule_ref")
            for row in work_order.get("source_refs", [])
            if isinstance(row, dict) and row.get("source_capsule_ref")
        ]
        source_capsule_existing_total = sum(1 for ref in source_capsule_refs if (root / str(ref)).exists())
        artifact_status = {
            "verified_open_source_capsule": artifact_overrides["verified_open_source_capsule"]
            or (bool(source_capsule_refs) and source_capsule_existing_total == len(source_capsule_refs)),
            "benchmark_case": artifact_overrides["benchmark_case"]
            or (bool(work_order.get("benchmark_case_ref")) and (root / str(work_order.get("benchmark_case_ref"))).exists()),
            "incumbent_comparator": artifact_overrides["incumbent_comparator"]
            or (bool(work_order.get("incumbent_comparator_ref")) and (root / str(work_order.get("incumbent_comparator_ref"))).exists()),
            "oc_prediction_scoring_row": artifact_overrides["oc_prediction_scoring_row"]
            or (bool(work_order.get("oc_scoring_ref")) and (root / str(work_order.get("oc_scoring_ref"))).exists()),
            "uncertainty_row": artifact_overrides["uncertainty_row"]
            or (bool(work_order.get("uncertainty_ref")) and (root / str(work_order.get("uncertainty_ref"))).exists()),
            "falsifier_row": artifact_overrides["falsifier_row"]
            or (bool(work_order.get("falsifier_ref")) and (root / str(work_order.get("falsifier_ref"))).exists()),
            "replay_record": artifact_overrides["replay_record"]
            or (bool(work_order.get("replay_record_ref")) and (root / str(work_order.get("replay_record_ref"))).exists()),
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


def comparator_gap_artifact_execution_rel(gap_id: str, artifact_key: str) -> Path:
    payload_hash = artifact_hash({"gap_id": gap_id, "artifact_key": artifact_key})[:16]
    return lane_execution_base("MODERN_SCIENCE_COMPARATOR_SUPERIORITY") / "artifact_jobs" / f"artifact_{payload_hash}.json"


def comparator_gap_scoring_work_order_rel(gap_id: str) -> Path:
    gap_hash = artifact_hash({"gap_id": gap_id})[:16]
    return lane_execution_base("MODERN_SCIENCE_COMPARATOR_SUPERIORITY") / "scoring_work_orders" / f"scoring_{gap_hash}.json"


def comparator_gap_scoring_work_order_exists(root: Path, gap_id: str) -> bool:
    payload = read_json(root / comparator_gap_scoring_work_order_rel(gap_id))
    return payload.get("schema_id") == "OC133_MODERN_SCIENCE_COMPARATOR_SCORING_WORK_ORDER_v1" and payload.get("gap_id") == gap_id


def comparator_gap_scoring_subartifact_rel(gap_id: str, subartifact_id: str) -> Path:
    payload_hash = artifact_hash({"gap_id": gap_id, "subartifact_id": subartifact_id})[:16]
    return (
        lane_execution_base("MODERN_SCIENCE_COMPARATOR_SUPERIORITY")
        / "scoring_subartifact_jobs"
        / f"subartifact_{payload_hash}.json"
    )


def comparator_scoring_executor_backlog_rel() -> Path:
    return lane_execution_base("MODERN_SCIENCE_COMPARATOR_SUPERIORITY") / "OC133_MODERN_SCIENCE_COMPARATOR_SCORING_EXECUTOR_BACKLOG.json"


def comparator_gap_research_artifact_rel(gap_id: str, artifact_key: str) -> Path:
    safe_key = re.sub(r"[^A-Za-z0-9_.-]+", "_", artifact_key).strip("_") or "unknown_artifact"
    gap_hash = artifact_hash({"gap_id": gap_id})[:16]
    return COMPARATOR_RESEARCH_ARTIFACT_BASE / gap_hash / f"{safe_key}.json"


def legacy_comparator_gap_research_artifact_rel(gap_id: str, artifact_key: str) -> Path:
    safe_gap = re.sub(r"[^A-Za-z0-9_.-]+", "_", gap_id).strip("_") or "UNKNOWN_GAP"
    safe_key = re.sub(r"[^A-Za-z0-9_.-]+", "_", artifact_key).strip("_") or "unknown_artifact"
    return COMPARATOR_RESEARCH_ARTIFACT_BASE / safe_gap / f"{safe_key}.json"


def comparator_gap_research_artifact_passes(root: Path, gap_id: str, artifact_key: str) -> bool:
    for rel_path in (
        comparator_gap_research_artifact_rel(gap_id, artifact_key),
        legacy_comparator_gap_research_artifact_rel(gap_id, artifact_key),
    ):
        payload = read_json(root / rel_path)
        if payload.get("status") == "PASS" and payload.get("artifact_key") == artifact_key:
            return True
    return False


def comparator_gap_research_artifact_exists(root: Path, gap_id: str, artifact_key: str) -> bool:
    payload = comparator_gap_research_artifact(root, gap_id, artifact_key)
    return payload.get("artifact_key") == artifact_key


def comparator_gap_research_artifact(root: Path, gap_id: str, artifact_key: str) -> dict[str, Any]:
    for rel_path in (
        comparator_gap_research_artifact_rel(gap_id, artifact_key),
        legacy_comparator_gap_research_artifact_rel(gap_id, artifact_key),
    ):
        payload = read_json(root / rel_path)
        if payload.get("artifact_key") == artifact_key:
            return payload
    return {}


def comparator_current_evidence(root: Path, executable_spec: dict[str, Any]) -> dict[str, Any]:
    evidence = executable_spec.get("current_evidence", {}) if isinstance(executable_spec.get("current_evidence"), dict) else {}
    evidence_ref = evidence.get("executable_evidence_ref")
    evidence_path = root / str(evidence_ref) if evidence_ref else None
    evidence_pack = read_json(evidence_path) if evidence_path else {}
    residuals = evidence_pack.get("residuals", {}) if isinstance(evidence_pack.get("residuals"), dict) else {}
    material_margin = residuals.get("material_margin_met")
    if material_margin is None and isinstance(residuals.get("model"), (int, float)) and isinstance(residuals.get("comparator"), (int, float)):
        material_margin = residuals.get("model") < residuals.get("comparator")
    pack_status_text = json.dumps(
        {
            "evidence_status": evidence.get("status"),
            "coverage_closure_status": executable_spec.get("coverage_closure_status"),
            "pack_status": evidence_pack.get("pack_status") or evidence_pack.get("status"),
            "coverage_closure_allowed": evidence_pack.get("coverage_closure_allowed"),
        },
        ensure_ascii=False,
        sort_keys=True,
    ).upper()
    fail_tokens = ("FAIL", "BLOCKED", "NOT_MET")
    return {
        "executable_evidence_exists": evidence.get("executable_evidence_exists") is True,
        "evidence_ref": evidence_ref,
        "evidence_ref_exists": bool(evidence_path and evidence_path.exists()),
        "evidence_pack_hash": sha256_file(evidence_path) if evidence_path and evidence_path.exists() else "",
        "material_margin_met": material_margin is True,
        "fail_closed_status_present": any(token in pack_status_text for token in fail_tokens),
        "pack_status_text": pack_status_text,
        "evidence_pack_summary": {
            "schema_id": evidence_pack.get("schema_id"),
            "pack_status": evidence_pack.get("pack_status") or evidence_pack.get("status"),
            "coverage_closure_allowed": evidence_pack.get("coverage_closure_allowed"),
            "residuals": residuals,
        },
    }


def formal_route_exact_evidence(root: Path, executable_spec: dict[str, Any]) -> dict[str, Any]:
    evidence = executable_spec.get("current_evidence", {}) if isinstance(executable_spec.get("current_evidence"), dict) else {}
    execution = executable_spec.get("execution_requirements", {}) if isinstance(executable_spec.get("execution_requirements"), dict) else {}
    replay_commands = execution.get("replay_commands") or ([execution.get("replay_command")] if execution.get("replay_command") else [])
    formal_exact = evidence.get("formal_exact_evidence_exists") is True
    status_text = json.dumps(
        {
            "current_evidence_status": evidence.get("status"),
            "coverage_closure_status": executable_spec.get("coverage_closure_status"),
            "coverage_closure_allowed": evidence.get("coverage_closure_allowed"),
            "remaining_blockers": evidence.get("remaining_blockers"),
        },
        ensure_ascii=False,
        sort_keys=True,
    ).upper()
    allowed_status_tokens = (
        "FORMAL_SUPPORT_ACCEPTED",
        "EXACT_STATISTICAL_PROBABILISTIC_FORMAL_CORPUS_BOUND_SCORER_PASS",
        "EXACT_COMPLEXITY_ALGORITHMIC_FORMAL_CORPUS_BOUND_SCORER_PASS",
        "EXISTING_FORMAL_ARTIFACTS_BOUND_BUT_EXACT_COVERAGE_EVIDENCE_NOT_CERTIFIED",
    )
    replay_results = [
        safe_run_command(root, str(command).split(), 300)
        for command in replay_commands[:4]
        if isinstance(command, str) and command.strip()
    ]
    replay_pass = bool(replay_results) and all(row.get("returncode") == 0 for row in replay_results)
    # Formal-route rows are deliberately not empirical evidence and do not unlock broad TOE wording by themselves.
    # This helper only certifies the local scoring/replay artifact for the comparator-gap dependency graph.
    return {
        "formal_route": True,
        "formal_exact_evidence_exists": formal_exact,
        "allowed_status_token_present": any(token in status_text for token in allowed_status_tokens),
        "coverage_closure_allowed": evidence.get("coverage_closure_allowed"),
        "broad_modern_science_superiority_allowed": evidence.get("broad_modern_science_superiority_allowed"),
        "empirical_numeric_prediction_allowed": execution.get("empirical_numeric_prediction_allowed"),
        "replay_command_total": len(replay_commands),
        "replay_pass": replay_pass,
        "replay_results": replay_results,
        "status_text": status_text,
        "status": "PASS" if formal_exact and replay_pass and any(token in status_text for token in allowed_status_tokens) else "OPEN",
    }


def comparator_scoring_root_cause(evidence: dict[str, Any], executable_spec: dict[str, Any]) -> tuple[str, str]:
    if not executable_spec:
        return (
            "EXECUTABLE_SPEC_MISSING_FOR_SCORING",
            "No executable comparator specification is bound to this gap, so the system cannot build a target-hidden OC scoring row.",
        )
    if not evidence.get("executable_evidence_exists"):
        return (
            "SCORING_EVIDENCE_NOT_MATERIALIZED",
            "The lane declares no executable evidence pack for the OC-vs-comparator scoring row.",
        )
    if evidence.get("evidence_ref") and not evidence.get("evidence_ref_exists"):
        return (
            "SCORING_EVIDENCE_REF_MISSING",
            f"The executable evidence ref `{evidence.get('evidence_ref')}` is declared but the file is absent.",
        )
    if evidence.get("fail_closed_status_present"):
        return (
            "SCORING_PACK_FAIL_CLOSED",
            "The current evidence pack carries a fail-closed status token, so broad comparator credit is prohibited.",
        )
    if not evidence.get("material_margin_met"):
        return (
            "COMPARATOR_BASELINE_NOT_BEATEN_WITH_UNCERTAINTY",
            "The current scoring pack does not demonstrate a material OC advantage over the preregistered comparator under uncertainty.",
        )
    return (
        "SCORING_ROW_READY_REPLAY_REQUIRED",
        "Strict scoring predicates are satisfied; the remaining blocker is independent replay and register propagation.",
    )


def build_comparator_gap_scoring_work_order(root: Path, gap_id: str) -> dict[str, Any]:
    gap_payload = comparator_gap_execution_payload(root, gap_id)
    queue_row = comparator_lane_queue_rows_by_gap(root).get(gap_id, {})
    executable_spec = queue_row.get("executable_work_order", {}) if isinstance(queue_row.get("executable_work_order"), dict) else {}
    evidence = comparator_current_evidence(root, executable_spec)
    root_cause, why = comparator_scoring_root_cause(evidence, executable_spec)
    data_lanes = [row for row in queue_row.get("required_data_lanes", []) or [] if isinstance(row, dict)]
    proof_lanes = [row for row in queue_row.get("required_proof_lanes", []) or [] if isinstance(row, (dict, str))]
    lane_by_role = {
        str(row.get("lane_role")): row
        for row in data_lanes
        if row.get("lane_role")
    }
    source_lane = lane_by_role.get("official_data_source", {})
    target_lane = lane_by_role.get("target_variable", {})
    model_lane = lane_by_role.get("formula_or_model", {})
    comparator_lane = lane_by_role.get("incumbent_comparator", {})
    uncertainty_lane = lane_by_role.get("uncertainty_policy", {}) or lane_by_role.get("residual_metric", {})
    falsifier_lane = lane_by_role.get("falsifier", {}) or lane_by_role.get("negative_control", {})
    payload = {
        "schema_id": "OC133_MODERN_SCIENCE_COMPARATOR_SCORING_WORK_ORDER_v1",
        "generated_at": stable_generated_at(root, comparator_gap_scoring_work_order_rel(gap_id)),
        "lane_id": "MODERN_SCIENCE_COMPARATOR_SUPERIORITY",
        "gap_id": gap_id,
        "status": "PASS" if root_cause == "SCORING_ROW_READY_REPLAY_REQUIRED" else "OPEN",
        "domain_class_id": gap_payload.get("domain_class_id") or queue_row.get("domain_class_id"),
        "phenomenon_class_id": gap_payload.get("phenomenon_class_id") or queue_row.get("phenomenon_class_id"),
        "work_order_id": queue_row.get("work_order_id"),
        "queue_row_found": bool(queue_row),
        "executable_spec_found": bool(executable_spec),
        "root_cause_class": root_cause,
        "why_it_failed": why,
        "repair_strategy": "Materialize a target-hidden scoring pack from the declared source, target, OC model, incumbent comparator, uncertainty rule, falsifier, and replay command; broad superiority remains blocked until the scoring row beats the comparator and replay passes.",
        "required_capability": "Research/ScoringExecutor",
        "required_next_artifacts": [
            {
                "artifact_id": "source_snapshot_acquisition",
                "required_source": source_lane or executable_spec.get("official_data_source", {}),
                "pass_predicate": "Open/free source snapshot exists locally, is hash-bound, and satisfies source separation policy.",
            },
            {
                "artifact_id": "target_hidden_task_table",
                "required_target": target_lane or executable_spec.get("target_variable", {}),
                "pass_predicate": "Target table is locked before scoring and hidden fields do not leak into model selection.",
            },
            {
                "artifact_id": "oc_formula_or_model",
                "required_model": model_lane or executable_spec.get("formula_requirement", {}) or executable_spec.get("residual_requirement", {}),
                "pass_predicate": "OC prediction/scoring rule is preregistered before target unsealing.",
            },
            {
                "artifact_id": "incumbent_comparator_scoring",
                "required_comparator": comparator_lane or executable_spec.get("incumbent_comparator_requirement", {}),
                "pass_predicate": "Incumbent comparator is scored on the same held-out targets.",
            },
            {
                "artifact_id": "residuals_materiality_uncertainty",
                "required_uncertainty": uncertainty_lane or executable_spec.get("uncertainty_requirement", {}),
                "pass_predicate": "OC residual advantage exceeds preregistered materiality threshold under uncertainty.",
            },
            {
                "artifact_id": "controls_and_falsifiers",
                "required_falsifier": falsifier_lane or executable_spec.get("falsifier_requirement", {}) or executable_spec.get("negative_control_requirement", {}),
                "pass_predicate": "Negative controls and falsifiers are declared and replayed without post-hoc adjustment.",
            },
            {
                "artifact_id": "independent_replay",
                "required_execution": executable_spec.get("execution_requirements", {}),
                "pass_predicate": "Clean replay regenerates the evidence pack hash and result verdict.",
            },
        ],
        "current_evidence": evidence,
        "proof_lane_requirements": proof_lanes,
        "execution_command": [sys.executable, "tools/oc133_toe_closure_factory.py", "--execute-comparator-scoring-work-order", gap_id, "--write"],
        "pass_predicate": "oc_prediction_scoring_row PASS requires executable evidence, existing evidence ref, material OC margin over comparator, no fail-closed status, then replay_record PASS.",
        "validator_binding": f"comparator_gap::{gap_id}::oc_prediction_scoring_row",
        "next_escalation": "If this work order remains OPEN, implement the listed artifact executor with the exact source/target/model/comparator/falsifier fields; do not promote broad superiority.",
        "no_fake_closure_policy": "A scoring work order is not scoring evidence. It narrows the research task and cannot close modern_science_comparator_superiority until its evidence pack passes.",
        "source_refs": [
            "reports/OC_CORE_1_3_3_MODERN_SCIENCE_COVERAGE_LANE_QUEUE.json",
            "benchmarks/modern_science/OC133_MODERN_SCIENCE_COVERAGE_WORK_ORDERS.json",
            "comparators/modern_science/OC133_MODERN_SCIENCE_COVERAGE_REGISTER.json",
        ],
    }
    payload["artifact_ref"] = rel(root, root / comparator_gap_scoring_work_order_rel(gap_id))
    payload["artifact_hash"] = artifact_hash(payload)
    write_json_artifact(root, comparator_gap_scoring_work_order_rel(gap_id), payload)
    return payload


def comparator_scoring_work_orders(root: Path) -> list[dict[str, Any]]:
    base = root / lane_execution_base("MODERN_SCIENCE_COMPARATOR_SUPERIORITY") / "scoring_work_orders"
    rows: list[dict[str, Any]] = []
    if base.exists():
        for path in sorted(base.glob("*.json")):
            payload = read_json(path)
            if payload.get("schema_id") == "OC133_MODERN_SCIENCE_COMPARATOR_SCORING_WORK_ORDER_v1":
                rows.append(payload)
    return rows


def build_comparator_scoring_executor_backlog(root: Path) -> dict[str, Any]:
    open_gap_ids = [
        str(row.get("gap_id"))
        for row in comparator_execution_gap_rows(root)
        if row.get("status") != "PASS" and "oc_prediction_scoring_row" in set(row.get("missing_artifacts") or [])
    ]
    for gap_id in open_gap_ids:
        # Rebuild every open scoring work order from the current dispatcher frontier.
        # Otherwise a repaired executable spec can leave an old root-cause row
        # stuck in the backlog and the autonomous graph will keep selecting a
        # capability that has already been implemented.
        build_comparator_gap_scoring_work_order(root, gap_id)
    rows: list[dict[str, Any]] = []
    root_cause_counts: dict[str, int] = {}
    open_gap_id_set = set(open_gap_ids)
    stale_scoring_order_refs: list[str] = []
    for scoring_order in comparator_scoring_work_orders(root):
        scoring_gap_id = str(scoring_order.get("gap_id") or "")
        if scoring_gap_id not in open_gap_id_set:
            if scoring_order.get("artifact_ref"):
                stale_scoring_order_refs.append(str(scoring_order.get("artifact_ref")))
            continue
        if scoring_order.get("status") == "PASS":
            continue
        root_cause = str(scoring_order.get("root_cause_class") or "UNKNOWN")
        root_cause_counts[root_cause] = root_cause_counts.get(root_cause, 0) + 1
        gap_id = str(scoring_order.get("gap_id") or "")
        if root_cause == "EXECUTABLE_SPEC_MISSING_FOR_SCORING":
            sub_artifacts = [
                {
                    "artifact_id": "executable_scoring_spec_generation",
                    "required_capability": "Research/BenchmarkDesign",
                    "pass_predicate": "Coverage lane has a complete executable_work_order with source, target, OC scoring rule, comparator, uncertainty, falsifier, and replay requirements.",
                }
            ]
        elif root_cause == "SCORING_PACK_FAIL_CLOSED":
            sub_artifacts = [
                {
                    "artifact_id": "strict_evidence_pack_diagnosis",
                    "required_capability": "Research/ScoringExecutor",
                    "pass_predicate": "Fail-closed evidence pack has an explicit diagnosis and a source-bound repair path; no broad superiority credit is granted.",
                },
                {
                    "artifact_id": "model_or_claim_repair_decision",
                    "required_capability": "Research/ModelComparison",
                    "pass_predicate": "Either OC materially beats the preregistered comparator after a valid repair, or the broad superiority claim remains blocked.",
                },
            ]
        else:
            sub_artifacts = scoring_order.get("required_next_artifacts") or []
        for index, artifact in enumerate(sub_artifacts, start=1):
            artifact_id = str(artifact.get("artifact_id") or f"subtask_{index:02d}")
            row = normalize_problem_row(
                {
                    "subwork_order_id": f"R017-SCORING-{artifact_hash({'gap_id': gap_id, 'artifact_id': artifact_id})[:16]}",
                    "lane_id": "MODERN_SCIENCE_COMPARATOR_SUPERIORITY",
                    "gap_id": gap_id,
                    "domain_class_id": scoring_order.get("domain_class_id"),
                    "phenomenon_class_id": scoring_order.get("phenomenon_class_id"),
                    "root_cause_class": root_cause,
                    "missing_artifact_type": "oc_prediction_scoring_row",
                    "scoring_subartifact_id": artifact_id,
                    "status": "OPEN",
                    "source_work_order_ref": scoring_order.get("artifact_ref"),
                    "required_source_block": artifact,
                    "why_it_failed": scoring_order.get("why_it_failed"),
                    "repair_strategy": f"Build `{artifact_id}` for gap `{gap_id}` from governed open/free sources, then rerun the target-hidden scorer and strict validator.",
                    "required_capability": artifact.get("required_capability") or scoring_order.get("required_capability") or "Research/ScoringExecutor",
                    "execution_command": [sys.executable, "tools/oc133_toe_closure_factory.py", "--execute-comparator-scoring-work-order", gap_id, "--write"],
                    "pass_predicate": artifact.get("pass_predicate") or scoring_order.get("pass_predicate"),
                    "next_escalation": "If no deterministic executor exists for this subartifact, create a lane-specific acquisition/scoring tool and keep r017 blocked.",
                    "validator_binding": f"comparator_gap::{gap_id}::oc_prediction_scoring_row::{artifact_id}",
                    "no_fake_closure_policy": "Subtasks describe required scientific work; they cannot close broad TOE superiority without a passing evidence pack and replay record.",
                },
                {},
            )
            row["subwork_hash"] = artifact_hash(row)
            rows.append(row)
    payload = {
        "schema_id": "OC133_MODERN_SCIENCE_COMPARATOR_SCORING_EXECUTOR_BACKLOG_v1",
        "generated_at": stable_generated_at(root, comparator_scoring_executor_backlog_rel()),
        "lane_id": "MODERN_SCIENCE_COMPARATOR_SUPERIORITY",
        "status": "OPEN" if rows else "PASS",
        "open_scoring_gap_total": len(open_gap_ids),
        "scoring_work_order_total": len(comparator_scoring_work_orders(root)),
        "root_cause_counts": root_cause_counts,
        "stale_scoring_work_order_total": len(stale_scoring_order_refs),
        "stale_scoring_work_order_refs": stale_scoring_order_refs[:100],
        "subwork_order_total": len(rows),
        "execution_command": [sys.executable, "tools/oc133_toe_closure_factory.py", "--compile-comparator-scoring-backlog", "--write"],
        "pass_predicate": "All scoring subtasks are replaced by passing target-hidden evidence packs, material OC-vs-comparator superiority, and clean replay records.",
        "why_it_failed": "Comparator broad coverage still lacks strict OC prediction scoring evidence for one or more gaps." if rows else "All comparator scoring work orders are closed.",
        "repair_strategy": "Execute subtasks in source -> target -> model -> comparator -> uncertainty -> falsifier -> replay order; never count a diagnostic work order as evidence.",
        "required_capability": "Research/ScoringExecutor",
        "next_escalation": "Implement lane-specific scoring executors for the earliest open subtask in each gap.",
        "no_fake_closure_policy": "This backlog is an internal research-control graph artifact. It is not a public claim and cannot promote modern_science_comparator_superiority.",
        "rows": rows,
    }
    payload["artifact_ref"] = rel(root, root / comparator_scoring_executor_backlog_rel())
    payload["artifact_hash"] = artifact_hash(payload)
    write_json_artifact(root, comparator_scoring_executor_backlog_rel(), payload)
    return payload


def comparator_scoring_backlog_rows(root: Path) -> list[dict[str, Any]]:
    payload = read_json(root / comparator_scoring_executor_backlog_rel())
    rows = payload.get("rows") or []
    return [row for row in rows if isinstance(row, dict)]


def build_comparator_scoring_subartifact_execution(root: Path, gap_id: str, subartifact_id: str) -> dict[str, Any]:
    backlog = build_comparator_scoring_executor_backlog(root)
    rows = [
        row
        for row in backlog.get("rows", [])
        if str(row.get("gap_id")) == gap_id and str(row.get("scoring_subartifact_id")) == subartifact_id
    ]
    generated_at = stable_generated_at(root, comparator_gap_scoring_subartifact_rel(gap_id, subartifact_id))
    if rows:
        row = rows[0]
        status = "OPEN"
        why = row.get("why_it_failed")
        repair = row.get("repair_strategy")
        required_capability = row.get("required_capability")
        required_source_block = row.get("required_source_block", {})
        pass_predicate = row.get("pass_predicate")
        source_work_order_ref = row.get("source_work_order_ref")
        root_cause_class = row.get("root_cause_class")
    else:
        status = "FAIL_CLOSED"
        why = "No scoring-subartifact backlog row exists for this gap/subartifact pair."
        repair = "Regenerate the comparator scoring backlog and verify the gap still lacks oc_prediction_scoring_row."
        required_capability = "Research/ScoringExecutor"
        required_source_block = {}
        pass_predicate = "Backlog row exists and then its source-bound executor materializes the required evidence object."
        source_work_order_ref = None
        root_cause_class = "SCORING_SUBARTIFACT_BACKLOG_ROW_MISSING"
    payload = normalize_problem_row(
        {
            "schema_id": "OC133_MODERN_SCIENCE_COMPARATOR_SCORING_SUBARTIFACT_EXECUTION_v1",
            "generated_at": generated_at,
            "lane_id": "MODERN_SCIENCE_COMPARATOR_SUPERIORITY",
            "gap_id": gap_id,
            "scoring_subartifact_id": subartifact_id,
            "status": status,
            "root_cause_class": root_cause_class,
            "source_work_order_ref": source_work_order_ref,
            "required_source_block": required_source_block,
            "why_it_failed": why,
            "repair_strategy": repair,
            "required_capability": required_capability,
            "execution_command": [
                sys.executable,
                "tools/oc133_toe_closure_factory.py",
                "--execute-comparator-scoring-subartifact",
                gap_id,
                subartifact_id,
                "--write",
            ],
            "pass_predicate": pass_predicate,
            "validator_binding": f"comparator_gap::{gap_id}::oc_prediction_scoring_row::{subartifact_id}",
            "next_escalation": "Implement the concrete source acquisition/scoring executor named by required_source_block; this diagnostic packet is not evidence.",
            "no_fake_closure_policy": "A scoring-subartifact execution packet narrows missing scientific work and cannot close broad superiority without a passing evidence pack.",
        },
        {
            "execution_command": [
                sys.executable,
                "tools/oc133_toe_closure_factory.py",
                "--execute-comparator-scoring-subartifact",
                gap_id,
                subartifact_id,
                "--write",
            ],
        },
    )
    payload["artifact_ref"] = rel(root, root / comparator_gap_scoring_subartifact_rel(gap_id, subartifact_id))
    payload["artifact_hash"] = artifact_hash(payload)
    write_json_artifact(root, comparator_gap_scoring_subartifact_rel(gap_id, subartifact_id), payload)
    return payload


def comparator_scoring_subartifact_execution_exists(root: Path, gap_id: str, subartifact_id: str) -> bool:
    payload = read_json(root / comparator_gap_scoring_subartifact_rel(gap_id, subartifact_id))
    return (
        payload.get("schema_id") == "OC133_MODERN_SCIENCE_COMPARATOR_SCORING_SUBARTIFACT_EXECUTION_v1"
        and payload.get("gap_id") == gap_id
        and payload.get("scoring_subartifact_id") == subartifact_id
    )


def build_all_comparator_scoring_subartifact_executions(root: Path) -> dict[str, Any]:
    generated_at = utc_now()
    rows = comparator_scoring_backlog_rows(root)
    built_rows: list[dict[str, Any]] = []
    for row in rows:
        if row.get("status") == "PASS":
            continue
        gap_id = str(row.get("gap_id") or "")
        subartifact_id = str(row.get("scoring_subartifact_id") or "")
        if not gap_id or not subartifact_id:
            continue
        payload = build_comparator_scoring_subartifact_execution(root, gap_id, subartifact_id)
        built_rows.append(
            {
                "gap_id": gap_id,
                "scoring_subartifact_id": subartifact_id,
                "status": payload.get("status"),
                "artifact_ref": payload.get("artifact_ref"),
            }
        )
    result = {
        "schema_id": "OC133_MODERN_SCIENCE_COMPARATOR_SCORING_SUBARTIFACT_BATCH_v1",
        "generated_at": generated_at,
        "status": "PASS",
        "subartifact_execution_total": len(built_rows),
        "open_subartifact_execution_total": sum(1 for row in built_rows if row.get("status") != "PASS"),
        "rows": built_rows,
        "no_fake_closure_policy": "Batch materialization creates lower-level work packets only; broad comparator PASS still requires evidence packs and replay records.",
    }
    result["artifact_hash"] = artifact_hash(result)
    return result


def build_comparator_gap_research_artifact(root: Path, gap_id: str, artifact_key: str) -> dict[str, Any]:
    gap_payload = comparator_gap_execution_payload(root, gap_id)
    queue_row = comparator_lane_queue_rows_by_gap(root).get(gap_id, {})
    executable_spec = queue_row.get("executable_work_order", {}) if isinstance(queue_row.get("executable_work_order"), dict) else {}
    source = executable_spec.get("official_data_source", {}) if isinstance(executable_spec.get("official_data_source"), dict) else {}
    target = executable_spec.get("target_variable", {}) if isinstance(executable_spec.get("target_variable"), dict) else {}
    comparator = executable_spec.get("incumbent_comparator_requirement", {}) if isinstance(executable_spec.get("incumbent_comparator_requirement"), dict) else {}
    uncertainty = executable_spec.get("uncertainty_requirement", {}) if isinstance(executable_spec.get("uncertainty_requirement"), dict) else {}
    falsifier = executable_spec.get("falsifier_requirement", {}) if isinstance(executable_spec.get("falsifier_requirement"), dict) else {}
    negative_control = executable_spec.get("negative_control_requirement", {}) if isinstance(executable_spec.get("negative_control_requirement"), dict) else {}
    execution = executable_spec.get("execution_requirements", {}) if isinstance(executable_spec.get("execution_requirements"), dict) else {}
    evidence = comparator_current_evidence(root, executable_spec)
    domain_class_id = str(gap_payload.get("domain_class_id") or queue_row.get("domain_class_id") or "")
    lane_route = str(queue_row.get("lane_route") or "")
    formal_evidence = (
        formal_route_exact_evidence(root, executable_spec)
        if domain_class_id == "formal_mathematics_and_logic" and lane_route == "FORMAL_ROUTE_PROTOCOL_ONLY"
        else {}
    )
    required_lanes = [
        row
        for row in queue_row.get("required_data_lanes", []) or []
        if isinstance(row, dict)
    ]

    def lane_by_role(*roles: str) -> dict[str, Any]:
        role_set = set(roles)
        return next((row for row in required_lanes if row.get("lane_role") in role_set), {})

    if not source:
        source = dict(COMPARATOR_FALLBACK_SOURCE_BLOCKS.get(domain_class_id, {}))
    if not target and lane_route == "FORMAL_ROUTE_PROTOCOL_ONLY":
        target = {
            "name": f"{gap_payload.get('phenomenon_class_id') or queue_row.get('phenomenon_class_id')}_formal_protocol_review",
            "target_fields": [
                "case_id",
                "theorem_or_property_id",
                "expected_formal_verdict",
                "observed_formal_verdict",
                "proof_corpus_hash",
            ],
            "extraction_rule": "Formal protocol route: observed proof verdicts remain withheld from the pre-execution input ledger.",
        }
    if not target:
        target = dict(COMPARATOR_FALLBACK_TARGET_BLOCKS.get(f"{domain_class_id}::{gap_payload.get('phenomenon_class_id') or queue_row.get('phenomenon_class_id')}", {}))
    if not comparator:
        lane = lane_by_role("incumbent_comparator")
        if lane:
            comparator = {
                "baseline_name": lane.get("baseline_name") or f"{gap_payload.get('phenomenon_class_id') or queue_row.get('phenomenon_class_id')}_declared_incumbent_baseline",
                "prediction_rule": lane.get("requirement"),
                "pre_registered": lane.get("pre_registered", True),
            }
        elif lane_route == "FORMAL_ROUTE_PROTOCOL_ONLY":
            comparator = {
                "baseline_name": f"{gap_payload.get('phenomenon_class_id') or queue_row.get('phenomenon_class_id')}_accept_all_formal_baseline",
                "prediction_rule": "predict ACCEPT for every formal route row; rejected controls must beat this baseline before any formal-equivalent closure claim",
                "pre_registered": True,
            }
    if not uncertainty:
        lane = lane_by_role("uncertainty_policy", "residual_metric", "oc_scoring")
        if lane:
            uncertainty = {
                "metric": lane.get("metric") or lane.get("metric_id") or f"{gap_payload.get('phenomenon_class_id') or queue_row.get('phenomenon_class_id')}_domain_local_residual",
                "rule": lane.get("requirement"),
            }
        elif lane_route == "FORMAL_ROUTE_PROTOCOL_ONLY":
            uncertainty = {
                "metric": "exact_formal_verdict_no_empirical_interval",
                "rule": "Formal protocol rows require exact replay equality; no empirical uncertainty interval is claimed.",
            }
    if not falsifier:
        lane = lane_by_role("falsifier", "negative_control")
        if lane:
            falsifier = {
                "falsifier_id": lane.get("falsifier_id") or lane.get("control_id") or f"{gap_payload.get('phenomenon_class_id') or queue_row.get('phenomenon_class_id')}_declared_falsifier",
                "trigger": lane.get("requirement"),
            }
        elif queue_row.get("required_proof_lanes"):
            falsifier = {
                "falsifier_id": f"{gap_payload.get('phenomenon_class_id') or queue_row.get('phenomenon_class_id')}_proof_lane_falsifier",
                "trigger": "; ".join(str(item) for item in queue_row.get("required_proof_lanes", []) if item),
            }
    if not negative_control:
        lane = lane_by_role("negative_control")
        if lane:
            negative_control = {
                "control_id": lane.get("control_id") or f"{gap_payload.get('phenomenon_class_id') or queue_row.get('phenomenon_class_id')}_declared_negative_control",
                "rule": lane.get("requirement"),
            }
        elif queue_row.get("required_proof_lanes"):
            negative_control = {
                "control_id": f"{gap_payload.get('phenomenon_class_id') or queue_row.get('phenomenon_class_id')}_proof_lane_negative_control",
                "rule": "Negative controls must be rejected before coverage closure; proof-lane text is preregistered but not scoring evidence.",
            }

    status = "OPEN"
    closure_scope = "artifact_missing"
    validation: dict[str, Any] = {}

    if artifact_key == "verified_open_source_capsule":
        required_snapshot_ref = source.get("required_local_snapshot_ref")
        required_lock_ref = source.get("required_lock_ref")
        snapshot_exists = bool(required_snapshot_ref) and (root / str(required_snapshot_ref)).exists()
        lock_exists = bool(required_lock_ref) and (root / str(required_lock_ref)).exists()
        status = "PASS" if source.get("source_id") and (source.get("official_endpoint_url") or source.get("official_documentation_url")) else "OPEN"
        closure_scope = "source_identity_and_open_url_bound; target/scoring/replay remain separate"
        validation = {
            "source_id_present": bool(source.get("source_id")),
            "official_url_present": bool(source.get("official_endpoint_url") or source.get("official_documentation_url")),
            "required_snapshot_ref": required_snapshot_ref,
            "required_snapshot_exists": snapshot_exists,
            "required_snapshot_sha256": sha256_file(root / str(required_snapshot_ref)) if snapshot_exists else "",
            "required_lock_ref": required_lock_ref,
            "required_lock_exists": lock_exists,
            "required_lock_sha256": sha256_file(root / str(required_lock_ref)) if lock_exists else "",
        }
    elif artifact_key == "benchmark_case":
        status = "PASS" if target.get("name") and target.get("target_fields") else "OPEN"
        closure_scope = "target/benchmark case preregistered; no target result credit counted here"
        validation = {
            "target_name_present": bool(target.get("name")),
            "target_fields_total": len(target.get("target_fields") or []),
            "minimum_rows_required": source.get("minimum_rows_required") or execution.get("minimum_n"),
            "target_hidden_policy": target.get("extraction_rule") or execution.get("target_hidden_until_scoring"),
        }
    elif artifact_key == "incumbent_comparator":
        status = "PASS" if comparator.get("baseline_name") and comparator.get("pre_registered") is True else "OPEN"
        closure_scope = "incumbent comparator preregistered; scoring superiority not asserted"
        validation = {
            "baseline_name_present": bool(comparator.get("baseline_name")),
            "pre_registered": comparator.get("pre_registered") is True,
            "prediction_rule_present": bool(comparator.get("prediction_rule")),
        }
    elif artifact_key == "uncertainty_row":
        status = "PASS" if uncertainty.get("metric") and (uncertainty.get("rule") or uncertainty.get("requirement")) else "OPEN"
        closure_scope = "uncertainty policy declared before scoring"
        validation = {
            "metric_present": bool(uncertainty.get("metric")),
            "rule_present": bool(uncertainty.get("rule") or uncertainty.get("requirement")),
        }
    elif artifact_key == "falsifier_row":
        trigger = falsifier.get("trigger") or falsifier.get("requirement")
        control = negative_control.get("rule") or negative_control.get("requirement")
        status = "PASS" if trigger and control else "OPEN"
        closure_scope = "falsifier and negative-control policy declared; not evidence of passed scoring"
        validation = {
            "falsifier_present": bool(trigger),
            "negative_control_present": bool(control),
            "falsifier_id": falsifier.get("falsifier_id"),
            "negative_control_id": negative_control.get("control_id"),
        }
    elif artifact_key == "oc_prediction_scoring_row":
        if formal_evidence:
            status = "PASS" if formal_evidence.get("status") == "PASS" else "OPEN"
            closure_scope = (
                "formal-route target-hidden scoring/replay artifact passed; not empirical or broad-modern-science evidence"
                if status == "PASS"
                else "formal-route scorer/replay did not pass all exact-evidence predicates"
            )
            validation = formal_evidence
        else:
            status = "PASS" if evidence["executable_evidence_exists"] and evidence["evidence_ref_exists"] and evidence["material_margin_met"] and not evidence["fail_closed_status_present"] else "OPEN"
            closure_scope = "strict scoring row passed material superiority predicates" if status == "PASS" else "scoring evidence absent or does not beat the preregistered comparator"
            validation = evidence
    elif artifact_key == "replay_record":
        replay_commands = execution.get("replay_commands") or ([execution.get("replay_command")] if execution.get("replay_command") else [])
        replay_results = []
        if formal_evidence:
            replay_results = list(formal_evidence.get("replay_results") or [])
            status = "PASS" if formal_evidence.get("replay_pass") is True and formal_evidence.get("status") == "PASS" else "OPEN"
            closure_scope = (
                "formal-route replay commands passed against source-bound finite/proof corpora"
                if status == "PASS"
                else "formal-route replay remains blocked"
            )
            validation = {
                "replay_command_total": len(replay_commands),
                "replay_executed_total": len(replay_results),
                "replay_results": replay_results,
                "formal_scoring_evidence": formal_evidence,
            }
        elif evidence["material_margin_met"] and not evidence["fail_closed_status_present"]:
            for command in replay_commands[:3]:
                if isinstance(command, str) and command.strip():
                    replay_results.append(safe_run_command(root, command.split(), 300))
            status = "PASS" if replay_results and all(row.get("returncode") == 0 for row in replay_results) else "OPEN"
            closure_scope = "independent replay passed for already-positive scoring evidence" if status == "PASS" else "replay not run or scoring evidence still blocked"
            validation = {
                "replay_command_total": len(replay_commands),
                "replay_executed_total": len(replay_results),
                "replay_results": replay_results,
                "scoring_evidence": evidence,
            }
        else:
            status = "OPEN"
            closure_scope = "replay not run or scoring evidence still blocked"
            validation = {
                "replay_command_total": len(replay_commands),
                "replay_executed_total": 0,
                "replay_results": [],
                "scoring_evidence": evidence,
            }

    payload = {
        "schema_id": "OC133_MODERN_SCIENCE_COMPARATOR_RESEARCH_ARTIFACT_v1",
        "generated_at": stable_generated_at(root, comparator_gap_research_artifact_rel(gap_id, artifact_key)),
        "lane_id": "MODERN_SCIENCE_COMPARATOR_SUPERIORITY",
        "gap_id": gap_id,
        "artifact_key": artifact_key,
        "status": status,
        "closure_scope": closure_scope,
        "domain_class_id": domain_class_id,
        "phenomenon_class_id": gap_payload.get("phenomenon_class_id") or queue_row.get("phenomenon_class_id"),
        "work_order_id": queue_row.get("work_order_id"),
        "queue_row_found": bool(queue_row),
        "executable_spec_found": bool(executable_spec),
        "source_refs": [
            "reports/OC_CORE_1_3_3_MODERN_SCIENCE_COVERAGE_LANE_QUEUE.json",
            "benchmarks/modern_science/OC133_MODERN_SCIENCE_COVERAGE_WORK_ORDERS.json",
            "comparators/modern_science/OC133_MODERN_SCIENCE_COVERAGE_REGISTER.json",
        ],
        "validation": validation,
        "why_it_failed": "Required comparator artifact still lacks source-bound support." if status != "PASS" else "Required comparator artifact is source-bound at its declared scope.",
        "repair_strategy": "Continue to the next missing artifact; do not close broad superiority until all source, benchmark, comparator, scoring, uncertainty, falsifier, and replay artifacts pass.",
        "required_capability": "Research/PriorArt",
        "execution_command": [sys.executable, "tools/oc133_toe_closure_factory.py", "--execute-comparator-gap-artifact", gap_id, artifact_key, "--write"],
        "pass_predicate": f"{artifact_key} status == PASS and the strict comparator gap row no longer lists it as missing.",
        "next_escalation": "If this row remains OPEN, create a narrower acquisition/scoring/replay executor for the exact failed validation field.",
        "no_fake_closure_policy": "This artifact can reduce a missing-artifact count only at its own scope. It cannot mark the coverage gap or broad TOE superiority PASS by itself.",
    }
    payload["artifact_ref"] = rel(root, root / comparator_gap_research_artifact_rel(gap_id, artifact_key))
    payload["artifact_hash"] = artifact_hash(payload)
    write_json_artifact(root, comparator_gap_research_artifact_rel(gap_id, artifact_key), payload)
    return payload


def comparator_gap_artifact_execution_payload(root: Path, gap_id: str, artifact_key: str, *, generated_at: str | None = None) -> dict[str, Any]:
    gap_payload = comparator_gap_execution_payload(root, gap_id)
    queue_row = comparator_lane_queue_rows_by_gap(root).get(gap_id, {})
    executable_spec = queue_row.get("executable_work_order", {}) if isinstance(queue_row.get("executable_work_order"), dict) else {}
    artifact_map = {
        "verified_open_source_capsule": {
            "source_block": executable_spec.get("official_data_source") or {"official_source_defaults": queue_row.get("official_source_defaults", [])},
            "required_output_kind": "source_capsule_and_snapshot_lock",
            "closure_predicate": "official source capsule exists, local snapshot/cache is locked, hash-bound, and source license/open-access status is recorded",
        },
        "benchmark_case": {
            "source_block": executable_spec.get("target_variable") or queue_row.get("required_data_lanes", []),
            "required_output_kind": "benchmark_case_with_hidden_target_policy",
            "closure_predicate": "benchmark case declares target variables, source separation, minimum N or formal equivalent, and target-hidden-until-scoring policy",
        },
        "incumbent_comparator": {
            "source_block": executable_spec.get("incumbent_comparator_requirement") or queue_row.get("required_data_lanes", []),
            "required_output_kind": "preregistered_incumbent_comparator",
            "closure_predicate": "incumbent baseline is preregistered and scored on the same held-out targets",
        },
        "oc_prediction_scoring_row": {
            "source_block": executable_spec.get("residual_requirement") or executable_spec.get("formula_requirement") or {},
            "required_output_kind": "oc_scoring_row_with_residuals",
            "closure_predicate": "OC score row has model output, comparator output, residual, materiality threshold, uncertainty, and pack hash",
        },
        "uncertainty_row": {
            "source_block": executable_spec.get("uncertainty_requirement") or {},
            "required_output_kind": "uncertainty_policy_and_interval_row",
            "closure_predicate": "uncertainty rule is declared before target opening and bound to the scoring pack",
        },
        "falsifier_row": {
            "source_block": executable_spec.get("falsifier_requirement") or executable_spec.get("negative_control_requirement") or {},
            "required_output_kind": "falsifier_and_negative_control_row",
            "closure_predicate": "falsifier trigger and negative controls are executable and not post-hoc",
        },
        "replay_record": {
            "source_block": executable_spec.get("execution_requirements") or {},
            "required_output_kind": "independent_replay_record",
            "closure_predicate": "clean-checkout replay command passes and binds the generated evidence pack",
        },
    }
    artifact_spec = artifact_map.get(artifact_key, {})
    missing = artifact_key in set(gap_payload.get("missing_artifacts") or COMPARATOR_REQUIRED_ARTIFACT_KEYS)
    payload = {
        "schema_id": "OC133_MODERN_SCIENCE_COMPARATOR_GAP_ARTIFACT_EXECUTION_v1",
        "generated_at": generated_at or stable_generated_at(root, comparator_gap_artifact_execution_rel(gap_id, artifact_key)),
        "lane_id": "MODERN_SCIENCE_COMPARATOR_SUPERIORITY",
        "gap_id": gap_id,
        "artifact_key": artifact_key,
        "status": "OPEN" if missing else "PASS",
        "required_output_kind": artifact_spec.get("required_output_kind") or "unknown_comparator_gap_artifact",
        "domain_class_id": gap_payload.get("domain_class_id") or queue_row.get("domain_class_id"),
        "phenomenon_class_id": gap_payload.get("phenomenon_class_id") or queue_row.get("phenomenon_class_id"),
        "queue_row_found": bool(queue_row),
        "executable_spec_found": bool(executable_spec),
        "source_block": artifact_spec.get("source_block", {}),
        "source_refs": [
            "reports/OC_CORE_1_3_3_MODERN_SCIENCE_COVERAGE_LANE_QUEUE.json",
            "benchmarks/modern_science/OC133_MODERN_SCIENCE_COVERAGE_WORK_ORDERS.json",
            "comparators/modern_science/OC133_MODERN_SCIENCE_COVERAGE_REGISTER.json",
        ],
        "why_it_failed": f"Comparator gap `{gap_id}` lacks `{artifact_key}`; no broad-superiority credit is awarded." if missing else f"Comparator gap `{gap_id}` already has `{artifact_key}`.",
        "repair_strategy": "Create the required artifact from governed open/free sources, bind hashes, then rerun the comparator gap and strict validator.",
        "required_capability": "Research/PriorArt",
        "execution_command": [sys.executable, "tools/oc133_toe_closure_factory.py", "--execute-comparator-gap-artifact", gap_id, artifact_key, "--write"],
        "pass_predicate": artifact_spec.get("closure_predicate") or "Artifact exists, is hash-bound, and passes comparator gap acceptance predicates.",
        "next_escalation": "If source acquisition is unavailable or evidence cannot be scored, create a lower-level governed acquisition/scoring/replay work order and keep r017 blocked.",
        "no_fake_closure_policy": "This artifact job is an executable research obligation. It does not mark the coverage gap PASS unless the concrete evidence artifact exists and the coverage register closes.",
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def build_comparator_gap_artifact_execution(root: Path, gap_id: str, artifact_key: str) -> dict[str, Any]:
    payload = comparator_gap_artifact_execution_payload(root, gap_id, artifact_key)
    research_artifact = build_comparator_gap_research_artifact(root, gap_id, artifact_key)
    payload["research_artifact_ref"] = research_artifact.get("artifact_ref")
    payload["research_artifact_status"] = research_artifact.get("status")
    payload["research_artifact_scope"] = research_artifact.get("closure_scope")
    payload["status"] = "PASS" if research_artifact.get("status") == "PASS" else payload.get("status", "OPEN")
    payload["pass_predicate_evaluation"] = {
        "artifact_key": artifact_key,
        "research_artifact_status": research_artifact.get("status"),
        "gap_pass_unchanged_by_single_artifact": True,
    }
    payload["artifact_hash"] = artifact_hash(payload)
    artifact_rel = comparator_gap_artifact_execution_rel(gap_id, artifact_key)
    payload["artifact_ref"] = rel(root, root / artifact_rel)
    write_json_artifact(root, artifact_rel, payload)
    return payload


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
    scoring_backlog = build_comparator_scoring_executor_backlog(root)
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
        "scoring_backlog_ref": scoring_backlog.get("artifact_ref"),
        "scoring_subwork_order_total": scoring_backlog.get("subwork_order_total"),
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
        "scoring_backlog_ref": scoring_backlog.get("artifact_ref"),
        "scoring_subwork_order_total": scoring_backlog.get("subwork_order_total"),
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


def capability_development_key(row: dict[str, Any]) -> str:
    missing_artifact_type = row.get("missing_artifact_type")
    source_node = str(row.get("source_graph_node_id") or "")
    if source_node.startswith("required_artifact:MODERN_SCIENCE_COMPARATOR_SUPERIORITY:"):
        parts = source_node.split(":")
        if len(parts) >= 4 and parts[3] in COMPARATOR_REQUIRED_ARTIFACT_KEYS:
            missing_artifact_type = parts[3]
    return artifact_hash(
        {
            "lane_id": row.get("lane_id"),
            "source_graph_node_id": row.get("source_graph_node_id"),
            "missing_artifact_type": missing_artifact_type,
            "scientific_frontier_hash": row.get("scientific_frontier_hash") or row.get("frontier_hash") or "UNKNOWN_FRONTIER",
        }
    )


def load_autonomous_capability_development_rows(root: Path) -> list[dict[str, Any]]:
    payload = read_json(root / AUTONOMOUS_SUPERVISOR_DIR / AUTONOMOUS_CAPABILITY_DEVELOPMENT_LEDGER_NAME)
    rows = payload.get("rows") or []
    return [row for row in rows if isinstance(row, dict)]


def capability_executor_for_row(row: dict[str, Any], compiled_capability_id: str) -> tuple[list[str], str, str]:
    lane_id = str(row.get("lane_id") or "TOE_CLOSURE_FACTORY")
    missing = str(row.get("missing_artifact_type") or row.get("required_artifact") or row.get("executor_type") or "unknown")
    if lane_id in {"AI", "ENTERPRISE_ARCHITECTURE"}:
        work_order_id = str(row.get("work_order_id") or "")
        source_action_id = str(row.get("source_action_id") or "")
        if source_action_id.startswith("AUTO-"):
            work_order_id = source_action_id.removeprefix("AUTO-")
        if work_order_id.startswith("R017-"):
            return (
                [sys.executable, "tools/oc133_toe_closure_factory.py", "--execute-source-intake-work-order", work_order_id, "--write"],
                "projection_source_intake",
                "Execute the exact AI/EA source-intake work order and preserve fail-closed support-pack output.",
            )
        return (
            [sys.executable, "tools/oc133_toe_closure_factory.py", "--execute-capability-lane", lane_id, "--write"],
            "projection_lane_capability",
            "Rebuild the lane support pack, proof sheet, guarded writer report, and source-intake work orders.",
        )
    if lane_id == "MODERN_SCIENCE_COMPARATOR_SUPERIORITY":
        gap_id = str(row.get("gap_id") or "")
        artifact_key = str(row.get("scoring_subartifact_id") or row.get("missing_artifact_type") or "")
        source_node = str(row.get("source_graph_node_id") or "")
        if not gap_id and source_node.startswith("required_artifact:MODERN_SCIENCE_COMPARATOR_SUPERIORITY:"):
            parts = source_node.split(":")
            if len(parts) >= 3:
                gap_id = parts[2]
            if len(parts) >= 4:
                artifact_key = parts[3]
        if gap_id and artifact_key in COMPARATOR_REQUIRED_ARTIFACT_KEYS:
            if artifact_key == "oc_prediction_scoring_row":
                return (
                    [sys.executable, "tools/oc133_toe_closure_factory.py", "--execute-comparator-scoring-work-order", gap_id, "--write"],
                    "comparator_scoring_work_order",
                    "Build the exact scoring/replay research work order for this comparator gap, with source, target, OC model, incumbent comparator, uncertainty, falsifier, replay, and fail-closed pass predicates.",
                )
            return (
                [sys.executable, "tools/oc133_toe_closure_factory.py", "--execute-comparator-gap-artifact", gap_id, artifact_key, "--write"],
                "comparator_gap_artifact",
                "Create the exact comparator gap artifact work packet before rerunning broad-coverage closure.",
            )
        if gap_id and artifact_key:
            return (
                [sys.executable, "tools/oc133_toe_closure_factory.py", "--execute-comparator-scoring-subartifact", gap_id, artifact_key, "--write"],
                "comparator_scoring_subartifact",
                "Build the exact lower-level scoring subartifact packet for this gap so source acquisition, target locking, model registration, comparator scoring, uncertainty, falsifier, or replay work can proceed without rerunning a generic wave.",
            )
        if gap_id:
            return (
                [sys.executable, "tools/oc133_toe_closure_factory.py", "--execute-comparator-gap", gap_id, "--write"],
                "comparator_gap",
                "Execute the comparator gap job for the exact missing broad-coverage artifact.",
            )
        return (
            [sys.executable, "tools/oc133_toe_closure_factory.py", "--execute-capability-lane", lane_id, "--write"],
            "comparator_lane_capability",
            "Rebuild comparator diagnostics and domain/gap execution reports.",
        )
    if lane_id == "GRAND_TOE_CLAIM_LEDGER_EVIDENCE":
        return (
            [sys.executable, "tools/oc133_toe_closure_factory.py", "--execute-capability-lane", lane_id, "--write"],
            "grand_promotion_capability",
            "Rebuild grand promotion diagnostics, prerequisite plan, and derivation report.",
        )
    if lane_id == "CERBERUS_RELEASE_REVIEW_GATE":
        return (
            lane_registry_by_id().get(lane_id, {}).get("execution_command", []),
            "cerberus_refresh",
            "Refresh Cerberus fingerprints and clean gate after science validator is green.",
        )
    return (
        list(row.get("execution_command") or []),
        f"generic_{missing}",
        "Execute the original row command under capability-development tracking.",
    )


def build_scientific_frontier(root: Path, *, generated_at: str | None = None) -> dict[str, Any]:
    refs = [
        FINAL_TOE_PROJECTION_LANE_TARGETS["AI"],
        FINAL_TOE_PROJECTION_LANE_TARGETS["ENTERPRISE_ARCHITECTURE"],
        GRAND_SCORECARD,
        GRAND_PROMOTION_REPORT,
        COMPARATOR_REGISTER,
        FINITE_CHECK_REPORT,
        CERBERUS_ACCEPTANCE,
        CERBERUS_FINDINGS,
    ]
    parts = current_validator_error_parts(root)
    ref_rows = []
    for ref in refs:
        path = root / ref
        ref_rows.append(
            {
                "ref": str(ref).replace("\\", "/"),
                "exists": path.exists(),
                "content_hash": artifact_hash({"payload": read_json(path)}) if path.suffix.lower() == ".json" and path.exists() else artifact_hash({"missing": not path.exists(), "ref": str(ref)}),
            }
        )
    payload = {
        "schema_id": "OC133_TOE_SCIENTIFIC_FRONTIER_v1",
        "generated_at": generated_at or utc_now(),
        "status": "OPEN" if validator_error_total(parts) else "PASS",
        "validator_error_total": validator_error_total(parts),
        "science_validator_error_total": len(parts["science_errors"]),
        "cerberus_error_total": len(parts["cerberus_errors"]),
        "frontier_policy": "Scientific frontier excludes supervisor bookkeeping, blocking-graph, capability-backlog, and diagnostic artifacts.",
        "refs": ref_rows,
    }
    payload["scientific_frontier_hash"] = artifact_hash({"validator_parts": parts, "refs": ref_rows})
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def current_open_validator_lanes(root: Path) -> set[str]:
    lanes: set[str] = set()
    for error in current_validator_errors(root):
        lowered = error.lower()
        if "ai lane" in lowered or "ai row" in lowered:
            lanes.add("AI")
        if "enterprise_architecture" in lowered or "enterprise architecture" in lowered:
            lanes.add("ENTERPRISE_ARCHITECTURE")
        if "modern_science_comparator_superiority" in lowered:
            lanes.add("MODERN_SCIENCE_COMPARATOR_SUPERIORITY")
        if "grand_toe_claim_ledger_evidence" in lowered or "all_domain_ready_no_send" in lowered:
            lanes.add("GRAND_TOE_CLAIM_LEDGER_EVIDENCE")
        if "cerberus" in lowered:
            lanes.add("CERBERUS_RELEASE_REVIEW_GATE")
    return lanes


def build_capability_implementation_registry(root: Path, *, generated_at: str | None = None) -> dict[str, Any]:
    generated_at = generated_at or utc_now()
    frontier = build_scientific_frontier(root, generated_at=generated_at)
    open_lanes = current_open_validator_lanes(root)
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for source_row in load_autonomous_capability_development_rows(root):
        row = dict(source_row)
        if (
            row.get("status") == "PASS"
            or row.get("superseded_by_research_artifact") is True
            or row.get("superseded_by_research_artifact_packet") is True
            or row.get("superseded_by_current_validator") is True
            or row.get("superseded_by_scoring_work_order") is True
            or row.get("superseded_by_scoring_subartifact_execution") is True
        ):
            continue
        source_node = str(row.get("source_graph_node_id") or "")
        if source_node.startswith("required_artifact:MODERN_SCIENCE_COMPARATOR_SUPERIORITY:"):
            parts = source_node.split(":")
            if len(parts) >= 4 and parts[3] in COMPARATOR_REQUIRED_ARTIFACT_KEYS:
                row["missing_artifact_type"] = parts[3]
        lane_id = str(row.get("lane_id") or "")
        if lane_id and lane_id not in open_lanes:
            continue
        row["scientific_frontier_hash"] = frontier["scientific_frontier_hash"]
        key = capability_development_key(row)
        if key in seen:
            continue
        seen.add(key)
        compiled_capability_id = f"R017-CAPDEV-{key[:12]}"
        executor_command, executor_type, strategy = capability_executor_for_row(row, compiled_capability_id)
        ready = bool(executor_command) and not (
            row.get("lane_id") == "CERBERUS_RELEASE_REVIEW_GATE"
            and frontier.get("science_validator_error_total", 0)
        )
        rows.append(
            normalize_problem_row(
                {
                    "capability_id": compiled_capability_id,
                    "capability_class": executor_type,
                    "compiled_capability_id": compiled_capability_id,
                    "capability_development_key": key,
                    "source_capability_development_id": row.get("capability_development_id"),
                    "source_graph_node_id": row.get("source_graph_node_id"),
                    "lane_id": row.get("lane_id"),
                    "executor_type": executor_type,
                    "missing_artifact_type": row.get("missing_artifact_type"),
                    "status": "READY" if ready else "BLOCKED",
                    "capability_executor_ready": ready,
                    "scientific_frontier_hash": frontier["scientific_frontier_hash"],
                    "executor_command": executor_command,
                    "execution_command": [sys.executable, "tools/oc133_toe_closure_factory.py", "--execute-capability-development", compiled_capability_id, "--write"],
                    "self_test_command": [sys.executable, "tools/oc133_toe_closure_factory.py", "--check"],
                    "output_artifact_ref": (CAPABILITY_IMPLEMENTATION_DIR / f"{compiled_capability_id}.json").as_posix(),
                    "validator_binding": row.get("validator_binding"),
                    "why_it_failed": row.get("why_it_failed") or "The graph dependency has not closed the strict TOE validator.",
                    "repair_strategy": strategy,
                    "required_capability": row.get("required_capability") or "Research/TOEClosureFactory",
                    "pass_predicate": row.get("pass_predicate") or "The compiled capability executes and strict validator errors decrease or disappear.",
                    "next_escalation": "If this compiled capability produces zero validator delta, generate a lower-level upstream research obligation for the exact missing source/evidence object.",
                },
                {
                    "execution_command": [sys.executable, "tools/oc133_toe_closure_factory.py", "--execute-capability-development", compiled_capability_id, "--write"],
                },
            )
        )
    payload = {
        "schema_id": "OC133_TOE_CAPABILITY_IMPLEMENTATION_REGISTRY_v1",
        "generated_at": generated_at,
        "status": "OPEN" if rows else "PASS",
        "scientific_frontier_ref": (FACTORY_DIR / SCIENTIFIC_FRONTIER_NAME).as_posix(),
        "scientific_frontier_hash": frontier["scientific_frontier_hash"],
        "source_capability_development_total": len(load_autonomous_capability_development_rows(root)),
        "compiled_capability_total": len(rows),
        "ready_capability_total": sum(1 for row in rows if row.get("capability_executor_ready") is True),
        "blocked_capability_total": sum(1 for row in rows if row.get("capability_executor_ready") is not True),
        "dedupe_policy": "Rows are keyed by lane_id + source_graph_node_id + missing_artifact_type + scientific_frontier_hash.",
        "no_fake_closure_policy": "Compiled capabilities execute research commands only; PASS still requires strict validator closure.",
        "rows": rows,
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def compile_capability_backlog(root: Path, *, write: bool = False) -> dict[str, Any]:
    generated_at = utc_now()
    frontier = build_scientific_frontier(root, generated_at=generated_at)
    registry = build_capability_implementation_registry(root, generated_at=generated_at)
    files = {
        root / FACTORY_DIR / SCIENTIFIC_FRONTIER_NAME: stable_json(frontier),
        root / FACTORY_DIR / CAPABILITY_IMPLEMENTATION_REGISTRY_NAME: stable_json(registry),
    }
    result = validation_result(files, write=write)
    payload = {
        "schema_id": "OC133_TOE_CAPABILITY_BACKLOG_COMPILATION_v1",
        "generated_at": generated_at,
        "status": "PASS" if result["state"] == "PASS" else "FAIL",
        "scientific_frontier_ref": (FACTORY_DIR / SCIENTIFIC_FRONTIER_NAME).as_posix(),
        "capability_implementation_registry_ref": (FACTORY_DIR / CAPABILITY_IMPLEMENTATION_REGISTRY_NAME).as_posix(),
        "compiled_capability_total": registry["compiled_capability_total"],
        "ready_capability_total": registry["ready_capability_total"],
        "blocked_capability_total": registry["blocked_capability_total"],
        "validation_result": result,
    }
    payload["artifact_hash"] = artifact_hash(payload)
    return payload


def execute_capability_development(root: Path, capability_id: str, timeout: int, *, write: bool = False) -> dict[str, Any]:
    registry = read_json(root / FACTORY_DIR / CAPABILITY_IMPLEMENTATION_REGISTRY_NAME)
    if not registry:
        compile_capability_backlog(root, write=True)
        registry = read_json(root / FACTORY_DIR / CAPABILITY_IMPLEMENTATION_REGISTRY_NAME)
    rows = registry.get("rows") or []
    match = next(
        (
            row
            for row in rows
            if row.get("compiled_capability_id") == capability_id
            or row.get("capability_id") == capability_id
            or row.get("source_capability_development_id") == capability_id
        ),
        None,
    )
    before_parts = current_validator_error_parts(root)
    before_total = validator_error_total(before_parts)
    generated_at = utc_now()
    if not match:
        payload = {
            "schema_id": "OC133_TOE_CAPABILITY_DEVELOPMENT_EXECUTION_v1",
            "generated_at": generated_at,
            "capability_id": capability_id,
            "compiled_capability_id": capability_id,
            "status": "FAIL_CLOSED",
            "why_it_failed": "Compiled capability id is not present in the implementation registry.",
            "repair_strategy": "Run --compile-capability-backlog --write before executing capability development.",
            "required_capability": "Research/TOEClosureFactory",
            "execution_command": [sys.executable, "tools/oc133_toe_closure_factory.py", "--execute-capability-development", capability_id, "--write"],
            "pass_predicate": "Capability id exists, executor is ready, and strict validator delta is positive.",
            "next_escalation": "Rebuild the capability implementation registry from the current graph.",
            "before_validator_error_total": before_total,
            "after_validator_error_total": before_total,
            "validator_error_delta": 0,
            "command_results": [],
        }
    elif match.get("capability_executor_ready") is not True:
        payload = {
            "schema_id": "OC133_TOE_CAPABILITY_DEVELOPMENT_EXECUTION_v1",
            "generated_at": generated_at,
            "capability_id": capability_id,
            "capability_class": match.get("capability_class") or match.get("executor_type"),
            "compiled_capability_id": capability_id,
            "status": "BLOCKED",
            "why_it_failed": "Capability exists but has no safe ready executor for the current scientific frontier.",
            "repair_strategy": match.get("repair_strategy"),
            "required_capability": match.get("required_capability"),
            "execution_command": [sys.executable, "tools/oc133_toe_closure_factory.py", "--execute-capability-development", capability_id, "--write"],
            "pass_predicate": match.get("pass_predicate"),
            "next_escalation": match.get("next_escalation"),
            "before_validator_error_total": before_total,
            "after_validator_error_total": before_total,
            "validator_error_delta": 0,
            "registry_row": match,
            "command_results": [],
        }
    else:
        command = list(match.get("executor_command") or [])
        result = safe_run_command(root, command, timeout) if command else {
            "cmd": command,
            "returncode": None,
            "stdout_tail": "",
            "stderr_tail": "No executor command was compiled.",
        }
        after_parts = current_validator_error_parts(root)
        after_total = validator_error_total(after_parts)
        payload = {
            "schema_id": "OC133_TOE_CAPABILITY_DEVELOPMENT_EXECUTION_v1",
            "generated_at": generated_at,
            "capability_id": capability_id,
            "capability_class": match.get("capability_class") or match.get("executor_type"),
            "compiled_capability_id": capability_id,
            "capability_development_key": match.get("capability_development_key"),
            "source_graph_node_id": match.get("source_graph_node_id"),
            "lane_id": match.get("lane_id"),
            "executor_type": match.get("executor_type"),
            "status": "PASS" if result.get("returncode") == 0 and before_total - after_total > 0 else "ZERO_DELTA_OPEN" if result.get("returncode") == 0 else "FAIL_CLOSED",
            "why_it_failed": "Compiled capability executed but did not reduce strict validator errors." if result.get("returncode") == 0 and before_total - after_total <= 0 else match.get("why_it_failed"),
            "repair_strategy": match.get("repair_strategy"),
            "required_capability": match.get("required_capability"),
            "execution_command": [sys.executable, "tools/oc133_toe_closure_factory.py", "--execute-capability-development", capability_id, "--write"],
            "executor_command": command,
            "pass_predicate": match.get("pass_predicate"),
            "next_escalation": match.get("next_escalation"),
            "before_validator_error_total": before_total,
            "after_validator_error_total": after_total,
            "validator_error_delta": before_total - after_total,
            "command_results": [result],
            "no_fake_closure_policy": "Zero delta remains OPEN and cannot satisfy r017.",
        }
    payload["artifact_hash"] = artifact_hash(payload)
    if write:
        write_json_artifact(root, CAPABILITY_IMPLEMENTATION_DIR / f"{capability_id}.json", payload)
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
    scientific_frontier_generated_at = existing_generated_at(base / SCIENTIFIC_FRONTIER_NAME) if preserve_existing_generated_at else None
    capability_registry_generated_at = existing_generated_at(base / CAPABILITY_IMPLEMENTATION_REGISTRY_NAME) if preserve_existing_generated_at else None
    obligations = build_obligations(root, validator_errors, generated_at=obligations_generated_at)
    lanes = build_lane_results(root, generated_at=lanes_generated_at)
    registry = build_lane_capability_registry(generated_at=registry_generated_at)
    scientific_frontier = build_scientific_frontier(root, generated_at=scientific_frontier_generated_at)
    capability_implementation_registry = build_capability_implementation_registry(root, generated_at=capability_registry_generated_at)
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
        base / SCIENTIFIC_FRONTIER_NAME: stable_json(scientific_frontier),
        base / CAPABILITY_IMPLEMENTATION_REGISTRY_NAME: stable_json(capability_implementation_registry),
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
    parser.add_argument("--compile-capability-backlog", action="store_true", help="Compile autonomous capability-development rows into executable capability registry entries.")
    parser.add_argument("--execute-capability-development", help="Execute one compiled autonomous capability-development entry.")
    parser.add_argument("--execute-source-intake-work-order", help="Execute one AI/EA source-intake work order.")
    parser.add_argument("--execute-comparator-gap", help="Execute one modern-science comparator coverage gap.")
    parser.add_argument("--execute-comparator-gap-artifact", nargs=2, metavar=("GAP_ID", "ARTIFACT_KEY"), help="Execute one modern-science comparator coverage-gap artifact work packet.")
    parser.add_argument("--execute-comparator-scoring-work-order", help="Build the exact scoring/replay research work order for one comparator coverage gap.")
    parser.add_argument("--execute-comparator-scoring-subartifact", nargs=2, metavar=("GAP_ID", "SUBARTIFACT_ID"), help="Build the exact lower-level scoring subartifact work packet for one comparator coverage gap.")
    parser.add_argument("--execute-all-comparator-scoring-subartifacts", action="store_true", help="Build all lower-level comparator scoring subartifact work packets in one deterministic batch.")
    parser.add_argument("--compile-comparator-scoring-backlog", action="store_true", help="Compile exact lower-level scoring executor subtasks for open comparator scoring work orders.")
    parser.add_argument("--execute-comparator-domain-job", help="Execute one modern-science comparator domain job such as MS-COV-JOB-001.")
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args(argv)
    if args.compile_capability_backlog:
        payload = compile_capability_backlog(ROOT, write=args.write)
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if payload.get("status") == "PASS" else 1
    if args.execute_capability_development:
        payload = execute_capability_development(ROOT, args.execute_capability_development, args.timeout, write=args.write)
        path = ROOT / CAPABILITY_IMPLEMENTATION_DIR / f"{args.execute_capability_development}.json"
        result = validation_result({path: stable_json(payload)}, write=args.write)
        print(json.dumps(result if args.write or args.check else payload, ensure_ascii=False, indent=2, sort_keys=True))
        if args.check and result["state"] != "PASS":
            return 1
        return 0 if payload.get("status") == "PASS" else 1
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
    if args.execute_comparator_gap_artifact:
        gap_id, artifact_key = args.execute_comparator_gap_artifact
        payload = build_comparator_gap_artifact_execution(ROOT, gap_id, artifact_key)
        artifact_ref = payload.get("artifact_ref")
        path = ROOT / artifact_ref if isinstance(artifact_ref, str) and artifact_ref else ROOT / comparator_gap_artifact_execution_rel(gap_id, artifact_key)
        result = validation_result({path: stable_json(payload)}, write=args.write)
        print(json.dumps(result if args.write or args.check else payload, ensure_ascii=False, indent=2, sort_keys=True))
        return 1 if args.check and result["state"] != "PASS" else 0
    if args.execute_comparator_scoring_work_order:
        payload = build_comparator_gap_scoring_work_order(ROOT, args.execute_comparator_scoring_work_order)
        artifact_ref = payload.get("artifact_ref")
        path = ROOT / artifact_ref if isinstance(artifact_ref, str) and artifact_ref else ROOT / comparator_gap_scoring_work_order_rel(args.execute_comparator_scoring_work_order)
        result = validation_result({path: stable_json(payload)}, write=args.write)
        print(json.dumps(result if args.write or args.check else payload, ensure_ascii=False, indent=2, sort_keys=True))
        return 1 if args.check and result["state"] != "PASS" else 0
    if args.execute_comparator_scoring_subartifact:
        gap_id, subartifact_id = args.execute_comparator_scoring_subartifact
        payload = build_comparator_scoring_subartifact_execution(ROOT, gap_id, subartifact_id)
        artifact_ref = payload.get("artifact_ref")
        path = ROOT / artifact_ref if isinstance(artifact_ref, str) and artifact_ref else ROOT / comparator_gap_scoring_subartifact_rel(gap_id, subartifact_id)
        result = validation_result({path: stable_json(payload)}, write=args.write)
        print(json.dumps(result if args.write or args.check else payload, ensure_ascii=False, indent=2, sort_keys=True))
        return 1 if args.check and result["state"] != "PASS" else 0
    if args.execute_all_comparator_scoring_subartifacts:
        payload = build_all_comparator_scoring_subartifact_executions(ROOT)
        path = ROOT / lane_execution_base("MODERN_SCIENCE_COMPARATOR_SUPERIORITY") / "OC133_MODERN_SCIENCE_COMPARATOR_SCORING_SUBARTIFACT_BATCH.json"
        result = validation_result({path: stable_json(payload)}, write=args.write)
        print(json.dumps(result if args.write or args.check else payload, ensure_ascii=False, indent=2, sort_keys=True))
        return 1 if args.check and result["state"] != "PASS" else 0
    if args.compile_comparator_scoring_backlog:
        payload = build_comparator_scoring_executor_backlog(ROOT)
        artifact_ref = payload.get("artifact_ref")
        path = ROOT / artifact_ref if isinstance(artifact_ref, str) and artifact_ref else ROOT / comparator_scoring_executor_backlog_rel()
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
