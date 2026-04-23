# Repository Architecture — Ontology of Continua Core public source and release corpus

This document defines the current canonical architecture of the public
`ontology-of-continua-core-main` repository as it exists for the Core 1.3
public source and release program.

The repository is source-first, but it is not source-only. It contains:

1. the public scientific source corpus;
2. the deterministic build, validation, and release toolchain;
3. the outward Core 1.3 release bundle and public editorial surfaces.

## 1. Top-level architecture

```text
/
  .github/
    workflows/
      build-pdf.yml
      core-release-on-tag.yml

  appendix/
  bib/
  content/
  figures/
  releases/
    oc_core_1_3/
      assets/
      editorial/
      journal_core/
      manuscripts/
      monograph/
      .zenodo.json
      OC_CORE_1_3_ZENODO_EN_ONLY_MANIFEST.json
      README.md

  tools/
    generate_core_from_yaml.py
    validate_core_structure.py
    generate_auto_inputs.py
    fix_math_in_headings.py
    validate_oc_core_1_3_science_spot.py
    run_oc_core_1_3_cerberus_review.py
    stage_oc_core_1_3_zenodo_en_release.py
    stage_oc_public_release_artifacts.py
    build_oc_public_repo_release_hardening_v8.py
    ...

  main.tex
  preamble.tex
  master_core_structure.yaml
  build_core.sh
  README.md
  ARCHITECTURE.md
  BUILD_NOTES.md
  CONVENTIONS.md
  LICENSE
  .zenodo.json
  VERSION
```

The repository may also contain many `build_*` and review/staging directories
from prior release waves. Those are derived residues, not architectural source
authority.

## 2. Canonical source-owned scientific layer

The canonical public science source layer consists of:

- `main.tex`
- `preamble.tex`
- `content/`
- `appendix/`
- `bib/`
- `figures/`
- `master_core_structure.yaml`

Rules:

- authored science lives in `content/` and `appendix/`;
- figures live in `figures/`;
- bibliography lives in `bib/references.bib`;
- generated include files such as `content/_auto_core_inputs.tex` are derived
  outputs, even when checked in for reproducibility.

## 3. Build and validation layer

The canonical local build entrypoint is:

```text
./build_core.sh
```

The build layer includes:

- source generation and include regeneration;
- structure validation;
- heading math normalization;
- XeLaTeX + biber compilation;
- fail-closed output checks.

Release-critical validation is performed by:

- `tools/validate_oc_core_1_3_science_spot.py`
- `tools/build_oc_public_repo_release_hardening_v8.py`
- `tools/stage_oc_core_1_3_zenodo_en_release.py`
- `tools/stage_oc_public_release_artifacts.py`

The CI and tag-release workflows must call these explicit tools rather than
discovering artifacts ad hoc.

## 4. Core 1.3 release bundle layer

`releases/oc_core_1_3/` is the outward public release bundle.

Its sublayers are:

- `monograph/`: release-facing monograph assets and source package
- `journal_core/`: bounded journal-core route
- `manuscripts/`: flagship manuscript route
- `assets/`: outward visual/table assets
- `editorial/`: public editorial surfaces, public critique packs, and machine
  audit artifacts

`releases/oc_core_1_3/editorial/` is the authoritative home for public
machine-readable release hardening, safety, critique-readiness, and parity
surfaces.

## 5. Public/private boundary

This public repo may contain:

- source-owned science files;
- public editorial surfaces;
- packaged mirrors explicitly intended for public release;
- hostile-review/public critique packs.

This public repo must not contain:

- private Logion owner boards;
- private allocator or revenue wedges;
- internal-only governance queues;
- any public artifact stronger than its source science or stronger than the
  declared public/private parity contract.

If an editorial JSON surface declares a `metadata.surface` path under
`logion/...`, that public file is treated as a packaged mirror or declared
mirror target, not as a blanket authorization to expose the rest of the
private tree.

## 6. Reproducibility and release packaging

Release packaging is explicit and deterministic:

- the English-only Zenodo package is staged from
  `OC_CORE_1_3_ZENODO_EN_ONLY_MANIFEST.json`;
- the public reproducibility archive is staged from
  `OC_PUBLIC_RELEASE_ARTIFACT_MAP_latest.json`;
- tag release must read deterministic asset refs from the artifact map and
  require `OC_PUBLIC_RELEASE_GATE_CERT_latest.json`.

Neither CI nor tag release may use `find | head`, wildcard-only discovery, or
implicit repo-wide zipping as release authority.

## 7. Workflow provenance

`.github/workflows/` is part of the reproducibility story and belongs in the
explicit reproducibility archive. Workflow provenance is not optional metadata;
it is part of the release contract.

## 8. Drift handling

Docs, workflows, and release contracts must describe the repository that
actually exists. If Core 1.3 release architecture changes, this file,
`README.md`, and `BUILD_NOTES.md` must be updated together.
