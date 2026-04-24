# Run All

- materialize the release authority: `python tools/build_oc_core_1_3_1_independent_release_v14.py`
- validate the release bundle: `python tools/validate_oc_release_bundle_v1.py`
- run the simulation corpus: `python simulations/run_all.py`
- attempt the release when fully authorized: `python tools/execute_oc_core_1_3_1_release_v14.py --tag v1.3.1`
