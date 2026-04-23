from __future__ import annotations

import argparse
import json
import re
import shutil
import zipfile
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO_ROOT / "releases" / "oc_core_1_3" / "OC_CORE_1_3_ZENODO_EN_ONLY_MANIFEST.json"
DEFAULT_STAGE_DIR = REPO_ROOT / "build_oc_core_1_3_zenodo_en_only"
ZIP_TIMESTAMP = (2026, 4, 23, 0, 0, 0)

LANGUAGE_PATH_PATTERN = re.compile(
    r"(^|[/\\_-])(ru|de)(?=\.|_|-|[/\\]|$)|(^|[/\\_-])(RU|DE)(?=\.|_|-|[/\\]|$)"
)


def repo_rel(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT).as_posix()


def assert_inside(path: Path, parent: Path, label: str) -> None:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError as exc:
        raise SystemExit(f"{label} escapes expected root: {path}") from exc


def has_language_marker(ref: str) -> bool:
    normalized = ref.replace("\\", "/")
    return LANGUAGE_PATH_PATTERN.search(normalized) is not None


def load_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"Manifest not found: {repo_rel(path) if path.is_relative_to(REPO_ROOT) else path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    files = data.get("files")
    if not isinstance(files, list) or not files:
        raise SystemExit("Manifest must contain a non-empty 'files' list.")
    return data


def validate_manifest(manifest: dict[str, Any]) -> None:
    active = manifest.get("active_language_codes")
    if active != ["EN"]:
        raise SystemExit(f"Manifest active_language_codes must be ['EN'], found: {active!r}")

    seen_stage_refs: set[str] = set()
    for index, item in enumerate(manifest["files"]):
        if not isinstance(item, dict):
            raise SystemExit(f"Manifest entry {index} is not an object.")
        source_ref = item.get("source_ref")
        stage_ref = item.get("stage_ref", source_ref)
        if not isinstance(source_ref, str) or not source_ref:
            raise SystemExit(f"Manifest entry {index} has no source_ref.")
        if not isinstance(stage_ref, str) or not stage_ref:
            raise SystemExit(f"Manifest entry {index} has no stage_ref.")
        if has_language_marker(source_ref) or has_language_marker(stage_ref):
            raise SystemExit(f"RU/DE path marker is forbidden in EN-only manifest entry: {source_ref} -> {stage_ref}")
        if stage_ref in seen_stage_refs:
            raise SystemExit(f"Duplicate staged path in manifest: {stage_ref}")
        seen_stage_refs.add(stage_ref)


def prepare_stage_dir(stage_dir: Path) -> None:
    stage_dir = stage_dir.resolve()
    assert_inside(stage_dir, REPO_ROOT, "Stage directory")
    if stage_dir.name != "build_oc_core_1_3_zenodo_en_only":
        raise SystemExit(f"Refusing to clear unexpected stage directory name: {stage_dir}")
    if stage_dir.exists():
        shutil.rmtree(stage_dir)
    stage_dir.mkdir(parents=True, exist_ok=True)


def copy_manifest_files(manifest: dict[str, Any], stage_dir: Path) -> list[str]:
    copied: list[str] = []
    for item in manifest["files"]:
        source_ref = item["source_ref"]
        stage_ref = item.get("stage_ref", source_ref)
        source_path = (REPO_ROOT / source_ref).resolve()
        stage_path = (stage_dir / stage_ref).resolve()
        assert_inside(source_path, REPO_ROOT, "Source path")
        assert_inside(stage_path, stage_dir, "Stage path")
        if not source_path.exists():
            raise SystemExit(f"Manifest source missing: {source_ref}")
        if source_path.is_dir():
            raise SystemExit(f"Manifest entries must be files, not directories: {source_ref}")
        stage_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, stage_path)
        copied.append(stage_path.relative_to(stage_dir).as_posix())
    return copied


def validate_staged_paths(stage_dir: Path) -> None:
    offenders = [
        path.relative_to(stage_dir).as_posix()
        for path in stage_dir.rglob("*")
        if path.is_file() and has_language_marker(path.relative_to(stage_dir).as_posix())
    ]
    if offenders:
        preview = "\n".join(offenders[:25])
        raise SystemExit(f"Staged output contains RU/DE-marked paths:\n{preview}")


def write_zip(stage_dir: Path, zip_path: Path) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file_path in sorted(path for path in stage_dir.rglob("*") if path.is_file()):
            rel_path = file_path.relative_to(stage_dir).as_posix()
            info = zipfile.ZipInfo(rel_path, date_time=ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, file_path.read_bytes())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage the OC Core 1.3 English-only Zenodo upload package.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--stage-dir", type=Path, default=DEFAULT_STAGE_DIR)
    parser.add_argument("--zip-path", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_path = args.manifest.resolve()
    stage_dir = args.stage_dir.resolve()
    assert_inside(manifest_path, REPO_ROOT, "Manifest path")

    manifest = load_manifest(manifest_path)
    validate_manifest(manifest)
    prepare_stage_dir(stage_dir)
    copied = copy_manifest_files(manifest, stage_dir)
    validate_staged_paths(stage_dir)
    if args.zip_path is not None:
        write_zip(stage_dir, args.zip_path.resolve())

    print(f"Staged {len(copied)} EN-only files into {repo_rel(stage_dir)}")
    print(f"Manifest: {repo_rel(manifest_path)}")
    if args.zip_path is not None:
        print(f"Archive: {args.zip_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
