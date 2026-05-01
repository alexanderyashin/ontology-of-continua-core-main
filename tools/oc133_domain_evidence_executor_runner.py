from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_ID = "OC133_DOMAIN_EVIDENCE_EXECUTOR_RUN_v1"
RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
CAPABILITY_OWNER = "Research/EmpiricalScience"
EXECUTOR_ROOT_REL = "validation/heldout/domain_evidence"
REPORT_JSON_REL = "reports/OC_CORE_1_3_3_DOMAIN_EVIDENCE_EXECUTOR_RUN.json"
REPORT_MD_REL = "reports/OC_CORE_1_3_3_DOMAIN_EVIDENCE_EXECUTOR_RUN.md"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def public_command(cmd: list[str]) -> list[str]:
    if cmd and Path(cmd[0]).name.lower().startswith("python"):
        return ["python", *cmd[1:]]
    if cmd and Path(cmd[0]).resolve() == Path(sys.executable).resolve():
        return ["python", *cmd[1:]]
    return cmd


def sanitize_text(root: Path, text: str) -> str:
    replacements = {
        str(root): "<REPO_ROOT>",
        str(root).replace("\\", "/"): "<REPO_ROOT>",
        str(Path.home()): "<LOCAL_HOME>",
        str(Path.home()).replace("\\", "/"): "<LOCAL_HOME>",
        str(Path(sys.executable)): "python",
        str(Path(sys.executable)).replace("\\", "/"): "python",
    }
    out = text
    for needle, replacement in replacements.items():
        if needle:
            out = out.replace(needle, replacement)
    return out


def extract_json(stdout: str) -> Any:
    text = stdout.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    for line in reversed(text.splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            continue
    return None


def load_executor_artifact_payload(root: Path, executor_ref: str) -> dict[str, Any] | None:
    artifact_root = root / "validation" / "heldout" / "grand_science"
    if not artifact_root.exists():
        return None
    matches: list[tuple[str, dict[str, Any]]] = []
    for path in sorted(artifact_root.rglob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(payload, dict):
            continue
        if payload.get("executor") != executor_ref:
            continue
        if "candidate_pack_total" not in payload and "domains" not in payload:
            continue
        matches.append((rel(root, path), payload))
    if not matches:
        return None
    ref, payload = matches[-1]
    payload = dict(payload)
    payload.setdefault("artifact_report_ref", ref)
    return payload


def payload_candidate_total(payload: dict[str, Any]) -> int:
    value = payload.get("candidate_pack_total")
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    domains = payload.get("domains")
    if isinstance(domains, list):
        return len([row for row in domains if isinstance(row, dict) and row.get("candidate_pack_ref")])
    return 0


def payload_valid_total(payload: dict[str, Any]) -> int:
    for key in ("valid_pack_total", "valid_candidate_pack_total", "valid_under_current_grand_schema_total", "valid_under_grand_gate_total"):
        value = payload.get(key)
        if isinstance(value, int) and not isinstance(value, bool):
            return value
    domains = payload.get("domains")
    if isinstance(domains, list):
        return sum(
            1
            for row in domains
            if isinstance(row, dict)
            and (
                row.get("valid_under_current_grand_schema") is True
                or row.get("candidate_pack_valid_under_current_grand_schema") is True
            )
        )
    return 0


def payload_is_blocked(payload: dict[str, Any]) -> bool:
    verdict = str(payload.get("verdict", "")).upper()
    if verdict.startswith("BLOCKED"):
        return True
    candidate_total = payload_candidate_total(payload)
    valid_total = payload_valid_total(payload)
    blocked_value = payload.get("blocked_pack_total", payload.get("blocked_candidate_pack_total"))
    if isinstance(blocked_value, int) and blocked_value > 0:
        return True
    return candidate_total > 0 and valid_total < candidate_total


def discover_executors(root: Path) -> list[Path]:
    executor_root = root / EXECUTOR_ROOT_REL
    if not executor_root.exists():
        return []
    return [
        path
        for path in sorted(executor_root.rglob("*_evidence_executor.py"))
        if path.is_file() and not path.name.startswith("_")
    ]


def _run(root: Path, cmd: list[str]) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(root) if not existing else str(root) + os.pathsep + existing
    return subprocess.run(
        cmd,
        cwd=root,
        env=env,
        text=True,
        capture_output=True,
        timeout=300,
    )


def run_command(root: Path, executor: Path) -> dict[str, Any]:
    standard_cmd = [
        sys.executable,
        rel(root, executor),
        "--write",
        "--allow-blocked-exit-zero",
    ]
    completed = _run(root, standard_cmd)
    compatibility_retry = False
    cmd = standard_cmd
    if completed.returncode == 2 and "unrecognized arguments: --allow-blocked-exit-zero" in completed.stderr:
        compatibility_retry = True
        cmd = [sys.executable, rel(root, executor), "--write"]
        completed = _run(root, cmd)
    parsed = extract_json(completed.stdout)
    parsed_payload = parsed if isinstance(parsed, dict) else None
    artifact_payload = load_executor_artifact_payload(root, rel(root, executor))
    effective_payload = parsed_payload or artifact_payload
    return {
        "executor_ref": rel(root, executor),
        "command": public_command(cmd),
        "standard_command": public_command(standard_cmd),
        "compatibility_retry_without_allow_blocked_exit_zero": compatibility_retry,
        "returncode": completed.returncode,
        "stdout_tail": sanitize_text(root, completed.stdout[-4000:]),
        "stderr_tail": sanitize_text(root, completed.stderr[-4000:]),
        "parsed_payload": parsed_payload,
        "artifact_payload": artifact_payload,
        "effective_payload": effective_payload,
        "parsed_json": isinstance(parsed, dict),
        "artifact_payload_found": isinstance(artifact_payload, dict),
        "command_pass": completed.returncode == 0,
    }


def build_payload(root: Path, *, write: bool) -> dict[str, Any]:
    executors = discover_executors(root)
    results = [run_command(root, executor) for executor in executors]
    failed = [row for row in results if row["returncode"] != 0]
    payloads = [row["effective_payload"] for row in results if isinstance(row.get("effective_payload"), dict)]
    blocked_total = sum(1 for payload in payloads if payload_is_blocked(payload))
    valid_pack_total = sum(payload_valid_total(payload) for payload in payloads)
    candidate_pack_total = sum(payload_candidate_total(payload) for payload in payloads)
    payload = {
        "schema_id": SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "capability_owner": CAPABILITY_OWNER,
        "executor_root_ref": EXECUTOR_ROOT_REL,
        "executor_total": len(executors),
        "executor_refs": [rel(root, path) for path in executors],
        "command_failure_total": len(failed),
        "command_failure_refs": [row["executor_ref"] for row in failed],
        "parsed_payload_total": sum(1 for row in results if isinstance(row.get("parsed_payload"), dict)),
        "artifact_payload_total": sum(1 for row in results if isinstance(row.get("artifact_payload"), dict)),
        "effective_payload_total": len(payloads),
        "candidate_pack_total": candidate_pack_total,
        "valid_pack_total": valid_pack_total,
        "blocked_executor_payload_total": blocked_total,
        "results": results,
        "write_requested": write,
        "no_send": True,
        "publish_allowed": False,
        "journal_submissions_allowed": False,
        "verdict": "EXECUTOR_COMMAND_FAILURE" if failed else "EXECUTORS_RAN_BLOCKERS_ALLOWED",
        "closure_policy": "This runner only executes capability-owned evidence generators. Grand empirical closure is decided later by validation/grand_science/evidence_pack_factory.py; executor existence or zero return code is not scientific closure.",
    }
    if write:
        write_json(root / REPORT_JSON_REL, payload)
        write_markdown(root / REPORT_MD_REL, payload)
    return payload


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# OC Core 1.3.3 Domain Evidence Executor Run",
        "",
        f"Verdict: `{payload['verdict']}`",
        f"Executors: `{payload['executor_total']}`",
        f"Command failures: `{payload['command_failure_total']}`",
        f"Candidate packs reported: `{payload['candidate_pack_total']}`",
        f"Valid packs reported: `{payload['valid_pack_total']}`",
        f"Blocked executor payloads: `{payload['blocked_executor_payload_total']}`",
        "",
        payload["closure_policy"],
        "",
        "| Executor | Return code | Parsed JSON | Candidate packs | Valid packs | Verdict |",
        "| --- | ---: | --- | ---: | ---: | --- |",
    ]
    for row in payload["results"]:
        parsed = row.get("effective_payload") or {}
        lines.append(
            f"| `{row['executor_ref']}` | `{row['returncode']}` | `{str(row['parsed_json']).lower()}` | "
            f"`{payload_candidate_total(parsed)}` | `{payload_valid_total(parsed)}` | `{parsed.get('verdict', 'UNKNOWN')}` |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Logion OC133 domain evidence executors.")
    parser.add_argument("--root", default=str(repo_root()))
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--allow-blocked-exit-zero", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    payload = build_payload(root, write=args.write)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if payload["command_failure_total"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
