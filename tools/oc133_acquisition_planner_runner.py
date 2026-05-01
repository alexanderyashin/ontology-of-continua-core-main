from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_ID = "OC133_ACQUISITION_PLANNER_RUN_v1"
RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
CAPABILITY_OWNER = "Logion IT/Research"
REPORT_JSON_REL = "reports/OC_CORE_1_3_3_ACQUISITION_PLANNER_RUN.json"
REPORT_MD_REL = "reports/OC_CORE_1_3_3_ACQUISITION_PLANNER_RUN.md"
PLANNER_GLOB = "tools/oc133_*_acquisition_planner.py"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def public_command(cmd: list[str]) -> list[str]:
    return ["python", *cmd[1:]] if cmd and Path(cmd[0]).name.lower().startswith("python") else cmd


def sanitize_text(root: Path, text: str) -> str:
    out = text
    for needle, replacement in {
        str(root): "<REPO_ROOT>",
        str(root).replace("\\", "/"): "<REPO_ROOT>",
        str(Path.home()): "<LOCAL_HOME>",
        str(Path.home()).replace("\\", "/"): "<LOCAL_HOME>",
        str(Path(sys.executable)): "python",
        str(Path(sys.executable)).replace("\\", "/"): "python",
    }.items():
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
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        return payload if isinstance(payload, dict) else None
    return None


def discover_planners(root: Path) -> list[Path]:
    return [
        path
        for path in sorted((root / "tools").glob("oc133_*_acquisition_planner.py"))
        if path.name != Path(__file__).name
    ]


def run_planner(root: Path, planner: Path) -> dict[str, Any]:
    cmd = [sys.executable, rel(root, planner), "--write", "--allow-blocked-exit-zero"]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root) if not env.get("PYTHONPATH") else str(root) + os.pathsep + env["PYTHONPATH"]
    completed = subprocess.run(cmd, cwd=root, env=env, text=True, capture_output=True, timeout=300)
    compatibility_retry = False
    if completed.returncode == 2 and "unrecognized arguments: --allow-blocked-exit-zero" in completed.stderr:
        compatibility_retry = True
        cmd = [sys.executable, rel(root, planner), "--write"]
        completed = subprocess.run(cmd, cwd=root, env=env, text=True, capture_output=True, timeout=300)
    payload = extract_json(completed.stdout)
    return {
        "planner_ref": rel(root, planner),
        "command": public_command(cmd),
        "compatibility_retry_without_allow_blocked_exit_zero": compatibility_retry,
        "returncode": completed.returncode,
        "stdout_tail": sanitize_text(root, completed.stdout[-4000:]),
        "stderr_tail": sanitize_text(root, completed.stderr[-4000:]),
        "parsed_payload": payload,
        "parsed_json": isinstance(payload, dict),
    }


def blocker_total(payload: dict[str, Any] | None) -> int:
    if not isinstance(payload, dict):
        return 0
    for key in ("blocker_total", "open_blocker_total", "blocked_domain_total"):
        value = payload.get(key)
        if isinstance(value, int) and not isinstance(value, bool):
            return value
    rows = payload.get("domains") or payload.get("rows") or []
    return sum(1 for row in rows if isinstance(row, dict) and row.get("status") != "READY")


def build_payload(root: Path, *, write: bool) -> dict[str, Any]:
    planners = discover_planners(root)
    results = [run_planner(root, planner) for planner in planners]
    command_failures = [row for row in results if row["returncode"] != 0]
    parsed = [row["parsed_payload"] for row in results if isinstance(row.get("parsed_payload"), dict)]
    payload = {
        "schema_id": SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "capability_owner": CAPABILITY_OWNER,
        "planner_glob": PLANNER_GLOB,
        "planner_total": len(planners),
        "planner_refs": [rel(root, planner) for planner in planners],
        "command_failure_total": len(command_failures),
        "command_failure_refs": [row["planner_ref"] for row in command_failures],
        "parsed_payload_total": len(parsed),
        "blocked_obligation_total": sum(blocker_total(row) for row in parsed),
        "results": results,
        "closure_policy": "Acquisition planners produce future evidence protocols only. They cannot close grand empirical or modern-science superiority gates without separately registered evidence packs and comparator results.",
        "no_send": True,
        "publish_allowed": False,
        "journal_submissions_allowed": False,
        "verdict": "PLANNER_COMMAND_FAILURE" if command_failures else "ACQUISITION_PLANNERS_RAN",
    }
    if write:
        write_json(root / REPORT_JSON_REL, payload)
        write_markdown(root / REPORT_MD_REL, payload)
    return payload


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# OC Core 1.3.3 Acquisition Planner Run",
        "",
        f"Verdict: `{payload['verdict']}`",
        f"Planners: `{payload['planner_total']}`",
        f"Command failures: `{payload['command_failure_total']}`",
        f"Blocked obligations reported: `{payload['blocked_obligation_total']}`",
        "",
        payload["closure_policy"],
        "",
        "| Planner | Return code | Parsed JSON | Blockers | Verdict |",
        "| --- | ---: | --- | ---: | --- |",
    ]
    for row in payload["results"]:
        parsed = row.get("parsed_payload") or {}
        lines.append(
            f"| `{row['planner_ref']}` | `{row['returncode']}` | `{str(row['parsed_json']).lower()}` | "
            f"`{blocker_total(parsed)}` | `{parsed.get('verdict', 'UNKNOWN')}` |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run OC133 official-data acquisition planners.")
    parser.add_argument("--root", default=str(repo_root()))
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--allow-blocked-exit-zero", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    payload = build_payload(root, write=args.write)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if payload["command_failure_total"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
