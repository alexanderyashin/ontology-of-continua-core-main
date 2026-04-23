from __future__ import annotations

import argparse
import json
import shutil
import zipfile
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
EDITORIAL_DIR = REPO_ROOT / "releases" / "oc_core_1_3" / "editorial"
DEFAULT_ARTIFACT_MAP = EDITORIAL_DIR / "OC_PUBLIC_RELEASE_ARTIFACT_MAP_latest.json"
DEFAULT_STAGE_DIR = REPO_ROOT / "build_oc_public_release_archive"
ZIP_TIMESTAMP = (2026, 4, 23, 0, 0, 0)


def repo_rel(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()


def assert_inside(path: Path, parent: Path, label: str) -> None:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError as exc:
        raise SystemExit(f"{label} escapes expected root: {path}") from exc


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"Artifact map not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def prepare_stage_dir(stage_dir: Path) -> None:
    assert_inside(stage_dir, REPO_ROOT, "Stage directory")
    if stage_dir.exists():
        shutil.rmtree(stage_dir)
    stage_dir.mkdir(parents=True, exist_ok=True)


def iter_member_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return sorted(file_path for file_path in path.rglob("*") if file_path.is_file())


def copy_member(member_ref: str, stage_dir: Path) -> list[str]:
    source_path = (REPO_ROOT / member_ref).resolve()
    assert_inside(source_path, REPO_ROOT, "Source path")
    if not source_path.exists():
        raise SystemExit(f"Artifact-map member missing: {member_ref}")
    copied: list[str] = []
    for file_path in iter_member_files(source_path):
        rel_path = file_path.relative_to(REPO_ROOT).as_posix()
        target_path = (stage_dir / rel_path).resolve()
        assert_inside(target_path, stage_dir, "Stage target")
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, target_path)
        copied.append(rel_path)
    return copied


def write_zip(stage_dir: Path, zip_path: Path) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file_path in sorted(path for path in stage_dir.rglob("*") if path.is_file()):
            rel_path = file_path.relative_to(stage_dir).as_posix()
            info = zipfile.ZipInfo(rel_path, date_time=ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, file_path.read_bytes())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage the explicit OC public reproducibility archive.")
    parser.add_argument("--artifact-map", type=Path, default=DEFAULT_ARTIFACT_MAP)
    parser.add_argument("--stage-dir", type=Path, default=DEFAULT_STAGE_DIR)
    parser.add_argument("--zip-path", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    artifact_map = load_json(args.artifact_map.resolve())
    members = artifact_map.get("reproducibility_archive_members")
    if not isinstance(members, list) or not members:
        raise SystemExit("Artifact map must contain a non-empty reproducibility_archive_members list.")

    stage_dir = args.stage_dir.resolve()
    prepare_stage_dir(stage_dir)

    copied: list[str] = []
    for member_ref in members:
        if not isinstance(member_ref, str) or not member_ref:
            raise SystemExit(f"Invalid reproducibility-archive member: {member_ref!r}")
        copied.extend(copy_member(member_ref, stage_dir))

    if args.zip_path is not None:
        write_zip(stage_dir, args.zip_path.resolve())

    print(f"Staged {len(copied)} public release files into {repo_rel(stage_dir)}")
    if args.zip_path is not None:
        print(f"Archive: {args.zip_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
