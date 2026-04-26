from __future__ import annotations

import json

from release_machine import core


def run(release: str = core.RELEASE_ID, channel: str = "all", max_iterations: int = 5) -> dict:
    iterations = []
    final = None
    for index in range(max(1, max_iterations)):
        summary = core.evaluate_release(release, channel, "dry-run", write=True)
        iterations.append({
            "iteration": index + 1,
            "release_state": summary["release_state"],
            "critical_findings": summary["critical_findings"],
            "high_findings": summary["high_findings"],
            "publish_allowed": summary["publish_allowed"],
        })
        final = summary
        if summary["release_state"] == "RELEASE_READY_NO_SEND":
            break
    payload = {
        "release_id": release,
        "channel": channel,
        "max_iterations": max_iterations,
        "iteration_total": len(iterations),
        "release_state": final["release_state"] if final else "NOT_RUN",
        "critical_findings": final["critical_findings"] if final else 0,
        "high_findings": final["high_findings"] if final else 0,
        "owner_approval_required": True,
        "global_no_send_lock": True,
        "publish_allowed": False,
        "iterations": iterations,
    }
    root = core.repo_root()
    dossier_dir = root / "release_machine" / "reports" / "latest"
    dossier_dir.mkdir(parents=True, exist_ok=True)
    json_path = dossier_dir / "RELEASE_SHIT_CONTROL_v1.3.2_latest.json"
    md_path = dossier_dir / "RELEASE_SHIT_CONTROL_v1.3.2_latest.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(
        "\n".join([
            "# Release Quality Control Loop: OC Core v1.3.2",
            "",
            f"Initial/final iteration total: `{payload['iteration_total']}`",
            f"Final release state: `{payload['release_state']}`",
            f"Critical findings: `{payload['critical_findings']}`",
            f"High findings: `{payload['high_findings']}`",
            "Publish allowed: `false`",
        ]) + "\n",
        encoding="utf-8",
    )
    return payload
