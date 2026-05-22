"""Finite witnesses for OC 034 packet gates."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Packet:
    exact: bool
    proposition: bool
    observables: bool
    constraints: bool
    operators: bool
    invariants: bool
    falsifier: bool
    replay_surface: bool
    refs: bool
    dependencies: bool
    verification: bool


def complete(packet: Packet) -> bool:
    return all(packet.__dict__.values())


def empirical_allowed(packet: Packet, chapter_level_empirical_evidence: bool) -> bool:
    return complete(packet) and chapter_level_empirical_evidence


def full_closeout_allowed(remaining_open_rows: int) -> bool:
    return remaining_open_rows == 0


def main() -> None:
    packet = Packet(True, True, True, True, True, True, True, True, True, True, True)
    incomplete = Packet(True, True, True, True, True, True, False, True, True, True, True)

    assert complete(packet)
    assert not complete(incomplete)
    assert not empirical_allowed(packet, False)
    assert empirical_allowed(packet, True)
    assert not full_closeout_allowed(15)
    assert full_closeout_allowed(0)

    print("OC 034 packet witnesses: PASS")
    print("packet_cases=2")
    print("empirical_gate_cases=2")
    print("closeout_cases=2")


if __name__ == "__main__":
    main()
