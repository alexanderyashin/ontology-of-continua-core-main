from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "public_science" / "canonical"
SCRIPT_REL = "tools/build_canonical_scientific_graph.py"
SOURCE_EDITION = "OC Core 1.3.3"
TEXT_HASH_SUFFIXES = {".json", ".lean", ".md", ".py", ".tex", ".txt"}

MANIFEST_REL = "public_science/canonical/CANONICAL_SCIENTIFIC_GRAPH_MANIFEST.json"
THEOREM_GRAPH_REL = "public_science/canonical/THEOREM_GRAPH.json"
PROOF_GRAPH_REL = "public_science/canonical/PROOF_GRAPH.json"
EVIDENCE_GRAPH_REL = "public_science/canonical/EVIDENCE_GRAPH.json"
README_REL = "public_science/canonical/README.md"
GLOSSARY_JSON_REL = "public_science/canonical/CANONICAL_SCIENTIFIC_GRAPH_GLOSSARY.json"
GLOSSARY_MD_REL = "public_science/canonical/CANONICAL_SCIENTIFIC_GRAPH_GLOSSARY.md"
MAPPING_JSON_REL = "public_science/canonical/INTERNAL_TO_PUBLIC_GRAPH_MAPPING.json"
MAPPING_MD_REL = "public_science/canonical/INTERNAL_TO_PUBLIC_GRAPH_MAPPING.md"

SOURCE_ROLES = {
    "claims/CLAIM_LEDGER_1_3_3.json": "claim-ledger",
    "proofs/THEOREM_REGISTRY_1_3_3.json": "theorem-registry",
    "proofs/PROOF_DEPENDENCY_GRAPH_1_3_3.json": "proof-dependency-graph",
    "proofs/FINITE_MODEL_CHECKS_1_3_3.json": "finite-model-checks",
    "proofs/GRAND_TOE_FORMAL_OBLIGATION_LEDGER_1_3_3.json": "grand-formal-obligation-ledger",
    "proofs/grand_promotion/OC133_GRAND_PROMOTION_CONTRACT_REPORT.json": "grand-promotion-contract",
    "formal/lean/OC133V12.lean": "lean-source",
    "formal/lean/OC133GrandPromotion.lean": "lean-source",
    "formal/lean/LEAN_BUILD_CERTIFICATE_1_3_3.json": "lean-build-certificate",
    "reports/OC_CORE_1_3_3_GRAND_EMPIRICAL_REPORT.json": "grand-empirical-report",
    "comparators/OC_1_3_3_MODERN_SCIENCE_SUPERIORITY_REGISTER.json": "modern-science-comparator-register",
    "operations/logion_release_mission/oc_core_1_3_3/OC133_ALL_DOMAIN_READINESS_SCORECARD.json": "all-domain-readiness-scorecard",
    "operations/logion_release_mission/oc_core_1_3_3/toe_closure_factory/OC133_TOE_CLOSURE_COCKPIT.json": "toe-closure-science-cockpit",
    "releases/oc_core_1_3/editorial/OC_CORE_1_3_SCIENCE_SPOT_latest.json": "science-spot-review-gate",
}

FORBIDDEN_PUBLIC_TOKENS = (
    "estra-private-work",
    "logion_local",
    "C:\\",
    "c:\\",
)


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def read_text(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8", errors="replace")


def read_json(rel_path: str) -> dict[str, Any]:
    path = ROOT / rel_path
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def write_json(rel_path: str, payload: dict[str, Any]) -> None:
    path = ROOT / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def sha256_file(rel_path: str) -> str:
    payload = (ROOT / rel_path).read_bytes()
    if Path(rel_path).suffix.lower() in TEXT_HASH_SUFFIXES:
        payload = payload.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(payload).hexdigest()


def safe_int(value: Any) -> int:
    try:
        if isinstance(value, bool):
            return int(value)
        return int(value or 0)
    except Exception:
        return 0


def rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [row for row in list(payload.get("rows") or []) if isinstance(row, dict)]


def string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            out.extend(string_list(item))
        return out
    return [str(value)]


def lean_decl(lean_ref: str) -> str:
    return lean_ref.split("::", 1)[1].strip() if "::" in lean_ref else ""


def lean_source(lean_ref: str) -> str:
    return lean_ref.split("::", 1)[0].strip().replace("\\", "/")


def md_cell(value: Any) -> str:
    return str(value or "").replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def theorem_rows() -> list[dict[str, Any]]:
    return rows(read_json("proofs/THEOREM_REGISTRY_1_3_3.json"))


def claim_rows() -> list[dict[str, Any]]:
    return rows(read_json("claims/CLAIM_LEDGER_1_3_3.json"))


def finite_rows() -> list[dict[str, Any]]:
    return rows(read_json("proofs/FINITE_MODEL_CHECKS_1_3_3.json"))


def selected_evidence_rows(empirical: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        row
        for row in list(empirical.get("candidate_rows") or [])
        if isinstance(row, dict) and row.get("selected_for_domain_support") is True
    ]


def source_artifacts(extra_refs: list[str]) -> list[dict[str, Any]]:
    refs = sorted(set(list(SOURCE_ROLES) + extra_refs + [SCRIPT_REL]))
    artifacts = []
    for ref in refs:
        path = ROOT / ref
        artifacts.append(
            {
                "path": ref,
                "role": SOURCE_ROLES.get(ref, "selected-evidence-pack" if ref in extra_refs else "public-science-tool"),
                "exists": path.exists(),
                "sha256": sha256_file(ref) if path.exists() else "",
                "sha256_policy": "sha256 over LF-normalized text bytes",
            }
        )
    return artifacts


def build_theorem_graph() -> dict[str, Any]:
    theorem_nodes = []
    edge_rows = []
    claims_by_id = {str(row.get("claim_id") or ""): row for row in claim_rows()}
    finite_by_theorem: dict[str, list[dict[str, Any]]] = {}
    for row in finite_rows():
        finite_by_theorem.setdefault(str(row.get("theorem_id") or ""), []).append(row)

    for theorem in theorem_rows():
        theorem_id = str(theorem.get("theorem_id") or "")
        if not theorem_id:
            continue
        claim = claims_by_id.get(theorem_id, {})
        lean_ref = str(theorem.get("lean_ref") or "")
        proof_sheet_ref = str(theorem.get("proof_sheet_ref") or "")
        theorem_nodes.append(
            {
                "node_id": f"theorem:{theorem_id}",
                "node_type": "theorem",
                "theorem_id": theorem_id,
                "title": theorem.get("title"),
                "scientific_promotion_allowed": theorem.get("scientific_promotion_allowed") is True,
                "release_promotion_allowed": theorem.get("release_promotion_allowed") is True,
                "proof_status": theorem.get("proof_status"),
                "proof_sheet_ref": proof_sheet_ref,
                "lean_ref": lean_ref,
                "claim_ref": f"claim:{theorem_id}" if claim else "",
                "finite_case_total": len(finite_by_theorem.get(theorem_id, [])),
                "public_claim_boundary": theorem.get("public_claim_boundary"),
                "scope_limit": theorem.get("scope_limit"),
            }
        )
        if claim:
            edge_rows.append({"edge_type": "proves", "source": f"theorem:{theorem_id}", "target": f"claim:{theorem_id}"})
        if proof_sheet_ref:
            edge_rows.append({"edge_type": "has_proof_sheet", "source": f"theorem:{theorem_id}", "target": proof_sheet_ref})
        if lean_ref:
            edge_rows.append({"edge_type": "formalized_by_lean", "source": f"theorem:{theorem_id}", "target": lean_ref})
        for finite in finite_by_theorem.get(theorem_id, []):
            edge_rows.append({"edge_type": "finite_checked_by", "source": f"theorem:{theorem_id}", "target": f"finite_case:{finite.get('case_id')}"})

    return {
        "schema_id": "CanonicalTheoremGraph_v1",
        "source_edition": SOURCE_EDITION,
        "status": "PASS",
        "nodes": theorem_nodes,
        "edges": edge_rows,
        "summary": {
            "theorem_total": len(theorem_nodes),
            "scientific_promotion_allowed_total": sum(1 for row in theorem_nodes if row["scientific_promotion_allowed"]),
            "lean_formalization_edge_total": sum(1 for row in edge_rows if row["edge_type"] == "formalized_by_lean"),
            "finite_check_edge_total": sum(1 for row in edge_rows if row["edge_type"] == "finite_checked_by"),
        },
    }


def build_proof_graph() -> dict[str, Any]:
    dependency_graph = read_json("proofs/PROOF_DEPENDENCY_GRAPH_1_3_3.json")
    lean_certificate = read_json("formal/lean/LEAN_BUILD_CERTIFICATE_1_3_3.json")
    finite = read_json("proofs/FINITE_MODEL_CHECKS_1_3_3.json")
    grand = read_json("proofs/GRAND_TOE_FORMAL_OBLIGATION_LEDGER_1_3_3.json")
    promotion = read_json("proofs/grand_promotion/OC133_GRAND_PROMOTION_CONTRACT_REPORT.json")
    cert_refs = [
        {
            "declaration": row.get("name"),
            "source_ref": row.get("source_ref"),
            "present": row.get("present") is True,
            "declaration_sha256": row.get("declaration_sha256"),
        }
        for row in list(lean_certificate.get("theorem_refs") or [])
        if isinstance(row, dict)
    ]
    return {
        "schema_id": "CanonicalProofGraph_v1",
        "source_edition": SOURCE_EDITION,
        "status": "PASS",
        "proof_dependency_nodes": dependency_graph.get("nodes") or [],
        "proof_dependency_edges": dependency_graph.get("edges") or [],
        "lean_certificate": {
            "ref": "formal/lean/LEAN_BUILD_CERTIFICATE_1_3_3.json",
            "returncode": lean_certificate.get("returncode"),
            "clean_returncode": lean_certificate.get("clean_returncode"),
            "theorem_ref_total": lean_certificate.get("theorem_ref_total"),
            "theorem_ref_missing_total": lean_certificate.get("theorem_ref_missing_total"),
            "lean_source_sha256": lean_certificate.get("lean_source_sha256"),
            "theorem_refs": cert_refs,
        },
        "finite_model_checks": {
            "ref": "proofs/FINITE_MODEL_CHECKS_1_3_3.json",
            "case_total": finite.get("case_total") or len(rows(finite)),
            "failure_total": finite.get("failure_total"),
            "sample_rows": rows(finite)[:20],
        },
        "grand_formal_obligation": {
            "ref": "proofs/GRAND_TOE_FORMAL_OBLIGATION_LEDGER_1_3_3.json",
            "state": grand.get("state"),
            "release_promotion_allowed": grand.get("release_promotion_allowed") is True,
            "scientific_promotion_allowed": grand.get("scientific_promotion_allowed") is True,
            "promoted_grand_claim_ids": grand.get("promoted_grand_claim_ids") or [],
            "failed_gate_predicates": grand.get("failed_gate_predicates") or [],
        },
        "grand_promotion_contract": {
            "ref": "proofs/grand_promotion/OC133_GRAND_PROMOTION_CONTRACT_REPORT.json",
            "verdict": promotion.get("verdict"),
            "promotion_allowed": promotion.get("promotion_allowed") is True,
        },
    }


def build_evidence_graph(empirical: dict[str, Any]) -> dict[str, Any]:
    selected = selected_evidence_rows(empirical)
    evidence_nodes = []
    edge_rows = []
    for row in selected:
        source_ref = str(row.get("source_ref") or "")
        evidence_id = str(row.get("evidence_pack_id") or source_ref)
        evidence_nodes.append(
            {
                "node_id": f"evidence:{evidence_id}",
                "node_type": "evidence_pack",
                "evidence_pack_id": evidence_id,
                "domain": row.get("domain"),
                "source_ref": source_ref,
                "source_sha256": sha256_file(source_ref) if source_ref and (ROOT / source_ref).exists() else "",
                "source_separation_mode": row.get("source_separation_mode"),
                "n": row.get("n"),
                "model_residual": row.get("model_residual"),
                "comparator_residual": row.get("comparator_residual"),
                "superiority_margin": row.get("superiority_margin"),
            }
        )
        edge_rows.append(
            {
                "edge_type": "supports_claim",
                "source": f"evidence:{evidence_id}",
                "target": "grand_claim:DECLARED_TOE_SCIENTIFIC_CLOSURE",
            }
        )
    return {
        "schema_id": "CanonicalEvidenceGraph_v1",
        "source_edition": SOURCE_EDITION,
        "status": "PASS",
        "empirical_report_ref": "reports/OC_CORE_1_3_3_GRAND_EMPIRICAL_REPORT.json",
        "empirical_gate": {
            "verdict": empirical.get("verdict"),
            "empirical_domain_support_allowed": empirical.get("empirical_domain_support_allowed") is True,
            "domain_predictive_superiority_supported": empirical.get("domain_predictive_superiority_supported") is True,
            "blocked_domain_total": empirical.get("blocked_domain_total"),
            "valid_evidence_pack_total": empirical.get("valid_evidence_pack_total"),
        },
        "nodes": evidence_nodes,
        "edges": edge_rows,
        "summary": {
            "selected_evidence_pack_total": len(evidence_nodes),
            "domain_total": len({row.get("domain") for row in evidence_nodes}),
            "missing_source_total": sum(1 for row in evidence_nodes if not row.get("source_sha256")),
        },
    }


def gate_failures(empirical: dict[str, Any], artifacts: list[dict[str, Any]]) -> list[str]:
    failures = []
    grand = read_json("proofs/GRAND_TOE_FORMAL_OBLIGATION_LEDGER_1_3_3.json")
    promotion = read_json("proofs/grand_promotion/OC133_GRAND_PROMOTION_CONTRACT_REPORT.json")
    finite = read_json("proofs/FINITE_MODEL_CHECKS_1_3_3.json")
    lean = read_json("formal/lean/LEAN_BUILD_CERTIFICATE_1_3_3.json")
    comparator = read_json("comparators/OC_1_3_3_MODERN_SCIENCE_SUPERIORITY_REGISTER.json")
    readiness = read_json("operations/logion_release_mission/oc_core_1_3_3/OC133_ALL_DOMAIN_READINESS_SCORECARD.json")
    cockpit = read_json("operations/logion_release_mission/oc_core_1_3_3/toe_closure_factory/OC133_TOE_CLOSURE_COCKPIT.json")
    spot = read_json("releases/oc_core_1_3/editorial/OC_CORE_1_3_SCIENCE_SPOT_latest.json")
    spot_global = spot.get("global_verdict") if isinstance(spot.get("global_verdict"), dict) else {}

    if any(not row["exists"] for row in artifacts):
        failures.append("PUBLIC_SCIENCE_SOURCE_ARTIFACT_MISSING")
    if grand.get("release_promotion_allowed") is not True or grand.get("scientific_promotion_allowed") is not True:
        failures.append("GRAND_FORMAL_PROMOTION_NOT_ALLOWED")
    if promotion.get("verdict") != "PASS" or promotion.get("promotion_allowed") is not True:
        failures.append("GRAND_PROMOTION_CONTRACT_NOT_PASS")
    if safe_int(lean.get("returncode")) != 0 or safe_int(lean.get("clean_returncode")) != 0:
        failures.append("LEAN_BUILD_NOT_PASS")
    if safe_int(lean.get("theorem_ref_missing_total")) != 0 or safe_int(lean.get("theorem_ref_total")) <= 0:
        failures.append("LEAN_THEOREM_REF_COVERAGE_NOT_PASS")
    if safe_int(finite.get("failure_total")) != 0 or safe_int(finite.get("case_total") or len(rows(finite))) <= 0:
        failures.append("FINITE_MODEL_CHECKS_NOT_PASS")
    if empirical.get("verdict") != "EMPIRICAL_DOMAIN_SUPPORT_ALLOWED":
        failures.append("EMPIRICAL_REPORT_NOT_PASS")
    if empirical.get("empirical_domain_support_allowed") is not True:
        failures.append("EMPIRICAL_DOMAIN_SUPPORT_NOT_ALLOWED")
    if empirical.get("domain_predictive_superiority_supported") is not True:
        failures.append("EMPIRICAL_SUPERIORITY_NOT_SUPPORTED")
    if safe_int(empirical.get("blocked_domain_total")) != 0:
        failures.append("EMPIRICAL_BLOCKED_DOMAINS_PRESENT")
    if len(selected_evidence_rows(empirical)) < max(1, safe_int(empirical.get("empirical_domain_total") or empirical.get("domain_total"))):
        failures.append("EMPIRICAL_SELECTED_PACK_COVERAGE_INCOMPLETE")
    if comparator.get("release_promotion_allowed") is not True or safe_int(comparator.get("failure_total")) != 0 or safe_int(comparator.get("coverage_gap_total")) != 0:
        failures.append("COMPARATOR_GATE_NOT_PASS")
    if safe_int(readiness.get("blocker_total")) != 0 or safe_int(readiness.get("work_order_total")) != 0:
        failures.append("ALL_DOMAIN_READINESS_NOT_PASS")
    if cockpit.get("scientific_lane_status") != "PASS" or safe_int(cockpit.get("science_validator_error_total")) != 0:
        failures.append("TOE_CLOSURE_SCIENTIFIC_LANES_NOT_PASS")
    if spot_global.get("closure_verdict") != "PASS" or safe_int(spot_global.get("hostile_review_blocking_total")) != 0:
        failures.append("SCIENCE_SPOT_NOT_PASS")
    return sorted(set(failures))


def build_manifest(theorem_graph: dict[str, Any], proof_graph: dict[str, Any], evidence_graph: dict[str, Any], artifacts: list[dict[str, Any]], failures: list[str]) -> dict[str, Any]:
    spot = read_json("releases/oc_core_1_3/editorial/OC_CORE_1_3_SCIENCE_SPOT_latest.json")
    spot_global = spot.get("global_verdict") if isinstance(spot.get("global_verdict"), dict) else {}
    return {
        "schema_id": "CanonicalScientificGraphManifest_v1",
        "version": "v1",
        "status": "PASS" if not failures else "FAIL_CLOSED",
        "canon_id": "CANONICAL_SCIENTIFIC_GRAPH",
        "source_edition": SOURCE_EDITION,
        "scope": "Canonical scientific graph for the declared TOE scientific closure.",
        "public_reference_policy": "All refs are repository-relative paths inside this public OC repository. No private workspace paths are allowed.",
        "source_hash_policy": "sha256 over LF-normalized text bytes for text artifacts.",
        "verification_command": f"python {SCRIPT_REL} --verify-only",
        "graph_refs": {
            "theorem_graph": THEOREM_GRAPH_REL,
            "proof_graph": PROOF_GRAPH_REL,
            "evidence_graph": EVIDENCE_GRAPH_REL,
        },
        "reference_refs": {
            "glossary_json": GLOSSARY_JSON_REL,
            "glossary_md": GLOSSARY_MD_REL,
            "internal_to_public_mapping_json": MAPPING_JSON_REL,
            "internal_to_public_mapping_md": MAPPING_MD_REL,
        },
        "source_artifacts": artifacts,
        "failure_reason_codes": failures,
        "summary": {
            "theorem_total": theorem_graph["summary"]["theorem_total"],
            "scientific_promotion_allowed_theorem_total": theorem_graph["summary"]["scientific_promotion_allowed_total"],
            "lean_theorem_ref_total": proof_graph["lean_certificate"]["theorem_ref_total"],
            "lean_theorem_ref_missing_total": proof_graph["lean_certificate"]["theorem_ref_missing_total"],
            "finite_case_total": proof_graph["finite_model_checks"]["case_total"],
            "finite_failure_total": proof_graph["finite_model_checks"]["failure_total"],
            "selected_evidence_pack_total": evidence_graph["summary"]["selected_evidence_pack_total"],
            "empirical_domain_total": evidence_graph["summary"]["domain_total"],
            "science_spot_closure_verdict": spot_global.get("closure_verdict"),
            "science_spot_hostile_review_blocking_total": spot_global.get("hostile_review_blocking_total"),
        },
    }


def build_readme(manifest: dict[str, Any]) -> str:
    summary = manifest["summary"]
    lines = [
        "# Canonical Scientific Graph",
        "",
        "This directory is the public, science-only verification surface for the canonical scientific graph.",
        f"Current source edition: {manifest.get('source_edition')}.",
        "It exposes graph-shaped scientific artifacts, not private project machinery.",
        "",
        "## Verify",
        "",
        "```bash",
        manifest["verification_command"],
        "```",
        "",
        "The verifier checks LF-normalized source artifact hashes, graph status, gate status, theorem/proof/Lean/evidence connectivity, and absence of private workspace path leaks.",
        "",
        "## Graphs",
        "",
        f"- Theorem graph: `{THEOREM_GRAPH_REL}`",
        f"- Proof graph: `{PROOF_GRAPH_REL}`",
        f"- Evidence graph: `{EVIDENCE_GRAPH_REL}`",
        f"- Manifest: `{MANIFEST_REL}`",
        f"- Reviewer glossary: `{GLOSSARY_MD_REL}`",
        f"- Internal-to-public graph mapping: `{MAPPING_JSON_REL}`",
        "",
        "## Closure Counts",
        "",
        f"- Theorems: {summary['theorem_total']}",
        f"- Scientific-promotion theorem rows: {summary['scientific_promotion_allowed_theorem_total']}",
        f"- Lean theorem refs: {summary['lean_theorem_ref_total']} missing {summary['lean_theorem_ref_missing_total']}",
        f"- Finite-model cases: {summary['finite_case_total']} failures {summary['finite_failure_total']}",
        f"- Selected empirical evidence packs: {summary['selected_evidence_pack_total']} across {summary['empirical_domain_total']} domains",
        f"- Science SPOT closure verdict: {summary['science_spot_closure_verdict']}",
        f"- Hostile-review blockers: {summary['science_spot_hostile_review_blocking_total']}",
        "",
        "## Boundary",
        "",
        "This is a public scientific graph. Publication/release-review authorization is a separate gate.",
    ]
    return "\n".join(lines) + "\n"


def build_glossary_payload(manifest: dict[str, Any], theorem_graph: dict[str, Any], proof_graph: dict[str, Any], evidence_graph: dict[str, Any]) -> dict[str, Any]:
    entries: list[dict[str, Any]] = [
        {
            "term_id": "canonical_scientific_graph",
            "term": "Canonical scientific graph",
            "kind": "graph-system",
            "public_ref": MANIFEST_REL,
            "reviewer_use": "Start here to check status, source hashes, verification command, and graph references.",
        },
        {
            "term_id": "theorem_graph",
            "term": "Theorem graph",
            "kind": "graph",
            "public_ref": THEOREM_GRAPH_REL,
            "reviewer_use": "Lists promoted theorem nodes and their claim, proof sheet, Lean, and finite-check edges.",
        },
        {
            "term_id": "proof_graph",
            "term": "Proof graph",
            "kind": "graph",
            "public_ref": PROOF_GRAPH_REL,
            "reviewer_use": "Carries proof dependency rows, Lean certificate refs, finite checks, and grand formal obligation status.",
        },
        {
            "term_id": "evidence_graph",
            "term": "Evidence graph",
            "kind": "graph",
            "public_ref": EVIDENCE_GRAPH_REL,
            "reviewer_use": "Carries selected empirical evidence packs and support edges into the grand scientific closure claim.",
        },
        {
            "term_id": "lean_build_certificate",
            "term": "Lean build certificate",
            "kind": "formal-certificate",
            "public_ref": "formal/lean/LEAN_BUILD_CERTIFICATE_1_3_3.json",
            "reviewer_use": "Checks compiled Lean source refs and theorem declaration coverage.",
        },
        {
            "term_id": "finite_model_checks",
            "term": "Finite model checks",
            "kind": "finite-check-ledger",
            "public_ref": "proofs/FINITE_MODEL_CHECKS_1_3_3.json",
            "reviewer_use": "Checks finite accept/reject witness cases bound to theorem rows.",
        },
        {
            "term_id": "grand_formal_obligation",
            "term": "Grand formal obligation ledger",
            "kind": "promotion-ledger",
            "public_ref": "proofs/GRAND_TOE_FORMAL_OBLIGATION_LEDGER_1_3_3.json",
            "reviewer_use": "Checks the formal promotion gate for the declared scientific closure.",
        },
        {
            "term_id": "science_spot_gate",
            "term": "Science SPOT gate",
            "kind": "review-gate",
            "public_ref": "releases/oc_core_1_3/editorial/OC_CORE_1_3_SCIENCE_SPOT_latest.json",
            "reviewer_use": "Checks hostile-review closure for the science surface used by this graph.",
        },
    ]

    for node in list(theorem_graph.get("nodes") or []):
        if not isinstance(node, dict):
            continue
        theorem_id = str(node.get("theorem_id") or "")
        entries.append(
            {
                "term_id": f"theorem:{theorem_id}",
                "term": str(node.get("title") or theorem_id),
                "kind": "theorem",
                "public_ref": THEOREM_GRAPH_REL,
                "public_node_id": node.get("node_id"),
                "proof_sheet_ref": node.get("proof_sheet_ref"),
                "lean_ref": node.get("lean_ref"),
                "finite_case_total": node.get("finite_case_total"),
                "reviewer_use": "Inspect theorem statement boundary, proof sheet, Lean declaration, and finite-check edges.",
            }
        )

    for node in list(evidence_graph.get("nodes") or []):
        if not isinstance(node, dict):
            continue
        evidence_id = str(node.get("evidence_pack_id") or node.get("node_id") or "")
        entries.append(
            {
                "term_id": f"evidence:{evidence_id}",
                "term": f"{node.get('domain')} evidence pack",
                "kind": "evidence-pack",
                "public_ref": EVIDENCE_GRAPH_REL,
                "public_node_id": node.get("node_id"),
                "source_ref": node.get("source_ref"),
                "source_sha256": node.get("source_sha256"),
                "reviewer_use": "Inspect target-hidden/prospective evidence source and its supports_claim edge.",
            }
        )

    return {
        "schema_id": "CanonicalScientificGraphGlossary_v1",
        "status": "PASS",
        "canon_id": manifest.get("canon_id"),
        "source_edition": manifest.get("source_edition"),
        "manifest_ref": MANIFEST_REL,
        "verification_command": manifest.get("verification_command"),
        "entries": entries,
        "summary": {
            "entry_total": len(entries),
            "theorem_entry_total": sum(1 for row in entries if row.get("kind") == "theorem"),
            "evidence_entry_total": sum(1 for row in entries if row.get("kind") == "evidence-pack"),
        },
    }


def build_glossary_md(glossary: dict[str, Any], theorem_graph: dict[str, Any], evidence_graph: dict[str, Any]) -> str:
    lines = [
        "# Canonical Scientific Graph Glossary",
        "",
        "This glossary is the public reviewer navigation copy for the canonical scientific graph.",
        "",
        "## First Checks",
        "",
        f"- Manifest: `{MANIFEST_REL}`",
        f"- Verification command: `{glossary.get('verification_command')}`",
        f"- Theorem graph: `{THEOREM_GRAPH_REL}`",
        f"- Proof graph: `{PROOF_GRAPH_REL}`",
        f"- Evidence graph: `{EVIDENCE_GRAPH_REL}`",
        "",
        "## Core Terms",
        "",
        "| Term | Kind | Public ref | Reviewer use |",
        "| --- | --- | --- | --- |",
    ]
    for entry in list(glossary.get("entries") or []):
        if not isinstance(entry, dict) or entry.get("kind") in {"theorem", "evidence-pack"}:
            continue
        lines.append(
            f"| {md_cell(entry.get('term'))} | {md_cell(entry.get('kind'))} | `{md_cell(entry.get('public_ref'))}` | {md_cell(entry.get('reviewer_use'))} |"
        )

    lines.extend(
        [
            "",
            "## Theorem Navigation",
            "",
            "| Theorem id | Title | Proof sheet | Lean ref | Finite cases |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for node in list(theorem_graph.get("nodes") or []):
        if not isinstance(node, dict):
            continue
        lines.append(
            "| "
            + " | ".join(
                [
                    md_cell(node.get("theorem_id")),
                    md_cell(node.get("title")),
                    f"`{md_cell(node.get('proof_sheet_ref'))}`",
                    f"`{md_cell(node.get('lean_ref'))}`",
                    md_cell(node.get("finite_case_total")),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Evidence Navigation",
            "",
            "| Domain | Evidence pack | Source ref | Supports |",
            "| --- | --- | --- | --- |",
        ]
    )
    for node in list(evidence_graph.get("nodes") or []):
        if not isinstance(node, dict):
            continue
        lines.append(
            "| "
            + " | ".join(
                [
                    md_cell(node.get("domain")),
                    md_cell(node.get("evidence_pack_id")),
                    f"`{md_cell(node.get('source_ref'))}`",
                    "`grand_claim:DECLARED_TOE_SCIENTIFIC_CLOSURE`",
                ]
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def build_mapping_payload(manifest: dict[str, Any], theorem_graph: dict[str, Any], proof_graph: dict[str, Any], evidence_graph: dict[str, Any]) -> dict[str, Any]:
    mapping_rows: list[dict[str, Any]] = [
        {
            "internal_element_type": "private-canonical-status",
            "internal_element_ref": "logion/k0/governance/status/CANONICAL_SCIENTIFIC_GRAPH_latest.json",
            "public_element_type": "public-manifest",
            "public_element_ref": MANIFEST_REL,
            "mapping_status": "PASS",
            "use_for_artifact_builder": "Use the public manifest as the root public reference for canonical scientific graph status.",
        },
        {
            "internal_element_type": "private-skeleton-gate",
            "internal_element_ref": "logion/k0/governance/status/SCIENTIFIC_CORE_SKELETON_latest.json",
            "public_element_type": "public-graph-surface",
            "public_element_ref": MANIFEST_REL,
            "mapping_status": "PASS",
            "use_for_artifact_builder": "Use public graph refs instead of private skeleton paths when a reader-facing artifact needs a citation target.",
        },
    ]

    for node in list(theorem_graph.get("nodes") or []):
        if not isinstance(node, dict):
            continue
        theorem_id = str(node.get("theorem_id") or "")
        mapping_rows.append(
            {
                "internal_element_type": "scientific-theorem",
                "internal_element_ref": f"ScientificCoreSkeleton.theorem::{theorem_id}",
                "public_element_type": "public-theorem-node",
                "public_element_ref": f"{THEOREM_GRAPH_REL}#theorem:{theorem_id}",
                "public_node_id": node.get("node_id"),
                "public_proof_sheet_ref": node.get("proof_sheet_ref"),
                "public_lean_ref": node.get("lean_ref"),
                "mapping_status": "PASS",
                "use_for_artifact_builder": "Cite the theorem node, proof sheet, or Lean declaration directly from the public repository.",
            }
        )

    cert = proof_graph.get("lean_certificate") if isinstance(proof_graph.get("lean_certificate"), dict) else {}
    for row in list(cert.get("theorem_refs") or []):
        if not isinstance(row, dict):
            continue
        declaration = str(row.get("declaration") or "")
        source_ref = str(row.get("source_ref") or "")
        mapping_rows.append(
            {
                "internal_element_type": "lean-declaration",
                "internal_element_ref": f"LeanDeclaration::{declaration}",
                "public_element_type": "public-lean-declaration",
                "public_element_ref": f"{source_ref}::{declaration}",
                "public_certificate_ref": "formal/lean/LEAN_BUILD_CERTIFICATE_1_3_3.json",
                "mapping_status": "PASS" if row.get("present") is True else "FAIL_CLOSED",
                "use_for_artifact_builder": "Use this declaration ref when a publication artifact needs a formal proof anchor.",
            }
        )

    for node in list(evidence_graph.get("nodes") or []):
        if not isinstance(node, dict):
            continue
        evidence_id = str(node.get("evidence_pack_id") or node.get("node_id") or "")
        mapping_rows.append(
            {
                "internal_element_type": "evidence-pack",
                "internal_element_ref": f"EvidenceExecutionLedger.evidence_pack::{evidence_id}",
                "public_element_type": "public-evidence-node",
                "public_element_ref": f"{EVIDENCE_GRAPH_REL}#evidence:{evidence_id}",
                "public_source_ref": node.get("source_ref"),
                "mapping_status": "PASS",
                "use_for_artifact_builder": "Cite the public evidence node or source pack when an artifact needs empirical support.",
            }
        )

    for artifact in list(manifest.get("source_artifacts") or []):
        if not isinstance(artifact, dict):
            continue
        path = str(artifact.get("path") or "")
        if not path:
            continue
        mapping_rows.append(
            {
                "internal_element_type": "source-artifact",
                "internal_element_ref": f"RecoveredScientificCorpus.source_artifact::{path}",
                "public_element_type": "public-source-artifact",
                "public_element_ref": path,
                "mapping_status": "PASS" if artifact.get("exists") is True else "FAIL_CLOSED",
                "sha256": artifact.get("sha256"),
                "sha256_policy": artifact.get("sha256_policy"),
                "use_for_artifact_builder": "Use the public repository-relative path as the stable citation target.",
            }
        )

    return {
        "schema_id": "CanonicalScientificGraphInternalPublicMapping_v1",
        "status": "PASS" if all(row.get("mapping_status") == "PASS" for row in mapping_rows) else "FAIL_CLOSED",
        "canon_id": manifest.get("canon_id"),
        "source_edition": manifest.get("source_edition"),
        "manifest_ref": MANIFEST_REL,
        "mapping_policy": "Map internal logical scientific graph elements to public repository-relative graph nodes and source refs. No absolute private workspace paths are used.",
        "rows": mapping_rows,
        "summary": {
            "mapping_total": len(mapping_rows),
            "theorem_mapping_total": sum(1 for row in mapping_rows if row.get("internal_element_type") == "scientific-theorem"),
            "lean_mapping_total": sum(1 for row in mapping_rows if row.get("internal_element_type") == "lean-declaration"),
            "evidence_mapping_total": sum(1 for row in mapping_rows if row.get("internal_element_type") == "evidence-pack"),
            "failing_mapping_total": sum(1 for row in mapping_rows if row.get("mapping_status") != "PASS"),
        },
    }


def build_mapping_md(mapping: dict[str, Any]) -> str:
    lines = [
        "# Internal To Public Scientific Graph Mapping",
        "",
        "This file tells internal artifact builders which public scientific graph element to cite.",
        "",
        "| Internal element | Public element | Public source | Builder use |",
        "| --- | --- | --- | --- |",
    ]
    for row in list(mapping.get("rows") or []):
        if not isinstance(row, dict):
            continue
        public_ref = row.get("public_element_ref") or row.get("public_source_ref") or ""
        source_ref = row.get("public_source_ref") or row.get("public_certificate_ref") or ""
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{md_cell(row.get('internal_element_ref'))}`",
                    f"`{md_cell(public_ref)}`",
                    f"`{md_cell(source_ref)}`",
                    md_cell(row.get("use_for_artifact_builder")),
                ]
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def build() -> dict[str, Any]:
    empirical = read_json("reports/OC_CORE_1_3_3_GRAND_EMPIRICAL_REPORT.json")
    evidence_refs = [str(row.get("source_ref") or "") for row in selected_evidence_rows(empirical) if row.get("source_ref")]
    artifacts = source_artifacts(evidence_refs)
    theorem_graph = build_theorem_graph()
    proof_graph = build_proof_graph()
    evidence_graph = build_evidence_graph(empirical)
    failures = gate_failures(empirical, artifacts)
    manifest = build_manifest(theorem_graph, proof_graph, evidence_graph, artifacts, failures)

    write_json(THEOREM_GRAPH_REL, theorem_graph)
    write_json(PROOF_GRAPH_REL, proof_graph)
    write_json(EVIDENCE_GRAPH_REL, evidence_graph)
    write_json(MANIFEST_REL, manifest)
    readme_path = ROOT / README_REL
    readme_path.parent.mkdir(parents=True, exist_ok=True)
    readme_path.write_text(build_readme(manifest), encoding="utf-8", newline="\n")
    glossary = build_glossary_payload(manifest, theorem_graph, proof_graph, evidence_graph)
    write_json(GLOSSARY_JSON_REL, glossary)
    (ROOT / GLOSSARY_MD_REL).write_text(build_glossary_md(glossary, theorem_graph, evidence_graph), encoding="utf-8", newline="\n")
    mapping = build_mapping_payload(manifest, theorem_graph, proof_graph, evidence_graph)
    write_json(MAPPING_JSON_REL, mapping)
    (ROOT / MAPPING_MD_REL).write_text(build_mapping_md(mapping), encoding="utf-8", newline="\n")
    return manifest


def graph_connectivity_failures(manifest: dict[str, Any], theorem_graph: dict[str, Any], proof_graph: dict[str, Any], evidence_graph: dict[str, Any]) -> list[str]:
    failures: list[str] = []

    graph_refs = manifest.get("graph_refs") if isinstance(manifest.get("graph_refs"), dict) else {}
    expected_refs = {
        "theorem_graph": THEOREM_GRAPH_REL,
        "proof_graph": PROOF_GRAPH_REL,
        "evidence_graph": EVIDENCE_GRAPH_REL,
    }
    for key, expected in expected_refs.items():
        if graph_refs.get(key) != expected:
            failures.append(f"PUBLIC_SCIENCE_GRAPH_REF_MISMATCH::{key}")
        if not (ROOT / expected).exists():
            failures.append(f"PUBLIC_SCIENCE_GRAPH_FILE_MISSING::{expected}")

    theorem_nodes = [row for row in list(theorem_graph.get("nodes") or []) if isinstance(row, dict)]
    theorem_edges = [row for row in list(theorem_graph.get("edges") or []) if isinstance(row, dict)]
    proof_nodes = list(proof_graph.get("proof_dependency_nodes") or [])
    proof_edges = list(proof_graph.get("proof_dependency_edges") or [])
    if not theorem_nodes:
        failures.append("PUBLIC_SCIENCE_THEOREM_GRAPH_EMPTY")
    if not proof_nodes:
        failures.append("PUBLIC_SCIENCE_PROOF_DEPENDENCY_NODES_EMPTY")
    if not proof_edges:
        failures.append("PUBLIC_SCIENCE_PROOF_DEPENDENCY_EDGES_EMPTY")

    edges_by_source: dict[str, list[dict[str, Any]]] = {}
    for edge in theorem_edges:
        edges_by_source.setdefault(str(edge.get("source") or ""), []).append(edge)

    cert = proof_graph.get("lean_certificate") if isinstance(proof_graph.get("lean_certificate"), dict) else {}
    cert_ref_names = {
        str(row.get("declaration") or "")
        for row in list(cert.get("theorem_refs") or [])
        if isinstance(row, dict) and row.get("present") is True
    }
    lean_texts: dict[str, str] = {}

    for node in theorem_nodes:
        node_id = str(node.get("node_id") or "")
        theorem_id = str(node.get("theorem_id") or node_id)
        source_edges = edges_by_source.get(node_id, [])
        edge_types = {str(edge.get("edge_type") or "") for edge in source_edges}
        if node.get("scientific_promotion_allowed") is not True:
            failures.append(f"PUBLIC_SCIENCE_THEOREM_NOT_SCIENTIFICALLY_PROMOTED::{theorem_id}")
        if "proves" not in edge_types:
            failures.append(f"PUBLIC_SCIENCE_THEOREM_PROVES_EDGE_MISSING::{theorem_id}")
        if "has_proof_sheet" not in edge_types:
            failures.append(f"PUBLIC_SCIENCE_THEOREM_PROOF_SHEET_EDGE_MISSING::{theorem_id}")
        if "formalized_by_lean" not in edge_types:
            failures.append(f"PUBLIC_SCIENCE_THEOREM_LEAN_EDGE_MISSING::{theorem_id}")
        if "finite_checked_by" not in edge_types:
            failures.append(f"PUBLIC_SCIENCE_THEOREM_FINITE_EDGE_MISSING::{theorem_id}")

        proof_sheet_ref = str(node.get("proof_sheet_ref") or "")
        if not proof_sheet_ref or not (ROOT / proof_sheet_ref).exists():
            failures.append(f"PUBLIC_SCIENCE_THEOREM_PROOF_SHEET_MISSING::{theorem_id}")

        lean_ref = str(node.get("lean_ref") or "")
        decl = lean_decl(lean_ref)
        source_ref = lean_source(lean_ref)
        if not lean_ref or not decl or not source_ref:
            failures.append(f"PUBLIC_SCIENCE_THEOREM_LEAN_REF_MISSING::{theorem_id}")
        elif not (ROOT / source_ref).exists():
            failures.append(f"PUBLIC_SCIENCE_THEOREM_LEAN_SOURCE_MISSING::{theorem_id}::{source_ref}")
        else:
            lean_texts.setdefault(source_ref, read_text(source_ref))
            if decl not in lean_texts[source_ref]:
                failures.append(f"PUBLIC_SCIENCE_THEOREM_LEAN_DECL_MISSING::{theorem_id}::{decl}")
            if decl not in cert_ref_names:
                failures.append(f"PUBLIC_SCIENCE_THEOREM_LEAN_CERT_REF_MISSING::{theorem_id}::{decl}")

        if safe_int(node.get("finite_case_total")) <= 0:
            failures.append(f"PUBLIC_SCIENCE_THEOREM_FINITE_CASES_MISSING::{theorem_id}")

    finite = proof_graph.get("finite_model_checks") if isinstance(proof_graph.get("finite_model_checks"), dict) else {}
    if safe_int(finite.get("case_total")) <= 0 or safe_int(finite.get("failure_total")) != 0:
        failures.append("PUBLIC_SCIENCE_FINITE_MODEL_SUMMARY_NOT_PASS")

    for row in list(cert.get("theorem_refs") or []):
        if not isinstance(row, dict):
            continue
        declaration = str(row.get("declaration") or "")
        source_ref = str(row.get("source_ref") or "")
        if row.get("present") is not True:
            failures.append(f"PUBLIC_SCIENCE_LEAN_CERT_DECL_NOT_PRESENT::{declaration}")
        if not source_ref or not (ROOT / source_ref).exists():
            failures.append(f"PUBLIC_SCIENCE_LEAN_CERT_SOURCE_MISSING::{declaration}")

    evidence_nodes = [row for row in list(evidence_graph.get("nodes") or []) if isinstance(row, dict)]
    evidence_edges = [row for row in list(evidence_graph.get("edges") or []) if isinstance(row, dict)]
    if not evidence_nodes:
        failures.append("PUBLIC_SCIENCE_EVIDENCE_GRAPH_EMPTY")
    support_sources = {
        str(edge.get("source") or "")
        for edge in evidence_edges
        if edge.get("edge_type") == "supports_claim"
    }
    for node in evidence_nodes:
        node_id = str(node.get("node_id") or "")
        source_ref = str(node.get("source_ref") or "")
        evidence_id = str(node.get("evidence_pack_id") or node_id)
        if node_id not in support_sources:
            failures.append(f"PUBLIC_SCIENCE_EVIDENCE_SUPPORT_EDGE_MISSING::{evidence_id}")
        if not source_ref or not (ROOT / source_ref).exists():
            failures.append(f"PUBLIC_SCIENCE_EVIDENCE_SOURCE_MISSING::{evidence_id}")
        elif node.get("source_sha256") != sha256_file(source_ref):
            failures.append(f"PUBLIC_SCIENCE_EVIDENCE_SOURCE_HASH_MISMATCH::{evidence_id}")
        if not node.get("domain"):
            failures.append(f"PUBLIC_SCIENCE_EVIDENCE_DOMAIN_MISSING::{evidence_id}")

    return failures


def verify() -> list[str]:
    failures: list[str] = []
    manifest = read_json(MANIFEST_REL)
    theorem_graph = read_json(THEOREM_GRAPH_REL)
    proof_graph = read_json(PROOF_GRAPH_REL)
    evidence_graph = read_json(EVIDENCE_GRAPH_REL)
    glossary = read_json(GLOSSARY_JSON_REL)
    mapping = read_json(MAPPING_JSON_REL)
    for rel_path, payload in (
        (MANIFEST_REL, manifest),
        (THEOREM_GRAPH_REL, theorem_graph),
        (PROOF_GRAPH_REL, proof_graph),
        (EVIDENCE_GRAPH_REL, evidence_graph),
        (GLOSSARY_JSON_REL, glossary),
        (MAPPING_JSON_REL, mapping),
    ):
        if not payload:
            failures.append(f"PUBLIC_SCIENCE_EXPORT_MISSING::{rel_path}")
        elif payload.get("status") != "PASS":
            failures.append(f"PUBLIC_SCIENCE_EXPORT_NOT_PASS::{rel_path}")
    for key, rel_path in dict(manifest.get("reference_refs") or {}).items():
        if not (ROOT / str(rel_path)).exists():
            failures.append(f"PUBLIC_SCIENCE_REFERENCE_MISSING::{key}")
    if safe_int(glossary.get("summary", {}).get("theorem_entry_total") if isinstance(glossary.get("summary"), dict) else 0) != safe_int(theorem_graph.get("summary", {}).get("theorem_total") if isinstance(theorem_graph.get("summary"), dict) else 0):
        failures.append("PUBLIC_SCIENCE_GLOSSARY_THEOREM_COVERAGE_MISMATCH")
    if safe_int(mapping.get("summary", {}).get("theorem_mapping_total") if isinstance(mapping.get("summary"), dict) else 0) != safe_int(theorem_graph.get("summary", {}).get("theorem_total") if isinstance(theorem_graph.get("summary"), dict) else 0):
        failures.append("PUBLIC_SCIENCE_MAPPING_THEOREM_COVERAGE_MISMATCH")
    if safe_int(mapping.get("summary", {}).get("failing_mapping_total") if isinstance(mapping.get("summary"), dict) else 1) != 0:
        failures.append("PUBLIC_SCIENCE_MAPPING_FAILURES_PRESENT")
    for artifact in list(manifest.get("source_artifacts") or []):
        if not isinstance(artifact, dict):
            continue
        ref = str(artifact.get("path") or "")
        if not ref or not (ROOT / ref).exists():
            failures.append(f"PUBLIC_SCIENCE_SOURCE_MISSING::{ref}")
            continue
        if artifact.get("sha256") != sha256_file(ref):
            failures.append(f"PUBLIC_SCIENCE_SOURCE_HASH_MISMATCH::{ref}")
    for rel_path in (MANIFEST_REL, THEOREM_GRAPH_REL, PROOF_GRAPH_REL, EVIDENCE_GRAPH_REL, README_REL, GLOSSARY_JSON_REL, GLOSSARY_MD_REL, MAPPING_JSON_REL, MAPPING_MD_REL):
        text = read_text(rel_path) if (ROOT / rel_path).exists() else ""
        for token in FORBIDDEN_PUBLIC_TOKENS:
            if token in text:
                failures.append(f"PUBLIC_SCIENCE_PRIVATE_PATH_LEAK::{rel_path}::{token}")
    failures.extend(graph_connectivity_failures(manifest, theorem_graph, proof_graph, evidence_graph))
    return sorted(set(failures))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build and verify the canonical scientific graph.")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args(argv)
    if not args.verify_only:
        manifest = build()
        if manifest.get("status") != "PASS":
            print(json.dumps({"status": manifest.get("status"), "failure_reason_codes": manifest.get("failure_reason_codes")}, sort_keys=True))
            return 2
    failures = verify()
    status = "PASS" if not failures else "FAIL_CLOSED"
    print(json.dumps({"status": status, "failure_reason_codes": failures}, sort_keys=True))
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
