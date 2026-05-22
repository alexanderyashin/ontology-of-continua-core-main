"""Finite witnesses for OC 038 K3 cognition empirical upgrade gates."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CognitionSubclaim:
    exact_statement: bool
    proposition: bool
    local_dataset: bool
    replay_script: bool
    acceptance_thresholds: bool
    falsifier: bool
    dependency_closure: bool
    verification: bool


def empirical_cognition_subclaim_closed(subclaim: CognitionSubclaim) -> bool:
    return (
        subclaim.exact_statement
        and subclaim.proposition
        and subclaim.local_dataset
        and subclaim.replay_script
        and subclaim.acceptance_thresholds
        and subclaim.falsifier
        and subclaim.dependency_closure
        and subclaim.verification
    )


def full_k3_upgrade(all_subclaims_terminal: bool, ambiguous_open: int, roadside_open: int, promoted_rows_sound: bool) -> bool:
    return all_subclaims_terminal and ambiguous_open == 0 and roadside_open == 0 and promoted_rows_sound


def full_program_closeout(remaining_input_obligations: int, open_followups: int, promoted_rows_sound: bool) -> bool:
    return remaining_input_obligations == 0 and open_followups == 0 and promoted_rows_sound


def main() -> None:
    complete_dataset = CognitionSubclaim(True, True, True, True, True, True, True, True)
    missing_dataset = CognitionSubclaim(True, True, False, False, False, True, True, True)

    assert empirical_cognition_subclaim_closed(complete_dataset)
    assert not empirical_cognition_subclaim_closed(missing_dataset)
    assert not full_k3_upgrade(True, 1, 1, True)
    assert not full_k3_upgrade(True, 0, 1, True)
    assert full_k3_upgrade(True, 0, 0, True)
    assert not full_program_closeout(59, 4, True)
    assert full_program_closeout(0, 0, True)

    print("OC 038 K3 cognition witnesses: PASS")
    print("empirical_cognition_requires_local_dataset=True")
    print("empirical_cognition_requires_replay_and_thresholds=True")
    print("k3_full_upgrade_blocked_by_ambiguity_and_roadside_gaps=True")
    print("program_closeout_requires_zero_remaining_and_zero_followups=True")


if __name__ == "__main__":
    main()
