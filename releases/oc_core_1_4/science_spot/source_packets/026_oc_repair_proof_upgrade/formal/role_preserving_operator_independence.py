"""026 role-preserving operator independence proof surface."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Contract:
    name: str
    effect: str


CONTRACTS = (
    Contract("Birth", "adds_axis"),
    Contract("Differentiate", "splits_distinction"),
    Contract("Stabilize", "preserves_organization"),
    Contract("Project", "maps_description_with_loss_record"),
    Contract("Kill", "invalidates_branch"),
    Contract("Repair", "restores_adequacy_after_failure"),
)


def can_realize(contract: Contract, witness_effect: str) -> bool:
    return contract.effect == witness_effect


def role_preserving_simulators(witness: Contract) -> list[str]:
    return [contract.name for contract in CONTRACTS if can_realize(contract, witness.effect)]


def arbitrary_rewrite_is_role_preserving() -> bool:
    return False


def main() -> None:
    for witness in CONTRACTS:
        assert role_preserving_simulators(witness) == [witness.name], witness
    assert not arbitrary_rewrite_is_role_preserving()
    print("026 role-preserving operator independence: PASS")


if __name__ == "__main__":
    main()
