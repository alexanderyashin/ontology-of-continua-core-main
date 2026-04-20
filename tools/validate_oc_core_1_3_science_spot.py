from __future__ import annotations

import argparse
import sys

from oc_core_1_3_science_spot_lib import REPO_ROOT, validate_existing_bundle


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the OC Core 1.3 science SPOT and its projected surfaces.")
    parser.add_argument(
        "--require-final-toe-pass",
        action="store_true",
        help="Fail unless the repository already satisfies the full final TOE closure bar.",
    )
    args = parser.parse_args()
    errors = validate_existing_bundle(REPO_ROOT, require_final_toe_pass=args.require_final_toe_pass)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("OC Core 1.3 science SPOT bundle is internally consistent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
