# OC Repair Proof Notebook 026

## Purpose

026 repairs OC by replacing refuted strong claims with proof-grade bounded
claims. It keeps 025 as diagnosis and guard rail.

## Repair Ledger

| Claim id | Old strong claim | 025 reason for failure | Repaired status |
| --- | --- | --- | --- |
| `OC26-CP-REPAIRED-001` | Every contradiction births dimension/collapse | Existing repair can resolve the conflict | `PROVED_REPAIRED_THEOREM` |
| `OC26-OP-REPAIRED-001` | Six operators are globally minimal/unique | Arbitrary rewrite simulates finite transitions | `PROVED_REPAIRED_THEOREM` |
| `OC26-K-REPAIRED-001` | K0-K12 is unique/exhaustive/minimal | Alternative strict invariant chains exist | `PROVED_REPAIRED_THEOREM` |
| `OC26-LAW-REPAIRED-001` | Law wording can be unconditional | Existing repair breaks unconditional law | `PROVED_REPAIRED_THEOREM` |
| `OC26-PROJ-REPAIRED-001` | Core signature validates domains alone | Same signature can have different local validation | `PROVED_REPAIRED_THEOREM` |
| `OC26-CROWN-CORE-001` | Crown stones are established by full strong model | Dependencies include refuted strong claims | `REJECTED_FROM_CORE` |

## Theorem 026-T001 - Repaired Central Schema

Repaired claim:

If active constraints cannot be satisfied by any admissible same-description
repair while preserving the organization predicate, then either an admissible
extension repair satisfies them or, if task organization requires satisfaction,
the organization predicate fails.

Artifact:

`formal/repaired_central_schema.py`

Result:

`PROVED_REPAIRED_THEOREM`

Article consequence:

Use "bounded central schema under explicit trigger." Do not use "universal law."

## Theorem 026-T002 - Role-Preserving Operator Independence

Repaired claim:

The six source operators are locally independent only relative to typed
role-preserving effect contracts. They are not globally minimal or unique.

Artifact:

`formal/role_preserving_operator_independence.py`

Result:

`PROVED_REPAIRED_THEOREM`

Article consequence:

Use "role-preserving operator vocabulary with local independence." Do not use
"globally minimal operator basis."

## Theorem 026-T003 - K-Ladder Reference Theorem

Repaired claim:

K0-K12 is a reference stratification. Given declared adjacent invariants, each
adjacent step is non-collapsible relative to those invariants. The count is not
unique or exhaustive.

Artifact:

`formal/k_ladder_reference_theorem.py`

Result:

`PROVED_REPAIRED_THEOREM`

Article consequence:

Use "reference ladder with declared invariants." Do not use "unique hierarchy
of reality."

## Theorem 026-T004 - Law Scope Admissibility

Repaired claim:

An OC law-like statement is article-admissible only when it names trigger,
scope, boundary, operator, outcome criterion, and falsifier.

Artifact:

`formal/law_scope_admissibility_theorem.py`

Result:

`PROVED_REPAIRED_THEOREM`

Article consequence:

Use "candidate law/schema with scope conditions." Do not use unconditional law
wording.

## Theorem 026-T005 - Domain Projection Validation Protocol

Repaired claim:

The OC core supplies projection obligations, not domain validation. A domain
projection is valid only with local observables, operator, falsifier, and
evidence package.

Artifact:

`formal/domain_projection_validation_protocol.py`

Result:

`PROVED_REPAIRED_THEOREM`

Article consequence:

Use "locally validated projection." Do not use "validated by OC core alone."

## Rejection 026-R001 - Crown Stones As Core

Rejected claim:

Crown stones are established core consequences of the full strong model.

Reason:

The full strong dependencies are refuted in 025. Until each crown-stone claim
has its own theorem chain from repaired 026 dependencies, it is not core.

Artifact:

`formal/crown_core_rejection.py`

Result:

`REJECTED_FROM_CORE`

## Integrity Closeout

026 repaired core status:

- repaired theorem rows: 5;
- rejected-from-core rows: 1;
- retained 025 refutation guards: 6;
- bad final statuses: 0.

All formal artifacts pass:

- `formal/repaired_central_schema.py`;
- `formal/role_preserving_operator_independence.py`;
- `formal/k_ladder_reference_theorem.py`;
- `formal/law_scope_admissibility_theorem.py`;
- `formal/domain_projection_validation_protocol.py`;
- `formal/crown_core_rejection.py`.

Honest result:

OC is repaired as a bounded formal theory of description repair under
unresolved constraint pressure. It is not repaired as a universal law, a unique
hierarchy of reality, a globally minimal operator algebra, or an automatic
domain-validation engine.
