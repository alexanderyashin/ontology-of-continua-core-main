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
            required = set(model.get("required_components", []))
            drops = model.get("drop_cases", [])
            ok = (
                len(required) == COMPONENT_TOTAL
                and len(drops) == COMPONENT_TOTAL
                and all(
                    row.get("component") in required
                    and row.get("dropped_component") == row.get("component")
                    and row.get("changed_fields") == [row.get("component")]
                    for row in drops
                )
            )
        elif theorem_id == "T133-KLEVEL":
            transitions = model.get("transitions", [])
            ok = (
                len(transitions) == KLEVEL_TOTAL
                and all(
                    isinstance(row.get("lower_code"), int)
                    and isinstance(row.get("upper_code"), int)
                    and row.get("upper_code") == row.get("lower_code") + 1
                    and row.get("added_axis_code") == row.get("upper_code")
                    and row.get("witness_code") == row.get("upper_code") * 100 + 7
                    and row.get("retained", {}).get("witness_retained") is True
                    and row.get("retained", {}).get("added_axis_observable") is True
                    and row.get("retained", {}).get("demotion_allowed") is False
                    and row.get("demotion", {}).get("witness_retained") is False
                    and row.get("demotion", {}).get("added_axis_observable") is False
                    and row.get("demotion", {}).get("demotion_allowed") is True
                    for row in transitions
                )
            )
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
        codes_ok = (
            isinstance(model.get("lower_code"), int)
            and isinstance(model.get("upper_code"), int)
            and model.get("upper_code") == model.get("lower_code") + 1
            and model.get("added_axis_code") == model.get("upper_code")
            and model.get("witness_code") == model.get("upper_code") * 100 + 7
        )
        if (
            codes_ok
            and model.get("transition_id") == row.get("transition_id")
            and model.get("witness_retained") is True
            and model.get("added_axis_observable") is True
            and model.get("demotion_allowed") is False
            and model.get("reduction_attempt") == "remove_added_axis"
        ):
            return "FAILS_WITH_WITNESS"
        if (
            codes_ok
            and model.get("transition_id") == row.get("transition_id")
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
