from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
PACK_DIR = REPO_ROOT / "releases" / "oc_core_1_3_1" / "editorial" / "corporate_projections"
ATLAS_PATH = PACK_DIR / "OC_CORE_1_3_1_CORPORATE_PROJECTION_ATLAS_latest.json"
CONTROL_PLANE_PATH = REPO_ROOT / "releases" / "oc_core_1_3_1" / "editorial" / "OC_CORE_1_3_1_RELEASE_CONTROL_PLANE_latest.json"
READY_BOARD_PATH = REPO_ROOT / "releases" / "oc_core_1_3_1" / "editorial" / "OC_CORE_1_3_1_RELEASE_READY_BOARD_latest.json"
PUBLIC_RELEASE_CERT_PATH = REPO_ROOT / "releases" / "oc_core_1_3_1" / "editorial" / "OC_1_3_1_PUBLIC_RELEASE_EXECUTION_CERT_latest.json"
REPAIR_AUDIT_PATH = REPO_ROOT / "releases" / "oc_core_1_3_1" / "editorial" / "OC_CORE_1_3_1_PUBLICATION_REPAIR_AUDIT_latest.json"

EXPECTED_CLASSES = {
    "INSTRUMENT",
    "TOOLING",
    "PRODUCT",
    "BUSINESS",
    "PUBLICATION",
}
ALLOWED_USABLE_NOW_SUPPORT_CLASSES = {
    "FORMALLY_PROVED",
    "THEOREM_NATIVE_HELD_OUT_VALIDATED",
    "OPERATIONALLY_SUPPORTED_WITHIN_BOUNDS",
}
REQUIRED_ROW_FIELDS = {
    "row_id",
    "projection_class",
    "title",
    "support_class",
    "usable_now",
    "source_refs",
    "inputs",
    "outputs",
    "non_claims",
    "risks",
    "validation_gate",
    "next_artifact",
}
REQUIRED_ARRAY_FIELDS = {
    "source_refs",
    "inputs",
    "outputs",
    "non_claims",
    "risks",
}


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    return payload if isinstance(payload, dict) else {}


def _repo_path(ref: str) -> Path:
    path = Path(ref)
    return path if path.is_absolute() else REPO_ROOT / path


def _source_ref_exists(ref: str) -> bool:
    if ref.startswith("http://") or ref.startswith("https://"):
        return True
    return _repo_path(ref).exists()


def _publication_row_has_release_anchor(row: dict[str, Any]) -> bool:
    refs = [str(ref) for ref in row.get("source_refs", [])]
    for ref in refs:
        if ref.startswith("releases/oc_core_1_3_1/manuscripts/") and ref.endswith(".pdf"):
            return True
        if ref.endswith("OC_CORE_1_3_1_PUBLICATION_REPAIR_AUDIT_latest.json"):
            return True
        if ref.endswith("OC_1_3_1_PUBLIC_RELEASE_EXECUTION_CERT_latest.json"):
            return True
    return False


def validate_atlas(atlas: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if atlas.get("schema_id") != "OC_CORE_1_3_1_CORPORATE_PROJECTION_ATLAS_v1":
        errors.append("atlas schema_id mismatch")
    if atlas.get("status") != "PASS":
        errors.append(f"atlas status={atlas.get('status')}")
    if atlas.get("publication_mode") != "TRACKED_SUPPLEMENTARY_GOVERNANCE_NOT_RELEASE_ASSET":
        errors.append("atlas publication_mode must mark this pack as non-release-asset governance")

    declared_classes = set(atlas.get("projection_classes", []) or [])
    if declared_classes != EXPECTED_CLASSES:
        errors.append(f"projection_classes={sorted(declared_classes)} expected={sorted(EXPECTED_CLASSES)}")

    rows = atlas.get("rows", [])
    if not isinstance(rows, list) or not rows:
        return errors + ["atlas rows are missing"]
    row_classes = {str(row.get("projection_class")) for row in rows if isinstance(row, dict)}
    if row_classes != EXPECTED_CLASSES:
        errors.append(f"row projection classes={sorted(row_classes)} expected={sorted(EXPECTED_CLASSES)}")

    row_ids: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"rows[{index}] is not an object")
            continue
        row_id = str(row.get("row_id", f"rows[{index}]"))
        if row_id in row_ids:
            errors.append(f"{row_id}: duplicate row_id")
        row_ids.add(row_id)
        missing = sorted(field for field in REQUIRED_ROW_FIELDS if field not in row)
        if missing:
            errors.append(f"{row_id}: missing fields {missing}")
        for field in REQUIRED_ARRAY_FIELDS:
            value = row.get(field)
            if not isinstance(value, list) or not value or any(not str(item).strip() for item in value):
                errors.append(f"{row_id}: {field} must be a non-empty string list")
        if not str(row.get("validation_gate", "")).strip():
            errors.append(f"{row_id}: missing validation_gate")
        if not str(row.get("next_artifact", "")).strip():
            errors.append(f"{row_id}: missing next_artifact")
        support_class = str(row.get("support_class", ""))
        if bool(row.get("usable_now")) and support_class not in ALLOWED_USABLE_NOW_SUPPORT_CLASSES:
            errors.append(f"{row_id}: usable-now row has illegal support_class={support_class}")
        if row.get("projection_class") in {"PRODUCT", "BUSINESS"} and support_class not in ALLOWED_USABLE_NOW_SUPPORT_CLASSES:
            errors.append(f"{row_id}: product/business row outruns bounded support classes")
        if row.get("projection_class") == "PUBLICATION" and not _publication_row_has_release_anchor(row):
            errors.append(f"{row_id}: publication row must point to a 1.3.1 PDF or release audit")
        if bool(row.get("usable_now")):
            for ref in row.get("source_refs", []):
                if not _source_ref_exists(str(ref)):
                    errors.append(f"{row_id}: missing source_ref {ref}")

    summary = atlas.get("summary", {}) if isinstance(atlas.get("summary"), dict) else {}
    if summary.get("projection_class_total") != len(EXPECTED_CLASSES):
        errors.append("summary projection_class_total mismatch")
    if summary.get("row_total") != len(rows):
        errors.append("summary row_total mismatch")
    for projection_class in EXPECTED_CLASSES:
        expected_count = sum(1 for row in rows if isinstance(row, dict) and row.get("projection_class") == projection_class)
        summary_key = projection_class.lower() + "_row_total"
        if summary.get(summary_key) != expected_count:
            errors.append(f"summary {summary_key}={summary.get(summary_key)} expected={expected_count}")
    return errors


def validate_publication_lineage(atlas: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    cert = _read_json(PUBLIC_RELEASE_CERT_PATH)
    repair = _read_json(REPAIR_AUDIT_PATH)
    canonical = atlas.get("canonical_publication", {}) if isinstance(atlas.get("canonical_publication"), dict) else {}
    repair_canonical = repair.get("canonical_zenodo_record", {}) if isinstance(repair.get("canonical_zenodo_record"), dict) else {}
    repair_superseded = repair.get("superseded_standalone_zenodo_record", {}) if isinstance(repair.get("superseded_standalone_zenodo_record"), dict) else {}

    if canonical.get("zenodo_doi") != "10.5281/zenodo.19741958":
        errors.append("canonical Zenodo DOI mismatch in corporate atlas")
    if canonical.get("zenodo_conceptdoi") != "10.5281/zenodo.17899134":
        errors.append("canonical Zenodo concept DOI mismatch in corporate atlas")
    if canonical.get("superseded_standalone_zenodo_doi") != "10.5281/zenodo.19741582":
        errors.append("superseded standalone DOI mismatch in corporate atlas")
    if cert.get("canonical_zenodo_doi") != canonical.get("zenodo_doi"):
        errors.append("public execution cert canonical DOI does not match corporate atlas")
    if cert.get("canonical_zenodo_conceptdoi") != canonical.get("zenodo_conceptdoi"):
        errors.append("public execution cert concept DOI does not match corporate atlas")
    if cert.get("superseded_standalone_zenodo_doi") != canonical.get("superseded_standalone_zenodo_doi"):
        errors.append("public execution cert superseded DOI does not match corporate atlas")
    if repair_canonical.get("doi") != canonical.get("zenodo_doi"):
        errors.append("publication repair audit canonical DOI does not match corporate atlas")
    if repair_canonical.get("conceptdoi") != canonical.get("zenodo_conceptdoi"):
        errors.append("publication repair audit concept DOI does not match corporate atlas")
    if repair_superseded.get("doi") != canonical.get("superseded_standalone_zenodo_doi"):
        errors.append("publication repair audit superseded DOI does not match corporate atlas")
    return errors


def validate_editorial_refs() -> list[str]:
    errors: list[str] = []
    control = _read_json(CONTROL_PLANE_PATH)
    ready = _read_json(READY_BOARD_PATH)
    refs = control.get("refs", {}) if isinstance(control.get("refs"), dict) else {}
    expected_atlas_ref = "releases/oc_core_1_3_1/editorial/corporate_projections/OC_CORE_1_3_1_CORPORATE_PROJECTION_ATLAS_latest.json"
    if refs.get("corporate_projection_atlas_ref") != expected_atlas_ref:
        errors.append("release control plane missing corporate_projection_atlas_ref")
    if control.get("summary", {}).get("corporate_projection_pack_status") != "PASS":
        errors.append("release control plane summary missing corporate projection PASS status")
    if ready.get("summary", {}).get("corporate_projection_pack_status") != "PASS":
        errors.append("release ready board summary missing corporate projection PASS status")
    rows = ready.get("rows", []) if isinstance(ready.get("rows"), list) else []
    if not any(row.get("gate_id") == "CORPORATE_PROJECTION_PACK" and row.get("status") == "PASS" for row in rows if isinstance(row, dict)):
        errors.append("release ready board missing CORPORATE_PROJECTION_PACK PASS row")
    return errors


def main() -> int:
    atlas = _read_json(ATLAS_PATH)
    errors = []
    if not atlas:
        errors.append(f"missing corporate projection atlas: {ATLAS_PATH}")
    else:
        errors.extend(validate_atlas(atlas))
        errors.extend(validate_publication_lineage(atlas))
    errors.extend(validate_editorial_refs())

    if errors:
        for error in errors:
            print(f"FAIL {error}")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
