from __future__ import annotations

from build_oc_core_1_3_1_release_v11 import materialize_oc_core_1_3_1_release_v11


if __name__ == "__main__":
    payload = materialize_oc_core_1_3_1_release_v11(run_id="stage_oc_zenodo_release_v1")
    print(payload["control_plane"]["refs"]["zenodo_stage_ref"])
