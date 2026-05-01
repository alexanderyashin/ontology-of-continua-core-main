from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from validation.grand_science import evidence_pack_factory as grand_factory  # noqa: E402
from tools import oc133_official_readonly_acquisition_runner as acquisition_runner  # noqa: E402


RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
CAPABILITY_OWNER = "Research/EmpiricalScience"
PLANNER_REF = "tools/oc133_chemistry_pubchem_hbond_donor_factory.py"

SCHEMA_ID = "OC133_CHEMISTRY_PUBCHEM_HBOND_DONOR_FACTORY_v1"
TASKS_SCHEMA_ID = "OC133_CHEMISTRY_PUBCHEM_HBOND_DONOR_TASKS_v1"
PROTOCOL_SCHEMA_ID = "OC133_CHEMISTRY_PUBCHEM_HBOND_DONOR_PROTOCOL_v1"
REPORT_SCHEMA_ID = "OC133_CHEMISTRY_PUBCHEM_HBOND_DONOR_REPORT_v1"
ACQUISITION_SCHEMA_ID = "OC133_CHEMISTRY_PUBCHEM_HBOND_DONOR_ACQUISITION_PACKET_v1"
HASHES_SCHEMA_ID = "OC133_CHEMISTRY_PUBCHEM_HBOND_DONOR_HASHES_v1"

OUTPUT_ROOT_REL = "validation/heldout/grand_science/chemistry/pubchem_hbond_donor"
TASKS_REL = f"{OUTPUT_ROOT_REL}/OC133_CHEMISTRY_PUBCHEM_HBOND_DONOR_TASKS.json"
PROTOCOL_REL = f"{OUTPUT_ROOT_REL}/OC133_CHEMISTRY_PUBCHEM_HBOND_DONOR_PROTOCOL.json"
CANDIDATE_PACK_REL = f"{OUTPUT_ROOT_REL}/OC133_CHEMISTRY_PUBCHEM_HBOND_DONOR_CANDIDATE_PACK.json"
REPORT_REL = f"{OUTPUT_ROOT_REL}/OC133_CHEMISTRY_PUBCHEM_HBOND_DONOR_REPORT.json"
ACQUISITION_REL = f"{OUTPUT_ROOT_REL}/OC133_CHEMISTRY_PUBCHEM_HBOND_DONOR_ACQUISITION_PACKET.json"
HASHES_REL = f"{OUTPUT_ROOT_REL}/OC133_CHEMISTRY_PUBCHEM_HBOND_DONOR_HASHES.json"
README_REL = f"{OUTPUT_ROOT_REL}/README.md"
WORK_ORDER_REL = f"{OUTPUT_ROOT_REL}/OC133_CHEMISTRY_PUBCHEM_HBOND_DONOR_ACQUISITION_WORK_ORDER.json"
REQUIREMENTS_REL = "benchmarks/grand_science/domain_requirements.json"

OFFICIAL_RUN_ROOT_REL = acquisition_runner.RUN_ROOT_REL
OFFICIAL_LOCKS_REL = acquisition_runner.LOCK_ROOT_REL
OFFICIAL_SNAPSHOTS_REL = acquisition_runner.SNAPSHOT_ROOT_REL

TARGET_FIELD = "HBondDonorCount"
TARGET_CLASS = "pubchem_hydrogen_bond_donor_count"
VISIBLE_FIELDS = ["CID", "MolecularFormula", "ConnectivitySMILES"]
TARGET_FIELDS = [TARGET_FIELD]
PROPERTY_FIELDS = "MolecularFormula,CanonicalSMILES,ConnectivitySMILES,HBondDonorCount"
OFFICIAL_PUG_ENDPOINT_PREFIX = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid"
MINIMUM_N_DEFAULT = 20
ROW_HASH_POLICY = "sha256 over canonical row JSON before row_hash insertion"
PACK_HASH_POLICY = "sha256 over canonical JSON"
OFFICIAL_HASH_POLICY = acquisition_runner.HASH_POLICY
MODEL_UNDER_TEST = "target-blind SMILES hydrogen-bond donor atom counter"
MODEL_KIND = "smiles_hbond_donor_count_v1"
COMPARATOR_KIND = "formula_hetero_atom_count_donor_baseline"
COMPARATOR_NAME = "formula-only nitrogen/oxygen heteroatom donor-count baseline"
COMPARATOR_RULE = (
    "parse only MolecularFormula from the visible projection and predict the count of N plus O atoms as donor atoms, "
    "ignoring bonding, protonation, and functional group context"
)
COMPARATOR_BASELINE_PAYLOAD = {
    "kind": COMPARATOR_KIND,
    "name": COMPARATOR_NAME,
    "prediction_rule": COMPARATOR_RULE,
    "target_field": TARGET_FIELD,
    "target_values_used_for_baseline_design": False,
}
MIN_COMPARATOR_ADVANTAGE = 0.2
MAX_MODEL_MAE = 0.05
MAX_ROW_ABS_ERROR = 0.0
SUPPORT_POLICY = (
    "Grand chemistry support is emitted only for N>=20 official PubChem PUG REST rows where HBondDonorCount is "
    "hidden until scoring, predictions are materialized from visible SMILES before target opening, the target is not "
    "MolecularWeight or any formula-mass replay, a preregistered formula-only heteroatom baseline is materially worse, "
    "negative controls are rejected, falsifiers are retained, and source hashes/locks validate."
)

DEFAULT_CID_PLAN = (
    "962",   # water
    "702",   # ethanol
    "176",   # acetic acid
    "180",   # acetone
    "241",   # benzene
    "887",   # methanol
    "284",   # formic acid
    "996",   # phenol
    "6115",  # aniline
    "178",   # acetamide
    "8254",  # dimethyl ether
    "8857",  # ethyl acetate
    "1049",  # pyridine
    "795",   # imidazole
    "1176",  # urea
    "6342",  # acetonitrile
    "753",   # glycerol
    "280",   # carbon dioxide
    "222",   # ammonia
    "297",   # methane
)

NO_SEND_LOCKS = dict(acquisition_runner.NO_SEND_LOCKS)


def repo_root() -> Path:
    return ROOT


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_object(payload: Any) -> str:
    return sha256_bytes(canonical_json(payload).encode("utf-8"))


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


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


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


def list_of_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    return []


def pubchem_property_url(cid: str) -> str:
    return f"{OFFICIAL_PUG_ENDPOINT_PREFIX}/{cid}/property/{PROPERTY_FIELDS}/JSON"


def acquisition_id(index: int) -> str:
    return f"OC133-CHEM-PUBCHEM-HBD-ACQ-{index:03d}"


def prospective_lock_metadata() -> dict[str, Any]:
    return {
        **acquisition_runner.DEFAULT_PROSPECTIVE_LOCK_METADATA,
        "source_snapshot_pre_target_lock": True,
        "target_hidden_until_scoring": True,
        "target_field": TARGET_FIELD,
        "target_class": TARGET_CLASS,
        "model_kind": MODEL_KIND,
        "comparator_baseline_sha256": comparator_baseline_sha256(),
    }


def acquisition_request(index: int, cid: str) -> dict[str, Any]:
    request_id = acquisition_id(index)
    return {
        "request_id": request_id,
        "acquisition_id": request_id,
        "cid": cid,
        "method": "GET",
        "official_source": "PubChem PUG REST",
        "official_endpoint_url": pubchem_property_url(cid),
        "expected_local_snapshot_ref": f"{OUTPUT_ROOT_REL}/raw/pubchem_cid_{cid}_hbond_donor.json",
        "required_fields": PROPERTY_FIELDS.split(","),
        "visible_training_fields": list(VISIBLE_FIELDS),
        "target_field": TARGET_FIELD,
        "target_class": TARGET_CLASS,
        "no_send_lock": True,
        "prospective_lock_metadata": prospective_lock_metadata(),
        "missing_reason": "official PubChem HBondDonorCount target row required for independent chemistry target lane",
    }


def acquisition_packet(current_refs: list[str], rows: list[dict[str, Any]], blockers: list[str]) -> dict[str, Any]:
    acquired_ids = {as_str(row.get("acquisition_id")) for row in rows}
    requests = [
        acquisition_request(index, cid)
        for index, cid in enumerate(DEFAULT_CID_PLAN, start=1)
        if acquisition_id(index) not in acquired_ids
    ]
    return {
        "schema_id": ACQUISITION_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "planner": PLANNER_REF,
        "status": "ACQUISITION_REQUIRED" if requests or blockers else "ACQUIRED_READONLY_READY_FOR_SCORING",
        "official_acquisition_run_root_ref": OFFICIAL_RUN_ROOT_REL,
        "current_snapshot_refs": current_refs,
        "acquisition_requests": requests,
        "request_total": len(requests),
        "missing_official_snapshot_total": len(requests),
        "minimum_n": MINIMUM_N_DEFAULT,
        "current_n": len(rows),
        "target_class": TARGET_CLASS,
        "target_field": TARGET_FIELD,
        "independence_policy": "HBondDonorCount requires structural/protonation context and is not direct MolecularFormula fixed atomic-weight arithmetic.",
        "blockers": ordered_unique(blockers),
        "no_send": True,
        "locks": NO_SEND_LOCKS,
    }


def parse_pubchem_record(payload: Any) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None
    table = payload.get("PropertyTable")
    properties = table.get("Properties") if isinstance(table, dict) else None
    if not isinstance(properties, list) or not properties or not isinstance(properties[0], dict):
        return None
    return dict(properties[0])


def load_official_snapshots(root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    blockers: list[str] = []
    locks_dir = root / OFFICIAL_LOCKS_REL
    if not locks_dir.exists():
        return rows, ["OFFICIAL_ACQUISITION_LOCK_DIR_MISSING"]
    expected_ids = {acquisition_id(index) for index in range(1, len(DEFAULT_CID_PLAN) + 1)}
    for lock_path in sorted(locks_dir.glob("OC133-CHEM-PUBCHEM-HBD-ACQ-*.lock.json")):
        try:
            lock = read_json(lock_path)
        except Exception as exc:
            blockers.append(f"OFFICIAL_LOCK_PARSE_FAILED::{rel(root, lock_path)}::{exc.__class__.__name__}")
            continue
        if not isinstance(lock, dict):
            blockers.append(f"OFFICIAL_LOCK_NOT_OBJECT::{rel(root, lock_path)}")
            continue
        acq_id = as_str(lock.get("acquisition_id"))
        if acq_id not in expected_ids:
            continue
        snapshot_ref = as_str(lock.get("snapshot_ref"))
        if not snapshot_ref.startswith(OFFICIAL_SNAPSHOTS_REL):
            blockers.append(f"OFFICIAL_SNAPSHOT_REF_UNEXPECTED::{acq_id}::{snapshot_ref}")
            continue
        snapshot_path = resolve_under_root(root, snapshot_ref)
        if not snapshot_path.is_file():
            blockers.append(f"OFFICIAL_SNAPSHOT_MISSING::{acq_id}::{snapshot_ref}")
            continue
        raw = snapshot_path.read_bytes()
        actual_sha = sha256_bytes(raw)
        if actual_sha != as_str(lock.get("snapshot_sha256")):
            blockers.append(f"OFFICIAL_SNAPSHOT_HASH_MISMATCH::{acq_id}")
            continue
        if as_int(lock.get("http_status")) < 200 or as_int(lock.get("http_status")) >= 300:
            blockers.append(f"OFFICIAL_HTTP_STATUS_NOT_SUCCESS::{acq_id}::{lock.get('http_status')}")
            continue
        if lock.get("locks") != NO_SEND_LOCKS:
            blockers.append(f"OFFICIAL_NO_SEND_LOCK_MISSING_OR_WEAK::{acq_id}")
            continue
        try:
            payload = json.loads(raw.decode("utf-8"))
        except Exception as exc:
            blockers.append(f"OFFICIAL_SNAPSHOT_JSON_PARSE_FAILED::{acq_id}::{exc.__class__.__name__}")
            continue
        record = parse_pubchem_record(payload)
        if record is None:
            blockers.append(f"PUBCHEM_PROPERTY_RECORD_MISSING::{acq_id}")
            continue
        rows.append(
            {
                "acquisition_id": acq_id,
                "snapshot_ref": snapshot_ref,
                "snapshot_sha256": actual_sha,
                "snapshot_byte_count": len(raw),
                "lock_ref": rel(root, lock_path),
                "lock_sha256": sha256_bytes(lock_path.read_bytes()),
                "official_endpoint_url": as_str(lock.get("official_endpoint_url")),
                "hash_policy": as_str(lock.get("hash_policy"), OFFICIAL_HASH_POLICY),
                "pre_target_sequence_proof": lock.get("pre_target_sequence_proof", {}),
                "record": record,
            }
        )
    return rows, ordered_unique(blockers)


def parse_formula_counts(formula: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for element, count_text in re.findall(r"([A-Z][a-z]?)(\d*)", formula):
        counts[element] = counts.get(element, 0) + (int(count_text) if count_text else 1)
    return counts


def formula_hetero_baseline(formula: str) -> int:
    counts = parse_formula_counts(formula)
    return int(counts.get("N", 0) + counts.get("O", 0))


def comparator_baseline_sha256() -> str:
    return sha256_object(COMPARATOR_BASELINE_PAYLOAD)


def default_comparator() -> dict[str, Any]:
    return {
        **COMPARATOR_BASELINE_PAYLOAD,
        "pre_registered": True,
        "baseline_sha256": comparator_baseline_sha256(),
        "required_material_margin": MIN_COMPARATOR_ADVANTAGE,
    }


def comparator_uses_target(comparator: dict[str, Any]) -> bool:
    if comparator.get("target_values_used_for_baseline_design") is True:
        return True
    if comparator.get("uses_target_values") is True or comparator.get("uses_target") is True:
        return True
    for key in ("prediction_inputs", "fields_used", "inputs", "leakage_fields"):
        values = comparator.get(key)
        if isinstance(values, str):
            values = [values]
        if isinstance(values, list) and any(str(value) == TARGET_FIELD for value in values):
            return True
    return False


def comparator_is_trivial(comparator: dict[str, Any]) -> bool:
    kind = as_str(comparator.get("kind")).lower()
    name = as_str(comparator.get("name")).lower()
    rule = as_str(comparator.get("prediction_rule")).lower()
    return (
        kind in {"constant", "constant_zero", "zero", "zero_count"}
        or comparator.get("prediction_value") == 0
        or comparator.get("value") == 0
        or "constant zero" in rule
        or "zero" in name
    )


def comparator_failures(comparator: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if comparator.get("pre_registered") is not True:
        failures.append("COMPARATOR_BASELINE_NOT_PREREGISTERED")
    if comparator_uses_target(comparator):
        failures.append("COMPARATOR_TARGET_LEAKAGE")
    if comparator_is_trivial(comparator):
        failures.append("TRIVIAL_COMPARATOR_BASELINE_NOT_ALLOWED")
    expected = default_comparator()
    if not comparator_is_trivial(comparator):
        for key in ("kind", "name", "prediction_rule"):
            if comparator.get(key) != expected[key]:
                failures.append("NONTRIVIAL_COMPARATOR_REQUIRED")
                break
    declared_sha = as_str(comparator.get("baseline_sha256"))
    if declared_sha and declared_sha != expected["baseline_sha256"]:
        failures.append("COMPARATOR_BASELINE_PREREGISTRATION_STALE")
    return ordered_unique(failures)


def smiles_atom_tokens(smiles: str) -> list[dict[str, Any]]:
    atoms: list[dict[str, Any]] = []
    current: int | None = None
    branch_stack: list[int | None] = []
    ring_starts: dict[str, tuple[int, float]] = {}
    pending_bond = 1.0
    i = 0
    while i < len(smiles):
        char = smiles[i]
        if char == "[":
            end = smiles.find("]", i + 1)
            if end == -1:
                break
            content = smiles[i + 1 : end]
            match = re.match(r"(?:\d+)?([A-Z][a-z]?|[cnops])", content)
            if match:
                symbol = match.group(1)
                element = symbol.capitalize()
                explicit_h = re.search(r"H(\d*)", content)
                h_count = 0
                if explicit_h:
                    h_count = int(explicit_h.group(1) or "1")
                current = add_smiles_atom(atoms, current, element, symbol.islower(), True, h_count, pending_bond)
                pending_bond = 1.0
            i = end + 1
            continue
        if char in "-=#:.":
            pending_bond = {"-": 1.0, "=": 2.0, "#": 3.0, ":": 1.5, ".": 0.0}[char]
            i += 1
            continue
        if char == "(":
            branch_stack.append(current)
            i += 1
            continue
        if char == ")":
            current = branch_stack.pop() if branch_stack else current
            i += 1
            continue
        if char.isdigit() and current is not None:
            if char in ring_starts:
                other, stored_bond = ring_starts.pop(char)
                bond = pending_bond if pending_bond != 1.0 else stored_bond
                atoms[current]["bond_order_sum"] += bond
                atoms[other]["bond_order_sum"] += bond
            else:
                ring_starts[char] = (current, pending_bond)
            pending_bond = 1.0
            i += 1
            continue
        if smiles.startswith("Cl", i) or smiles.startswith("Br", i):
            element = smiles[i : i + 2]
            current = add_smiles_atom(atoms, current, element, False, False, 0, pending_bond)
            pending_bond = 1.0
            i += 2
            continue
        if char in "BCNOPSFI":
            current = add_smiles_atom(atoms, current, char, False, False, 0, pending_bond)
            pending_bond = 1.0
            i += 1
            continue
        if char in "cnops":
            current = add_smiles_atom(atoms, current, char.upper(), True, False, 0, pending_bond)
            pending_bond = 1.0
            i += 1
            continue
        i += 1
    return atoms


def add_smiles_atom(
    atoms: list[dict[str, Any]],
    current: int | None,
    element: str,
    aromatic: bool,
    bracketed: bool,
    explicit_h_count: int,
    bond_order: float,
) -> int:
    index = len(atoms)
    atom = {
        "element": element,
        "aromatic": aromatic,
        "bracketed": bracketed,
        "explicit_h_count": explicit_h_count,
        "bond_order_sum": 0.0,
    }
    atoms.append(atom)
    if current is not None and bond_order > 0.0:
        atoms[current]["bond_order_sum"] += bond_order
        atoms[index]["bond_order_sum"] += bond_order
    return index


def smiles_hbond_donor_count(smiles: str) -> int:
    donors = 0
    for atom in smiles_atom_tokens(smiles):
        element = atom["element"]
        if element not in {"N", "O"}:
            continue
        if atom["bracketed"]:
            if as_int(atom.get("explicit_h_count")) > 0:
                donors += 1
            continue
        if element == "O" and not atom["aromatic"] and as_float(atom["bond_order_sum"], 99.0) <= 1.0:
            donors += 1
        elif element == "N" and not atom["aromatic"] and as_float(atom["bond_order_sum"], 99.0) <= 2.0:
            donors += 1
    return donors


def row_hash(row: dict[str, Any]) -> str:
    clean = {key: value for key, value in row.items() if key not in {"row_hash", "row_hash_policy"}}
    return sha256_object(clean)


def build_negative_controls(row_id: str, observed: float, model_residual: float, comparator_residual: float) -> list[dict[str, Any]]:
    controls = []
    for control_id, description, residual, nontrivial in (
        (
            f"chemistry-hbd-formula-heteroatom-control::{row_id}",
            "formula-only N+O heteroatom baseline must be materially worse than the SMILES donor predictor",
            comparator_residual,
            True,
        ),
        (
            f"chemistry-hbd-zero-count-control::{row_id}",
            "constant zero donor-count sanity control must be worse when donors are present and no better in aggregate",
            abs(0.0 - observed),
            False,
        ),
    ):
        margin = residual - model_residual
        controls.append(
            {
                "control_id": control_id,
                "description": description,
                "residual": residual,
                "material_margin": margin,
                "required_material_margin": MIN_COMPARATOR_ADVANTAGE if nontrivial else 0.0,
                "nontrivial": nontrivial,
                "rejected": margin >= (MIN_COMPARATOR_ADVANTAGE if nontrivial else 0.0),
                "status": "REJECTED" if margin >= (MIN_COMPARATOR_ADVANTAGE if nontrivial else 0.0) else "NOT_REJECTED",
            }
        )
    return controls


def build_row(
    source: dict[str, Any],
    index: int,
    *,
    comparator: dict[str, Any],
    visible_fields: list[str],
) -> tuple[dict[str, Any] | None, list[str]]:
    record = source["record"]
    failures: list[str] = []
    cid = as_str(record.get("CID"))
    formula = as_str(record.get("MolecularFormula"))
    connectivity = as_str(record.get("ConnectivitySMILES"), as_str(record.get("CanonicalSMILES")))
    canonical = as_str(record.get("CanonicalSMILES"), connectivity)
    smiles = canonical or connectivity
    target = as_float(record.get(TARGET_FIELD), math.nan)
    if TARGET_FIELD in visible_fields:
        failures.append("TARGET_LEAKAGE_VISIBLE_FIELD")
    if not cid:
        failures.append("PUBCHEM_CID_MISSING")
    if not formula:
        failures.append("PUBCHEM_MOLECULAR_FORMULA_MISSING")
    if not smiles:
        failures.append("PUBCHEM_SMILES_MISSING")
    if not math.isfinite(target):
        failures.append(f"PUBCHEM_TARGET_INVALID::{TARGET_FIELD}")
    if failures:
        return None, failures

    predicted = smiles_hbond_donor_count(smiles)
    comparator_prediction = 0 if comparator_is_trivial(comparator) else formula_hetero_baseline(formula)
    model_residual = abs(float(predicted) - target)
    comparator_residual = abs(float(comparator_prediction) - target)
    row_id = f"CHEM-PUBCHEM-HBD-{index:04d}-{sha256_object({'cid': cid, 'snapshot': source['snapshot_ref']})[:12].upper()}"
    controls = build_negative_controls(row_id, target, model_residual, comparator_residual)
    nontrivial_controls = [row for row in controls if row["nontrivial"]]
    falsifier_triggered = model_residual > MAX_ROW_ABS_ERROR or comparator_failures(comparator)
    sequence = source.get("pre_target_sequence_proof") if isinstance(source.get("pre_target_sequence_proof"), dict) else {}
    row = {
        "observation_id": row_id,
        "claim_id": f"OC133-CHEMISTRY-PUBCHEM-HBD-{index:04d}",
        "task_type": "pubchem_smiles_to_hbond_donor_count",
        "target_class": TARGET_CLASS,
        "target_field": TARGET_FIELD,
        "snapshot_ref": source["snapshot_ref"],
        "snapshot_sha256": source["snapshot_sha256"],
        "source_snapshot_hash": source["snapshot_sha256"],
        "source_snapshot_hash_policy": source["hash_policy"],
        "acquisition_id": source["acquisition_id"],
        "lock_ref": source["lock_ref"],
        "lock_sha256": source["lock_sha256"],
        "official_source": "PubChem PUG REST",
        "official_source_url": source["official_endpoint_url"],
        "official_source_confirmed": source["official_endpoint_url"].startswith(OFFICIAL_PUG_ENDPOINT_PREFIX),
        "pre_target_sequence_proof": sequence,
        "declared_before_scoring_lock": sequence.get("source_snapshot_pre_target_lock") is True,
        "target_hidden_until_scoring": sequence.get("target_hidden_until_scoring") is True,
        "prediction_materialized_before_target_open": sequence.get("prediction_materialization_required_before_scoring") is True,
        "target_read_before_prediction_materialization": sequence.get("target_projection_read_before_prediction_materialization") is True,
        "cid": cid,
        "molecular_formula": formula,
        "canonical_smiles": canonical,
        "connectivity_smiles": connectivity,
        "visible_projection": {field: record.get(field) for field in visible_fields},
        "target_projection": {TARGET_FIELD: record.get(TARGET_FIELD)},
        "training_source": f"{source['snapshot_ref']}::CID={cid}::visible_fields({','.join(visible_fields)})",
        "target_source": f"{source['snapshot_ref']}::CID={cid}::target_field({TARGET_FIELD})",
        "formula": "count hydrogen-bond donor atoms from visible SMILES structural tokens",
        "formula_inputs": {"smiles": smiles, "model_kind": MODEL_KIND},
        "prediction_inputs": {"visible_fields": visible_fields, "target_fields_excluded": TARGET_FIELDS},
        "predicted_value": predicted,
        "observed_value": target,
        "observed_value_text": as_str(record.get(TARGET_FIELD)),
        "uncertainty": MAX_ROW_ABS_ERROR,
        "uncertainty_basis": "integer PubChem descriptor; exact match required per row",
        "model_residual": model_residual,
        "residual_within_uncertainty": model_residual <= MAX_ROW_ABS_ERROR,
        "comparator_baseline_kind": as_str(comparator.get("kind")),
        "comparator_baseline_name": as_str(comparator.get("name")),
        "comparator_prediction_rule": as_str(comparator.get("prediction_rule")),
        "comparator_pre_registered": comparator.get("pre_registered") is True,
        "comparator_baseline_sha256": as_str(comparator.get("baseline_sha256")),
        "comparator_prediction": comparator_prediction,
        "comparator_residual": comparator_residual,
        "comparator_material_margin": comparator_residual - model_residual,
        "comparator_material_margin_met": comparator_residual - model_residual >= MIN_COMPARATOR_ADVANTAGE,
        "negative_controls": controls,
        "negative_control_id": controls[0]["control_id"],
        "negative_control_description": controls[0]["description"],
        "negative_control_rejected": all(row["rejected"] for row in controls),
        "nontrivial_negative_controls_rejected": all(row["rejected"] for row in nontrivial_controls),
        "falsifier": "SMILES donor-count residual is nonzero, target leaks into visible/comparator inputs, target is formula-mass replay, or aggregate formula-only comparator is not materially worse",
        "falsifier_status": "TRIGGERED" if falsifier_triggered else "NOT_TRIGGERED",
    }
    failures.extend(comparator_failures(comparator))
    if row["official_source_confirmed"] is not True:
        failures.append("OFFICIAL_PUBCHEM_PROVENANCE_REQUIRED")
    if row["declared_before_scoring_lock"] is not True:
        failures.append("DECLARED_BEFORE_SCORING_LOCK_MISSING")
    if row["target_hidden_until_scoring"] is not True:
        failures.append("TARGET_HIDDEN_UNTIL_SCORING_REQUIRED")
    if row["prediction_materialized_before_target_open"] is not True:
        failures.append("PREDICTION_MATERIALIZATION_LOCK_MISSING")
    if row["target_read_before_prediction_materialization"] is True:
        failures.append("TARGET_READ_BEFORE_PREDICTION_MATERIALIZATION")
    if TARGET_FIELD == "MolecularWeight":
        failures.append("FORMULA_MASS_TARGET_NOT_INDEPENDENT")
    row["row_hash"] = row_hash(row)
    row["row_hash_policy"] = ROW_HASH_POLICY
    return row, ordered_unique(failures)


def residual_summary(rows: list[dict[str, Any]]) -> dict[str, float]:
    if not rows:
        return {"model": 0.0, "comparator": 0.0, "superiority_margin": 0.0}
    model = sum(as_float(row["model_residual"]) for row in rows) / len(rows)
    comparator = sum(as_float(row["comparator_residual"]) for row in rows) / len(rows)
    return {"model": model, "comparator": comparator, "superiority_margin": comparator - model}


def clean_pack_source() -> dict[str, Any]:
    return {
        "mode": "prospective",
        "pre_target_lock": True,
        "target_hidden_until_scoring": True,
        "training_sources": [f"{ACQUISITION_REL}::visible_fields({','.join(VISIBLE_FIELDS)})"],
        "target_sources": [f"{ACQUISITION_REL}::target_field({TARGET_FIELD})"],
    }


def build_pack(rows: list[dict[str, Any]], comparator: dict[str, Any], *, support_allowed: bool) -> dict[str, Any]:
    residuals = residual_summary(rows)
    maximum_model_residual = max([as_float(row["model_residual"]) for row in rows], default=0.0)
    aggregate_zero_residual = (
        sum(abs(0.0 - as_float(row["observed_value"])) for row in rows) / len(rows)
        if rows
        else 0.0
    )
    return {
        "schema_id": grand_factory.EVIDENCE_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "capability_owner": CAPABILITY_OWNER,
        "evidence_pack_id": "OC133-GRAND-CHEMISTRY-PUBCHEM-HBOND-DONOR",
        "domain": "chemistry",
        "source_separation": clean_pack_source(),
        "n": len(rows),
        "model_under_test": MODEL_UNDER_TEST,
        "comparator_baseline": {
            "name": as_str(comparator.get("name")),
            "prediction_rule": as_str(comparator.get("prediction_rule")),
            "pre_registered": comparator.get("pre_registered") is True,
        },
        "uncertainty": {
            "metric": "mean absolute error in PubChem HBondDonorCount units",
            "method": "integer descriptor exact-match scoring; row residuals must be zero",
            "interval": [0.0, max(MAX_MODEL_MAE, maximum_model_residual)],
        },
        "residuals": residuals,
        "negative_controls": [
            {
                "control_id": "chemistry-hbd-formula-heteroatom-aggregate-control",
                "description": "formula-only N+O heteroatom donor baseline is materially worse than the SMILES donor predictor in aggregate",
                "rejected": residuals["comparator"] - residuals["model"] >= MIN_COMPARATOR_ADVANTAGE,
            },
            {
                "control_id": "chemistry-hbd-zero-count-aggregate-control",
                "description": "constant zero donor-count sanity control is worse than the SMILES donor predictor in aggregate",
                "rejected": aggregate_zero_residual - residuals["model"] >= MIN_COMPARATOR_ADVANTAGE,
            },
        ],
        "falsifiers": ordered_unique([as_str(row.get("falsifier")) for row in rows if row.get("falsifier")]),
        "grand_toe_support_allowed": support_allowed,
    }


def validate_rows(rows: list[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    required = (
        "observation_id",
        "training_source",
        "target_source",
        "source_snapshot_hash",
        "lock_ref",
        "canonical_smiles",
        "formula_inputs",
        "prediction_inputs",
        "predicted_value",
        "observed_value",
        "comparator_prediction",
        "model_residual",
        "comparator_residual",
        "negative_control_id",
        "negative_control_description",
        "falsifier",
        "falsifier_status",
        "row_hash",
    )
    for row in rows:
        row_id = as_str(row.get("observation_id"), "unknown")
        for field in required:
            if row.get(field) in (None, ""):
                failures.append(f"ROW_FIELD_MISSING::{row_id}::{field}")
        for field in ("predicted_value", "observed_value", "model_residual", "comparator_residual"):
            if not is_number(row.get(field)):
                failures.append(f"ROW_NUMERIC_INVALID::{row_id}::{field}")
        if row.get("target_field") == "MolecularWeight":
            failures.append(f"FORMULA_MASS_TARGET_NOT_INDEPENDENT::{row_id}")
        if row.get("training_source") == row.get("target_source"):
            failures.append(f"ROW_SOURCE_OVERLAP::{row_id}")
        if row.get("official_source_confirmed") is not True:
            failures.append(f"OFFICIAL_PUBCHEM_PROVENANCE_REQUIRED::{row_id}")
        if row.get("declared_before_scoring_lock") is not True:
            failures.append(f"DECLARED_BEFORE_SCORING_LOCK_MISSING::{row_id}")
        if row.get("target_hidden_until_scoring") is not True:
            failures.append(f"TARGET_HIDDEN_UNTIL_SCORING_REQUIRED::{row_id}")
        if row.get("target_read_before_prediction_materialization") is True:
            failures.append(f"TARGET_READ_BEFORE_PREDICTION_MATERIALIZATION::{row_id}")
        if row.get("residual_within_uncertainty") is not True:
            failures.append(f"RESIDUAL_EXCEEDS_UNCERTAINTY::{row_id}")
        if row.get("falsifier_status") != "NOT_TRIGGERED":
            failures.append(f"FALSIFIER_TRIGGERED::{row_id}")
    return ordered_unique(failures)


def validate_source_separation() -> list[str]:
    source = clean_pack_source()
    if set(source["training_sources"]) & set(source["target_sources"]):
        return ["TRAINING_TARGET_SOURCE_OVERLAP"]
    return []


def build_protocol(blockers: list[str]) -> dict[str, Any]:
    return {
        "schema_id": PROTOCOL_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "generated_by": PLANNER_REF,
        "target_class": TARGET_CLASS,
        "target_field": TARGET_FIELD,
        "official_source": "PubChem PUG REST",
        "minimum_n": MINIMUM_N_DEFAULT,
        "visible_fields": VISIBLE_FIELDS,
        "target_fields": TARGET_FIELDS,
        "model_under_test": MODEL_UNDER_TEST,
        "comparator_baseline": default_comparator(),
        "uncertainty_policy": {"max_row_abs_error": MAX_ROW_ABS_ERROR, "max_model_mae": MAX_MODEL_MAE},
        "negative_controls": [
            "formula-only N+O heteroatom baseline",
            "constant zero donor-count sanity control",
        ],
        "falsifiers": [
            "target field appears in visible projection or comparator inputs",
            "target field is MolecularWeight or formula-mass replay",
            "SMILES donor-count residual is nonzero",
            "formula-only comparator is not materially worse",
            "N<20 or official source hash/lock missing",
        ],
        "current_blockers": ordered_unique(blockers),
        "support_policy": SUPPORT_POLICY,
        "no_send": True,
    }


def build_work_order(acquisition: dict[str, Any], blockers: list[str]) -> dict[str, Any]:
    return {
        "schema_id": "OC133_CHEMISTRY_PUBCHEM_HBOND_DONOR_ACQUISITION_WORK_ORDER_v1",
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "planner": PLANNER_REF,
        "status": "BLOCKED_ACQUISITION_REQUIRED" if acquisition["request_total"] else "BLOCKED_SCORING_REQUIRED",
        "reason": "Chemistry independent HBondDonorCount lane cannot close until official no-send PubChem snapshots and strict scoring pass.",
        "acquisition_packet_ref": ACQUISITION_REL,
        "standard_runner_command": (
            f"python tools/oc133_official_readonly_acquisition_runner.py --packet {ACQUISITION_REL} --execute-network"
        ),
        "request_total": acquisition["request_total"],
        "current_n": acquisition["current_n"],
        "minimum_n": acquisition["minimum_n"],
        "remaining_blockers": ordered_unique(blockers),
        "no_send": True,
        "locks": NO_SEND_LOCKS,
    }


def build_report(
    rows: list[dict[str, Any]],
    blockers: list[str],
    support_allowed: bool,
    pack: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_id": REPORT_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "generated_by": PLANNER_REF,
        "target_class": TARGET_CLASS,
        "target_field": TARGET_FIELD,
        "candidate_n": len(rows),
        "minimum_n": MINIMUM_N_DEFAULT,
        "residuals": residual_summary(rows),
        "grand_toe_support_allowed": support_allowed,
        "candidate_pack_ref": CANDIDATE_PACK_REL,
        "candidate_pack_sha256": sha256_object(pack),
        "blockers": ordered_unique(blockers),
        "support_policy": SUPPORT_POLICY,
    }


def build_hashes(root: Path, payloads: dict[str, Any]) -> dict[str, Any]:
    artifact_hashes = {ref: sha256_object(payload) for ref, payload in payloads.items() if ref != README_REL}
    return {
        "schema_id": HASHES_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "generated_by": PLANNER_REF,
        "hash_policy": PACK_HASH_POLICY,
        "artifact_hashes": artifact_hashes,
        "artifact_set_sha256": sha256_object(artifact_hashes),
    }


def build_readme(report: dict[str, Any], acquisition: dict[str, Any]) -> str:
    blockers = "\n".join(f"- `{blocker}`" for blocker in report["blockers"]) or "- none"
    return (
        "# OC133 Chemistry PubChem HBondDonorCount Target Lane\n\n"
        f"- Target: `{TARGET_FIELD}` (`{TARGET_CLASS}`)\n"
        f"- Candidate N: `{report['candidate_n']}` / `{report['minimum_n']}`\n"
        f"- Missing acquisitions: `{acquisition['request_total']}`\n"
        f"- Grand TOE support allowed: `{str(report['grand_toe_support_allowed']).lower()}`\n\n"
        "## Blockers\n\n"
        f"{blockers}\n"
    )


def build_payload(
    root: Path | None = None,
    *,
    comparator_baseline: dict[str, Any] | None = None,
    visible_fields: list[str] | None = None,
) -> dict[str, Any]:
    root = root or ROOT
    comparator = comparator_baseline or default_comparator()
    visible = visible_fields or list(VISIBLE_FIELDS)
    requirements = read_json(root / REQUIREMENTS_REL) if (root / REQUIREMENTS_REL).exists() else {"minimum_per_domain_n": MINIMUM_N_DEFAULT}
    minimum_n = int(requirements.get("minimum_per_domain_n", MINIMUM_N_DEFAULT))
    sources, source_blockers = load_official_snapshots(root)
    rows: list[dict[str, Any]] = []
    row_blockers: list[str] = []
    for index, source in enumerate(sorted(sources, key=lambda row: row["acquisition_id"]), start=1):
        row, failures = build_row(source, index, comparator=comparator, visible_fields=visible)
        row_blockers.extend(failures)
        if row is not None:
            rows.append(row)

    blockers = [*source_blockers, *row_blockers, *validate_rows(rows), *validate_source_separation()]
    if len(rows) < minimum_n:
        blockers.append(f"N_BELOW_MINIMUM::{len(rows)}/{minimum_n}")
    if comparator_failures(comparator):
        blockers.extend(comparator_failures(comparator))
    residuals = residual_summary(rows)
    if rows and residuals["model"] > MAX_MODEL_MAE:
        blockers.append("MODEL_RESIDUAL_EXCEEDS_POLICY")
    if rows and residuals["superiority_margin"] < MIN_COMPARATOR_ADVANTAGE:
        blockers.append("COMPARATOR_NOT_WORSE_THAN_MODEL_BY_AGGREGATE_MARGIN")

    blockers = ordered_unique(blockers)
    support_allowed = len(rows) >= minimum_n and not blockers
    pack = build_pack(rows, comparator, support_allowed=support_allowed)
    if not support_allowed:
        pack["grand_toe_support_allowed"] = False
    acquisition = acquisition_packet([row["snapshot_ref"] for row in sources], rows, blockers)
    protocol = build_protocol(blockers)
    report = build_report(rows, blockers, support_allowed, pack)
    tasks = {
        "schema_id": TASKS_SCHEMA_ID,
        "release_id": RELEASE_ID,
        "version": VERSION,
        "capability_owner": CAPABILITY_OWNER,
        "generated_by": PLANNER_REF,
        "target_class": TARGET_CLASS,
        "target_field": TARGET_FIELD,
        "row_hash_policy": ROW_HASH_POLICY,
        "rows": rows,
        "blockers": blockers,
    }
    work_order = build_work_order(acquisition, blockers)
    payloads: dict[str, Any] = {
        TASKS_REL: tasks,
        PROTOCOL_REL: protocol,
        CANDIDATE_PACK_REL: pack,
        REPORT_REL: report,
        ACQUISITION_REL: acquisition,
        WORK_ORDER_REL: work_order,
    }
    hashes = build_hashes(root, payloads)
    return {
        "tasks": tasks,
        "protocol": protocol,
        "candidate_pack": pack,
        "report": report,
        "acquisition_packet": acquisition,
        "work_order": work_order,
        "hashes": hashes,
        "readme": build_readme(report, acquisition),
        "payloads": {**payloads, HASHES_REL: hashes},
    }


def write_outputs(root: Path | None = None) -> dict[str, Any]:
    root = root or ROOT
    payload = build_payload(root)
    for ref, artifact in payload["payloads"].items():
        write_json(root / ref, artifact)
    write_text(root / README_REL, payload["readme"])
    return payload


def check_stored(root: Path | None = None) -> list[str]:
    root = root or ROOT
    expected = build_payload(root)
    failures: list[str] = []
    for ref, payload in expected["payloads"].items():
        path = root / ref
        if not path.exists():
            failures.append(f"MISSING::{ref}")
            continue
        try:
            actual = read_json(path)
        except Exception as exc:
            failures.append(f"PARSE_FAILED::{ref}::{exc.__class__.__name__}")
            continue
        if actual != payload:
            failures.append(f"CONTENT_MISMATCH::{ref}")
    readme_path = root / README_REL
    if not readme_path.exists():
        failures.append(f"MISSING::{README_REL}")
    elif readme_path.read_text(encoding="utf-8") != expected["readme"]:
        failures.append(f"CONTENT_MISMATCH::{README_REL}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Build PubChem HBondDonorCount independent chemistry target artifacts.")
    parser.add_argument("--check", action="store_true", help="Check stored artifacts against regenerated payloads.")
    parser.add_argument("--write", action="store_true", help="Write generated artifacts.")
    parser.add_argument("--allow-blocked-exit-zero", action="store_true")
    args = parser.parse_args()

    if args.check:
        failures = check_stored(ROOT)
        print(json.dumps({"check_failures": failures}, indent=2))
        return 1 if failures else 0
    payload = write_outputs(ROOT) if args.write else build_payload(ROOT)
    print(json.dumps(payload["report"], indent=2))
    if payload["report"]["grand_toe_support_allowed"] is True:
        return 0
    return 0 if args.allow_blocked_exit_zero else 2


if __name__ == "__main__":
    raise SystemExit(main())
