from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from validation.grand_science.evidence_pack_factory import (  # noqa: E402
    build_grand_empirical_payload,
    write_grand_empirical_outputs,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the OC133 grand empirical evidence-pack factory report.")
    parser.add_argument(
        "--allow-blocked-exit-zero",
        action="store_true",
        help="Return zero after writing the factory outputs even when the empirical blocker remains.",
    )
    args = parser.parse_args()
    payload = build_grand_empirical_payload(ROOT)
    write_grand_empirical_outputs(ROOT, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if payload["grand_toe_support_allowed"] is True and payload["blocked_domain_total"] == 0:
        return 0
    return 0 if args.allow_blocked_exit_zero else 2


if __name__ == "__main__":
    raise SystemExit(main())
