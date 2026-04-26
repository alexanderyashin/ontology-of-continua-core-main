from __future__ import annotations

import argparse
import json

from release_machine import core


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the OC Core release-machine master gate.")
    parser.add_argument("--release", default=core.RELEASE_ID)
    parser.add_argument("--channel", default="all")
    parser.add_argument("--mode", default="pre_publish")
    args = parser.parse_args()
    payload = core.evaluate_release(args.release, args.channel, args.mode, write=True)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload.get("master_verdict") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
