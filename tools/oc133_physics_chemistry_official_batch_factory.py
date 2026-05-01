from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
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
OFFICIAL_ACQUISITION_RUN_ROOT_REL = "validation/heldout/acquisition_runs/oc133_official_readonly"
PHYSICS_CODATA_ACQUISITION_ID = "OC133-PHYSICS-CODATA-PROSPECTIVE-ALLASCII-001"
PHYSICS_ASD_ACQUISITION_ID = "OC133-PHYSICS-NIST-ASD-HYDROGEN-BALMER-001"
PHYSICS_CODATA_ACQUIRED_SNAPSHOT_REL = (
    f"{OFFICIAL_ACQUISITION_RUN_ROOT_REL}/snapshots/{PHYSICS_CODATA_ACQUISITION_ID}.txt"
)
PHYSICS_CODATA_ACQUIRED_METADATA_REL = (
    f"{OFFICIAL_ACQUISITION_RUN_ROOT_REL}/snapshots/{PHYSICS_CODATA_ACQUISITION_ID}.metadata.json"
)
PHYSICS_CODATA_ACQUIRED_LOCK_REL = f"{OFFICIAL_ACQUISITION_RUN_ROOT_REL}/locks/{PHYSICS_CODATA_ACQUISITION_ID}.lock.json"
PHYSICS_CODATA_ACQUIRED_ORDER_REL = (
    f"{OFFICIAL_ACQUISITION_RUN_ROOT_REL}/order_records/{PHYSICS_CODATA_ACQUISITION_ID}.order.json"
)
PHYSICS_ASD_ACQUIRED_SNAPSHOT_REL = f"{OFFICIAL_ACQUISITION_RUN_ROOT_REL}/snapshots/{PHYSICS_ASD_ACQUISITION_ID}.tsv"

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
PHYSICS_SOURCE_LOCK_SCHEMA_ID = "OC133_PHYSICS_OFFICIAL_BATCH_SOURCE_SEPARATION_LOCK_v1"
PHYSICS_SOURCE_LOCK_EVENT_SEQUENCE = (
    "source_snapshot_locked",
    "source_separation_declared",
    "visible_projection_locked",
    "prediction_materialized",
    "target_projection_unsealed_for_scoring",
    "scoring_started",
)
PROSPECTIVE_LOCK_METADATA_SCHEMA_ID = "OC133_OFFICIAL_READONLY_PROSPECTIVE_LOCK_METADATA_v1"
PHYSICS_PROSPECTIVE_LOCK_EVENT_SEQUENCE = PHYSICS_SOURCE_LOCK_EVENT_SEQUENCE
PHYSICS_PROSPECTIVE_MODEL_FAMILY = "OC133 physics official-batch deterministic visible-field scorer"
PHYSICS_PROSPECTIVE_COMPARATOR_BASELINE = {
    "name": "physics official-batch preregistered same-target formula ablation baseline",
    "prediction_rule": (
        "For each declared CODATA target, evaluate the preregistered target formula after replacing the first "
        "visible ingredient with dimensionless 1.0; score that same-target ablation under the same residual metric."
    ),
    "pre_registered": True,
    "residual_metric_id": RESIDUAL_METRIC_ID,
}
PHYSICS_PROSPECTIVE_SCORING_POLICY = {
    "residual_metric_id": RESIDUAL_METRIC_ID,
    "scoring_started": False,
    "scoring_started_at": "",
    "target_projection_unsealed_for_scoring": False,
    "target_projection_unsealed_for_scoring_at": "",
    "prediction_materialization_required_before_scoring": True,
    "target_projection_read_before_prediction_materialization": False,
    "scientific_pass": False,
}
PHYSICS_PROSPECTIVE_TARGET_SPLIT_POLICY = {
    "target_hidden_until_scoring": True,
    "target_values_in_metadata_allowed": False,
    "target_value_fields_excluded": [
        "target_quantity",
        "observed_value",
        "target_unit",
        "official_uncertainty",
        "uncertainty",
    ],
    "target_projection_fields_excluded": [
        "target_quantity",
        "observed_value",
        "target_unit",
        "official_uncertainty",
        "uncertainty",
        "target_source",
        "target_projection",
        "target_projection_id",
        "target_hash",
        "observed_value_text",
        "official_uncertainty_text",
        "model_residual",
        "model_residual_score",
        "residual_within_uncertainty",
    ],
    "policy": "Metadata may name excluded target fields but must not carry target values.",
}
PHYSICS_PROSPECTIVE_NO_SEND_LOCKS = {
    "no_send": True,
    "publish_allowed": False,
    "push_allowed": False,
    "public_release_action_allowed": False,
    "registry_write_allowed": False,
    "journal_submissions_allowed": False,
}
PHYSICS_PROSPECTIVE_METADATA_FORBIDDEN_VALUE_KEYS = {
    "target_value",
    "target_values",
    "target_observed_value",
    "target_observed_value_text",
    "observed_value",
    "observed_value_text",
    "official_uncertainty",
    "official_uncertainty_text",
    "target_hash",
    "target_projection",
    "target_fields",
    "ground_truth",
}

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

PHYSICS_SCORING_TARGET_FIELDS = (
    "target_quantity",
    "observed_value",
    "target_unit",
    "official_uncertainty",
    "uncertainty",
)

PHYSICS_PREDICTION_FORBIDDEN_FIELDS = (
    *PHYSICS_SCORING_TARGET_FIELDS,
    "target_source",
    "target_projection",
    "target_projection_id",
    "target_hash",
    "observed_value_text",
    "official_uncertainty_text",
    "model_residual",
    "model_residual_score",
    "residual_within_uncertainty",
)

PHYSICS_FORBIDDEN_COMPARATOR_TEXT = (
    "zero-value",
    "zero baseline",
    "null baseline",
    " null ",
    "wrong-field",
    "wrong field",
    "wrong-string",
    "wrong string",
    "wrong-compound",
    "wrong compound",
)

PHYSICS_STALE_LOCK_BLOCKER_TEXT = (
    "not acquired under a pre-target hidden lock",
    "not independently pre-target locked",
    "already visible before this run",
    "remains a blocker for promotion",
    "no pre-target lock manifest proves",
)


def repo_root() -> Path:
    return ROOT


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_object(payload: Any) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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


def parse_iso_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed


def timestamp_plus_seconds(value: str, seconds: int) -> str:
    parsed = parse_iso_timestamp(value)
    if parsed is None:
        parsed = datetime.fromisoformat("2026-04-28T00:00:00+00:00")
    return (parsed + timedelta(seconds=seconds)).isoformat().replace("+00:00", "Z")


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


def acquisition_record_hash_valid(order_record: dict[str, Any]) -> bool:
    return order_record.get("order_record_sha256") == sha256_object(
        {key: value for key, value in order_record.items() if key != "order_record_sha256"}
    )


def successful_physics_codata_acquisition(root: Path) -> tuple[dict[str, Any] | None, list[str]]:
    snapshot_path = resolve_under_root(root, PHYSICS_CODATA_ACQUIRED_SNAPSHOT_REL)
    metadata_path = resolve_under_root(root, PHYSICS_CODATA_ACQUIRED_METADATA_REL)
    lock_path = resolve_under_root(root, PHYSICS_CODATA_ACQUIRED_LOCK_REL)
    order_path = resolve_under_root(root, PHYSICS_CODATA_ACQUIRED_ORDER_REL)
    if not (snapshot_path.is_file() and metadata_path.is_file() and lock_path.is_file() and order_path.is_file()):
        return None, ["PHYSICS_PROSPECTIVE_CODATA_ACQUISITION_MISSING"]
    try:
        metadata = read_json(metadata_path)
        lock = read_json(lock_path)
        order_record = read_json(order_path)
        source_bytes = snapshot_path.read_bytes()
    except Exception as exc:
        return None, [f"PHYSICS_PROSPECTIVE_CODATA_ACQUISITION_PARSE_FAILED::{exc.__class__.__name__}"]
    failures: list[str] = []
    source_bytes_sha = sha256_bytes(source_bytes)
    text_sha = sha256_file_text(snapshot_path)
    if metadata.get("status") != "ACQUIRED_READONLY" or lock.get("http_status") not in range(200, 300):
        failures.append("PHYSICS_PROSPECTIVE_CODATA_ACQUISITION_NOT_SUCCESSFUL")
    for payload_name, payload in (("metadata", metadata), ("lock", lock), ("order_record", order_record)):
        locks = payload.get("locks") if isinstance(payload, dict) else {}
        if not isinstance(locks, dict) or locks.get("no_send") is not True:
            failures.append(f"PHYSICS_PROSPECTIVE_CODATA_NO_SEND_LOCK_MISSING::{payload_name}")
        for key in ("publish_allowed", "push_allowed", "journal_submissions_allowed"):
            if locks.get(key) is not False:
                failures.append(f"PHYSICS_PROSPECTIVE_CODATA_PUBLIC_ACTION_LOCK_INVALID::{payload_name}::{key}")
    if lock.get("snapshot_ref") != PHYSICS_CODATA_ACQUIRED_SNAPSHOT_REL:
        failures.append("PHYSICS_PROSPECTIVE_CODATA_LOCK_SNAPSHOT_REF_MISMATCH")
    if lock.get("source_bytes_sha256") != source_bytes_sha or metadata.get("source_bytes_sha256") != source_bytes_sha:
        failures.append("PHYSICS_PROSPECTIVE_CODATA_SOURCE_BYTES_HASH_MISMATCH")
    if lock.get("snapshot_sha256") != source_bytes_sha or metadata.get("sha256") != text_sha:
        failures.append("PHYSICS_PROSPECTIVE_CODATA_SNAPSHOT_HASH_MISMATCH")
    if lock.get("order_record_ref") != PHYSICS_CODATA_ACQUIRED_ORDER_REL:
        failures.append("PHYSICS_PROSPECTIVE_CODATA_LOCK_ORDER_REF_MISMATCH")
    if metadata.get("order_record_ref") != PHYSICS_CODATA_ACQUIRED_ORDER_REL:
        failures.append("PHYSICS_PROSPECTIVE_CODATA_METADATA_ORDER_REF_MISMATCH")
    if lock.get("order_record_sha256") != order_record.get("order_record_sha256"):
        failures.append("PHYSICS_PROSPECTIVE_CODATA_LOCK_ORDER_HASH_MISMATCH")
    if metadata.get("order_record_sha256") != order_record.get("order_record_sha256"):
        failures.append("PHYSICS_PROSPECTIVE_CODATA_METADATA_ORDER_HASH_MISMATCH")
    if not acquisition_record_hash_valid(order_record):
        failures.append("PHYSICS_PROSPECTIVE_CODATA_ORDER_RECORD_HASH_INVALID")
    sequence = lock.get("pre_target_sequence_proof")
    if not isinstance(sequence, dict):
        failures.append("PHYSICS_PROSPECTIVE_CODATA_SEQUENCE_PROOF_MISSING")
        sequence = {}
    required_sequence = {
        "source_snapshot_locked_before_scoring": True,
        "source_snapshot_pre_target_lock": True,
        "target_hidden_until_scoring": True,
        "target_projection_unsealed_for_scoring": False,
        "scoring_started": False,
        "prediction_materialization_required_before_scoring": True,
        "target_projection_read_before_prediction_materialization": False,
    }
    for key, expected in required_sequence.items():
        if sequence.get(key) is not expected:
            failures.append(f"PHYSICS_PROSPECTIVE_CODATA_SEQUENCE_PROOF_INVALID::{key}")
    acquired_at = str(order_record.get("acquired_at_utc") or "")
    if parse_iso_timestamp(acquired_at) is None:
        failures.append("PHYSICS_PROSPECTIVE_CODATA_ACQUIRED_AT_INVALID")
    if failures:
        return None, ordered_unique(failures)
    return (
        {
            "source_id": "physics_nist_constants_prospective_allascii",
            "source_ref": PHYSICS_CODATA_ACQUIRED_SNAPSHOT_REL,
            "official_url": "https://physics.nist.gov/cuu/Constants/Table/allascii.txt",
            "exists": True,
            "byte_count": len(lf_bytes(snapshot_path)),
            "source_bytes_byte_count": len(source_bytes),
            "sha256": text_sha,
            "source_bytes_sha256": source_bytes_sha,
            "sha256_expected": text_sha,
            "sha256_match": True,
            "hash_policy": SNAPSHOT_HASH_POLICY,
            "acquisition_id": PHYSICS_CODATA_ACQUISITION_ID,
            "acquisition_lock_ref": PHYSICS_CODATA_ACQUIRED_LOCK_REL,
            "acquisition_lock_sha256": sha256_file_text(lock_path),
            "acquisition_metadata_ref": PHYSICS_CODATA_ACQUIRED_METADATA_REL,
            "acquisition_metadata_sha256": sha256_file_text(metadata_path),
            "acquisition_order_record_ref": PHYSICS_CODATA_ACQUIRED_ORDER_REL,
            "acquisition_order_record_sha256": str(order_record.get("order_record_sha256") or ""),
            "acquisition_order_record_file_sha256": sha256_file_text(order_path),
            "acquired_at_utc": acquired_at,
            "pre_target_sequence_proof": sequence,
        },
        [],
    )


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


def physics_visible_projection(
    spec: PhysicsFormula,
    constants: dict[str, NistConstant],
    *,
    snapshot_ref: str = PHYSICS_NIST_CONSTANTS_REF,
) -> dict[str, Any]:
    return {
        "projection_id": f"{spec.task_id}-VISIBLE-PROJECTION-v1",
        "source_ref": snapshot_ref,
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


def physics_target_projection(
    spec: PhysicsFormula,
    target: NistConstant,
    *,
    snapshot_ref: str = PHYSICS_NIST_CONSTANTS_REF,
) -> dict[str, Any]:
    return {
        "projection_id": f"{spec.task_id}-TARGET-PROJECTION-v1",
        "source_ref": snapshot_ref,
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


def physics_prediction_materialization(
    spec: PhysicsFormula,
    visible: dict[str, Any],
    predicted_value: float,
) -> dict[str, Any]:
    prediction = {
        "materialization_id": f"{spec.task_id}-PREDICTION-MATERIALIZATION-v1",
        "task_id": spec.task_id,
        "visible_projection_id": visible["projection_id"],
        "visible_projection_hash": visible["projection_hash"],
        "formula": spec.formula,
        "ingredients": list(spec.ingredients),
        "predicted_value": predicted_value,
        "hash_excludes": list(PHYSICS_PREDICTION_FORBIDDEN_FIELDS),
    }
    prediction["prediction_hash"] = sha256_object(
        {k: v for k, v in prediction.items() if k != "prediction_hash"}
    )
    return prediction


def physics_target_projection_lock(
    spec: PhysicsFormula,
    visible: dict[str, Any],
    prediction: dict[str, Any],
    target: dict[str, Any],
) -> dict[str, Any]:
    lock = {
        "lock_id": f"{spec.task_id}-TARGET-PROJECTION-LOCK-v1",
        "visible_projection_id": visible["projection_id"],
        "visible_projection_hash": visible["projection_hash"],
        "prediction_materialization_id": prediction["materialization_id"],
        "prediction_materialization_hash": prediction["prediction_hash"],
        "target_projection_id": target["projection_id"],
        "target_projection_hash": target["target_hash"],
        "prediction_materialized_before_target_projection": True,
        "target_projection_hidden_until_scoring": True,
        "target_projection_depends_on_prediction_hash": True,
        "scoring_target_fields": list(PHYSICS_SCORING_TARGET_FIELDS),
        "visible_target_fields_excluded": list(PHYSICS_SCORING_TARGET_FIELDS),
        "closure_policy": "artifact existence alone does not verify pre-target source lock",
        "lock_hash_policy": "sha256 over canonical projection-lock JSON excluding lock_hash",
    }
    lock["lock_hash"] = sha256_object({k: v for k, v in lock.items() if k != "lock_hash"})
    return lock


def physics_projection_declaration(
    spec: PhysicsFormula,
    visible: dict[str, Any],
    target: dict[str, Any],
    projection_lock: dict[str, Any],
    *,
    source_snapshot_pre_target_lock: bool = False,
) -> dict[str, Any]:
    declaration = {
        "declaration_id": f"{spec.task_id}-PROJECTION-DECLARATION-v1",
        "visible_projection_id": visible["projection_id"],
        "target_projection_id": target["projection_id"],
        "target_projection_lock_id": projection_lock["lock_id"],
        "declared_before_scoring": True,
        "prediction_materialized_before_target_projection": True,
        "target_projection_hidden_until_scoring": True,
        "source_snapshot_pre_target_lock": bool(source_snapshot_pre_target_lock),
        "declared_before_target_snapshot_access": bool(source_snapshot_pre_target_lock),
        "target_hidden_until_scoring": True,
        "separation_class": (
            "prospective_source_snapshot_target_projection_lock"
            if source_snapshot_pre_target_lock
            else "target_projection_locked_source_snapshot_posthoc"
        ),
    }
    if not source_snapshot_pre_target_lock:
        declaration["promotion_blocker"] = (
            "row-level target projection is locked and auditable, but the local CODATA source snapshot "
            "was already visible before this run"
        )
    return declaration


def physics_same_target_ablation_comparator(
    spec: PhysicsFormula,
    values: dict[str, float],
) -> dict[str, Any]:
    ablated_quantity = spec.ingredients[0]
    ablated_values = dict(values)
    ablated_values[ablated_quantity] = 1.0
    prediction = float(spec.predictor(ablated_values))
    return {
        "comparator_id": f"{spec.task_id}-SAME-TARGET-FORMULA-ABLATION-v1",
        "kind": "same_target_formula_ablation",
        "name": "same-target formula ablation baseline",
        "target_quantity": spec.target,
        "prediction_rule": (
            "evaluate the declared target formula after replacing the first visible ingredient with dimensionless 1.0"
        ),
        "ablated_quantity": ablated_quantity,
        "ablated_value": 1.0,
        "prediction_value": prediction,
        "pre_registered": True,
        "residual_metric_id": RESIDUAL_METRIC_ID,
    }


def physics_preregistration(
    spec: PhysicsFormula,
    tolerance: float,
    *,
    declared_before_target_snapshot_access: bool = False,
    comparator: dict[str, Any] | None = None,
) -> dict[str, Any]:
    comparator = comparator or {
        "comparator_id": f"{spec.task_id}-SAME-TARGET-FORMULA-ABLATION-v1",
        "kind": "same_target_formula_ablation",
        "name": "same-target formula ablation baseline",
        "target_quantity": spec.target,
        "prediction_rule": (
            "evaluate the declared target formula after replacing the first visible ingredient with dimensionless 1.0"
        ),
        "prediction_value": 1.0,
        "pre_registered": True,
        "residual_metric_id": RESIDUAL_METRIC_ID,
    }
    return {
        "preregistration_id": f"{spec.task_id}-ANALYSIS-PREREG-v1",
        "declared_before_scoring": True,
        "declared_before_target_snapshot_access": bool(declared_before_target_snapshot_access),
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
        "comparator": comparator,
        "negative_control": {
            "control_id": f"{spec.task_id}-SAME-TARGET-ABLATION-CONTROL",
            "rule": "same-target formula ablation must have a larger residual score than the formula prediction",
        },
        "falsifier": "formula residual score exceeds 1.0 or the same-target ablation baseline is not worse",
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


def payload_has_forbidden_key(payload: Any, forbidden: set[str]) -> bool:
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in forbidden:
                return True
            if payload_has_forbidden_key(value, forbidden):
                return True
    elif isinstance(payload, list):
        return any(payload_has_forbidden_key(item, forbidden) for item in payload)
    return False


def physics_visible_projection_hash_valid(row: dict[str, Any]) -> bool:
    visible = row.get("visible_projection")
    if not isinstance(visible, dict):
        return False
    fields = visible.get("visible_fields")
    if not isinstance(fields, list):
        return False
    ingredients = []
    for field in fields:
        if not isinstance(field, dict):
            return False
        ingredients.append(
            {
                "quantity": field.get("quantity"),
                "value_text": field.get("value_text"),
                "unit": field.get("unit"),
                "uncertainty_text": field.get("uncertainty_text"),
            }
        )
    return visible.get("projection_hash") == sha256_object(
        {
            "task_id": row.get("task_id"),
            "ingredients": ingredients,
        }
    )


def physics_target_projection_hash_valid(row: dict[str, Any]) -> bool:
    target = row.get("target_projection")
    if not isinstance(target, dict):
        return False
    target_fields = target.get("target_fields")
    if not isinstance(target_fields, dict):
        return False
    return target.get("target_hash") == sha256_object(
        {
            "target_quantity": target_fields.get("target_quantity"),
            "observed_value_text": target_fields.get("observed_value_text"),
            "target_unit": target_fields.get("target_unit"),
            "official_uncertainty_text": target_fields.get("official_uncertainty_text"),
        }
    )


def physics_prediction_materialization_hash_valid(row: dict[str, Any]) -> bool:
    prediction = row.get("prediction_materialization")
    visible = row.get("visible_projection")
    if not isinstance(prediction, dict) or not isinstance(visible, dict):
        return False
    if payload_has_forbidden_key(prediction, set(PHYSICS_PREDICTION_FORBIDDEN_FIELDS)):
        return False
    if prediction.get("task_id") != row.get("task_id"):
        return False
    if prediction.get("visible_projection_id") != visible.get("projection_id"):
        return False
    if prediction.get("visible_projection_hash") != visible.get("projection_hash"):
        return False
    if prediction.get("formula") != row.get("formula"):
        return False
    if prediction.get("ingredients") != row.get("ingredients"):
        return False
    if prediction.get("predicted_value") != row.get("predicted_value"):
        return False
    return prediction.get("prediction_hash") == sha256_object(
        {k: v for k, v in prediction.items() if k != "prediction_hash"}
    )


def physics_target_projection_lock_failures(row: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    visible = row.get("visible_projection")
    prediction = row.get("prediction_materialization")
    target = row.get("target_projection")
    lock = row.get("target_projection_lock")
    declaration = row.get("projection_declaration")
    if visible_projection_has_target_leakage(row):
        failures.append("VISIBLE_PROJECTION_TARGET_LEAKAGE")
    if not isinstance(visible, dict) or not physics_visible_projection_hash_valid(row):
        failures.append("VISIBLE_PROJECTION_HASH_INVALID")
    if not isinstance(prediction, dict) or not physics_prediction_materialization_hash_valid(row):
        failures.append("PREDICTION_MATERIALIZATION_HASH_INVALID")
    if not isinstance(target, dict) or not physics_target_projection_hash_valid(row):
        failures.append("TARGET_PROJECTION_HASH_INVALID")
    if not isinstance(lock, dict):
        failures.append("TARGET_PROJECTION_LOCK_MISSING")
        return ordered_unique(failures)
    if not isinstance(declaration, dict):
        failures.append("PROJECTION_DECLARATION_MISSING")
    excluded = set((visible or {}).get("target_fields_excluded", [])) if isinstance(visible, dict) else set()
    if not set(PHYSICS_SCORING_TARGET_FIELDS).issubset(excluded):
        failures.append("VISIBLE_PROJECTION_TARGET_EXCLUSIONS_INCOMPLETE")
    if isinstance(visible, dict) and lock.get("visible_projection_hash") != visible.get("projection_hash"):
        failures.append("LOCK_VISIBLE_HASH_MISMATCH")
    if isinstance(prediction, dict) and lock.get("prediction_materialization_hash") != prediction.get("prediction_hash"):
        failures.append("LOCK_PREDICTION_HASH_MISMATCH")
    if isinstance(target, dict) and lock.get("target_projection_hash") != target.get("target_hash"):
        failures.append("LOCK_TARGET_HASH_MISMATCH")
    if lock.get("prediction_materialized_before_target_projection") is not True:
        failures.append("PREDICTION_NOT_MATERIALIZED_BEFORE_TARGET_PROJECTION")
    if lock.get("target_projection_hidden_until_scoring") is not True:
        failures.append("TARGET_PROJECTION_NOT_HIDDEN_UNTIL_SCORING")
    if lock.get("target_projection_depends_on_prediction_hash") is not True:
        failures.append("TARGET_PROJECTION_DOES_NOT_DEPEND_ON_PREDICTION_HASH")
    if set(lock.get("scoring_target_fields", [])) != set(PHYSICS_SCORING_TARGET_FIELDS):
        failures.append("SCORING_TARGET_FIELDS_MISMATCH")
    if lock.get("lock_hash") != sha256_object({k: v for k, v in lock.items() if k != "lock_hash"}):
        failures.append("TARGET_PROJECTION_LOCK_HASH_INVALID")
    if isinstance(declaration, dict):
        if declaration.get("target_projection_lock_id") != lock.get("lock_id"):
            failures.append("DECLARATION_LOCK_ID_MISMATCH")
        if declaration.get("prediction_materialized_before_target_projection") is not True:
            failures.append("DECLARATION_PREDICTION_ORDER_MISSING")
        if declaration.get("target_projection_hidden_until_scoring") is not True:
            failures.append("DECLARATION_TARGET_HIDDEN_LOCK_MISSING")
    return ordered_unique(failures)


def physics_target_projection_lock_valid(row: dict[str, Any]) -> bool:
    return not physics_target_projection_lock_failures(row)


def physics_source_lock_expected_hashes(rows: list[dict[str, Any]]) -> dict[str, Any]:
    visible_projection_hashes = ordered_unique(
        [
            str((row.get("visible_projection") or {}).get("projection_hash"))
            for row in rows
            if isinstance(row.get("visible_projection"), dict) and (row.get("visible_projection") or {}).get("projection_hash")
        ]
    )
    prediction_materialization_hashes = ordered_unique(
        [
            str((row.get("prediction_materialization") or {}).get("prediction_hash"))
            for row in rows
            if isinstance(row.get("prediction_materialization"), dict)
            and (row.get("prediction_materialization") or {}).get("prediction_hash")
        ]
    )
    target_projection_hashes = ordered_unique(
        [
            str((row.get("target_projection") or {}).get("target_hash"))
            for row in rows
            if isinstance(row.get("target_projection"), dict) and (row.get("target_projection") or {}).get("target_hash")
        ]
    )
    scoring_order = [
        {
            "task_id": str(row.get("task_id")),
            "row_hash": str(row.get("row_hash") or ""),
            "prediction_hash": str((row.get("prediction_materialization") or {}).get("prediction_hash") or ""),
            "target_hash": str((row.get("target_projection") or {}).get("target_hash") or ""),
        }
        for row in rows
    ]
    source_refs = ordered_unique([str(row.get("snapshot_ref") or "") for row in rows if str(row.get("snapshot_ref") or "")])
    source_hashes = ordered_unique([str(row.get("snapshot_sha256") or "") for row in rows if str(row.get("snapshot_sha256") or "")])
    return {
        "source_refs": source_refs,
        "source_hashes": source_hashes,
        "visible_projection_hashes": visible_projection_hashes,
        "prediction_materialization_hashes": prediction_materialization_hashes,
        "target_projection_hashes": target_projection_hashes,
        "visible_projection_set_hash": sha256_object(visible_projection_hashes),
        "prediction_materialization_set_hash": sha256_object(prediction_materialization_hashes),
        "target_projection_set_hash": sha256_object(target_projection_hashes),
        "scoring_order_hash": sha256_object(scoring_order),
        "target_hidden_commitment_hash": sha256_object(
            {
                "visible_projection_hashes": visible_projection_hashes,
                "prediction_materialization_hashes": prediction_materialization_hashes,
                "target_projection_hashes": target_projection_hashes,
            }
        ),
    }


def build_physics_machine_source_lock(
    rows: list[dict[str, Any]],
    *,
    source_snapshot_locked_at: str = "2026-04-28T00:00:00Z",
    source_separation_declared_at: str = "2026-04-28T00:01:00Z",
    visible_projection_locked_at: str = "2026-04-28T00:02:00Z",
    prediction_materialized_at: str = "2026-04-28T00:03:00Z",
    target_projection_unsealed_at: str = "2026-04-28T00:04:00Z",
    scoring_started_at: str = "2026-04-28T00:05:00Z",
    acquisition_record: dict[str, Any] | None = None,
) -> dict[str, Any]:
    expected = physics_source_lock_expected_hashes(rows)
    source_ref = expected["source_refs"][0] if len(expected["source_refs"]) == 1 else ""
    source_sha = expected["source_hashes"][0] if len(expected["source_hashes"]) == 1 else ""
    source_declaration_hash = sha256_object(
        {
            "schema_id": PHYSICS_SOURCE_LOCK_SCHEMA_ID,
            "mode": "target_blind",
            "source_ref": source_ref,
            "source_sha256": source_sha,
            "visible_projection_set_hash": expected["visible_projection_set_hash"],
            "prediction_materialization_set_hash": expected["prediction_materialization_set_hash"],
            "target_hidden_commitment_hash": expected["target_hidden_commitment_hash"],
        }
    )
    event_hashes = {
        "source_snapshot_locked": source_sha,
        "source_separation_declared": source_declaration_hash,
        "visible_projection_locked": expected["visible_projection_set_hash"],
        "prediction_materialized": expected["prediction_materialization_set_hash"],
        "target_projection_unsealed_for_scoring": expected["target_projection_set_hash"],
        "scoring_started": expected["scoring_order_hash"],
    }
    event_timestamps = {
        "source_snapshot_locked": source_snapshot_locked_at,
        "source_separation_declared": source_separation_declared_at,
        "visible_projection_locked": visible_projection_locked_at,
        "prediction_materialized": prediction_materialized_at,
        "target_projection_unsealed_for_scoring": target_projection_unsealed_at,
        "scoring_started": scoring_started_at,
    }
    lock = {
        "schema_id": PHYSICS_SOURCE_LOCK_SCHEMA_ID,
        "source_lock_id": "OC133-PHYSICS-OFFICIAL-BATCH-SOURCE-SEPARATION-LOCK",
        "source_snapshot": {
            "source_id": "physics_nist_constants",
            "source_ref": source_ref,
            "sha256": source_sha,
            "hash_policy": SNAPSHOT_HASH_POLICY,
        },
        "source_declaration_hash": source_declaration_hash,
        "visible_projection_hashes": expected["visible_projection_hashes"],
        "visible_projection_set_hash": expected["visible_projection_set_hash"],
        "prediction_materialization_hashes": expected["prediction_materialization_hashes"],
        "prediction_materialization_set_hash": expected["prediction_materialization_set_hash"],
        "target_projection_hashes": expected["target_projection_hashes"],
        "target_projection_set_hash": expected["target_projection_set_hash"],
        "target_hidden_commitment_hash": expected["target_hidden_commitment_hash"],
        "scoring_order_hash": expected["scoring_order_hash"],
        "order_records": [
            {
                "order_index": index,
                "event_type": event_type,
                "timestamp": event_timestamps[event_type],
                "artifact_hash": event_hashes[event_type],
            }
            for index, event_type in enumerate(PHYSICS_SOURCE_LOCK_EVENT_SEQUENCE, start=1)
        ],
        "hash_policy": "sha256 over canonical source-separation lock JSON excluding source_lock_hash",
        "artifact_exists_closes_lock": False,
    }
    if acquisition_record:
        lock["official_readonly_acquisition"] = {
            "acquisition_id": str(acquisition_record.get("acquisition_id") or ""),
            "lock_ref": str(acquisition_record.get("acquisition_lock_ref") or ""),
            "lock_sha256": str(acquisition_record.get("acquisition_lock_sha256") or ""),
            "metadata_ref": str(acquisition_record.get("acquisition_metadata_ref") or ""),
            "metadata_sha256": str(acquisition_record.get("acquisition_metadata_sha256") or ""),
            "order_record_ref": str(acquisition_record.get("acquisition_order_record_ref") or ""),
            "order_record_sha256": str(acquisition_record.get("acquisition_order_record_sha256") or ""),
            "order_record_file_sha256": str(acquisition_record.get("acquisition_order_record_file_sha256") or ""),
            "source_bytes_sha256": str(acquisition_record.get("source_bytes_sha256") or ""),
            "pre_target_sequence_proof": acquisition_record.get("pre_target_sequence_proof") or {},
        }
    lock["source_lock_hash"] = sha256_object({k: v for k, v in lock.items() if k != "source_lock_hash"})
    return lock


def physics_source_lock_order_failures(lock: dict[str, Any], expected: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    records = lock.get("order_records")
    if not isinstance(records, list) or not records:
        return ["PHYSICS_SOURCE_LOCK_ORDER_RECORDS_MISSING"]
    by_type: dict[str, dict[str, Any]] = {}
    sorted_indices: list[int] = []
    for record in records:
        if not isinstance(record, dict):
            failures.append("PHYSICS_SOURCE_LOCK_ORDER_RECORD_INVALID")
            continue
        event_type = str(record.get("event_type") or "")
        order_index = record.get("order_index")
        if not isinstance(order_index, int):
            failures.append(f"PHYSICS_SOURCE_LOCK_ORDER_INDEX_INVALID::{event_type or 'missing'}")
            continue
        sorted_indices.append(order_index)
        if event_type in by_type:
            failures.append(f"PHYSICS_SOURCE_LOCK_ORDER_EVENT_DUPLICATE::{event_type}")
            continue
        by_type[event_type] = record
    if sorted_indices != sorted(sorted_indices) or len(set(sorted_indices)) != len(sorted_indices):
        failures.append("PHYSICS_SOURCE_LOCK_ORDER_INDEX_SEQUENCE_INVALID")
    required_hashes = {
        "source_snapshot_locked": (expected["source_hashes"][0] if len(expected["source_hashes"]) == 1 else ""),
        "source_separation_declared": str(lock.get("source_declaration_hash") or ""),
        "visible_projection_locked": expected["visible_projection_set_hash"],
        "prediction_materialized": expected["prediction_materialization_set_hash"],
        "target_projection_unsealed_for_scoring": expected["target_projection_set_hash"],
        "scoring_started": expected["scoring_order_hash"],
    }
    parsed_records: dict[str, tuple[int, datetime]] = {}
    for event_type in PHYSICS_SOURCE_LOCK_EVENT_SEQUENCE:
        record = by_type.get(event_type)
        if not isinstance(record, dict):
            failures.append(f"PHYSICS_SOURCE_LOCK_ORDER_EVENT_MISSING::{event_type}")
            continue
        timestamp = parse_iso_timestamp(record.get("timestamp"))
        if timestamp is None:
            failures.append(f"PHYSICS_SOURCE_LOCK_TIMESTAMP_INVALID::{event_type}")
            continue
        if record.get("artifact_hash") != required_hashes[event_type]:
            failures.append(f"PHYSICS_SOURCE_LOCK_ORDER_HASH_MISMATCH::{event_type}")
        parsed_records[event_type] = (int(record["order_index"]), timestamp)
    for earlier, later in zip(PHYSICS_SOURCE_LOCK_EVENT_SEQUENCE, PHYSICS_SOURCE_LOCK_EVENT_SEQUENCE[1:]):
        if earlier not in parsed_records or later not in parsed_records:
            continue
        earlier_index, earlier_timestamp = parsed_records[earlier]
        later_index, later_timestamp = parsed_records[later]
        if earlier_index >= later_index or earlier_timestamp >= later_timestamp:
            failures.append(f"PHYSICS_SOURCE_LOCK_ORDER_NOT_PRECEDENT::{earlier}->{later}")
    if "source_snapshot_locked" in parsed_records and "target_projection_unsealed_for_scoring" in parsed_records:
        if parsed_records["source_snapshot_locked"][1] >= parsed_records["target_projection_unsealed_for_scoring"][1]:
            failures.append("PHYSICS_SOURCE_LOCK_NOT_PRE_TARGET")
    if "source_separation_declared" in parsed_records and "scoring_started" in parsed_records:
        if parsed_records["source_separation_declared"][1] >= parsed_records["scoring_started"][1]:
            failures.append("PHYSICS_SOURCE_LOCK_DECLARED_AFTER_SCORING")
    if "prediction_materialized" in parsed_records and "target_projection_unsealed_for_scoring" in parsed_records:
        if parsed_records["prediction_materialized"][1] >= parsed_records["target_projection_unsealed_for_scoring"][1]:
            failures.append("PHYSICS_SOURCE_LOCK_TARGET_NOT_HIDDEN")
    if "target_projection_unsealed_for_scoring" in parsed_records and "scoring_started" in parsed_records:
        if parsed_records["target_projection_unsealed_for_scoring"][1] > parsed_records["scoring_started"][1]:
            failures.append("PHYSICS_SOURCE_LOCK_TARGET_UNSEALED_AFTER_SCORING")
    return ordered_unique(failures)


def physics_source_lock_failures(source: dict[str, Any], rows: list[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    lock = source.get("machine_checkable_source_lock")
    if not isinstance(lock, dict):
        failures.append("PHYSICS_SOURCE_LOCK_NOT_MACHINE_VERIFIED")
        failures.append("PHYSICS_SOURCE_LOCK_ATTESTATION_MISSING")
        failures.append("PHYSICS_PROSPECTIVE_SOURCE_LOCK_REQUIRED")
        if source.get("strict_source_separation_attested") is True or str(source.get("attestation_ref") or ""):
            failures.append("PHYSICS_NO_ARTIFACT_EXISTS_CLOSURE")
        return failures
    if lock.get("artifact_exists_closes_lock") is True or lock.get("verification_method") == "artifact_exists":
        failures.append("PHYSICS_NO_ARTIFACT_EXISTS_CLOSURE")
    if lock.get("verification_status") == "passed":
        failures.append("PHYSICS_SOURCE_LOCK_STATUS_TOKEN_NOT_ACCEPTED")
    if lock.get("schema_id") != PHYSICS_SOURCE_LOCK_SCHEMA_ID:
        failures.append("PHYSICS_SOURCE_LOCK_SCHEMA_ID_MISMATCH")
    if any(visible_projection_has_target_leakage(row) for row in rows):
        failures.append("PHYSICS_SOURCE_LOCK_TARGET_LEAKAGE")
    expected = physics_source_lock_expected_hashes(rows)
    source_snapshot = lock.get("source_snapshot")
    if not isinstance(source_snapshot, dict):
        failures.append("PHYSICS_SOURCE_LOCK_SOURCE_SNAPSHOT_MISSING")
    else:
        if source_snapshot.get("source_ref") not in expected["source_refs"] or len(expected["source_refs"]) != 1:
            failures.append("PHYSICS_SOURCE_LOCK_SOURCE_REF_MISMATCH")
        if source_snapshot.get("sha256") not in expected["source_hashes"] or len(expected["source_hashes"]) != 1:
            failures.append("PHYSICS_SOURCE_LOCK_SOURCE_SHA256_MISMATCH")
        if source_snapshot.get("hash_policy") != SNAPSHOT_HASH_POLICY:
            failures.append("PHYSICS_SOURCE_LOCK_SOURCE_HASH_POLICY_MISMATCH")
    if lock.get("prediction_materialization_hashes") != expected["prediction_materialization_hashes"]:
        failures.append("PHYSICS_SOURCE_LOCK_PREDICTION_HASHES_MISMATCH")
    if lock.get("prediction_materialization_set_hash") != expected["prediction_materialization_set_hash"]:
        failures.append("PHYSICS_SOURCE_LOCK_PREDICTION_SET_HASH_MISMATCH")
    if lock.get("visible_projection_hashes") != expected["visible_projection_hashes"]:
        failures.append("PHYSICS_SOURCE_LOCK_VISIBLE_HASHES_MISMATCH")
    if lock.get("visible_projection_set_hash") != expected["visible_projection_set_hash"]:
        failures.append("PHYSICS_SOURCE_LOCK_VISIBLE_SET_HASH_MISMATCH")
    if lock.get("target_projection_hashes") != expected["target_projection_hashes"]:
        failures.append("PHYSICS_SOURCE_LOCK_TARGET_HASHES_MISMATCH")
    if lock.get("target_projection_set_hash") != expected["target_projection_set_hash"]:
        failures.append("PHYSICS_SOURCE_LOCK_TARGET_SET_HASH_MISMATCH")
    if lock.get("scoring_order_hash") != expected["scoring_order_hash"]:
        failures.append("PHYSICS_SOURCE_LOCK_SCORING_ORDER_HASH_MISMATCH")
    if lock.get("target_hidden_commitment_hash") != expected["target_hidden_commitment_hash"]:
        failures.append("PHYSICS_SOURCE_LOCK_TARGET_HIDDEN_COMMITMENT_MISMATCH")
    failures.extend(physics_source_lock_order_failures(lock, expected))
    if lock.get("source_lock_hash") != sha256_object(
        {k: v for k, v in lock.items() if k != "source_lock_hash"}
    ):
        failures.append("PHYSICS_SOURCE_LOCK_HASH_INVALID")
    machine_failures = [
        failure
        for failure in failures
        if failure not in {"PHYSICS_NO_ARTIFACT_EXISTS_CLOSURE", "PHYSICS_SOURCE_LOCK_STATUS_TOKEN_NOT_ACCEPTED"}
    ]
    if machine_failures:
        failures.append("PHYSICS_SOURCE_LOCK_NOT_MACHINE_VERIFIED")
    return ordered_unique(failures)


def physics_row_pre_target_proof_failures(row: dict[str, Any]) -> list[str]:
    task_id = str(row.get("task_id") or "unknown")
    failures: list[str] = []
    declaration = row.get("projection_declaration")
    if not isinstance(declaration, dict):
        return [f"PHYSICS_ROW_PRE_TARGET_PROOF_MISSING::{task_id}"]
    if declaration.get("source_snapshot_pre_target_lock") is not True:
        failures.append(f"PHYSICS_ROW_SOURCE_SNAPSHOT_PRE_TARGET_LOCK_MISSING::{task_id}")
    if declaration.get("target_projection_hidden_until_scoring") is not True:
        failures.append(f"PHYSICS_ROW_TARGET_HIDDEN_UNTIL_SCORING_MISSING::{task_id}")
    if declaration.get("prediction_materialized_before_target_projection") is not True:
        failures.append(f"PHYSICS_ROW_PREDICTION_BEFORE_TARGET_PROJECTION_MISSING::{task_id}")
    return failures


def object_text_contains(payload: Any, needles: tuple[str, ...]) -> bool:
    if isinstance(payload, dict):
        return any(object_text_contains(value, needles) for value in payload.values())
    if isinstance(payload, list):
        return any(object_text_contains(item, needles) for item in payload)
    if isinstance(payload, str):
        lower = f" {payload.lower()} "
        return any(needle in lower for needle in needles)
    return False


def physics_stale_policy_text_failures(rows: list[dict[str, Any]], source: dict[str, Any]) -> list[str]:
    if not (
        source.get("mode") == "prospective"
        and source.get("pre_target_lock") is True
        and source.get("target_hidden_until_scoring") is True
    ):
        return []
    return [
        f"PHYSICS_STALE_SOURCE_SEPARATION_POLICY_TEXT::{row.get('task_id')}"
        for row in rows
        if object_text_contains(row, PHYSICS_STALE_LOCK_BLOCKER_TEXT)
    ]


def physics_comparator_semantics_failures(row: dict[str, Any]) -> list[str]:
    task_id = str(row.get("task_id") or "unknown")
    failures: list[str] = []
    preregistration = row.get("preregistration")
    comparator = row.get("comparator")
    prereg_comparator = preregistration.get("comparator") if isinstance(preregistration, dict) else None
    if not isinstance(comparator, dict) or not isinstance(prereg_comparator, dict):
        return [f"PHYSICS_COMPARATOR_MISSING::{task_id}"]
    if comparator != prereg_comparator:
        failures.append(f"PHYSICS_COMPARATOR_PREREGISTRATION_MISMATCH::{task_id}")
    if comparator.get("pre_registered") is not True:
        failures.append(f"PHYSICS_COMPARATOR_NOT_PREREGISTERED::{task_id}")
    if comparator.get("kind") != "same_target_formula_ablation":
        failures.append(f"PHYSICS_COMPARATOR_NOT_SAME_TARGET_ABLATION::{task_id}")
    if comparator.get("target_quantity") != row.get("target_quantity"):
        failures.append(f"PHYSICS_COMPARATOR_TARGET_MISMATCH::{task_id}")
    if comparator.get("residual_metric_id") != row.get("residual_metric_id"):
        failures.append(f"PHYSICS_COMPARATOR_METRIC_MISMATCH::{task_id}")
    prediction = comparator.get("prediction_value")
    row_prediction = row.get("comparator_prediction")
    if not is_number(prediction) or not math.isfinite(float(prediction)):
        failures.append(f"PHYSICS_COMPARATOR_PREDICTION_INVALID::{task_id}")
    elif abs(float(prediction)) == 0.0:
        failures.append(f"PHYSICS_COMPARATOR_NULL_OR_ZERO_BASELINE::{task_id}")
    if prediction != row_prediction:
        failures.append(f"PHYSICS_COMPARATOR_ROW_PREDICTION_MISMATCH::{task_id}")
    text_payload = {
        "comparator": comparator,
        "comparator_baseline": row.get("comparator_baseline"),
        "negative_control_id": row.get("negative_control_id"),
        "negative_control_description": row.get("negative_control_description"),
        "falsifier": row.get("falsifier"),
    }
    if object_text_contains(text_payload, PHYSICS_FORBIDDEN_COMPARATOR_TEXT):
        failures.append(f"PHYSICS_COMPARATOR_NULL_OR_WRONG_FIELD_TEXT::{task_id}")
    if row.get("comparator_residual_score", 0) <= row.get("model_residual_score", 0):
        failures.append(f"PHYSICS_COMPARATOR_NOT_NONTRIVIAL_SUPERIORITY_BASELINE::{task_id}")
    return ordered_unique(failures)


def build_physics_rows(
    root: Path,
    snapshot_ref: str,
    manifest: dict[str, dict[str, Any]],
    *,
    acquisition_record: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], list[str], dict[str, Any]]:
    record = acquisition_record or snapshot_record(root, snapshot_ref, manifest, "physics_nist_constants")
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
        comparator = physics_same_target_ablation_comparator(spec, values)
        comparator_prediction = float(comparator["prediction_value"])
        comparator_residual = abs(comparator_prediction - observed)
        model_score = residual_score(model_residual, uncertainty)
        comparator_score = residual_score(comparator_residual, uncertainty)
        visible_projection = physics_visible_projection(spec, constants, snapshot_ref=snapshot_ref)
        prediction_materialization = physics_prediction_materialization(spec, visible_projection, predicted)
        target_projection = physics_target_projection(spec, target, snapshot_ref=snapshot_ref)
        target_projection_lock = physics_target_projection_lock(
            spec,
            visible_projection,
            prediction_materialization,
            target_projection,
        )
        projection_declaration = physics_projection_declaration(
            spec,
            visible_projection,
            target_projection,
            target_projection_lock,
            source_snapshot_pre_target_lock=bool(acquisition_record),
        )
        preregistration = physics_preregistration(
            spec,
            uncertainty,
            declared_before_target_snapshot_access=bool(acquisition_record),
            comparator=comparator,
        )
        if acquisition_record:
            grand_scope = (
                "prospective CODATA source snapshot locked before scoring with target projection hidden until scoring "
                f"under acquisition {acquisition_record.get('acquisition_id')} "
                f"snapshot_sha256={acquisition_record.get('sha256')} "
                f"lock_sha256={acquisition_record.get('acquisition_lock_sha256')} "
                f"order_record_sha256={acquisition_record.get('acquisition_order_record_sha256')}"
            )
        else:
            grand_scope = "official snapshot consistency task; not independently pre-target locked in the current repo"
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
            "prediction_materialization": prediction_materialization,
            "target_projection": target_projection,
            "target_projection_lock": target_projection_lock,
            "projection_declaration": projection_declaration,
            "preregistration": preregistration,
            "predicted_value": predicted,
            "observed_value": observed,
            "official_uncertainty": target.uncertainty,
            "uncertainty": uncertainty,
            "residual_metric_id": RESIDUAL_METRIC_ID,
            "model_residual": model_residual,
            "model_residual_score": model_score,
            "comparator": comparator,
            "comparator_baseline": comparator["name"],
            "comparator_prediction": comparator_prediction,
            "comparator_residual": comparator_residual,
            "comparator_residual_score": comparator_score,
            "negative_control_id": comparator["comparator_id"],
            "negative_control_description": (
                "replace the first visible formula ingredient with dimensionless 1.0 and require a larger same-target residual"
            ),
            "negative_control_rejected": comparator_score > model_score,
            "falsifier": "official relation residual exceeds display/uncertainty tolerance or the same-target ablation baseline is not worse",
            "residual_within_uncertainty": model_residual <= uncertainty,
            "grand_scope": grand_scope,
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
        "grand_scope": "official snapshot field or cross-source consistency task; support remains blocked pending prospective source separation",
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


def prospective_physics_source_separation(rows: list[dict[str, Any]], acquisition_record: dict[str, Any]) -> dict[str, Any]:
    acquired_at = str(acquisition_record.get("acquired_at_utc") or "2026-04-28T00:00:00Z")
    lock = build_physics_machine_source_lock(
        rows,
        source_snapshot_locked_at=acquired_at,
        source_separation_declared_at=timestamp_plus_seconds(acquired_at, 1),
        visible_projection_locked_at=timestamp_plus_seconds(acquired_at, 2),
        prediction_materialized_at=timestamp_plus_seconds(acquired_at, 3),
        target_projection_unsealed_at=timestamp_plus_seconds(acquired_at, 4),
        scoring_started_at=timestamp_plus_seconds(acquired_at, 5),
        acquisition_record=acquisition_record,
    )
    return {
        "mode": "prospective",
        "pre_target_lock": True,
        "target_hidden_until_scoring": True,
        "declared_before_scoring": True,
        "visible_target_projection_declared": bool(rows),
        "visible_projection_ids": ordered_unique(
            [
                str(row["visible_projection"]["projection_id"])
                for row in rows
                if isinstance(row.get("visible_projection"), dict)
            ]
        ),
        "target_projection_ids": ordered_unique(
            [
                str(row["target_projection"]["projection_id"])
                for row in rows
                if isinstance(row.get("target_projection"), dict)
            ]
        ),
        "strict_source_separation_attested": True,
        "attestation_ref": str(acquisition_record.get("acquisition_lock_ref") or ""),
        "source_separation_class": "machine_verified_prospective_official_readonly_source_lock",
        "training_sources": ordered_unique([str(row["training_source"]) for row in rows if row.get("training_source")]),
        "target_sources": ordered_unique([str(row["target_source"]) for row in rows if row.get("target_source")]),
        "machine_checkable_source_lock": lock,
        "official_readonly_acquisition": {
            "acquisition_id": str(acquisition_record.get("acquisition_id") or ""),
            "snapshot_ref": str(acquisition_record.get("source_ref") or ""),
            "snapshot_sha256": str(acquisition_record.get("sha256") or ""),
            "source_bytes_sha256": str(acquisition_record.get("source_bytes_sha256") or ""),
            "lock_ref": str(acquisition_record.get("acquisition_lock_ref") or ""),
            "lock_sha256": str(acquisition_record.get("acquisition_lock_sha256") or ""),
            "metadata_ref": str(acquisition_record.get("acquisition_metadata_ref") or ""),
            "metadata_sha256": str(acquisition_record.get("acquisition_metadata_sha256") or ""),
            "order_record_ref": str(acquisition_record.get("acquisition_order_record_ref") or ""),
            "order_record_sha256": str(acquisition_record.get("acquisition_order_record_sha256") or ""),
            "order_record_file_sha256": str(acquisition_record.get("acquisition_order_record_file_sha256") or ""),
        },
    }


def physics_codata_lock_satisfied(source: dict[str, Any]) -> bool:
    acquisition = source.get("official_readonly_acquisition")
    return (
        source.get("mode") == "prospective"
        and source.get("pre_target_lock") is True
        and source.get("target_hidden_until_scoring") is True
        and source.get("strict_source_separation_attested") is True
        and isinstance(acquisition, dict)
        and acquisition.get("acquisition_id") == PHYSICS_CODATA_ACQUISITION_ID
        and bool(acquisition.get("snapshot_sha256"))
        and bool(acquisition.get("lock_sha256"))
        and bool(acquisition.get("order_record_sha256"))
    )


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
        acquisition = source.get("official_readonly_acquisition")
        if isinstance(acquisition, dict):
            cleaned["official_readonly_acquisition"] = {
                "acquisition_id": str(acquisition.get("acquisition_id") or ""),
                "snapshot_ref": str(acquisition.get("snapshot_ref") or ""),
                "snapshot_sha256": str(acquisition.get("snapshot_sha256") or ""),
                "source_bytes_sha256": str(acquisition.get("source_bytes_sha256") or ""),
                "lock_ref": str(acquisition.get("lock_ref") or ""),
                "lock_sha256": str(acquisition.get("lock_sha256") or ""),
                "metadata_ref": str(acquisition.get("metadata_ref") or ""),
                "metadata_sha256": str(acquisition.get("metadata_sha256") or ""),
                "order_record_ref": str(acquisition.get("order_record_ref") or ""),
                "order_record_sha256": str(acquisition.get("order_record_sha256") or ""),
                "order_record_file_sha256": str(acquisition.get("order_record_file_sha256") or ""),
            }
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
    source_locked = bool(rows) and all(row.get("declared_before_target_snapshot_access") is True for row in prereg_rows)
    policy = (
        "Formulas, same-target ablation comparators, residual metrics, uncertainty rules, negative controls, and "
        "falsifiers are declared before row scoring with the CODATA source snapshot/order/lock hashes recorded "
        "in source_separation."
        if source_locked
        else (
            "Formulas, comparators, residual metrics, uncertainty rules, negative controls, and falsifiers are "
            "declared in this artifact before row scoring, but the present CODATA text was not acquired under "
            "a pre-target hidden lock; this remains a blocker for promotion."
        )
    )
    return {
        "domain": domain,
        "preregistered_before_scoring": bool(rows) and len(prereg_rows) == len(rows),
        "preregistered_before_target_snapshot_access": source_locked,
        "preregistration_ids": [
            str(row.get("preregistration_id")) for row in prereg_rows if str(row.get("preregistration_id") or "")
        ],
        "formula_total": len([row for row in prereg_rows if isinstance(row.get("formula"), dict)]),
        "comparator_total": len(comparator_registered),
        "comparator_preregistered_total": sum(1 for value in comparator_registered if value),
        "residual_metric_id": RESIDUAL_METRIC_ID,
        "policy": policy,
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
                "name": "physics official-snapshot same-target formula ablation baseline",
                "prediction_rule": (
                    "For each declared CODATA target, evaluate the preregistered target formula after replacing "
                    "the first visible ingredient with dimensionless 1.0; score that same-target ablation under "
                    "the same residual metric."
                ),
                "kind": "same_target_formula_ablation",
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


def prospective_metadata_visible_request_fields(row: dict[str, Any]) -> dict[str, Any]:
    visible = {
        key: value
        for key, value in row.items()
        if key
        not in {
            "prospective_lock_metadata",
            "source_separation_lock_metadata",
            "execution_lock_metadata",
        }
    }
    return dict(sorted(visible.items(), key=lambda item: item[0]))


def prospective_metadata_order_proof() -> dict[str, Any]:
    event_order = [
        {
            "event_index": index,
            "event": event,
            "performed_by_acquisition_runner": event == "source_snapshot_locked",
            "must_precede_scoring": event
            in {
                "source_snapshot_locked",
                "source_separation_declared",
                "visible_projection_locked",
                "prediction_materialized",
            },
        }
        for index, event in enumerate(PHYSICS_PROSPECTIVE_LOCK_EVENT_SEQUENCE, start=1)
    ]
    proof = {
        "event_order": event_order,
        "strict_precedence": (
            "source_snapshot_locked < source_separation_declared < visible_projection_locked < "
            "prediction_materialized < target_projection_unsealed_for_scoring <= scoring_started"
        ),
        "source_snapshot_locked_before_scoring": True,
        "target_unsealed_before_acquisition": False,
        "scoring_started_before_acquisition": False,
        "post_acquisition_events_not_performed_by_runner": [
            "target_projection_unsealed_for_scoring",
            "scoring_started",
        ],
    }
    proof["order_hash"] = sha256_object({key: value for key, value in proof.items() if key != "order_hash"})
    return proof


def build_physics_prospective_lock_metadata(row: dict[str, Any]) -> dict[str, Any]:
    request_visible_fields = prospective_metadata_visible_request_fields(row)
    order_proof = prospective_metadata_order_proof()
    metadata_inputs = {
        "request_visible_fields": request_visible_fields,
        "model_family": PHYSICS_PROSPECTIVE_MODEL_FAMILY,
        "comparator_baseline": PHYSICS_PROSPECTIVE_COMPARATOR_BASELINE,
        "scoring_policy": PHYSICS_PROSPECTIVE_SCORING_POLICY,
        "target_split_policy": PHYSICS_PROSPECTIVE_TARGET_SPLIT_POLICY,
        "no_send_locks": PHYSICS_PROSPECTIVE_NO_SEND_LOCKS,
        "prospective_order_hash": order_proof["order_hash"],
    }
    metadata = {
        "schema_id": PROSPECTIVE_LOCK_METADATA_SCHEMA_ID,
        "source_snapshot_pre_target_lock": True,
        "target_hidden_until_scoring": True,
        "target_projection_unsealed_for_scoring": False,
        "scoring_started": False,
        "prediction_materialization_required_before_scoring": True,
        "target_projection_read_before_prediction_materialization": False,
        "public_release_action_allowed": False,
        "publish_allowed": False,
        "push_allowed": False,
        "request_visible_fields": request_visible_fields,
        "request_visible_fields_hash": sha256_object(request_visible_fields),
        "model_family": PHYSICS_PROSPECTIVE_MODEL_FAMILY,
        "model_family_hash": sha256_object(PHYSICS_PROSPECTIVE_MODEL_FAMILY),
        "comparator_baseline": PHYSICS_PROSPECTIVE_COMPARATOR_BASELINE,
        "comparator_baseline_hash": sha256_object(PHYSICS_PROSPECTIVE_COMPARATOR_BASELINE),
        "scoring_policy": PHYSICS_PROSPECTIVE_SCORING_POLICY,
        "scoring_policy_hash": sha256_object(PHYSICS_PROSPECTIVE_SCORING_POLICY),
        "target_split_policy": PHYSICS_PROSPECTIVE_TARGET_SPLIT_POLICY,
        "target_split_policy_hash": sha256_object(PHYSICS_PROSPECTIVE_TARGET_SPLIT_POLICY),
        "no_send_locks": PHYSICS_PROSPECTIVE_NO_SEND_LOCKS,
        "no_send_locks_hash": sha256_object(PHYSICS_PROSPECTIVE_NO_SEND_LOCKS),
        "prospective_order_proof": order_proof,
        "prospective_order_hash": order_proof["order_hash"],
        "order_proof": order_proof,
        "order_hash": order_proof["order_hash"],
        "metadata_inputs_hash": sha256_object(metadata_inputs),
        "target_value_leak_check": {
            "target_values_present": False,
            "target_value_fields_excluded": PHYSICS_PROSPECTIVE_TARGET_SPLIT_POLICY["target_value_fields_excluded"],
        },
    }
    metadata["metadata_hash"] = sha256_object({key: value for key, value in metadata.items() if key != "metadata_hash"})
    return metadata


def attach_physics_prospective_lock_metadata(row: dict[str, Any]) -> dict[str, Any]:
    result = dict(row)
    result["prospective_lock_metadata"] = build_physics_prospective_lock_metadata(result)
    return result


def payload_has_prospective_metadata_target_value(payload: Any) -> bool:
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in PHYSICS_PROSPECTIVE_METADATA_FORBIDDEN_VALUE_KEYS:
                return True
            if payload_has_prospective_metadata_target_value(value):
                return True
    elif isinstance(payload, list):
        return any(payload_has_prospective_metadata_target_value(item) for item in payload)
    return False


def physics_prospective_lock_metadata_failures(row: dict[str, Any]) -> list[str]:
    metadata = row.get("prospective_lock_metadata")
    if not isinstance(metadata, dict) or not metadata:
        return ["PROSPECTIVE_LOCK_METADATA_MISSING"]
    failures: list[str] = []
    required_values = {
        "schema_id": PROSPECTIVE_LOCK_METADATA_SCHEMA_ID,
        "source_snapshot_pre_target_lock": True,
        "target_hidden_until_scoring": True,
        "target_projection_unsealed_for_scoring": False,
        "scoring_started": False,
        "prediction_materialization_required_before_scoring": True,
        "target_projection_read_before_prediction_materialization": False,
        "public_release_action_allowed": False,
        "publish_allowed": False,
        "push_allowed": False,
    }
    for key, expected in required_values.items():
        if metadata.get(key) != expected:
            failures.append(f"PROSPECTIVE_LOCK_METADATA_INVALID::{key}")
    scoring_policy = metadata.get("scoring_policy") if isinstance(metadata.get("scoring_policy"), dict) else {}
    if metadata.get("scoring_started_at") or scoring_policy.get("scoring_started_at"):
        failures.append("POST_SCORING_ACQUISITION_NOT_ALLOWED")
    if metadata.get("target_projection_unsealed_for_scoring_at") or scoring_policy.get(
        "target_projection_unsealed_for_scoring_at"
    ):
        failures.append("TARGET_UNSEALED_BEFORE_ACQUISITION_NOT_ALLOWED")
    order_proof = metadata.get("prospective_order_proof")
    if not isinstance(order_proof, dict) or not order_proof:
        failures.append("PROSPECTIVE_LOCK_METADATA_ORDER_PROOF_MISSING")
    elif metadata.get("prospective_order_hash") != sha256_object(
        {key: value for key, value in order_proof.items() if key != "order_hash"}
    ):
        failures.append("PROSPECTIVE_LOCK_METADATA_ORDER_HASH_STALE")
    if payload_has_prospective_metadata_target_value(metadata):
        failures.append("PROSPECTIVE_LOCK_METADATA_TARGET_VALUE_LEAKAGE")
    expected = build_physics_prospective_lock_metadata(row)
    if metadata.get("metadata_hash") != expected.get("metadata_hash") or metadata != expected:
        failures.append("PROSPECTIVE_LOCK_METADATA_STALE")
    return ordered_unique(failures)


def physics_acquisition_requests(current_n: int, minimum_n: int) -> list[dict[str, Any]]:
    rows = [
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
                "The official-readonly runner allowlist accepts this exact NIST ASD hydrogen Balmer TSV query."
            ),
            "missing_reason": "No independent NIST ASD target snapshot is pinned for a physics held-out spectral-line class.",
        },
    ]
    return [attach_physics_prospective_lock_metadata(row) for row in rows]


def build_physics_acquisition_packet(physics_eval: dict[str, Any]) -> dict[str, Any]:
    all_rows = physics_acquisition_requests(int(physics_eval["candidate_n"]), int(physics_eval["minimum_n"]))
    codata_lock_satisfied = physics_codata_lock_satisfied(physics_eval.get("source_separation", {}))
    rows = [row for row in all_rows if not (codata_lock_satisfied and row["acquisition_id"] == PHYSICS_CODATA_ACQUISITION_ID)]
    protocol_blockers = ["INDEPENDENT_PHYSICS_TARGET_CLASS_REQUIRED"] if codata_lock_satisfied else [
        "PRE_TARGET_LOCK_REQUIRED",
        "TARGET_HIDDEN_UNTIL_SCORING_REQUIRED",
        "SOURCE_SEPARATION_ATTESTATION_REQUIRED",
        "INDEPENDENT_PHYSICS_TARGET_CLASS_REQUIRED",
    ]
    packet = {
        "schema_id": PHYSICS_ACQUISITION_PACKET_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "generated_by": "tools/oc133_physics_chemistry_official_batch_factory.py",
        "domain": "physics",
        "source_lane": "official_batch",
        "status": "PARTIAL_ACQUISITION_REQUIRED" if codata_lock_satisfied else "ACQUISITION_REQUIRED",
        "no_send": True,
        "publish_allowed": False,
        "registry_write_allowed": False,
        "scientific_pass": False,
        "grand_toe_support_allowed": False,
        "candidate_n": physics_eval["candidate_n"],
        "minimum_n": physics_eval["minimum_n"],
        "request_total": len(rows),
        "missing_official_snapshot_total": len(rows),
        "missing_official_snapshots": rows,
        "acquisition_requests": rows,
        "exact_acquisition_requests": rows,
        "official_acquisition_run_root_ref": OFFICIAL_ACQUISITION_RUN_ROOT_REL,
        "codata_prospective_lock_satisfied": codata_lock_satisfied,
        "codata_prospective_lock_evidence": (
            physics_eval["source_separation"].get("official_readonly_acquisition", {})
            if codata_lock_satisfied
            else {}
        ),
        "protocol_blockers": protocol_blockers,
        "automated_prospective_protocol": {
            "protocol_id": "OC133-PHYSICS-OFFICIAL-BATCH-PROSPECTIVE-ACQUISITION-v1",
            "runner_tool_ref": "tools/oc133_official_readonly_acquisition_runner.py",
            "phase_order": [
                "freeze_formula_comparator_uncertainty_controls_and_falsifiers",
                "write_no_send_acquisition_packet",
                "dry_run_runner_validation",
                "execute_readonly_official_https_get_after_packet_hash_is_fixed",
                "materialize_prediction_rows_from_visible_fields_only",
                "unseal_target_projection_for_scoring",
                "rerun_factory_check_and_grand_gate",
            ],
            "acceptance_gates": [
                "all acquisition requests validate against the official-readonly runner allowlist",
                "acquired snapshot hashes match the runner metadata and no-send locks",
                "source-separation lock event order is strictly source_snapshot_locked < source_separation_declared < visible_projection_locked < prediction_materialized < target_projection_unsealed_for_scoring <= scoring_started",
                "prediction materialization hashes exclude all scoring target fields",
                "N>=20, comparator preregistered, residuals within uncertainty, negative controls rejected, falsifiers not triggered",
                "grand_toe_support_allowed remains false unless the strict grand gate has no failures",
            ],
            "dry_run_command": (
                f"python tools/oc133_official_readonly_acquisition_runner.py --packet {PHYSICS_ACQUISITION_PACKET_REL} "
                "--allow-blocked-exit-zero"
            ),
            "execute_command_no_public_action": (
                f"python tools/oc133_official_readonly_acquisition_runner.py --packet {PHYSICS_ACQUISITION_PACKET_REL} "
                "--execute-network --allow-blocked-exit-zero"
            ),
            "post_acquisition_factory_check_command": (
                "python tools/oc133_physics_chemistry_official_batch_factory.py --check --allow-blocked-exit-zero"
            ),
            "known_current_runner_blocker": (
                "No dry-run runner validation blocker is expected; network acquisition still requires explicit "
                "--execute-network and intact no-send prospective locks."
            ),
        },
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
    prediction_tamper_rejected = False
    target_projection_tamper_rejected = False
    visible_projection_tamper_rejected = False
    hidden_lock_tamper_rejected = False
    if first_physics:
        mutated = dict(first_physics)
        observed = as_float(mutated.get("observed_value"), 0.0)
        mutated["observed_value"] = observed + max(abs(observed) * 1e-6, 1e-300)
        tamper_hash_changes = row_hash(mutated) != first_physics.get("row_hash")
        prediction_tamper = json.loads(json.dumps(first_physics))
        prediction_tamper["prediction_materialization"]["predicted_value"] = (
            as_float(prediction_tamper["prediction_materialization"].get("predicted_value"), 0.0) + 1.0
        )
        prediction_tamper_rejected = not physics_target_projection_lock_valid(prediction_tamper)
        target_tamper = json.loads(json.dumps(first_physics))
        target_tamper["target_projection"]["target_fields"]["observed_value_text"] = "tampered"
        target_projection_tamper_rejected = not physics_target_projection_lock_valid(target_tamper)
        visible_tamper = json.loads(json.dumps(first_physics))
        visible_tamper["visible_projection"]["visible_fields"].append(
            {
                "quantity": visible_tamper["target_quantity"],
                "observed_value": visible_tamper["observed_value"],
            }
        )
        visible_projection_tamper_rejected = not physics_target_projection_lock_valid(visible_tamper)
        hidden_lock_tamper = json.loads(json.dumps(first_physics))
        hidden_lock_tamper["target_projection_lock"]["target_projection_hidden_until_scoring"] = False
        hidden_lock_tamper_rejected = not physics_target_projection_lock_valid(hidden_lock_tamper)
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
            "test_id": "physics-target-projection-lock-valid",
            "description": "each physics row has a machine-checkable visible/prediction/target projection lock",
            "passed": bool(physics_rows) and all(physics_target_projection_lock_valid(row) for row in physics_rows),
        },
        {
            "test_id": "physics-prediction-materialization-tamper-rejected",
            "description": "mutating a pre-target physics prediction materialization breaks its projection lock",
            "passed": bool(first_physics) and prediction_tamper_rejected,
        },
        {
            "test_id": "physics-target-projection-tamper-rejected",
            "description": "mutating a physics target projection breaks its target hash and projection lock",
            "passed": bool(first_physics) and target_projection_tamper_rejected,
        },
        {
            "test_id": "physics-visible-projection-target-leak-tamper-rejected",
            "description": "adding a scoring target field to the visible projection breaks the projection lock",
            "passed": bool(first_physics) and visible_projection_tamper_rejected,
        },
        {
            "test_id": "physics-target-hidden-lock-tamper-rejected",
            "description": "turning off the target-hidden lock flag breaks the projection lock",
            "passed": bool(first_physics) and hidden_lock_tamper_rejected,
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


def domain_missing_official_snapshots(
    domain: str,
    current_n: int,
    minimum_n: int,
    source: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
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
        rows = []
        if not (
            isinstance(source, dict)
            and source.get("mode") == "prospective"
            and source.get("pre_target_lock") is True
            and source.get("strict_source_separation_attested") is True
        ):
            rows.append(
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
                }
            )
        rows.append(
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
            }
        )
        return rows
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
        projection_lock_failures = ordered_unique(
            [
                failure
                for row in rows
                for failure in physics_target_projection_lock_failures(row)
            ]
        )
        blockers.extend(f"PHYSICS_TARGET_PROJECTION_LOCK::{failure}" for failure in projection_lock_failures)
        blockers.extend(physics_source_lock_failures(source, rows))
        blockers.extend(
            ordered_unique(
                [
                    failure
                    for row in rows
                    for failure in physics_row_pre_target_proof_failures(row)
                ]
            )
        )
        blockers.extend(
            ordered_unique(
                [
                    failure
                    for row in rows
                    for failure in physics_comparator_semantics_failures(row)
                ]
            )
        )
        blockers.extend(physics_stale_policy_text_failures(rows, source))
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
        "missing_official_snapshots": domain_missing_official_snapshots(domain, len(rows), minimum_n, source),
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

    physics_acquisition_record, physics_acquisition_failures = successful_physics_codata_acquisition(root)
    physics_snapshot_ref = (
        str(physics_acquisition_record["source_ref"]) if physics_acquisition_record else PHYSICS_NIST_CONSTANTS_REF
    )
    physics_rows, physics_blockers, physics_snapshot = build_physics_rows(
        root,
        physics_snapshot_ref,
        manifest,
        acquisition_record=physics_acquisition_record,
    )
    if physics_acquisition_record is None and physics_acquisition_failures != ["PHYSICS_PROSPECTIVE_CODATA_ACQUISITION_MISSING"]:
        physics_blockers = ordered_unique([*physics_blockers, *physics_acquisition_failures])
    chemistry_rows, chemistry_blockers, chemistry_snapshots = build_chemistry_rows(root, manifest)

    physics_source = source_separation_overrides.get("physics") or (
        prospective_physics_source_separation(physics_rows, physics_acquisition_record)
        if physics_acquisition_record
        else default_source_separation("physics", physics_rows)
    )
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
