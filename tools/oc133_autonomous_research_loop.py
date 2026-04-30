from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CERBERUS_DIR = ROOT / "reviews" / "oc133_llm_cerberus"
RESULT_DIR = CERBERUS_DIR / "results"
REPAIR_DIR = CERBERUS_DIR / "repair"
TRIGGER_TABLE = REPAIR_DIR / "OC133_CERBERUS_REPAIR_TRIGGER_TABLE.json"
WORK_ORDERS = REPAIR_DIR / "OC133_CERBERUS_REPAIR_WORK_ORDERS.json"
RUN_LEDGER = REPAIR_DIR / "OC133_AUTONOMOUS_RESEARCH_LOOP_LEDGER.json"
PROFILE_LEDGER = REPAIR_DIR / "OC133_CAPABILITY_REPAIR_EXECUTION_LEDGER.json"
DIRECTOR_PACKET = ROOT / "operations" / "institute_director" / "oc_core_1_3_3" / "OC133_INSTITUTE_DIRECTOR_PACKET.json"
DIRECTOR_WORK_ORDERS = ROOT / "operations" / "institute_director" / "oc_core_1_3_3" / "OC133_INSTITUTE_DIRECTOR_WORK_ORDERS.json"

DIRECTOR_CAPABILITY_PROFILE_MAP = {
    "formal_lifecycle_morphism_repair": "v12_lifecycle_invariant_repair",
    "identity_truth_table_repair": "v12_lifecycle_invariant_repair",
    "hybrid_operator_semantics_repair": "v12_hybrid_operator_repair",
    "klevel_non_circular_semantics_repair": "v12_klevel_semantic_repair",
    "numeric_replay_leakage_repair": "v12_empirical_quarantine_repair",
    "phenomenon_coverage_repair": "v12_klevel_semantic_repair",
    "public_surface_no_send_repair": "v12_no_send_public_surface_repair",
    "attack_matrix_reopen_recompute_repair": "v12_attack_matrix_binding_repair",
    "cerberus_timeout_context_repair": "v12_lean_certificate_repair",
}

REPAIR_PROFILES = {
    "v12_klevel_semantic_repair": "K-level atlas, retained witness, demotion, and finite transition repair.",
    "v12_hybrid_operator_repair": "Hybrid/smooth/update semantics and finite guard/reset repair.",
    "v12_minimality_tuple_repair": "Release tuple component keep/drop witness repair.",
    "v12_k0_countermodel_repair": "K0 raw separation versus resolution distinction finite/Lean repair.",
    "v12_kzero_semantic_repair": "Continuumness k=0 zero-cause semantics and negative-control repair.",
    "v12_attack_matrix_binding_repair": "Concrete Cerberus finding to evidence-row repair.",
    "v12_lifecycle_invariant_repair": "Death/live/residue/rebirth identity invariant repair.",
    "v12_empirical_quarantine_repair": "Numeric replay quarantine and no fake prediction support repair.",
    "v12_target_blind_empirical_repair": "Bounded target-blind empirical reconstruction repair with row-level predicates and no broad domain-validation promotion.",
    "v12_novelty_positioning_repair": "Prior-art positioning, no uniqueness/priority promotion repair.",
    "v12_no_send_public_surface_repair": "Owner approval and public-channel no-send parity repair.",
    "v12_lean_certificate_repair": "Lean build certificate and theorem-ref binding repair.",
    "v12_integrated_materializer": "Integrated materializer that applies all currently implemented repair capabilities.",
}


@dataclass(frozen=True)
class Trigger:
    trigger_id: str
    profile: str
    claim_tokens: tuple[str, ...]
    artifact_tokens: tuple[str, ...]
    failure_tokens: tuple[str, ...]
    repair_refs: tuple[str, ...]


TRIGGERS = (
    Trigger(
        trigger_id="R-FORMAL-KLEVEL-ATLAS",
        profile="v12_klevel_semantic_repair",
        claim_tokens=("T133-KLEVEL", "K-level", "K0->K12"),
        artifact_tokens=("formal/lean/OC133V12.lean", "proofs/finite_model_checks", "review/OC_1_3_3_TOTAL_ATTACK_MATRIX.json"),
        failure_tokens=("atlas", "reduction", "demotion", "threshold", "toy", "witness"),
        repair_refs=(
            "formal/lean/OC133V12.lean::every_adjacent_transition_matches_atlas_with_witness_and_lawful_demotion",
            "data/k_level_irreducibility_matrix.json",
            "proofs/finite_model_checks/run_finite_model_checks.py::klevel_reduction_verdict",
        ),
    ),
    Trigger(
        trigger_id="R-FORMAL-HYBRID-SHARED-STATE",
        profile="v12_hybrid_operator_repair",
        claim_tokens=("T133-HYBRID", "Hybrid", "differential"),
        artifact_tokens=("formal/lean/OC133V12.lean", "proofs/finite_model_checks"),
        failure_tokens=("smooth", "derivative", "chart", "hybrid", "state types", "ODE"),
        repair_refs=(
            "formal/lean/OC133V12.lean::smooth_hybrid_operator_semantics",
            "proofs/FINITE_MODEL_CHECKS_1_3_3.json::FM-T133-HYBRID-POS",
        ),
    ),
    Trigger(
        trigger_id="R-FORMAL-MIN-RELEASE-TUPLE",
        profile="v12_minimality_tuple_repair",
        claim_tokens=("T133-MIN", "minimality", "tuple"),
        artifact_tokens=("formal/lean/OC133V12.lean", "data/OC133_GLOBAL_MINIMALITY_WITNESSES.json"),
        failure_tokens=("component", "minimality", "relabel", "hardcoded", "release tuple"),
        repair_refs=(
            "formal/lean/OC133V12.lean::release_tuple_semantic_component_irredundant",
            "data/OC133_GLOBAL_MINIMALITY_WITNESSES.json",
            "proofs/FINITE_MODEL_CHECKS_1_3_3.json::FM-MIN-*",
        ),
    ),
    Trigger(
        trigger_id="R-FORMAL-K0-COUNTERMODEL",
        profile="v12_k0_countermodel_repair",
        claim_tokens=("T133-K0-RES", "K0", "raw global discreteness"),
        artifact_tokens=("formal/lean/OC133V12.lean", "docs/OC_1_3_3_PHENOMENON_COVERAGE_MATRIX.json"),
        failure_tokens=("raw", "global discreteness", "non-entailment", "countermodel"),
        repair_refs=(
            "formal/lean/OC133V12.lean::k0_countermodel_raw_separation_not_resolution_distinction",
            "proofs/FINITE_MODEL_CHECKS_1_3_3.json::FM-T133-K0-RES-POS",
        ),
    ),
    Trigger(
        trigger_id="R-FORMAL-KZERO-ZERO-CAUSE",
        profile="v12_kzero_semantic_repair",
        claim_tokens=("T133-K-ZERO", "Continuumness zero", "k=0", "zero-cause"),
        artifact_tokens=("formal/lean/OC133V12.lean", "proofs/THEOREM_INVENTORY_1_3_3.json", "proofs/FINITE_MODEL_CHECKS_1_3_3.json"),
        failure_tokens=("definitional", "zero-cause", "continuumness", "theorem theater", "empty admissibility"),
        repair_refs=(
            "formal/lean/OC133V12.lean::continuumness_zero_case_iff_declared_zero_cause_with_support",
            "proofs/FINITE_MODEL_CHECKS_1_3_3.json::FM-T133-K-ZERO-POS",
            "proofs/FINITE_MODEL_CHECKS_1_3_3.json::FM-T133-K-ZERO-NEG",
        ),
    ),
    Trigger(
        trigger_id="R-ATTACK-MATRIX-EVIDENCE-BINDING",
        profile="v12_attack_matrix_binding_repair",
        claim_tokens=("critical_unresolved_total", "high_unresolved_total", "CLOSED_BY_SPECIFIC_V12_EVIDENCE"),
        artifact_tokens=("review/OC_1_3_3_TOTAL_ATTACK_MATRIX.json", "reviews/OC_CORE_1_3_3_REVIEWER_RESPONSE_MATRIX.json"),
        failure_tokens=("attack matrix", "closure", "same artifacts", "status tokens", "generic"),
        repair_refs=(
            "review/OC_1_3_3_TOTAL_ATTACK_MATRIX.json::closure_verification_query",
            "reviews/oc133_llm_cerberus/repair/OC133_CERBERUS_REPAIR_WORK_ORDERS.json",
        ),
    ),
    Trigger(
        trigger_id="R-FORMAL-LIFECYCLE-INVARIANTS",
        profile="v12_lifecycle_invariant_repair",
        claim_tokens=("T133-OMEGA-STATUS", "death", "residue", "rebirth", "liveness"),
        artifact_tokens=("formal/lean/OC133V12.lean", "claims/CLAIM_LEDGER_1_3_3.json"),
        failure_tokens=("death", "live", "coexist", "typed separation", "invariant", "non-identity"),
        repair_refs=(
            "formal/lean/OC133V12.lean::death_live_conflict_impossible",
            "formal/lean/OC133V12.lean::residue_rebirth_are_typed_source_target_relations",
            "proofs/FINITE_MODEL_CHECKS_1_3_3.json::FM-T133-OMEGA-STATUS-NEG",
        ),
    ),
    Trigger(
        trigger_id="R-EMPIRICAL-REPLAY-QUARANTINE",
        profile="v12_empirical_quarantine_repair",
        claim_tokens=("OC133-NUM", "numeric", "prediction", "replay", "PubChem", "NIST", "GEO"),
        artifact_tokens=("validation/numeric_predictions/OC133_NUMERIC_PREDICTION_TABLE.json", "validation/numeric_predictions"),
        failure_tokens=("snapshot replay", "formula", "empirical", "prediction support", "quarantine", "promotion"),
        repair_refs=(
            "validation/numeric_predictions/OC133_NUMERIC_PREDICTION_TABLE.json::prediction_support_allowed=false",
            "validation/numeric_predictions/OC133_NUMERIC_REPLAY_LOG.json",
            "reports/OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.json::quarantined_replay_qa_total",
        ),
    ),
    Trigger(
        trigger_id="R-NOVELTY-POSITIONING-DEMOTION",
        profile="v12_novelty_positioning_repair",
        claim_tokens=("OC133-NOVELTY-001", "novelty", "prior-art", "bounded positioning"),
        artifact_tokens=("comparators/OC_1_3_3_NOVELTY_AND_PRIORITY_REGISTER.json", "comparators/source_snapshots"),
        failure_tokens=("NOT_FOUND_IN_SOURCE_PAGE", "absence", "source drift", "query", "systematic", "priority", "uniqueness"),
        repair_refs=(
            "comparators/OC_1_3_3_NOVELTY_AND_PRIORITY_REGISTER.json::systematic_priority_search_status",
            "comparators/source_snapshots/*.txt",
            "claims/CLAIM_LEDGER_1_3_3.json::OC133-NOVELTY-001",
        ),
    ),
    Trigger(
        trigger_id="R-NOSEND-PUBLIC-SURFACE-PARITY",
        profile="v12_no_send_public_surface_repair",
        claim_tokens=("OC133-NOSEND-001", "no-send", "publish_allowed", "owner_approved"),
        artifact_tokens=("OWNER_RELEASE_APPROVAL_v1.3.3.json", "OC_CORE_1_3_3_PUBLISH_MANIFEST_DRAFT.json"),
        failure_tokens=("zenodo", "github", "journal", "doi", "software heritage", "public action", "owner artifact"),
        repair_refs=(
            "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_PUBLISH_MANIFEST_DRAFT.json::all_public_channels_false",
            "proofs/FINITE_MODEL_CHECKS_1_3_3.json::ADV-NOSEND-PUBLISH",
        ),
    ),
    Trigger(
        trigger_id="R-LEAN-BUILD-CERTIFICATE",
        profile="v12_lean_certificate_repair",
        claim_tokens=("machine_checked_subset_total", "Lean", "lake build"),
        artifact_tokens=("formal/lean/OC133V12.lean", "formal/lean/LEAN_BUILD_CERTIFICATE_1_3_3.json"),
        failure_tokens=("certificate", "execution", "theorem-name", "source hash", "toolchain"),
        repair_refs=(
            "formal/lean/LEAN_BUILD_CERTIFICATE_1_3_3.json",
            "proofs/FINITE_MODEL_CHECKS_1_3_3.json::lean_build_certificate_ref",
        ),
    ),
)


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def command(cmd: list[str], *, timeout: int = 900) -> dict[str, Any]:
    completed = subprocess.run(cmd, cwd=ROOT, text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=timeout)
    return {
        "cmd": cmd,
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout[-4000:],
        "stderr_tail": completed.stderr[-4000:],
    }


def open_findings() -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for path in sorted(RESULT_DIR.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        role = payload.get("role", path.stem)
        for row in payload.get("findings", []):
            severity = str(row.get("severity", "")).upper()
            status = str(row.get("status", "OPEN")).upper()
            if severity in {"CRITICAL", "HIGH"} and status not in {"CLOSED", "RESOLVED", "CLOSED_BY_V12_EVIDENCE"}:
                enriched = dict(row)
                enriched["role"] = role
                enriched["source_result_ref"] = rel(path)
                findings.append(enriched)
    return findings


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def director_orders() -> list[dict[str, Any]]:
    """Import subordinate Institute Director work orders as authoritative repair input."""

    payload = read_json(DIRECTOR_WORK_ORDERS)
    rows = payload.get("rows", [])
    if not isinstance(rows, list):
        return []
    normalized: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        capability_id = str(row.get("capability_id", ""))
        profile = DIRECTOR_CAPABILITY_PROFILE_MAP.get(capability_id, "BLOCKED_UNKNOWN_REPAIR_PROFILE")
        normalized.append(
            {
                "work_order_id": row.get("work_order_id"),
                "finding_hash": sha256_text(json.dumps(row, ensure_ascii=False, sort_keys=True))[:16],
                "source": "institute_director_work_order",
                "director_decision": row.get("director_decision"),
                "director_capability_id": capability_id,
                "director_repair_kind": row.get("repair_kind"),
                "director_repair_contract": row.get("repair_contract"),
                "director_owned_artifacts": row.get("owned_artifacts", []),
                "source_result_ref": row.get("source_result_ref"),
                "role": row.get("role"),
                "severity": row.get("severity"),
                "artifact_ref": row.get("artifact_ref"),
                "claim": row.get("claim"),
                "failure_mode": row.get("failure_mode"),
                "required_repair": row.get("required_repair"),
                "trigger_id": f"DIRECTOR::{capability_id}" if profile in REPAIR_PROFILES else "DIRECTOR::UNKNOWN",
                "trigger_score": row.get("capability_score", 0),
                "profile": profile,
                "repair_refs": row.get("owned_artifacts", []),
                "status": "QUEUED" if profile in REPAIR_PROFILES else "BLOCKED_UNKNOWN_REPAIR_PROFILE",
            }
        )
    return normalized


def trigger_payload() -> dict[str, Any]:
    return {
        "schema_id": "OC133_CERBERUS_REPAIR_TRIGGER_TABLE_v1",
        "release_id": "oc_core_1_3_3",
        "version": "1.3.3",
        "policy": "Critical/high Cerberus findings become repair work orders. Unknown or unsupported repairs remain blockers; the loop may not mint PASS from status tokens.",
        "profiles": {
            profile: {
                "description": description,
                "entrypoint": f"tools/oc133_capability_repair_executor.py --profile {profile}",
                "bootstrap_entrypoint": "tools/materialize_oc_core_1_3_3_v12_closure.py",
                "implementation_note": "The integrated materializer may refresh shared generated surfaces once, but closure is verified by this profile-specific executor and its predicate ledger.",
                "no_send": True,
            }
            for profile, description in REPAIR_PROFILES.items()
        },
        "triggers": [
            {
                "trigger_id": trigger.trigger_id,
                "profile": trigger.profile,
                "claim_tokens": list(trigger.claim_tokens),
                "artifact_tokens": list(trigger.artifact_tokens),
                "failure_tokens": list(trigger.failure_tokens),
                "repair_refs": list(trigger.repair_refs),
            }
            for trigger in TRIGGERS
        ],
    }


def score_trigger(trigger: Trigger, finding: dict[str, Any]) -> int:
    haystack = "\n".join(
        str(finding.get(key, ""))
        for key in ("claim", "artifact_ref", "failure_mode", "required_repair")
    ).lower()
    score = 0
    for token in trigger.claim_tokens:
        if token.lower() in haystack:
            score += 4
    for token in trigger.artifact_tokens:
        if token.lower() in haystack:
            score += 3
    for token in trigger.failure_tokens:
        if token.lower() in haystack:
            score += 2
    return score


def build_work_orders(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    orders: list[dict[str, Any]] = []
    for idx, finding in enumerate(findings, start=1):
        ranked = sorted(((score_trigger(trigger, finding), trigger) for trigger in TRIGGERS), key=lambda item: item[0], reverse=True)
        score, trigger = ranked[0]
        finding_text = json.dumps(finding, ensure_ascii=False, sort_keys=True)
        orders.append(
            {
                "work_order_id": f"OC133-AUTO-REPAIR-{idx:03d}",
                "finding_hash": sha256_text(finding_text)[:16],
                "source_result_ref": finding.get("source_result_ref"),
                "role": finding.get("role"),
                "severity": finding.get("severity"),
                "artifact_ref": finding.get("artifact_ref"),
                "claim": finding.get("claim"),
                "failure_mode": finding.get("failure_mode"),
                "required_repair": finding.get("required_repair"),
                "trigger_id": trigger.trigger_id if score > 0 else "UNKNOWN",
                "trigger_score": score,
                "profile": trigger.profile if score > 0 else "BLOCKED_UNKNOWN_REPAIR_PROFILE",
                "repair_refs": list(trigger.repair_refs) if score > 0 else [],
                "status": "QUEUED" if score > 0 else "BLOCKED_UNKNOWN_REPAIR_PROFILE",
            }
        )
    return orders


def apply_profiles(orders: list[dict[str, Any]]) -> list[dict[str, Any]]:
    profiles = sorted({order["profile"] for order in orders if order["status"] == "QUEUED"})
    results: list[dict[str, Any]] = []
    known_profiles = [profile for profile in profiles if profile in REPAIR_PROFILES]
    unknown_profiles = [profile for profile in profiles if profile not in REPAIR_PROFILES]
    integrated_result: dict[str, Any] | None = None
    if known_profiles:
        integrated_result = command([sys.executable, "tools/materialize_oc_core_1_3_3_v12_closure.py"], timeout=900)
        integrated_result["profile"] = "v12_integrated_materializer"
        integrated_result["capability_profiles_applied"] = known_profiles
        integrated_result["role"] = "shared_generated_surface_bootstrap_only"
        results.append(integrated_result)
        class_remediation_result = command([sys.executable, "tools/oc133_vulnerability_class_remediator.py", "--apply"], timeout=420)
        class_remediation_result["profile"] = "v12_vulnerability_class_remediator"
        class_remediation_result["capability_description"] = "Class-level Cerberus finding remediation axis: finding class -> repair function -> predicate ledger."
        class_remediation_result["role"] = "shared_class_level_repair_axis"
        if class_remediation_result["returncode"] != 0:
            sync_result = command([sys.executable, "tools/materialize_oc_core_1_3_3_v12_closure.py"], timeout=900)
            sync_result["profile"] = "v12_post_class_remediation_materializer_sync"
            sync_result["capability_description"] = "Regenerate dependent artifacts after class-level edits before deciding whether the class repair truly failed."
            sync_result["role"] = "shared_generated_surface_sync_after_class_repair"
            results.append(sync_result)
            retry_result = command([sys.executable, "tools/oc133_vulnerability_class_remediator.py", "--apply"], timeout=420)
            retry_result["profile"] = "v12_vulnerability_class_remediator_retry_after_sync"
            retry_result["capability_description"] = "One deterministic retry after materializer sync; prevents stale generated artifacts from masquerading as class-repair failure."
            retry_result["role"] = "shared_class_level_repair_axis"
            results.append(retry_result)
            if retry_result["returncode"] == 0:
                class_remediation_result["returncode"] = 0
                class_remediation_result["stale_generated_artifact_failure_recovered_by_retry"] = True
                class_remediation_result["retry_profile_ref"] = retry_result["profile"]
        final_sync_result = command([sys.executable, "tools/materialize_oc_core_1_3_3_v12_closure.py"], timeout=900)
        final_sync_result["profile"] = "v12_pre_profile_executor_materializer_sync"
        final_sync_result["capability_description"] = "Ensure profile executors evaluate the synchronized post-remediator artifact graph."
        final_sync_result["role"] = "shared_generated_surface_sync_before_profile_checks"
        results.append(class_remediation_result)
        results.append(final_sync_result)
    for profile in known_profiles:
        result = command([sys.executable, "tools/oc133_capability_repair_executor.py", "--profile", profile, "--work-order-file", str(WORK_ORDERS)], timeout=420)
        result["profile"] = profile
        result["capability_description"] = REPAIR_PROFILES[profile]
        result["profile_executor"] = "tools/oc133_capability_repair_executor.py"
        result["bootstrap_materializer_returncode"] = (integrated_result or {}).get("returncode")
        result["class_remediator_ref"] = "reviews/oc133_llm_cerberus/repair/OC133_VULNERABILITY_CLASS_REMEDIATION_LEDGER.json"
        results.append(result)
        for order in orders:
            if order.get("profile") == profile and order.get("status") == "QUEUED":
                order["status"] = "APPLIED" if result["returncode"] == 0 else "REPAIR_COMMAND_FAILED"
                order["repair_command_returncode"] = result["returncode"]
                order["profile_executor"] = "tools/oc133_capability_repair_executor.py"
                order["profile_verification_status"] = "PASS" if result["returncode"] == 0 else "FAIL"
                order["integrated_materializer_profile"] = "bootstrap_only"
                order["class_remediator_ref"] = "reviews/oc133_llm_cerberus/repair/OC133_VULNERABILITY_CLASS_REMEDIATION_LEDGER.json"
    for profile in unknown_profiles:
        result = {"cmd": [profile], "returncode": 99, "stdout_tail": "", "stderr_tail": "unknown repair profile", "profile": profile}
        results.append(result)
        for order in orders:
            if order.get("profile") == profile and order.get("status") == "QUEUED":
                order["status"] = "REPAIR_COMMAND_FAILED"
                order["repair_command_returncode"] = result["returncode"]
    return results


def focused_checks() -> list[dict[str, Any]]:
    return [
        command([sys.executable, "-m", "py_compile", "tools/materialize_oc_core_1_3_3_v12_closure.py", "proofs/finite_model_checks/run_finite_model_checks.py", "tools/oc133_autonomous_research_loop.py", "tools/oc133_capability_repair_executor.py", "tools/oc133_vulnerability_class_remediator.py"], timeout=120),
        command([sys.executable, "tools/oc133_vulnerability_class_remediator.py"], timeout=120),
        command([sys.executable, "proofs/finite_model_checks/run_finite_model_checks.py"], timeout=120),
        command(["lake", "build", "OC133V12"], timeout=600),
        command([sys.executable, "validation/run_all.py", "--qa-only"], timeout=240),
        command([sys.executable, "-m", "unittest", "release_machine.tests.test_release_machine.ReleaseMachineTests.test_oc133_scientific_closure_gates_are_no_send"], timeout=240),
        command([sys.executable, "-m", "release_machine", "evaluate", "--release", "oc_core_1_3_3", "--channel", "all", "--mode", "dry-run"], timeout=240),
    ]


def maybe_rerun_cerberus(args: argparse.Namespace) -> dict[str, Any] | None:
    if not args.rerun_cerberus:
        return None
    cmd = [
        sys.executable,
        "tools/run_oc133_v12_cerberus.py",
        "--max-workers",
        str(args.max_workers),
    ]
    if args.roles:
        cmd.extend(["--roles", args.roles])
    return command(cmd, timeout=args.cerberus_timeout)


def main() -> int:
    parser = argparse.ArgumentParser(description="OC Core 1.3.3 Cerberus finding -> autonomous repair loop.")
    parser.add_argument("--apply", action="store_true", help="Apply mapped repair profiles.")
    parser.add_argument("--checks", action="store_true", help="Run focused checks after repair.")
    parser.add_argument("--rerun-cerberus", action="store_true", help="Rerun Cerberus after repair.")
    parser.add_argument("--roles", default="", help="Comma-separated Cerberus roles for rerun; empty means all roles.")
    parser.add_argument("--max-workers", type=int, default=3, help="Parallel Cerberus workers for rerun.")
    parser.add_argument("--cerberus-timeout", type=int, default=7200, help="Overall Cerberus rerun timeout seconds.")
    args = parser.parse_args()

    REPAIR_DIR.mkdir(parents=True, exist_ok=True)
    write_json(TRIGGER_TABLE, trigger_payload())

    findings = open_findings()
    cerberus_orders = build_work_orders(findings)
    imported_director_orders = director_orders()
    orders = cerberus_orders + imported_director_orders
    director_packet = read_json(DIRECTOR_PACKET)
    write_json(
        WORK_ORDERS,
        {
            "schema_id": "OC133_CERBERUS_REPAIR_WORK_ORDERS_v1",
            "release_id": "oc_core_1_3_3",
            "version": "1.3.3",
            "open_finding_total": len(findings),
            "cerberus_order_total": len(cerberus_orders),
            "director_order_total": len(imported_director_orders),
            "director_packet_ref": rel(DIRECTOR_PACKET) if DIRECTOR_PACKET.exists() else None,
            "authority_chain": director_packet.get("authority", {}).get("authority_chain", []),
            "safety_gate": director_packet.get("safety_gate", {}),
            "blocked_unknown_repair_total": sum(1 for order in orders if order["status"].startswith("BLOCKED")),
            "orders": orders,
        },
    )

    profile_results: list[dict[str, Any]] = []
    check_results: list[dict[str, Any]] = []
    cerberus_result = None
    if args.apply and orders:
        profile_results = apply_profiles(orders)
        write_json(
            WORK_ORDERS,
            {
                "schema_id": "OC133_CERBERUS_REPAIR_WORK_ORDERS_v1",
                "release_id": "oc_core_1_3_3",
                "version": "1.3.3",
                "open_finding_total": len(findings),
                "cerberus_order_total": len(cerberus_orders),
                "director_order_total": len(imported_director_orders),
                "director_packet_ref": rel(DIRECTOR_PACKET) if DIRECTOR_PACKET.exists() else None,
                "authority_chain": director_packet.get("authority", {}).get("authority_chain", []),
                "safety_gate": director_packet.get("safety_gate", {}),
                "blocked_unknown_repair_total": sum(1 for order in orders if order["status"].startswith("BLOCKED")),
                "orders": orders,
            },
        )
    if args.checks:
        check_results = focused_checks()
    if args.rerun_cerberus:
        cerberus_result = maybe_rerun_cerberus(args)

    unknown_total = sum(1 for order in orders if order["status"].startswith("BLOCKED"))
    repair_fail_total = sum(1 for result in profile_results if result.get("returncode") != 0)
    check_fail_total = sum(1 for result in check_results if result.get("returncode") != 0)
    payload = {
        "schema_id": "OC133_AUTONOMOUS_RESEARCH_LOOP_LEDGER_v1",
        "release_id": "oc_core_1_3_3",
        "version": "1.3.3",
        "no_send": True,
        "open_finding_total_at_start": len(findings),
        "work_order_ref": rel(WORK_ORDERS),
        "trigger_table_ref": rel(TRIGGER_TABLE),
        "director_packet_ref": rel(DIRECTOR_PACKET) if DIRECTOR_PACKET.exists() else None,
        "director_work_orders_ref": rel(DIRECTOR_WORK_ORDERS) if DIRECTOR_WORK_ORDERS.exists() else None,
        "profile_execution_ledger_ref": rel(PROFILE_LEDGER) if PROFILE_LEDGER.exists() else None,
        "known_work_order_front_hash": sha256_text(json.dumps(orders, ensure_ascii=False, sort_keys=True)),
        "resource_policy": "Bootstrap shared generated surfaces once, then run narrow capability-specific executors and focused checks before widening to full Cerberus.",
        "cerberus_order_total": len(cerberus_orders),
        "director_order_total": len(imported_director_orders),
        "safety_gate": director_packet.get("safety_gate", {}),
        "profile_results": profile_results,
        "check_results": check_results,
        "cerberus_rerun_result": cerberus_result,
        "unknown_repair_total": unknown_total,
        "repair_fail_total": repair_fail_total,
        "check_fail_total": check_fail_total,
        "verdict": "PASS_AUTONOMOUS_REPAIR_APPLIED" if unknown_total == 0 and repair_fail_total == 0 and check_fail_total == 0 else "BLOCKED_AUTONOMOUS_REPAIR_INCOMPLETE",
    }
    write_json(RUN_LEDGER, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["verdict"] == "PASS_AUTONOMOUS_REPAIR_APPLIED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
