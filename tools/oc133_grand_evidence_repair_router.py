from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import oc133_empirical_capability_registry as capability_registry  # noqa: E402
from tools import oc133_grand_evidence_registry_sync_factory as registry_sync  # noqa: E402


SCHEMA_ID = "OC133_GRAND_EVIDENCE_REPAIR_ROUTER_v1"
RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
CAPABILITY_OWNER = "Logion IT/Research"
REPORT_JSON_REL = "reports/OC_CORE_1_3_3_GRAND_EVIDENCE_REPAIR_ROUTER.json"
REPORT_MD_REL = "reports/OC_CORE_1_3_3_GRAND_EVIDENCE_REPAIR_ROUTER.md"

NO_SEND_LOCKS = {
    "no_send": True,
    "publish_allowed": False,
    "journal_submissions_allowed": False,
    "external_network_allowed": False,
    "owner_approval_required": True,
}

ROUTE_HINTS = {
    ("biology", "insufficient_sample_size"): ("tools/oc133_biology_ncbi_batch_factory.py", "Expand or acquire NCBI/GEO batch evidence."),
    ("biology", "source_separation_failure"): ("tools/oc133_biology_ncbi_batch_factory.py", "Regenerate NCBI/GEO target-hidden source-lock material."),
    ("biology", "grand_support_not_authorized"): ("tools/oc133_biology_ncbi_batch_factory.py", "Keep biology blocked until strict grand evidence passes."),
    ("chemistry", "insufficient_sample_size"): ("tools/oc133_chemistry_pubchem_formula_batch_factory.py", "Acquire or consume more PubChem formula snapshots."),
    ("chemistry", "source_separation_failure"): ("tools/oc133_chemistry_pubchem_formula_batch_factory.py", "Generate target-hidden PubChem acquisition protocol."),
    ("chemistry", "grand_support_not_authorized"): ("tools/oc133_chemistry_pubchem_formula_batch_factory.py", "Keep chemistry blocked until strict grand evidence passes."),
    ("physics", "source_separation_failure"): ("tools/oc133_physics_chemistry_official_batch_factory.py", "Separate CODATA formula inputs and target quantities."),
    ("physics", "grand_support_not_authorized"): ("tools/oc133_physics_chemistry_official_batch_factory.py", "Keep physics blocked until official batch criteria pass."),
    ("systems", "negative_control_failure"): ("tools/oc133_systems_wdi_predictive_search_v2_factory.py", "Run stricter WDI predictive search and keep failing rows open."),
    ("systems", "comparator_or_residual_failure"): ("tools/oc133_systems_wdi_predictive_search_v2_factory.py", "Re-score WDI predictors against comparator baselines."),
    ("systems", "grand_support_not_authorized"): ("tools/oc133_systems_wdi_predictive_search_v2_factory.py", "Keep systems blocked until all strict controls pass."),
    ("mathematics", "insufficient_sample_size"): ("validation/heldout/domain_evidence/mathematics_evidence_executor.py", "Do not convert proof-corpus QA into empirical grand support."),
    ("mathematics", "grand_support_not_authorized"): ("validation/heldout/domain_evidence/mathematics_evidence_executor.py", "Keep mathematics empirical grand support blocked without a valid empirical protocol."),
}

CLASS_FALLBACKS = {
    "source_separation_failure": "tools/oc133_official_readonly_acquisition_runner.py",
    "insufficient_sample_size": "tools/oc133_official_readonly_acquisition_runner.py",
    "schema_or_identity_failure": "tools/oc133_grand_evidence_registry_sync_factory.py",
    "negative_control_failure": "tools/oc133_grand_empirical_evidence_factory.py",
    "comparator_or_residual_failure": "tools/oc133_grand_empirical_evidence_factory.py",
    "falsifier_failure": "tools/oc133_grand_empirical_evidence_factory.py",
    "grand_support_not_authorized": "tools/oc133_grand_empirical_evidence_factory.py",
}


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


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def canonical_sha256(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def component_map(registry_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = registry_payload.get("components", [])
    if not isinstance(rows, list):
        return {}
    return {str(row.get("component_ref")): row for row in rows if isinstance(row, dict) and row.get("component_ref")}


def preferred_component(domain: str, failure_class: str) -> tuple[str, str]:
    if (domain, failure_class) in ROUTE_HINTS:
        return ROUTE_HINTS[(domain, failure_class)]
    return (
        CLASS_FALLBACKS.get(failure_class, "tools/oc133_grand_empirical_evidence_factory.py"),
        "Route to the generic grand empirical capability until a class-specific capability exists.",
    )


def route_work_order(row: dict[str, Any], components: dict[str, dict[str, Any]]) -> dict[str, Any]:
    domain = str(row.get("domain") or "unknown")
    failure_class = str(row.get("failure_class") or "unclassified_evidence_failure")
    ref, action = preferred_component(domain, failure_class)
    component = components.get(ref, {})
    available = bool(component)
    return {
        "route_id": f"ROUTE::{row.get('work_order_id')}",
        "work_order_id": row.get("work_order_id"),
        "domain": domain,
        "failure_class": failure_class,
        "owner_capability": row.get("owner_capability"),
        "preferred_component_ref": ref,
        "preferred_component_available": available,
        "preferred_component_command": component.get("command") if available else None,
        "route_status": "ROUTED_TO_AVAILABLE_CAPABILITY" if available else "BLOCKED_CAPABILITY_MISSING",
        "repair_action": action,
        "candidate_refs": row.get("candidate_refs", []),
        "failure_examples": row.get("failure_examples", []),
        "closure_evidence_required": row.get("closure_evidence_required", []),
        "artifact_exists_is_not_closure": True,
        **NO_SEND_LOCKS,
    }


def build_payload(root: Path, *, write: bool = False) -> dict[str, Any]:
    work_orders = read_json(root / registry_sync.WORK_ORDERS_REL)
    registry_payload = capability_registry.build_payload(root, write=False)
    components = component_map(registry_payload)
    work_order_rows = [row for row in work_orders.get("rows", []) if isinstance(row, dict)]
    route_rows = [route_work_order(row, components) for row in work_order_rows]
    missing = [row for row in route_rows if row["preferred_component_available"] is not True]
    payload = {
        "schema_id": SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": utc_now(),
        "capability_owner": CAPABILITY_OWNER,
        "work_orders_ref": registry_sync.WORK_ORDERS_REL,
        "capability_registry_ref": capability_registry.REPORT_JSON_REL,
        "work_order_total": len(work_order_rows),
        "routed_work_order_total": len(route_rows),
        "missing_capability_total": len(missing),
        "missing_capability_refs": sorted({row["preferred_component_ref"] for row in missing}),
        "route_queue_sha256": canonical_sha256(route_rows),
        "rows": route_rows,
        "no_send_locks": dict(NO_SEND_LOCKS),
        **NO_SEND_LOCKS,
        "verdict": "REPAIR_ROUTE_READY" if not missing else "REPAIR_ROUTE_BLOCKED_CAPABILITIES_MISSING",
        "closure_policy": "Routing does not close evidence blockers. A routed work order closes only after the preferred capability emits a strict valid evidence pack and the grand empirical gate re-audits it as valid.",
    }
    if write:
        write_json(root / REPORT_JSON_REL, payload)
        write_markdown(root / REPORT_MD_REL, payload)
    return payload


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# OC Core 1.3.3 Grand Evidence Repair Router",
        "",
        f"Verdict: `{payload['verdict']}`",
        f"Work orders: `{payload['work_order_total']}`",
        f"Missing capabilities: `{payload['missing_capability_total']}`",
        f"No-send: `{payload['no_send']}`",
        "",
        payload["closure_policy"],
        "",
        "| Work Order | Domain | Failure Class | Component | Status |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in payload["rows"]:
        lines.append(f"| `{row['work_order_id']}` | `{row['domain']}` | `{row['failure_class']}` | `{row['preferred_component_ref']}` | `{row['route_status']}` |")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Route strict grand evidence repair work orders to Logion capabilities.")
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    payload = build_payload(Path(args.root).resolve(), write=args.write)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
