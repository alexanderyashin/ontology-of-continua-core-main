# OC 032 Empirical Crown And Domain Closure Order

## Authority

This package extends 031 evidence closure into a stricter crown/domain
program. 031 remains the formal baseline: OC core, operators, K-ladder,
law/domain discipline, and bounded source-domain evidence ceilings are accepted
only as recorded in `031/evidence_operationalization`.

032 must not promote a stronger empirical or crown-stone claim unless the row
has local evidence, falsifier, replay or replication check, dependency closure,
and article-safe wording.

## Queue

The active queue is built from:

- all 031 domain evidence rows;
- 031 guard rows and 030/025/026 crown-boundary counterproof artifacts;
- source graph domain nodes and replay/completion evidence files.

## Final Statuses

Allowed final statuses are:

- `EMPIRICALLY_PROVED_WITH_EVIDENCE`
- `PROVED_AS_DESCRIPTIVE_PROJECTION`
- `PROVED_AS_CONDITIONAL_CROWN_COROLLARY`
- `REJECTED_WITH_COUNTEREVIDENCE`
- `REQUIRES_NEW_LOCAL_DATA`

No other status is allowed in the 032 DB.

## Rules

- Domain rows may be empirical only when replay, validation, completion,
  acceptance criterion, falsifier, refs, and no-blocker checks all pass.
- Mathematics is not promoted as an empirical prediction row; it remains a
  descriptive/proof-expansion projection unless a later empirical package exists.
- Crown stones are not proved by OC vocabulary alone. They are promotable only
  as dependency-closed conditional corollaries or as rows with their own local
  evidence package.
- `REQUIRES_NEW_LOCAL_DATA` is a lawful scientific terminal for 032 inventory
  rows that have a source claim but lack the local evidence needed for empirical
  promotion.

## Required Checks

- Run 031 regression first: `lake build` and `python formal/python/validate_031.py`.
- Run 032 `lake build`.
- Run `python formal/python/build_empirical_db_032.py`.
- Run `python formal/python/empirical_witnesses_032.py`.
- Run `python formal/python/validate_032.py`.
