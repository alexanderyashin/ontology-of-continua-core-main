from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
WORK_ROOT = ROOT.parents[2]
PRIVATE_ROOT = WORK_ROOT / "estra-private-work"
DIRECTOR_DIR = ROOT / "operations" / "institute_director" / "oc_core_1_3_3"
DIRECTOR_PACKET = DIRECTOR_DIR / "OC133_INSTITUTE_DIRECTOR_PACKET.json"
DIRECTOR_COCKPIT = DIRECTOR_DIR / "OC133_INSTITUTE_DIRECTOR_COCKPIT.md"
DIRECTOR_WORK_ORDERS = DIRECTOR_DIR / "OC133_INSTITUTE_DIRECTOR_WORK_ORDERS.json"
DIRECTOR_LEDGER = DIRECTOR_DIR / "OC133_INSTITUTE_DIRECTOR_CYCLE_LEDGER.json"
ALL_DOMAIN_SCORECARD = ROOT / "operations" / "logion_release_mission" / "oc_core_1_3_3" / "OC133_ALL_DOMAIN_READINESS_SCORECARD.json"
ALL_DOMAIN_WORK_ORDERS = ROOT / "operations" / "logion_release_mission" / "oc_core_1_3_3" / "OC133_ALL_DOMAIN_WORK_ORDERS.json"


AUTHORITY_REFS = {
    "strategy_hq_authority": "logion/k7/spe/state/strategy/STRATEGY_HQ_AUTHORITY_latest.json",
    "strategic_order": "logion/k7/spe/state/strategy/STRATEGIC_ORDER_latest.json",
    "science_loop_state": "logion/k7/spe/state/strategy/SCIENCE_LOOP_STATE_latest.json",
    "research_master_plan": "logion/k7/spe/state/strategy/RESEARCH_MASTER_PLAN_latest.json",
    "ordering_authority": "logion/k7/roles/strategy_hq/STRATEGY_HQ_ORDERING_AUTHORITY_v1.md",
}


SAFETY_DIRECTIVE = {
    "directive_id": "OC133_SAFETY_DIRECTIVE_NO_SEND",
    "rank": 0,
    "rules": [
        "No push, public release, Zenodo, GitHub release, Software Heritage deposit, DOI minting, email, or journal submission.",
        "No release PASS may be minted from artifact existence, status tokens, or unsupported LLM closure text.",
        "Critical/high Cerberus findings are blockers until repaired by exact artifact changes or explicit public-claim boundary corrections.",
        "Private Strategy HQ/K6 surfaces are authority inputs by default; this director writes only public-repo telemetry unless export is explicitly requested.",
        "Ambitious claims may remain research targets, but promoted release claims must match proof/data/simulation evidence.",
    ],
}


@dataclass(frozen=True)
class RepairCapability:
    capability_id: str
    rank: int
    root_tokens: tuple[str, ...]
    repair_kind: str
    owned_artifacts: tuple[str, ...]
    repair_contract: str


CAPABILITIES = (
    RepairCapability(
        "formal_lifecycle_morphism_repair",
        10,
        ("omega", "lifecycle", "residueof", "rebirthof", "morphismevidence", "live status", "death"),
        "FORMAL_AND_FINITE_REPAIR",
        ("formal/lean/OC133V12.lean", "proofs/FINITE_MODEL_CHECKS_1_3_3.json", "claims/CLAIM_LEDGER_1_3_3.json"),
        "Tie lifecycle residue/rebirth source-target relations to morphism evidence, or rewrite promoted claim to exact supported scope.",
    ),
    RepairCapability(
        "identity_truth_table_repair",
        11,
        ("identity", "rebirth", "residue", "unless", "invariant", "truth table"),
        "FINITE_TRUTH_TABLE_AND_CLAIM_BOUNDARY",
        ("proofs/finite_model_checks/OC133_FINITE_MODEL_INPUTS.json", "proofs/FINITE_MODEL_CHECKS_1_3_3.json", "proofs/proof_sheets/T133-ID.md"),
        "Generate exhaustive morphism_class x invariant_preserved x claimed_identity_continuation cases and align wording: identity requires identity class plus invariant preservation.",
    ),
    RepairCapability(
        "hybrid_operator_semantics_repair",
        12,
        ("hybrid", "differential", "ode", "smooth", "derivative", "guard", "reset"),
        "FORMAL_REPAIR_OR_SCOPE_CORRECTION",
        ("formal/lean/OC133V12.lean", "content/OC_1_3_3_OPERATOR_SEMANTICS.tex", "proofs/FINITE_MODEL_CHECKS_1_3_3.json"),
        "Either formalize stronger smooth/hybrid semantics or downgrade public wording to typed update plus optional chart and guard/reset routing.",
    ),
    RepairCapability(
        "klevel_non_circular_semantics_repair",
        13,
        ("klevel", "k-level", "k11_to_k12", "civilizational", "irreducibility", "atlas", "booleans", "registry consistency"),
        "SEMANTIC_EVALUATOR_OR_SCOPE_CORRECTION",
        ("data/k_level_irreducibility_matrix.json", "formal/lean/OC133V12.lean", "docs/OC_1_3_3_PHENOMENON_COVERAGE_MATRIX.json"),
        "Replace absolute-sounding K-level language with bounded classifier/atlas language unless independent per-axis semantics are added.",
    ),
    RepairCapability(
        "numeric_replay_leakage_repair",
        14,
        ("gdp", "heldout", "prediction", "uncertainty", "target", "numeric", "replay log"),
        "EMPIRICAL_REPLAY_REWRITE",
        ("validation/numeric_predictions/OC133_NUMERIC_PREDICTION_TABLE.json", "validation/numeric_predictions/OC133_NUMERIC_REPLAY_LOG.json"),
        "Remove prediction/heldout/falsifier-threshold language from retrospective replay rows or implement target-blind train-only replay.",
    ),
    RepairCapability(
        "phenomenon_coverage_repair",
        15,
        ("phenomenon", "p008", "p009", "p010", "p011", "p012", "coverage", "model card", "does not explain"),
        "COVERAGE_MODEL_CARD_REPAIR",
        ("docs/OC_1_3_3_PHENOMENON_COVERAGE_MATRIX.json", "docs/OC_1_3_3_HOSTILE_READER_GUIDE.md"),
        "Separate scoped formal illustrations from real phenomenon closure; route no-send through manifest/approval, not a missing Lean theorem.",
    ),
    RepairCapability(
        "public_surface_no_send_repair",
        16,
        ("no-send", "nosend", "owner approval", "publish", "zenodo", "github", "software heritage", "doi", "journal"),
        "CONTROL_PLANE_PARITY_REPAIR",
        ("releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_PUBLISH_MANIFEST_DRAFT.json", "proofs/FINITE_MODEL_CHECKS_1_3_3.json"),
        "Model both reject and hypothetical approve states with every public channel gate explicit; no-send remains locked in current release.",
    ),
    RepairCapability(
        "attack_matrix_reopen_recompute_repair",
        17,
        ("attack matrix", "critical_unresolved_total", "high_unresolved_total", "closed_by_specific", "theater", "non-responsive"),
        "REOPEN_RECOMPUTE",
        ("review/OC_1_3_3_TOTAL_ATTACK_MATRIX.json", "reviews/OC_CORE_1_3_3_REVIEWER_RESPONSE_MATRIX.json"),
        "Rows must remain OPEN until the exact attacked artifact is repaired; unresolved totals must be computed from row status.",
    ),
    RepairCapability(
        "cerberus_timeout_context_repair",
        18,
        ("timeout", "exceeded timeout", "stale prior", "codex", "exec"),
        "LLM_REVIEW_INFRA_REPAIR",
        ("tools/run_oc133_v12_cerberus.py", "reviews/oc133_llm_cerberus/results"),
        "Rerun timeout roles with smaller context bundles or longer per-role timeout; stale JSON may not certify G58.",
    ),
    RepairCapability(
        "grand_formal_toe_research",
        1,
        ("grand", "toe", "all-domain", "proof", "lean", "finite", "claim-ledger"),
        "GRAND_FORMAL_RESEARCH_PROGRAM",
        ("claims/CLAIM_LEDGER_1_3_3.json", "proofs/THEOREM_INVENTORY_1_3_3.json", "formal/lean/OC133V12.lean"),
        "Create or reject the dedicated grand TOE/all-domain theorem obligation. This capability may not close by artifact existence.",
    ),
    RepairCapability(
        "grand_empirical_superiority_research",
        2,
        ("grand", "superiority", "target-blind", "held-out", "residual", "comparator", "all-domain"),
        "GRAND_EMPIRICAL_RESEARCH_PROGRAM",
        ("validation/target_blind", "validation/heldout", "reports/OC_CORE_1_3_3_DOMAIN_VALIDATION_REPORT.json"),
        "Produce strict per-domain predictive superiority evidence or keep broad empirical promotion blocked.",
    ),
    RepairCapability(
        "modern_science_comparator_research",
        3,
        ("modern science", "comparator", "benchmark", "superiority", "prior-art"),
        "MODERN_SCIENCE_COMPARATOR_PROGRAM",
        ("comparators/OC_1_3_3_MODERN_SCIENCE_SUPERIORITY_REGISTER.json", "benchmarks", "claims/CLAIM_LEDGER_1_3_3.json"),
        "Build source-backed modern-science comparator benchmarks before any superiority claim can be promoted.",
    ),
)


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        try:
            return path.resolve().relative_to(WORK_ROOT.resolve()).as_posix()
        except ValueError:
            return path.name


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def command(cmd: list[str], timeout: int) -> dict[str, Any]:
    started = time.time()
    completed = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=timeout)
    return {
        "cmd": cmd,
        "returncode": completed.returncode,
        "duration_seconds": round(time.time() - started, 3),
        "stdout_tail": completed.stdout[-4000:],
        "stderr_tail": completed.stderr[-4000:],
    }


def authority_snapshot() -> dict[str, Any]:
    refs = {}
    for key, rel_ref in AUTHORITY_REFS.items():
        path = PRIVATE_ROOT / rel_ref
        if path.suffix.lower() == ".json":
            payload = read_json(path)
            status = payload.get("status")
            executive_superior = payload.get("executive_superior_id")
            command_seat = payload.get("command_seat")
        else:
            payload = {"text_head": path.read_text(encoding="utf-8", errors="ignore")[:1000]} if path.exists() else {}
            status = "PRESENT" if path.exists() else "MISSING"
            executive_superior = None
            command_seat = None
        refs[key] = {
            "ref": rel_ref,
            "present": path.exists(),
            "sha256": sha256_file(path),
            "status": status,
            "executive_superior_id": executive_superior,
            "command_seat": command_seat,
            "summary": payload.get("summary", {}),
            "cycle_targets": payload.get("cycle_targets", []),
            "selected_executive_priority": payload.get("selected_executive_priority"),
        }
    strategy = refs.get("strategy_hq_authority", {})
    order = refs.get("strategic_order", {})
    return {
        "schema_id": "OC133_AUTHORITY_SNAPSHOT_v1",
        "authority_chain": [
            {"rank": 0, "authority_id": "SAFETY_DIRECTIVE", "source": "local no-send scientific safety directive"},
            {"rank": 1, "authority_id": "LOGI", "source": "corporate executive superior declared by Strategy HQ authority"},
            {"rank": 2, "authority_id": "K6_STRATEGY_HQ", "source": "Strategy HQ / command seat K6"},
            {"rank": 3, "authority_id": "OC133_INSTITUTE_DIRECTOR", "source": "subordinate scientific director for this release only"},
            {"rank": 4, "authority_id": "CAPABILITY_WORKERS", "source": "research, review, repair, release-machine, publication-governor capabilities"},
        ],
        "strategy_hq_authority_pass": strategy.get("status") == "PASS",
        "corporate_director_id": strategy.get("executive_superior_id") or "LOGI",
        "command_seat": order.get("command_seat") or "K6",
        "zero_external_actions_ordered": "PRESERVE_ZERO_EXTERNAL_ACTIONS_UNTIL_OWNER_RELEASE" in order.get("cycle_targets", []),
        "refs": refs,
    }


def cerberus_findings() -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    result_dir = ROOT / "reviews" / "oc133_llm_cerberus" / "results"
    for path in sorted(result_dir.glob("*.json")):
        payload = read_json(path)
        role = payload.get("role", path.stem)
        for row in payload.get("findings", []):
            severity = str(row.get("severity", "")).upper()
            status = str(row.get("status", "OPEN")).upper()
            if severity in {"CRITICAL", "HIGH"} and status not in {"CLOSED", "RESOLVED", "CLOSED_BY_V12_EVIDENCE"}:
                item = dict(row)
                item["role"] = role
                item["result_ref"] = rel(path)
                findings.append(item)
    return findings


def capability_for_finding(finding: dict[str, Any]) -> tuple[RepairCapability, int]:
    haystack = "\n".join(str(finding.get(key, "")) for key in ("claim", "artifact_ref", "failure_mode", "required_repair")).lower()
    ranked: list[tuple[int, RepairCapability]] = []
    for capability in CAPABILITIES:
        score = sum(1 for token in capability.root_tokens if token in haystack)
        ranked.append((score, capability))
    ranked.sort(key=lambda item: (item[0], -item[1].rank), reverse=True)
    score, capability = ranked[0]
    if score == 0:
        return next(cap for cap in CAPABILITIES if cap.capability_id == "attack_matrix_reopen_recompute_repair"), 0
    return capability, score


def build_director_work_orders(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    orders = []
    for idx, finding in enumerate(findings, start=1):
        capability, score = capability_for_finding(finding)
        severity = str(finding.get("severity", "HIGH")).upper()
        orders.append(
            {
                "work_order_id": f"OC133-DIRECTOR-WO-{idx:03d}",
                "source": "cerberus_open_finding",
                "role": finding.get("role"),
                "severity": severity,
                "priority": 1000 if severity == "CRITICAL" else 700,
                "capability_id": capability.capability_id,
                "capability_rank": capability.rank,
                "capability_score": score,
                "repair_kind": capability.repair_kind,
                "owned_artifacts": list(capability.owned_artifacts),
                "repair_contract": capability.repair_contract,
                "artifact_ref": finding.get("artifact_ref"),
                "claim": finding.get("claim"),
                "failure_mode": finding.get("failure_mode"),
                "required_repair": finding.get("required_repair"),
                "director_decision": "REPAIR_REQUIRED_BEFORE_RELEASE",
                "release_gate_effect": "G58_AND_G70_BLOCKED",
            }
        )
    orders.sort(key=lambda row: (-row["priority"], row["capability_rank"], row["work_order_id"]))
    return orders


def all_domain_science_work_orders() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    scorecard = read_json(ALL_DOMAIN_SCORECARD)
    queue = read_json(ALL_DOMAIN_WORK_ORDERS)
    rows = queue.get("rows", []) if isinstance(queue.get("rows"), list) else []
    capability_map = {
        "Research/FormalScience": "grand_formal_toe_research",
        "Research/EmpiricalScience": "grand_empirical_superiority_research",
        "Research/PriorArt": "modern_science_comparator_research",
    }
    normalized: list[dict[str, Any]] = []
    for idx, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            continue
        owner = str(row.get("owner_capability", ""))
        capability_id = capability_map.get(owner, "attack_matrix_reopen_recompute_repair")
        cap = next((item for item in CAPABILITIES if item.capability_id == capability_id), CAPABILITIES[0])
        normalized.append(
            {
                "work_order_id": f"OC133-DIRECTOR-GRAND-WO-{idx:03d}",
                "source": "all_domain_grand_science_blocker",
                "severity": row.get("severity", "CRITICAL"),
                "priority": row.get("priority", 900),
                "capability_id": capability_id,
                "capability_rank": cap.rank,
                "capability_score": 999,
                "repair_kind": cap.repair_kind,
                "owned_artifacts": row.get("owned_artifacts", list(cap.owned_artifacts)),
                "repair_contract": row.get("rollback_or_block_condition", cap.repair_contract),
                "artifact_ref": ",".join(row.get("owned_artifacts", [])) if isinstance(row.get("owned_artifacts"), list) else "",
                "claim": row.get("title"),
                "failure_mode": row.get("before_predicate"),
                "required_repair": row.get("after_predicate"),
                "verification_command": row.get("verification_command"),
                "closure_evidence_required": row.get("closure_evidence_required", []),
                "director_decision": "GRAND_SCIENCE_RESEARCH_REQUIRED_BEFORE_FINAL_RELEASE",
                "release_gate_effect": "ALL_DOMAIN_FINAL_READINESS_AND_G70_BLOCKED",
                "source_work_order_id": row.get("work_order_id"),
                "no_send": True,
            }
        )
    normalized.sort(key=lambda row: (-int(row["priority"]), row["capability_rank"], row["work_order_id"]))
    return scorecard, normalized


def gate_director(authority: dict[str, Any]) -> dict[str, Any]:
    failures = []
    if not authority.get("strategy_hq_authority_pass"):
        failures.append("strategy_hq_authority_not_pass")
    if authority.get("corporate_director_id") != "LOGI":
        failures.append("corporate_director_not_LOGI")
    if authority.get("command_seat") != "K6":
        failures.append("command_seat_not_K6")
    if not authority.get("zero_external_actions_ordered"):
        failures.append("zero_external_actions_order_missing")
    return {
        "state": "PASS" if not failures else "BLOCKED",
        "failures": failures,
        "subordination": {
            "safety_directive_rank": 0,
            "corporate_director": authority.get("corporate_director_id"),
            "command_seat": authority.get("command_seat"),
            "institute_director_rank": 3,
        },
    }


def render_cockpit(packet: dict[str, Any]) -> str:
    lines = [
        "# OC Core 1.3.3 Institute Director Cockpit",
        "",
        f"Director verdict: `{packet['director_verdict']}`",
        f"Safety gate: `{packet['safety_gate']['state']}`",
        f"Corporate director: `{packet['authority']['corporate_director_id']}`",
        f"Command seat: `{packet['authority']['command_seat']}`",
        f"Zero external actions ordered: `{str(packet['authority']['zero_external_actions_ordered']).lower()}`",
        f"Open critical/high findings: `{packet['open_finding_total']}`",
        f"Grand science blockers: `{packet.get('grand_science_blocker_total', 0)}`",
        f"Grand work orders: `{packet.get('grand_work_order_total', 0)}`",
        f"Work orders: `{packet['work_order_total']}`",
        "",
        "## Authority Chain",
        "",
    ]
    for row in packet["authority"]["authority_chain"]:
        lines.append(f"- `{row['rank']}` `{row['authority_id']}`: {row['source']}")
    lines.extend(["", "## Capability Load", ""])
    for cap_id, count in packet["capability_load"].items():
        lines.append(f"- `{cap_id}`: `{count}`")
    lines.extend(["", "## Top Work Orders", ""])
    for row in packet["work_orders"][:20]:
        claim = str(row.get("claim") or row.get("artifact_ref") or "")[:120]
        lines.append(f"- `{row['severity']}` `{row['capability_id']}` `{row['work_order_id']}`: {claim}")
    return "\n".join(lines) + "\n"


def build_packet() -> dict[str, Any]:
    authority = authority_snapshot()
    safety_gate = gate_director(authority)
    findings = cerberus_findings()
    cerberus_work_orders = build_director_work_orders(findings)
    all_domain_scorecard, grand_work_orders = all_domain_science_work_orders()
    work_orders = grand_work_orders + cerberus_work_orders
    capability_load: dict[str, int] = {}
    for row in work_orders:
        capability_load[row["capability_id"]] = capability_load.get(row["capability_id"], 0) + 1
    external_review_ready = all_domain_scorecard.get("external_review_ready_no_send") is True
    all_domain_blocked = (
        external_review_ready is not True
        and (all_domain_scorecard.get("all_domain_ready_no_send") is False or all_domain_scorecard.get("blocker_total", 0) > 0)
    )
    blocked = bool(findings) or bool(grand_work_orders) or all_domain_blocked or safety_gate["state"] != "PASS"
    packet = {
        "schema_id": "OC133_INSTITUTE_DIRECTOR_PACKET_v1",
        "release_id": "oc_core_1_3_3",
        "version": "1.3.3",
        "director_id": "OC133_INSTITUTE_DIRECTOR",
        "director_scope": "subordinate scientific director for OC Core 1.3.3 only",
        "director_verdict": "SCIENTIFIC_REPAIR_LOOP_REQUIRED" if blocked else "READY_FOR_K6_OWNER_REVIEW_NO_SEND",
        "no_send": True,
        "public_action_allowed": False,
        "authority": authority,
        "safety_directive": SAFETY_DIRECTIVE,
        "safety_gate": safety_gate,
        "capabilities": [
            {
                "capability_id": cap.capability_id,
                "rank": cap.rank,
                "repair_kind": cap.repair_kind,
                "owned_artifacts": list(cap.owned_artifacts),
                "repair_contract": cap.repair_contract,
            }
            for cap in CAPABILITIES
        ],
        "capability_load": capability_load,
        "open_finding_total": len(findings),
        "grand_science_blocker_total": all_domain_scorecard.get("blocker_total", 0),
        "grand_science_blocker_ids": all_domain_scorecard.get("blocker_ids", []),
        "all_domain_ready_no_send": all_domain_scorecard.get("all_domain_ready_no_send"),
        "external_review_ready_no_send": external_review_ready,
        "full_science_program_state": all_domain_scorecard.get("full_science_program_state"),
        "critical_open_total": sum(1 for row in findings if str(row.get("severity", "")).upper() == "CRITICAL"),
        "high_open_total": sum(1 for row in findings if str(row.get("severity", "")).upper() == "HIGH"),
        "work_order_total": len(work_orders),
        "grand_work_order_total": len(grand_work_orders),
        "cerberus_work_order_total": len(cerberus_work_orders),
        "work_orders_ref": rel(DIRECTOR_WORK_ORDERS),
        "work_orders": work_orders,
    }
    write_json(
        DIRECTOR_WORK_ORDERS,
        {
            "schema_id": "OC133_INSTITUTE_DIRECTOR_WORK_ORDERS_v1",
            "grand_science_blocker_total": all_domain_scorecard.get("blocker_total", 0),
            "grand_work_order_total": len(grand_work_orders),
            "cerberus_work_order_total": len(cerberus_work_orders),
            "rows": work_orders,
        },
    )
    write_json(DIRECTOR_PACKET, packet)
    DIRECTOR_COCKPIT.parent.mkdir(parents=True, exist_ok=True)
    DIRECTOR_COCKPIT.write_text(render_cockpit(packet), encoding="utf-8")
    return packet


def run_cycle(args: argparse.Namespace, packet: dict[str, Any]) -> list[dict[str, Any]]:
    commands = []
    commands.append(command([sys.executable, "-m", "py_compile", "tools/oc133_institute_director.py", "tools/oc133_autonomous_research_loop.py", "tools/materialize_oc_core_1_3_3_v12_closure.py"], timeout=120))
    if args.apply_repairs and packet["open_finding_total"]:
        commands.append(command([sys.executable, "tools/oc133_autonomous_research_loop.py", "--apply", "--checks"], timeout=1800))
    if args.rerun_cerberus:
        roles = args.roles or ""
        cmd = [sys.executable, "tools/run_oc133_v12_cerberus.py", "--max-workers", str(args.max_workers), "--role-timeout", str(args.role_timeout)]
        if roles:
            cmd.extend(["--roles", roles])
        commands.append(command(cmd, timeout=args.cerberus_timeout))
    commands.append(command([sys.executable, "-m", "release_machine", "evaluate", "--release", "oc_core_1_3_3", "--channel", "all", "--mode", "dry-run"], timeout=360))
    return commands


def main() -> int:
    parser = argparse.ArgumentParser(description="Subordinate institute director for OC Core 1.3.3 scientific closure.")
    parser.add_argument("--run-cycle", action="store_true", help="Run one director-supervised repair/evaluate cycle.")
    parser.add_argument("--apply-repairs", action="store_true", help="Invoke autonomous repair after issuing director work orders.")
    parser.add_argument("--rerun-cerberus", action="store_true", help="Rerun Cerberus under director supervision.")
    parser.add_argument("--roles", default="", help="Comma-separated Cerberus roles for targeted rerun.")
    parser.add_argument("--max-workers", type=int, default=2)
    parser.add_argument("--role-timeout", type=int, default=900)
    parser.add_argument("--cerberus-timeout", type=int, default=7200)
    args = parser.parse_args()

    packet = build_packet()
    commands = run_cycle(args, packet) if args.run_cycle else []
    if commands:
        ledger = {
            "schema_id": "OC133_INSTITUTE_DIRECTOR_CYCLE_LEDGER_v1",
            "release_id": "oc_core_1_3_3",
            "version": "1.3.3",
            "director_packet_ref": rel(DIRECTOR_PACKET),
            "commands": commands,
            "failure_total": sum(1 for item in commands if item.get("returncode") != 0),
            "no_send": True,
        }
        write_json(DIRECTOR_LEDGER, ledger)
        packet = build_packet()
        packet["last_cycle_ledger_ref"] = rel(DIRECTOR_LEDGER)
        write_json(DIRECTOR_PACKET, packet)
        DIRECTOR_COCKPIT.write_text(render_cockpit(packet), encoding="utf-8")
    print(json.dumps({"director_packet": rel(DIRECTOR_PACKET), "cockpit": rel(DIRECTOR_COCKPIT), "director_verdict": packet["director_verdict"]}, ensure_ascii=False, indent=2))
    return 0 if packet["director_verdict"] == "READY_FOR_K6_OWNER_REVIEW_NO_SEND" else 1


if __name__ == "__main__":
    raise SystemExit(main())
