"""026 domain projection validation protocol."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Projection:
    name: str
    core_signature: bool
    local_observables: bool
    local_operator: bool
    local_falsifier: bool
    evidence_package: bool


def projection_validated(projection: Projection) -> bool:
    return all(
        (
            projection.core_signature,
            projection.local_observables,
            projection.local_operator,
            projection.local_falsifier,
            projection.evidence_package,
        )
    )


ARCHIVE_PROJECTION = Projection(
    "archive_projection",
    core_signature=True,
    local_observables=True,
    local_operator=True,
    local_falsifier=True,
    evidence_package=True,
)

CORE_ONLY_ANALOGY = Projection(
    "core_only_analogy",
    core_signature=True,
    local_observables=False,
    local_operator=False,
    local_falsifier=False,
    evidence_package=False,
)


def main() -> None:
    assert projection_validated(ARCHIVE_PROJECTION)
    assert not projection_validated(CORE_ONLY_ANALOGY)
    print("026 domain projection validation protocol: PASS")


if __name__ == "__main__":
    main()
