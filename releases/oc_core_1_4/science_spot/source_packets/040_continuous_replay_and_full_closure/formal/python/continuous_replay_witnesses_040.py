"""Finite witnesses for OC 040 closeout and overpromotion gates."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ClosureRow:
    source_statement: bool
    proposition: bool
    lawful_dataset_or_proof: bool
    replay_or_proof: bool
    falsifier: bool
    dependency_closure: bool
    verification: bool


def promotable(row: ClosureRow) -> bool:
    return (
        row.source_statement
        and row.proposition
        and row.lawful_dataset_or_proof
        and row.replay_or_proof
        and row.falsifier
        and row.dependency_closure
        and row.verification
    )


def closeout_allowed(represented: int, open_rows: int, closeout_flag: bool) -> bool:
    return represented == 63 and open_rows == 0 and closeout_flag


def main() -> None:
    seed_only = ClosureRow(True, True, True, False, True, True, True)
    replay_closed = ClosureRow(True, True, True, True, True, True, True)
    no_falsifier = ClosureRow(True, True, True, True, False, True, True)

    assert not promotable(seed_only)
    assert promotable(replay_closed)
    assert not promotable(no_falsifier)
    assert not closeout_allowed(63, 1, True)
    assert not closeout_allowed(62, 0, True)
    assert closeout_allowed(63, 0, True)

    print("OC 040 continuous replay witnesses: PASS")
    print("seed_download_alone_is_not_promotable=True")
    print("promotion_requires_falsifier_and_replay=True")
    print("closeout_requires_63_represented_and_zero_open=True")


if __name__ == "__main__":
    main()
