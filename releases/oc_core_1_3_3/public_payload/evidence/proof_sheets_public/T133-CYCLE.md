# T133-CYCLE - Live-status cycle-mode requirement theorem

Status: `PROMOTED_BOUNDED_THEOREM_V12_OWNER_REVIEW_LOCKED`
Primary artifact: `content/OC_1_3_3_CYCLE_TAXONOMY.tex`
Machine-checked subset: `formal/lean/OC133V12.lean::eligible_live_requires_cycle_or_maintenance`
Attacked claim: Declared eligible-live status requires an explicit cycle mode or non-vacuous maintenance predicate.

## Assumptions
- Live status is not static persistence.
- Maintenance, renewal, replay, regulatory, and degenerate cycle modes are distinct.
- A degenerate fixed point is live only if its maintenance predicate is non-vacuous.

## Definitions
- Cycle mode: typed recurrence, maintenance, replay, or regulation condition.
- Frozen persistence: status that stays unchanged without support obligation.
- Degenerate maintenance: identity recurrence plus active support checks.

## Lemma 1
No declared cycle mode means the live predicate is under-specified.

## Lemma 2
A fixed point with active support obligations can satisfy degenerate maintenance.

## Theorem
OC live status requires explicit cycle evidence; static labels are residue or inert records.

## Proof
Liveness is defined through support that can fail or be maintained. Lemma 1 rejects unsupported static labels. Lemma 2 admits legitimate fixed points. The theorem follows by the typed live predicate.

The proof is promoted only as a bounded owner-review release claim with the stated assumptions. It is linked to the finite witness corpus and
to the Lean subset named above. The Lean item checks the corresponding typed invariant, while the
finite corpus checks the release verdict behavior used by the public claim ledger.

## Counterexample Boundary
An artifact that never updates, replays, checks, or maintains itself is archive residue, not live continuum.

## Machine-Checkable Finite Example
A constant automaton with an energy-maintenance check passes; a label with no check fails.

## Dependency Refs
- `proofs/THEOREM_INVENTORY_1_3_3.json`
- `proofs/FINITE_MODEL_CHECKS_1_3_3.json`
- `formal/lean/OC133V12.lean`
- `content/OC_1_3_3_CYCLE_TAXONOMY.tex`

## Reviewer Attack Answered
The hostile attack is answered by separating type assumptions, exact theorem scope, executable
witnesses, and a falsifier boundary. If a reviewer removes the assumptions, the claim is not silently
weakened; the relevant v12 gate fails.
