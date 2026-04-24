from __future__ import annotations

import json
from pathlib import Path


def main() -> int:
    path = Path(__file__).resolve().parents[1] / "OC_DATASET_MANIFEST_1_3_2.json"
    print(json.dumps(json.loads(path.read_text(encoding="utf-8")), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
