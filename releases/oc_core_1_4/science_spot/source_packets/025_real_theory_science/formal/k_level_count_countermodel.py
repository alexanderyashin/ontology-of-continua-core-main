"""Countermodel to strong K0-K12 uniqueness/exhaustiveness.

The checked claim refuted here is the strong reading:

K0-K12 is the unique, exhaustive, or minimal hierarchy count for OC.

Countermodel:

If the admissibility rule for a K hierarchy is strict monotone addition of
typed invariants, then an alternative hierarchy can split one multi-invariant
source level into two strict levels. Both chains satisfy the same monotone
criterion, but they have different counts. Therefore the K0-K12 count is not
forced by the invariant rule alone.
"""

from __future__ import annotations


InvariantSet = frozenset[str]


SOURCE_CHAIN: tuple[InvariantSet, ...] = (
    frozenset(),
    frozenset({"geometry"}),
    frozenset({"geometry", "field", "phase"}),
    frozenset({"geometry", "field", "phase", "reaction"}),
    frozenset({"geometry", "field", "phase", "reaction", "boundary"}),
)


ALTERNATIVE_CHAIN: tuple[InvariantSet, ...] = (
    frozenset(),
    frozenset({"geometry"}),
    frozenset({"geometry", "field"}),
    frozenset({"geometry", "field", "phase"}),
    frozenset({"geometry", "field", "phase", "reaction"}),
    frozenset({"geometry", "field", "phase", "reaction", "boundary"}),
)


def strict_monotone(chain: tuple[InvariantSet, ...]) -> bool:
    return all(left < right for left, right in zip(chain, chain[1:]))


def same_endpoint(left: tuple[InvariantSet, ...], right: tuple[InvariantSet, ...]) -> bool:
    return left[-1] == right[-1]


def main() -> None:
    assert strict_monotone(SOURCE_CHAIN)
    assert strict_monotone(ALTERNATIVE_CHAIN)
    assert same_endpoint(SOURCE_CHAIN, ALTERNATIVE_CHAIN)
    assert len(SOURCE_CHAIN) != len(ALTERNATIVE_CHAIN)

    print("OC25 K-level count countermodel: PASS")
    print(f"Source chain length: {len(SOURCE_CHAIN)}")
    print(f"Alternative chain length: {len(ALTERNATIVE_CHAIN)}")
    print("Both chains are strict monotone invariant extensions with the same endpoint.")
    print("Strong uniqueness/exhaustiveness of the K-level count is refuted.")


if __name__ == "__main__":
    main()
