from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from oc133_manuscript_structure_transfer_lib import MAX_DEPTH, run_index, run_l1


ROOT = Path(__file__).resolve().parents[1]
TRANSFER_DIR = ROOT / "tools" / "oc133_manuscript_structure_transfers"


def run_step(command: list[str]) -> dict[str, object]:
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    stdout = completed.stdout.strip()
    stderr = completed.stderr.strip()
    try:
        payload = json.loads(stdout) if stdout else {}
    except json.JSONDecodeError:
        payload = {"raw_stdout": stdout}
    payload["returncode"] = completed.returncode
    if stderr:
        payload["stderr"] = stderr
    if completed.returncode != 0:
        payload["state"] = "FAIL"
    return payload


def run_transfers(*, write: bool) -> dict[str, object]:
    flag = "--write" if write else "--check"
    steps: list[dict[str, object]] = []
    l1_result = run_l1(write=write)
    steps.append(l1_result)
    if l1_result["state"] != "PASS":
        return {"state": "FAIL", "steps": steps}

    for depth in range(2, MAX_DEPTH + 1):
        script = TRANSFER_DIR / f"transfer_l{depth - 1:02d}_to_l{depth:02d}.py"
        result = run_step([sys.executable, str(script), flag])
        steps.append(result)
        if result.get("state") != "PASS":
            return {"state": "FAIL", "steps": steps}

    index_result = run_index(write=write)
    steps.append(index_result)
    state = "PASS" if all(step.get("state") == "PASS" for step in steps) else "FAIL"
    changed: list[str] = []
    missing: list[str] = []
    for step in steps:
        changed.extend(str(item) for item in step.get("changed", []))
        missing.extend(str(item) for item in step.get("missing", []))
    return {
        "changed": changed,
        "file_total": 22,
        "missing": missing,
        "state": state,
        "steps": steps,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Orchestrate separate OC133 manuscript structure transfers L01-L10.")
    parser.add_argument("--write", action="store_true", help="Write generated structure artifacts if changed.")
    parser.add_argument("--check", action="store_true", help="Check generated structure artifacts without writing.")
    args = parser.parse_args(argv)
    if not args.write and not args.check:
        args.check = True
    result = run_transfers(write=args.write)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["state"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
