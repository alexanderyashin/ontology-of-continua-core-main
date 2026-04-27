from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


SEVERITY_RANK = {
    "info": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
    "blocker": 5,
}


@dataclass(frozen=True)
class ParfitFinding:
    finding_id: str
    pass_id: str
    category: str
    severity: str
    blocking: bool
    title: str
    summary: str
    affected_refs: list[str] = field(default_factory=list)
    required_fixes: list[str] = field(default_factory=list)
    waiver_eligible: bool = False
    owner_waiver_required: bool = False
    details: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "pass_id": self.pass_id,
            "category": self.category,
            "severity": self.severity,
            "blocking": self.blocking,
            "title": self.title,
            "summary": self.summary,
            "affected_refs": self.affected_refs,
            "required_fixes": self.required_fixes,
            "waiver_eligible": self.waiver_eligible,
            "owner_waiver_required": self.owner_waiver_required,
            "details": self.details,
        }


@dataclass(frozen=True)
class RelationRScore:
    score: int
    label: str
    hard_break: bool
    missing_hard_invariants: list[str]
    violated_hard_invariants: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "label": self.label,
            "hard_break": self.hard_break,
            "missing_hard_invariants": self.missing_hard_invariants,
            "violated_hard_invariants": self.violated_hard_invariants,
        }
