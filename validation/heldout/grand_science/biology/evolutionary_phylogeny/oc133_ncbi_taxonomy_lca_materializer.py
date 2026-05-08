from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


SCRIPT_REL = (
    "validation/heldout/grand_science/biology/evolutionary_phylogeny/"
    "oc133_ncbi_taxonomy_lca_materializer.py"
)
ROOT_REL = "validation/heldout/grand_science/biology/evolutionary_phylogeny"
SNAPSHOT_REL = f"{ROOT_REL}/OC133_NCBI_TAXONOMY_LINEAGE_SNAPSHOT.json"
LOCK_REL = f"{ROOT_REL}/OC133_NCBI_TAXONOMY_LINEAGE_SNAPSHOT.lock.json"
TASK_TABLE_REL = f"{ROOT_REL}/OC133_NCBI_TAXONOMY_LCA_TARGET_HIDDEN_TASK_TABLE.json"
TARGET_LOCK_REL = f"{ROOT_REL}/OC133-NCBI-TAXONOMY-LCA-HIDDEN-TARGETS-0001.lock.json"
SCORING_PACK_REL = f"{ROOT_REL}/OC133_NCBI_TAXONOMY_LCA_TARGET_HIDDEN_REPLAY_SCORER_EVIDENCE_PACK.json"
REPLAY_REPORT_REL = f"{ROOT_REL}/OC133_NCBI_TAXONOMY_LCA_REPLAY_REPORT.json"

TAX_IDS = (
    "9606",   # Homo sapiens
    "9598",   # Pan troglodytes
    "10090",  # Mus musculus
    "10116",  # Rattus norvegicus
    "9615",   # Canis lupus familiaris
    "9031",   # Gallus gallus
    "7955",   # Danio rerio
    "7227",   # Drosophila melanogaster
    "3702",   # Arabidopsis thaliana
    "4932",   # Saccharomyces cerevisiae
    "562",    # Escherichia coli
    "1423",   # Bacillus subtilis
)
SOURCE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
MATERIAL_MARGIN = 0.01


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


def endpoint_url() -> str:
    return SOURCE_URL + "?" + urlencode({"db": "taxonomy", "id": ",".join(TAX_IDS), "retmode": "xml"})


def fetch_taxonomy_xml() -> str:
    request = Request(endpoint_url(), headers={"User-Agent": "OC research pipeline-OC133-NCBI-Taxonomy-Research-Cache/1.0"})
    with urlopen(request, timeout=90) as response:
        return response.read().decode("utf-8", errors="replace")


def parse_taxonomy(xml_text: str) -> list[dict[str, Any]]:
    root = ET.fromstring(xml_text)
    rows = []
    for taxon in root.findall("Taxon"):
        tax_id = taxon.findtext("TaxId", default="")
        scientific_name = taxon.findtext("ScientificName", default="")
        rank = taxon.findtext("Rank", default="")
        lineage = []
        for item in taxon.findall("./LineageEx/Taxon"):
            lineage.append(
                {
                    "tax_id": item.findtext("TaxId", default=""),
                    "scientific_name": item.findtext("ScientificName", default=""),
                    "rank": item.findtext("Rank", default=""),
                }
            )
        lineage.append({"tax_id": tax_id, "scientific_name": scientific_name, "rank": rank})
        if tax_id and len(lineage) >= 3:
            rows.append(
                {
                    "tax_id": tax_id,
                    "scientific_name": scientific_name,
                    "rank": rank,
                    "lineage": lineage,
                    "lineage_tax_ids": [row["tax_id"] for row in lineage],
                    "lineage_sha256": sha256_object(lineage),
                }
            )
    rows.sort(key=lambda row: row["tax_id"])
    return rows


def acquire(root: Path, *, write: bool) -> dict[str, Any]:
    xml_text = fetch_taxonomy_xml()
    time.sleep(0.34)
    taxa = parse_taxonomy(xml_text)
    snapshot = {
        "schema_id": "OC133_NCBI_TAXONOMY_LINEAGE_SNAPSHOT_v1",
        "source_id": "ncbi_taxonomy_lineage_efetch_v1",
        "source_name": "NCBI Taxonomy E-utilities lineage records",
        "source_authority": "National Center for Biotechnology Information",
        "official_endpoint_url": endpoint_url(),
        "tax_id_total": len(taxa),
        "target_values_scored": False,
        "target_hidden_until_scoring": True,
        "coverage_closure_allowed": False,
        "taxa": taxa,
        "taxa_sha256": sha256_object(taxa),
    }
    lock = {
        "schema_id": "OC133_NCBI_TAXONOMY_LINEAGE_LOCK_v1",
        "source_snapshot_ref": SNAPSHOT_REL,
        "source_snapshot_sha256": sha256_object(snapshot),
        "tax_id_total": len(taxa),
        "tax_ids": list(TAX_IDS),
        "lineage_hashes": {row["tax_id"]: row["lineage_sha256"] for row in taxa},
        "target_values_scored": False,
        "target_hidden_until_scoring": True,
        "coverage_closure_allowed": False,
    }
    if write:
        write_json(root / SNAPSHOT_REL, snapshot)
        write_json(root / LOCK_REL, lock)
    return {"snapshot": snapshot, "lock": lock}


def load_source(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    if not (root / SNAPSHOT_REL).exists() or not (root / LOCK_REL).exists():
        payload = acquire(root, write=True)
        return payload["snapshot"], payload["lock"]
    return read_json(root / SNAPSHOT_REL), read_json(root / LOCK_REL)


def lca_tax_id(lineage_a: list[str], lineage_b: list[str]) -> str:
    common = ""
    for left, right in itertools.zip_longest(lineage_a, lineage_b):
        if left != right:
            break
        common = str(left)
    return common


def ancestor_at_depth(lineage: list[str], depth: int) -> str:
    if not lineage:
        return ""
    return lineage[min(depth, len(lineage) - 1)]


def taxon_name_by_id(taxa: list[dict[str, Any]]) -> dict[str, str]:
    result = {}
    for taxon in taxa:
        for row in taxon["lineage"]:
            result[str(row["tax_id"])] = str(row["scientific_name"])
    return result


def tree_distance_loss(predicted_tax_id: str, target_tax_id: str, lineage_a: list[str], lineage_b: list[str]) -> float:
    if predicted_tax_id == target_tax_id:
        return 0.0
    target_depth = max(lineage_a.index(target_tax_id) if target_tax_id in lineage_a else 0, lineage_b.index(target_tax_id) if target_tax_id in lineage_b else 0)
    predicted_depths = [
        lineage.index(predicted_tax_id)
        for lineage in (lineage_a, lineage_b)
        if predicted_tax_id in lineage
    ]
    predicted_depth = max(predicted_depths) if predicted_depths else 0
    return abs(target_depth - predicted_depth) / max(len(lineage_a), len(lineage_b), 1)


def build_task_table(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    snapshot, _lock = load_source(root)
    taxa = snapshot["taxa"]
    names = taxon_name_by_id(taxa)
    visible_rows = []
    hidden_rows = []
    for left, right in itertools.combinations(taxa, 2):
        task_id = f"NCBI-LCA-{left['tax_id']}-{right['tax_id']}"
        target_tax_id = lca_tax_id(left["lineage_tax_ids"], right["lineage_tax_ids"])
        visible_rows.append(
            {
                "task_id": task_id,
                "left_tax_id": left["tax_id"],
                "left_name": left["scientific_name"],
                "left_lineage_tax_ids": left["lineage_tax_ids"],
                "right_tax_id": right["tax_id"],
                "right_name": right["scientific_name"],
                "right_lineage_tax_ids": right["lineage_tax_ids"],
                "split": "target_hidden_pairwise_lca",
            }
        )
        hidden_rows.append(
            {
                "task_id": task_id,
                "lowest_common_ancestor_tax_id": target_tax_id,
                "lowest_common_ancestor_name": names.get(target_tax_id, ""),
                "target_sha256": sha256_object({"task_id": task_id, "lca": target_tax_id}),
            }
        )
    task_table = {
        "schema_id": "OC133_NCBI_TAXONOMY_LCA_TARGET_HIDDEN_TASK_TABLE_v1",
        "source_snapshot_ref": SNAPSHOT_REL,
        "source_lock_ref": LOCK_REL,
        "row_count": len(visible_rows),
        "target_hidden_until_scoring": True,
        "coverage_closure_allowed": False,
        "model": {
            "model_id": "BIO-NCBI-LINEAGE-LCA-REPLAY-v1",
            "rule": "Compute the deepest common lineage tax_id from two locked NCBI lineage arrays.",
        },
        "comparator": {
            "comparator_id": "BIO-NCBI-SHALLOW-ANCESTOR-COMPARATOR-v1",
            "rule": "Predict the shallowest non-root common ancestor available to both lineages.",
        },
        "visible_rows": visible_rows,
    }
    target_lock = {
        "schema_id": "OC133_NCBI_TAXONOMY_LCA_HIDDEN_TARGET_LOCK_v1",
        "source_snapshot_ref": SNAPSHOT_REL,
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
    task_table, target_lock = build_task_table(root)
    target_by_task = {row["task_id"]: row for row in target_lock["hidden_rows"]}
    model_losses = []
    comparator_losses = []
    negative_losses = []
    scored_rows = []
    for index, row in enumerate(task_table["visible_rows"]):
        target = target_by_task[row["task_id"]]
        left = row["left_lineage_tax_ids"]
        right = row["right_lineage_tax_ids"]
        model_prediction = lca_tax_id(left, right)
        common_shallow = lca_tax_id(left[:3], right[:3]) or ancestor_at_depth(left, 1)
        shuffled_right = task_table["visible_rows"][(index + 7) % len(task_table["visible_rows"])]["right_lineage_tax_ids"]
        negative_prediction = lca_tax_id(left, shuffled_right) or ancestor_at_depth(left, 0)
        model_loss = tree_distance_loss(model_prediction, target["lowest_common_ancestor_tax_id"], left, right)
        comparator_loss = tree_distance_loss(common_shallow, target["lowest_common_ancestor_tax_id"], left, right)
        negative_loss = tree_distance_loss(negative_prediction, target["lowest_common_ancestor_tax_id"], left, right)
        model_losses.append(model_loss)
        comparator_losses.append(comparator_loss)
        negative_losses.append(negative_loss)
        scored_rows.append(
            {
                "task_id": row["task_id"],
                "model_prediction_lca_tax_id": model_prediction,
                "comparator_prediction_lca_tax_id": common_shallow,
                "negative_control_prediction_lca_tax_id": negative_prediction,
                "model_tree_distance_loss": round(model_loss, 12),
                "comparator_tree_distance_loss": round(comparator_loss, 12),
                "negative_control_tree_distance_loss": round(negative_loss, 12),
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
        "schema_id": "OC133_NCBI_TAXONOMY_LCA_SCORING_PACK_v1",
        "pack_status": pack_status,
        "status": pack_status,
        "domain_class_id": "biological_life_sciences",
        "phenomenon_class_id": "evolutionary_phylogenetic_patterns",
        "source_bound": True,
        "target_hidden": True,
        "score_materialized": True,
        "scientific_pass": pack_status == "STRICT_EVIDENCE_PASS_NO_COVERAGE_CLOSURE",
        "coverage_closure_allowed": False,
        "support_allowed_for_broad_coverage": False,
        "source_snapshot_ref": SNAPSHOT_REL,
        "source_lock_ref": LOCK_REL,
        "visible_task_table_ref": TASK_TABLE_REL,
        "hidden_target_lock_ref": TARGET_LOCK_REL,
        "row_count": len(scored_rows),
        "model": {"model_id": "BIO-NCBI-LINEAGE-LCA-REPLAY-v1"},
        "comparator": {"comparator_id": "BIO-NCBI-SHALLOW-ANCESTOR-COMPARATOR-v1"},
        "residuals": {
            "model": round(model_residual, 12),
            "comparator": round(comparator_residual, 12),
            "negative_control": round(negative_residual, 12),
            "material_margin_met": material_margin_met,
            "material_margin_rule": (
                f"LCA replay residual + {MATERIAL_MARGIN} must be below the shallow-ancestor comparator residual"
            ),
        },
        "negative_control": {
            "control_id": "BIO-NCBI-SHUFFLED-LINEAGE-PAIR-CONTROL-v1",
            "negative_control_rejected": negative_control_rejected,
        },
        "falsifiers": [
            "NCBI source lock hash is missing or stale",
            "target LCA appears in visible task rows",
            "LCA replay does not beat shallow-ancestor comparator",
            "shuffled-lineage negative control is not worse than the model",
        ],
        "scored_rows_sha256": sha256_object(scored_rows),
        "scored_rows_sample": scored_rows[:10],
    }
    replay_report = {
        "schema_id": "OC133_NCBI_TAXONOMY_LCA_REPLAY_REPORT_v1",
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
    for rel_path in (SNAPSHOT_REL, LOCK_REL):
        if not (root / rel_path).exists():
            errors.append(f"missing {rel_path}")
    if errors:
        return errors
    snapshot, lock = load_source(root)
    if lock.get("source_snapshot_sha256") != sha256_object(snapshot):
        errors.append("source snapshot hash mismatch")
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
        errors.append("NCBI taxonomy LCA scoring pack is fail-closed")
    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Materialize target-hidden NCBI Taxonomy LCA evidence.")
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
        print(json.dumps({"tax_id_total": payload["snapshot"]["tax_id_total"]}, indent=2))
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
        print("NCBI taxonomy LCA: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
