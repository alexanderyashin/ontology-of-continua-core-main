from __future__ import annotations


def plan(findings: list[dict]) -> list[dict]:
    return [{"finding": item, "automatic_repair_allowed": item.get("severity") not in {"CRITICAL", "HIGH"}} for item in findings]
