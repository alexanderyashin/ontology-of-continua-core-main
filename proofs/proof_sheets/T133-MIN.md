# T133-MIN - Declared semantic-verdict component independence theorem

Status: `FORMAL_CONSISTENCY_CHECK_NO_SEND_NOT_SCIENTIFIC_THEOREM`
Primary artifact: `appendix/OC_1_3_3_GLOBAL_MINIMALITY_WITNESSES.tex`
Machine-checked subset: `formal/lean/OC133V12.lean::release_tuple_semantic_component_irredundant`
Attacked claim: Within the declared v12 release tuple semantics, each tuple component has a one-field semantic keep/drop witness that changes the release verdict.

## Assumptions
- Minimality is claimed for the release-governed OC verdict class, not for all possible theories.
- Each declared component has a witness pair that changes a declared OC verdict when the component is removed or weakened.
- Witnesses are checked by the finite-model ledger and by the Lean component-witness schema.

## Definitions
- Verdict-invariant: preserves pass/fail classification of the declared OC tests.
- Witness pair: two cases differing only in one component and producing different verdicts.
- Global tuple minimality: every declared tuple component has at least one witness pair.

## Lemma 1
A component with a verdict-changing witness cannot be removed verdict-invariantly.

## Lemma 2
The v12 witness ledger covers every declared tuple component.

## Theorem
The declared v12 tuple has component-wise independence for the declared semantic verdict suite.

## Proof
For each component c, the witness ledger gives keep_c and drop_c cases whose semantic records differ only in c's obligation field and whose verdicts differ. Lemma 1 proves that c is required for the release verdict suite. Lemma 2 ranges over the full declared tuple. Therefore no declared component can be removed while preserving this declared v12 verdict suite.

This proof sheet is a formal release-consistency check only; it is not promoted as an independent scientific theorem and remains no-send while G57/G58/G70 remain open. It is linked to the finite witness corpus and
to the Lean subset named above. The Lean item checks the corresponding typed invariant, while the
finite corpus checks the release verdict behavior used by the public claim ledger.

## Counterexample Boundary
If any declared tuple component can be removed while `FM-MIN-*` still returns PASS for the declared semantic verdict suite, the minimality card fails.

## Machine-Checkable Finite Example
Removing boundary admits a state rejected by the full tuple; removing cycle mode admits a frozen non-live object.

## Dependency Refs
- `proofs/THEOREM_INVENTORY_1_3_3.json`
- `proofs/FINITE_MODEL_CHECKS_1_3_3.json`
- `formal/lean/OC133V12.lean`
- `appendix/OC_1_3_3_GLOBAL_MINIMALITY_WITNESSES.tex`

## Reviewer Attack Answered
The hostile attack is answered by separating type assumptions, exact theorem scope, executable
witnesses, and a falsifier boundary. If a reviewer removes the assumptions, the claim is not silently
weakened; the relevant v12 gate fails.
