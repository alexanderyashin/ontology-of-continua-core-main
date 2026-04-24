# OC Core 1.3.2 Reproducibility

Reproducibility entry points:
- `python -m release_machine evaluate --release oc_core_1_3_2 --channel all --mode dry-run`
- `python -m release_machine shit-control --release oc_core_1_3_2 --channel all --max-iterations 5`
- `python simulations/run_all.py --write-report`
- `python -m release_machine package --release oc_core_1_3_2 --channel all --no-publish`

The resulting release state is `RELEASE_READY_NO_SEND`. External publication remains impossible until owner approval binds the exact artifact hashes and publish manifest.
