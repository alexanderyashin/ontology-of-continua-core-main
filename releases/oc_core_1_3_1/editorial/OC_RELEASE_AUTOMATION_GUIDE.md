# OC Release Automation Guide

1. Materialize `build_oc_core_1_3_1_release_v11.py`.
2. Refresh the source-bound manuscript tree, release contract, and bundle inventory.
3. Validate that mandatory manuscript artifacts are substantive and source-bound before trusting compile success.
4. Stage Zenodo package with `stage_oc_zenodo_release_v1.py`.
5. Stop at `RELEASE_READY_NO_SEND` until owner approval.
