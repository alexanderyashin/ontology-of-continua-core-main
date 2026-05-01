from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlencode


RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
GENERATED_ON = "2026-05-01"
SCHEMA_ID = "OC133_ENGINEERING_MODERN_SCIENCE_COVERAGE_WORK_ORDERS_v1"
CAPABILITY_OWNER = "Logion Engineering Evidence / Applied Measurement Sources"

SCRIPT_REL = (
    "validation/heldout/grand_science/engineering/coverage_work_orders/"
    "oc133_engineering_modern_science_coverage_work_orders.py"
)
OUTPUT_REL = (
    "validation/heldout/grand_science/engineering/coverage_work_orders/"
    "OC133_ENGINEERING_MODERN_SCIENCE_COVERAGE_WORK_ORDERS.json"
)
COVERAGE_REGISTER_REL = "comparators/modern_science/OC133_MODERN_SCIENCE_COVERAGE_REGISTER.json"
MODERN_WORK_ORDERS_REL = "benchmarks/modern_science/OC133_MODERN_SCIENCE_COVERAGE_WORK_ORDERS.json"

NO_SEND_LOCKS = {
    "no_send": True,
    "public_release_action_allowed": False,
    "publish_allowed": False,
    "push_allowed": False,
    "registry_write_allowed": False,
    "journal_submission_allowed": False,
    "email_allowed": False,
    "doi_registration_allowed": False,
    "coverage_closure_allowed": False,
    "broad_modern_science_superiority_allowed": False,
}

SPEC_REQUIRED_FIELDS = (
    "official_source",
    "target_variable",
    "target_hidden_split",
    "formula_or_model",
    "preregistered_comparator",
    "uncertainty_and_residual",
    "negative_control",
    "falsifier",
    "N",
    "replay_command",
    "fail_closed_current_evidence",
)

COMMON_CLOSURE_PREDICATES = [
    "STRICT_PACK_SCHEMA_PASS",
    "OFFICIAL_SOURCE_SNAPSHOT_HASH_BOUND",
    "TARGET_VARIABLE_EXACTLY_DECLARED",
    "TARGET_HIDDEN_OR_PROSPECTIVE_LOCK_DECLARED",
    "FORMULA_OR_MODEL_PREREGISTERED",
    "COMPARATOR_PREREGISTERED_AND_TARGET_SEPARATED",
    "UNCERTAINTY_AND_RESIDUAL_DECLARED",
    "NEGATIVE_CONTROL_REJECTION_REQUIRED",
    "FALSIFIER_PREDICATES_EXECUTABLE",
    "INDEPENDENT_REPLAY_PASS",
    "COVERAGE_REGISTER_GAP_CLOSED_BY_REVIEW",
    "NO_BROAD_SUPERIORITY_CERTIFICATION",
]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[5]


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def sha256_object(payload: Any) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8", newline="\n")


def no_send() -> dict[str, Any]:
    return dict(NO_SEND_LOCKS)


def with_hash(row: dict[str, Any]) -> dict[str, Any]:
    row = dict(row)
    row["row_sha256"] = sha256_object(row)
    return row


def fail_closed_evidence(reason: str) -> dict[str, Any]:
    return {
        "current_status": "OPEN_FAIL_CLOSED_NO_EXECUTABLE_EVIDENCE",
        "executable_evidence_exists": False,
        "strict_evidence_pack_ref": None,
        "source_snapshot_hash_bound": False,
        "source_snapshot_ref": None,
        "source_snapshot_sha256": None,
        "reason": reason,
        "coverage_closure_allowed": False,
        "broad_modern_science_superiority_allowed": False,
        "scientific_pass": False,
    }


def jarvis_url() -> str:
    return "https://jarvis.nist.gov/optimade/jarvisdft/v1/structures/?" + urlencode(
        {"filter": "nelements>=1"}
    )


def nist_fluid_url() -> str:
    return "https://webbook.nist.gov/cgi/fluid.cgi?" + urlencode(
        {
            "Action": "Data",
            "Wide": "on",
            "ID": "C7732185",
            "Type": "IsoBar",
            "Digits": "5",
            "P": "101.325",
            "THigh": "373.15",
            "TLow": "273.15",
            "TInc": "5",
            "RefState": "DEF",
            "TUnit": "K",
            "PUnit": "kPa",
            "DUnit": "mol/l",
            "HUnit": "kJ/mol",
            "WUnit": "m/s",
            "VisUnit": "uPa*s",
            "STUnit": "N/m",
        }
    )


def build_work_orders() -> list[dict[str, Any]]:
    rows = [
        {
            "work_order_id": "MS-COV-WO-022",
            "domain_class_id": "engineering_materials_sciences",
            "phenomenon_class_id": "materials_property_and_failure_prediction",
            "phenomenon_label": "materials property and failure prediction",
            "lane_status": "OPEN_FAIL_CLOSED_NO_EXECUTABLE_EVIDENCE",
            "coverage_closure_allowed": False,
            "support_allowed_for_broad_coverage": False,
            "executable_spec": {
                "official_source": {
                    "source_id": "engineering_nist_jarvis_materials_properties_v1",
                    "source_name": "NIST-JARVIS JARVIS-DFT OPTIMADE structures and materials-property records",
                    "source_authority": "National Institute of Standards and Technology",
                    "official_documentation_url": "https://jarvis.nist.gov/optimade/jarvisdft/",
                    "official_endpoint_url": jarvis_url(),
                    "required_local_snapshot_refs": [
                        "validation/heldout/grand_science/engineering/coverage_work_orders/raw/nist_jarvis_nelements_ge_1_page1.json"
                    ],
                    "snapshot_status": "NOT_ACQUIRED_FOR_THIS_COVERAGE_CLASS",
                },
                "target_variable": {
                    "name": "elastic_stiffness_and_bandgap_material_property",
                    "unit": "GPa for moduli; eV for bandgap",
                    "target_fields": [
                        "data[].attributes._jarvis_bulk_modulus_kv",
                        "data[].attributes._jarvis_shear_modulus_gv",
                        "data[].attributes._jarvis_optb88vdw_bandgap",
                    ],
                    "target_field": "JARVIS_DFT[structure_id].attributes._jarvis_bulk_modulus_kv",
                },
                "target_hidden_split": {
                    "mode": "target_blind_material_property_holdout",
                    "visible_inputs": [
                        "chemical_formula_reduced",
                        "elements",
                        "nelements",
                        "space group",
                        "density",
                        "dimensionality",
                    ],
                    "hidden_target_fields": [
                        "_jarvis_bulk_modulus_kv",
                        "_jarvis_shear_modulus_gv",
                        "_jarvis_optb88vdw_bandgap",
                    ],
                    "split_rule": "Lock the JARVIS response; hide target property fields for every other accepted structure until the preregistered descriptor model is materialized.",
                    "target_hidden_until_scoring": True,
                    "target_values_used_for_selection": False,
                },
                "formula_or_model": {
                    "model_id": "JARVIS-COMPOSITION-STRUCTURE-DESCRIPTOR-RIDGE",
                    "rule": "Predict hidden property = fixed linear ridge map of visible composition counts, element summary descriptors, density, dimensionality, and space-group number.",
                    "required_inputs": [
                        "formula-derived element fractions",
                        "density",
                        "dimensionality",
                        "space-group number",
                    ],
                    "target_values_may_be_used_for_model_design": False,
                },
                "preregistered_comparator": {
                    "comparator_id": "JARVIS-COMPOSITION-FAMILY-MEDIAN",
                    "prediction_rule": "Predict each hidden property using the visible-row median for the same element-count family; fall back to global visible median.",
                    "pre_registered": True,
                    "target_values_used_for_baseline_design": False,
                },
                "uncertainty_and_residual": {
                    "uncertainty_method": "visible-row bootstrap interval declared before hidden property fields are unsealed",
                    "residual_metric": "absolute residual per material/property plus aggregate MAE over hidden targets",
                    "superiority_rule": "descriptor model MAE plus bootstrap upper margin must be lower than the composition-family median comparator",
                },
                "negative_control": {
                    "control_id": "JARVIS-ELEMENT-LABEL-SHUFFLE",
                    "description": "Shuffle element labels among hidden rows after source lock.",
                    "rejection_predicate": "element-label shuffle changes row hashes and loses material-property residual superiority",
                },
                "falsifier": {
                    "falsifier_id": "JARVIS-MATERIALS-FAIL-CLOSED-FALSIFIER",
                    "triggers": [
                        "hidden JARVIS target property appears in visible descriptors",
                        "official JARVIS snapshot hash is missing or changes",
                        "composition-family median comparator ties or beats the model within uncertainty",
                        "fewer than 20 material/property targets are scored",
                    ],
                },
                "N": {
                    "minimum_n": 20,
                    "planned_source_rows": 20,
                    "planned_hidden_target_rows": 20,
                    "unit": "material/property targets",
                },
                "replay_command": {
                    "commands": [
                        "acquire the NIST-JARVIS OPTIMADE endpoint listed in this spec and hash response bytes",
                        "python validation/heldout/grand_science/engineering/coverage_work_orders/oc133_engineering_modern_science_coverage_work_orders.py --check",
                    ],
                    "acceptance_predicates": COMMON_CLOSURE_PREDICATES,
                },
                "fail_closed_current_evidence": fail_closed_evidence(
                    "JARVIS source snapshot, target-hidden scorer, negative-control replay, and strict evidence pack are not yet bound."
                ),
            },
            "no_send_locks": no_send(),
        },
        {
            "work_order_id": "MS-COV-WO-023",
            "domain_class_id": "engineering_materials_sciences",
            "phenomenon_class_id": "control_systems_and_signal_measurement",
            "phenomenon_label": "control systems and signal measurement",
            "lane_status": "OPEN_FAIL_CLOSED_NO_EXECUTABLE_EVIDENCE",
            "coverage_closure_allowed": False,
            "support_allowed_for_broad_coverage": False,
            "executable_spec": {
                "official_source": {
                    "source_id": "engineering_nist_its90_type_k_thermocouple_v1",
                    "source_name": "NIST SRD 60 ITS-90 Type K thermocouple reference functions and coefficients",
                    "source_authority": "National Institute of Standards and Technology",
                    "official_documentation_url": "https://www.nist.gov/publications/nist-60-nist-its-90-thermocouple-database",
                    "official_endpoint_url": "https://srdata.nist.gov/its90/type_k/kcoefficients.html",
                    "required_local_snapshot_refs": [
                        "validation/heldout/grand_science/engineering/coverage_work_orders/raw/nist_its90_type_k_coefficients.html"
                    ],
                    "snapshot_status": "NOT_ACQUIRED_FOR_THIS_COVERAGE_CLASS",
                },
                "target_variable": {
                    "name": "type_k_thermocouple_emf_signal",
                    "unit": "millivolts",
                    "target_fields": ["type_k_emf_mV_at_locked_temperature_C"],
                    "target_field": "NIST_ITS90_TYPE_K[temperature_C].emf_mV",
                },
                "target_hidden_split": {
                    "mode": "target_blind_standards_table_holdout",
                    "visible_inputs": ["temperature_C", "thermocouple type", "published valid temperature interval"],
                    "hidden_target_fields": ["official Type K EMF mV table/function values for locked temperatures"],
                    "split_rule": "Lock NIST SRD 60 source bytes; materialize predictions at 20 preregistered temperatures before official EMF values are unsealed.",
                    "target_hidden_until_scoring": True,
                    "target_values_used_for_selection": False,
                },
                "formula_or_model": {
                    "model_id": "ITS90-TYPE-K-PUBLISHED-POLYNOMIAL",
                    "rule": "Use the preregistered ITS-90 Type K reference polynomial over the locked temperature interval to predict EMF in mV.",
                    "required_inputs": ["temperature_C", "type K interval", "published coefficient block"],
                    "target_values_may_be_used_for_model_design": False,
                },
                "preregistered_comparator": {
                    "comparator_id": "TYPE-K-LINEAR-SEEBECK-APPROXIMATION",
                    "prediction_rule": "Predict EMF using a single fixed 41 microvolt/C Seebeck slope with zero intercept over the same temperatures.",
                    "pre_registered": True,
                    "target_values_used_for_baseline_design": False,
                },
                "uncertainty_and_residual": {
                    "uncertainty_method": "NIST table precision plus a fixed preregistered rounding tolerance; no post-target tolerance tuning",
                    "residual_metric": "absolute mV residual per locked temperature; aggregate max absolute error and MAE",
                    "superiority_rule": "published-polynomial residual must be below tolerance and materially lower than the linear Seebeck comparator",
                },
                "negative_control": {
                    "control_id": "TYPE-K-TEMPERATURE-SIGN-FLIP",
                    "description": "Flip the sign of locked Celsius temperatures after source lock.",
                    "rejection_predicate": "temperature sign flip changes target row hashes and violates the residual tolerance policy",
                },
                "falsifier": {
                    "falsifier_id": "NIST-ITS90-SIGNAL-MEASUREMENT-FAIL-CLOSED-FALSIFIER",
                    "triggers": [
                        "official EMF target values are read before prediction materialization",
                        "NIST SRD 60 source snapshot hash is missing or changes",
                        "linear comparator ties or beats the polynomial model within uncertainty",
                        "fewer than 20 locked temperature targets are scored",
                    ],
                },
                "N": {
                    "minimum_n": 20,
                    "planned_source_rows": 20,
                    "planned_hidden_target_rows": 20,
                    "unit": "locked thermocouple temperature points",
                },
                "replay_command": {
                    "commands": [
                        "acquire the NIST SRD 60 Type K endpoint listed in this spec and hash response bytes",
                        "python validation/heldout/grand_science/engineering/coverage_work_orders/oc133_engineering_modern_science_coverage_work_orders.py --check",
                    ],
                    "acceptance_predicates": COMMON_CLOSURE_PREDICATES,
                },
                "fail_closed_current_evidence": fail_closed_evidence(
                    "NIST SRD 60 source snapshot, target-hidden scorer, negative-control replay, and strict evidence pack are not yet bound."
                ),
            },
            "no_send_locks": no_send(),
        },
        {
            "work_order_id": "MS-COV-WO-024",
            "domain_class_id": "engineering_materials_sciences",
            "phenomenon_class_id": "energy_transport_and_manufacturing_processes",
            "phenomenon_label": "energy transport and manufacturing processes",
            "lane_status": "OPEN_FAIL_CLOSED_NO_EXECUTABLE_EVIDENCE",
            "coverage_closure_allowed": False,
            "support_allowed_for_broad_coverage": False,
            "executable_spec": {
                "official_source": {
                    "source_id": "engineering_nist_webbook_water_isobaric_transport_v1",
                    "source_name": "NIST Chemistry WebBook SRD 69 thermophysical fluid-property table for water",
                    "source_authority": "National Institute of Standards and Technology",
                    "official_documentation_url": "https://webbook.nist.gov/chemistry/fluid/",
                    "official_endpoint_url": nist_fluid_url(),
                    "required_local_snapshot_refs": [
                        "validation/heldout/grand_science/engineering/coverage_work_orders/raw/nist_webbook_water_isobaric_101325pa_273_373k.tsv"
                    ],
                    "snapshot_status": "NOT_ACQUIRED_FOR_THIS_COVERAGE_CLASS",
                },
                "target_variable": {
                    "name": "water_thermal_transport_properties_at_one_atmosphere",
                    "unit": "density mol/l, viscosity uPa*s, thermal conductivity W/m*K",
                    "target_fields": ["Density (mol/l)", "Viscosity (uPa*s)", "Therm. Cond. (W/m*K)"],
                    "target_field": "NIST_WEBBOOK_WATER[temperature_K, pressure_kPa=101.325].Therm. Cond. (W/m*K)",
                },
                "target_hidden_split": {
                    "mode": "target_blind_temperature_grid_holdout",
                    "visible_inputs": ["temperature_K", "pressure_kPa", "phase label", "visible neighboring grid rows"],
                    "hidden_target_fields": ["density", "viscosity", "thermal conductivity"],
                    "split_rule": "Lock the NIST WebBook TSV response; hide every other temperature-grid row until the preregistered transport interpolation model is materialized.",
                    "target_hidden_until_scoring": True,
                    "target_values_used_for_selection": False,
                },
                "formula_or_model": {
                    "model_id": "NIST-WATER-TRANSPORT-LOG-LINEAR-TEMPERATURE-INTERPOLATOR",
                    "rule": "Predict hidden transport property by log-linear interpolation in temperature using only visible neighboring grid rows within the same phase.",
                    "required_inputs": ["temperature_K", "pressure_kPa", "phase", "visible neighboring rows"],
                    "target_values_may_be_used_for_model_design": False,
                },
                "preregistered_comparator": {
                    "comparator_id": "ROOM-TEMPERATURE-CONSTANT-TRANSPORT-COMPARATOR",
                    "prediction_rule": "Predict every hidden row using the visible row closest to 298.15 K for that property.",
                    "pre_registered": True,
                    "target_values_used_for_baseline_design": False,
                },
                "uncertainty_and_residual": {
                    "uncertainty_method": "fixed table precision plus visible-row interpolation residual envelope",
                    "residual_metric": "relative absolute residual per hidden property; aggregate mean relative absolute error",
                    "superiority_rule": "interpolator aggregate residual plus uncertainty allowance must be lower than the room-temperature constant comparator",
                },
                "negative_control": {
                    "control_id": "NIST-WATER-TEMPERATURE-SHUFFLE",
                    "description": "Shuffle hidden temperature labels after source lock.",
                    "rejection_predicate": "temperature shuffle changes row hashes and worsens transport-property residuals relative to locked rows",
                },
                "falsifier": {
                    "falsifier_id": "NIST-WEBBOOK-ENERGY-TRANSPORT-FAIL-CLOSED-FALSIFIER",
                    "triggers": [
                        "hidden transport properties appear in visible rows before prediction materialization",
                        "NIST WebBook source snapshot hash is missing or changes",
                        "constant room-temperature comparator ties or beats the interpolation model",
                        "fewer than 20 hidden property targets are scored",
                    ],
                },
                "N": {
                    "minimum_n": 20,
                    "planned_source_rows": 21,
                    "planned_hidden_target_rows": 30,
                    "unit": "temperature/property targets",
                },
                "replay_command": {
                    "commands": [
                        "acquire the NIST WebBook fluid endpoint listed in this spec and hash response bytes",
                        "python validation/heldout/grand_science/engineering/coverage_work_orders/oc133_engineering_modern_science_coverage_work_orders.py --check",
                    ],
                    "acceptance_predicates": COMMON_CLOSURE_PREDICATES,
                },
                "fail_closed_current_evidence": fail_closed_evidence(
                    "NIST WebBook source snapshot, target-hidden scorer, negative-control replay, and strict evidence pack are not yet bound."
                ),
            },
            "no_send_locks": no_send(),
        },
    ]
    return [with_hash(row) for row in rows]


def build_payload() -> dict[str, Any]:
    rows = build_work_orders()
    return {
        "schema_id": SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "generated_on": GENERATED_ON,
        "capability_owner": CAPABILITY_OWNER,
        "generated_by": SCRIPT_REL,
        "coverage_register_ref": COVERAGE_REGISTER_REL,
        "modern_science_work_orders_ref": MODERN_WORK_ORDERS_REL,
        "domain_class_id": "engineering_materials_sciences",
        "target_work_order_ids": ["MS-COV-WO-022", "MS-COV-WO-023", "MS-COV-WO-024"],
        "work_order_total": len(rows),
        "coverage_closure_allowed": False,
        "broad_modern_science_superiority_allowed": False,
        "no_send_locks": no_send(),
        "work_orders": rows,
    }


def validate_executable_spec(spec: dict[str, Any], *, row_id: str) -> list[str]:
    failures: list[str] = []
    for field in SPEC_REQUIRED_FIELDS:
        if not spec.get(field):
            failures.append(f"SPEC_FIELD_MISSING::{row_id}::{field}")
    source = spec.get("official_source", {})
    if not str(source.get("source_authority", "")):
        failures.append(f"OFFICIAL_SOURCE_AUTHORITY_MISSING::{row_id}")
    if not str(source.get("official_documentation_url", "")).startswith("https://"):
        failures.append(f"OFFICIAL_SOURCE_DOC_URL_MISSING::{row_id}")
    if not str(source.get("official_endpoint_url", "")).startswith("https://"):
        failures.append(f"OFFICIAL_SOURCE_ENDPOINT_URL_MISSING::{row_id}")
    target = spec.get("target_variable", {})
    if not target.get("target_fields"):
        failures.append(f"TARGET_FIELDS_MISSING::{row_id}")
    split = spec.get("target_hidden_split", {})
    if split.get("target_hidden_until_scoring") is not True:
        failures.append(f"TARGET_NOT_HIDDEN_UNTIL_SCORING::{row_id}")
    if split.get("target_values_used_for_selection") is not False:
        failures.append(f"TARGET_VALUES_USED_FOR_SELECTION::{row_id}")
    formula = spec.get("formula_or_model", {})
    if formula.get("target_values_may_be_used_for_model_design") is not False:
        failures.append(f"FORMULA_TARGET_LEAK_ALLOWED::{row_id}")
    comparator = spec.get("preregistered_comparator", {})
    if comparator.get("pre_registered") is not True:
        failures.append(f"COMPARATOR_NOT_PREREGISTERED::{row_id}")
    if comparator.get("target_values_used_for_baseline_design") is not False:
        failures.append(f"COMPARATOR_TARGET_LEAK_ALLOWED::{row_id}")
    if not spec.get("uncertainty_and_residual", {}).get("residual_metric"):
        failures.append(f"RESIDUAL_METRIC_MISSING::{row_id}")
    if not spec.get("negative_control", {}).get("rejection_predicate"):
        failures.append(f"NEGATIVE_CONTROL_REJECTION_MISSING::{row_id}")
    if not spec.get("falsifier", {}).get("triggers"):
        failures.append(f"FALSIFIER_TRIGGERS_MISSING::{row_id}")
    if int(spec.get("N", {}).get("minimum_n", 0) or 0) < 20:
        failures.append(f"MINIMUM_N_LT_20::{row_id}")
    if not spec.get("replay_command", {}).get("commands"):
        failures.append(f"REPLAY_COMMAND_MISSING::{row_id}")
    evidence = spec.get("fail_closed_current_evidence", {})
    if evidence.get("coverage_closure_allowed") is not False:
        failures.append(f"FAIL_CLOSED_EVIDENCE_ALLOWS_CLOSURE::{row_id}")
    if evidence.get("scientific_pass") is not False:
        failures.append(f"FAIL_CLOSED_EVIDENCE_FAKE_PASS::{row_id}")
    return failures


def validate_payload(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    rows = payload.get("work_orders", [])
    if payload.get("coverage_closure_allowed") is not False:
        failures.append("PAYLOAD_COVERAGE_CLOSURE_ALLOWED")
    if payload.get("broad_modern_science_superiority_allowed") is not False:
        failures.append("PAYLOAD_BROAD_SUPERIORITY_ALLOWED")
    if not isinstance(rows, list) or payload.get("work_order_total") != len(rows):
        failures.append("WORK_ORDER_TOTAL_MISMATCH")
        return failures
    expected_ids = {"MS-COV-WO-022", "MS-COV-WO-023", "MS-COV-WO-024"}
    if {str(row.get("work_order_id")) for row in rows if isinstance(row, dict)} != expected_ids:
        failures.append("ENGINEERING_WORK_ORDER_SET_MISMATCH")
    for row in rows:
        if not isinstance(row, dict):
            failures.append("WORK_ORDER_NOT_OBJECT")
            continue
        row_id = str(row.get("work_order_id", "unknown"))
        if row.get("coverage_closure_allowed") is not False:
            failures.append(f"COVERAGE_CLOSURE_ALLOWED::{row_id}")
        if row.get("support_allowed_for_broad_coverage") is not False:
            failures.append(f"BROAD_SUPPORT_ALLOWED::{row_id}")
        if str(row.get("lane_status", "")).upper() == "PASS":
            failures.append(f"FAKE_PASS_STATUS::{row_id}")
        failures.extend(validate_executable_spec(row.get("executable_spec", {}), row_id=row_id))
        expected_hash = sha256_object({key: value for key, value in row.items() if key != "row_sha256"})
        if row.get("row_sha256") != expected_hash:
            failures.append(f"ROW_HASH_MISMATCH::{row_id}")
    return failures


def check_stored(root: Path | None = None) -> list[str]:
    root = root or repo_root()
    expected = build_payload()
    failures = validate_payload(expected)
    path = root / OUTPUT_REL
    if not path.exists():
        return [*failures, f"missing::{OUTPUT_REL}"]
    actual = read_json(path)
    if actual != expected:
        failures.append(f"mismatch::{OUTPUT_REL}")
    failures.extend(validate_payload(actual if isinstance(actual, dict) else {}))
    return sorted(set(failures))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build/check engineering modern-science coverage work orders.")
    parser.add_argument("--root", default=str(repo_root()), help="repository root")
    parser.add_argument("--write", action="store_true", help="write deterministic work-order artifact")
    parser.add_argument("--check", action="store_true", help="check stored artifact synchronization")
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
        print(json.dumps({"status": "ok", "checked": OUTPUT_REL}, indent=2))
        return 0
    payload = build_payload()
    failures = validate_payload(payload)
    if args.write:
        write_json(root / OUTPUT_REL, payload)
    print(json.dumps({"status": "ok" if not failures else "failed", "output_ref": OUTPUT_REL, "failures": failures}, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
