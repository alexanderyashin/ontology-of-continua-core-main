from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import oc133_empirical_capability_registry as registry


SCHEMA_ID = "OC133_EMPIRICAL_CAPABILITY_DISPATCHER_v1"
RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
CAPABILITY_OWNER = "Logion IT/Research"
REPORT_JSON_REL = "reports/OC_CORE_1_3_3_EMPIRICAL_CAPABILITY_DISPATCHER.json"
REPORT_MD_REL = "reports/OC_CORE_1_3_3_EMPIRICAL_CAPABILITY_DISPATCHER.md"
DEFAULT_MAX_ACTIONS = 3
COMMAND_TIMEOUT_SECONDS = 300

REQUIRED_NO_SEND_LOCKS = {
    "no_send": True,
    "publish_allowed": False,
    "journal_submissions_allowed": False,
    "external_network_allowed": False,
}

ALLOWED_ARGS_BY_TYPE = {
    "factory": {"--write", "--allow-blocked-exit-zero"},
    "harvester": {"--write", "--offline", "--allow-blocked-exit-zero"},
    "executor": {"--write", "--allow-blocked-exit-zero"},
    "planner": {"--write", "--allow-blocked-exit-zero"},
}

FORBIDDEN_COMMAND_TOKENS = {
    "curl",
    "wget",
    "git",
    "gh",
    "hub",
    "scp",
    "rsync",
    "zenodo",
    "twine",
}

FORBIDDEN_COMMAND_WORDS = {
    "doi",
    "publish",
    "published",
    "submission",
    "submissions",
    "submit",
    "upload",
    "push",
    "release-upload",
}

HASH_EXCLUDED_DIRS = {
    ".git",
    ".lake",
    ".pytest_cache",
    "__pycache__",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def canonical_sha256(payload: Any) -> str:
    data = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _skip_hash_path(path: Path) -> bool:
    return any(part in HASH_EXCLUDED_DIRS for part in path.parts)


def tree_hash(root: Path) -> dict[str, Any]:
    hasher = hashlib.sha256()
    file_count = 0
    byte_count = 0
    for path in sorted(root.rglob("*")):
        if not path.is_file() or _skip_hash_path(path):
            continue
        file_rel = rel(root, path)
        data = path.read_bytes()
        hasher.update(file_rel.encode("utf-8"))
        hasher.update(b"\0")
        hasher.update(hashlib.sha256(data).hexdigest().encode("ascii"))
        hasher.update(b"\0")
        file_count += 1
        byte_count += len(data)
    return {
        "sha256": hasher.hexdigest(),
        "file_total": file_count,
        "byte_total": byte_count,
        "excluded_dirs": sorted(HASH_EXCLUDED_DIRS),
    }


def sanitize_text(root: Path, text: str) -> str:
    out = text
    replacements = {
        str(root): "<REPO_ROOT>",
        str(root).replace("\\", "/"): "<REPO_ROOT>",
        str(Path.home()): "<LOCAL_HOME>",
        str(Path.home()).replace("\\", "/"): "<LOCAL_HOME>",
        str(Path(sys.executable)): "python",
        str(Path(sys.executable)).replace("\\", "/"): "python",
    }
    for needle, replacement in replacements.items():
        if needle:
            out = out.replace(needle, replacement)
    return out


def extract_json(stdout: str) -> dict[str, Any] | None:
    text = stdout.strip()
    if not text:
        return None
    try:
        payload = json.loads(text)
        return payload if isinstance(payload, dict) else None
    except json.JSONDecodeError:
        pass
    for line in reversed(text.splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        return payload if isinstance(payload, dict) else None
    return None


def int_field(payload: dict[str, Any] | None, *keys: str) -> int:
    if not isinstance(payload, dict):
        return 0
    for key in keys:
        value = payload.get(key)
        if isinstance(value, int) and not isinstance(value, bool):
            return value
    return 0


def scientific_payload(row: dict[str, Any], parsed_payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if isinstance(parsed_payload, dict):
        if isinstance(parsed_payload.get("report"), dict):
            return parsed_payload["report"]
        return parsed_payload
    effective = row.get("effective_payload")
    return effective if isinstance(effective, dict) else None


def scientific_blockers(payload: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {
            "scientific_blocked": False,
            "scientific_blocker_total": 0,
            "scientific_blocker_reasons": [],
            "scientific_verdict": "NO_SCIENTIFIC_PAYLOAD",
        }
    verdict = str(payload.get("verdict", "UNKNOWN"))
    verdict_upper = verdict.upper()
    blocker_total = max(
        int_field(payload, "open_blocker_total", "blocker_total", "blocked_total", "blocked_domain_total"),
        int_field(payload, "blocked_candidate_pack_total", "blocked_pack_total"),
    )
    candidate_total = int_field(payload, "candidate_pack_total", "candidate_total", "task_total", "n")
    valid_total = int_field(
        payload,
        "valid_pack_total",
        "valid_candidate_pack_total",
        "valid_under_current_grand_schema_total",
        "valid_under_grand_gate_total",
    )
    reasons = payload.get("blockers")
    if not isinstance(reasons, list):
        reasons = payload.get("pack_failure_reasons")
    if not isinstance(reasons, list):
        reasons = []
    support_allowed = payload.get("grand_toe_support_allowed")
    blocked = (
        verdict_upper.startswith("BLOCKED")
        or "BLOCKED_PENDING" in verdict_upper
        or blocker_total > 0
        or support_allowed is False
        or (candidate_total > 0 and valid_total == 0 and "READY" not in verdict_upper)
    )
    return {
        "scientific_blocked": blocked,
        "scientific_blocker_total": blocker_total,
        "scientific_blocker_reasons": [str(item) for item in reasons],
        "scientific_verdict": verdict,
    }


def load_registry_payload(root: Path, *, refresh_registry: bool = False) -> dict[str, Any]:
    if refresh_registry:
        return registry.build_payload(root, write=False)
    payload = read_json(root / registry.REPORT_JSON_REL)
    if payload:
        return payload
    return registry.build_payload(root, write=False)


def _as_position(value: Any) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return 1_000_000


def select_ranked_actions(registry_payload: dict[str, Any], max_actions: int | None = DEFAULT_MAX_ACTIONS) -> list[dict[str, Any]]:
    if max_actions is not None and max_actions <= 0:
        return []
    rows = registry_payload.get("components")
    components = [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []
    component_by_ref = {str(row.get("component_ref")): row for row in components if row.get("component_ref")}
    queue = registry_payload.get("next_action_queue")
    queue_rows = [row for row in queue if isinstance(row, dict)] if isinstance(queue, list) else []
    if not queue_rows:
        queue_rows = [
            {
                "action_id": f"DISPATCH-DERIVED-{idx:03d}",
                "position": idx,
                "component_ref": row.get("component_ref"),
                "resource_class": row.get("resource_class", row.get("component_type")),
                "unblock_value": row.get("unblock_value", 0),
                "next_action": row.get("next_action", ""),
            }
            for idx, row in enumerate(
                sorted(
                    components,
                    key=lambda item: (
                        -int(item.get("unblock_value", 0) or 0),
                        -int(item.get("resource_class_rank", 0) or 0),
                        str(item.get("component_ref", "")),
                    ),
                ),
                start=1,
            )
        ]
    ordered = sorted(
        queue_rows,
        key=lambda item: (
            _as_position(item.get("position")),
            str(item.get("action_id", "")),
            str(item.get("component_ref", "")),
        ),
    )
    selected: list[dict[str, Any]] = []
    for idx, action in enumerate(ordered, start=1):
        component_ref = str(action.get("component_ref", ""))
        component = component_by_ref.get(component_ref, {})
        merged = dict(component)
        merged.update(action)
        merged["selected_position"] = idx
        merged["component_ref"] = component_ref
        if "component_type" not in merged:
            merged["component_type"] = merged.get("resource_class")
        selected.append(merged)
        if max_actions is not None and len(selected) >= max_actions:
            break
    return selected


def _token_has_forbidden_word(token: str) -> bool:
    lowered = token.lower()
    if lowered in FORBIDDEN_COMMAND_TOKENS or lowered in FORBIDDEN_COMMAND_WORDS:
        return True
    if lowered.startswith(("http://", "https://", "ftp://")) or "doi.org" in lowered:
        return True
    parts = lowered.replace("_", "-").replace(".", "-").split("-")
    return any(part in FORBIDDEN_COMMAND_WORDS for part in parts)


def _component_type(row: dict[str, Any]) -> str:
    value = row.get("component_type") or row.get("resource_class")
    return str(value or "").lower()


def _script_allowed(component_ref: str, component_type: str) -> bool:
    if component_type == "factory":
        return component_ref.startswith("tools/oc133_") and component_ref.endswith("_factory.py")
    if component_type == "harvester":
        return component_ref.startswith("validation/heldout/harvesters/") and component_ref.endswith("_harvester.py")
    if component_type == "executor":
        return component_ref.startswith("validation/heldout/domain_evidence/") and component_ref.endswith("_evidence_executor.py")
    if component_type == "planner":
        return component_ref.startswith("tools/oc133_") and (
            component_ref.endswith("_acquisition_planner.py")
            or component_ref.endswith("_acquisition_runner.py")
        )
    return False


def validate_no_send_locks(registry_payload: dict[str, Any], row: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    lock_payload = registry_payload.get("no_send_locks")
    locks = lock_payload if isinstance(lock_payload, dict) else {}
    for key, expected in REQUIRED_NO_SEND_LOCKS.items():
        observed = locks.get(key, registry_payload.get(key))
        if observed is not expected:
            reasons.append(f"registry_lock::{key}::{observed!r}!=expected::{expected!r}")
    for key, expected in REQUIRED_NO_SEND_LOCKS.items():
        if key in row and row.get(key) is not expected:
            reasons.append(f"component_lock::{key}::{row.get(key)!r}!=expected::{expected!r}")
    return reasons


def validate_command(root: Path, registry_payload: dict[str, Any], row: dict[str, Any]) -> tuple[list[str], list[str]]:
    reasons = validate_no_send_locks(registry_payload, row)
    command = str(row.get("command") or "")
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError as exc:
        return [], [*reasons, f"command_parse_error::{exc}"]
    if len(tokens) < 2:
        return tokens, [*reasons, "command_must_be_python_script"]
    executable = Path(tokens[0]).name.lower()
    if executable not in {"python", "python.exe"}:
        reasons.append("command_executable_not_allowlisted")
    if any(_token_has_forbidden_word(token) for token in tokens):
        reasons.append("command_contains_forbidden_publish_network_or_push_token")
    component_ref = str(row.get("component_ref", "")).replace("\\", "/")
    script_ref = tokens[1].replace("\\", "/")
    if script_ref != component_ref:
        reasons.append(f"command_script_mismatch::{script_ref}!=component::{component_ref}")
    if Path(script_ref).is_absolute() or ".." in Path(script_ref).parts:
        reasons.append("command_script_must_be_relative_under_repo")
    script_path = (root / script_ref).resolve()
    try:
        script_path.relative_to(root.resolve())
    except ValueError:
        reasons.append("command_script_escapes_repo")
    if not script_path.is_file():
        reasons.append("command_script_missing")
    component_type = _component_type(row)
    if not _script_allowed(component_ref, component_type):
        reasons.append(f"command_script_not_allowlisted_for::{component_type or 'unknown'}")
    allowed_args = ALLOWED_ARGS_BY_TYPE.get(component_type, set())
    args = tokens[2:]
    for arg in args:
        if arg not in allowed_args:
            reasons.append(f"command_arg_not_allowlisted::{arg}")
    if component_type == "harvester" and "--offline" not in args:
        reasons.append("harvester_requires_offline_arg")
    if "--write" not in args:
        reasons.append("command_requires_write_arg_for_auditable_outputs")
    return tokens, reasons


def public_command(cmd: list[str]) -> list[str]:
    if cmd and Path(cmd[0]).resolve() == Path(sys.executable).resolve():
        return ["python", *cmd[1:]]
    return cmd


def _run(root: Path, tokens: list[str]) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, *tokens[1:]]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root) if not env.get("PYTHONPATH") else str(root) + os.pathsep + env["PYTHONPATH"]
    env["LOGION_NO_NETWORK"] = "1"
    env["OC133_NO_NETWORK"] = "1"
    env["NO_NETWORK"] = "1"
    for key in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
        env.pop(key, None)
    return subprocess.run(
        cmd,
        cwd=root,
        env=env,
        text=True,
        capture_output=True,
        timeout=COMMAND_TIMEOUT_SECONDS,
    )


def unsupported_args(stderr: str) -> set[str]:
    marker = "unrecognized arguments:"
    if marker not in stderr:
        return set()
    tail = stderr.split(marker, 1)[1].strip()
    return {token for token in tail.split() if token.startswith("--")}


def retry_without_unsupported_args(root: Path, tokens: list[str], completed: subprocess.CompletedProcess[str]) -> tuple[subprocess.CompletedProcess[str], dict[str, Any] | None]:
    args = unsupported_args(completed.stderr)
    if not args:
        return completed, None
    retry_tokens = [token for token in tokens if token not in args]
    if retry_tokens == tokens or len(retry_tokens) < 2:
        return completed, None
    retry_completed = _run(root, retry_tokens)
    return retry_completed, {
        "reason": "legacy_cli_unrecognized_arguments",
        "removed_args": sorted(args),
        "original_returncode": completed.returncode,
        "original_stderr_tail": sanitize_text(root, completed.stderr[-1000:]),
        "retry_public_command": public_command([sys.executable, *retry_tokens[1:]]),
        "retry_returncode": retry_completed.returncode,
    }


def dispatch_action(
    root: Path,
    registry_payload: dict[str, Any],
    row: dict[str, Any],
    *,
    execute: bool,
) -> dict[str, Any]:
    tokens, rejection_reasons = validate_command(root, registry_payload, row)
    allowed = not rejection_reasons
    before_hash = tree_hash(root)
    result: dict[str, Any] = {
        "action_id": row.get("action_id"),
        "position": row.get("position"),
        "selected_position": row.get("selected_position"),
        "component_ref": row.get("component_ref"),
        "component_type": _component_type(row),
        "resource_class": row.get("resource_class"),
        "next_action": row.get("next_action"),
        "command": row.get("command"),
        "public_command": public_command([sys.executable, *tokens[1:]]) if tokens else [],
        "allowlist_pass": allowed,
        "rejection_reasons": rejection_reasons,
        "execute_requested": execute,
        "executed": False,
        "returncode": None,
        "stdout_tail": "",
        "stderr_tail": "",
        "parsed_payload": None,
        "command_success": False,
        "executor_success": False,
        "scientific_payload_found": False,
        "scientific_blocked": False,
        "scientific_blocker_total": 0,
        "scientific_blocker_reasons": [],
        "scientific_verdict": "NOT_EXECUTED",
        "scientific_pass": False,
        "action_outcome": "DRY_RUN_ALLOWED" if allowed else "REJECTED",
        "repo_hash_before": before_hash,
        "repo_hash_after": before_hash,
        "repo_hash_changed": False,
    }
    if not allowed:
        return result
    if not execute:
        return result

    retry_info = None
    try:
        completed = _run(root, tokens)
        completed, retry_info = retry_without_unsupported_args(root, tokens, completed)
    except subprocess.TimeoutExpired as exc:
        after_hash = tree_hash(root)
        result.update(
            {
                "executed": True,
                "returncode": None,
                "stderr_tail": sanitize_text(root, str(exc))[-4000:],
                "action_outcome": "COMMAND_TIMEOUT",
                "repo_hash_after": after_hash,
                "repo_hash_changed": after_hash["sha256"] != before_hash["sha256"],
            }
        )
        return result

    parsed = extract_json(completed.stdout)
    payload = scientific_payload(row, parsed)
    science = scientific_blockers(payload)
    structured_scientific_blocker = isinstance(payload, dict) and science["scientific_blocked"]
    command_success = completed.returncode == 0 or structured_scientific_blocker
    scientific_pass = completed.returncode == 0 and isinstance(payload, dict) and not science["scientific_blocked"]
    if not command_success:
        outcome = "COMMAND_FAILED"
    elif science["scientific_blocked"]:
        outcome = "SCIENTIFIC_BLOCKED" if completed.returncode == 0 else "SCIENTIFIC_BLOCKED_LEGACY_NONZERO"
    elif scientific_pass:
        outcome = "PASS"
    else:
        outcome = "EXECUTOR_SUCCESS_NO_SCIENCE_PAYLOAD"
    after_hash = tree_hash(root)
    result.update(
        {
            "executed": True,
            "returncode": completed.returncode,
            "stdout_tail": sanitize_text(root, completed.stdout[-4000:]),
            "stderr_tail": sanitize_text(root, completed.stderr[-4000:]),
            "parsed_payload": parsed,
            "retry_info": retry_info,
            "command_success": command_success,
            "executor_success": command_success,
            "scientific_payload_found": isinstance(payload, dict),
            "scientific_blocked": science["scientific_blocked"],
            "scientific_blocker_total": science["scientific_blocker_total"],
            "scientific_blocker_reasons": science["scientific_blocker_reasons"],
            "scientific_verdict": science["scientific_verdict"],
            "scientific_pass": scientific_pass,
            "action_outcome": outcome,
            "repo_hash_after": after_hash,
            "repo_hash_changed": after_hash["sha256"] != before_hash["sha256"],
        }
    )
    return result


def build_payload(
    root: Path,
    *,
    write: bool,
    execute: bool = False,
    max_actions: int | None = DEFAULT_MAX_ACTIONS,
    refresh_registry: bool = False,
) -> dict[str, Any]:
    registry_payload = load_registry_payload(root, refresh_registry=refresh_registry)
    selected = select_ranked_actions(registry_payload, max_actions=max_actions)
    results = [dispatch_action(root, registry_payload, row, execute=execute) for row in selected]
    rejected = [row for row in results if row["allowlist_pass"] is not True]
    executed = [row for row in results if row["executed"]]
    command_failures = [row for row in executed if row["command_success"] is not True]
    scientific_blocked = [row for row in executed if row["scientific_blocked"]]
    passed = [row for row in executed if row["scientific_pass"] is True]
    if rejected:
        verdict = "DISPATCH_REJECTED_UNSAFE_ACTIONS"
    elif command_failures:
        verdict = "DISPATCH_COMMAND_FAILURE"
    elif scientific_blocked:
        verdict = "DISPATCH_RAN_WITH_SCIENTIFIC_BLOCKERS"
    elif execute and executed:
        verdict = "DISPATCH_PASS"
    else:
        verdict = "DISPATCH_DRY_RUN_READY"
    payload: dict[str, Any] = {
        "schema_id": SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": utc_now(),
        "capability_owner": CAPABILITY_OWNER,
        "registry_report_ref": registry.REPORT_JSON_REL,
        "registry_payload_sha256": canonical_sha256(registry_payload),
        "registry_schema_id": registry_payload.get("schema_id"),
        "execute_requested": execute,
        "max_actions": max_actions,
        "selected_action_total": len(selected),
        "executed_action_total": len(executed),
        "rejected_action_total": len(rejected),
        "executor_success_total": sum(1 for row in executed if row["executor_success"]),
        "command_failure_total": len(command_failures),
        "scientific_blocked_total": len(scientific_blocked),
        "passed_action_total": len(passed),
        "selected_component_refs": [str(row.get("component_ref")) for row in selected],
        "rejected_component_refs": [str(row.get("component_ref")) for row in rejected],
        "scientific_blocked_component_refs": [str(row.get("component_ref")) for row in scientific_blocked],
        "passed_component_refs": [str(row.get("component_ref")) for row in passed],
        "results": results,
        "no_send_locks": registry_payload.get("no_send_locks", {}),
        "no_send": registry_payload.get("no_send"),
        "publish_allowed": registry_payload.get("publish_allowed"),
        "journal_submissions_allowed": registry_payload.get("journal_submissions_allowed"),
        "external_network_allowed": registry_payload.get("external_network_allowed"),
        "network_policy": "No network by default: only allowlisted local Python commands run; harvester commands require --offline; proxy variables are stripped from command environments.",
        "closure_policy": "Dispatcher PASS means command execution succeeded and the returned scientific payload is not blocked. A zero return code with blockers is recorded as executor_success plus SCIENTIFIC_BLOCKED, not PASS.",
        "verdict": verdict,
    }
    if write:
        write_json(root / REPORT_JSON_REL, payload)
        write_markdown(root / REPORT_MD_REL, payload)
    return payload


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# OC Core 1.3.3 Empirical Capability Dispatcher",
        "",
        f"Verdict: `{payload['verdict']}`",
        f"Execute requested: `{payload['execute_requested']}`",
        f"Selected actions: `{payload['selected_action_total']}`",
        f"Executed actions: `{payload['executed_action_total']}`",
        f"Rejected actions: `{payload['rejected_action_total']}`",
        f"Executor successes: `{payload['executor_success_total']}`",
        f"Command failures: `{payload['command_failure_total']}`",
        f"Scientific blockers: `{payload['scientific_blocked_total']}`",
        f"PASS actions: `{payload['passed_action_total']}`",
        "",
        payload["network_policy"],
        "",
        payload["closure_policy"],
        "",
        "## Cockpit Locks",
        "",
        "| Lock | Value |",
        "| --- | ---: |",
    ]
    locks = payload.get("no_send_locks") if isinstance(payload.get("no_send_locks"), dict) else {}
    for key in sorted(locks):
        lines.append(f"| `{key}` | `{locks[key]}` |")
    lines.extend(
        [
            "",
            "## Dispatch Results",
            "",
            "| Action | Component | Allowed | Executed | Return code | Outcome | Science verdict | Hash changed |",
            "| --- | --- | --- | --- | ---: | --- | --- | --- |",
        ]
    )
    for row in payload["results"]:
        lines.append(
            f"| `{row.get('action_id')}` | `{row.get('component_ref')}` | `{row['allowlist_pass']}` | "
            f"`{row['executed']}` | `{row['returncode']}` | `{row['action_outcome']}` | "
            f"`{row['scientific_verdict']}` | `{row['repo_hash_changed']}` |"
        )
    lines.extend(
        [
            "",
            "## Rejections",
            "",
        ]
    )
    rejected = [row for row in payload["results"] if row["allowlist_pass"] is not True]
    if not rejected:
        lines.append("- `none`")
    else:
        for row in rejected:
            reasons = ", ".join(f"`{reason}`" for reason in row["rejection_reasons"])
            lines.append(f"- `{row.get('component_ref')}`: {reasons}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Safely dispatch local OC133 empirical capabilities.")
    parser.add_argument("--root", default=str(repo_root()), help="repository root")
    parser.add_argument("--write", action="store_true", help="write JSON/MD cockpit reports")
    parser.add_argument("--execute", action="store_true", help="run selected allowlisted local commands")
    parser.add_argument("--refresh-registry", action="store_true", help="build registry payload in memory before dispatch")
    parser.add_argument("--max-actions", type=int, default=DEFAULT_MAX_ACTIONS, help="maximum ranked actions to select")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    max_actions = args.max_actions if args.max_actions >= 0 else None
    payload = build_payload(
        Path(args.root).resolve(),
        write=args.write,
        execute=args.execute,
        max_actions=max_actions,
        refresh_registry=args.refresh_registry,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if payload["rejected_action_total"] or payload["command_failure_total"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
