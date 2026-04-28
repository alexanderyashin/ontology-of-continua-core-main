from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    report = json.loads((ROOT / "reports" / "OC_CORE_1_3_3_ADVERSARIAL_SIMULATION_REPORT.json").read_text(encoding="utf-8"))
    print(json.dumps(report, indent=2))
    return 0 if report.get("failure_total") == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
