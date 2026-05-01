from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SERVICE_ROOT = ROOT / "operations" / "logion_services"
REGISTRY = SERVICE_ROOT / "LOGION_SERVICE_REGISTRY.json"
CONTRACTS = SERVICE_ROOT / "LOGION_SERVICE_CONTRACTS.json"
ROUTER = SERVICE_ROOT / "LOGION_SERVICE_ROUTER.json"
COCKPIT = SERVICE_ROOT / "LOGION_SERVICE_COCKPIT.md"


def read_json(path: Path, default: Any | None = None) -> Any:
    if not path.exists():
        return {} if default is None else default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {} if default is None else default


def write_text_if_changed(path: Path, text: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = text.rstrip() + "\n"
    if path.exists() and path.read_text(encoding="utf-8", errors="ignore") == data:
        return False
    path.write_text(data, encoding="utf-8", newline="\n")
    return True


def write_json_if_changed(path: Path, payload: Any) -> bool:
    return write_text_if_changed(path, json.dumps(payload, ensure_ascii=False, indent=2))


def sha256_object(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def build_services() -> list[dict[str, Any]]:
    return [
        {
            "service_id": "strategy_hq",
            "name": "Strategy HQ / K6",
            "service_type": "command_and_portfolio_control",
            "authority": "LOGI -> K6 Strategy HQ",
            "mission": "Own portfolio priorities, resource policy, service activation, and cross-service arbitration.",
            "owns": ["portfolio state", "budget policy", "service priorities", "release critical path"],
            "does_not_own": ["scientific claim creation", "manuscript editing", "public upload execution"],
            "interfaces": {
                "inputs": ["owner directive", "service telemetry", "incident signals", "release gate state"],
                "outputs": ["portfolio directives", "resource budget", "service activation orders", "arbitration decisions"],
            },
            "primary_artifacts": [
                "operations/project_control/LOGION_PROJECT_COCKPIT.md",
                "operations/project_control/LOGION_PORTFOLIO_STATE.json",
            ],
        },
        {
            "service_id": "incident_management",
            "name": "Incident Management",
            "service_type": "signal_triage_root_cause_and_containment",
            "authority": "Strategy HQ / K6",
            "mission": "Classify incidents, freeze unsafe downstream actions, assign service-owned work orders, and record RCA/postmortem.",
            "owns": ["incident queue", "severity matrix", "containment state", "RCA", "postmortem"],
            "does_not_own": ["research repairs", "editorial generation", "release publication"],
            "interfaces": {
                "inputs": ["bad public record", "gate failure", "public-surface defect", "self-dirtying check"],
                "outputs": ["incident case", "service work orders", "containment directive", "closure predicates"],
            },
            "primary_artifacts": [
                "operations/incidents/",
                "operations/project_control/LOGION_ESCALATION_MATRIX.json",
                "operations/project_control/LOGION_INCIDENT_QUEUE.json",
            ],
        },
        {
            "service_id": "research_science",
            "name": "Research Science Contour",
            "service_type": "model_proof_data_and_prediction_work",
            "authority": "Institute Director / Research Director",
            "mission": "Develop OC model content, theorem obligations, proof/data artifacts, prediction lanes, novelty comparisons, and claim boundaries.",
            "owns": ["model sources", "claim ledger", "proof ledger", "Lean sources", "finite semantics", "validation lanes"],
            "does_not_own": ["public release metadata", "Zenodo/GitHub publication", "incident severity"],
            "interfaces": {
                "inputs": ["research mission", "review findings", "claim gaps", "empirical protocol gaps"],
                "outputs": ["science artifacts", "claim/evidence mappings", "promotion/demotion evidence", "research blockers"],
            },
            "primary_artifacts": ["<product>/claims/", "<product>/proofs/", "<product>/formal/", "<product>/validation/", "<product>/reports/"],
        },
        {
            "service_id": "editorial_manuscript",
            "name": "Editorial Manuscript Integration",
            "service_type": "science_to_document_projection",
            "authority": "Publication Director + Research Director",
            "mission": "Project approved science into monographs, articles, guides, response maps, and journal-owner-review packets.",
            "owns": ["corpus ledger", "source-to-PDF trace", "manuscript structure", "title/frontmatter/dedication", "reading order"],
            "does_not_own": ["scientific truth claims", "public upload execution", "incident management"],
            "interfaces": {
                "inputs": ["science corpus", "claim ledger", "proof/evidence refs", "review boundaries"],
                "outputs": ["monograph", "article", "methods companion", "reviewer map", "journal package drafts"],
            },
            "primary_artifacts": [
                "<product>/editorial/corpus_ledger.json",
                "<product>/artifacts/master_monograph.pdf",
                "<product>/submission_packages/",
            ],
        },
        {
            "service_id": "verification_review",
            "name": "Verification and Review",
            "service_type": "gates_audits_cerberus_and_owner_review",
            "authority": "Review Director",
            "mission": "Run deterministic checks, Cerberus roles, evidence audits, owner-review audits, and closure verification.",
            "owns": ["gate verdicts", "review findings", "audit reports", "closure-evidence validation"],
            "does_not_own": ["artifact repair implementation", "research content creation", "publication execution"],
            "interfaces": {
                "inputs": ["candidate artifacts", "work-order closure evidence", "release package"],
                "outputs": ["PASS/FAIL/BLOCKED verdicts", "findings", "reopened work orders", "owner-review verdict"],
            },
            "primary_artifacts": ["<product>/reviews/", "<product>/editorial/*AUDIT*.json", "<product>/editorial/*SCORECARD*.json"],
        },
        {
            "service_id": "release_engineering",
            "name": "Release Engineering",
            "service_type": "artifact_packaging_versioning_and_space_migration",
            "authority": "IT Department Director",
            "mission": "Build deterministic package outputs, manage release versioning, enforce development/verification/release space boundaries, and keep checks delta-stable.",
            "owns": ["release machine", "public payload builder", "release-space migration", "Delta Queue", "reproducibility"],
            "does_not_own": ["scientific claim ambition", "journal submission decision", "incident severity"],
            "interfaces": {
                "inputs": ["verified science corpus", "editorial outputs", "publication approval contract"],
                "outputs": ["public payload", "checksums", "metadata", "release package", "space-boundary audit"],
            },
            "primary_artifacts": ["release_machine/", "tools/*release_payload*.py", "tools/*release_spaces*.py"],
        },
        {
            "service_id": "publication_records",
            "name": "Publication Records",
            "service_type": "github_zenodo_public_record_execution",
            "authority": "Publication Director",
            "mission": "Execute GitHub and Zenodo publication/replacement only after approval, exact file set, and postflight gates.",
            "owns": ["GitHub Release body/assets", "Zenodo metadata/files", "DOI record", "post-release report"],
            "does_not_own": ["journal submissions", "scientific content editing", "release artifact generation"],
            "interfaces": {
                "inputs": ["public payload", "approval contract", "tokens", "postflight expectations"],
                "outputs": ["public URLs", "DOI", "publication execution report", "postflight verification"],
            },
            "primary_artifacts": ["<product>/editorial/public_release_execution_report.json"],
        },
        {
            "service_id": "safety_governance",
            "name": "Safety and Governance",
            "service_type": "scope_locks_secret_scans_and_policy",
            "authority": "Safety Directive / LOGI",
            "mission": "Enforce approval scope, secret/local-path scans, journal/SWH/email locks, and private/public boundaries.",
            "owns": ["approval contracts", "secret scan policy", "scope locks", "private/public separation"],
            "does_not_own": ["scientific content", "editorial quality", "public upload mechanics"],
            "interfaces": {
                "inputs": ["publication request", "artifact set", "scope change"],
                "outputs": ["allow/block decision", "scope contract", "policy findings"],
            },
            "primary_artifacts": [
                "<product>/editorial/owner_release_approval.json",
                "<product>/editorial/publish_manifest.json",
            ],
        },
    ]


def build_router() -> dict[str, Any]:
    routes = [
        {
            "signal": "bad_public_release_record",
            "primary_service": "incident_management",
            "downstream_services": ["release_engineering", "editorial_manuscript", "verification_review", "publication_records"],
            "rule": "Incident service opens RCA and assigns work orders; each downstream service repairs only its own owned class.",
        },
        {
            "signal": "science_content_gap",
            "primary_service": "research_science",
            "downstream_services": ["verification_review", "editorial_manuscript"],
            "rule": "Research creates or blocks evidence; editorial may only project verified science into documents.",
        },
        {
            "signal": "manuscript_projection_gap",
            "primary_service": "editorial_manuscript",
            "downstream_services": ["research_science", "verification_review", "release_engineering"],
            "rule": "Editorial rebuilds document structure and traceability; research supplies missing science, release engineering packages it.",
        },
        {
            "signal": "public_payload_or_metadata_gap",
            "primary_service": "release_engineering",
            "downstream_services": ["editorial_manuscript", "safety_governance", "verification_review"],
            "rule": "Release engineering fixes package/version/space migration machinery; it must not rewrite scientific claims.",
        },
        {
            "signal": "github_zenodo_execution_gap",
            "primary_service": "publication_records",
            "downstream_services": ["release_engineering", "safety_governance", "verification_review"],
            "rule": "Publication records executes or repairs public records after approved artifacts pass gates.",
        },
        {
            "signal": "approval_scope_or_secret_gap",
            "primary_service": "safety_governance",
            "downstream_services": ["release_engineering", "publication_records"],
            "rule": "Safety blocks scope leaks and token/path leaks; publication waits for clearance.",
        },
    ]
    return {
        "schema_id": "LOGION_SERVICE_ROUTER_v1",
        "routing_principle": "Signals route between independent services; no service is embedded as a private subroutine of another.",
        "routes": routes,
        "router_hash": sha256_object(routes),
    }


def build_contracts(services: list[dict[str, Any]], router: dict[str, Any]) -> dict[str, Any]:
    service_ids = {service["service_id"] for service in services}
    contracts = []
    for route in router["routes"]:
        contracts.append(
            {
                "contract_id": f"{route['signal']}__service_route",
                "signal": route["signal"],
                "primary_service": route["primary_service"],
                "downstream_services": route["downstream_services"],
                "preconditions": [
                    f"primary_service in registry: {route['primary_service'] in service_ids}",
                    "work order must name artifact refs, expected predicate, verification command, and rollback/block rule",
                ],
                "postconditions": [
                    "closure evidence is validated by verification_review",
                    "service boundaries remain intact",
                    "no direct Codex hand-patch is accepted as service closure",
                ],
            }
        )
    return {
        "schema_id": "LOGION_SERVICE_CONTRACTS_v1",
        "contracts": contracts,
        "contract_hash": sha256_object(contracts),
    }


def build_registry() -> dict[str, Any]:
    services = build_services()
    router = build_router()
    contracts = build_contracts(services, router)
    registry = {
        "schema_id": "LOGION_SERVICE_REGISTRY_v1",
        "authority_chain": ["Safety Directive", "LOGI", "K6 Strategy HQ", "Service Directors", "Managers", "Executors"],
        "architecture_principle": "Logion is a service organization: incident, research, editorial, verification, release, publication, and governance are independent services connected by contracts.",
        "services": services,
        "service_total": len(services),
        "router_ref": rel(ROUTER),
        "contracts_ref": rel(CONTRACTS),
    }
    registry["registry_hash"] = sha256_object({key: value for key, value in registry.items() if key != "registry_hash"})
    return {"registry": registry, "router": router, "contracts": contracts}


def validate(outputs: dict[str, Any]) -> dict[str, Any]:
    registry = outputs["registry"]
    router = outputs["router"]
    services = registry["services"]
    service_ids = {service["service_id"] for service in services}
    failures: list[str] = []
    required = {
        "strategy_hq",
        "incident_management",
        "research_science",
        "editorial_manuscript",
        "verification_review",
        "release_engineering",
        "publication_records",
        "safety_governance",
    }
    for service_id in sorted(required - service_ids):
        failures.append(f"missing_service::{service_id}")
    for service in services:
        if not service.get("does_not_own"):
            failures.append(f"missing_negative_boundary::{service['service_id']}")
        if not service.get("interfaces", {}).get("inputs") or not service.get("interfaces", {}).get("outputs"):
            failures.append(f"missing_interface::{service['service_id']}")
    for route in router["routes"]:
        if route["primary_service"] not in service_ids:
            failures.append(f"route_unknown_primary::{route['signal']}::{route['primary_service']}")
        for downstream in route.get("downstream_services", []):
            if downstream not in service_ids:
                failures.append(f"route_unknown_downstream::{route['signal']}::{downstream}")
    if "incident_management" not in service_ids or "editorial_manuscript" not in service_ids:
        failures.append("incident_and_editorial_not_separate")
    return {
        "schema_id": "LOGION_SERVICE_ARCHITECTURE_VALIDATION_v1",
        "state": "PASS" if not failures else "FAIL",
        "failure_total": len(failures),
        "failures": failures,
        "service_total": len(services),
        "route_total": len(router["routes"]),
    }


def write_outputs(outputs: dict[str, Any]) -> list[str]:
    changed = []
    if write_json_if_changed(REGISTRY, outputs["registry"]):
        changed.append(rel(REGISTRY))
    if write_json_if_changed(CONTRACTS, outputs["contracts"]):
        changed.append(rel(CONTRACTS))
    if write_json_if_changed(ROUTER, outputs["router"]):
        changed.append(rel(ROUTER))
    cockpit = render_cockpit(outputs)
    if write_text_if_changed(COCKPIT, cockpit):
        changed.append(rel(COCKPIT))
    return changed


def render_cockpit(outputs: dict[str, Any]) -> str:
    registry = outputs["registry"]
    router = outputs["router"]
    lines = [
        "# Logion Service Cockpit",
        "",
        f"- service total: `{registry['service_total']}`",
        f"- route total: `{len(router['routes'])}`",
        f"- registry hash: `{registry['registry_hash']}`",
        f"- router hash: `{router['router_hash']}`",
        "",
        "## Services",
        "",
    ]
    for service in registry["services"]:
        lines.append(f"- `{service['service_id']}`: {service['mission']}")
    lines.extend(["", "## Routes", ""])
    for route in router["routes"]:
        downstream = ", ".join(route["downstream_services"])
        lines.append(f"- `{route['signal']}` -> `{route['primary_service']}`; downstream: {downstream}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build and validate Logion's independent service architecture.")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    outputs = build_registry()
    validation = validate(outputs)
    if args.write:
        validation["changed"] = write_outputs(outputs)
    if args.check:
        existing = {
            "registry": read_json(REGISTRY, {}),
            "contracts": read_json(CONTRACTS, {}),
            "router": read_json(ROUTER, {}),
            "cockpit": COCKPIT.read_text(encoding="utf-8") if COCKPIT.exists() else "",
        }
        stale = []
        for key in ["registry", "contracts", "router"]:
            if existing[key] != outputs[key]:
                stale.append(key)
        if existing["cockpit"] != render_cockpit(outputs).rstrip() + "\n":
            stale.append("cockpit")
        validation["stale_output_total"] = len(stale)
        validation["stale_outputs"] = stale
        if stale:
            validation["state"] = "FAIL"
            validation["failure_total"] += len(stale)
    print(json.dumps(validation, ensure_ascii=False, indent=2))
    return 0 if validation["state"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
