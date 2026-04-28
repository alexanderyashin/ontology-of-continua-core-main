# T133-HYBRID - Hybrid operator semantics theorem

Status: `PROMOTED_BOUNDED_THEOREM_V12`
Primary artifact: `content/OC_1_3_3_OPERATOR_SEMANTICS.tex`
Machine-checked subset: `formal/lean/OC133V12.lean::smooth_operator_is_update_special_case`
Attacked claim: Differential operator notation is a smooth-realization specialization of typed update semantics.

## Assumptions
- Operators are typed update components over realization states.
- A derivative is available only when the realization declares smooth charts.
- Discrete, stochastic, rewrite, proof-replay, graph, and hybrid automaton updates are first-class.

## Definitions
- Update semantics: state and admissible input map to a successor object or distribution.
- Smooth semantics: update admits differentiable local charts.
- Hybrid semantics: smooth segments and discrete jumps live in one typed transition system.

## Lemma 1
A differentiable flow induces typed update relations by time-t maps.

## Lemma 2
A typed update relation need not induce a derivative without extra smoothness assumptions.

## Theorem
OC operators F,G,H,Q,R,S,U are typed updates, with differential notation only as a special realization.

## Proof
The primitive object is the update relation. Smooth systems interpret it through flows, while proof and rewrite systems interpret it through transition steps. Lemma 1 embeds smooth systems; Lemma 2 blocks universal derivative overreach.

The proof is promoted only with the stated assumptions. It is linked to the finite witness corpus and
to the Lean subset named above. The Lean item checks the corresponding typed invariant, while the
finite corpus checks the release verdict behavior used by the public claim ledger.

## Counterexample Boundary
Any section differentiating a rewrite-only state without smooth assumptions fails G41.

## Machine-Checkable Finite Example
A proof-replay operator maps theorem states through rewrite steps; it is well typed and has no derivative.

## Dependency Refs
- `proofs/THEOREM_INVENTORY_1_3_3.json`
- `proofs/FINITE_MODEL_CHECKS_1_3_3.json`
- `formal/lean/OC133V12.lean`
- `content/OC_1_3_3_OPERATOR_SEMANTICS.tex`

## Reviewer Attack Answered
The hostile attack is answered by separating type assumptions, exact theorem scope, executable
witnesses, and a falsifier boundary. If a reviewer removes the assumptions, the claim is not silently
weakened; the relevant v12 gate fails.
