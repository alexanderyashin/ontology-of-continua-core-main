from __future__ import annotations

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
    return {
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
