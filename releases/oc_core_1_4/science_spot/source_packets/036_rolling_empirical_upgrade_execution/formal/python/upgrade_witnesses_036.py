"""Finite witnesses for OC 036 upgrade gates."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Subclaim:
    exact_statement: bool
    proposition: bool
    evidence_match: bool
    falsifier: bool
    dependency_closure: bool
    verification: bool


def empirical_subclaim_closed(subclaim: Subclaim) -> bool:
    return (
        subclaim.exact_statement
        and subclaim.proposition
        and subclaim.evidence_match
        and subclaim.falsifier
        and subclaim.dependency_closure
        and subclaim.verification
    )


def full_chapter_upgrade(all_subclaims_terminal: bool, open_local_data_requirements: int, promoted_rows_sound: bool) -> bool:
    return all_subclaims_terminal and open_local_data_requirements == 0 and promoted_rows_sound


def full_program_closeout(remaining_input_obligations: int, open_followups: int, promoted_rows_sound: bool) -> bool:
    return remaining_input_obligations == 0 and open_followups == 0 and promoted_rows_sound


def main() -> None:
    benchmark_matched = Subclaim(True, True, True, True, True, True)
    formose_gap = Subclaim(True, True, False, True, True, True)

    assert empirical_subclaim_closed(benchmark_matched)
    assert not empirical_subclaim_closed(formose_gap)
    assert not full_chapter_upgrade(True, 1, True)
    assert full_chapter_upgrade(True, 0, True)
    assert not full_program_closeout(61, 1, True)
    assert full_program_closeout(0, 0, True)

    print("OC 036 upgrade witnesses: PASS")
    print("empirical_subclaim_requires_evidence_match=True")
    print("k1_full_upgrade_blocked_by_formose_raf_gap=True")
    print("program_closeout_requires_zero_remaining_and_zero_followups=True")


if __name__ == "__main__":
    main()
