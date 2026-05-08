# OC Core 1.3.3 Grand Empirical Report

Verdict: `EMPIRICAL_DOMAIN_SUPPORT_ALLOWED`
Empirical-domain support allowed: `true`
TOE/final/broad modern-science promotion allowed by this gate: `false`
Candidate evidence packs: `19`
Current evidence packs: `5`
Superseded evidence packs: `14`
Valid evidence packs: `4`
Bounded baseline rows: `5`
Blocked empirical domains: `0/4`
Formal required domains: `1`
Decomposition queue rows: `0`
Sync run: `not-bound`
Source artifact set: `not-bound`

This factory/gate emits only bounded empirical-domain support from qualifying packs. It does not emit TOE, final-theory, broad modern-science coverage, or modern-science superiority promotion from bounded OC133 reconstructions, sample packs, or artifact existence. Unresolved domains remain BLOCKED until prospective or target-blind evidence packs clear the configured criteria.
Formal required domains are exposed here as dependencies, but excluded from empirical support counts and blockers.

| Domain | Status | Candidate packs | Current packs | Superseded packs | Valid packs | Valid N | Minimum N | Bounded baseline rows | Empirical-domain support | TOE/final promotion | Blockers |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| `biology` | `EVIDENCE_SUFFICIENT_PENDING_REVIEW` | `5` | `1` | `4` | `1` | `30` | `20` | `1` | `true` | `false` |  |
| `chemistry` | `EVIDENCE_SUFFICIENT_PENDING_REVIEW` | `4` | `1` | `3` | `1` | `20` | `20` | `1` | `true` | `false` |  |
| `physics` | `EVIDENCE_SUFFICIENT_PENDING_REVIEW` | `2` | `1` | `1` | `1` | `44` | `20` | `1` | `true` | `false` |  |
| `systems` | `EVIDENCE_SUFFICIENT_PENDING_REVIEW` | `7` | `1` | `6` | `1` | `20` | `20` | `1` | `true` | `false` |  |

## Formal Route Dependencies

| Domain | Route | Status | Empirical support allowed | Formal support report |
| --- | --- | --- | --- | --- |
| `mathematics` | `formal` | `ROUTED_TO_FORMAL_SUPPORT` | `false` | validation/heldout/grand_science/mathematics/OC133_MATHEMATICS_EVIDENCE_EXECUTION_REPORT.json |

## Candidate Factory

Candidate scan: `validation/heldout/OC133_GRAND_EMPIRICAL_CANDIDATE_SCAN.json`
Decomposition queue: `validation/heldout/OC133_GRAND_EMPIRICAL_DECOMPOSITION_QUEUE.json`
Sample-only pack: `validation/heldout/samples/grand_empirical_evidence_pack.sample.json`

## Bounded Baseline

Current target-blind rows are retained as bounded reconstruction evidence only. They are not promoted to broad domain validation, TOE/final-theory support, or modern-science superiority.

| Domain | Baseline ID | N | Model residual | Comparator residual | Support scope |
| --- | --- | ---: | ---: | ---: | --- |
| `physics` | `OC133-TARGETBLIND-PHYSICS-001` | `1` | `1.4892870576445277e-35` | `1.9864458503739297e-25` | target-blind reconstruction of a held-out CODATA relationship from exact defining constants; not a novel physics law |
| `chemistry` | `OC133-TARGETBLIND-CHEMISTRY-001` | `1` | `0.000280000000000058` | `25.994500000000002` | target-blind reconstruction of a held-out official snapshot field; not a novel chemistry law |
| `biology` | `OC133-TARGETBLIND-BIOLOGY-001` | `1` | `0.0` | `43988.0` | target-blind reconstruction of a held-out NCBI/GEO API snapshot field; not a biological mechanism law |
| `systems` | `OC133-TARGETBLIND-SYSTEMS-001` | `1` | `59572919095.09375` | `4241013358949.0` | retrospective target-blind holdout over pinned WDI rows; not a prospective macroeconomic law |
| `mathematics` | `OC133-TARGETBLIND-MATHEMATICS-001` | `1` | `0.0` | `11.0` | target-blind reconstruction of a finite proof-corpus aggregate; not a TOE truth proof or empirical law |
