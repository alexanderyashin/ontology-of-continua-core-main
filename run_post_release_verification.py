from __future__ import annotations

import argparse
import json

from release_machine import core


def main() -> int:
    parser = argparse.ArgumentParser(description="Run post-release verification after owner-approved publication.")
    parser.add_argument("--release", default=core.RELEASE_ID)
    parser.add_argument("--channel", default="zenodo")
    parser.add_argument("--public-url", default="")
    args = parser.parse_args()
    payload = core.postflight(args.release, args.channel, args.public_url)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
