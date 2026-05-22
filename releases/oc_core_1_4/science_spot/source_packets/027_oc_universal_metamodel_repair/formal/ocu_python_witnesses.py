"""Finite witnesses for OC-U 027.

The witnesses show why the old two-outcome fork was incomplete and why the
repaired universal metamodel needs four outcomes:

absorption, extension, collapse, and underdetermination.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Outcome(StrEnum):
    ABSORPTION = "absorption"
    EXTENSION = "extension"
    COLLAPSE = "collapse"
    UNDERDETERMINED = "underdetermined"


@dataclass(frozen=True)
class Context:
    name: str
    evidence_bound: bool
    same_description_repair: bool
    extension_repair: bool
    invariant_failure: bool
    local_instantiation: bool


def classify(context: Context) -> Outcome:
    if not context.evidence_bound:
        return Outcome.UNDERDETERMINED
    if context.same_description_repair:
        return Outcome.ABSORPTION
    if context.extension_repair:
        return Outcome.EXTENSION
    if context.invariant_failure:
        return Outcome.COLLAPSE
    return Outcome.UNDERDETERMINED


ABSORPTION_CASE = Context(
    name="archive_existing_redaction_repair",
    evidence_bound=True,
    same_description_repair=True,
    extension_repair=False,
    invariant_failure=False,
    local_instantiation=True,
)

EXTENSION_CASE = Context(
    name="binary_archive_requires_redaction_axis",
    evidence_bound=True,
    same_description_repair=False,
    extension_repair=True,
    invariant_failure=False,
    local_instantiation=True,
)

COLLAPSE_CASE = Context(
    name="unsatisfiable_task_invariant_failure",
    evidence_bound=True,
    same_description_repair=False,
    extension_repair=False,
    invariant_failure=True,
    local_instantiation=True,
)

UNDERDETERMINED_CASE = Context(
    name="domain_claim_without_observables",
    evidence_bound=False,
    same_description_repair=False,
    extension_repair=False,
    invariant_failure=False,
    local_instantiation=False,
)


def old_two_outcome_fork(context: Context) -> bool:
    return classify(context) in {Outcome.EXTENSION, Outcome.COLLAPSE}


def projection_validated(context: Context) -> bool:
    return context.local_instantiation and context.evidence_bound


def main() -> None:
    assert classify(ABSORPTION_CASE) == Outcome.ABSORPTION
    assert classify(EXTENSION_CASE) == Outcome.EXTENSION
    assert classify(COLLAPSE_CASE) == Outcome.COLLAPSE
    assert classify(UNDERDETERMINED_CASE) == Outcome.UNDERDETERMINED

    assert not old_two_outcome_fork(ABSORPTION_CASE)
    assert not projection_validated(UNDERDETERMINED_CASE)

    print("OC-U 027 finite witnesses: PASS")
    for case in [ABSORPTION_CASE, EXTENSION_CASE, COLLAPSE_CASE, UNDERDETERMINED_CASE]:
        print(f"{case.name}: {classify(case)}")
    print("Old two-outcome fork is incomplete because absorption is a valid OC-U outcome.")


if __name__ == "__main__":
    main()
