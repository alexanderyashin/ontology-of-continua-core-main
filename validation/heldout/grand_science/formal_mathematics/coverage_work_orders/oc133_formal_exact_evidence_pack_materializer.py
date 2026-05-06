from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[5]

LANES: dict[str, dict[str, Any]] = {
    "computational_complexity_algorithmic_proof": {
        "domain_class_id": "formal_mathematics_and_logic",
        "phenomenon_class_id": "computational_complexity_and_algorithmic_proof",
        "scorer_ref": (
            "validation/heldout/grand_science/formal_mathematics/coverage_work_orders/"
            "planned_corpora/computational_complexity_algorithmic_proof/"
            "OC133_COMPLEXITY_ALGORITHMIC_SCORER.py"
        ),
        "input_ref": (
            "validation/heldout/grand_science/formal_mathematics/coverage_work_orders/"
            "planned_corpora/computational_complexity_algorithmic_proof/"
            "OC133_COMPLEXITY_ALGORITHMIC_FORMAL_INPUTS.json"
        ),
        "executed_ref": (
            "validation/heldout/grand_science/formal_mathematics/coverage_work_orders/"
            "planned_corpora/computational_complexity_algorithmic_proof/"
            "OC133_COMPLEXITY_ALGORITHMIC_EXECUTED_PROOF_CORPUS.json"
        ),
        "lock_ref": (
            "validation/heldout/grand_science/formal_mathematics/coverage_work_orders/"
            "planned_corpora/computational_complexity_algorithmic_proof/"
            "OC133_COMPLEXITY_ALGORITHMIC_WITHHELD_AGGREGATES.lock.json"
        ),
        "output_ref": (
            "validation/heldout/grand_science/formal_mathematics/exact_evidence/"
            "computational_complexity_algorithmic_proof/"
            "OC133_FORMAL_COMPLEXITY_ALGORITHMIC_STRICT_EVIDENCE_PACK.json"
        ),
        "model_label": "deterministic complexity derivation replay",
        "comparator_label": "predeclared naive/incorrect formal comparator",
    },
    "formal_theorem_reconstruction": {
        "domain_class_id": "formal_mathematics_and_logic",
        "phenomenon_class_id": "formal_theorem_reconstruction",
        "math_executor_ref": "validation/heldout/domain_evidence/mathematics_evidence_executor.py",
        "report_ref": "validation/heldout/grand_science/mathematics/OC133_MATHEMATICS_EVIDENCE_EXECUTION_REPORT.json",
        "candidate_pack_ref": "validation/heldout/grand_science/mathematics/mathematics_candidate_evidence_pack.json",
        "output_ref": (
            "validation/heldout/grand_science/formal_mathematics/exact_evidence/"
            "formal_theorem_reconstruction/"
            "OC133_FORMAL_THEOREM_RECONSTRUCTION_STRICT_EVIDENCE_PACK.json"
        ),
        "model_label": "finite/proof/Lean theorem reconstruction replay",
        "comparator_label": "accept-all formal comparator",
    },
    "statistical_inference_identifiability": {
        "domain_class_id": "formal_mathematics_and_logic",
        "phenomenon_class_id": "statistical_inference_identifiability",
        "scorer_ref": (
            "validation/heldout/grand_science/formal_mathematics/coverage_work_orders/"
            "planned_corpora/statistical_probabilistic_inference/"
            "OC133_STAT_PROB_IDENTIFIABILITY_SCORER.py"
        ),
        "input_ref": (
            "validation/heldout/grand_science/formal_mathematics/coverage_work_orders/"
            "planned_corpora/statistical_probabilistic_inference/"
            "OC133_STAT_PROB_IDENTIFIABILITY_FORMAL_INPUTS.json"
        ),
        "executed_ref": (
            "validation/heldout/grand_science/formal_mathematics/coverage_work_orders/"
            "planned_corpora/statistical_probabilistic_inference/"
            "OC133_STAT_PROB_IDENTIFIABILITY_EXECUTED_PROOF_CORPUS.json"
        ),
        "lock_ref": (
            "validation/heldout/grand_science/formal_mathematics/coverage_work_orders/"
            "planned_corpora/statistical_probabilistic_inference/"
            "OC133_STAT_PROB_IDENTIFIABILITY_WITHHELD_AGGREGATES.lock.json"
        ),
        "output_ref": (
            "validation/heldout/grand_science/formal_mathematics/exact_evidence/"
            "statistical_inference_identifiability/"
            "OC133_FORMAL_STAT_PROB_IDENTIFIABILITY_STRICT_EVIDENCE_PACK.json"
        ),
        "model_label": "deterministic identifiability derivation replay",
        "comparator_label": "predeclared naive identifiability comparator",
    },
}


def read_json(ref: str) -> Any:
    with open(io_path(ROOT / ref), "r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(ref: str, payload: Any) -> None:
    path = ROOT / ref
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(io_path(path), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def io_path(path: Path) -> str:
    if os.name != "nt":
        return str(path)
    absolute = str(path.resolve())
    return absolute if absolute.startswith("\\\\?\\") else "\\\\?\\" + absolute


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(ref: str) -> str:
    with open(io_path(ROOT / ref), "rb") as handle:
        return sha256_bytes(handle.read())


def sha256_object(payload: Any) -> str:
    return sha256_bytes(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def run_json_command(command: list[str]) -> dict[str, Any]:
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"command failed: {' '.join(command)}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"command did not emit JSON: {' '.join(command)}\nSTDOUT:\n{result.stdout}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"command emitted non-object JSON: {' '.join(command)}")
    return payload


def run_plain_command(command: list[str]) -> None:
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"command failed: {' '.join(command)}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")


def formal_pack_from_scorer(lane_id: str, cfg: dict[str, Any]) -> dict[str, Any]:
    scorer = run_json_command([sys.executable, cfg["scorer_ref"], "--check"])
    input_payload = read_json(cfg["input_ref"])
    executed_payload = read_json(cfg["executed_ref"])
    lock_payload = read_json(cfg["lock_ref"])
    failures = list(scorer.get("failures") or [])
    row_count = int(scorer.get("row_count") or 0)
    model = float(scorer.get("model_mismatch_count") or 0)
    comparator = float(scorer.get("comparator_mismatch_count") or 0)
    negative = float(scorer.get("negative_control_rejections") or 0)
    pass_ready = scorer.get("status") == "pass" and row_count >= 20 and model == 0.0 and comparator > model and negative > 0 and not failures
    return {
        "schema_id": "OC133_FORMAL_EXACT_STRICT_EVIDENCE_PACK_v1",
        "pack_status": "STRICT_EVIDENCE_PASS_NO_COVERAGE_CLOSURE" if pass_ready else "FAIL_CLOSED_FORMAL_EXACT_EVIDENCE_NOT_MET",
        "status": "STRICT_EVIDENCE_PASS_NO_COVERAGE_CLOSURE" if pass_ready else "FAIL_CLOSED_FORMAL_EXACT_EVIDENCE_NOT_MET",
        "lane_id": lane_id,
        "domain_class_id": cfg["domain_class_id"],
        "phenomenon_class_id": cfg["phenomenon_class_id"],
        "source_bound": True,
        "target_hidden": True,
        "score_materialized": True,
        "scientific_pass": pass_ready,
        "coverage_closure_allowed": False,
        "support_allowed_for_broad_coverage": False,
        "empirical_numeric_prediction_allowed": False,
        "broad_modern_science_superiority_allowed": False,
        "source_snapshot_ref": cfg["input_ref"],
        "source_snapshot_sha256": sha256_file(cfg["input_ref"]),
        "source_lock_ref": cfg["lock_ref"],
        "source_lock_sha256": sha256_file(cfg["lock_ref"]),
        "visible_task_table_ref": cfg["input_ref"],
        "executed_proof_corpus_ref": cfg["executed_ref"],
        "executed_proof_corpus_sha256": sha256_file(cfg["executed_ref"]),
        "hidden_target_lock_ref": cfg["lock_ref"],
        "row_count": row_count,
        "model": {"model_id": cfg["model_label"], "mismatch_count": model},
        "comparator": {"comparator_id": cfg["comparator_label"], "mismatch_count": comparator},
        "residuals": {
            "model": model,
            "comparator": comparator,
            "negative_control": negative,
            "material_margin_met": pass_ready,
            "material_margin_rule": "formal replay mismatch count must be zero and below the preregistered comparator mismatch count",
        },
        "negative_control": {
            "control_id": f"OC133-{lane_id.upper()}-FORMAL-NEGATIVE-CONTROL",
            "negative_control_rejected": negative > 0,
            "rejected_total": int(negative),
        },
        "falsifiers": [
            "the scorer exits nonzero",
            "the target-hidden input hash or lock hash changes",
            "the formal replay model has any mismatch",
            "the preregistered comparator is not strictly worse",
            "the negative control is not rejected",
        ],
        "formal_scorer_ref": cfg["scorer_ref"],
        "formal_scorer_result": scorer,
        "formal_input_sha256": sha256_object(input_payload),
        "formal_executed_sha256": sha256_object(executed_payload),
        "formal_lock_sha256": sha256_object(lock_payload),
        "replay_command": {
            "commands": [
                f"{sys.executable} {cfg['scorer_ref']} --check",
                f"{sys.executable} validation/heldout/grand_science/formal_mathematics/coverage_work_orders/oc133_formal_exact_evidence_pack_materializer.py --lane {lane_id} --check",
            ]
        },
    }


def formal_pack_from_mathematics_executor(lane_id: str, cfg: dict[str, Any]) -> dict[str, Any]:
    run_plain_command([sys.executable, cfg["math_executor_ref"], "--check"])
    report = read_json(cfg["report_ref"])
    domains = [row for row in report.get("domains", []) if isinstance(row, dict) and row.get("domain") == "mathematics"]
    domain = domains[0] if domains else {}
    residuals = domain.get("residuals", {}) if isinstance(domain.get("residuals"), dict) else {}
    source_assessment = domain.get("source_assessment", {}) if isinstance(domain.get("source_assessment"), dict) else {}
    source_separation = domain.get("source_separation", {}) if isinstance(domain.get("source_separation"), dict) else {}
    model = float(residuals.get("model") or 0.0)
    comparator = float(residuals.get("comparator") or 0.0)
    negative_total = int(domain.get("negative_control_total") or source_assessment.get("negative_control_total") or 0)
    negative_rejected = int(domain.get("negative_control_rejected_total") or source_assessment.get("negative_control_rejected_total") or 0)
    pass_ready = (
        report.get("valid_under_executor_total") == 1
        and report.get("blocked_pack_total") == 0
        and domain.get("formal_support_verdict") == "FORMAL_SUPPORT_ACCEPTED"
        and source_assessment.get("lean_build_returncode") == 0
        and source_separation.get("target_hidden_until_scoring") is True
        and model == 0.0
        and comparator > model
        and negative_total > 0
        and negative_rejected == negative_total
    )
    return {
        "schema_id": "OC133_FORMAL_EXACT_STRICT_EVIDENCE_PACK_v1",
        "pack_status": "STRICT_EVIDENCE_PASS_NO_COVERAGE_CLOSURE" if pass_ready else "FAIL_CLOSED_FORMAL_THEOREM_RECONSTRUCTION_NOT_MET",
        "status": "STRICT_EVIDENCE_PASS_NO_COVERAGE_CLOSURE" if pass_ready else "FAIL_CLOSED_FORMAL_THEOREM_RECONSTRUCTION_NOT_MET",
        "lane_id": lane_id,
        "domain_class_id": cfg["domain_class_id"],
        "phenomenon_class_id": cfg["phenomenon_class_id"],
        "source_bound": True,
        "target_hidden": True,
        "score_materialized": True,
        "scientific_pass": pass_ready,
        "coverage_closure_allowed": False,
        "support_allowed_for_broad_coverage": False,
        "empirical_numeric_prediction_allowed": False,
        "broad_modern_science_superiority_allowed": False,
        "source_snapshot_ref": str(domain.get("snapshot_ref") or "proofs/FINITE_MODEL_CHECKS_1_3_3.json"),
        "source_snapshot_sha256": str(domain.get("snapshot_sha256") or ""),
        "source_lock_ref": str(domain.get("input_ref") or "proofs/finite_model_checks/OC133_FINITE_MODEL_INPUTS.json"),
        "source_lock_sha256": str(domain.get("input_sha256") or ""),
        "visible_task_table_ref": str(domain.get("input_ref") or ""),
        "hidden_target_lock_ref": str(domain.get("snapshot_ref") or ""),
        "candidate_pack_ref": cfg["candidate_pack_ref"],
        "candidate_pack_sha256": str(domain.get("candidate_pack_sha256") or sha256_file(cfg["candidate_pack_ref"])),
        "execution_report_ref": cfg["report_ref"],
        "execution_report_sha256": sha256_file(cfg["report_ref"]),
        "row_count": int(domain.get("candidate_n") or 0),
        "model": {"model_id": cfg["model_label"], "mismatch_count": model},
        "comparator": {"comparator_id": cfg["comparator_label"], "mismatch_count": comparator},
        "residuals": {
            "model": model,
            "comparator": comparator,
            "negative_control": float(negative_rejected),
            "material_margin_met": pass_ready,
            "material_margin_rule": "formal theorem replay residual must be zero and below the accept-all comparator residual",
        },
        "negative_control": {
            "control_id": "OC133-FORMAL-THEOREM-RECONSTRUCTION-NEGATIVE-CONTROL",
            "negative_control_rejected": negative_rejected == negative_total and negative_total > 0,
            "rejected_total": negative_rejected,
        },
        "falsifiers": list(domain.get("falsifiers") or []),
        "formal_theorem_ids": list(domain.get("formal_theorem_ids") or []),
        "formal_proof_sheet_refs": list(domain.get("formal_proof_sheet_refs") or []),
        "formal_lean_refs": list(domain.get("formal_lean_refs") or []),
        "formal_finite_case_ids": list(domain.get("formal_finite_case_ids") or []),
        "source_assessment": source_assessment,
        "source_separation": source_separation,
        "replay_command": {
            "commands": [
                f"{sys.executable} {cfg['math_executor_ref']} --check",
                f"{sys.executable} validation/heldout/grand_science/formal_mathematics/coverage_work_orders/oc133_formal_exact_evidence_pack_materializer.py --lane {lane_id} --check",
            ]
        },
    }


def materialize_lane(lane_id: str) -> dict[str, Any]:
    cfg = LANES[lane_id]
    if "scorer_ref" in cfg:
        return formal_pack_from_scorer(lane_id, cfg)
    return formal_pack_from_mathematics_executor(lane_id, cfg)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Materialize exact formal-route strict evidence packs for OC 1.3.3 coverage rows.")
    parser.add_argument("--lane", choices=sorted(LANES), required=True)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    cfg = LANES[args.lane]
    pack = materialize_lane(args.lane)
    if args.write:
        write_json(cfg["output_ref"], pack)
    if args.check:
        written = read_json(cfg["output_ref"]) if (ROOT / cfg["output_ref"]).exists() else {}
        failures: list[str] = []
        if not written:
            failures.append("FORMAL_STRICT_EVIDENCE_PACK_MISSING")
        if written.get("scientific_pass") is not True:
            failures.append("FORMAL_STRICT_EVIDENCE_PACK_NOT_PASS")
        if written.get("source_bound") is not True or written.get("target_hidden") is not True:
            failures.append("FORMAL_STRICT_EVIDENCE_PACK_NOT_SOURCE_BOUND")
        if written.get("coverage_closure_allowed") is not False:
            failures.append("FORMAL_PACK_MUST_NOT_ALLOW_DIRECT_COVERAGE_CLOSURE")
        if written.get("residuals", {}).get("material_margin_met") is not True:
            failures.append("FORMAL_PACK_MATERIAL_MARGIN_NOT_MET")
        print(json.dumps({"lane_id": args.lane, "status": "PASS" if not failures else "FAIL", "failures": failures}, indent=2, sort_keys=True))
        return 0 if not failures else 1
    print(json.dumps(pack, indent=2, sort_keys=True))
    return 0 if pack.get("scientific_pass") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
