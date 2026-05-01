from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ARCH_ROOT = ROOT / "operations" / "logion_architecture"
TAXONOMY = ARCH_ROOT / "LOGION_LAYER_TAXONOMY.json"
FUNCTIONS = ARCH_ROOT / "LOGION_FUNCTION_REGISTRY.json"
PRODUCTION_LINES = ARCH_ROOT / "LOGION_PRODUCTION_LINES.json"
PRODUCTS = ARCH_ROOT / "LOGION_PRODUCT_OUTCOME_LEDGER.json"
ROUTING = ARCH_ROOT / "LOGION_FUNCTION_PRODUCT_ROUTING.json"
AUDIT = ARCH_ROOT / "LOGION_FUNCTION_PRODUCT_SEPARATION_AUDIT.json"
COCKPIT = ARCH_ROOT / "LOGION_FUNCTION_PRODUCT_COCKPIT.md"

PRODUCT_TOKEN_RE = re.compile(
    r"\bOC133\b|oc_core_1_3_3|OC_CORE_1_3_3|v1\.3\.3|version\s+1\.3\.3|zenodo\.199|19957779",
    re.IGNORECASE,
)


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


def build_taxonomy() -> dict[str, Any]:
    layers = [
        {
            "layer_id": "control_layer",
            "definition": "Direction, priority, budget, arbitration, and safety policy.",
            "examples": ["Strategy HQ/K6", "portfolio controller", "budget ledger", "approval authority"],
            "must_not_contain": ["product-specific scientific claims", "manuscript body"],
        },
        {
            "layer_id": "function_layer",
            "definition": "Stable organizational capabilities that can act on many products.",
            "examples": ["research science", "editorial integration", "verification review", "release engineering", "publication records"],
            "must_not_contain": ["version-specific DOI", "single-release artifact inventory as service definition"],
        },
        {
            "layer_id": "production_line_layer",
            "definition": "Reusable flow that turns inputs into a class of outcomes.",
            "examples": ["scientific release line", "journal package line", "product/tool release line"],
            "must_not_contain": ["one-off incident RCA", "single product as the line definition"],
        },
        {
            "layer_id": "repair_line_layer",
            "definition": "Reusable line for defect containment, root-cause analysis, class repair, regression gates, and postmortem.",
            "examples": ["incident management", "self-repair work-order loop", "postflight correction"],
            "must_not_contain": ["normal editorial work disguised as incident work"],
        },
        {
            "layer_id": "methodology_layer",
            "definition": "Standards and protocols used by functions and lines.",
            "examples": ["Delta Queue", "source-to-PDF trace", "target-blind replay protocol", "public payload suitability gate"],
            "must_not_contain": ["specific release payload as a standard"],
        },
        {
            "layer_id": "machine_layer",
            "definition": "Executable stations, scripts, release-machine modules, local tools, and LLM bridges.",
            "examples": ["release_machine", "materializers", "auditors", "Cerberus runner"],
            "must_not_contain": ["authority decisions", "scientific truth claims"],
        },
        {
            "layer_id": "product_layer",
            "definition": "Concrete outcomes: a release, article package, dataset, product build, or public record.",
            "examples": ["OC Core 1.3.3", "Zenodo record", "GitHub release", "journal package set"],
            "must_not_contain": ["definition of the organization function itself"],
        },
    ]
    payload = {
        "schema_id": "LOGION_LAYER_TAXONOMY_v1",
        "principle": "Function is the capacity to produce; product is the concrete produced outcome. Lines and machines connect them without merging them.",
        "layers": layers,
    }
    payload["taxonomy_hash"] = sha256_object(payload)
    return payload


def build_functions() -> dict[str, Any]:
    rows = [
        ("strategy_control", "control_layer", "Set priorities, budgets, locks, and cross-service arbitration."),
        ("research_science", "function_layer", "Produce model, proof, data, evidence, comparator, and claim-boundary work."),
        ("editorial_manuscript", "function_layer", "Project approved science into readable, traceable manuscripts and journal packages."),
        ("verification_review", "function_layer", "Run deterministic gates, Cerberus reviews, owner reviews, and closure audits."),
        ("release_engineering", "function_layer", "Package artifacts, version outputs, enforce spaces, and keep checks reproducible."),
        ("publication_records", "function_layer", "Operate GitHub/Zenodo/public-record execution and postflight verification."),
        ("incident_management", "repair_line_layer", "Classify signals, contain damage, assign service-owned repair, and close RCA."),
        ("safety_governance", "control_layer", "Enforce approval scope, secret/local-path scans, and public/private boundaries."),
        ("delta_queue", "methodology_layer", "Trigger downstream work only on meaningful semantic deltas."),
    ]
    functions = [
        {
            "function_id": function_id,
            "layer_id": layer_id,
            "mission": mission,
            "product_agnostic": True,
            "output_class": "capability_service_output",
            "quantitative_metrics": [
                "input_signal_count",
                "work_order_count",
                "closure_evidence_count",
                "failure_total",
                "mean_runtime_seconds",
                "semantic_delta_count",
            ],
        }
        for function_id, layer_id, mission in rows
    ]
    payload = {
        "schema_id": "LOGION_FUNCTION_REGISTRY_v1",
        "functions": functions,
        "function_total": len(functions),
    }
    payload["function_registry_hash"] = sha256_object(payload)
    return payload


def build_production_lines() -> dict[str, Any]:
    lines = [
        {
            "line_id": "scientific_release_line",
            "layer_id": "production_line_layer",
            "purpose": "Turn a verified science corpus into release-ready public scientific artifacts and records.",
            "ordered_functions": [
                "research_science",
                "editorial_manuscript",
                "verification_review",
                "release_engineering",
                "safety_governance",
                "publication_records",
            ],
            "quality_metrics": [
                "claim_evidence_coverage_ratio",
                "source_to_pdf_trace_coverage_ratio",
                "public_surface_contamination_total",
                "substantive_pdf_count",
                "postflight_failure_total",
            ],
        },
        {
            "line_id": "journal_package_line",
            "layer_id": "production_line_layer",
            "purpose": "Turn a release corpus into venue-specific owner-review journal packages.",
            "ordered_functions": ["editorial_manuscript", "verification_review", "safety_governance"],
            "quality_metrics": ["venue_package_total", "component_problem_total", "unsupported_claim_total"],
        },
        {
            "line_id": "incident_repair_line",
            "layer_id": "repair_line_layer",
            "purpose": "Turn a defect signal into containment, RCA, class-level repair, regression gates, and postmortem.",
            "ordered_functions": ["incident_management", "strategy_control", "release_engineering", "verification_review"],
            "quality_metrics": ["severity", "containment_time_seconds", "root_cause_total", "regression_gate_total", "reopen_count"],
        },
        {
            "line_id": "background_science_line",
            "layer_id": "production_line_layer",
            "purpose": "Run continuous research lanes without mutating release products until promotion gates pass.",
            "ordered_functions": ["research_science", "verification_review", "delta_queue"],
            "quality_metrics": ["lane_count", "evidence_pack_count", "promotion_gate_pass_count", "budget_used_tokens"],
        },
    ]
    payload = {
        "schema_id": "LOGION_PRODUCTION_LINES_v1",
        "production_lines": lines,
        "production_line_total": len(lines),
    }
    payload["production_line_hash"] = sha256_object(payload)
    return payload


def build_products() -> dict[str, Any]:
    products = [
        {
            "product_id": "OC_CORE_1_3_3_PUBLIC_RELEASE_REPLACEMENT",
            "product_family": "OC Core",
            "version": "1.3.3",
            "layer_id": "product_layer",
            "production_line_id": "scientific_release_line",
            "current_problem_signal": "bad_public_release_record",
            "outcome_refs": [
                "releases/oc_core_1_3_3/artifacts/OC_CORE_1_3_3_MASTER_MONOGRAPH_EN.pdf",
                "releases/oc_core_1_3_3/artifacts/oc_core_1_3_3_public_release.zip",
                "manifest.json",
                ".zenodo.json",
            ],
            "required_function_outputs": [
                "research_science:evidence-bound science corpus",
                "editorial_manuscript:science monolith and source-to-PDF trace",
                "verification_review:public payload, PDF, Cerberus, and owner-review gates",
                "release_engineering:public payload and release-space audit",
                "publication_records:GitHub/Zenodo replacement and postflight",
            ],
            "status": "IN_REPAIR_UNTIL_PUBLIC_RECORDS_REPLACED",
        }
    ]
    payload = {
        "schema_id": "LOGION_PRODUCT_OUTCOME_LEDGER_v1",
        "products": products,
        "product_total": len(products),
    }
    payload["product_ledger_hash"] = sha256_object(payload)
    return payload


def build_routing(functions: dict[str, Any], lines: dict[str, Any], products: dict[str, Any]) -> dict[str, Any]:
    function_ids = {row["function_id"] for row in functions["functions"]}
    line_by_id = {row["line_id"]: row for row in lines["production_lines"]}
    rows = []
    for product in products["products"]:
        line = line_by_id.get(product["production_line_id"], {})
        missing_functions = [function_id for function_id in line.get("ordered_functions", []) if function_id not in function_ids]
        rows.append(
            {
                "product_id": product["product_id"],
                "production_line_id": product["production_line_id"],
                "function_route": line.get("ordered_functions", []),
                "missing_function_total": len(missing_functions),
                "missing_functions": missing_functions,
                "next_function": "publication_records"
                if product.get("status") == "IN_REPAIR_UNTIL_PUBLIC_RECORDS_REPLACED"
                else (line.get("ordered_functions") or [None])[0],
            }
        )
    payload = {
        "schema_id": "LOGION_FUNCTION_PRODUCT_ROUTING_v1",
        "routing_rows": rows,
        "routing_row_total": len(rows),
    }
    payload["routing_hash"] = sha256_object(payload)
    return payload


def product_token_hits(payload: Any, *, allow_product_layer: bool = False) -> list[dict[str, Any]]:
    hits = []
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    for match in PRODUCT_TOKEN_RE.finditer(text):
        hits.append({"match": match.group(0), "offset": match.start()})
    return [] if allow_product_layer else hits


def build_outputs() -> dict[str, Any]:
    taxonomy = build_taxonomy()
    functions = build_functions()
    lines = build_production_lines()
    products = build_products()
    routing = build_routing(functions, lines, products)
    return {
        "taxonomy": taxonomy,
        "functions": functions,
        "production_lines": lines,
        "products": products,
        "routing": routing,
    }


def validate(outputs: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    functions = outputs["functions"]
    lines = outputs["production_lines"]
    products = outputs["products"]
    routing = outputs["routing"]
    function_ids = {row["function_id"] for row in functions["functions"]}
    layer_ids = {row["layer_id"] for row in outputs["taxonomy"]["layers"]}
    for required in [
        "control_layer",
        "function_layer",
        "production_line_layer",
        "repair_line_layer",
        "methodology_layer",
        "machine_layer",
        "product_layer",
    ]:
        if required not in layer_ids:
            failures.append(f"missing_layer::{required}")
    function_product_hits = product_token_hits(functions)
    line_product_hits = product_token_hits(lines)
    if function_product_hits:
        failures.append("function_registry_contains_product_tokens")
    if line_product_hits:
        failures.append("production_line_registry_contains_product_tokens")
    for line in lines["production_lines"]:
        for function_id in line.get("ordered_functions", []):
            if function_id not in function_ids:
                failures.append(f"line_unknown_function::{line['line_id']}::{function_id}")
    for row in routing["routing_rows"]:
        if row["missing_function_total"]:
            failures.append(f"product_route_missing_function::{row['product_id']}")
    release_space_audit = read_json(ROOT / "operations" / "project_control" / "LOGION_RELEASE_SPACE_AUDIT.json", {})
    public_payload_audit = read_json(ROOT / "releases" / "oc_core_1_3_3" / "editorial" / "PUBLIC_PAYLOAD_SUITABILITY_1.3.3_latest.json", {})
    if release_space_audit.get("state") != "PASS":
        failures.append("release_space_audit_not_pass")
    if public_payload_audit.get("state") != "PASS":
        failures.append("public_payload_suitability_not_pass")
    quantitative_metrics = {
        "layer_total": len(outputs["taxonomy"]["layers"]),
        "function_total": functions["function_total"],
        "production_line_total": lines["production_line_total"],
        "product_total": products["product_total"],
        "function_registry_product_token_hit_total": len(function_product_hits),
        "production_line_product_token_hit_total": len(line_product_hits),
        "routing_missing_function_total": sum(row["missing_function_total"] for row in routing["routing_rows"]),
        "release_space_failure_total": int(release_space_audit.get("failure_total", 999)),
        "release_space_control_language_hit_total": int(release_space_audit.get("control_language_hit_total", 999)),
        "public_payload_failure_total": int(public_payload_audit.get("failure_total", 999)),
    }
    return {
        "schema_id": "LOGION_FUNCTION_PRODUCT_SEPARATION_AUDIT_v1",
        "state": "PASS" if not failures else "FAIL",
        "failure_total": len(failures),
        "failures": failures,
        "quantitative_metrics": quantitative_metrics,
        "behavior_prevention": {
            "bad_release_from_verification_artifacts_prevented_by": [
                "function registry cannot contain product tokens",
                "release space audit must pass before public record execution",
                "public payload suitability must pass before publication",
                "product outcome ledger is separate from stable functions",
            ],
            "pattern_scope": "entire Logion release behavior, not only OC Core 1.3.3",
        },
    }


def write_outputs(outputs: dict[str, Any], audit: dict[str, Any]) -> list[str]:
    changed = []
    for path, payload in [
        (TAXONOMY, outputs["taxonomy"]),
        (FUNCTIONS, outputs["functions"]),
        (PRODUCTION_LINES, outputs["production_lines"]),
        (PRODUCTS, outputs["products"]),
        (ROUTING, outputs["routing"]),
        (AUDIT, audit),
    ]:
        if write_json_if_changed(path, payload):
            changed.append(rel(path))
    if write_text_if_changed(COCKPIT, render_cockpit(outputs, audit)):
        changed.append(rel(COCKPIT))
    return changed


def render_cockpit(outputs: dict[str, Any], audit: dict[str, Any]) -> str:
    metrics = audit["quantitative_metrics"]
    lines = [
        "# Logion Function/Product Separation Cockpit",
        "",
        f"- state: `{audit['state']}`",
        f"- failures: `{audit['failure_total']}`",
        f"- layers: `{metrics['layer_total']}`",
        f"- functions: `{metrics['function_total']}`",
        f"- production lines: `{metrics['production_line_total']}`",
        f"- products: `{metrics['product_total']}`",
        f"- function product-token hits: `{metrics['function_registry_product_token_hit_total']}`",
        f"- line product-token hits: `{metrics['production_line_product_token_hit_total']}`",
        f"- release-space control hits: `{metrics['release_space_control_language_hit_total']}`",
        "",
        "## Functions",
        "",
    ]
    for row in outputs["functions"]["functions"]:
        lines.append(f"- `{row['function_id']}` layer=`{row['layer_id']}`")
    lines.extend(["", "## Products", ""])
    for row in outputs["products"]["products"]:
        lines.append(f"- `{row['product_id']}` line=`{row['production_line_id']}` status=`{row['status']}`")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Separate Logion functions, lines, machines, methods, and products.")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    outputs = build_outputs()
    audit = validate(outputs)
    if args.write:
        audit["changed"] = write_outputs(outputs, audit)
    if args.check:
        existing = {
            "taxonomy": read_json(TAXONOMY, {}),
            "functions": read_json(FUNCTIONS, {}),
            "production_lines": read_json(PRODUCTION_LINES, {}),
            "products": read_json(PRODUCTS, {}),
            "routing": read_json(ROUTING, {}),
            "audit": read_json(AUDIT, {}),
            "cockpit": COCKPIT.read_text(encoding="utf-8") if COCKPIT.exists() else "",
        }
        stale = []
        if existing["taxonomy"] != outputs["taxonomy"]:
            stale.append("taxonomy")
        if existing["functions"] != outputs["functions"]:
            stale.append("functions")
        if existing["production_lines"] != outputs["production_lines"]:
            stale.append("production_lines")
        if existing["products"] != outputs["products"]:
            stale.append("products")
        if existing["routing"] != outputs["routing"]:
            stale.append("routing")
        expected_audit = dict(audit)
        if "changed" in expected_audit:
            expected_audit.pop("changed")
        existing_audit = dict(existing["audit"])
        existing_audit.pop("changed", None)
        if existing_audit != expected_audit:
            stale.append("audit")
        if existing["cockpit"] != render_cockpit(outputs, audit).rstrip() + "\n":
            stale.append("cockpit")
        audit["stale_output_total"] = len(stale)
        audit["stale_outputs"] = stale
        if stale:
            audit["state"] = "FAIL"
            audit["failure_total"] += len(stale)
    print(json.dumps(audit, ensure_ascii=False, indent=2))
    return 0 if audit["state"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
