# OC Core 1.3.3 Grand Empirical Report

Verdict: `BLOCKED_PENDING_GENUINE_PER_DOMAIN_EVIDENCE`
Grand TOE support allowed: `false`
Candidate evidence packs: `10`
Valid evidence packs: `0`
Bounded baseline rows: `5`
Blocked domains: `5/5`
Decomposition queue rows: `5`

This factory/gate does not emit a grand empirical support allowance from bounded OC133 reconstructions, sample packs, or artifact existence. Unresolved domains remain BLOCKED until prospective or target-blind evidence packs clear the configured criteria.

| Domain | Status | Candidate packs | Valid packs | Valid N | Minimum N | Bounded baseline rows | Grand TOE support | Blockers |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `biology` | `BLOCKED` | `3` | `0` | `0` | `20` | `1` | `false` | GENUINE_EVIDENCE_N_BELOW_MINIMUM::0/20; NO_VALID_PROSPECTIVE_OR_TARGET_BLIND_EVIDENCE_PACK; CANDIDATE_EVIDENCE_PACKS_INVALID::3 |
| `chemistry` | `BLOCKED` | `1` | `0` | `0` | `20` | `1` | `false` | GENUINE_EVIDENCE_N_BELOW_MINIMUM::0/20; NO_VALID_PROSPECTIVE_OR_TARGET_BLIND_EVIDENCE_PACK; CANDIDATE_EVIDENCE_PACKS_INVALID::1 |
| `mathematics` | `BLOCKED` | `1` | `0` | `0` | `20` | `1` | `false` | GENUINE_EVIDENCE_N_BELOW_MINIMUM::0/20; NO_VALID_PROSPECTIVE_OR_TARGET_BLIND_EVIDENCE_PACK; CANDIDATE_EVIDENCE_PACKS_INVALID::1; CURRENT_FORMAL_CORPUS_BASELINE_IS_NOT_EMPIRICAL_GRAND_SCIENCE_EVIDENCE |
| `physics` | `BLOCKED` | `1` | `0` | `0` | `20` | `1` | `false` | GENUINE_EVIDENCE_N_BELOW_MINIMUM::0/20; NO_VALID_PROSPECTIVE_OR_TARGET_BLIND_EVIDENCE_PACK; CANDIDATE_EVIDENCE_PACKS_INVALID::1 |
| `systems` | `BLOCKED` | `4` | `0` | `0` | `20` | `1` | `false` | GENUINE_EVIDENCE_N_BELOW_MINIMUM::0/20; NO_VALID_PROSPECTIVE_OR_TARGET_BLIND_EVIDENCE_PACK; CANDIDATE_EVIDENCE_PACKS_INVALID::4 |

## Candidate Factory

Candidate scan: `validation/heldout/OC133_GRAND_EMPIRICAL_CANDIDATE_SCAN.json`
Decomposition queue: `validation/heldout/OC133_GRAND_EMPIRICAL_DECOMPOSITION_QUEUE.json`
Sample-only pack: `validation/heldout/samples/grand_empirical_evidence_pack.sample.json`

## Bounded Baseline

Current target-blind rows are retained as bounded reconstruction evidence only. They are not promoted to broad domain validation or grand TOE support.

| Domain | Baseline ID | N | Model residual | Comparator residual | Support scope |
| --- | --- | ---: | ---: | ---: | --- |
| `physics` | `OC133-TARGETBLIND-PHYSICS-001` | `1` | `1.4892870576445277e-35` | `1.9864458503739297e-25` | target-blind reconstruction of a held-out CODATA relationship from exact defining constants; not a novel physics law |
| `chemistry` | `OC133-TARGETBLIND-CHEMISTRY-001` | `1` | `0.000280000000000058` | `25.994500000000002` | target-blind reconstruction of a held-out official snapshot field; not a novel chemistry law |
| `biology` | `OC133-TARGETBLIND-BIOLOGY-001` | `1` | `0.0` | `43988.0` | target-blind reconstruction of a held-out NCBI/GEO API snapshot field; not a biological mechanism law |
| `systems` | `OC133-TARGETBLIND-SYSTEMS-001` | `1` | `59572919095.09375` | `4241013358949.0` | retrospective target-blind holdout over pinned WDI rows; not a prospective macroeconomic law |
| `mathematics` | `OC133-TARGETBLIND-MATHEMATICS-001` | `1` | `0.0` | `11.0` | target-blind reconstruction of a finite proof-corpus aggregate; not a TOE truth proof or empirical law |
