# OC Core Source-Series Release Bundle

This folder contains the public source-series release bundle used by the current
public pointer `1.4`. The folder name remains `oc_core_1_3` because it is a
concrete source-series and artifact-history path; public version labels are
resolved through `../CURRENT_RELEASE.json`.

- `monograph/` contains the English master monograph built from the public
  LaTeX source corpus.
- `journal_core/` contains the bounded English journal-facing extraction and
  owner-review material.
- `manuscripts/` keeps the flagship-manuscript convenience surface.
- `editorial/science_sources/` is the public source-owned science corpus for
  the release.
- `editorial/domain_packets/` contains the packetized hard-closure domain
  dossiers with benchmark routes, replay commands, and falsifier definitions.
- `editorial/DOMAIN_EMPIRICAL_EXECUTION_PROTOCOLS_latest.json`,
  `editorial/DOMAIN_BENCHMARK_DATASET_MANIFEST_latest.json`,
  `editorial/DOMAIN_REPLAY_REPORTS_latest.json`, and
  `editorial/INSTITUTE_RUN_MEASUREMENT_PROGRAM_latest.json` expose the public
  empirical/replay evidence surfaces where present.
- `OC_CORE_1_3_ZENODO_EN_ONLY_MANIFEST.json` defines the English public package
  intended for owner review before any Zenodo action.

Draft preparation files and non-public working traces are intentionally excluded
from this public release bundle.
