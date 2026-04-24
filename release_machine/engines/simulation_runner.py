from __future__ import annotations

from release_machine.core import repo_root, run_simulation_report


def run() -> dict:
    return run_simulation_report(repo_root())
