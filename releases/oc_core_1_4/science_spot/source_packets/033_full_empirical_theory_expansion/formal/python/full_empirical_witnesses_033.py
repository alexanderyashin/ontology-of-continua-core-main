"""Finite witnesses for OC 033 full empirical expansion gates."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EmpiricalEvidence:
    observables: bool
    constraints: bool
    operators: bool
    invariants: bool
    falsifier: bool
    refs: int
    replay: bool
    claim_ceiling: bool
    blockers: int


@dataclass(frozen=True)
class CrownChain:
    exact_statement: bool
    core_chain: bool
    no_refuted_dependency: bool
    proof_body: bool
    falsifier: bool
    local_evidence_if_empirical: bool


def empirically_proved(evidence: EmpiricalEvidence) -> bool:
    return (
        evidence.observables
        and evidence.constraints
        and evidence.operators
        and evidence.invariants
        and evidence.falsifier
        and evidence.refs > 0
        and evidence.replay
        and evidence.claim_ceiling
        and evidence.blockers == 0
    )


def crown_stone_proved(chain: CrownChain) -> bool:
    return (
        chain.exact_statement
        and chain.core_chain
        and chain.no_refuted_dependency
        and chain.proof_body
        and chain.falsifier
        and chain.local_evidence_if_empirical
    )


def closeout_allowed(open_rows: int, promoted_rows_sound: bool) -> bool:
    return open_rows == 0 and promoted_rows_sound


def main() -> None:
    complete = EmpiricalEvidence(True, True, True, True, True, 2, True, True, 0)
    missing_replay = EmpiricalEvidence(True, True, True, True, True, 2, False, True, 0)
    blocked = EmpiricalEvidence(True, True, True, True, True, 2, True, True, 1)

    assert empirically_proved(complete)
    assert not empirically_proved(missing_replay)
    assert not empirically_proved(blocked)

    crown_ok = CrownChain(True, True, True, True, True, True)
    crown_core_only = CrownChain(True, False, True, True, True, False)
    crown_bad_dep = CrownChain(True, True, False, True, True, True)

    assert crown_stone_proved(crown_ok)
    assert not crown_stone_proved(crown_core_only)
    assert not crown_stone_proved(crown_bad_dep)

    assert closeout_allowed(0, True)
    assert not closeout_allowed(1, True)
    assert not closeout_allowed(0, False)

    print("OC 033 full empirical witnesses: PASS")
    print("empirical_cases=3")
    print("crown_cases=3")
    print("closeout_cases=3")


if __name__ == "__main__":
    main()
