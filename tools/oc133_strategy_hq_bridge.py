from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
WORK_ROOT = ROOT.parents[2]
PRIVATE_ROOT = WORK_ROOT / "estra-private-work"
BRIDGE_DIR = ROOT / "operations" / "strategy_hq_bridge" / "oc_core_1_3_3"
BRIDGE_PACKET = BRIDGE_DIR / "OC133_STRATEGY_HQ_BRIDGE_PACKET.json"
COCKPIT_JSON = BRIDGE_DIR / "OC133_PROCESS_COCKPIT.json"
COCKPIT_MD = BRIDGE_DIR / "OC133_PROCESS_COCKPIT.md"
CAPABILITY_GRAPH = BRIDGE_DIR / "OC133_CAPABILITY_LINK_GRAPH.json"


CAPABILITIES = [
    {
        "capability_id": "oc133_platinum_release_mission",
        "hq_owner_ref": "LOGI -> K6 Strategy HQ -> OC133 institute director",
        "role": "mission contract, content-closure scorecard, live dispatch queue, and platinum cockpit",
        "entrypoint": "tools/oc133_logion_release_mission.py --write",
        "outputs": ["operations/logion_release_mission/oc_core_1_3_3/OC133_CONTENT_CLOSURE_SCORECARD.json"],
    },
    {
        "capability_id": "oc133_institute_director",
        "hq_owner_ref": "LOGI -> K6 Strategy HQ",
        "role": "subordinate scientific director: enforces Safety Directive, corporate/Strategy HQ authority, and capability work-order routing",
        "entrypoint": "tools/oc133_institute_director.py --run-cycle",
        "outputs": ["operations/institute_director/oc_core_1_3_3/OC133_INSTITUTE_DIRECTOR_PACKET.json"],
    },
    {
        "capability_id": "oc133_research_corpus",
        "hq_owner_ref": "logion/k7/spe/orchestrator/k6",
        "role": "materialize bounded release science artifacts",
        "entrypoint": "tools/materialize_oc_core_1_3_3_v12_closure.py",
        "outputs": ["formal/lean/OC133V12.lean", "proofs/FINITE_MODEL_CHECKS_1_3_3.json", "review/OC_1_3_3_TOTAL_ATTACK_MATRIX.json"],
    },
    {
        "capability_id": "oc133_cerberus_review",
        "hq_owner_ref": "logion/k7/roles/formal_methods_validation_hq",
        "role": "parallel read-only hostile LLM review",
        "entrypoint": "tools/run_oc133_v12_cerberus.py --max-workers N",
        "outputs": ["reviews/oc133_llm_cerberus/OC133_LLM_CERBERUS_SUMMARY.json"],
    },
    {
        "capability_id": "oc133_autonomous_repair",
        "hq_owner_ref": "logion/k7/spe/orchestrator/k6",
        "role": "convert Cerberus findings into deterministic repair work orders",
        "entrypoint": "tools/oc133_autonomous_research_loop.py --apply --checks",
        "outputs": ["reviews/oc133_llm_cerberus/repair/OC133_CERBERUS_REPAIR_WORK_ORDERS.json"],
    },
    {
        "capability_id": "oc133_release_machine",
        "hq_owner_ref": "logion/k6/science/architecture",
        "role": "G32-G70 dry-run release gate evaluation under no-send",
        "entrypoint": "python -m release_machine evaluate --release oc_core_1_3_3 --channel all --mode dry-run",
        "outputs": ["releases/oc_core_1_3_3/release_machine"],
    },
    {
        "capability_id": "oc133_publication_governor",
        "hq_owner_ref": "logion/k0/governance/status",
        "role": "owner-gated no-send state; no push/public/doi/journal action",
        "entrypoint": "releases/oc_core_1_3_3/editorial/OWNER_RELEASE_APPROVAL_v1.3.3.json",
        "outputs": ["releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_PUBLISH_MANIFEST_DRAFT.json"],
    },
    {
        "capability_id": "oc133_journal_package_factory",
        "hq_owner_ref": "LOGI -> K6 Strategy HQ -> Publication capability",
        "role": "version-aware 1.3.3 owner-review no-send journal package generator",
        "entrypoint": "python -m release_machine submission-packages --release-id oc_core_1_3_3",
        "outputs": ["releases/oc_core_1_3_3/submission_packages/SUBMISSION_PACKAGE_INDEX.json"],
    },
]

EDGES = [
    ("oc133_platinum_release_mission", "oc133_institute_director", "mission contract gives the director content blockers and capability work orders"),
    ("oc133_platinum_release_mission", "oc133_journal_package_factory", "publication blocker dispatches to version-aware no-send package generator"),
    ("oc133_institute_director", "oc133_research_corpus", "director issues repair-scoped scientific work orders under Safety Directive and Strategy HQ/K6"),
    ("oc133_institute_director", "oc133_cerberus_review", "director selects targeted adversarial reruns and blocks stale review certification"),
    ("oc133_institute_director", "oc133_release_machine", "director requires G32-G70 evidence before owner review"),
    ("oc133_research_corpus", "oc133_cerberus_review", "research artifacts become adversarial review context"),
    ("oc133_cerberus_review", "oc133_autonomous_repair", "critical/high findings become repair work orders"),
    ("oc133_cerberus_review", "oc133_institute_director", "critical/high findings are escalated to the subordinate institute director"),
    ("oc133_autonomous_repair", "oc133_research_corpus", "repair profiles regenerate scientific artifacts"),
    ("oc133_autonomous_repair", "oc133_institute_director", "repair results return to director for gate and authority checks"),
    ("oc133_research_corpus", "oc133_release_machine", "formal/finite/validation artifacts feed G32-G70"),
    ("oc133_release_machine", "oc133_publication_governor", "ready state remains no-send until owner approval"),
    ("oc133_publication_governor", "oc133_cerberus_review", "public-surface/no-send locks are reviewed as claims"),
    ("oc133_journal_package_factory", "oc133_release_machine", "1.3.3 submission package inventory becomes tracked package input"),
    ("oc133_release_machine", "oc133_platinum_release_mission", "technical G32-G70 state is subordinated to scientific content-closure readiness"),
]


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


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


def command(cmd: list[str], timeout: int = 900) -> dict[str, Any]:
    started = time.time()
    completed = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=timeout)
    return {
        "cmd": cmd,
        "returncode": completed.returncode,
        "duration_seconds": round(time.time() - started, 3),
        "stdout_tail": completed.stdout[-3000:],
        "stderr_tail": completed.stderr[-3000:],
    }


def git_status(path: Path) -> dict[str, Any]:
    completed = subprocess.run(["git", "status", "--short", "--branch"], cwd=path, text=True, capture_output=True, timeout=60)
    lines = completed.stdout.splitlines()
    dirty = [line for line in lines if line and not line.startswith("## ")]
    return {"branch": lines[0] if lines else "", "dirty_total": len(dirty), "dirty_files": dirty[:80]}


def cerberus_state() -> dict[str, Any]:
    summary = read_json(ROOT / "reviews" / "oc133_llm_cerberus" / "OC133_LLM_CERBERUS_SUMMARY.json")
    open_findings = []
    for path in sorted((ROOT / "reviews" / "oc133_llm_cerberus" / "results").glob("*.json")):
        payload = read_json(path)
        for row in payload.get("findings", []):
            severity = str(row.get("severity", "")).upper()
            status = str(row.get("status", "OPEN")).upper()
            if severity in {"CRITICAL", "HIGH"} and status not in {"CLOSED", "RESOLVED", "CLOSED_BY_V12_EVIDENCE"}:
                item = dict(row)
                item["role"] = payload.get("role", path.stem)
                item["result_ref"] = rel(path)
                open_findings.append(item)
    return {"summary": summary, "open_findings": open_findings}


def release_state() -> dict[str, Any]:
    candidates = [
        ROOT / "releases" / "oc_core_1_3_3" / "editorial" / "OC_CORE_1_3_3_RELEASE_SCORECARD_latest.json",
        ROOT / "releases" / "oc_core_1_3_3" / "release_machine" / "OC_CORE_1_3_3_RELEASE_MACHINE_EVALUATION.json",
        ROOT / "releases" / "oc_core_1_3_3" / "release_machine" / "OC_CORE_1_3_3_V12_GATE_SCORECARD.json",
    ]
    for path in candidates:
        if path.exists():
            payload = read_json(path)
            payload["_source_ref"] = rel(path)
            return payload
    return {}


def capability_graph() -> dict[str, Any]:
    return {
        "schema_id": "OC133_CAPABILITY_LINK_GRAPH_v1",
        "release_id": "oc_core_1_3_3",
        "version": "1.3.3",
        "authority_note": "Strategy HQ/K6 remains the governing layer under LOGI. The institute director is a subordinate scientific decision module, not a competing corporate authority.",
        "authority_chain": ["Safety Directive", "LOGI corporate director", "K6 Strategy HQ", "OC133 institute director", "capability workers"],
        "no_send": True,
        "capabilities": CAPABILITIES,
        "edges": [{"from": a, "to": b, "trigger": trigger} for a, b, trigger in EDGES],
    }


def render_cockpit(packet: dict[str, Any]) -> str:
    lines = [
        "# OC Core 1.3.3 Strategy HQ Bridge Cockpit",
        "",
        f"Bridge verdict: `{packet['bridge_verdict']}`",
        f"No-send: `{packet['no_send']}`",
        f"Owner approved: `{packet['owner_approved']}`",
        f"Public action allowed: `{packet['public_action_allowed']}`",
        f"Cerberus open critical/high: `{packet['cerberus_open_total']}`",
        f"Release state: `{packet['release_master_verdict']}`",
        f"Content closure: `{packet['content_closure_state']}`",
        f"Content blockers: `{packet['content_blocker_total']}`",
        "",
        "## Capability Links",
        "",
    ]
    for cap in CAPABILITIES:
        lines.append(f"- `{cap['capability_id']}` -> `{cap['hq_owner_ref']}` -> {cap['role']}")
    lines.extend(["", "## Commands", ""])
    for item in packet.get("commands", [])[-12:]:
        lines.append(f"- `{item.get('returncode')}` `{' '.join(item.get('cmd', []))}` ({item.get('duration_seconds', 'NA')}s)")
    lines.extend(["", "## Open Findings", ""])
    for finding in packet["cerberus"]["open_findings"][:20]:
        lines.append(f"- `{finding.get('severity')}` `{finding.get('role')}` `{finding.get('artifact_ref')}`: {finding.get('claim')}")
    if not packet["cerberus"]["open_findings"]:
        lines.append("- none")
    lines.extend(["", "## Content Blockers", ""])
    for blocker in packet.get("content_blocker_ids", []):
        lines.append(f"- `{blocker}`")
    if not packet.get("content_blocker_ids"):
        lines.append("- none")
    return "\n".join(lines) + "\n"


def build_packet(commands: list[dict[str, Any]]) -> dict[str, Any]:
    write_json(CAPABILITY_GRAPH, capability_graph())
    director = read_json(ROOT / "operations" / "institute_director" / "oc_core_1_3_3" / "OC133_INSTITUTE_DIRECTOR_PACKET.json")
    cerb = cerberus_state()
    rel_state = release_state()
    score_summary = rel_state.get("summary", {}) if isinstance(rel_state.get("summary"), dict) else {}
    release_master = str(score_summary.get("master_verdict") or rel_state.get("master_verdict") or rel_state.get("release_state") or "UNKNOWN")
    content = read_json(ROOT / "operations" / "logion_release_mission" / "oc_core_1_3_3" / "OC133_CONTENT_CLOSURE_SCORECARD.json")
    content_state = str(content.get("state") or score_summary.get("content_closure_state") or "UNKNOWN")
    content_blockers = content.get("blocker_ids") or score_summary.get("content_closure_blocker_ids") or []
    if not isinstance(content_blockers, list):
        content_blockers = []
    open_total = len(cerb["open_findings"])
    ready = open_total == 0 and release_master == "PASS" and content_state == "PASS"
    packet = {
        "schema_id": "OC133_STRATEGY_HQ_BRIDGE_PACKET_v1",
        "release_id": "oc_core_1_3_3",
        "version": "1.3.3",
        "authority_home": "Strategy HQ / K6",
        "adapter_scope": "public release-repo telemetry, subordinate institute director state, and callable helpers only",
        "corporate_director": "LOGI",
        "command_seat": "K6",
        "institute_director_ref": "operations/institute_director/oc_core_1_3_3/OC133_INSTITUTE_DIRECTOR_PACKET.json",
        "institute_director": director,
        "no_send": True,
        "owner_approved": False,
        "public_action_allowed": False,
        "bridge_verdict": "READY_FOR_K6_OWNER_REVIEW_NO_SEND" if ready else "K6_CONTINUE_SCIENTIFIC_CONTENT_CLOSURE",
        "cerberus_open_total": open_total,
        "release_master_verdict": release_master,
        "content_closure_state": content_state,
        "content_blocker_total": len(content_blockers),
        "content_blocker_ids": content_blockers,
        "capability_graph_ref": rel(CAPABILITY_GRAPH),
        "cerberus": cerb,
        "release": rel_state,
        "commands": commands,
        "git": {
            "public": git_status(ROOT),
            "private": git_status(PRIVATE_ROOT) if PRIVATE_ROOT.exists() else {"dirty_total": None, "dirty_files": ["private root not found"]},
        },
    }
    write_json(BRIDGE_PACKET, packet)
    write_json(COCKPIT_JSON, packet)
    COCKPIT_MD.parent.mkdir(parents=True, exist_ok=True)
    COCKPIT_MD.write_text(render_cockpit(packet), encoding="utf-8")
    return packet


def run_cycle(args: argparse.Namespace) -> list[dict[str, Any]]:
    commands: list[dict[str, Any]] = []
    if args.materialize:
        commands.append(command([sys.executable, "tools/materialize_oc_core_1_3_3_v12_closure.py"], timeout=900))
    commands.append(command([sys.executable, "-m", "py_compile", "tools/materialize_oc_core_1_3_3_v12_closure.py", "tools/oc133_autonomous_research_loop.py", "tools/oc133_strategy_hq_bridge.py", "tools/run_oc133_v12_cerberus.py", "proofs/finite_model_checks/run_finite_model_checks.py"], timeout=120))
    commands.append(command([sys.executable, "proofs/finite_model_checks/run_finite_model_checks.py"], timeout=120))
    commands.append(command(["lake", "build"], timeout=240))
    commands.append(command([sys.executable, "validation/run_all.py", "--qa-only"], timeout=240))
    if args.cerberus:
        commands.append(command([sys.executable, "tools/run_oc133_v12_cerberus.py", "--max-workers", str(args.max_workers)], timeout=args.cerberus_timeout))
    if cerberus_state()["open_findings"]:
        commands.append(command([sys.executable, "tools/oc133_institute_director.py"], timeout=180))
        commands.append(command([sys.executable, "tools/oc133_autonomous_research_loop.py", "--apply", "--checks"], timeout=1800))
    commands.append(command([sys.executable, "-m", "release_machine", "evaluate", "--release", "oc_core_1_3_3", "--channel", "all", "--mode", "dry-run"], timeout=240))
    commands.append(command([sys.executable, "tools/oc133_logion_release_mission.py", "--write"], timeout=180))
    return commands


def export_to_strategy_hq(packet: dict[str, Any], private_root: Path) -> dict[str, Any]:
    status_dir = private_root / "logion" / "k0" / "governance" / "status"
    ui_dir = private_root / "User_Interfaces" / "LOGION" / "K7" / "Strategy_HQ" / "reports"
    status_path = status_dir / "OC_CORE_1_3_3_STRATEGY_HQ_BRIDGE_latest.json"
    report_path = ui_dir / "OC_CORE_1_3_3_STRATEGY_HQ_BRIDGE_latest.md"
    status_dir.mkdir(parents=True, exist_ok=True)
    ui_dir.mkdir(parents=True, exist_ok=True)
    exported = dict(packet)
    exported["public_repo_bridge_packet_ref"] = str(BRIDGE_PACKET)
    exported["export_policy"] = "K6 remains authority; this is imported telemetry, not a new supervisor."
    status_path.write_text(json.dumps(exported, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_path.write_text(render_cockpit(packet), encoding="utf-8")
    return {"status_path": str(status_path), "report_path": str(report_path)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Lightweight OC133 -> Strategy HQ/K6 bridge and cockpit helper.")
    parser.add_argument("--run-cycle", action="store_true", help="Run one subordinate research/review/repair/evaluate cycle.")
    parser.add_argument("--materialize", action="store_true", help="Regenerate v12 artifacts before checks.")
    parser.add_argument("--cerberus", action="store_true", help="Run parallel Cerberus in this cycle.")
    parser.add_argument("--max-workers", type=int, default=3)
    parser.add_argument("--cerberus-timeout", type=int, default=7200)
    parser.add_argument("--export-strategy-hq", action="store_true", help="Write imported telemetry into existing private Strategy HQ/K6 status surfaces.")
    args = parser.parse_args()

    commands = run_cycle(args) if args.run_cycle else []
    packet = build_packet(commands)
    if args.export_strategy_hq:
        packet["strategy_hq_export"] = export_to_strategy_hq(packet, PRIVATE_ROOT)
        write_json(BRIDGE_PACKET, packet)
        write_json(COCKPIT_JSON, packet)
    print(json.dumps({"bridge_packet": rel(BRIDGE_PACKET), "cockpit": rel(COCKPIT_MD), "bridge_verdict": packet["bridge_verdict"]}, ensure_ascii=False, indent=2))
    return 0 if packet["bridge_verdict"] == "READY_FOR_K6_OWNER_REVIEW_NO_SEND" else 1


if __name__ == "__main__":
    raise SystemExit(main())
