from __future__ import annotations

import argparse
import json
from pathlib import Path

from build_oc_core_1_3_1_independent_release_v14 import (
    MANDATORY_MANUSCRIPT_CLASSES,
    PUBLIC_ARTIFACT_INVENTORY_PATH,
    PUBLIC_CONTROL_PLANE_PATH,
    materialize_oc_core_1_3_1_independent_release_v14,
)


REPO_ROOT = Path(__file__).resolve().parent.parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate the OC Core 1.3.1 release bundle.")
    parser.add_argument(
        "--check-existing",
        action="store_true",
        help="Validate the already-materialized release artifacts without rewriting generated files.",
    )
    return parser.parse_args()


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    return payload if isinstance(payload, dict) else {}


def _repo_path(ref: str) -> Path:
    path = Path(str(ref))
    return path if path.is_absolute() else REPO_ROOT / path


def _existing_payload() -> dict:
    return {
        "control_plane": _read_json(PUBLIC_CONTROL_PLANE_PATH),
        "artifact_inventory": _read_json(PUBLIC_ARTIFACT_INVENTORY_PATH),
    }


def main() -> int:
    args = parse_args()
    payload = (
        _existing_payload()
        if args.check_existing
        else materialize_oc_core_1_3_1_independent_release_v14(run_id="validate_oc_release_bundle_v1")
    )
    summary = payload["control_plane"]["summary"]
    inventory_rows = payload["artifact_inventory"].get("rows") or []

    problems: list[str] = []
    if summary.get("independent_audit_status") != "PASS":
        problems.append(f"independent_audit_status={summary.get('independent_audit_status')}")
    if summary.get("reader_route_status") != "PASS":
        problems.append(f"reader_route_status={summary.get('reader_route_status')}")

    manuscript_rows = [
        row for row in inventory_rows if str(row.get("artifact_class", "")).strip() in MANDATORY_MANUSCRIPT_CLASSES
    ]
    if len(manuscript_rows) != len(MANDATORY_MANUSCRIPT_CLASSES):
        problems.append(
            f"mandatory_manuscript_row_total={len(manuscript_rows)} expected={len(MANDATORY_MANUSCRIPT_CLASSES)}"
        )
    for row in manuscript_rows:
        if str(row.get("status", "")).strip() != "ASSEMBLED":
            problems.append(f"{row.get('artifact_id')}: status={row.get('status')}")
        if str(row.get("artifact_substance_class", "")).strip() == "SUMMARY_ONLY_WRAPPER":
            problems.append(f"{row.get('artifact_id')}: summary-only wrapper")
        if not row.get("source_corpus_root"):
            problems.append(f"{row.get('artifact_id')}: missing source_corpus_root")
        if not (row.get("source_section_refs") or row.get("source_appendix_refs")):
            problems.append(f"{row.get('artifact_id')}: missing source bindings")
        if not row.get("source_tex_entrypoint"):
            problems.append(f"{row.get('artifact_id')}: missing source_tex_entrypoint")

    for row in [row for row in inventory_rows if bool(row.get("mandatory"))]:
        artifact_ref = str(row.get("artifact_ref", "")).strip()
        if str(row.get("status", "")).strip() != "ASSEMBLED":
            problems.append(f"{row.get('artifact_id')}: mandatory status={row.get('status')}")
        if not artifact_ref:
            problems.append(f"{row.get('artifact_id')}: missing artifact_ref")
        elif not _repo_path(artifact_ref).exists():
            problems.append(f"{row.get('artifact_id')}: missing artifact file {artifact_ref}")

    if problems:
        for line in problems:
            print(f"FAIL {line}")
        return 1

    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
