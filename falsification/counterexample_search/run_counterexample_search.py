from __future__ import annotations

import contextlib
import io
import json
import runpy
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    with contextlib.redirect_stdout(io.StringIO()):
        runpy.run_path(str(root / "tools" / "materialize_oc_core_1_3_3_v12_closure.py"), run_name="__main__")
    payload = json.loads((root / "reports" / "OC_CORE_1_3_3_COUNTEREXAMPLE_REPORT.json").read_text(encoding="utf-8"))
    print(json.dumps(payload, indent=2))
    return 0 if payload.get("failure_total") == 0 and payload.get("open_counterexample_total", 0) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
