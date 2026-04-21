# OC Core 1.3 Release Bundle

This folder contains the outward-facing OC Core 1.3 release bundle for public
review, citation, and archival release.

## Release metadata

- Release line: OC Core 1.3 public release bundle.
- Release date: April 21, 2026.
- Baseline witness: [`commit SHA 7ceb46acfbcb4e83d6568fea3c2530bd9eb95719`](https://github.com/alexanderyashin/ontology-of-continua-core-main/commit/7ceb46acfbcb4e83d6568fea3c2530bd9eb95719).
- Current acceptance state: governed by
  [`editorial/OC_CORE_1_3_CERBERUS_ACCEPTANCE_CERT_latest.json`](editorial/OC_CORE_1_3_CERBERUS_ACCEPTANCE_CERT_latest.json);
  the release verdict is the certificate's `status` field.
- Science-state projection:
  [`editorial/OC_CORE_1_3_SCIENCE_SPOT_latest.json`](editorial/OC_CORE_1_3_SCIENCE_SPOT_latest.json).

The sections below separate the source-owned scientific corpus, bundle-local
projection surfaces, and packaged mirrors. Directories such as `monograph/`,
`journal_core/`, `manuscripts/`, `assets/`, `editorial/dossier_packages/`, and
`editorial/domain_packets/` are bundle contents or mirrors rather than
source-owned science files.

The scientific `PASS` claim in this bundle applies only to the canonical
`CORE_1_3_SCIENCE_ONLY` scope recorded in
`editorial/OC_CORE_1_3_SCIENCE_SPOT_latest.json`. Frame-only and refuted lanes
remain outside the public closure claim and are not promoted here as solved
science.

## Bundle contents

- `monograph/` contains the English master monograph built directly from the public LaTeX source corpus.
- German and Russian guided-reading editions in `monograph/` remain translation drafts under theorem review; they are localised access aids, not proof-bearing master texts.
- `journal_core/` contains the bounded Journal Core article in English plus German and Russian companion translation drafts.
- `manuscripts/` contains EN/DE/RU flagship manuscript variants. Each variant ships as a PDF and companion Markdown file with a shared base stem.
- `assets/` contains the outward visual and table assets shared across the same scientific version.

## Science source corpus

- `editorial/science_sources/` is the source-owned science corpus for the
  release. It contains the authored closure bundles, hostile-review dossiers,
  K-level source rows, and practical-comparison source catalogues from which
  the release-facing projection surfaces are generated.
- Reviewers should cite the source corpus when auditing authored scientific
  support, and cite the projection surfaces when auditing the generated
  release state that appears in the monograph and package.

## Bundle-local projection surfaces

- `editorial/` contains the release-bundled `_latest.json` projection
  surfaces.
- `editorial/OC_CORE_1_3_SCIENCE_SPOT_latest.json` is the bundle-local
  scientific state projection for Core 1.3; the foundational dossier,
  empirical execution surfaces, validation matrix, command board, and generated
  science chapters are generated from the source-owned corpus through this
  SPOT projection.
- `editorial/OC_CORE_1_3_FULL_SCIENTIFIC_CLOSURE_PROGRAM_latest.json` carries the long-horizon closure program.
- `editorial/OC_CORE_1_3_UNIFIED_SCIENCE_ATLAS_latest.json` carries the cross-domain atlas scaffold.
- `editorial/OC_CORE_1_3_PROOF_OBLIGATION_REGISTRY_latest.json` carries the load-bearing proof obligations.
- `editorial/OC_CORE_1_3_HOSTILE_REVIEW_BACKLOG_latest.json` carries the hostile-review blockers.
- `editorial/OC_CORE_1_3_DOMAIN_CLOSURE_BUNDLE_REGISTRY_latest.json` carries the per-claim closure bundles.
- `editorial/OC_CORE_1_3_PHASE1_CLOSED_CORE_DOSSIER_latest.json` carries the first-class Phase 1 closed-core dossier.
- `editorial/OC_CORE_1_3_TOE_SYNTHESIS_latest.json` is the manuscript-facing unified science closure surface. The `TOE` filename is retained for compatibility; public TOE naming is permitted only after the `FINAL_TOE_VALIDATOR_PASS` policy recorded in `editorial/OC_CORE_1_3_SCIENCE_SPOT_latest.json`.
- `editorial/DOMAIN_EMPIRICAL_EXECUTION_PROTOCOLS_latest.json` exposes the hybrid-escalation evidence bar and the per-domain execution discipline.
- `editorial/DOMAIN_BENCHMARK_DATASET_MANIFEST_latest.json` exposes the pinned benchmark datasets and held-out split locks.
- `editorial/DOMAIN_REPLAY_REPORTS_latest.json` exposes the replay packets and their measured outcomes.
- `editorial/INSTITUTE_RUN_MEASUREMENT_PROGRAM_latest.json` is the authoritative
  institute-run measurement surface for stand-by wave packets, lawful command
  chains, and uncovered benchmark families.

## Packaged mirrors

- `editorial/OC_CORE_1_3_PRACTICAL_UTILITY_ATLAS_latest.json` is the release-bundled mirror of the governing practical-status authority `logion/k0/governance/status/OC_CORE_1_3_PRACTICAL_UTILITY_ATLAS_latest.json` cited inside the monograph. The `logion/...` surface remains canonical; the editorial file is its packaged materialisation inside this release bundle.

## Supporting generated dossiers and source package

- `editorial/dossier_packages/` materialises the dossier set on disk: one dossier package per closure bundle, one formal dossier per hostile-review blocker, and one consolidated package for the Phase 1 closed core.
- `editorial/domain_packets/` contains the packaged hard-closure domain dossiers with benchmark routes, replay commands, and falsifier definitions.
- The monograph source package includes the reader guide, source-audit chapter, and foundational consistency dossier.
- The monograph source package includes revision law, minimality ablation ledger, alternative-model competition matrix, and bounded compression benchmark.
- The monograph source package includes the practical-consequences chapter and appendix, which state bounded prediction, audit, comparison, and operational-use lanes while keeping frontier and hypothesis-only rows explicit.
- The monograph source package also includes the generated unified science closure section with explicit K0 through K12 numerical rows.
- The `Theory of Everything Synthesis` title follows that science-spot gate policy.
