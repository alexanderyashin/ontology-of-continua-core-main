from __future__ import annotations

from release_machine import core


def generate(release: str = core.RELEASE_ID, channel: str = "all") -> dict:
    return core.evaluate_release(release, channel, "dry-run", write=True)
