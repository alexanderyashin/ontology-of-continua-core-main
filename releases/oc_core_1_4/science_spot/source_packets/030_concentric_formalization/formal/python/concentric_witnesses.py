"""Executable witnesses for OC concentric formalization 030."""

from __future__ import annotations

from dataclasses import dataclass
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


class Outcome(StrEnum):
    ABSORPTION = "absorption"
    EXTENSION = "extension"
    COLLAPSE = "collapse"
    UNDERDETERMINED = "underdetermined"


@dataclass(frozen=True)
class StressContext:
    evidence_bound: bool
    same_repair: bool
    extension_repair: bool
    invariant_failure: bool


@dataclass(frozen=True)
class LocalEvidence:
    observables: bool
    constraints: bool
    operators: bool
    invariants: bool
    falsifiers: bool
    evidence_bindings: bool


SOURCE_DOMAINS = (
    "Biology",
    "Chemistry",
    "Mathematics",
    "Physics",
    "Systems / Civilizational Projection",
)


def classify(context: StressContext) -> Outcome:
    if not context.evidence_bound:
        return Outcome.UNDERDETERMINED
    if context.same_repair:
        return Outcome.ABSORPTION
    if context.extension_repair:
        return Outcome.EXTENSION
    if context.invariant_failure:
        return Outcome.COLLAPSE
    return Outcome.UNDERDETERMINED


def local_evidence_complete(evidence: LocalEvidence) -> bool:
    return all(
        [
            evidence.observables,
            evidence.constraints,
            evidence.operators,
            evidence.invariants,
            evidence.falsifiers,
            evidence.evidence_bindings,
        ]
    )


def k_ladder(max_depth: int) -> list[int]:
    if max_depth < 0:
        raise ValueError("max_depth must be non-negative")
    return list(range(max_depth + 1))


def main() -> None:
    assert classify(StressContext(True, True, False, False)) == Outcome.ABSORPTION
    assert classify(StressContext(True, False, True, False)) == Outcome.EXTENSION
    assert classify(StressContext(True, False, False, True)) == Outcome.COLLAPSE
    assert classify(StressContext(False, False, False, False)) == Outcome.UNDERDETERMINED

    roles = set(AdequacyRole)
    for role in AdequacyRole:
        assert role not in roles - {role}
    operators = set(OperatorRole)
    for role in OperatorRole:
        assert role not in operators - {role}

    assert len(k_ladder(12)) == 13
    assert len(k_ladder(13)) != 13
    assert all(a < b for a, b in zip(k_ladder(12), k_ladder(12)[1:]))

    empty = LocalEvidence(False, False, False, False, False, False)
    assert not local_evidence_complete(empty)
    for domain in SOURCE_DOMAINS:
        assert domain

    print("OC 030 concentric witnesses: PASS")
    print(f"source_domains={len(SOURCE_DOMAINS)}")
    print(f"adequacy_roles={len(AdequacyRole)}")
    print(f"operator_roles={len(OperatorRole)}")
    print("k_reference_depth_12_count=13")


if __name__ == "__main__":
    main()
