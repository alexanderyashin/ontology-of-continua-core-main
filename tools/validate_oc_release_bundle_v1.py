from __future__ import annotations

from build_oc_core_1_3_1_independent_release_v14 import (
    MANDATORY_MANUSCRIPT_CLASSES,
    materialize_oc_core_1_3_1_independent_release_v14,
)


if __name__ == "__main__":
    payload = materialize_oc_core_1_3_1_independent_release_v14(run_id="validate_oc_release_bundle_v1")
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
        if str(row.get("artifact_substance_class", "")).strip() == "SUMMARY_ONLY_WRAPPER":
            problems.append(f"{row.get('artifact_id')}: summary-only wrapper")
        if not row.get("source_corpus_root"):
            problems.append(f"{row.get('artifact_id')}: missing source_corpus_root")
        if not (row.get("source_section_refs") or row.get("source_appendix_refs")):
            problems.append(f"{row.get('artifact_id')}: missing source bindings")
        if not row.get("source_tex_entrypoint"):
            problems.append(f"{row.get('artifact_id')}: missing source_tex_entrypoint")

    if problems:
        for line in problems:
            print(f"FAIL {line}")
        raise SystemExit(1)

    print("PASS")
    raise SystemExit(0)
