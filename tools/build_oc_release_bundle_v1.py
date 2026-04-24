from __future__ import annotations

from build_oc_core_1_3_1_independent_release_v14 import materialize_oc_core_1_3_1_independent_release_v14


if __name__ == "__main__":
    payload = materialize_oc_core_1_3_1_independent_release_v14(run_id="build_oc_release_bundle_v1")
    print(payload["control_plane"]["refs"]["artifact_inventory_ref"])
