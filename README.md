# Ontology of Continua — Core public source corpus

This repository is the canonical public LaTeX source corpus for the
**Ontology of Continua — Core** line and the public release bundle for
**Core 1.3**.

It is no longer accurate to describe this repo as a frozen Core 1.1 shell or a
Core 1.2 architecture-freeze witness. The repository now carries three
distinct but connected layers:

1. the canonical source corpus under the root source tree (`content/`,
   `appendix/`, `bib/`, `figures/`, `main.tex`, `preamble.tex`);
2. the deterministic build and validation pipeline under `build_core.sh`,
   `.github/workflows/`, and `tools/`;
3. the outward Core 1.3 release bundle under `releases/oc_core_1_3/`,
   including editorial `_latest` surfaces, public hostile-review packs, and
   release metadata.

The public/private boundary matters:

- this repository is the public source and release surface;
- `releases/oc_core_1_3/editorial/` contains public editorial surfaces and
  packaged mirrors that are allowed to exist in the public bundle;
- private Logion governance, owner, allocator, and revenue surfaces do **not**
  belong here unless a specific public editorial file is an explicitly declared
  packaged mirror.

## What the repository currently contains

### Canonical source corpus

- `main.tex` and `preamble.tex` as the root LaTeX entrypoints
- scientific content in `content/`
- appendices in `appendix/`
- bibliography in `bib/`
- figures in `figures/`
- section ordering in `master_core_structure.yaml`

### Build and validation pipeline

- `build_core.sh` as the canonical local PDF build entrypoint
- `tools/generate_core_from_yaml.py`
- `tools/validate_core_structure.py`
- `tools/generate_auto_inputs.py`
- `tools/fix_math_in_headings.py`
- `tools/validate_oc_core_1_3_science_spot.py`
- `tools/run_oc_core_1_3_cerberus_review.py`
- `tools/stage_oc_core_1_3_zenodo_en_release.py`
- `.github/workflows/build-pdf.yml`
- `.github/workflows/core-release-on-tag.yml`

### Core 1.3 release bundle

The outward Core 1.3 bundle lives in:

`releases/oc_core_1_3/`

It contains:

- the master monograph and journal-core release routes;
- public editorial `_latest` surfaces;
- public hostile-review and dossier packages;
- Zenodo metadata and the English-only upload manifest;
- release-facing assets and packaged mirrors needed for public review.

### Derived build and staging directories

The repository also contains multiple `build_*` directories and historical
staging folders from prior review and release passes. They are derived outputs,
not canonical source authority. Public release packaging is controlled by
explicit manifests and archive contracts rather than by sweeping up whatever
happens to be present in those directories.

## Current Core 1.3 release routes

- **Canonical source-first route**: the root LaTeX corpus and release bundle
  together define the public Core 1.3 surface.
- **Bundle route**: `releases/oc_core_1_3/` materializes the outward package.
- **Zenodo English-only route**: staged by
  `tools/stage_oc_core_1_3_zenodo_en_release.py` from
  `releases/oc_core_1_3/OC_CORE_1_3_ZENODO_EN_ONLY_MANIFEST.json`.
- **Public hardening route**: materialized by
  `tools/build_oc_public_repo_release_hardening_v8.py`, which emits the public
  audit, artifact-map, archive-contract, parity, and critique-readiness
  surfaces under `releases/oc_core_1_3/editorial/`.

## Local build and validation

Requirements:

- TeX Live 2023+ with `xelatex`
- `biber`
- Python 3

Recommended build:

```bash
./build_core.sh
```

Public release validation:

```bash
python tools/validate_oc_core_1_3_science_spot.py
python tools/build_oc_public_repo_release_hardening_v8.py
python tools/stage_oc_core_1_3_zenodo_en_release.py --zip-path build_oc_core_1_3_zenodo_en_only.zip
python tools/stage_oc_public_release_artifacts.py --zip-path build_oc_public_release_archive.zip
```

Tag release is lawful only when
`releases/oc_core_1_3/editorial/OC_PUBLIC_RELEASE_GATE_CERT_latest.json`
reports `release_gate_status = RELEASE_SAFE`.

## Structure overview

- `content/` and `appendix/`: authored scientific source
- `tools/`: generation, validation, Cerberus, staging, and public-release
  hardening helpers
- `.github/workflows/`: CI and tag-release execution
- `releases/oc_core_1_3/`: outward release bundle
- `releases/oc_core_1_3/editorial/`: public editorial surfaces and critique
  packs

For the authoritative repo structure and build law, see:

- `ARCHITECTURE.md`
- `BUILD_NOTES.md`
- `CONVENTIONS.md`
