from __future__ import annotations

import json


def main() -> int:
    print(json.dumps({
        "status": "NO_DOWNLOAD_PERFORMED",
        "reason": "v1.3.2 has public discovery routes only; no pinned validation-grade snapshots are claimed.",
        "validation_claim_allowed": False,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
