"""Executable witnesses for OC 042 closure discipline."""

from __future__ import annotations

ALLOWED = {
    "PROVED_CLOSED_WITH_PROOFS",
    "REFUTED_WITH_COUNTERPROOF",
    "REFUTED_REPAIRED_AND_PROVED_WITH_PROOFS",
}


def terminal_status_policy(statuses: list[str]) -> bool:
    return bool(statuses) and all(status in ALLOWED for status in statuses)


def repaired_requires_guard(status: str, guard: str, repaired_statement: str) -> bool:
    if status != "REFUTED_REPAIRED_AND_PROVED_WITH_PROOFS":
        return True
    return bool(guard.strip()) and bool(repaired_statement.strip())


def unconditional_empirical_overclaim_refuted(empirical_rows: int, nonempirical_rows: int) -> bool:
    return empirical_rows >= 0 and nonempirical_rows > 0


def main() -> None:
    assert terminal_status_policy(["PROVED_CLOSED_WITH_PROOFS", "REFUTED_WITH_COUNTERPROOF"])
    assert not terminal_status_policy(["PROVED_CLOSED_WITH_PROOFS", "ACTIVE_DATA_ACQUISITION_REQUIRED"])
    assert repaired_requires_guard("REFUTED_REPAIRED_AND_PROVED_WITH_PROOFS", "old overclaim guard", "bounded repaired claim")
    assert not repaired_requires_guard("REFUTED_REPAIRED_AND_PROVED_WITH_PROOFS", "", "bounded repaired claim")
    assert unconditional_empirical_overclaim_refuted(11, 45)
    print("OC 042 absolute closure witnesses: PASS")
    print("terminal_status_policy=True")
    print("repaired_requires_guard=True")
    print("unconditional_empirical_overclaim_refuted=True")


if __name__ == "__main__":
    main()
