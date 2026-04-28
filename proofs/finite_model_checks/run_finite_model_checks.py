from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "proofs" / "finite_model_checks" / "OC133_FINITE_MODEL_INPUTS.json"
OUTPUT = ROOT / "proofs" / "FINITE_MODEL_CHECKS_1_3_3.json"
COMPONENT_TOTAL = 11
KLEVEL_TOTAL = 12


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def observed(row: dict) -> str:
    model = row.get("model", {})
    theorem_id = row.get("theorem_id")
    case_type = row.get("case_type")
    if case_type == "theorem_case":
        if theorem_id == "T133-K0-RES":
            ok = model.get("rho_cell_a") == model.get("rho_cell_b") and model.get("claims_raw_separation") is False
        elif theorem_id == "T133-OMEGA-STATUS":
            ok = model.get("admissible") is True and model.get("live") is True and model.get("death") is False and model.get("cycle_mode") not in {None, "", "none"} and model.get("residue_class") != model.get("identity_class")
        elif theorem_id == "T133-K-ZERO":
            causes = model.get("zero_causes", {})
            ok = bool(causes) and model.get("k_value") == 0 and any(bool(value) for value in causes.values())
        elif theorem_id == "T133-BOUNDARY":
            ok = model.get("boundary_kind") == "classifier" and model.get("metric_specialization") in {True, False} and model.get("failure_equivalence_checked") is True
        elif theorem_id == "T133-HYBRID":
            ok = model.get("primitive") == "typed_update" and model.get("smooth_requires_chart") is True and model.get("hybrid_guard_reset_checked") is True
        elif theorem_id == "T133-DIM":
            ok = model.get("historical_rank", 0) > model.get("effective_rank", 0) and model.get("historical_erased") is False
        elif theorem_id == "T133-CYCLE":
            ok = model.get("live") is True and (model.get("cycle_mode") not in {None, "", "none"} or model.get("maintenance_predicate") is True)
        elif theorem_id == "T133-ID":
            ok = model.get("morphism") in {"residue", "rebirth"} and model.get("identity_invariant_preserved") is False and model.get("classified_as_identity") is False
        elif theorem_id == "T133-MIN":
            ok = model.get("witness_pair_count") == COMPONENT_TOTAL and model.get("all_one_component_deltas") is True and model.get("all_verdict_changes") is True
        elif theorem_id == "T133-KLEVEL":
            ok = model.get("transition_count") == KLEVEL_TOTAL and model.get("all_reductions_fail_with_retained_witness") is True and model.get("lawful_demotion_rule_present") is True
        else:
            ok = False
        return "ACCEPT" if ok else "REJECT"
    if case_type == "component_keep_drop_witness":
        required = set(model.get("required_components", []))
        ok = (
            model.get("component") == row.get("component")
            and model.get("keep_present") is True
            and model.get("drop_present") is False
            and model.get("changed_fields") == [row.get("component")]
            and row.get("component") in required
            and model.get("dropped_component") == row.get("component")
        )
        return "FAIL" if ok else "PASS"
    if case_type == "adjacent_k_transition_witness":
        if (
            model.get("transition_id") == row.get("transition_id")
            and model.get("witness_retained") is True
            and model.get("added_axis_observable") is True
            and model.get("demotion_allowed") is False
            and model.get("reduction_attempt") == "remove_added_axis"
        ):
            return "FAILS_WITH_WITNESS"
        if (
            model.get("transition_id") == row.get("transition_id")
            and model.get("witness_retained") is False
            and model.get("added_axis_observable") is False
            and model.get("demotion_allowed") is True
            and model.get("lawful_demotion_condition") == "witness_unobservable"
        ):
            return "DEMOTABLE_WITH_LOST_WITNESS"
        return "REDUCTION_UNCHECKED"
    if case_type == "no_send_state_machine":
        owner_approved = model.get("owner_approved") is True
        publish_requested = model.get("publish_requested") is True
        publish_allowed = model.get("publish_allowed") is True
        if publish_requested and not owner_approved and not publish_allowed:
            return "REJECT_PUBLIC_ACTION"
        if publish_requested and owner_approved and publish_allowed:
            return "ALLOW_AFTER_OWNER_APPROVAL"
        return "NO_ACTION"
    return "UNKNOWN"


def evaluate(row: dict) -> dict:
    out = dict(row)
    if any(key.startswith("observed_") for key in row):
        out["input_schema_violation"] = "input rows must not contain observed_* verdict fields"
        out["passed"] = False
        return out
    obs = observed(row)
    if row.get("case_type") == "component_keep_drop_witness":
        out["observed_keep_verdict"] = "PASS" if obs == "FAIL" else "FAIL"
        out["observed_drop_verdict"] = obs
        out["passed"] = obs == row.get("expected_drop_verdict")
    elif row.get("case_type") == "adjacent_k_transition_witness":
        out["observed_reduction_verdict"] = obs
        out["passed"] = obs == row.get("expected_reduction_verdict")
    else:
        out["observed_verdict"] = obs
        out["passed"] = obs == row.get("expected_verdict")
    return out


def main() -> int:
    inputs = json.loads(INPUT.read_text(encoding="utf-8"))
    rows = [evaluate(row) for row in inputs["rows"]]
    failures = [row for row in rows if not row.get("passed")]
    payload = {
        "schema_id": "OC133_FINITE_MODEL_CHECKS_v12_SEMANTIC_EXECUTED",
        "release_id": "oc_core_1_3_3",
        "version": "1.3.3",
        "runner": "proofs/finite_model_checks/run_finite_model_checks.py",
        "runner_sha256": sha256_file(Path(__file__)),
        "input_ref": "proofs/finite_model_checks/OC133_FINITE_MODEL_INPUTS.json",
        "input_sha256": sha256_file(INPUT),
        "command": "python proofs/finite_model_checks/run_finite_model_checks.py",
        "semantic_evaluator": True,
        "input_observed_field_total": sum(1 for row in inputs["rows"] for key in row if key.startswith("observed_")),
        "case_total": len(rows),
        "positive_case_total": sum(1 for row in rows if row.get("case_type") == "theorem_case" and row.get("expected_verdict") == "ACCEPT"),
        "negative_case_total": sum(1 for row in rows if row.get("case_type") == "theorem_case" and row.get("expected_verdict") == "REJECT"),
        "component_witness_total": sum(1 for row in rows if row.get("case_type") == "component_keep_drop_witness"),
        "k_transition_witness_total": sum(1 for row in rows if row.get("case_type") == "adjacent_k_transition_witness" and row.get("expected_reduction_verdict") == "FAILS_WITH_WITNESS"),
        "k_transition_negative_total": sum(1 for row in rows if row.get("case_type") == "adjacent_k_transition_witness" and row.get("expected_reduction_verdict") == "DEMOTABLE_WITH_LOST_WITNESS"),
        "no_send_state_machine_total": sum(1 for row in rows if row.get("case_type") == "no_send_state_machine"),
        "failure_total": len(failures),
        "machine_checked_subset_total": 10,
        "rows": rows,
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
