# Build Notes — Ontology of Continua Core public build and release pipeline

This document describes the current Core 1.3 public build, validation, and
release flow for the public source repository.

It supersedes the older historical build description. The repository now
supports both source compilation and outward public release hardening.

## 1. Canonical build entrypoint

The canonical local build command is:

```bash
./build_core.sh
```

This script is responsible for the PDF build itself. It is fail-closed for:

- missing required executables;
- structure validation failures;
- missing bibliography inputs;
- missing `build/main.bcf`;
- XeLaTeX or biber failures;
- missing final `build/main.pdf`.

## 2. build_core.sh execution sequence

`build_core.sh` performs the following deterministic steps:

1. verify required commands are available;
2. generate missing section files from `master_core_structure.yaml`;
3. validate repository structure with `tools/validate_core_structure.py`;
4. normalize math in headings and captions with `tools/fix_math_in_headings.py`;
5. regenerate `content/_auto_core_inputs.tex`;
6. copy bibliography into the build area;
7. run XeLaTeX, biber, XeLaTeX, XeLaTeX;
8. fail unless `build/main.pdf` exists.

The script is for the canonical PDF build. Public-release hardening is layered
on top through the explicit validators and staging tools below.

## 3. Public release validation

After the canonical PDF build, the public release lane uses:

```bash
python tools/validate_oc_core_1_3_science_spot.py
python tools/build_oc_public_repo_release_hardening_v8.py
python tools/stage_oc_core_1_3_zenodo_en_release.py --zip-path build_oc_core_1_3_zenodo_en_only.zip
python tools/stage_oc_public_release_artifacts.py --zip-path build_oc_public_release_archive.zip
```

These tools provide:

- science bundle consistency checks;
- public docs/workflow/governance audit;
- deterministic artifact map and archive contract generation;
- explicit public/private parity audit;
- public critique-readiness surfaces;
- deterministic staging for both the Zenodo bundle and reproducibility archive.

## 4. CI workflow

`.github/workflows/build-pdf.yml` is the public CI build-and-validate workflow.

It must:

- build the canonical PDF;
- validate the checked-in science bundle;
- materialize the public release-hardening surfaces;
- stage the Zenodo package and reproducibility archive;
- upload the resulting public artifacts for inspection.

This workflow is allowed to produce `PARTIALLY_HARDENED` public control-plane
state while hardening work is in progress. It still fails closed on missing
artifacts, validator errors, or staging-contract violations.

## 5. Tag release workflow

`.github/workflows/core-release-on-tag.yml` is the release workflow.

It must:

- rebuild the PDF;
- require a Cerberus-clean science bundle;
- materialize the public release-hardening surfaces;
- require `OC_PUBLIC_RELEASE_GATE_CERT_latest.json` to report
  `release_gate_status = RELEASE_SAFE`;
- stage release assets deterministically from the explicit contracts;
- publish only those deterministic assets.

The tag-release workflow must not:

- select the PDF with `find | head`;
- zip the entire repository implicitly;
- exclude workflow provenance from the reproducibility archive;
- outrun the Cerberus/publication gate.

## 6. Deterministic release contracts

The public release lane now depends on these machine-readable contracts:

- `releases/oc_core_1_3/editorial/OC_PUBLIC_RELEASE_ARTIFACT_MAP_latest.json`
- `releases/oc_core_1_3/editorial/OC_PUBLIC_RELEASE_ARCHIVE_CONTRACT_latest.json`
- `releases/oc_core_1_3/editorial/OC_PUBLIC_RELEASE_GATE_CERT_latest.json`
- `releases/oc_core_1_3/editorial/OC_PUBLIC_PRIVATE_DRIFT_AUDIT_latest.json`

These are not commentary. They are the explicit release authority for
public-release safety, parity, and archive composition.

## 7. Zenodo staging policy

The English-only Zenodo bundle remains manifest-driven:

- manifest:
  `releases/oc_core_1_3/OC_CORE_1_3_ZENODO_EN_ONLY_MANIFEST.json`
- staging helper:
  `tools/stage_oc_core_1_3_zenodo_en_release.py`

That tool is the canonical staging authority for the scientific release
package. It may emit a deterministic zip, but it does not discover files on its
own; it follows the manifest exactly.

## 8. Reproducibility archive policy

The reproducibility archive is explicit rather than repo-wide. Its membership
is defined by:

- `OC_PUBLIC_RELEASE_ARTIFACT_MAP_latest.json`
- `OC_PUBLIC_RELEASE_ARCHIVE_CONTRACT_latest.json`

Workflow provenance under `.github/workflows/` is included in that archive so
reviewers can inspect the CI and tag-release rules that produced the public
release surface.
