from __future__ import annotations

import argparse
import copy
import json
import math
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import oc133_chemistry_pubchem_formula_batch_factory as chemistry_factory
from tools import oc133_target_projection_lock_factory as lock_factory


SCHEMA_ID = "OC133_TARGET_PROJECTION_LOCK_ORCHESTRATOR_REPORT_v1"
RELEASE_ID = lock_factory.RELEASE_ID
VERSION = lock_factory.VERSION
CAPABILITY_OWNER = lock_factory.CAPABILITY_OWNER

OUTPUT_ROOT_REL = lock_factory.OUTPUT_ROOT_REL
ORCHESTRATOR_REPORT_REL = f"{OUTPUT_ROOT_REL}/OC133_TARGET_PROJECTION_LOCK_ORCHESTRATOR_REPORT.json"
DECLARATION_ROOT_REL = f"{OUTPUT_ROOT_REL}/declarations"
SNAPSHOT_ROOT_REL = f"{OUTPUT_ROOT_REL}/snapshots"

BIOLOGY_PACKET_REL = (
    "validation/heldout/grand_science/biology/ncbi_batch/"
    "OC133_BIOLOGY_NCBI_BATCH_ACQUISITION_PACKET.json"
)
CHEMISTRY_PACKET_REL = (
    "validation/heldout/grand_science/chemistry/pubchem_formula_batch/"
    "OC133_CHEMISTRY_PUBCHEM_FORMULA_BATCH_ACQUISITION_PACKET.json"
)
OFFICIAL_SNAPSHOT_ROOT_REL = "validation/heldout/acquisition_runs/oc133_official_readonly/snapshots"

BIOLOGY_LOCK_ID = "OC133-BIOLOGY-NCBI-BATCH-TARGET-PROJECTION-LOCK"
BIOLOGY_DECLARATION_REL = f"{DECLARATION_ROOT_REL}/biology_ncbi_batch/{BIOLOGY_LOCK_ID}.json"
BIOLOGY_SNAPSHOT_REL = f"{SNAPSHOT_ROOT_REL}/biology_ncbi_batch/OC133_BIOLOGY_NCBI_BATCH_TARGET_ROWS.json"
BIOLOGY_VISIBLE_FIELDS = [
    "esearchresult.idlist",
    "esearchresult.retstart",
    "esearchresult.querytranslation",
]
BIOLOGY_TARGET_FIELDS = ["esearchresult.retmax"]
BIOLOGY_MODEL_KIND = "list_length"

CHEMISTRY_DECLARATION_DIR_REL = f"{DECLARATION_ROOT_REL}/chemistry_pubchem_formula_batch"
CHEMISTRY_SNAPSHOT_DIR_REL = f"{SNAPSHOT_ROOT_REL}/chemistry_pubchem_formula_batch"
CHEMISTRY_VISIBLE_FIELDS = ["CID", "MolecularFormula"]
CHEMISTRY_TARGET_FIELDS = ["MolecularWeight"]
CHEMISTRY_MODEL_KIND = "chemical_formula_weight"
CHEMISTRY_ATOMIC_WEIGHT_TABLE_ID = "OC133_FIXED_AVERAGE_ATOMIC_WEIGHTS_v2"
CHEMISTRY_ATOMIC_WEIGHTS = chemistry_factory.ATOMIC_WEIGHTS


def repo_root() -> Path:
    return ROOT


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8", newline="\n")


def resolve_under_root(root: Path, ref: str) -> Path:
    path = (root / ref).resolve()
    path.relative_to(root.resolve())
    return path


def sha256_object(payload: Any) -> str:
    return lock_factory.sha256_object(payload)


def sha256_file(path: Path) -> str:
    return lock_factory.sha256_bytes(path.read_bytes())


def as_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def as_int(value: Any, default: int = 0) -> int:
    try:
        if isinstance(value, bool):
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def as_float(value: Any, default: float = math.nan) -> float:
    try:
        if isinstance(value, bool):
            return default
        result = float(str(value).strip())
    except (TypeError, ValueError):
        return default
    return result if math.isfinite(result) else default


def request_id(row: dict[str, Any]) -> str:
    return as_str(row.get("acquisition_id")) or as_str(row.get("request_id")) or as_str(row.get("cid"))


def official_snapshot_ref(acquisition_id: str) -> str:
    return f"{OFFICIAL_SNAPSHOT_ROOT_REL}/{acquisition_id}.json"


def no_send_status() -> dict[str, Any]:
    return dict(lock_factory.NO_SEND_LOCKS)


def model_declaration_supported(kind: str) -> bool:
    blockers: list[str] = []
    if kind == BIOLOGY_MODEL_KIND:
        value = lock_factory.materialize_declared_prediction(
            {"kind": kind, "field": "esearchresult.idlist"},
            {"esearchresult.idlist": ["1", "2"]},
            blockers,
            "MODEL",
        )
        return value == 2 and not blockers
    if kind == CHEMISTRY_MODEL_KIND:
        value = lock_factory.materialize_declared_prediction(
            {
                "kind": kind,
                "formula_field": "MolecularFormula",
                "atomic_weight_table_id": CHEMISTRY_ATOMIC_WEIGHT_TABLE_ID,
                "atomic_weights": CHEMISTRY_ATOMIC_WEIGHTS,
            },
            {"MolecularFormula": "H2O"},
            blockers,
            "MODEL",
        )
        return isinstance(value, (int, float)) and math.isfinite(float(value)) and not blockers
    return False


def normalized_biology_rows(root: Path, packet: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    blockers: list[str] = []
    requests = packet.get("source_acquisition_requests")
    if not isinstance(requests, list):
        return rows, ["BIOLOGY_SOURCE_ACQUISITION_REQUESTS_MISSING"]
    for request in requests:
        if not isinstance(request, dict):
            continue
        acquisition_id = request_id(request)
        if not acquisition_id:
            blockers.append("BIOLOGY_ACQUISITION_ID_MISSING")
            continue
        snapshot_ref = official_snapshot_ref(acquisition_id)
        snapshot_path = resolve_under_root(root, snapshot_ref)
        if not snapshot_path.exists():
            blockers.append(f"BIOLOGY_OFFICIAL_SNAPSHOT_MISSING::{acquisition_id}")
            continue
        payload = read_json(snapshot_path)
        if not isinstance(payload, dict):
            blockers.append(f"BIOLOGY_OFFICIAL_SNAPSHOT_NOT_OBJECT::{acquisition_id}")
            continue
        esearch = payload.get("esearchresult")
        if not isinstance(esearch, dict):
            blockers.append(f"BIOLOGY_ESEARCHRESULT_MISSING::{acquisition_id}")
            continue
        normalized_esearch = copy.deepcopy(esearch)
        normalized_esearch["retmax"] = as_int(esearch.get("retmax"))
        normalized_esearch["retstart"] = as_int(esearch.get("retstart"))
        normalized_esearch["idlist"] = [as_str(item) for item in esearch.get("idlist", []) if as_str(item)]
        rows.append(
            {
                "acquisition_id": acquisition_id,
                "source_snapshot_ref": snapshot_ref,
                "source_snapshot_sha256": sha256_file(snapshot_path),
                "header": copy.deepcopy(payload.get("header", {})),
                "esearchresult": normalized_esearch,
            }
        )
    return rows, blockers


def pubchem_record(payload: Any, acquisition_id: str) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None
    properties = payload.get("PropertyTable", {}).get("Properties") if isinstance(payload.get("PropertyTable"), dict) else None
    if not isinstance(properties, list) or not properties or not isinstance(properties[0], dict):
        return None
    record = copy.deepcopy(properties[0])
    weight = as_float(record.get("MolecularWeight"))
    if math.isfinite(weight):
        record["MolecularWeight"] = weight
    record["acquisition_id"] = acquisition_id
    return record


def normalized_chemistry_rows(root: Path, packet: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    rows: dict[str, dict[str, Any]] = {}
    blockers: list[str] = []
    requests = packet.get("source_acquisition_requests")
    if not isinstance(requests, list):
        return rows, ["CHEMISTRY_SOURCE_ACQUISITION_REQUESTS_MISSING"]
    for request in requests:
        if not isinstance(request, dict):
            continue
        acquisition_id = request_id(request)
        if not acquisition_id:
            blockers.append("CHEMISTRY_ACQUISITION_ID_MISSING")
            continue
        snapshot_ref = official_snapshot_ref(acquisition_id)
        snapshot_path = resolve_under_root(root, snapshot_ref)
        if not snapshot_path.exists():
            blockers.append(f"CHEMISTRY_OFFICIAL_SNAPSHOT_MISSING::{acquisition_id}")
            continue
        record = pubchem_record(read_json(snapshot_path), acquisition_id)
        if record is None:
            blockers.append(f"CHEMISTRY_PUBCHEM_RECORD_MISSING::{acquisition_id}")
            continue
        record["source_snapshot_ref"] = snapshot_ref
        record["source_snapshot_sha256"] = sha256_file(snapshot_path)
        rows[acquisition_id] = record
    return rows, blockers


def base_declaration(
    *,
    lock_id: str,
    snapshot_ref: str,
    row_id_field: str,
    visible_fields: list[str],
    target_fields: list[str],
    model_declaration: dict[str, Any],
    comparator_declaration: dict[str, Any],
    residual_metric: str,
    uncertainty_policy: dict[str, Any],
    negative_control_id: str,
    domain: str,
    acquisition_packet_ref: str,
) -> dict[str, Any]:
    return {
        "schema_id": "OC133_TARGET_PROJECTION_LOCK_DECLARATION_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "generated_by": "tools/oc133_target_projection_lock_orchestrator.py",
        "standard_factory": "tools/oc133_target_projection_lock_factory.py",
        "domain": domain,
        "acquisition_packet_ref": acquisition_packet_ref,
        "lock_id": lock_id,
        "declared_before_scoring": True,
        "snapshot_ref": snapshot_ref,
        "snapshot_format": "json",
        "row_id_field": row_id_field,
        "visible_fields": visible_fields,
        "target_fields": target_fields,
        "row_inclusion_rule": {"include_all": True},
        "model_declaration": model_declaration,
        "comparator_declaration": comparator_declaration,
        "residual_metric": residual_metric,
        "uncertainty_policy": uncertainty_policy,
        "negative_controls": [{"control_id": negative_control_id, "kind": "locked-visible-only"}],
        "locks": no_send_status(),
        "support_policy": "This lock declaration only freezes target-blind projections; it never grants grand support.",
    }


def biology_declaration() -> dict[str, Any]:
    return base_declaration(
        lock_id=BIOLOGY_LOCK_ID,
        snapshot_ref=BIOLOGY_SNAPSHOT_REL,
        row_id_field="acquisition_id",
        visible_fields=list(BIOLOGY_VISIBLE_FIELDS),
        target_fields=list(BIOLOGY_TARGET_FIELDS),
        model_declaration={"kind": BIOLOGY_MODEL_KIND, "field": "esearchresult.idlist"},
        comparator_declaration={"kind": "constant", "value": 0},
        residual_metric="mae",
        uncertainty_policy={"max_model_residual": 0.0, "min_model_advantage": 0.0},
        negative_control_id="biology-ncbi-visible-only-null",
        domain="biology_ncbi_batch",
        acquisition_packet_ref=BIOLOGY_PACKET_REL,
    )


def chemistry_declaration(acquisition_id: str, snapshot_ref: str) -> dict[str, Any]:
    return base_declaration(
        lock_id=f"{acquisition_id}-TARGET-PROJECTION-LOCK",
        snapshot_ref=snapshot_ref,
        row_id_field="acquisition_id",
        visible_fields=list(CHEMISTRY_VISIBLE_FIELDS),
        target_fields=list(CHEMISTRY_TARGET_FIELDS),
        model_declaration={
            "kind": CHEMISTRY_MODEL_KIND,
            "formula_field": "MolecularFormula",
            "atomic_weight_table_id": CHEMISTRY_ATOMIC_WEIGHT_TABLE_ID,
            "atomic_weights": CHEMISTRY_ATOMIC_WEIGHTS,
        },
        comparator_declaration={"kind": "constant", "value": 0},
        residual_metric="mae",
        uncertainty_policy={"max_model_residual": 0.2, "min_model_advantage": 0.0},
        negative_control_id="chemistry-pubchem-formula-visible-only-null",
        domain="chemistry_pubchem_formula_batch",
        acquisition_packet_ref=CHEMISTRY_PACKET_REL,
    )


def expected_hash_declaration(declaration: dict[str, Any], record: dict[str, Any]) -> dict[str, Any]:
    updated = copy.deepcopy(declaration)
    updated.update(
        {
            "expected_declaration_sha256": sha256_object(
                lock_factory.declaration_payload_for_hash(updated)
            ),
            "expected_snapshot_sha256": record["snapshot_sha256"],
            "expected_visible_projection_sha256": record["visible_projection_sha256"],
            "expected_prediction_materialization_sha256": record["prediction_materialization_sha256"],
            "expected_target_projection_sha256": record["target_projection_sha256"],
        }
    )
    return updated


def record_status(record: dict[str, Any], *, declaration_ref: str, model_kind: str) -> dict[str, Any]:
    refs = {
        "declaration_ref": declaration_ref,
        "visible_projection_lock_ref": record["visible_lock_ref"],
        "prediction_materialization_lock_ref": record["prediction_lock_ref"],
        "target_projection_lock_ref": record["target_lock_ref"],
        "factory_report_ref": lock_factory.REPORT_JSON_REL,
    }
    hashes = {
        "declaration_sha256": record["declaration_sha256"],
        "snapshot_sha256": record["snapshot_sha256"],
        "visible_projection_lock_sha256": record["visible_projection_sha256"],
        "prediction_materialization_lock_sha256": record["prediction_materialization_sha256"],
        "target_projection_lock_sha256": record["target_projection_sha256"],
    }
    blockers = list(record.get("blockers", []))
    verified = record.get("verdict") == "LOCKED_PASS" and not blockers
    return {
        "required": True,
        "verified": verified,
        "valid": verified,
        "source_separation_derived": verified,
        "generated_by": "tools/oc133_target_projection_lock_orchestrator.py",
        "standard_factory": "tools/oc133_target_projection_lock_factory.py",
        "factory_model_kind": model_kind,
        "factory_model_kind_available": model_declaration_supported(model_kind),
        "verdict": record.get("verdict"),
        "refs": refs,
        "expected_refs": {
            "declaration_ref": refs["declaration_ref"],
            "visible_lock_ref": refs["visible_projection_lock_ref"],
            "prediction_lock_ref": refs["prediction_materialization_lock_ref"],
            "target_lock_ref": refs["target_projection_lock_ref"],
        },
        "hashes": hashes,
        "failures": blockers,
        "locks": no_send_status(),
        "support_policy": "Attached refs and hashes do not set or imply grand support.",
    }


def build_outputs(root: Path) -> dict[str, Any]:
    biology_packet = read_json(resolve_under_root(root, BIOLOGY_PACKET_REL))
    chemistry_packet = read_json(resolve_under_root(root, CHEMISTRY_PACKET_REL))

    snapshots: dict[str, Any] = {}
    declarations: dict[str, dict[str, Any]] = {}
    blockers: list[str] = []

    biology_rows, biology_blockers = normalized_biology_rows(root, biology_packet)
    blockers.extend(biology_blockers)
    snapshots[BIOLOGY_SNAPSHOT_REL] = {
        "schema_id": "OC133_TARGET_PROJECTION_NORMALIZED_SNAPSHOT_v1",
        "domain": "biology_ncbi_batch",
        "acquisition_packet_ref": BIOLOGY_PACKET_REL,
        "row_total": len(biology_rows),
        "rows": biology_rows,
        "locks": no_send_status(),
    }
    declarations[BIOLOGY_DECLARATION_REL] = biology_declaration()

    chemistry_rows, chemistry_blockers = normalized_chemistry_rows(root, chemistry_packet)
    blockers.extend(chemistry_blockers)
    for acquisition_id, row in sorted(chemistry_rows.items()):
        snapshot_ref = f"{CHEMISTRY_SNAPSHOT_DIR_REL}/{acquisition_id}.json"
        declaration_ref = f"{CHEMISTRY_DECLARATION_DIR_REL}/{acquisition_id}.json"
        snapshots[snapshot_ref] = {
            "schema_id": "OC133_TARGET_PROJECTION_NORMALIZED_SNAPSHOT_v1",
            "domain": "chemistry_pubchem_formula_batch",
            "acquisition_packet_ref": CHEMISTRY_PACKET_REL,
            "acquisition_id": acquisition_id,
            "row_total": 1,
            "rows": [row],
            "locks": no_send_status(),
        }
        declarations[declaration_ref] = chemistry_declaration(acquisition_id, snapshot_ref)

    declaration_paths = [resolve_under_root(root, ref) for ref in sorted(declarations)]
    return {
        "snapshots": snapshots,
        "declarations": declarations,
        "declaration_paths": declaration_paths,
        "build_blockers": sorted(set(blockers)),
    }


def materialize_outputs(root: Path) -> dict[str, Any]:
    outputs = build_outputs(root)
    for ref, payload in outputs["snapshots"].items():
        write_json(resolve_under_root(root, ref), payload)
    for ref, payload in outputs["declarations"].items():
        write_json(resolve_under_root(root, ref), payload)

    report, records = lock_factory.build_report_with_locks(root, outputs["declaration_paths"])
    records_by_declaration = {record["declaration_ref"]: record for record in records}
    final_declarations = {
        ref: expected_hash_declaration(payload, records_by_declaration[ref])
        for ref, payload in outputs["declarations"].items()
    }
    for ref, payload in final_declarations.items():
        write_json(resolve_under_root(root, ref), payload)

    report, records = lock_factory.build_report_with_locks(root, outputs["declaration_paths"])
    lock_factory.write_outputs(root, report, records)
    return orchestration_report(outputs, final_declarations, report, records)


def orchestration_report(
    outputs: dict[str, Any],
    declarations: dict[str, dict[str, Any]],
    factory_report: dict[str, Any],
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    records_by_declaration = {record["declaration_ref"]: record for record in records}
    biology_record = records_by_declaration[BIOLOGY_DECLARATION_REL]
    chemistry_records = {
        Path(ref).stem: record
        for ref, record in records_by_declaration.items()
        if ref.startswith(CHEMISTRY_DECLARATION_DIR_REL + "/")
    }
    chemistry_statuses = {
        acquisition_id: record_status(
            record,
            declaration_ref=record["declaration_ref"],
            model_kind=CHEMISTRY_MODEL_KIND,
        )
        for acquisition_id, record in sorted(chemistry_records.items())
    }
    report = {
        "schema_id": SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "generated_by": "tools/oc133_target_projection_lock_orchestrator.py",
        "standard_factory": "tools/oc133_target_projection_lock_factory.py",
        "output_root_ref": OUTPUT_ROOT_REL,
        "build_blockers": outputs["build_blockers"],
        "factory_report_ref": lock_factory.REPORT_JSON_REL,
        "declaration_refs": sorted(declarations),
        "snapshot_refs": sorted(outputs["snapshots"]),
        "biology": record_status(
            biology_record,
            declaration_ref=BIOLOGY_DECLARATION_REL,
            model_kind=BIOLOGY_MODEL_KIND,
        ),
        "chemistry": {
            "request_total": len(chemistry_statuses),
            "requests": chemistry_statuses,
            "verified_total": sum(1 for status in chemistry_statuses.values() if status["verified"]),
        },
        "factory_summary": {
            "record_total": factory_report.get("record_total"),
            "blocked_total": factory_report.get("blocked_total"),
            "locked_pass_total": factory_report.get("locked_pass_total"),
            "open_blocker_total": factory_report.get("open_blocker_total"),
            "blockers": factory_report.get("blockers", []),
        },
        "locks": no_send_status(),
        "support_policy": "This orchestrator writes target-projection refs and hashes only; grand support is never enabled.",
    }
    report["report_sha256"] = sha256_object({key: value for key, value in report.items() if key != "report_sha256"})
    return report


def attach_to_packets(root: Path, report: dict[str, Any]) -> None:
    biology_path = resolve_under_root(root, BIOLOGY_PACKET_REL)
    biology_packet = read_json(biology_path)
    biology_packet["target_projection_lock"] = report["biology"]
    write_json(biology_path, biology_packet)

    chemistry_path = resolve_under_root(root, CHEMISTRY_PACKET_REL)
    chemistry_packet = read_json(chemistry_path)
    request_statuses = report["chemistry"]["requests"]
    for request in chemistry_packet.get("source_acquisition_requests", []):
        if isinstance(request, dict):
            acquisition_id = request_id(request)
            if acquisition_id in request_statuses:
                request["target_projection_lock"] = request_statuses[acquisition_id]
    chemistry_packet["target_projection_lock"] = {
        "required": True,
        "valid": report["chemistry"]["verified_total"] == report["chemistry"]["request_total"]
        and report["chemistry"]["request_total"] > 0,
        "verified": report["chemistry"]["verified_total"] == report["chemistry"]["request_total"]
        and report["chemistry"]["request_total"] > 0,
        "request_total": report["chemistry"]["request_total"],
        "verified_total": report["chemistry"]["verified_total"],
        "factory_model_kind": CHEMISTRY_MODEL_KIND,
        "factory_model_kind_available": model_declaration_supported(CHEMISTRY_MODEL_KIND),
        "factory_report_ref": lock_factory.REPORT_JSON_REL,
        "orchestrator_report_ref": ORCHESTRATOR_REPORT_REL,
        "locks": no_send_status(),
        "support_policy": "Attached refs and hashes do not set or imply grand support.",
    }
    write_json(chemistry_path, chemistry_packet)


def check_stored(root: Path) -> list[str]:
    failures: list[str] = []
    expected = build_outputs(root)
    for ref, payload in expected["snapshots"].items():
        path = resolve_under_root(root, ref)
        if not path.exists():
            failures.append(f"missing::{ref}")
            continue
        if read_json(path) != payload:
            failures.append(f"mismatch::{ref}")
    for ref in expected["declarations"]:
        path = resolve_under_root(root, ref)
        if not path.exists():
            failures.append(f"missing::{ref}")
    if not failures:
        lock_failures = lock_factory.check_stored(root, expected["declaration_paths"])
        failures.extend(lock_failures)
    for ref in (ORCHESTRATOR_REPORT_REL, BIOLOGY_PACKET_REL, CHEMISTRY_PACKET_REL):
        if not resolve_under_root(root, ref).exists():
            failures.append(f"missing::{ref}")
    return failures


def run(root: Path, *, write: bool, attach: bool) -> dict[str, Any]:
    report = materialize_outputs(root) if write else orchestration_report_from_existing(root)
    if write:
        write_json(resolve_under_root(root, ORCHESTRATOR_REPORT_REL), report)
    if attach:
        attach_to_packets(root, report)
    return report


def orchestration_report_from_existing(root: Path) -> dict[str, Any]:
    outputs = build_outputs(root)
    report, records = lock_factory.build_report_with_locks(root, outputs["declaration_paths"])
    declarations = {
        ref: read_json(resolve_under_root(root, ref)) if resolve_under_root(root, ref).exists() else payload
        for ref, payload in outputs["declarations"].items()
    }
    return orchestration_report(outputs, declarations, report, records)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate and attach no-send target-projection locks from OC133 acquisition packets."
    )
    parser.add_argument("--root", default=str(repo_root()), help="repository root")
    parser.add_argument("--write", action="store_true", help="write declarations, lock artifacts, and report")
    parser.add_argument("--attach", action="store_true", help="attach target_projection_lock refs and hashes to packets")
    parser.add_argument("--check", action="store_true", help="check stored orchestrator and lock artifacts")
    parser.add_argument("--allow-blocked-exit-zero", action="store_true", help="return zero while factory kinds are pending")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    if args.check:
        failures = check_stored(root)
        if failures:
            for failure in failures:
                print(f"ERROR: {failure}")
            return 1
        print(json.dumps({"status": "ok", "checked": [ORCHESTRATOR_REPORT_REL, lock_factory.REPORT_JSON_REL]}, indent=2))
        return 0
    report = run(root, write=args.write, attach=args.attach)
    print(json.dumps(report, ensure_ascii=True, indent=2))
    blocked = bool(report["build_blockers"]) or int(report["factory_summary"]["open_blocker_total"] or 0) > 0
    if blocked and not args.allow_blocked_exit_zero:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
