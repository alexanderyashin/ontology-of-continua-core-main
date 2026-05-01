from __future__ import annotations

import contextlib
import io
import json
import runpy
import argparse
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--materialize-if-missing",
        action="store_true",
        help="Developer repair mode only. Release checks read existing reports and must not rewrite release artifacts.",
    )
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    report = root / "reports" / "OC_CORE_1_3_3_COUNTEREXAMPLE_REPORT.json"
    if not report.exists() and args.materialize_if_missing:
        with contextlib.redirect_stdout(io.StringIO()):
            try:
                runpy.run_path(str(root / "tools" / "materialize_oc_core_1_3_3_v12_closure.py"), run_name="__main__")
            except SystemExit as exc:
                if int(exc.code or 0) != 0:
                    raise
    if not report.exists():
        print(json.dumps({
            "schema_id": "OC133_COUNTEREXAMPLE_REPORT_READONLY_MISSING_v1",
            "failure_total": 1,
            "open_counterexample_total": 1,
            "error": "counterexample report missing; run explicit repair/materialization outside release verification",
        }, indent=2))
        return 1
    payload = json.loads(report.read_text(encoding="utf-8"))
    print(json.dumps(payload, indent=2))
    return 0 if payload.get("failure_total") == 0 and payload.get("open_counterexample_total", 0) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
