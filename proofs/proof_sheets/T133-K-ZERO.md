# T133-K-ZERO - Continuumness zero obstruction theorem

Status: `BLOCKED_PENDING_ADVERSARIAL_REPAIR_V12`
Primary artifact: `appendix/OC_1_3_3_CONTINUUMNESS_FUNCTIONALS.tex`
Machine-checked subset: `formal/lean/OC133V12.lean::continuumness_zero_case_iff_declared_zero_cause_with_support`
Attacked claim: Continuumness zero requires live support, an independently clear obstruction ledger, and a declared zero-cause family; a zero-cause label alone does not compute k=0.

## Assumptions
- The continuumness score k is separate from live status.
- Zero-cause predicates are explicitly declared for each realization.
- A product formula is a local representation only when independence assumptions are stated.

## Definitions
- ZeroCause(K,t): disjunction of typed collapse causes.
- ObstructionLedger(K,t): typed flow/coherence/identity/embedding obstruction flags.
- k(K,t)=0: score-zero event computed from the obstruction ledger and licensed by at least one active zero-cause.
- Local aggregator: product or other numeric representation derived after semantics are fixed.

## Lemma 1
Flow-support collapse can make k zero while admissibility and cycles are nonempty.

## Lemma 2
Coherence contradiction can make k zero without set emptiness.

## Theorem
Within v12, k=0 is equivalent to nonempty support, an active declared zero-cause, and no active obstruction in the independent obstruction ledger.

## Proof
The score is computed from the obstruction ledger, not from the zero-cause label. Lemma 1 proves zero score iff no obstruction is active. Lemma 2 proves a zero-cause with clear obstruction licenses the zero verdict, while an active obstruction rejects k=0 even if a zero-cause label exists.

This is a candidate proof sheet and is not release-promoted while G57/G58/G70 remain open. It is linked to the finite witness corpus and
to the Lean subset named above. The Lean item checks the corresponding typed invariant, while the
finite corpus checks the release verdict behavior used by the public claim ledger.

## Counterexample Boundary
A realization with undeclared zero-cause, missing live support, or any active obstruction may not promote k=0.

## Machine-Checkable Finite Example
Omega={s}, C={c}, flow_zero_cause=true, and all obstruction flags false gives k=0; a matching obstruction-active control rejects k=0 despite the zero-cause label.

## Dependency Refs
- `proofs/THEOREM_INVENTORY_1_3_3.json`
- `proofs/FINITE_MODEL_CHECKS_1_3_3.json`
- `formal/lean/OC133V12.lean`
- `appendix/OC_1_3_3_CONTINUUMNESS_FUNCTIONALS.tex`

## Reviewer Attack Answered
The hostile attack is answered by separating type assumptions, exact theorem scope, executable
witnesses, and a falsifier boundary. If a reviewer removes the assumptions, the claim is not silently
weakened; the relevant v12 gate fails.
