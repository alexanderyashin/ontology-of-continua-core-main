# T133-K-ZERO - Continuumness zero obstruction theorem

Status: `PROMOTED_BOUNDED_THEOREM_V12_release-governed`
Primary artifact: `master monograph appendix: Continuumness Functionals`
Machine-checked subset: `Lean declaration continuumness_zero_case_iff_declared_zero_cause_with_support`
Attacked claim: Continuumness zero requires live support, an independently clear obstruction register, and a declared zero-cause family; a zero-cause label alone does not compute k=0.

## Assumptions
- The continuumness score k is separate from live status.
- Zero-cause predicates are explicitly declared for each realization.
- A product formula is a local representation only when independence assumptions are stated.

## Definitions
- ZeroCause(K,t): disjunction of typed collapse causes.
- ObstructionLedger(K,t): typed flow/coherence/identity/embedding obstruction flags.
- k(K,t)=0: score-zero event computed from the obstruction register and licensed by at least one active zero-cause.
- Local aggregator: product or other numeric representation derived after semantics are fixed.

## Lemma 1
Flow-support collapse can make k zero while admissibility and cycles are nonempty.

## Lemma 2
Coherence contradiction can make k zero without set emptiness.

## Theorem
Within current formal profile, k=0 is equivalent to nonempty support, an active declared zero-cause, and no active obstruction in the independent obstruction register.

## Proof
The score is computed from the obstruction register, not from the zero-cause label. Lemma 1 proves zero score iff no obstruction is active. Lemma 2 proves that a declared zero-cause licenses the zero verdict only when the obstruction register is clear, while an active obstruction rejects k=0 even if a zero-cause label exists.

The proof is promoted only as a bounded release-governed release claim with the stated assumptions. It is linked to the finite witness corpus and
to the Lean subset named above. The Lean item checks the corresponding typed invariant, while the
finite corpus checks the release verdict behavior used by the public claim register.

## Counterexample Boundary
A realization with undeclared zero-cause, missing live support, or any active obstruction may not promote k=0.

## Machine-Checkable Finite Example
Omega={s}, C={c}, flow_zero_cause=true, and all obstruction flags false gives k=0; a matching obstruction-active control rejects k=0 despite the zero-cause label.

## Dependency Refs
- `repository path proofs/THEOREM_INVENTORY_1_3_3.json`
- `finite-model semantic report`
- `formal/lean/OC133V12.lean`
- `master monograph appendix: Continuumness Functionals`

## Reviewer Attack Answered
The hostile attack is answered by separating type assumptions, exact theorem scope, executable
witnesses, and a falsifier boundary. If a reviewer removes the assumptions, the claim is not silently
weakened; the relevant current verification criterion fails.
