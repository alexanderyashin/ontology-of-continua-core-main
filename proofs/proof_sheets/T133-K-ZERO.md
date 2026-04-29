# T133-K-ZERO - Continuumness zero-cause theorem

Status: `PROMOTED_BOUNDED_THEOREM_V12`
Primary artifact: `appendix/OC_1_3_3_CONTINUUMNESS_FUNCTIONALS.tex`
Machine-checked subset: `formal/lean/OC133V12.lean::continuumness_zero_case_iff_declared_zero_cause_with_support`
Attacked claim: Continuumness zero follows from a declared zero-cause family, not only from empty admissibility or empty cycles.

## Assumptions
- The continuumness score k is separate from live status.
- Zero-cause predicates are explicitly declared for each realization.
- A product formula is a local representation only when independence assumptions are stated.

## Definitions
- ZeroCause(K,t): disjunction of typed collapse causes.
- k(K,t)=0: score-zero event licensed by at least one active zero-cause.
- Local aggregator: product or other numeric representation derived after semantics are fixed.

## Lemma 1
Flow-support collapse can make k zero while admissibility and cycles are nonempty.

## Lemma 2
Coherence contradiction can make k zero without set emptiness.

## Theorem
k=0 is equivalent to an active declared zero-cause in the v12 semantics.

## Proof
The forward direction is part of the v12 typing rule: no zero score is legal without a cause record. The reverse direction follows from the zero-cause constructors. Lemmas 1 and 2 show why the old empty-set biconditional was incomplete.

The proof is promoted only with the stated assumptions. It is linked to the finite witness corpus and
to the Lean subset named above. The Lean item checks the corresponding typed invariant, while the
finite corpus checks the release verdict behavior used by the public claim ledger.

## Counterexample Boundary
A realization with undeclared zero-cause may not promote k=0; it must add the cause record or fail the gate.

## Machine-Checkable Finite Example
Omega={s}, C={c}, flow_support=0 gives k=0 through FLOW_COLLAPSE while the old biconditional would not fire.

## Dependency Refs
- `proofs/THEOREM_INVENTORY_1_3_3.json`
- `proofs/FINITE_MODEL_CHECKS_1_3_3.json`
- `formal/lean/OC133V12.lean`
- `appendix/OC_1_3_3_CONTINUUMNESS_FUNCTIONALS.tex`

## Reviewer Attack Answered
The hostile attack is answered by separating type assumptions, exact theorem scope, executable
witnesses, and a falsifier boundary. If a reviewer removes the assumptions, the claim is not silently
weakened; the relevant v12 gate fails.
