from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Any
from urllib import error, request

from build_oc_core_1_3_1_independent_release_v14 import (
    PUBLIC_CONTROL_PLANE_PATH,
    PUBLIC_GATE_CERT_PATH,
    PUBLIC_OWNER_GATE_PATH,
    PUBLIC_PUBLISH_MANIFEST_PATH,
    PUBLIC_RELEASE_READY_BOARD_PATH,
    PUBLIC_ZENODO_DRAFT_PATH,
    materialize_oc_core_1_3_1_independent_release_v14,
)


TOOLS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOLS_DIR.parent
EDITORIAL_DIR = REPO_ROOT / "releases" / "oc_core_1_3_1" / "editorial"
PUBLIC_EXECUTION_CERT_PATH = EDITORIAL_DIR / "OC_1_3_1_PUBLIC_RELEASE_EXECUTION_CERT_latest.json"
PUBLIC_EXECUTION_STEPS_PATH = EDITORIAL_DIR / "OC_1_3_1_PUBLIC_RELEASE_EXECUTION_STEPS_latest.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Execute the real OC Core 1.3.1 public release path.")
    parser.add_argument("--tag", default="v1.3.1")
    parser.add_argument("--run-id", default="execute_oc_core_1_3_1_release_v14")
    parser.add_argument("--ci", action="store_true")
    return parser.parse_args()


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _token(*names: str) -> str:
    for name in names:
        value = str(os.environ.get(name, "") or "").strip()
        if value:
            return value
    return ""


def _repo_slug() -> str:
    proc = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if proc.returncode != 0:
        return ""
    remote = proc.stdout.strip()
    if remote.endswith(".git"):
        remote = remote[:-4]
    if remote.startswith("git@github.com:"):
        return remote.split(":", 1)[1]
    if "github.com/" in remote:
        return remote.split("github.com/", 1)[1]
    return ""


def _run(cmd: list[str], *, timeout: int = 1800) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
    )


def _request_json(url: str, *, method: str, token: str, payload: dict[str, Any] | None = None, content_type: str = "application/json") -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/json")
    if payload is not None:
        req.add_header("Content-Type", content_type)
    with request.urlopen(req, timeout=120) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw) if raw.strip() else {}


def _upload_binary(url: str, *, token: str, data: bytes, content_type: str = "application/octet-stream") -> None:
    req = request.Request(url, data=data, method="PUT")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", content_type)
    with request.urlopen(req, timeout=300):
        return


def _asset_paths() -> list[Path]:
    manifest = _read_json(PUBLIC_PUBLISH_MANIFEST_PATH)
    artifact_map_ref = str(manifest.get("artifact_map_ref", "") or "").strip()
    if not artifact_map_ref:
        return []
    artifact_map = _read_json(REPO_ROOT / artifact_map_ref)
    paths = []
    for ref in artifact_map.get("reproducibility_archive_members", []) or []:
        path = REPO_ROOT / str(ref)
        if path.exists() and path.is_file():
            paths.append(path)
    return paths


def _set_blocked_state(*, status: str, github_status: str, zenodo_status: str, detail: str, tag_name: str) -> None:
    control = _read_json(PUBLIC_CONTROL_PLANE_PATH)
    gate = _read_json(PUBLIC_GATE_CERT_PATH)
    owner_gate = _read_json(PUBLIC_OWNER_GATE_PATH)
    ready_board = _read_json(PUBLIC_RELEASE_READY_BOARD_PATH)
    publish_manifest = _read_json(PUBLIC_PUBLISH_MANIFEST_PATH)

    summary = control.get("summary", {})
    summary.update(
        {
            "release_execution_status": status,
            "github_release_status": github_status,
            "zenodo_deposit_status": zenodo_status,
            "tag_name": tag_name,
        }
    )
    control["summary"] = summary
    control["status"] = "WARN"

    gate_summary = gate.get("summary", {})
    gate_summary.update(
        {
            "release_execution_status": status,
            "github_release_status": github_status,
            "zenodo_deposit_status": zenodo_status,
            "tag_name": tag_name,
            "publish_action_performed": False,
        }
    )
    gate["summary"] = gate_summary
    gate["status"] = "WARN"

    owner_gate.update(
        {
            "release_execution_status": status,
            "publish_allowed": False,
            "next_action": detail,
        }
    )

    ready_board["status"] = status
    ready_board["rows"] = list(ready_board.get("rows") or []) + [
        {"gate_id": "RELEASE_EXECUTION", "status": status, "detail": detail}
    ]
    ready_board["summary"] = {**ready_board.get("summary", {}), **summary}

    publish_manifest.update(
        {
            "release_execution_status": status,
            "github_release_status": github_status,
            "zenodo_deposit_status": zenodo_status,
            "tag_name": tag_name,
        }
    )

    _write_json(PUBLIC_CONTROL_PLANE_PATH, control)
    _write_json(PUBLIC_GATE_CERT_PATH, gate)
    _write_json(PUBLIC_OWNER_GATE_PATH, owner_gate)
    _write_json(PUBLIC_RELEASE_READY_BOARD_PATH, ready_board)
    _write_json(PUBLIC_PUBLISH_MANIFEST_PATH, publish_manifest)
    _write_json(
        PUBLIC_EXECUTION_CERT_PATH,
        {
            "schema_id": "OC_1_3_1_PUBLIC_RELEASE_EXECUTION_CERT_v1",
            "status": status,
            "detail": detail,
            "tag_name": tag_name,
            "github_release_status": github_status,
            "zenodo_deposit_status": zenodo_status,
            "publish_action_performed": False,
        },
    )


def _create_or_verify_tag(tag_name: str) -> str:
    existing = _run(["git", "rev-parse", tag_name], timeout=30)
    if existing.returncode == 0:
        current = _run(["git", "rev-parse", "HEAD"], timeout=30)
        if current.returncode == 0 and existing.stdout.strip() == current.stdout.strip():
            return "TAG_ALREADY_PRESENT_ON_HEAD"
        raise RuntimeError(f"Tag {tag_name} already exists on a different commit.")
    proc = _run(["git", "tag", "-a", tag_name, "-m", f"OC Core {tag_name}"], timeout=30)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or f"Failed to create tag {tag_name}.")
    return "TAG_CREATED"


def _push_tag(tag_name: str) -> str:
    proc = _run(["git", "push", "origin", tag_name], timeout=300)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or f"Failed to push tag {tag_name}.")
    return "TAG_PUSHED"


def _github_release(repo_slug: str, tag_name: str, github_token: str, assets: list[Path]) -> str:
    release = _request_json(
        f"https://api.github.com/repos/{repo_slug}/releases",
        method="POST",
        token=github_token,
        payload={
            "tag_name": tag_name,
            "name": f"Ontology of Continua — Core {tag_name}",
            "draft": False,
            "prerelease": False,
            "body": "OC Core 1.3.1 public release built from the v14 independent release authority.",
        },
    )
    upload_url = str(release.get("upload_url", "")).split("{", 1)[0]
    for asset in assets:
        if not upload_url:
            break
        target = f"{upload_url}?name={asset.name}"
        req = request.Request(target, data=asset.read_bytes(), method="POST")
        req.add_header("Authorization", f"Bearer {github_token}")
        req.add_header("Content-Type", "application/octet-stream")
        req.add_header("Accept", "application/json")
        with request.urlopen(req, timeout=600):
            pass
    return "RELEASED"


def _zenodo_publish(zenodo_token: str, tag_name: str) -> str:
    draft = _read_json(PUBLIC_ZENODO_DRAFT_PATH)
    stage = _read_json(EDITORIAL_DIR / "OC_ZENODO_STAGING_PACKAGE_latest.json")
    zip_ref = str(stage.get("zip_ref", "") or "").strip()
    if not zip_ref:
        raise RuntimeError("Zenodo staging zip is missing.")
    zip_path = REPO_ROOT / zip_ref
    if not zip_path.exists():
        raise RuntimeError(f"Zenodo staging zip missing: {zip_path}")

    deposition = _request_json(
        "https://zenodo.org/api/deposit/depositions",
        method="POST",
        token=zenodo_token,
        payload={},
    )
    bucket_url = str((deposition.get("links") or {}).get("bucket", "") or "").strip()
    if not bucket_url:
        raise RuntimeError("Zenodo bucket URL missing.")
    _upload_binary(f"{bucket_url}/{zip_path.name}", token=zenodo_token, data=zip_path.read_bytes(), content_type="application/zip")
    metadata = {
        "metadata": {
            "title": draft.get("title", f"Ontology of Continua — Core {tag_name}"),
            "upload_type": "publication",
            "publication_type": "article",
            "version": draft.get("version", "1.3.1"),
            "description": "OC Core 1.3.1 public release.",
            "creators": [{"name": "Alexander Yashin"}],
        }
    }
    deposition_id = deposition.get("id")
    _request_json(
        f"https://zenodo.org/api/deposit/depositions/{deposition_id}",
        method="PUT",
        token=zenodo_token,
        payload=metadata,
    )
    _request_json(
        f"https://zenodo.org/api/deposit/depositions/{deposition_id}/actions/publish",
        method="POST",
        token=zenodo_token,
        payload={},
    )
    return "PUBLISHED"


if __name__ == "__main__":
    args = parse_args()
    payload = materialize_oc_core_1_3_1_independent_release_v14(run_id=args.run_id)
    summary = payload["control_plane"]["summary"]

    steps: list[dict[str, Any]] = [
        {"step_id": "BUILD", "status": "PASS", "detail": "v14 release authority materialized"}
    ]

    if summary.get("independent_audit_status") != "PASS" or summary.get("reader_route_status") != "PASS":
        detail = "Independent audit or reader route did not pass."
        _set_blocked_state(
            status="BLOCKED_BY_INDEPENDENT_AUDIT",
            github_status=str(summary.get("github_release_status", "NOT_ATTEMPTED")),
            zenodo_status=str(summary.get("zenodo_deposit_status", "NOT_ATTEMPTED")),
            detail=detail,
            tag_name=args.tag,
        )
        _write_json(PUBLIC_EXECUTION_STEPS_PATH, {"rows": steps + [{"step_id": "EXECUTION", "status": "FAIL", "detail": detail}]})
        raise SystemExit(1)

    github_token = _token("GITHUB_TOKEN", "GH_TOKEN")
    zenodo_token = _token("ZENODO_TOKEN", "ZENODO_SANDBOX_TOKEN")
    if not github_token or not zenodo_token:
        detail = "Missing GitHub or Zenodo release credentials in environment."
        _set_blocked_state(
            status="BLOCKED_BY_RELEASE_CHANNEL_CREDENTIALS",
            github_status="READY" if github_token else "AUTH_MISSING",
            zenodo_status="READY" if zenodo_token else "AUTH_MISSING",
            detail=detail,
            tag_name=args.tag,
        )
        _write_json(PUBLIC_EXECUTION_STEPS_PATH, {"rows": steps + [{"step_id": "CHANNEL_AUTH", "status": "FAIL", "detail": detail}]})
        raise SystemExit(1)

    repo_slug = _repo_slug()
    if not repo_slug:
        detail = "Unable to resolve GitHub repository slug from origin remote."
        _set_blocked_state(
            status="BLOCKED_BY_RELEASE_CHANNEL_CREDENTIALS",
            github_status="FAIL",
            zenodo_status="READY",
            detail=detail,
            tag_name=args.tag,
        )
        _write_json(PUBLIC_EXECUTION_STEPS_PATH, {"rows": steps + [{"step_id": "REMOTE", "status": "FAIL", "detail": detail}]})
        raise SystemExit(1)

    try:
        steps.append({"step_id": "TAG_CREATE", "status": "PASS", "detail": _create_or_verify_tag(args.tag)})
        steps.append({"step_id": "TAG_PUSH", "status": "PASS", "detail": _push_tag(args.tag)})
        assets = _asset_paths()
        steps.append({"step_id": "ASSET_INDEX", "status": "PASS", "detail": f"asset_total={len(assets)}"})
        steps.append({"step_id": "GITHUB_RELEASE", "status": "PASS", "detail": _github_release(repo_slug, args.tag, github_token, assets)})
        steps.append({"step_id": "ZENODO", "status": "PASS", "detail": _zenodo_publish(zenodo_token, args.tag)})
    except Exception as exc:
        detail = str(exc)
        _set_blocked_state(
            status="BLOCKED_BY_RELEASE_EXECUTION_ERROR",
            github_status="FAIL",
            zenodo_status="FAIL" if "Zenodo" in detail or "zenodo" in detail else "READY",
            detail=detail,
            tag_name=args.tag,
        )
        steps.append({"step_id": "EXECUTION", "status": "FAIL", "detail": detail})
        _write_json(PUBLIC_EXECUTION_STEPS_PATH, {"rows": steps})
        raise SystemExit(1)

    control = _read_json(PUBLIC_CONTROL_PLANE_PATH)
    gate = _read_json(PUBLIC_GATE_CERT_PATH)
    owner_gate = _read_json(PUBLIC_OWNER_GATE_PATH)
    ready_board = _read_json(PUBLIC_RELEASE_READY_BOARD_PATH)
    publish_manifest = _read_json(PUBLIC_PUBLISH_MANIFEST_PATH)

    control_summary = control.get("summary", {})
    control_summary.update(
        {
            "release_execution_status": "RELEASED",
            "github_release_status": "RELEASED",
            "zenodo_deposit_status": "PUBLISHED",
            "tag_name": args.tag,
        }
    )
    control["summary"] = control_summary
    control["status"] = "PASS"
    gate_summary = gate.get("summary", {})
    gate_summary.update(
        {
            "release_execution_status": "RELEASED",
            "github_release_status": "RELEASED",
            "zenodo_deposit_status": "PUBLISHED",
            "tag_name": args.tag,
            "publish_action_performed": True,
        }
    )
    gate["summary"] = gate_summary
    gate["status"] = "PASS"
    owner_gate.update({"publish_allowed": True, "release_execution_status": "RELEASED"})
    ready_board["status"] = "RELEASED"
    ready_board["summary"] = {**ready_board.get("summary", {}), **control_summary}
    publish_manifest.update(
        {
            "release_execution_status": "RELEASED",
            "github_release_status": "RELEASED",
            "zenodo_deposit_status": "PUBLISHED",
            "tag_name": args.tag,
        }
    )

    _write_json(PUBLIC_CONTROL_PLANE_PATH, control)
    _write_json(PUBLIC_GATE_CERT_PATH, gate)
    _write_json(PUBLIC_OWNER_GATE_PATH, owner_gate)
    _write_json(PUBLIC_RELEASE_READY_BOARD_PATH, ready_board)
    _write_json(PUBLIC_PUBLISH_MANIFEST_PATH, publish_manifest)
    _write_json(
        PUBLIC_EXECUTION_CERT_PATH,
        {
            "schema_id": "OC_1_3_1_PUBLIC_RELEASE_EXECUTION_CERT_v1",
            "status": "RELEASED",
            "tag_name": args.tag,
            "github_release_status": "RELEASED",
            "zenodo_deposit_status": "PUBLISHED",
            "publish_action_performed": True,
        },
    )
    _write_json(PUBLIC_EXECUTION_STEPS_PATH, {"rows": steps})
    print("RELEASED")
