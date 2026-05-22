"""026 K-ladder repaired reference theorem."""

from __future__ import annotations


K_LADDER: tuple[tuple[str, frozenset[str]], ...] = (
    ("K0", frozenset({"distinguishability"})),
    ("K1", frozenset({"distinguishability", "continuity"})),
    ("K2", frozenset({"distinguishability", "continuity", "field"})),
    ("K3", frozenset({"distinguishability", "continuity", "field", "reaction"})),
    ("K4", frozenset({"distinguishability", "continuity", "field", "reaction", "boundary"})),
    ("K5", frozenset({"distinguishability", "continuity", "field", "reaction", "boundary", "excitability"})),
    ("K6", frozenset({"distinguishability", "continuity", "field", "reaction", "boundary", "excitability", "internal_model"})),
    ("K7", frozenset({"distinguishability", "continuity", "field", "reaction", "boundary", "excitability", "internal_model", "institution"})),
    ("K8", frozenset({"distinguishability", "continuity", "field", "reaction", "boundary", "excitability", "internal_model", "institution", "infrastructure"})),
    ("K9", frozenset({"distinguishability", "continuity", "field", "reaction", "boundary", "excitability", "internal_model", "institution", "infrastructure", "theory_object"})),
    ("K10", frozenset({"distinguishability", "continuity", "field", "reaction", "boundary", "excitability", "internal_model", "institution", "infrastructure", "theory_object", "meta_theory"})),
    ("K11", frozenset({"distinguishability", "continuity", "field", "reaction", "boundary", "excitability", "internal_model", "institution", "infrastructure", "theory_object", "meta_theory", "operator_of_operator"})),
    ("K12", frozenset({"distinguishability", "continuity", "field", "reaction", "boundary", "excitability", "internal_model", "institution", "infrastructure", "theory_object", "meta_theory", "operator_of_operator", "global_semantic_coherence"})),
)


ALTERNATIVE_VALID_CHAIN = (
    frozenset({"distinguishability"}),
    frozenset({"distinguishability", "continuity"}),
    frozenset({"distinguishability", "continuity", "field"}),
    frozenset({"distinguishability", "continuity", "field", "reaction"}),
    frozenset({"distinguishability", "continuity", "field", "reaction", "boundary"}),
    frozenset({"distinguishability", "continuity", "field", "reaction", "boundary", "excitability"}),
    frozenset({"distinguishability", "continuity", "field", "reaction", "boundary", "excitability", "internal_model", "institution"}),
)


def strict_adjacent_noncollapse(chain: tuple[tuple[str, frozenset[str]], ...]) -> bool:
    return all(left[1] < right[1] for left, right in zip(chain, chain[1:]))


def has_alternative_partition() -> bool:
    source_prefix_endpoint = K_LADDER[7][1]
    return (
        all(left < right for left, right in zip(ALTERNATIVE_VALID_CHAIN, ALTERNATIVE_VALID_CHAIN[1:]))
        and ALTERNATIVE_VALID_CHAIN[-1] == source_prefix_endpoint
        and len(ALTERNATIVE_VALID_CHAIN) != 8
    )


def main() -> None:
    assert len(K_LADDER) == 13
    assert strict_adjacent_noncollapse(K_LADDER)
    assert has_alternative_partition()
    print("026 K-ladder reference theorem: PASS")


if __name__ == "__main__":
    main()
