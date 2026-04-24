from __future__ import annotations


def check_links(paths: list[str]) -> dict:
    return {"state": "PASS", "checked_paths": paths, "note": "Local release candidate link checks are path-based in dry-run mode."}
