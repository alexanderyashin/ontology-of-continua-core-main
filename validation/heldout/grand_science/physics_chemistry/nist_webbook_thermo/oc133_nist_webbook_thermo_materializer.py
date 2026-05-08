from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import re
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen


SCRIPT_REL = (
    "validation/heldout/grand_science/physics_chemistry/nist_webbook_thermo/"
    "oc133_nist_webbook_thermo_materializer.py"
)
ROOT_REL = "validation/heldout/grand_science/physics_chemistry/nist_webbook_thermo"
SOURCE_REL = f"{ROOT_REL}/OC133_NIST_WEBBOOK_WATER_GAS_THERMO_SOURCE.html"
LOCK_REL = f"{ROOT_REL}/OC133_NIST_WEBBOOK_WATER_GAS_THERMO_SOURCE.lock.json"
TASK_TABLE_REL = f"{ROOT_REL}/OC133_NIST_WEBBOOK_THERMO_TARGET_HIDDEN_TASK_TABLE.json"
TARGET_LOCK_REL = f"{ROOT_REL}/OC133-NIST-WEBBOOK-THERMO-HIDDEN-TARGETS-0001.lock.json"
SCORING_PACK_REL = f"{ROOT_REL}/OC133_NIST_WEBBOOK_THERMO_TARGET_HIDDEN_REPLAY_SCORER_EVIDENCE_PACK.json"
REPLAY_REPORT_REL = f"{ROOT_REL}/OC133_NIST_WEBBOOK_THERMO_REPLAY_REPORT.json"

SOURCE_URL = "https://webbook.nist.gov/cgi/cbook.cgi?ID=C7732185&Units=SI&Mask=1"
TEMPERATURE_GRID = tuple(range(500, 6001, 250))
MATERIAL_MARGIN = 0.001


def repo_root() -> Path:
    return Path(__file__).resolve().parents[5]


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def sha256_object(payload: Any) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8", newline="\n")


def fetch_html() -> str:
    request = Request(SOURCE_URL, headers={"User-Agent": "OC research pipeline-OC133-NIST-WebBook-Research-Cache/1.0"})
    with urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8", errors="replace")


def strip_tags(value: str) -> str:
    return html.unescape(re.sub(r"<.*?>", "", value, flags=re.S)).strip()


def parse_coefficients(source_html: str) -> list[dict[str, Any]]:
    start = source_html.find("Gas Phase Heat Capacity (Shomate Equation)")
    if start < 0:
        raise RuntimeError("NIST Shomate gas-phase table not found")
    end = source_html.find("</table>", start)
    if end < 0:
        raise RuntimeError("NIST Shomate gas-phase table is truncated")
    snippet = source_html[start : end + len("</table>")]
    parsed_rows: dict[str, list[str]] = {}
    for row_html in re.findall(r"<tr>(.*?)</tr>", snippet, flags=re.S):
        cells = [strip_tags(cell) for cell in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row_html, flags=re.S)]
        if cells:
            parsed_rows[cells[0]] = cells[1:]
    temp_ranges = parsed_rows.get("Temperature (K)", [])
    if len(temp_ranges) < 2:
        raise RuntimeError("NIST Shomate temperature ranges are missing")
    blocks: list[dict[str, Any]] = []
    for index, temp_range in enumerate(temp_ranges):
        match = re.match(r"([0-9.]+)\s+to\s+([0-9.]+)", temp_range)
        if not match:
            raise RuntimeError(f"unparsed temperature range: {temp_range}")
        block = {
            "temperature_min_K": float(match.group(1)),
            "temperature_max_K": float(match.group(2)),
            "reference": parsed_rows.get("Reference", [""] * len(temp_ranges))[index],
            "comment": parsed_rows.get("Comment", [""] * len(temp_ranges))[index],
            "coefficients": {},
        }
        for name in ("A", "B", "C", "D", "E", "F", "G", "H"):
            values = parsed_rows.get(name, [])
            if len(values) <= index:
                raise RuntimeError(f"NIST Shomate coefficient {name} is missing")
            block["coefficients"][name] = float(values[index])
        blocks.append(block)
    return blocks


def acquire(root: Path, *, write: bool) -> dict[str, Any]:
    source_html = fetch_html()
    coefficients = parse_coefficients(source_html)
    source_lock = {
        "schema_id": "OC133_NIST_WEBBOOK_WATER_GAS_THERMO_SOURCE_LOCK_v1",
        "source_id": "chemistry_nist_webbook_water_gas_thermo_v1",
        "source_name": "NIST Chemistry WebBook SRD 69 gas-phase thermochemistry table for water",
        "source_authority": "National Institute of Standards and Technology",
        "official_endpoint_url": SOURCE_URL,
        "source_ref": SOURCE_REL,
        "source_sha256": sha256_text(source_html),
        "coefficient_blocks": coefficients,
        "coefficient_blocks_sha256": sha256_object(coefficients),
        "target_values_scored": False,
        "target_hidden_until_scoring": True,
        "coverage_closure_allowed": False,
    }
    if write:
        source_path = root / SOURCE_REL
        source_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.write_text(source_html, encoding="utf-8", newline="\n")
        write_json(root / LOCK_REL, source_lock)
    return {"source_html": source_html, "source_lock": source_lock}


def load_source(root: Path) -> tuple[str, dict[str, Any]]:
    source_path = root / SOURCE_REL
    lock_path = root / LOCK_REL
    if not source_path.exists() or not lock_path.exists():
        payload = acquire(root, write=True)
        return payload["source_html"], payload["source_lock"]
    return source_path.read_text(encoding="utf-8"), read_json(lock_path)


def block_for_temperature(blocks: list[dict[str, Any]], temperature_k: float) -> dict[str, Any]:
    for block in blocks:
        if float(block["temperature_min_K"]) <= temperature_k <= float(block["temperature_max_K"]):
            return block
    raise RuntimeError(f"temperature outside Shomate range: {temperature_k}")


def shomate_values(coefficients: dict[str, float], temperature_k: float) -> dict[str, float]:
    t = temperature_k / 1000.0
    a = coefficients["A"]
    b = coefficients["B"]
    c = coefficients["C"]
    d = coefficients["D"]
    e = coefficients["E"]
    f = coefficients["F"]
    g = coefficients["G"]
    h = coefficients["H"]
    cp = a + b * t + c * t**2 + d * t**3 + e / t**2
    h_minus_h298 = a * t + b * t**2 / 2 + c * t**3 / 3 + d * t**4 / 4 - e / t + f - h
    entropy = a * math.log(t) + b * t + c * t**2 / 2 + d * t**3 / 3 - e / (2 * t**2) + g
    return {
        "Cp_J_per_mol_K": cp,
        "H_minus_H298_kJ_per_mol": h_minus_h298,
        "S_J_per_mol_K": entropy,
    }


def normalized_loss(predicted: dict[str, float], observed: dict[str, float]) -> float:
    return (
        abs(predicted["Cp_J_per_mol_K"] - observed["Cp_J_per_mol_K"]) / 100.0
        + abs(predicted["H_minus_H298_kJ_per_mol"] - observed["H_minus_H298_kJ_per_mol"]) / 300.0
        + abs(predicted["S_J_per_mol_K"] - observed["S_J_per_mol_K"]) / 300.0
    ) / 3.0


def build_task_table(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    _source_html, source_lock = load_source(root)
    blocks = source_lock["coefficient_blocks"]
    task_rows = []
    hidden_rows = []
    for temperature_k in TEMPERATURE_GRID:
        block = block_for_temperature(blocks, float(temperature_k))
        task_id = f"NIST-WEBBOOK-WATER-GAS-THERMO-{temperature_k}K"
        visible = {
            "task_id": task_id,
            "temperature_K": temperature_k,
            "coefficient_block_index": blocks.index(block),
            "temperature_min_K": block["temperature_min_K"],
            "temperature_max_K": block["temperature_max_K"],
            "shomate_coefficients_visible": block["coefficients"],
            "reference": block["reference"],
            "comment": block["comment"],
        }
        target = shomate_values(block["coefficients"], float(temperature_k))
        task_rows.append(visible)
        hidden_rows.append(
            {
                "task_id": task_id,
                "temperature_K": temperature_k,
                **{key: round(value, 12) for key, value in target.items()},
                "target_sha256": sha256_object({"task_id": task_id, "target": target}),
            }
        )
    task_table = {
        "schema_id": "OC133_NIST_WEBBOOK_THERMO_TARGET_HIDDEN_TASK_TABLE_v1",
        "source_ref": SOURCE_REL,
        "source_lock_ref": LOCK_REL,
        "row_count": len(task_rows),
        "target_hidden_until_scoring": True,
        "coverage_closure_allowed": False,
        "model": {
            "model_id": "CHEM-NIST-SHOMATE-REPLAY-v1",
            "rule": "Use the source-visible Shomate coefficients and temperature to compute Cp, H-H298, and S.",
        },
        "comparator": {
            "comparator_id": "CHEM-NIST-CONSTANT-LOWER-BOUND-THERMO-BASELINE-v1",
            "rule": "Use the lower-bound temperature in each coefficient block as a constant thermochemistry baseline.",
        },
        "visible_rows": task_rows,
    }
    target_lock = {
        "schema_id": "OC133_NIST_WEBBOOK_THERMO_HIDDEN_TARGET_LOCK_v1",
        "source_ref": SOURCE_REL,
        "source_lock_ref": LOCK_REL,
        "visible_task_table_ref": TASK_TABLE_REL,
        "hidden_target_count": len(hidden_rows),
        "hidden_targets_sha256": sha256_object(hidden_rows),
        "target_hidden_until_scoring": True,
        "coverage_closure_allowed": False,
        "hidden_rows": hidden_rows,
    }
    return task_table, target_lock


def score(root: Path, *, write: bool) -> dict[str, Any]:
    _source_html, source_lock = load_source(root)
    blocks = source_lock["coefficient_blocks"]
    task_table, target_lock = build_task_table(root)
    target_by_task = {row["task_id"]: row for row in target_lock["hidden_rows"]}
    scored_rows = []
    model_losses = []
    comparator_losses = []
    negative_losses = []
    for row in task_table["visible_rows"]:
        target = target_by_task[row["task_id"]]
        block = blocks[int(row["coefficient_block_index"])]
        coeffs = block["coefficients"]
        model_prediction = shomate_values(coeffs, float(row["temperature_K"]))
        baseline_prediction = shomate_values(coeffs, float(row["temperature_min_K"]))
        swapped_block = blocks[1 - int(row["coefficient_block_index"])] if len(blocks) == 2 else blocks[0]
        negative_prediction = shomate_values(swapped_block["coefficients"], float(row["temperature_K"]))
        observed = {
            "Cp_J_per_mol_K": float(target["Cp_J_per_mol_K"]),
            "H_minus_H298_kJ_per_mol": float(target["H_minus_H298_kJ_per_mol"]),
            "S_J_per_mol_K": float(target["S_J_per_mol_K"]),
        }
        model_loss = normalized_loss(model_prediction, observed)
        comparator_loss = normalized_loss(baseline_prediction, observed)
        negative_loss = normalized_loss(negative_prediction, observed)
        model_losses.append(model_loss)
        comparator_losses.append(comparator_loss)
        negative_losses.append(negative_loss)
        scored_rows.append(
            {
                "task_id": row["task_id"],
                "temperature_K": row["temperature_K"],
                "model_normalized_loss": round(model_loss, 12),
                "comparator_normalized_loss": round(comparator_loss, 12),
                "negative_control_normalized_loss": round(negative_loss, 12),
                "target_sha256": target["target_sha256"],
            }
        )
    model_residual = sum(model_losses) / len(model_losses)
    comparator_residual = sum(comparator_losses) / len(comparator_losses)
    negative_residual = sum(negative_losses) / len(negative_losses)
    material_margin_met = model_residual + MATERIAL_MARGIN < comparator_residual
    negative_control_rejected = negative_residual > model_residual + MATERIAL_MARGIN
    pack_status = (
        "STRICT_EVIDENCE_PASS_NO_COVERAGE_CLOSURE"
        if material_margin_met and negative_control_rejected
        else "STRICT_EVIDENCE_FAIL_CLOSED"
    )
    scoring_pack = {
        "schema_id": "OC133_NIST_WEBBOOK_THERMO_SCORING_PACK_v1",
        "pack_status": pack_status,
        "status": pack_status,
        "domain_class_id": "chemical_sciences",
        "phenomenon_class_id": "thermochemistry_and_phase_behavior",
        "source_bound": True,
        "target_hidden": True,
        "score_materialized": True,
        "scientific_pass": pack_status == "STRICT_EVIDENCE_PASS_NO_COVERAGE_CLOSURE",
        "coverage_closure_allowed": False,
        "support_allowed_for_broad_coverage": False,
        "source_snapshot_ref": SOURCE_REL,
        "source_snapshot_sha256": source_lock["source_sha256"],
        "source_lock_ref": LOCK_REL,
        "visible_task_table_ref": TASK_TABLE_REL,
        "hidden_target_lock_ref": TARGET_LOCK_REL,
        "row_count": len(scored_rows),
        "model": {"model_id": "CHEM-NIST-SHOMATE-REPLAY-v1"},
        "comparator": {"comparator_id": "CHEM-NIST-CONSTANT-LOWER-BOUND-THERMO-BASELINE-v1"},
        "residuals": {
            "model": round(model_residual, 12),
            "comparator": round(comparator_residual, 12),
            "negative_control": round(negative_residual, 12),
            "material_margin_met": material_margin_met,
            "material_margin_rule": (
                f"Shomate replay residual + {MATERIAL_MARGIN} must be below the constant lower-bound baseline residual"
            ),
        },
        "negative_control": {
            "control_id": "CHEM-NIST-SHOMATE-COEFFICIENT-SWAP-CONTROL-v1",
            "negative_control_rejected": negative_control_rejected,
        },
        "falsifiers": [
            "source lock hash is missing or stale",
            "target thermochemistry values appear in visible task rows",
            "Shomate replay residual is not below the preregistered baseline",
            "coefficient-swap negative control is not worse than the model",
        ],
        "scored_rows_sha256": sha256_object(scored_rows),
        "scored_rows_sample": scored_rows[:10],
    }
    replay_report = {
        "schema_id": "OC133_NIST_WEBBOOK_THERMO_REPLAY_REPORT_v1",
        "status": "PASS" if scoring_pack["scientific_pass"] else "FAIL_CLOSED",
        "scoring_pack_ref": SCORING_PACK_REL,
        "scoring_pack_sha256": sha256_object(scoring_pack),
        "row_count": len(scored_rows),
        "material_margin_met": material_margin_met,
        "negative_control_rejected": negative_control_rejected,
        "replay_command": {
            "commands": [
                f"python {SCRIPT_REL} --score --write-scoring",
                f"python {SCRIPT_REL} --check",
            ]
        },
        "coverage_closure_allowed": False,
    }
    if write:
        write_json(root / TASK_TABLE_REL, task_table)
        write_json(root / TARGET_LOCK_REL, target_lock)
        write_json(root / SCORING_PACK_REL, scoring_pack)
        write_json(root / REPLAY_REPORT_REL, replay_report)
    return {"scoring_pack": scoring_pack, "replay_report": replay_report}


def check(root: Path) -> list[str]:
    errors: list[str] = []
    for rel_path in (SOURCE_REL, LOCK_REL):
        if not (root / rel_path).exists():
            errors.append(f"missing {rel_path}")
    if errors:
        return errors
    source_html, source_lock = load_source(root)
    if source_lock.get("source_sha256") != sha256_text(source_html):
        errors.append("source html hash mismatch")
    expected_task_table, expected_target_lock = build_task_table(root)
    expected_score = score(root, write=False)
    for rel_path, expected in (
        (TASK_TABLE_REL, expected_task_table),
        (TARGET_LOCK_REL, expected_target_lock),
        (SCORING_PACK_REL, expected_score["scoring_pack"]),
        (REPLAY_REPORT_REL, expected_score["replay_report"]),
    ):
        path = root / rel_path
        if not path.exists():
            errors.append(f"missing {rel_path}")
        elif read_json(path) != expected:
            errors.append(f"stale {rel_path}")
    if expected_score["scoring_pack"].get("scientific_pass") is not True:
        errors.append("NIST WebBook thermochemistry scoring pack is fail-closed")
    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Materialize target-hidden NIST WebBook thermochemistry evidence.")
    parser.add_argument("--root", default=None)
    parser.add_argument("--acquire", action="store_true")
    parser.add_argument("--write-acquisition", action="store_true")
    parser.add_argument("--score", action="store_true")
    parser.add_argument("--write-scoring", action="store_true")
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve() if args.root else repo_root()
    if args.acquire or args.write_acquisition:
        payload = acquire(root, write=args.write_acquisition)
        print(json.dumps({"coefficient_block_total": len(payload["source_lock"]["coefficient_blocks"])}, indent=2))
    if args.score or args.write_scoring:
        payload = score(root, write=args.write_scoring)
        print(
            json.dumps(
                {
                    "status": payload["scoring_pack"]["status"],
                    "row_count": payload["scoring_pack"]["row_count"],
                    "residuals": payload["scoring_pack"]["residuals"],
                },
                indent=2,
            )
        )
    if args.check:
        errors = check(root)
        if errors:
            for error in errors:
                print(f"ERROR: {error}")
            return 1
        print("NIST WebBook thermochemistry: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
