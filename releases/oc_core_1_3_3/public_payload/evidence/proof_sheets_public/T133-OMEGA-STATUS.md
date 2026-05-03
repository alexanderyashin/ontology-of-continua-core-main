# T133-OMEGA-STATUS - Typed liveness, death, residue, and rebirth evidence-consistency theorem

Status: `PROMOTED_BOUNDED_THEOREM_V12_release-governed`
Primary artifact: `content/OC_1_3_3_TYPED_FOUNDATION.tex`
Machine-checked subset: `Lean declaration lifecycle_residue_rebirth_morphism_boundary`
Attacked claim: Death blocks live status; residue and rebirth are token-bound evidence relations with distinct class-specific endpoint rules: residue separates source from residue while returning to the source endpoint, and rebirth separates source, residue, and new target tokens. Rebirth is non-identity unless endpoint-bound identity evidence has identity class, declared invariant preservation, no residue token, and equal source/target endpoint evidence. No categorical Hom/composition theorem is promoted.

## Assumptions
- Admissibility, liveness, death, residue, rebirth, and identity are separate typed fields.
- Every realization declares the predicates that can change live status.
- Residue preservation is not identity continuation unless endpoint-bound identity evidence is present: identity class, preserved invariants, no residue token, and equal source/target endpoints.

## Definitions
- Live(K,t): typed boolean status over a realization.
- Residue(K,t): preserved post-death structure with its own carrier.
- Rebirth morphism: a construction from residue into a new live realization.

## Lemma 1
Nonempty admissibility does not imply liveness without the live-support predicates.

## Lemma 2
Residue preservation does not imply identity continuation without identity morphism constraints.

## Theorem
The four statuses are jointly consistent and non-interchangeable in the typed OC model, and the residue/rebirth source-target route is bound to explicit token evidence.

## Proof
The fields have distinct codomains and transition rules. Lemma 1 separates admissibility from liveness. Lemma 2 separates residue from identity. The Lean theorem then takes explicit source, residue, and target tokens: residue evidence separates source from residue while returning to the source endpoint, and rebirth evidence carries pairwise source/residue/new-target separation. This proves death blocks liveness while residue/rebirth evidence is not endpoint-bound identity evidence.

The proof is promoted only as a bounded release-governed release claim with the stated assumptions. It is linked to the finite witness corpus and
to the Lean subset named above. The Lean item checks the corresponding typed invariant, while the
finite corpus checks the release verdict behavior used by the public claim register.

## Counterexample Boundary
Any claim reading residue-preserving restart as same-identity survival is rejected unless endpoint-bound identity evidence is supplied.

## Machine-Checkable Finite Example
A two-state automaton has admissible state A, failed cycle support, residue r, and new state B constructed from r; B is rebirth, not continuation.

## Dependency Refs
- `repository path proofs/THEOREM_INVENTORY_1_3_3.json`
- `finite-model semantic report`
- `formal/lean/OC133V12.lean`
- `content/OC_1_3_3_TYPED_FOUNDATION.tex`

## Reviewer Attack Answered
The hostile attack is answered by separating type assumptions, exact theorem scope, executable
witnesses, and a falsifier boundary. If a reviewer removes the assumptions, the claim is not silently
weakened; the relevant current verification criterion fails.
