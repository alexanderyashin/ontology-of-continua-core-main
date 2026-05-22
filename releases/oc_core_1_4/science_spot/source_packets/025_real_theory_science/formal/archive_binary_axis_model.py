"""Executable proof surface for OC25 archive binary-axis theorem.

This file intentionally proves only a tiny formal claim:

1. A whole-document binary public/private classifier cannot satisfy a mixed
   document whose public part must be released and private part withheld.
2. A part-level release/redaction axis can satisfy that same obligation.
3. An archive that already has the part-level axis is a countermodel to the
   overbroad reading "every contradiction births a new dimension or collapses".

The script is not evidence for a universal OC law. It is a checked finite model
for the first local theorem/countertheorem in campaign 025.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


Part = str
ReleaseDecision = bool

PUBLIC_POLICY_TEXT: Part = "public_policy_text"
PRIVATE_PERSONAL_DATA: Part = "private_personal_data"


OBLIGATIONS: Dict[Part, ReleaseDecision] = {
    PUBLIC_POLICY_TEXT: True,
    PRIVATE_PERSONAL_DATA: False,
}


BINARY_LABEL_SEMANTICS: Dict[str, Dict[Part, ReleaseDecision]] = {
    "PUBLIC": {
        PUBLIC_POLICY_TEXT: True,
        PRIVATE_PERSONAL_DATA: True,
    },
    "PRIVATE": {
        PUBLIC_POLICY_TEXT: False,
        PRIVATE_PERSONAL_DATA: False,
    },
}


ENRICHED_LABEL_SEMANTICS: Dict[str, Dict[Part, ReleaseDecision]] = {
    "RELEASE_PUBLIC_REDACT_PRIVATE": {
        PUBLIC_POLICY_TEXT: True,
        PRIVATE_PERSONAL_DATA: False,
    }
}


@dataclass(frozen=True)
class CheckResult:
    label: str
    satisfies: bool
    violated_parts: tuple[Part, ...]


def check_label(label: str, semantics: Dict[Part, ReleaseDecision]) -> CheckResult:
    violated = tuple(
        part
        for part, required_decision in OBLIGATIONS.items()
        if semantics[part] != required_decision
    )
    return CheckResult(label=label, satisfies=not violated, violated_parts=violated)


def binary_solutions() -> list[CheckResult]:
    return [
        check_label(label, semantics)
        for label, semantics in BINARY_LABEL_SEMANTICS.items()
        if check_label(label, semantics).satisfies
    ]


def enriched_solutions() -> list[CheckResult]:
    return [
        check_label(label, semantics)
        for label, semantics in ENRICHED_LABEL_SEMANTICS.items()
        if check_label(label, semantics).satisfies
    ]


def existing_redaction_countermodel() -> bool:
    """True means the overbroad universal claim is refuted.

    If redaction/review structure already exists, the mixed obligation is
    resolved by existing structure. At that event no new axis is born and the
    archive does not collapse.
    """

    already_has_redaction_axis = bool(enriched_solutions())
    no_event_dimension_birth = already_has_redaction_axis
    no_collapse = already_has_redaction_axis
    return already_has_redaction_axis and no_event_dimension_birth and no_collapse


def main() -> None:
    checked_binary = [
        check_label(label, semantics)
        for label, semantics in BINARY_LABEL_SEMANTICS.items()
    ]
    checked_enriched = [
        check_label(label, semantics)
        for label, semantics in ENRICHED_LABEL_SEMANTICS.items()
    ]

    assert binary_solutions() == [], checked_binary
    assert len(enriched_solutions()) == 1, checked_enriched
    assert existing_redaction_countermodel()

    print("OC25 archive theorem check: PASS")
    print(f"Binary solutions: {binary_solutions()}")
    print(f"Enriched solutions: {enriched_solutions()}")
    print("Overbroad central-principle countermodel: PASS")


if __name__ == "__main__":
    main()
