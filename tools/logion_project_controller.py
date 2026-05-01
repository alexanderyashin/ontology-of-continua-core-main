from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from release_machine.constants import TIMESTAMP  # noqa: E402
from tools import logion_dirty_tree_governance as dirty_governance  # noqa: E402

PROJECT_CONTROL_REL = "operations/project_control"

PORTFOLIO_REL = f"{PROJECT_CONTROL_REL}/LOGION_WORKSTREAM_PORTFOLIO.json"
RESOURCE_POLICY_REL = f"{PROJECT_CONTROL_REL}/LOGION_RESOURCE_POLICY.json"
BUDGET_LEDGER_REL = f"{PROJECT_CONTROL_REL}/LOGION_BUDGET_LEDGER.json"
WORKSTREAM_LOCKS_REL = f"{PROJECT_CONTROL_REL}/LOGION_WORKSTREAM_LOCKS.json"
MILESTONE_PLAN_REL = f"{PROJECT_CONTROL_REL}/LOGION_MILESTONE_PLAN.json"
DIRTY_LEDGER_REL = dirty_governance.LEDGER_REL
DELTA_QUEUE_LEDGER_REL = f"{PROJECT_CONTROL_REL}/LOGION_DELTA_QUEUE_LEDGER.json"
DELTA_QUEUE_POLICY_REL = f"{PROJECT_CONTROL_REL}/LOGION_DELTA_QUEUE_POLICY.json"
PROCESS_COHERENCE_GUARD_REL = f"{PROJECT_CONTROL_REL}/LOGION_PROCESS_COHERENCE_GUARD.json"
ESCALATION_MATRIX_REL = f"{PROJECT_CONTROL_REL}/LOGION_ESCALATION_MATRIX.json"
INCIDENT_QUEUE_REL = f"{PROJECT_CONTROL_REL}/LOGION_INCIDENT_QUEUE.json"
INCIDENT_COCKPIT_REL = f"{PROJECT_CONTROL_REL}/LOGION_INCIDENT_CONTROL_COCKPIT.md"
RELEASE_SPACE_AUDIT_REL = f"{PROJECT_CONTROL_REL}/LOGION_RELEASE_SPACE_AUDIT.json"
SERVICE_REGISTRY_REL = "operations/logion_services/LOGION_SERVICE_REGISTRY.json"
SERVICE_ROUTER_REL = "operations/logion_services/LOGION_SERVICE_ROUTER.json"
FUNCTION_PRODUCT_AUDIT_REL = "operations/logion_architecture/LOGION_FUNCTION_PRODUCT_SEPARATION_AUDIT.json"
FUNCTION_PRODUCT_ROUTING_REL = "operations/logion_architecture/LOGION_FUNCTION_PRODUCT_ROUTING.json"
COCKPIT_JSON_REL = f"{PROJECT_CONTROL_REL}/LOGION_PROJECT_CONTROL_COCKPIT.json"
COCKPIT_MD_REL = f"{PROJECT_CONTROL_REL}/LOGION_PROJECT_CONTROL_COCKPIT.md"
SELF_GENERATED_DIR_PREFIX = f"{PROJECT_CONTROL_REL}/"

ALL_DOMAIN_SCORECARD_REL = (
    "operations/logion_release_mission/oc_core_1_3_3/OC133_ALL_DOMAIN_READINESS_SCORECARD.json"
)
COMPUTE_AUDIT_REL = "operations/logion_release_mission/oc_core_1_3_3/OC133_COMPUTE_EFFICIENCY_AUDIT.json"
STRATEGY_BRIDGE_REL = "operations/strategy_hq_bridge/oc_core_1_3_3/OC133_STRATEGY_HQ_BRIDGE_PACKET.json"
INSTITUTE_DIRECTOR_REL = "operations/institute_director/oc_core_1_3_3/OC133_INSTITUTE_DIRECTOR_PACKET.json"
JOURNAL_INDEX_REL = "releases/oc_core_1_3_3/submission_packages/SUBMISSION_PACKAGE_INDEX.json"
CERBERUS_SUMMARY_REL = "reviews/oc133_llm_cerberus/OC133_LLM_CERBERUS_SUMMARY.json"
RELEASE_SCORECARD_REL = "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_RELEASE_SCORECARD_latest.json"

EXTERNAL_LLM_DAILY_BUDGET_TOKENS = 2_000_000
RELEASE_STATE = "OC_CORE_1_3_3_EXTERNAL_REVIEW_READY_NO_SEND"
FULL_SCIENCE_STATE = "OC_FULL_SCIENCE_PROGRAM_RUNNING"


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
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text, encoding="utf-8", newline="\n")


def sha256_object(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def git_status(root: Path) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            ["git", "status", "--short", "--branch"],
            cwd=root,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=30,
        )
    except Exception as exc:
        return {"available": False, "error": str(exc), "dirty_total": None}
    lines = completed.stdout.splitlines()
    dirty = [
        line
        for line in lines
        if line
        and not line.startswith("## ")
        and SELF_GENERATED_DIR_PREFIX not in line.replace("\\", "/")
    ]
    return {
        "available": completed.returncode == 0,
        "branch": lines[0] if lines else "",
        "dirty_total": len(dirty),
        "dirty_files_sample": dirty[:80],
    }


def dirty_tree_governance(root: Path) -> dict[str, Any]:
    required = (root / ".git").exists()
    ledger = read_json(root / DIRTY_LEDGER_REL)
    if not ledger:
        return {
            "state": "DIRTY_LEDGER_MISSING" if required else "DIRTY_LEDGER_NOT_REQUIRED_FOR_TEMP_ROOT",
            "required": required,
            "governed": not required,
            "ledger_current": not required,
            "ledger_ref": DIRTY_LEDGER_REL,
            "public_dirty_total": None,
            "private_dirty_total": None,
            "public_class_counts": {},
            "private_class_counts": {},
        }
    current = dirty_governance.current_fingerprint(root)
    ledger_current = ledger.get("dirty_tree_fingerprint") == current
    governed = (
        ledger.get("governance_state") == "GOVERNED_DIRTY_TREE"
        and ledger_current
        and ledger.get("public_unclassified_total") == 0
        and ledger.get("private_unknown_total") == 0
    )
    return {
        "state": ledger.get("governance_state", "UNKNOWN"),
        "required": required,
        "governed": governed,
        "ledger_current": ledger_current,
        "ledger_ref": DIRTY_LEDGER_REL,
        "public_dirty_total": ledger.get("public_dirty_total"),
        "private_dirty_total": ledger.get("private_dirty_total"),
        "public_class_counts": ledger.get("public_class_counts", {}),
        "private_class_counts": ledger.get("private_class_counts", {}),
        "fingerprint": ledger.get("dirty_tree_fingerprint"),
        "current_fingerprint": current,
    }


def package_summary(index: dict[str, Any]) -> dict[str, Any]:
    rows = index.get("rows") if isinstance(index.get("rows"), list) else []
    return {
        "package_total": index.get("package_total", len(rows)),
        "recommended_package_total": index.get("recommended_package_total"),
        "package_status_counts": index.get("package_status_counts", {}),
        "submission_allowed": index.get("submission_allowed"),
        "journal_submissions_allowed": index.get("journal_submissions_allowed"),
        "owner_approval_required": index.get("owner_approval_required"),
        "all_packages_owner_review_ready_no_send": (
            index.get("package_total", len(rows)) == 8
            and index.get("journal_submissions_allowed") is False
            and index.get("submission_allowed") is False
            and index.get("package_status_counts", {}).get("OWNER_REVIEW_READY_NO_SEND") == 8
        ),
    }


def resource_policy() -> dict[str, Any]:
    return {
        "schema_id": "LOGION_RESOURCE_POLICY_v1",
        "generated_at": TIMESTAMP,
        "external_llm_daily_budget_tokens": EXTERNAL_LLM_DAILY_BUDGET_TOKENS,
        "external_llm_budget_owner": "Strategy HQ/K6 under owner control",
        "external_llm_default_mode": "SPARSE_MILESTONE_REVIEW",
        "host_compute_policy": "ALLOWED_WITHIN_SAFETY_PROTOCOL",
        "internal_llm_policy": "USE_FOR_NON_RELEASE_CRITICAL_BACKGROUND_WORK_WHEN_AVAILABLE",
        "budget_override_action": "REQUEST_EXTRA_LLM_BUDGET",
        "budget_override_effect": "records owner request only; does not automatically unlock spending",
        "broad_review_allowed_when": [
            "release-critical deterministic blocker delta exists",
            "journal package milestone is ready for adversarial review",
            "owner explicitly approves a budget override",
        ],
        "forbidden_spend_patterns": [
            "full Cerberus reruns while deterministic blockers are unchanged",
            "parallel subagents without disjoint write scopes and expected blocker delta",
            "planning-only work orders executed as scientific repair",
            "release package regeneration when the Delta Queue semantic fingerprint is unchanged",
        ],
        "delta_queue_policy": {
            "policy_ref": DELTA_QUEUE_POLICY_REL,
            "ledger_ref": DELTA_QUEUE_LEDGER_REL,
            "principle": "No downstream capability signal without a material qualitative delta over threshold.",
            "release_checks_default_mode": "release",
        },
        "no_send": True,
        "publish_allowed": False,
        "journal_submissions_allowed": False,
    }


def workstream_locks() -> dict[str, Any]:
    return {
        "schema_id": "LOGION_WORKSTREAM_LOCKS_v1",
        "generated_at": TIMESTAMP,
        "global_no_send": True,
        "locks": [
            {
                "lock_id": "OC133_RELEASE_ARTIFACT_LOCK",
                "owner_workstream": "OC133_RELEASE_FOREGROUND",
                "protected_paths": [
                    "releases/oc_core_1_3_3/",
                    "claims/CLAIM_LEDGER_1_3_3.json",
                    "proofs/",
                    "formal/lean/",
                ],
                "write_allowed_for": ["release stabilization", "journal package verification", "bounded claim governance"],
                "background_science_write_allowed": False,
            },
            {
                "lock_id": "OC_FULL_SCIENCE_BACKGROUND_LOCK",
                "owner_workstream": "OC_FULL_SCIENCE_BACKGROUND",
                "protected_paths": [
                    "validation/heldout/",
                    "benchmarks/modern_science/",
                    "comparators/modern_science/",
                    "operations/logion_release_mission/oc_core_1_3_3/",
                ],
                "write_allowed_for": ["research queue", "evidence lanes", "future-release roadmap"],
                "release_package_regeneration_allowed": False,
            },
            {
                "lock_id": "NON_OC_WORKSTREAM_ISOLATION_LOCK",
                "owner_workstream": "ESTRA_TOOLKIT_EA2O_OTHER",
                "protected_paths": ["estra toolkit workstream", "EA2O workstream", "business/product workstreams"],
                "may_mutate_oc133_release_artifacts": False,
            },
        ],
        "collision_policy": "If a planned write crosses workstream ownership, controller must block it or require an explicit handoff record.",
    }


def milestone_plan() -> dict[str, Any]:
    return {
        "schema_id": "LOGION_MILESTONE_PLAN_v1",
        "generated_at": TIMESTAMP,
        "foreground_release": {
            "release_id": "oc_core_1_3_3",
            "target_state": RELEASE_STATE,
            "minimum_contents": [
                "typed model foundation",
                "theorem inventory and proof sheets",
                "Lean and finite-model evidence",
                "bounded cross-domain empirical/formal evidence",
                "novelty and comparator positioning",
                "hostile-reader guide with explicit boundaries",
                "8 owner-review-ready no-send journal packages",
            ],
        },
        "background_science_releases": [
            {
                "release": "1.3.4",
                "goal": "empirical lane expansion with additional target-blind/held-out evidence packs",
            },
            {
                "release": "1.4.0",
                "goal": "broad modern-science comparator program and source-backed superiority tests",
            },
            {
                "release": "1.5.x",
                "goal": "product/tool integration evidence and operational domain packages",
            },
            {
                "release": "future full-domain projection series",
                "goal": "complete domain projection atlas and stronger TOE obligations when evidence exists",
            },
        ],
        "background_lane_contract": [
            "source lock",
            "target-blind or held-out protocol",
            "formula",
            "comparator",
            "uncertainty",
            "residual",
            "negative control",
            "falsifier",
            "replay hash",
        ],
    }


def build_portfolio(root: Path) -> dict[str, Any]:
    all_domain = read_json(root / ALL_DOMAIN_SCORECARD_REL)
    compute = read_json(root / COMPUTE_AUDIT_REL)
    bridge = read_json(root / STRATEGY_BRIDGE_REL)
    director = read_json(root / INSTITUTE_DIRECTOR_REL)
    journal = read_json(root / JOURNAL_INDEX_REL)
    cerberus = read_json(root / CERBERUS_SUMMARY_REL)
    release = read_json(root / RELEASE_SCORECARD_REL)
    dirty = dirty_tree_governance(root)
    delta_queue = read_json(root / DELTA_QUEUE_LEDGER_REL)
    coherence = read_json(root / PROCESS_COHERENCE_GUARD_REL)
    incident_queue = read_json(root / INCIDENT_QUEUE_REL)
    escalation_matrix = read_json(root / ESCALATION_MATRIX_REL)
    release_space = read_json(root / RELEASE_SPACE_AUDIT_REL)
    service_registry = read_json(root / SERVICE_REGISTRY_REL)
    service_router = read_json(root / SERVICE_ROUTER_REL)
    function_product = read_json(root / FUNCTION_PRODUCT_AUDIT_REL)
    function_product_routing = read_json(root / FUNCTION_PRODUCT_ROUTING_REL)

    external_ready = all_domain.get("external_review_ready_no_send") is True
    all_domain_ready = all_domain.get("all_domain_ready_no_send") is True
    release_state = (
        "ALL_DOMAIN_READY_NO_SEND"
        if all_domain_ready
        else RELEASE_STATE
        if external_ready
        else all_domain.get("final_readiness_state", "UNKNOWN")
    )
    workstreams = [
        {
            "workstream_id": "OC133_RELEASE_FOREGROUND",
            "state": release_state,
            "priority": 1,
            "current_focus": "bounded external-review-ready release package",
            "may_use_external_llm": True,
            "external_llm_budget_class": "release-critical sparse review",
            "release_artifact_write_owner": True,
        },
        {
            "workstream_id": "OC_FULL_SCIENCE_BACKGROUND",
            "state": all_domain.get("full_science_program_state", FULL_SCIENCE_STATE),
            "priority": 2,
            "current_focus": "complete domain projection and broad comparator/superiority research",
            "may_use_external_llm": True,
            "external_llm_budget_class": "2M/day research contour",
            "release_artifact_write_owner": False,
        },
        {
            "workstream_id": "ESTRA_TOOLKIT",
            "state": "AVAILABLE_ISOLATED_NOT_OC133_RELEASE_OWNER",
            "priority": 3,
            "current_focus": "separate product/tool workstream",
            "may_use_external_llm": False,
            "release_artifact_write_owner": False,
        },
        {
            "workstream_id": "EA2O",
            "state": "AVAILABLE_ISOLATED_NOT_OC133_RELEASE_OWNER",
            "priority": 4,
            "current_focus": "separate architecture/business workstream",
            "may_use_external_llm": False,
            "release_artifact_write_owner": False,
        },
        {
            "workstream_id": "OTHER_WORKSTREAMS",
            "state": "AVAILABLE_ISOLATED_NOT_OC133_RELEASE_OWNER",
            "priority": 5,
            "current_focus": "explicit handoff required before touching OC133 release artifacts",
            "may_use_external_llm": False,
            "release_artifact_write_owner": False,
        },
    ]
    return {
        "schema_id": "LOGION_WORKSTREAM_PORTFOLIO_v1",
        "generated_at": TIMESTAMP,
        "authority_chain": ["Safety Directive", "LOGI", "K6 Strategy HQ", "Project Controller", "Capability Directors"],
        "portfolio_state": "LOGION_PROJECT_CONTROL_ACTIVE",
        "release_id": "oc_core_1_3_3",
        "release_state": release_state,
        "external_review_ready_no_send": external_ready,
        "all_domain_ready_no_send": all_domain_ready,
        "full_science_program_state": all_domain.get("full_science_program_state", FULL_SCIENCE_STATE),
        "all_domain_blocker_total": all_domain.get("blocker_total"),
        "all_domain_blocker_ids": all_domain.get("blocker_ids", []),
        "release_machine_state": release.get("summary", {}).get("release_state"),
        "cerberus_critical_open_total": cerberus.get("critical_open_total"),
        "cerberus_high_open_total": cerberus.get("high_open_total"),
        "journal_packages": package_summary(journal),
        "compute_efficiency": compute.get("findings", {}),
        "strategy_bridge_state": bridge.get("bridge_verdict"),
        "institute_director_state": director.get("director_verdict"),
        "workstreams": workstreams,
        "git_state": git_status(root),
        "dirty_tree_governance": dirty,
        "dirty_tree_governance_state": dirty["state"],
        "dirty_tree_governed": dirty["governed"],
        "dirty_tree_ledger_current": dirty["ledger_current"],
        "delta_queue": {
            "ledger_ref": DELTA_QUEUE_LEDGER_REL,
            "mode": delta_queue.get("mode"),
            "semantic_fingerprint": delta_queue.get("semantic_fingerprint"),
            "significant_delta": delta_queue.get("significant_delta"),
            "changed_classes": delta_queue.get("changed_classes", []),
            "downstream_trigger_allowed": delta_queue.get("downstream_trigger_allowed"),
            "no_send_valid": delta_queue.get("no_send_valid"),
        },
        "process_coherence": {
            "guard_ref": PROCESS_COHERENCE_GUARD_REL,
            "state": coherence.get("state"),
            "critical_high_total": coherence.get("critical_high_total"),
            "issue_total": coherence.get("issue_total"),
        },
        "incident_control": {
            "matrix_ref": ESCALATION_MATRIX_REL,
            "queue_ref": INCIDENT_QUEUE_REL,
            "cockpit_ref": INCIDENT_COCKPIT_REL,
            "matrix_present": bool(escalation_matrix),
            "incident_total": incident_queue.get("incident_total"),
            "p0_total": incident_queue.get("p0_total"),
            "active_total": incident_queue.get("active_total"),
            "queue_hash": incident_queue.get("queue_hash"),
            "manual_repair_allowed": escalation_matrix.get("manual_repair_policy", {}).get("codex_direct_hand_fix_allowed"),
        },
        "service_architecture": {
            "service_registry_ref": SERVICE_REGISTRY_REL,
            "service_router_ref": SERVICE_ROUTER_REL,
            "service_total": service_registry.get("service_total"),
            "route_total": len(service_router.get("routes", [])),
            "registry_hash": service_registry.get("registry_hash"),
            "router_hash": service_router.get("router_hash"),
        },
        "function_product_separation": {
            "audit_ref": FUNCTION_PRODUCT_AUDIT_REL,
            "routing_ref": FUNCTION_PRODUCT_ROUTING_REL,
            "state": function_product.get("state"),
            "failure_total": function_product.get("failure_total"),
            "metrics": function_product.get("quantitative_metrics", {}),
            "routing_row_total": function_product_routing.get("routing_row_total"),
        },
        "release_space_control": {
            "audit_ref": RELEASE_SPACE_AUDIT_REL,
            "state": release_space.get("state"),
            "failure_total": release_space.get("failure_total"),
            "control_language_hit_total": release_space.get("control_language_hit_total"),
            "release_space_path_total": release_space.get("release_space_path_total"),
        },
        "no_send": True,
        "publish_allowed": False,
        "journal_submissions_allowed": False,
    }


def budget_ledger(root: Path, portfolio: dict[str, Any]) -> dict[str, Any]:
    policy = resource_policy()
    return {
        "schema_id": "LOGION_BUDGET_LEDGER_v1",
        "generated_at": TIMESTAMP,
        "daily_external_llm_budget_tokens": EXTERNAL_LLM_DAILY_BUDGET_TOKENS,
        "daily_external_llm_spent_tokens_recorded": 0,
        "daily_external_llm_remaining_tokens_recorded": EXTERNAL_LLM_DAILY_BUDGET_TOKENS,
        "host_compute_allowed": True,
        "budget_override_action": policy["budget_override_action"],
        "budget_override_requested": False,
        "budget_override_approved": False,
        "budget_rows": [
            {
                "workstream_id": "OC133_RELEASE_FOREGROUND",
                "external_llm_token_budget": 500_000,
                "policy": "release-critical review only",
            },
            {
                "workstream_id": "OC_FULL_SCIENCE_BACKGROUND",
                "external_llm_token_budget": 1_500_000,
                "policy": "background research contour; local host first",
            },
            {
                "workstream_id": "ESTRA_TOOLKIT",
                "external_llm_token_budget": 0,
                "policy": "use internal/local mechanisms unless separately budgeted",
            },
            {
                "workstream_id": "EA2O",
                "external_llm_token_budget": 0,
                "policy": "use internal/local mechanisms unless separately budgeted",
            },
        ],
        "release_state": portfolio["release_state"],
        "input_refs": [PORTFOLIO_REL, RESOURCE_POLICY_REL],
        "ledger_hash": "",
    }


def render_cockpit(cockpit: dict[str, Any]) -> str:
    portfolio = cockpit["portfolio"]
    budget = cockpit["budget_ledger"]
    lines = [
        "# Logion Project Control Cockpit",
        "",
        f"- Portfolio state: `{portfolio['portfolio_state']}`",
        f"- OC133 release state: `{portfolio['release_state']}`",
        f"- External-review ready no-send: `{str(portfolio['external_review_ready_no_send']).lower()}`",
        f"- Full science program: `{portfolio['full_science_program_state']}`",
        f"- All-domain blockers: `{portfolio['all_domain_blocker_total']}`",
        f"- Cerberus critical/high: `{portfolio.get('cerberus_critical_open_total')}` / `{portfolio.get('cerberus_high_open_total')}`",
        f"- Journal packages: `{portfolio['journal_packages']['package_total']}`",
        f"- Dirty tree governed/current: `{str(portfolio['dirty_tree_governed']).lower()}` / `{str(portfolio['dirty_tree_ledger_current']).lower()}`",
        f"- Delta Queue significant/trigger: `{str(portfolio['delta_queue'].get('significant_delta')).lower()}` / `{str(portfolio['delta_queue'].get('downstream_trigger_allowed')).lower()}`",
        f"- Process coherence: `{portfolio['process_coherence'].get('state')}` critical/high=`{portfolio['process_coherence'].get('critical_high_total')}`",
        f"- Incident queue P0/active: `{portfolio['incident_control'].get('p0_total')}` / `{portfolio['incident_control'].get('active_total')}`",
        f"- Manual repair allowed: `{str(portfolio['incident_control'].get('manual_repair_allowed')).lower()}`",
        f"- Services/routes: `{portfolio['service_architecture'].get('service_total')}` / `{portfolio['service_architecture'].get('route_total')}`",
        f"- Function/product separation: `{portfolio['function_product_separation'].get('state')}` failures=`{portfolio['function_product_separation'].get('failure_total')}`",
        f"- Release-space audit: `{portfolio['release_space_control'].get('state')}` control hits=`{portfolio['release_space_control'].get('control_language_hit_total')}`",
        f"- External LLM budget/day: `{budget['daily_external_llm_budget_tokens']}`",
        f"- Host compute: `allowed`",
        f"- Budget action: `{budget['budget_override_action']}`",
        "",
        "## Workstreams",
        "",
    ]
    for row in portfolio["workstreams"]:
        lines.append(
            f"- `{row['workstream_id']}` state=`{row['state']}` priority=`{row['priority']}` release_owner=`{str(row['release_artifact_write_owner']).lower()}`"
        )
    lines.extend(["", "## Locks", ""])
    for row in cockpit["workstream_locks"]["locks"]:
        lines.append(
            f"- `{row['lock_id']}` owner=`{row['owner_workstream']}` background_release_write=`{str(row.get('background_science_write_allowed', row.get('may_mutate_oc133_release_artifacts', False))).lower()}`"
        )
    lines.extend(["", f"Controller hash: `{cockpit['controller_hash']}`", ""])
    return "\n".join(lines)


def build_cockpit(root: Path = ROOT) -> dict[str, Any]:
    portfolio = build_portfolio(root)
    policy = resource_policy()
    locks = workstream_locks()
    milestones = milestone_plan()
    budget = budget_ledger(root, portfolio)
    budget["ledger_hash"] = sha256_object({key: value for key, value in budget.items() if key != "ledger_hash"})
    cockpit = {
        "schema_id": "LOGION_PROJECT_CONTROL_COCKPIT_v1",
        "generated_at": TIMESTAMP,
        "portfolio": portfolio,
        "resource_policy": policy,
        "budget_ledger": budget,
        "workstream_locks": locks,
        "milestone_plan": milestones,
        "refs": {
            "portfolio_ref": PORTFOLIO_REL,
            "resource_policy_ref": RESOURCE_POLICY_REL,
            "budget_ledger_ref": BUDGET_LEDGER_REL,
            "workstream_locks_ref": WORKSTREAM_LOCKS_REL,
            "milestone_plan_ref": MILESTONE_PLAN_REL,
            "dirty_tree_ledger_ref": DIRTY_LEDGER_REL,
            "delta_queue_ledger_ref": DELTA_QUEUE_LEDGER_REL,
            "delta_queue_policy_ref": DELTA_QUEUE_POLICY_REL,
            "process_coherence_guard_ref": PROCESS_COHERENCE_GUARD_REL,
            "escalation_matrix_ref": ESCALATION_MATRIX_REL,
            "incident_queue_ref": INCIDENT_QUEUE_REL,
            "incident_cockpit_ref": INCIDENT_COCKPIT_REL,
            "cockpit_json_ref": COCKPIT_JSON_REL,
            "cockpit_md_ref": COCKPIT_MD_REL,
        },
        "controller_hash": "",
    }
    cockpit["controller_hash"] = sha256_object({key: value for key, value in cockpit.items() if key != "controller_hash"})
    return cockpit


def write_outputs(root: Path, cockpit: dict[str, Any]) -> None:
    write_json(root / PORTFOLIO_REL, cockpit["portfolio"])
    write_json(root / RESOURCE_POLICY_REL, cockpit["resource_policy"])
    write_json(root / BUDGET_LEDGER_REL, cockpit["budget_ledger"])
    write_json(root / WORKSTREAM_LOCKS_REL, cockpit["workstream_locks"])
    write_json(root / MILESTONE_PLAN_REL, cockpit["milestone_plan"])
    write_json(root / COCKPIT_JSON_REL, cockpit)
    write_text(root / COCKPIT_MD_REL, render_cockpit(cockpit))


def check_outputs(root: Path, cockpit: dict[str, Any]) -> list[str]:
    expected = {
        PORTFOLIO_REL: cockpit["portfolio"],
        RESOURCE_POLICY_REL: cockpit["resource_policy"],
        BUDGET_LEDGER_REL: cockpit["budget_ledger"],
        WORKSTREAM_LOCKS_REL: cockpit["workstream_locks"],
        MILESTONE_PLAN_REL: cockpit["milestone_plan"],
        COCKPIT_JSON_REL: cockpit,
    }
    mismatches = []
    for rel_path, payload in expected.items():
        if read_json(root / rel_path) != payload:
            mismatches.append(rel_path)
    if not (root / COCKPIT_MD_REL).exists() or (root / COCKPIT_MD_REL).read_text(encoding="utf-8") != render_cockpit(cockpit):
        mismatches.append(COCKPIT_MD_REL)
    dirty = cockpit["portfolio"]["dirty_tree_governance"]
    if dirty["required"] and not dirty["governed"]:
        mismatches.append(DIRTY_LEDGER_REL)
    return mismatches


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Logion project control, budget, and workstream isolation cockpit.")
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    if args.write:
        ledger = dirty_governance.build_ledger(root)
        dirty_governance.write_json(root / dirty_governance.LEDGER_REL, ledger)
        dirty_governance.write_text(root / dirty_governance.LEDGER_MD_REL, dirty_governance.render_markdown(ledger))
    cockpit = build_cockpit(root)
    if args.write:
        write_outputs(root, cockpit)
    if args.check:
        mismatches = check_outputs(root, cockpit)
        if mismatches:
            print(json.dumps({"state": "FAIL", "mismatches": mismatches}, ensure_ascii=False, indent=2))
            return 1
    print(
        json.dumps(
            {
                "state": cockpit["portfolio"]["portfolio_state"],
                "release_state": cockpit["portfolio"]["release_state"],
                "external_review_ready_no_send": cockpit["portfolio"]["external_review_ready_no_send"],
                "daily_external_llm_budget_tokens": cockpit["budget_ledger"]["daily_external_llm_budget_tokens"],
                "dirty_tree_governed": cockpit["portfolio"]["dirty_tree_governed"],
                "dirty_tree_ledger_current": cockpit["portfolio"]["dirty_tree_ledger_current"],
                "cockpit_ref": COCKPIT_JSON_REL,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
