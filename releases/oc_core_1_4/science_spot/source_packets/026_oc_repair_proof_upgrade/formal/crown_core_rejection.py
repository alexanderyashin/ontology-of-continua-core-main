"""026 rejection artifact for crown stones as repaired core claims."""

from __future__ import annotations


REPAIRED_DEPENDENCIES = {
    "bounded_central_schema": True,
    "role_preserving_operator_independence": True,
    "k_ladder_reference_theorem": True,
    "law_scope_admissibility": True,
    "domain_projection_protocol": True,
}

REFUTED_STRONG_DEPENDENCIES = {
    "global_operator_minimality": False,
    "unique_exhaustive_k_count": False,
    "unconditional_dimension_collapse_law": False,
    "core_only_domain_validation": False,
}


def crown_as_full_strong_core_established() -> bool:
    return all(REFUTED_STRONG_DEPENDENCIES.values())


def future_crown_corollary_allowed() -> bool:
    return all(REPAIRED_DEPENDENCIES.values())


def main() -> None:
    assert not crown_as_full_strong_core_established()
    assert future_crown_corollary_allowed()
    print("026 crown core rejection: PASS")
    print("Strong crown-core wording rejected.")
    print("Future conditional crown corollaries remain allowed after separate theorem chains.")


if __name__ == "__main__":
    main()
