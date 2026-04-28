from __future__ import annotations

import argparse
import json

from . import core
from . import lrgef
from . import publication


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

    init = sub.add_parser("init")
    init.add_argument("--project", default="logion")
    init.add_argument("--version", default=core.VERSION)
    init.add_argument("--class", dest="release_class", default="scientific")
    init.add_argument("--root-task", default="oc_core_1_3_2")
    init.add_argument("--source-ref", default="main")
    init.add_argument("--release-id", default=core.RELEASE_ID)

    freeze = sub.add_parser("freeze")
    freeze.add_argument("--release-id", default=core.RELEASE_ID)

    build = sub.add_parser("build")
    build.add_argument("--release-id", default=core.RELEASE_ID)
    build.add_argument("--clean", action="store_true")

    gates = sub.add_parser("gates")
    gates_sub = gates.add_subparsers(dest="gates_command", required=True)
    gates_run = gates_sub.add_parser("run")
    gates_run.add_argument("--release-id", default=core.RELEASE_ID)
    gates_run.add_argument("--all", action="store_true")

    verdict = sub.add_parser("verdict")
    verdict.add_argument("--release-id", default=core.RELEASE_ID)

    sign = sub.add_parser("sign")
    sign.add_argument("--release-id", default=core.RELEASE_ID)

    publish = sub.add_parser("publish")
    publish.add_argument("--release-id", default=core.RELEASE_ID)
    publish.add_argument("--dry-run", action="store_true")
    publish.add_argument("--execute", action="store_true")
    publish.add_argument("--channel", action="append", default=[])

    approve = sub.add_parser("owner-approve")
    approve.add_argument("--release-id", default=core.RELEASE_ID)
    approve.add_argument("--owner-identity", default="Alexander Yashin")

    preflight = sub.add_parser("publication-preflight")
    preflight.add_argument("--release-id", default=core.RELEASE_ID)

    submissions = sub.add_parser("submission-packages")
    submissions.add_argument("--release-id", default=core.RELEASE_ID)

    presentation = sub.add_parser("publication-presentation")
    presentation.add_argument("--release-id", default=core.RELEASE_ID)
    presentation.add_argument("--sync", action="store_true")
    presentation.add_argument("--verify", action="store_true")

    repair = sub.add_parser("repair")
    repair.add_argument("--release-id", default=core.RELEASE_ID)

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
    elif args.command == "init":
        payload = {
            "schema_id": "LRGEF_RELEASE_INIT_v1",
            "project": args.project,
            "release_id": args.release_id,
            "version": args.version,
            "release_class": args.release_class,
            "root_task": args.root_task,
            "source_ref": args.source_ref,
            "policy": lrgef.RELEASE_CLASSES,
            "publish_allowed": False,
        }
    elif args.command == "freeze":
        payload = core.build_package(core.repo_root(), channel="all", no_publish=True)
        payload["release_id"] = args.release_id
        payload["freeze_status"] = "FROZEN_NO_SEND"
    elif args.command == "build":
        payload = core.build_package(core.repo_root(), channel="all", no_publish=True)
        payload["release_id"] = args.release_id
        payload["clean_requested"] = bool(args.clean)
    elif args.command == "gates":
        payload = core.evaluate_release(args.release_id, "all", "pre_publish", write=True)
        payload["gates_command"] = args.gates_command
        payload["all"] = bool(args.all)
    elif args.command == "verdict":
        payload = core.evaluate_release(args.release_id, "all", "dry-run", write=True)
    elif args.command == "sign":
        summary = core.evaluate_release(args.release_id, "all", "dry-run", write=True)
        root = core.repo_root()
        signature = core.read_json(root / "releases" / core.RELEASE_ID / "editorial" / "LRGEF_MANIFEST_SIGNATURE_latest.json")
        payload = {"release_id": args.release_id, "summary": summary, "signature": signature}
    elif args.command == "publish":
        channel = args.channel[0] if len(args.channel) == 1 else "all"
        if args.execute and not args.dry_run:
            payload = publication.publish_execute(core.repo_root())
        else:
            payload = core.publish_plan(args.release_id, channel)
            payload["dry_run"] = bool(args.dry_run)
            payload["execute_requested"] = bool(args.execute)
            payload["publish_allowed"] = False
    elif args.command == "owner-approve":
        payload = publication.grant_owner_approval(core.repo_root(), owner_identity=args.owner_identity)
    elif args.command == "publication-preflight":
        payload = publication.publication_preflight(core.repo_root())
    elif args.command == "submission-packages":
        payload = publication.generate_submission_packages(core.repo_root())
    elif args.command == "publication-presentation":
        root = core.repo_root()
        if args.sync:
            payload = publication.sync_public_release_presentation(root)
            if args.verify:
                payload = {"sync": payload, "verify": publication.verify_public_release_presentation(root)}
        elif args.verify:
            payload = publication.verify_public_release_presentation(root)
        else:
            payload = publication.build_public_release_presentation(root)
    elif args.command == "repair":
        payload = core.evaluate_release(args.release_id, "all", "pre_publish", write=True)
        payload["repair_status"] = "REPAIRED_OR_CONFIRMED_NO_SEND"
    else:
        raise AssertionError(args.command)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0
