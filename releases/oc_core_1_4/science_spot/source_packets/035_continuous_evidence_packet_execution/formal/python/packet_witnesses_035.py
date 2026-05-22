"""Finite witnesses for OC 035 packet gates."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ChapterProjection:
    packet_complete: bool
    empirical_claim: bool
    chapter_level_empirical_evidence: bool
    source_denies_empirical_promotion: bool


def formal_nonempirical_projection_closed(packet: ChapterProjection) -> bool:
    return packet.packet_complete and (not packet.empirical_claim) and packet.source_denies_empirical_promotion


def empirical_projection_closed(packet: ChapterProjection) -> bool:
    return packet.packet_complete and packet.empirical_claim and packet.chapter_level_empirical_evidence


@dataclass(frozen=True)
class CrownCandidate:
    named_statement: bool
    theorem_chain: bool
    no_refuted_dependency: bool
    falsifier: bool
    evidence_if_empirical: bool


def crown_stone_proved(candidate: CrownCandidate) -> bool:
    return (
        candidate.named_statement
        and candidate.theorem_chain
        and candidate.no_refuted_dependency
        and candidate.falsifier
        and candidate.evidence_if_empirical
    )


def full_empirical_closeout_allowed(packet_open_rows: int, empirical_upgrade_open_rows: int, promoted_rows_sound: bool) -> bool:
    return packet_open_rows == 0 and empirical_upgrade_open_rows == 0 and promoted_rows_sound


def main() -> None:
    k_projection = ChapterProjection(True, False, False, True)
    overclaim = ChapterProjection(True, True, False, True)
    empirical_ok = ChapterProjection(True, True, True, False)
    crown_partial = CrownCandidate(True, False, True, True, True)
    crown_ok = CrownCandidate(True, True, True, True, True)

    assert formal_nonempirical_projection_closed(k_projection)
    assert not empirical_projection_closed(k_projection)
    assert not empirical_projection_closed(overclaim)
    assert empirical_projection_closed(empirical_ok)
    assert not crown_stone_proved(crown_partial)
    assert crown_stone_proved(crown_ok)
    assert not full_empirical_closeout_allowed(0, 1, True)
    assert not full_empirical_closeout_allowed(1, 0, True)
    assert full_empirical_closeout_allowed(0, 0, True)

    print("OC 035 packet witnesses: PASS")
    print("nonempirical_projection_blocks_empirical_promotion=True")
    print("crown_partial_blocks_crown_promotion=True")
    print("closeout_requires_zero_packet_and_upgrade_open_rows=True")


if __name__ == "__main__":
    main()
