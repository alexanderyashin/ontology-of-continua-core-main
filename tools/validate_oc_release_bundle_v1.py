from __future__ import annotations

from build_oc_core_1_3_1_release_v11 import materialize_oc_core_1_3_1_release_v11


if __name__ == "__main__":
    payload = materialize_oc_core_1_3_1_release_v11(run_id="validate_oc_release_bundle_v1")
    status = payload["control_plane"]["summary"]["release_gate_status"]
    print(status)
    raise SystemExit(0 if status == "RELEASE_READY_NO_SEND" else 1)
