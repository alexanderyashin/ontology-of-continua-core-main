from __future__ import annotations

import argparse
import json

from . import core


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m release_machine")
    sub = parser.add_subparsers(dest="command", required=True)

    evaluate = sub.add_parser("evaluate")
    evaluate.add_argument("--release", default=core.RELEASE_ID)
    evaluate.add_argument("--channel", default="all")
    evaluate.add_argument("--mode", default="dry-run")

    sc = sub.add_parser("shit-control")
    sc.add_argument("--release", default=core.RELEASE_ID)
    sc.add_argument("--channel", default="all")
    sc.add_argument("--max-iterations", type=int, default=5)

    package = sub.add_parser("package")
    package.add_argument("--release", default=core.RELEASE_ID)
    package.add_argument("--channel", default="all")
    package.add_argument("--no-publish", action="store_true")

    plan = sub.add_parser("publish-plan")
    plan.add_argument("--release", default=core.RELEASE_ID)
    plan.add_argument("--channel", default="all")

    postflight = sub.add_parser("postflight")
    postflight.add_argument("--release", default=core.RELEASE_ID)
    postflight.add_argument("--channel", default="zenodo")
    postflight.add_argument("--public-url", default="")

    args = parser.parse_args(argv)
    if args.command == "evaluate":
        payload = core.evaluate_release(args.release, args.channel, args.mode, write=True)
    elif args.command == "shit-control":
        from .engines.shit_control_loop import run
        payload = run(args.release, args.channel, args.max_iterations)
    elif args.command == "package":
        payload = core.build_package(core.repo_root(), channel=args.channel, no_publish=args.no_publish)
        payload["release"] = args.release
    elif args.command == "publish-plan":
        payload = core.publish_plan(args.release, args.channel)
    elif args.command == "postflight":
        payload = core.postflight(args.release, args.channel, args.public_url)
    else:
        raise AssertionError(args.command)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0
