# OC Release Automation Guide

1. Materialize `build_oc_core_1_3_1_release_v11.py`.
2. Refresh contract, bundle inventory, and publish manifest builders.
3. Stage Zenodo package with `stage_oc_zenodo_release_v1.py`.
4. Stop at `RELEASE_READY_NO_SEND` until owner approval.
