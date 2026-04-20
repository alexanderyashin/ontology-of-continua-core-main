from __future__ import annotations

import argparse
import sys

from oc_core_1_3_science_spot_lib import REPO_ROOT, build_spot, load_input_bundle, validate_existing_bundle, write_projection_bundle


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the OC Core 1.3 science SPOT and all derived science surfaces.")
    parser.parse_args()
    inputs = load_input_bundle(REPO_ROOT)
    spot = build_spot(inputs, repo_root=REPO_ROOT)
    write_projection_bundle(spot)
    errors = validate_existing_bundle(REPO_ROOT)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Built OC Core 1.3 science SPOT and synchronized derived surfaces.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
