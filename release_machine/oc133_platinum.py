from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from .constants import TIMESTAMP


RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
MISSION_ID = "OC_CORE_1_3_3_PLATINUM_RELEASE_MISSION"
MISSION_DIR_REL = "operations/logion_release_mission/oc_core_1_3_3"
ALL_DOMAIN_STATE_RUNNING = "OC_CORE_1_3_3_ALL_DOMAIN_SCIENTIFIC_READINESS_RUNNING"
ALL_DOMAIN_READY_STATE = "ALL_DOMAIN_READY_NO_SEND"
REQUIRED_EMPIRICAL_DOMAINS = ("physics", "chemistry", "biology", "systems", "mathematics")
MODERN_SCIENCE_COMPARATOR_REGISTER_REL = "comparators/OC_1_3_3_MODERN_SCIENCE_SUPERIORITY_REGISTER.json"
GRAND_EMPIRICAL_REPORT_REL = "reports/OC_CORE_1_3_3_GRAND_EMPIRICAL_REPORT.json"
GRAND_TOE_FORMAL_OBLIGATION_LEDGER_REL = "claims/GRAND_TOE_FORMAL_OBLIGATION_LEDGER_1_3_3.json"
GRAND_PROMOTION_CONTRACT_REL = "proofs/grand_promotion/OC133_GRAND_PROMOTION_CONTRACT_REPORT.json"
GRAND_SCIENCE_CLAIM_CLASSES = (
    "numerically_proven_toe",
    "all_domain_numerical_prediction",
    "predicts_better_than_modern_science",
)
GRAND_SCIENCE_REQUESTED_AMBITION = (
    "numerically proven TOE across all domains and better than modern science"
)


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


def rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def sha256_object(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


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
        return {"status_available": False, "error": str(exc)}
    lines = completed.stdout.splitlines()
    dirty = [line for line in lines if line and not line.startswith("## ")]
    return {
        "status_available": completed.returncode == 0,
        "branch": lines[0] if lines else "",
        "dirty_total": len(dirty),
        "dirty_files": dirty[:80],
    }


def mission_dir(root: Path) -> Path:
    return root / MISSION_DIR_REL


def _state(ok: bool) -> str:
    return "PASS" if ok else "FAIL"


def _work_order(
    *,
    idx: int,
    capability: str,
    title: str,
    severity: str,
    artifacts: list[str],
    before_predicate: str,
    after_predicate: str,
    verification_command: str,
    closure_evidence_required: list[str],
    block_condition: str,
    dependency_ids: list[str] | None = None,
    dependency_blocker_ids: list[str] | None = None,
) -> dict[str, Any]:
    priority_base = {"CRITICAL": 1000, "HIGH": 700, "MEDIUM": 400, "LOW": 100}.get(severity, 400)
    return {
        "work_order_id": f"OC133-PLATINUM-WO-{idx:03d}",
        "mission_id": MISSION_ID,
        "owner_capability": capability,
        "title": title,
        "severity": severity,
        "priority": priority_base - idx,
        "owned_artifacts": artifacts,
        "before_predicate": before_predicate,
        "after_predicate": after_predicate,
        "verification_command": verification_command,
        "closure_evidence_required": closure_evidence_required,
        "rollback_or_block_condition": block_condition,
        "dependency_ids": dependency_ids or [],
        "dependency_blocker_ids": dependency_blocker_ids or [],
        "implementation_policy": "Execute through Logion capability worker; Codex may repair orchestration only if this work order cannot run.",
        "no_send": True,
    }


def _dependency_aware_work_order_sort(orders: list[dict[str, Any]], open_blocker_ids: set[str]) -> list[dict[str, Any]]:
    for row in orders:
        dependency_blocker_ids = [
            str(blocker_id)
            for blocker_id in row.get("dependency_blocker_ids", [])
            if str(blocker_id) in open_blocker_ids
        ]
        row["open_dependency_blocker_ids"] = dependency_blocker_ids
        row["blocked_by_open_dependency_total"] = len(dependency_blocker_ids)
    return sorted(
        orders,
        key=lambda row: (
            int(row.get("blocked_by_open_dependency_total", 0)) > 0,
            -int(row["priority"]),
            row["work_order_id"],
        ),
    )


def _journal_package_audit(root: Path) -> dict[str, Any]:
    base = root / "releases" / RELEASE_ID / "submission_packages"
    index = read_json(base / "SUBMISSION_PACKAGE_INDEX.json")
    rows = index.get("rows", []) if isinstance(index.get("rows"), list) else []
    required_files = {
        "SUBMISSION_PACKAGE.json",
        "REQUIRED_COMPONENT_MANIFEST.json",
        "REQUIRED_COMPONENT_MANIFEST.md",
        "COVER_LETTER_DRAFT.md",
        "CHECKLIST.md",
        "REPRODUCIBILITY_AND_DATA_STATEMENT.md",
        "AI_ASSISTANCE_DISCLOSURE.md",
        "CONFLICT_AND_FUNDING_STATEMENT.md",
        "VENUE_FIT_VERDICT.md",
    }
    missing: list[str] = []
    stale_refs: list[str] = []
    for row in rows:
        venue_id = str(row.get("venue_id", ""))
        d = base / venue_id
        for filename in required_files:
            if not (d / filename).exists():
                missing.append(f"{rel(root, d / filename)}")
        serialized = json.dumps(row, ensure_ascii=False)
        if "oc_core_1_3_2" in serialized or "1_3_2" in serialized or "1.3.2" in serialized:
            stale_refs.append(venue_id)
    status_counts = index.get("package_status_counts", {}) if isinstance(index.get("package_status_counts"), dict) else {}
    ok = (
        index.get("release_id") == RELEASE_ID
        and index.get("version") == VERSION
        and index.get("package_total") == 8
        and index.get("recommended_package_total") == 2
        and index.get("no_send") is True
        and index.get("submission_allowed") is False
        and index.get("journal_submissions_allowed") is False
        and not missing
        and not stale_refs
        and status_counts.get("OWNER_REVIEW_READY_NO_SEND", 0) == 8
    )
    return {
        "state": _state(ok),
        "index_ref": rel(root, base / "SUBMISSION_PACKAGE_INDEX.json"),
        "package_total": index.get("package_total", 0),
        "recommended_package_total": index.get("recommended_package_total", 0),
        "package_status_counts": status_counts,
        "missing_component_total": len(missing),
        "missing_components": missing[:40],
        "stale_132_ref_total": len(stale_refs),
        "stale_132_ref_venues": stale_refs[:20],
    }


def _package_surface_overclaim_audit(root: Path) -> dict[str, Any]:
    patterns = [
        "README.md",
        "reports/OC_CORE_1_3_3_*.md",
        "reports/OC_CORE_1_3_3_*.json",
        "releases/oc_core_1_3_3/**/*.md",
        "releases/oc_core_1_3_3/**/*.json",
        "claims/*1_3_3*.json",
        "docs/OC_1_3_3_*.md",
        "docs/OC_1_3_3_*.json",
    ]
    forbidden = {
        "theory of everything": "TOE-level claim",
        "irrefutable": "irrefutability claim",
        "final truth": "final-truth claim",
        "universal numerical prediction": "universal numerical prediction claim",
        "all-domain numerical prediction": "all-domain numerical prediction claim",
        "ready to submit": "send-readiness claim",
        "submission ready": "send-readiness claim",
        "ready for submission": "send-readiness claim",
    }
    allowed_context = (
        "not ",
        "no ",
        "false",
        "forbidden",
        "blocked",
        "no-send",
        "owner approval",
        "owner-review",
        "owner review",
        "required",
        "pending",
    )
    hits: list[dict[str, Any]] = []
    seen: set[Path] = set()
    for pattern in patterns:
        for path in root.glob(pattern):
            if not path.is_file() or path in seen or "__pycache__" in path.parts:
                continue
            seen.add(path)
            body = path.read_text(encoding="utf-8", errors="ignore")
            lower = body.lower()
            for phrase, reason in forbidden.items():
                start = 0
                while True:
                    idx = lower.find(phrase, start)
                    if idx < 0:
                        break
                    ctx = lower[max(0, idx - 120): idx + len(phrase) + 120].replace("\n", " ")
                    if not any(token in ctx for token in allowed_context):
                        hits.append({
                            "path": rel(root, path),
                            "phrase": phrase,
                            "reason": reason,
                            "context": ctx[:240],
                        })
                    start = idx + len(phrase)
    return {
        "state": _state(not hits),
        "hit_total": len(hits),
        "hits": hits[:40],
        "scan_policy": "Blocks unsupported TOE, all-domain prediction, irrefutability, final truth, and actual send-readiness claims unless context explicitly negates or owner-gates them.",
    }


def _all_domain_empirical_audit(root: Path) -> dict[str, Any]:
    target = read_json(root / "validation" / "target_blind" / "OC133_TARGET_BLIND_PREDICTION_TABLE.json")
    validation = read_json(root / "reports" / "OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.json")
    rows = target.get("rows", []) if isinstance(target.get("rows"), list) else []
    passed_domains = sorted({
        str(row.get("lane"))
        for row in rows
        if row.get("prediction_support_allowed") is True
        and row.get("empirical_support_allowed") is True
        and row.get("negative_control_rejected") is True
        and row.get("residual") is not None
        and row.get("uncertainty") is not None
        and row.get("comparator_residual") is not None
        and row.get("dataset_snapshot_ref")
        and (root / str(row.get("dataset_snapshot_ref"))).exists()
    })
    missing = [domain for domain in REQUIRED_EMPIRICAL_DOMAINS if domain not in passed_domains]
    row_field_failures = []
    required_fields = (
        "claim_id",
        "lane",
        "dataset_snapshot_ref",
        "target_blind_split",
        "formula",
        "predicted_value",
        "observed_value",
        "uncertainty",
        "comparator_baseline",
        "comparator_prediction",
        "residual",
        "comparator_residual",
        "negative_control",
        "negative_control_rejected",
        "falsifier",
        "snapshot_sha256",
        "replay_hash",
        "support_scope",
    )
    for row in rows:
        missing_fields = [field for field in required_fields if row.get(field) in {None, ""}]
        if missing_fields:
            row_field_failures.append({"claim_id": row.get("claim_id"), "missing_fields": missing_fields})
    ok = (
        not missing
        and not row_field_failures
        and target.get("generated_by") == "LOGION_CAPABILITY_WORKER"
        and target.get("capability_owner") == "Research/EmpiricalScience"
        and target.get("failure_total") == 0
        and validation.get("broad_domain_validation_promoted") is False
        and validation.get("domain_validation_promoted") is False
    )
    return {
        "state": _state(ok),
        "required_domains": list(REQUIRED_EMPIRICAL_DOMAINS),
        "passed_domains": passed_domains,
        "passed_domain_total": len(passed_domains),
        "missing_domains": missing,
        "missing_domain_total": len(missing),
        "target_blind_row_total": len(rows),
        "target_blind_failure_total": target.get("failure_total"),
        "target_blind_generated_by": target.get("generated_by"),
        "target_blind_capability_owner": target.get("capability_owner"),
        "row_field_failure_total": len(row_field_failures),
        "row_field_failures": row_field_failures[:20],
        "broad_domain_validation_promoted": validation.get("broad_domain_validation_promoted"),
        "domain_validation_promoted": validation.get("domain_validation_promoted"),
        "blocker": "All-domain readiness requires held-out or target-blind numeric evidence for every required domain. Partial target-blind support cannot certify all-domain readiness.",
    }


def _grand_science_toe_ambition_audit(
    root: Path,
    claims: dict[str, Any],
    theorem_inventory: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    validation = read_json(root / "reports" / "OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.json")
    target = read_json(root / "validation" / "target_blind" / "OC133_TARGET_BLIND_PREDICTION_TABLE.json")
    grand_empirical_report_path = root / GRAND_EMPIRICAL_REPORT_REL
    grand_empirical_report = read_json(grand_empirical_report_path)
    formal_obligation_layer_path = root / GRAND_TOE_FORMAL_OBLIGATION_LEDGER_REL
    formal_obligation_layer = read_json(formal_obligation_layer_path)
    promotion_contract_path = root / GRAND_PROMOTION_CONTRACT_REL
    promotion_contract = read_json(promotion_contract_path)
    comparator_register_path = root / MODERN_SCIENCE_COMPARATOR_REGISTER_REL
    comparator_register = read_json(comparator_register_path)
    claim_rows = claims.get("rows", []) if isinstance(claims.get("rows"), list) else []
    target_rows = target.get("rows", []) if isinstance(target.get("rows"), list) else []

    grand_tokens = (
        "theory of everything",
        "toe",
        "all-domain",
        "all domain",
        "across all domains",
        "modern science",
        "superior",
        "better than",
    )
    formal_tokens = ("theorem", "proof", "lean", "finite")
    promoted_grand_claims = []
    grand_claims_missing_formal_artifacts = []
    formal_blocker_claim_ids = []
    for row in claim_rows:
        row_text = json.dumps(row, ensure_ascii=False).lower()
        if not any(token in row_text for token in grand_tokens):
            continue
        if str(row.get("public_status", "")).upper() == "FORMAL_BLOCKER_NOT_PROMOTED_V12":
            formal_blocker_claim_ids.append(row.get("claim_id"))
            continue
        is_promoted = (
            row.get("scientific_promotion_allowed") is True
            and row.get("release_promotion_allowed") is True
            and "PROMOTED" in str(row.get("public_status", "")).upper()
        )
        supporting_refs = row.get("supporting_evidence_refs", [])
        if not isinstance(supporting_refs, list):
            supporting_refs = []
        has_formal_evidence = (
            any(token in str(row.get("support", "")).lower() for token in formal_tokens)
            and (
                any(token in str(row.get("evidence_ref", "")).lower() for token in formal_tokens)
                or any(any(token in str(ref).lower() for token in formal_tokens) for ref in supporting_refs)
            )
        )
        if is_promoted and has_formal_evidence:
            promoted_grand_claims.append(row.get("claim_id"))
        elif is_promoted or any(token in row_text for token in ("numerically proven", "predicts better", "all-domain")):
            grand_claims_missing_formal_artifacts.append(row.get("claim_id"))

    per_domain_superiority: dict[str, dict[str, Any]] = {}
    for row in target_rows:
        domain = str(row.get("lane"))
        if domain not in REQUIRED_EMPIRICAL_DOMAINS:
            continue
        try:
            residual = float(row.get("residual"))
            comparator_residual = float(row.get("comparator_residual"))
            uncertainty = float(row.get("uncertainty"))
        except (TypeError, ValueError):
            residual = comparator_residual = uncertainty = float("nan")
        target_blind_or_heldout = bool(row.get("target_blind_split") or row.get("heldout_split") or row.get("heldout_policy"))
        beats_comparator = comparator_residual > residual
        within_uncertainty = residual <= uncertainty
        grand_claim_support_allowed = (
            row.get("grand_toe_support_allowed") is True
            or row.get("broad_domain_validation_support_allowed") is True
            or row.get("modern_science_superiority_support_allowed") is True
        )
        per_domain_superiority[domain] = {
            "claim_id": row.get("claim_id"),
            "target_blind_or_heldout": target_blind_or_heldout,
            "prediction_support_allowed": row.get("prediction_support_allowed") is True,
            "empirical_support_allowed": row.get("empirical_support_allowed") is True,
            "grand_claim_support_allowed": grand_claim_support_allowed,
            "comparator_baseline_present": bool(row.get("comparator_baseline")),
            "residual": row.get("residual"),
            "uncertainty": row.get("uncertainty"),
            "comparator_residual": row.get("comparator_residual"),
            "beats_comparator": beats_comparator,
            "within_uncertainty": within_uncertainty,
            "support_scope": row.get("support_scope"),
            "passes_strict_predictive_superiority": (
                target_blind_or_heldout
                and row.get("prediction_support_allowed") is True
                and row.get("empirical_support_allowed") is True
                and grand_claim_support_allowed
                and bool(row.get("comparator_baseline"))
                and beats_comparator
                and within_uncertainty
                and row.get("negative_control_rejected") is True
            ),
        }
    missing_superiority_domains = [
        domain
        for domain in REQUIRED_EMPIRICAL_DOMAINS
        if not per_domain_superiority.get(domain, {}).get("passes_strict_predictive_superiority")
    ]
    grand_empirical_domains = (
        grand_empirical_report.get("domains", [])
        if isinstance(grand_empirical_report.get("domains"), list)
        else []
    )
    grand_empirical_domain_results = {
        str(row.get("domain")): row
        for row in grand_empirical_domains
        if isinstance(row, dict) and row.get("domain")
    }
    grand_empirical_supported_domains = sorted(
        domain
        for domain, row in grand_empirical_domain_results.items()
        if row.get("grand_toe_support_allowed") is True
        and str(row.get("status", "")).upper() != "BLOCKED"
    )
    missing_grand_empirical_domains = [
        domain
        for domain in REQUIRED_EMPIRICAL_DOMAINS
        if domain not in grand_empirical_supported_domains
    ]
    grand_empirical_ok = (
        grand_empirical_report_path.exists()
        and grand_empirical_report.get("release_id") == RELEASE_ID
        and grand_empirical_report.get("grand_toe_support_allowed") is True
        and int(grand_empirical_report.get("blocked_domain_total", 1) or 0) == 0
        and all(domain in grand_empirical_supported_domains for domain in REQUIRED_EMPIRICAL_DOMAINS)
    )

    comparator_rows = comparator_register.get("rows", []) if isinstance(comparator_register.get("rows"), list) else []
    certified_domains = sorted({
        str(row.get("domain"))
        for row in comparator_rows
        if (
            row.get("superiority_certified") is True
            or str(row.get("superiority_claim_status", "")).upper() in {"CERTIFIED", "SUPERIORITY_CERTIFIED"}
        )
        and (row.get("modern_science_comparator_present") is True or row.get("source_refs"))
        and (row.get("benchmark_ref") or row.get("benchmark_predicate_ref"))
        and (row.get("oc_result_ref") or row.get("oc_result_refs") or row.get("oc_current_evidence_refs"))
        and (row.get("comparator_result_ref") or row.get("comparator_result_refs") or row.get("source_refs"))
    })
    comparator_blocked_total = int(comparator_register.get("blocked_superiority_total", 1) or 0)
    comparator_certified_total = int(comparator_register.get("superiority_certified_total", 0) or 0)
    comparator_failure_total = int(comparator_register.get("failure_total", 0) or 0)
    comparator_claim_allowed = (
        comparator_register.get("superiority_claim_allowed") is True
        or comparator_register.get("release_promotion_allowed") is True
        or str(comparator_register.get("current_release_state", "")).upper() in {
            "CERTIFIED_MODERN_SCIENCE_SUPERIORITY",
            "SUPERIORITY_CERTIFIED",
        }
    )
    comparator_ok = (
        comparator_register_path.exists()
        and comparator_register.get("release_id") == RELEASE_ID
        and comparator_claim_allowed
        and comparator_failure_total == 0
        and comparator_blocked_total == 0
        and comparator_certified_total >= len(REQUIRED_EMPIRICAL_DOMAINS)
        and all(domain in certified_domains for domain in REQUIRED_EMPIRICAL_DOMAINS)
    )

    promotion_contract_ok = (
        promotion_contract_path.exists()
        and promotion_contract.get("release_id") == RELEASE_ID
        and promotion_contract.get("promotion_allowed") is True
        and str(promotion_contract.get("verdict", "")).upper() in {"PASS", "PROMOTION_ALLOWED"}
        and not promotion_contract.get("open_blockers")
        and not promotion_contract.get("failed_gate_predicates")
    )
    claim_ledger_ok = (
        claims.get("release_promotion_allowed") is True
        and claims.get("unsupported_promoted_total") == 0
        and bool(promoted_grand_claims)
        and theorem_inventory.get("machine_checked_subset_total") == theorem_inventory.get("theorem_total")
        and theorem_inventory.get("scientific_promotion_allowed_total", 0) > 0
        and promotion_contract_ok
    )
    empirical_superiority_ok = not missing_superiority_domains and grand_empirical_ok
    stronger_evidence_ok = claim_ledger_ok and empirical_superiority_ok and comparator_ok
    broad_promoted = validation.get("broad_domain_validation_promoted") is True
    broad_guard_ok = broad_promoted is False or stronger_evidence_ok
    formal_layer_machine_nonpromotion = (
        formal_obligation_layer_path.exists()
        and formal_obligation_layer.get("blocker_id") == "grand_toe_claim_ledger_evidence"
        and formal_obligation_layer.get("state") == "CURRENT_ARTIFACT_CLASS_CANNOT_PROMOTE"
        and formal_obligation_layer.get("machine_proved_nonpromotion") is True
        and formal_obligation_layer.get("release_promotion_allowed") is False
    )

    return {
        "grand_toe_claim_ledger_evidence": {
            "state": _state(claim_ledger_ok),
            "requested_claim_classes": list(GRAND_SCIENCE_CLAIM_CLASSES),
            "requested_ambition_level": GRAND_SCIENCE_REQUESTED_AMBITION,
            "release_promotion_allowed": claims.get("release_promotion_allowed"),
            "promoted_grand_claim_ids": promoted_grand_claims,
            "promoted_grand_claim_total": len(promoted_grand_claims),
            "grand_claims_missing_formal_artifacts": grand_claims_missing_formal_artifacts[:20],
            "formal_blocker_claim_ids": formal_blocker_claim_ids,
            "formal_obligation_layer_ref": GRAND_TOE_FORMAL_OBLIGATION_LEDGER_REL,
            "formal_obligation_layer_exists": formal_obligation_layer_path.exists(),
            "formal_obligation_layer_state": formal_obligation_layer.get("state"),
            "machine_proved_nonpromotion": formal_layer_machine_nonpromotion,
            "grand_promotion_contract_ref": GRAND_PROMOTION_CONTRACT_REL,
            "grand_promotion_contract_exists": promotion_contract_path.exists(),
            "grand_promotion_contract_verdict": promotion_contract.get("verdict"),
            "grand_promotion_contract_allowed": promotion_contract.get("promotion_allowed"),
            "grand_promotion_contract_open_blockers": promotion_contract.get("open_blockers", []),
            "grand_promotion_contract_failed_gate_predicates": promotion_contract.get("failed_gate_predicates", []),
            "machine_proof_refs": formal_obligation_layer.get("machine_proof_refs", {}),
            "formal_gate_vector": formal_obligation_layer.get("formal_gate_vector", {}),
            "failed_gate_predicates": formal_obligation_layer.get("failed_gate_predicates", []),
            "work_order_decomposition": formal_obligation_layer.get("work_order_decomposition", []),
            "theorem_total": theorem_inventory.get("theorem_total"),
            "machine_checked_subset_total": theorem_inventory.get("machine_checked_subset_total"),
            "scientific_promotion_allowed_total": theorem_inventory.get("scientific_promotion_allowed_total"),
            "required_evidence_layer": "Dedicated promoted TOE/all-domain claim row with theorem/proof/Lean/finite evidence refs; bounded theorem rows and the formal non-promotion blocker do not satisfy grand-claim promotion by themselves.",
            "blocker": (
                "TOE/all-domain promotion requires a dedicated promoted claim-ledger row bound to theorem, proof, Lean, and finite evidence. "
                "The current artifact class is machine-proved non-promotable when the formal obligation layer reports CURRENT_ARTIFACT_CLASS_CANNOT_PROMOTE."
            ),
        },
        "grand_toe_empirical_superiority": {
            "state": _state(empirical_superiority_ok),
            "requested_ambition_level": GRAND_SCIENCE_REQUESTED_AMBITION,
            "required_domains": list(REQUIRED_EMPIRICAL_DOMAINS),
            "strict_domain_results": per_domain_superiority,
            "missing_or_not_superior_domains": missing_superiority_domains,
            "grand_empirical_report_ref": GRAND_EMPIRICAL_REPORT_REL,
            "grand_empirical_report_exists": grand_empirical_report_path.exists(),
            "grand_empirical_verdict": grand_empirical_report.get("verdict"),
            "grand_empirical_blocked_domain_total": grand_empirical_report.get("blocked_domain_total"),
            "grand_empirical_evidence_pack_total": grand_empirical_report.get("evidence_pack_total"),
            "grand_empirical_supported_domains": grand_empirical_supported_domains,
            "grand_empirical_missing_domains": missing_grand_empirical_domains,
            "grand_empirical_domain_results": grand_empirical_domain_results,
            "bounded_target_blind_rows_visible_not_final": len(target_rows),
            "target_blind_generated_by": target.get("generated_by"),
            "target_blind_capability_owner": target.get("capability_owner"),
            "blocker": "Grand all-domain claims require target-blind or held-out predictive evidence that beats a comparator baseline in every required domain; mere artifact existence is not enough.",
            "required_evidence_layer": "Each per-domain empirical row must explicitly set grand_toe_support_allowed after target-blind/held-out scoring beats the comparator, and the strict grand empirical report must clear every required domain.",
        },
        "modern_science_comparator_superiority": {
            "state": _state(comparator_ok),
            "requested_ambition_level": GRAND_SCIENCE_REQUESTED_AMBITION,
            "register_ref": MODERN_SCIENCE_COMPARATOR_REGISTER_REL,
            "register_exists": comparator_register_path.exists(),
            "schema_id": comparator_register.get("schema_id"),
            "claim_classes": comparator_register.get("claim_classes"),
            "current_release_state": comparator_register.get("current_release_state"),
            "superiority_claim_allowed": comparator_claim_allowed,
            "failure_total": comparator_failure_total,
            "superiority_certified_total": comparator_certified_total,
            "blocked_superiority_total": comparator_blocked_total,
            "certified_domains": certified_domains,
            "missing_certified_domains": [domain for domain in REQUIRED_EMPIRICAL_DOMAINS if domain not in certified_domains],
            "blocker": "Claims that OC predicts better than modern science require a modern-science comparator/benchmark register certifying superiority for every required domain.",
        },
        "broad_domain_validation_promotion_guard": {
            "state": _state(broad_guard_ok),
            "broad_domain_validation_promoted": validation.get("broad_domain_validation_promoted"),
            "stronger_grand_science_evidence_exists": stronger_evidence_ok,
            "stronger_evidence_components": {
                "claim_ledger": claim_ledger_ok,
                "empirical_superiority": empirical_superiority_ok,
                "modern_science_comparator": comparator_ok,
            },
            "bounded_readiness_data_visible_not_final": True,
            "blocker": "broad_domain_validation_promoted may be true only after the strict grand-science evidence layer passes.",
        },
    }


def _journal_send_readiness_audit(root: Path, journal: dict[str, Any]) -> dict[str, Any]:
    base = root / "releases" / RELEASE_ID / "submission_packages"
    index = read_json(base / "SUBMISSION_PACKAGE_INDEX.json")
    rows = index.get("rows", []) if isinstance(index.get("rows"), list) else []
    bad_send_unlocks = []
    for row in rows:
        venue_id = row.get("venue_id")
        if row.get("submission_allowed") is not False or row.get("journal_submissions_allowed") is not False:
            bad_send_unlocks.append(venue_id)
    ok = (
        journal.get("state") == "PASS"
        and index.get("submission_allowed") is False
        and index.get("journal_submissions_allowed") is False
        and not bad_send_unlocks
    )
    return {
        "state": _state(ok),
        "owner_review_package_ready": journal.get("state") == "PASS",
        "send_allowed_now": False,
        "submission_allowed": index.get("submission_allowed"),
        "journal_submissions_allowed": index.get("journal_submissions_allowed"),
        "bad_send_unlock_total": len(bad_send_unlocks),
        "bad_send_unlock_venues": bad_send_unlocks,
        "package_total": journal.get("package_total", 0),
        "recommended_package_total": journal.get("recommended_package_total", 0),
        "blocker": "Journal packages may be owner-review-ready, but actual send readiness remains locked until owner approval and scientific all-domain evidence pass.",
    }


def all_domain_readiness_audit(root: Path, base_audit: dict[str, Any] | None = None) -> dict[str, Any]:
    base_audit = base_audit or {}
    journal = _journal_package_audit(root)
    empirical = _all_domain_empirical_audit(root)
    overclaim = _package_surface_overclaim_audit(root)
    journal_send = _journal_send_readiness_audit(root, journal)
    claims = read_json(root / "claims" / "CLAIM_LEDGER_1_3_3.json")
    cerberus = read_json(root / "reviews" / "oc133_llm_cerberus" / "OC133_LLM_CERBERUS_SUMMARY.json")
    theorem_inventory = read_json(root / "proofs" / "THEOREM_INVENTORY_1_3_3.json")
    grand_science = _grand_science_toe_ambition_audit(root, claims, theorem_inventory)
    theorem_ok = (
        claims.get("unsupported_promoted_total") == 0
        and theorem_inventory.get("machine_checked_subset_total") == theorem_inventory.get("theorem_total")
        and theorem_inventory.get("scientific_promotion_allowed_total", 0) > 0
    )
    cerberus_ok = (
        cerberus.get("critical_open_total", 1) == 0
        and cerberus.get("high_open_total", 1) == 0
        and cerberus.get("parse_failure_total", 1) == 0
        and cerberus.get("execution_bad_total", 1) == 0
    )
    checks = {
        "all_domain_empirical_predictions": empirical,
        "claim_boundary_no_overclaim": overclaim,
        "journal_owner_review_packages": journal,
        "journal_send_readiness_minus_owner_lock": journal_send,
        "formal_theorem_evidence": {
            "state": _state(theorem_ok),
            "theorem_total": theorem_inventory.get("theorem_total"),
            "machine_checked_subset_total": theorem_inventory.get("machine_checked_subset_total"),
            "scientific_promotion_allowed_total": theorem_inventory.get("scientific_promotion_allowed_total"),
            "unsupported_promoted_total": claims.get("unsupported_promoted_total"),
        },
        "cerberus_critical_high": {
            "state": _state(cerberus_ok),
            "critical_open_total": cerberus.get("critical_open_total"),
            "high_open_total": cerberus.get("high_open_total"),
            "parse_failure_total": cerberus.get("parse_failure_total"),
            "execution_bad_total": cerberus.get("execution_bad_total"),
        },
    }
    checks.update(grand_science)
    blockers = {key: row for key, row in checks.items() if row.get("state") != "PASS"}
    if "journal_owner_review_packages" in blockers or "journal_send_readiness_minus_owner_lock" in blockers:
        final_state = "JOURNAL_PACKAGE_REPAIR_REQUIRED"
    elif blockers:
        final_state = "SCIENTIFIC_BLOCKERS_REMAIN"
    else:
        final_state = ALL_DOMAIN_READY_STATE
    work_orders = build_all_domain_work_orders(blockers)
    return {
        "schema_id": "OC133_ALL_DOMAIN_SCIENTIFIC_READINESS_AUDIT_v1",
        "mission_id": MISSION_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": TIMESTAMP,
        "state": ALL_DOMAIN_READY_STATE if not blockers else ALL_DOMAIN_STATE_RUNNING,
        "final_readiness_state": final_state,
        "all_domain_ready_no_send": not blockers,
        "bounded_all_domain_readiness_visible_not_final": True,
        "bounded_all_domain_ready_no_send": empirical.get("state") == "PASS",
        "blocker_total": len(blockers),
        "blocker_ids": list(blockers),
        "checks": checks,
        "work_order_total": len(work_orders),
        "work_order_queue_sha256": sha256_object(work_orders),
        "next_automatic_action": work_orders[0]["work_order_id"] if work_orders else "OWNER_REVIEW_NO_SEND",
        "base_content_closure_state": base_audit.get("state"),
        "base_content_closure_blocker_total": base_audit.get("blocker_total"),
        "no_send": True,
        "publish_allowed": False,
        "journal_submissions_allowed": False,
        "work_orders": work_orders,
    }


def content_closure_audit(root: Path) -> dict[str, Any]:
    claims = read_json(root / "claims" / "CLAIM_LEDGER_1_3_3.json")
    theorem_inventory = read_json(root / "proofs" / "THEOREM_INVENTORY_1_3_3.json")
    validation = read_json(root / "reports" / "OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.json")
    target_blind = read_json(root / "validation" / "target_blind" / "OC133_TARGET_BLIND_PREDICTION_TABLE.json")
    numeric = target_blind or read_json(root / "validation" / "numeric_predictions" / "OC133_NUMERIC_PREDICTION_TABLE.json")
    novelty = read_json(root / "comparators" / "OC_1_3_3_NOVELTY_AND_PRIORITY_REGISTER.json")
    phenomenon = read_json(root / "docs" / "OC_1_3_3_PHENOMENON_COVERAGE_MATRIX.json")
    cerberus = read_json(root / "reviews" / "oc133_llm_cerberus" / "OC133_LLM_CERBERUS_SUMMARY.json")
    journal = _journal_package_audit(root)

    theorem_ok = (
        theorem_inventory.get("scientific_promotion_allowed_total", 0) > 0
        and theorem_inventory.get("formal_consistency_check_total", 0) < theorem_inventory.get("theorem_total", 0)
        and claims.get("scientific_promotion_allowed_total", 0) > 0
        and claims.get("formal_consistency_limited_claim_total", 0) < claims.get("claim_total", 0)
    )
    empirical_ok = (
        validation.get("heldout_prediction_support_present") is True
        and validation.get("target_blind_bounded_reconstruction_support_present") is True
        and validation.get("broad_domain_validation_promoted") is False
        and validation.get("domain_validation_support_allowed") is False
        and numeric.get("prediction_support_allowed_total", 0) > 0
        and numeric.get("failure_total", 0) == 0
        and numeric.get("unsupported_promoted_total", 0) == 0
        and target_blind.get("generated_by") == "LOGION_CAPABILITY_WORKER"
        and target_blind.get("capability_owner") == "Research/EmpiricalScience"
        and target_blind.get("closure_predicates", {}).get("all_rows_have_formula_snapshot_split_uncertainty_comparator_residual_negative_control_falsifier") is True
        and target_blind.get("closure_predicates", {}).get("scope_is_bounded_not_domain_validation") is True
    )
    novelty_ok = (
        (
            novelty.get("bounded_equivalence_search_status") == "COMPLETED_SOURCE_BACKED_RESIDUAL_DELTA"
            or novelty.get("systematic_priority_search_status") in {"COMPLETED_NO_EQUIVALENCE_FOUND", "COMPLETED_SOURCE_BACKED_RESIDUAL_DELTA"}
        )
        and novelty.get("unsupported_uniqueness_total", 1) == 0
    )
    phenomenon_ok = (
        (
            phenomenon.get("phenomenon_coverage_row_total", 0) > 0
            or phenomenon.get("formal_model_card_replay_total", 0) >= 10
        )
        and phenomenon.get("unsupported_closed_total", 1) == 0
        and phenomenon.get("matrix_role") == "INTERNAL_NO_SEND_MODEL_CARD_GAP_REGISTER_NOT_DOMAIN_PHENOMENON_COVERAGE"
    )
    cerberus_ok = (
        cerberus.get("critical_open_total", 1) == 0
        and cerberus.get("high_open_total", 1) == 0
        and cerberus.get("parse_failure_total", 1) == 0
        and cerberus.get("execution_bad_total", 1) == 0
    )

    checks = {
        "theorem_promotion": {
            "state": _state(theorem_ok),
            "public_promoted_theorem_total": theorem_inventory.get("public_promoted_theorem_total", 0),
            "scientific_promotion_allowed_total": theorem_inventory.get("scientific_promotion_allowed_total", 0),
            "formal_consistency_check_total": theorem_inventory.get("formal_consistency_check_total", 0),
            "claim_scientific_promotion_allowed_total": claims.get("scientific_promotion_allowed_total", 0),
            "claim_formal_consistency_limited_total": claims.get("formal_consistency_limited_claim_total", 0),
            "blocker": "Current theorem/claim surface is release-consistency only, not promoted scientific theorem support.",
        },
        "empirical_prediction_promotion": {
            "state": _state(empirical_ok),
            "heldout_prediction_support_present": validation.get("heldout_prediction_support_present", False),
            "domain_validation_promoted": validation.get("domain_validation_promoted", False),
            "broad_domain_validation_promoted": validation.get("broad_domain_validation_promoted"),
            "target_blind_bounded_reconstruction_support_present": validation.get("target_blind_bounded_reconstruction_support_present"),
            "prediction_support_allowed_total": numeric.get("prediction_support_allowed_total", 0),
            "target_blind_prediction_support_allowed_total": validation.get("target_blind_prediction_support_allowed_total", 0),
            "target_blind_generated_by": target_blind.get("generated_by"),
            "target_blind_capability_owner": target_blind.get("capability_owner"),
            "target_blind_required_predicates_ok": target_blind.get("closure_predicates", {}).get("all_rows_have_formula_snapshot_split_uncertainty_comparator_residual_negative_control_falsifier"),
            "validation_verdict": validation.get("verdict"),
            "blocker": "Current numeric lanes are QA replay quarantine, not held-out or target-blind empirical prediction evidence.",
        },
        "novelty_equivalence_closure": {
            "state": _state(novelty_ok),
            "bounded_equivalence_search_status": novelty.get("bounded_equivalence_search_status", "MISSING"),
            "systematic_priority_search_status": novelty.get("systematic_priority_search_status", "MISSING"),
            "unsupported_uniqueness_total": novelty.get("unsupported_uniqueness_total", 0),
            "blocker": "Comparator register is positioning-only until bounded equivalence or systematic priority/equivalence search is completed.",
        },
        "phenomenon_coverage": {
            "state": _state(phenomenon_ok),
            "phenomenon_coverage_row_total": phenomenon.get("phenomenon_coverage_row_total", 0),
            "empirical_domain_phenomenon_coverage_total": phenomenon.get("empirical_domain_phenomenon_coverage_total", 0),
            "formal_model_card_replay_total": phenomenon.get("formal_model_card_replay_total", 0),
            "blocker": "Phenomenon coverage is insufficient only when scoped model cards are missing, unsupported rows are closed, or broad domain coverage is promoted without empirical support.",
        },
        "journal_submission_packages": journal,
        "cerberus_critical_high": {
            "state": _state(cerberus_ok),
            "critical_open_total": cerberus.get("critical_open_total"),
            "high_open_total": cerberus.get("high_open_total"),
            "parse_failure_total": cerberus.get("parse_failure_total"),
            "execution_bad_total": cerberus.get("execution_bad_total"),
        },
        "no_send_governance": {
            "state": "PASS",
            "owner_approved": False,
            "publish_allowed": False,
            "journal_submissions_allowed": False,
        },
    }
    blocker_checks = {key: row for key, row in checks.items() if row.get("state") != "PASS"}
    work_orders = build_work_orders(blocker_checks)
    queue_hash = sha256_object(work_orders)
    return {
        "schema_id": "OC133_PLATINUM_CONTENT_CLOSURE_AUDIT_v1",
        "mission_id": MISSION_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": TIMESTAMP,
        "state": "PASS" if not blocker_checks else "SCIENTIFIC_CONTENT_CLOSURE_RUNNING",
        "platinum_ready_no_send": not blocker_checks,
        "blocker_total": len(blocker_checks),
        "blocker_ids": list(blocker_checks),
        "checks": checks,
        "work_order_total": len(work_orders),
        "work_order_queue_sha256": queue_hash,
        "next_automatic_action": work_orders[0]["work_order_id"] if work_orders else "OWNER_REVIEW_NO_SEND",
        "no_send": True,
        "publish_allowed": False,
        "journal_submissions_allowed": False,
        "work_orders": work_orders,
    }


def build_work_orders(blocker_checks: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    orders: list[dict[str, Any]] = []
    idx = 1
    if "theorem_promotion" in blocker_checks:
        orders.append(_work_order(
            idx=idx,
            capability="Research/FormalScience",
            title="Promote real theorem claims beyond release-consistency checks",
            severity="CRITICAL",
            artifacts=[
                "formal/lean/OC133V12.lean",
                "proofs/THEOREM_INVENTORY_1_3_3.json",
                "proofs/proof_sheets/*.md",
                "claims/CLAIM_LEDGER_1_3_3.json",
            ],
            before_predicate="public_promoted_theorem_total == 0 or scientific_promotion_allowed_total == 0",
            after_predicate="at least one load-bearing theorem has independent assumptions, proof chain, Lean/finite binding, falsifier boundary, and scientific_promotion_allowed=true",
            verification_command="lake build OC133V12 && python proofs/finite_model_checks/run_finite_model_checks.py && python -m release_machine evaluate --release oc_core_1_3_3 --channel all --mode dry-run",
            closure_evidence_required=[
                "Lean theorem IDs",
                "proof sheet IDs",
                "finite-model case IDs",
                "claim ledger promoted row IDs",
            ],
            block_condition="If no theorem can honestly be promoted, keep release in SCIENTIFIC_CONTENT_CLOSURE_RUNNING.",
        ))
        idx += 1
    if "empirical_prediction_promotion" in blocker_checks:
        orders.append(_work_order(
            idx=idx,
            capability="Research/EmpiricalScience",
            title="Build held-out or target-blind numeric prediction lanes",
            severity="CRITICAL",
            artifacts=[
                "validation/numeric_predictions/",
                "validation/target_blind/",
                "reports/OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.json",
                "claims/CLAIM_LEDGER_1_3_3.json",
            ],
            before_predicate="heldout_prediction_support_present=false and numeric replay rows are QA-only",
            after_predicate="formula, dataset snapshot, split policy, prediction, uncertainty, comparator, residuals, negative control, and falsifier are present for each promoted empirical claim",
            verification_command="python tools/oc133_logion_release_mission.py --execute-next --write",
            closure_evidence_required=[
                "dataset manifest hashes",
                "train/test or target-blind replay logs",
                "numeric prediction table rows",
                "negative-control/falsifier outputs",
                "Logion capability execution ledger row",
            ],
            block_condition="If official-data prediction cannot close, empirical claims remain unpromoted and platinum readiness stays blocked.",
        ))
        idx += 1
    if "novelty_equivalence_closure" in blocker_checks:
        orders.append(_work_order(
            idx=idx,
            capability="Research/PriorArt",
            title="Complete source-backed novelty and equivalence attack closure",
            severity="HIGH",
            artifacts=[
                "comparators/OC_1_3_3_NOVELTY_AND_PRIORITY_REGISTER.json",
                "docs/OC_1_3_3_PRIOR_ART_COMPARATOR_MATRIX.json",
                "claims/CLAIM_LEDGER_1_3_3.json",
            ],
            before_predicate="systematic_priority_search_status is positioning-only",
            after_predicate="source-backed systematic search protocol either supports a bounded residual-delta claim or demotes uniqueness/priority claims",
            verification_command="python -m release_machine evaluate --release oc_core_1_3_3 --channel all --mode dry-run",
            closure_evidence_required=[
                "source-backed comparator rows",
                "search protocol refs",
                "overlap/residual-delta verdicts",
                "claim-boundary corrections",
            ],
            block_condition="If search cannot support novelty, novelty claims stay positioning-only and release remains scientifically blocked.",
        ))
        idx += 1
    if "phenomenon_coverage" in blocker_checks:
        orders.append(_work_order(
            idx=idx,
            capability="Research/Phenomenology",
            title="Replace internal model-card illustrations with promoted phenomenon coverage or explicit blockers",
            severity="HIGH",
            artifacts=[
                "docs/OC_1_3_3_PHENOMENON_COVERAGE_MATRIX.json",
                "docs/OC_1_3_3_HOSTILE_READER_GUIDE.md",
                "claims/CLAIM_LEDGER_1_3_3.json",
            ],
            before_predicate="phenomenon_coverage_row_total == 0 and empirical_domain_phenomenon_coverage_total == 0",
            after_predicate="each promoted phenomenon has OC instance, observable, prediction/replay path, comparator, negative control, falsifier, and honest status",
            verification_command="python -m release_machine evaluate --release oc_core_1_3_3 --channel all --mode dry-run",
            closure_evidence_required=[
                "phenomenon model-card IDs",
                "prediction/replay outputs",
                "comparator refs",
                "falsifier refs",
            ],
            block_condition="Unsupported phenomena remain blockers, not PASS rows.",
        ))
        idx += 1
    if "journal_submission_packages" in blocker_checks:
        orders.append(_work_order(
            idx=idx,
            capability="Publication/JournalPackages",
            title="Generate material 1.3.3 journal submission packages under no-send lock",
            severity="HIGH",
            artifacts=[
                "releases/oc_core_1_3_3/submission_packages/",
                "release_machine/publication.py",
            ],
            before_predicate="1.3.3 submission package index missing/incomplete/stale",
            after_predicate="8 venue packages exist with manifests, cover letters, reproducibility/data statements, conflict/funding, AI disclosure, venue-fit verdict, and NO_SEND locks",
            verification_command="python -m release_machine submission-packages --release-id oc_core_1_3_3",
            closure_evidence_required=[
                "SUBMISSION_PACKAGE_INDEX.json",
                "venue REQUIRED_COMPONENT_MANIFEST.json files",
                "NO_SEND/OWNER_APPROVAL_REQUIRED fields",
            ],
            block_condition="No journal submission or public action may occur; package generation is local owner-review material only.",
        ))
        idx += 1
    if "cerberus_critical_high" in blocker_checks:
        orders.append(_work_order(
            idx=idx,
            capability="Review/Cerberus",
            title="Rerun Logion Cerberus through standard LLM bridge until critical/high closure is fresh",
            severity="CRITICAL",
            artifacts=["reviews/oc133_llm_cerberus/", "tools/run_oc133_v12_cerberus.py"],
            before_predicate="critical/high/parse/execution failures are nonzero",
            after_predicate="critical_open_total=0, high_open_total=0, parse_failure_total=0, execution_bad_total=0",
            verification_command="python tools/run_oc133_v12_cerberus.py --max-workers 4",
            closure_evidence_required=["structured Cerberus JSON role outputs", "OC133_LLM_CERBERUS_SUMMARY.json"],
            block_condition="Stale, failed, or unparsable LLM output cannot close G58 or platinum readiness.",
        ))
    return sorted(orders, key=lambda row: (-int(row["priority"]), row["work_order_id"]))


def build_all_domain_work_orders(blocker_checks: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    orders: list[dict[str, Any]] = []
    idx = 1
    if "grand_toe_claim_ledger_evidence" in blocker_checks:
        orders.append(_work_order(
            idx=idx,
            capability="Research/FormalScience",
            title="Prove or demote grand TOE/all-domain claim promotion",
            severity="CRITICAL",
            artifacts=[
                "claims/CLAIM_LEDGER_1_3_3.json",
                GRAND_TOE_FORMAL_OBLIGATION_LEDGER_REL,
                "proofs/THEOREM_INVENTORY_1_3_3.json",
                "proofs/proof_sheets/",
                "formal/lean/",
                "proofs/FINITE_MODEL_CHECKS_1_3_3.json",
                "tools/oc133_grand_toe_formal_obligations.py",
            ],
            before_predicate="no dedicated promoted TOE/all-domain claim-ledger row with theorem/proof/Lean/finite evidence, or formal obligation layer rejects current artifact class",
            after_predicate="any TOE/all-domain promoted claim has explicit claim-ledger row, theorem/proof/Lean/finite evidence refs, unsupported_promoted_total=0, and release_promotion_allowed=true",
            verification_command="lake build OC133V12 && python proofs/finite_model_checks/run_finite_model_checks.py && python tools/oc133_logion_all_domain_readiness.py --write --allow-blocked-exit-zero",
            closure_evidence_required=[
                "dedicated grand-claim ledger row ID",
                "theorem inventory IDs",
                "Lean theorem IDs",
                "proof sheet refs",
                "finite-model witness case IDs",
                "or, if not closable, formal non-promotion proof refs and work-order decomposition",
            ],
            block_condition="If this evidence cannot honestly be produced, keep TOE/all-domain claims demoted and final readiness in SCIENTIFIC_BLOCKERS_REMAIN.",
            dependency_blocker_ids=[
                "grand_toe_empirical_superiority",
                "modern_science_comparator_superiority",
            ],
        ))
        idx += 1
    if "grand_toe_empirical_superiority" in blocker_checks:
        row = blocker_checks["grand_toe_empirical_superiority"]
        orders.append(_work_order(
            idx=idx,
            capability="Research/EmpiricalScience",
            title="Replace bounded rows with strict per-domain predictive superiority evidence",
            severity="CRITICAL",
            artifacts=[
                "validation/target_blind/",
                "validation/heldout/",
                "reports/OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.json",
                "claims/CLAIM_LEDGER_1_3_3.json",
            ],
            before_predicate=f"missing_or_not_superior_domains == {row.get('missing_or_not_superior_domains', [])}",
            after_predicate="each required empirical domain has target-blind or held-out prediction evidence, uncertainty, falsifier, negative control, and numeric residual strictly better than comparator residual",
            verification_command="python tools/oc133_logion_all_domain_readiness.py --execute-next --write --allow-blocked-exit-zero",
            closure_evidence_required=[
                "per-domain target-blind or held-out prediction rows",
                "dataset snapshot refs and hashes",
                "OC residual and comparator residual calculations",
                "negative-control/falsifier outputs",
                "Logion capability execution ledger row",
            ],
            block_condition="If any required domain lacks genuine predictive superiority, keep bounded readiness visible but not final for grand TOE claims.",
        ))
        idx += 1
    if "modern_science_comparator_superiority" in blocker_checks:
        orders.append(_work_order(
            idx=idx,
            capability="Research/PriorArt",
            title="Create modern-science comparator superiority register",
            severity="CRITICAL",
            artifacts=[
                MODERN_SCIENCE_COMPARATOR_REGISTER_REL,
                "comparators/",
                "benchmarks/",
                "claims/CLAIM_LEDGER_1_3_3.json",
            ],
            before_predicate="modern-science comparator register missing or not certifying superiority across required domains",
            after_predicate="register exists for grand claim classes and certifies OC superiority against modern-science comparator benchmarks for every required empirical domain",
            verification_command="python tools/oc133_logion_all_domain_readiness.py --write --allow-blocked-exit-zero",
            closure_evidence_required=[
                "modern-science comparator/benchmark register",
                "per-domain benchmark refs",
                "OC result refs",
                "modern-science comparator result refs",
                "superiority certification verdicts",
            ],
            block_condition="If superiority over modern science is not certified, remove or demote superiority claims and keep final readiness scientifically blocked.",
        ))
        idx += 1
    if "all_domain_empirical_predictions" in blocker_checks:
        row = blocker_checks["all_domain_empirical_predictions"]
        orders.append(_work_order(
            idx=idx,
            capability="Research/EmpiricalScience",
            title="Close all-domain held-out or target-blind numeric prediction evidence",
            severity="CRITICAL",
            artifacts=[
                "validation/target_blind/",
                "reports/OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.json",
                "operations/logion_release_mission/oc_core_1_3_3/OC133_ALL_DOMAIN_READINESS_SCORECARD.json",
            ],
            before_predicate=f"missing_domains == {row.get('missing_domains', [])}",
            after_predicate="each required domain has formula, pinned snapshot, split policy, numeric prediction, uncertainty, comparator, residual, negative control, falsifier, and replay hash",
            verification_command="python tools/oc133_logion_all_domain_readiness.py --execute-next --write --allow-blocked-exit-zero",
            closure_evidence_required=[
                "per-domain target-blind or held-out prediction rows",
                "dataset snapshot refs and hashes",
                "negative-control/falsifier outputs",
                "Logion capability execution ledger row",
            ],
            block_condition="If a domain cannot honestly close, keep ALL_DOMAIN_SCIENTIFIC_READINESS_RUNNING and do not claim TOE/all-domain prediction readiness.",
        ))
        idx += 1
    if "claim_boundary_no_overclaim" in blocker_checks:
        orders.append(_work_order(
            idx=idx,
            capability="Review/ClaimBoundary",
            title="Remove or block unsupported TOE/all-domain/send-readiness overclaims",
            severity="CRITICAL",
            artifacts=[
                "README.md",
                "reports/OC_CORE_1_3_3_*.md",
                "releases/oc_core_1_3_3/submission_packages/",
                "claims/CLAIM_LEDGER_1_3_3.json",
            ],
            before_predicate="overclaim hit_total > 0",
            after_predicate="no unsupported TOE, irrefutable, final-truth, all-domain prediction, or send-readiness wording appears outside explicit negation/owner-gated context",
            verification_command="python tools/oc133_logion_all_domain_readiness.py --write --allow-blocked-exit-zero",
            closure_evidence_required=["overclaim scan hit_total=0", "claim-boundary correction refs"],
            block_condition="Unsupported ambitious claims remain blockers until proven or removed from promoted surfaces.",
        ))
        idx += 1
    if "journal_owner_review_packages" in blocker_checks or "journal_send_readiness_minus_owner_lock" in blocker_checks:
        orders.append(_work_order(
            idx=idx,
            capability="Publication/JournalPackages",
            title="Verify journal package completeness without unlocking submission",
            severity="HIGH",
            artifacts=["releases/oc_core_1_3_3/submission_packages/"],
            before_predicate="package missing, stale, overclaiming, or submission_allowed not false",
            after_predicate="8 complete owner-review no-send packages exist; actual submission remains locked by owner approval and scientific all-domain gates",
            verification_command="python tools/oc133_logion_all_domain_readiness.py --write --allow-blocked-exit-zero",
            closure_evidence_required=["SUBMISSION_PACKAGE_INDEX.json", "venue manifests", "NO_SEND/OWNER_APPROVAL_REQUIRED fields"],
            block_condition="No journal package may claim actual send readiness while owner approval is pending.",
        ))
    return _dependency_aware_work_order_sort(orders, set(blocker_checks))


def render_cockpit(audit: dict[str, Any]) -> str:
    lines = [
        "# OC Core 1.3.3 Platinum Release Mission Cockpit",
        "",
        f"Mission: `{MISSION_ID}`",
        f"State: `{audit['state']}`",
        f"Platinum ready no-send: `{str(audit['platinum_ready_no_send']).lower()}`",
        f"Blockers: `{audit['blocker_total']}`",
        f"Next automatic action: `{audit['next_automatic_action']}`",
        "Public action allowed: `false`",
        "Journal submissions allowed: `false`",
        "",
        "## Capability Checks",
        "",
        "| Check | State | Key Counter |",
        "| --- | --- | --- |",
    ]
    for key, row in audit["checks"].items():
        counter = ""
        for candidate in (
            "public_promoted_theorem_total",
            "heldout_prediction_support_present",
            "systematic_priority_search_status",
            "phenomenon_coverage_row_total",
            "package_total",
            "critical_open_total",
        ):
            if candidate in row:
                counter = f"`{candidate}={row[candidate]}`"
                break
        lines.append(f"| `{key}` | `{row.get('state')}` | {counter} |")
    lines.extend(["", "## Active Work Orders", ""])
    if not audit["work_orders"]:
        lines.append("- none")
    for row in audit["work_orders"]:
        lines.append(f"- `{row['work_order_id']}` `{row['owner_capability']}` `{row['severity']}`: {row['title']}")
        lines.append(f"  Verification: `{row['verification_command']}`")
    return "\n".join(lines) + "\n"


def render_all_domain_cockpit(audit: dict[str, Any]) -> str:
    empirical = audit["checks"].get("all_domain_empirical_predictions", {})
    journal = audit["checks"].get("journal_owner_review_packages", {})
    lines = [
        "# OC Core 1.3.3 All-Domain Scientific Readiness Cockpit",
        "",
        f"Mission: `{MISSION_ID}`",
        f"State: `{audit['state']}`",
        f"Final readiness state: `{audit['final_readiness_state']}`",
        f"All-domain ready no-send: `{str(audit['all_domain_ready_no_send']).lower()}`",
        f"Blockers: `{audit['blocker_total']}`",
        f"Next automatic action: `{audit['next_automatic_action']}`",
        "Public action allowed: `false`",
        "Journal submissions allowed: `false`",
        "",
        "## Counters",
        "",
        f"- Required empirical domains: `{len(REQUIRED_EMPIRICAL_DOMAINS)}`",
        f"- Passed empirical domains: `{empirical.get('passed_domain_total', 0)}`",
        f"- Missing empirical domains: `{empirical.get('missing_domain_total', 0)}`",
        f"- Journal owner-review packages: `{journal.get('package_total', 0)}`",
        "",
        "## Capability Checks",
        "",
        "| Check | State | Key Counter |",
        "| --- | --- | --- |",
    ]
    for key, row in audit["checks"].items():
        counter = ""
        for candidate in (
            "missing_domain_total",
            "hit_total",
            "package_total",
            "bad_send_unlock_total",
            "theorem_total",
            "critical_open_total",
        ):
            if candidate in row:
                counter = f"`{candidate}={row[candidate]}`"
                break
        lines.append(f"| `{key}` | `{row.get('state')}` | {counter} |")
    lines.extend(["", "## Active Work Orders", ""])
    if not audit["work_orders"]:
        lines.append("- none")
    for row in audit["work_orders"]:
        lines.append(f"- `{row['work_order_id']}` `{row['owner_capability']}` `{row['severity']}`: {row['title']}")
        lines.append(f"  Verification: `{row['verification_command']}`")
    return "\n".join(lines) + "\n"


def write_mission_outputs(root: Path, audit: dict[str, Any] | None = None) -> dict[str, str]:
    audit = audit or content_closure_audit(root)
    all_domain_audit = all_domain_readiness_audit(root, audit)
    base = mission_dir(root)
    mission_packet = {
        "schema_id": "OC133_PLATINUM_RELEASE_MISSION_CONTRACT_v1",
        "mission_id": MISSION_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": TIMESTAMP,
        "authority_chain": [
            "Safety Directive",
            "LOGI corporate director",
            "K6 Strategy HQ",
            "Subordinate Institute Director",
            "Research/IT/Publication/Review capability workers",
        ],
        "mission_state": audit["state"],
        "all_domain_scientific_readiness_state": all_domain_audit["state"],
        "final_readiness_state": all_domain_audit["final_readiness_state"],
        "codex_role": "controller_auditor_orchestration_repair_only",
        "no_send": True,
        "owner_approval_required": True,
        "owner_approved": False,
        "publish_allowed": False,
        "journal_submissions_allowed": False,
        "content_closure_audit_ref": f"{MISSION_DIR_REL}/OC133_CONTENT_CLOSURE_SCORECARD.json",
        "all_domain_readiness_audit_ref": f"{MISSION_DIR_REL}/OC133_ALL_DOMAIN_READINESS_SCORECARD.json",
        "dispatch_queue_ref": f"{MISSION_DIR_REL}/OC133_LOGION_LIVE_DISPATCH_QUEUE.json",
        "all_domain_dispatch_queue_ref": f"{MISSION_DIR_REL}/OC133_ALL_DOMAIN_WORK_ORDERS.json",
        "cockpit_ref": f"{MISSION_DIR_REL}/OC133_LOGION_RELEASE_COCKPIT.md",
        "all_domain_cockpit_ref": f"{MISSION_DIR_REL}/OC133_ALL_DOMAIN_READINESS_COCKPIT.md",
        "historical_intent_preflight_policy": "Run/reuse K6 historical-intent preflight before creating duplicate factory/factory-of-factories infrastructure; extend existing Logion capabilities where possible.",
    }
    dispatch = {
        "schema_id": "OC133_LOGION_LIVE_DISPATCH_QUEUE_v1",
        "mission_id": MISSION_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": TIMESTAMP,
        "queue_sha256": audit["work_order_queue_sha256"],
        "state": "ACTIVE" if audit["work_orders"] else "EMPTY_OWNER_REVIEW_NO_SEND",
        "ordering_policy": "safety/no-send, severity, gate unblock value, dependency unblock value, stable work_order_id",
        "work_order_total": audit["work_order_total"],
        "rows": audit["work_orders"],
    }
    trajectory = {
        "schema_id": "OC133_LOGION_TRAJECTORY_CERTIFICATE_v1",
        "mission_id": MISSION_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": TIMESTAMP,
        "known_blocker_hash": sha256_object(audit["blocker_ids"]),
        "queue_hash": audit["work_order_queue_sha256"],
        "selected_next_action": audit["next_automatic_action"],
        "optimality_claim": "Deterministic priority optimum over the known finite blocker queue and current no-send compute policy; not an omniscient proof over unknown future findings.",
        "resource_policy": "Prefer existing Logion capability executors and generated audits before manual artifact edits.",
        "git_status_policy": "Full dirty-file listing is intentionally excluded from this certificate to avoid self-referential staging drift; use external git status for closeout.",
        "no_send": True,
    }
    all_domain_dispatch = {
        "schema_id": "OC133_ALL_DOMAIN_WORK_ORDERS_v1",
        "mission_id": MISSION_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": TIMESTAMP,
        "queue_sha256": all_domain_audit["work_order_queue_sha256"],
        "state": "ACTIVE" if all_domain_audit["work_orders"] else "EMPTY_OWNER_REVIEW_NO_SEND",
        "ordering_policy": "safety/no-send, all-domain evidence blocker, claim-boundary blocker, journal-package blocker, stable work_order_id",
        "work_order_total": all_domain_audit["work_order_total"],
        "rows": all_domain_audit["work_orders"],
    }
    write_json(base / "OC_CORE_1_3_3_PLATINUM_RELEASE_MISSION.json", mission_packet)
    write_json(base / "OC133_CONTENT_CLOSURE_SCORECARD.json", audit)
    write_json(base / "OC133_ALL_DOMAIN_READINESS_SCORECARD.json", all_domain_audit)
    write_json(base / "OC133_LOGION_LIVE_DISPATCH_QUEUE.json", dispatch)
    write_json(base / "OC133_ALL_DOMAIN_WORK_ORDERS.json", all_domain_dispatch)
    write_json(base / "OC133_TRAJECTORY_CERTIFICATE_latest.json", trajectory)
    write_text(base / "OC133_LOGION_RELEASE_COCKPIT.md", render_cockpit(audit))
    write_text(base / "OC133_ALL_DOMAIN_READINESS_COCKPIT.md", render_all_domain_cockpit(all_domain_audit))
    return {
        "mission_ref": f"{MISSION_DIR_REL}/OC_CORE_1_3_3_PLATINUM_RELEASE_MISSION.json",
        "scorecard_ref": f"{MISSION_DIR_REL}/OC133_CONTENT_CLOSURE_SCORECARD.json",
        "all_domain_scorecard_ref": f"{MISSION_DIR_REL}/OC133_ALL_DOMAIN_READINESS_SCORECARD.json",
        "dispatch_ref": f"{MISSION_DIR_REL}/OC133_LOGION_LIVE_DISPATCH_QUEUE.json",
        "all_domain_dispatch_ref": f"{MISSION_DIR_REL}/OC133_ALL_DOMAIN_WORK_ORDERS.json",
        "cockpit_ref": f"{MISSION_DIR_REL}/OC133_LOGION_RELEASE_COCKPIT.md",
        "all_domain_cockpit_ref": f"{MISSION_DIR_REL}/OC133_ALL_DOMAIN_READINESS_COCKPIT.md",
        "trajectory_ref": f"{MISSION_DIR_REL}/OC133_TRAJECTORY_CERTIFICATE_latest.json",
    }
