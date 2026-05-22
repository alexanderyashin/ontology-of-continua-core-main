"""Finite witnesses for OC 032 empirical/crown closure."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class DomainStatus(StrEnum):
    EMPIRICAL = "EMPIRICALLY_PROVED_WITH_EVIDENCE"
    DESCRIPTIVE = "PROVED_AS_DESCRIPTIVE_PROJECTION"
    NEEDS_DATA = "REQUIRES_NEW_LOCAL_DATA"


@dataclass(frozen=True)
class LocalEvidence:
    replay: bool
    validation: bool
    completion: bool
    blockers: int
    refs: int
    acceptance: bool
    falsifier: bool
    claim_ceiling: bool


@dataclass(frozen=True)
class CrownState:
    core_vocabulary: bool
    dependency_chain: bool
    local_evidence_or_condition: bool
    refuted_dependency: bool
    falsifier: bool


def evidence_complete(evidence: LocalEvidence) -> bool:
    return (
        evidence.replay
        and evidence.validation
        and evidence.completion
        and evidence.blockers == 0
        and evidence.refs > 0
        and evidence.acceptance
        and evidence.falsifier
        and evidence.claim_ceiling
    )


def domain_status(domain_id: str, claim_level: str, evidence: LocalEvidence) -> DomainStatus:
    if not evidence_complete(evidence):
        return DomainStatus.NEEDS_DATA
    if domain_id == "MATHEMATICS" or claim_level == "descriptive_only":
        return DomainStatus.DESCRIPTIVE
    if claim_level == "validated_predictive":
        return DomainStatus.EMPIRICAL
    return DomainStatus.NEEDS_DATA


def crown_core_only_promotable(crown: CrownState) -> bool:
    return (
        crown.core_vocabulary
        and crown.dependency_chain
        and crown.local_evidence_or_condition
        and not crown.refuted_dependency
        and crown.falsifier
    )


def main() -> None:
    complete = LocalEvidence(True, True, True, 0, 3, True, True, True)
    incomplete = LocalEvidence(True, True, True, 1, 3, True, True, True)

    assert domain_status("PHYSICS", "validated_predictive", complete) == DomainStatus.EMPIRICAL
    assert domain_status("BIOLOGY", "validated_predictive", complete) == DomainStatus.EMPIRICAL
    assert domain_status("MATHEMATICS", "descriptive_only", complete) == DomainStatus.DESCRIPTIVE
    assert domain_status("PHYSICS", "validated_predictive", incomplete) == DomainStatus.NEEDS_DATA

    core_only = CrownState(True, False, False, False, True)
    conditional = CrownState(True, True, True, False, True)
    bad_dependency = CrownState(True, True, True, True, True)

    assert not crown_core_only_promotable(core_only)
    assert crown_core_only_promotable(conditional)
    assert not crown_core_only_promotable(bad_dependency)

    print("OC 032 empirical witnesses: PASS")
    print("domain_empirical_witnesses=2")
    print("domain_descriptive_witnesses=1")
    print("crown_guard_witnesses=3")


if __name__ == "__main__":
    main()
