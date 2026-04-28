# T133-K0-RES - K0 resolution-relative distinguishability theorem

Status: `PROMOTED_BOUNDED_THEOREM_V12`
Primary artifact: `appendix/OC_1_3_3_K0_RESOLUTION_FOUNDATION.tex`
Machine-checked subset: `formal/lean/OC133V12.lean::k0_same_cell_not_distinguished`
Attacked claim: K0 support is resolution-relative and never imposes raw global discreteness.

## Assumptions
- A raw carrier may be continuous, finite, countable, graph-like, proof-theoretic, or typed-combinatorial.
- A resolution regime supplies an observational equivalence relation over raw states.
- Separation is asserted only for resolved quotient classes and only inside the declared regime.

## Definitions
- Resolved carrier S/rho: raw states modulo the observational equivalence induced by rho.
- Distinguishable state: two quotient classes are unequal under the declared resolution.
- K0 support: bookkeeping distinguishability for a declared model state, not ontology of raw atoms.

## Lemma 1
If two raw points are in the same rho-cell, no OC theorem may infer raw separation between them.

## Lemma 2
If two rho-cells are distinct and the quotient metric declares positive separation, K0 distinguishability follows without a raw lower bound.

## Theorem
K0 is compatible with continuous raw carriers because the required separation is a quotient property.

## Proof
The proof factors every K0 reference through rho. Lemma 1 blocks raw discreteness leakage. Lemma 2 supplies the only positive separation used by downstream K0 claims. Therefore the promoted theorem is about resolved classes, not raw points.

The proof is promoted only with the stated assumptions. It is linked to the finite witness corpus and
to the Lean subset named above. The Lean item checks the corresponding typed invariant, while the
finite corpus checks the release verdict behavior used by the public claim ledger.

## Counterexample Boundary
A proof that assumes every pair of raw real states is epsilon-separated is outside v12 and fails G33.

## Machine-Checkable Finite Example
Partition [0,1] into four cells. Points 0.10 and 0.11 remain unresolved, while the first and second cells are separated as quotient classes.

## Dependency Refs
- `proofs/THEOREM_INVENTORY_1_3_3.json`
- `proofs/FINITE_MODEL_CHECKS_1_3_3.json`
- `formal/lean/OC133V12.lean`
- `appendix/OC_1_3_3_K0_RESOLUTION_FOUNDATION.tex`

## Reviewer Attack Answered
The hostile attack is answered by separating type assumptions, exact theorem scope, executable
witnesses, and a falsifier boundary. If a reviewer removes the assumptions, the claim is not silently
weakened; the relevant v12 gate fails.
