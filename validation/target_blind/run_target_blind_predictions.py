from __future__ import annotations

import json
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


def parse_h2o_formula_weight(formula: str) -> float:
    if formula != "H2O":
        raise ValueError(f"Unsupported target-blind formula fixture: {formula}")
    return 2 * ATOMIC_WEIGHTS["H"] + ATOMIC_WEIGHTS["O"]


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
    return {
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
    }


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
    return {
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
    }


def build_payload() -> dict[str, Any]:
    rows = [chemistry_row(), systems_row()]
    failures = []
    for row in rows:
        for field in ("prediction_support_allowed", "empirical_support_allowed", "negative_control_rejected"):
            if row.get(field) is not True:
                failures.append(f"{row['claim_id']}::{field}")
    return {
        "schema_id": "OC133_TARGET_BLIND_PREDICTION_TABLE_v1",
        "release_id": "oc_core_1_3_3",
        "version": "1.3.3",
        "generated_by": "LOGION_CAPABILITY_WORKER",
        "capability_owner": "Research/EmpiricalScience",
        "work_order_id": "OC133-PLATINUM-WO-001",
        "executor": "validation/target_blind/run_target_blind_predictions.py",
        "execution_policy": "This worker may generate bounded target-blind evidence only when dispatched by the Logion release mission or validation runner; no broad domain validation or TOE truth claim is permitted.",
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
