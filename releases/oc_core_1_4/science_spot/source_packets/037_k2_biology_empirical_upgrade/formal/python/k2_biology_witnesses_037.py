"""Finite witnesses for OC 037 K2 biology empirical upgrade gates."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BiologySubclaim:
    exact_statement: bool
    proposition: bool
    benchmark_evidence: bool
    falsifier: bool
    dependency_closure: bool
    verification: bool


def empirical_biology_subclaim_closed(subclaim: BiologySubclaim) -> bool:
    return (
        subclaim.exact_statement
        and subclaim.proposition
        and subclaim.benchmark_evidence
        and subclaim.falsifier
        and subclaim.dependency_closure
        and subclaim.verification
    )


def full_k2_upgrade(all_subclaims_terminal: bool, open_comparative_requirements: int, promoted_rows_sound: bool) -> bool:
    return all_subclaims_terminal and open_comparative_requirements == 0 and promoted_rows_sound


def full_program_closeout(remaining_input_obligations: int, open_followups: int, promoted_rows_sound: bool) -> bool:
    return remaining_input_obligations == 0 and open_followups == 0 and promoted_rows_sound


def main() -> None:
    benchmark_matched = BiologySubclaim(True, True, True, True, True, True)
    wound_gap = BiologySubclaim(True, True, False, True, True, True)

    assert empirical_biology_subclaim_closed(benchmark_matched)
    assert not empirical_biology_subclaim_closed(wound_gap)
    assert not full_k2_upgrade(True, 1, True)
    assert full_k2_upgrade(True, 0, True)
    assert not full_program_closeout(60, 2, True)
    assert full_program_closeout(0, 0, True)

    print("OC 037 K2 biology witnesses: PASS")
    print("empirical_biology_subclaim_requires_benchmark_evidence=True")
    print("k2_full_upgrade_blocked_by_comparative_gap=True")
    print("program_closeout_requires_zero_remaining_and_zero_followups=True")


if __name__ == "__main__":
    main()
