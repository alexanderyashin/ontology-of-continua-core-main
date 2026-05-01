from __future__ import annotations

import argparse
import json

from . import core
from . import lrgef
from . import oc133
from . import publication
from . import public_release
from . import versioning


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m release_machine")
    sub = parser.add_subparsers(dest="command", required=True)

    evaluate = sub.add_parser("evaluate")
    evaluate.add_argument("--release", default=None)
    evaluate.add_argument("--channel", default="all")
    evaluate.add_argument("--mode", default="dry-run")

    sc = sub.add_parser("shit-control")
    sc.add_argument("--release", default=None)
    sc.add_argument("--channel", default="all")
    sc.add_argument("--max-iterations", type=int, default=5)

    package = sub.add_parser("package")
    package.add_argument("--release", default=None)
    package.add_argument("--channel", default="all")
    package.add_argument("--no-publish", action="store_true")

    plan = sub.add_parser("publish-plan")
    plan.add_argument("--release", default=None)
    plan.add_argument("--channel", default="all")

    postflight = sub.add_parser("postflight")
    postflight.add_argument("--release", default=None)
    postflight.add_argument("--channel", default="zenodo")
    postflight.add_argument("--public-url", default="")

    init = sub.add_parser("init")
    init.add_argument("--project", default="logion")
    init.add_argument("--version", default=None)
    init.add_argument("--class", dest="release_class", default="scientific")
    init.add_argument("--root-task", default=None)
    init.add_argument("--source-ref", default="main")
    init.add_argument("--release-id", default=None)

    freeze = sub.add_parser("freeze")
    freeze.add_argument("--release-id", default=None)

    build = sub.add_parser("build")
    build.add_argument("--release-id", default=None)
    build.add_argument("--clean", action="store_true")

    gates = sub.add_parser("gates")
    gates_sub = gates.add_subparsers(dest="gates_command", required=True)
    gates_run = gates_sub.add_parser("run")
    gates_run.add_argument("--release-id", default=None)
    gates_run.add_argument("--all", action="store_true")

    verdict = sub.add_parser("verdict")
    verdict.add_argument("--release-id", default=None)

    sign = sub.add_parser("sign")
    sign.add_argument("--release-id", default=None)

    publish = sub.add_parser("publish")
    publish.add_argument("--release-id", default=None)
    publish.add_argument("--dry-run", action="store_true")
    publish.add_argument("--execute", action="store_true")
    publish.add_argument("--channel", action="append", default=[])

    publish_resume = sub.add_parser("publish-resume")
    publish_resume.add_argument("--release-id", default=None)

    approve = sub.add_parser("owner-approve")
    approve.add_argument("--release-id", default=None)
    approve.add_argument("--owner-identity", default="Alexander Yashin")

    preflight = sub.add_parser("publication-preflight")
    preflight.add_argument("--release-id", default=None)

    submissions = sub.add_parser("submission-packages")
    submissions.add_argument("--release-id", default=None)

    presentation = sub.add_parser("publication-presentation")
    presentation.add_argument("--release-id", default=None)
    presentation.add_argument("--sync", action="store_true")
    presentation.add_argument("--verify", action="store_true")

    repair = sub.add_parser("repair")
    repair.add_argument("--release-id", default=None)

    args = parser.parse_args(argv)
    current = versioning.current_release()
    release = getattr(args, "release", None) or getattr(args, "release_id", None) or current.release_id
    release_id = getattr(args, "release_id", None) or release
    version = getattr(args, "version", None) or current.version
    root_task = getattr(args, "root_task", None) or release_id
    if args.command == "evaluate":
        if release == oc133.RELEASE_ID:
            payload = oc133.evaluate_release(release, args.channel, args.mode, write=True)
        else:
            payload = core.evaluate_release(release, args.channel, args.mode, write=True)
    elif args.command == "shit-control":
        from .engines.shit_control_loop import run
        payload = run(release, args.channel, args.max_iterations)
    elif args.command == "package":
        if release == oc133.RELEASE_ID:
            payload = oc133.build_package(oc133.repo_root(), channel=args.channel, no_publish=args.no_publish)
        else:
            payload = core.build_package(core.repo_root(), channel=args.channel, no_publish=args.no_publish)
        payload["release"] = release
    elif args.command == "publish-plan":
        payload = core.publish_plan(release, args.channel)
    elif args.command == "postflight":
        if release == oc133.RELEASE_ID:
            payload = public_release.postflight(public_release.repo_root(), release_id=release)
        else:
            payload = core.postflight(release, args.channel, args.public_url)
    elif args.command == "init":
        payload = {
            "schema_id": "LRGEF_RELEASE_INIT_v1",
            "project": args.project,
            "release_id": release_id,
            "version": version,
            "release_class": args.release_class,
            "root_task": root_task,
            "source_ref": args.source_ref,
            "policy": lrgef.RELEASE_CLASSES,
            "publish_allowed": False,
        }
    elif args.command == "freeze":
        payload = core.build_package(core.repo_root(), channel="all", no_publish=True)
        payload["release_id"] = release_id
        payload["freeze_status"] = "FROZEN_NO_SEND"
    elif args.command == "build":
        if release_id == oc133.RELEASE_ID:
            payload = oc133.build_package(oc133.repo_root(), channel="all", no_publish=True)
        else:
            payload = core.build_package(core.repo_root(), channel="all", no_publish=True)
        payload["release_id"] = release_id
        payload["clean_requested"] = bool(args.clean)
    elif args.command == "gates":
        if release_id == oc133.RELEASE_ID:
            payload = oc133.evaluate_release(release_id, "all", "pre_publish", write=True)
        else:
            payload = core.evaluate_release(release_id, "all", "pre_publish", write=True)
        payload["gates_command"] = args.gates_command
        payload["all"] = bool(args.all)
    elif args.command == "verdict":
        if release_id == oc133.RELEASE_ID:
            payload = oc133.evaluate_release(release_id, "all", "dry-run", write=True)
        else:
            payload = core.evaluate_release(release_id, "all", "dry-run", write=True)
    elif args.command == "sign":
        summary = core.evaluate_release(release_id, "all", "dry-run", write=True)
        root = core.repo_root()
        signature = core.read_json(root / "releases" / core.RELEASE_ID / "editorial" / "LRGEF_MANIFEST_SIGNATURE_latest.json")
        payload = {"release_id": release_id, "summary": summary, "signature": signature}
    elif args.command == "publish":
        channel = args.channel[0] if len(args.channel) == 1 else "all"
        if release_id == oc133.RELEASE_ID:
            if args.execute and not args.dry_run:
                payload = public_release.publish_execute(public_release.repo_root(), release_id=release_id)
            else:
                payload = public_release.publication_preflight(public_release.repo_root(), release_id=release_id, write=False, require_approval=True)
                payload["dry_run"] = bool(args.dry_run)
                payload["execute_requested"] = bool(args.execute)
                payload["channel"] = channel
        elif args.execute and not args.dry_run:
            payload = publication.publish_execute(core.repo_root())
        else:
            payload = core.publish_plan(release_id, channel)
            payload["dry_run"] = bool(args.dry_run)
            payload["execute_requested"] = bool(args.execute)
            payload["publish_allowed"] = False
    elif args.command == "publish-resume":
        if release_id == oc133.RELEASE_ID:
            payload = public_release.resume_github_after_zenodo(public_release.repo_root(), release_id=release_id)
        else:
            raise ValueError(f"publish-resume is not implemented for {release_id}")
    elif args.command == "owner-approve":
        if release_id == oc133.RELEASE_ID:
            payload = public_release.grant_owner_approval(public_release.repo_root(), release_id=release_id, owner_identity=args.owner_identity)
        else:
            payload = publication.grant_owner_approval(core.repo_root(), owner_identity=args.owner_identity)
    elif args.command == "publication-preflight":
        if release_id == oc133.RELEASE_ID:
            payload = public_release.publication_preflight(public_release.repo_root(), release_id=release_id, write=True, require_approval=True)
        else:
            payload = publication.publication_preflight(core.repo_root())
    elif args.command == "submission-packages":
        payload = publication.generate_submission_packages(core.repo_root(), release_id=release_id)
    elif args.command == "publication-presentation":
        root = core.repo_root()
        if release_id == oc133.RELEASE_ID:
            profile = public_release.load_profile(public_release.repo_root(), release_id)
            payload = public_release.build_public_metadata(public_release.repo_root(), profile, write=bool(args.sync))
            payload["sync_requested"] = bool(args.sync)
            payload["verify_requested"] = bool(args.verify)
        elif args.sync:
            payload = publication.sync_public_release_presentation(root)
            if args.verify:
                payload = {"sync": payload, "verify": publication.verify_public_release_presentation(root)}
        elif args.verify:
            payload = publication.verify_public_release_presentation(root)
        else:
            payload = publication.build_public_release_presentation(root)
    elif args.command == "repair":
        payload = oc133.evaluate_release(release_id, "all", "pre_publish", write=True) if release_id == oc133.RELEASE_ID else core.evaluate_release(release_id, "all", "pre_publish", write=True)
        payload["repair_status"] = "REPAIRED_OR_CONFIRMED_NO_SEND"
    else:
        raise AssertionError(args.command)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0
