"""Countermodel to core-only validation of OC domain projections.

The checked claim refuted here is:

The OC core theorem chain alone validates domain projections.

Countermodel:

Two projected cases can share the same abstract OC signature while differing
in local observables, falsifier definition, or empirical support. A core
signature therefore cannot by itself validate the domain claim.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProjectedCase:
    name: str
    abstract_oc_signature: str
    local_observables_bound: bool
    local_falsifier_defined: bool
    empirical_support_present: bool


SUPPORTED_ARCHIVE = ProjectedCase(
    name="supported_archive_projection",
    abstract_oc_signature="no_same_repair_then_extension",
    local_observables_bound=True,
    local_falsifier_defined=True,
    empirical_support_present=True,
)


UNSUPPORTED_ANALOGY = ProjectedCase(
    name="unsupported_analogy_projection",
    abstract_oc_signature="no_same_repair_then_extension",
    local_observables_bound=False,
    local_falsifier_defined=False,
    empirical_support_present=False,
)


def core_signature_matches(left: ProjectedCase, right: ProjectedCase) -> bool:
    return left.abstract_oc_signature == right.abstract_oc_signature


def domain_validated(case: ProjectedCase) -> bool:
    return (
        case.local_observables_bound
        and case.local_falsifier_defined
        and case.empirical_support_present
    )


def core_only_validation_rule(case: ProjectedCase) -> bool:
    return case.abstract_oc_signature == "no_same_repair_then_extension"


def main() -> None:
    assert core_signature_matches(SUPPORTED_ARCHIVE, UNSUPPORTED_ANALOGY)
    assert domain_validated(SUPPORTED_ARCHIVE)
    assert not domain_validated(UNSUPPORTED_ANALOGY)
    assert core_only_validation_rule(UNSUPPORTED_ANALOGY)

    print("OC25 domain projection countermodel: PASS")
    print("Same abstract OC signature, different local validation status.")
    print("Core-only domain validation wording is refuted.")


if __name__ == "__main__":
    main()
