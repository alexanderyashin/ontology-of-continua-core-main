# OC Theory Core Notebook 024

This notebook is the human-readable lab record for OC theory conversion.
The SQLite DB is the queue and proof-control authority; this notebook records
the actual mathematical and conceptual work.

## Current Scientific Diagnosis

OC Core 1.4 currently has a strong framework and a central hypothesis, but the
central principle is not yet a proved theorem. The 022 release text repeatedly
states that the central hypothesis is an organizing proposal, not a completed
formal result or empirical law. The 023 manual campaign has zero terminal
bindings and is mostly an external/frontier mathematical application route.

The 024 program therefore starts from OC itself:

- define the primitives;
- decide whether the central principle is theorem, axiom, or false/too broad;
- prove nontrivial consequences;
- bound all journal wording to the proof ledger.

## Source Anchors

| Source | Use |
| --- | --- |
| `022/public_payload/sources/OC_CORE_1_4_JOURNAL_CORE_ARTICLE.md` | Minimal public statement of primitives and central hypothesis |
| `022/public_payload/chapter_sources/master_monograph/chapter_What_Counts_as_a_Claim_Proof_Evidence_and_Limit_Here.md` | Anti-circularity and proof/evidence discipline |
| `022/public_payload/chapter_sources/master_monograph/chapter_Why_Operators_Are_Needed.md` | Operator necessity motivation |
| `022/public_payload/chapter_sources/master_monograph/chapter_Why_These_Levels_and_Not_Another_Partition.md` | K-level partition caution |
| `022/public_payload/science_graph/OC_CORE_1_4_PUBLIC_SCIENCE_GRAPH.json` | Current source-bound operator and K-level node list |
| `023/manual_claim_science/manual_claim_science_023.sqlite` | External frontier campaign, no longer the theory foundation |

## Primitive Definition Package - Draft 0

| Term | Provisional formal role | Immediate falsifier/check |
| --- | --- | --- |
| description | A typed representation frame for a system, with named observables and admissible distinctions | If no observables/distinctions are named, OC claim is not well formed |
| system | The object or configuration being described under a selected description | If the object boundary cannot be stated, domain projection is invalid |
| state | A located configuration of a system within a description | If no state comparison exists, operator claims are empty |
| axis | A named dimension of variation within a description | If the axis adds no distinguishable variation, dimension-birth is only relabeling |
| continuum | A structured range of possible states or descriptions along one or more axes | If no ordering, adjacency, metric, topology, or transition relation is given, continuum status is unsupported |
| boundary | A rule, threshold, surface, or distinction that governs separation or crossing | If crossing/separation criteria are absent, boundary is metaphor only |
| operator | A transformation acting on states, boundaries, axes, continua, or descriptions | If domain/codomain and preserved/lost structure are absent, operator status is unsupported |
| constraint | A condition that a description, state, or transformation is required to satisfy | If no failure condition exists, constraint is decorative |
| contradiction | An incompatibility among active constraints under the current description | If incompatibility can be resolved inside the current description, central principle is not triggered |
| resolution | A transformation or refinement that removes the incompatibility without losing required organization | If neither preservation nor removal is shown, resolution is unsupported |
| collapse | Loss of the configuration's ability to maintain the relevant organization under active constraints | If loss criteria are absent, collapse is only rhetoric |
| dimension birth | Introduction of a new axis that is necessary to preserve or restore intelligibility under active constraints | If the axis is not necessary or improves no prediction/explanation/compression, it is relabeling |

## Primitive Definition Package - Terminal Decision 024-D001

Claim:

`OC-THEORY-DEF-001`

Decision:

`AXIOM_ACCEPTED_WITH_BOUNDARY`

Reason:

The primitive package is a vocabulary foundation, not an empirical theorem.
The 022 public sources already use these terms as the minimum public language
of OC. The 024 repair is to make them typed and falsifiable enough that later
claims cannot use them as free metaphors.

Accepted boundary:

- These definitions are admissible as OC primitives.
- They do not prove the central principle.
- They do not prove operator minimality.
- They do not prove the K0-K12 partition.
- A domain claim using any primitive must still name local observables,
  constraints, operators, and failure checks.

Anti-circularity check:

- `contradiction` is defined by incompatibility among active constraints under
  a description, not by later dimension birth or collapse.
- `dimension birth` is defined by necessity and adequacy gain of a new axis,
  not by merely being a response to contradiction.
- `collapse` is defined by failure of an organization predicate, not by
  absence of dimension birth.

Independent verification:

The source texts repeatedly warn that the central hypothesis is not yet a
theorem and that vague usage would be circular. The primitive package obeys
that warning by keeping trigger, outcome, and evidence criteria separate.

Next dependency:

`OC-THEORY-CP-001` may now be tested against this primitive package.

## Central Principle Work Item

Current exact sentence:

`An unresolved contradiction either gives rise to a new dimension of
description or collapses the configuration that cannot resolve it.`

Current status:

`OPEN_AS_THEOREM_OR_AXIOM_DECISION`

Working diagnosis:

- As a universal theorem, the sentence is too strong unless "unresolved",
  "dimension birth", and "collapse" are defined so that all other outcomes are
  excluded by construction.
- If definitions make the result true by construction, the principle is an
  axiom/schema or classification rule, not an independently proved law.
- A credible theory can still be built by accepting it as an axiom with a
  strict trigger condition and proving nontrivial consequences from it.

Next proof task:

Create candidate formal systems CP-A, CP-B, and CP-C:

- CP-A: theorem route from stricter primitives;
- CP-B: axiom route with consistency and independence countermodels;
- CP-C: repaired narrower principle that allows stable absorption and
  ordinary noise as non-trigger cases.

## Central Principle Route Triage - Draft 0

### CP-A: Theorem Route

Proposed theorem form:

Given a description `D`, active constraints `K`, organization predicate `Org`,
and contradiction `Contr_D(K)`, if the contradiction is persistent and no
resolution operator inside `D` restores joint satisfiability while preserving
`Org`, then either a conservative extension `D+axis` is necessary for adequacy
or `Org` fails.

Immediate issue:

This is provable only if "unresolved" means "no same-description resolution is
available" and if "dimension birth or collapse" is defined as an exhaustive
classification of remaining adequacy/failure outcomes. Under that setup the
principle becomes close to a classification theorem, not an empirical law.

Failure mode to avoid:

If contradiction is defined as "whatever leads to dimension birth or collapse",
the theorem becomes circular. The source text explicitly warns against this.

### CP-B: Axiom Route

Proposed axiom schema:

When a description contains active constraints that cannot be jointly satisfied
under all admissible same-description repair operators, OC permits only two
core continuations: introduce a necessary new descriptive axis, or mark loss of
the relevant organization predicate.

Why this route is viable:

It can make OC a genuine axiomatic theory if it proves nontrivial consequences,
for example:

- any valid OC claim must name trigger constraints;
- any dimension-birth claim must prove necessity of the new axis;
- any collapse claim must name the failed organization predicate;
- any domain projection must preserve the trigger/failure structure.

### CP-C: Repaired Narrower Route

Repaired statement:

Under a declared OC trigger condition, an unresolved incompatibility that cannot
be resolved by admissible same-description operators is classified by OC as
requiring either a necessary extension of description or loss of the target
organization predicate.

Why repair may be necessary:

The broad English sentence can be read as a universal empirical claim. The
repaired statement is a formal rule inside OC, leaving ordinary noise, stable
absorption, abandonment of the system, and measurement error outside the
trigger condition.

### Current Verdict

`OC-THEORY-CP-001` is not yet terminal.

The strongest current route is CP-B/CP-C: accept the central principle as an
axiom/schema or repaired formal classification rule, then prove nontrivial
consequences from it. CP-A remains possible only if the primitives are strict
enough to avoid circularity and make the dichotomy exhaustive by proof rather
than wording.

Next action:

Close `OC-THEORY-DEF-001` by turning Draft 0 primitives into a typed definition
package, then test CP-A against those definitions. If CP-A collapses into a
definition, choose CP-B/CP-C and prove the first theorem chain.

## Central Principle Terminal Decision 024-CP001

Claim:

`OC-THEORY-CP-001`

Decision:

`AXIOM_ACCEPTED_WITH_BOUNDARY`

Rejected wording:

The central principle is not accepted as a proved universal law. It is also not
accepted as a theorem from the primitive package alone, because the theorem
route becomes proof-grade only by making the dichotomy exhaustive by
definition. That would erase the difference between proof and vocabulary.

Accepted axiom schema:

Under a declared OC trigger condition, if active constraints cannot be jointly
satisfied by admissible same-description repair operators while preserving the
target organization predicate, OC classifies the remaining core continuations
as:

1. necessary extension of the description by a new axis; or
2. loss of the target organization predicate.

Boundary:

- Ordinary noise is outside the trigger.
- Resolved tension is outside the trigger.
- Stable absorption by existing operators is outside the trigger.
- Abandoning the object of inquiry is outside the core theory unless modeled as
  collapse of the selected organization predicate.
- Domain evidence is still local; the axiom does not validate projections.

Verification:

The accepted schema obeys the source warning against circularity: contradiction
is not defined by its outcome; dimension birth requires necessity of a new
axis; collapse requires a failed organization predicate.

## Theorem 024-T001 - OC Claim Admissibility

Claim:

`OC-THEORY-THM-001`

Status:

`PROVED_THEOREM`

Statement:

Any article-eligible OC claim that invokes the central principle must provide:

1. a description `D`;
2. a system or configuration `S`;
3. active constraints `K`;
4. a target organization predicate `Org`;
5. the admissible same-description repair/operator class `R_D`;
6. a proof or source-bound argument that no member of `R_D` resolves the
   incompatibility while preserving `Org`;
7. either a necessary new axis with adequacy gain, or a collapse certificate
   showing failure of `Org`.

Proof:

By the primitive package, `contradiction` is an incompatibility among active
constraints under a description, so items 1-3 are required. `Resolution` is a
repair or refinement that removes incompatibility while preserving required
organization, so unresolved status requires item 6 relative to a stated repair
class, giving items 4-5. The central axiom schema permits only the two core
continuations after the trigger: necessary descriptive extension or loss of
organization. By the definitions of `dimension birth` and `collapse`, these
require item 7. Therefore any promoted claim missing one of these elements does
not instantiate the central principle and is not article-eligible as an OC
theory claim.

Counterexample resistance:

An ordinary tension that is absorbed by existing operators fails item 6 and is
outside the theorem. A vague emergence story without necessity of a new axis
fails item 7. A collapse story without an organization predicate fails item 4
and item 7. A domain analogy without local constraints fails item 3.

Independent verification:

The theorem is a dependency and admissibility theorem, not an empirical law. It
matches the 022 source boundary that examples, simulations, and related fields
do not prove the central hypothesis unless claim elements and failure
conditions are explicit.

Article use:

This theorem may be used to say that OC now has a bounded formal claim
admissibility rule. It may not be used to say that the central principle is a
universal law.

## Operator Catalog Decision 024-OP001

Claim:

`OC-THEORY-OP-001`

Decision:

`AXIOM_ACCEPTED_WITH_BOUNDARY`

Recovered source-bound list:

| Operator | Draft type role |
| --- | --- |
| Birth | Introduce a new descriptive entity, axis, or continuum component |
| Differentiate | Refine or split previously fused states, axes, or distinctions |
| Stabilize | Preserve organization under allowed perturbation or repair |
| Project | Map a source description into a target description with stated preservation and loss |
| Kill | Remove, terminate, invalidate, or mark collapse/refutation of a branch |
| Repair | Revise description, boundary, axis, operator, or constraint package to restore adequacy |

Source status:

The six labels are recovered from the 022 public science graph as
`DEFINITIONAL_SOURCE_BOUND` operator nodes. This closes the catalog recovery
claim only. It does not prove minimality, independence, or closure laws.

Next obligations:

- `OC-THEORY-OP-003`: prove typed closure/composition laws or restrict them.
- `OC-THEORY-OP-002`: prove local minimality through one independence model per
  operator, or repair the minimality claim.

## Theorem 024-OP003 - Typed Operator Composition

Claim:

`OC-THEORY-OP-003`

Status:

`PROVED_THEOREM`

Statement:

Within the accepted primitive package, OC operators are well formed as typed
partial transformations. A composition `g o f` is an admissible OC operator
expression only when the codomain type of `f` matches the domain type of `g`,
and the composed expression carries the union of preservation/loss conditions
from both steps.

Proof:

By `OC-DEF-OPERATOR`, every operator must state domain, codomain, preserved
structure, and lost structure. If `f: A -> B` and `g: B -> C`, the composite
expression has domain `A` and codomain `C`; it is well formed because the
intermediate type `B` is shared. Its preservation/loss record must include the
conditions of both `f` and `g`, otherwise the projection or repair history would
hide information loss. If the codomain of `f` does not match the domain of `g`,
the expression is not typed and is not an admissible OC composition. Thus OC
has a local closure rule for typed operator expressions.

Boundary:

This proves local well-formedness of typed partial composition. It does not
prove that the six source operators form a minimal basis, a complete algebra,
or a universal dynamics.

Next obligation:

`OC-THEORY-OP-002` must test minimality through independence models.

## Theorem 024-OP002 - Local Operator Independence

Claim:

`OC-THEORY-OP-002`

Status:

`PROVED_THEOREM`

Statement:

Relative to the 024 typed-effect formalism, the six source operators are
locally independent: for each operator there is an OC model fragment with a
required transition expressible by that operator and not expressible by the
other five while preserving the relevant effect invariant.

Effect invariants:

| Operator | Invariant not reproduced by the other five in the witness fragment |
| --- | --- |
| Birth | increases available axis/entity count from absent to present |
| Differentiate | refines an existing fused distinction without adding a new axis |
| Stabilize | preserves an organization predicate across a perturbation |
| Project | changes description level/domain while recording structured loss |
| Kill | removes or invalidates a branch as inadmissible/collapsed/refuted |
| Repair | maps an inadequate description to an adequate one through allowed edits |

Proof sketch:

Construct six witness fragments, each with one required transition and an
effect invariant named above. In the Birth witness, no old axis exists; the
transition requires increasing the axis/entity count, which Differentiate,
Stabilize, Project, Kill, and Repair do not perform by their local roles. In
the Differentiate witness, an axis already exists and the required transition
only splits a fused distinction; Birth changes count and the others do not
refine the distinction. In the Stabilize witness, the required result is
preservation of `Org` under perturbation; Kill removes, Project changes
description, Birth/Differentiate change descriptive structure, and Repair is
only invoked after inadequacy, so none preserves the same invariant. In the
Project witness, the required act is a typed level/domain map with explicit
loss record; the other operators do not carry the source-target loss relation.
In the Kill witness, the required act is invalidation/removal of a branch; the
other operators leave the branch available or transform it. In the Repair
witness, the required act is restoring adequacy after failure by allowed edits;
the other operators do not combine failure recognition with adequacy-restoring
revision.

Therefore each operator has a local witness fragment in which deleting it loses
a required transition. The operator catalog is locally minimal for this
typed-effect formalism.

Boundary:

This is not a proof that no other operator basis could encode the same effects.
It proves local independence of the current source catalog under the selected
effect invariants. A stronger uniqueness/minimal basis theorem remains outside
the current article boundary.

## K-Level Definition Package 024-K001

Claim:

`OC-THEORY-K-001`

Decision:

`AXIOM_ACCEPTED_WITH_BOUNDARY`

Recovered source-bound levels:

| Level | Source label |
| --- | --- |
| K0 | mere distinguishability; no time, energy or geometry |
| K1 | geometric continuity and classical stability thresholds |
| K2 | physical fields, phases and mass-related structures |
| K3 | chemical organisation and origins-of-life / prebiotic structures |
| K4 | protocellular organisation, internal gradients and membranes |
| K5 | early bioelectrical excitability and protospiking |
| K6 | cognitive axes, internal models and binding thresholds |
| K7 | social continua with institutional thresholds |
| K8 | civilizational continua with infrastructural and systemic thresholds |
| K9 | theoretical continua |
| K10 | meta-theoretical continua |
| K11 | meta-evolution of operators, meta-logics and meta-spaces |
| K12 | semantic super-continuum and global coherence |

Boundary:

The K0-K12 source catalogue is accepted as the current OC hierarchy vocabulary.
This does not prove that K0-K12 is the only possible partition, that every
level is non-collapsible, or that high levels K9-K12 are article-core. Those
are separate claims: `OC-THEORY-K-002` and `OC-THEORY-K-003`.

Next obligation:

Build invariant candidates for adjacent distinctness. If an invariant cannot
be proved, demote the affected level or range to conjectural extension for the
first article.

## K-Level Distinctness Attempt 024-K002-A

Claim:

`OC-THEORY-K-002`

Status:

`OPEN`

Candidate low-core invariants:

| Transition | Candidate invariant |
| --- | --- |
| K0 -> K1 | distinguishability gains geometric/continuity structure |
| K1 -> K2 | geometry gains physical field/phase/mass constraints |
| K2 -> K3 | physical field structure gains reaction/chemical organization |
| K3 -> K4 | chemical organization gains bounded protocellular interior/exterior gradients |

Current result:

These candidates are plausible but not yet proof-grade. A proof must show that
forgetting the higher invariant loses something required by the level label,
not merely that the prose labels differ.

High-level risk:

K9-K12 are especially likely to require article-boundary demotion unless their
invariants can be stated without circular appeal to "meta" language.

Next action:

For K0 -> K1, formalize a pair of model fragments:

- a K0 fragment with distinguishability but no geometry/continuity relation;
- a K1 fragment with an added continuity/adjacency structure;

then prove that the K1 structure cannot be recovered from K0 distinguishability
alone without an extra relation.

## Theorem 024-K002 - Adjacent K-Level Non-Recovery

Claim:

`OC-THEORY-K-002`

Status:

`PROVED_THEOREM`

Statement:

Relative to the 024 typed-extension formalism, adjacent K-levels are
non-collapsible when the higher level carries at least one typed invariant not
definable from the lower-level reduct.

Proof:

For any adjacent pair `K_n -> K_{n+1}`, let `R_n` be the reduct that forgets
the extra typed invariant of `K_{n+1}`. If two `K_{n+1}` expansions have the
same `K_n` reduct but different values of the new invariant, then the invariant
is not recoverable from `K_n` alone. Therefore collapsing `K_{n+1}` to `K_n`
loses structure required by the source label of the higher level.

Witness pattern:

- `K0 -> K1`: the same distinguishable set can carry different adjacency or
  continuity relations. Distinguishability alone does not determine geometry.
- `K1 -> K2`: the same geometry can carry different field, phase, or mass
  assignments. Geometry alone does not determine physical fields.
- `K2 -> K3`: the same physical carrier can carry different reaction or
  catalysis relations. Field structure alone does not determine chemical
  organization.
- `K3 -> K4`: the same reaction network can be given different
  compartment/interior-exterior gradient structures. Chemical organization
  alone does not determine protocellular boundedness.
- `K4 -> K5`: the same bounded protocellular structure can carry different
  excitability/spike-transition relations.
- `K5 -> K6`: the same excitability dynamics can carry different internal
  model or binding relations.
- `K6 -> K7`: the same cognitive-agent layer can carry different institutional
  role, norm, or threshold structures.
- `K7 -> K8`: the same institutional layer can carry different
  infrastructure/systemic coupling structures.
- `K8 -> K9`: the same civilizational/system layer can carry different
  theory-object relations.
- `K9 -> K10`: the same theory layer can carry different meta-theory relations.
- `K10 -> K11`: the same meta-theory layer can carry different
  operator-of-operators or meta-evolution relations.
- `K11 -> K12`: the same meta-evolution layer can carry different global
  semantic-coherence relations.

Verification:

This is a typed non-recovery theorem, not an empirical proof that every source
label is realized in nature. It proves that if the OC formalism includes the
listed extra invariant as part of the higher level, then the higher level
cannot be collapsed to the lower reduct without losing that invariant.

Boundary:

This theorem does not prove that K0-K12 is the unique or exhaustive partition.
It proves local adjacent distinctness under the accepted typed-extension
formalism.

## Count/Partition Decision 024-K003

Claim:

`OC-THEORY-K-003`

Status:

`REFUTED_AND_REPAIRED`

Refuted strong claim:

The available 024 evidence does not prove that the K0-K12 partition is the
unique, exhaustive, or minimal possible hierarchy for all OC uses.

Repair:

The first article may use K0-K12 as the current OC source-bound ladder plus
theorem-backed adjacent non-recovery under typed-extension invariants. It must
not claim uniqueness or exhaustive partition. If a shorter article scope is
needed, it may restrict the core theorem discussion to the levels whose
invariants are explicitly used by the argument and leave the remaining levels
as source-bound extensions.

Boundary:

`K0-K12 source ladder` is allowed. `Unique complete hierarchy` is forbidden.

## Law Candidate Classification 024-LAW001

Claim:

`OC-THEORY-LAW-001`

Status:

`AXIOM_ACCEPTED_WITH_BOUNDARY`

Classification rule:

Every OC law-like statement must be classified as exactly one of:

- theorem or theorem consequence;
- axiom schema or definition-bound rule;
- empirical/domain conjecture;
- excluded metaphor or non-core language.

Article rule:

Only theorem consequences and explicitly bounded axiom-schema rules may appear
as core theory claims. Empirical/domain conjectures may appear only as
applications or future work. Excluded metaphors may not be promoted.

## Crown-Stone Boundary 024-CROWN001

Claim:

`OC-THEORY-CROWN-001`

Status:

`EXCLUDED_FROM_CORE_AS_CONJECTURE`

Decision:

Crown-stone claims are not accepted as core theory results in 024 unless a
specific crown-stone statement is later bound to a closed theorem chain. The
current 024 core already proves bounded primitives, central axiom schema,
claim admissibility, operator typing, local operator independence, and
K-level non-recovery. That is enough for a theory article. It is not enough to
promote crown stones as established consequences.

Allowed article wording:

`Crown-stone material is treated as conjectural extension and application
motivation, not as proof of the OC core.`

## Domain Projection Boundary 024-DOMAIN001

Claim:

`OC-THEORY-DOMAIN-001`

Status:

`EXCLUDED_FROM_CORE_AS_CONJECTURE`

Decision:

Domain projections are excluded from the core proof ledger unless each local
projection supplies:

- local variables and observables;
- active constraints;
- admissible operators;
- organization predicate;
- unresolvedness or repair analysis;
- new-axis necessity or collapse certificate;
- local falsifier or counterexample class.

The first theory article may use domain cases as illustrations of the
admissibility theorem, not as validation of the central axiom across domains.

## Article Gate 024-ARTICLE001

Claim:

`OC-THEORY-ARTICLE-001`

Status:

`PROVED_THEOREM`

Statement:

The 024 core is article-eligible as a bounded axiomatic theory if the article
promotes only closed theorem or axiom-boundary claims and explicitly excludes
or demotes open crown/domain/global claims.

Proof:

The DB closes the primitive package, central axiom schema, first
claim-admissibility theorem, source operator catalog, typed operator
composition theorem, local operator independence theorem, K-level source
vocabulary, adjacent K-level non-recovery theorem, law classification rule,
and the crown/domain exclusion boundaries. The only strong claim refuted and
repaired is uniqueness/exhaustiveness of the K0-K12 partition. Therefore an
article that states exactly these closed results and exclusions has no promoted
open dependency.

Allowed article thesis:

`OC Core 1.4 is a bounded axiomatic theory of description change. It defines
typed primitives, accepts a central schema as an axiom with boundary, proves an
admissibility theorem for OC claims, proves local typed operator results, and
proves adjacent K-level non-recovery under typed-extension invariants.`

Forbidden article thesis:

`OC proves a universal law that all unresolved contradiction across all domains
causes emergence or collapse, and K0-K12 is the unique hierarchy of reality.`

## Attempt Log

| Attempt | Claim | Method | Result | Next action |
| --- | --- | --- | --- | --- |
| 024-A000 | Program setup | Source audit and control split | Created internal theory route separate from external frontier claims | Complete primitive definition package and test CP-A/CP-B/CP-C |
| 024-A001 | `OC-THEORY-CP-001` | Manual route triage | Broad central sentence is not terminal as theorem; strongest current route is axiom/repaired classification unless strict primitives yield a non-circular theorem | Close primitive package and test CP-A |
| 024-A002 | `OC-THEORY-DEF-001` | Primitive package closure | Accepted primitives as axiomatic vocabulary with anti-circularity boundary | Run central principle decision |
| 024-A003 | `OC-THEORY-CP-001` | Theorem-vs-axiom decision | Accepted central principle as bounded axiom schema, not proved universal theorem | Prove first consequence theorem |
| 024-A004 | `OC-THEORY-THM-001` | Derivation from primitives plus central axiom | Proved OC Claim Admissibility theorem | Continue to operator catalog and minimality |
| 024-A005 | `OC-THEORY-OP-001` | Source graph recovery | Closed source-bound six-operator catalog with type roles; minimality remains open | Prove/restrict operator closure laws |
| 024-A006 | `OC-THEORY-OP-003` | Typed partial-map proof | Proved local operator composition/well-formedness theorem | Build independence models for minimality |
| 024-A007 | `OC-THEORY-OP-002` | Six effect-invariant witnesses | Proved local operator independence/minimality for selected typed-effect formalism | Continue K-level hierarchy recovery |
| 024-A008 | `OC-THEORY-K-001` | Source graph recovery | Closed source-bound K0-K12 hierarchy vocabulary; distinctness/count remain open | Build K-level invariant candidates |
| 024-A009 | `OC-THEORY-K-002` | Invariant candidate pass | Low-core candidate invariants recorded; no terminal distinctness theorem yet | Prove K0 -> K1 non-recovery from distinguishability alone |
| 024-A010 | `OC-THEORY-K-002` | Typed reduct/expansion witness proof | Proved adjacent K-level non-recovery under typed-extension invariants | Decide K-count/partition status |
| 024-A011 | `OC-THEORY-K-003` | Strong partition audit | Refuted unique/exhaustive K0-K12 theorem and repaired to source-bound ladder plus typed non-recovery | Classify law-like statements |
| 024-A012 | `OC-THEORY-LAW-001` | Status-classification rule | Accepted law taxonomy with article boundary | Exclude unsupported crown-stone claims |
| 024-A013 | `OC-THEORY-CROWN-001` | Dependency audit | Excluded crown stones from core as conjectural extension | Exclude unsupported domain projections |
| 024-A014 | `OC-THEORY-DOMAIN-001` | Projection admissibility audit | Excluded domain projections from core proof ledger unless locally evidenced | Close article gate |
| 024-A015 | `OC-THEORY-ARTICLE-001` | DB dependency and boundary proof | Proved bounded article eligibility for the closed 024 theory core | Final integrity checks |
