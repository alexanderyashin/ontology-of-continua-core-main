from __future__ import annotations

import argparse
import sys

from oc_core_1_3_cerberus_lib import validate_existing_cerberus_bundle
from oc_core_1_3_science_spot_lib import REPO_ROOT, validate_existing_bundle


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the OC Core 1.3 science SPOT and its projected surfaces.")
    parser.add_argument(
        "--require-final-toe-pass",
        action="store_true",
        help="Fail unless the repository already satisfies the full final synthesis closure bar.",
    )
    parser.add_argument(
        "--require-cerberus-clean",
        action="store_true",
        help="Fail unless the Cerberus release-review bundle exists, matches the current HEAD, and reports zero open defect findings.",
    )
    parser.add_argument(
        "--allow-cerberus-pending",
        action="store_true",
        help=(
            "Permit a science-only final TOE validation before the mandatory Cerberus run. "
            "The release gate must still pass --require-cerberus-clean afterwards."
        ),
    )
    args = parser.parse_args()
    errors = validate_existing_bundle(REPO_ROOT, require_final_toe_pass=args.require_final_toe_pass)
    require_cerberus_clean = args.require_cerberus_clean or (
        args.require_final_toe_pass and not args.allow_cerberus_pending
    )
    if require_cerberus_clean:
        errors.extend(validate_existing_cerberus_bundle(REPO_ROOT, require_clean=True))
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("OC Core 1.3 science SPOT bundle is internally consistent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
