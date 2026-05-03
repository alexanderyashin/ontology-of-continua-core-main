# T133-BOUNDARY - Metric-threshold boundary specialization theorem

Status: `PROMOTED_BOUNDED_THEOREM_V12_release-governed`
Primary artifact: `master monograph appendix: Boundary Representation Theorem`
Machine-checked subset: `Lean declaration metric_boundary_specialization`
Attacked claim: Metric thresholds are a specialization of typed classifier boundaries.

## Assumptions
- Boundary predicates are typed classifiers into status objects.
- Metric thresholds are admitted only when the domain supplies a metric measurement rule.
- Logical, categorical, graph, social, and proof-state boundaries may remain non-metric.

## Definitions
- Classifier boundary: b_i:S -> Status_i plus a failure predicate over Status_i.
- Metric boundary: classifier with Status_i = real-valued or ordered numeric status.
- Logical boundary: classifier with Status_i = {true,false}.

## Lemma 1
Every real-valued threshold boundary embeds as a classifier boundary.

## Lemma 2
A boolean admissibility rule is a classifier boundary without inventing a fake numeric distance.

## Theorem
The current formal profile boundary formalism conservatively extends metric-threshold OC boundaries.

## Proof
Map each threshold measurement to a classifier returning its measured status and use the threshold comparison as the failure predicate. Non-metric domains instantiate the same classifier type directly. Thus old metric cases are preserved and non-metric cases stop pretending to be metric.

The proof is promoted only as a bounded release-governed release claim with the stated assumptions. It is linked to the finite witness corpus and
to the Lean subset named above. The Lean item checks the corresponding typed invariant, while the
finite corpus checks the release verdict behavior used by the public claim register.

## Counterexample Boundary
A social or logical boundary represented numerically without a measurement rule is blocked by release criterion.

## Machine-Checkable Finite Example
A proof state is admissible iff Consistent(state)=true; no real-valued boundary is required.

## Dependency Refs
- `repository path proofs/THEOREM_INVENTORY_1_3_3.json`
- `finite-model semantic report`
- `formal/lean/OC133V12.lean`
- `master monograph appendix: Boundary Representation Theorem`

## Reviewer Attack Answered
The hostile attack is answered by separating type assumptions, exact theorem scope, executable
witnesses, and a falsifier boundary. If a reviewer removes the assumptions, the claim is not silently
weakened; the relevant current verification criterion fails.
