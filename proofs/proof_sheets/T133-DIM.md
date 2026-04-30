# T133-DIM - Historical axis and effective-rank compatibility theorem

Status: `BLOCKED_PENDING_ADVERSARIAL_REPAIR_V12`
Primary artifact: `appendix/OC_1_3_3_K_LEVEL_IRREDUCIBILITY_ATLAS.tex`
Machine-checked subset: `formal/lean/OC133V12.lean::historical_axis_survives_rank_drop`
Attacked claim: Historical axis activation and effective working rank are kept as distinct no-send formal release-consistency fields; a finite/Lean witness shows compatibility of monotone historical bookkeeping with decreasing effective rank, but v12 does not promote an independent scientific dimension theorem.

## Assumptions
- Historical axes record realized dependence history.
- Effective rank records currently active independent degrees of freedom.
- A lawful demotion must prove the historical axis is unobservable under the declared equivalence.

## Definitions
- A_hist: set of historically activated axes.
- rank_eff(t): rank of currently active support.
- Axis witness: a finite pair whose verdict changes when the axis is removed.

## Lemma 1
A frozen memory axis can remain historically present after active rank falls.

## Lemma 2
Reduction from K(n+1) to K(n) fails when a witness remains observable.

## Theorem
Historical monotonicity and effective-rank decrease are compatible inside the release semantics because they measure different typed quantities.

## Proof
A_hist is accumulated over realized dependence events; rank_eff is recomputed over active support. Lemma 1 gives compatibility; Lemma 2 gives the irreducibility test used by the atlas.

This is a candidate proof sheet and is not release-promoted while G57/G58/G70 remain open. It is linked to the finite witness corpus and
to the Lean subset named above. The Lean item checks the corresponding typed invariant, while the
finite corpus checks the release verdict behavior used by the public claim ledger.

## Counterexample Boundary
A K-level is demotable only when the alleged new axis has no witness and no observable consequence.

## Machine-Checkable Finite Example
A two-axis automaton activates memory and later freezes it; historical axes remain two while active rank becomes one.

## Dependency Refs
- `proofs/THEOREM_INVENTORY_1_3_3.json`
- `proofs/FINITE_MODEL_CHECKS_1_3_3.json`
- `formal/lean/OC133V12.lean`
- `appendix/OC_1_3_3_K_LEVEL_IRREDUCIBILITY_ATLAS.tex`

## Reviewer Attack Answered
The hostile attack is answered by separating type assumptions, exact theorem scope, executable
witnesses, and a falsifier boundary. If a reviewer removes the assumptions, the claim is not silently
weakened; the relevant v12 gate fails.
