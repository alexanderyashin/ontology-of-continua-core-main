from __future__ import annotations

import json
from pathlib import Path

from build_oc_core_1_3_1_independent_release_v14 import materialize_oc_core_1_3_1_independent_release_v14


if __name__ == "__main__":
    materialize_oc_core_1_3_1_independent_release_v14(run_id="stage_oc_zenodo_release_v1")
    stage_path = Path("releases/oc_core_1_3_1/editorial/OC_ZENODO_STAGING_PACKAGE_latest.json")
    payload = json.loads(stage_path.read_text(encoding="utf-8")) if stage_path.exists() else {}
    print(payload.get("zip_ref", ""))
