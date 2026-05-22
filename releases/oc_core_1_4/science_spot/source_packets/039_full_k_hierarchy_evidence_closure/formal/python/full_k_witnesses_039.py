"""Finite witnesses for OC 039 evidence-acquisition gates."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EmpiricalPacket:
    source_bound_statement: bool
    lawful_dataset_manifest: bool
    checksum_recorded: bool
    replay_script: bool
    thresholds: bool
    falsifier: bool
    dependency_closure: bool
    verification: bool


def empirical_packet_closed(packet: EmpiricalPacket) -> bool:
    return (
        packet.source_bound_statement
        and packet.lawful_dataset_manifest
        and packet.checksum_recorded
        and packet.replay_script
        and packet.thresholds
        and packet.falsifier
        and packet.dependency_closure
        and packet.verification
    )


def lawful_full_closeout(active_acquisition_rows: int, remaining_obligations: int, closeout_flag: bool) -> bool:
    return active_acquisition_rows == 0 and remaining_obligations == 0 and closeout_flag


def main() -> None:
    acquired_seed_only = EmpiricalPacket(True, True, True, False, False, True, True, True)
    replay_closed = EmpiricalPacket(True, True, True, True, True, True, True, True)

    assert not empirical_packet_closed(acquired_seed_only)
    assert empirical_packet_closed(replay_closed)
    assert not lawful_full_closeout(63, 59, False)
    assert not lawful_full_closeout(1, 0, True)
    assert lawful_full_closeout(0, 0, True)

    print("OC 039 full K hierarchy witnesses: PASS")
    print("empirical_packet_requires_manifest_replay_thresholds=True")
    print("seed_acquisition_alone_is_not_empirical_closure=True")
    print("closeout_requires_zero_active_acquisition=True")


if __name__ == "__main__":
    main()
