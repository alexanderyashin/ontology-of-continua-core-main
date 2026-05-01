from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROJECT_CONTROL_REL = "operations/project_control"
MATRIX_REL = f"{PROJECT_CONTROL_REL}/LOGION_ESCALATION_MATRIX.json"
PLAYBOOK_REL = f"{PROJECT_CONTROL_REL}/LOGION_INCIDENT_RESPONSE_PLAYBOOK.json"
QUEUE_REL = f"{PROJECT_CONTROL_REL}/LOGION_INCIDENT_QUEUE.json"
COCKPIT_REL = f"{PROJECT_CONTROL_REL}/LOGION_INCIDENT_CONTROL_COCKPIT.md"
INCIDENTS_REL = "operations/incidents"

OC133_INCIDENT_ID = "INC_OC133_PUBLIC_RELEASE_MONOGRAPH_SURROGATE_20260501"


def read_json(path: Path, default: Any | None = None) -> Any:
    if not path.exists():
        return {} if default is None else default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {} if default is None else default


def write_json_if_changed(path: Path, payload: Any) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if path.exists() and path.read_bytes() == data:
        return False
    path.write_bytes(data)
    return True


def write_text_if_changed(path: Path, text: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (text.rstrip() + "\n").encode("utf-8")
    if path.exists() and path.read_bytes() == data:
        return False
    path.write_bytes(data)
    return True


def sha256_object(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def build_capability_directory() -> list[dict[str, Any]]:
    return [
        {
            "capability_id": "StrategyHQ/IncidentCommand",
            "director": "K6 Strategy HQ",
            "manager_roles": ["incident commander", "decision-quality controller", "resource controller"],
            "executor_boundary": "may route, freeze, authorize, and require work orders; does not hand-edit release science",
            "primary_artifacts": [QUEUE_REL, COCKPIT_REL],
        },
        {
            "capability_id": "ServiceArchitecture/Router",
            "director": "K6 Strategy HQ / Service Architecture",
            "manager_roles": ["service registry owner", "service router owner", "boundary-contract auditor"],
            "executor_boundary": "defines independent Logion services and routes signals between them; does not absorb service work into incidents",
            "primary_artifacts": [
                "operations/logion_services/LOGION_SERVICE_REGISTRY.json",
                "operations/logion_services/LOGION_SERVICE_ROUTER.json",
            ],
        },
        {
            "capability_id": "Research/ManuscriptIntegration",
            "director": "Institute Director / Research Director",
            "manager_roles": ["corpus curator", "science-to-manuscript integrator", "claim-boundary reviewer"],
            "executor_boundary": "builds the science monolith and corpus ledger from approved public-safe science sources",
            "primary_artifacts": [
                "releases/oc_core_1_3_3/artifacts/OC_CORE_1_3_3_MASTER_MONOGRAPH_EN.pdf",
                "releases/oc_core_1_3_3/editorial/SCIENCE_MONOLITH_CORPUS_LEDGER_1_3_3_latest.json",
            ],
        },
        {
            "capability_id": "Research/EmpiricalScience",
            "director": "Institute Director / Empirical Science Director",
            "manager_roles": ["evidence-lane planner", "target-blind replay owner", "comparator protocol owner"],
            "executor_boundary": "runs background evidence lanes and candidate-pack validators; cannot promote grand claims without promotion gates",
            "primary_artifacts": [
                "validation/heldout/grand_science_evidence_registry.json",
                "reports/OC_CORE_1_3_3_GRAND_EMPIRICAL_REPORT.json",
                "operations/logion_release_mission/oc_core_1_3_3/OC133_GRAND_SCIENCE_RESEARCH_PROGRAM.json",
            ],
        },
        {
            "capability_id": "IT/ReleaseAutomation",
            "director": "IT Department Director",
            "manager_roles": ["release-machine maintainer", "Delta Queue maintainer", "safe-executor maintainer"],
            "executor_boundary": "edits automation, gates, templates, and deterministic generators; never promotes unsupported claims",
            "primary_artifacts": [
                "release_machine/public_release.py",
                "release_machine/science_monolith.py",
                "tools/oc133_public_release_payload.py",
                "tools/logion_incident_pipeline.py",
            ],
        },
        {
            "capability_id": "Review/Cerberus",
            "director": "Review Director",
            "manager_roles": ["hostile reviewer", "claim-boundary prosecutor", "public-surface auditor"],
            "executor_boundary": "opens findings and validates closure evidence; artifact existence is never closure",
            "primary_artifacts": [
                "reviews/oc133_llm_cerberus/OC133_LLM_CERBERUS_SUMMARY.json",
                "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_PERSONAL_RELEASE_AUDIT_latest.json",
            ],
        },
        {
            "capability_id": "Publication/PublicRecords",
            "director": "Publication Director",
            "manager_roles": ["GitHub release executor", "Zenodo executor", "metadata curator"],
            "executor_boundary": "publishes only after StrategyHQ approval, clean local gates, exact asset set, and production tokens",
            "primary_artifacts": [
                "releases/oc_core_1_3_3/editorial/PUBLIC_RELEASE_EXECUTION_REPORT_v1.3.3.json",
                "releases/oc_core_1_3_3/editorial/PUBLIC_RELEASE_PRESENTATION_1.3.3_latest.json",
            ],
        },
        {
            "capability_id": "Safety/Governance",
            "director": "Safety Directive / LOGI",
            "manager_roles": ["no-send lock owner", "secret/local-path scanner", "publication-scope controller"],
            "executor_boundary": "blocks unsafe scope, secret leakage, private-path leakage, or unapproved public action",
            "primary_artifacts": [
                "releases/oc_core_1_3_3/editorial/OWNER_RELEASE_APPROVAL_v1.3.3.json",
                "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_PUBLISH_MANIFEST_DRAFT.json",
            ],
        },
    ]


def build_matrix() -> dict[str, Any]:
    severity_tiers = [
        {
            "severity": "P0",
            "name": "PUBLIC_RELEASE_OR_SAFETY_DEFECT",
            "examples": [
                "bad public GitHub/Zenodo release",
                "wrong primary scientific asset",
                "secret/local private path leak",
                "journal/SWH/email scope opened without explicit approval",
            ],
            "strategy_hq_signal": "IMMEDIATE",
            "freeze_policy": "freeze further public actions except controlled replacement/containment",
            "sla": "same working session until contained or explicitly blocked by external service",
            "closure_authority": ["Safety/Governance", "StrategyHQ/IncidentCommand", "Owner"],
        },
        {
            "severity": "P1",
            "name": "RELEASE_BLOCKING_SCIENTIFIC_OR_REPRODUCIBILITY_DEFECT",
            "examples": ["G32-G70 fail", "Cerberus critical/high open", "strict reproducibility fail"],
            "strategy_hq_signal": "HIGH_PRIORITY",
            "freeze_policy": "block release readiness; allow capability-owned repair",
            "sla": "before any publication/replacement action",
            "closure_authority": ["StrategyHQ/IncidentCommand", "Review/Cerberus", "affected capability director"],
        },
        {
            "severity": "P2",
            "name": "BACKGROUND_SCIENCE_OR_ROADMAP_DEFECT",
            "examples": ["grand TOE evidence blocker", "modern-science superiority not yet evidenced"],
            "strategy_hq_signal": "QUEUE_BACKGROUND",
            "freeze_policy": "do not block bounded release if claim boundary excludes it",
            "sla": "roadmap milestone",
            "closure_authority": ["Research Director", "StrategyHQ/IncidentCommand"],
        },
        {
            "severity": "P3",
            "name": "PROCESS_TELEMETRY_OR_DELTA_QUEUE_DEFECT",
            "examples": ["read-only check dirties tree", "stale dirty ledger", "unnecessary rerun chain"],
            "strategy_hq_signal": "NORMAL",
            "freeze_policy": "block automation loop that self-dirties until coherence is restored",
            "sla": "next controller refresh",
            "closure_authority": ["IT/ReleaseAutomation", "Project Controller"],
        },
        {
            "severity": "P4",
            "name": "COSMETIC_OR_NON_RELEASE_DEFECT",
            "examples": ["non-public wording cleanup", "background note formatting"],
            "strategy_hq_signal": "LOW",
            "freeze_policy": "no release freeze unless it crosses public-surface gates",
            "sla": "batch with next relevant artifact regeneration",
            "closure_authority": ["owning capability manager"],
        },
    ]
    routing_rules = [
        {
            "signal_class": "bad_public_release_record",
            "severity": "P0",
            "owner_capability": "StrategyHQ/IncidentCommand",
            "support_capabilities": ["Publication/PublicRecords", "IT/ReleaseAutomation", "Research/ManuscriptIntegration", "Review/Cerberus"],
            "required_work_order_fields": [
                "work_order_id",
                "owner_capability",
                "artifacts",
                "closure_predicate",
                "verification_command",
                "rollback_or_block_rule",
            ],
            "safe_executor_policy": "controlled replacement only; no one-off manual asset upload",
            "closure_evidence_required": ["postflight PASS", "exact GitHub asset set", "exact Zenodo file set", "incident postmortem"],
        },
        {
            "signal_class": "service_boundary_confusion",
            "severity": "P1",
            "owner_capability": "ServiceArchitecture/Router",
            "support_capabilities": ["StrategyHQ/IncidentCommand", "IT/ReleaseAutomation", "Research/ManuscriptIntegration", "Publication/PublicRecords"],
            "safe_executor_policy": "service registry/router contract; incident, editorial, research, verification, release, and publication remain independent services",
            "closure_evidence_required": [
                "LOGION_SERVICE_REGISTRY PASS",
                "incident_management and editorial_manuscript are separate service ids",
                "routes assign primary/downstream services without monolithic pipeline ownership",
            ],
        },
        {
            "signal_class": "function_product_confusion",
            "severity": "P1",
            "owner_capability": "ServiceArchitecture/Router",
            "support_capabilities": ["StrategyHQ/IncidentCommand", "Research/ManuscriptIntegration", "IT/ReleaseAutomation", "Publication/PublicRecords"],
            "safe_executor_policy": "function/product separation audit; functions, production lines, repair lines, methods, machines, and products must be distinct ledgers",
            "closure_evidence_required": [
                "LOGION_FUNCTION_PRODUCT_SEPARATION_AUDIT state PASS",
                "function_registry_product_token_hit_total=0",
                "production_line_product_token_hit_total=0",
                "product outcomes are represented only in LOGION_PRODUCT_OUTCOME_LEDGER",
            ],
        },
        {
            "signal_class": "science_to_manuscript_projection_gap",
            "severity": "P1",
            "owner_capability": "Research/ManuscriptIntegration",
            "support_capabilities": ["IT/ReleaseAutomation", "Review/Cerberus"],
            "safe_executor_policy": "science_monolith builder and corpus ledger only",
            "closure_evidence_required": ["SCIENCE_MONOLITH_AUDIT PASS", "corpus ledger missing_total=0"],
        },
        {
            "signal_class": "public_payload_role_semantics_gap",
            "severity": "P1",
            "owner_capability": "IT/ReleaseAutomation",
            "support_capabilities": ["Publication/PublicRecords", "Review/Cerberus"],
            "safe_executor_policy": "public-payload builder/gates; reject route sheets and no-send primary assets",
            "closure_evidence_required": [
                "public payload materialized after source rebinding",
                "PUBLIC_PAYLOAD_SUITABILITY PASS",
                "PUBLIC_FILE_SET_GATE ok",
            ],
        },
        {
            "signal_class": "approval_scope_contract_conflict",
            "severity": "P1",
            "owner_capability": "IT/ReleaseAutomation",
            "support_capabilities": ["Safety/Governance", "Review/Cerberus"],
            "safe_executor_policy": "mode-aware gate contracts; no-send checks remain strict in no-send mode",
            "closure_evidence_required": ["finite checks PASS in current mode", "owner audit blocker_total=0"],
        },
        {
            "signal_class": "source_certificate_binding_drift",
            "severity": "P1",
            "owner_capability": "IT/ReleaseAutomation",
            "support_capabilities": ["Research/ManuscriptIntegration", "Review/Cerberus"],
            "safe_executor_policy": "pre-approval certificate rebinding through materializer; publication approval controls must not be reset after approval",
            "closure_evidence_required": ["LEAN certificate source manifest matches current source", "finite model certificate_binding_failure_total=0"],
        },
        {
            "signal_class": "background_science_evidence_gap",
            "severity": "P2",
            "owner_capability": "Research/EmpiricalScience",
            "support_capabilities": ["Research/PriorArt", "Review/Cerberus"],
            "safe_executor_policy": "background evidence lanes only; cannot mutate public release claims without promotion gate",
            "closure_evidence_required": ["valid evidence pack", "comparator result", "claim promotion gate PASS"],
        },
        {
            "signal_class": "self_dirtying_verification",
            "severity": "P3",
            "owner_capability": "IT/ReleaseAutomation",
            "support_capabilities": ["Project Controller"],
            "safe_executor_policy": "Delta Queue thresholding; read-only checks cannot alter release package artifacts",
            "closure_evidence_required": ["repeat check significant_delta=false", "public/private trees clean or governed"],
        },
    ]
    return {
        "schema_id": "LOGION_ESCALATION_MATRIX_v1",
        "authority_chain": ["Safety Directive", "LOGI", "K6 Strategy HQ", "Project Controller", "Capability Directors", "Executors"],
        "manual_repair_policy": {
            "codex_direct_hand_fix_allowed": False,
            "capability_executor_required": True,
            "artifact_exists_is_not_closure": True,
            "closure_must_cite_evidence": True,
        },
        "severity_tiers": severity_tiers,
        "capability_directory": build_capability_directory(),
        "routing_rules": routing_rules,
        "matrix_hash": "",
    }


def classify_incident(payload: dict[str, Any]) -> dict[str, Any]:
    incident_id = payload.get("incident_id", "UNKNOWN")
    bad_records = payload.get("bad_public_records", [])
    root_causes = payload.get("root_causes", [])
    work_orders = payload.get("work_orders", [])
    if bad_records:
        severity = "P0"
        signal_class = "bad_public_release_record"
    elif any("monograph" in json.dumps(row).lower() for row in root_causes):
        severity = "P1"
        signal_class = "science_to_manuscript_projection_gap"
    else:
        severity = "P3"
        signal_class = "process_telemetry_or_delta_queue_defect"
    open_orders = [row for row in work_orders if row.get("status") not in {"CLOSED"}]
    return {
        "incident_id": incident_id,
        "severity": severity,
        "signal_class": signal_class,
        "state": payload.get("state"),
        "open_work_order_total": len(open_orders),
        "next_required_action": (
            "controlled_public_replacement"
            if severity == "P0" and len(open_orders) == 1 and open_orders[0].get("owner_capability") == "Publication/PublicRecords"
            else "capability_repair_loop"
            if open_orders
            else "postmortem_closeout"
        ),
        "strategy_hq_notified": True,
        "incident_commander": "K6 Strategy HQ",
        "capability_owners": sorted({row.get("owner_capability") for row in work_orders if row.get("owner_capability")}),
        "case_ref": f"{INCIDENTS_REL}/{incident_id}/INCIDENT_CASE.json",
    }


def build_queue(root: Path = ROOT) -> dict[str, Any]:
    incidents = []
    incident_root = root / INCIDENTS_REL
    if incident_root.exists():
        for path in sorted(incident_root.glob("*/INCIDENT_CASE.json")):
            payload = read_json(path, {})
            if isinstance(payload, dict) and payload:
                incidents.append(classify_incident(payload))
    incidents.sort(key=lambda row: ({"P0": 0, "P1": 1, "P2": 2, "P3": 3, "P4": 4}.get(row["severity"], 9), row["incident_id"]))
    return {
        "schema_id": "LOGION_INCIDENT_QUEUE_v1",
        "authority_home": "Strategy HQ / K6",
        "incident_total": len(incidents),
        "p0_total": sum(1 for row in incidents if row["severity"] == "P0"),
        "active_total": sum(1 for row in incidents if row["state"] not in {"CLOSED", "POSTMORTEM_CLOSED"}),
        "rows": incidents,
        "queue_hash": sha256_object(incidents),
    }


def build_playbook(matrix: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_id": "LOGION_INCIDENT_RESPONSE_PLAYBOOK_v1",
        "entry_conditions": [
            "public surface defect",
            "release gate fail",
            "self-dirtying verification loop",
            "claim/evidence contradiction",
            "missing capability executor for a repeated repair class",
        ],
        "response_steps": [
            "open incident under operations/incidents/<incident_id>",
            "classify severity through LOGION_ESCALATION_MATRIX",
            "freeze unsafe downstream actions according to severity tier",
            "assign capability-owned work orders with closure predicates",
            "run only safe executors or create an IT work order if no executor exists",
            "rerun deterministic gates and Cerberus/review gates only when Delta Queue reports material change",
            "publish or replace public records only after StrategyHQ and Safety/Governance closure",
            "write postmortem, regression gate, and project-control update",
        ],
        "required_case_artifacts": [
            "INCIDENT_CASE.json",
            "WORK_ORDERS.json",
            "RCA_AND_COCKPIT.md",
            "ARCHITECTURE_SELF_REPAIR_CONTRACT.json",
            "ARCHITECTURE_SELF_REPAIR_EXECUTION.json when self-repair runs",
        ],
        "routing_rules": [row["signal_class"] for row in matrix["routing_rules"]],
        "no_manual_bypass_rule": "If no safe executor exists, the next action is an IT capability work order to build one; direct artifact patching is not closure.",
    }


def render_cockpit(matrix: dict[str, Any], queue: dict[str, Any]) -> str:
    lines = [
        "# Logion Incident Control Cockpit",
        "",
        f"- authority: `{queue['authority_home']}`",
        f"- incidents: `{queue['incident_total']}`",
        f"- P0 incidents: `{queue['p0_total']}`",
        f"- active incidents: `{queue['active_total']}`",
        f"- manual repair allowed: `{str(matrix['manual_repair_policy']['codex_direct_hand_fix_allowed']).lower()}`",
        f"- queue hash: `{queue['queue_hash']}`",
        "",
        "## Active Queue",
        "",
    ]
    if not queue["rows"]:
        lines.append("- none")
    for row in queue["rows"]:
        lines.append(
            f"- `{row['incident_id']}` severity=`{row['severity']}` signal=`{row['signal_class']}` state=`{row['state']}` next=`{row['next_required_action']}`"
        )
    lines.extend(["", "## Routing Rules", ""])
    for row in matrix["routing_rules"]:
        lines.append(f"- `{row['signal_class']}` -> `{row['severity']}` `{row['owner_capability']}`")
    return "\n".join(lines)


def build_outputs(root: Path = ROOT) -> dict[str, Any]:
    matrix = build_matrix()
    matrix["matrix_hash"] = sha256_object({key: value for key, value in matrix.items() if key != "matrix_hash"})
    queue = build_queue(root)
    playbook = build_playbook(matrix)
    cockpit = render_cockpit(matrix, queue)
    return {"matrix": matrix, "queue": queue, "playbook": playbook, "cockpit_md": cockpit}


def validate(outputs: dict[str, Any]) -> dict[str, Any]:
    matrix = outputs["matrix"]
    queue = outputs["queue"]
    failures: list[str] = []
    severities = {row["severity"] for row in matrix.get("severity_tiers", [])}
    for severity in ["P0", "P1", "P2", "P3", "P4"]:
        if severity not in severities:
            failures.append(f"missing_severity::{severity}")
    capability_ids = {row["capability_id"] for row in matrix.get("capability_directory", [])}
    for row in matrix.get("routing_rules", []):
        if row.get("owner_capability") not in capability_ids:
            failures.append(f"unknown_owner_capability::{row.get('signal_class')}::{row.get('owner_capability')}")
        if not row.get("closure_evidence_required"):
            failures.append(f"missing_closure_evidence::{row.get('signal_class')}")
        if not row.get("safe_executor_policy"):
            failures.append(f"missing_safe_executor_policy::{row.get('signal_class')}")
    if matrix.get("manual_repair_policy", {}).get("codex_direct_hand_fix_allowed") is not False:
        failures.append("manual_repair_not_forbidden")
    incident = next((row for row in queue.get("rows", []) if row.get("incident_id") == OC133_INCIDENT_ID), None)
    if not incident:
        failures.append(f"missing_current_incident::{OC133_INCIDENT_ID}")
    else:
        if incident.get("severity") != "P0":
            failures.append(f"current_incident_not_p0::{incident.get('severity')}")
        for capability in ["Publication/PublicRecords", "IT/ReleaseAutomation", "Research/ManuscriptIntegration", "Review/Cerberus"]:
            if capability not in incident.get("capability_owners", []):
                failures.append(f"current_incident_missing_capability::{capability}")
    return {
        "schema_id": "LOGION_ESCALATION_MATRIX_VALIDATION_v1",
        "state": "PASS" if not failures else "FAIL",
        "failure_total": len(failures),
        "failures": failures,
        "incident_total": queue.get("incident_total"),
        "p0_total": queue.get("p0_total"),
    }


def write_outputs(root: Path, outputs: dict[str, Any]) -> list[str]:
    changed = []
    if write_json_if_changed(root / MATRIX_REL, outputs["matrix"]):
        changed.append(MATRIX_REL)
    if write_json_if_changed(root / PLAYBOOK_REL, outputs["playbook"]):
        changed.append(PLAYBOOK_REL)
    if write_json_if_changed(root / QUEUE_REL, outputs["queue"]):
        changed.append(QUEUE_REL)
    if write_text_if_changed(root / COCKPIT_REL, outputs["cockpit_md"]):
        changed.append(COCKPIT_REL)
    return changed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Logion escalation matrix and incident control.")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    outputs = build_outputs(ROOT)
    validation = validate(outputs)
    if args.write:
        validation["changed"] = write_outputs(ROOT, outputs)
    if args.check:
        existing = {
            "matrix": read_json(ROOT / MATRIX_REL, {}),
            "playbook": read_json(ROOT / PLAYBOOK_REL, {}),
            "queue": read_json(ROOT / QUEUE_REL, {}),
            "cockpit_md": (ROOT / COCKPIT_REL).read_text(encoding="utf-8") if (ROOT / COCKPIT_REL).exists() else "",
        }
        stale = []
        for key in ["matrix", "playbook", "queue"]:
            if existing[key] != outputs[key]:
                stale.append(key)
        if existing["cockpit_md"] != outputs["cockpit_md"].rstrip() + "\n":
            stale.append("cockpit_md")
        validation["stale_output_total"] = len(stale)
        validation["stale_outputs"] = stale
        if stale:
            validation["state"] = "FAIL"
            validation["failure_total"] += len(stale)
    print(json.dumps(validation, ensure_ascii=False, indent=2))
    return 0 if validation["state"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
