# T133-HYBRID - Typed update and chart-labelled operator semantics theorem

Status: `BLOCKED_PENDING_ADVERSARIAL_REPAIR_V12`
Primary artifact: `content/OC_1_3_3_OPERATOR_SEMANTICS.tex`
Machine-checked subset: `formal/lean/OC133V12.lean::integrated_operator_semantics`
Attacked claim: OC operators are typed update semantics; chart-labelled flow-one notation is admitted only for declared chart records, while proof/rewrite and guard/reset updates remain first-class non-smooth cases. No differentiability or ODE-solution theorem is promoted in v12.

## Assumptions
- Operators are typed update components over realization states.
- A derivative claim is not licensed by this v12 theorem; chart records only gate flow-one notation in the typed update subset.
- The promoted formal subset covers smooth-chart updates, proof/rewrite updates, and guard/reset hybrid updates; stochastic and graph operators remain unpromoted extension obligations until separately formalized.

## Definitions
- Update semantics: state and admissible input map to a successor object or distribution.
- Chart-labelled semantics: update may carry chart metadata, but differentiability is not promoted without a separate theorem.
- Hybrid semantics: smooth segments and discrete jumps live in one typed transition system.

## Lemma 1
A declared chart-labelled flow-one route induces a typed update relation in the v12 subset.

## Lemma 2
A typed update relation need not induce a derivative without extra smoothness assumptions.

## Theorem
OC operators F,G,H,Q,R,S,U are typed updates; chart-labelled flow-one, proof/rewrite, and guard/reset hybrid routes are separate typed realizations.

## Proof
The primitive object is a route-specific operator-admission record. The Lean theorem `integrated_operator_semantics` binds the smooth-chart flow-one update, chart/domain/local-law obligations, guard/reset update branch, and proof/rewrite non-smooth branch in one statement; `operator_admission_route_obligations` remains a supporting decomposition lemma. The Lean theorem `bound_hybrid_admission_obligations` adds a system/source-bound hybrid admission record, tying guard observation, guard value, reset source/target typing, codomain typing, and reset admissibility to the actual `HybridSystem` and source state. The false-guard pass-through branch is checked by `hybrid_no_guard_uses_update` and by finite rows whose operator admission records guard evaluation rather than assuming the guard value is true. The finite runner independently evaluates the same fields and fails if labels are correct but obligations are missing.

This is a candidate proof sheet and is not release-promoted while G57/G58/G70 remain open. It is linked to the finite witness corpus and
to the Lean subset named above. The Lean item checks the corresponding typed invariant, while the
finite corpus checks the release verdict behavior used by the public claim ledger.

## Counterexample Boundary
Any route treating a chart token as differentiability, manifold, vector-field, or ODE-solution evidence is outside the v12 operator theorem and remains a future lint/proof obligation.

## Machine-Checkable Finite Example
The finite corpus includes smooth-chart positive/negative cases, guard/reset positive/negative cases, proof/rewrite positive/negative cases, and tamper controls for missing local law, wrong reset codomain, and derivative leakage.

## Dependency Refs
- `proofs/THEOREM_INVENTORY_1_3_3.json`
- `proofs/FINITE_MODEL_CHECKS_1_3_3.json`
- `formal/lean/OC133V12.lean`
- `content/OC_1_3_3_OPERATOR_SEMANTICS.tex`

## Reviewer Attack Answered
The hostile attack is answered by separating type assumptions, exact theorem scope, executable
witnesses, and a falsifier boundary. If a reviewer removes the assumptions, the claim is not silently
weakened; the relevant v12 gate fails.
