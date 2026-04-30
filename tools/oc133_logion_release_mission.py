from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
WORK_ROOT = ROOT.parents[2]
PRIVATE_K7 = WORK_ROOT / "estra-private-work" / "logion" / "k7"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from release_machine import oc133_platinum, publication  # noqa: E402


def command(cmd: list[str], *, cwd: Path = ROOT, timeout: int = 300) -> dict[str, Any]:
    completed = subprocess.run(
        cmd,
        cwd=cwd,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=timeout,
    )
    return {
        "cmd": cmd,
        "cwd": str(cwd),
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout[-4000:],
        "stderr_tail": completed.stderr[-4000:],
    }


def run_historical_intent_preflight(output_ref: str) -> dict[str, Any]:
    script = PRIVATE_K7 / "spe" / "orchestrator" / "k6" / "query_logion_historical_intent_preflight_v1.py"
    if not script.exists():
        return {"state": "BLOCKED", "reason": "historical intent preflight script missing", "script": str(script)}
    request = (
        "OC Core 1.3.3 platinum release mission must reuse existing Logion Strategy HQ, "
        "institute director, research, IT, publication, review, LLM bridge, and factory/factory-of-factories "
        "capabilities instead of creating duplicate standalone supervisors."
    )
    result = command(
        [
            sys.executable,
            str(script),
            "--request-text",
            request,
            "--reuse-decision",
            "REPAIR_EXISTING",
            "--run-id",
            "OC_CORE_1_3_3_PLATINUM_RELEASE_MISSION_PREFLIGHT",
            "--output",
            output_ref,
        ],
        cwd=PRIVATE_K7,
        timeout=180,
    )
    state = "PASS" if result["returncode"] == 0 else "BLOCKED"
    return {"state": state, "command": result, "output_ref": output_ref}


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap and audit the Logion-owned OC Core 1.3.3 platinum release mission.")
    parser.add_argument("--write", action="store_true", help="Write mission packet, dispatch queue, cockpit, and trajectory certificate.")
    parser.add_argument("--run-preflight", action="store_true", help="Run private K6 historical-intent preflight and store the public evidence packet.")
    parser.add_argument("--run-publication", action="store_true", help="Run Publication capability to generate 1.3.3 no-send journal packages.")
    args = parser.parse_args()

    preflight = None
    if args.run_preflight:
        preflight_output = ROOT / oc133_platinum.MISSION_DIR_REL / "OC133_HISTORICAL_INTENT_PREFLIGHT.json"
        preflight = run_historical_intent_preflight(str(preflight_output))

    publication_index = None
    if args.run_publication:
        publication_index = publication.generate_submission_packages(ROOT, release_id=oc133_platinum.RELEASE_ID)

    audit = oc133_platinum.content_closure_audit(ROOT)
    refs = oc133_platinum.write_mission_outputs(ROOT, audit) if args.write else {}
    payload = {
        "schema_id": "OC133_LOGION_RELEASE_MISSION_RUN_v1",
        "mission_id": oc133_platinum.MISSION_ID,
        "release_id": oc133_platinum.RELEASE_ID,
        "version": oc133_platinum.VERSION,
        "state": audit["state"],
        "blocker_total": audit["blocker_total"],
        "next_automatic_action": audit["next_automatic_action"],
        "preflight": preflight,
        "publication_index": publication_index,
        "mission_refs": refs,
        "no_send": True,
        "publish_allowed": False,
        "journal_submissions_allowed": False,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if preflight is None or preflight.get("state") == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
