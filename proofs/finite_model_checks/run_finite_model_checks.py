from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "proofs" / "finite_model_checks" / "OC133_FINITE_MODEL_INPUTS.json"
OUTPUT = ROOT / "proofs" / "FINITE_MODEL_CHECKS_1_3_3.json"


FORBIDDEN_MODEL_KEYS = {
    "observed_verdict",
    "observed_drop_verdict",
    "observed_keep_verdict",
    "observed_reduction_verdict",
    "failure_equivalence_checked",
    "hybrid_guard_reset_checked",
    "semantic_evaluator",
    "oracle_attestation",
    "witness_retained",
    "added_axis_observable",
    "demotion_allowed",
    "keep_present",
    "drop_present",
    "changed_fields",
}

COMPONENT_FIELDS = {
    "carrier": "carrier_witness",
    "realization": "realization_interprets",
    "lawful_possibility": "lawful_transition_only",
    "liveness": "live_support_witness",
    "residue": "residue_separated",
    "morphisms": "morphism_invariant_checked",
    "boundaries": "boundary_rejects_bad_state",
    "operators": "typed_operator_update",
    "cycles": "cycle_or_maintenance",
    "dimension": "dimension_axes_separated",
    "k": "k_zero_cause_declared",
}

EXPECTED_KLEVEL = {
    "K0_to_K1": {
        "from_k": 0,
        "to_k": 1,
        "added_axis": "distinguishable state -> minimal continuum",
        "witness_pair": "continuity obligation changes verdict",
        "reduction_failure_criterion": "remove continuity and frozen label passes",
        "lawful_demotion_criterion": "demote if no continuity obligation is observed",
    },
    "K1_to_K2": {
        "from_k": 1,
        "to_k": 2,
        "added_axis": "minimal continuum -> phase threshold",
        "witness_pair": "threshold crossing changes admissibility",
        "reduction_failure_criterion": "encode as K1 and miss crossing",
        "lawful_demotion_criterion": "demote if threshold never affects verdict",
    },
    "K2_to_K3": {
        "from_k": 2,
        "to_k": 3,
        "added_axis": "phase threshold -> autocatalytic closure",
        "witness_pair": "closure production is required",
        "reduction_failure_criterion": "phase-only model accepts non-producing set",
        "lawful_demotion_criterion": "demote if closure production is irrelevant",
    },
    "K3_to_K4": {
        "from_k": 3,
        "to_k": 4,
        "added_axis": "closure -> membrane boundary",
        "witness_pair": "inside/outside classifier changes verdict",
        "reduction_failure_criterion": "closure-only model admits leaking state",
        "lawful_demotion_criterion": "demote if boundary classifier has no observable effect",
    },
    "K4_to_K5": {
        "from_k": 4,
        "to_k": 5,
        "added_axis": "boundary -> excitable regulation",
        "witness_pair": "signal-triggered update changes verdict",
        "reduction_failure_criterion": "membrane-only model misses excitation",
        "lawful_demotion_criterion": "demote if excitation never affects status",
    },
    "K5_to_K6": {
        "from_k": 5,
        "to_k": 6,
        "added_axis": "regulation -> binding prediction",
        "witness_pair": "binding relation changes next-state prediction",
        "reduction_failure_criterion": "regulation-only model misses binding",
        "lawful_demotion_criterion": "demote if binding is observationally inert",
    },
    "K6_to_K7": {
        "from_k": 6,
        "to_k": 7,
        "added_axis": "binding -> trust coordination",
        "witness_pair": "norm/role classifier changes allowed action",
        "reduction_failure_criterion": "binding-only model admits norm violation",
        "lawful_demotion_criterion": "demote if roles do not change allowed actions",
    },
    "K7_to_K8": {
        "from_k": 7,
        "to_k": 8,
        "added_axis": "coordination -> regime shift",
        "witness_pair": "meta-state transition changes future rules",
        "reduction_failure_criterion": "coordination-only model freezes rules",
        "lawful_demotion_criterion": "demote if regime state is constant",
    },
    "K8_to_K9": {
        "from_k": 8,
        "to_k": 9,
        "added_axis": "regime -> theory dynamics",
        "witness_pair": "claim/evidence update changes theory verdict",
        "reduction_failure_criterion": "regime-only model lacks claim revision",
        "lawful_demotion_criterion": "demote if claim revision is disabled",
    },
    "K9_to_K10": {
        "from_k": 9,
        "to_k": 10,
        "added_axis": "theory dynamics -> recursive self-application",
        "witness_pair": "model applies to its own updates",
        "reduction_failure_criterion": "K9 model cannot type self-update",
        "lawful_demotion_criterion": "demote if self-reference is absent",
    },
    "K10_to_K11": {
        "from_k": 10,
        "to_k": 11,
        "added_axis": "recursion -> cross-domain coherence",
        "witness_pair": "translation invariant changes verdict",
        "reduction_failure_criterion": "recursive single-domain model passes incoherent translation",
        "lawful_demotion_criterion": "demote if no cross-domain bridge exists",
    },
    "K11_to_K12": {
        "from_k": 11,
        "to_k": 12,
        "added_axis": "coherence -> release-governed civilizational closure",
        "witness_pair": "owner-gated public action state changes verdict",
        "reduction_failure_criterion": "K11 model cannot represent no-send governance",
        "lawful_demotion_criterion": "demote if no release-governed action exists",
    },
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def has_forbidden_key(value: Any) -> bool:
    if isinstance(value, dict):
        return any(key in FORBIDDEN_MODEL_KEYS or has_forbidden_key(child) for key, child in value.items())
    if isinstance(value, list):
        return any(has_forbidden_key(child) for child in value)
    return False


def cycle_or_maintenance(model: dict[str, Any]) -> bool:
    cycle = model.get("cycle_mode")
    maintenance = model.get("maintenance", {})
    return cycle not in {None, "", "none"} or (
        maintenance.get("obligation_checked") is True and maintenance.get("support_available") is True
    )


def zero_cause_active(causes: dict[str, Any]) -> bool:
    return any(bool(causes.get(name)) for name in ("flow", "coherence", "identity", "embedding"))


def semantic_tuple_verdict(model: dict[str, Any]) -> str:
    checks = [
        bool(model.get("carrier_witness")),
        bool(model.get("realization_interprets")),
        bool(model.get("lawful_transition_only")),
        bool(model.get("live_support_witness")),
        bool(model.get("residue_separated")),
        bool(model.get("morphism_invariant_checked")),
        bool(model.get("boundary_rejects_bad_state")),
        bool(model.get("typed_operator_update")),
        bool(model.get("cycle_or_maintenance")),
        bool(model.get("dimension_axes_separated")),
        bool(model.get("k_zero_cause_declared")),
    ]
    return "PASS" if all(checks) else "FAIL"


def semantic_delta_fields(keep: dict[str, Any], drop: dict[str, Any]) -> list[str]:
    return sorted(key for key in COMPONENT_FIELDS.values() if bool(keep.get(key)) != bool(drop.get(key)))


def component_case_valid(case: dict[str, Any]) -> bool:
    target = case.get("target_component")
    target_field = COMPONENT_FIELDS.get(str(target))
    if not target_field:
        return False
    keep = case.get("keep", {})
    drop = case.get("drop", {})
    return (
        semantic_tuple_verdict(keep) == "PASS"
        and semantic_tuple_verdict(drop) == "FAIL"
        and semantic_delta_fields(keep, drop) == [target_field]
        and str(target) in str(case.get("drop_reason", ""))
    )


def klevel_schema_valid(model: dict[str, Any]) -> bool:
    expected = EXPECTED_KLEVEL.get(str(model.get("transition_id")))
    if not expected:
        return False
    return all(model.get(key) == value for key, value in expected.items())


def klevel_reduction_verdict(model: dict[str, Any]) -> str:
    if not klevel_schema_valid(model):
        return "REDUCTION_UNCHECKED"
    threshold = int(model.get("threshold", 0))
    upper = int(model.get("upper_axis_value", 0)) > threshold
    reduced = int(model.get("reduced_axis_value", 0)) > threshold
    if upper and not reduced:
        return "FAILS_WITH_WITNESS"
    if upper == reduced:
        return "DEMOTABLE_WITH_LOST_WITNESS"
    return "REDUCTION_UNCHECKED"


def observed(row: dict[str, Any]) -> str:
    if has_forbidden_key(row.get("model", {})):
        return "REJECT_FLAG_ORACLE_INPUT"
    model = row.get("model", {})
    theorem_id = row.get("theorem_id")
    case_type = row.get("case_type")
    if case_type == "theorem_case":
        if theorem_id == "T133-K0-RES":
            ok = model.get("rho_cell_a") == model.get("rho_cell_b") and model.get("claims_raw_separation") is False
        elif theorem_id == "T133-OMEGA-STATUS":
            ok = (
                model.get("death") is True
                and model.get("live") is False
                and model.get("residue_id") not in {None, "", model.get("identity_token")}
                and model.get("rebirth_source_residue_id") == model.get("residue_id")
                and model.get("claimed_identity_continuation") is False
            )
        elif theorem_id == "T133-K-ZERO":
            ok = (
                model.get("admissible_nonempty") is True
                and model.get("cycle_witness") is True
                and model.get("claimed_k") == 0
                and zero_cause_active(model.get("zero_causes", {}))
            )
        elif theorem_id == "T133-BOUNDARY":
            if model.get("metric_measure_declared") is True:
                threshold = float(model.get("threshold"))
                value = float(model.get("state_value"))
                metric_failure = value > threshold
            else:
                metric_failure = None
            classifier_failure = bool(model.get("classifier_failure"))
            ok = model.get("boundary_kind") == "classifier" and (
                metric_failure is None or metric_failure == classifier_failure
            )
        elif theorem_id == "T133-HYBRID":
            guard = bool(model.get("guard"))
            expected_next = model.get("reset_target") if guard else model.get("step_target")
            derivative_ok = not bool(model.get("derivative_requested")) or bool(model.get("charted"))
            smooth_step_ok = model.get("smooth_step_target") in {None, model.get("flow_one_target")}
            ok = model.get("actual_next") == expected_next and derivative_ok and smooth_step_ok
        elif theorem_id == "T133-DIM":
            hist = model.get("historical", [])
            eff = model.get("effective", [])
            ok = (
                len(hist) >= 3
                and len(eff) >= 3
                and all(hist[idx] <= hist[idx + 1] for idx in range(len(hist) - 1))
                and any(eff[idx + 1] < eff[idx] for idx in range(len(eff) - 1))
            )
        elif theorem_id == "T133-CYCLE":
            ok = bool(model.get("live")) and cycle_or_maintenance(model)
        elif theorem_id == "T133-ID":
            ok = (
                model.get("morphism_class") in {"residue", "rebirth"}
                and model.get("identity_invariant_preserved") is False
                and model.get("claimed_identity_continuation") is False
            )
        elif theorem_id == "T133-MIN":
            cases = model.get("component_cases", [])
            ok = (
                len(cases) == len(COMPONENT_FIELDS)
                and {case.get("target_component") for case in cases} == set(COMPONENT_FIELDS)
                and all(component_case_valid(case) for case in cases)
            )
        elif theorem_id == "T133-KLEVEL":
            transitions = model.get("transitions", [])
            ok = (
                len(transitions) == len(EXPECTED_KLEVEL)
                and {transition.get("transition_id") for transition in transitions} == set(EXPECTED_KLEVEL)
                and all(
                klevel_reduction_verdict(transition) == "FAILS_WITH_WITNESS"
                and klevel_reduction_verdict(transition.get("demotion_case", {})) == "DEMOTABLE_WITH_LOST_WITNESS"
                for transition in transitions
                )
            )
        else:
            ok = False
        return "ACCEPT" if ok else "REJECT"
    if case_type == "component_keep_drop_witness":
        return semantic_tuple_verdict(model.get("drop", {}))
    if case_type == "adjacent_k_transition_witness":
        return klevel_reduction_verdict(model)
    if case_type == "mutation_control":
        mutated = dict(model.get("mutated_row", {}))
        return observed(mutated)
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


def evaluate(row: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)
    if any(key.startswith("observed_") for key in row):
        out["input_schema_violation"] = "input rows must not contain observed_* verdict fields"
        out["passed"] = False
        return out
    obs = observed(row)
    if row.get("case_type") == "component_keep_drop_witness":
        out["observed_keep_verdict"] = semantic_tuple_verdict(row.get("model", {}).get("keep", {}))
        out["observed_drop_verdict"] = obs
        out["passed"] = out["observed_keep_verdict"] == row.get("expected_keep_verdict") and obs == row.get("expected_drop_verdict")
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
        "schema_id": "OC133_FINITE_MODEL_CHECKS_v12_HARDENED_SEMANTIC_EXECUTED",
        "release_id": "oc_core_1_3_3",
        "version": "1.3.3",
        "runner": "proofs/finite_model_checks/run_finite_model_checks.py",
        "runner_sha256": sha256_file(Path(__file__)),
        "input_ref": "proofs/finite_model_checks/OC133_FINITE_MODEL_INPUTS.json",
        "input_sha256": sha256_file(INPUT),
        "command": "python proofs/finite_model_checks/run_finite_model_checks.py",
        "semantic_evaluator": True,
        "input_observed_field_total": sum(1 for row in inputs["rows"] for key in row if key.startswith("observed_")),
        "flag_oracle_key_total": sum(
            1 for row in inputs["rows"]
            if row.get("case_type") != "mutation_control" and has_forbidden_key(row.get("model", {}))
        ),
        "flag_oracle_mutation_total": sum(
            1 for row in inputs["rows"]
            if row.get("case_type") == "mutation_control" and has_forbidden_key(row.get("model", {}))
        ),
        "case_total": len(rows),
        "positive_case_total": sum(1 for row in rows if row.get("case_type") == "theorem_case" and row.get("expected_verdict") == "ACCEPT"),
        "negative_case_total": sum(1 for row in rows if row.get("case_type") == "theorem_case" and row.get("expected_verdict") == "REJECT"),
        "component_witness_total": sum(1 for row in rows if row.get("case_type") == "component_keep_drop_witness"),
        "k_transition_witness_total": sum(1 for row in rows if row.get("case_type") == "adjacent_k_transition_witness" and row.get("expected_reduction_verdict") == "FAILS_WITH_WITNESS"),
        "k_transition_negative_total": sum(1 for row in rows if row.get("case_type") == "adjacent_k_transition_witness" and row.get("expected_reduction_verdict") == "DEMOTABLE_WITH_LOST_WITNESS"),
        "mutation_control_total": sum(1 for row in rows if row.get("case_type") == "mutation_control"),
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
