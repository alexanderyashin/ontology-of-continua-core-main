# OC Core 1.3 Release Bundle

This folder contains the outward-facing OC Core 1.3 bundle for public review,
citation, and archival use.

## Static release metadata

- Release line: OC Core 1.3 public release bundle.
- Versioned release name: Ontology of Continua — Core v1.3.0. The short
  bundle label `Core 1.3` and the semantic version `v1.3.0` refer to the same
  release.
- Release date: April 22, 2026.
- Public source witness: public `v1.2.1` source commit
  [`2c61b7879ed36cd8366d87892a066082b6418ce8`](https://github.com/alexanderyashin/ontology-of-continua-core-main/commit/2c61b7879ed36cd8366d87892a066082b6418ce8),
  paired with the archived Core v1.2.0 DOI witness.

## Citation

For public citation, use the release metadata in the bundle-local
[`./.zenodo.json`](.zenodo.json) together with the archived DOI record when
the bundle is deposited. Until deposition, use this provisional citation:

- Author: Alexander Yashin.
- Title: *Ontology of Continua — Core v1.3.0*.
- Repository: [`alexanderyashin/ontology-of-continua-core-main`](https://github.com/alexanderyashin/ontology-of-continua-core-main).
- Release date: April 22, 2026.
- Public source witness: public `v1.2.1` source commit
  [`2c61b7879ed36cd8366d87892a066082b6418ce8`](https://github.com/alexanderyashin/ontology-of-continua-core-main/commit/2c61b7879ed36cd8366d87892a066082b6418ce8).

## Gate status snapshot

Current public-readiness rule: this bundle is publication-ready only when the
Cerberus certificate reports both `status = PASS` and `llm_gate_status = PASS`.
The files below are the machine-readable evidence for that status.
Current checked-in gate state is the certificate linked below; this README is
only a pointer to the machine-readable release surfaces.

- Snapshot source:
  [`editorial/OC_CORE_1_3_CERBERUS_ACCEPTANCE_CERT_latest.json`](editorial/OC_CORE_1_3_CERBERUS_ACCEPTANCE_CERT_latest.json).
- Cerberus scope: the scripted release-review authority
  `OC_CORE_1_3_ENGLISH_FLAGSHIP_RELEASE_PACKAGE`.
- Current inline status: this README is a pointer to the checked-in Cerberus
  surfaces; publication readiness is not claimed unless the certificate itself
  reports `status = PASS` and `llm_gate_status = PASS`.
- Checked-in Cerberus verdict: inspect
  [`editorial/OC_CORE_1_3_CERBERUS_ACCEPTANCE_CERT_latest.json`](editorial/OC_CORE_1_3_CERBERUS_ACCEPTANCE_CERT_latest.json)
  and
  [`editorial/OC_CORE_1_3_CERBERUS_REVIEW_FINDINGS_latest.json`](editorial/OC_CORE_1_3_CERBERUS_REVIEW_FINDINGS_latest.json)
  for the current gate state and open findings.
- Publication readiness requires regenerating
  [`editorial/OC_CORE_1_3_CERBERUS_ACCEPTANCE_CERT_latest.json`](editorial/OC_CORE_1_3_CERBERUS_ACCEPTANCE_CERT_latest.json)
  with `status = PASS` and `llm_gate_status = PASS`.
- The public synthesis title is `Unified Science Synthesis`. Compatibility
  filenames used by tooling are not public claim language and must not be read
  as a claim that OC is an unrestricted universal explanation.

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

## Permanent publication dedication

Every OC Core release from Core 1.3 onward carries the author's title-page
dedication in each active publication-language monograph route. The exact
dedication is guarded by the `DEDICATION_REQUIRED_DO_NOT_REMOVE` and
`OC_CORE_PUBLICATION_DEDICATION` markers in the monograph frontmatter. For this
English-only release gate, Cerberus treats omission, text drift, or
root/release-source mirror drift in the English route as a release-blocking
defect. Russian and German dedication carriers remain in the source tree for
the deferred translation work.

## Bundle contents

- `monograph/` contains the release-ready English master monograph built from
  the full Core 1.3 platinum source graph. Russian and German translation
  sources may be present in the repository, but they are deferred with status
  `DEFERRED_TRANSLATION_REVIEW_REQUIRED` and are not part of this release gate.
- `journal_core/` contains the bounded Journal Core article in English. Any
  Russian or German companion translation files are draft/deferred materials
  until they pass their own translation review.
- `manuscripts/` contains the English flagship manuscript PDF and companion
  Markdown surface for the same scientific version. The English manuscript PDF
  and English master monograph PDF are generated from the same accepted
  flagship build and must remain hash-identical.
- `assets/` contains the outward visual and table assets shared across the same scientific version.

## Zenodo upload manifest

The Core 1.3 Zenodo upload is English-only. The upload set is defined by
[`OC_CORE_1_3_ZENODO_EN_ONLY_MANIFEST.json`](OC_CORE_1_3_ZENODO_EN_ONLY_MANIFEST.json)
and staged by:

```powershell
python tools\stage_oc_core_1_3_zenodo_en_release.py
```

The staging helper copies only manifest-listed files into
`build_oc_core_1_3_zenodo_en_only/`. Russian and German PDFs, Markdown files,
localized assets, and localized LaTeX source files remain in the repository as
deferred Core 1.3.1 translation draft work, but they are excluded from the
Core 1.3 Zenodo upload.

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
- Science-state projection authority:
  `editorial/OC_CORE_1_3_SCIENCE_SPOT_latest.json`, the Science Projection
  and Operational Truth surface.
- `editorial/OC_CORE_1_3_SCIENCE_SPOT_latest.json` is the bundle-local
  scientific state projection for Core 1.3; the foundational dossier,
  empirical execution surfaces, validation matrix, command board, and science
  chapters are projected from the source-owned corpus through this SPOT
  surface.
- `editorial/OC_CORE_1_3_FULL_SCIENTIFIC_CLOSURE_PROGRAM_latest.json` carries the long-horizon closure program.
- `editorial/OC_CORE_1_3_UNIFIED_SCIENCE_ATLAS_latest.json` carries the cross-domain atlas scaffold.
- `editorial/OC_CORE_1_3_PROOF_OBLIGATION_REGISTRY_latest.json` carries the load-bearing proof obligations.
- `editorial/OC_CORE_1_3_HOSTILE_REVIEW_BACKLOG_latest.json` carries the hostile-review blockers.
- `editorial/OC_CORE_1_3_DOMAIN_CLOSURE_BUNDLE_REGISTRY_latest.json` carries the per-claim closure bundles.
- `editorial/OC_CORE_1_3_PHASE1_CLOSED_CORE_DOSSIER_latest.json` carries the first-class Phase 1 closed-core dossier.
- `editorial/OC_CORE_1_3_UNIFIED_SYNTHESIS_latest.json` is the
  manuscript-facing unified science closure surface generated from
  `editorial/OC_CORE_1_3_SCIENCE_SPOT_latest.json`.
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
- The monograph source package includes the reader guide, source-audit chapter,
  foundational consistency dossier, revision law, minimality ablation ledger,
  alternative-model competition matrix, and bounded compression benchmark.
- Its practical-consequences chapter and appendix state bounded prediction,
  audit, comparison, and operational-use lanes while keeping frontier and
  hypothesis-only rows explicit.
- Its generated unified science synthesis section includes explicit K0 through
  K12 numerical rows.
