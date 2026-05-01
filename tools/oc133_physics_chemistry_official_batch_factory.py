from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from validation.grand_science import evidence_pack_factory as grand_factory  # noqa: E402


RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
CAPABILITY_OWNER = "Research/EmpiricalScience"
BLOCKER_ID = "grand_toe_empirical_superiority"

OUTPUT_ROOT_REL = "validation/heldout/grand_science/physics_chemistry/official_batch"
TASKS_REL = f"{OUTPUT_ROOT_REL}/OC133_PHYSICS_CHEMISTRY_OFFICIAL_BATCH_TASKS.json"
REPORT_REL = f"{OUTPUT_ROOT_REL}/OC133_PHYSICS_CHEMISTRY_OFFICIAL_BATCH_REPORT.json"
PROTOCOL_REL = f"{OUTPUT_ROOT_REL}/OC133_PHYSICS_CHEMISTRY_OFFICIAL_BATCH_PROTOCOL.json"
README_REL = f"{OUTPUT_ROOT_REL}/README.md"
PHYSICS_PACK_REL = f"{OUTPUT_ROOT_REL}/physics_official_batch_candidate_evidence_pack.json"
CHEMISTRY_PACK_REL = f"{OUTPUT_ROOT_REL}/chemistry_official_batch_candidate_evidence_pack.json"
PHYSICS_ACQUISITION_PACKET_REL = f"{OUTPUT_ROOT_REL}/OC133_PHYSICS_OFFICIAL_BATCH_ACQUISITION_PACKET.json"

REQUIREMENTS_REL = "benchmarks/grand_science/domain_requirements.json"
MANIFEST_REL = "data/OC_DATASET_SNAPSHOT_MANIFEST_1_3_3.json"
EVIDENCE_SCHEMA_REL = "validation/grand_science/grand_empirical_evidence.schema.json"

PHYSICS_NIST_CONSTANTS_REF = "validation/_raw/physics_nist_constants.txt"
CHEMISTRY_PUBCHEM_WATER_REF = "validation/_raw/chemistry_pubchem_water.txt"
CHEMISTRY_NIST_WEBBOOK_WATER_REF = "validation/_raw/chemistry_nist_webbook_water.txt"

DOMAINS = ("physics", "chemistry")
MINIMUM_N_DEFAULT = 20
SNAPSHOT_HASH_POLICY = "LF_NORMALIZED_TEXT_SNAPSHOT_HASH"
ROW_HASH_POLICY = "sha256 over canonical row JSON excluding row_hash fields"
PACK_HASH_POLICY = "sha256 over canonical JSON"
RESIDUAL_METRIC_ID = "absolute_error_with_uncertainty_normalized_score_v1"

REPORT_SCHEMA_ID = "OC133_PHYSICS_CHEMISTRY_OFFICIAL_BATCH_REPORT_v1"
PROTOCOL_SCHEMA_ID = "OC133_PHYSICS_CHEMISTRY_OFFICIAL_BATCH_PROTOCOL_v1"
TASKS_SCHEMA_ID = "OC133_PHYSICS_CHEMISTRY_OFFICIAL_BATCH_TASKS_v1"
PHYSICS_ACQUISITION_PACKET_SCHEMA_ID = "OC133_PHYSICS_OFFICIAL_BATCH_ACQUISITION_PACKET_v1"

NO_SEND_POLICY = (
    "Official NIST/PubChem snapshot rows are scored and hashed, but no grand TOE support is emitted unless "
    "the domain pack has N>=20, pre-target target-blind or prospective separation, preregistered comparator "
    "baselines, residual superiority, rejected negative controls, falsifiers, and a clean grand empirical gate."
)

ATOMIC_WEIGHTS = {
    "H": 1.00784,
    "C": 12.011,
    "N": 14.0067,
    "O": 15.999,
    "Na": 22.98976928,
    "Cl": 35.45,
}


@dataclass(frozen=True)
class NistConstant:
    quantity: str
    value: float
    value_text: str
    uncertainty: float
    uncertainty_text: str
    unit: str
    source_ref: str
    snapshot_sha256: str


@dataclass(frozen=True)
class PhysicsFormula:
    task_id: str
    target: str
    formula: str
    ingredients: tuple[str, ...]
    predictor: Callable[[dict[str, float]], float]


PHYSICS_TARGET_FIELDS = (
    "target_quantity",
    "observed_value",
    "target_unit",
    "official_uncertainty",
    "uncertainty",
)


def repo_root() -> Path:
    return ROOT


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_object(payload: Any) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def lf_bytes(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n")


def sha256_file_text(path: Path) -> str:
    return hashlib.sha256(lf_bytes(path)).hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_under_root(root: Path, ref: str) -> Path:
    path = (root / ref).resolve()
    path.relative_to(root.resolve())
    return path


def ordered_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def as_float(value: Any, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return default
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    return result if math.isfinite(result) else default


def load_requirements(root: Path) -> tuple[dict[str, Any], list[str]]:
    path = root / REQUIREMENTS_REL
    if not path.exists():
        return (
            {
                "minimum_per_domain_n": MINIMUM_N_DEFAULT,
                "required_domains": list(DOMAINS),
                "required_source_separation_modes": ["prospective", "target_blind"],
            },
            ["REQUIREMENTS_MISSING::using_defaults"],
        )
    payload = read_json(path)
    if not isinstance(payload, dict):
        return (
            {
                "minimum_per_domain_n": MINIMUM_N_DEFAULT,
                "required_domains": list(DOMAINS),
                "required_source_separation_modes": ["prospective", "target_blind"],
            },
            ["REQUIREMENTS_NOT_OBJECT::using_defaults"],
        )
    return payload, []


def load_manifest(root: Path) -> dict[str, dict[str, Any]]:
    path = root / MANIFEST_REL
    if not path.exists():
        return {}
    try:
        payload = read_json(path)
    except Exception:
        return {}
    rows = payload.get("rows") if isinstance(payload, dict) else []
    if not isinstance(rows, list):
        return {}
    return {str(row.get("source_id")): row for row in rows if isinstance(row, dict) and row.get("source_id")}


def snapshot_record(root: Path, ref: str, manifest: dict[str, dict[str, Any]], source_id: str) -> dict[str, Any]:
    path = resolve_under_root(root, ref)
    exists = path.is_file()
    actual_sha = sha256_file_text(path) if exists else ""
    manifest_row = manifest.get(source_id, {})
    expected_sha = str(manifest_row.get("sha256") or manifest_row.get("source_sha256") or "")
    return {
        "source_id": source_id,
        "source_ref": ref,
        "official_url": str(manifest_row.get("url") or official_url_for_source(source_id)),
        "exists": exists,
        "byte_count": len(lf_bytes(path)) if exists else 0,
        "sha256": actual_sha,
        "sha256_expected": expected_sha,
        "sha256_match": bool(actual_sha and expected_sha and actual_sha == expected_sha),
        "hash_policy": SNAPSHOT_HASH_POLICY,
    }


def official_url_for_source(source_id: str) -> str:
    return {
        "physics_nist_constants": "https://physics.nist.gov/cuu/Constants/Table/allascii.txt",
        "chemistry_pubchem_water": (
            "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/962/property/"
            "MolecularFormula,MolecularWeight,CanonicalSMILES,InChIKey/JSON"
        ),
        "chemistry_nist_webbook_water": "https://webbook.nist.gov/cgi/cbook.cgi?ID=C7732185&Units=SI",
    }.get(source_id, "")


NUMBER_RE = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?")


def parse_number(text: str) -> float | None:
    cleaned = text.replace("...", "").replace(" ", "").replace(",", "").strip()
    cleaned = cleaned.replace("(exact)", "")
    match = NUMBER_RE.search(cleaned)
    if not match:
        return None
    try:
        value = float(match.group(0))
    except ValueError:
        return None
    return value if math.isfinite(value) else None


def parse_nist_constants(text: str, source_ref: str, snapshot_sha256: str) -> dict[str, NistConstant]:
    constants: dict[str, NistConstant] = {}
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.startswith("-") or raw_line.strip().startswith("Quantity"):
            continue
        parts = re.split(r"\s{2,}", raw_line.strip())
        if len(parts) < 3:
            continue
        quantity = parts[0].strip()
        value_text = parts[1].strip()
        uncertainty_text = parts[2].strip()
        unit = " ".join(parts[3:]).strip()
        value = parse_number(value_text)
        if not quantity or value is None:
            continue
        uncertainty = 0.0 if "(exact)" in uncertainty_text else (parse_number(uncertainty_text) or 0.0)
        constants[quantity] = NistConstant(
            quantity=quantity,
            value=value,
            value_text=value_text,
            uncertainty=uncertainty,
            uncertainty_text=uncertainty_text,
            unit=unit,
            source_ref=source_ref,
            snapshot_sha256=snapshot_sha256,
        )
    return constants


def physics_formulas() -> tuple[PhysicsFormula, ...]:
    c = "speed of light in vacuum"
    h = "Planck constant"
    e = "elementary charge"
    k = "Boltzmann constant"
    u = "atomic mass constant"
    eh = "Hartree energy"
    rinf = "Rydberg constant"
    na = "Avogadro constant"
    return (
        PhysicsFormula("PHYS-CODATA-001", "inverse meter-hertz relationship", "c", (c,), lambda v: v[c]),
        PhysicsFormula("PHYS-CODATA-002", "hertz-joule relationship", "h", (h,), lambda v: v[h]),
        PhysicsFormula("PHYS-CODATA-003", "electron volt-joule relationship", "e", (e,), lambda v: v[e]),
        PhysicsFormula("PHYS-CODATA-004", "electron volt", "e", (e,), lambda v: v[e]),
        PhysicsFormula("PHYS-CODATA-005", "hertz-electron volt relationship", "h/e", (h, e), lambda v: v[h] / v[e]),
        PhysicsFormula("PHYS-CODATA-006", "electron volt-hertz relationship", "e/h", (e, h), lambda v: v[e] / v[h]),
        PhysicsFormula("PHYS-CODATA-007", "inverse meter-joule relationship", "h*c", (h, c), lambda v: v[h] * v[c]),
        PhysicsFormula("PHYS-CODATA-008", "inverse meter-electron volt relationship", "h*c/e", (h, c, e), lambda v: v[h] * v[c] / v[e]),
        PhysicsFormula("PHYS-CODATA-009", "electron volt-inverse meter relationship", "e/(h*c)", (e, h, c), lambda v: v[e] / (v[h] * v[c])),
        PhysicsFormula("PHYS-CODATA-010", "electron volt-kelvin relationship", "e/k", (e, k), lambda v: v[e] / v[k]),
        PhysicsFormula("PHYS-CODATA-011", "kelvin-electron volt relationship", "k/e", (k, e), lambda v: v[k] / v[e]),
        PhysicsFormula("PHYS-CODATA-012", "hertz-kelvin relationship", "h/k", (h, k), lambda v: v[h] / v[k]),
        PhysicsFormula("PHYS-CODATA-013", "kelvin-hertz relationship", "k/h", (k, h), lambda v: v[k] / v[h]),
        PhysicsFormula("PHYS-CODATA-014", "inverse meter-kelvin relationship", "h*c/k", (h, c, k), lambda v: v[h] * v[c] / v[k]),
        PhysicsFormula("PHYS-CODATA-015", "kelvin-inverse meter relationship", "k/(h*c)", (k, h, c), lambda v: v[k] / (v[h] * v[c])),
        PhysicsFormula("PHYS-CODATA-016", "joule-inverse meter relationship", "1/(h*c)", (h, c), lambda v: 1.0 / (v[h] * v[c])),
        PhysicsFormula("PHYS-CODATA-017", "joule-kelvin relationship", "1/k", (k,), lambda v: 1.0 / v[k]),
        PhysicsFormula("PHYS-CODATA-018", "joule-kilogram relationship", "1/c^2", (c,), lambda v: 1.0 / (v[c] ** 2)),
        PhysicsFormula("PHYS-CODATA-019", "kilogram-joule relationship", "c^2", (c,), lambda v: v[c] ** 2),
        PhysicsFormula("PHYS-CODATA-020", "kilogram-hertz relationship", "c^2/h", (c, h), lambda v: (v[c] ** 2) / v[h]),
        PhysicsFormula("PHYS-CODATA-021", "kilogram-inverse meter relationship", "c/h", (c, h), lambda v: v[c] / v[h]),
        PhysicsFormula("PHYS-CODATA-022", "kilogram-kelvin relationship", "c^2/k", (c, k), lambda v: (v[c] ** 2) / v[k]),
        PhysicsFormula("PHYS-CODATA-023", "kilogram-electron volt relationship", "c^2/e", (c, e), lambda v: (v[c] ** 2) / v[e]),
        PhysicsFormula("PHYS-CODATA-024", "electron volt-kilogram relationship", "e/c^2", (e, c), lambda v: v[e] / (v[c] ** 2)),
        PhysicsFormula("PHYS-CODATA-025", "atomic mass unit-kilogram relationship", "u", (u,), lambda v: v[u]),
        PhysicsFormula("PHYS-CODATA-026", "atomic mass unit-joule relationship", "u*c^2", (u, c), lambda v: v[u] * (v[c] ** 2)),
        PhysicsFormula("PHYS-CODATA-027", "atomic mass unit-electron volt relationship", "u*c^2/e", (u, c, e), lambda v: v[u] * (v[c] ** 2) / v[e]),
        PhysicsFormula("PHYS-CODATA-028", "atomic mass unit-hertz relationship", "u*c^2/h", (u, c, h), lambda v: v[u] * (v[c] ** 2) / v[h]),
        PhysicsFormula("PHYS-CODATA-029", "atomic mass unit-inverse meter relationship", "u*c/h", (u, c, h), lambda v: v[u] * v[c] / v[h]),
        PhysicsFormula("PHYS-CODATA-030", "atomic mass unit-kelvin relationship", "u*c^2/k", (u, c, k), lambda v: v[u] * (v[c] ** 2) / v[k]),
        PhysicsFormula("PHYS-CODATA-031", "kelvin-atomic mass unit relationship", "k/(u*c^2)", (k, u, c), lambda v: v[k] / (v[u] * (v[c] ** 2))),
        PhysicsFormula("PHYS-CODATA-032", "hartree-joule relationship", "Eh", (eh,), lambda v: v[eh]),
        PhysicsFormula("PHYS-CODATA-033", "hartree-electron volt relationship", "Eh/e", (eh, e), lambda v: v[eh] / v[e]),
        PhysicsFormula("PHYS-CODATA-034", "hartree-hertz relationship", "Eh/h", (eh, h), lambda v: v[eh] / v[h]),
        PhysicsFormula("PHYS-CODATA-035", "hartree-inverse meter relationship", "Eh/(h*c)", (eh, h, c), lambda v: v[eh] / (v[h] * v[c])),
        PhysicsFormula("PHYS-CODATA-036", "hartree-kelvin relationship", "Eh/k", (eh, k), lambda v: v[eh] / v[k]),
        PhysicsFormula("PHYS-CODATA-037", "hartree-kilogram relationship", "Eh/c^2", (eh, c), lambda v: v[eh] / (v[c] ** 2)),
        PhysicsFormula("PHYS-CODATA-038", "kelvin-hartree relationship", "k/Eh", (k, eh), lambda v: v[k] / v[eh]),
        PhysicsFormula("PHYS-CODATA-039", "Rydberg constant times c in Hz", "Rinf*c", (rinf, c), lambda v: v[rinf] * v[c]),
        PhysicsFormula("PHYS-CODATA-040", "Rydberg constant times hc in J", "Rinf*h*c", (rinf, h, c), lambda v: v[rinf] * v[h] * v[c]),
        PhysicsFormula("PHYS-CODATA-041", "Rydberg constant times hc in eV", "Rinf*h*c/e", (rinf, h, c, e), lambda v: v[rinf] * v[h] * v[c] / v[e]),
        PhysicsFormula("PHYS-CODATA-042", "molar Planck constant", "h*NA", (h, na), lambda v: v[h] * v[na]),
        PhysicsFormula("PHYS-CODATA-043", "Faraday constant", "e*NA", (e, na), lambda v: v[e] * v[na]),
        PhysicsFormula("PHYS-CODATA-044", "molar gas constant", "k*NA", (k, na), lambda v: v[k] * v[na]),
    )


def row_hash(row: dict[str, Any]) -> str:
    return sha256_object({k: v for k, v in row.items() if k not in {"row_hash", "row_hash_policy"}})


def row_hash_valid(row: dict[str, Any]) -> bool:
    return bool(row.get("row_hash")) and row_hash(row) == row.get("row_hash")


def display_tolerance(observed: float, official_uncertainty: float, value_text: str) -> float:
    if official_uncertainty > 0:
        return max(official_uncertainty, abs(observed) * 1e-12, 1e-300)
    if "..." in value_text:
        return max(abs(observed) * 1e-8, 1e-300)
    return max(abs(observed) * 1e-12, 1e-300)


def residual_score(residual: float, tolerance: float) -> float:
    return abs(residual) / max(abs(tolerance), 1e-300)


def physics_visible_projection(spec: PhysicsFormula, constants: dict[str, NistConstant]) -> dict[str, Any]:
    return {
        "projection_id": f"{spec.task_id}-VISIBLE-PROJECTION-v1",
        "source_ref": PHYSICS_NIST_CONSTANTS_REF,
        "visible_fields": [
            {
                "quantity": name,
                "value_text": constants[name].value_text,
                "unit": constants[name].unit,
                "uncertainty_text": constants[name].uncertainty_text,
            }
            for name in spec.ingredients
        ],
        "target_fields_excluded": list(PHYSICS_TARGET_FIELDS),
        "projection_hash": sha256_object(
            {
                "task_id": spec.task_id,
                "ingredients": [
                    {
                        "quantity": name,
                        "value_text": constants[name].value_text,
                        "unit": constants[name].unit,
                        "uncertainty_text": constants[name].uncertainty_text,
                    }
                    for name in spec.ingredients
                ],
            }
        ),
    }


def physics_target_projection(spec: PhysicsFormula, target: NistConstant) -> dict[str, Any]:
    return {
        "projection_id": f"{spec.task_id}-TARGET-PROJECTION-v1",
        "source_ref": PHYSICS_NIST_CONSTANTS_REF,
        "target_fields": {
            "target_quantity": spec.target,
            "observed_value_text": target.value_text,
            "target_unit": target.unit,
            "official_uncertainty_text": target.uncertainty_text,
        },
        "target_hash": sha256_object(
            {
                "target_quantity": spec.target,
                "observed_value_text": target.value_text,
                "target_unit": target.unit,
                "official_uncertainty_text": target.uncertainty_text,
            }
        ),
    }


def physics_projection_declaration(spec: PhysicsFormula, visible: dict[str, Any], target: dict[str, Any]) -> dict[str, Any]:
    return {
        "declaration_id": f"{spec.task_id}-PROJECTION-DECLARATION-v1",
        "visible_projection_id": visible["projection_id"],
        "target_projection_id": target["projection_id"],
        "declared_before_scoring": True,
        "declared_before_target_snapshot_access": False,
        "target_hidden_until_scoring": False,
        "separation_class": "posthoc_visible_target_projection_not_target_blind",
        "promotion_blocker": "projection is explicit and auditable, but the local CODATA snapshot was already visible before this run",
    }


def physics_preregistration(spec: PhysicsFormula, tolerance: float) -> dict[str, Any]:
    return {
        "preregistration_id": f"{spec.task_id}-ANALYSIS-PREREG-v1",
        "declared_before_scoring": True,
        "declared_before_target_snapshot_access": False,
        "formula": {
            "expression": spec.formula,
            "visible_inputs": list(spec.ingredients),
            "target_quantity": spec.target,
        },
        "residual_metric": {
            "metric_id": RESIDUAL_METRIC_ID,
            "absolute_residual": "abs(predicted_value - observed_value)",
            "score": "absolute_residual / row_uncertainty_or_display_tolerance",
            "row_tolerance": tolerance,
        },
        "comparator": {
            "comparator_id": f"{spec.task_id}-ZERO-VALUE-NULL-v1",
            "name": "zero-value null baseline",
            "prediction_rule": "predict numeric zero for the target under the same residual metric",
            "prediction_value": 0.0,
            "pre_registered": True,
        },
        "negative_control": {
            "control_id": f"{spec.task_id}-ZERO-BASELINE",
            "rule": "zero-value null baseline must have a larger residual score than the formula prediction",
        },
        "falsifier": "formula residual score exceeds 1.0 or zero-value null baseline is not worse",
    }


def visible_projection_has_target_leakage(row: dict[str, Any]) -> bool:
    visible = row.get("visible_projection")
    if not isinstance(visible, dict):
        return True
    target = str(row.get("target_quantity") or "")
    visible_fields = visible.get("visible_fields", [])
    if not isinstance(visible_fields, list):
        return True
    for field in visible_fields:
        if not isinstance(field, dict):
            return True
        if target and str(field.get("quantity")) == target:
            return True
        if any(key in field for key in PHYSICS_TARGET_FIELDS):
            return True
    return False


def build_physics_rows(root: Path, snapshot_ref: str, manifest: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str], dict[str, Any]]:
    record = snapshot_record(root, snapshot_ref, manifest, "physics_nist_constants")
    if not record["exists"]:
        return [], [f"OFFICIAL_SNAPSHOT_MISSING::physics::{snapshot_ref}"], record
    text = resolve_under_root(root, snapshot_ref).read_text(encoding="utf-8", errors="replace")
    constants = parse_nist_constants(text, snapshot_ref, record["sha256"])
    values = {key: constant.value for key, constant in constants.items()}
    rows: list[dict[str, Any]] = []
    blockers: list[str] = []
    for spec in physics_formulas():
        missing = [name for name in (spec.target, *spec.ingredients) if name not in constants]
        if missing:
            blockers.append(f"PHYSICS_FORMULA_INPUT_MISSING::{spec.task_id}::{','.join(missing)}")
            continue
        target = constants[spec.target]
        try:
            predicted = float(spec.predictor(values))
        except Exception as exc:
            blockers.append(f"PHYSICS_FORMULA_EVALUATION_FAILED::{spec.task_id}::{exc.__class__.__name__}")
            continue
        observed = float(target.value)
        uncertainty = display_tolerance(observed, target.uncertainty, target.value_text)
        model_residual = abs(predicted - observed)
        comparator_prediction = 0.0
        comparator_residual = abs(comparator_prediction - observed)
        model_score = residual_score(model_residual, uncertainty)
        comparator_score = residual_score(comparator_residual, uncertainty)
        visible_projection = physics_visible_projection(spec, constants)
        target_projection = physics_target_projection(spec, target)
        projection_declaration = physics_projection_declaration(spec, visible_projection, target_projection)
        preregistration = physics_preregistration(spec, uncertainty)
        row = {
            "task_id": spec.task_id,
            "domain": "physics",
            "source_kind": "official_snapshot_formula_replay",
            "official_source_id": "physics_nist_constants",
            "snapshot_ref": snapshot_ref,
            "snapshot_sha256": record["sha256"],
            "target_quantity": spec.target,
            "target_unit": target.unit,
            "training_source": f"{snapshot_ref}::{spec.task_id}::formula_inputs::{','.join(spec.ingredients)}",
            "target_source": f"{snapshot_ref}::{spec.task_id}::target::{spec.target}",
            "formula": spec.formula,
            "ingredients": list(spec.ingredients),
            "visible_projection": visible_projection,
            "target_projection": target_projection,
            "projection_declaration": projection_declaration,
            "preregistration": preregistration,
            "predicted_value": predicted,
            "observed_value": observed,
            "official_uncertainty": target.uncertainty,
            "uncertainty": uncertainty,
            "residual_metric_id": RESIDUAL_METRIC_ID,
            "model_residual": model_residual,
            "model_residual_score": model_score,
            "comparator_baseline": "zero-value null baseline",
            "comparator_prediction": comparator_prediction,
            "comparator_residual": comparator_residual,
            "comparator_residual_score": comparator_score,
            "negative_control_id": f"{spec.task_id}-ZERO-BASELINE",
            "negative_control_description": "replace the derived CODATA relation with a zero-value null baseline and require a larger residual",
            "negative_control_rejected": comparator_score > model_score,
            "falsifier": "official relation residual exceeds display/uncertainty tolerance or the zero baseline is not worse",
            "residual_within_uncertainty": model_residual <= uncertainty,
            "grand_scope": "official snapshot consistency task; not independently pre-target locked in the current repo",
        }
        row["row_hash"] = row_hash(row)
        row["row_hash_policy"] = ROW_HASH_POLICY
        rows.append(row)
        if model_residual > uncertainty:
            blockers.append(f"PHYSICS_RESIDUAL_EXCEEDS_UNCERTAINTY::{spec.task_id}")
        if comparator_score <= model_score:
            blockers.append(f"PHYSICS_NEGATIVE_CONTROL_NOT_REJECTED::{spec.task_id}")
        if visible_projection_has_target_leakage(row):
            blockers.append(f"PHYSICS_VISIBLE_PROJECTION_TARGET_LEAKAGE::{spec.task_id}")
    return rows, ordered_unique(blockers), record


def formula_mass(formula: str) -> float | None:
    parts = re.findall(r"([A-Z][a-z]?)(\d*)", formula)
    if not parts:
        return None
    total = 0.0
    for element, raw_count in parts:
        if element not in ATOMIC_WEIGHTS:
            return None
        count = int(raw_count) if raw_count else 1
        total += ATOMIC_WEIGHTS[element] * count
    return total


def parse_pubchem_payload(root: Path, snapshot_ref: str) -> tuple[dict[str, Any], list[str]]:
    path = resolve_under_root(root, snapshot_ref)
    try:
        payload = read_json(path)
    except Exception as exc:
        return {}, [f"PUBCHEM_SNAPSHOT_PARSE_FAILED::{snapshot_ref}::{exc.__class__.__name__}"]
    props = payload.get("PropertyTable", {}).get("Properties", []) if isinstance(payload, dict) else []
    if not isinstance(props, list) or not props:
        return {}, [f"PUBCHEM_PROPERTY_ROWS_MISSING::{snapshot_ref}"]
    row = props[0] if isinstance(props[0], dict) else {}
    return row, []


def html_unescape_minimal(text: str) -> str:
    return (
        text.replace("&amp;", "&")
        .replace("&quot;", '"')
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&nbsp;", " ")
    )


def parse_webbook_payload(root: Path, snapshot_ref: str) -> tuple[dict[str, Any], list[str]]:
    path = resolve_under_root(root, snapshot_ref)
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return {}, [f"NIST_WEBBOOK_SNAPSHOT_READ_FAILED::{snapshot_ref}::{exc.__class__.__name__}"]
    data: dict[str, Any] = {}
    title = re.search(r"<title>(.*?)</title>", text, re.IGNORECASE | re.DOTALL)
    if title:
        data["name"] = html_unescape_minimal(re.sub(r"\s+", " ", title.group(1)).strip())
    formula = re.search(r'"molecularFormula"\s*:\s*"([^"]+)"', text)
    if formula:
        data["MolecularFormula"] = formula.group(1)
    weight = re.search(r'"molecularWeight"\s*:\s*"([^"]+?)\s+amu"', text)
    if weight:
        data["MolecularWeight"] = weight.group(1)
    inchi_key = re.search(r'"inChIKey"\s*:\s*"([^"]+)"', text)
    if inchi_key:
        data["InChIKey"] = inchi_key.group(1)
    cas = re.search(r"CAS Registry Number:</strong>\s*([^<\s]+)", text)
    if cas:
        data["CAS"] = cas.group(1)
    if not data:
        return {}, [f"NIST_WEBBOOK_FIELDS_MISSING::{snapshot_ref}"]
    return data, []


def metric_row(
    *,
    task_id: str,
    domain: str,
    source_kind: str,
    official_source_id: str,
    snapshot_ref: str,
    snapshot_sha256: str,
    target_name: str,
    formula: str,
    predicted: float,
    observed: float,
    uncertainty: float,
    comparator_prediction: float,
    comparator_name: str,
    negative_control_description: str,
    falsifier: str,
) -> dict[str, Any]:
    model_residual = abs(predicted - observed)
    comparator_residual = abs(comparator_prediction - observed)
    row = {
        "task_id": task_id,
        "domain": domain,
        "source_kind": source_kind,
        "official_source_id": official_source_id,
        "snapshot_ref": snapshot_ref,
        "snapshot_sha256": snapshot_sha256,
        "target_quantity": target_name,
        "training_source": f"{snapshot_ref}::{task_id}::visible-fields",
        "target_source": f"{snapshot_ref}::{task_id}::target-field::{target_name}",
        "formula": formula,
        "predicted_value": predicted,
        "observed_value": observed,
        "uncertainty": uncertainty,
        "model_residual": model_residual,
        "comparator_baseline": comparator_name,
        "comparator_prediction": comparator_prediction,
        "comparator_residual": comparator_residual,
        "negative_control_id": f"{task_id}-NEGATIVE-CONTROL",
        "negative_control_description": negative_control_description,
        "negative_control_rejected": comparator_residual > model_residual,
        "falsifier": falsifier,
        "residual_within_uncertainty": model_residual <= uncertainty,
        "grand_scope": "official snapshot field or cross-source consistency task; not independently pre-target locked in the current repo",
    }
    row["row_hash"] = row_hash(row)
    row["row_hash_policy"] = ROW_HASH_POLICY
    return row


def build_string_match_row(
    *,
    task_id: str,
    official_source_id: str,
    snapshot_ref: str,
    snapshot_sha256: str,
    target_name: str,
    expected: str,
    observed_text: str,
    wrong_value: str,
) -> dict[str, Any]:
    matched = expected == observed_text
    wrong_matched = wrong_value == observed_text
    return metric_row(
        task_id=task_id,
        domain="chemistry",
        source_kind="official_snapshot_metadata_replay",
        official_source_id=official_source_id,
        snapshot_ref=snapshot_ref,
        snapshot_sha256=snapshot_sha256,
        target_name=target_name,
        formula=f"exact string match to preregistered value {expected!r}",
        predicted=1.0 if matched else 0.0,
        observed=1.0,
        uncertainty=0.0,
        comparator_prediction=1.0 if wrong_matched else 0.0,
        comparator_name=f"wrong-string control {wrong_value!r}",
        negative_control_description=f"replace {target_name} with {wrong_value!r} and require mismatch",
        falsifier=f"{target_name} in official snapshot differs from {expected!r} or wrong-string control matches",
    )


def build_chemistry_rows(root: Path, manifest: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str], list[dict[str, Any]]]:
    pubchem_record = snapshot_record(root, CHEMISTRY_PUBCHEM_WATER_REF, manifest, "chemistry_pubchem_water")
    webbook_record = snapshot_record(root, CHEMISTRY_NIST_WEBBOOK_WATER_REF, manifest, "chemistry_nist_webbook_water")
    snapshot_records = [pubchem_record, webbook_record]
    rows: list[dict[str, Any]] = []
    blockers: list[str] = []
    pubchem: dict[str, Any] = {}
    webbook: dict[str, Any] = {}

    if pubchem_record["exists"]:
        pubchem, failures = parse_pubchem_payload(root, CHEMISTRY_PUBCHEM_WATER_REF)
        blockers.extend(failures)
    else:
        blockers.append(f"OFFICIAL_SNAPSHOT_MISSING::chemistry::{CHEMISTRY_PUBCHEM_WATER_REF}")

    if webbook_record["exists"]:
        webbook, failures = parse_webbook_payload(root, CHEMISTRY_NIST_WEBBOOK_WATER_REF)
        blockers.extend(failures)
    else:
        blockers.append(f"OFFICIAL_SNAPSHOT_MISSING::chemistry::{CHEMISTRY_NIST_WEBBOOK_WATER_REF}")

    if pubchem:
        pubchem_weight = parse_number(str(pubchem.get("MolecularWeight", "")))
        formula = str(pubchem.get("MolecularFormula", ""))
        formula_prediction = formula_mass(formula)
        if pubchem_weight is not None:
            rows.append(
                metric_row(
                    task_id="CHEM-PUBCHEM-001",
                    domain="chemistry",
                    source_kind="official_snapshot_field_replay",
                    official_source_id="chemistry_pubchem_water",
                    snapshot_ref=CHEMISTRY_PUBCHEM_WATER_REF,
                    snapshot_sha256=pubchem_record["sha256"],
                    target_name="MolecularWeight",
                    formula="PubChem MolecularWeight field replay",
                    predicted=pubchem_weight,
                    observed=pubchem_weight,
                    uncertainty=0.02,
                    comparator_prediction=44.0095,
                    comparator_name="CO2 molecular weight negative control",
                    negative_control_description="use CO2 molecular weight against water and require larger residual",
                    falsifier="PubChem MolecularWeight for CID 962 cannot be recovered or CO2 control is not worse",
                )
            )
        if formula and formula_prediction is not None and pubchem_weight is not None:
            rows.append(
                metric_row(
                    task_id="CHEM-PUBCHEM-002",
                    domain="chemistry",
                    source_kind="official_snapshot_formula_mass_reconstruction",
                    official_source_id="chemistry_pubchem_water",
                    snapshot_ref=CHEMISTRY_PUBCHEM_WATER_REF,
                    snapshot_sha256=pubchem_record["sha256"],
                    target_name="MolecularWeight",
                    formula=f"local atomic-weight reconstruction from {formula}",
                    predicted=formula_prediction,
                    observed=pubchem_weight,
                    uncertainty=0.05,
                    comparator_prediction=44.0095,
                    comparator_name="CO2 molecular weight negative control",
                    negative_control_description="replace H2O by CO2 and require larger residual",
                    falsifier="formula-mass residual exceeds tolerance or CO2 control is not worse",
                )
            )
        if formula:
            rows.append(
                build_string_match_row(
                    task_id="CHEM-PUBCHEM-003",
                    official_source_id="chemistry_pubchem_water",
                    snapshot_ref=CHEMISTRY_PUBCHEM_WATER_REF,
                    snapshot_sha256=pubchem_record["sha256"],
                    target_name="MolecularFormula",
                    expected="H2O",
                    observed_text=formula,
                    wrong_value="CO2",
                )
            )
        if pubchem.get("InChIKey"):
            rows.append(
                build_string_match_row(
                    task_id="CHEM-PUBCHEM-004",
                    official_source_id="chemistry_pubchem_water",
                    snapshot_ref=CHEMISTRY_PUBCHEM_WATER_REF,
                    snapshot_sha256=pubchem_record["sha256"],
                    target_name="InChIKey",
                    expected="XLYOFNOQVPJJNP-UHFFFAOYSA-N",
                    observed_text=str(pubchem.get("InChIKey")),
                    wrong_value="BSYNRYMUTXBXSQ-UHFFFAOYSA-N",
                )
            )
        if pubchem.get("ConnectivitySMILES"):
            rows.append(
                build_string_match_row(
                    task_id="CHEM-PUBCHEM-005",
                    official_source_id="chemistry_pubchem_water",
                    snapshot_ref=CHEMISTRY_PUBCHEM_WATER_REF,
                    snapshot_sha256=pubchem_record["sha256"],
                    target_name="ConnectivitySMILES",
                    expected="O",
                    observed_text=str(pubchem.get("ConnectivitySMILES")),
                    wrong_value="O=C=O",
                )
            )

    if webbook:
        webbook_weight = parse_number(str(webbook.get("MolecularWeight", "")))
        if webbook_weight is not None:
            rows.append(
                metric_row(
                    task_id="CHEM-NIST-WEBBOOK-001",
                    domain="chemistry",
                    source_kind="official_snapshot_field_replay",
                    official_source_id="chemistry_nist_webbook_water",
                    snapshot_ref=CHEMISTRY_NIST_WEBBOOK_WATER_REF,
                    snapshot_sha256=webbook_record["sha256"],
                    target_name="molecularWeight",
                    formula="NIST WebBook molecularWeight field replay",
                    predicted=webbook_weight,
                    observed=webbook_weight,
                    uncertainty=0.02,
                    comparator_prediction=44.0095,
                    comparator_name="CO2 molecular weight negative control",
                    negative_control_description="use CO2 molecular weight against WebBook water and require larger residual",
                    falsifier="NIST WebBook molecularWeight for water cannot be recovered or CO2 control is not worse",
                )
            )
        if webbook.get("MolecularFormula"):
            rows.append(
                build_string_match_row(
                    task_id="CHEM-NIST-WEBBOOK-002",
                    official_source_id="chemistry_nist_webbook_water",
                    snapshot_ref=CHEMISTRY_NIST_WEBBOOK_WATER_REF,
                    snapshot_sha256=webbook_record["sha256"],
                    target_name="molecularFormula",
                    expected="H2O",
                    observed_text=str(webbook.get("MolecularFormula")),
                    wrong_value="CO2",
                )
            )
        if webbook.get("InChIKey"):
            rows.append(
                build_string_match_row(
                    task_id="CHEM-NIST-WEBBOOK-003",
                    official_source_id="chemistry_nist_webbook_water",
                    snapshot_ref=CHEMISTRY_NIST_WEBBOOK_WATER_REF,
                    snapshot_sha256=webbook_record["sha256"],
                    target_name="inChIKey",
                    expected="XLYOFNOQVPJJNP-UHFFFAOYSA-N",
                    observed_text=str(webbook.get("InChIKey")),
                    wrong_value="BSYNRYMUTXBXSQ-UHFFFAOYSA-N",
                )
            )
        if webbook.get("CAS"):
            rows.append(
                build_string_match_row(
                    task_id="CHEM-NIST-WEBBOOK-004",
                    official_source_id="chemistry_nist_webbook_water",
                    snapshot_ref=CHEMISTRY_NIST_WEBBOOK_WATER_REF,
                    snapshot_sha256=webbook_record["sha256"],
                    target_name="CAS Registry Number",
                    expected="7732-18-5",
                    observed_text=str(webbook.get("CAS")),
                    wrong_value="124-38-9",
                )
            )

    pubchem_weight = parse_number(str(pubchem.get("MolecularWeight", ""))) if pubchem else None
    webbook_weight = parse_number(str(webbook.get("MolecularWeight", ""))) if webbook else None
    if pubchem_weight is not None and webbook_weight is not None:
        rows.append(
            metric_row(
                task_id="CHEM-CROSS-SOURCE-001",
                domain="chemistry",
                source_kind="official_snapshot_cross_source_consistency",
                official_source_id="chemistry_pubchem_water+chemistry_nist_webbook_water",
                snapshot_ref=f"{CHEMISTRY_PUBCHEM_WATER_REF}+{CHEMISTRY_NIST_WEBBOOK_WATER_REF}",
                snapshot_sha256=sha256_object([pubchem_record["sha256"], webbook_record["sha256"]]),
                target_name="MolecularWeight cross-source consistency",
                formula="PubChem MolecularWeight predicts NIST WebBook molecularWeight",
                predicted=pubchem_weight,
                observed=webbook_weight,
                uncertainty=0.02,
                comparator_prediction=44.0095,
                comparator_name="CO2 molecular weight negative control",
                negative_control_description="use CO2 molecular weight against water cross-source target and require larger residual",
                falsifier="PubChem/WebBook water molecular-weight disagreement exceeds tolerance or CO2 control is not worse",
            )
        )
    if pubchem.get("MolecularFormula") and webbook.get("MolecularFormula"):
        rows.append(
            build_string_match_row(
                task_id="CHEM-CROSS-SOURCE-002",
                official_source_id="chemistry_pubchem_water+chemistry_nist_webbook_water",
                snapshot_ref=f"{CHEMISTRY_PUBCHEM_WATER_REF}+{CHEMISTRY_NIST_WEBBOOK_WATER_REF}",
                snapshot_sha256=sha256_object([pubchem_record["sha256"], webbook_record["sha256"]]),
                target_name="MolecularFormula cross-source consistency",
                expected=str(pubchem.get("MolecularFormula")),
                observed_text=str(webbook.get("MolecularFormula")),
                wrong_value="CO2",
            )
        )
    if pubchem.get("InChIKey") and webbook.get("InChIKey"):
        rows.append(
            build_string_match_row(
                task_id="CHEM-CROSS-SOURCE-003",
                official_source_id="chemistry_pubchem_water+chemistry_nist_webbook_water",
                snapshot_ref=f"{CHEMISTRY_PUBCHEM_WATER_REF}+{CHEMISTRY_NIST_WEBBOOK_WATER_REF}",
                snapshot_sha256=sha256_object([pubchem_record["sha256"], webbook_record["sha256"]]),
                target_name="InChIKey cross-source consistency",
                expected=str(pubchem.get("InChIKey")),
                observed_text=str(webbook.get("InChIKey")),
                wrong_value="BSYNRYMUTXBXSQ-UHFFFAOYSA-N",
            )
        )
    for row in rows:
        if row.get("negative_control_rejected") is not True:
            blockers.append(f"CHEMISTRY_NEGATIVE_CONTROL_NOT_REJECTED::{row.get('task_id')}")
        if row.get("residual_within_uncertainty") is not True:
            blockers.append(f"CHEMISTRY_RESIDUAL_EXCEEDS_UNCERTAINTY::{row.get('task_id')}")
    return rows, ordered_unique(blockers), snapshot_records


def default_source_separation(domain: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    visible_projection_ids = ordered_unique(
        [
            str((row.get("visible_projection") or {}).get("projection_id"))
            for row in rows
            if isinstance(row.get("visible_projection"), dict) and (row.get("visible_projection") or {}).get("projection_id")
        ]
    )
    target_projection_ids = ordered_unique(
        [
            str((row.get("target_projection") or {}).get("projection_id"))
            for row in rows
            if isinstance(row.get("target_projection"), dict) and (row.get("target_projection") or {}).get("projection_id")
        ]
    )
    return {
        "mode": "official_snapshot_replay",
        "pre_target_lock": False,
        "target_hidden_until_scoring": False,
        "declared_before_scoring": False,
        "visible_target_projection_declared": bool(rows),
        "visible_projection_ids": visible_projection_ids,
        "target_projection_ids": target_projection_ids,
        "strict_source_separation_attested": False,
        "attestation_ref": "",
        "source_separation_class": "posthoc_projection_only",
        "training_sources": ordered_unique([str(row["training_source"]) for row in rows if row.get("training_source")]),
        "target_sources": ordered_unique([str(row["target_source"]) for row in rows if row.get("target_source")]),
        "blocker": f"{domain} rows were generated from already-visible official snapshots, not a pre-target lock",
    }


def clean_pack_source(source: dict[str, Any], *, include_projection: bool = False) -> dict[str, Any]:
    cleaned = {
        "mode": str(source.get("mode", "official_snapshot_replay")),
        "pre_target_lock": source.get("pre_target_lock") is True,
        "target_hidden_until_scoring": source.get("target_hidden_until_scoring") is True,
        "training_sources": [str(item) for item in source.get("training_sources", []) if str(item)],
        "target_sources": [str(item) for item in source.get("target_sources", []) if str(item)],
    }
    if include_projection:
        cleaned.update(
            {
                "visible_target_projection_declared": source.get("visible_target_projection_declared") is True,
                "visible_projection_ids": [str(item) for item in source.get("visible_projection_ids", []) if str(item)],
                "target_projection_ids": [str(item) for item in source.get("target_projection_ids", []) if str(item)],
                "strict_source_separation_attested": source.get("strict_source_separation_attested") is True,
                "attestation_ref": str(source.get("attestation_ref") or ""),
                "source_separation_class": str(source.get("source_separation_class") or ""),
            }
        )
    return cleaned


def source_separation_blockers(source: dict[str, Any], requirements: dict[str, Any], domain: str) -> list[str]:
    blockers: list[str] = []
    allowed = {str(mode) for mode in requirements.get("required_source_separation_modes", ["prospective", "target_blind"])}
    if source.get("mode") not in allowed:
        blockers.append(f"SOURCE_SEPARATION_MODE_NOT_ALLOWED::{source.get('mode')}")
    if source.get("pre_target_lock") is not True:
        blockers.append("PRE_TARGET_LOCK_REQUIRED")
    if source.get("target_hidden_until_scoring") is not True:
        blockers.append("TARGET_HIDDEN_UNTIL_SCORING_REQUIRED")
    if source.get("declared_before_scoring") is not True:
        blockers.append("SOURCE_SEPARATION_NOT_DECLARED_BEFORE_SCORING")
    projection_required = domain == "physics"
    if projection_required and source.get("visible_target_projection_declared") is not True:
        blockers.append("VISIBLE_TARGET_PROJECTION_DECLARATION_REQUIRED")
    if source.get("strict_source_separation_attested") is not True:
        blockers.append("SOURCE_SEPARATION_ATTESTATION_REQUIRED")
    cleaned = clean_pack_source(source, include_projection=True)
    training_sources = cleaned["training_sources"]
    target_sources = cleaned["target_sources"]
    visible_projection_ids = cleaned["visible_projection_ids"]
    target_projection_ids = cleaned["target_projection_ids"]
    if projection_required and (not visible_projection_ids or not target_projection_ids):
        blockers.append("VISIBLE_AND_TARGET_PROJECTION_IDS_REQUIRED")
    if not training_sources or not target_sources:
        blockers.append("TRAINING_AND_TARGET_SOURCES_REQUIRED")
    if set(training_sources) & set(target_sources):
        blockers.append("TRAINING_TARGET_SOURCE_OVERLAP")
    return ordered_unique(blockers)


def residual_summary(rows: list[dict[str, Any]]) -> dict[str, float]:
    model = [
        float(row.get("model_residual_score", row.get("model_residual")))
        for row in rows
        if is_number(row.get("model_residual_score", row.get("model_residual")))
    ]
    comparator = [
        float(row.get("comparator_residual_score", row.get("comparator_residual")))
        for row in rows
        if is_number(row.get("comparator_residual_score", row.get("comparator_residual")))
    ]
    model_mean = sum(model) / len(model) if model else 0.0
    comparator_mean = sum(comparator) / len(comparator) if comparator else 0.0
    score_metric = any(row.get("residual_metric_id") == RESIDUAL_METRIC_ID for row in rows)
    return {
        "model": model_mean,
        "comparator": comparator_mean,
        "superiority_margin": comparator_mean - model_mean,
        "metric": RESIDUAL_METRIC_ID if score_metric else "mean_absolute_residual_v1",
    }


def uncertainty_interval(rows: list[dict[str, Any]], model_mean: float) -> list[float]:
    if any(row.get("residual_metric_id") == RESIDUAL_METRIC_ID for row in rows):
        residuals = [float(row["model_residual_score"]) for row in rows if is_number(row.get("model_residual_score"))]
        high = max([1.0, model_mean, *residuals], default=1.0)
        return [0.0, high]
    uncertainties = [float(row["uncertainty"]) for row in rows if is_number(row.get("uncertainty"))]
    residuals = [float(row["model_residual"]) for row in rows if is_number(row.get("model_residual"))]
    high = max([model_mean, *uncertainties, *residuals], default=0.0)
    return [0.0, high]


def preregistration_summary(domain: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    prereg_rows = [row.get("preregistration") for row in rows if isinstance(row.get("preregistration"), dict)]
    comparator_registered = [
        bool((row.get("comparator") or {}).get("pre_registered"))
        for row in prereg_rows
        if isinstance(row, dict)
    ]
    return {
        "domain": domain,
        "preregistered_before_scoring": bool(rows) and len(prereg_rows) == len(rows),
        "preregistered_before_target_snapshot_access": bool(rows)
        and all(row.get("declared_before_target_snapshot_access") is True for row in prereg_rows),
        "preregistration_ids": [
            str(row.get("preregistration_id")) for row in prereg_rows if str(row.get("preregistration_id") or "")
        ],
        "formula_total": len([row for row in prereg_rows if isinstance(row.get("formula"), dict)]),
        "comparator_total": len(comparator_registered),
        "comparator_preregistered_total": sum(1 for value in comparator_registered if value),
        "residual_metric_id": RESIDUAL_METRIC_ID,
        "policy": (
            "Formulas, comparators, residual metrics, uncertainty rules, negative controls, and falsifiers are "
            "declared in this artifact before row scoring, but the present CODATA text was not acquired under "
            "a pre-target hidden lock; this remains a blocker for promotion."
        ),
    }


def build_candidate_pack(domain: str, rows: list[dict[str, Any]], source: dict[str, Any], support_allowed: bool) -> dict[str, Any]:
    residuals = residual_summary(rows)
    pack_residuals: dict[str, Any] = dict(residuals)
    if domain != "physics":
        pack_residuals.pop("metric", None)
    controls = [
        {
            "control_id": str(row["negative_control_id"]),
            "description": str(row["negative_control_description"]),
            "rejected": row.get("negative_control_rejected") is True,
        }
        for row in rows
        if row.get("negative_control_id")
    ]
    if not controls:
        controls = [
            {
                "control_id": f"OFFICIAL-BATCH-{domain.upper()}-NO-ROWS",
                "description": "no official snapshot rows were available for a domain negative control",
                "rejected": False,
            }
        ]
    falsifiers = ordered_unique([str(row.get("falsifier")) for row in rows if str(row.get("falsifier") or "").strip()])
    if not falsifiers:
        falsifiers = [f"official {domain} snapshot rows missing; support remains blocked"]
    comparator_baseline = {
        "name": f"{domain} official-snapshot null/wrong-field negative controls",
        "prediction_rule": "Use each row's preregistered null, wrong-compound, or wrong-string control under the same residual metric.",
        "pre_registered": bool(rows)
        and all(
            (row.get("preregistration") or {}).get("comparator", {}).get("pre_registered") is True
            if isinstance(row.get("preregistration"), dict)
            else True
            for row in rows
        ),
    }
    if domain == "physics":
        comparator_baseline.update(
            {
                "preregistration_ref": PROTOCOL_REL,
                "residual_metric_id": RESIDUAL_METRIC_ID,
            }
        )
    pack = {
        "schema_id": grand_factory.EVIDENCE_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "capability_owner": CAPABILITY_OWNER,
        "evidence_pack_id": f"OC133-{domain.upper()}-OFFICIAL-SNAPSHOT-BATCH-CANDIDATE",
        "domain": domain,
        "source_separation": clean_pack_source(source, include_projection=domain == "physics"),
        "n": len(rows),
        "model_under_test": f"OC133 official-snapshot {domain} batch scorer over NIST/PubChem rows",
        "comparator_baseline": comparator_baseline,
        "uncertainty": {
            "metric": residuals["metric"] if domain == "physics" else "mean absolute residual across official snapshot tasks",
            "method": "deterministic official snapshot replay envelope; blocked unless target-blind/prospective source separation exists",
            "interval": uncertainty_interval(rows, residuals["model"]),
        },
        "residuals": pack_residuals,
        "negative_controls": controls,
        "falsifiers": falsifiers,
        "grand_toe_support_allowed": bool(support_allowed),
    }
    if domain == "physics":
        pack["preregistration"] = preregistration_summary(domain, rows)
    return pack


def physics_acquisition_requests(current_n: int, minimum_n: int) -> list[dict[str, Any]]:
    return [
        {
            "acquisition_id": "OC133-PHYSICS-CODATA-PROSPECTIVE-ALLASCII-001",
            "official_source": "NIST CODATA 2022 fundamental constants complete ASCII listing",
            "official_endpoint_url": "https://physics.nist.gov/cuu/Constants/Table/allascii.txt",
            "expected_local_snapshot_ref": "validation/_raw/physics_nist_constants_prospective_allascii.txt",
            "required_fields": [
                "Quantity",
                "Value",
                "Uncertainty",
                "Unit",
            ],
            "query_params": {},
            "no_send_lock": True,
            "minimum_rows_required": minimum_n,
            "current_official_batch_rows": current_n,
            "missing_reason": (
                "The pinned CODATA snapshot is usable for deterministic formula replay, but a prospective "
                "read-only acquisition/lock is still needed before any target-blind promotion claim."
            ),
        },
        {
            "acquisition_id": "OC133-PHYSICS-NIST-ASD-HYDROGEN-BALMER-001",
            "official_source": "NIST Atomic Spectra Database hydrogen Balmer lines",
            "official_endpoint_url": (
                "https://physics.nist.gov/cgi-bin/ASD/lines1.pl?spectra=H&limits_type=0&low_w=&upp_w="
                "&unit=1&de=0&format=3&line_out=0&remove_js=on&en_unit=1&output=0&page_size=50"
                "&show_obs_wl=1&show_calc_wl=1&show_wn=1"
            ),
            "expected_local_snapshot_ref": "validation/_raw/physics_nist_asd_hydrogen_balmer_lines_v1.tsv",
            "required_fields": [
                "observed_wavelength",
                "calculated_wavelength",
                "wavenumber",
            ],
            "query_params": {
                "spectra": "H",
                "format": "3",
                "show_obs_wl": "1",
                "show_calc_wl": "1",
                "show_wn": "1",
            },
            "no_send_lock": True,
            "minimum_rows_required": minimum_n,
            "current_official_batch_rows": 0,
            "runner_validation_note": (
                "Current official-readonly runner allowlist only covers physics.nist.gov/cuu/Constants; "
                "this ASD request is intentionally visible as a protocol blocker until the allowlist is extended."
            ),
            "missing_reason": "No independent NIST ASD target snapshot is pinned for a physics held-out spectral-line class.",
        },
    ]


def build_physics_acquisition_packet(physics_eval: dict[str, Any]) -> dict[str, Any]:
    rows = physics_acquisition_requests(int(physics_eval["candidate_n"]), int(physics_eval["minimum_n"]))
    packet = {
        "schema_id": PHYSICS_ACQUISITION_PACKET_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "generated_by": "tools/oc133_physics_chemistry_official_batch_factory.py",
        "domain": "physics",
        "source_lane": "official_batch",
        "no_send": True,
        "publish_allowed": False,
        "registry_write_allowed": False,
        "scientific_pass": False,
        "grand_toe_support_allowed": False,
        "candidate_n": physics_eval["candidate_n"],
        "minimum_n": physics_eval["minimum_n"],
        "missing_official_snapshot_total": len(rows),
        "missing_official_snapshots": rows,
        "acquisition_requests": rows,
        "protocol_blockers": [
            "PRE_TARGET_LOCK_REQUIRED",
            "TARGET_HIDDEN_UNTIL_SCORING_REQUIRED",
            "SOURCE_SEPARATION_ATTESTATION_REQUIRED",
            "INDEPENDENT_PHYSICS_TARGET_CLASS_REQUIRED",
        ],
        "runner": {
            "tool_ref": "tools/oc133_official_readonly_acquisition_runner.py",
            "example_dry_run_command": (
                f"python tools/oc133_official_readonly_acquisition_runner.py --packet {PHYSICS_ACQUISITION_PACKET_REL} --write"
            ),
            "example_execute_command": (
                "python tools/oc133_official_readonly_acquisition_runner.py "
                f"--packet {PHYSICS_ACQUISITION_PACKET_REL} --execute-network --allow-blocked-exit-zero"
            ),
        },
        "policy": "Acquisition requests pin official bytes only; they do not constitute empirical PASS or grand TOE support.",
    }
    packet["packet_sha256"] = sha256_object({k: v for k, v in packet.items() if k != "packet_sha256"})
    return packet


def build_tamper_tests(rows_by_domain: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    physics_rows = rows_by_domain.get("physics", [])
    first_physics = physics_rows[0] if physics_rows else None
    tamper_hash_changes = False
    if first_physics:
        mutated = dict(first_physics)
        observed = as_float(mutated.get("observed_value"), 0.0)
        mutated["observed_value"] = observed + max(abs(observed) * 1e-6, 1e-300)
        tamper_hash_changes = row_hash(mutated) != first_physics.get("row_hash")
    return [
        {
            "test_id": "physics-row-hash-target-tamper-rejected",
            "description": "mutating a physics target observed_value changes the canonical row hash",
            "passed": bool(first_physics) and tamper_hash_changes,
        },
        {
            "test_id": "physics-visible-projection-has-no-target-fields",
            "description": "visible CODATA projections contain only declared input constants, not target values or units",
            "passed": bool(physics_rows) and not any(visible_projection_has_target_leakage(row) for row in physics_rows),
        },
        {
            "test_id": "physics-comparator-preregistered-for-each-row",
            "description": "every physics row declares its comparator before scoring",
            "passed": bool(physics_rows)
            and all(
                isinstance(row.get("preregistration"), dict)
                and (row.get("preregistration") or {}).get("comparator", {}).get("pre_registered") is True
                and (row.get("preregistration") or {}).get("declared_before_scoring") is True
                for row in physics_rows
            ),
        },
        {
            "test_id": "physics-n-ge-20-when-codata-snapshot-exists",
            "description": "the pinned CODATA snapshot yields at least 20 deterministic physics formula rows when present",
            "passed": len(physics_rows) >= MINIMUM_N_DEFAULT,
        },
    ]


def domain_missing_official_snapshots(domain: str, current_n: int, minimum_n: int) -> list[dict[str, Any]]:
    pubchem_cids = ",".join(
        [
            "962",
            "297",
            "222",
            "280",
            "977",
            "947",
            "783",
            "702",
            "241",
            "180",
            "176",
            "5234",
            "5793",
            "2244",
            "2519",
            "784",
            "887",
            "1118",
            "5957",
            "23931",
        ]
    )
    if domain == "physics":
        acquisition_rows = physics_acquisition_requests(current_n, minimum_n)
        return [
            {
                "source_id": "physics_nist_constants_pre_target_lock_manifest_v1",
                "acquisition_id": acquisition_rows[0]["acquisition_id"],
                "official_url": acquisition_rows[0]["official_endpoint_url"],
                "official_endpoint_url": acquisition_rows[0]["official_endpoint_url"],
                "expected_local_snapshot_ref": acquisition_rows[0]["expected_local_snapshot_ref"],
                "required_local_snapshot_ref": "validation/_raw/physics_nist_constants_pre_target_lock_manifest_v1.json",
                "required_lock_ref": f"{OUTPUT_ROOT_REL}/locks/physics_nist_constants_pre_target_lock_manifest_v1.json",
                "minimum_rows_required": minimum_n,
                "current_official_batch_rows": current_n,
                "missing_reason": "CODATA constants snapshot is present, but no pre-target lock manifest proves target fields were hidden until scoring.",
            },
            {
                "source_id": "physics_nist_asd_hydrogen_balmer_lines_v1",
                "acquisition_id": acquisition_rows[1]["acquisition_id"],
                "official_url": acquisition_rows[1]["official_endpoint_url"],
                "official_endpoint_url": acquisition_rows[1]["official_endpoint_url"],
                "expected_local_snapshot_ref": acquisition_rows[1]["expected_local_snapshot_ref"],
                "required_local_snapshot_ref": "validation/_raw/physics_nist_asd_hydrogen_balmer_lines_v1.tsv",
                "required_lock_ref": f"{OUTPUT_ROOT_REL}/locks/physics_nist_asd_hydrogen_balmer_lines_v1.json",
                "minimum_rows_required": minimum_n,
                "current_official_batch_rows": 0,
                "missing_reason": "No NIST ASD spectral-line snapshot is available for an independent target-hidden physics blocker class.",
            },
        ]
    return [
        {
            "source_id": "chemistry_pubchem_20_compound_properties_v1",
            "official_url": (
                "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/"
                f"{pubchem_cids}/property/MolecularFormula,MolecularWeight,CanonicalSMILES,InChIKey/JSON"
            ),
            "required_local_snapshot_ref": "validation/_raw/chemistry_pubchem_20_compound_properties_v1.json",
            "required_lock_ref": f"{OUTPUT_ROOT_REL}/locks/chemistry_pubchem_20_compound_properties_v1.json",
            "minimum_rows_required": minimum_n,
            "current_official_batch_rows": current_n,
            "missing_reason": "Only the water PubChem snapshot is present; chemistry needs at least 20 target-hidden/prospective official rows.",
        },
        {
            "source_id": "chemistry_nist_webbook_water_gas_thermo_v1",
            "official_url": "https://webbook.nist.gov/cgi/cbook.cgi?ID=C7732185&Units=SI&Mask=1#Thermo-Gas",
            "required_local_snapshot_ref": "validation/_raw/chemistry_nist_webbook_water_gas_thermo_v1.html",
            "required_lock_ref": f"{OUTPUT_ROOT_REL}/locks/chemistry_nist_webbook_water_gas_thermo_v1.json",
            "minimum_rows_required": minimum_n,
            "current_official_batch_rows": 0,
            "missing_reason": "The current WebBook water page is a species landing page, not a thermochemistry target snapshot.",
        },
        {
            "source_id": "chemistry_nist_webbook_water_ir_spectrum_v1",
            "official_url": "https://webbook.nist.gov/cgi/cbook.cgi?ID=C7732185&Units=SI&Mask=80#IR-Spec",
            "required_local_snapshot_ref": "validation/_raw/chemistry_nist_webbook_water_ir_spectrum_v1.html",
            "required_lock_ref": f"{OUTPUT_ROOT_REL}/locks/chemistry_nist_webbook_water_ir_spectrum_v1.json",
            "minimum_rows_required": minimum_n,
            "current_official_batch_rows": 0,
            "missing_reason": "No NIST WebBook spectral target snapshot is available for chemistry spectral blocker rows.",
        },
        {
            "source_id": "chemistry_nist_kinetics_water_v1",
            "official_url": "https://kinetics.nist.gov/kinetics/rpSearch?cas=7732185",
            "required_local_snapshot_ref": "validation/_raw/chemistry_nist_kinetics_water_v1.html",
            "required_lock_ref": f"{OUTPUT_ROOT_REL}/locks/chemistry_nist_kinetics_water_v1.json",
            "minimum_rows_required": minimum_n,
            "current_official_batch_rows": 0,
            "missing_reason": "No NIST kinetics target snapshot is available for chemistry kinetic/equilibrium blocker rows.",
        },
    ]


def evaluate_domain(
    domain: str,
    rows: list[dict[str, Any]],
    source: dict[str, Any],
    local_blockers: list[str],
    requirements: dict[str, Any],
    pack_rel: str,
) -> dict[str, Any]:
    minimum_n = int(requirements.get("minimum_per_domain_n", MINIMUM_N_DEFAULT))
    blockers = list(local_blockers)
    blockers.extend(source_separation_blockers(source, requirements, domain))
    if len(rows) < minimum_n:
        blockers.append(f"N_BELOW_MINIMUM::{domain}::{len(rows)}/{minimum_n}")
    if not rows:
        blockers.append(f"NO_OFFICIAL_BATCH_ROWS::{domain}")
    if any(row.get("negative_control_rejected") is not True for row in rows):
        blockers.append(f"NEGATIVE_CONTROLS_NOT_ALL_REJECTED::{domain}")
    if any(row.get("residual_within_uncertainty") is not True for row in rows):
        blockers.append(f"RESIDUALS_OUTSIDE_UNCERTAINTY::{domain}")
    if any(not row_hash_valid(row) for row in rows):
        blockers.append(f"ROW_HASH_TAMPER_DETECTED::{domain}")
    if domain == "physics":
        if any(visible_projection_has_target_leakage(row) for row in rows):
            blockers.append("PHYSICS_VISIBLE_PROJECTION_TARGET_LEAKAGE")
        if any(not isinstance(row.get("preregistration"), dict) for row in rows):
            blockers.append("PHYSICS_PREREGISTRATION_MISSING")
        if any(
            (row.get("preregistration") or {}).get("comparator", {}).get("pre_registered") is not True
            for row in rows
            if isinstance(row.get("preregistration"), dict)
        ):
            blockers.append("PHYSICS_COMPARATOR_NOT_PREREGISTERED")

    candidate_true = build_candidate_pack(domain, rows, source, support_allowed=True)
    gate_failures_if_true = grand_factory.pack_failure_reasons(candidate_true, requirements)
    support_allowed = not ordered_unique(blockers) and not gate_failures_if_true
    pack = build_candidate_pack(domain, rows, source, support_allowed=support_allowed)
    gate_failures = grand_factory.pack_failure_reasons(pack, requirements)
    blockers = ordered_unique([*blockers, *gate_failures])
    pack_sha = sha256_object(pack)
    return {
        "domain": domain,
        "candidate_pack": pack,
        "candidate_pack_ref": pack_rel,
        "candidate_pack_sha256": pack_sha,
        "candidate_pack_hash_policy": PACK_HASH_POLICY,
        "candidate_n": len(rows),
        "minimum_n": minimum_n,
        "missing_n": max(0, minimum_n - len(rows)),
        "grand_eligible_n": len(rows) if support_allowed else 0,
        "source_separation": source,
        "source_separation_for_pack": clean_pack_source(source, include_projection=domain == "physics"),
        "residuals": pack["residuals"],
        "negative_control_total": len(pack["negative_controls"]),
        "falsifier_total": len(pack["falsifiers"]),
        "candidate_pack_valid_under_current_grand_gate": not gate_failures,
        "candidate_pack_grand_gate_failures": gate_failures,
        "blockers": blockers,
        "open_blocker_total": len(blockers),
        "missing_official_snapshots": domain_missing_official_snapshots(domain, len(rows), minimum_n),
        "grand_toe_support_allowed": support_allowed,
        "status": "READY_FOR_PARENT_REGISTRY_REVIEW" if support_allowed else "BLOCKED_ACQUISITION_READY_NO_SEND",
    }


def build_payload(
    root: Path | None = None,
    *,
    source_separation_overrides: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    root = (root or repo_root()).resolve()
    requirements, requirement_blockers = load_requirements(root)
    manifest = load_manifest(root)
    source_separation_overrides = source_separation_overrides or {}

    physics_rows, physics_blockers, physics_snapshot = build_physics_rows(root, PHYSICS_NIST_CONSTANTS_REF, manifest)
    chemistry_rows, chemistry_blockers, chemistry_snapshots = build_chemistry_rows(root, manifest)

    physics_source = source_separation_overrides.get("physics") or default_source_separation("physics", physics_rows)
    chemistry_source = source_separation_overrides.get("chemistry") or default_source_separation("chemistry", chemistry_rows)

    physics_eval = evaluate_domain(
        "physics",
        physics_rows,
        physics_source,
        [*requirement_blockers, *physics_blockers],
        requirements,
        PHYSICS_PACK_REL,
    )
    chemistry_eval = evaluate_domain(
        "chemistry",
        chemistry_rows,
        chemistry_source,
        [*requirement_blockers, *chemistry_blockers],
        requirements,
        CHEMISTRY_PACK_REL,
    )
    domain_evals = [physics_eval, chemistry_eval]
    all_blockers = ordered_unique([blocker for row in domain_evals for blocker in row["blockers"]])
    snapshot_records = [physics_snapshot, *chemistry_snapshots]
    tamper_tests = build_tamper_tests({"physics": physics_rows, "chemistry": chemistry_rows})
    physics_acquisition_packet = build_physics_acquisition_packet(physics_eval)

    tasks = {
        "schema_id": TASKS_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "generated_by": "tools/oc133_physics_chemistry_official_batch_factory.py",
        "requirements_ref": REQUIREMENTS_REL,
        "manifest_ref": MANIFEST_REL,
        "snapshot_hash_policy": SNAPSHOT_HASH_POLICY,
        "row_hash_policy": ROW_HASH_POLICY,
        "snapshot_records": snapshot_records,
        "tamper_tests": tamper_tests,
        "domains": [
            {
                "domain": "physics",
                "row_total": len(physics_rows),
                "rows": physics_rows,
                "blockers": physics_eval["blockers"],
            },
            {
                "domain": "chemistry",
                "row_total": len(chemistry_rows),
                "rows": chemistry_rows,
                "blockers": chemistry_eval["blockers"],
            },
        ],
    }
    protocol_domains = [
        {
            "domain": row["domain"],
            "status": row["status"],
            "candidate_pack_ref": row["candidate_pack_ref"],
            "candidate_pack_sha256": row["candidate_pack_sha256"],
            "candidate_n": row["candidate_n"],
            "grand_eligible_n": row["grand_eligible_n"],
            "minimum_n": row["minimum_n"],
            "missing_n": row["missing_n"],
            "source_separation_for_pack": row["source_separation_for_pack"],
            "candidate_pack_grand_gate_failures": row["candidate_pack_grand_gate_failures"],
            "blockers": row["blockers"],
            "missing_official_snapshots": row["missing_official_snapshots"],
            "required_protocol_steps": [
                "freeze official NIST/PubChem source snapshots and LF-normalized hashes",
                "declare model, comparator baseline, residual metric, uncertainty, negative controls, and falsifiers before scoring",
                "separate visible training/source-development fields from target fields before scoring",
                "keep target fields hidden until scoring or use a prospective official snapshot",
                "require at least the configured minimum N per domain",
                "run the current grand empirical gate before registry integration",
            ],
        }
        for row in domain_evals
    ]
    protocol = {
        "schema_id": PROTOCOL_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "blocker_id": BLOCKER_ID,
        "requirements_ref": REQUIREMENTS_REL,
        "evidence_schema_ref": EVIDENCE_SCHEMA_REL,
        "tasks_ref": TASKS_REL,
        "report_ref": REPORT_REL,
        "candidate_pack_refs": [PHYSICS_PACK_REL, CHEMISTRY_PACK_REL],
        "acquisition_packet_refs": [PHYSICS_ACQUISITION_PACKET_REL],
        "minimum_per_domain_n": int(requirements.get("minimum_per_domain_n", MINIMUM_N_DEFAULT)),
        "domains": protocol_domains,
        "tamper_tests": tamper_tests,
        "open_blocker_total": len(all_blockers),
        "blockers": all_blockers,
        "grand_toe_support_allowed": all(row["grand_toe_support_allowed"] for row in domain_evals),
        "no_send_locks": {
            "no_send": True,
            "publish_allowed": False,
            "journal_submissions_allowed": False,
            "registry_integration_allowed": False,
        },
        "no_fabricated_success_policy": NO_SEND_POLICY,
    }
    protocol["protocol_sha256"] = sha256_object({k: v for k, v in protocol.items() if k != "protocol_sha256"})

    report_domains = [
        {
            "domain": row["domain"],
            "status": row["status"],
            "candidate_pack_ref": row["candidate_pack_ref"],
            "candidate_pack_sha256": row["candidate_pack_sha256"],
            "candidate_n": row["candidate_n"],
            "grand_eligible_n": row["grand_eligible_n"],
            "minimum_n": row["minimum_n"],
            "missing_n": row["missing_n"],
            "residuals": row["residuals"],
            "negative_control_total": row["negative_control_total"],
            "falsifier_total": row["falsifier_total"],
            "candidate_pack_valid_under_current_grand_gate": row["candidate_pack_valid_under_current_grand_gate"],
            "candidate_pack_grand_gate_failures": row["candidate_pack_grand_gate_failures"],
            "open_blocker_total": row["open_blocker_total"],
            "blockers": row["blockers"],
            "missing_official_snapshots": row["missing_official_snapshots"],
            "grand_toe_support_allowed": row["grand_toe_support_allowed"],
        }
        for row in domain_evals
    ]
    report = {
        "schema_id": REPORT_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "blocker_id": BLOCKER_ID,
        "generated_by": "tools/oc133_physics_chemistry_official_batch_factory.py",
        "protocol_ref": PROTOCOL_REL,
        "tasks_ref": TASKS_REL,
        "requirements_ref": REQUIREMENTS_REL,
        "manifest_ref": MANIFEST_REL,
        "candidate_pack_total": len(domain_evals),
        "valid_candidate_pack_total": sum(1 for row in domain_evals if row["candidate_pack_valid_under_current_grand_gate"]),
        "blocked_candidate_pack_total": sum(1 for row in domain_evals if not row["candidate_pack_valid_under_current_grand_gate"]),
        "minimum_per_domain_n": int(requirements.get("minimum_per_domain_n", MINIMUM_N_DEFAULT)),
        "open_blocker_total": len(all_blockers),
        "blockers": all_blockers,
        "domains": report_domains,
        "snapshot_records": snapshot_records,
        "tamper_tests": tamper_tests,
        "acquisition_packet_refs": [PHYSICS_ACQUISITION_PACKET_REL],
        "physics_acquisition_request_total": physics_acquisition_packet["missing_official_snapshot_total"],
        "artifact_hashes": {
            "physics_candidate_pack_sha256": physics_eval["candidate_pack_sha256"],
            "chemistry_candidate_pack_sha256": chemistry_eval["candidate_pack_sha256"],
            "physics_acquisition_packet_sha256": physics_acquisition_packet["packet_sha256"],
            "tasks_sha256": sha256_object(tasks),
            "protocol_sha256": protocol["protocol_sha256"],
        },
        "grand_toe_support_allowed": all(row["grand_toe_support_allowed"] for row in domain_evals),
        "verdict": (
            "READY_FOR_PARENT_REGISTRY_REVIEW"
            if all(row["grand_toe_support_allowed"] for row in domain_evals)
            else "BLOCKED_ACQUISITION_READY_NO_SEND"
        ),
        "no_send": True,
        "publish_allowed": False,
        "journal_submissions_allowed": False,
        "registry_integration_allowed": False,
        "no_fabricated_success_policy": NO_SEND_POLICY,
    }
    report["report_sha256"] = sha256_object({k: v for k, v in report.items() if k != "report_sha256"})
    readme = render_readme(report)
    return {
        "tasks": tasks,
        "protocol": protocol,
        "report": report,
        "readme": readme,
        PHYSICS_PACK_REL: physics_eval["candidate_pack"],
        CHEMISTRY_PACK_REL: chemistry_eval["candidate_pack"],
        PHYSICS_ACQUISITION_PACKET_REL: physics_acquisition_packet,
    }


def render_readme(report: dict[str, Any]) -> str:
    lines = [
        "# Physics/Chemistry Official Batch Factory",
        "",
        f"Verdict: `{report['verdict']}`",
        f"Grand TOE support allowed: `{str(report['grand_toe_support_allowed']).lower()}`",
        f"Open blockers: `{report['open_blocker_total']}`",
        "",
        "| Domain | Candidate N | Eligible N | Minimum N | Gate valid | Status |",
        "| --- | ---: | ---: | ---: | --- | --- |",
    ]
    for row in report["domains"]:
        lines.append(
            f"| `{row['domain']}` | `{row['candidate_n']}` | `{row['grand_eligible_n']}` | "
            f"`{row['minimum_n']}` | `{str(row['candidate_pack_valid_under_current_grand_gate']).lower()}` | `{row['status']}` |"
        )
    lines.extend(["", "No-send locks are active. Candidate packs in this directory must not be registered while blocked.", ""])
    lines.extend(
        [
            "Physics acquisition packet:",
            f"- `{PHYSICS_ACQUISITION_PACKET_REL}`",
            "",
        ]
    )
    lines.append("## Missing Official Snapshots")
    for domain in report["domains"]:
        lines.append("")
        lines.append(f"### {domain['domain'].title()}")
        for item in domain["missing_official_snapshots"]:
            lines.append(f"- `{item['source_id']}` -> `{item['required_local_snapshot_ref']}`")
    lines.extend(["", "## Open Blockers"])
    if report["blockers"]:
        lines.extend(f"- `{item}`" for item in report["blockers"])
    else:
        lines.append("- `none`")
    return "\n".join(lines) + "\n"


def write_outputs(root: Path | None = None) -> dict[str, Any]:
    root = (root or repo_root()).resolve()
    payload = build_payload(root)
    write_json(root / PHYSICS_PACK_REL, payload[PHYSICS_PACK_REL])
    write_json(root / CHEMISTRY_PACK_REL, payload[CHEMISTRY_PACK_REL])
    write_json(root / PHYSICS_ACQUISITION_PACKET_REL, payload[PHYSICS_ACQUISITION_PACKET_REL])
    write_json(root / TASKS_REL, payload["tasks"])
    write_json(root / PROTOCOL_REL, payload["protocol"])
    write_json(root / REPORT_REL, payload["report"])
    write_text(root / README_REL, payload["readme"])
    return payload["report"]


def check_stored(root: Path | None = None) -> list[str]:
    root = (root or repo_root()).resolve()
    expected = build_payload(root)
    checks = [
        (PHYSICS_PACK_REL, expected[PHYSICS_PACK_REL]),
        (CHEMISTRY_PACK_REL, expected[CHEMISTRY_PACK_REL]),
        (PHYSICS_ACQUISITION_PACKET_REL, expected[PHYSICS_ACQUISITION_PACKET_REL]),
        (TASKS_REL, expected["tasks"]),
        (PROTOCOL_REL, expected["protocol"]),
        (REPORT_REL, expected["report"]),
    ]
    failures: list[str] = []
    for rel_path, expected_payload in checks:
        path = root / rel_path
        if not path.exists():
            failures.append(f"missing::{rel_path}")
            continue
        try:
            actual = read_json(path)
        except Exception as exc:
            failures.append(f"parse_error::{rel_path}::{exc.__class__.__name__}")
            continue
        if actual != expected_payload:
            failures.append(f"mismatch::{rel_path}")
    readme_path = root / README_REL
    if not readme_path.exists():
        failures.append(f"missing::{README_REL}")
    elif readme_path.read_text(encoding="utf-8") != expected["readme"]:
        failures.append(f"mismatch::{README_REL}")
    return failures


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build strict physics/chemistry official snapshot batch artifacts.")
    parser.add_argument("--root", default=str(repo_root()), help="repository root")
    parser.add_argument("--write", action="store_true", help="write artifacts under the official_batch output directory")
    parser.add_argument("--check", action="store_true", help="check stored artifacts against deterministic output")
    parser.add_argument("--allow-blocked-exit-zero", action="store_true", help="return zero even when the report is blocked")
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
        print(
            json.dumps(
                {
                    "status": "ok",
                    "checked": [
                        PHYSICS_PACK_REL,
                        CHEMISTRY_PACK_REL,
                        PHYSICS_ACQUISITION_PACKET_REL,
                        TASKS_REL,
                        PROTOCOL_REL,
                        REPORT_REL,
                        README_REL,
                    ],
                },
                indent=2,
            )
        )
        return 0
    report = write_outputs(root) if args.write else build_payload(root)["report"]
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["grand_toe_support_allowed"] is not True and not args.allow_blocked_exit_zero:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
