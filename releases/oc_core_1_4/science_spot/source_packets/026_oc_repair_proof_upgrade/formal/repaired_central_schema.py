"""026 repaired central schema proof surface."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Literal


Outcome = Literal["SAME_REPAIR", "EXTENSION_REPAIR", "COLLAPSE"]


@dataclass(frozen=True)
class Task:
    constraints: tuple[tuple[str, bool], ...]
    same_repairs: tuple[dict[str, bool], ...]
    extension_repairs: tuple[dict[str, bool], ...]
    organization_requires_satisfaction: bool


def satisfies(repair: dict[str, bool], constraints: tuple[tuple[str, bool], ...]) -> bool:
    return all(repair.get(name) is value for name, value in constraints)


def all_repairs(parts: tuple[str, ...]) -> tuple[dict[str, bool], ...]:
    return tuple(dict(zip(parts, values)) for values in product([False, True], repeat=len(parts)))


def classify(task: Task) -> Outcome:
    if any(satisfies(repair, task.constraints) for repair in task.same_repairs):
        return "SAME_REPAIR"
    if any(satisfies(repair, task.constraints) for repair in task.extension_repairs):
        return "EXTENSION_REPAIR"
    if task.organization_requires_satisfaction:
        return "COLLAPSE"
    raise AssertionError("Outside repaired OC trigger: organization predicate was not declared.")


def archive_extension_case() -> Task:
    parts = ("public_text", "private_data")
    binary = (
        {"public_text": True, "private_data": True},
        {"public_text": False, "private_data": False},
    )
    return Task(
        constraints=(("public_text", True), ("private_data", False)),
        same_repairs=binary,
        extension_repairs=all_repairs(parts),
        organization_requires_satisfaction=True,
    )


def existing_repair_guard_case() -> Task:
    return Task(
        constraints=(("public_text", True), ("private_data", False)),
        same_repairs=({"public_text": True, "private_data": False},),
        extension_repairs=(),
        organization_requires_satisfaction=True,
    )


def collapse_case() -> Task:
    return Task(
        constraints=(("x", True), ("x", False)),
        same_repairs=({"x": True}, {"x": False}),
        extension_repairs=({"x": True}, {"x": False}),
        organization_requires_satisfaction=True,
    )


def main() -> None:
    assert classify(archive_extension_case()) == "EXTENSION_REPAIR"
    assert classify(existing_repair_guard_case()) == "SAME_REPAIR"
    assert classify(collapse_case()) == "COLLAPSE"
    print("026 repaired central schema: PASS")


if __name__ == "__main__":
    main()
