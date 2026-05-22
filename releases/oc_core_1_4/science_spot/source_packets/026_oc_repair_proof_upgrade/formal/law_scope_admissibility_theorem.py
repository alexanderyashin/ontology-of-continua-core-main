"""026 law scope/admissibility theorem."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LawCandidate:
    name: str
    trigger: bool
    scope: bool
    boundary: bool
    operator: bool
    outcome_criterion: bool
    falsifier: bool


def article_admissible(candidate: LawCandidate) -> bool:
    return all(
        (
            candidate.trigger,
            candidate.scope,
            candidate.boundary,
            candidate.operator,
            candidate.outcome_criterion,
            candidate.falsifier,
        )
    )


BOUNDED_CP = LawCandidate(
    "bounded_central_schema",
    trigger=True,
    scope=True,
    boundary=True,
    operator=True,
    outcome_criterion=True,
    falsifier=True,
)

UNCONDITIONAL_CP = LawCandidate(
    "unconditional_dimension_collapse_law",
    trigger=False,
    scope=False,
    boundary=False,
    operator=False,
    outcome_criterion=False,
    falsifier=False,
)


def main() -> None:
    assert article_admissible(BOUNDED_CP)
    assert not article_admissible(UNCONDITIONAL_CP)
    print("026 law scope admissibility theorem: PASS")


if __name__ == "__main__":
    main()
