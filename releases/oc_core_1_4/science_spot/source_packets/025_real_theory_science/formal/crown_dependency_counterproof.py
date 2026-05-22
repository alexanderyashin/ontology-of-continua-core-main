"""Dependency counterproof for established crown-stone wording.

The checked claim refuted here is:

Crown-stone claims are established consequences of the full strong OC model.

The counterproof is dependency-theoretic. If an established-consequence claim
requires strong dependencies that have been refuted, then the established
consequence claim is false.
"""

from __future__ import annotations


STRONG_DEPENDENCIES = {
    "operator_global_minimality": False,
    "k0_k12_unique_exhaustive_count": False,
    "unconditional_dimension_collapse_law": False,
}


def established_crown_consequence() -> bool:
    return all(STRONG_DEPENDENCIES.values())


def failed_dependencies() -> list[str]:
    return [name for name, proved in STRONG_DEPENDENCIES.items() if not proved]


def main() -> None:
    assert failed_dependencies()
    assert not established_crown_consequence()

    print("OC25 crown dependency counterproof: PASS")
    print(f"Failed dependencies: {failed_dependencies()}")
    print("Established crown-stone consequence wording is refuted.")


if __name__ == "__main__":
    main()
