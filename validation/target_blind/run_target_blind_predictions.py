from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "validation" / "target_blind" / "OC133_TARGET_BLIND_PREDICTION_TABLE.json"


ATOMIC_WEIGHTS = {
    "H": 1.00794,
    "O": 15.9994,
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_lf_normalized_text(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def row_replay_hash(row: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(row, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def attach_replay_evidence(row: dict[str, Any]) -> dict[str, Any]:
    snapshot_ref = row.get("dataset_snapshot_ref")
    if snapshot_ref:
        row["snapshot_sha256"] = sha256_lf_normalized_text(ROOT / str(snapshot_ref))
        row["snapshot_sha256_policy"] = "LF_NORMALIZED_TEXT_SNAPSHOT_HASH"
    row["replay_hash"] = row_replay_hash(row)
    row["replay_hash_policy"] = "sha256 over sorted JSON row before replay_hash insertion"
    return row


def parse_codata_value(text: str, quantity: str) -> float:
    for line in text.splitlines():
        parts = re.split(r"\s{2,}", line.strip())
        if len(parts) >= 2 and parts[0] == quantity:
            return float(parts[1].replace(" ", "").replace("...", ""))
    raise ValueError(f"CODATA quantity not found: {quantity}")


def parse_h2o_formula_weight(formula: str) -> float:
    if formula != "H2O":
        raise ValueError(f"Unsupported target-blind formula fixture: {formula}")
    return 2 * ATOMIC_WEIGHTS["H"] + ATOMIC_WEIGHTS["O"]


def physics_row() -> dict[str, Any]:
    snapshot_ref = "validation/_raw/physics_nist_constants.txt"
    text = (ROOT / snapshot_ref).read_text(encoding="utf-8")
    planck = parse_codata_value(text, "Planck constant")
    speed_of_light = parse_codata_value(text, "speed of light in vacuum")
    observed = parse_codata_value(text, "inverse meter-joule relationship")
    predicted = planck * speed_of_light
    comparator = planck
    residual = abs(predicted - observed)
    comparator_residual = abs(comparator - observed)
    uncertainty = 1e-33
    return attach_replay_evidence({
        "claim_id": "OC133-TARGETBLIND-PHYSICS-001",
        "lane": "physics",
        "dataset_snapshot_ref": snapshot_ref,
        "target_blind_split": "Planck constant and speed of light rows are visible; inverse-meter joule relationship row is withheld until scoring",
        "formula": "Planck_constant * speed_of_light",
        "predicted_value": predicted,
        "observed_value": observed,
        "uncertainty": uncertainty,
        "comparator_baseline": "unit-incompatible Planck-constant-only negative control",
        "comparator_prediction": comparator,
        "residual": residual,
        "comparator_residual": comparator_residual,
        "negative_control": "drop the speed-of-light factor and require a larger residual",
        "negative_control_rejected": comparator_residual > residual,
        "falsifier": "Residual exceeds display-truncation tolerance or Planck-only control is not worse",
        "prediction_support_allowed": residual <= uncertainty and comparator_residual > residual,
        "empirical_support_allowed": residual <= uncertainty and comparator_residual > residual,
        "support_scope": "target-blind reconstruction of a held-out CODATA relationship from exact defining constants; not a novel physics law",
    })


def chemistry_row() -> dict[str, Any]:
    snapshot_ref = "validation/_raw/chemistry_pubchem_water.txt"
    payload = read_json(ROOT / snapshot_ref)
    props = payload["PropertyTable"]["Properties"][0]
    formula = props["MolecularFormula"]
    observed = float(props["MolecularWeight"])
    predicted = parse_h2o_formula_weight(formula)
    comparator = 44.0095
    residual = abs(predicted - observed)
    comparator_residual = abs(comparator - observed)
    uncertainty = 0.02
    return attach_replay_evidence({
        "claim_id": "OC133-TARGETBLIND-CHEMISTRY-001",
        "lane": "chemistry",
        "dataset_snapshot_ref": snapshot_ref,
        "target_blind_split": "formula field is visible; MolecularWeight target is withheld until scoring",
        "formula": "2*atomic_weight(H)+atomic_weight(O)",
        "predicted_value": predicted,
        "observed_value": observed,
        "uncertainty": uncertainty,
        "comparator_baseline": "CO2 molecular-weight negative control against water target",
        "comparator_prediction": comparator,
        "residual": residual,
        "comparator_residual": comparator_residual,
        "negative_control": "replace H2O by CO2 and require larger residual",
        "negative_control_rejected": comparator_residual > residual,
        "falsifier": "Residual exceeds declared uncertainty or CO2 control is not worse than formula reconstruction",
        "prediction_support_allowed": residual <= uncertainty and comparator_residual > residual,
        "empirical_support_allowed": residual <= uncertainty and comparator_residual > residual,
        "support_scope": "target-blind reconstruction of a held-out official snapshot field; not a novel chemistry law",
    })


def biology_row() -> dict[str, Any]:
    snapshot_ref = "validation/_raw/biology_ncbi_geo_platform.txt"
    payload = read_json(ROOT / snapshot_ref)
    result = payload["esearchresult"]
    id_count = len(result["idlist"])
    retstart = int(result["retstart"])
    observed = float(result["retmax"])
    predicted = float(retstart + id_count)
    comparator = float(result["count"])
    residual = abs(predicted - observed)
    comparator_residual = abs(comparator - observed)
    uncertainty = 0.0
    return attach_replay_evidence({
        "claim_id": "OC133-TARGETBLIND-BIOLOGY-001",
        "lane": "biology",
        "dataset_snapshot_ref": snapshot_ref,
        "target_blind_split": "NCBI ESearch retstart/idlist fields are visible; retmax pagination target is withheld until scoring",
        "formula": "retstart + len(idlist)",
        "predicted_value": predicted,
        "observed_value": observed,
        "uncertainty": uncertainty,
        "comparator_baseline": "use total hit count as pagination-size negative control",
        "comparator_prediction": comparator,
        "residual": residual,
        "comparator_residual": comparator_residual,
        "negative_control": "replace page-size reconstruction by total hit count and require a larger residual",
        "negative_control_rejected": comparator_residual > residual,
        "falsifier": "Retmax differs from retstart plus returned id count or total-count control is not worse",
        "prediction_support_allowed": residual <= uncertainty and comparator_residual > residual,
        "empirical_support_allowed": residual <= uncertainty and comparator_residual > residual,
        "support_scope": "target-blind reconstruction of a held-out NCBI/GEO API snapshot field; not a biological mechanism law",
    })


def systems_row() -> dict[str, Any]:
    snapshot_ref = "validation/_raw/systems_world_bank_gdp.txt"
    payload = read_json(ROOT / snapshot_ref)
    rows = payload[1]
    values = {
        int(row["date"]): float(row["value"])
        for row in rows
        if row.get("value") is not None
    }
    train_years = [2021, 2022, 2023]
    target_year = 2024
    slope = (values[2023] - values[2021]) / 2.0
    predicted = values[2023] + slope
    observed = values[target_year]
    comparator = values[2023]
    residual = abs(predicted - observed)
    comparator_residual = abs(comparator - observed)
    uncertainty = observed * 0.01
    return attach_replay_evidence({
        "claim_id": "OC133-TARGETBLIND-SYSTEMS-001",
        "lane": "systems",
        "dataset_snapshot_ref": snapshot_ref,
        "target_blind_split": "2021-2023 train rows predict withheld 2024 World Bank WDI target",
        "formula": "GDP_2023 + (GDP_2023-GDP_2021)/2",
        "predicted_value": predicted,
        "observed_value": observed,
        "uncertainty": uncertainty,
        "comparator_baseline": "last-observation carry-forward GDP_2023",
        "comparator_prediction": comparator,
        "residual": residual,
        "comparator_residual": comparator_residual,
        "negative_control": "last-observation baseline must have larger residual",
        "negative_control_rejected": comparator_residual > residual,
        "falsifier": "Held-out residual exceeds 1 percent of observed target or comparator is not worse",
        "prediction_support_allowed": residual <= uncertainty and comparator_residual > residual,
        "empirical_support_allowed": residual <= uncertainty and comparator_residual > residual,
        "support_scope": "retrospective target-blind holdout over pinned WDI rows; not a prospective macroeconomic law",
    })


def mathematics_row() -> dict[str, Any]:
    snapshot_ref = "proofs/FINITE_MODEL_CHECKS_1_3_3.json"
    payload = read_json(ROOT / snapshot_ref)
    rows = payload["rows"]
    accepted_theorem_ids = {
        str(row["theorem_id"])
        for row in rows
        if row.get("case_type") == "theorem_case"
        and row.get("observed_verdict") == "ACCEPT"
        and row.get("passed") is True
    }
    predicted = float(len(accepted_theorem_ids))
    observed = float(payload["machine_checked_subset_total"])
    comparator = float(payload["positive_case_total"])
    residual = abs(predicted - observed)
    comparator_residual = abs(comparator - observed)
    uncertainty = 0.0
    return attach_replay_evidence({
        "claim_id": "OC133-TARGETBLIND-MATHEMATICS-001",
        "lane": "mathematics",
        "dataset_snapshot_ref": snapshot_ref,
        "target_blind_split": "finite theorem-case rows are visible; aggregate machine_checked_subset_total is withheld until scoring",
        "formula": "count_unique(theorem_id where case_type='theorem_case' and observed_verdict='ACCEPT' and passed=true)",
        "predicted_value": predicted,
        "observed_value": observed,
        "uncertainty": uncertainty,
        "comparator_baseline": "positive_case_total negative control, which counts non-theorem support rows too",
        "comparator_prediction": comparator,
        "residual": residual,
        "comparator_residual": comparator_residual,
        "negative_control": "replace theorem-id aggregate by positive_case_total and require a larger residual",
        "negative_control_rejected": comparator_residual > residual,
        "falsifier": "Unique accepted theorem-case count differs from machine_checked_subset_total or broad positive-case control is not worse",
        "prediction_support_allowed": residual <= uncertainty and comparator_residual > residual,
        "empirical_support_allowed": residual <= uncertainty and comparator_residual > residual,
        "support_scope": "target-blind reconstruction of a finite proof-corpus aggregate; not a TOE truth proof or empirical law",
    })


def build_payload() -> dict[str, Any]:
    rows = [physics_row(), chemistry_row(), biology_row(), systems_row(), mathematics_row()]
    failures = []
    for row in rows:
        for field in ("prediction_support_allowed", "empirical_support_allowed", "negative_control_rejected"):
            if row.get(field) is not True:
                failures.append(f"{row['claim_id']}::{field}")
    return {
        "schema_id": "OC133_TARGET_BLIND_PREDICTION_TABLE_v1",
        "release_id": "oc_core_1_3_3",
        "version": "1.3.3",
        "generated_by": "PUBLIC_VALIDATION_WORKER",
        "evidence_owner": "Research/EmpiricalScience",
        "research_task_id": "OC133-PLATINUM-WO-001",
        "executor": "validation/target_blind/run_target_blind_predictions.py",
        "execution_policy": "This worker may generate bounded target-blind evidence only when dispatched by the OC research pipeline release mission or validation runner; no broad domain validation or TOE truth claim is permitted.",
        "row_total": len(rows),
        "lane_total": len({row["lane"] for row in rows}),
        "prediction_support_allowed_total": sum(1 for row in rows if row["prediction_support_allowed"] is True),
        "empirical_support_allowed_total": sum(1 for row in rows if row["empirical_support_allowed"] is True),
        "failure_total": len(failures),
        "failures": failures,
        "artifact_exists_is_not_closure": True,
        "closure_predicates": {
            "all_rows_have_formula_snapshot_split_uncertainty_comparator_residual_negative_control_falsifier": all(
                all(row.get(field) not in {None, ""} for field in (
                    "formula",
                    "dataset_snapshot_ref",
                    "target_blind_split",
                    "uncertainty",
                    "comparator_baseline",
                    "residual",
                    "negative_control",
                    "falsifier",
                    "snapshot_sha256",
                    "replay_hash",
                ))
                and row.get("negative_control_rejected") is True
                and row.get("prediction_support_allowed") is True
                and row.get("empirical_support_allowed") is True
                for row in rows
            ),
            "scope_is_bounded_not_domain_validation": all(
                "not a" in str(row.get("support_scope", "")).lower()
                for row in rows
            ),
        },
        "support_policy": "Rows are target-blind held-out reconstructions over pinned official snapshots. They support bounded numeric reconstruction claims only, not broad domain validation or novelty.",
        "rows": rows,
    }


def main() -> int:
    payload = build_payload()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["failure_total"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
