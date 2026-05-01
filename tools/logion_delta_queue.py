from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROJECT_CONTROL_REL = "operations/project_control"
LEDGER_REL = f"{PROJECT_CONTROL_REL}/LOGION_DELTA_QUEUE_LEDGER.json"
POLICY_REL = f"{PROJECT_CONTROL_REL}/LOGION_DELTA_QUEUE_POLICY.json"

RELEASE_SCORECARD_REL = "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_RELEASE_SCORECARD_latest.json"
CERBERUS_SUMMARY_REL = "reviews/oc133_llm_cerberus/OC133_LLM_CERBERUS_SUMMARY.json"
JOURNAL_INDEX_REL = "releases/oc_core_1_3_3/submission_packages/SUBMISSION_PACKAGE_INDEX.json"
DIRTY_LEDGER_REL = f"{PROJECT_CONTROL_REL}/LOGION_DIRTY_TREE_GOVERNANCE_LEDGER.json"
ZIP_INTEGRITY_REL = "releases/oc_core_1_3_3/editorial/OC_CORE_1_3_3_ZIP_INTEGRITY_latest.json"

MODES = {"diagnostic", "test", "productive", "release"}
SELF_TELEMETRY_PREFIXES = (f"{PROJECT_CONTROL_REL}/",)


def read_json(path: Path) -> Any:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_json_if_changed(path: Path, payload: Any) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if path.exists() and path.read_bytes() == data:
        return False
    path.write_bytes(data)
    return True


def sha256_object(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def git_status_summary(root: Path) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            ["git", "status", "--short", "-uall"],
            cwd=root,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=30,
        )
    except Exception as exc:
        return {"available": False, "dirty_total": None, "error": str(exc)}
    rows = []
    for line in completed.stdout.splitlines():
        if not line.strip():
            continue
        path = line[3:].replace("\\", "/") if len(line) >= 4 else ""
        if any(path.startswith(prefix) for prefix in SELF_TELEMETRY_PREFIXES):
            continue
        rows.append(line)
    return {
        "available": completed.returncode == 0,
        "dirty_total": len(rows),
        "dirty_paths": [line[3:].replace("\\", "/") for line in rows[:80] if len(line) >= 4],
    }


def scorecard_summary(root: Path) -> dict[str, Any]:
    payload = read_json(root / RELEASE_SCORECARD_REL)
    summary = payload.get("summary", payload) if isinstance(payload, dict) else {}
    return {
        "release_state": summary.get("release_state"),
        "technical_gate_state": summary.get("technical_gate_state"),
        "master_verdict": summary.get("master_verdict"),
        "gate_counts": summary.get("gate_counts", {}),
        "content_closure_blocker_total": summary.get("content_closure_blocker_total"),
        "all_domain_blocker_total": summary.get("all_domain_blocker_total"),
        "all_domain_blocker_ids": summary.get("all_domain_blocker_ids", []),
        "external_review_ready_no_send": summary.get("external_review_ready_no_send"),
        "all_domain_ready_no_send": summary.get("all_domain_ready_no_send"),
        "full_science_program_state": summary.get("full_science_program_state"),
        "publish_allowed": summary.get("publish_allowed"),
        "journal_submissions_allowed": summary.get("journal_submissions_allowed"),
    }


def semantic_snapshot(root: Path) -> dict[str, Any]:
    cerberus = read_json(root / CERBERUS_SUMMARY_REL)
    journal = read_json(root / JOURNAL_INDEX_REL)
    dirty = read_json(root / DIRTY_LEDGER_REL)
    integrity = read_json(root / ZIP_INTEGRITY_REL)
    return {
        "schema_id": "LOGION_DELTA_QUEUE_SEMANTIC_SNAPSHOT_v1",
        "release": scorecard_summary(root),
        "cerberus": {
            "critical_open_total": cerberus.get("critical_open_total"),
            "high_open_total": cerberus.get("high_open_total"),
            "parse_failure_total": cerberus.get("parse_failure_total"),
        },
        "journal_packages": {
            "package_total": journal.get("package_total"),
            "package_status_counts": journal.get("package_status_counts", {}),
            "submission_allowed": journal.get("submission_allowed"),
            "journal_submissions_allowed": journal.get("journal_submissions_allowed"),
        },
        "dirty_tree": {
            "governance_state": dirty.get("governance_state"),
            "public_dirty_total": dirty.get("public_dirty_total"),
            "public_unclassified_total": dirty.get("public_unclassified_total"),
            "private_dirty_total": dirty.get("private_dirty_total"),
            "private_unknown_total": dirty.get("private_unknown_total"),
        },
        "working_tree": git_status_summary(root),
        "package": {
            "package_sha256": integrity.get("package_sha256"),
            "package_size_bytes": integrity.get("package_size_bytes"),
            "package_member_total": integrity.get("package_member_total"),
        },
    }


def policy() -> dict[str, Any]:
    return {
        "schema_id": "LOGION_DELTA_QUEUE_POLICY_v1",
        "principle": "A downstream Logion node receives a signal only when a material qualitative delta crosses the configured threshold.",
        "modes": {
            "diagnostic": {
                "writes": "optional ledger only when --write is supplied",
                "triggers_downstream": False,
                "use": "inspect drift and explain why no further chain should run",
            },
            "test": {
                "writes": "test ledger allowed",
                "triggers_downstream": False,
                "use": "prove delta routing and idempotence without operational effects",
            },
            "productive": {
                "writes": "ledger allowed",
                "triggers_downstream": "only when significant_delta=true",
                "use": "normal Logion workstream operation",
            },
            "release": {
                "writes": "ledger allowed",
                "triggers_downstream": "only when significant_delta=true and no-send locks remain valid",
                "use": "release verification; checks must not dirty artifacts without material delta",
            },
        },
        "significant_delta_classes": [
            "release_verdict_or_state_change",
            "gate_count_change",
            "critical_or_high_review_count_change",
            "dirty_tree_governance_change",
            "working_tree_delta_change",
            "journal_send_lock_or_package_status_change",
            "no_send_lock_change",
            "package_member_set_or_package_hash_change",
            "all_domain_blocker_set_change",
        ],
        "non_significant_examples": [
            "rerun with byte-identical generated output",
            "diagnostic command with unchanged semantic snapshot",
            "cache refresh that does not change release-visible artifact hashes",
        ],
    }


def changed_classes(previous: dict[str, Any], current: dict[str, Any]) -> list[str]:
    if not previous:
        return ["initial_snapshot"]
    classes: list[str] = []
    prev = previous.get("semantic_snapshot", previous)
    if prev.get("release", {}).get("release_state") != current.get("release", {}).get("release_state") or prev.get("release", {}).get("master_verdict") != current.get("release", {}).get("master_verdict"):
        classes.append("release_verdict_or_state_change")
    if prev.get("release", {}).get("gate_counts") != current.get("release", {}).get("gate_counts"):
        classes.append("gate_count_change")
    if (
        prev.get("cerberus", {}).get("critical_open_total"),
        prev.get("cerberus", {}).get("high_open_total"),
        prev.get("cerberus", {}).get("parse_failure_total"),
    ) != (
        current.get("cerberus", {}).get("critical_open_total"),
        current.get("cerberus", {}).get("high_open_total"),
        current.get("cerberus", {}).get("parse_failure_total"),
    ):
        classes.append("critical_or_high_review_count_change")
    if prev.get("dirty_tree") != current.get("dirty_tree"):
        classes.append("dirty_tree_governance_change")
    if prev.get("working_tree", {}).get("dirty_paths") != current.get("working_tree", {}).get("dirty_paths"):
        classes.append("working_tree_delta_change")
    if prev.get("journal_packages") != current.get("journal_packages"):
        classes.append("journal_send_lock_or_package_status_change")
    if (
        prev.get("release", {}).get("publish_allowed"),
        prev.get("release", {}).get("journal_submissions_allowed"),
        prev.get("journal_packages", {}).get("submission_allowed"),
        prev.get("journal_packages", {}).get("journal_submissions_allowed"),
    ) != (
        current.get("release", {}).get("publish_allowed"),
        current.get("release", {}).get("journal_submissions_allowed"),
        current.get("journal_packages", {}).get("submission_allowed"),
        current.get("journal_packages", {}).get("journal_submissions_allowed"),
    ):
        classes.append("no_send_lock_change")
    if prev.get("package") != current.get("package"):
        classes.append("package_member_set_or_package_hash_change")
    if prev.get("release", {}).get("all_domain_blocker_ids") != current.get("release", {}).get("all_domain_blocker_ids"):
        classes.append("all_domain_blocker_set_change")
    return classes


def evaluate(root: Path, mode: str) -> dict[str, Any]:
    if mode not in MODES:
        raise ValueError(f"unknown mode: {mode}")
    current = semantic_snapshot(root)
    previous = read_json(root / LEDGER_REL)
    classes = changed_classes(previous, current)
    significant = bool(classes)
    no_send_valid = (
        current["release"].get("publish_allowed") is False
        and current["release"].get("journal_submissions_allowed") is False
        and current["journal_packages"].get("submission_allowed") is False
        and current["journal_packages"].get("journal_submissions_allowed") is False
    )
    triggers_allowed = mode in {"productive", "release"} and significant and (mode != "release" or no_send_valid)
    return {
        "schema_id": "LOGION_DELTA_QUEUE_LEDGER_v1",
        "mode": mode,
        "semantic_fingerprint": sha256_object(current),
        "previous_semantic_fingerprint": previous.get("semantic_fingerprint") if isinstance(previous, dict) else None,
        "significant_delta": significant,
        "changed_classes": classes,
        "downstream_trigger_allowed": triggers_allowed,
        "no_send_valid": no_send_valid,
        "semantic_snapshot": current,
        "policy_ref": POLICY_REL,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=sorted(MODES), default="diagnostic")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    payload = evaluate(ROOT, args.mode)
    if args.write:
        write_json_if_changed(ROOT / POLICY_REL, policy())
        write_json_if_changed(ROOT / LEDGER_REL, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if args.check and args.mode == "release" and payload["significant_delta"] and not payload["downstream_trigger_allowed"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
