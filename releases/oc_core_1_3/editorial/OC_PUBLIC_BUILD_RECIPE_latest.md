# OC Public Build Recipe

The public Core 1.3 release flow is deterministic and split into four explicit stages:

1. Build the canonical PDF:
   `./build_core.sh`
2. Validate the checked-in Core 1.3 science bundle:
   `python tools/validate_oc_core_1_3_science_spot.py`
3. Materialize public release-hardening surfaces:
   `python tools/build_oc_public_repo_release_hardening_v8.py`
4. Stage deterministic upload and reproducibility archives:
   `python tools/stage_oc_core_1_3_zenodo_en_release.py --zip-path build_oc_core_1_3_zenodo_en_only.zip`
   `python tools/stage_oc_public_release_artifacts.py --zip-path build_oc_public_release_archive.zip`

Tag release is lawful only when `OC_PUBLIC_RELEASE_GATE_CERT_latest.json` reports
`release_gate_status = RELEASE_SAFE`.

The reproducibility archive includes `.github/workflows/` so workflow provenance
remains inspectable inside the release package itself.
