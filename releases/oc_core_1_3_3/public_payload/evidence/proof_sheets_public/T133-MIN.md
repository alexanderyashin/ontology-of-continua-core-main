# T133-MIN - Declared semantic-verdict component independence theorem

Status: `PROMOTED_BOUNDED_THEOREM_V12_release-governed`
Primary artifact: `master monograph appendix: Global Minimality Witnesses`
Machine-checked subset: `Lean declaration release_tuple_semantic_component_irredundant`
Attacked claim: Within the declared current release tuple semantics, each tuple component has a one-field semantic keep/drop witness that changes the release verdict.

## Assumptions
- Minimality is claimed for the release-governed OC verdict class, not for all possible theories.
- Each declared component has a witness pair that changes a declared OC verdict when the component is removed or weakened.
- Witnesses are checked by the finite-model register and by the Lean component-witness schema.

## Definitions
- Verdict-invariant: preserves pass/fail classification of the declared OC tests.
- Witness pair: two cases differing only in one component and producing different verdicts.
- Global tuple minimality: every declared tuple component has at least one witness pair.

## Lemma 1
A component with a verdict-changing witness cannot be removed verdict-invariantly.

## Lemma 2
The current formal profile witness register covers every declared tuple component.

## Theorem
The declared current formal profile tuple has component-wise independence for the declared semantic verdict suite.

## Proof
For each component c, the witness register gives keep_c and drop_c cases whose semantic records differ only in c's obligation field and whose verdicts differ. Lemma 1 proves that c is required for the release verdict suite. Lemma 2 ranges over the full declared tuple. Therefore no declared component can be removed while preserving this declared current formal profile verdict suite.

The proof is promoted only as a bounded release-governed release claim with the stated assumptions. It is linked to the finite witness corpus and
to the Lean subset named above. The Lean item checks the corresponding typed invariant, while the
finite corpus checks the release verdict behavior used by the public claim register.

## Counterexample Boundary
If any declared tuple component can be removed while `FM-MIN-*` still returns PASS for the declared semantic verdict suite, the minimality card fails.

## Machine-Checkable Finite Example
Removing boundary admits a state rejected by the full tuple; removing cycle mode admits a frozen non-live object.

## Dependency Refs
- `repository path proofs/THEOREM_INVENTORY_1_3_3.json`
- `finite-model semantic report`
- `formal/lean/OC133V12.lean`
- `master monograph appendix: Global Minimality Witnesses`

## Reviewer Attack Answered
The hostile attack is answered by separating type assumptions, exact theorem scope, executable
witnesses, and a falsifier boundary. If a reviewer removes the assumptions, the claim is not silently
weakened; the relevant current verification criterion fails.
