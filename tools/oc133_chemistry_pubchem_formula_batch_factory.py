from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from validation.grand_science import evidence_pack_factory as grand_factory  # noqa: E402
from tools import oc133_target_projection_lock_factory as target_lock_factory  # noqa: E402


RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
CAPABILITY_OWNER = "Research/EmpiricalScience"
PLANNER_REF = "tools/oc133_chemistry_pubchem_formula_batch_factory.py"

SCHEMA_ID = "OC133_CHEMISTRY_PUBCHEM_FORMULA_BATCH_FACTORY_v1"
TASKS_SCHEMA_ID = "OC133_CHEMISTRY_PUBCHEM_FORMULA_BATCH_TASKS_v1"
PROTOCOL_SCHEMA_ID = "OC133_CHEMISTRY_PUBCHEM_FORMULA_BATCH_PROTOCOL_v1"
REPORT_SCHEMA_ID = "OC133_CHEMISTRY_PUBCHEM_FORMULA_BATCH_REPORT_v1"
ACQUISITION_SCHEMA_ID = "OC133_CHEMISTRY_PUBCHEM_FORMULA_BATCH_ACQUISITION_PACKET_v1"
HASHES_SCHEMA_ID = "OC133_CHEMISTRY_PUBCHEM_FORMULA_BATCH_HASHES_v1"

OUTPUT_ROOT_REL = "validation/heldout/grand_science/chemistry/pubchem_formula_batch"
TASKS_REL = f"{OUTPUT_ROOT_REL}/OC133_CHEMISTRY_PUBCHEM_FORMULA_BATCH_TASKS.json"
PROTOCOL_REL = f"{OUTPUT_ROOT_REL}/OC133_CHEMISTRY_PUBCHEM_FORMULA_BATCH_PROTOCOL.json"
CANDIDATE_PACK_REL = f"{OUTPUT_ROOT_REL}/OC133_CHEMISTRY_PUBCHEM_FORMULA_BATCH_CANDIDATE_PACK.json"
REPORT_REL = f"{OUTPUT_ROOT_REL}/OC133_CHEMISTRY_PUBCHEM_FORMULA_BATCH_REPORT.json"
ACQUISITION_REL = f"{OUTPUT_ROOT_REL}/OC133_CHEMISTRY_PUBCHEM_FORMULA_BATCH_ACQUISITION_PACKET.json"
HASHES_REL = f"{OUTPUT_ROOT_REL}/OC133_CHEMISTRY_PUBCHEM_FORMULA_BATCH_HASHES.json"
README_REL = f"{OUTPUT_ROOT_REL}/README.md"
WORK_ORDER_REL = f"{OUTPUT_ROOT_REL}/OC133_CHEMISTRY_PUBCHEM_FORMULA_BATCH_STRONGER_TARGET_WORK_ORDER.json"

REQUIREMENTS_REL = "benchmarks/grand_science/domain_requirements.json"
DEFAULT_SNAPSHOT_REF = "validation/_raw/chemistry_pubchem_water.txt"
DEFAULT_DISCOVERY_ROOTS = (
    "validation/_raw",
    "data/chemistry",
    "empirical/chemistry",
    f"{OUTPUT_ROOT_REL}/raw",
)
OFFICIAL_ACQUISITION_RUN_ROOT_REL = "validation/heldout/acquisition_runs/oc133_official_readonly"
OFFICIAL_ACQUISITION_LOCKS_REL = f"{OFFICIAL_ACQUISITION_RUN_ROOT_REL}/locks"
OFFICIAL_ACQUISITION_SNAPSHOTS_REL = f"{OFFICIAL_ACQUISITION_RUN_ROOT_REL}/snapshots"

SNAPSHOT_HASH_POLICY = "LF_NORMALIZED_TEXT_SNAPSHOT_HASH"
OFFICIAL_ACQUISITION_HASH_POLICY = "sha256 over acquired response bytes as stored"
ROW_HASH_POLICY = "sha256 over canonical row JSON before row_hash insertion"
PACK_HASH_POLICY = "sha256 over canonical JSON"
OFFICIAL_PUG_PROPERTY_FIELDS = "MolecularFormula,MolecularWeight,CanonicalSMILES,InChIKey"
OFFICIAL_PUG_ENDPOINT_PREFIX = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid"
TARGET_PROJECTION_VISIBLE_FIELDS = ["CID", "MolecularFormula"]
TARGET_PROJECTION_TARGET_FIELDS = ["MolecularWeight"]
LEGACY_SEED_LOCK_SCHEMA_ID = "OC133_CHEMISTRY_PUBCHEM_FORMULA_LEGACY_SEED_TARGET_PROJECTION_LOCK_v1"
LEGACY_SEED_LOCK_ROOT_REL = f"{OUTPUT_ROOT_REL}/legacy_seed_locks"
GENERATED_NAME_PREFIX = "OC133_CHEMISTRY_PUBCHEM_FORMULA_BATCH_"
MOLECULAR_WEIGHT_UNCERTAINTY_DA = 0.05
COMPARATOR_BASELINE_KIND = "formula_atom_count_carbon_equivalent_mass"
COMPARATOR_BASELINE_NAME = "formula atom-count carbon-equivalent molecular-weight baseline"
COMPARATOR_PREDICTION_RULE = (
    "parse MolecularFormula from the visible projection, count all atoms, and predict "
    "12.0 Da per atom while ignoring element identities"
)
COMPARATOR_ATOM_COUNT_MASS_DA = 12.0
COMPARATOR_MATERIAL_MARGIN_DA = 0.5
ZERO_DA_CONTROL_NAME = "zero-Da molecular-weight null sanity control"
ZERO_DA_CONTROL_RULE = "predict zero molecular weight for every PubChem compound"
SUPPORT_POLICY = (
    "Grand support is emitted only for an N>=20 PubChem PUG REST formula batch with explicit source separation, "
    "pre-target lock, hidden target manifest, official PubChem provenance, a preregistered nontrivial formula-visible "
    "atom-count comparator, residual superiority by material margin, rejected nontrivial and sanity negative controls, "
    "falsifiers, and a clean grand empirical gate. Local formula/weight snapshots are scored as official-data "
    "reconstruction rows but remain blocked until every strict criterion passes."
)
BOUNDED_REPLAY_BLOCKER = "CURRENT_PUBCHEM_FORMULA_MASS_REPLAY_IS_BOUNDED_BASELINE_NOT_GRAND_CHEMISTRY_SUPPORT"
STRONGER_TARGET_WORK_ORDER_BLOCKER = "STRONGER_CHEMISTRY_TARGET_WORK_ORDER_REQUIRED"

# Fixed average atomic weights used by this factory. They are intentionally
# embedded in the artifact so the formula-mass computation is auditable.
ATOMIC_WEIGHT_TABLE_ID = "OC133_FIXED_AVERAGE_ATOMIC_WEIGHTS_v2"
ATOMIC_WEIGHT_SOURCE_NOTE = (
    "Fixed local conventional average atomic weights for deterministic PubChem MolecularWeight replay; "
    "v2 expands heavy/metal coverage for acquired PubChem formulas, including mercury. "
    "Values are not fetched at runtime and are not tuned per compound."
)
ATOMIC_WEIGHTS = {
    "H": 1.00794,
    "He": 4.002602,
    "Li": 6.941,
    "Be": 9.012182,
    "B": 10.811,
    "C": 12.0107,
    "N": 14.0067,
    "O": 15.9994,
    "F": 18.998403163,
    "Ne": 20.1797,
    "Na": 22.98976928,
    "Mg": 24.305,
    "Al": 26.9815385,
    "Si": 28.0855,
    "P": 30.973761998,
    "S": 32.065,
    "Cl": 35.453,
    "Ar": 39.948,
    "K": 39.0983,
    "Ca": 40.078,
    "Sc": 44.95591,
    "Ti": 47.867,
    "V": 50.9415,
    "Cr": 51.9961,
    "Mn": 54.938049,
    "Fe": 55.845,
    "Co": 58.9332,
    "Ni": 58.6934,
    "Cu": 63.546,
    "Zn": 65.38,
    "Ga": 69.723,
    "Ge": 72.64,
    "As": 74.9216,
    "Se": 78.96,
    "Br": 79.904,
    "Kr": 83.8,
    "Rb": 85.4678,
    "Sr": 87.62,
    "Y": 88.90585,
    "Zr": 91.224,
    "Nb": 92.90638,
    "Mo": 95.94,
    "Ru": 101.07,
    "Rh": 102.9055,
    "Pd": 106.42,
    "Ag": 107.8682,
    "Cd": 112.411,
    "In": 114.818,
    "Sn": 118.71,
    "Sb": 121.76,
    "Te": 127.6,
    "I": 126.90447,
    "Xe": 131.293,
    "Cs": 132.90545,
    "Ba": 137.327,
    "La": 138.9055,
    "Ce": 140.116,
    "Pr": 140.90765,
    "Nd": 144.24,
    "Sm": 150.36,
    "Eu": 151.964,
    "Gd": 157.25,
    "Tb": 158.92534,
    "Dy": 162.5,
    "Ho": 164.93032,
    "Er": 167.259,
    "Tm": 168.93421,
    "Yb": 173.04,
    "Lu": 174.967,
    "Hf": 178.49,
    "Ta": 180.9479,
    "W": 183.84,
    "Re": 186.207,
    "Os": 190.23,
    "Ir": 192.217,
    "Pt": 195.078,
    "Au": 196.96655,
    "Hg": 200.59,
    "Tl": 204.3833,
    "Pb": 207.2,
    "Bi": 208.98038,
}

DEFAULT_CID_PLAN = (
    "962",
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
    "5950",
    "3672",
    "1983",
    "33032",
    "5288826",
    "54670067",
)


class FormulaError(ValueError):
    pass


def repo_root() -> Path:
    return ROOT


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def sha256_object(payload: Any) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def sha256_text(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def lf_bytes(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def resolve_under_root(root: Path, ref: str) -> Path:
    path = (root / ref).resolve()
    path.relative_to(root.resolve())
    return path


def rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def ordered_unique(values: list[Any]) -> list[Any]:
    seen: set[str] = set()
    out: list[Any] = []
    for value in values:
        key = canonical_json(value) if isinstance(value, (dict, list)) else str(value)
        if key in seen:
            continue
        seen.add(key)
        out.append(value)
    return out


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


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        if isinstance(value, bool):
            return default
        result = float(str(value).strip())
    except (TypeError, ValueError):
        return default
    return result if math.isfinite(result) else default


def is_number(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def load_requirements(root: Path) -> tuple[dict[str, Any], list[str]]:
    fallback = {
        "minimum_per_domain_n": 20,
        "required_domains": ["biology", "chemistry", "mathematics", "physics", "systems"],
        "required_source_separation_modes": ["prospective", "target_blind"],
    }
    path = root / REQUIREMENTS_REL
    if not path.exists():
        return fallback, ["REQUIREMENTS_MISSING::using_defaults"]
    try:
        payload = read_json(path)
    except Exception as exc:
        return fallback, [f"REQUIREMENTS_PARSE_ERROR::{exc.__class__.__name__}"]
    if not isinstance(payload, dict):
        return fallback, ["REQUIREMENTS_NOT_OBJECT::using_defaults"]
    return {**fallback, **payload}, []


def pubchem_property_url(cid: str | int) -> str:
    encoded_cid = quote(str(cid).strip(), safe=",")
    return f"{OFFICIAL_PUG_ENDPOINT_PREFIX}/{encoded_cid}/property/{OFFICIAL_PUG_PROPERTY_FIELDS}/JSON"


def has_pubchem_hint(path: Path) -> bool:
    lowered = path.as_posix().lower()
    return "pubchem" in lowered or "pug" in lowered


def is_generated_artifact(path: Path) -> bool:
    name = path.name
    return name == "README.md" or name.startswith(GENERATED_NAME_PREFIX)


def discover_snapshot_refs(root: Path, explicit_refs: list[str] | None = None) -> list[str]:
    if explicit_refs is not None:
        return ordered_unique([ref.replace("\\", "/") for ref in explicit_refs if ref.strip()])

    refs: list[str] = []
    if (root / DEFAULT_SNAPSHOT_REF).exists():
        refs.append(DEFAULT_SNAPSHOT_REF)
    for base_ref in DEFAULT_DISCOVERY_ROOTS:
        base = root / base_ref
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file() or is_generated_artifact(path):
                continue
            if path.suffix.lower() not in {".json", ".txt", ".ndjson"}:
                continue
            if not has_pubchem_hint(path):
                continue
            try:
                refs.append(rel(root, path))
            except ValueError:
                continue
    return ordered_unique(refs)


def parse_json_or_ndjson(path: Path) -> tuple[Any | None, list[str]]:
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text), []
    except json.JSONDecodeError as json_exc:
        rows: list[Any] = []
        for line_number, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                rows.append(json.loads(stripped))
            except json.JSONDecodeError:
                return None, [f"SNAPSHOT_PARSE_ERROR::{path.name}::line={line_number}::{json_exc.__class__.__name__}"]
        if rows:
            return rows, []
        return None, [f"SNAPSHOT_PARSE_ERROR::{path.name}::{json_exc.__class__.__name__}"]


def load_snapshot(root: Path, ref: str) -> dict[str, Any]:
    path = resolve_under_root(root, ref)
    if not path.exists():
        return {
            "ref": ref,
            "exists": False,
            "payload": None,
            "sha256": "",
            "byte_count": 0,
            "failures": [f"SNAPSHOT_MISSING::{ref}"],
        }
    if not path.is_file():
        return {
            "ref": ref,
            "exists": False,
            "payload": None,
            "sha256": "",
            "byte_count": 0,
            "failures": [f"SNAPSHOT_NOT_FILE::{ref}"],
        }
    payload, failures = parse_json_or_ndjson(path)
    return {
        "ref": ref,
        "exists": True,
        "payload": payload,
        "sha256": hashlib.sha256(lf_bytes(path)).hexdigest(),
        "byte_count": len(lf_bytes(path)),
        "failures": failures,
        "acquisition": {},
    }


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def target_projection_ref_keys() -> tuple[tuple[str, str, str], ...]:
    return (
        ("visible_projection_lock_ref", "visible_projection_lock_sha256", "VISIBLE_PROJECTION_LOCK"),
        ("prediction_materialization_lock_ref", "prediction_materialization_lock_sha256", "PREDICTION_MATERIALIZATION_LOCK"),
        ("target_projection_lock_ref", "target_projection_lock_sha256", "TARGET_PROJECTION_LOCK"),
    )


def target_projection_source(lock: dict[str, Any], request: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any] | None, str]:
    lock_has_projection_refs = any(
        as_str(lock.get(key)) or as_str(lock.get(hash_key))
        for key, hash_key, _label in target_projection_ref_keys()
    )
    if lock_has_projection_refs:
        return lock, None, "official_acquisition_lock"

    status = dict_or_empty(request.get("target_projection_lock"))
    if not status:
        return lock, None, "official_acquisition_lock"

    refs = dict_or_empty(status.get("refs"))
    expected_refs = dict_or_empty(status.get("expected_refs"))
    hashes = dict_or_empty(status.get("hashes"))
    return (
        {
            "declaration_ref": as_str(refs.get("declaration_ref"), as_str(expected_refs.get("declaration_ref"))),
            "declaration_sha256": as_str(hashes.get("declaration_sha256")),
            "snapshot_sha256": as_str(hashes.get("snapshot_sha256")),
            "visible_projection_lock_ref": as_str(
                refs.get("visible_projection_lock_ref"),
                as_str(refs.get("visible_lock_ref"), as_str(expected_refs.get("visible_lock_ref"))),
            ),
            "visible_projection_lock_sha256": as_str(hashes.get("visible_projection_lock_sha256")),
            "prediction_materialization_lock_ref": as_str(
                refs.get("prediction_materialization_lock_ref"),
                as_str(refs.get("prediction_lock_ref"), as_str(expected_refs.get("prediction_lock_ref"))),
            ),
            "prediction_materialization_lock_sha256": as_str(hashes.get("prediction_materialization_lock_sha256")),
            "target_projection_lock_ref": as_str(
                refs.get("target_projection_lock_ref"),
                as_str(refs.get("target_lock_ref"), as_str(expected_refs.get("target_lock_ref"))),
            ),
            "target_projection_lock_sha256": as_str(hashes.get("target_projection_lock_sha256")),
        },
        status,
        "packet_request_attachment",
    )


def validate_projection_snapshot_binding(
    root: Path,
    *,
    projection_snapshot_ref: str,
    projection_snapshot_sha256: str,
    official_snapshot_ref: str,
    official_snapshot_sha256: str,
    acquisition_id: str,
    blockers: list[str],
) -> None:
    if not projection_snapshot_ref:
        blockers.append(f"TARGET_PROJECTION_SNAPSHOT_REF_MISSING::{acquisition_id}")
        return
    try:
        snapshot_path = resolve_under_root(root, projection_snapshot_ref)
    except ValueError:
        blockers.append(f"TARGET_PROJECTION_SNAPSHOT_REF_OUTSIDE_REPO::{acquisition_id}")
        return
    if not snapshot_path.exists() or not snapshot_path.is_file():
        blockers.append(f"TARGET_PROJECTION_SNAPSHOT_MISSING::{acquisition_id}")
        return
    actual_sha = sha256_bytes(snapshot_path.read_bytes())
    if projection_snapshot_sha256 and actual_sha != projection_snapshot_sha256:
        blockers.append(f"TARGET_PROJECTION_SNAPSHOT_HASH_MISMATCH::{acquisition_id}")
    try:
        snapshot_payload = read_json(snapshot_path)
    except Exception as exc:
        blockers.append(f"TARGET_PROJECTION_SNAPSHOT_PARSE_FAILED::{acquisition_id}::{exc.__class__.__name__}")
        return
    rows = snapshot_payload.get("rows") if isinstance(snapshot_payload, dict) else None
    if not isinstance(rows, list) or not rows:
        blockers.append(f"TARGET_PROJECTION_SNAPSHOT_ROWS_MISSING::{acquisition_id}")
        return
    matching_rows = [
        row
        for row in rows
        if isinstance(row, dict)
        and (
            as_str(row.get("acquisition_id")) == acquisition_id
            or (len(rows) == 1 and not as_str(row.get("acquisition_id")))
        )
    ]
    if not matching_rows:
        blockers.append(f"TARGET_PROJECTION_SNAPSHOT_ROW_MISSING::{acquisition_id}")
        return
    row = matching_rows[0]
    if as_str(row.get("source_snapshot_ref")) and row.get("source_snapshot_ref") != official_snapshot_ref:
        blockers.append(f"TARGET_PROJECTION_SNAPSHOT_SOURCE_REF_MISMATCH::{acquisition_id}")
    if as_str(row.get("source_snapshot_sha256")) and row.get("source_snapshot_sha256") != official_snapshot_sha256:
        blockers.append(f"TARGET_PROJECTION_SNAPSHOT_SOURCE_HASH_MISMATCH::{acquisition_id}")


def load_declared_target_projection_lock(
    root: Path,
    lock: dict[str, Any],
    request: dict[str, Any],
    *,
    snapshot_ref: str,
    snapshot_sha256: str,
) -> dict[str, Any]:
    acquisition_id = as_str(lock.get("acquisition_id"), request_key(request))
    blockers: list[str] = []
    loaded: dict[str, dict[str, Any]] = {}
    refs: dict[str, str] = {}
    hashes: dict[str, str] = {}
    source, packet_status, source_kind = target_projection_source(lock, request)

    if packet_status is not None:
        if packet_status.get("verified") is not True or packet_status.get("valid") is not True:
            blockers.append(f"TARGET_PROJECTION_PACKET_ATTACHMENT_NOT_VERIFIED::{acquisition_id}")
        if dict_or_empty(packet_status.get("locks")) != target_lock_factory.NO_SEND_LOCKS:
            blockers.append(f"TARGET_PROJECTION_PACKET_NO_SEND_LOCKS_MISSING_OR_WEAK::{acquisition_id}")

    for ref_key, hash_key, label in target_projection_ref_keys():
        ref = as_str(source.get(ref_key))
        expected_sha = as_str(source.get(hash_key))
        if not ref:
            blockers.append(f"{label}_REF_MISSING::{acquisition_id}")
            continue
        if not expected_sha:
            blockers.append(f"{label}_HASH_MISSING::{acquisition_id}")
            continue
        refs[ref_key] = ref
        try:
            path = resolve_under_root(root, ref)
        except ValueError:
            blockers.append(f"{label}_REF_OUTSIDE_REPO::{acquisition_id}")
            continue
        if not path.exists() or not path.is_file():
            blockers.append(f"{label}_MISSING::{acquisition_id}")
            continue
        try:
            payload = read_json(path)
        except Exception as exc:
            blockers.append(f"{label}_PARSE_FAILED::{acquisition_id}::{exc.__class__.__name__}")
            continue
        if not isinstance(payload, dict):
            blockers.append(f"{label}_NOT_OBJECT::{acquisition_id}")
            continue
        actual_sha = sha256_object(payload)
        hashes[hash_key] = actual_sha
        if actual_sha != expected_sha:
            blockers.append(f"{label}_HASH_MISMATCH::{acquisition_id}")
        loaded[label] = payload

    declaration_ref = as_str(source.get("declaration_ref"))
    declaration = {}
    if packet_status is not None:
        if not declaration_ref:
            blockers.append(f"TARGET_PROJECTION_DECLARATION_REF_MISSING::{acquisition_id}")
        else:
            try:
                declaration_path = resolve_under_root(root, declaration_ref)
            except ValueError:
                blockers.append(f"TARGET_PROJECTION_DECLARATION_REF_OUTSIDE_REPO::{acquisition_id}")
            else:
                if not declaration_path.exists() or not declaration_path.is_file():
                    blockers.append(f"TARGET_PROJECTION_DECLARATION_MISSING::{acquisition_id}")
                else:
                    try:
                        raw_declaration = read_json(declaration_path)
                    except Exception as exc:
                        blockers.append(f"TARGET_PROJECTION_DECLARATION_PARSE_FAILED::{acquisition_id}::{exc.__class__.__name__}")
                    else:
                        if isinstance(raw_declaration, dict):
                            declaration = raw_declaration
                            actual_declaration_sha = sha256_object(
                                target_lock_factory.declaration_payload_for_hash(raw_declaration)
                            )
                            hashes["declaration_sha256"] = actual_declaration_sha
                            if actual_declaration_sha != as_str(source.get("declaration_sha256")):
                                blockers.append(f"TARGET_PROJECTION_DECLARATION_HASH_MISMATCH::{acquisition_id}")
                        else:
                            blockers.append(f"TARGET_PROJECTION_DECLARATION_NOT_OBJECT::{acquisition_id}")

    visible = loaded.get("VISIBLE_PROJECTION_LOCK", {})
    prediction = loaded.get("PREDICTION_MATERIALIZATION_LOCK", {})
    target = loaded.get("TARGET_PROJECTION_LOCK", {})
    if len(loaded) != len(target_projection_ref_keys()):
        return {"verified": False, "blockers": ordered_unique(blockers), "refs": refs, "hashes": hashes, "source_kind": source_kind}

    schema_expectations = (
        (visible, target_lock_factory.VISIBLE_LOCK_SCHEMA_ID, "VISIBLE_PROJECTION_LOCK_SCHEMA_MISMATCH"),
        (prediction, target_lock_factory.PREDICTION_LOCK_SCHEMA_ID, "PREDICTION_MATERIALIZATION_LOCK_SCHEMA_MISMATCH"),
        (target, target_lock_factory.TARGET_LOCK_SCHEMA_ID, "TARGET_PROJECTION_LOCK_SCHEMA_MISMATCH"),
    )
    for payload, schema_id, blocker in schema_expectations:
        if payload.get("schema_id") != schema_id:
            blockers.append(f"{blocker}::{acquisition_id}")

    visible_sha = hashes.get("visible_projection_lock_sha256", "")
    prediction_sha = hashes.get("prediction_materialization_lock_sha256", "")
    target_sha = hashes.get("target_projection_lock_sha256", "")
    if prediction.get("visible_projection_sha256") != visible_sha:
        blockers.append(f"PREDICTION_VISIBLE_LOCK_HASH_MISMATCH::{acquisition_id}")
    if target.get("visible_projection_sha256") != visible_sha:
        blockers.append(f"TARGET_VISIBLE_LOCK_HASH_MISMATCH::{acquisition_id}")
    if target.get("prediction_materialization_sha256") != prediction_sha:
        blockers.append(f"TARGET_PREDICTION_LOCK_HASH_MISMATCH::{acquisition_id}")

    projection_snapshot_ref = as_str(declaration.get("snapshot_ref"), as_str(visible.get("snapshot_ref")))
    projection_snapshot_sha256 = as_str(
        declaration.get("expected_snapshot_sha256"),
        as_str(source.get("snapshot_sha256"), as_str(visible.get("snapshot_sha256"))),
    )
    for payload, label in (
        (visible, "VISIBLE_PROJECTION_LOCK"),
        (target, "TARGET_PROJECTION_LOCK"),
    ):
        lock_snapshot_ref = as_str(payload.get("snapshot_ref"))
        lock_snapshot_sha256 = as_str(payload.get("snapshot_sha256"))
        if projection_snapshot_ref and lock_snapshot_ref != projection_snapshot_ref:
            blockers.append(f"{label}_SNAPSHOT_REF_MISMATCH::{acquisition_id}")
        if projection_snapshot_sha256 and lock_snapshot_sha256 != projection_snapshot_sha256:
            blockers.append(f"{label}_SNAPSHOT_HASH_MISMATCH::{acquisition_id}")
    if projection_snapshot_ref == snapshot_ref:
        if projection_snapshot_sha256 and projection_snapshot_sha256 != snapshot_sha256:
            blockers.append(f"TARGET_PROJECTION_SNAPSHOT_HASH_MISMATCH::{acquisition_id}")
    else:
        validate_projection_snapshot_binding(
            root,
            projection_snapshot_ref=projection_snapshot_ref,
            projection_snapshot_sha256=projection_snapshot_sha256,
            official_snapshot_ref=snapshot_ref,
            official_snapshot_sha256=snapshot_sha256,
            acquisition_id=acquisition_id,
            blockers=blockers,
        )

    expected_visible = list_of_strings(request.get("visible_training_fields")) or TARGET_PROJECTION_VISIBLE_FIELDS
    expected_target = [as_str(request.get("target_field"), TARGET_PROJECTION_TARGET_FIELDS[0])]
    actual_visible = list_of_strings(visible.get("visible_fields"))
    actual_target = list_of_strings(target.get("target_fields"))
    if actual_visible != expected_visible:
        blockers.append(f"VISIBLE_PROJECTION_FIELDS_MISMATCH::{acquisition_id}")
    if actual_target != expected_target:
        blockers.append(f"TARGET_PROJECTION_FIELDS_MISMATCH::{acquisition_id}")
    for visible_field in actual_visible:
        for target_field in actual_target:
            if target_lock_factory.paths_overlap(visible_field, target_field):
                blockers.append(f"TARGET_FIELD_IN_VISIBLE_PROJECTION::{acquisition_id}::{target_field}")

    row_count = as_int(visible.get("row_count"))
    target_row_count = as_int(target.get("row_count"))
    prediction_rows = prediction.get("prediction_rows")
    prediction_count = len(prediction_rows) if isinstance(prediction_rows, list) else -1
    if row_count <= 0 or target_row_count != row_count or prediction_count != row_count:
        blockers.append(f"TARGET_PROJECTION_ROW_COUNT_MISMATCH::{acquisition_id}")
    if isinstance(prediction_rows, list) and any(row.get("target_opened") is not False for row in prediction_rows if isinstance(row, dict)):
        blockers.append(f"PREDICTION_ROWS_OPEN_TARGET_BEFORE_SCORING::{acquisition_id}")
    separation = dict_or_empty(prediction.get("algorithmic_target_separation"))
    if separation.get("target_projection_read_before_prediction_materialization") is not False:
        blockers.append(f"TARGET_PROJECTION_READ_BEFORE_PREDICTION::{acquisition_id}")
    if separation.get("target_opened_after_prediction_materialization") is not True:
        blockers.append(f"TARGET_NOT_OPENED_AFTER_PREDICTION::{acquisition_id}")
    if target.get("target_opened_after_prediction_materialization") is not True:
        blockers.append(f"TARGET_LOCK_OPEN_ORDER_MISSING::{acquisition_id}")

    for payload, label in (
        (visible, "VISIBLE_PROJECTION_LOCK"),
        (prediction, "PREDICTION_MATERIALIZATION_LOCK"),
        (target, "TARGET_PROJECTION_LOCK"),
    ):
        if dict_or_empty(payload.get("locks")) != target_lock_factory.NO_SEND_LOCKS:
            blockers.append(f"{label}_NO_SEND_LOCKS_MISSING_OR_WEAK::{acquisition_id}")

    blockers = ordered_unique(blockers)
    return {
        "verified": not blockers,
        "blockers": blockers,
        "refs": refs,
        "hashes": hashes,
        "visible_fields": actual_visible,
        "target_fields": actual_target,
        "source_kind": source_kind,
    }


def source_separation_from_target_projection_lock(status: dict[str, Any]) -> dict[str, Any]:
    return {
        "mode": "target_blind",
        "kind": "target_projection_lock_verified_pubchem_formula_batch",
        "pre_target_lock": True,
        "target_hidden_until_scoring": True,
        "declared_before_scoring": True,
        "training_sources": [f"{ACQUISITION_REL}::target_projection_visible_fields(CID,MolecularFormula)"],
        "target_sources": [f"{ACQUISITION_REL}::target_projection_target_field(MolecularWeight)"],
        "training_manifest_sha256": as_str(status.get("hashes", {}).get("visible_projection_lock_sha256")),
        "target_manifest_sha256": as_str(status.get("hashes", {}).get("target_projection_lock_sha256")),
        "derived_from_target_projection_lock": True,
    }


def comparator_preregistration_contract() -> dict[str, Any]:
    baseline_payload = {
        "kind": COMPARATOR_BASELINE_KIND,
        "name": COMPARATOR_BASELINE_NAME,
        "prediction_rule": COMPARATOR_PREDICTION_RULE,
        "visible_formula_field": TARGET_PROJECTION_VISIBLE_FIELDS[1],
        "target_field": TARGET_PROJECTION_TARGET_FIELDS[0],
        "atom_count_mass_da": COMPARATOR_ATOM_COUNT_MASS_DA,
        "target_values_used_for_baseline_design": False,
        "required_material_margin_da": COMPARATOR_MATERIAL_MARGIN_DA,
    }
    return {
        "kind": COMPARATOR_BASELINE_KIND,
        "name": COMPARATOR_BASELINE_NAME,
        "prediction_rule": COMPARATOR_PREDICTION_RULE,
        "pre_registered": True,
        "preregistration_method": "machine_derived_from_legacy_seed_target_projection_contract",
        "visible_formula_field": TARGET_PROJECTION_VISIBLE_FIELDS[1],
        "atom_count_mass_da": COMPARATOR_ATOM_COUNT_MASS_DA,
        "required_material_margin_da": COMPARATOR_MATERIAL_MARGIN_DA,
        "target_values_used_for_baseline_design": False,
        "baseline_sha256": sha256_object(baseline_payload),
    }


def legacy_seed_metadata(record: dict[str, Any]) -> dict[str, Any]:
    for key in ("legacy_seed_lock", "legacy_seed_target_projection_lock", "target_projection_seed_lock"):
        value = record.get(key)
        if isinstance(value, dict):
            return value
    return {}


def is_legacy_seed_candidate(
    record: dict[str, Any],
    source_candidate: dict[str, Any],
    comparator: dict[str, Any],
) -> bool:
    if source_candidate or comparator or legacy_seed_metadata(record):
        return bool(legacy_seed_metadata(record)) or (not source_candidate and not comparator)
    return (
        as_str(record.get("CID"), as_str(record.get("cid")))
        and as_str(record.get("MolecularFormula"), as_str(record.get("molecular_formula")))
        and as_str(record.get("MolecularWeight"), as_str(record.get("molecular_weight")))
    )


def legacy_seed_lock_id(source_ref: str, source_sha256: str, record_index: int, record: dict[str, Any]) -> str:
    cid = as_str(record.get("CID"), as_str(record.get("cid"), f"record-{record_index}"))
    formula = as_str(record.get("MolecularFormula"), as_str(record.get("molecular_formula")))
    token = sha256_object(
        {
            "source_ref": source_ref,
            "source_sha256": source_sha256,
            "record_index": record_index,
            "cid": cid,
            "molecular_formula": formula,
            "visible_fields": TARGET_PROJECTION_VISIBLE_FIELDS,
            "target_fields": TARGET_PROJECTION_TARGET_FIELDS,
        }
    )[:16].upper()
    return f"OC133-CHEM-PUBCHEM-FORMULA-LEGACY-SEED-{token}"


def build_legacy_seed_projection_status(
    *,
    source_ref: str,
    source_sha256: str,
    record_index: int,
    record: dict[str, Any],
) -> dict[str, Any]:
    cid = as_str(record.get("CID"), as_str(record.get("cid"), f"record-{record_index}"))
    formula = as_str(record.get("MolecularFormula"), as_str(record.get("molecular_formula")))
    molecular_weight = as_float(as_str(record.get("MolecularWeight"), as_str(record.get("molecular_weight"))), math.nan)
    lock_id = legacy_seed_lock_id(source_ref, source_sha256, record_index, record)
    lock_ref = f"{LEGACY_SEED_LOCK_ROOT_REL}/{lock_id}.lock.json"
    visible_ref = f"{LEGACY_SEED_LOCK_ROOT_REL}/{lock_id}.visible_projection_lock.json"
    prediction_ref = f"{LEGACY_SEED_LOCK_ROOT_REL}/{lock_id}.prediction_materialization_lock.json"
    target_ref = f"{LEGACY_SEED_LOCK_ROOT_REL}/{lock_id}.target_projection_lock.json"
    declaration_ref = f"{LEGACY_SEED_LOCK_ROOT_REL}/{lock_id}.declaration.json"
    blockers: list[str] = []
    predicted = math.nan
    try:
        predicted, _trace = formula_weight(parse_formula(formula))
    except FormulaError as exc:
        blockers.append(f"LEGACY_SEED_FORMULA_PARSE_FAILED::{source_ref}::{record_index}::{exc}")
    if not math.isfinite(molecular_weight):
        blockers.append(f"LEGACY_SEED_TARGET_INVALID::{source_ref}::{record_index}")

    comparator_contract = comparator_preregistration_contract()
    declaration = {
        "schema_id": "OC133_CHEMISTRY_LEGACY_SEED_TARGET_PROJECTION_DECLARATION_v1",
        "release_id": RELEASE_ID,
        "generated_by": PLANNER_REF,
        "lock_id": lock_id,
        "declared_before_scoring": True,
        "source_snapshot_ref": source_ref,
        "source_snapshot_sha256": source_sha256,
        "row_index": record_index,
        "row_id_field": "CID",
        "visible_fields": TARGET_PROJECTION_VISIBLE_FIELDS,
        "target_fields": TARGET_PROJECTION_TARGET_FIELDS,
        "model_declaration": {
            "kind": "chemical_formula_weight",
            "formula_field": "MolecularFormula",
            "atomic_weight_table_id": ATOMIC_WEIGHT_TABLE_ID,
            "atomic_weights_sha256": sha256_object(ATOMIC_WEIGHTS),
        },
        "comparator_declaration": {
            "kind": COMPARATOR_BASELINE_KIND,
            "visible_formula_field": TARGET_PROJECTION_VISIBLE_FIELDS[1],
            "atom_count_mass_da": COMPARATOR_ATOM_COUNT_MASS_DA,
            "prediction_rule": COMPARATOR_PREDICTION_RULE,
            "baseline_sha256": comparator_contract["baseline_sha256"],
        },
        "residual_metric": "absolute_error_da",
        "uncertainty_policy": {"max_row_residual_da": MOLECULAR_WEIGHT_UNCERTAINTY_DA},
        "negative_controls": [
            {
                "control_id": "chemistry-pubchem-atom-count-carbon-equivalent-control",
                "kind": COMPARATOR_BASELINE_KIND,
                "required_material_margin_da": COMPARATOR_MATERIAL_MARGIN_DA,
            },
            {"control_id": "chemistry-pubchem-zero-da-control", "kind": "constant_zero_da"},
        ],
        "locks": dict(target_lock_factory.NO_SEND_LOCKS),
    }
    declaration_sha = sha256_object(declaration)
    visible_row = {
        "row_index": record_index,
        "row_id": cid,
        "visible": {"CID": record.get("CID", record.get("cid")), "MolecularFormula": formula},
    }
    visible_row_sha = sha256_object(visible_row)
    visible_projection_lock = {
        "schema_id": target_lock_factory.VISIBLE_LOCK_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "lock_id": lock_id,
        "declaration_ref": declaration_ref,
        "snapshot_ref": source_ref,
        "snapshot_sha256": source_sha256,
        "declaration_sha256": declaration_sha,
        "visible_fields": TARGET_PROJECTION_VISIBLE_FIELDS,
        "row_count": 1,
        "rows": [{**visible_row, "visible_row_sha256": visible_row_sha}],
        "locks": dict(target_lock_factory.NO_SEND_LOCKS),
    }
    visible_sha = sha256_object(visible_projection_lock)
    prediction_materialization_lock = {
        "schema_id": target_lock_factory.PREDICTION_LOCK_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "lock_id": lock_id,
        "declaration_ref": declaration_ref,
        "declaration_sha256": declaration_sha,
        "visible_projection_sha256": visible_sha,
        "model_declaration": declaration["model_declaration"],
        "comparator_declaration": declaration["comparator_declaration"],
        "prediction_rows": [
            {
                "row_index": record_index,
                "row_id": cid,
                "visible_row_sha256": visible_row_sha,
                "declaration_sha256": declaration_sha,
                "model_prediction": predicted if math.isfinite(predicted) else None,
                "comparator_prediction": atom_count_baseline_prediction(parse_formula(formula)) if not blockers else None,
                "target_opened": False,
            }
        ],
        "algorithmic_target_separation": {
            "prediction_inputs": "raw CID and MolecularFormula visible projection plus locked declarations only",
            "target_projection_read_before_prediction_materialization": False,
            "target_opened_after_prediction_materialization": True,
        },
        "locks": dict(target_lock_factory.NO_SEND_LOCKS),
    }
    prediction_sha = sha256_object(prediction_materialization_lock)
    target_projection_lock = {
        "schema_id": target_lock_factory.TARGET_LOCK_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "lock_id": lock_id,
        "declaration_ref": declaration_ref,
        "snapshot_ref": source_ref,
        "snapshot_sha256": source_sha256,
        "declaration_sha256": declaration_sha,
        "visible_projection_sha256": visible_sha,
        "prediction_materialization_sha256": prediction_sha,
        "target_fields": TARGET_PROJECTION_TARGET_FIELDS,
        "row_count": 1,
        "rows": [
            {
                "row_index": record_index,
                "row_id": cid,
                "target": {"MolecularWeight": record.get("MolecularWeight", record.get("molecular_weight"))},
                "source_row_sha256": sha256_object(record),
            }
        ],
        "target_opened_after_prediction_materialization": True,
        "locks": dict(target_lock_factory.NO_SEND_LOCKS),
    }
    target_sha = sha256_object(target_projection_lock)
    seed_lock = {
        "schema_id": LEGACY_SEED_LOCK_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "generated_by": PLANNER_REF,
        "lock_id": lock_id,
        "lock_ref": lock_ref,
        "source_snapshot_ref": source_ref,
        "source_snapshot_sha256": source_sha256,
        "record_index": record_index,
        "cid": cid,
        "visible_projection_lock_ref": visible_ref,
        "visible_projection_lock_sha256": visible_sha,
        "prediction_materialization_lock_ref": prediction_ref,
        "prediction_materialization_lock_sha256": prediction_sha,
        "target_projection_lock_ref": target_ref,
        "target_projection_lock_sha256": target_sha,
        "declaration_ref": declaration_ref,
        "declaration_sha256": declaration_sha,
        "comparator_baseline": comparator_contract,
        "locks": dict(target_lock_factory.NO_SEND_LOCKS),
        "support_policy": "Legacy seed upgrade proves projection order only; grand support remains gated by all empirical requirements.",
    }
    seed_lock_sha = sha256_object(seed_lock)
    status = {
        "required": True,
        "verified": not blockers,
        "valid": not blockers,
        "source_separation_derived": True,
        "source_kind": "legacy_seed_auto_projection",
        "generated_by": PLANNER_REF,
        "standard_factory": PLANNER_REF,
        "refs": {
            "legacy_seed_lock_ref": lock_ref,
            "declaration_ref": declaration_ref,
            "visible_projection_lock_ref": visible_ref,
            "prediction_materialization_lock_ref": prediction_ref,
            "target_projection_lock_ref": target_ref,
        },
        "hashes": {
            "legacy_seed_lock_sha256": seed_lock_sha,
            "declaration_sha256": declaration_sha,
            "snapshot_sha256": source_sha256,
            "visible_projection_lock_sha256": visible_sha,
            "prediction_materialization_lock_sha256": prediction_sha,
            "target_projection_lock_sha256": target_sha,
            "comparator_baseline_sha256": comparator_contract["baseline_sha256"],
        },
        "visible_fields": TARGET_PROJECTION_VISIBLE_FIELDS,
        "target_fields": TARGET_PROJECTION_TARGET_FIELDS,
        "blockers": blockers,
        "locks": dict(target_lock_factory.NO_SEND_LOCKS),
    }
    return {
        "lock_ref": lock_ref,
        "lock_sha256": seed_lock_sha,
        "lock_payload": seed_lock,
        "artifacts": {
            declaration_ref: declaration,
            visible_ref: visible_projection_lock,
            prediction_ref: prediction_materialization_lock,
            target_ref: target_projection_lock,
            lock_ref: seed_lock,
        },
        "target_projection_lock": status,
        "comparator_baseline": comparator_contract,
        "blockers": blockers,
    }


def validate_declared_legacy_seed_metadata(
    metadata: dict[str, Any],
    upgrade: dict[str, Any],
    *,
    source_ref: str,
    record_index: int,
) -> list[str]:
    if not metadata:
        return []
    status = dict_or_empty(upgrade.get("target_projection_lock"))
    refs = dict_or_empty(status.get("refs"))
    hashes = dict_or_empty(status.get("hashes"))
    failures: list[str] = []
    expected_lock_ref = as_str(metadata.get("lock_ref"), as_str(metadata.get("legacy_seed_lock_ref")))
    if expected_lock_ref and expected_lock_ref != as_str(upgrade.get("lock_ref")):
        failures.append(f"LEGACY_SEED_LOCK_REF_MISMATCH::{source_ref}::{record_index}")
    expected_lock_sha = as_str(metadata.get("lock_sha256"), as_str(metadata.get("legacy_seed_lock_sha256")))
    if expected_lock_sha and expected_lock_sha != as_str(upgrade.get("lock_sha256")):
        failures.append(f"LEGACY_SEED_LOCK_HASH_MISMATCH::{source_ref}::{record_index}")
    expected_comparator_sha = as_str(metadata.get("comparator_baseline_sha256"))
    if expected_comparator_sha and expected_comparator_sha != as_str(hashes.get("comparator_baseline_sha256")):
        failures.append(f"LEGACY_SEED_COMPARATOR_BASELINE_STALE::{source_ref}::{record_index}")
    for ref_key, hash_key, label in target_projection_ref_keys():
        expected_ref = as_str(metadata.get(ref_key))
        expected_sha = as_str(metadata.get(hash_key))
        if expected_ref and expected_ref != as_str(refs.get(ref_key)):
            failures.append(f"LEGACY_SEED_{label}_REF_MISMATCH::{source_ref}::{record_index}")
        if expected_sha and expected_sha != as_str(hashes.get(hash_key)):
            failures.append(f"LEGACY_SEED_{label}_HASH_MISMATCH::{source_ref}::{record_index}")
    if "locks" in metadata and dict_or_empty(metadata.get("locks")) != target_lock_factory.NO_SEND_LOCKS:
        failures.append(f"LEGACY_SEED_NO_SEND_LOCKS_MISSING_OR_WEAK::{source_ref}::{record_index}")
    return failures


def legacy_seed_upgrade_for_record(
    *,
    source_ref: str,
    source_sha256: str,
    record_index: int,
    record: dict[str, Any],
    source_candidate: dict[str, Any],
    comparator: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], list[str]]:
    if not is_legacy_seed_candidate(record, source_candidate, comparator):
        return {}, source_candidate, comparator, []
    upgrade = build_legacy_seed_projection_status(
        source_ref=source_ref,
        source_sha256=source_sha256,
        record_index=record_index,
        record=record,
    )
    metadata_failures = validate_declared_legacy_seed_metadata(
        legacy_seed_metadata(record),
        upgrade,
        source_ref=source_ref,
        record_index=record_index,
    )
    status = dict_or_empty(upgrade.get("target_projection_lock"))
    blockers = ordered_unique([*list_of_strings(status.get("blockers")), *metadata_failures])
    if blockers:
        status = {**status, "verified": False, "valid": False, "blockers": blockers}
        upgrade = {**upgrade, "target_projection_lock": status}
    acquisition = {
        "acquisition_id": as_str(dict_or_empty(status.get("refs")).get("legacy_seed_lock_ref")),
        "packet_ref": "",
        "packet_schema_id": "",
        "expected_local_snapshot_ref": source_ref,
        "official_endpoint_url": pubchem_property_url(as_str(record.get("CID"), as_str(record.get("cid")))),
        "lock_ref": as_str(upgrade.get("lock_ref")),
        "lock_sha256": as_str(upgrade.get("lock_sha256")),
        "declared_before_scoring_lock": status.get("verified") is True,
        "hash_policy": "sha256 over deterministic legacy seed target-projection contract",
        "required_fields": [*TARGET_PROJECTION_VISIBLE_FIELDS, *TARGET_PROJECTION_TARGET_FIELDS],
        "target_projection_lock": status,
        "legacy_seed_upgrade": True,
        "legacy_seed_artifacts": dict_or_empty(upgrade.get("artifacts")),
    }
    upgraded_source = (
        source_separation_from_target_projection_lock(status)
        if status.get("verified") is True
        else source_candidate
    )
    return acquisition, upgraded_source, dict_or_empty(upgrade.get("comparator_baseline")), blockers


def packet_acquisition_rows(packet: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("source_acquisition_requests", "exact_acquisition_requests", "missing_official_snapshots", "official_snapshots", "acquisition_requests", "snapshots"):
        rows = packet.get(key)
        if isinstance(rows, list):
            return [row for row in rows if isinstance(row, dict)]
    return []


def load_packet_requests(root: Path) -> list[dict[str, Any]]:
    path = root / ACQUISITION_REL
    if not path.exists():
        return []
    try:
        packet = read_json(path)
    except Exception:
        return []
    if not isinstance(packet, dict):
        return []
    requests: list[dict[str, Any]] = []
    for index, row in enumerate(packet_acquisition_rows(packet), start=1):
        acquisition_id = as_str(
            row.get("acquisition_id"),
            as_str(row.get("request_id"), f"OC133-CHEM-PUBCHEM-FORMULA-ACQ-{index:03d}"),
        )
        requests.append(
            {
                **row,
                "acquisition_id": acquisition_id,
                "packet_ref": ACQUISITION_REL,
                "packet_schema_id": as_str(packet.get("schema_id")),
            }
        )
    return requests


def request_key(row: dict[str, Any]) -> str:
    return as_str(row.get("acquisition_id")) or as_str(row.get("request_id")) or as_str(row.get("expected_local_snapshot_ref"))


def load_official_acquisition_snapshots(root: Path, packet_requests: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    requests_by_id = {request_key(row): row for row in packet_requests if request_key(row)}
    requests_by_expected_ref = {
        as_str(row.get("expected_local_snapshot_ref")): row
        for row in packet_requests
        if as_str(row.get("expected_local_snapshot_ref"))
    }
    locks_dir = root / OFFICIAL_ACQUISITION_LOCKS_REL
    if not locks_dir.exists():
        return [], []

    snapshots: list[dict[str, Any]] = []
    failures: list[str] = []
    for lock_path in sorted(locks_dir.glob("*.lock.json")):
        try:
            lock = read_json(lock_path)
        except Exception as exc:
            failures.append(f"OFFICIAL_ACQUISITION_LOCK_PARSE_FAILED::{rel(root, lock_path)}::{exc.__class__.__name__}")
            continue
        if not isinstance(lock, dict):
            failures.append(f"OFFICIAL_ACQUISITION_LOCK_NOT_OBJECT::{rel(root, lock_path)}")
            continue
        acquisition_id = as_str(lock.get("acquisition_id"))
        expected_ref = as_str(lock.get("expected_local_snapshot_ref"))
        request = requests_by_id.get(acquisition_id) or requests_by_expected_ref.get(expected_ref)
        if request is None:
            continue
        snapshot_ref = as_str(lock.get("snapshot_ref"))
        if not snapshot_ref.startswith(OFFICIAL_ACQUISITION_SNAPSHOTS_REL):
            failures.append(f"OFFICIAL_ACQUISITION_SNAPSHOT_REF_UNEXPECTED::{acquisition_id}::{snapshot_ref}")
            continue
        snapshot_path = resolve_under_root(root, snapshot_ref)
        if not snapshot_path.exists() or not snapshot_path.is_file():
            failures.append(f"OFFICIAL_ACQUISITION_SNAPSHOT_MISSING::{acquisition_id}::{snapshot_ref}")
            continue
        raw_bytes = snapshot_path.read_bytes()
        actual_sha = sha256_bytes(raw_bytes)
        declared_sha = as_str(lock.get("snapshot_sha256"))
        if actual_sha != declared_sha:
            failures.append(f"OFFICIAL_ACQUISITION_SNAPSHOT_HASH_MISMATCH::{acquisition_id}")
            continue
        if as_int(lock.get("http_status")) < 200 or as_int(lock.get("http_status")) >= 300:
            failures.append(f"OFFICIAL_ACQUISITION_HTTP_STATUS_NOT_SUCCESS::{acquisition_id}::{lock.get('http_status')}")
            continue
        if dict_or_empty(lock.get("locks")).get("no_send") is not True:
            failures.append(f"OFFICIAL_ACQUISITION_NO_SEND_LOCK_MISSING::{acquisition_id}")
            continue
        try:
            payload = json.loads(raw_bytes.decode("utf-8"))
        except Exception as exc:
            failures.append(f"OFFICIAL_ACQUISITION_SNAPSHOT_PARSE_FAILED::{acquisition_id}::{exc.__class__.__name__}")
            continue
        lock_ref = rel(root, lock_path)
        target_projection_status = load_declared_target_projection_lock(
            root,
            lock,
            request,
            snapshot_ref=snapshot_ref,
            snapshot_sha256=actual_sha,
        )
        failures.extend(target_projection_status.get("blockers", []))
        snapshots.append(
            {
                "ref": snapshot_ref,
                "exists": True,
                "payload": payload,
                "sha256": actual_sha,
                "byte_count": len(raw_bytes),
                "failures": [],
                "acquisition": {
                    "acquisition_id": acquisition_id,
                    "packet_ref": as_str(request.get("packet_ref"), ACQUISITION_REL),
                    "packet_schema_id": as_str(request.get("packet_schema_id")),
                    "expected_local_snapshot_ref": expected_ref,
                    "official_endpoint_url": as_str(lock.get("official_endpoint_url"), as_str(request.get("official_endpoint_url"))),
                    "lock_ref": lock_ref,
                    "lock_sha256": sha256_bytes(lock_path.read_bytes()),
                    "declared_before_scoring_lock": True,
                    "hash_policy": as_str(lock.get("hash_policy"), OFFICIAL_ACQUISITION_HASH_POLICY),
                    "required_fields": request.get("required_fields", []),
                    "target_projection_lock": target_projection_status,
                },
            }
        )
    return snapshots, failures


def dict_or_empty(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def list_of_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def source_separation_from_payload(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    raw = payload.get("source_separation", payload.get("oc133_source_separation", {}))
    return dict_or_empty(raw)


def comparator_from_payload(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    raw = payload.get("comparator_baseline", payload.get("oc133_comparator_baseline", {}))
    return dict_or_empty(raw)


def provenance_from_payload(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    raw = payload.get("snapshot_provenance", payload.get("provenance", {}))
    return dict_or_empty(raw)


def normalize_source_separation(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "mode": as_str(raw.get("mode"), "snapshot_replay"),
        "kind": as_str(raw.get("kind"), "snapshot_replay"),
        "pre_target_lock": raw.get("pre_target_lock") is True,
        "target_hidden_until_scoring": raw.get("target_hidden_until_scoring") is True,
        "declared_before_scoring": raw.get("declared_before_scoring") is True,
        "training_sources": ordered_unique(list_of_strings(raw.get("training_sources"))),
        "target_sources": ordered_unique(list_of_strings(raw.get("target_sources"))),
        "training_manifest_sha256": as_str(raw.get("training_manifest_sha256")),
        "target_manifest_sha256": as_str(raw.get("target_manifest_sha256")),
        "derived_from_target_projection_lock": raw.get("derived_from_target_projection_lock") is True,
    }


def pubchem_properties(payload: dict[str, Any]) -> list[dict[str, Any]]:
    table = dict_or_empty(payload.get("PropertyTable"))
    props = table.get("Properties")
    if not isinstance(props, list):
        return []
    return [row for row in props if isinstance(row, dict)]


def iter_payload_records(payload: Any) -> list[tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]]:
    records: list[tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]] = []
    batch_source = source_separation_from_payload(payload)
    batch_comparator = comparator_from_payload(payload)
    batch_provenance = provenance_from_payload(payload)

    def append(raw_record: Any) -> None:
        if not isinstance(raw_record, dict):
            return
        if pubchem_properties(raw_record):
            for prop in pubchem_properties(raw_record):
                records.append((prop, source_separation_from_payload(raw_record) or batch_source, comparator_from_payload(raw_record) or batch_comparator, provenance_from_payload(raw_record) or batch_provenance))
            return
        records.append(
            (
                raw_record,
                source_separation_from_payload(raw_record) or batch_source,
                comparator_from_payload(raw_record) or batch_comparator,
                provenance_from_payload(raw_record) or batch_provenance,
            )
        )

    if isinstance(payload, dict):
        if pubchem_properties(payload):
            append(payload)
            return records
        for key in ("snapshots", "records", "rows"):
            if isinstance(payload.get(key), list):
                for item in payload[key]:
                    append(item)
                return records
        append(payload)
    elif isinstance(payload, list):
        for item in payload:
            append(item)
    return records


def parse_count(text: str, pos: int) -> tuple[int, int]:
    start = pos
    while pos < len(text) and text[pos].isdigit():
        pos += 1
    if pos == start:
        return 1, pos
    return int(text[start:pos]), pos


def merge_counts(target: dict[str, int], source: dict[str, int], multiplier: int = 1) -> None:
    for element, count in source.items():
        target[element] += count * multiplier


def parse_formula_segment(text: str, pos: int = 0, terminator: str | None = None) -> tuple[dict[str, int], int]:
    counts: dict[str, int] = defaultdict(int)
    while pos < len(text):
        char = text[pos]
        if terminator and char == terminator:
            return dict(counts), pos + 1
        if char in ")]":
            raise FormulaError(f"unexpected_group_close::{char}")
        if char in "([":
            close = ")" if char == "(" else "]"
            nested, pos = parse_formula_segment(text, pos + 1, close)
            multiplier, pos = parse_count(text, pos)
            merge_counts(counts, nested, multiplier)
            continue
        if char.isupper():
            element = char
            pos += 1
            if pos < len(text) and text[pos].islower():
                element += text[pos]
                pos += 1
            count, pos = parse_count(text, pos)
            counts[element] += count
            continue
        raise FormulaError(f"unsupported_formula_character::{char}")
    if terminator:
        raise FormulaError(f"missing_group_close::{terminator}")
    return dict(counts), pos


def parse_formula(formula: str) -> dict[str, int]:
    cleaned = formula.strip().replace(" ", "").replace("\u00b7", ".")
    if not cleaned:
        raise FormulaError("formula_empty")
    total: dict[str, int] = defaultdict(int)
    for part in cleaned.split("."):
        if not part:
            continue
        multiplier, pos = parse_count(part, 0)
        counts, end = parse_formula_segment(part, pos)
        if end != len(part):
            raise FormulaError(f"formula_parse_incomplete::{formula}")
        merge_counts(total, counts, multiplier)
    if not total:
        raise FormulaError("formula_empty")
    unknown = sorted(element for element in total if element not in ATOMIC_WEIGHTS)
    if unknown:
        raise FormulaError(f"unknown_atomic_weight::{','.join(unknown)}")
    return dict(sorted(total.items()))


def formula_weight(composition: dict[str, int]) -> tuple[float, list[dict[str, Any]]]:
    trace: list[dict[str, Any]] = []
    total = 0.0
    for element, count in composition.items():
        atomic_weight = ATOMIC_WEIGHTS[element]
        contribution = atomic_weight * count
        trace.append(
            {
                "element": element,
                "count": count,
                "atomic_weight": atomic_weight,
                "contribution": contribution,
            }
        )
        total += contribution
    return total, trace


def atom_count_baseline_prediction(composition: dict[str, int]) -> float:
    return sum(composition.values()) * COMPARATOR_ATOM_COUNT_MASS_DA


def comparator_baseline_sha256() -> str:
    return comparator_preregistration_contract()["baseline_sha256"]


def comparator_uses_target(comparator: dict[str, Any]) -> bool:
    if comparator.get("target_values_used_for_baseline_design") is True:
        return True
    if comparator.get("uses_target_values") is True or comparator.get("uses_target") is True:
        return True
    for key in ("leakage_fields", "prediction_inputs", "fields_used", "inputs"):
        values = comparator.get(key)
        if isinstance(values, str):
            values = [values]
        if isinstance(values, list) and any(str(value) in TARGET_PROJECTION_TARGET_FIELDS for value in values):
            return True
    return False


def comparator_is_trivial_zero(comparator: dict[str, Any]) -> bool:
    name = as_str(comparator.get("name")).lower()
    rule = as_str(comparator.get("prediction_rule")).lower()
    kind = as_str(comparator.get("kind")).lower()
    return (
        kind in {"constant_zero_da", "zero_da", "constant"}
        or "zero-da" in name
        or "zero molecular weight" in rule
        or comparator.get("prediction_value") == 0
        or comparator.get("value") == 0
    )


def normalize_comparator(comparator: dict[str, Any]) -> dict[str, Any]:
    if not comparator:
        return comparator_preregistration_contract()
    return {
        **comparator,
        "kind": as_str(comparator.get("kind")),
        "name": as_str(comparator.get("name")),
        "prediction_rule": as_str(comparator.get("prediction_rule")),
        "pre_registered": comparator.get("pre_registered") is True,
    }


def comparator_registration_failures(comparator: dict[str, Any], row_id: str) -> list[str]:
    failures: list[str] = []
    if comparator.get("pre_registered") is not True:
        failures.append(f"COMPARATOR_BASELINE_NOT_PREREGISTERED::{row_id}")
    if comparator_uses_target(comparator):
        failures.append(f"COMPARATOR_TARGET_LEAKAGE::{row_id}")
    expected = comparator_preregistration_contract()
    if comparator_is_trivial_zero(comparator):
        failures.append(f"TRIVIAL_COMPARATOR_BASELINE_NOT_ALLOWED::{row_id}")
    elif (
        as_str(comparator.get("kind")) != COMPARATOR_BASELINE_KIND
        or as_str(comparator.get("name")) != COMPARATOR_BASELINE_NAME
        or as_str(comparator.get("prediction_rule")) != COMPARATOR_PREDICTION_RULE
    ):
        failures.append(f"NONTRIVIAL_COMPARATOR_REQUIRED::{row_id}")
    declared_sha = as_str(comparator.get("baseline_sha256"))
    if declared_sha and declared_sha != expected["baseline_sha256"]:
        failures.append(f"COMPARATOR_BASELINE_PREREGISTRATION_STALE::{row_id}")
    return ordered_unique(failures)


def build_negative_controls(
    *,
    row_id: str,
    observed: float,
    model_residual: float,
    composition: dict[str, int],
) -> list[dict[str, Any]]:
    controls: list[dict[str, Any]] = []
    for control_id, description, prediction, nontrivial in (
        (
            f"chemistry-pubchem-atom-count-carbon-equivalent-control::{row_id}",
            "replace element-specific formula mass with a visible-formula atom-count baseline and require a materially larger residual",
            atom_count_baseline_prediction(composition),
            True,
        ),
        (
            f"chemistry-pubchem-zero-da-sanity-control::{row_id}",
            "replace formula-derived mass with a zero-Da null sanity control and require a materially larger residual",
            0.0,
            False,
        ),
    ):
        residual = abs(prediction - observed)
        margin = residual - model_residual
        controls.append(
            {
                "control_id": control_id,
                "description": description,
                "prediction": prediction,
                "residual": residual,
                "material_margin_da": margin,
                "required_material_margin_da": COMPARATOR_MATERIAL_MARGIN_DA,
                "nontrivial": nontrivial,
                "rejected": margin >= COMPARATOR_MATERIAL_MARGIN_DA,
                "status": "REJECTED" if margin >= COMPARATOR_MATERIAL_MARGIN_DA else "NOT_REJECTED",
            }
        )
    return controls


def official_url_is_pubchem(url: str) -> bool:
    lowered = url.lower()
    return lowered.startswith("https://pubchem.ncbi.nlm.nih.gov/rest/pug/")


def provenance_status(provenance: dict[str, Any], cid: str, source_ref: str) -> tuple[bool, str, str]:
    source = as_str(provenance.get("official_source"), as_str(provenance.get("source"), ""))
    url = as_str(provenance.get("official_url"), as_str(provenance.get("source_url"), ""))
    if not url and cid:
        url = pubchem_property_url(cid)
    source_ok = "pubchem" in source.lower() or bool(cid)
    url_ok = official_url_is_pubchem(url)
    if source_ok and url_ok:
        return True, source or "PubChem PUG REST", url
    return False, source or "UNDECLARED_PUBCHEM_PROVENANCE", url or f"{source_ref}::NO_OFFICIAL_PUG_REST_URL_DECLARED"


def row_hash(row: dict[str, Any]) -> str:
    clean = {key: value for key, value in row.items() if key not in {"row_hash", "row_hash_policy"}}
    return sha256_object(clean)


def build_row(
    *,
    record: dict[str, Any],
    source_ref: str,
    source_sha256: str,
    record_index: int,
    comparator: dict[str, Any],
    provenance: dict[str, Any],
    acquisition: dict[str, Any] | None = None,
) -> tuple[dict[str, Any] | None, list[str]]:
    acquisition = acquisition or {}
    cid = as_str(record.get("CID"), as_str(record.get("cid"), f"record-{record_index}"))
    formula = as_str(record.get("MolecularFormula"), as_str(record.get("molecular_formula")))
    molecular_weight_text = as_str(record.get("MolecularWeight"), as_str(record.get("molecular_weight")))
    failures: list[str] = []
    if not formula:
        return None, [f"PUBCHEM_MOLECULAR_FORMULA_MISSING::{source_ref}::{record_index}"]
    if not molecular_weight_text:
        return None, [f"PUBCHEM_MOLECULAR_WEIGHT_MISSING::{source_ref}::{record_index}"]
    observed = as_float(molecular_weight_text, math.nan)
    if not math.isfinite(observed):
        return None, [f"PUBCHEM_MOLECULAR_WEIGHT_INVALID::{source_ref}::{record_index}::{molecular_weight_text}"]
    try:
        composition = parse_formula(formula)
        predicted, trace = formula_weight(composition)
    except FormulaError as exc:
        return None, [f"FORMULA_PARSE_FAILED::{source_ref}::{record_index}::{exc}"]

    model_residual = abs(predicted - observed)
    row_id_hash = sha256_object({"source_ref": source_ref, "record_index": record_index, "cid": cid, "formula": formula})[:12].upper()
    row_id = f"CHEM-PUBCHEM-FORMULA-{record_index:04d}-{row_id_hash}"
    if acquisition:
        provenance = {
            **provenance,
            "official_source": "PubChem PUG REST",
            "official_url": acquisition.get("official_endpoint_url"),
        }
    comparator = normalize_comparator(comparator)
    comparator_prediction = 0.0 if comparator_is_trivial_zero(comparator) else atom_count_baseline_prediction(composition)
    comparator_residual = abs(comparator_prediction - observed)
    comparator_failures = comparator_registration_failures(comparator, row_id)
    negative_controls = build_negative_controls(
        row_id=row_id,
        observed=observed,
        model_residual=model_residual,
        composition=composition,
    )
    nontrivial_controls = [control for control in negative_controls if control.get("nontrivial") is True]
    all_controls_rejected = bool(negative_controls) and all(control.get("rejected") is True for control in negative_controls)
    nontrivial_controls_rejected = bool(nontrivial_controls) and all(
        control.get("rejected") is True for control in nontrivial_controls
    )
    primary_control = nontrivial_controls[0] if nontrivial_controls else negative_controls[0]
    comparator_name = as_str(comparator.get("name"), COMPARATOR_BASELINE_NAME)
    comparator_rule = as_str(comparator.get("prediction_rule"), COMPARATOR_PREDICTION_RULE)
    comparator_pre_registered = comparator.get("pre_registered") is True
    official_ok, official_source, official_url = provenance_status(provenance, cid, source_ref)
    target_projection_status = dict_or_empty(acquisition.get("target_projection_lock"))
    row = {
        "observation_id": row_id,
        "claim_id": f"OC133-CHEMISTRY-PUBCHEM-FORMULA-{record_index:04d}",
        "task_type": "pubchem_formula_to_molecular_weight_reconstruction",
        "snapshot_ref": source_ref,
        "snapshot_sha256": source_sha256,
        "source_snapshot_hash": source_sha256,
        "source_snapshot_hash_policy": acquisition.get("hash_policy", SNAPSHOT_HASH_POLICY),
        "acquisition_id": as_str(acquisition.get("acquisition_id")),
        "expected_local_snapshot_ref": as_str(acquisition.get("expected_local_snapshot_ref")),
        "lock_ref": as_str(acquisition.get("lock_ref")),
        "lock_sha256": as_str(acquisition.get("lock_sha256")),
        "declared_before_scoring_lock": acquisition.get("declared_before_scoring_lock") is True,
        "target_projection_lock_verified": target_projection_status.get("verified") is True,
        "target_projection_lock_refs": target_projection_status.get("refs", {}),
        "target_projection_lock_hashes": target_projection_status.get("hashes", {}),
        "acquisition_packet_ref": as_str(acquisition.get("packet_ref")),
        "record_index": record_index,
        "cid": cid,
        "official_source_confirmed": official_ok,
        "official_source": official_source,
        "official_source_url": official_url,
        "molecular_formula": formula,
        "atomic_composition": composition,
        "atomic_weight_table_id": ATOMIC_WEIGHT_TABLE_ID,
        "atomic_weight_source_note": ATOMIC_WEIGHT_SOURCE_NOTE,
        "formula_evaluation_trace": trace,
        "training_source": f"{source_ref}::record={record_index}::visible_field(MolecularFormula)::CID={cid}",
        "target_source": f"{source_ref}::record={record_index}::target_field(MolecularWeight)::CID={cid}",
        "formula": "sum(count[element] * fixed_atomic_weight[element])",
        "formula_inputs": {
            "molecular_formula": formula,
            "atomic_composition": composition,
            "atomic_weight_table_id": ATOMIC_WEIGHT_TABLE_ID,
        },
        "prediction_inputs": {
            "visible_fields": ["CID", "MolecularFormula"],
            "target_field": "MolecularWeight",
        },
        "predicted_value": predicted,
        "observed_value": observed,
        "observed_value_text": molecular_weight_text,
        "uncertainty": MOLECULAR_WEIGHT_UNCERTAINTY_DA,
        "uncertainty_basis": "fixed 0.05 Da tolerance for PubChem display/API rounding and fixed-table rounding",
        "model_residual": model_residual,
        "residual_within_uncertainty": model_residual <= MOLECULAR_WEIGHT_UNCERTAINTY_DA,
        "comparator_baseline_name": comparator_name,
        "comparator_baseline_kind": as_str(comparator.get("kind")),
        "comparator_prediction_rule": comparator_rule,
        "comparator_pre_registered": comparator_pre_registered,
        "comparator_baseline_sha256": as_str(comparator.get("baseline_sha256")),
        "comparator_required_material_margin_da": COMPARATOR_MATERIAL_MARGIN_DA,
        "comparator_prediction": comparator_prediction,
        "comparator_residual": comparator_residual,
        "comparator_material_margin_da": comparator_residual - model_residual,
        "comparator_material_margin_met": comparator_residual - model_residual >= COMPARATOR_MATERIAL_MARGIN_DA,
        "comparator_validation_failures": comparator_failures,
        "negative_controls": negative_controls,
        "nontrivial_negative_controls_rejected": nontrivial_controls_rejected,
        "negative_control_id": primary_control["control_id"],
        "negative_control_description": primary_control["description"],
        "negative_control_rejected": all_controls_rejected,
        "negative_control_status": "REJECTED" if all_controls_rejected else "NOT_REJECTED",
        "falsifier": "formula-derived residual exceeds declared PubChem MolecularWeight tolerance, target leakage is detected, or a nontrivial comparator/control is not worse by the material margin",
        "falsifier_status": "TRIGGERED"
        if (
            model_residual > MOLECULAR_WEIGHT_UNCERTAINTY_DA
            or comparator_residual - model_residual < COMPARATOR_MATERIAL_MARGIN_DA
            or not all_controls_rejected
            or comparator_failures
        )
        else "NOT_TRIGGERED",
    }
    if not official_ok:
        failures.append(f"OFFICIAL_PUBCHEM_PROVENANCE_MISSING::{row_id}")
    failures.extend(comparator_failures)
    row["row_hash"] = row_hash(row)
    row["row_hash_policy"] = ROW_HASH_POLICY
    return row, failures


def select_source_separation(candidates: list[dict[str, Any]]) -> tuple[dict[str, Any], list[str]]:
    normalized = [normalize_source_separation(candidate) for candidate in candidates if candidate]
    non_default = [candidate for candidate in normalized if candidate["mode"] != "snapshot_replay"]
    if not non_default:
        return normalize_source_separation({}), ["SOURCE_SEPARATION_MISSING::defaulting_to_snapshot_replay"]
    def contract_key(candidate: dict[str, Any]) -> dict[str, Any]:
        return {
            key: candidate.get(key)
            for key in (
                "mode",
                "kind",
                "pre_target_lock",
                "target_hidden_until_scoring",
                "declared_before_scoring",
                "training_sources",
                "target_sources",
                "derived_from_target_projection_lock",
            )
        }

    unique_keys = ordered_unique([contract_key(candidate) for candidate in non_default])
    failures: list[str] = []
    if len(unique_keys) > 1:
        failures.append("SOURCE_SEPARATION_CONFLICT_ACROSS_SNAPSHOTS")
    selected = dict(non_default[0])
    training_hashes = ordered_unique(
        [as_str(candidate.get("training_manifest_sha256")) for candidate in non_default if candidate.get("training_manifest_sha256")]
    )
    target_hashes = ordered_unique(
        [as_str(candidate.get("target_manifest_sha256")) for candidate in non_default if candidate.get("target_manifest_sha256")]
    )
    if len(training_hashes) > 1:
        selected["training_manifest_sha256"] = sha256_object(training_hashes)
    if len(target_hashes) > 1:
        selected["target_manifest_sha256"] = sha256_object(target_hashes)
    return selected, failures


def validate_source_separation(source: dict[str, Any], requirements: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    allowed_modes = {str(mode) for mode in requirements.get("required_source_separation_modes", ["target_blind", "prospective"])}
    if source.get("mode") not in allowed_modes:
        failures.append(f"SOURCE_SEPARATION_MODE_NOT_ALLOWED::{source.get('mode')}")
    if source.get("kind") in {"snapshot_replay", "single_raw_snapshot", "snapshot_only", "replay_only"}:
        failures.append(f"TARGET_SEPARATION_NOT_REAL::{source.get('kind')}")
    if source.get("pre_target_lock") is not True:
        failures.append("PRE_TARGET_LOCK_REQUIRED")
    if source.get("target_hidden_until_scoring") is not True:
        failures.append("TARGET_HIDDEN_UNTIL_SCORING_REQUIRED")
    if source.get("declared_before_scoring") is not True:
        failures.append("SOURCE_SEPARATION_NOT_DECLARED_BEFORE_SCORING")
    if source.get("derived_from_target_projection_lock") is not True:
        failures.append("TARGET_PROJECTION_LOCK_REQUIRED_FOR_SOURCE_SEPARATION")
    training_sources = list_of_strings(source.get("training_sources"))
    target_sources = list_of_strings(source.get("target_sources"))
    if not training_sources or not target_sources:
        failures.append("TRAINING_AND_TARGET_SOURCES_REQUIRED")
    if set(training_sources) & set(target_sources):
        failures.append("TRAINING_TARGET_SOURCE_OVERLAP")
    return ordered_unique(failures)


def validate_rows(rows: list[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    required = (
        "observation_id",
        "training_source",
        "target_source",
        "source_snapshot_hash",
        "lock_ref",
        "molecular_formula",
        "formula_inputs",
        "prediction_inputs",
        "predicted_value",
        "observed_value",
        "comparator_prediction",
        "model_residual",
        "comparator_residual",
        "comparator_material_margin_da",
        "negative_control_id",
        "negative_control_description",
        "negative_control_status",
        "falsifier",
        "falsifier_status",
        "row_hash",
    )
    for row in rows:
        row_id = as_str(row.get("observation_id"), "unknown")
        for field in required:
            if row.get(field) in (None, ""):
                failures.append(f"ROW_FIELD_MISSING::{row_id}::{field}")
        for field in (
            "predicted_value",
            "observed_value",
            "comparator_prediction",
            "model_residual",
            "comparator_residual",
            "comparator_material_margin_da",
            "uncertainty",
        ):
            if not is_number(row.get(field)):
                failures.append(f"ROW_NUMERIC_INVALID::{row_id}::{field}")
        failures.extend(list_of_strings(row.get("comparator_validation_failures")))
        if row.get("training_source") == row.get("target_source"):
            failures.append(f"ROW_SOURCE_OVERLAP::{row_id}")
        if row.get("official_source_confirmed") is not True:
            failures.append(f"OFFICIAL_PUBCHEM_PROVENANCE_REQUIRED::{row_id}")
        if row.get("declared_before_scoring_lock") is not True:
            failures.append(f"DECLARED_BEFORE_SCORING_LOCK_MISSING::{row_id}")
        if row.get("comparator_pre_registered") is not True:
            failures.append(f"COMPARATOR_BASELINE_NOT_PREREGISTERED::{row_id}")
        if row.get("residual_within_uncertainty") is not True:
            failures.append(f"RESIDUAL_EXCEEDS_UNCERTAINTY::{row_id}")
        if row.get("negative_control_rejected") is not True:
            failures.append(f"NEGATIVE_CONTROL_NOT_REJECTED::{row_id}")
        if row.get("nontrivial_negative_controls_rejected") is not True:
            failures.append(f"NONTRIVIAL_NEGATIVE_CONTROL_NOT_REJECTED::{row_id}")
        if row.get("comparator_material_margin_met") is not True:
            failures.append(f"COMPARATOR_NOT_WORSE_THAN_MODEL_BY_MATERIAL_MARGIN::{row_id}")
        if as_float(row.get("comparator_residual")) - as_float(row.get("model_residual")) < COMPARATOR_MATERIAL_MARGIN_DA:
            failures.append(f"COMPARATOR_NOT_WORSE_THAN_MODEL_BY_MATERIAL_MARGIN::{row_id}")
        if row.get("falsifier_status") != "NOT_TRIGGERED":
            failures.append(f"FALSIFIER_TRIGGERED::{row_id}")
    if rows and not all(row.get("declared_before_scoring_lock") is True for row in rows):
        failures.append("DECLARED_BEFORE_SCORING_LOCK_REQUIRED")
    return ordered_unique(failures)


def residual_summary(rows: list[dict[str, Any]]) -> dict[str, float]:
    if not rows:
        return {"model": 0.0, "comparator": 0.0, "superiority_margin": 0.0}
    model = sum(as_float(row.get("model_residual")) for row in rows) / len(rows)
    comparator = sum(as_float(row.get("comparator_residual")) for row in rows) / len(rows)
    return {
        "model": model,
        "comparator": comparator,
        "superiority_margin": comparator - model,
    }


def clean_pack_source(source: dict[str, Any]) -> dict[str, Any]:
    return {
        "mode": source.get("mode"),
        "pre_target_lock": source.get("pre_target_lock") is True,
        "target_hidden_until_scoring": source.get("target_hidden_until_scoring") is True,
        "training_sources": list_of_strings(source.get("training_sources")),
        "target_sources": list_of_strings(source.get("target_sources")),
    }


def build_pack(rows: list[dict[str, Any]], source: dict[str, Any], *, support_allowed: bool) -> dict[str, Any]:
    residuals = residual_summary(rows)
    maximum_model_residual = max([as_float(row.get("model_residual")) for row in rows], default=0.0)
    return {
        "schema_id": grand_factory.EVIDENCE_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "capability_owner": CAPABILITY_OWNER,
        "evidence_pack_id": "OC133-GRAND-CHEMISTRY-PUBCHEM-FORMULA-BATCH",
        "domain": "chemistry",
        "source_separation": clean_pack_source(source),
        "n": len(rows),
        "model_under_test": "fixed atomic-weight molecular-formula sum compared to PubChem MolecularWeight",
        "comparator_baseline": {
            "kind": rows[0]["comparator_baseline_kind"] if rows else COMPARATOR_BASELINE_KIND,
            "name": rows[0]["comparator_baseline_name"] if rows else COMPARATOR_BASELINE_NAME,
            "prediction_rule": rows[0]["comparator_prediction_rule"] if rows else COMPARATOR_PREDICTION_RULE,
            "pre_registered": bool(rows) and all(row.get("comparator_pre_registered") is True for row in rows),
            "baseline_sha256": rows[0].get("comparator_baseline_sha256", "") if rows else comparator_baseline_sha256(),
            "required_material_margin_da": COMPARATOR_MATERIAL_MARGIN_DA,
        },
        "uncertainty": {
            "metric": "mean absolute residual in daltons",
            "method": "fixed 0.05 Da per-row PubChem display/API rounding tolerance",
            "interval": [0.0, max(MOLECULAR_WEIGHT_UNCERTAINTY_DA, maximum_model_residual)],
        },
        "residuals": residuals,
        "negative_controls": [
            {
                "control_id": control["control_id"],
                "description": control["description"],
                "nontrivial": control.get("nontrivial") is True,
                "material_margin_da": control.get("material_margin_da"),
                "required_material_margin_da": control.get("required_material_margin_da"),
                "rejected": control.get("rejected") is True,
            }
            for row in rows
            for control in row.get("negative_controls", [])
        ],
        "falsifiers": ordered_unique([as_str(row.get("falsifier")) for row in rows if row.get("falsifier")]),
        "grand_toe_support_allowed": support_allowed,
    }


def missing_pubchem_requests(
    rows: list[dict[str, Any]],
    minimum_n: int,
    packet_requests: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    observed_cids = {as_str(row.get("cid")) for row in rows if row.get("cid")}
    missing_n = max(0, minimum_n - len(rows))
    requests: list[dict[str, Any]] = []
    acquired_ids = {as_str(row.get("acquisition_id")) for row in rows if row.get("acquisition_id")}
    acquired_expected_refs = {
        as_str(row.get("expected_local_snapshot_ref")) for row in rows if row.get("expected_local_snapshot_ref")
    }
    for request in packet_requests or []:
        if len(requests) >= missing_n:
            break
        acquisition_id = as_str(request.get("acquisition_id"))
        expected_ref = as_str(request.get("expected_local_snapshot_ref"))
        if acquisition_id in acquired_ids or expected_ref in acquired_expected_refs:
            continue
        requests.append(
            {
                "request_id": as_str(request.get("request_id"), acquisition_id),
                "acquisition_id": acquisition_id,
                "cid": as_str(request.get("cid")),
                "method": as_str(request.get("method"), "GET"),
                "official_endpoint_url": as_str(request.get("official_endpoint_url")),
                "expected_local_snapshot_ref": expected_ref,
                "required_fields": request.get("required_fields", OFFICIAL_PUG_PROPERTY_FIELDS.split(",")),
                "target_field": as_str(request.get("target_field"), "MolecularWeight"),
                "visible_training_fields": request.get("visible_training_fields", ["CID", "MolecularFormula"]),
                "missing_reason": "pinned official acquisition lock/snapshot is absent or failed validation",
                "no_send_lock": True,
            }
        )
    if len(requests) >= missing_n:
        return requests

    missing_cids = [cid for cid in DEFAULT_CID_PLAN if cid not in observed_cids]
    for idx, cid in enumerate(missing_cids[:missing_n], start=1):
        if len(requests) >= missing_n:
            break
        requests.append(
            {
                "request_id": f"OC133-CHEM-PUBCHEM-FORMULA-ACQ-{idx:03d}",
                "acquisition_id": f"OC133-CHEM-PUBCHEM-FORMULA-ACQ-{idx:03d}",
                "cid": cid,
                "method": "GET",
                "official_endpoint_url": pubchem_property_url(cid),
                "expected_local_snapshot_ref": f"{OUTPUT_ROOT_REL}/raw/pubchem_cid_{cid}_properties.json",
                "required_fields": OFFICIAL_PUG_PROPERTY_FIELDS.split(","),
                "target_field": "MolecularWeight",
                "visible_training_fields": ["CID", "MolecularFormula"],
                "missing_reason": "additional pinned PubChem PUG REST formula/weight row required for N>=20 chemistry batch",
                "no_send_lock": True,
            }
        )
    return requests


def build_tamper_tests(rows: list[dict[str, Any]], snapshot_hashes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "test_id": "formula_field_target_blind_split_declared",
            "description": "training sources must name MolecularFormula while target sources name MolecularWeight",
            "sample_total": len(rows),
            "passed": bool(rows)
            and all("MolecularFormula" in row["training_source"] and "MolecularWeight" in row["target_source"] for row in rows),
        },
        {
            "test_id": "snapshot_hashes_present",
            "description": "every loaded PubChem snapshot receives an LF-normalized hash before scoring",
            "sample_total": len(snapshot_hashes),
            "passed": bool(snapshot_hashes) and all(item.get("snapshot_sha256") for item in snapshot_hashes),
        },
        {
            "test_id": "negative_controls_rejected",
            "description": "every row-level nontrivial atom-count control and zero-Da sanity control must be worse than the formula residual by the material margin",
            "sample_total": len(rows),
            "passed": bool(rows)
            and all(row.get("negative_control_rejected") is True for row in rows)
            and all(row.get("nontrivial_negative_controls_rejected") is True for row in rows),
        },
        {
            "test_id": "fixed_atomic_table_bound",
            "description": "every row binds the fixed local atomic-weight table identifier and evaluation trace",
            "sample_total": len(rows),
            "passed": bool(rows)
            and all(row.get("atomic_weight_table_id") == ATOMIC_WEIGHT_TABLE_ID and row.get("formula_evaluation_trace") for row in rows),
        },
        {
            "test_id": "target_projection_lock_refs_present",
            "description": "every scored row must carry a machine-derived target projection lock and lock_ref before support can pass",
            "sample_total": len(rows),
            "passed": bool(rows)
            and all(
                row.get("lock_ref")
                and row.get("declared_before_scoring_lock") is True
                and row.get("target_projection_lock_verified") is True
                for row in rows
            ),
        },
        {
            "test_id": "comparator_preregistration_locked",
            "description": "the nontrivial formula atom-count comparator must be preregistered by a lock or deterministic legacy seed contract",
            "sample_total": len(rows),
            "passed": bool(rows)
            and all(row.get("comparator_pre_registered") is True for row in rows)
            and all(row.get("comparator_baseline_kind") == COMPARATOR_BASELINE_KIND for row in rows)
            and all(row.get("comparator_material_margin_met") is True for row in rows),
        },
        {
            "test_id": "target_leakage_absent_from_comparator",
            "description": "comparator metadata must not declare target-value use or MolecularWeight as a comparator input",
            "sample_total": len(rows),
            "passed": bool(rows)
            and all(
                not any("COMPARATOR_TARGET_LEAKAGE" in failure for failure in row.get("comparator_validation_failures", []))
                for row in rows
            ),
        },
    ]


def build_acquisition_packet(
    *,
    rows: list[dict[str, Any]],
    minimum_n: int,
    blockers: list[str],
    snapshot_refs: list[str],
    packet_requests: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    requests = missing_pubchem_requests(rows, minimum_n, packet_requests)
    return {
        "schema_id": ACQUISITION_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "planner": PLANNER_REF,
        "status": "ACQUISITION_REQUIRED" if blockers or requests else "ACQUISITION_NOT_REQUIRED",
        "current_snapshot_refs": snapshot_refs,
        "official_acquisition_run_root_ref": OFFICIAL_ACQUISITION_RUN_ROOT_REL,
        "source_acquisition_requests": packet_requests or [],
        "current_usable_row_total": len(rows),
        "minimum_n": minimum_n,
        "missing_n": max(0, minimum_n - len(rows)),
        "request_total": len(requests),
        "missing_official_snapshot_total": len(requests),
        "missing_official_snapshots": requests,
        "exact_acquisition_requests": requests,
        "missing_protocol_material": [
            {
                "material_id": "OC133-PUBCHEM-FORMULA-PRETARGET-LOCK-MANIFEST",
                "required": True,
                "description": "pre-target manifest freezing visible MolecularFormula fields, fixed atomic-weight table, comparator, residual metric, uncertainty, and row inclusion rule before scoring",
            },
            {
                "material_id": "OC133-PUBCHEM-FORMULA-TARGET-HIDDEN-MANIFEST",
                "required": True,
                "description": "manifest proving MolecularWeight target fields were hidden from model/comparator selection until scoring",
            },
            {
                "material_id": "OC133-PUBCHEM-FORMULA-COMPARATOR-REGISTRATION",
                "required": True,
                "description": "preregister the formula atom-count carbon-equivalent comparator and material-margin rejection criterion before target scoring; zero-Da nulls remain sanity controls only",
            },
        ],
        "blockers": blockers,
        "no_send": True,
        "publish_allowed": False,
        "journal_submissions_allowed": False,
        "registry_write_allowed": False,
        "release_promotion_allowed": False,
    }


def build_tasks(
    *,
    rows: list[dict[str, Any]],
    blockers: list[str],
    snapshot_hashes: list[dict[str, Any]],
    source: dict[str, Any],
    minimum_n: int,
) -> dict[str, Any]:
    return {
        "schema_id": TASKS_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "planner": PLANNER_REF,
        "snapshot_hash_policy": SNAPSHOT_HASH_POLICY,
        "row_hash_policy": ROW_HASH_POLICY,
        "atomic_weight_table": {
            "table_id": ATOMIC_WEIGHT_TABLE_ID,
            "source_note": ATOMIC_WEIGHT_SOURCE_NOTE,
            "weights": ATOMIC_WEIGHTS,
            "table_sha256": sha256_object(ATOMIC_WEIGHTS),
        },
        "minimum_n": minimum_n,
        "candidate_n": len(rows),
        "missing_n": max(0, minimum_n - len(rows)),
        "source_separation": source,
        "snapshot_manifest": snapshot_hashes,
        "rows": rows,
        "comparator_baselines": ordered_unique(
            [
                {
                    "kind": row.get("comparator_baseline_kind"),
                    "name": row.get("comparator_baseline_name"),
                    "prediction_rule": row.get("comparator_prediction_rule"),
                    "pre_registered": row.get("comparator_pre_registered") is True,
                    "baseline_sha256": row.get("comparator_baseline_sha256"),
                    "required_material_margin_da": row.get("comparator_required_material_margin_da"),
                }
                for row in rows
            ]
        ),
        "residuals": residual_summary(rows),
        "negative_controls": [
            {
                "control_id": control["control_id"],
                "description": control["description"],
                "nontrivial": control.get("nontrivial") is True,
                "material_margin_da": control.get("material_margin_da"),
                "required_material_margin_da": control.get("required_material_margin_da"),
                "rejected": control.get("rejected") is True,
            }
            for row in rows
            for control in row.get("negative_controls", [])
        ],
        "falsifiers": ordered_unique([as_str(row.get("falsifier")) for row in rows if row.get("falsifier")]),
        "blockers": blockers,
    }


def build_protocol(
    *,
    candidate_pack: dict[str, Any],
    rows: list[dict[str, Any]],
    blockers: list[str],
    source: dict[str, Any],
    minimum_n: int,
    snapshot_hashes: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "schema_id": PROTOCOL_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "planner": PLANNER_REF,
        "requirements_ref": REQUIREMENTS_REL,
        "candidate_pack_ref": CANDIDATE_PACK_REL,
        "candidate_pack_sha256": sha256_object(candidate_pack),
        "candidate_pack_hash_policy": PACK_HASH_POLICY,
        "tasks_ref": TASKS_REL,
        "report_ref": REPORT_REL,
        "acquisition_packet_ref": ACQUISITION_REL,
        "snapshot_hashes": snapshot_hashes,
        "source_separation_claim": source,
        "minimum_n": minimum_n,
        "candidate_n": len(rows),
        "criteria": {
            "n_at_least_minimum": len(rows) >= minimum_n,
            "source_separation_mode_allowed": source.get("mode") in {"target_blind", "prospective"},
            "pre_target_lock_required": source.get("pre_target_lock") is True,
            "target_hidden_until_scoring_required": source.get("target_hidden_until_scoring") is True,
            "comparator_preregistered_required": bool(rows) and all(row.get("comparator_pre_registered") is True for row in rows),
            "nontrivial_comparator_required": bool(rows) and all(row.get("comparator_baseline_kind") == COMPARATOR_BASELINE_KIND for row in rows),
            "comparator_material_margin_required": bool(rows) and all(row.get("comparator_material_margin_met") is True for row in rows),
            "negative_controls_rejected_required": bool(rows) and all(row.get("negative_control_rejected") is True for row in rows),
            "nontrivial_negative_controls_rejected_required": bool(rows) and all(row.get("nontrivial_negative_controls_rejected") is True for row in rows),
            "residuals_within_uncertainty_required": bool(rows) and all(row.get("residual_within_uncertainty") is True for row in rows),
            "falsifiers_not_triggered_required": bool(rows) and all(row.get("falsifier_status") == "NOT_TRIGGERED" for row in rows),
            "official_pubchem_provenance_required": bool(rows) and all(row.get("official_source_confirmed") is True for row in rows),
        },
        "required_protocol_steps": [
            "discover only local pinned PubChem PUG REST snapshots inside the public repo",
            "hash every raw snapshot with LF-normalized SHA256 before scoring",
            "freeze source separation, visible fields, target fields, atomic-weight table, comparator, residual metric, negative controls, and falsifiers before scoring",
            "construct one row per PubChem PropertyTable.Properties record",
            "compute MolecularWeight from MolecularFormula using the fixed local atomic-weight table",
            "compare formula mass against PubChem MolecularWeight and the preregistered formula-visible atom-count comparator baseline",
            "retain the zero-Da null only as a sanity control that cannot by itself unlock grand support",
            "block grand_toe_support_allowed unless N>=20 and every strict criterion passes",
            "emit exact PubChem PUG REST acquisition requests when current local snapshots are insufficient",
        ],
        "blockers": blockers,
        "no_send": True,
        "publish_allowed": False,
    }


def build_report(
    *,
    candidate_pack: dict[str, Any],
    rows: list[dict[str, Any]],
    blockers: list[str],
    local_blockers: list[str],
    pack_gate_failures: list[str],
    final_pack_failures: list[str],
    tamper_tests: list[dict[str, Any]],
    source: dict[str, Any],
    minimum_n: int,
    snapshot_refs: list[str],
    snapshot_hashes: list[dict[str, Any]],
    packet_requests: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    support_allowed = candidate_pack.get("grand_toe_support_allowed") is True
    missing_requests = missing_pubchem_requests(rows, minimum_n, packet_requests)
    return {
        "schema_id": REPORT_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "planner": PLANNER_REF,
        "support_policy": SUPPORT_POLICY,
        "requirements_ref": REQUIREMENTS_REL,
        "candidate_pack_ref": CANDIDATE_PACK_REL,
        "candidate_pack_sha256": sha256_object(candidate_pack),
        "candidate_pack_hash_policy": PACK_HASH_POLICY,
        "protocol_ref": PROTOCOL_REL,
        "tasks_ref": TASKS_REL,
        "acquisition_packet_ref": ACQUISITION_REL,
        "hashes_ref": HASHES_REL,
        "snapshot_refs": snapshot_refs,
        "snapshot_hashes": snapshot_hashes,
        "snapshot_hash_policy": SNAPSHOT_HASH_POLICY,
        "row_hash_policy": ROW_HASH_POLICY,
        "row_hashes": [row.get("row_hash") for row in rows],
        "atomic_weight_table_id": ATOMIC_WEIGHT_TABLE_ID,
        "atomic_weight_table_sha256": sha256_object(ATOMIC_WEIGHTS),
        "minimum_n": minimum_n,
        "candidate_n": len(rows),
        "missing_n": max(0, minimum_n - len(rows)),
        "missing_official_snapshot_total": len(missing_requests),
        "source_separation": source,
        "residuals": candidate_pack.get("residuals", {}),
        "comparator_baseline": candidate_pack.get("comparator_baseline", {}),
        "negative_controls": candidate_pack.get("negative_controls", []),
        "falsifiers": candidate_pack.get("falsifiers", []),
        "tamper_tests": tamper_tests,
        "local_blockers": local_blockers,
        "candidate_gate_failures": pack_gate_failures,
        "final_pack_failure_reasons": final_pack_failures,
        "eligibility_reasons": [] if support_allowed else blockers,
        "blockers": blockers,
        "open_blocker_total": len(blockers),
        "blocked_total": len(blockers),
        "candidate_pack_total": 1,
        "valid_pack_total": 1 if support_allowed else 0,
        "blocked_candidate_pack_total": 0 if support_allowed else 1,
        "grand_toe_support_allowed": support_allowed,
        "verdict": "READY_FOR_PARENT_REGISTRY_REVIEW" if support_allowed else "BLOCKED_ACQUISITION_READY_PUBCHEM_FORMULA_BATCH",
        "support_scope": "strict PubChem formula-to-molecular-weight reconstruction; not a chemistry database superiority claim",
        "no_fabricated_pass_policy": SUPPORT_POLICY,
        "no_send": True,
        "publish_allowed": False,
        "journal_submissions_allowed": False,
        "registry_write_allowed": False,
        "release_promotion_allowed": False,
    }


def build_stronger_target_work_order(
    *,
    rows: list[dict[str, Any]],
    blockers: list[str],
    source: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_id": "OC133_CHEMISTRY_PUBCHEM_FORMULA_BATCH_STRONGER_TARGET_WORK_ORDER_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "planner": PLANNER_REF,
        "cerberus_key": "CERBERUS-K-OC133-CHEMISTRY-TRIVIAL-COMPARATOR-001",
        "status": "OPEN_STRONGER_CHEMISTRY_TARGET_REQUIRED" if BOUNDED_REPLAY_BLOCKER in blockers else "NOT_REQUIRED",
        "reason": (
            "The comparator has been upgraded from a zero-Da null to a preregistered formula-visible atom-count "
            "baseline, but the target remains PubChem MolecularWeight reconstructed from MolecularFormula. This is "
            "bounded formula-mass replay, not independent grand chemistry support."
        ),
        "current_pack_ref": CANDIDATE_PACK_REL,
        "current_report_ref": REPORT_REL,
        "current_rows": len(rows),
        "current_source_separation": clean_pack_source(source),
        "blocked_grand_toe_support": BOUNDED_REPLAY_BLOCKER in blockers,
        "required_successor_target": {
            "target_class": "independent_chemistry_property",
            "examples": [
                "experimental boiling/melting point with temperature/unit normalization",
                "measured density or vapor pressure with phase and temperature controls",
                "spectral peak/property prediction with instrument/source provenance",
                "bio/cheminformatics activity target with scaffold or family holdout",
            ],
            "must_not_be": [
                "MolecularWeight directly determined by MolecularFormula",
                "exact formula-mass replay using the same visible formula",
                "target values used to tune comparator or row inclusion",
            ],
        },
        "required_controls": [
            "retain the nontrivial formula-visible comparator or a preregistered chemistry-aware successor",
            "include nontrivial negative controls that must be worse by a material margin",
            "fail closed on target leakage, stale preregistration hashes, or trivial-only comparators",
        ],
        "no_send": True,
        "publish_allowed": False,
        "journal_submissions_allowed": False,
        "registry_write_allowed": False,
    }


def build_hashes(
    *,
    tasks: dict[str, Any],
    protocol: dict[str, Any],
    candidate_pack: dict[str, Any],
    report: dict[str, Any],
    acquisition_packet: dict[str, Any],
    work_order: dict[str, Any],
    readme: str,
    snapshot_hashes: list[dict[str, Any]],
    rows: list[dict[str, Any]],
    legacy_seed_artifacts: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    legacy_seed_artifacts = legacy_seed_artifacts or {}
    return {
        "schema_id": HASHES_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "hash_policy": PACK_HASH_POLICY,
        "artifact_hashes": [
            {"artifact_ref": TASKS_REL, "sha256": sha256_object(tasks), "hash_policy": PACK_HASH_POLICY},
            {"artifact_ref": PROTOCOL_REL, "sha256": sha256_object(protocol), "hash_policy": PACK_HASH_POLICY},
            {"artifact_ref": CANDIDATE_PACK_REL, "sha256": sha256_object(candidate_pack), "hash_policy": PACK_HASH_POLICY},
            {"artifact_ref": REPORT_REL, "sha256": sha256_object(report), "hash_policy": PACK_HASH_POLICY},
            {"artifact_ref": ACQUISITION_REL, "sha256": sha256_object(acquisition_packet), "hash_policy": PACK_HASH_POLICY},
            {"artifact_ref": WORK_ORDER_REL, "sha256": sha256_object(work_order), "hash_policy": PACK_HASH_POLICY},
            {"artifact_ref": README_REL, "sha256": sha256_text(readme), "hash_policy": "sha256 over UTF-8 README text"},
            *[
                {"artifact_ref": ref, "sha256": sha256_object(payload), "hash_policy": PACK_HASH_POLICY}
                for ref, payload in sorted(legacy_seed_artifacts.items())
            ],
        ],
        "atomic_weight_table": {
            "table_id": ATOMIC_WEIGHT_TABLE_ID,
            "sha256": sha256_object(ATOMIC_WEIGHTS),
            "hash_policy": PACK_HASH_POLICY,
        },
        "snapshot_hashes": snapshot_hashes,
        "row_hashes": [
            {
                "observation_id": row.get("observation_id"),
                "row_hash": row.get("row_hash"),
                "row_hash_policy": ROW_HASH_POLICY,
            }
            for row in rows
        ],
    }


def render_readme(report: dict[str, Any], acquisition_packet: dict[str, Any]) -> str:
    lines = [
        "# Chemistry PubChem Formula Batch Factory",
        "",
        f"Verdict: `{report.get('verdict')}`",
        f"Grand TOE support allowed: `{report.get('grand_toe_support_allowed')}`",
        f"Rows: `{report.get('candidate_n')}`",
        f"Minimum N: `{report.get('minimum_n')}`",
        f"Missing official snapshots: `{acquisition_packet.get('request_total')}`",
        "",
        "## Open blockers",
    ]
    blockers = report.get("blockers", [])
    if blockers:
        lines.extend(f"- `{blocker}`" for blocker in blockers)
    else:
        lines.append("- `none`")
    lines.extend(
        [
            "",
            "## Atomic Weight Table",
            f"- `{ATOMIC_WEIGHT_TABLE_ID}`",
            f"- `sha256`: `{sha256_object(ATOMIC_WEIGHTS)}`",
            "",
            "## No-Send Locks",
            f"- `no_send`: `{report.get('no_send')}`",
            f"- `publish_allowed`: `{report.get('publish_allowed')}`",
            f"- `registry_write_allowed`: `{report.get('registry_write_allowed')}`",
            "",
            "## Acquisition",
        ]
    )
    for item in acquisition_packet.get("exact_acquisition_requests", [])[:5]:
        lines.append(f"- `{item['expected_local_snapshot_ref']}` from `{item['official_endpoint_url']}`")
    remaining = max(0, len(acquisition_packet.get("exact_acquisition_requests", [])) - 5)
    if remaining:
        lines.append(f"- `{remaining}` additional PubChem requests listed in the acquisition packet")
    return "\n".join(lines) + "\n"


def build_payload(root: Path | None = None, snapshot_refs: list[str] | None = None) -> dict[str, Any]:
    root = (root or repo_root()).resolve()
    requirements, requirement_failures = load_requirements(root)
    minimum_n = as_int(requirements.get("minimum_per_domain_n"), 20)
    discovered_refs = discover_snapshot_refs(root, snapshot_refs)
    packet_requests = load_packet_requests(root)
    loaded_snapshots = [load_snapshot(root, ref) for ref in discovered_refs]
    official_snapshots: list[dict[str, Any]] = []
    official_failures: list[str] = []
    if snapshot_refs is None:
        official_snapshots, official_failures = load_official_acquisition_snapshots(root, packet_requests)
        loaded_snapshots.extend(official_snapshots)
        discovered_refs = ordered_unique([*discovered_refs, *[item["ref"] for item in official_snapshots]])
    snapshot_hashes = [
        {
            "snapshot_ref": item["ref"],
            "snapshot_sha256": item["sha256"],
            "source_snapshot_hash": item["sha256"],
            "snapshot_hash_policy": item.get("acquisition", {}).get("hash_policy", SNAPSHOT_HASH_POLICY),
            "snapshot_byte_count": item["byte_count"],
            "parsed": not item["failures"],
            "failures": item["failures"],
            "acquisition_id": item.get("acquisition", {}).get("acquisition_id", ""),
            "expected_local_snapshot_ref": item.get("acquisition", {}).get("expected_local_snapshot_ref", ""),
            "lock_ref": item.get("acquisition", {}).get("lock_ref", ""),
            "declared_before_scoring_lock": item.get("acquisition", {}).get("declared_before_scoring_lock") is True,
        }
        for item in loaded_snapshots
    ]

    rows: list[dict[str, Any]] = []
    local_blockers: list[str] = [*requirement_failures, *official_failures]
    source_candidates: list[dict[str, Any]] = []
    legacy_seed_artifacts: dict[str, dict[str, Any]] = {}
    record_index = 0
    for snapshot in loaded_snapshots:
        local_blockers.extend(snapshot["failures"])
        payload = snapshot.get("payload")
        acquisition = dict_or_empty(snapshot.get("acquisition"))
        if payload is None:
            continue
        records = iter_payload_records(payload)
        if not records:
            local_blockers.append(f"PUBCHEM_PROPERTY_ROWS_MISSING::{snapshot['ref']}")
            continue
        for record, source_candidate, comparator, provenance in records:
            record_index += 1
            row_acquisition = acquisition
            if acquisition:
                target_projection_status = dict_or_empty(acquisition.get("target_projection_lock"))
                if target_projection_status.get("verified") is True:
                    source_candidate = source_separation_from_target_projection_lock(target_projection_status)
                else:
                    source_candidate = {
                        "mode": "official_readonly_snapshot_replay",
                        "kind": "official_readonly_acquisition_lock",
                        "pre_target_lock": True,
                        "target_hidden_until_scoring": False,
                        "declared_before_scoring": True,
                        "training_sources": [f"{ACQUISITION_REL}::visible_fields(CID,MolecularFormula)"],
                        "target_sources": [f"{ACQUISITION_REL}::target_field(MolecularWeight)"],
                        "training_manifest_sha256": "",
                        "target_manifest_sha256": "",
                    }
            else:
                row_acquisition, source_candidate, comparator, legacy_failures = legacy_seed_upgrade_for_record(
                    source_ref=snapshot["ref"],
                    source_sha256=snapshot["sha256"],
                    record_index=record_index,
                    record=record,
                    source_candidate=source_candidate,
                    comparator=comparator,
                )
                local_blockers.extend(legacy_failures)
                legacy_seed_artifacts.update(dict_or_empty(row_acquisition.get("legacy_seed_artifacts")))
            source_candidates.append(source_candidate)
            row, row_failures = build_row(
                record=record,
                source_ref=snapshot["ref"],
                source_sha256=snapshot["sha256"],
                record_index=record_index,
                comparator=comparator,
                provenance=provenance,
                acquisition=row_acquisition,
            )
            local_blockers.extend(row_failures)
            if row is not None:
                rows.append(row)

    if not discovered_refs:
        local_blockers.append("NO_LOCAL_PUBCHEM_PUG_REST_SNAPSHOTS_DISCOVERED")
    if loaded_snapshots and not rows:
        local_blockers.append("NO_SCORABLE_PUBCHEM_FORMULA_ROWS")
    rows_by_snapshot: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        rows_by_snapshot[as_str(row.get("snapshot_ref"))].append(row)
    for item in snapshot_hashes:
        if item.get("lock_ref"):
            continue
        snapshot_rows = rows_by_snapshot.get(as_str(item.get("snapshot_ref")), [])
        if snapshot_rows and all(row.get("declared_before_scoring_lock") is True for row in snapshot_rows):
            item["lock_ref"] = as_str(snapshot_rows[0].get("lock_ref"))
            item["declared_before_scoring_lock"] = True
            item["target_projection_lock_verified"] = all(row.get("target_projection_lock_verified") is True for row in snapshot_rows)
            item["legacy_seed_upgrade"] = all(row.get("lock_ref", "").startswith(LEGACY_SEED_LOCK_ROOT_REL) for row in snapshot_rows)

    source, source_selection_failures = select_source_separation(source_candidates)
    local_blockers.extend(source_selection_failures)
    local_blockers.extend(validate_source_separation(source, requirements))
    local_blockers.extend(validate_rows(rows))
    if rows and any(row.get("comparator_pre_registered") is not True for row in rows):
        local_blockers.append("COMPARATOR_BASELINE_NOT_PREREGISTERED")
    if rows and any(row.get("comparator_baseline_kind") != COMPARATOR_BASELINE_KIND for row in rows):
        local_blockers.append("NONTRIVIAL_COMPARATOR_REQUIRED")
    if rows and any(any("TRIVIAL_COMPARATOR_BASELINE_NOT_ALLOWED" in failure for failure in row.get("comparator_validation_failures", [])) for row in rows):
        local_blockers.append("TRIVIAL_COMPARATOR_BASELINE_NOT_ALLOWED")
    if rows and any(any("COMPARATOR_TARGET_LEAKAGE" in failure for failure in row.get("comparator_validation_failures", [])) for row in rows):
        local_blockers.append("COMPARATOR_TARGET_LEAKAGE")
    if rows and any(any("COMPARATOR_BASELINE_PREREGISTRATION_STALE" in failure for failure in row.get("comparator_validation_failures", [])) for row in rows):
        local_blockers.append("COMPARATOR_BASELINE_PREREGISTRATION_STALE")
    if rows and any(row.get("comparator_material_margin_met") is not True for row in rows):
        local_blockers.append("COMPARATOR_MATERIAL_MARGIN_NOT_MET")
    if rows and any(row.get("nontrivial_negative_controls_rejected") is not True for row in rows):
        local_blockers.append("NONTRIVIAL_NEGATIVE_CONTROL_NOT_REJECTED")

    if len(rows) < minimum_n:
        local_blockers.append(f"N_BELOW_MINIMUM::{len(rows)}/{minimum_n}")
        local_blockers.append("CURRENT_RAW_DATA_TOO_THIN_FOR_PUBCHEM_FORMULA_BATCH")
    if residual_summary(rows)["superiority_margin"] <= 0:
        local_blockers.append("RESIDUAL_SUPERIORITY_NOT_MET")
    if (
        rows
        and dict_or_empty(requirements.get("criteria")).get("current_target_blind_reconstructions_are_bounded_baseline_only")
        is True
        and all(row.get("task_type") == "pubchem_formula_to_molecular_weight_reconstruction" for row in rows)
    ):
        local_blockers.append(BOUNDED_REPLAY_BLOCKER)
        local_blockers.append(STRONGER_TARGET_WORK_ORDER_BLOCKER)

    local_blockers = ordered_unique(local_blockers)
    gate_pack = build_pack(rows, source, support_allowed=True)
    pack_gate_failures = grand_factory.pack_failure_reasons(gate_pack, requirements)
    support_allowed = not ordered_unique([*local_blockers, *pack_gate_failures])
    candidate_pack = build_pack(rows, source, support_allowed=support_allowed)
    final_pack_failures = grand_factory.pack_failure_reasons(candidate_pack, requirements)
    blockers = ordered_unique([*local_blockers, *pack_gate_failures])
    if not support_allowed:
        blockers = ordered_unique([*blockers, "GRAND_TOE_SUPPORT_NOT_ALLOWED"])

    tamper_tests = build_tamper_tests(rows, snapshot_hashes)
    tasks = build_tasks(rows=rows, blockers=blockers, snapshot_hashes=snapshot_hashes, source=source, minimum_n=minimum_n)
    acquisition_packet = build_acquisition_packet(
        rows=rows,
        minimum_n=minimum_n,
        blockers=blockers,
        snapshot_refs=discovered_refs,
        packet_requests=packet_requests,
    )
    protocol = build_protocol(
        candidate_pack=candidate_pack,
        rows=rows,
        blockers=blockers,
        source=source,
        minimum_n=minimum_n,
        snapshot_hashes=snapshot_hashes,
    )
    report = build_report(
        candidate_pack=candidate_pack,
        rows=rows,
        blockers=blockers,
        local_blockers=local_blockers,
        pack_gate_failures=pack_gate_failures,
        final_pack_failures=final_pack_failures,
        tamper_tests=tamper_tests,
        source=source,
        minimum_n=minimum_n,
        snapshot_refs=discovered_refs,
        snapshot_hashes=snapshot_hashes,
        packet_requests=packet_requests,
    )
    work_order = build_stronger_target_work_order(rows=rows, blockers=blockers, source=source)
    readme = render_readme(report, acquisition_packet)
    hashes = build_hashes(
        tasks=tasks,
        protocol=protocol,
        candidate_pack=candidate_pack,
        report=report,
        acquisition_packet=acquisition_packet,
        work_order=work_order,
        readme=readme,
        snapshot_hashes=snapshot_hashes,
        rows=rows,
        legacy_seed_artifacts=legacy_seed_artifacts,
    )
    return {
        "tasks": tasks,
        "protocol": protocol,
        "candidate_pack": candidate_pack,
        "report": report,
        "acquisition_packet": acquisition_packet,
        "work_order": work_order,
        "hashes": hashes,
        "readme": readme,
        "legacy_seed_artifacts": legacy_seed_artifacts,
    }


def write_outputs(root: Path | None = None, snapshot_refs: list[str] | None = None) -> dict[str, Any]:
    root = (root or repo_root()).resolve()
    payload = build_payload(root, snapshot_refs=snapshot_refs)
    write_json(root / TASKS_REL, payload["tasks"])
    write_json(root / PROTOCOL_REL, payload["protocol"])
    write_json(root / CANDIDATE_PACK_REL, payload["candidate_pack"])
    write_json(root / REPORT_REL, payload["report"])
    write_json(root / ACQUISITION_REL, payload["acquisition_packet"])
    write_json(root / WORK_ORDER_REL, payload["work_order"])
    write_json(root / HASHES_REL, payload["hashes"])
    write_text(root / README_REL, payload["readme"])
    for rel_path, artifact in sorted(dict_or_empty(payload.get("legacy_seed_artifacts")).items()):
        write_json(root / rel_path, artifact)
    return payload


def check_stored(root: Path | None = None, snapshot_refs: list[str] | None = None) -> list[str]:
    root = (root or repo_root()).resolve()
    expected = build_payload(root, snapshot_refs=snapshot_refs)
    checks = [
        (TASKS_REL, expected["tasks"]),
        (PROTOCOL_REL, expected["protocol"]),
        (CANDIDATE_PACK_REL, expected["candidate_pack"]),
        (REPORT_REL, expected["report"]),
        (ACQUISITION_REL, expected["acquisition_packet"]),
        (WORK_ORDER_REL, expected["work_order"]),
        (HASHES_REL, expected["hashes"]),
        *sorted(dict_or_empty(expected.get("legacy_seed_artifacts")).items()),
    ]
    failures: list[str] = []
    for rel_path, payload in checks:
        path = root / rel_path
        if not path.exists():
            failures.append(f"missing::{rel_path}")
            continue
        if read_json(path) != payload:
            failures.append(f"mismatch::{rel_path}")
    readme_path = root / README_REL
    if not readme_path.exists():
        failures.append(f"missing::{README_REL}")
    elif readme_path.read_text(encoding="utf-8") != expected["readme"]:
        failures.append(f"mismatch::{README_REL}")
    return failures


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build strict OC133 chemistry PubChem formula batch artifacts.")
    parser.add_argument("--root", default=str(repo_root()), help="repository root")
    parser.add_argument("--snapshot-ref", action="append", default=None, help="explicit local PubChem PUG REST snapshot ref")
    parser.add_argument("--write", action="store_true", help="write artifacts")
    parser.add_argument("--check", action="store_true", help="check persisted artifacts")
    parser.add_argument("--allow-blocked-exit-zero", action="store_true", help="exit zero when the honest result is blocked")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    if args.check:
        failures = check_stored(root, snapshot_refs=args.snapshot_ref)
        if failures:
            for failure in failures:
                print(f"ERROR: {failure}")
            return 1
        expected = build_payload(root, snapshot_refs=args.snapshot_ref)
        checked = [
            TASKS_REL,
            PROTOCOL_REL,
            CANDIDATE_PACK_REL,
            REPORT_REL,
            ACQUISITION_REL,
            WORK_ORDER_REL,
            HASHES_REL,
            README_REL,
            *sorted(dict_or_empty(expected.get("legacy_seed_artifacts")).keys()),
        ]
        print(json.dumps({"status": "ok", "checked": checked}, indent=2))
        return 0

    payload = write_outputs(root, snapshot_refs=args.snapshot_ref) if args.write else build_payload(root, snapshot_refs=args.snapshot_ref)
    print(json.dumps(payload["report"], ensure_ascii=True, indent=2))
    if payload["report"].get("grand_toe_support_allowed") is not True and not args.allow_blocked_exit_zero:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
