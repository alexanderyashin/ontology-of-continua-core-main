# OC 040 Continuous Replay, Acquisition, And Full Obligation Closure Order

This package continues from OC 039. The queue authority is
`../039/full_k_hierarchy_evidence_closure/oc_full_k_hierarchy_evidence_closure_039.sqlite`.

Mandatory control rule: while any obligation is not terminal, a progress note is only a
handoff, not completion. The execution loop must keep taking the next row, searching
local evidence first, then lawful public evidence, then replaying or proving the exact
bounded claim.

No empirical row may be promoted from vocabulary, analogy, chapter prose, or seed
download alone. Promotion requires source statement, proposition, evidence refs,
replay or proof artifact, falsifier, dependency closure, and verification.

Heavy datasets are stored outside git under `D:\Logion Storage\oc_evidence_datasets\040`.
The repository tracks only manifests, checksums, schemas, replay scripts, proof scripts,
DB state, notebooks, and validators.

Allowed terminal statuses:

- `EMPIRICALLY_PROVED_WITH_EVIDENCE`
- `FORMALLY_PROVED_NONEMPIRICAL_PROJECTION`
- `PROVED_CROWN_STONE_WITH_THEOREM_CHAIN`
- `REJECTED_AND_MODEL_REPAIRED_WITH_COUNTEREVIDENCE`

Allowed working statuses:

- `ACTIVE_DATA_ACQUISITION_REQUIRED`
- `REPLAY_IN_PROGRESS`
- `PROOF_IN_PROGRESS`
- `FORCED_HANDOFF_NOT_COMPLETION`

Full empirical closeout is lawful only when every one of the 63 inherited obligations
has a terminal status and no promoted row exceeds its evidence ceiling.
