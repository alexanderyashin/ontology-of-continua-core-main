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
        "implementation_policy": "Execute through Logion capability worker; Codex may repair orchestration only if this work order cannot run.",
        "no_send": True,
    }


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


def content_closure_audit(root: Path) -> dict[str, Any]:
    claims = read_json(root / "claims" / "CLAIM_LEDGER_1_3_3.json")
    theorem_inventory = read_json(root / "proofs" / "THEOREM_INVENTORY_1_3_3.json")
    validation = read_json(root / "reports" / "OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.json")
    numeric = read_json(root / "validation" / "numeric_predictions" / "OC133_NUMERIC_PREDICTION_TABLE.json")
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
        and validation.get("domain_validation_promoted") is True
        and numeric.get("prediction_support_allowed_total", 0) > 0
        and numeric.get("unsupported_promoted_total", 0) == 0
    )
    novelty_ok = (
        (
            novelty.get("bounded_equivalence_search_status") == "COMPLETED_SOURCE_BACKED_RESIDUAL_DELTA"
            or novelty.get("systematic_priority_search_status") in {"COMPLETED_NO_EQUIVALENCE_FOUND", "COMPLETED_SOURCE_BACKED_RESIDUAL_DELTA"}
        )
        and novelty.get("unsupported_uniqueness_total", 1) == 0
    )
    phenomenon_ok = (
        phenomenon.get("phenomenon_coverage_row_total", 0) > 0
        and phenomenon.get("empirical_domain_phenomenon_coverage_total", 0) > 0
        and phenomenon.get("unsupported_closed_total", 1) == 0
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
            "prediction_support_allowed_total": numeric.get("prediction_support_allowed_total", 0),
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
            "blocker": "Phenomenon coverage is internal formal model cards, not broad domain phenomenon coverage.",
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
                "reports/OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.json",
                "claims/CLAIM_LEDGER_1_3_3.json",
            ],
            before_predicate="heldout_prediction_support_present=false and numeric replay rows are QA-only",
            after_predicate="formula, dataset snapshot, split policy, prediction, uncertainty, comparator, residuals, negative control, and falsifier are present for each promoted empirical claim",
            verification_command="python validation/run_all.py && python -m release_machine evaluate --release oc_core_1_3_3 --channel all --mode dry-run",
            closure_evidence_required=[
                "dataset manifest hashes",
                "train/test or target-blind replay logs",
                "numeric prediction table rows",
                "negative-control/falsifier outputs",
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


def write_mission_outputs(root: Path, audit: dict[str, Any] | None = None) -> dict[str, str]:
    audit = audit or content_closure_audit(root)
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
        "codex_role": "controller_auditor_orchestration_repair_only",
        "no_send": True,
        "owner_approval_required": True,
        "owner_approved": False,
        "publish_allowed": False,
        "journal_submissions_allowed": False,
        "content_closure_audit_ref": f"{MISSION_DIR_REL}/OC133_CONTENT_CLOSURE_SCORECARD.json",
        "dispatch_queue_ref": f"{MISSION_DIR_REL}/OC133_LOGION_LIVE_DISPATCH_QUEUE.json",
        "cockpit_ref": f"{MISSION_DIR_REL}/OC133_LOGION_RELEASE_COCKPIT.md",
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
    write_json(base / "OC_CORE_1_3_3_PLATINUM_RELEASE_MISSION.json", mission_packet)
    write_json(base / "OC133_CONTENT_CLOSURE_SCORECARD.json", audit)
    write_json(base / "OC133_LOGION_LIVE_DISPATCH_QUEUE.json", dispatch)
    write_json(base / "OC133_TRAJECTORY_CERTIFICATE_latest.json", trajectory)
    write_text(base / "OC133_LOGION_RELEASE_COCKPIT.md", render_cockpit(audit))
    return {
        "mission_ref": f"{MISSION_DIR_REL}/OC_CORE_1_3_3_PLATINUM_RELEASE_MISSION.json",
        "scorecard_ref": f"{MISSION_DIR_REL}/OC133_CONTENT_CLOSURE_SCORECARD.json",
        "dispatch_ref": f"{MISSION_DIR_REL}/OC133_LOGION_LIVE_DISPATCH_QUEUE.json",
        "cockpit_ref": f"{MISSION_DIR_REL}/OC133_LOGION_RELEASE_COCKPIT.md",
        "trajectory_ref": f"{MISSION_DIR_REL}/OC133_TRAJECTORY_CERTIFICATE_latest.json",
    }
