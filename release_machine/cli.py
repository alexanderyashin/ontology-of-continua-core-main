from __future__ import annotations

import argparse
import json

from . import core
from . import lrgef
from . import oc133
from . import publication
from . import public_release
from . import science_monolith
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

    publish_replace = sub.add_parser("publish-replace")
    publish_replace.add_argument("--release-id", default=None)

    replacement_draft = sub.add_parser("publication-replacement-draft")
    replacement_draft.add_argument("--release-id", default=None)

    public_payload = sub.add_parser("public-payload")
    public_payload.add_argument("--release-id", default=None)
    public_payload.add_argument("--doi", default=None)
    public_payload.add_argument("--zenodo-record-url", default=None)
    public_payload.add_argument("--github-release-url", default=None)
    public_payload.add_argument("--check", action="store_true")

    monolith = sub.add_parser("science-monolith")
    monolith.add_argument("--release-id", default=None)
    monolith.add_argument("--doi", default=None)
    monolith.add_argument("--zenodo-record-url", default=None)
    monolith.add_argument("--check", action="store_true")

    incident = sub.add_parser("incident")
    incident.add_argument("--release-id", default=None)
    incident.add_argument("--write", action="store_true")
    incident.add_argument("--run-self-repair", action="store_true")

    escalation = sub.add_parser("escalation")
    escalation.add_argument("--release-id", default=None)
    escalation.add_argument("--write", action="store_true")
    escalation.add_argument("--check", action="store_true")

    release_spaces = sub.add_parser("release-spaces")
    release_spaces.add_argument("--release-id", default=None)
    release_spaces.add_argument("--write", action="store_true")
    release_spaces.add_argument("--repair", action="store_true")
    release_spaces.add_argument("--check", action="store_true")

    services = sub.add_parser("services")
    services.add_argument("--write", action="store_true")
    services.add_argument("--check", action="store_true")

    function_product = sub.add_parser("function-product")
    function_product.add_argument("--write", action="store_true")
    function_product.add_argument("--check", action="store_true")

    zenodo_republish = sub.add_parser("zenodo-republish")
    zenodo_republish.add_argument("--release-id", default=None)

    zenodo_presentation_repair = sub.add_parser("zenodo-presentation-repair")
    zenodo_presentation_repair.add_argument("--release-id", default=None)

    github_presentation_repair = sub.add_parser("github-presentation-repair")
    github_presentation_repair.add_argument("--release-id", default=None)

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
    elif args.command == "publication-replacement-draft":
        if release_id == oc133.RELEASE_ID:
            payload = public_release.prepare_zenodo_replacement_draft(public_release.repo_root(), release_id=release_id)
        else:
            raise ValueError(f"publication-replacement-draft is not implemented for {release_id}")
    elif args.command == "publish-replace":
        if release_id == oc133.RELEASE_ID:
            payload = public_release.replace_public_release(public_release.repo_root(), release_id=release_id)
        else:
            raise ValueError(f"publish-replace is not implemented for {release_id}")
    elif args.command == "public-payload":
        if release_id == oc133.RELEASE_ID:
            from tools import oc133_public_release_payload
            if args.check:
                payload = oc133_public_release_payload.audit_public_payload(write=False)
            else:
                payload = oc133_public_release_payload.materialize(
                    doi=args.doi,
                    zenodo_record_url=args.zenodo_record_url,
                    github_release_url=args.github_release_url,
                )
        else:
            raise ValueError(f"public-payload is not implemented for {release_id}")
    elif args.command == "science-monolith":
        if release_id == oc133.RELEASE_ID:
            if args.check:
                payload = science_monolith.audit_monolith(science_monolith.repo_root())
            else:
                payload = science_monolith.materialize_monolith(
                    science_monolith.repo_root(),
                    doi=args.doi,
                    zenodo_record_url=args.zenodo_record_url,
                )
        else:
            raise ValueError(f"science-monolith is not implemented for {release_id}")
    elif args.command == "incident":
        if release_id == oc133.RELEASE_ID:
            from tools import logion_incident_pipeline

            payload = logion_incident_pipeline.build_incident_payload()
            if args.run_self_repair:
                execution = logion_incident_pipeline.run_self_repair_contract()
                payload["self_repair_execution"] = execution
                if args.write:
                    logion_incident_pipeline.write_json_if_changed(
                        logion_incident_pipeline.INCIDENT_ROOT / "ARCHITECTURE_SELF_REPAIR_EXECUTION.json",
                        execution,
                    )
            if args.write:
                payload["write_result"] = logion_incident_pipeline.write_incident(payload)
        else:
            raise ValueError(f"incident is not implemented for {release_id}")
    elif args.command == "escalation":
        if release_id == oc133.RELEASE_ID:
            from tools import logion_escalation_matrix

            outputs = logion_escalation_matrix.build_outputs(logion_escalation_matrix.ROOT)
            payload = logion_escalation_matrix.validate(outputs)
            if args.write:
                payload["changed"] = logion_escalation_matrix.write_outputs(logion_escalation_matrix.ROOT, outputs)
            if args.check:
                existing = {
                    "matrix": logion_escalation_matrix.read_json(logion_escalation_matrix.ROOT / logion_escalation_matrix.MATRIX_REL, {}),
                    "playbook": logion_escalation_matrix.read_json(logion_escalation_matrix.ROOT / logion_escalation_matrix.PLAYBOOK_REL, {}),
                    "queue": logion_escalation_matrix.read_json(logion_escalation_matrix.ROOT / logion_escalation_matrix.QUEUE_REL, {}),
                    "cockpit_md": (
                        logion_escalation_matrix.ROOT / logion_escalation_matrix.COCKPIT_REL
                    ).read_text(encoding="utf-8")
                    if (logion_escalation_matrix.ROOT / logion_escalation_matrix.COCKPIT_REL).exists()
                    else "",
                }
                stale = []
                for key in ["matrix", "playbook", "queue"]:
                    if existing[key] != outputs[key]:
                        stale.append(key)
                if existing["cockpit_md"] != outputs["cockpit_md"].rstrip() + "\n":
                    stale.append("cockpit_md")
                payload["stale_output_total"] = len(stale)
                payload["stale_outputs"] = stale
                if stale:
                    payload["state"] = "FAIL"
                    payload["failure_total"] += len(stale)
        else:
            raise ValueError(f"escalation is not implemented for {release_id}")
    elif args.command == "release-spaces":
        if release_id == oc133.RELEASE_ID:
            from tools import logion_release_spaces

            repair = logion_release_spaces.repair_release_space() if args.repair else None
            payload = repair["audit"] if repair else logion_release_spaces.audit_spaces()
            if repair is not None:
                payload = dict(payload)
                payload["repair"] = repair
            if args.write:
                payload["changed"] = logion_release_spaces.write_outputs(repair["audit"] if repair else payload)
            if args.check and payload.get("state") != "PASS":
                print(json.dumps(payload, ensure_ascii=False, indent=2))
                return 1
        else:
            raise ValueError(f"release-spaces is not implemented for {release_id}")
    elif args.command == "services":
        from tools import logion_service_architecture

        outputs = logion_service_architecture.build_registry()
        payload = logion_service_architecture.validate(outputs)
        if args.write:
            payload["changed"] = logion_service_architecture.write_outputs(outputs)
        if args.check:
            existing = {
                "registry": logion_service_architecture.read_json(logion_service_architecture.REGISTRY, {}),
                "contracts": logion_service_architecture.read_json(logion_service_architecture.CONTRACTS, {}),
                "router": logion_service_architecture.read_json(logion_service_architecture.ROUTER, {}),
                "cockpit": (
                    logion_service_architecture.COCKPIT.read_text(encoding="utf-8")
                    if logion_service_architecture.COCKPIT.exists()
                    else ""
                ),
            }
            stale = []
            for key in ["registry", "contracts", "router"]:
                if existing[key] != outputs[key]:
                    stale.append(key)
            if existing["cockpit"] != logion_service_architecture.render_cockpit(outputs).rstrip() + "\n":
                stale.append("cockpit")
            payload["stale_output_total"] = len(stale)
            payload["stale_outputs"] = stale
            if stale:
                payload["state"] = "FAIL"
                payload["failure_total"] += len(stale)
        if args.check and payload.get("state") != "PASS":
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 1
    elif args.command == "function-product":
        from tools import logion_function_product_separation

        outputs = logion_function_product_separation.build_outputs()
        payload = logion_function_product_separation.validate(outputs)
        if args.write:
            payload["changed"] = logion_function_product_separation.write_outputs(outputs, payload)
        if args.check:
            existing = {
                "taxonomy": logion_function_product_separation.read_json(logion_function_product_separation.TAXONOMY, {}),
                "functions": logion_function_product_separation.read_json(logion_function_product_separation.FUNCTIONS, {}),
                "production_lines": logion_function_product_separation.read_json(logion_function_product_separation.PRODUCTION_LINES, {}),
                "products": logion_function_product_separation.read_json(logion_function_product_separation.PRODUCTS, {}),
                "routing": logion_function_product_separation.read_json(logion_function_product_separation.ROUTING, {}),
                "audit": logion_function_product_separation.read_json(logion_function_product_separation.AUDIT, {}),
                "cockpit": (
                    logion_function_product_separation.COCKPIT.read_text(encoding="utf-8")
                    if logion_function_product_separation.COCKPIT.exists()
                    else ""
                ),
            }
            stale = []
            for key, expected in [
                ("taxonomy", outputs["taxonomy"]),
                ("functions", outputs["functions"]),
                ("production_lines", outputs["production_lines"]),
                ("products", outputs["products"]),
                ("routing", outputs["routing"]),
            ]:
                if existing[key] != expected:
                    stale.append(key)
            expected_audit = dict(payload)
            expected_audit.pop("changed", None)
            existing_audit = dict(existing["audit"])
            existing_audit.pop("changed", None)
            if existing_audit != expected_audit:
                stale.append("audit")
            if existing["cockpit"] != logion_function_product_separation.render_cockpit(outputs, payload).rstrip() + "\n":
                stale.append("cockpit")
            payload["stale_output_total"] = len(stale)
            payload["stale_outputs"] = stale
            if stale:
                payload["state"] = "FAIL"
                payload["failure_total"] += len(stale)
        if args.check and payload.get("state") != "PASS":
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 1
    elif args.command == "zenodo-republish":
        if release_id == oc133.RELEASE_ID:
            payload = public_release.republish_clean_zenodo_and_update_github(public_release.repo_root(), release_id=release_id)
        else:
            raise ValueError(f"zenodo-republish is not implemented for {release_id}")
    elif args.command == "zenodo-presentation-repair":
        if release_id == oc133.RELEASE_ID:
            payload = public_release.repair_zenodo_presentation_in_place(public_release.repo_root(), release_id=release_id)
        else:
            raise ValueError(f"zenodo-presentation-repair is not implemented for {release_id}")
    elif args.command == "github-presentation-repair":
        if release_id == oc133.RELEASE_ID:
            payload = public_release.repair_github_presentation(public_release.repo_root(), release_id=release_id)
        else:
            raise ValueError(f"github-presentation-repair is not implemented for {release_id}")
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
