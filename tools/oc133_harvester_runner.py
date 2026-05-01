from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_ID = "OC133_HARVESTER_RUN_v1"
RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
CAPABILITY_OWNER = "Logion Research/EmpiricalScience"
HARVESTER_ROOT_REL = "validation/heldout/harvesters"
REPORT_JSON_REL = "reports/OC_CORE_1_3_3_HARVESTER_RUN.json"
REPORT_MD_REL = "reports/OC_CORE_1_3_3_HARVESTER_RUN.md"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def public_command(cmd: list[str]) -> list[str]:
    if cmd and Path(cmd[0]).resolve() == Path(sys.executable).resolve():
        return ["python", *cmd[1:]]
    return cmd


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


def discover_harvesters(root: Path) -> list[Path]:
    path = root / HARVESTER_ROOT_REL
    if not path.exists():
        return []
    return sorted(item for item in path.rglob("*_harvester.py") if item.is_file())


def run_harvester(root: Path, harvester: Path) -> dict[str, Any]:
    cmd = [sys.executable, rel(root, harvester), "--write", "--offline", "--allow-blocked-exit-zero"]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root) if not env.get("PYTHONPATH") else str(root) + os.pathsep + env["PYTHONPATH"]
    completed = subprocess.run(cmd, cwd=root, env=env, text=True, capture_output=True, timeout=300)
    compatibility_retry = False
    if completed.returncode == 2 and "unrecognized arguments: --allow-blocked-exit-zero" in completed.stderr:
        compatibility_retry = True
        cmd = [sys.executable, rel(root, harvester), "--write", "--offline"]
        completed = subprocess.run(cmd, cwd=root, env=env, text=True, capture_output=True, timeout=300)
    payload = extract_json(completed.stdout)
    return {
        "harvester_ref": rel(root, harvester),
        "command": public_command(cmd),
        "compatibility_retry_without_allow_blocked_exit_zero": compatibility_retry,
        "returncode": completed.returncode,
        "stdout_tail": sanitize_text(root, completed.stdout[-4000:]),
        "stderr_tail": sanitize_text(root, completed.stderr[-4000:]),
        "parsed_payload": payload,
        "parsed_json": isinstance(payload, dict),
    }


def int_field(payload: dict[str, Any] | None, *keys: str) -> int:
    if not isinstance(payload, dict):
        return 0
    for key in keys:
        value = payload.get(key)
        if isinstance(value, int) and not isinstance(value, bool):
            return value
    return 0


def build_payload(root: Path, *, write: bool) -> dict[str, Any]:
    harvesters = discover_harvesters(root)
    results = [run_harvester(root, harvester) for harvester in harvesters]
    command_failures = [row for row in results if row["returncode"] != 0]
    parsed = [row["parsed_payload"] for row in results if isinstance(row.get("parsed_payload"), dict)]
    candidate_total = sum(int_field(row, "candidate_pack_total", "candidate_total") for row in parsed)
    valid_total = sum(int_field(row, "valid_pack_total", "valid_candidate_pack_total") for row in parsed)
    blocker_total = sum(int_field(row, "blocker_total", "open_blocker_total", "blocked_domain_total") for row in parsed)
    payload = {
        "schema_id": SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "capability_owner": CAPABILITY_OWNER,
        "harvester_root_ref": HARVESTER_ROOT_REL,
        "harvester_total": len(harvesters),
        "harvester_refs": [rel(root, harvester) for harvester in harvesters],
        "command_failure_total": len(command_failures),
        "command_failure_refs": [row["harvester_ref"] for row in command_failures],
        "parsed_payload_total": len(parsed),
        "candidate_pack_total": candidate_total,
        "valid_pack_total": valid_total,
        "blocked_obligation_total": blocker_total,
        "results": results,
        "closure_policy": "Harvesters may create candidate evidence packs, but grand empirical closure is decided only by validation/grand_science/evidence_pack_factory.py after registry/source-separation/schema checks.",
        "no_send": True,
        "publish_allowed": False,
        "journal_submissions_allowed": False,
        "verdict": "HARVESTER_COMMAND_FAILURE" if command_failures else "HARVESTERS_RAN",
    }
    if write:
        write_json(root / REPORT_JSON_REL, payload)
        write_markdown(root / REPORT_MD_REL, payload)
    return payload


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# OC Core 1.3.3 Harvester Run",
        "",
        f"Verdict: `{payload['verdict']}`",
        f"Harvesters: `{payload['harvester_total']}`",
        f"Command failures: `{payload['command_failure_total']}`",
        f"Candidate packs: `{payload['candidate_pack_total']}`",
        f"Valid packs reported: `{payload['valid_pack_total']}`",
        f"Blocked obligations: `{payload['blocked_obligation_total']}`",
        "",
        payload["closure_policy"],
        "",
        "| Harvester | Return code | Parsed JSON | Candidate packs | Valid packs | Verdict |",
        "| --- | ---: | --- | ---: | ---: | --- |",
    ]
    for row in payload["results"]:
        parsed = row.get("parsed_payload") or {}
        lines.append(
            f"| `{row['harvester_ref']}` | `{row['returncode']}` | `{str(row['parsed_json']).lower()}` | "
            f"`{int_field(parsed, 'candidate_pack_total', 'candidate_total')}` | "
            f"`{int_field(parsed, 'valid_pack_total', 'valid_candidate_pack_total')}` | `{parsed.get('verdict', 'UNKNOWN')}` |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run OC133 held-out evidence harvesters.")
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
