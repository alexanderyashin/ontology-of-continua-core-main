"""Finite proof surface for the bounded OC central schema.

The theorem checked here is deliberately narrow:

If a task has no same-description repair satisfying its active constraints,
then the finite model has an exhaustive alternative:

1. some extension repair satisfies the constraints; or
2. no extension repair satisfies them, and the task collapses when the
   organization predicate requires successful constraint satisfaction.

This proves a bounded classification theorem. It does not prove the broad
sentence "every contradiction in every domain births a dimension or collapses".
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Iterable, Literal


Part = str
Decision = bool
Constraint = tuple[Part, Decision]
Repair = dict[Part, Decision]
Outcome = Literal[
    "SAME_DESCRIPTION_REPAIR",
    "DIMENSION_EXTENSION",
    "COLLAPSE",
    "NON_OC_UNRESOLVED",
]


@dataclass(frozen=True)
class Task:
    name: str
    parts: tuple[Part, ...]
    constraints: tuple[Constraint, ...]
    same_description_repairs: tuple[Repair, ...]
    extension_repairs: tuple[Repair, ...]
    organization_requires_success: bool


def satisfies(repair: Repair, constraints: Iterable[Constraint]) -> bool:
    return all(repair.get(part) is required for part, required in constraints)


def all_part_level_repairs(parts: tuple[Part, ...]) -> tuple[Repair, ...]:
    repairs: list[Repair] = []
    for decisions in product([False, True], repeat=len(parts)):
        repairs.append(dict(zip(parts, decisions)))
    return tuple(repairs)


def classify(task: Task) -> Outcome:
    if any(satisfies(repair, task.constraints) for repair in task.same_description_repairs):
        return "SAME_DESCRIPTION_REPAIR"

    if any(satisfies(repair, task.constraints) for repair in task.extension_repairs):
        return "DIMENSION_EXTENSION"

    if task.organization_requires_success:
        return "COLLAPSE"

    return "NON_OC_UNRESOLVED"


def archive_binary_task() -> Task:
    parts = ("public_policy_text", "private_personal_data")
    binary_repairs = (
        {"public_policy_text": True, "private_personal_data": True},
        {"public_policy_text": False, "private_personal_data": False},
    )
    return Task(
        name="archive_binary_mixed_obligation",
        parts=parts,
        constraints=(
            ("public_policy_text", True),
            ("private_personal_data", False),
        ),
        same_description_repairs=binary_repairs,
        extension_repairs=all_part_level_repairs(parts),
        organization_requires_success=True,
    )


def inconsistent_task() -> Task:
    parts = ("x",)
    all_repairs = all_part_level_repairs(parts)
    return Task(
        name="inconsistent_single_part_obligation",
        parts=parts,
        constraints=(("x", True), ("x", False)),
        same_description_repairs=all_repairs,
        extension_repairs=all_repairs,
        organization_requires_success=True,
    )


def existing_redaction_task() -> Task:
    parts = ("public_policy_text", "private_personal_data")
    enriched = {"public_policy_text": True, "private_personal_data": False}
    return Task(
        name="archive_existing_redaction_axis",
        parts=parts,
        constraints=(
            ("public_policy_text", True),
            ("private_personal_data", False),
        ),
        same_description_repairs=(enriched,),
        extension_repairs=all_part_level_repairs(parts),
        organization_requires_success=True,
    )


def main() -> None:
    assert classify(archive_binary_task()) == "DIMENSION_EXTENSION"
    assert classify(inconsistent_task()) == "COLLAPSE"
    assert classify(existing_redaction_task()) == "SAME_DESCRIPTION_REPAIR"

    print("OC25 bounded central schema check: PASS")
    print(f"Archive binary task: {classify(archive_binary_task())}")
    print(f"Inconsistent task: {classify(inconsistent_task())}")
    print(f"Existing redaction task: {classify(existing_redaction_task())}")


if __name__ == "__main__":
    main()
