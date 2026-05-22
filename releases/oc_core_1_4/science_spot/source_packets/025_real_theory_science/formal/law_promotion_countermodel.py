"""Countermodel to unconditional promotion of OC law-like statements.

The checked claim refuted here is:

An OC law-like sentence about contradiction tending toward dimension/collapse
may be promoted as an unconditional law without trigger and scope conditions.

Countermodel:

A mixed obligation exists, but the current archive description already has a
redaction/review structure that resolves it. The conflict is real as a task
pressure, but it does not cause event-level dimension birth and does not
collapse the archive. The unconditional law wording is therefore false.
"""

from __future__ import annotations


def mixed_obligation_exists() -> bool:
    return True


def existing_repair_satisfies_obligations() -> bool:
    release_public_policy_text = True
    release_private_personal_data = False
    return release_public_policy_text and not release_private_personal_data


def event_level_dimension_birth() -> bool:
    return False


def archive_collapse() -> bool:
    return False


def unconditional_law_claim_holds() -> bool:
    if mixed_obligation_exists():
        return event_level_dimension_birth() or archive_collapse()
    return True


def main() -> None:
    assert existing_repair_satisfies_obligations()
    assert not unconditional_law_claim_holds()

    print("OC25 law-promotion countermodel: PASS")
    print("Mixed obligation exists.")
    print("Existing repair satisfies the obligations.")
    print("No event-level dimension birth; no archive collapse.")
    print("Unconditional law promotion is refuted.")


if __name__ == "__main__":
    main()
