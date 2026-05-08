from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


CURRENT_RELEASE_MARKER = "CURRENT_RELEASE.json"
ENV_OVERRIDE_UNLOCK = "OC_RELEASE_ALLOW_OVERRIDE"
RELEASE_ID_RE = re.compile(r"^oc_core_(\d+)_(\d+)_(\d+)(?:_(.+))?$")
BRANCH_VERSION_RE = re.compile(r"oc[-_]core[-_](\d+)\.(\d+)\.(\d+)", re.I)


@dataclass(frozen=True)
class ReleaseIdentity:
    release_id: str
    version: str
    source: str


def release_id_from_version(version: str) -> str:
    parts = version.strip().split(".")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        raise ValueError(f"Unsupported release version: {version!r}")
    return "oc_core_" + "_".join(parts)


def version_from_release_id(release_id: str) -> str:
    match = RELEASE_ID_RE.match(release_id.strip())
    if not match:
        raise ValueError(f"Unsupported release id: {release_id!r}")
    return ".".join(match.group(index) for index in (1, 2, 3))


def _repo_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / ".git").exists() and (candidate / "releases").exists():
            return candidate
    return current


def _git_branch(root: Path) -> str:
    try:
        completed = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=root,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=30,
        )
    except Exception:
        return ""
    return completed.stdout.strip() if completed.returncode == 0 else ""


def _identity_from_branch(root: Path) -> ReleaseIdentity | None:
    branch = _git_branch(root)
    match = BRANCH_VERSION_RE.search(branch)
    if not match:
        return None
    version = ".".join(match.group(index) for index in (1, 2, 3))
    release_id = release_id_from_version(version)
    if (root / "releases" / release_id).exists():
        return ReleaseIdentity(release_id=release_id, version=version, source=f"git_branch:{branch}")
    return None


def _identity_from_marker(root: Path) -> ReleaseIdentity | None:
    path = root / "releases" / CURRENT_RELEASE_MARKER
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        release_id = str(payload["release_id"])
        version = str(payload.get("version") or version_from_release_id(release_id))
    except Exception:
        return None
    if (root / "releases" / release_id).exists():
        return ReleaseIdentity(release_id=release_id, version=version, source=f"marker:{path.as_posix()}")
    return None


def _identity_from_root_version(root: Path) -> ReleaseIdentity | None:
    path = root / "VERSION"
    if not path.exists():
        return None
    try:
        version = path.read_text(encoding="utf-8").strip()
        release_id = release_id_from_version(version)
    except Exception:
        return None
    if (root / "releases" / release_id).exists():
        return ReleaseIdentity(release_id=release_id, version=version, source=f"root_version:{path.as_posix()}")
    return None


def _release_sort_key(release_id: str) -> tuple[int, int, int, str] | None:
    match = RELEASE_ID_RE.match(release_id)
    if not match:
        return None
    suffix = match.group(4) or ""
    # Stable releases outrank prerelease suffixes with the same numeric version.
    suffix_rank = "z" if not suffix else suffix
    return (int(match.group(1)), int(match.group(2)), int(match.group(3)), suffix_rank)


def _identity_from_latest_release_dir(root: Path) -> ReleaseIdentity | None:
    releases_dir = root / "releases"
    stable_candidates: list[tuple[tuple[int, int, int, str], str]] = []
    prerelease_candidates: list[tuple[tuple[int, int, int, str], str]] = []
    if not releases_dir.exists():
        return None
    for path in releases_dir.iterdir():
        if not path.is_dir():
            continue
        key = _release_sort_key(path.name)
        if key is not None:
            if RELEASE_ID_RE.match(path.name).group(4):
                prerelease_candidates.append((key, path.name))
            else:
                stable_candidates.append((key, path.name))
    candidates = stable_candidates or prerelease_candidates
    if not candidates:
        return None
    release_id = sorted(candidates)[-1][1]
    return ReleaseIdentity(release_id=release_id, version=version_from_release_id(release_id), source="latest_release_dir")


def current_release(start: Path | None = None) -> ReleaseIdentity:
    root = _repo_root(start)
    env_release = os.environ.get("OC_RELEASE_ID", "").strip()
    env_version = os.environ.get("OC_RELEASE_VERSION", "").strip()
    env_override_allowed = os.environ.get(ENV_OVERRIDE_UNLOCK, "").strip() in {"1", "true", "TRUE", "yes", "YES"}
    if env_override_allowed and env_release:
        return ReleaseIdentity(
            release_id=env_release,
            version=env_version or version_from_release_id(env_release),
            source="env:OC_RELEASE_ID",
        )
    if env_override_allowed and env_version:
        return ReleaseIdentity(
            release_id=release_id_from_version(env_version),
            version=env_version,
            source="env:OC_RELEASE_VERSION",
        )
    # The owner-controlled marker is the canonical public-version pointer.
    # Branch names and legacy VERSION files are fallbacks for historical or
    # fixture contexts only; they must not override the current public release
    # decision.
    for resolver in (_identity_from_marker, _identity_from_branch, _identity_from_root_version, _identity_from_latest_release_dir):
        identity = resolver(root)
        if identity is not None:
            return identity
    raise RuntimeError(f"Could not resolve current release under {root}")


def write_current_release_marker(root: Path, release_id: str, version: str, *, source: str) -> Path:
    path = root / "releases" / CURRENT_RELEASE_MARKER
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_id": "OC_CURRENT_RELEASE_POINTER_v1",
        "release_id": release_id,
        "version": version,
        "source": source,
        "policy": f"Current release is resolved by this owner-controlled marker first, then git branch, root VERSION, and highest stable release directory. Env override requires {ENV_OVERRIDE_UNLOCK}=1.",
        "publish_allowed": False,
        "no_send": True,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return path
