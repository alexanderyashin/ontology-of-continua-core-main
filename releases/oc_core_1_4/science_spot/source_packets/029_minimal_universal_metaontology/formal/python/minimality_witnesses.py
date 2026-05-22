"""Finite witnesses for OC-M 029 minimal universal metaontology.

The witnesses exercise the lower-bound reading of the theorem:
remove any required adequacy role or typed operator role and adequacy fails.
They also keep the K-ladder repair honest: K0-K12 can be a reference
instantiation, but the absolute count is not derived without a depth parameter.
"""

from __future__ import annotations

from enum import StrEnum


class AdequacyRole(StrEnum):
    OBSERVATION_COVERAGE = "observation_coverage"
    DISTINGUISHABILITY = "distinguishability"
    STATE_DYNAMICS = "state_dynamics"
    CONSTRAINT_PRESSURE = "constraint_pressure"
    SAME_REPAIR = "same_repair"
    EXTENSION = "extension"
    COLLAPSE = "collapse"
    UNDERDETERMINATION = "underdetermination"
    PROJECTION_NON_INFLATION = "projection_non_inflation"
    EVIDENCE_BINDING = "evidence_binding"
    COMPOSITIONAL_REFINEMENT = "compositional_refinement"


class OperatorRole(StrEnum):
    INTRODUCE = "introduce"
    DIFFERENTIATE = "differentiate"
    STABILIZE = "stabilize"
    PROJECT = "project"
    INVALIDATE = "invalidate"
    REPAIR = "repair"


def adequate(roles: set[AdequacyRole]) -> bool:
    return set(AdequacyRole).issubset(roles)


def operator_adequate(roles: set[OperatorRole]) -> bool:
    return set(OperatorRole).issubset(roles)


def k_ladder(max_depth: int) -> list[int]:
    if max_depth < 0:
        raise ValueError("max_depth must be non-negative")
    return list(range(max_depth + 1))


def check_role_minimality() -> None:
    full = set(AdequacyRole)
    assert adequate(full)
    for role in AdequacyRole:
        missing = full - {role}
        assert not adequate(missing), f"role unexpectedly eliminable: {role}"


def check_operator_minimality() -> None:
    full = set(OperatorRole)
    assert operator_adequate(full)
    for role in OperatorRole:
        missing = full - {role}
        assert not operator_adequate(missing), f"operator unexpectedly eliminable: {role}"


def check_k_ladder_repair() -> None:
    reference = k_ladder(12)
    assert len(reference) == 13
    assert all(a < b for a, b in zip(reference, reference[1:]))
    assert len(k_ladder(13)) != 13


def main() -> None:
    check_role_minimality()
    check_operator_minimality()
    check_k_ladder_repair()
    print("OC-M 029 minimality witnesses: PASS")
    print(f"adequacy_roles={len(AdequacyRole)}")
    print(f"operator_roles={len(OperatorRole)}")
    print("k_ladder_depth_12_count=13")
    print("absolute_k_count_guard=PASS")


if __name__ == "__main__":
    main()
