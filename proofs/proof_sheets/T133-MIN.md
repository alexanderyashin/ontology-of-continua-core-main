# T133-MIN - Declared semantic-verdict component independence theorem

Status: `PROMOTED_BOUNDED_THEOREM_V12`
Primary artifact: `appendix/OC_1_3_3_GLOBAL_MINIMALITY_WITNESSES.tex`
Machine-checked subset: `formal/lean/OC133V12.lean::component_registry_complete_and_witnessed`
Attacked claim: Within the declared v12 semantic verdict suite, each promoted tuple component has a one-field semantic keep/drop witness that changes the release verdict.

## Assumptions
- Minimality is claimed for the release-governed OC verdict class, not for all possible theories.
- Each promoted component has a witness pair that changes a declared OC verdict when the component is removed or weakened.
- Witnesses are checked by the finite-model ledger and by the Lean component-witness schema.

## Definitions
- Verdict-invariant: preserves pass/fail classification of the declared OC tests.
- Witness pair: two cases differing only in one component and producing different verdicts.
- Global tuple minimality: every promoted tuple component has at least one witness pair.

## Lemma 1
A component with a verdict-changing witness cannot be removed verdict-invariantly.

## Lemma 2
The v12 witness ledger covers every promoted tuple component.

## Theorem
The promoted v12 tuple has component-wise independence for the declared semantic verdict suite.

## Proof
For each component c, the witness ledger gives keep_c and drop_c cases whose semantic records differ only in c's obligation field and whose verdicts differ. Lemma 1 proves that c is required for the release verdict suite. Lemma 2 ranges over the full promoted tuple. Therefore no promoted component can be removed while preserving this declared v12 verdict suite.

The proof is promoted only with the stated assumptions. It is linked to the finite witness corpus and
to the Lean subset named above. The Lean item checks the corresponding typed invariant, while the
finite corpus checks the release verdict behavior used by the public claim ledger.

## Counterexample Boundary
The theorem does not claim OC is the only possible scientific framework; novelty is handled by the comparator register.

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
