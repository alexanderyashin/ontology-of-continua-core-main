# OC Real Theory Science Lab Notebook 025

## Campaign Diagnosis

024 is rejected as proof-grade closure because it terminalized several claims
by boundary labels or exclusions. Those decisions are useful article hygiene,
but they are not proof or refutation of OC's internal model.

025 therefore restarts the scientific ledger with only two terminal statuses:

- `PROVED_WITH_PROOF`
- `REFUTED_WITH_COUNTERPROOF`

## Source Anchors

| Source | Role |
| --- | --- |
| `022/public_payload/chapter_sources/master_monograph/chapter_Candidate_Laws_and_Scope_Conditions.md` | Archive filing example and formal proof invitation |
| `022/public_payload/chapter_sources/master_monograph/chapter_Why_OC_Appears_at_This_Point_in_the_Lineage.md` | Central hypothesis wording and anti-universality warnings |
| `022/public_payload/chapter_sources/master_monograph/chapter_Why_the_Basic_Principle_Must_Work_at_Minimal_Substrate.md` | Minimal substrate and scope wording |
| `024/theory_conversion/OC_THEORY_CORE_NOTEBOOK_024.md` | Boundary attempt; not proof authority |

## Active Claim Queue

| Claim id | Subject | Current 025 state | Next action |
| --- | --- | --- | --- |
| `OC25-LOCAL-ARCHIVE-001` | Binary archive classification theorem | Terminal | Use as first local OC theorem surface |
| `OC25-CP-UNIVERSAL-001` | Broad universal reading of central principle | Terminal | Keep as boundary counterproof against overclaim |
| `OC25-CP-SCHEMA-001` | Bounded central schema | Terminal | Use only as bounded formal schema, not universal law |
| `OC25-PRIMITIVES-001` | Primitive package adequacy | Terminal | Use only for bounded schema; domain adequacy still needs local evidence |
| `OC25-OPERATORS-001` | Operator catalogue sufficiency/minimality | Terminal | Strong global minimality is refuted; six names remain optional vocabulary |
| `OC25-KLEVEL-001` | K-level distinctness/count | Terminal | Strong unique/exhaustive count is refuted |
| `OC25-LAWS-001` | Law-like statements | Terminal | Unconditional law-promotion wording is refuted |
| `OC25-CROWN-001` | Crown stones | Terminal | Established-consequence wording is refuted by failed dependencies |
| `OC25-DOMAIN-001` | Domain projections | Terminal | Core-only validation wording is refuted |

## Terminal Result 025-T001

Claim id:

`OC25-LOCAL-ARCHIVE-001`

Exact source-bound statement:

The Candidate Laws chapter states that a filing system using only two labels,
public and private, fails for a document that contains public policy text,
private personal data, and a statutory obligation to disclose part of the
record. It also says a formal model could prove that no binary assignment
satisfies all obligations while a richer label space does.

Formal proposition:

Let a document have two relevant parts:

- `p`: public policy text, required to be released;
- `q`: private personal data, required to be withheld.

A whole-document binary classifier has only two labels:

- `PUBLIC`, which releases all document parts;
- `PRIVATE`, which withholds all document parts.

Then no whole-document binary label satisfies both obligations. An enriched
classifier with part-level release decisions satisfies both obligations by
releasing `p` and withholding `q`.

Status:

`PROVED_WITH_PROOF`

Proof:

A binary whole-document classifier induces a constant release function on all
parts of the document. If the label is `PUBLIC`, both `p` and `q` are released.
That violates the constraint that `q` must be withheld. If the label is
`PRIVATE`, both `p` and `q` are withheld. That violates the constraint that
`p` must be released. These are the only binary labels, so no binary assignment
satisfies the mixed obligation.

An enriched classifier that records part-level release status assigns
`release(p)=true` and `release(q)=false`. This satisfies both obligations.
Therefore the binary continuum is inadequate for the mixed case, and a richer
classification axis is sufficient inside this formal model.

Executable artifact:

`formal/archive_binary_axis_model.py`

Falsifier check:

This theorem would be falsified by a binary whole-document label whose semantics
both releases `p` and withholds `q`. Such a label is not in the binary
public/private system. If an institution already has a redaction or review
axis, the theorem's binary-system hypothesis is false rather than the theorem
being refuted.

Dependency closure:

Depends only on the defined parts, constraints, label semantics, and exhaustive
case split over the two binary labels.

Independent verification:

The Python artifact enumerates the binary labels and confirms that the solution
set is empty, then checks that the enriched part-level classifier satisfies the
constraints.

## Terminal Result 025-R001

Claim id:

`OC25-CP-UNIVERSAL-001`

Exact statement refuted:

Every contradiction, merely by being a contradiction, necessarily produces a
new dimension or collapse.

Status:

`REFUTED_WITH_COUNTERPROOF`

Counterproof:

Consider the same mixed document in an archive whose current description
already contains `release`, `redact`, `restrict`, and `review` categories. The
document is processed by the existing redaction operator: release public policy
text and withhold private personal data. No new axis is born at this event,
and the archive does not collapse. The conflict is resolved by already
available structure.

Therefore the overbroad universal reading is false. The only viable central
principle must be bounded by an explicit trigger: the current description lacks
an admissible same-description repair that satisfies the active constraints.

Executable artifact:

`formal/archive_binary_axis_model.py`

Falsifier check:

The counterexample fails only if the broad claim is narrowed to unresolved
contradictions under a description with no adequate existing repair. That
narrowed claim is a different proposition and remains open as
`OC25-CP-SCHEMA-001`.

## Terminal Result 025-T002

Claim id:

`OC25-CP-SCHEMA-001`

Exact bounded statement:

If a task has no same-description repair satisfying its active constraints,
then either an extension repair satisfies the constraints, or no such extension
repair exists and the organization predicate fails when task organization
requires successful constraint satisfaction.

Status:

`PROVED_WITH_PROOF`

Proof:

Assume the trigger: no repair in the current description satisfies the active
constraints. Now inspect the extension repair class. By excluded middle, either
at least one extension repair satisfies the constraints, or none does. In the
first case, the task has the OC dimension-extension route. In the second case,
if the organization predicate requires successful satisfaction of the active
constraints, then the task cannot maintain that organization under the active
operation; this is the collapse route. These cases exhaust the bounded finite
model.

Executable artifact:

`formal/bounded_central_schema_model.py`

Falsifier check:

The theorem would be falsified by a task satisfying the trigger where no
same-description repair exists, no extension repair exists, successful
constraint satisfaction is required for organization, and yet organization
does not fail. That violates the explicit organization predicate used by the
bounded model. A task resolved by an existing repair is not a falsifier; it
fails the trigger.

Dependency closure:

Depends on `OC25-LOCAL-ARCHIVE-001` as the positive extension example and on
`OC25-CP-UNIVERSAL-001` as the boundary counterexample against universal
wording. It also depends on the explicitly defined repair classes and
organization predicate in the executable artifact.

Independent verification:

The Python artifact checks three cases: archive binary task routes to
`DIMENSION_EXTENSION`; inconsistent task routes to `COLLAPSE`; existing
redaction task routes to `SAME_DESCRIPTION_REPAIR`, proving that the broad
universal reading remains refuted and outside this theorem.

## Terminal Result 025-T003

Claim id:

`OC25-PRIMITIVES-001`

Exact bounded statement:

The primitive package needed by the bounded central schema can be ordered
without defining contradiction, dimension extension, or collapse by appeal to
the central schema itself.

Status:

`PROVED_WITH_PROOF`

Proof:

The formal dependency graph defines `constraint`, `repair`, `description`,
repair classes, and `organization_predicate` before the central schema.
`contradiction_trigger` depends on constraints and the same-description repair
class. `dimension_extension_route` depends on constraints and the extension
repair class. `collapse_route` depends on constraints, extension repairs, and
the organization predicate. Only after these terms are defined does
`bounded_central_schema` depend on them. Therefore the bounded schema can be
stated without defining its trigger or outcomes by the schema itself.

Executable artifact:

`formal/primitive_dependency_audit.py`

Falsifier check:

This result would be falsified by a dependency cycle or by any primitive
definition depending on `bounded_central_schema`. The executable audit checks
for both and finds none.

Dependency closure:

Depends on `OC25-CP-SCHEMA-001` only as the schema being typed; the primitive
definitions themselves are checked not to depend on it.

Independent verification:

The Python artifact verifies that the dependency graph is acyclic, no primitive
definition depends on the central schema, and all schema-required primitive
terms are present.

## Terminal Result 025-R002

Claim id:

`OC25-OPERATORS-001`

Exact strong statement refuted:

The six source operators Birth, Differentiate, Stabilize, Project, Kill, and
Repair form a globally minimal or unique operator basis for finite OC
transitions.

Status:

`REFUTED_WITH_COUNTERPROOF`

Counterproof:

In the finite transition model, each source operator is represented as a state
transition over a finite record of OC-relevant fields. A single parameterized
operator `rewrite(source, target)` maps any finite source state to any finite
target state. For each of the six source-operator witness transitions, choose
the corresponding target state produced by that source operator. The single
`rewrite` operator reproduces the same input-output transition.

Therefore the six-operator catalogue is not globally minimal or unique as a
basis for finite OC transitions. The six names may still be useful typed
semantic labels, but the stronger minimality claim is false.

Executable artifact:

`formal/operator_minimality_countermodel.py`

Falsifier check:

This counterproof would fail if `rewrite` could not reproduce at least one of
the six finite witness transitions. The executable artifact checks all six.

Dependency closure:

Depends only on the finite state representation and the explicitly defined
source-operator witness transitions.

Independent verification:

The Python artifact asserts that `rewrite(BASE, target)` equals the target for
Birth, Differentiate, Stabilize, Project, Kill, and Repair.

## Terminal Result 025-R003

Claim id:

`OC25-KLEVEL-001`

Exact strong statement refuted:

K0-K12 is the unique, exhaustive, or minimal hierarchy count forced by the OC
typed-invariant rule.

Status:

`REFUTED_WITH_COUNTERPROOF`

Counterproof:

Let a K hierarchy be admissible when each adjacent level strictly adds typed
invariants. A source-style chain can add `field` and `phase` together at one
physical level. An alternative chain can add `field` first and `phase` at the
next level. Both chains are strict monotone invariant extensions and reach the
same endpoint, but they have different counts. Therefore the invariant rule
does not force the K0-K12 count.

Executable artifact:

`formal/k_level_count_countermodel.py`

Falsifier check:

This counterproof would fail if the alternative chain were not strict monotone,
if it did not reach the same endpoint, or if it had the same count. The
executable artifact checks all three conditions.

Dependency closure:

Depends only on the typed-invariant criterion. It does not deny that adjacent
levels may be locally distinct when their invariants are explicitly stated.

Independent verification:

The Python artifact reports a source chain of length 5 and an alternative
chain of length 6 with the same endpoint and strict invariant growth.

## Terminal Result 025-R004

Claim id:

`OC25-LAWS-001`

Exact strong statement refuted:

An OC law-like sentence about contradiction tending toward dimension/collapse
may be promoted as an unconditional law without trigger and scope conditions.

Status:

`REFUTED_WITH_COUNTERPROOF`

Counterproof:

Use the mixed archive obligation again, but place it inside a current archive
description that already contains redaction/review structure. The mixed
obligation exists, and the existing repair satisfies it by releasing public
policy text while withholding private personal data. In this event no new axis
is born and the archive does not collapse. Therefore the unconditional law
wording is false.

Executable artifact:

`formal/law_promotion_countermodel.py`

Falsifier check:

This counterproof would fail if the existing repair did not satisfy the mixed
obligation, or if the event necessarily created a new axis or collapse. The
executable artifact checks the opposite.

Dependency closure:

Depends on the same archive model family already used by
`OC25-LOCAL-ARCHIVE-001` and `OC25-CP-UNIVERSAL-001`.

Independent verification:

The Python artifact asserts that a mixed obligation exists, existing repair
satisfies it, and unconditional dimension/collapse output is false.

## Terminal Result 025-R005

Claim id:

`OC25-CROWN-001`

Exact strong statement refuted:

Crown-stone claims are established consequences of the full strong OC model.

Status:

`REFUTED_WITH_COUNTERPROOF`

Counterproof:

An established-consequence claim requires its necessary theorem-chain
dependencies to be true. In 025, three strong dependencies have already been
refuted: global operator minimality, unique/exhaustive K0-K12 count, and
unconditional dimension/collapse law wording. Therefore any crown-stone claim
that depends on the full strong OC model is not an established consequence.

Executable artifact:

`formal/crown_dependency_counterproof.py`

Falsifier check:

This counterproof would fail if no required dependency had failed. The
executable artifact lists failed dependencies and verifies that established
crown-consequence status is false.

Dependency closure:

Depends on `OC25-OPERATORS-001`, `OC25-KLEVEL-001`, and `OC25-LAWS-001`.

Independent verification:

The Python artifact asserts that failed dependencies exist and that the
established crown consequence predicate is false.

## Terminal Result 025-R006

Claim id:

`OC25-DOMAIN-001`

Exact strong statement refuted:

The OC core theorem chain alone validates domain projections.

Status:

`REFUTED_WITH_COUNTERPROOF`

Counterproof:

Construct two projected cases with the same abstract OC signature:
`no_same_repair_then_extension`. In one case, local observables, local
falsifier, and empirical support are present. In the other, they are absent.
The core signature alone treats both as matching the same OC pattern, but only
the first is locally validated. Therefore the core theorem chain alone cannot
validate a domain projection.

Executable artifact:

`formal/domain_projection_countermodel.py`

Falsifier check:

This counterproof would fail if identical core signatures forced identical
local validation status. The executable artifact checks that the signatures
match while validation status differs.

Dependency closure:

Depends on the bounded central schema only as an abstract signature; the
counterproof shows why local domain evidence remains an independent obligation.

Independent verification:

The Python artifact asserts same abstract signature, supported status for one
case, unsupported status for the other, and false core-only validation.

## Attempt Log

| Attempt | Claim | Method | Result | Next action |
| --- | --- | --- | --- | --- |
| 025-A000 | Campaign reset | 024 audit | 024 statuses rejected as proof authority | Build strict 025 DB and formal front |
| 025-A001 | `OC25-LOCAL-ARCHIVE-001` | Exhaustive binary-label case split plus executable check | `PROVED_WITH_PROOF` | Use theorem to test bounded central schema |
| 025-A002 | `OC25-CP-UNIVERSAL-001` | Existing-redaction countermodel | `REFUTED_WITH_COUNTERPROOF` | Formalize bounded unresolved-trigger schema |
| 025-A003 | `OC25-CP-SCHEMA-001` | Exhaustive repair/extension/collapse case split | `PROVED_WITH_PROOF` | Audit primitive definitions for non-circular sufficiency |
| 025-A004 | `OC25-PRIMITIVES-001` | Dependency graph acyclicity audit | `PROVED_WITH_PROOF` | Rebuild operator claims as typed transition witnesses |
| 025-A005 | `OC25-OPERATORS-001` | One-operator rewrite countermodel | `REFUTED_WITH_COUNTERPROOF` | Split K-level distinctness from K-count/exhaustiveness |
| 025-A006 | `OC25-KLEVEL-001` | Alternative strict invariant chain | `REFUTED_WITH_COUNTERPROOF` | Recover law-like statements and test each one |
| 025-A007 | `OC25-LAWS-001` | Existing-repair law countermodel | `REFUTED_WITH_COUNTERPROOF` | Test crown-stone established-consequence wording |
| 025-A008 | `OC25-CROWN-001` | Failed-dependency counterproof | `REFUTED_WITH_COUNTERPROOF` | Test domain-projection validation wording |
| 025-A009 | `OC25-DOMAIN-001` | Same-signature/different-validation countermodel | `REFUTED_WITH_COUNTERPROOF` | Run DB and artifact integrity checks |
| 025-A010 | Integrity | DB query plus all executable artifacts | PASS: 9/9 terminal, 3 proved, 6 refuted, 0 bad statuses | Do not overclaim beyond 025 top-level internal queue |

## Next Action

Do not overclaim beyond 025:

The 025 top-level internal queue is terminal, but this is not a proof that
every sentence in the full OC corpus has been atomized. The honest scientific
status is:

- a bounded formal OC schema has proof support;
- the broad universal-law reading is refuted;
- strong operator minimality, unique K-count, unconditional law promotion,
  established crown-stone consequence, and core-only domain validation are
  refuted;
- future work must atomize remaining source-level prose claims before any
  "full corpus closure" claim is allowed.
