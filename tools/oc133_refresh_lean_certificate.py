from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import materialize_oc_core_1_3_3_v12_closure as materializer  # noqa: E402


def main() -> int:
    payload = materializer.write_lean_build_certificate(ROOT)
    summary = {
        "schema_id": "OC133_LEAN_CERTIFICATE_REFRESH_RESULT_v1",
        "release_id": "oc_core_1_3_3",
        "version": "1.3.3",
        "certificate_ref": "formal/lean/LEAN_BUILD_CERTIFICATE_1_3_3.json",
        "returncode": payload.get("returncode"),
        "theorem_ref_missing_total": payload.get("theorem_ref_missing_total"),
        "clean_source_manifest_sha256": payload.get("clean_source_manifest_sha256"),
        "generated_artifact_manifest_sha256": payload.get("generated_artifact_manifest_sha256"),
        "no_send": True,
        "publish_allowed": False,
        "journal_submissions_allowed": False,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if payload.get("returncode") == 0 and payload.get("theorem_ref_missing_total") == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
