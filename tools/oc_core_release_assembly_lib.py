from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ASSEMBLY_ROOT = ROOT / "operations" / "release_assembly" / "oc_core"

RELEASE_IDENTITY_TOKEN_RE = re.compile(r"\b(?:OC Core\s+)?v?1\.3\.3\b|oc_core_1_3_3", re.IGNORECASE)
COMMON_SURFACE_FORBIDDEN_RE = re.compile(
    r"github|zenodo|\.pdf\b|\.zip\b|publication metadata|public tag|doi mint",
    re.IGNORECASE,
)


def stable_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def compact_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def payload_without_hash(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if key != "artifact_hash"}


def artifact_hash(payload: dict[str, Any]) -> str:
    return sha256_text(compact_json(payload_without_hash(payload)))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def relative(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT.resolve())).replace("\\", "/")


def write_text_if_changed(path: Path, text: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = text.rstrip() + "\n"
    if path.exists() and path.read_text(encoding="utf-8", errors="replace") == normalized:
        return False
    path.write_text(normalized, encoding="utf-8", newline="\n")
    return True


def check_files(files: dict[Path, str]) -> dict[str, Any]:
    missing: list[str] = []
    changed: list[str] = []
    for path, text in files.items():
        expected = text.rstrip() + "\n"
        if not path.exists():
            missing.append(relative(path))
        elif path.read_text(encoding="utf-8", errors="replace") != expected:
            changed.append(relative(path))
    return {"state": "PASS" if not missing and not changed else "FAIL", "missing": missing, "changed": changed}


def write_files(files: dict[Path, str]) -> list[str]:
    changed: list[str] = []
    for path, text in files.items():
        if write_text_if_changed(path, text):
            changed.append(relative(path))
    return changed


def validation_result(files: dict[Path, str], *, write: bool) -> dict[str, Any]:
    if write:
        return {"state": "PASS", "missing": [], "changed": write_files(files)}
    return check_files(files)


def collect_text(payload: Any) -> str:
    if isinstance(payload, dict):
        return "\n".join(f"{key}\n{collect_text(value)}" for key, value in payload.items())
    if isinstance(payload, list):
        return "\n".join(collect_text(value) for value in payload)
    return str(payload)


def assert_no_common_layer_forbidden(payload: dict[str, Any]) -> list[str]:
    text = collect_text(payload)
    failures: list[str] = []
    if RELEASE_IDENTITY_TOKEN_RE.search(text):
        failures.append("common_layer_contains_release_identity_token")
    if COMMON_SURFACE_FORBIDDEN_RE.search(text):
        failures.append("common_layer_contains_publication_or_file_surface_token")
    return failures
