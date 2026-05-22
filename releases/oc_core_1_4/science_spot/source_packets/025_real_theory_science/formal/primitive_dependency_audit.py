"""Primitive non-circularity audit for OC25.

This is a small proof/check artifact for the exact claim:

The primitive package needed by the bounded central schema can be ordered
without defining contradiction, dimension extension, or collapse by appeal to
the central schema itself.
"""

from __future__ import annotations


DEFINITION_DEPENDENCIES: dict[str, set[str]] = {
    "part": set(),
    "decision": set(),
    "constraint": {"part", "decision"},
    "repair": {"part", "decision"},
    "description": {"part", "same_description_repair_class", "extension_repair_class"},
    "same_description_repair_class": {"repair"},
    "extension_repair_class": {"repair"},
    "organization_predicate": {"constraint", "repair"},
    "contradiction_trigger": {"constraint", "same_description_repair_class"},
    "dimension_extension_route": {"constraint", "extension_repair_class"},
    "collapse_route": {
        "constraint",
        "extension_repair_class",
        "organization_predicate",
    },
    "bounded_central_schema": {
        "contradiction_trigger",
        "dimension_extension_route",
        "collapse_route",
    },
}


PRIMITIVES_REQUIRED_BY_SCHEMA = {
    "part",
    "decision",
    "constraint",
    "repair",
    "description",
    "same_description_repair_class",
    "extension_repair_class",
    "organization_predicate",
    "contradiction_trigger",
    "dimension_extension_route",
    "collapse_route",
}


def has_cycle(graph: dict[str, set[str]]) -> bool:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        for dep in graph.get(node, set()):
            if visit(dep):
                return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(visit(node) for node in graph)


def definitions_depend_on_schema() -> set[str]:
    offenders = set()
    for term, deps in DEFINITION_DEPENDENCIES.items():
        if term != "bounded_central_schema" and "bounded_central_schema" in deps:
            offenders.add(term)
    return offenders


def required_terms_available() -> bool:
    return PRIMITIVES_REQUIRED_BY_SCHEMA <= set(DEFINITION_DEPENDENCIES)


def main() -> None:
    assert not has_cycle(DEFINITION_DEPENDENCIES)
    assert definitions_depend_on_schema() == set()
    assert required_terms_available()

    print("OC25 primitive dependency audit: PASS")
    print("Dependency graph is acyclic.")
    print("No primitive definition depends on bounded_central_schema.")
    print("All schema-required primitive terms are available.")


if __name__ == "__main__":
    main()
