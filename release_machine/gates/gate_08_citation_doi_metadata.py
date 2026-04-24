from __future__ import annotations

from release_machine import core


GATE_ID = "gate_08_citation_doi_metadata"
TITLE = "Citation and DOI metadata"


def evaluate(release: str = core.RELEASE_ID, channel: str = "all", mode: str = "dry-run") -> dict:
    results = core._all_gate_results(core.repo_root(), release, channel, mode)
    for result in results:
        if result["gate_id"] == GATE_ID:
            return result
    return core.gate_result(GATE_ID, TITLE, "NOT_RUN", "INFO", "Gate was not included in the active registry.", executed=False)
