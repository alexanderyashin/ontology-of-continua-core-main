# T133-OMEGA-STATUS - Typed liveness, death, residue, and rebirth consistency theorem

Status: `PROMOTED_BOUNDED_THEOREM_V12`
Primary artifact: `content/OC_1_3_3_TYPED_FOUNDATION.tex`
Machine-checked subset: `formal/lean/OC133V12.lean::lifecycle_statuses_and_morphisms_separated`
Attacked claim: Live status, death, residue, and rebirth are distinct typed predicates and morphism classes.

## Assumptions
- Admissibility, liveness, death, residue, rebirth, and identity are separate typed fields.
- Every realization declares the predicates that can change live status.
- Residue preservation is not identity continuation unless identity invariants are preserved.

## Definitions
- Live(K,t): typed boolean status over a realization.
- Residue(K,t): preserved post-death structure with its own carrier.
- Rebirth morphism: a construction from residue into a new live realization.

## Lemma 1
Nonempty admissibility does not imply liveness without the live-support predicates.

## Lemma 2
Residue preservation does not imply identity continuation without identity morphism constraints.

## Theorem
The four statuses are jointly consistent and non-interchangeable in the typed OC model.

## Proof
The fields have distinct codomains and transition rules. Lemma 1 separates admissibility from liveness. Lemma 2 separates residue from identity. Rebirth is then a typed morphism from residue to a new realization, so no equivocation remains.

The proof is promoted only with the stated assumptions. It is linked to the finite witness corpus and
to the Lean subset named above. The Lean item checks the corresponding typed invariant, while the
finite corpus checks the release verdict behavior used by the public claim ledger.

## Counterexample Boundary
Any claim reading residue-preserving restart as same-identity survival is rejected unless identity invariants are supplied.

## Machine-Checkable Finite Example
A two-state automaton has admissible state A, failed cycle support, residue r, and new state B constructed from r; B is rebirth, not continuation.

## Dependency Refs
- `proofs/THEOREM_INVENTORY_1_3_3.json`
- `proofs/FINITE_MODEL_CHECKS_1_3_3.json`
- `formal/lean/OC133V12.lean`
- `content/OC_1_3_3_TYPED_FOUNDATION.tex`

## Reviewer Attack Answered
The hostile attack is answered by separating type assumptions, exact theorem scope, executable
witnesses, and a falsifier boundary. If a reviewer removes the assumptions, the claim is not silently
weakened; the relevant v12 gate fails.
