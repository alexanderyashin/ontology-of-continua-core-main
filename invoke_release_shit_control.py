from __future__ import annotations

import argparse
import json

from release_machine.engines.shit_control_loop import run


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the OC Core release-machine repair/re-audit loop.")
    parser.add_argument("--release", default="oc_core_1_3_2")
    parser.add_argument("--channel", default="all")
    parser.add_argument("--max-iterations", type=int, default=5)
    args = parser.parse_args()
    payload = run(args.release, args.channel, args.max_iterations)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload.get("release_state") == "RELEASE_READY_NO_SEND" else 1


if __name__ == "__main__":
    raise SystemExit(main())
