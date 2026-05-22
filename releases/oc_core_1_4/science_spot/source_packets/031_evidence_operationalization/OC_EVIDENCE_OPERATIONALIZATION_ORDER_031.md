# OC Evidence Operationalization Order 031

## Governing Rule

031 converts the 030 concentric proof graph into evidence-bound operational
rows. The canonical promoted status is:

`PROVED_WITH_EVIDENCE`

The spelling `Prooved with evidence` is treated only as a user-facing alias.

False inherited formulations do not receive promoted rows. They are retained in
`guard_rows` as `EVIDENCE_BOUND_GUARD`, while the repaired theorem-grade
statement receives the promoted evidence row.

## Evidence Inputs

031 must bind:

- 029/030 Lean theorem chains;
- 029/030 Python witnesses and validators;
- 022 source graph root, K, operator, and domain nodes;
- `DOMAIN_REPLAY_REPORTS_latest.json`;
- `EMPIRICAL_DOMAIN_VALIDATION_MATRIX_latest.json`;
- `OC_DOMAIN_PROJECTION_COMPLETION_latest.json`.

## Domain Rule

Domain projections may be marked `PROVED_WITH_EVIDENCE` only at their lawful
claim ceiling. A replay or validation pass does not authorize stronger wording
than the row's `claim_level` and completion `claim_ceiling`.

Required domain evidence:

- replay `status = PASS`;
- replay status is pass/replayable;
- validation matrix `validation_status = PASS`;
- no blocking ids;
- nonempty acceptance criterion;
- nonempty falsifier;
- nonempty evidence refs;
- explicit claim level and claim ceiling;
- completion status `PASS`.

## Closeout Gate

031 closeout is allowed only when:

- every promoted evidence row has status `PROVED_WITH_EVIDENCE`;
- every row has source, proposition, assumptions, proof/evidence body,
  falsifier, dependency closure, verification note, and artifact refs;
- all five source domains have domain evidence rows;
- no article wording exceeds the domain claim ceiling;
- `lake build` passes in `formal/`;
- `python formal/python/build_evidence_db_031.py` and
  `python formal/python/validate_031.py` pass;
- 027/028/029/030 regression checks pass.
