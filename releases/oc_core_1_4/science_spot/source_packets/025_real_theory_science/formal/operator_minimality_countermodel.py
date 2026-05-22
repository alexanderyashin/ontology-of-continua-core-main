"""Countermodel to strong OC operator minimality/uniqueness.

The checked claim refuted here is the strong reading:

The six source operators are a globally minimal or unique basis for finite OC
transitions.

Countermodel:

A single parameterized `rewrite` operator maps any finite state to any target
finite state. It can reproduce the same input-output transitions used as
witnesses for Birth, Differentiate, Stabilize, Project, Kill, and Repair.

This does not refute the usefulness of the six names as a semantic vocabulary.
It refutes only global minimality/uniqueness as a basis of finite transitions.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OCState:
    axes: int
    distinctions: int
    organization_preserved: bool
    description_level: int
    branch_alive: bool
    adequate: bool
    loss_recorded: bool


BASE = OCState(
    axes=0,
    distinctions=1,
    organization_preserved=False,
    description_level=0,
    branch_alive=True,
    adequate=False,
    loss_recorded=False,
)


def birth(state: OCState) -> OCState:
    return OCState(**{**state.__dict__, "axes": state.axes + 1})


def differentiate(state: OCState) -> OCState:
    return OCState(**{**state.__dict__, "distinctions": state.distinctions + 1})


def stabilize(state: OCState) -> OCState:
    return OCState(**{**state.__dict__, "organization_preserved": True})


def project(state: OCState) -> OCState:
    return OCState(
        **{
            **state.__dict__,
            "description_level": state.description_level + 1,
            "loss_recorded": True,
        }
    )


def kill(state: OCState) -> OCState:
    return OCState(**{**state.__dict__, "branch_alive": False})


def repair(state: OCState) -> OCState:
    return OCState(**{**state.__dict__, "adequate": True})


def rewrite(_: OCState, target: OCState) -> OCState:
    return target


SOURCE_OPERATORS = {
    "Birth": birth,
    "Differentiate": differentiate,
    "Stabilize": stabilize,
    "Project": project,
    "Kill": kill,
    "Repair": repair,
}


def main() -> None:
    for name, operator in SOURCE_OPERATORS.items():
        target = operator(BASE)
        simulated = rewrite(BASE, target)
        assert simulated == target, name

    print("OC25 operator minimality countermodel: PASS")
    print("A one-operator parameterized rewrite basis simulates all six finite witness transitions.")
    print("Strong global minimality/uniqueness of the six-operator basis is refuted.")


if __name__ == "__main__":
    main()
